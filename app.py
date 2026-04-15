import streamlit as st
import pandas as pd
import requests

# PAGE CONFIG
st.set_page_config(page_title="Terminal V0.5", layout="centered")

st.markdown("<h2 style='text-align: center; color: #FF4B4B;'>🦅 WEATHER COMMAND</h2>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #888;'>Autonomous Datalink Active</p>", unsafe_allow_html=True)

# 1. SETUP
all_airports = ["ATL", "AUS", "BNA", "BOS", "CLT", "DCA", "DTW", "HOU", "JAX", "LAX", "LGA", "MDW", "MIA", "MSP", "OKC", "PHX", "SAT", "SEA", "SFO"]
active_cities = st.multiselect("Active Battlegrounds", all_airports, default=["LGA", "MDW"])

# 2. LOAD SECURE KEY
try:
    API_KEY = st.secrets["CLIMATESIGHT_API_KEY"]
except:
    st.error("🔑 API Key missing in Streamlit Secrets!")
    st.stop()

HEADERS = {"Authorization": f"Bearer {API_KEY}"}

# 3. AUTO-MAPPER ENGINE (Finds the secret numeric IDs)
@st.cache_data(ttl=3600) # Caches the mapping for an hour so we don't spam their server
def get_station_map():
    url = "https://www.climatesight.app/api/markets"
    try:
        res = requests.get(url, headers=HEADERS, timeout=10)
        if res.status_code == 200:
            return res.json()
    except:
        pass
    return []

markets_data = get_station_map()

# Build the dictionary mapping (e.g., {"LGA": 42})
station_map = {}
if isinstance(markets_data, list):
    for m in markets_data:
        m_id = str(m.get('id', '')).upper()
        s_id = m.get('station')
        if s_id:
            # Match the market ID string to our 3-letter active cities
            for city in all_airports:
                if city in m_id:
                    station_map[city] = s_id

# 4. THE HF ENGINE (Pulls the tape using the numeric ID)
def get_station_tape(numeric_id):
    url = f"https://www.climatesight.app/api/stations/{numeric_id}"
    try:
        res = requests.get(url, headers=HEADERS, timeout=10)
        if res.status_code == 200:
            data = res.json()
            # We look for the observations list inside the package
            if isinstance(data, dict) and 'observations' in data:
                return data['observations']
            elif isinstance(data, list):
                return data
            return [data]
    except:
        return []

# 5. THE DISPLAY
for city in active_cities:
    numeric_id = station_map.get(city)
    
    with st.container():
        if numeric_id:
            obs = get_station_tape(numeric_id)
            if obs and len(obs) > 0:
                latest = obs[0]
                val = latest.get('temp')
                temp_f = round((val * 9/5) + 32, 1) if val is not None else "N/A"
                
                # METRIC DISPLAY
                col1, col2 = st.columns([1, 1])
                with col1:
                    st.metric(label=f"📍 {city} ({latest.get('kind', latest.get('type', 'OMO'))})", value=f"{temp_f}°F")
                with col2:
                    ts = latest.get('observedAt', latest.get('observed_at', ''))
                    st.caption(f"Last Hit: {ts[11:16] if ts else 'N/A'} UTC")
                    st.caption(f"Station ID: #{numeric_id}")
                
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
                st.warning(f"Numeric ID #{numeric_id} linked, but waiting for live runway tape...")
        else:
            st.error(f"Offline: Could not find the secret numeric ID for {city}. Market may be closed.")
            
        st.divider()

# DIAGNOSTIC BACKUP
with st.expander("System Diagnostics (Raw Market Directory)"):
    st.write("This shows the raw numeric IDs pulled from the server:")
    st.json(station_map)

st.caption("V0.5 - Datalink Secured")
