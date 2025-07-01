import streamlit as st
import pyrebase
from datetime import time, datetime
import os
from dotenv import load_dotenv

# --- Page Configuration ---
st.set_page_config(
    page_title="Smart School Bell",
    page_icon="🔔",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- Firebase Configuration Loader ---
def get_firebase_config():
    """
    Retrieves Firebase config from Streamlit secrets if available,
    otherwise falls back to a local .env file for development.
    """
    # Check if running on Streamlit Cloud (where st.secrets is available)
    if hasattr(st, 'secrets'):
        try:
            return {
                "apiKey": st.secrets["firebase"]["apiKey"],
                "authDomain": st.secrets["firebase"]["authDomain"],
                "databaseURL": st.secrets["firebase"]["databaseURL"],
                "projectId": st.secrets["firebase"]["projectId"],
                "storageBucket": st.secrets["firebase"]["storageBucket"],
                "messagingSenderId": st.secrets["firebase"]["messagingSenderId"],
                "appId": st.secrets["firebase"]["appId"]
            }
        except (KeyError, AttributeError):
            st.error("Firebase secrets not found on Streamlit Cloud. Please configure them in your app's settings.")
            st.stop()
           
    # Fallback for local development using a .env file
    else:
        load_dotenv()
        required_keys = [
            "FIREBASE_API_KEY", "FIREBASE_AUTH_DOMAIN", "FIREBASE_DATABASE_URL",
            "FIREBASE_PROJECT_ID", "FIREBASE_STORAGE_BUCKET",
            "FIREBASE_MESSAGING_SENDER_ID", "FIREBASE_APP_ID"
        ]
        if not all(os.getenv(key) for key in required_keys):
            st.error("A .env file with all required Firebase keys was not found for local development. Please create one.")
            st.stop()
           
        return {
            "apiKey": os.getenv("FIREBASE_API_KEY"),
            "authDomain": os.getenv("FIREBASE_AUTH_DOMAIN"),
            "databaseURL": os.getenv("FIREBASE_DATABASE_URL"),
            "projectId": os.getenv("FIREBASE_PROJECT_ID"),
            "storageBucket": os.getenv("FIREBASE_STORAGE_BUCKET"),
            "messagingSenderId": os.getenv("FIREBASE_MESSAGING_SENDER_ID"),
            "appId": os.getenv("FIREBASE_APP_ID")
        }

# --- Firebase Initialization ---
try:
    firebase_config = get_firebase_config()
    firebase = pyrebase.initialize_app(firebase_config)
    auth = firebase.auth()
    db = firebase.database()
except Exception as e:
    st.error(f"Firebase initialization failed. Please check your credentials. Error: {e}")
    st.stop()

# --- App State Management ---
if 'user' not in st.session_state:
    st.session_state.user = None

# --- UI Functions ---
def apply_custom_css():
    st.markdown("""
        <style>
            .stButton>button {
                width: 100%;
                border-radius: 20px;
            }
            /* Add a nice border and padding to containers */
            .st-emotion-cache-1xw8zd6, .st-emotion-cache-4z1n4h {
                border: 1px solid rgba(49, 51, 63, 0.2);
                border-radius: 0.5rem;
                padding: 1rem;
            }
            .st-emotion-cache-16txtl3 {
                padding-top: 1rem;
            }
        </style>
    """, unsafe_allow_html=True)

# --- Main Application ---
apply_custom_css()

# --- Header ---
col_logo, col_title = st.columns([1, 4])
with col_logo:
    st.image("https://em-content.zobj.net/source/apple/354/bell_1f514.png", width=100)
with col_title:
    st.title("Smart School Bell System")
st.markdown("---")

# --- Page Router ---
if st.session_state.user:
    # --- DASHBOARD PAGE ---
    st.sidebar.subheader("Welcome,")
    st.sidebar.write(st.session_state.user['email'])
    if st.sidebar.button("Logout", type="primary"):
        st.session_state.user = None
        st.rerun()

    # The teacher's schedule is stored under a node named after their unique user ID (UID)
    uid = st.session_state.user['localId']
    schedule_ref = db.child("schedules").child(uid)
   
    # Using st.session_state to hold the schedule for editing
    if 'lectures' not in st.session_state or st.session_state.user.get('uid_changed'):
        schedule_data = schedule_ref.get().val() or []
        st.session_state.lectures = schedule_data
        if st.session_state.user:
            st.session_state.user['uid_changed'] = False

    st.header("Manage Your Lecture Schedule")
   
    # Display existing lectures
    if st.session_state.lectures:
        st.subheader("Current Lectures")
        for i, lecture in enumerate(st.session_state.lectures):
            col1, col2, col3, col4 = st.columns([1, 3, 3, 1])
            with col1:
                st.write(f"**{i+1}.**")
            with col2:
                new_start = st.time_input(
                    "Start",
                    value=datetime.strptime(lecture['start'], "%H:%M").time(),
                    key=f"start_{i}",
                )
                st.session_state.lectures[i]['start'] = new_start.strftime("%H:%M")
            with col3:
                new_end = st.time_input(
                    "End",
                    value=datetime.strptime(lecture['end'], "%H:%M").time(),
                    key=f"end_{i}",
                )
                st.session_state.lectures[i]['end'] = new_end.strftime("%H:%M")
            with col4:
                st.write("")  # Add spacing
                if st.button("🗑️", key=f"delete_{i}", help="Delete this lecture"):
                    st.session_state.lectures.pop(i)
                    st.rerun()
        st.markdown("---")
    
    # Add new lecture section
    st.subheader("Add New Lecture")
    col_new_start, col_new_end, col_add_btn = st.columns([2, 2, 1])
    
    with col_new_start:
        new_start_time = st.time_input(
            "Start Time", 
            value=time(9, 0),  # Default to 9:00 AM
            key="new_lecture_start"
        )
    
    with col_new_end:
        new_end_time = st.time_input(
            "End Time", 
            value=time(9, 45),  # Default to 9:45 AM
            key="new_lecture_end"
        )
    
    with col_add_btn:
        st.write("")  # Add some spacing
        st.write("")  # Add more spacing to align with time inputs
        if st.button("➕ Add Lecture", key="add_new_lecture", help="Add this lecture to schedule"):
            # Validate that end time is after start time
            if new_end_time > new_start_time:
                new_lecture = {
                    'start': new_start_time.strftime("%H:%M"),
                    'end': new_end_time.strftime("%H:%M")
                }
                st.session_state.lectures.append(new_lecture)
                st.success(f"Added lecture: {new_start_time.strftime('%H:%M')} - {new_end_time.strftime('%H:%M')}")
                st.rerun()
            else:
                st.error("End time must be after start time!")
    
    # Save button
    st.markdown("---")
    col_save1, col_save2, col_save3 = st.columns([1, 2, 1])
    with col_save2:
        if st.button("💾 Save All Changes", type="primary", use_container_width=True):
            # Sort lectures by start time before saving
            st.session_state.lectures.sort(key=lambda x: x['start'])
            schedule_ref.set(st.session_state.lectures)
            st.toast("Schedule saved successfully!", icon="🎉")

else:
    # --- LOGIN / SIGNUP PAGE ---
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.subheader("Welcome to Smart School Bell")
        choice = st.selectbox("Choose an Action", ["Login", "Sign Up"])
       
        email = st.text_input("Email Address", key="email_input")
        password = st.text_input("Password", type="password", key="password_input")
       
        if choice == "Login":
            if st.button("Login", type="primary", use_container_width=True):
                if email and password:
                    try:
                        user = auth.sign_in_with_email_and_password(email, password)
                        st.session_state.user = user
                        st.session_state.user['uid_changed'] = True # Flag to reload schedule
                        st.success("Login successful!")
                        st.rerun()
                    except Exception as e:
                        error_message = str(e)
                        if "INVALID_EMAIL" in error_message:
                            st.error("Invalid email format.")
                        elif "EMAIL_NOT_FOUND" in error_message:
                            st.error("No account found with this email.")
                        elif "INVALID_PASSWORD" in error_message:
                            st.error("Incorrect password.")
                        else:
                            st.error("Login failed. Please check your credentials.")
                else:
                    st.error("Please enter both email and password.")
       
        if choice == "Sign Up":
            if st.button("Create Account", type="primary", use_container_width=True):
                if email and password:
                    try:
                        user = auth.create_user_with_email_and_password(email, password)
                        # Create an empty schedule for new users
                        db.child("schedules").child(user['localId']).set([])
                        st.session_state.user = user
                        st.session_state.user['uid_changed'] = True
                        st.success("Account created successfully! You are now logged in.")
                        st.rerun()
                    except Exception as e:
                        error_message = str(e)
                        if "EMAIL_EXISTS" in error_message:
                            st.error("An account with this email already exists. Please log in instead.")
                        elif "WEAK_PASSWORD" in error_message:
                            st.error("The password is too weak. It must be at least 6 characters long.")
                        elif "INVALID_EMAIL" in error_message:
                            st.error("Invalid email format.")
                        else:
                            st.error("Could not create account. Please try again.")
                else:
                    st.error("Please enter both email and password.")

        # Additional info
        st.markdown("---")
        st.info("💡 **Tip**: After logging in, you can add and manage your lecture schedule. Times will be automatically sorted when saved.")
