# 🚢 AeroPort CargoGrid DGX

**Autonomous Edge-to-Cloud Maritime Logistics Command Center**  
*Solo Submission for the Scrape-Verse Hackathon (Best Use of Bright Data Track) - NVIDIA DGX Spark*

---

## 🌍 The Problem
Global maritime supply chains bleed billions to cascading delays because port operators rely on static, opaque data. When target domain structures mutate, standard scrapers break, logistics halt, and floor operators are left in the dark until engineers patch the pipeline.

## 🚀 The Solution
**AeroPort CargoGrid DGX** eradicates data latency by bridging Bright Data’s cloud extraction infrastructure directly to physical IoT edge hardware. It acts as an autonomous coding agent that not only extracts and normalizes live maritime data but actively monitors pipeline health and triggers physical hardware alarms on the factory floor when the web mutates.

---

## 🏗️ Architecture & The Bright Data Rubric

### 1. The Custom Scraper (Scraper Studio)
We engineered a custom collector (`c_mt4su8bs1cavzw7gss`) inside **Bright Data’s Scraper Studio**. By leveraging Bright Data's proxy infrastructure, the scraper effortlessly bypasses severe bot protections to extract live maritime entities (vessel names, coordinates, and logistics data) from highly volatile public domains.

### 2. The Coding Agent (FastAPI)
Data is useless if it’s dormant. An autonomous **Python FastAPI daemon** acts as the central coding agent. It continuously orchestrates the proxy network, polls the completed Scraper Studio datasets, and aggressively normalizes the nested JSON payloads into a strict downstream schema. 

### 3. DOM Mutation & AI Self-Healing
The web is volatile. When target sites mutate, the FastAPI agent instantly detects the schema invalidation. It drops the UI into a critical state and **autonomously triggers a physical ESP32 hardware SOS alarm**. Instead of waiting hours for an engineer, the system simulates the deployment of **Bright Data’s AI Web Unlocker** to dynamically recalculate broken selectors, patch the pipeline, and silence the hardware sentry.

### 4. Structured Output to the Edge (Streamlit + ESP32)
The structured JSON output powers two endpoints simultaneously:
1. **The Digital Command Center:** A zero-flicker Streamlit dashboard providing real-time data visualization, JSON firehose logs, and pipeline control.
2. **The Physical Edge Sentry:** An ESP32 microcontroller acting as a perfect digital twin, receiving live web telemetry and physically alerting operators via a TFT screen and Piezo buzzer.

---

## 🔌 Hardware Deployment Schematic (ESP32)

The physical edge node requires the following GPIO wiring:

```text
[ESP32 Sentry Node]
 ├── TFT_CS   -> GPIO 5
 ├── TFT_RST  -> GPIO 4
 ├── TFT_DC   -> GPIO 2
 ├── TFT_MOSI -> GPIO 23
 ├── TFT_SCLK -> GPIO 18
 └── PIEZO    -> GPIO 15
```

---

## 💻 How to Run Locally

### 1. Start the FastAPI Agent (Backend)
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000
```

### 2. Start the Command Center (Frontend)
```bash
cd backend
streamlit run streamlit_app.py
```

### 3. Flash the ESP32 (Hardware)
Upload the `ESP32_AeroPort_Sentry.ino` firmware to your ESP32 board via the Arduino IDE. Ensure the board is connected to the same local Wi-Fi network as the FastAPI server.

---

*Built with Python, FastAPI, Streamlit, C++, and Bright Data.*
