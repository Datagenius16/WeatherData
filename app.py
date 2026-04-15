import streamlit as st
import requests

st.set_page_config(page_title="Diagnostic Scanner", layout="centered")

st.markdown("<h2 style='text-align: center; color: #FF4B4B;'>🦅 WEATHER COMMAND</h2>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #888;'>SSE Raw Diagnostic Scanner</p>", unsafe_allow_html=True)

try:
    API_KEY = st.secrets["CLIMATESIGHT_API_KEY"]
except:
    st.error("🔑 API Key missing!")
    st.stop()

headers = {"Authorization": f"Bearer {API_KEY}", "Accept": "text/event-stream"}

# 1. Fetch Market ID
st.subheader("1. Hunting for LGA Market ID...")
markets_url = "https://www.climatesight.app/api/markets"
try:
    res = requests.get(markets_url, headers={"Authorization": f"Bearer {API_KEY}"})
    markets = res.json()
    lga_id = next((m["id"] for m in markets if m.get("nwsLocationCode") == "LGA"), None)
    if lga_id:
        st.success(f"✅ LGA successfully mapped to Market ID: `{lga_id}`")
    else:
        st.error("❌ Could not find LGA in the markets directory.")
        st.json(markets[:5])
except Exception as e:
    st.error(f"Failed to fetch markets: {e}")

# 2. Test Stream Connection
if lga_id:
    st.subheader("2. Tapping the SSE Wire...")
    stream_url = f"https://www.climatesight.app/api/stream/sse?market={lga_id}&lastEventId=0"
    st.code(f"GET {stream_url}")
    
    try:
        # stream=True keeps the line open to see if the server talks
        res = requests.get(stream_url, headers=headers, stream=True, timeout=5)
        st.write(f"**HTTP Status Code:** `{res.status_code}`")
        
        if res.status_code == 200:
            st.success("Connection Accepted! Waiting 5 seconds for data payload...")
            lines = []
            for i, line in enumerate(res.iter_lines()):
                if line:
                    lines.append(line.decode('utf-8'))
                if i >= 5: # Grab the first few lines and cut the wire
                    break
            
            if lines:
                st.write("Server transmitted the following payload:")
                st.code("\n".join(lines), language="text")
            else:
                st.warning("Server accepted the connection but sat in complete silence (No data transmitted).")
                
        else:
            st.error("Connection Rejected by ClimateSight.")
            # If it's a 400 error, the server sends a normal JSON reason, not a stream
            st.code(res.text, language="json")
            
    except requests.exceptions.ReadTimeout:
        st.warning("⚠️ Read Timeout. The server accepted the connection but refused to replay the history within 5 seconds.")
    except Exception as e:
        st.error(f"System Crash: {e}")
