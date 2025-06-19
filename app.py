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

# Utility Functions
def load_states():
    return ref.get() or {}

def save_state(relay_key, data):
    ref.child(relay_key).set(data)

def format_time(timestamp):
    if not timestamp:
        return "-"
    try:
        return datetime.datetime.fromisoformat(timestamp).astimezone(IST).strftime("%H:%M:%S")
    except:
        return "Invalid"

# Streamlit UI Setup
st.set_page_config(layout="wide", page_title="Smart Home Dashboard")
st.title("\U0001F4A1 Smart Relay Control")

st.markdown("""
<style>
.relay-box {
    padding: 1rem;
    border-radius: 10px;
    margin: 0.5rem;
    color: white;
    flex: 1;
    min-width: 45%;
}
.row-container {
    display: flex;
    justify-content: space-between;
    flex-wrap: wrap;
}
</style>
""", unsafe_allow_html=True)

relay_states = load_states()
now = datetime.datetime.now(IST)

# Main Grid UI
st.markdown("<div class='row-container'>", unsafe_allow_html=True)
for i in range(1, 5):
    relay_key = f"relay{i}"

    if relay_key not in relay_states:
        relay_states[relay_key] = {}

    relay = relay_states[relay_key]
    relay.setdefault("status", False)
    relay.setdefault("last_on", None)
    relay.setdefault("last_off", None)
    relay.setdefault("total_on_time", 0)
    relay.setdefault("name", f"Relay {i}")

    now = datetime.datetime.now(IST)

    name_key = relay_key + "_name"
    toggle_key = relay_key + "_toggle"
    auto_on_key = relay_key + "_auto_on"
    auto_off_key = relay_key + "_auto_off"
    sched_on_key = relay_key + "_sched_on"
    sched_off_key = relay_key + "_sched_off"

    # Init session_state defaults
    if name_key not in st.session_state:
        st.session_state[name_key] = relay["name"]
    if toggle_key not in st.session_state:
        st.session_state[toggle_key] = relay["status"]
    if auto_on_key not in st.session_state:
        st.session_state[auto_on_key] = 0
    if auto_off_key not in st.session_state:
        st.session_state[auto_off_key] = 0
    if sched_on_key not in st.session_state:
        st.session_state[sched_on_key] = datetime.time(0, 0)
    if sched_off_key not in st.session_state:
        st.session_state[sched_off_key] = datetime.time(0, 0)

    auto_on = st.session_state[auto_on_key]
    auto_off = st.session_state[auto_off_key]
    sched_on = st.session_state[sched_on_key]
    sched_off = st.session_state[sched_off_key]

    # Auto ON/OFF logic
    if auto_on > 0 and relay["last_off"] and not relay["status"]:
        if (now - datetime.datetime.fromisoformat(relay["last_off"])).total_seconds() >= auto_on:
            relay["status"] = True
            relay["last_on"] = now.isoformat()

    if auto_off > 0 and relay["last_on"] and relay["status"]:
        if (now - datetime.datetime.fromisoformat(relay["last_on"])).total_seconds() >= auto_off:
            relay["status"] = False
            relay["last_off"] = now.isoformat()
            relay["total_on_time"] += int((now - datetime.datetime.fromisoformat(relay["last_on"])).total_seconds())

    # Schedule ON/OFF
    if sched_on and now.time().hour == sched_on.hour and now.time().minute == sched_on.minute and not relay["status"]:
        relay["status"] = True
        relay["last_on"] = now.isoformat()

    if sched_off and now.time().hour == sched_off.hour and now.time().minute == sched_off.minute and relay["status"]:
        relay["status"] = False
        relay["last_off"] = now.isoformat()
        relay["total_on_time"] += int((now - datetime.datetime.fromisoformat(relay["last_on"])).total_seconds())

    save_state(relay_key, relay)

    # Visual Tile
    bg_color = "green" if relay["status"] else "red"
    st.markdown(f"""
    <div class='relay-box' style='background-color:{bg_color};'>
        <h3>{st.session_state[name_key]}</h3>
        <p>Last ON: {format_time(relay.get('last_on'))}</p>
        <p>Last OFF: {format_time(relay.get('last_off'))}</p>
        <p>Total ON Time: {str(datetime.timedelta(seconds=relay['total_on_time']))}</p>
    </div>
    """, unsafe_allow_html=True)

    toggle = st.toggle("Toggle", key=toggle_key, value=relay["status"])
    if toggle != relay["status"]:
        relay["status"] = toggle
        if toggle:
            relay["last_on"] = now.isoformat()
        else:
            relay["last_off"] = now.isoformat()
        save_state(relay_key, relay)

    with st.expander("⚙️ Options", expanded=False):
        new_name = st.text_input("Rename", value=st.session_state[name_key], key=name_key)
        if new_name != relay["name"]:
            relay["name"] = new_name
            save_state(relay_key, relay)
        st.session_state[auto_on_key] = st.number_input("Auto ON (s)", min_value=0, key=auto_on_key)
        st.session_state[auto_off_key] = st.number_input("Auto OFF (s)", min_value=0, key=auto_off_key)
        st.session_state[sched_on_key] = st.time_input("Schedule ON", value=st.session_state[sched_on_key], key=sched_on_key)
        st.session_state[sched_off_key] = st.time_input("Schedule OFF", value=st.session_state[sched_off_key], key=sched_off_key)

st.markdown("</div>", unsafe_allow_html=True)
