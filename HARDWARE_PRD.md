# CardioTwin AI — Hardware Integration PRD (Revised)

**Version:** 2.0 | **Date:** February 22, 2026 | **Owner:** Hardware Engineer (Person 1)
**Status:** FINAL — Revised to match actual components on hand

---

## 1. Purpose

This is the **revised hardware PRD** reflecting the actual components the team has. The previous version included an NTC thermistor, vibration motor, and transistor — those have been **removed**. This document covers exactly what we're building with **what we have**.

### What Changed from v1

| Item | v1 (Old) | v2 (This Document) |
|---|---|---|
| Temperature sensor | NTC Thermistor + voltage divider | **Removed** — temperature derived from MAX30102 die temp |
| Alert output | Vibration motor + 2N2222 transistor | **Passive buzzer** (direct GPIO drive) |
| MAX30102 pins | 4-pin wiring (missing INT) | **5-pin wiring** (INT, SDA, SCL, GND, VIN) |
| Components count | 13 items | **7 items** (simpler, fewer failure points) |

---

## 2. Backend Architecture (Already Built — No Changes)

The hardware talks to the existing backend in the `Techdee1/Kardio-Twin` repository:

```
Techdee1/Kardio-Twin Repository
├── main.py                     ← FastAPI entry point
├── config.py                   ← Settings (calibration threshold = 15)
├── routers/
│   ├── readingRouter.py        ← POST /api/reading (HARDWARE TARGET)
│   └── sessionRouter.py        ← POST /api/session/start
├── ai_engine/
│   ├── engine.py               ← CardioTwinEngine orchestrator
│   ├── scoring.py              ← Weighted scoring (HR 25%, HRV 40%, SpO₂ 20%, Temp 15%)
│   ├── baseline.py             ← Baseline from first 15 readings (IQR outlier removal)
│   ├── zones.py                ← GREEN (80-100) / YELLOW (55-79) / ORANGE (30-54) / RED (0-29)
│   ├── anomaly.py              ← Alert detection (sudden drops, sustained decline, SpO₂ critical)
│   ├── nudges.py               ← Groq LLM nudge generation (multi-language)
│   ├── validation.py           ← Input validation + range checks
│   ├── projection.py           ← What-if risk projections
│   └── api.py                  ← CardioTwinAPI facade
├── service/
│   ├── readingService.py       ← DB storage + legacy scoring
│   └── sessionService.py       ← Session CRUD
├── dtos/
│   ├── readingsDto.py          ← Request/response Pydantic models
│   └── sessionDto.py           ← Session Pydantic models
├── model/
│   └── dataModel.py            ← SQLAlchemy models (Session, BiometricReading)
└── repository/
    └── database.py             ← Database connection
```

**The hardware is DUMB by design. Read sensors → send JSON → check response. That's it.**

---

## 3. API Contract

### 3.1 What Hardware Sends — `POST /api/reading`

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
| `bpm` | float | 30–220 | MAX30102 beat detection → rolling average |
| `hrv` | float | 0–200 | RMSSD calculated from beat-to-beat intervals |
| `spo2` | float | 70–100 | MAX30102 RED/IR ratio → linear approximation |
| `temperature` | float | 30.0–42.0 | MAX30102 on-chip die temperature sensor |
| `timestamp` | int | ≥ 0 | `millis()` since ESP32 boot |
| `session_id` | string | any | Fixed to `"demo"` for hackathon |

> **Temperature Note:** Without an NTC thermistor, we use the MAX30102's built-in die temperature register. It reads the sensor module's internal temperature, which rises when a warm finger is placed on it. It's not clinical-grade skin temperature, but it provides a **relative thermal proxy** that tracks changes — which is all the scoring engine needs (it compares against YOUR baseline, not an absolute value).

### 3.2 What Hardware Receives

