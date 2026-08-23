"""
AeroPort CargoGrid – FastAPI Backend Core
"""
import asyncio
import logging
import os
import time
import random
from contextlib import asynccontextmanager
from datetime import datetime, timezone, timedelta
from typing import Optional
from pydantic import BaseModel

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from brightdata_client import BrightDataClient

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("aeroport")

LOG_BUFFER: list[str] = []
class TerminalBufferHandler(logging.Handler):
    def emit(self, record: logging.LogRecord) -> None:
        LOG_BUFFER.append(self.format(record))
        if len(LOG_BUFFER) > 100: LOG_BUFFER.pop(0)

_bh = TerminalBufferHandler()
_bh.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
logging.getLogger().addHandler(_bh)

BRIGHTDATA_API_KEY      = os.environ.get("BRIGHTDATA_API_KEY", "85795523-3150-4c38-ad57-0bad18050567")
POLL_INTERVAL_SECONDS   = 2 

bd_client = BrightDataClient(api_key=BRIGHTDATA_API_KEY)

def generate_initial_history():
    hist = []
    now = datetime.now(timezone.utc)
    for i in range(30, 0, -1):
        ts = now - timedelta(seconds=i*POLL_INTERVAL_SECONDS)
        hist.append({"time": ts.strftime("%H:%M:%S"), "delay": 0})
    return hist

class AppState:
    vessel_name:          str           = "Awaiting Pipeline Sync..."
    bay_id:               str           = "---"
    status:               str           = "INITIALIZING"
    delay_minutes:        int           = 0
    raw_message:          str           = "Booting secure connection..."
    last_updated:         Optional[str] = None
    scraper_healthy:      bool          = False
    consecutive_failures: int           = 0
    impact_score:         int           = 0
    risk_level:           str           = "LOW"
    cascading_delays:     list[float]   = []
    hardware_alarm:       bool          = False
    
    system_phase:         str           = "NORMAL" 
    scraper_paused:       bool          = False
    
    active_scraper:       str           = "c_mt4su8bs1cavzw7gss"
    audio_muted:          bool          = False
    
    history:              list[dict]    = generate_initial_history()
    collectors:           list[dict]    = [
        {"id": "c_mt4su8bs1cavzw7gss", "name": "c_mt4su8bs1cavzw7gss", "status": "ACTIVE", "records": "16.1K"},
        {"id": "cli-scraper-1787431404", "name": "cli-scraper-1787431404", "status": "STANDBY", "records": "25"},
        {"id": "cli-scraper-1787431255", "name": "cli-scraper-1787431255", "status": "STANDBY", "records": "75"},
        {"id": "cli-scraper-1787428800", "name": "cli-scraper-1787428800", "status": "STANDBY", "records": "0"}
    ]
    
    total_pipeline_breaks: int = 0
    total_pipeline_heals: int = 0
    last_hw_sync_time: float = 0.0
    recent_payloads: list[dict] = []

app_state = AppState()

def calculate_impact_score(delay_minutes: int, status: str) -> dict:
    if status in ("OFFLINE", "INITIALIZING", "NO_DATA") or delay_minutes <= 0:
        return {"impact_score": 0, "cascading_delays": [], "risk_level": "LOW"}
    cascading = []
    curr = float(delay_minutes)
    for _ in range(8):
        curr *= 0.65
        cascading.append(round(curr, 1))
    total = delay_minutes + sum(cascading)
    max_p = delay_minutes * (1 + sum(0.65**i for i in range(1, 9)))
    score = min(100, round((total / max_p) * 100)) if max_p > 0 else 0
    risk = "CRITICAL" if score >= 75 else "HIGH" if score >= 50 else "MEDIUM" if score >= 25 else "LOW"
    return {"impact_score": score, "cascading_delays": cascading, "risk_level": risk}

def update_history(delay: int):
    now = datetime.now(timezone.utc).strftime("%H:%M:%S")
    app_state.history.append({"time": now, "delay": delay})
    if len(app_state.history) > 60:
        app_state.history.pop(0)

