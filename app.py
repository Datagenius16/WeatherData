import streamlit as st
import pandas as pd
import requests

# PAGE CONFIG
st.set_page_config(page_title="Terminal V0.4.1", layout="centered")

st.markdown("<h2 style='text-align: center; color: #FF4B4B;'>🦅 WEATHER COMMAND</h2>", unsafe_allow_html=True)

# 1. SETUP
all_airports = ["ATL", "AUS", "BNA", "BOS", "CLT", "DCA", "DTW", "HOU", "JAX", "LAX", "LGA", "MDW", "MIA", "MSP", "OKC", "PHX", "SAT", "SEA", "SFO"]
active_cities = st.multiselect("Active Battlegrounds", all_airports, default=["LGA", "MDW"])

# 2. LOAD SECURE KEY
try:
    API_KEY = st.secrets["CLIMATESIGHT_API_KEY"]
except:
    st.error("🔑 API Key missing in Streamlit Secrets!")
    st.stop()

# 3. THE HF ENGINE (ClimateSight 2026 Protocol)
def get_climatesight_data(station):
    # ClimateSight v2 requires lowercase IDs (e.g., klga)
    station_id = f"k{station.lower()}"
    url = f"https://www.climatesight.app/api/stations/{station_id}"
    headers = {"Authorization": f"Bearer {API_KEY}"}
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            # We grab the 'observations' list which contains OMO/HFM/ASOS
            return response.json().get('observations', [])
        else:
            return []
    except:
        return []

# 4. THE DISPLAY
for city in active_cities:
    obs = get_climatesight_data(city)
    
    with st.container():
        if obs and len(obs) > 0:
            latest = obs[0]
            # ClimateSight reports in Celsius; we convert to Fahrenheit
            temp_f = round((latest['temp'] * 9/5) + 32, 1)
            
            # BIG METRIC (Top of card)
            col1, col2 = st.columns([1, 1])
            with col1:
                st.metric(label=f"📍 {city} ({latest.get('type', 'OMO')})", value=f"{temp_f}°F")
            with col2:
                # Extracts HH:MM from the timestamp
                time_display = latest['observed_at'][11:16] if 'observed_at' in latest else "N/A"
                st.caption(f"Last Hit: {time_display} UTC")
                st.caption(f"Status: Live Runway Feed")

            # THE TAPE (The scrolling 1-minute data)
            with st.expander("View 1-Min Tape (OMO/HFM/ASOS)"):
                tape_list = []
                for o in obs[:12]: # Show the last 12 hits (approx 12 mins of data)
                    f_val = round((o['temp'] * 9/5) + 32, 1)
                    tape_list.append({
                        "Time (UTC)": o.get('observed_at', 'N/A')[11:16],
                        "Type": o.get('type', 'OMO'),
                        "Temp": f"{f_val}°F"
                    })
                st.table(pd.DataFrame(tape_list))
        else:
            st.warning(f"Connecting to {city} HFM/OMO stream... (Check API key or station ID)")
        st.divider()

st.caption("V0.4.1 - Institutional Datalink Locked")
