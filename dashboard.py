import streamlit as st
from pymongo import MongoClient
from urllib.parse import quote_plus
from bson import ObjectId

# Hardcoded credentials for development; replace with st.secrets for production
username = "anhoang100402"
password = "Abc1234"

# MongoDB setup
username = quote_plus(username)
password = quote_plus(password)
mongo_uri = f"mongodb+srv://{username}:{password}@cluster0.qeoxq3z.mongodb.net/?retryWrites=true&w=majority"
client = MongoClient(mongo_uri)
db = client['user_db']  # Use the same database name as in app_main.py
collection_heart_keys = db['information_heart_keys']
collection_heart_sounds = db['information_heart_sounds']
collection_heart_ecgs = db['information_heart_ecgs']

# Function to fetch data from MongoDB
def fetch_users(account_type):
    collection_name = 'doctors' if account_type == 'doctor' else 'users'
    collection_heart_keys = db[collection_name]
    return list(collection_heart_keys.find({}))

def fetch_heart_key_data():
    """Fetches heart key data from MongoDB."""
    collection_heart_keys = db['information_heart_keys']  # Adjust collection name accordingly
    records = list(collection_heart_keys.find({}))
    return records

def fetch_heart_sound_data():
    collection_heart_sounds = db['information_heart_sounds']  # Adjust collection name accordingly
    records_sounds = list(collection_heart_sounds.find({}))
    return records_sounds

def fetch_heart_ecg_data():
    collection_heart_ecgs = db['information_heart_ecgs']  # Adjust collection name accordingly
    records_ecgs = list(collection_heart_ecgs.find({}))
    return records_ecgs

def display_users(account_type):
    users = fetch_users(account_type)
    collection_name = 'doctors' if account_type == 'doctor' else 'users'
    
    # Manual headers
    header_cols = st.columns([2, 1.5, 2, 0.6, 0.7])  # Adjusted for the edit action
    header_cols[0].write("ID")
    header_cols[1].write("Name")
    header_cols[2].write("Email")
    header_cols[3].write("")
    header_cols[4].write("Actions")

    for user in users:
        cols = st.columns([2, 1.5, 2, 0.6, 0.7])  # Adjust for the edit and delete button
        cols[0].write(user['_id'])
        cols[1].write(user['username'])
        cols[2].write(user['email'])
        
        # Edit functionality
        edit_key = f"edit-{user['_id']}"
        if cols[3].button('Edit', key=edit_key):
            # Using Streamlit's session state to hold the editing user's ID and current details
            st.session_state['editing_user_id'] = user['_id']
            st.session_state['editing_username'] = user['username']
            st.session_state['editing_email'] = user['email']
            st.session_state['edit_mode'] = True
            st.session_state['collection_name'] = collection_name  # Save collection name in session state

        # Delete functionality
        delete_key = f"delete-{user['_id']}"
        if cols[4].button('Delete', key=delete_key):
            db[collection_name].delete_one({"_id": user['_id']})
            st.experimental_rerun()

    # Check if we are in edit mode
    if st.session_state.get('edit_mode'):
        with st.form("edit_user_form"):
            st.write("Edit Details")
            edited_name = st.text_input("Name", value=st.session_state['editing_username'], key="edit_name")
            edited_email = st.text_input("Email", value=st.session_state['editing_email'], key="edit_email")
            
            save_changes = st.form_submit_button("Save Changes")
            cancel_changes = st.form_submit_button("Cancel")

            if save_changes:
                # Perform the update operation in MongoDB
                db[st.session_state['collection_name']].update_one(
                    {"_id": st.session_state['editing_user_id']},
                    {"$set": {"username": edited_name, "email": edited_email}}
                )
                # Clear the session state after updating
                clear_edit_session_state()
                st.experimental_rerun()

            if cancel_changes:
                # Clear the session state without updating
                clear_edit_session_state()
                st.experimental_rerun()

def clear_edit_session_state():
    """Helper function to clear the session state related to editing a user."""
    for key in ['editing_user_id', 'editing_username', 'editing_email', 'edit_mode', 'collection_name']:
        if key in st.session_state:
            del st.session_state[key]

records = fetch_heart_key_data()  # Sử dụng hàm đã định nghĩa trước đó để lấy dữ liệu

