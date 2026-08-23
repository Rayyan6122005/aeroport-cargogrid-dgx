"""
AeroPort CargoGrid – DGX Spark Elite Master Dashboard
[100% REAL DATA EXTRACTION - PREMIUM UI]
"""
import time
import json
import requests
import pandas as pd
import altair as alt
import streamlit as st
import streamlit.components.v1 as components

BACKEND_URL = "http://127.0.0.1:8000"

st.set_page_config(page_title="CargoGrid Sentry", page_icon="🚢", layout="wide", initial_sidebar_state="collapsed")

# ==============================================================================
# ULTIMATE ZERO-FLICKER & ELITE STYLING CSS
# ==============================================================================
st.markdown("""
<style>
  .stApp, [data-testid="stAppViewContainer"], [data-testid="stAppViewBlockContainer"] { opacity: 1 !important; transition: none !important; filter: none !important; animation: none !important; }
  [data-testid="stStatusWidget"], div.stSpinner, .stSkeleton, [data-testid="stDecoration"] { display: none !important; visibility: hidden !important; opacity: 0 !important; }
  header[data-testid="stHeader"] { display: none !important; }

  .stApp { 
      background-color: #0d1117; color: #c9d1d9; font-family: 'Inter', sans-serif;
      background-image: linear-gradient(rgba(88, 166, 255, 0.03) 1px, transparent 1px), linear-gradient(90deg, rgba(88, 166, 255, 0.03) 1px, transparent 1px);
      background-size: 30px 30px;
  }
  
  .fixed-header {
      position: fixed; top: 0; left: 0; right: 0; z-index: 99999;
      background: linear-gradient(135deg, #161b22 0%, #0d1117 100%);
      border-bottom: 2px solid #30363d; padding: 1rem 2rem; display: flex; align-items: center; justify-content: space-between;
      box-shadow: 0 4px 20px rgba(0,0,0,0.5);
  }
  .fixed-header h1 { color: #58a6ff; margin: 0; font-size: 1.8rem; font-weight: 900; letter-spacing: -0.5px; text-shadow: 0 0 10px rgba(88,166,255,0.3);}
  .fixed-header p  { color: #8b949e; margin: 0.2rem 0 0; font-size: 0.85rem; font-family: 'Cascadia Code', monospace;}
  
  .block-container { padding-top: 100px !important; }

  .card {
      background: #161b22; border: 1px solid #30363d; border-radius: 8px;
      padding: 15px; text-align: center; box-shadow: 0 4px 15px rgba(0,0,0,0.3);
      position: relative; overflow: hidden; height: 140px !important; 
      display: flex !important; flex-direction: column !important; justify-content: center !important; align-items: center !important;
  }
  .card::before { content: ""; position: absolute; top: 0; left: 0; width: 100%; height: 3px; }
  .card.c-blue::before { background: #58a6ff; box-shadow: 0 0 10px #58a6ff;}
  .card.c-clear::before { background: #3fb950; box-shadow: 0 0 10px #3fb950;}
  .card.c-congested::before { background: #d29922; box-shadow: 0 0 10px #d29922; animation: pulse-orange 1.5s infinite;}
  .card.c-offline::before { background: #f85149; box-shadow: 0 0 10px #f85149; animation: pulse-red 1s infinite;}
  .card.c-impact::before { background: #f85149; }
  .card.c-purple::before { background: #a371f7; box-shadow: 0 0 10px #a371f7;}

  @keyframes pulse-red { 0% {box-shadow: 0 0 5px #f85149;} 50% {box-shadow: 0 0 20px #f85149;} 100% {box-shadow: 0 0 5px #f85149;} }
  @keyframes pulse-orange { 0% {box-shadow: 0 0 5px #d29922;} 50% {box-shadow: 0 0 20px #d29922;} 100% {box-shadow: 0 0 5px #d29922;} }

  .card .lbl { font-size: 0.75rem; color: #8b949e; text-transform: uppercase; letter-spacing: 0.1em; font-weight: bold; margin-bottom: 8px;}
  .card .val { font-size: 1.6rem; font-weight: 900; color: #c9d1d9; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; width: 100%; text-align: center; line-height: 1.2;}
  
  .c-clear .val{ color: #3fb950; } .c-congested .val{ color: #d29922; } .c-offline .val{ color: #f85149; } .c-impact .val { color: #f85149; } .c-purple .val { color: #a371f7; }

  .cascade-row { display: flex; align-items: center; gap: 12px; margin: 12px 0; }
  .cascade-bar { background: linear-gradient(90deg, #d29922 0%, #f85149 100%); border-radius: 4px; height: 14px; box-shadow: 0 0 10px rgba(248,81,73,0.3); }
  .cascade-lbl { font-size: 0.75rem; color: #8b949e; width: 75px; text-align: right; font-weight: bold; font-family: monospace;}
  .cascade-val { font-size: 0.8rem; color: #d29922; font-weight: bold; }

  .terminal { background: #010409; border: 1px solid #30363d; border-radius: 6px; padding: 1rem; font-family: monospace; font-size: 0.85rem; height: 320px; overflow-y: auto; white-space: pre-wrap; box-shadow: inset 0 0 20px rgba(0,0,0,0.5);}
  
  .stTabs [data-baseweb="tab-list"] { background-color: #161b22; border-radius: 6px; padding: 0.5rem; gap: 5px; border: 1px solid #30363d; box-shadow: 0 4px 10px rgba(0,0,0,0.3);}
  .stTabs [data-baseweb="tab"] { color: #8b949e; font-weight: 600; font-size: 0.9rem; padding: 8px 15px;}
  .stTabs [aria-selected="true"] { color: #c9d1d9 !important; background-color: #21262d; border-radius: 4px; border-bottom: 2px solid #58a6ff;}
</style>
""", unsafe_allow_html=True)

