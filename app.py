import streamlit as st
import firebase_admin
from firebase_admin import credentials, db
import json

# Initialize Firebase only once
if 'firebase_initialized' not in st.session_state:
    cred = credentials.Certificate({
        "type": st.secrets["firebase"]["type"],
        "project_id": st.secrets["firebase"]["project_id"],
        "private_key_id": st.secrets["firebase"]["private_key_id"],
        "private_key": st.secrets["firebase"]["private_key"].replace('\\n', '\n'),
        "client_email": st.secrets["firebase"]["client_email"],
        "client_id": st.secrets["firebase"]["client_id"],
        "auth_uri": st.secrets["firebase"]["auth_uri"],
        "token_uri": st.secrets["firebase"]["token_uri"],
        "auth_provider_x509_cert_url": st.secrets["firebase"]["auth_provider_x509_cert_url"],
        "client_x509_cert_url": st.secrets["firebase"]["client_x509_cert_url"],
        "universe_domain": st.secrets["firebase"]["universe_domain"]
    })

    firebase_admin.initialize_app(cred, {
        'databaseURL': 'https://home---automation-default-rtdb.firebaseio.com/'
    })
    st.session_state.firebase_initialized = True

# UI
st.title("💡 Firebase Realtime Control Panel")

# Input field
relay_state = st.selectbox("Relay State", ["ON", "OFF"])

if st.button("Send to Firebase"):
    try:
        ref = db.reference("/relay1")
        ref.set(relay_state)
        st.success(f"Successfully set relay to: {relay_state}")
    except Exception as e:
        st.error(f"Error writing to Firebase: {e}")

# Read current value
if st.button("Check Current Value"):
    try:
        value = db.reference("/relay1").get()
        st.info(f"Current Firebase value: {value}")
    except Exception as e:
        st.error(f"Error reading from Firebase: {e}")
