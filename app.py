import streamlit as st
import pandas as pd
import requests
import json
import time

# PAGE CONFIG
st.set_page_config(page_title="Terminal V0.6", layout="centered")

st.markdown("<h2 style='text-align: center; color: #FF4B4B;'>🦅 WEATHER COMMAND</h2>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #888;'>SSE Live Datalink Interceptor</p>", unsafe_allow_html=True)

# 1. SETUP
all_airports = ["ATL", "AUS", "BNA", "BOS", "CLT", "DCA", "DTW", "HOU", "JAX", "LAX", "LGA", "MDW", "MIA", "MSP", "OKC", "PHX", "SAT", "SEA", "SFO"]
active_cities = st.multiselect("Active Battlegrounds", all_airports, default=["LGA", "MDW"])

try:
    API_KEY = st.secrets["CLIMATESIGHT_API_KEY"]
except:
    st.error("🔑 API Key missing in Streamlit Secrets!")
    st.stop()

# 2. THE MARKET MAPPER (Translates LGA -> new-york-lga)
@st.cache_data(ttl=3600)
def get_market_map():
    url = "https://www.climatesight.app/api/markets"
    headers = {"Authorization": f"Bearer {API_KEY}"}
    try:
        res = requests.get(url, headers=headers, timeout=10)
        if res.status_code == 200:
            mapping = {}
            for m in res.json():
                nws = m.get("nwsLocationCode") # Grabs 'LGA'
                m_id = m.get("id") # Grabs 'new-york-lga'
                if nws and m_id:
                    mapping[nws] = m_id
            return mapping
    except:
        pass
    return {}

station_map = get_market_map()

# 3. THE SSE INTERCEPTOR (Taps the live fiber-optic stream)
def intercept_stream(market_id):
    url = f"https://www.climatesight.app/api/stream/sse?market={market_id}"
    # SSE requires the specific 'text/event-stream' accept header
    headers = {"Authorization": f"Bearer {API_KEY}", "Accept": "text/event-stream"}
    tape = []
    
    try:
        # stream=True opens the pipeline. 
        with requests.get(url, headers=headers, stream=True, timeout=5) as response:
            start_time = time.time()
            
            # We listen to the live wire for exactly 3 seconds to catch the data burst
            for line in response.iter_lines():
                if time.time() - start_time > 3:
                    break # Severs the connection so Streamlit doesn't freeze
                    
                if line:
                    decoded = line.decode('utf-8')
                    # We are hunting for the 'data: ' payload string
                    if decoded.startswith("data:"):
                        try:
                            # Strip 'data: ' to parse the raw JSON
                            payload = json.loads(decoded[5:].strip())
                            
                            # We only want weather points ('pt'), ignore keep-alive heartbeats ('hb')
                            if payload.get("type") == "pt":
                                tape.append(payload.get("event"))
                                if len(tape) >= 15:
                                    break
                        except:
                            pass
    except Exception as e:
        pass
        
    # Sort the tape chronologically so the newest hit is at the top
    return sorted(tape, key=lambda x: x.get("observedAt", ""), reverse=True)

# 4. THE DISPLAY
for city in active_cities:
    market_id = station_map.get(city)
    
    with st.container():
        if market_id:
            obs = intercept_stream(market_id)
            if obs and len(obs) > 0:
                latest = obs[0]
                
                # The schema natively provides Fahrenheit calculations 
                temp_f = latest.get('tempF')
                display_temp = f"{temp_f}°F" if temp_f is not None else "N/A"
                
                # Extract 'product' (e.g., ASOS-HFM) or fallback to 'kind'
                obs_type = latest.get('product', latest.get('kind', 'OMO'))
                
                # METRIC DISPLAY
                col1, col2 = st.columns([1, 1])
                with col1:
                    st.metric(label=f"📍 {city} ({obs_type})", value=display_temp)
                with col2:
                    ts = latest.get('observedAt', '')
                    st.caption(f"Last Hit: {ts[11:16] if len(ts)>15 else 'N/A'} UTC")
                    st.caption(f"Stream: Active")
                
                # THE TAPE
                with st.expander("View 1-Min Tape (OMO/HFM)"):
                    tape_list = []
                    for o in obs:
                        t_val = o.get('tempF')
                        t_str = f"{t_val}°F" if t_val is not None else "N/A"
                        t_type = o.get('product', o.get('kind', 'OMO'))
                        t_time = o.get('observedAt', '')
                        t_time = t_time[11:16] if len(t_time)>15 else 'N/A'
                        tape_list.append({"Time (UTC)": t_time, "Type": t_type, "Temp": t_str})
                    st.table(pd.DataFrame(tape_list))
            else:
                st.warning(f"Intercepting SSE stream for {city}... (Awaiting next 60s data burst)")
        else:
            st.error(f"Offline: Could not map {city} to a supported market ID.")
            
        st.divider()

st.caption("V0.6 - Live SSE Interceptor Active")