def delete_record_by_id(record_id):
    collection_heart_keys = db['information_heart_keys']
    # Chuyển đổi record_id từ chuỗi sang ObjectId nếu cần
    result = collection_heart_keys.delete_one({'_id': ObjectId(record_id)})
    if result.deleted_count > 0:
        st.success(f"Record with ID {record_id} has been deleted.")
    else:
        st.error("Failed to delete record.")

def display_heart_key_data():
    if records:
        # Tạo tiêu đề cho dữ liệu được hiển thị
        header_cols = st.columns([0.8, 2.5, 3.2, 3, 2.5, 2.5, 2])  # Điều chỉnh để bao gồm cột STT và datetime một cách chính xác
        header_cols[0].write("STT")  # STT
        header_cols[1].write("Patient name")
        header_cols[2].write("Heart disease factors")
        header_cols[3].write("Prediction")
        header_cols[4].write("Probability of heart disease (%)")
        header_cols[5].write("Date time")
        header_cols[6].write("Action")

        for index, record in enumerate(records, start=1):
            cols = st.columns([0.8, 2.5, 3.2, 3, 2.5, 2.5, 2])  # Phù hợp với layout đã được điều chỉnh
            cols[0].write(index)  # Hiển thị số thứ tự
            # Giả định 'username' hoặc một key tương tự để hiển thị tên bệnh nhân
            cols[1].write(record.get('username', 'N/A'))
            # Hiển thị 'user_input' dưới dạng text hoặc JSON, tùy thuộc vào sở thích của bạn
            cols[2].json(record['user_input'])  # Nếu bạn muốn hiển thị JSON trực tiếp
            cols[3].write("Heart disease" if record['prediction'] == 1 else "No heart disease")
            cols[4].write(f"{record['prediction_probability'] * 100:.2f}%")
            # Định dạng ngày giờ như mong muốn
            datetime_str = record.get('timestamp', 'Not available').strftime('%Y-%m-%d %H:%M:%S') if 'timestamp' in record else 'Not available'
            cols[5].write(datetime_str)
            # Giả sử `_id` được lưu trữ trong `record`
            if cols[6].button("Delete", key=f"delete_{index}"):
                record_id = record['_id']  # Lấy _id từ bản ghi, đảm bảo nó là chuỗi hoặc ObjectId
                delete_record_by_id(str(record_id))  # Chuyển đổi thành chuỗi nếu cần
                st.experimental_rerun()
 # Dừng vòng lặp để tránh re-render lỗi
    else:
        st.write("No records found.")


records_sounds = fetch_heart_sound_data()  # Sử dụng hàm đã định nghĩa trước đó để lấy dữ liệu

def delete_records_sounds_by_id(record_id):
    collection_heart_sounds = db['information_heart_sounds']
    # Chuyển đổi record_id từ chuỗi sang ObjectId nếu cần
    result = collection_heart_sounds.delete_one({'_id': ObjectId(record_id)})
    if result.deleted_count > 0:
        st.success(f"Record with ID {record_id} has been deleted.")
    else:
        st.error("Failed to delete record.")

def display_heart_sound_data():
    if records_sounds:
        # Tạo tiêu đề cho dữ liệu được hiển thị
        header_cols = st.columns([1, 2.5, 2, 1.5, 3, 2.6, 2.2, 2])  # Điều chỉnh để bao gồm cột STT và datetime một cách chính xác
        header_cols[0].write("STT")  # STT
        header_cols[1].write("Patient name")
        header_cols[2].write("Gender")
        header_cols[3].write("Age")
        header_cols[4].write("Heartbeat sound")
        header_cols[5].write("Probability (%)")
        header_cols[6].write("Date time")
        header_cols[7].write("Action")

        for index, record in enumerate(records_sounds, start=1):
            cols = st.columns([1, 2.5, 2, 1.5, 3, 2.6, 2.2, 2])  # Phù hợp với layout đã được điều chỉnh
            cols[0].write(index)  # Hiển thị số thứ tự
            # Giả định 'patient_name' hoặc một key tương tự để hiển thị tên bệnh nhân
            cols[1].write(record.get('patient_name', 'N/A'))
            # Hiển thị 'gender' dưới dạng text hoặc JSON, tùy thuộc vào sở thích của bạn
            cols[2].write(record['gender'])
            cols[3].write(f"{record['age']}")
            cols[4].write(record['prediction'])
            cols[5].write(f"{record['confidence'] * 100:.2f}%")
            # Định dạng ngày giờ như mong muốn
            datetime_str = record.get('timestamp', 'Not available').strftime('%Y-%m-%d %H:%M:%S') if 'timestamp' in record else 'Not available'
            cols[6].write(datetime_str)
            # Giả sử `_id` được lưu trữ trong `record`
            delete_button_key = f"delete_{record['_id']}"  # Tạo khóa duy nhất dựa trên _id
            if cols[7].button("Delete", key=delete_button_key):
                delete_records_sounds_by_id(str(record['_id']))  # Chuyển đổi thành chuỗi nếu cần
                st.experimental_rerun()
    # Dừng vòng lặp để tránh re-render lỗi
    else:
        st.write("No records found.")



