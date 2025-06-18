import streamlit as st
import datetime
import pytz
import firebase_admin
from firebase_admin import credentials, db

# Firebase setup
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

IST = pytz.timezone('Asia/Kolkata')
ref = db.reference("relays")

def load_states():
    return ref.get() or {}

def save_state(relay_key, data):
    ref.child(relay_key).set(data)

relay_states = load_states()
now = datetime.datetime.now(IST)

def format_time(timestamp):
    if not timestamp:
        return "-"
    return datetime.datetime.fromisoformat(timestamp).astimezone(IST).strftime("%H:%M:%S")

st.set_page_config(layout="wide", page_title="Smart Home Dashboard")
st.title("💡 Smart Relay Control")

def update_relay(relay_key):
    relay = relay_states[relay_key]
    now = datetime.datetime.now(IST)

    auto_on = st.session_state.get(relay_key + "_auto_on", 0)
    auto_off = st.session_state.get(relay_key + "_auto_off", 0)
    sched_on = st.session_state.get(relay_key + "_sched_on")
    sched_off = st.session_state.get(relay_key + "_sched_off")

    if auto_on > 0 and relay["last_off"] and not relay["status"]:
        if (now - datetime.datetime.fromisoformat(relay["last_off"])).total_seconds() >= auto_on:
            relay["status"] = True
            relay["last_on"] = now.isoformat()

    if auto_off > 0 and relay["last_on"] and relay["status"]:
        if (now - datetime.datetime.fromisoformat(relay["last_on"])).total_seconds() >= auto_off:
            relay["status"] = False
            relay["last_off"] = now.isoformat()
            relay["total_on_time"] += int((now - datetime.datetime.fromisoformat(relay["last_on"])).total_seconds())

    if sched_on and now.time().hour == sched_on.hour and now.time().minute == sched_on.minute and not relay["status"]:
        relay["status"] = True
        relay["last_on"] = now.isoformat()

    if sched_off and now.time().hour == sched_off.hour and now.time().minute == sched_off.minute and relay["status"]:
        relay["status"] = False
        relay["last_off"] = now.isoformat()
        relay["total_on_time"] += int((now - datetime.datetime.fromisoformat(relay["last_on"])).total_seconds())

    save_state(relay_key, relay)

for i in range(1, 5):
    relay_key = f"relay{i}"
    if relay_key not in relay_states:
        relay_states[relay_key] = {
            "status": False,
            "last_on": None,
            "last_off": None,
            "total_on_time": 0,
            "name": f"Relay {i}"
        }
    update_relay(relay_key)

    bg_color = "green" if relay_states[relay_key]["status"] else "red"
    st.markdown(f"""
    <div style='background-color:{bg_color};padding:1rem;border-radius:10px;margin-bottom:1rem'>
        <h3 style='color:white;'>{relay_states[relay_key]['name']}</h3>
        <form action="#">
            <input type="checkbox" id="{relay_key}_toggle" {'checked' if relay_states[relay_key]['status'] else ''} onchange="window.location.reload()">
            <label for="{relay_key}_toggle" style='color:white;font-size:1.2rem'> Toggle </label>
        </form>
        <p style='color:white;'>Last ON: {format_time(relay_states[relay_key]['last_on'])}</p>
        <p style='color:white;'>Last OFF: {format_time(relay_states[relay_key]['last_off'])}</p>
        <p style='color:white;'>Total ON Time: {str(datetime.timedelta(seconds=relay_states[relay_key]['total_on_time']))}</p>
    </div>
    """, unsafe_allow_html=True)

    toggle = st.toggle("", key=relay_key + "_toggle", value=relay_states[relay_key]["status"])
    if toggle != relay_states[relay_key]["status"]:
        relay_states[relay_key]["status"] = toggle
        if toggle:
            relay_states[relay_key]["last_on"] = now.isoformat()
        else:
            relay_states[relay_key]["last_off"] = now.isoformat()
        save_state(relay_key, relay_states[relay_key])

    with st.expander("⚙️ Options"):
        st.number_input("Auto ON (s)", min_value=0, key=relay_key + "_auto_on")
        st.number_input("Auto OFF (s)", min_value=0, key=relay_key + "_auto_off")
        st.time_input("Schedule ON", value=datetime.time(0, 0), key=relay_key + "_sched_on")
        st.time_input("Schedule OFF", value=datetime.time(0, 0), key=relay_key + "_sched_off")
        st.text_input("Rename", value=relay_states[relay_key]['name'], key=relay_key + "_name")
