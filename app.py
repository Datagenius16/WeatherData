import streamlit as st
import pandas as pd
import requests
from datetime import datetime

# PAGE CONFIG
st.set_page_config(page_title="Terminal", layout="centered")

st.markdown("<h2 style='text-align: center; color: #FF4B4B;'>🦅 WEATHER COMMAND</h2>", unsafe_allow_html=True)

all_airports = [
    "ATL", "AUS", "BNA", "BOS", "CLT", "DCA", "DTW", "HOU", "JAX", 
    "LAX", "LGA", "MDW", "MIA", "MSP", "OKC", "PHX", "SAT", "SEA", "SFO"
]

active_cities = st.multiselect("Active Battlegrounds", all_airports, default=["LGA", "MDW"])

# 2. THE DATA ENGINE (NWS Live Aviation Feed)
def get_weather(station):
    # NWS requires a 4-letter code (LGA becomes KLGA)
    station_code = f"K{station}" if len(station) == 3 else station
    url = f"https://api.weather.gov/stations/{station_code}/observations/latest"
    headers = {"User-Agent": "RiskDeskTerminal (stealth@command.com)"}
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        
        # Check if the government API is down
        if response.status_code != 200:
            return {"temp": "API LAG", "time": "N/A"}
            
        data = response.json()
        temp_c = data['properties']['temperature']['value']
        
        # Convert Celsius to Fahrenheit
        if temp_c is not None:
            temp_f = round((temp_c * 9/5) + 32, 1)
        else:
            temp_f = "NO DATA"
            
        # Format the timestamp
        raw_time = data['properties']['timestamp']
        time_str = raw_time[11:16] + " UTC" # Just grabs the HH:MM
        
        return {"temp": temp_f, "time": time_str}
        
    except Exception as e:
        return {"temp": "ERROR", "time": str(e)[:20]}

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

st.caption("V0.1 Stealth Prototype - NWS Live Feed")