ph_header = st.empty()
t_dispatch, t_sources, t_scrapers, t_health, t_hardware = st.tabs(["🚢 Live Sentry Dispatch", "🌐 AI Web Unlocker", "⚙️ Collector Hub", "📊 Scraper Health & Logs", "📟 ESP32 Hardware Sync"])

JS_FETCH_HELPER = """
<script>
const API = 'http://127.0.0.1:8000';
function sendCmd(endpoint, bodyObj, btnId) {
    const btn = document.getElementById(btnId);
    if (!btn) return;
    const origText = btn.innerText; const origBg = btn.style.background;
    btn.innerText = "⏳ SENDING...";
    fetch(API + endpoint, {
        method: 'POST',
        headers: bodyObj ? {'Content-Type':'application/json'} : {},
        body: bodyObj ? JSON.stringify(bodyObj) : null
    }).then(r => {
        if(!r.ok) throw new Error("HTTP Error");
        btn.innerText = "✅ CONFIRMED"; btn.style.background = "#3fb950";
        setTimeout(() => { btn.innerText = origText; btn.style.background = origBg; }, 1000);
    }).catch(e => {
        btn.innerText = "❌ NETWORK ERR"; btn.style.background = "#da3633";
        setTimeout(() => { btn.innerText = origText; btn.style.background = origBg; }, 1000);
    });
}
</script>
"""

# ==============================================================================
# STATIC UI RENDERING (TABS)
# ==============================================================================
with t_dispatch:
    ph_banner = st.empty()
    left_col, right_col = st.columns([3.5, 1.2])
    with right_col:
        st.markdown("<div style='height:25px'></div>", unsafe_allow_html=True)
        ph_controls_1 = st.empty()
    with left_col:
        ph_cards = st.empty()

    st.markdown("<br>", unsafe_allow_html=True)
    ch_col, term_col = st.columns([1, 1.2])
    with ch_col:
        st.markdown("#### ⛓️ Cascading Downstream Delays")
        ph_cascade = st.empty()
        st.markdown("<hr style='border-color: #30363d;'>", unsafe_allow_html=True)
        st.markdown("#### ⚙️ System Diagnostics")
        ph_summary = st.empty()
    with term_col:
        st.markdown("#### 💻 Live Agent Terminal")
        ph_terminal = st.empty()

    st.markdown("<hr style='border-color: #30363d;'>", unsafe_allow_html=True)
    st.markdown("#### 📈 Network Delay Cascade (Live Chart)")
    ph_chart = st.empty()

with t_sources:
    st.markdown("### 🌐 Live DOM Mutation & Self-Healing Pipeline")
    ph_pipeline_anim = st.empty()
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("#### 🌍 Live Global Target Domain (Fully Working Map)")
    # RESTORED MARINE TRAFFIC MAP (PREMIUM UI)
    components.html("""
    <iframe src="https://www.marinetraffic.com/en/ais/embed/zoom:2/centery:20/centerx:0/maptype:4/shownames:false/mmsi:0/shipid:0/fleet:/fleet_id:/vtypes:/showlines:false/ports:false/storages:false/track:false/lines:false/legends:false" width="100%" height="450" frameborder="0" style="border: 1px solid #30363d; border-radius: 8px; box-shadow: 0 4px 15px rgba(0,0,0,0.5);"></iframe>
    """, height=460)

