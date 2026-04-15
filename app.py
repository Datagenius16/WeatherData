import streamlit as st
import pandas as pd
import requests
import json
import threading
import time

# PAGE CONFIG
st.set_page_config(page_title="Terminal V1.1", layout="centered")

st.markdown("<h2 style='text-align: center; color: #FF4B4B;'>🦅 WEATHER COMMAND</h2>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #888;'>Background Threading Active</p>", unsafe_allow_html=True)

# 1. SETUP
all_airports = ["ATL", "AUS", "BNA", "BOS", "CLT", "DCA", "DTW", "HOU", "JAX", "LAX", "LGA", "MDW", "MIA", "MSP", "OKC", "PHX", "SAT", "SEA", "SFO"]
active_cities = st.multiselect("Active Battlegrounds", all_airports, default=["LGA", "MDW"])

try:
    API_KEY = st.secrets["CLIMATESIGHT_API_KEY"]
except:
    st.error("🔑 API Key missing in Streamlit Secrets!")
    st.stop()

# 2. SHARED MEMORY VAULT
# This cache persists in the server's memory across all page refreshes
@st.cache_resource
def get_tape_vault():
    return {}

DATA_VAULT = get_tape_vault()

# 3. MARKET MAPPER
@st.cache_data(ttl=3600)
def get_market_map():
    url = "https://www.climatesight.app/api/markets"
    headers = {"Authorization": f"Bearer {API_KEY}"}
    try:
        res = requests.get(url, headers=headers, timeout=10)
        if res.status_code == 200:
            mapping = {}
            for m in res.json():
                nws = m.get("nwsLocationCode")
                if nws:
                    mapping[nws] = m.get("id")
            return mapping
    except:
        pass
    return {}

station_map = get_market_map()

# 4. BACKGROUND WORKER (The Silent Wiretaps)
@st.cache_resource
def start_background_workers(_market_map, api_key):
    def tap_wire(city, market_id):
        url = f"https://www.climatesight.app/api/stream/sse?market={market_id}"
        headers = {"Authorization": f"Bearer {api_key}", "Accept": "text/event-stream"}
        
        # Infinite loop keeps the background thread alive forever
        while True:
            try:
                with requests.get(url, headers=headers, stream=True, timeout=90) as res:
                    for line in res.iter_lines():
                        if line:
                            decoded = line.decode('utf-8')
                            if decoded.startswith("data:"):
                                try:
                                    payload = json.loads(decoded[5:].strip())
                                    if payload.get("type") == "pt" and "event" in payload:
                                        event = payload["event"]
                                        
                                        if city not in DATA_VAULT:
                                            DATA_VAULT[city] = []
                                        
                                        # Deduplicate by ID and insert new data at the top
                                        existing_ids = [e.get("id") for e in DATA_VAULT[city]]
                                        if event.get("id") not in existing_ids:
                                            DATA_VAULT[city].insert(0, event)
                                            # Keep only the last 15 minutes of tape
                                            DATA_VAULT[city] = DATA_VAULT[city][:15] 
                                except:
                                    pass
            except Exception as e:
                time.sleep(5) # If the connection drops, wait 5 seconds and reconnect
                
    # Deploy a silent thread for every airport in the directory
    for city, market_id in _market_map.items():
        if city not in DATA_VAULT:
            DATA_VAULT[city] = []
        # daemon=True ensures these threads run invisibly in the background
        t = threading.Thread(target=tap_wire, args=(city, market_id), daemon=True)
        t.start()
        
    return True

# Initialize the threads once
if station_map:
    start_background_workers(station_map, API_KEY)

# 5. DASHBOARD DISPLAY
col1, col2 = st.columns([3, 1])
with col1:
    st.caption("Data streams silently in the background.")
with col2:
    # A native button that forces the Streamlit UI to re-read the Vault instantly
    st.button("🔄 Sync Feed")

for city in active_cities:
    market_id = station_map.get(city)
    
    with st.container():
        if market_id:
            tape = DATA_VAULT.get(city, [])
            if tape and len(tape) > 0:
                latest = tape[0]
                temp_f = latest.get('tempF')
                display_temp = f"{temp_f}°F" if temp_f is not None else "N/A"
                
                obs_type = latest.get('product', latest.get('kind', 'OMO'))
                
                mcol1, mcol2 = st.columns([1, 1])
                with mcol1:
                    st.metric(label=f"📍 {city} ({obs_type})", value=display_temp)
                with mcol2:
                    ts = latest.get('observedAt', '')
                    st.caption(f"Last Hit: {ts[11:16] if len(ts)>15 else 'N/A'} UTC")
                    st.caption("Status: Active Vault Link")
                
                with st.expander("View 1-Min Tape (OMO/HFM)", expanded=True):
                    tape_list = []
                    for o in tape:
                        t_val = o.get('tempF')
                        t_str = f"{t_val}°F" if t_val is not None else "N/A"
                        t_type = o.get('product', o.get('kind', 'OMO'))
                        t_time = o.get('observedAt', '')
                        t_time = t_time[11:16] if len(t_time)>15 else 'N/A'
                        tape_list.append({"Time (UTC)": t_time, "Type": t_type, "Temp": t_str})
                    st.table(pd.DataFrame(tape_list))
            else:
                st.info(f"Background thread tapped into {city} wire... (Awaiting first 60s payload)")
        else:
            st.error(f"Offline: Could not map {city}.")
            
        st.divider()

st.caption("V1.1 - Python Background Daemon Active")
