import streamlit as st
import firebase_admin
from firebase_admin import credentials, db

# Initialize Firebase once
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

st.title("🔌 Home Automation Dashboard")
st.subheader("Control up to 4 Relays")

# UI Layout for 4 relays
for i in range(1, 5):
    col1, col2 = st.columns([2, 1])
    with col1:
        label = st.text_input(f"Relay {i} Name", f"Relay {i}", key=f"name_{i}")
    with col2:
        toggle = st.toggle("On/Off", key=f"toggle_{i}")

    # Update Firebase on toggle
    try:
        db.reference(f"/relay{i}").set(toggle)
    except Exception as e:
        st.error(f"Failed to update relay{i}: {e}")
