# CardioTwin AI — Hardware Integration PRD

**Version:** 1.0 | **Date:** February 21, 2026 | **Owner:** Hardware Engineer (Person 1)
**Status:** FINAL — Ready for Build

---

## 1. Purpose

This document is the **single source of truth** for the hardware engineer building the CardioTwin sensor station. It covers every component, every wire, every pin, the complete firmware logic, and — critically — the exact API contract the hardware must speak to integrate with the backend already built in the `Techdee1/Kardio-Twin` repository.

---

## 2. Existing Backend Integration Points

The backend is already built. Here's what the hardware needs to talk to:

### 2.1 Backend Architecture (Already Built)

```
Techdee1/Kardio-Twin Repository
├── main.py                     ← FastAPI entry point
├── config.py                   ← Settings (DB URL, calibration threshold=15)
├── routers/
│   ├── readingRouter.py        ← POST /api/reading (YOUR main target)
│   └── sessionRouter.py        ← POST /api/session/start
├── ai_engine/
│   ├── engine.py               ← CardioTwinEngine (session + scoring orchestrator)
│   ├── scoring.py              ← Score functions (HR 25%, HRV 40%, SpO₂ 20%, Temp 15%)
│   ├── baseline.py             ← Baseline calibration (first 15 readings, IQR outlier removal)
│   ├── zones.py                ← Zone classification (GREEN/YELLOW/ORANGE/RED)
│   ├── anomaly.py              ← Alert detection (sudden drops, sustained decline, etc.)
│   ├── nudges.py               ← Groq-powered nudge generation (multi-language)
│   ├── validation.py           ← Input validation (range checks, NaN detection)
│   ├── projection.py           ← What-if risk projections
│   └── api.py                  ← CardioTwinAPI facade (backend imports this)
├── service/
│   ├── readingService.py       ← Stores readings in DB + legacy scoring
│   └── sessionService.py       ← Session CRUD operations
├── dtos/
│   ├── readingsDto.py          ← Pydantic models for reading requests/responses
│   └── sessionDto.py           ← Pydantic models for session requests/responses
├── model/
│   └── dataModel.py            ← SQLAlchemy DB models
└── repository/
    └── database.py             ← Database connection (SQLite default)
```

### 2.2 API Endpoints the Hardware Talks To

The hardware ONLY makes HTTP POST requests to **one endpoint**:

| Endpoint | Method | Purpose |
|---|---|---|
| `POST /api/reading` | POST | Send biometric data every 2 seconds |

The backend internally handles:
- Input validation (`ai_engine/validation.py` — range: BPM 30-220, HRV 0-200, SpO₂ 70-100, Temp 30-42°C)
- Baseline calibration (`ai_engine/baseline.py` — first 15 readings, IQR outlier removal)
- Score calculation (`ai_engine/scoring.py` — weighted composite)
- Zone classification (`ai_engine/zones.py` — GREEN/YELLOW/ORANGE/RED)
- Anomaly detection (`ai_engine/anomaly.py` — sudden drops, sustained decline, SpO₂ critical)
- AI nudge generation (`ai_engine/nudges.py` — Groq LLM, multi-language)
- WhatsApp/SMS alerts (`routers/readingRouter.py` — Twilio integration)

**The hardware is DUMB by design. It reads sensors, sends JSON, and checks the response. That's it.**

---

## 3. API Contract (Exact Match to Backend)

### 3.1 Request — What Hardware Sends

The backend's `readingsDto.BiometricReadingRequest` Pydantic model expects:

```json
{
  "bpm": 72,
  "hrv": 42.3,
  "spo2": 98.1,
  "temperature": 36.4,
  "timestamp": 45000,
  "session_id": "demo"
}
```

