import streamlit as st
import datetime
from datetime import timedelta

st.set_page_config(page_title="Smart Home Dashboard", layout="wide")
st.title("🏡 My Smart Home")

# Placeholder for Firebase status (normally fetched from DB)
if "devices" not in st.session_state:
    st.session_state.devices = {
        "relay1": {"name": "Frame TV", "status": False, "last_on": None, "last_off": None, "on_duration": timedelta()},
        "relay2": {"name": "Bulb", "status": False, "last_on": None, "last_off": None, "on_duration": timedelta()},
        "relay3": {"name": "Speaker", "status": False, "last_on": None, "last_off": None, "on_duration": timedelta()},
        "relay4": {"name": "Air Conditioner", "status": False, "last_on": None, "last_off": None, "on_duration": timedelta()}
    }

st.markdown("### Living Room")

cols = st.columns(4)
now = datetime.datetime.now()

for i, (key, device) in enumerate(st.session_state.devices.items()):
    with cols[i]:
        new_name = st.text_input(f"Rename {key}", value=device["name"], key=f"name_{key}")
        st.session_state.devices[key]["name"] = new_name

        is_on = st.toggle("On/Off", value=device["status"], key=f"toggle_{key}")
        if is_on != device["status"]:
            st.session_state.devices[key]["status"] = is_on
            if is_on:
                st.session_state.devices[key]["last_on"] = now
            else:
                st.session_state.devices[key]["last_off"] = now
                if device["last_on"]:
                    delta = now - device["last_on"]
                    st.session_state.devices[key]["on_duration"] += delta

        st.write(f"**Status:** {'🟢 On' if device['status'] else '🔴 Off'}")
        st.write(f"**Last On:** {device['last_on'].strftime('%H:%M:%S') if device['last_on'] else 'N/A'}")
        st.write(f"**Last Off:** {device['last_off'].strftime('%H:%M:%S') if device['last_off'] else 'N/A'}")
        st.write(f"**Today On Duration:** {device['on_duration']}")

st.markdown("---")
st.header("🕒 Timer & Scheduling")

with st.expander("⏲ Set Auto ON/OFF Timer"):
    selected_device = st.selectbox("Select Device", list(st.session_state.devices.keys()))
    timer_action = st.radio("Action", ["Turn ON after", "Turn OFF after"])
    timer_duration = st.slider("Timer Duration (minutes)", 1, 120, 5)
    if st.button("Set Timer"):
        st.success(f"Timer to {timer_action.split()[1]} {st.session_state.devices[selected_device]['name']} in {timer_duration} minutes set.")
        # You can use threading/timers or schedule this in Firebase for real effect

with st.expander("🗓 Schedule ON/OFF"):
    schedule_device = st.selectbox("Device to Schedule", list(st.session_state.devices.keys()), key="schedule_device")
    schedule_time = st.time_input("Schedule Time")
    schedule_action = st.radio("Action", ["Turn ON", "Turn OFF"], key="schedule_action")
    if st.button("Add to Schedule"):
        st.success(f"Scheduled {schedule_action} for {st.session_state.devices[schedule_device]['name']} at {schedule_time}.")
        # You can write this to Firebase as a schedule node

with st.expander("📊 Device Stats"):
    for key, device in st.session_state.devices.items():
        st.markdown(f"**{device['name']}**")
        st.write(f"- Last ON: {device['last_on']}")
        st.write(f"- Last OFF: {device['last_off']}")
        st.write(f"- Total ON Today: {device['on_duration']}")
        st.write("---")
