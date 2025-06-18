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
pir_ref = db.reference("pir")
pir_settings_ref = db.reference("pir_settings")

def load_states():
    data = ref.get()
    if not data:
        return {}
    return data

def load_pir():
    data = pir_ref.get()
    if not data:
        return {}
    return data

def save_state(relay_key, data):
    ref.child(relay_key).set(data)

# Real-time refresh
st.experimental_rerun_interval = 2000  # every 2 seconds

# Load initial states
relay_states = load_states()
pir_states = load_pir()
current_time = datetime.datetime.now(IST)

def format_time(timestamp):
    if not timestamp:
        return "-"
    dt = datetime.datetime.fromisoformat(timestamp).astimezone(IST)
    return dt.strftime("%H:%M:%S")

def update_relay_state(relay_key):
    relay = relay_states[relay_key]
    now = datetime.datetime.now(IST)

    # Auto ON/OFF Logic
    auto_on = st.session_state.get(relay_key + "_auto_on", 0)
    auto_off = st.session_state.get(relay_key + "_auto_off", 0)

    if auto_on > 0 and relay["last_off"] and not st.session_state.get(relay_key + "_manual_override", False):
        off_time = datetime.datetime.fromisoformat(relay["last_off"])
        if (now - off_time).total_seconds() >= auto_on and not relay["status"]:
            relay["status"] = True
            relay["last_on"] = now.isoformat()

    if auto_off > 0 and relay["last_on"] and not st.session_state.get(relay_key + "_manual_override", False):
        on_time = datetime.datetime.fromisoformat(relay["last_on"])
        if (now - on_time).total_seconds() >= auto_off and relay["status"]:
            relay["status"] = False
            relay["last_off"] = now.isoformat()
            relay["total_on_time"] += int((now - on_time).total_seconds())

    # Scheduler Logic
    sched_on = st.session_state.get(relay_key + "_sched_on")
    sched_off = st.session_state.get(relay_key + "_sched_off")

    if sched_on and now.time().hour == sched_on.hour and now.time().minute == sched_on.minute and not relay["status"]:
        relay["status"] = True
        relay["last_on"] = now.isoformat()

    if sched_off and now.time().hour == sched_off.hour and now.time().minute == sched_off.minute and relay["status"]:
        relay["status"] = False
        relay["last_off"] = now.isoformat()
        relay["total_on_time"] += int((now - datetime.datetime.fromisoformat(relay["last_on"])).total_seconds())

    save_state(relay_key, relay)

# Ensure all relays exist
for i in range(1, 5):
    relay_key = f"relay{i}"
    if relay_key not in relay_states:
        relay_states[relay_key] = {
            "status": False,
            "last_on": None,
            "last_off": None,
            "total_on_time": 0,
            "name": f"Relay {i}",
            "pir_enabled": False,
            "manual_override": False
        }
    update_relay_state(relay_key)

st.set_page_config(layout="wide", page_title="Smart Home Dashboard", page_icon="🏠")
st.markdown("## 🏠 Smart Home Dashboard")

# Page selector
page = st.sidebar.selectbox("Choose page", ["Main Dashboard", "Schedule", "Statistics", "PIR Status", "PIR Settings"])

def relay_ui(index):
    relay_key = f"relay{index}"
    relay = relay_states[relay_key]

    col1, col2 = st.columns([3, 1])
    with col1:
        relay["name"] = st.text_input(f"Name for Relay {index}", relay["name"], key=relay_key + "_name")
    with col2:
        toggle = st.toggle("", value=relay["status"], key=relay_key + "_toggle")
        now = datetime.datetime.now(IST)
        if toggle != relay["status"]:
            relay["status"] = toggle
            st.session_state[relay_key + "_manual_override"] = True
            relay["manual_override"] = True
            if toggle:
                relay["last_on"] = now.isoformat()
            else:
                relay["last_off"] = now.isoformat()
                if relay["last_on"]:
                    last_on_dt = datetime.datetime.fromisoformat(relay["last_on"])
                    relay["total_on_time"] += int((now - last_on_dt).total_seconds())
            save_state(relay_key, relay)

    with st.expander(f"⚙️ Options for Relay {index}"):
        st.write("**Last ON:**", format_time(relay.get("last_on")))
        st.write("**Last OFF:**", format_time(relay.get("last_off")))
        st.write("**Today's ON Time:**", str(datetime.timedelta(seconds=relay.get("total_on_time", 0))))

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

        st.checkbox("Enable PIR Control", value=relay.get("pir_enabled", False), key=relay_key + "_pir_enabled")
        st.checkbox("Manual Override (disable PIR)", value=relay.get("manual_override", False), key=relay_key + "_manual_override")

if page == "Main Dashboard":
    for row in range(2):
        cols = st.columns(2)
        for col in range(2):
            with cols[col]:
                relay_ui(row * 2 + col + 1)

elif page == "Schedule":
    st.markdown("## 📅 Scheduled Tasks")
    for i in range(1, 5):
        relay_key = f"relay{i}"
        st.write(f"**{relay_states[relay_key]['name']}**")
        st.write("Scheduled ON:", st.session_state.get(relay_key + "_sched_on"))
        st.write("Scheduled OFF:", st.session_state.get(relay_key + "_sched_off"))
        st.markdown("---")

elif page == "Statistics":
    st.markdown("## 📊 Relay Usage Statistics")
    for i in range(1, 5):
        relay_key = f"relay{i}"
        relay = relay_states[relay_key]
        st.write(f"**{relay['name']}**")
        st.write("Last ON:", format_time(relay.get("last_on")))
        st.write("Last OFF:", format_time(relay.get("last_off")))
        st.write("Total ON time today:", str(datetime.timedelta(seconds=relay.get("total_on_time", 0))))
        st.markdown("---")

elif page == "PIR Status":
    st.markdown("## 🚨 PIR Sensor Status")
    if not pir_states:
        st.info("No PIR data available.")
    else:
        for pir_key, status in pir_states.items():
            st.write(f"**{pir_key.upper()}**: {'🚶 Motion Detected' if status else '🛑 No Motion'}")

elif page == "PIR Settings":
    st.markdown("## 🕵️ PIR Sensor Settings")

    pir_data = pir_settings_ref.get() or {
        "enabled": False,
        "manual_override": False,
        "relays": []
    }

    enabled = st.checkbox("Enable PIR Motion Detection", value=pir_data.get("enabled", False))
    manual_override = st.checkbox("Manual Override (Disable PIR Response)", value=pir_data.get("manual_override", False))

    relay_choices = ["relay1", "relay2", "relay3", "relay4"]
    selected_relays = st.multiselect(
        "Select Relays to be Controlled by PIR",
        options=relay_choices,
        default=pir_data.get("relays", [])
    )

    if st.button("💾 Save PIR Settings"):
        pir_settings_ref.set({
            "enabled": enabled,
            "manual_override": manual_override,
            "relays": selected_relays
        })
        st.success("PIR settings updated!")