| Field | Type | Valid Range | Source |
|---|---|---|---|
| `bpm` | int/float | 30–220 | MAX30102 (beat detection algorithm) |
| `hrv` | float | 0–200 | Calculated RMSSD from beat intervals |
| `spo2` | float | 70–100 | MAX30102 RED/IR ratio approximation |
| `temperature` | float | 30.0–42.0 | NTC thermistor via voltage divider |
| `timestamp` | int | ≥ 0 | `millis()` since ESP32 boot |
| `session_id` | string | any | Fixed to `"demo"` for hackathon |

**⚠️ CRITICAL:** If any value is outside the valid range, the backend's `validation.py` will reject it. The firmware MUST clamp or filter values before sending.

### 3.2 Response — What Hardware Receives

**During Calibration (first 15 readings):**
```json
{
  "status": "calibrating",
  "readings_collected": 8,
  "readings_needed": 15,
  "alert": false
}
```

**After Calibration (scored):**
```json
{
  "status": "scored",
  "score": 86.2,
  "zone": "GREEN",
  "zone_label": "Thriving",
  "zone_emoji": "🟢",
  "alert": false,
  "nudge_sent": false,
  "components": {
    "heart_rate": { "value": 72, "score": 95.2 },
    "hrv": { "value": 42.3, "score": 88.1 },
    "spo2": { "value": 98.1, "score": 100.0 },
    "temperature": { "value": 36.4, "score": 93.5 }
  },
  "baseline": {
    "resting_bpm": 71.5,
    "resting_hrv": 43.1,
    "normal_spo2": 98.0,
    "normal_temp": 36.35
  }
}
```

**Hardware only cares about ONE field in the response:**
```
"alert": true/false
```
- `true` → BUZZ the vibration motor + RED LED flash
- `false` → GREEN LED blink (data sent OK)

---

## 4. Hardware Components

### 4.1 Bill of Materials

| # | Component | Specification | Purpose | Est. Cost |
|---|---|---|---|---|
| 1 | ESP32-WROOM-32 Dev Board | 240MHz dual-core, WiFi+BLE | Microcontroller | ~₦3,500 |
| 2 | MAX30102 Module | I2C, 3.3V, PPG sensor | Heart Rate, HRV, SpO₂ | ~₦2,000 |
| 3 | 10kΩ NTC Thermistor | Bead type, B=3950 | Skin Temperature | ~₦300 |
| 4 | 10kΩ Resistor | ¼W, ±5% | Voltage divider for NTC | ~₦50 |
| 5 | Green LED | 3mm or 5mm | "Data Sent OK" indicator | ~₦50 |
| 6 | Red LED | 3mm or 5mm | "Error / No Finger" indicator | ~₦50 |
| 7 | 220Ω Resistors (×2) | ¼W | LED current limiting | ~₦50 |
| 8 | 2N2222 NPN Transistor | TO-92 package | Motor driver switch | ~₦100 |
| 9 | 1kΩ Resistor | ¼W | Transistor base resistor | ~₦30 |
| 10 | Mini Vibration Motor | 3V coin type | Haptic alert | ~₦500 |
| 11 | Breadboard | Half-size or full | Assembly | ~₦500 |
| 12 | Jumper Wires (M-M) | ~20 pieces | Connections | ~₦300 |
| 13 | Micro-USB Cable | Data-capable | Power + programming | ~₦500 |
| | **TOTAL** | | | **~₦7,930 (~$10)** |

---

## 5. Pin Assignment

```
┌─────────────────────────────────────────────────────────┐
│              ESP32-WROOM-32 PIN MAP                     │
├──────────────┬──────────────┬───────────────────────────┤
│  ESP32 PIN   │  CONNECTS TO │  FUNCTION                 │
├──────────────┼──────────────┼───────────────────────────┤
│  3.3V        │  Power rail  │  All component power      │
│  GND         │  Ground rail │  All component ground     │
│  GPIO 21     │  MAX30102 SDA│  I2C Data                 │
│  GPIO 22     │  MAX30102 SCL│  I2C Clock                │
│  GPIO 34     │  NTC junction│  ADC temp reading         │
│  GPIO 25     │  1kΩ→2N2222  │  Vibration motor control  │
│  GPIO 26     │  220Ω→Green  │  Data-sent LED            │
│  GPIO 27     │  220Ω→Red    │  Error/no-finger LED      │
└──────────────┴──────────────┴───────────────────────────┘
```

