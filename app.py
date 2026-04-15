import streamlit as st
import requests
import streamlit.components.v1 as components

# PAGE CONFIG
st.set_page_config(page_title="Terminal V1.0", layout="centered")

st.markdown("<h2 style='text-align: center; color: #FF4B4B;'>🦅 WEATHER COMMAND</h2>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #888;'>Live Asynchronous Web-Tap Active</p>", unsafe_allow_html=True)

# 1. SETUP
all_airports = ["ATL", "AUS", "BNA", "BOS", "CLT", "DCA", "DTW", "HOU", "JAX", "LAX", "LGA", "MDW", "MIA", "MSP", "OKC", "PHX", "SAT", "SEA", "SFO"]
active_cities = st.multiselect("Active Battlegrounds", all_airports, default=["LGA", "MDW"])

try:
    API_KEY = st.secrets["CLIMATESIGHT_API_KEY"]
except:
    st.error("🔑 API Key missing in Streamlit Secrets!")
    st.stop()

# 2. THE MARKET MAPPER (Python handles this instantly)
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

# 3. THE ASYNCHRONOUS COMPONENT (JavaScript handles the live wire)
def render_live_terminal(city, market_id, token):
    # This HTML/JS block runs natively in your browser to prevent Python from freezing
    html_code = f"""
    <!DOCTYPE html>
    <html>
    <head>
    <style>
        body {{
            background-color: #0E1117;
            color: #FAFAFA;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
            margin: 0;
            padding: 10px;
        }}
        .metric-card {{
            background-color: #1E2329;
            border-radius: 8px;
            padding: 15px;
            margin-bottom: 10px;
            border: 1px solid #333;
        }}
        .header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 1px solid #333;
            padding-bottom: 10px;
            margin-bottom: 10px;
        }}
        .city-name {{ font-size: 1.2rem; font-weight: 600; }}
        .temp-value {{ font-size: 2.2rem; font-weight: 700; color: #FF4B4B; }}
        .status-box {{ text-align: right; }}
        .status-text {{ font-size: 0.8rem; color: #888; margin-top: 5px; }}
        .status-indicator {{ color: #E2A03F; font-weight: bold; }}
        .tape-table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 0.9rem;
        }}
        .tape-table th, .tape-table td {{
            padding: 6px 4px;
            text-align: left;
            border-bottom: 1px solid #2A2E35;
        }}
        .tape-table th {{ color: #888; font-weight: 500; }}
    </style>
    </head>
    <body>
        <div class="metric-card">
            <div class="header">
                <div>
                    <div class="city-name">📍 {city}</div>
                    <div class="status-text">Hardware: Climate Site</div>
                </div>
                <div class="status-box">
                    <div class="temp-value" id="temp_{city}">--.-°F</div>
                    <div class="status-text" id="status_{city}"><span class="status-indicator">Connecting to SSE wire...</span></div>
                </div>
            </div>
            <table class="tape-table">
                <thead><tr><th>Time (UTC)</th><th>Type</th><th>Temp</th></tr></thead>
                <tbody id="tape_{city}"></tbody>
            </table>
        </div>

        <script>
            const marketId = "{market_id}";
            const token = "{token}";
            const tapeBody = document.getElementById("tape_{city}");
            const tempDisplay = document.getElementById("temp_{city}");
            const statusDisplay = document.getElementById("status_{city}");
            
            let tapeData = [];

            async function connectLiveWire() {{
                try {{
                    const response = await fetch(`https://www.climatesight.app/api/stream/sse?market=${{marketId}}`, {{
                        headers: {{ 'Authorization': `Bearer ${{token}}` }}
                    }});
                    
                    if (!response.ok) {{
                        statusDisplay.innerHTML = `<span style="color:#FF4B4B">Connection Rejected</span>`;
                        return;
                    }}
                    
                    statusDisplay.innerHTML = `<span style="color:#00FF00">Live: Awaiting payload...</span>`;

                    const reader = response.body.getReader();
                    const decoder = new TextDecoder();
                    let buffer = "";

                    while (true) {{
                        const {{ value, done }} = await reader.read();
                        if (done) break;
                        
                        buffer += decoder.decode(value, {{stream: true}});
                        const lines = buffer.split('\\n');
                        buffer = lines.pop(); 

                        for (const line of lines) {{
                            if (line.startsWith("data:")) {{
                                try {{
                                    const payload = JSON.parse(line.substring(5).trim());
                                    if (payload.type === "pt" && payload.event) {{
                                        updateTape(payload.event);
                                    }} else if (payload.type === "hb") {{
                                        // Silent heartbeat to keep line open
                                    }}
                                }} catch (e) {{}}
                            }}
                        }}
                    }}
                }} catch (err) {{
                    statusDisplay.innerHTML = `<span style="color:#E2A03F">Line dropped. Reconnecting...</span>`;
                    setTimeout(connectLiveWire, 3000);
                }}
            }}

            function updateTape(event) {{
                const tempF = event.tempF !== null ? event.tempF.toFixed(1) : "--.-";
                const obsType = event.product || event.kind || "OMO";
                let timeUTC = event.observedAt || "";
                if (timeUTC.length > 15) timeUTC = timeUTC.substring(11, 16);

                // Flash the new temperature
                tempDisplay.innerText = `${{tempF}}°F`;
                statusDisplay.innerHTML = `<span style="color:#00FF00">Last: ${{timeUTC}} UTC</span>`;

                // Add to rolling tape
                tapeData.unshift({{time: timeUTC, type: obsType, temp: tempF}});
                if (tapeData.length > 8) tapeData.pop();

                // Draw the tape table
                tapeBody.innerHTML = "";
                tapeData.forEach(hit => {{
                    const tr = document.createElement("tr");
                    tr.innerHTML = `<td>${{hit.time}}</td><td>${{hit.type}}</td><td style="color:#FF4B4B; font-weight:bold;">${{hit.temp}}°F</td>`;
                    tapeBody.appendChild(tr);
                }});
            }}

            // Initiate the tap
            connectLiveWire();
        </script>
    </body>
    </html>
    """
    components.html(html_code, height=380, scrolling=True)

# 4. RENDER DASHBOARD
for city in active_cities:
    market_id = station_map.get(city)
    if market_id:
        render_live_terminal(city, market_id, API_KEY)
    else:
        st.error(f"Offline: Could not find Market ID for {city}.")

st.caption("V1.0 - Native Institutional SSE Terminal Active")
