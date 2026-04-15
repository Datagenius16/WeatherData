import streamlit as st
import pandas as pd
import requests
from datetime import datetime

# PAGE CONFIG - This makes it look like an app on your iPhone
st.set_page_config(page_title="Terminal", layout="centered")

st.markdown("<h2 style='text-align: center; color: #FF4B4B;'>🦅 WEATHER COMMAND</h2>", unsafe_content_usage=True)

# 1. THE TOGGLE: Only show what you're trading (Alphabetized)
all_airports = [
    "ATL", "AUS", "BNA", "BOS", "CLT", "DCA", "DTW", "HOU", "JAX", 
    "LAX", "LGA", "MDW", "MIA", "MSP", "OKC", "PHX", "SAT", "SEA", "SFO"
]

active_cities = st.multiselect("Active Battlegrounds", all_airports, default=["LGA", "MDW"])

# 2. THE DATA ENGINE (Free Prototype Version)
def get_weather(station):
    # This pulls from the free Iowa Mesonet (IEM) ASOS feed
    url = f"https://mesonet.agron.iastate.edu/api/1/last_asos.json?station={station}"
    try:
        data = requests.get(url).json()['data'][0]
        return {
            "temp": data['tmpf'],
            "time": data['local_valid'],
            "trend": "N/A" # We will build the 5-min trend next
        }
    except:
        return {"temp": "ERROR", "time": "N/A"}

# 3. THE DISPLAY
for city in active_cities:
    data = get_weather(city)
    with st.container():
        col1, col2 = st.columns([1, 1])
        with col1:
            st.metric(label=f"📍 {city}", value=f"{data['temp']}°F")
        with col2:
            st.caption(f"Last Update: {data['time']}")
        st.divider()

st.caption("V0.1 Stealth Prototype - Raw ASOS Feed")