---

## 6. Wiring Diagrams

### 6.1 MAX30102 (Heart Rate + SpO₂)

```
ESP32 3.3V ──────── MAX30102 VIN
ESP32 GND  ──────── MAX30102 GND
ESP32 GPIO 21 ───── MAX30102 SDA
ESP32 GPIO 22 ───── MAX30102 SCL

NOTES:
• Use 3.3V, NOT 5V
• Keep I2C wires SHORT (< 10cm)
• GPIO 21/22 are DEFAULT I2C pins — do not change
• Mount sensor FACE UP for finger placement
```

### 6.2 NTC Thermistor (Temperature)

```
ESP32 3.3V
    │
   ┌┴┐
   │ │  10kΩ FIXED RESISTOR
   └┬┘
    │
    ├──── ESP32 GPIO 34 (ADC INPUT)
    │
   ┌┴┐
   │ │  10kΩ NTC THERMISTOR
   └┬┘
    │
ESP32 GND

NOTES:
• Forms a voltage divider
• GPIO 34 reads voltage at the junction
• Position NTC bead where finger touches
```

### 6.3 Status LEDs

```
ESP32 GPIO 26 ── 220Ω ── Green LED (long leg) ── GND (short leg)
ESP32 GPIO 27 ── 220Ω ── Red LED (long leg)   ── GND (short leg)

NOTES:
• 220Ω REQUIRED — prevents LED burnout
• Long leg (anode) toward GPIO, short leg (cathode) toward GND
• If LED doesn't light, flip it around
```

### 6.4 Vibration Motor (via 2N2222 Transistor)

```
ESP32 3.3V ──── Motor (+, red wire)
                Motor (-, black wire) ──── 2N2222 COLLECTOR
ESP32 GPIO 25 ── 1kΩ ──── 2N2222 BASE
                           2N2222 EMITTER ──── ESP32 GND

2N2222 PIN IDENTIFICATION (flat side facing you):
    ┌─────────┐
    │ 2N2222  │
    └─┬──┬──┬─┘
      E  B  C
    Left Mid Right

NOTES:
• GPIO 25 HIGH → base current flows → transistor ON → motor buzzes
• GPIO 25 LOW → transistor OFF → motor silent
• The 1kΩ resistor limits base current to protect ESP32 GPIO
```

---

## 7. Firmware Architecture

### 7.1 Program Flow

