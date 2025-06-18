import streamlit as st
import datetime
import pytz

# Set timezone
IST = pytz.timezone('Asia/Kolkata')

# Relay State (simulated, replace with Firebase logic later)
relay_states = {
    "Relay 1": {"status": False, "last_on": None, "last_off": None, "total_on_time": datetime.timedelta()},
    "Relay 2": {"status": False, "last_on": None, "last_off": None, "total_on_time": datetime.timedelta()},
    "Relay 3": {"status": False, "last_on": None, "last_off": None, "total_on_time": datetime.timedelta()},
    "Relay 4": {"status": False, "last_on": None, "last_off": None, "total_on_time": datetime.timedelta()}
}

def relay_toggle_ui(relay_name):
    state = relay_states[relay_name]["status"]
    color = "green" if state else "red"
    icon = "🔛" if state else "🔴"

    col1, col2 = st.columns([3, 1])
    with col1:
        new_name = st.text_input(f"Name for {relay_name}", relay_name, key=relay_name + "_name")
    with col2:
        if st.button(icon, key=relay_name + "_toggle"):
            relay_states[relay_name]["status"] = not state
            now = datetime.datetime.now(IST)
            if relay_states[relay_name]["status"]:
                relay_states[relay_name]["last_on"] = now
            else:
                relay_states[relay_name]["last_off"] = now
                if relay_states[relay_name]["last_on"]:
                    relay_states[relay_name]["total_on_time"] += now - relay_states[relay_name]["last_on"]

    with st.expander(f"⚙️ Options for {relay_name}"):
        st.write("**Last ON:**", relay_states[relay_name]["last_on"])
        st.write("**Last OFF:**", relay_states[relay_name]["last_off"])
        st.write("**Today's ON Time:**", str(relay_states[relay_name]["total_on_time"]))

        timer_col1, timer_col2 = st.columns(2)
        with timer_col1:
            on_timer = st.number_input("Auto ON after (seconds)", min_value=0, key=relay_name + "_on_timer")
        with timer_col2:
            off_timer = st.number_input("Auto OFF after (seconds)", min_value=0, key=relay_name + "_off_timer")

        sched_col1, sched_col2 = st.columns(2)
        with sched_col1:
            sched_on = st.time_input("Schedule ON", value=datetime.time(0, 0), key=relay_name + "_sched_on")
        with sched_col2:
            sched_off = st.time_input("Schedule OFF", value=datetime.time(0, 0), key=relay_name + "_sched_off")

        st.success("Timers & schedules saved (simulation)")

st.set_page_config(layout="wide")
st.markdown("## 🏠 Smart Home Dashboard")

col1, col2 = st.columns(2)
with col1:
    relay_toggle_ui("Relay 1")
    relay_toggle_ui("Relay 3")

with col2:
    relay_toggle_ui("Relay 2")
    relay_toggle_ui("Relay 4")