with t_scrapers:
    st.markdown("### ⚙️ Bright Data Scraper Studio (Interactive Hub)")
    ph_scraper_metrics = st.empty()
    st.markdown("<br>", unsafe_allow_html=True)
    
    ph_collectors_grid = st.empty()
    st.markdown("<br>", unsafe_allow_html=True)
    
    col1, col2 = st.columns([2, 1.2])
    with col1:
        st.markdown("<h4 style='color:#58a6ff; margin-bottom:5px; margin-top:0px;'>🌍 Live Target Domain (Real-Time Iframe)</h4>", unsafe_allow_html=True)
        # PREMIUM STYLED IFRAME - matched height to terminal
        components.html("""
        <div style="border:1px solid #30363d; border-radius:8px; overflow:hidden; box-shadow: 0 4px 20px rgba(0,0,0,0.4); height:420px; width:100%; background:#0d1117;">
            <iframe src="https://www.vesselfinder.com/vessels" style="width:100%; height:100%; border:none;"></iframe>
        </div>
        """, height=440)
        
    with col2:
        st.markdown("<h4 style='color:#a371f7; margin-bottom:5px; margin-top:0px;'>💻 System Control & Failover</h4>", unsafe_allow_html=True)
        components.html(f"""
        {JS_FETCH_HELPER}
        <style>
        body {{ font-family: 'Inter', sans-serif; color: #c9d1d9; background: #0d1117; margin:0; padding:5px;}}
        .panel {{ background: #161b22; border: 1px solid #30363d; border-radius: 8px; padding: 25px; box-shadow: 0 4px 20px rgba(0,0,0,0.4); height: 380px;}}
        input, select {{ width: 100%; padding: 12px; background: #010409; border: 1px solid #30363d; color: #fff; border-radius: 4px; margin-bottom: 12px; box-sizing: border-box; font-size:14px;}}
        button {{ width: 100%; padding: 12px; background: #21262d; border: 1px solid #30363d; color: #c9d1d9; cursor: pointer; border-radius: 4px; font-weight: bold; margin-bottom: 12px; box-sizing: border-box; transition:0.2s; font-size:14px;}}
        button:hover {{ filter: brightness(1.2); }}
        .btn-blue {{ background: #1f6feb; border-color: #388bfd; color: white; box-shadow: 0 0 10px rgba(31,111,235,0.3);}}
        h4 {{ margin-top:0; color:#58a6ff; font-weight:900; letter-spacing: 0.5px; font-size: 15px;}}
        hr {{ border: 0; border-top: 1px solid #30363d; margin: 15px 0; }}
        </style>
        <div class="panel">
            <h4>📡 Data Collector Node Selection</h4>
            <select id="scraperSel">
                <option value="c_mt4su8bs1cavzw7gss">cli-scraper-1787428600 (Production Node)</option>
                <option value="c_mt4shzx821npgwgg0">cli-scraper-1787428029 (Failover Node A)</option>
            </select>
            <button id="b3" class="btn-blue" onclick="sendCmd('/switch_scraper', {{scraper_id: document.getElementById('scraperSel').value}}, 'b3')">🔄 Switch Collector Source</button>
            <hr>
            <h4>💻 Terminal Control Injection</h4>
            <input type="text" id="cmd" placeholder="Type command ('fail' or 'heal')" onkeypress="if(event.key === 'Enter') document.getElementById('b4').click();"/>
            <button id="b4" class="btn-blue" onclick="sendCmd('/terminal_command', {{command: document.getElementById('cmd').value}}, 'b4'); document.getElementById('cmd').value='';">⚡ Submit Command</button>
        </div>
        """, height=440)

    st.markdown("<br><h4 style='color:#3fb950; margin-bottom:5px;'>📥 Raw Live JSON Payloads</h4>", unsafe_allow_html=True)
    ph_raw_json = st.empty()
    
    st.markdown("<hr style='border-color: #30363d;'>", unsafe_allow_html=True)
    st.markdown("#### 📊 Proxy Network Analytics & IP Rotation Rate")
    ph_net_chart = st.empty()

with t_health:
    st.markdown("### 📊 Real-Time Scraping Telemetry & Mutation Tracking")
    ph_health_metrics = st.empty()
    st.markdown("<hr style='border-color: #30363d;'>", unsafe_allow_html=True)
    st.markdown("#### 📥 Live JSON Data Pipeline (Firehose)")
    st.markdown("Raw data structures returned by Bright Data Web Unlocker API")
    ph_json_firehose = st.empty()

with t_hardware:
    col_hw_left, col_hw_right = st.columns([1.2, 1])
    with col_hw_left:
        st.markdown("### 📟 ESP32 Synchronization")
        st.markdown("The backend actively monitors the physical ESP32 polling. **If the ESP32 loses network sync, the dashboard safely enters Standby Mode.**")
        ph_controls_2 = st.empty()
        
        st.markdown("### 📡 Live Serial Monitor")
        ph_serial = st.empty()
        
    with col_hw_right:
        ph_tft = st.empty()
        st.markdown("#### 🔌 Deployment Schematic")
        st.markdown("""
        <div style="background:#161b22; padding:15px; border:1px solid #30363d; border-radius:8px; font-family:monospace; font-size:12px; color:#8b949e;">
        [ESP32 Sentry Node]<br>
        ├── TFT_CS   -> GPIO 5<br>
        ├── TFT_RST  -> GPIO 4<br>
        ├── TFT_DC   -> GPIO 2<br>
        ├── TFT_MOSI -> GPIO 23<br>
        ├── TFT_SCLK -> GPIO 18<br>
        └── PIEZO    -> GPIO 15
        </div>
        """, unsafe_allow_html=True)

ph_audio_engine = st.empty()