```
                    ┌─────────┐
                    │  BOOT   │
                    └────┬────┘
                         │
                    ┌────▼────┐
                    │  SETUP  │
                    │ • Init pins (LEDs, motor)
                    │ • Init MAX30102 (I2C)
                    │ • Connect WiFi
                    │ • Flash green 3× = ready
                    └────┬────┘
                         │
                    ┌────▼────┐
              ┌─────│  LOOP   │◄────────────────────────┐
              │     └────┬────┘                          │
              │          │                               │
              │     ┌────▼─────────┐                     │
              │     │ Read IR value │                     │
              │     └────┬─────────┘                     │
              │          │                               │
              │     ┌────▼─────────────┐    NO           │
              │     │ IR > 50000?      ├────────┐        │
              │     │ (finger present?)│         │        │
              │     └────┬─────────────┘    ┌───▼───┐    │
              │          │ YES              │Red LED │    │
              │          │                  │ ON     │    │
              │     ┌────▼─────────┐        │"No     │    │
              │     │ Detect beats  │        │finger" │    │
              │     │ Calculate:    │        └───┬───┘    │
              │     │ • BPM average │            │        │
              │     │ • HRV (RMSSD) │       delay(200ms)  │
              │     │ • SpO₂ ratio  │            │        │
              │     │ • Temperature │            │        │
              │     └────┬─────────┘            └────────┘
              │          │
              │     ┌────▼──────────────┐
              │     │ 2 seconds elapsed? │ NO──┘
              │     └────┬──────────────┘
              │          │ YES
              │     ┌────▼──────────────┐
              │     │ HTTP POST to       │
              │     │ /api/reading       │
              │     │ {bpm, hrv, spo2,   │
              │     │  temperature,      │
              │     │  timestamp,        │
              │     │  session_id}       │
              │     └────┬──────────────┘
              │          │
              │     ┌────▼─────────────────┐
              │     │ Response received?    │
              │     └────┬────────┬────────┘
              │          │        │
              │       SUCCESS    FAIL
              │          │        │
              │     ┌────▼───┐ ┌─▼──────┐
              │     │Green   │ │Red LED │
              │     │LED     │ │blink   │
              │     │blink   │ │        │
              │     └────┬───┘ │Retry   │
              │          │     │counter+│
              │     ┌────▼───┐ └───┬────┘
              │     │alert:  │     │
              │     │true?   │     │
              │     └──┬──┬──┘     │
              │     YES│  │NO      │
              │     ┌──▼┐ │        │
              │     │BUZZ│ │        │
              │     │3×  │ │        │
              │     └──┬─┘ │        │
              │        │   │        │
              └────────┴───┴────────┘
```

### 7.2 Sensor Reading Specifications

| Sensor | Method | Algorithm | Output |
|---|---|---|---|
| **Heart Rate** | MAX30102 IR LED PPG | SparkFun `checkForBeat()` peak detection → beat-to-beat interval → 60/(interval_ms/1000) | `int bpm` (30-220, 10-sample rolling average) |
| **HRV** | Derived from beat intervals | RMSSD: √(mean of squared successive differences of beat intervals) | `float hrv` (ms, from last 20 beat intervals) |
| **SpO₂** | MAX30102 RED + IR LEDs | Ratio = RED/IR → SpO₂ ≈ 110 - 25×ratio (linear approx) | `float spo2` (clamped 85-100%) |
| **Temperature** | NTC via ADC | ADC → resistance → Steinhart-Hart B-parameter equation → °C | `float temperature` (°C) |

### 7.3 LED Behavior

| State | Green LED | Red LED | Meaning |
|---|---|---|---|
| Boot / WiFi connecting | OFF | BLINKING | System starting up |
| Ready, no finger | OFF | SOLID ON | Waiting for user |
| Reading, data sent OK | BLINK (100ms) | OFF | Healthy data transmission |
| Reading, send failed | OFF | BLINK (100ms) | Network error |
| Alert triggered | OFF | OFF | Motor buzzing handles alert |

### 7.4 Vibration Motor Behavior

| Trigger | Pattern | Duration |
|---|---|---|
| Backend returns `"alert": true` | 3 pulses (250ms ON, 150ms OFF) | ~1.2 seconds |
| Score drops to ORANGE or RED zone | Triggered by backend alert flag | Same pattern |

---

## 8. Software Dependencies

### 8.1 Arduino IDE Setup

1. **Board Package:** ESP32 by Espressif Systems
   - URL: `https://raw.githubusercontent.com/espressif/arduino-esp32/gh-pages/package_esp32_index.json`
   - Board Selection: **ESP32 Dev Module**

2. **Libraries (via Library Manager):**

| Library | Author | Purpose |
|---|---|---|
| SparkFun MAX3010x | SparkFun | Pulse oximeter sensor driver |
| ArduinoJson | Benoit Blanchon | JSON serialization for API payloads |
| Wire | Built-in | I2C communication |
| WiFi | Built-in | ESP32 WiFi connectivity |
| HTTPClient | Built-in | HTTP POST requests |

---

## 9. Configuration Constants

