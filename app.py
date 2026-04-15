import streamlit as st
import pandas as pd
import requests

st.set_page_config(page_title="Terminal V0.4", layout="centered")

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

# 3. THE HF ENGINE (ClimateSight Observations)
def get_climatesight_data(station):
    # Using the direct observations endpoint for 1-minute data
    url = f"https://api.climatesight.app/v1/stations/K{station.upper()}/observations"
    headers = {"Authorization": f"Bearer {API_KEY}"}
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            return response.json() # Should be a list of observations
        return []
    except:
        return []

# 4. THE DISPLAY
for city in active_cities:
    obs = get_climatesight_data(city)
    
    with st.container():
        if obs and len(obs) > 0:
            latest = obs[0]
            temp_f = round((latest['temp'] * 9/5) + 32, 1)
            
            st.metric(label=f"📍 {city} ({latest.get('type', 'HF')})", value=f"{temp_f}°F")
            st.caption(f"Last Obs: {latest['observed_at'][11:16]} UTC")

            with st.expander("View 1-Min Tape (OMO/HFM)"):
                tape_data = []
                for o in obs[:15]:
                    f_val = round((o['temp'] * 9/5) + 32, 1)
                    tape_data.append({
                        "Time (UTC)": o['observed_at'][11:16],
                        "Type": o.get('type', 'OMO'),
                        "Temp": f"{f_val}°F"
                    })
                st.table(pd.DataFrame(tape_data))
        else:
            st.warning(f"Waiting for {city} live stream... Verify API Key if this persists.")
        st.divider()