# AUTOMATIC BREAK/HEAL LIFECYCLE
async def auto_mutation_lifecycle():
    await asyncio.sleep(15) # Wait for initial boot
    while True:
        # Run normally for 25 seconds
        await asyncio.sleep(25)
        
        if app_state.system_phase == "NORMAL" and not app_state.scraper_paused:
            log.warning("⚠️ AUTOMATIC DOM MUTATION TRIGGERED ON TARGET SITE...")
            app_state.system_phase = "SCRAPER_BROKEN"
            app_state.hardware_alarm = True
            app_state.total_pipeline_breaks += 1
            
            # Stay broken for 8 seconds so user can see it
            await asyncio.sleep(8)
            
            if app_state.system_phase == "SCRAPER_BROKEN": # Ensure it wasn't manually overridden
                log.info("🤖 INITIATING AUTOMATIC AI SELF-HEAL SEQUENCE...")
                app_state.system_phase = "HEALING"
                app_state.hardware_alarm = False
                app_state.total_pipeline_heals += 1
                
                # Heal for 6 seconds
                await asyncio.sleep(6)
                
                app_state.system_phase = "NORMAL"
                log.info("✅ PIPELINE RESTORED AUTOMATICALLY.")


async def continuous_scraper_loop() -> None:
    await asyncio.sleep(2) 
    log.info("🚀 Agent: Starting DGX Pipeline. Scraper running.")

    while True:
        if app_state.scraper_paused:
            app_state.status = "PAUSED"
            await asyncio.sleep(POLL_INTERVAL_SECONDS)
            continue
            
        try:
            if app_state.system_phase == "SCRAPER_BROKEN":
                raise Exception("DOM Class Mutated: '.vessel-row' -> '.v-row-x8'")
                
            force_fail = (app_state.system_phase == "MUTATING")
            record = await bd_client.trigger_scraper(app_state.active_scraper, force_fail=force_fail)
            
            if app_state.active_scraper == "cli-scraper-1787428800":
                vn    = "[8800] NO RECORDS FOUND"
                bay   = "N/A"
                delay = 0
                sts   = "NO_DATA"
                msg   = "Selected Collector Database is Empty."
                record = {"error": "Collector has 0 records"}
            else:
                vn    = record.get("vessel_name", "UNKNOWN")
                bay   = record.get("bay_id", "N/A")
                delay = int(record.get("delay_minutes", 0))
                sts   = record.get("status", "CONGESTED")
                if app_state.active_scraper != "c_mt4su8bs1cavzw7gss":
                    vn = f"[{app_state.active_scraper[-4:]}] {vn}"
                msg   = f"Delay: {delay} min" if delay > 0 else "Schedule: ON TIME"
            
            if app_state.hardware_alarm:
                sts = "OFFLINE"
                msg = "CRITICAL HARDWARE ALARM TRIGGERED"
                delay = 999
            
            analytics = calculate_impact_score(delay if not app_state.hardware_alarm else 0, sts)
            
            app_state.vessel_name          = vn
            app_state.bay_id               = bay
            app_state.status               = sts
            app_state.delay_minutes        = delay
            app_state.raw_message          = msg
            app_state.scraper_healthy      = True
            app_state.consecutive_failures = 0
            app_state.last_updated         = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
            app_state.impact_score         = analytics["impact_score"] if not app_state.hardware_alarm else 100
            app_state.risk_level           = analytics["risk_level"] if not app_state.hardware_alarm else "CRITICAL"
            app_state.cascading_delays     = analytics["cascading_delays"]
            
            app_state.recent_payloads.insert(0, {"timestamp": app_state.last_updated, "payload": record})
            if len(app_state.recent_payloads) > 15: app_state.recent_payloads.pop()
            
            update_history(delay if delay != 999 else 0)

        except Exception as exc:
            app_state.consecutive_failures += 1
            app_state.scraper_healthy       = False
            app_state.status                = "OFFLINE"
            app_state.raw_message           = f"SCRAPER EXCEPTION: {str(exc)}"
            app_state.impact_score          = 100 
            app_state.risk_level            = "CRITICAL"
            app_state.cascading_delays      = []
            app_state.hardware_alarm        = True # FORCE ALARM ON ANY REAL FAILURE
            
            err_record = {"timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"), "payload": {"error": str(exc), "status": "PIPELINE_BROKEN", "reason": "DOM Mutation / API Failure Detected"}}
            app_state.recent_payloads.insert(0, err_record)
            if len(app_state.recent_payloads) > 15: app_state.recent_payloads.pop()
            
            update_history(0)
            
        await asyncio.sleep(POLL_INTERVAL_SECONDS)

@asynccontextmanager
async def lifespan(app: FastAPI):
    task1 = asyncio.create_task(continuous_scraper_loop())
    task2 = asyncio.create_task(auto_mutation_lifecycle())
    yield
    task1.cancel()
    task2.cancel()

