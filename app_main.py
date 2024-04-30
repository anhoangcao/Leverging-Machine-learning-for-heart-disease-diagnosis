
import streamlit as st

# Set the page config as the first command
st.set_page_config(
    page_title="Heart Disease Prediction App",
    page_icon="images/heart-fav.png"
)

from pymongo import MongoClient
import hashlib
from urllib.parse import quote_plus
import app_heart_key
import app_heart_sound
import app_heart_ecg

# # This should be your first Streamlit command
# st.set_page_config(
#     page_title="Heart Disease Prediction App",
#     page_icon="🧡",
#     layout="wide",
#     initial_sidebar_state="expanded",
# )

# Check if logged_out flag is set to True
if 'logged_out' in st.session_state and st.session_state['logged_out']:
    # Reset the session state as needed
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    # Optionally, you can direct the user to a specific page or state
    st.session_state['page'] = 'login'  # Assuming you have a page state management

# Hardcoded credentials for development; replace with st.secrets for production
username = "anhoang100402"
password = "Abc1234"

# MongoDB setup
username = quote_plus(username)
password = quote_plus(password)
mongo_uri = f"mongodb+srv://{username}:{password}@cluster0.qeoxq3z.mongodb.net/?retryWrites=true&w=majority"
client = MongoClient(mongo_uri)
db = client['user_db']

# Password hashing
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# Registration form (Updated to include Account Type)
def show_registration_page():
    st.title('Register')
    email = st.text_input('Email', key='register_email')
    username = st.text_input('Username', key='register_username')
    password = st.text_input('Password', type='password', key='register_password')
    account_type = st.radio("Account type", ('Patient', 'Doctor'))

    if st.button('Register'):
        if username and password and email:
            if account_type == 'Patient':
                collection = db['users']
            else:
                collection = db['doctors']

            # Check if the username or email already exists
            if collection.count_documents({'$or': [{'username': username}, {'email': email}]}) == 0:
                hashed_pwd = hash_password(password)
                collection.insert_one({'username': username, 'password': hashed_pwd, 'email': email})
                st.success('User registered successfully!')
            else:
                st.error('Username or email already exists.')
        else:
            st.error('Username, password, or email cannot be empty.')


# Login form (Updated to handle both users and doctors)
def show_login_page():
    st.title('Login')
    email = st.text_input('Email', key='login_email')  # Thêm trường email
    username = st.text_input('Username', key='login_username')
    password = st.text_input('Password', type='password', key='login_password')
    account_type = st.radio("Account type", ('Patient', 'Doctor'))

    if st.button('Login'):
        if account_type == 'Patient':
            collection = db['users']
        else:
            collection = db['doctors']

        # Tìm người dùng bằng cả tên người dùng và email
        user = collection.find_one({'username': username, 'email': email, 'password': hash_password(password)})
        if user:
            st.success('Logged in successfully!')
            st.session_state['login_status'] = True
            st.session_state['email'] = email  # Lưu email vào trạng thái phiên
            st.session_state['username'] = username
            st.session_state['account_type'] = account_type
        else:
            st.error('Invalid username, email, or password.')


# Main app logic (Updated)
if 'login_status' not in st.session_state:
    st.session_state['login_status'] = False
    st.session_state['account_type'] = None  # Initialize account type in session state

if st.session_state['login_status']:
    st.title('Heart Condition Prediction')
    if st.session_state['account_type'] == 'Doctor':
        # Doctors can access both tabs
        tab1, tab2, tab3 = st.tabs(["Diagnosis is by signs of heart disease", "Diagnosis of heart disease using ECG images", "Diagnose heart disease using heartbeat sounds"])
        with tab1:
            app_heart_key.main()
        with tab2:
            app_heart_ecg.main()
        with tab3:         
            app_heart_sound.main()
    elif st.session_state['account_type'] == 'Patient':
        # Users can only access the first tab
        app_heart_key.main()
else:
    page = st.sidebar.selectbox('Page', ['Login', 'Register'])

    if page == 'Login':
        show_login_page()
    else:
        show_registration_page()

