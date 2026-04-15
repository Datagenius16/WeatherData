import streamlit as st
import requests

st.set_page_config(page_title="Auto-Decoder", layout="centered")

st.markdown("<h2 style='text-align: center; color: #FF4B4B;'>🦅 WEATHER COMMAND</h2>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #888;'>Brute-Force Auto-Decoder Active</p>", unsafe_allow_html=True)

try:
    API_KEY = st.secrets["CLIMATESIGHT_API_KEY"]
except:
    st.error("🔑 API Key Missing!")
    st.stop()

def run_decoder():
    st.subheader("📍 Target: LGA")
    headers = {"Authorization": f"Bearer {API_KEY}"}
    
    # Testing every possible string format
    test_formats = ["LGA", "lga", "KLGA", "klga"]
    
    for fmt in test_formats:
        url = f"https://www.climatesight.app/api/stations/{fmt}"
        res = requests.get(url, headers=headers)
        
        if res.status_code == 200:
            st.success(f"✅ LOCK ACQUIRED! Server accepted format: **{fmt}**")
            st.write("Raw Payload Data (Dictionary Keys):")
            st.json(res.json()) # This dumps the exact data structure on screen
            return # Stops after finding the correct format
        else:
            st.error(f"❌ Rejected format: {fmt} (Code: {res.status_code})")
            
    st.warning("All standard formats rejected. The API might require internal numeric IDs or a different endpoint.")

run_decoder()
