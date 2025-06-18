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
    try:
        return datetime.datetime.fromisoformat(timestamp).astimezone(IST).strftime("%H:%M:%S")
    except:
        return "Invalid timestamp"

st.set_page_config(layout="wide", page_title="Smart Home Dashboard")
st.title("💡 Smart Relay Control")

st.markdown("""
<style>
.relay-box {
    padding: 1rem;
    border-radius: 10px;
    margin: 0.5rem;
    color: white;
    flex: 1;
}
.row-container {
    display: flex;
    justify-content: space-between;
    flex-wrap: wrap;
}
</style>
""", unsafe_allow_html=True)

# Group relays into 2x2 grid
for row in range(2):
    st.markdown("<div class='row-container'>", unsafe_allow_html=True)
    for col in range(2):
        i = row * 2 + col + 1
        relay_key = f"relay{i}"

        if relay_key not in relay_states:
            relay_states[relay_key] = {
                "status": False,
                "last_on": None,
                "last_off": None,
                "total_on_time": 0,
                "name": f"Relay {i}"
            }

        now = datetime.datetime.now(IST)
        relay = relay_states[relay_key]

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

        bg_color = "green" if relay["status"] else "red"

        st.markdown(f"""
        <div class='relay-box' style='background-color:{bg_color};'>
            <h3>{st.session_state.get(relay_key + '_name', relay['name'])}</h3>
            <p>Last ON: {format_time(relay.get('last_on'))}</p>
            <p>Last OFF: {format_time(relay.get('last_off'))}</p>
            <p>Total ON Time: {str(datetime.timedelta(seconds=relay['total_on_time']))}</p>
        </div>
        """, unsafe_allow_html=True)

        toggle = st.toggle("Toggle", key=relay_key + "_toggle", value=relay["status"])
        if toggle != relay["status"]:
            relay["status"] = toggle
            if toggle:
                relay["last_on"] = now.isoformat()
            else:
                relay["last_off"] = now.isoformat()
            save_state(relay_key, relay)

        with st.expander("⚙️ Options", expanded=False):
            st.session_state[relay_key + '_name'] = st.text_input("Rename", value=relay['name'], key=relay_key + "_name")
            st.number_input("Auto ON (s)", min_value=0, key=relay_key + "_auto_on")
            st.number_input("Auto OFF (s)", min_value=0, key=relay_key + "_auto_off")
            st.time_input("Schedule ON", value=datetime.time(0, 0), key=relay_key + "_sched_on")
            st.time_input("Schedule OFF", value=datetime.time(0, 0), key=relay_key + "_sched_off")

    st.markdown("</div>", unsafe_allow_html=True)