**During Calibration (first 15 readings, ~30 seconds):**
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
  "components": { ... },
  "baseline": { ... }
}
```

**Hardware only checks ONE field:**
```
"alert": true  → BEEP buzzer + RED LED
"alert": false → GREEN LED blink
```

---

## 4. Components — Bill of Materials

These are the **actual components** we have:

| # | Component | Specification | Purpose |
|---|---|---|---|
| 1 | **ESP32-WROOM-32 Dev Board** | 240MHz dual-core, WiFi + BLE | Microcontroller + WiFi |
| 2 | **MAX30102 Breakout Module** | 5-pin (INT, SDA, SCL, GND, VIN) | Heart Rate, HRV, SpO₂, Temperature |
| 3 | **Green LED** | 3mm or 5mm | "Data Sent OK" indicator |
| 4 | **Red LED** | 3mm or 5mm | "Error / Alert / No Finger" indicator |
| 5 | **Passive Buzzer** | 3.3V compatible | Audio alert on anomaly |
| 6 | **220Ω Resistors (×2)** | ¼W | LED current limiting |
| 7 | **Breadboard + Jumper Wires** | Half-size + ~15 wires | Assembly |

**That's it. 7 items. Simple = reliable.**

### Why This Works Without NTC and Motor

| Removed Component | Replacement | Why It's Fine |
|---|---|---|
| NTC Thermistor | MAX30102 die temperature | Baseline-relative scoring doesn't need absolute accuracy — it needs consistent relative changes |
| Vibration Motor | Passive Buzzer | Buzzer is audible AND doesn't need a transistor driver circuit — one less thing to break |
| 2N2222 Transistor | Not needed | Buzzer draws < 30mA, safe to drive directly from ESP32 GPIO |
| 1kΩ + 10kΩ Resistors | Not needed | No voltage divider, no transistor base — only 220Ω for LEDs |

---

## 5. Pin Assignment

```
┌──────────────────────────────────────────────────────���───┐
│              ESP32-WROOM-32 PIN MAP (REVISED)            │
├──────────────┬────────────────┬───────────────────────────┤
│  ESP32 PIN   │  CONNECTS TO   │  FUNCTION                 │
├──────────────┼────────────────┼───────────────────────────┤
│  3.3V        │  MAX30102 VIN  │  Sensor power             │
│  GND         │  Common ground │  All components           │
│  GPIO 21     │  MAX30102 SDA  │  I2C Data                 │
│  GPIO 22     │  MAX30102 SCL  │  I2C Clock                │
│  GPIO 19     │  MAX30102 INT  │  Interrupt (data ready)   │
│  GPIO 26     │  220Ω → Green  │  Data-sent LED            │
│  GPIO 27     │  220Ω → Red    │  Error/alert LED          │
│  GPIO 25     │  Buzzer (+)    │  Audio alert              │
└──────────────┴────────────────┴───────────────────────────┘

ACTIVE GPIO PINS: 19, 21, 22, 25, 26, 27 (6 pins total)
POWER PINS: 3.3V, GND
```

---

## 6. Wiring Diagrams

### 6.1 MAX30102 (5-Pin Module)

Your module has pins in this order: **INT | SDA | SCL | GND | VIN**

```
MAX30102 MODULE (face up, pins at bottom):
┌─────────────────────────┐
│   ┌───────────────────┐ │
│   │  SENSOR WINDOW    │ │
│   │  (place finger)   │ │
│   └───────────────────┘ │
│                         │
│  INT  SDA  SCL  GND  VIN│
└──┬────┬────┬────┬────┬──┘
   │    │    │    │    │
   │    │    │    │    └──── ESP32 3.3V
   │    │    │    └───────── ESP32 GND
   │    │    └────────────── ESP32 GPIO 22
   │    └─────────────────── ESP32 GPIO 21
   └──────────────────────── ESP32 GPIO 19


WIRING TABLE:
    MAX30102 VIN ──────── ESP32 3.3V
    MAX30102 GND ──────── ESP32 GND
    MAX30102 SCL ──────── ESP32 GPIO 22
    MAX30102 SDA ──────── ESP32 GPIO 21
    MAX30102 INT ──────── ESP32 GPIO 19

⚠️ CRITICAL NOTES:
  • Use 3.3V ONLY — NOT 5V (will damage the sensor)
  • Keep I2C wires SHORT (< 10cm ideally)
  • GPIO 21/22 are ESP32's DEFAULT I2C pins
  • INT pin enables interrupt-driven reads (more reliable than polling)
  • Mount sensor FACE UP — the dark window faces the finger
```

### 6.2 Status LEDs

```
GREEN LED (Data OK):
    ESP32 GPIO 26 ──── 220Ω ──── LED long leg (anode) ──── LED short leg (cathode) ──── GND

