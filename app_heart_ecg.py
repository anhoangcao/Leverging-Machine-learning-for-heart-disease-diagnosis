import streamlit as st
import tensorflow as tf
import numpy as np
import cv2
from PIL import Image
from urllib.parse import quote_plus
from pymongo import MongoClient

# Import additional required libraries
from datetime import datetime

# Load model
@st.cache(allow_output_mutation=True)
def load_model():
    model = tf.keras.models.load_model('model/ECG1D-98.h5')
    return model

model = load_model()

# MongoDB setup
username = "anhoang100402"
password = "Abc1234"
username_encoded = quote_plus(username)
password_encoded = quote_plus(password)
mongo_uri = f"mongodb+srv://{username_encoded}:{password_encoded}@cluster0.qeoxq3z.mongodb.net/?retryWrites=true&w=majority"
client = MongoClient(mongo_uri)
db = client['user_db'] 
collection = db['information_heart_ecgs']  # The collection name

def save_to_mongodb(data):
    """Function to save data to MongoDB."""
    try:
        collection.insert_one(data)
    except Exception as e:
        st.error(f"An error occurred: {e}")

# Updated class labels
classes = {
    0: 'Myocardial Infarction',
    1: 'Have a History of Myocardial Infraction',
    2: 'Abnormal Heart Beat',
    3: 'Normal Heart'
}

def preprocess_image(image, target_size=(224, 224)):
    if image.mode != "RGB":
        image = image.convert("RGB")
    image = image.resize(target_size)
    image = np.array(image)
    image = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)  # Convert to grayscale
    image = np.expand_dims(image, axis=0)
    return image

def main():
    st.title("Diagnosis of heart disease using ECG images")
    st.subheader("This application is designed to help you accurately diagnose your heart disease condition through ECG images. Just upload the image file (.jpg, .png) of your heart disease ECG and they I will analyze that file to determine what type of heart disease your ECG image has.")

    col1, col2 = st.columns([1, 3])
    with col1:
        st.image("images/doctor.png",
                    caption="I will help you diagnose your heart health! - 2D Convolutional Neural Network",
                    width=150)
    with col2:
        st.markdown("""
        Here are the 4 main types of heart disease you need to know about:
                
        1. Myocardial Infarction: Myocardial infarction.
        2. Abnormal Heart Beat: Abnormal heart beat.
        3. Have a History of Myocardial Infraction: Have a history of myocardial infarction.
        4. Normal Heart: Normal heart.

        To start diagnosing, simply follow these steps:
        1. Fill in the necessary personal information.
        2. Click the "Browse Files" button to upload your image file and wait for the analysis results.
                
        **Use this app to gain a deeper understanding of your heart health.**
            
        """)

    # User information inputs
    name = st.text_input("Patient Name:")
    gender = st.selectbox("Gender:", ["Male", "Female", "Other"])
    age = st.number_input("Age:", min_value=0, max_value=120, step=1)

    uploaded_file = st.file_uploader("Choose an ECG image...", type=["jpg", "png"])
    if uploaded_file is not None:
        image = Image.open(uploaded_file)
        st.image(image, caption='Uploaded ECG Image.', use_column_width=True)
        st.write("")

        image = preprocess_image(image)

        # Make prediction
        predictions = model.predict(image)
        predicted_class = np.argmax(predictions, axis=1)[0]
        confidence = np.max(tf.nn.softmax(predictions[0])) * 100

        # Convert NumPy types to Python native types for MongoDB
        predicted_class_python = int(predicted_class)  # Convert to Python int
        confidence_python = float(confidence)  # Ensure confidence is a Python float

        # Get the class name instead of the class index
        predicted_class_name = classes[predicted_class_python]

        # Prepare data to save
        data_to_save = {
            "patient_name": name,
            "gender": gender,
            "age": age,
            "prediction": predicted_class_name,  # Save class name instead of index
            "confidence": confidence_python,
            "timestamp": datetime.now()
        }

        # Save data to MongoDB
        save_to_mongodb(data_to_save)

        # Display user information (optional)
        st.write("========================================================================================")
        st.write("Patient Information and Result Prediction:")
        st.write(f"Patient name: {name}")
        st.write(f"Gender: {gender}")
        st.write(f"Age: {age}")

        # Display the prediction
        st.write("Type of Heart Disease:")
        st.success(f"{classes[predicted_class]}")
        st.write(f"Prediction Probability: {confidence:.2f}%")

if __name__ == "__main__":
    main()
