# STREAMLIT UI - SMART ROOM DASHBOARD (Fully Synced with ESP8266 Firebase Logic)

import streamlit as st
import datetime
import pytz
import firebase_admin
from firebase_admin import credentials, db

# Firebase Credentials (from Streamlit secrets)
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

# Firebase Refs
relay_ref = db.reference("relays")
pir_settings_ref = db.reference("pir_settings")

IST = pytz.timezone('Asia/Kolkata')

# UI Config
st.set_page_config(layout="wide", page_title="Room Automation Dashboard")
st.title("🏠 Room Automation Dashboard")

st.markdown("""
<style>
.relay-box {
    padding: 1rem;
    border-radius: 15px;
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

# Load relay state
relays = relay_ref.get() or {}
now = datetime.datetime.now(IST)

# Ensure all 4 relays exist
for i in range(1, 5):
    key = f"relay{i}"
    if key not in relays:
        relays[key] = {
            "status": False,
            "name": f"Relay {i}",
            "last_on": None,
            "last_off": None,
            "total_on_time": 0
        }

# Load PIR Settings
pir_config = pir_settings_ref.get() or {"enabled": False, "relays": []}

# Render relays
st.markdown("<div class='row-container'>", unsafe_allow_html=True)
for i in range(1, 5):
    key = f"relay{i}"
    relay = relays[key]
    bg = "green" if relay["status"] else "red"
    
    # Display box
    st.markdown(f"""
    <div class='relay-box' style='background-color:{bg};'>
        <h3>{relay['name']}</h3>
        <p>Last ON: {relay['last_on'] or '-'}<br>
           Last OFF: {relay['last_off'] or '-'}<br>
           Total ON Today: {str(datetime.timedelta(seconds=relay['total_on_time']))}</p>
    </div>
    """, unsafe_allow_html=True)

    # Toggle control
    toggle = st.toggle("Toggle", key=key, value=relay["status"])
    if toggle != relay["status"]:
        now_iso = now.isoformat()
        relay["status"] = toggle
        if toggle:
            relay["last_on"] = now_iso
        else:
            relay["last_off"] = now_iso
            if relay["last_on"]:
                on_dt = datetime.datetime.fromisoformat(relay["last_on"])
                relay["total_on_time"] += int((now - on_dt).total_seconds())
        relay_ref.child(key).set(relay)

    # Options
    with st.expander("⚙️ Options"):
        new_name = st.text_input("Name", value=relay["name"], key=f"name_{key}")
        relay["name"] = new_name
        relay_ref.child(key).update({"name": new_name})

st.markdown("</div>", unsafe_allow_html=True)

# PIR settings
st.markdown("---")
st.header("🕵️ PIR Sensor Settings")

pir_enabled = st.checkbox("Enable PIR Mode", value=pir_config.get("enabled", False))
pir_selection = st.multiselect("Select relays to control via PIR", [f"relay{i}" for i in range(1, 5)], default=pir_config.get("relays", []))

if st.button("💾 Save PIR Settings"):
    pir_settings_ref.set({"enabled": pir_enabled, "relays": pir_selection})
    st.success("Settings saved!")