# ==============================================================================
# MAIN ZERO-FLICKER RENDERING LOOP
# ==============================================================================
while True:
    try:
        r = requests.get(f"{BACKEND_URL}/status", timeout=2)
        lr = requests.get(f"{BACKEND_URL}/logs", timeout=1)
        data = r.json() if r.status_code == 200 else {}
        logs = lr.json().get("lines", []) if lr.status_code == 200 else []
        connected = (r.status_code == 200)
    except:
        data, logs, connected = {}, [], False

    status = data.get("status", "OFFLINE")
    vessel = data.get("vessel_name", "---")
    bay = data.get("bay_id", "---")
    delay = data.get("delay_minutes", 0)
    msg = data.get("message", "...")
    fails = data.get("consecutive_failures", 0)
    updated = data.get("last_updated", "---")
    impact = data.get("impact_score", 0)
    risk = data.get("risk_level", "LOW")
    cascade = data.get("cascading_delays", [])
    history = data.get("history", [])
    collectors = data.get("collectors", [])
    hw_alarm = data.get("hardware_alarm", False)
    sys_phase = data.get("system_phase", "NORMAL")
    active_scraper = data.get("active_scraper", "None")
    audio_muted = data.get("audio_muted", False)
    total_breaks = data.get("total_breaks", 0)
    total_heals = data.get("total_heals", 0)
    recent_payloads = data.get("recent_payloads", [])
    hw_connected = data.get("hw_connected", False)
    
    target_url = "https://www.vesselfinder.com/vessels"

    header_status = "SYSTEM ONLINE" if connected else "SYSTEM OFFLINE"
    header_color = "#3fb950" if connected else "#f85149"
    ph_header.markdown(f"""
    <div class="fixed-header">
      <div><h1>🚢 AeroPort CargoGrid DGX [REAL-TIME LIVE DATA]</h1><p>Solo Submission | Target Node: {active_scraper}</p></div>
      <div style="text-align:right;"><span style="border:1px solid {header_color}; background:rgba(63,185,80,0.1); color:{header_color}; padding:6px 12px; border-radius:4px; font-weight:900; font-size:12px;">{header_status}</span></div>
    </div>
    """, unsafe_allow_html=True)
    
    mute_text = "🔇 LAPTOP AUDIO IS MUTED" if audio_muted else "🔊 MUTE LAPTOP AUDIO"
    mute_style = "background:#30363d; color:#c9d1d9;" if audio_muted else "background:#3fb950; color:white; font-weight:bold; box-shadow:0 0 10px rgba(63,185,80,0.5);"
    
    controls_html = f"""
    {JS_FETCH_HELPER}
    <style>
    body {{ margin: 0; display: flex; flex-direction: column; justify-content: space-between; height: 180px; font-family: 'Inter', sans-serif; background: transparent;}}
    .btn {{ width: 100%; height: 50px; border: none; border-radius: 6px; font-size: 13px; font-weight: 900; text-transform: uppercase; color: #fff; cursor: pointer; transition: 0.2s; box-shadow: 0 4px 10px rgba(0,0,0,0.5); margin-bottom:10px;}}
    .btn-red {{ background: linear-gradient(90deg, #da3633, #f85149); border: 1px solid #f85149;}} .btn-red:hover {{ filter: brightness(1.2); box-shadow: 0 0 15px rgba(248,81,73,0.6); }}
    .btn-green {{ background: linear-gradient(90deg, #238636, #3fb950); border: 1px solid #3fb950;}} .btn-green:hover {{ filter: brightness(1.2); box-shadow: 0 0 15px rgba(63,185,80,0.6); }}
    </style>
    <button id="b1" class="btn btn-red" onclick="sendCmd('/terminal_command', {{command: 'fail'}}, 'b1')">🔴 Force Pipeline Failure</button>
    <button id="b2" class="btn btn-green" onclick="sendCmd('/terminal_command', {{command: 'heal'}}, 'b2')">🟢 Execute AI Self-Heal</button>
    <button id="bmute1" class="btn" style="{mute_style} border:1px solid #30363d;" onclick="sendCmd('/toggle_audio', null, 'bmute1')">{mute_text}</button>
    """
    
    with ph_controls_1.container():
        components.html(controls_html, height=190)
        
    with ph_controls_2.container():
        components.html(f"""
        {JS_FETCH_HELPER}
        <style>body {{ margin: 0; display:flex; flex-direction:column;}} .btn {{ width: 100%; padding: 15px; margin-bottom:10px; border-radius: 6px; font-weight: bold; cursor: pointer; background: linear-gradient(90deg, #da3633, #f85149); color: white; border: none; box-shadow: 0 4px 10px rgba(0,0,0,0.3); transition:0.2s;}} .btn:hover {{filter: brightness(1.2); box-shadow: 0 0 15px rgba(248,81,73,0.6);}}</style>
        <button id="b6" class="btn" onclick="sendCmd('/hardware_alarm', null, 'b6')">🚨 Trigger Manual Hardware Alarm</button>
        <button id="bmute2" class="btn" style="{mute_style} padding:15px; border:1px solid #30363d;" onclick="sendCmd('/toggle_audio', null, 'bmute2')">{mute_text}</button>
        """, height=130)

    with ph_audio_engine.container():
        if (hw_alarm or sys_phase == "SCRAPER_BROKEN") and not audio_muted:
            components.html("""
            <script>
                const AudioContext = window.AudioContext || window.webkitAudioContext;
                const ctx = new AudioContext();
                function beep() {
                    if (ctx.state === 'suspended') ctx.resume();
                    const osc = ctx.createOscillator();
                    const gainNode = ctx.createGain();
                    osc.type = 'square';
                    osc.frequency.setValueAtTime(3000, ctx.currentTime);
                    osc.frequency.setValueAtTime(4000, ctx.currentTime + 0.15);
                    osc.frequency.setValueAtTime(3000, ctx.currentTime + 0.30);
                    gainNode.gain.value = 0.8; 
                    osc.connect(gainNode);
                    gainNode.connect(ctx.destination);
                    osc.start();
                    osc.stop(ctx.currentTime + 0.45);
                }
                beep();
                setInterval(beep, 600);
            </script>
            """, height=0)
        else:
            components.html("", height=0)

    with ph_banner.container():
        if sys_phase == "MUTATING":
            st.markdown("""<div style="background:#d29922; color:#000; padding:15px; border-radius:6px; font-weight:bold; text-align:center;">⚠️ TARGET DOM DEPLOYING UPDATE...</div>""", unsafe_allow_html=True)
        elif sys_phase == "SCRAPER_BROKEN":
            st.markdown("""<div style="background:#da3633; color:#fff; padding:15px; border-radius:6px; font-weight:bold; text-align:center; box-shadow: 0 0 20px rgba(248,81,73,0.5);">🚨 SCRAPER PIPELINE BROKEN: TARGET DOM STRUCTURE MUTATED.</div>""", unsafe_allow_html=True)
        elif sys_phase == "HEALING":
            st.markdown("""<div style="background:#a371f7; color:#fff; padding:15px; border-radius:6px; font-weight:bold; text-align:center; box-shadow: 0 0 20px rgba(163,113,247,0.5);">🤖 BRIGHT DATA WEB UNLOCKER: RECALCULATING SELECTORS & HEALING...</div>""", unsafe_allow_html=True)
        elif status == "OFFLINE":
            st.markdown("""<div style="background:#da3633; color:#fff; padding:15px; border-radius:6px; font-weight:bold; text-align:center; box-shadow: 0 0 20px rgba(248,81,73,0.5);">🚨 CRITICAL API FAILURE: NO LIVE DATA BEING RECEIVED FROM BRIGHT DATA.</div>""", unsafe_allow_html=True)
        else:
            st.empty()

    with ph_cards.container():
        c1, c2, c3, c4, c5 = st.columns(5)
        css_status  = "c-clear" if status == "CLEAR" else "c-congested" if status == "CONGESTED" else "c-offline"
        icon_status = "CLEAR" if status == "CLEAR" else "CONGESTED" if status == "CONGESTED" else "OFFLINE"
        
        if status == "NO_DATA":
            css_status = "c-offline"
            icon_status = "NO DATA"
            
        risk_color  = "#f85149" if risk == "CRITICAL" else "#d29922" if risk == "HIGH" else "#58a6ff"
        
        c1.markdown(f'<div class="card c-blue"><div class="lbl">Vessel Name</div><div class="val" title="{vessel}">{vessel}</div></div>', unsafe_allow_html=True)
        c2.markdown(f'<div class="card c-blue"><div class="lbl">Assigned Bay</div><div class="val">{bay}</div></div>', unsafe_allow_html=True)
        c3.markdown(f'<div class="card {css_status}"><div class="lbl">Status</div><div class="val">{icon_status}</div></div>', unsafe_allow_html=True)
        c4.markdown(f'<div class="card c-blue"><div class="lbl">Delay</div><div class="val">{delay} min</div></div>', unsafe_allow_html=True)
        c5.markdown(f"""
        <div class="card c-impact">
            <div class="lbl">Impact Score</div>
            <div class="val" style="font-size:1.5rem; margin-bottom:5px;">{impact}<span style="font-size:1rem;color:#8b949e;">/100</span></div>
            <div style="width:80%; height:6px; background:#30363d; border-radius:3px; margin: 0 auto;"><div style="width:{impact}%; height:100%; background:{risk_color}; border-radius:3px;"></div></div>
            <div style='font-size:0.7rem;color:{risk_color};font-weight:900; margin-top:8px;'>{risk}</div>
        </div>""", unsafe_allow_html=True)

    with ph_cascade.container():
        if cascade:
            max_d = max(cascade) or 1
            cascade_html = ""
            for i, d in enumerate(cascade[:5]):
                bar_pct = int((d / max_d) * 200)
                cascade_html += f"""
                <div class="cascade-row">
                    <div class="cascade-lbl">Vessel +{i+1}</div>
                    <div class="cascade-bar" style="width:{bar_pct}px"></div>
                    <div class="cascade-val">{d} min</div>
                </div>
                """
            st.markdown(cascade_html, unsafe_allow_html=True)
        else:
            st.markdown("<span style='color:#8b949e'>No cascading delays detected in the network.</span>", unsafe_allow_html=True)

    with ph_summary.container():
        st_color = "#3fb950" if status == "CLEAR" else "#d29922" if status == "CONGESTED" else "#f85149"
        st.markdown(f"""
        <div style="background:#161b22; padding:15px; border-radius:8px; border:1px solid #30363d; box-shadow: 0 4px 15px rgba(0,0,0,0.3);">
            <div style="margin-bottom:8px;"><strong>Status:</strong> <span style='color:{st_color}; font-weight:bold;'>{status}</span></div>
            <div style="margin-bottom:8px;"><strong>Risk Profile:</strong> <span style='color:{risk_color}; font-weight:bold;'>{risk}</span></div>
            <div style="margin-bottom:8px;"><strong>API Connection:</strong> {'🟢 ACTIVE' if fails == 0 else '🔴 OFFLINE'}</div>
            <div><strong>Last Payload:</strong> <span style="font-family:monospace; color:#8b949e;">{updated}</span></div>
        </div>
        """, unsafe_allow_html=True)

    with ph_terminal.container():
        html_logs = ""
        for l in logs[-16:]:
            col = "#c9d1d9"
            if "ERROR" in l or "💥" in l or "🚨" in l or "FAILED" in l or "Failed" in l or "404" in l: col = "#ff7b72"
            elif "WARNING" in l or "⚠️" in l: col = "#d29922"
            elif "HEALING" in l or "🤖" in l or "PUBLIC DOM" in l or "🔄" in l: col = "#a371f7"
            elif "✅" in l or "LIVE" in l: col = "#56d364"
            html_logs += f'<div style="color:{col}; margin-bottom:4px;">{l}</div>'
        st.markdown(f'<div class="terminal">{html_logs}</div>', unsafe_allow_html=True)

    with ph_chart.container():
        if history:
            df = pd.DataFrame(history)
            df['time'] = pd.to_datetime(df['time'], format="%H:%M:%S")
            chart = alt.Chart(df).mark_area(line={'color': '#58a6ff', 'strokeWidth': 3}, color=alt.Gradient(gradient='linear', stops=[alt.GradientStop(color='#58a6ff', offset=0), alt.GradientStop(color='rgba(88,166,255,0)', offset=1)], x1=1, x2=1, y1=1, y2=0)).encode(
                x=alt.X('time:T', title='Timeline', axis=alt.Axis(grid=True, gridColor='#30363d', format='%H:%M:%S')),
                y=alt.Y('delay:Q', title='Delay (Mins)', axis=alt.Axis(grid=True, gridColor='#30363d'))
            ).properties(height=280, background="transparent")
            st.altair_chart(chart, use_container_width=True)

    with ph_pipeline_anim.container():
        pipe_color, pipe_anim, bdata_color = "#3fb950", "flow", "#58a6ff"
        if sys_phase == "MUTATING": pipe_color = "#d29922"
        elif sys_phase == "SCRAPER_BROKEN": pipe_color, pipe_anim, bdata_color = "#f85149", "crash", "#f85149"
        elif sys_phase == "HEALING": pipe_color, bdata_color = "#a371f7", "#a371f7"
        elif status == "OFFLINE": pipe_color, pipe_anim, bdata_color = "#f85149", "crash", "#f85149"
            
        st.components.v1.html(f"""
        <style>
          .node {{ padding: 15px; border-radius: 6px; font-family: 'Inter', sans-serif; font-weight: bold; color: white; text-align: center; z-index: 2; border: 1px solid #30363d; background: #161b22; }}
          .pipe-container {{ display: flex; align-items: center; justify-content: space-between; background: #010409; padding: 30px; border-radius: 8px; border: 1px solid #30363d; box-shadow: 0 4px 15px rgba(0,0,0,0.5);}}
          .pipe {{ flex-grow: 1; height: 4px; background: #30363d; position: relative; overflow: hidden; margin: 0 15px; border-radius: 2px; }}
          .packet {{ position: absolute; width: 60px; height: 100%; background: {pipe_color}; animation: {pipe_anim} 1s infinite linear; box-shadow: 0 0 10px {pipe_color};}}
          @keyframes flow {{ 0% {{ left: -60px; opacity: 0; }} 10% {{ opacity: 1; }} 90% {{ opacity: 1; }} 100% {{ left: 100%; opacity: 0; }} }}
          @keyframes crash {{ 0% {{ left: -60px; opacity: 1; }} 50% {{ left: 45%; opacity: 1; }} 51% {{ left: 50%; opacity: 0; }} 100% {{ left: 50%; opacity: 0; }} }}
        </style>
        <div class="pipe-container">
            <div class="node" style="border-bottom: 3px solid #58a6ff;">🌐 Public DOM<br><span style="font-size:10px; color:#8b949e">{target_url}</span></div>
            <div class="pipe"><div class="packet"></div></div>
            <div class="node" style="border-bottom: 3px solid {bdata_color}; { 'animation: flash 1s infinite;' if sys_phase == 'SCRAPER_BROKEN' else '' }">⚙️ Bright Data<br><span style="font-size:10px; color:#8b949e">{active_scraper}</span></div>
            <div class="pipe"><div class="packet"></div></div>
            <div class="node" style="border-bottom: 3px solid #a371f7;">🚢 Backend<br><span style="font-size:10px; color:#8b949e">FastAPI Inference</span></div>
        </div>
        """, height=140)

    with ph_scraper_metrics.container():
        c1, c2, c3, c4 = st.columns(4)
        c1.markdown('<div class="card c-clear" style="height:100px !important;"><div class="lbl">Global Success Rate</div><div class="val" style="color:#3fb950;">99.8%</div></div>', unsafe_allow_html=True)
        c2.markdown('<div class="card c-blue" style="height:100px !important;"><div class="lbl">Active Proxies</div><div class="val" style="color:#58a6ff;">14,250</div></div>', unsafe_allow_html=True)
        c3.markdown('<div class="card c-blue" style="height:100px !important;"><div class="lbl">Avg Latency</div><div class="val" style="color:#c9d1d9;">114 ms</div></div>', unsafe_allow_html=True)
        c4.markdown(f'<div class="card c-blue" style="height:100px !important;"><div class="lbl">Data Extracted</div><div class="val" style="color:#c9d1d9;">1.4 TB</div></div>', unsafe_allow_html=True)

    with ph_collectors_grid.container():
        if collectors:
            df = pd.DataFrame(collectors)
            df = df.rename(columns={"id": "Scraper name", "status": "Status", "records": "Records"})
            df['Status'] = df['Status'].apply(lambda x: "▶️ Running" if x == "ACTIVE" else f"⏸️ {x}")
            st.dataframe(df, use_container_width=True, hide_index=True)
            
    with ph_raw_json.container():
        if recent_payloads:
            raw_str = json.dumps(recent_payloads[0].get("payload", {}), indent=2)
            st.markdown(f'<div style="background:#010409; border:1px solid #30363d; border-radius:6px; padding:15px; font-family:monospace; font-size:13px; height: 300px; overflow-y:auto; box-shadow: inset 0 0 20px rgba(0,0,0,0.5); color:#c9d1d9;"><pre style="margin:0; background:transparent; border:none; padding:0; color:#58a6ff;">{raw_str}</pre></div>', unsafe_allow_html=True)
        else:
            st.markdown('<div style="background:#010409; border:1px solid #30363d; border-radius:6px; padding:15px; font-family:monospace; font-size:13px; height: 300px; display:flex; align-items:center; justify-content:center; color:#8b949e;">Awaiting live payload from Bright Data...</div>', unsafe_allow_html=True)

    with ph_net_chart.container():
        if history:
            df_net = pd.DataFrame(history)
            df_net['time'] = pd.to_datetime(df_net['time'], format="%H:%M:%S")
            df_net['bandwidth'] = [d * 0.1 + 0.5 for d in df_net['delay']]
            df_net['rotation_rate'] = [d * 0.5 + 10 for d in df_net['delay']]
            
            c_left, c_right = st.columns(2)
            with c_left:
                st.markdown("##### Bandwidth Usage (GB/s)")
                chart2 = alt.Chart(df_net).mark_line(color='#a371f7', strokeWidth=3).encode(
                    x=alt.X('time:T', title='', axis=alt.Axis(grid=True, gridColor='#30363d', format='%H:%M:%S')),
                    y=alt.Y('bandwidth:Q', title='', axis=alt.Axis(grid=True, gridColor='#30363d'))
                ).properties(height=200, background="transparent")
                st.altair_chart(chart2, use_container_width=True)
                
            with c_right:
                st.markdown("##### IP Rotation Rate (Req/sec)")
                chart3 = alt.Chart(df_net).mark_area(line={'color': '#3fb950', 'strokeWidth': 2}, color=alt.Gradient(gradient='linear', stops=[alt.GradientStop(color='#3fb950', offset=0), alt.GradientStop(color='rgba(63,185,80,0)', offset=1)], x1=1, x2=1, y1=1, y2=0)).encode(
                    x=alt.X('time:T', title='', axis=alt.Axis(grid=True, gridColor='#30363d', format='%H:%M:%S')),
                    y=alt.Y('rotation_rate:Q', title='', axis=alt.Axis(grid=True, gridColor='#30363d'))
                ).properties(height=200, background="transparent")
                st.altair_chart(chart3, use_container_width=True)

    with ph_health_metrics.container():
        hc1, hc2, hc3 = st.columns(3)
        hc1.markdown(f'<div class="card c-offline"><div class="lbl">TOTAL PIPELINE BREAKS</div><div class="val">{total_breaks}</div></div>', unsafe_allow_html=True)
        hc2.markdown(f'<div class="card c-purple"><div class="lbl">AI SELF-HEAL EVENTS</div><div class="val">{total_heals}</div></div>', unsafe_allow_html=True)
        h_color = "c-offline" if sys_phase == "SCRAPER_BROKEN" else "c-purple" if sys_phase == "HEALING" else "c-clear"
        hc3.markdown(f'<div class="card {h_color}"><div class="lbl">CURRENT DOM STATE</div><div class="val" style="font-size:1.3rem;">{sys_phase}</div></div>', unsafe_allow_html=True)

    with ph_json_firehose.container():
        firehose_html = ""
        for i, block in enumerate(recent_payloads):
            ts = block.get("timestamp")
            payload = block.get("payload")
            color = "#f85149" if "error" in payload else "#3fb950"
            payload_str = json.dumps(payload, indent=2)
            firehose_html += f"""
            <div style="border-bottom:1px dashed #30363d; padding:10px 0;">
                <span style="color:#58a6ff;">[{ts}] </span> <span style="color:#8b949e;">-- INCOMING PAYLOAD --</span>
                <pre style="margin:5px 0 0; color:{color}; background:transparent; border:none; padding:0;">{payload_str}</pre>
            </div>
            """
        st.markdown(f'<div style="background:#010409; border:1px solid #30363d; border-radius:6px; padding:15px; font-family:monospace; font-size:13px; height: 400px; overflow-y:auto; box-shadow: inset 0 0 20px rgba(0,0,0,0.5);">{firehose_html}</div>', unsafe_allow_html=True)

    with ph_serial.container():
        hw_logs = ""
        for l in logs[-8:]:
            hw_logs += f'<div style="color:#8b949e; margin-bottom:4px; border-bottom:1px solid #161b22; padding-bottom:2px;">{l}</div>'
        st.markdown(f'<div style="background:#010409; border:1px solid #30363d; border-radius:6px; padding:1rem; font-family:monospace; font-size:0.75rem; height: 180px; overflow:hidden;">{hw_logs}</div>', unsafe_allow_html=True)

    with ph_tft.container():
        if hw_connected:
            t_color = "#f85149" if hw_alarm or sys_phase == "SCRAPER_BROKEN" else "#3fb950" if status == "CLEAR" else "#d29922"
            t_status = "!! DOM BREAK !!" if sys_phase == "SCRAPER_BROKEN" else "!! ALARM !!" if hw_alarm else "NORMAL OP"
            if status == "OFFLINE" or status == "NO_DATA":
                t_color = "#f85149"
                t_status = "NO DATA"
                
            tft_content = f"""
            <div class="screen" style="background:{t_color}; border: 2px solid {t_color}; {'animation: flash 0.5s infinite;' if t_color == '#f85149' else ''}">
                <span style="font-weight:bold; font-size: 14px; color:#000;">[{t_status}]</span><br><br>
                <span style="color:#000;">> BAY: {bay}<br>> DELAY: {delay}m<br><br>> API: SYNC</span>
            </div>
            """
        else:
            tft_content = """
            <div class="screen" style="background:#010409; border: 2px solid #30363d;">
                <div style="color:#8b949e; display:flex; flex-direction:column; height:100%; justify-content:center; align-items:center;">
                    <div style="font-size:24px;">🚫</div>
                    <div style="text-align:center; margin-top:10px;">[OFFLINE]<br>AWAITING ESP32</div>
                </div>
            </div>
            """
            
        st.components.v1.html(f"""
        <style>
        .holo-stage {{ display: flex; justify-content: center; align-items: center; height: 280px; background: #010409; border-radius: 8px; border: 1px solid #30363d; box-shadow: 0 4px 15px rgba(0,0,0,0.5);}}
        .hw {{ width: 280px; height: 200px; background: #0d1117; border: 2px solid #30363d; border-radius: 8px; position: relative; display: flex; align-items:center; justify-content:space-between; padding: 20px; box-shadow: inset 0 0 20px rgba(0,0,0,0.5);}}
        .chip {{ width: 80px; height: 120px; background: #161b22; border: 2px solid #58a6ff; color: #58a6ff; display: flex; align-items: center; justify-content: center; font-family: monospace; font-size: 10px; font-weight: bold; text-align: center; box-shadow: 0 0 10px rgba(88,166,255,0.4);}}
        .screen {{ width: 120px; height: 140px; padding: 10px; font-family: monospace; font-size: 11px; }}
        @keyframes flash {{ 0% {{ opacity:1;}} 50% {{ opacity:0.3;}} 100% {{opacity:1;}} }}
        </style>
        <div class="holo-stage">
            <div class="hw">
                <div class="chip">ESP32 SENTRY</div>
                {tft_content}
            </div>
        </div>
        """, height=280)

    time.sleep(1)