These are the values the firmware uses. **Change WiFi and API_ENDPOINT at the venue.**

```
WIFI_SSID              = "HACKATHON_WIFI"        ← Change at venue
WIFI_PASS              = "HACKATHON_PASSWORD"     ← Change at venue
API_ENDPOINT           = "https://cardiotwin.azurewebsites.net/api/reading"  ← Person 3 provides
SESSION_ID             = "demo"                   ← Matches frontend

NTC_PIN                = 34     (ADC input)
MOTOR_PIN              = 25     (vibration motor)
GREEN_LED              = 26     (data sent OK)
RED_LED                = 27     (error/no finger)

FINGER_THRESHOLD       = 50000  (IR value — below = no finger)
MIN_VALID_BPM          = 30     (reject below)
MAX_VALID_BPM          = 220    (reject above)
SEND_INTERVAL          = 2000   (ms — send every 2 seconds)
WIFI_TIMEOUT           = 15000  (ms — give up WiFi after 15s)

NTC_FIXED_RESISTOR     = 10000  (10kΩ reference)
NTC_NOMINAL_R          = 10000  (NTC resistance at 25°C)
NTC_BETA               = 3950   (check your specific NTC datasheet)
NTC_NOMINAL_T          = 25.0   (reference temperature °C)

RATE_BUFFER_SIZE       = 10     (rolling average window for BPM)
HRV_BUFFER_SIZE        = 20     (beat intervals stored for RMSSD)
MAX_CONSECUTIVE_FAILS  = 5      (reconnect WiFi after 5 failures)
```

---

## 10. Build Sequence (Step-by-Step)

### Phase 1: Setup Environment (30 min)
1. Install Arduino IDE + ESP32 board package
2. Install SparkFun MAX3010x + ArduinoJson libraries
3. Connect ESP32 via USB, select board + port
4. Upload blank test sketch → verify "ESP32 is alive!" in Serial Monitor

### Phase 2: Wire + Test MAX30102 (60 min)
1. Wire: VIN→3.3V, GND→GND, SDA→GPIO21, SCL→GPIO22
2. Upload MAX30102 test sketch
3. **PASS CRITERIA:** Serial prints IR/RED values. Place finger → values change significantly. "MAX30102 FOUND ✅"
4. **DO NOT PROCEED** if this fails. Fix wiring first.

### Phase 3: Wire + Test NTC Thermistor (30 min)
1. Wire voltage divider: 3.3V → 10kΩ resistor → junction (GPIO 34) → NTC → GND
2. Upload thermistor test sketch
3. **PASS CRITERIA:** Room temp reads ~22-28°C. Touch NTC bead → rises to ~30-35°C.

### Phase 4: Wire + Test LEDs (15 min)
1. Wire: GPIO 26 → 220Ω → Green LED → GND
2. Wire: GPIO 27 → 220Ω → Red LED → GND
3. Upload LED test sketch
4. **PASS CRITERIA:** Both LEDs alternate on/off every second.

### Phase 5: Wire + Test Vibration Motor (15 min)
1. Wire: GPIO 25 → 1kΩ → 2N2222 Base. Emitter → GND. Collector → Motor(-). Motor(+) → 3.3V
2. Upload motor test sketch
3. **PASS CRITERIA:** Motor buzzes 3 pulses, pauses 2 seconds, repeats.

### Phase 6: Full Firmware (No WiFi) (60 min)
1. Flash complete firmware with fake WiFi credentials
2. Open Serial Monitor at 115200 baud
3. Place finger on MAX30102
4. **PASS CRITERIA:** See HR, HRV, SpO₂, Temperature readings every 2 seconds. Red LED when no finger. Green LED attempts on send. Values within valid ranges.

### Phase 7: WiFi Integration (30 min)
1. Update firmware with real WiFi credentials
2. Update API_ENDPOINT with Person 3's Azure URL
3. Re-flash and test
4. **PASS CRITERIA:** Serial shows "Connected! ✅" and "Response (200)" with score data.

