import streamlit as st
import datetime
import pytz
import firebase_admin
from firebase_admin import credentials, db

# Initialize Firebase
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
        "client_x509_cert_url": st.secrets["client_x509_cert_url"]
    })
    firebase_admin.initialize_app(cred, {
        'databaseURL': st.secrets["database_url"]
    })

# Firebase reference
ref = db.reference("relays")
pir_ref = db.reference("pir_target")
IST = pytz.timezone('Asia/Kolkata')

# Helpers
def format_time(ts):
    if not ts:
        return "-"
    try:
        return datetime.datetime.fromisoformat(ts).astimezone(IST).strftime("%H:%M:%S")
    except:
        return "Invalid"

def get_relay_data():
    return ref.get() or {}

def save_relay(relay_id, data):
    ref.child(relay_id).set(data)

# Load states
relays = get_relay_data()
now = datetime.datetime.now(IST)

# Layout
st.set_page_config(layout="wide", page_title="Smart Home Dashboard")
st.title("💡 Smart Room Automation")

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
.row {
    display: flex;
    justify-content: space-between;
    flex-wrap: wrap;
}
</style>
""", unsafe_allow_html=True)

# Select PIR target
default_pir = pir_ref.get() or "relay1"
selected_pir = st.selectbox("👀 PIR Controls Which Relay?", [f"relay{i}" for i in range(1, 5)], index=int(default_pir[-1]) - 1)
pir_ref.set(selected_pir)

# UI Grid
st.markdown("<div class='row'>", unsafe_allow_html=True)
for i in range(1, 5):
    relay_id = f"relay{i}"
    if relay_id not in relays:
        relays[relay_id] = {
            "status": False,
            "last_on": None,
            "last_off": None,
            "total_on_time": 0,
            "name": f"Relay {i}"
        }

    relay = relays[relay_id]

    # UI controls
    st.session_state.setdefault(f"{relay_id}_name", relay["name"])
    st.session_state.setdefault(f"{relay_id}_toggle", relay["status"])

    # Calculate ON time
    if relay["status"] and relay["last_on"]:
        duration = (now - datetime.datetime.fromisoformat(relay["last_on"])).total_seconds()
    else:
        duration = 0

    bg = "green" if relay["status"] else "red"
    st.markdown(f"""
    <div class='relay-box' style='background-color:{bg};'>
        <h3>{st.session_state[f"{relay_id}_name"]}</h3>
        <p>Last ON: {format_time(relay['last_on'])}</p>
        <p>Last OFF: {format_time(relay['last_off'])}</p>
        <p>Total ON Time: {str(datetime.timedelta(seconds=relay['total_on_time'] + int(duration)))}</p>
    </div>
    """, unsafe_allow_html=True)

    toggle = st.toggle("Toggle", key=f"{relay_id}_toggle", value=relay["status"])
    if toggle != relay["status"]:
        relay["status"] = toggle
        timestamp = now.isoformat()
        if toggle:
            relay["last_on"] = timestamp
        else:
            relay["last_off"] = timestamp
            if relay["last_on"]:
                relay["total_on_time"] += int((now - datetime.datetime.fromisoformat(relay["last_on"])).total_seconds())
        save_relay(relay_id, relay)

    with st.expander("⚙️ Options"):
        new_name = st.text_input("Rename", value=st.session_state[f"{relay_id}_name"], key=f"{relay_id}_name_input")
        st.session_state[f"{relay_id}_name"] = new_name
        relay["name"] = new_name
        save_relay(relay_id, relay)

st.markdown("</div>", unsafe_allow_html=True)
