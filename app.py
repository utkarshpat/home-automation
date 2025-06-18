import streamlit as st
import firebase_admin
from firebase_admin import credentials, db

# Firebase setup
if not firebase_admin._apps:
    cred = credentials.Certificate("firebase_config.json")
    firebase_admin.initialize_app(cred, {
        'databaseURL': 'https://home---automation-default-rtdb.firebaseio.com/'
    })

# Streamlit UI
st.title("Relay Control Dashboard 🔌")

relay1 = st.checkbox("Relay 1")
relay2 = st.checkbox("Relay 2")
relay3 = st.checkbox("Relay 3")
relay4 = st.checkbox("Relay 4")

db.reference('/relay1').set(relay1)
db.reference('/relay2').set(relay2)
db.reference('/relay3').set(relay3)
db.reference('/relay4').set(relay4)