### Phase 8: End-to-End Test (30 min)
1. Person 4's frontend should show live data updating
2. Take baseline reading (45s finger on sensor, steady)
3. Do 30s of physical activity (burpees/jumping jacks)
4. Take post-stress reading (45s finger on sensor)
5. **PASS CRITERIA:** Score drops visibly. WhatsApp alert received. Motor buzzes on alert.

### Phase 9: Station Enclosure (30 min)
1. Small cardboard box, cut hole for MAX30102 sensor window
2. Cut hole for NTC bead to poke through
3. Cut holes for LEDs on front face
4. Hot glue everything secure — **sensor must NOT wobble**
5. Label: "☝️ Place Finger Here" on top, "CardioTwin AI" on front

---

## 11. Data Flow Summary

```
🔧 ESP32                           🖥️ Backend (FastAPI on Azure)
   │                                    │
   │ 1. Read MAX30102 (HR, SpO₂)        │
   │ 2. Read NTC (temperature)          │
   │ 3. Calculate HRV (RMSSD)           │
   │ 4. Package as JSON                 │
   │                                    │
   │─── POST /api/reading ────────────►│
   │    {bpm, hrv, spo2, temp,          │
   │     timestamp, session_id}         │
   │                                    │
   │                              ┌─────▼──────────────┐
   │                              │ readingRouter.py    │
   │                              │ → validation.py     │
   │                              │ → baseline.py       │
   │                              │ → scoring.py        │
   │                              │ → zones.py          │
   │                              │ → anomaly.py        │
   │                              │ → nudges.py (Groq)  │
   │                              │ → Twilio (WhatsApp) │
   │                              └─────┬──────────────┘
   │                                    │
   │◄── 200 OK + JSON ────────────────│
   │    {score, zone, alert, ...}       │
   │                                    │
   │ 5. Check "alert" field             │
   │    → true: BUZZ motor + RED LED    │
   │    → false: GREEN LED blink        │
   │                                    │
   │ 6. Wait 2 seconds                  │
   │ 7. Repeat from step 1              │
```

---

## 12. Validation Alignment

The backend's `ai_engine/validation.py` enforces these ranges. The firmware MUST respect them:

| Parameter | Backend Valid Range | Firmware Clamp Logic |
|---|---|---|
| `bpm` | 30–220 | Only accept `checkForBeat()` results in 30–220 range |
| `hrv` | 0–200 | RMSSD naturally falls in range; clamp if needed |
| `spo2` | 70–100 | Clamp: `constrain(spo2, 85, 100)` (85 min for demo safety) |
| `temperature` | 30.0–42.0 | NTC on skin reads 30-37°C naturally; reject outliers |

If a value falls outside these ranges, the backend returns a validation error. The firmware should either:
1. Clamp the value to the valid range, OR
2. Skip that reading and wait for the next cycle

---

## 13. Troubleshooting Guide

| Problem | Cause | Fix |
|---|---|---|
| "MAX30102 NOT FOUND" | Wiring error | Check SDA→21, SCL→22, VIN→3.3V, GND→GND. Reseat wires. |
| HR reads 0 or wild numbers | Finger not firm enough | Press more firmly. Hold STILL. Wait 10s to stabilize. |
| Temperature always 25°C | NTC not touching skin | Reposition bead closer to finger rest area. |
| SpO₂ always 85% (minimum) | RED/IR calibration off | Acceptable for demo. Mention "approximate" to judges. |
| WiFi won't connect | Wrong credentials / venue interference | Double-check SSID/password (case sensitive). Try phone hotspot. |
| HTTP 404 | Wrong API URL | Get correct URL from Person 3. Must end in `/api/reading`. |
| HTTP 500 | Backend crash | Person 3 checks Azure logs. May be DB or Groq API issue. |
| HTTP -1 | Connection refused | Backend not running. Redeploy or check Azure status. |
| Motor won't buzz | 2N2222 wiring wrong | Check E-B-C orientation (flat side: left-mid-right). |
| LED won't light | Polarity reversed | Flip LED (longer leg = anode = toward GPIO side). |
| ESP32 keeps rebooting | Bad USB cable or power | Use DATA cable (not charge-only). Try different USB port. |
| Readings jump erratically | Motion artifact | User must hold finger STILL during reading. |

