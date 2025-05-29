import streamlit as st
import requests
from datetime import datetime

# 🔒 Struggles that trigger the night reminder
night_struggles = ["masturbation", "porn", "overeating", "over eating", "lust", "late night", "overthinking"]

def get_motivation(tone, status):
    messages = {
        "coach": {
            "success": "Proud of you. Stack that win.",
            "struggled": "You showed up even when it wasn’t clean. That’s grit.",
            "fail": "We don’t fold. Tomorrow’s a bounce-back rep."
        },
        "faith": {
            "success": "Keep pressing on. God honors effort.",
            "struggled": "You are not alone in the fight. His strength is made perfect in weakness.",
            "fail": "Grace covers failure — but get back in the ring."
        },
        "chill": {
            "success": "Look at you go 🙌 Keep that energy.",
            "struggled": "Meh day? No worries. Just don’t stack Ls.",
            "fail": "Okay, it’s done. Shake it off and try again tomorrow."
        },
        "logic": {
            "success": "Positive reinforcement loop activated. Keep executing.",
            "struggled": "You met resistance and didn’t fully fold. That’s data.",
            "fail": "Record noted. Adjust inputs tomorrow."
        },
    }

    prompts = {
        "success": "What worked well today that you should repeat?",
        "struggled": "What slowed you down today that you *can* control?",
        "fail": "What was your trigger — and what’s your plan next time?"
    }

    return messages[tone][status], prompts[status]

API_URL = "http://localhost:8000"

st.set_page_config(page_title="Accountability Buddy", layout="centered")
st.title("🧠 Accountability Buddy App")

# --- User Registration ---
st.header("1. Create or Login")
username = st.text_input("Enter your username")
tone = st.selectbox("Choose your motivation style", ["coach", "faith", "chill", "logic"])

if st.button("Register / Login"):
    if username:
        res = requests.post(f"{API_URL}/register", json={"username": username, "tone": tone})
        if res.status_code == 200:
            st.success("User registered or logged in.")
        else:
            st.warning(res.json().get("detail", "Error during registration."))
    else:
        st.error("Please enter a username.")

# --- Add Struggles ---
st.header("2. Select Your Struggles")
struggle_input = st.text_input("What are you struggling with today?")

if st.button("Add Struggle"):
    if username and struggle_input:
        res = requests.post(f"{API_URL}/add_struggle", json={"username": username, "struggle": struggle_input})
        if res.status_code == 200:
            st.success("Struggle added.")
        else:
            st.error("Failed to add struggle.")
    else:
        st.warning("Enter both username and struggle.")

# --- Daily Logger ---
st.header("3. Daily Progress Logger")

trigger_night_warning = False  # Flag for night sin reminder

if username:
    response = requests.get(f"{API_URL}/get_struggles?username={username}")
    if response.status_code == 200:
        struggles = response.json().get("struggles", {})
        if struggles:
            selected = st.selectbox("Select a struggle to log", list(struggles.keys()))
            status = st.radio("Today's status", ["success", "struggled", "fail"])
            comment = st.text_input("Optional comment")

            # Check if any struggle is a night-related one
            for s in struggles.keys():
                if any(night_word in s.lower() for night_word in night_struggles):
                    trigger_night_warning = True
                    break

            if st.button("Log Day"):
                struggle_id = struggles[selected]
                payload = {
                    "struggle_id": struggle_id,
                    "status": status,
                    "comment": comment
                }
                res = requests.post(f"{API_URL}/log", json=payload)
                if res.status_code == 200:
                    st.success("✅ Log saved.")
                    msg, prompt = get_motivation(tone, status)
                    st.success(f"💬 {msg}")
                    st.info(f"🧠 Reflection Prompt: {prompt}")
                else:
                    st.error("❌ Failed to log.")

# --- Show 10PM Reminder if a night struggle is active
if trigger_night_warning:
    now = datetime.now()
    if now.hour == 22 and 0 <= now.minute <= 5:
        st.error("🕙 That sin lives at night. Reflect and fight back.")

# --- Streak Display ---
        if struggles:
            st.header("📈 Streak Tracker")
            struggle_id = list(struggles.values())[0]
            res = requests.get(f"{API_URL}/streak/{struggle_id}")
            if res.status_code == 200:
                streak_info = res.json()
                st.metric("Current Streak", f"{streak_info['current_streak']} days")
                st.metric("Logs Total", streak_info["log_count"])
            else:
                st.warning("Could not fetch streak data.")
