import streamlit as st
import librosa
import numpy as np
from tensorflow.keras.models import load_model
import matplotlib.pyplot as plt
import librosa.display
from pymongo import MongoClient
from urllib.parse import quote_plus

# Import additional required libraries
from datetime import datetime

# Assuming you have a trained LSTM model saved at 'model/lstm_model.h5'
MODEL_PATH = 'model/lstm_model.h5'
DURATION = 10  # Duration to which audio files will be padded or trimmed
SR = 22050  # Sampling rate to be used for audio files

# MongoDB setup
username = "anhoang100402"
password = "Abc1234"
username_encoded = quote_plus(username)
password_encoded = quote_plus(password)
mongo_uri = f"mongodb+srv://{username_encoded}:{password_encoded}@cluster0.qeoxq3z.mongodb.net/?retryWrites=true&w=majority"
client = MongoClient(mongo_uri)
db = client['user_db'] 
collection = db['information_heart_sounds']  # The collection name

def save_to_mongodb(data):
    """Function to save data to MongoDB."""
    try:
        collection.insert_one(data)
    except Exception as e:
        st.error(f"An error occurred: {e}")

def display_waveform(audio, sr):
    """Display Waveform."""
    plt.figure(figsize=(10, 4))
    librosa.display.waveshow(audio, sr=sr)
    plt.title('Waveform')
    plt.xlabel('Time (s)')  # Thêm tiêu đề trục hoành
    plt.ylabel('Amplitude')  # Thêm tiêu đề trục tung
    st.pyplot(plt)

def display_spectrum(audio, sr):
    """Display Spectrum."""
    plt.figure(figsize=(10, 4))
    fft = np.fft.fft(audio)
    magnitude = np.abs(fft)
    frequency = np.linspace(0, sr, len(magnitude))
    plt.plot(frequency[:int(len(frequency)/2)], magnitude[:int(len(magnitude)/2)])  # Display only half
    plt.title('Spectrum')
    plt.xlabel('Frequency (Hz)')  # Thêm tiêu đề trục hoành
    plt.ylabel('Magnitude')  # Thêm tiêu đề trục tung
    st.pyplot(plt)


def display_spectrogram(audio, sr):
    """Display Spectrogram."""
    plt.figure(figsize=(10, 4))
    stft = librosa.stft(audio)
    stft_db = librosa.amplitude_to_db(abs(stft))
    librosa.display.specshow(stft_db, sr=sr, x_axis='time', y_axis='hz', cmap='Blues')
    plt.colorbar(format="%+2.0f dB")
    plt.title('Spectrogram')
    plt.xlim([0, 8])  # Giới hạn trục thời gian từ 0 đến 8 giây
    st.pyplot(plt)


def display_mfccs(audio, sr):
    """Display MFCCs."""
    plt.figure(figsize=(10, 4))
    mfccs = librosa.feature.mfcc(y=audio, sr=sr, n_mfcc=20)
    librosa.display.specshow(mfccs, sr=sr, x_axis='time', y_axis='hz', cmap='Blues')
    plt.colorbar()
    plt.title('MFCCs')
    plt.xlim([0, 8])  # Giới hạn trục thời gian từ 0 đến 8 giây
    st.pyplot(plt)


def main():
    st.title("Diagnose heart disease using heartbeat sounds")
    st.subheader("Want to understand your heart rate better? This application is designed to help you accurately diagnose your heart rate condition. Just upload an audio file (.wav) recording of your heart sounds, and we will analyze it to determine the type of heartbeat you have.")

    col1, col2 = st.columns([1, 3])
    with col1:
        st.image("images/doctor.png",
                 caption="I'll help you diagnose your heart health! - Dr. Long Short Term Memory",
                 width=150)
    with col2:
        st.markdown("""
        Here are the 5 main heart sounds you need to know:
                    
        1. Artifact: Artifact sounds reflect disturbances not directly related to the heart's function, including noise from the surrounding environment or recording devices.
        2. Extra Heart Sounds (extrahls): Additional heart sounds, like "lub-lub dub" or "lub dub-dub," may indicate normality or abnormality depending on the specific context.
        3. Extrasystole: Extrasystole, a sign of abnormal heartbeats or skipped beats. While often not indicative of pathology, it can sometimes be related to heart issues.
        4. Murmur: Heart murmurs, a "whooshing" or "rumbling" sound occurring between "lub" and "dub" or after "dub," can be a manifestation of heart disease.
        5. Normal: Normal heart sounds, with a clear "lub dub" without any unusual noise, indicate a healthy heart state.

        To start the diagnosis, you just need to follow these steps:
        1. Fill in the necessary personal information.
        2. Click the "Browse files" button to upload your audio file and wait for the analysis results.
                    
        **Use this app to gain deeper insights into the health of your heart.**
              
        """)

    # Load the LSTM model
    model = load_model(MODEL_PATH)

    # Inputs for patient demographics
    patient_name = st.text_input("Patient Name")
    gender = st.selectbox("Gender", ["Male", "Female", "Other"])  # Gender input
    age = st.number_input("Age", min_value=0, max_value=120, step=1)  # Age input

    audio_file = st.file_uploader("Upload Heart Sound (.wav)", type=['wav'])
    if audio_file is not None:
        # Load and preprocess audio
        audio, sr = librosa.load(audio_file, sr=SR, duration=DURATION)
        if librosa.get_duration(y=audio, sr=sr) < DURATION:
            audio = librosa.util.fix_length(audio, size=SR * DURATION)

        st.write("========================================================================================")
        st.write("Patient Information and Result Prediction:")
        st.write(f"Patient name: {patient_name}")
        st.write(f"Gender: {gender}")
        st.write(f"Age: {age}")
        st.write(f"Audio signal charts:")

        # Display audio features separately
        display_waveform(audio, sr)
        display_spectrum(audio, sr)
        display_spectrogram(audio, sr)
        display_mfccs(audio, sr)

        # Extract MFCC features
        mfccs = librosa.feature.mfcc(y=audio, sr=sr, n_mfcc=52, n_fft=512, hop_length=2048)
        mfcc_mean = np.mean(mfccs.T, axis=0)

        # Reshape for the model
        mfcc_reshaped = mfcc_mean.reshape(1, 52, 1)

        # Predict the condition
        prediction = model.predict(mfcc_reshaped)

        # Map prediction to labels
        classes = ["artifact", "extrahls", "extrasystole", "murmur", "normal"]
        predicted_label = classes[np.argmax(prediction)]
        confidence = np.max(prediction)  # Get the confidence of the prediction

        # Prepare data to save
        data_to_save = {
            "patient_name": patient_name,
            "gender": gender,
            "age": age,
            "prediction": predicted_label,
            "confidence": float(confidence),
            "timestamp": datetime.now()
        }

        # Save data to MongoDB
        save_to_mongodb(data_to_save)

        st.write("Type of Heart Disease:")
        st.success(f"{predicted_label}")
        st.write(f"Classification Probability: {confidence}")

if __name__ == "__main__":
    main()