---

## 14. Pre-Demo Checklist

Run through this **30 minutes before** presentation:

```
POWER & CONNECTION
  [ ] ESP32 powered via USB — board LED on
  [ ] WiFi connected — Serial shows "Connected ✅"
  [ ] Backend reachable — Serial shows "Response (200)"

SENSORS
  [ ] Finger on sensor → "Finger detected!" in Serial
  [ ] Heart rate: 60-100 BPM (resting, stable)
  [ ] HRV: 20-60 ms (stable)
  [ ] SpO₂: 95-100% (stable)
  [ ] Temperature: 30-36°C (finger contact)
  [ ] Remove finger → "No finger" + Red LED

STATUS INDICATORS
  [ ] No finger → Red LED solid
  [ ] Data sent OK → Green LED blinks
  [ ] Send failed → Red LED blinks

ALERT SYSTEM
  [ ] Do jumping jacks (30s) → retake reading
  [ ] Score drops on dashboard
  [ ] Motor buzzes on alert
  [ ] WhatsApp message received

BACKUP
  [ ] Backup demo video recorded by Person 5
  [ ] Video loaded and ready to play
  [ ] Phone hotspot configured as WiFi backup
```

---

## 15. Station Enclosure Specification

```
TOP VIEW:
┌─────────────────────────────────┐
│  ┌──────────┐  ● ← NTC bead   │
│  │ MAX30102 │    (pokes out)   │
│  │ ┌──────┐ │                  │
│  │ │SENSOR│ │                  │
│  │ │WINDOW│ │                  │
│  │ └──────┘ │                  │
│  └──────────┘                  │
│                                │
│  "☝️ Place Finger Here"        │
└─────────────────────────────────┘

FRONT VIEW:
┌─────────────────────────────────┐
│                                 │
│  🟢 Data OK    🔴 Error/Wait   │
│                                 │
│         CardioTwin AI           │
│    "Your Heart's Early Warning" │
│                                 │
└─────────────────────────────────┘

BACK VIEW:
┌─────────────────────────────────┐
│                                 │
│       ┌──────────┐              │
│       │ USB hole │              │
│       └──────────┘              │
│                                 │
└─────────────────────────────────┘

MATERIALS: Cardboard phone box + hot glue + printed labels
BUILD TIME: 15-30 minutes
CRITICAL: Hot glue the MAX30102 module firmly — sensor MUST NOT wobble
```

---

## 16. Timeline (Hardware Engineer)

| Hour | Task | Deliverable |
|---|---|---|
| 0-0.5 | Arduino IDE + library setup | ESP32 responds to test sketch |
| 0.5-1.5 | Wire + test MAX30102 | Stable IR/RED readings with finger |
| 1.5-2 | Wire + test NTC thermistor | Accurate temperature readings |
| 2-2.5 | Wire + test LEDs + motor | All indicators working |
| 2.5-4.5 | Flash full firmware (no WiFi) | All sensors reading, all indicators working |
| 4.5-5.5 | WiFi integration + backend connect | HTTP 200 responses in Serial Monitor |
| 5.5-7 | End-to-end integration with team | Dashboard shows live data |
| 7-8 | Build station enclosure | Clean, labeled, secure |
| 8+ | Support integration testing + demo rehearsal | Rock-solid demo |

---

*This document contains everything needed to build, test, and deploy the CardioTwin hardware station. Follow the build sequence exactly. Test each component individually before combining. Do not skip test steps.*

**Go build it. 🔧🚀**