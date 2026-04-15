import streamlit as st
import pandas as pd
import requests
import json

# PAGE CONFIG
st.set_page_config(page_title="Terminal V0.6.1", layout="centered")

st.markdown("<h2 style='text-align: center; color: #FF4B4B;'>🦅 WEATHER COMMAND</h2>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #888;'>High-Frequency Replay Interceptor</p>", unsafe_allow_html=True)

# 1. SETUP
all_airports = ["ATL", "AUS", "BNA", "BOS", "CLT", "DCA", "DTW", "HOU", "JAX", "LAX", "LGA", "MDW", "MIA", "MSP", "OKC", "PHX", "SAT", "SEA", "SFO"]
active_cities = st.multiselect("Active Battlegrounds", all_airports, default=["LGA", "MDW"])

try:
    API_KEY = st.secrets["CLIMATESIGHT_API_KEY"]
except:
    st.error("🔑 API Key missing in Streamlit Secrets!")
    st.stop()

# 2. THE MARKET MAPPER
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
                m_id = m.get("id")
                if nws and m_id:
                    mapping[nws] = m_id
            return mapping
    except:
        pass
    return {}

station_map = get_market_map()

# 3. THE REPLAY INTERCEPTOR
def intercept_stream(market_id):
    # The Magic Key: lastEventId=0 forces the server to instantly dump its recent tape
    url = f"https://www.climatesight.app/api/stream/sse?market={market_id}&lastEventId=0"
    headers = {"Authorization": f"Bearer {API_KEY}", "Accept": "text/event-stream"}
    tape = []
    
    try:
        # timeout=(Connect Timeout, Read Timeout). 
        # If the server goes silent for 2.5s after the initial dump, we cut the line!
        with requests.get(url, headers=headers, stream=True, timeout=(3.0, 2.5)) as response:
            for line in response.iter_lines():
                if line:
                    decoded = line.decode('utf-8')
                    if decoded.startswith("data:"):
                        try:
                            payload = json.loads(decoded[5:].strip())
                            if payload.get("type") == "pt":
                                tape.append(payload.get("event"))
                        except:
                            pass
    except requests.exceptions.ReadTimeout:
        # We expect this! It means the historical dump finished and the line went quiet.
        pass
    except Exception as e:
        pass
        
    # Sort newest first, return top 15 hits
    sorted_tape = sorted(tape, key=lambda x: x.get("observedAt") or "", reverse=True)
    return sorted_tape[:15]

# 4. THE DISPLAY
for city in active_cities:
    market_id = station_map.get(city)
    
    with st.container():
        if market_id:
            obs = intercept_stream(market_id)
            if obs and len(obs) > 0:
                latest = obs[0]
                temp_f = latest.get('tempF')
                display_temp = f"{temp_f}°F" if temp_f is not None else "N/A"
                
                obs_type = latest.get('product', latest.get('kind', 'OMO'))
                
                col1, col2 = st.columns([1, 1])
                with col1:
                    st.metric(label=f"📍 {city} ({obs_type})", value=display_temp)
                with col2:
                    ts = latest.get('observedAt') or ''
                    st.caption(f"Last Hit: {ts[11:16] if len(ts)>15 else 'N/A'} UTC")
                    st.caption(f"Status: Tape Acquired")
                
                with st.expander("View 1-Min Tape (OMO/HFM)"):
                    tape_list = []
                    for o in obs:
                        t_val = o.get('tempF')
                        t_str = f"{t_val}°F" if t_val is not None else "N/A"
                        t_type = o.get('product', o.get('kind', 'OMO'))
                        t_time = o.get('observedAt') or ''
                        t_time = t_time[11:16] if len(t_time)>15 else 'N/A'
                        tape_list.append({"Time (UTC)": t_time, "Type": t_type, "Temp": t_str})
                    st.table(pd.DataFrame(tape_list))
            else:
                st.warning(f"Intercept failed for {city}. Refreshing line...")
        else:
            st.error(f"Offline: Could not map {city} to a supported market ID.")
            
        st.divider()

st.caption("V0.6.1 - High-Frequency Replay Interceptor Active")
