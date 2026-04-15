import streamlit as st
import pandas as pd
import requests

# PAGE CONFIG
st.set_page_config(page_title="Terminal V0.4.2", layout="centered")

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

# 3. THE HF ENGINE (ClimateSight 2026 Market Protocol)
def get_climatesight_data(station):
    # ClimateSight markets are typically 'station-temp-max' or 'station-temp-min'
    # We target the station detail directly to get the OMO/HFM feed
    station_id = f"k{station.lower()}"
    url = f"https://www.climatesight.app/api/stations/{station_id}"
    headers = {"Authorization": f"Bearer {API_KEY}"}
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            # We want the 'history' or 'observations' list
            data = response.json()
            return data.get('observations', []) or data.get('history', [])
        return []
    except:
        return []

# 4. THE DISPLAY
for city in active_cities:
    obs = get_climatesight_data(city)
    
    with st.container():
        if obs and len(obs) > 0:
            latest = obs[0]
            # ClimateSight uses Celsius; we convert to Fahrenheit
            # If they already provide 'temp_f', we'll use that as a fallback
            val = latest.get('temp')
            temp_f = round((val * 9/5) + 32, 1) if val is not None else "N/A"
            
            # METRIC DISPLAY
            col1, col2 = st.columns([1, 1])
            with col1:
                st.metric(label=f"📍 {city} ({latest.get('kind', latest.get('type', 'OMO'))})", value=f"{temp_f}°F")
            with col2:
                # Handle timestamp keys
                ts = latest.get('observedAt', latest.get('observed_at', ''))
                st.caption(f"Last Hit: {ts[11:16] if ts else 'N/A'} UTC")
                st.caption(f"Hardware: Climate Site")

            # THE TAPE
            with st.expander("View 1-Min Tape (OMO/HFM)"):
                tape_list = []
                for o in obs[:15]:
                    v = o.get('temp')
                    f_val = round((v * 9/5) + 32, 1) if v is not None else "N/A"
                    t_type = o.get('kind', o.get('type', 'OMO'))
                    t_time = o.get('observedAt', o.get('observed_at', ''))[11:16]
                    tape_list.append({"Time (UTC)": t_time, "Type": t_type, "Temp": f"{f_val}°F"})
                st.table(pd.DataFrame(tape_list))
        else:
            st.info(f"Establishing link to {city} runway sensors...")
        st.divider()

st.caption("V0.4.2 - High-Frequency Trading Feed Active")
