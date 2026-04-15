import streamlit as st
import requests

# PAGE CONFIG
st.set_page_config(page_title="Terminal Diagnostics", layout="centered")

st.markdown("<h2 style='text-align: center; color: #FF4B4B;'>🦅 WEATHER COMMAND</h2>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #888;'>Diagnostic Scanner Active</p>", unsafe_allow_html=True)

# 1. SETUP
all_airports = ["ATL", "AUS", "BNA", "BOS", "CLT", "DCA", "DTW", "HOU", "JAX", "LAX", "LGA", "MDW", "MIA", "MSP", "OKC", "PHX", "SAT", "SEA", "SFO"]
active_cities = st.multiselect("Active Battlegrounds", all_airports, default=["LGA"])

# 2. LOAD SECURE KEY
try:
    API_KEY = st.secrets["CLIMATESIGHT_API_KEY"]
except:
    st.error("🔑 API Key missing in Streamlit Secrets!")
    st.stop()

# 3. DIAGNOSTIC ENGINE
def scan_server(station):
    station_id = f"K{station.upper()}"
    url = f"https://www.climatesight.app/api/stations/{station_id}"
    headers = {"Authorization": f"Bearer {API_KEY}"}
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        return response.status_code, response.text
    except Exception as e:
        return 0, str(e)

# 4. THE RAW DISPLAY
for city in active_cities:
    st.subheader(f"📍 {city} Raw Server Scan")
    status_code, raw_text = scan_server(city)
    
    if status_code == 200:
        st.success(f"✅ Connection Successful (Code: {status_code})")
        st.write("Here is the raw package the server sent back:")
        st.code(raw_text[:1000], language="json")
    else:
        st.error(f"❌ Connection Rejected (Code: {status_code})")
        st.write("Error message from server:")
        st.code(raw_text, language="text")
    st.divider()
