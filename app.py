import streamlit as st
import datetime
import pytz
import firebase_admin
from firebase_admin import credentials, db
import json
import time

# Firebase setup using Streamlit secrets
if not firebase_admin._apps:
    cred = credentials.Certificate({
        "type": st.secrets["type"],
        "project_id": st.secrets["project_id"],
        "private_key_id": st.secrets["private_key_id"],
        "private_key": st.secrets["private_key"].replace("\\n", "\n"),
        "client_email": st.secrets["client_email"],
        "client_id": st.secrets["client_id"],
        "auth_uri": st.secrets["auth_uri"],
        "token_uri": st.secrets["token_uri"],
        "auth_provider_x509_cert_url": st.secrets["auth_provider_x509_cert_url"],
        "client_x509_cert_url": st.secrets["client_x509_cert_url"],
        "universe_domain": st.secrets["universe_domain"]
    })
    firebase_admin.initialize_app(cred, {
        'databaseURL': st.secrets["database_url"]
    })

# Timezone
IST = pytz.timezone('Asia/Kolkata')

# Load data from Firebase
ref = db.reference("relays")
def load_states():
    data = ref.get()
    if not data:
        return {}
    return data

def save_state(relay_name, data):
    ref.child(relay_name).set(data)

# Load initial states
relay_states = load_states()
current_time = datetime.datetime.now(IST)

def update_relay_state(relay_key):
    relay = relay_states[relay_key]

    # Auto ON/OFF Logic
    auto_on = st.session_state.get(relay_key + "_auto_on", 0)
    auto_off = st.session_state.get(relay_key + "_auto_off", 0)
    
    if auto_on > 0 and relay["last_off"]:
        off_time = datetime.datetime.fromisoformat(relay["last_off"])
        if (current_time - off_time).total_seconds() >= auto_on and not relay["status"]:
            relay["status"] = True
            relay["last_on"] = current_time.isoformat()

    if auto_off > 0 and relay["last_on"]:
        on_time = datetime.datetime.fromisoformat(relay["last_on"])
        if (current_time - on_time).total_seconds() >= auto_off and relay["status"]:
            relay["status"] = False
            relay["last_off"] = current_time.isoformat()
            relay["total_on_time"] += int((current_time - on_time).total_seconds())

    # Scheduler Logic
    sched_on = st.session_state.get(relay_key + "_sched_on")
    sched_off = st.session_state.get(relay_key + "_sched_off")

    if sched_on and current_time.time().hour == sched_on.hour and current_time.time().minute == sched_on.minute and not relay["status"]:
        relay["status"] = True
        relay["last_on"] = current_time.isoformat()

    if sched_off and current_time.time().hour == sched_off.hour and current_time.time().minute == sched_off.minute and relay["status"]:
        relay["status"] = False
        relay["last_off"] = current_time.isoformat()
        relay["total_on_time"] += int((current_time - datetime.datetime.fromisoformat(relay["last_on"])).total_seconds())

    save_state(relay_key, relay)

# Ensure all relays exist
for i in range(1, 5):
    relay_name = f"Relay {i}"
    if relay_name not in relay_states:
        relay_states[relay_name] = {
            "status": False,
            "last_on": None,
            "last_off": None,
            "total_on_time": 0,
            "name": relay_name
        }
    update_relay_state(relay_name)

st.set_page_config(layout="wide", page_title="Smart Home Dashboard", page_icon="🏠")
st.markdown("""
    <style>
    .stButton>button {
        height: 3em;
        width: 3em;
        font-size: 1.5em;
        border-radius: 50%;
    }
    </style>
""", unsafe_allow_html=True)
st.markdown("## 🏠 Smart Home Dashboard")

# Page selector
page = st.sidebar.selectbox("Choose page", ["Main Dashboard", "Schedule", "Statistics"])

def relay_ui(index):
    relay_key = f"Relay {index}"
    relay = relay_states[relay_key]

    col1, col2 = st.columns([3, 1])
    with col1:
        relay["name"] = st.text_input(f"Name for {relay_key}", relay["name"], key=relay_key + "_name")
    with col2:
        icon = "🟢" if relay["status"] else "🔴"
        if st.button(icon, key=relay_key + "_toggle"):
            now = datetime.datetime.now(IST)
            relay["status"] = not relay["status"]
            if relay["status"]:
                relay["last_on"] = now.isoformat()
            else:
                relay["last_off"] = now.isoformat()
                if relay["last_on"]:
                    last_on_dt = datetime.datetime.fromisoformat(relay["last_on"])
                    relay["total_on_time"] += int((now - last_on_dt).total_seconds())
            save_state(relay_key, relay)

    with st.expander(f"⚙️ Options for {relay_key}"):
        st.write("**Last ON:**", relay.get("last_on"))
        st.write("**Last OFF:**", relay.get("last_off"))
        st.write("**Today's ON Time (sec):**", relay.get("total_on_time", 0))

        timer_col1, timer_col2 = st.columns(2)
        with timer_col1:
            st.number_input("Auto ON after (sec)", min_value=0, key=relay_key + "_auto_on")
        with timer_col2:
            st.number_input("Auto OFF after (sec)", min_value=0, key=relay_key + "_auto_off")

        sched_col1, sched_col2 = st.columns(2)
        with sched_col1:
            st.time_input("Schedule ON", value=datetime.time(0, 0), key=relay_key + "_sched_on")
        with sched_col2:
            st.time_input("Schedule OFF", value=datetime.time(0, 0), key=relay_key + "_sched_off")

if page == "Main Dashboard":
    for row in range(2):
        cols = st.columns(2)
        for col in range(2):
            with cols[col]:
                relay_ui(row * 2 + col + 1)

elif page == "Schedule":
    st.markdown("## 📅 Scheduled Tasks")
    for i in range(1, 5):
        relay_key = f"Relay {i}"
        st.write(f"**{relay_states[relay_key]['name']}**")
        st.write("Scheduled ON:", st.session_state.get(relay_key + "_sched_on"))
        st.write("Scheduled OFF:", st.session_state.get(relay_key + "_sched_off"))
        st.markdown("---")

elif page == "Statistics":
    st.markdown("## 📊 Relay Usage Statistics")
    for i in range(1, 5):
        relay_key = f"Relay {i}"
        relay = relay_states[relay_key]
        st.write(f"**{relay['name']}**")
        st.write("Last ON:", relay.get("last_on"))
        st.write("Last OFF:", relay.get("last_off"))
        st.write("Total ON time today (sec):", relay.get("total_on_time", 0))
        st.markdown("---")