records_ecgs = fetch_heart_ecg_data()  # Sử dụng hàm đã định nghĩa trước đó để lấy dữ liệu

def delete_records_ecgs_by_id(record_id):
    collection_heart_ecgs = db['information_heart_ecgs']
    # Chuyển đổi record_id từ chuỗi sang ObjectId nếu cần
    result = collection_heart_ecgs.delete_one({'_id': ObjectId(record_id)})
    if result.deleted_count > 0:
        st.success(f"Record with ID {record_id} has been deleted.")
    else:
        st.error("Failed to delete record.")

def display_heart_ecg_data():
    if records_ecgs:
        # Tạo tiêu đề cho dữ liệu được hiển thị
        header_cols = st.columns([1, 2.5, 2, 1.5, 3, 2.6, 2.2, 2])  # Điều chỉnh để bao gồm cột STT và datetime một cách chính xác
        header_cols[0].write("STT")  # STT
        header_cols[1].write("Patient name")
        header_cols[2].write("Gender")
        header_cols[3].write("Age")
        header_cols[4].write("ECG heart disease")
        header_cols[5].write("Probability (%)")
        header_cols[6].write("Date time")
        header_cols[7].write("Action")

        for index, record in enumerate(records_ecgs, start=1):
            cols = st.columns([1, 2.5, 2, 1.5, 3, 2.6, 2.2, 2])  # Phù hợp với layout đã được điều chỉnh
            cols[0].write(index)  # Hiển thị số thứ tự
            # Giả định 'patient_name' hoặc một key tương tự để hiển thị tên bệnh nhân
            cols[1].write(record.get('patient_name', 'N/A'))
            # Hiển thị 'gender' dưới dạng text hoặc JSON, tùy thuộc vào sở thích của bạn
            cols[2].write(record['gender'])
            cols[3].write(f"{record['age']}")
            cols[4].write(record['prediction'])
            cols[5].write(f"{record['confidence'] * 1:.2f}%")
            # Định dạng ngày giờ như mong muốn
            datetime_str = record.get('timestamp', 'Not available').strftime('%Y-%m-%d %H:%M:%S') if 'timestamp' in record else 'Not available'
            cols[6].write(datetime_str)
            # Giả sử `_id` được lưu trữ trong `record`
            delete_button_key = f"delete_{record['_id']}"  # Tạo khóa duy nhất dựa trên _id
            if cols[7].button("Delete", key=delete_button_key):
                delete_records_ecgs_by_id(str(record['_id']))  # Chuyển đổi thành chuỗi nếu cần
                st.experimental_rerun()
    # Dừng vòng lặp để tránh re-render lỗi
    else:
        st.write("No records found.")

# Page configuration and layout
st.set_page_config(page_title="Dashboard", page_icon="📊", layout="wide")
st.sidebar.title("Categories")
selected_category = st.sidebar.selectbox("Select categories", ["Account management", "Patient management"])

st.title("Dashboard")

if selected_category == "Account management":
    st.subheader("Account management")
    tab1, tab2 = st.tabs(["Doctor account", "Patient account"])
    with tab1:
        display_users('doctor')  # Ensure the correct collection_name is used
    with tab2:
        display_users('user')  # Ensure the correct collection_name is used


elif selected_category == "Patient management":
    st.subheader("Patient management")
    # Tabs for different functionalities related to patients
    tab1, tab2, tab3 = st.tabs(["Diagnosis is by signs of heart disease", "Diagnosis of heart disease using ECG images", "Diagnose heart disease using heartbeat sounds"])

    with tab1:
        display_heart_key_data()
    with tab2:
        display_heart_ecg_data()
    with tab3:
        display_heart_sound_data()

# elif selected_category == "Quản lý bác sĩ":
#     st.subheader("Quản lý bác sĩ")
#     # Code for managing doctors goes here
#     st.write("Chức năng quản lý bác sĩ đang được phát triển.")