app = FastAPI(title="AeroPort CargoGrid - DGX Solo Edition", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

@app.get("/target_site", response_class=HTMLResponse)
async def get_target_site():
    """Returns a fully working, dynamically updating HTML website mimicking the target scraping domain."""
    mutation_active = "true" if app_state.system_phase in ["SCRAPER_BROKEN", "HEALING"] else "false"
    
    html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Global Maritime Data Provider</title>
        <style>
            body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f4f6f9; color: #333; padding: 20px; }}
            .header {{ background-color: #002147; color: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }}
            .table-container {{ background: white; padding: 20px; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }}
            table {{ width: 100%; border-collapse: collapse; margin-top: 10px; }}
            th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }}
            th {{ background-color: #f8f9fa; color: #555; }}
            tr:hover {{ background-color: #f1f3f5; }}
            .status-clear {{ color: #28a745; font-weight: bold; }}
            .status-delay {{ color: #ffc107; font-weight: bold; }}
            .mutation-banner {{ background: #dc3545; color: white; padding: 15px; border-radius: 8px; text-align: center; font-weight: bold; display: none; margin-bottom: 20px; animation: flash 1s infinite; }}
            @keyframes flash {{ 0% {{ opacity:1;}} 50% {{ opacity:0.7;}} 100% {{opacity:1;}} }}
        </style>
    </head>
    <body>
        <div class="mutation-banner" id="mutBanner">
            🚨 ADMINISTRATOR NOTICE: WEBSITE DOM STRUCTURE HAS BEEN UPDATED (v2.4.1) 🚨
        </div>
        <div class="header">
            <h1 style="margin: 0;">MarineData Live Schedule</h1>
            <p style="margin: 5px 0 0;">Public Vessel Tracking API Source</p>
        </div>
        <div class="table-container">
            <h3 style="margin-top:0;">Real-Time Bay Arrivals</h3>
            <p>Last updated: <span id="clock"></span></p>
            <table id="vesselTable">
                <thead>
                    <tr>
                        <th class="col-name">Vessel Name</th>
                        <th class="col-bay">Assigned Bay</th>
                        <th class="col-status">Status</th>
                        <th class="col-delay">Delay (Min)</th>
                    </tr>
                </thead>
                <tbody id="tableBody">
                    <!-- Javascript populates this to prove live updates -->
                </tbody>
            </table>
        </div>
        
        <script>
            const isMutated = {mutation_active};
            if(isMutated) {{
                document.getElementById('mutBanner').style.display = 'block';
                // Mutate the DOM structure to break the scraper
                document.querySelector('table').className = "new-table-layout-v2";
                document.querySelectorAll('th').forEach(th => th.className = "obfuscated-header-" + Math.random().toString(36).substring(7));
            }}
            
            function updateData() {{
                document.getElementById('clock').innerText = new Date().toLocaleTimeString();
                const vessels = ["MSC Isabella", "CMA CGM Jacques", "Ever Given", "HMM Algeciras", "OOCL Hong Kong"];
                const bays = ["BAY-01", "BAY-12", "BAY-04", "BAY-08", "BAY-22"];
                let html = "";
                for(let i=0; i<3; i++) {{
                    const v = vessels[Math.floor(Math.random() * vessels.length)];
                    const b = bays[Math.floor(Math.random() * bays.length)];
                    const delay = Math.random() > 0.6 ? Math.floor(Math.random() * 120) : 0;
                    const status = delay > 0 ? `<span class="status-delay">DELAYED</span>` : `<span class="status-clear">ON TIME</span>`;
                    
                    // If mutated, render with weird classes that break simple scrapers
                    const trClass = isMutated ? "data-row-x891" : "vessel-row";
                    html += `<tr class="${{trClass}}"><td>${{v}}</td><td>${{b}}</td><td>${{status}}</td><td>${{delay}}</td></tr>`;
                }}
                document.getElementById('tableBody').innerHTML = html;
            }}
            
            updateData();
            setInterval(updateData, 3000);
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html)


@app.get("/status")
async def get_status(request: Request):
    hw_connected = (time.time() - app_state.last_hw_sync_time) < 10 # 10 seconds timeout
    return {
        "vessel_name": app_state.vessel_name,
        "bay_id": app_state.bay_id,
        "status": app_state.status,
        "delay_minutes": app_state.delay_minutes,
        "message": app_state.raw_message,
        "scraper_healthy": app_state.scraper_healthy,
        "last_updated": app_state.last_updated,
        "consecutive_failures": app_state.consecutive_failures,
        "impact_score": app_state.impact_score,
        "risk_level": app_state.risk_level,
        "cascading_delays": app_state.cascading_delays,
        "history": app_state.history,
        "collectors": app_state.collectors,
        "hardware_alarm": app_state.hardware_alarm,
        "system_phase": app_state.system_phase,
        "scraper_paused": app_state.scraper_paused,
        "active_scraper": app_state.active_scraper,
        "target_url": "http://127.0.0.1:8000/target_site",
        "total_breaks": app_state.total_pipeline_breaks,
        "total_heals": app_state.total_pipeline_heals,
        "recent_payloads": app_state.recent_payloads,
        "hw_connected": hw_connected,
        "audio_muted": app_state.audio_muted
    }

@app.get("/esp32")
async def esp32_sync():
    app_state.last_hw_sync_time = time.time()
    return {
        "vessel_name": app_state.vessel_name,
        "bay_id": app_state.bay_id,
        "status": app_state.status,
        "delay_minutes": app_state.delay_minutes,
        "alarm": app_state.hardware_alarm or app_state.system_phase == "SCRAPER_BROKEN"
    }

@app.get("/logs")
async def get_logs():
    return {"lines": list(LOG_BUFFER)}

@app.post("/hardware_alarm")
async def hardware_alarm():
    app_state.hardware_alarm = True
    return {"triggered": True}

@app.post("/toggle_audio")
async def toggle_audio():
    app_state.audio_muted = not app_state.audio_muted
    return {"muted": app_state.audio_muted}

@app.post("/toggle_scraper")
async def toggle_scraper():
    app_state.scraper_paused = not app_state.scraper_paused
    for c in app_state.collectors:
        if c["id"] == app_state.active_scraper:
            c["status"] = "PAUSED" if app_state.scraper_paused else "ACTIVE"
    return {"paused": app_state.scraper_paused}

class ScraperInput(BaseModel):
    scraper_id: str

@app.post("/switch_scraper")
async def switch_scraper(data: ScraperInput):
    app_state.active_scraper = data.scraper_id
    app_state.scraper_paused = False 
    app_state.system_phase = "NORMAL" 
    app_state.hardware_alarm = False
    log.info(f"🔄 Switched active data collector to: {data.scraper_id}. Scraper STARTED.")
    for c in app_state.collectors:
        c["status"] = "ACTIVE" if c["id"] == data.scraper_id else "STANDBY"
    return {"msg": f"Switched to {data.scraper_id}"}

class CommandInput(BaseModel):
    command: str

async def delayed_auto_heal():
    await asyncio.sleep(8)
    if app_state.system_phase == "SCRAPER_BROKEN":
        log.info("🤖 INITIATING AUTOMATIC AI SELF-HEAL SEQUENCE (Post-Manual Break)...")
        app_state.system_phase = "HEALING"
        app_state.hardware_alarm = False
        app_state.total_pipeline_heals += 1
        await asyncio.sleep(6)
        if app_state.system_phase == "HEALING":
            app_state.system_phase = "NORMAL"
            log.info("✅ PIPELINE RESTORED AUTOMATICALLY.")

@app.post("/terminal_command")
async def terminal_command(cmd: CommandInput):
    c = cmd.command.strip().lower()
    log.info(f"💻 [Terminal Input] -> {c}")
    
    if c == "fail":
        app_state.total_pipeline_breaks += 1
        log.warning(f"🌐 PUBLIC TARGET ({bd_client.target_url}) DEPLOYING UPDATE...")
        app_state.system_phase = "SCRAPER_BROKEN"
        app_state.hardware_alarm = True
        asyncio.create_task(delayed_auto_heal())
        return {"msg": "Forced target DOM mutation. Auto-heal scheduled."}
        
    elif c == "heal":
        app_state.total_pipeline_heals += 1
        log.info("🤖 INITIATING BRIGHT DATA AI WEB UNLOCKER / MANUAL SELF-HEAL...")
        app_state.system_phase = "HEALING"
        app_state.hardware_alarm = False
        asyncio.create_task(trigger_full_restore())
        return {"msg": "AI Web Unlocker sequence initiated."}
        
    elif c == "pause":
        app_state.scraper_paused = True
        return {"msg": "Scraper pipeline paused."}
    elif c == "start":
        app_state.scraper_paused = False
        return {"msg": "Scraper pipeline started."}
    else:
        return {"msg": f"Command logged: {c}"}

async def trigger_full_restore():
    await asyncio.sleep(4)
    app_state.system_phase = "NORMAL"
    log.info("✅ SELECTORS RECALCULATED. PIPELINE RESTORED.")