RED LED (Error/Alert):
    ESP32 GPIO 27 ──── 220Ω ──── LED long leg (anode) ──── LED short leg (cathode) ──── GND


VISUAL:
    GPIO 26 ──┤220Ω├──►|── GND     (Green)
    GPIO 27 ──┤220Ω├──►|── GND     (Red)

⚠️ NOTES:
  • 220Ω resistor is REQUIRED — protects LED from burning out
  • Long leg = anode = toward GPIO side
  • Short leg = cathode = toward GND side
  • If LED doesn't light, flip it around
```

### 6.3 Passive Buzzer

```
    ESP32 GPIO 25 ──── Buzzer (+) positive terminal
    ESP32 GND     ──── Buzzer (-) negative terminal

VISUAL:
    GPIO 25 ──── [BUZZER] ──── GND

⚠️ NOTES:
  • Passive buzzer — driven by PWM tone from ESP32
  • Check buzzer polarity: (+) marked on top or longer leg
  • If no marking, try both orientations — wrong polarity = no sound (won't damage)
  • DO NOT use active buzzer (clicks instead of tones)
  • GPIO 25 can output PWM — use tone() function for different pitches
```

### 6.4 Complete Wiring (All Components)

```
                    ESP32 DEV BOARD
              ┌─────────────────────────┐
              │                         │
      3.3V ───┤ 3.3V             GND   ├─── GND RAIL
              │                         │
              │ GPIO 19 ────────────────┼──── MAX30102 INT
              │ GPIO 21 ────────────────┼──── MAX30102 SDA
              │ GPIO 22 ────────────────┼──── MAX30102 SCL
              │                         │
              │ GPIO 25 ────────────────┼──── Buzzer (+)
              │                         │
              │ GPIO 26 ──┤220Ω├────────┼──── Green LED (+)
              │ GPIO 27 ──┤220Ω├────────┼──── Red LED (+)
              │                         │
              └─────────────────────────┘

    POWER RAIL: 3.3V → MAX30102 VIN
    GND RAIL:   GND  → MAX30102 GND, Buzzer (-), Green LED (-), Red LED (-)

    TOTAL CONNECTIONS: 11 wires
    (3.3V, GND, GPIO 19, 21, 22, 25, 26, 27, plus LED/buzzer grounds)
```

---

## 7. Firmware Architecture

### 7.1 Program Flow

```
                    ┌─────────┐
                    │  BOOT   │
                    └────┬────┘
                         │
                    ┌────▼────────────────────────────┐
                    │           SETUP                   │
                    │  • pinMode(LEDs, buzzer)          │
                    │  • Wire.begin(21, 22)             │
                    │  • MAX30102.begin()               │
                    │  • WiFi.begin(ssid, pass)         │
                    │  • Boot melody on buzzer          │
                    │  • Green LED flash 3× = ready     │
                    └────┬────────────────────────────┘
                         │
              ┌──────────▼──────────┐
              │       MAIN LOOP      │◄──────────────────────┐
              └──────────┬──────────┘                        │
                         │                                   │
              ┌──────────▼──────────┐                        │
              │  Read MAX30102 IR   │                        │
              └──────────┬──────────┘                        │
                         │                                   │
              ┌──────────▼──────────┐    NO                  │
              │  IR > 50000?        ├───────────┐            │
              │  (finger present?)  │           │            │
              └──────────┬──────────┘     ┌─────▼──────┐     │
                         │ YES            │ Red LED ON  │     │
                         │                │ "No finger" │     │
              ┌──────────▼──────────┐     └─────┬──────┘     │
              │  Detect heartbeats   │          │            │
              │  Calculate:          │     delay(200ms)      │
              │  • BPM (avg of 10)   │          │            │
              │  • HRV (RMSSD)       │          │            │
              │  • SpO₂ (RED/IR)     │          │            │
              │  • Temp (die sensor)  │
              └──────────┬──────────┘
                         │
              ┌──────────▼──────────┐
              │  2 seconds elapsed?  │──NO──┘
              └──────────┬──────────┘
                         │ YES
              ┌──────────▼──────────┐
              │  HTTP POST to        │
              │  /api/reading        │
              │  {bpm, hrv, spo2,    │
              │   temperature,       │
              │   timestamp,         │
              │   session_id}        │
              └──────────┬──────────┘
                         │
              ┌──────────▼──────────┐
              │  Response OK?        │
              └──────┬────────┬─────┘
                     │        │
                  SUCCESS    FAIL
                     │        │
              ┌──────▼──┐ ┌──▼─────────┐
              │ Green    │ │ Red LED    │
              │ LED      │ │ blink      │
              │ blink    │ │ Error beep │
              └──────┬──┘ └──┬─────────┘
                     │       │
              ┌──────▼──┐    │
              │ alert    │    │
              │ == true? │    │
              └──┬───┬──┘    │
              YES│   │NO     │
              ┌──▼──┐│       │
              │BEEP ││       │
              │3×   ││       │
              │tone ││       │
              └──┬──┘│       │
                 │   │       │
                 └───┴───────┴──── wait 2 seconds ──── loop back ↑
```

### 7.2 Sensor Reading Methods

| Reading | Source | Method | Output |
|---|---|---|---|
| **Heart Rate** | MAX30102 IR LED | `checkForBeat()` peak detection → interval → 60/(ms/1000) | `float bpm` (30-220, 10-sample rolling avg) |
| **HRV** | Derived from beats | RMSSD: √(mean of squared successive differences of intervals) | `float hrv` (ms, from last 20 intervals) |
| **SpO₂** | MAX30102 RED+IR | Ratio = RED_AC/RED_DC ÷ IR_AC/IR_DC → SpO₂ ≈ 110 - 25×ratio | `float spo2` (clamped 85-100%) |
| **Temperature** | MAX30102 die temp | `particleSensor.readTemperature()` → °C | `float temperature` (°C, ~30-38 with finger) |

### 7.3 Temperature from MAX30102 — How It Works

```
WITHOUT FINGER:
  MAX30102 die temp ≈ ambient room temperature (~22-28°C)

WITH FINGER PLACED:
  Finger warms the sensor die through thermal conduction
  Die temp rises to ~30-36°C over 10-20 seconds
  Stabilizes at a value that CORRELATES with skin temperature

WHY THIS IS FINE:
  The backend's ai_engine/scoring.py scores temperature RELATIVE to baseline:
  → Calibration phase (first 15 readings) captures YOUR "normal" die temp
  → Subsequent readings are scored by DEVIATION from your normal
  → A 1°C rise from YOUR baseline scores the same whether
     the absolute value is 33°C (die) or 37°C (clinical thermometer)

IMPORTANT:
  → Tell user to keep finger on sensor for ENTIRE session
  → First 30 seconds = calibration (finger must be stable)
  → Removing and replacing finger will reset the thermal baseline
```

### 7.4 Buzzer Behavior

| Trigger | Tone Pattern | Meaning |
|---|---|---|
| Boot success | 3 ascending tones (C-E-G) | "System ready" |
| WiFi connected | 2 short beeps | "Online" |
| Data sent OK | 1 short tick (50ms) | "Heartbeat" confirmation |
| Send failed | 2 low tones | "Network error" |
| "alert": true | 3 urgent beeps (800Hz, 200ms ON, 100ms OFF) | "Health alert — check dashboard" |
| MAX30102 not found | Continuous low tone | "Fix wiring" |

### 7.5 LED Behavior

| State | Green LED | Red LED | Meaning |
|---|---|---|---|
| Booting / WiFi connecting | OFF | BLINKING | System starting |
| Ready, no finger | OFF | SOLID ON | Waiting for user |
| Reading + data sent OK | BLINK (100ms) | OFF | Healthy transmission |
| Reading + send failed | OFF | BLINK (100ms) | Network error |
| Alert triggered | OFF | RAPID BLINK | Buzzer handles audio |

---

## 8. Configuration Constants

```c
// WiFi — CHANGE AT VENUE
WIFI_SSID              = "HACKATHON_WIFI"
WIFI_PASS              = "HACKATHON_PASSWORD"

// API — Person 3 provides the deployed URL
API_ENDPOINT           = "https://your-backend-url.com/api/reading"
SESSION_ID             = "demo"

// Pin Definitions
MAX30102_INT_PIN       = 19
BUZZER_PIN             = 25
GREEN_LED              = 26
RED_LED                = 27
// SDA = 21, SCL = 22 (Wire library defaults)

// Sensor Thresholds
FINGER_THRESHOLD       = 50000   // IR value below this = no finger
MIN_VALID_BPM          = 30
MAX_VALID_BPM          = 220
SEND_INTERVAL_MS       = 2000    // POST every 2 seconds

// Buffer Sizes
BPM_BUFFER_SIZE        = 10      // Rolling average window
HRV_BUFFER_SIZE        = 20      // Beat intervals for RMSSD

// Network
WIFI_TIMEOUT_MS        = 15000   // 15 seconds to connect
MAX_CONSECUTIVE_FAILS  = 5       // Reconnect WiFi after 5 failures

// Buzzer Tones (Hz)
TONE_ALERT             = 800
TONE_SUCCESS           = 1000
TONE_ERROR             = 400
TONE_BOOT              = 523     // C5
```

---

## 9. Software Dependencies

### Arduino IDE Setup

1. **Board Package:** ESP32 by Espressif Systems
   - URL: `https://raw.githubusercontent.com/espressif/arduino-esp32/gh-pages/package_esp32_index.json`
   - Board: **ESP32 Dev Module**

2. **Libraries:**

| Library | Author | Purpose |
|---|---|---|
| SparkFun MAX3010x | SparkFun Electronics | Pulse oximeter + temperature sensor driver |
| ArduinoJson | Benoit Blanchon | JSON serialization for API requests |
| Wire | Built-in | I2C communication (SDA/SCL) |
| WiFi | Built-in | ESP32 WiFi connectivity |
| HTTPClient | Built-in | HTTP POST requests to backend |

No additional libraries needed for buzzer — `tone()` is built into ESP32 Arduino core.

---

## 10. Build Sequence

### Phase 1: Environment Setup (20 min)
1. Install Arduino IDE 2.x
2. Add ESP32 board URL → install ESP32 board package
3. Install SparkFun MAX3010x library
4. Install ArduinoJson library
5. Connect ESP32 via USB, select **ESP32 Dev Module** + correct port
6. Upload blank sketch → verify Serial Monitor shows output at 115200 baud
7. **✅ PASS:** "Hello from ESP32!" prints

### Phase 2: MAX30102 — Wire + Test (45 min)
1. Wire all 5 pins:
   - VIN → 3.3V
   - GND → GND
   - SCL → GPIO 22
   - SDA → GPIO 21
   - INT → GPIO 19
2. Upload MAX30102 test sketch
3. Place finger firmly on sensor
4. **✅ PASS:** Serial prints changing IR/RED values. "MAX30102 FOUND ✅"
5. **❌ FAIL:** Check wiring. SDA/SCL swapped is the #1 mistake.

### Phase 3: Heart Rate + Temperature Verification (30 min)
1. Upload beat detection + temperature sketch
2. Place finger, hold still for 30 seconds
3. **✅ PASS:** BPM reads 60-100 (resting), temperature reads 30-36°C with finger
4. **✅ PASS:** HRV values appear after ~10 beats detected

### Phase 4: LEDs — Wire + Test (10 min)
1. Wire: GPIO 26 → 220Ω → Green LED → GND
2. Wire: GPIO 27 → 220Ω → Red LED → GND
3. Upload LED blink test
4. **✅ PASS:** Both LEDs alternate on/off every second

### Phase 5: Buzzer — Wire + Test (10 min)
1. Wire: GPIO 25 → Buzzer (+), GND → Buzzer (-)
2. Upload buzzer test (plays 3 tones)
3. **✅ PASS:** Three ascending tones play clearly
4. **❌ FAIL:** Check polarity. Try swapping wires. If still silent, check if buzzer is passive (needs PWM) vs active (needs DC).

### Phase 6: Full Firmware — No WiFi (45 min)
1. Flash complete firmware with fake WiFi credentials
2. Open Serial Monitor at 115200 baud
3. Place finger on MAX30102
4. Check Serial output for: BPM, HRV, SpO₂, Temperature every 2 seconds
5. **✅ PASS:** All 4 values within valid ranges
6. **✅ PASS:** Red LED when no finger, Green LED blinks on "send attempt"
7. **✅ PASS:** Values are stable (not jumping wildly)

### Phase 7: WiFi + Backend Integration (30 min)
1. Update firmware with real WiFi credentials
2. Update API_ENDPOINT with deployed backend URL
3. Re-flash and test
4. **✅ PASS:** Serial shows "WiFi Connected ✅" and "HTTP 200" responses
5. **✅ PASS:** Response JSON visible in Serial Monitor

### Phase 8: End-to-End Integration (30 min)
1. Person 4's frontend dashboard should show live data
2. Resting reading: 45 seconds finger on sensor (baseline calibration)
3. Exercise: 30 seconds jumping jacks / burpees
4. Post-stress reading: 45 seconds finger on sensor
5. **✅ PASS:** Score drops visibly on dashboard
6. **✅ PASS:** Buzzer beeps on alert
7. **✅ PASS:** WhatsApp message received (if Twilio configured)

### Phase 9: Station Assembly (20 min)
1. Arrange components neatly on breadboard
2. Small box/enclosure — cut hole for MAX30102 sensor window on top
3. LEDs visible on front face
4. USB cable exits from back
5. Label: "☝️ Place Finger Here" on top
6. Label: "CardioTwin AI" on front
7. Hot glue MAX30102 firmly — **sensor MUST NOT wobble**

---

## 11. Data Flow

```
🔧 ESP32 + MAX30102                     🖥️ FastAPI Backend (Azure)
   │                                         │
   │ 1. Read MAX30102:                       │
   │    • IR/RED → beat detection → BPM      │
   │    • Beat intervals → RMSSD → HRV       │
   │    • RED/IR ratio → SpO₂                │
   │    • Die temperature → Temperature      │
   │                                         │
   │ 2. Package JSON:                        │
   │    {bpm, hrv, spo2, temperature,        │
   │     timestamp, session_id}              │
   │                                         │
   │──── POST /api/reading ─────────────────►│
   │                                         │
   │                                   ┌─────▼──────────────────┐
   │                                   │  readingRouter.py       │
   │                                   │  ├─ validation.py       │
   │                                   │  ├─ baseline.py (15 rds)│
   │                                   │  ├─ scoring.py          │
   │                                   │  │  HR:25% HRV:40%      │
   │                                   │  │  SpO₂:20% Temp:15%   │
   │                                   │  ├─ zones.py            │
   │                                   │  ├─ anomaly.py          │
   │                                   │  ├─ nudges.py (Groq AI) │
   │                                   │  └─ Twilio (WhatsApp)   │
   │                                   └─────┬──────────────────┘
   │                                         │
   │◄─── 200 OK + JSON ─────────────────────│
   │     {score, zone, alert, ...}           │
   │                                         │
   │ 3. Check "alert" field:                 │
   │    true  → BEEP buzzer + RED LED         │
   │    false → GREEN LED blink              │
   │                                         │
   │ 4. Wait 2 seconds → repeat             │
```

---

## 12. Validation Alignment

The backend's `ai_engine/validation.py` enforces these ranges. Firmware MUST respect them:

| Parameter | Backend Range | Firmware Strategy |
|---|---|---|
| `bpm` | 30–220 | Only accept `checkForBeat()` results in range; rolling avg of 10 |
| `hrv` | 0–200 | RMSSD naturally falls in range; `constrain(hrv, 0, 200)` |
| `spo2` | 70–100 | Clamp: `constrain(spo2, 85, 100)` — 85 min for demo safety |
| `temperature` | 30.0–42.0 | Die temp with finger: 30-38°C naturally; clamp if needed |

If a value falls outside range → **skip that reading**, wait for next 2-second cycle.

---

## 13. Troubleshooting

| Problem | Likely Cause | Fix |
|---|---|---|
| "MAX30102 NOT FOUND" | SDA/SCL swapped | Verify: SDA→21, SCL→22. Swap if reversed. |
| "MAX30102 NOT FOUND" | Bad connection | Reseat all 5 jumper wires. Check VIN→3.3V (not 5V). |
| HR reads 0 or jumps wildly | Finger not firm/still | Press FIRMLY. Hold STILL. Wait 10s to stabilize. |
| HR always 0 but IR values change | INT pin not connected | Wire INT→GPIO 19. |
| Temperature reads ~25°C | No finger on sensor | Die temp = room temp without finger. Place finger, wait 20s. |
| Temperature stuck at same value | Need to read temp register | Use `particleSensor.readTemperature()` after `readTemperatureFraction()`. |
| SpO₂ always 85% (minimum) | RED/IR calibration margin | Acceptable for demo. Mention "approximate values" to judges. |
| Buzzer silent | Wrong polarity or passive vs active | Swap wires. Ensure you're using `tone(pin, freq)` for passive buzzer. |
| Buzzer makes click instead of tone | Active buzzer (not passive) | Active buzzers don't respond to PWM. Replace with passive, or use `digitalWrite()` ON/OFF only. |
| LEDs don't light | Polarity reversed | Flip LED (long leg toward GPIO, short leg toward GND). |
| WiFi won't connect | Wrong SSID/password | Case-sensitive. Try phone hotspot as backup. |
| HTTP 404 | Wrong API URL | Must end in `/api/reading`. Get exact URL from Person 3. |
| HTTP 500 | Backend error | Person 3 checks server logs. |
| HTTP -1 | Connection refused | Backend not running or URL unreachable. |
| ESP32 rebooting | Bad USB cable | Use DATA cable (not charge-only). Try different port. |
| Readings jump erratically | Motion artifact | User must hold finger STILL. Any movement corrupts PPG signal. |

---

## 14. Pre-Demo Checklist

Run through **30 minutes before** presentation:

```
POWER & CONNECTION
  [ ] ESP32 powered via USB — board LED on
  [ ] Serial Monitor shows "WiFi Connected ✅"
  [ ] Serial Monitor shows "HTTP 200" responses

SENSOR
  [ ] Finger on sensor → "Finger detected!"
  [ ] Heart rate: 55-100 BPM (resting, stable after 10s)
  [ ] HRV: 15-70 ms (stable)
  [ ] SpO₂: 93-100% (stable)
  [ ] Temperature: 30-36°C (with finger, after 20s stabilization)
  [ ] Remove finger → "No finger" + Red LED

INDICATORS
  [ ] No finger → Red LED solid
  [ ] Data sent OK → Green LED blinks
  [ ] Send failed → Red LED blinks + error beep

ALERT TEST
  [ ] Do 30s jumping jacks → retake reading
  [ ] Score drops on dashboard
  [ ] Buzzer beeps on alert
  [ ] WhatsApp received (if Twilio configured)

BACKUP
  [ ] Demo video recorded (Person 5)
  [ ] Phone hotspot configured as WiFi backup
  [ ] Know how to restart ESP32 quickly (press EN button)
```

---

## 15. Station Layout

```
TOP VIEW:
┌────────────────────────────────┐
│                                │
│       ┌──────────────┐         │
│       │  MAX30102     │         │
│       │  ┌────────┐  │         │
│       │  │ SENSOR │  │         │
│       │  │ WINDOW │  │         │
│       │  └────────┘  │         │
│       └──────────────┘         │
│                                │
│    "☝️ Place Finger Here"      │
└────────────────────────────────┘

FRONT VIEW:
┌────────────────────────────────┐
│                                │
│   🟢 OK      🔴 Alert     🔊  │
│                                │
│        CardioTwin AI           │
│   "Your Heart's Early Warning" │
│                                │
└────────────────────────────────┘

BACK VIEW:
┌────────────────────────────────┐
│       ┌──────────┐             │
│       │ USB hole │             │
│       └──────────┘             │
└────────────────────────────────┘
```

---

## 16. Timeline

| Time | Task | Deliverable |
|---|---|---|
| 0:00–0:20 | Arduino IDE + library setup | ESP32 responds to test sketch |
| 0:20–1:05 | Wire + test MAX30102 (all 5 pins) | Stable IR/RED readings + temperature |
| 1:05–1:35 | Verify HR + HRV + SpO₂ + Temp readings | All 4 values in valid ranges |
| 1:35–1:55 | Wire + test LEDs + buzzer | All indicators working |
| 1:55–2:40 | Flash full firmware (offline mode) | Complete sensor loop running |
| 2:40–3:10 | WiFi integration + backend connection | HTTP 200 responses |
| 3:10–4:30 | End-to-end integration with team | Dashboard shows live data |
| 4:30–5:00 | Build station enclosure | Clean, labeled, secure |
| 5:00+ | Demo rehearsal + backup preparation | Rock-solid demo |

---

*This document reflects the actual components on hand. Follow the build sequence exactly. Test each component individually before combining. The simpler the hardware, the more reliable the demo.*

**Go build it. 🔧🚀**