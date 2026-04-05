# CardioTwin AI — Product Requirements Document

**Version:** 1.0 | **Date:** February 21, 2026 | **Status:** FINAL — Ready for 24-Hour Sprint

> Implementation Note (April 2026): The live demo currently uses a default 5-reading calibration cycle for faster UX. Product target language in this PRD may still reference a 15-reading flow.

---

## 1. Mission & Theme Alignment

**Mission:** Build a working prototype in 24 hours that demonstrates real-time cardiometabolic risk scoring from live sensor data, delivered through a web dashboard and WhatsApp notifications.

**Hackathon Theme:** *"From Data to Prevention: AI as Your Health Partner"*

| Theme Word | Our Implementation |
|---|---|
| **Data** | Live biometric data from MAX30102 + NTC sensors |
| **Prevention** | Predictive risk scoring + what-if projections |
| **AI** | Adaptive risk engine + pattern detection |
| **Health Partner** | Real-time nudges via WhatsApp + dashboard |

---

## 2. Problem Statement

- **~11% of all deaths** in Nigeria are attributed to CVDs (WHO)
- **70% of cardiovascular deaths** occur in people who were **never screened**
- Nigeria has **~4 physicians per 10,000 people** — preventive cardiology is nearly non-existent
- No existing system makes the connection between **"what I just did"** and **"what my heart just felt"** immediate, tangible, and personal

> **Our Hypothesis:** If we give people a real-time, personalized score that visibly reacts to their physiological state, they will make better health decisions because consequences become immediate — not abstract.

---

## 3. Solution Overview

**CardioTwin AI** is a station-based health screening system with three layers:

1. **Sense** — Captures HR, HRV, SpO₂, and skin temperature from a finger-placed sensor station
2. **Score** — AI risk engine processes raw biometrics into a **CardioTwin Score (0–100)**
3. **Nudge** — Delivers alerts via web dashboard, WhatsApp, and physical vibration buzz

### Scope: IN ✅
- Working hardware station with finger sensor
- Real-time data streaming to Azure cloud
- CardioTwin Score algorithm (0–100, 4 zones)
- Live web dashboard with graphs and score gauge
- WhatsApp alert integration via Twilio
- What-if risk projection (static/pre-calculated)
- Before/after demo capability
- Vibration motor alert on station

### Scope: OUT ❌
- Wearable device (pitched as v2 vision only)
- Facial expression analysis
- Mobile native app (web PWA only)
- User authentication / multi-user accounts
- Deep learning models
- Medical-grade diagnostic claims

---

## 4. System Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                        CARDIOTWIN AI                             │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│   LAYER 1: SENSING                                               │
│   ┌───────────────────────┐                                      │
│   │     HEALTH STATION    │                                      │
│   │  ┌─────────────────┐  │     WiFi / HTTP POST                 │
│   │  │ ESP32           │  │ ──────────────────┐                  │
│   │  │ + MAX30102      │  │                   │                  │
│   │  │ + NTC Therm.    │  │                   │                  │
│   │  │ + Vibration     │  │                   │                  │
│   │  │   Motor         │  │                   │                  │
│   │  └─────────────────┘  │                   │                  │
│   └───────────────────────┘                   │                  │
│                                               ▼                  │
│   LAYER 2: MODELING                 ┌─────────────────────┐      │
│                                     │    AZURE CLOUD      │      │
│                                     │                     │      │
│                                     │  ┌───────────────┐  │      │
│                                     │  │ Data Ingestion│  │      │
│                                     │  │ (FastAPI)     │  │      │
│                                     │  └──────┬────────┘  │      │
│                                     │         │           │      │
│                                     │  ┌──────▼────────┐  │      │
│                                     │  │ Adaptive Risk │  │      │
│                                     │  │ Engine        │  │      │
│                                     │  │ (Scikit-learn)│  │      │
│                                     │  └──────┬────────┘  │      │
│                                     │         │           │      │
│                                     │  ┌──────▼────────┐  │      │
│                                     │  │ CardioTwin    │  │      │
│                                     │  │ Score API     │  │      │
│                                     │  │ + Session DB  │  │      │
│                                     │  └──────┬────────┘  │      │
│                                     └─────────┼───────────┘      │
│                                               │                  │
│   LAYER 3: PREDICTING               ┌────────┼────────┐         │
│                                      │        │        │         │
│                                      ▼        ▼        ▼         │
│                                ┌────────┐ ┌───────┐ ┌───────┐   │
│                                │  WEB   │ │WHATS- │ │  SMS  │   │
│                                │  DASH  │ │ APP   │ │FALLBK │   │
│                                │(Next.js│ │(Twilio│ │(Twilio│   │
│                                │  +     │ │  API) │ │  API) │   │
│                                │Tailwind│ │       │ │       │   │
│                                │  CSS)  │ │       │ │       │   │
│                                └────────┘ └───────┘ └───────┘   │
└──────────────────────────────────────────────────────────────────┘
```

---

## 5. The CardioTwin Score

The single most important feature — transforms complex multi-dimensional biometric data into one number anyone can understand.

### Score Zones

| Zone | Range | Label | Trigger |
|---|---|---|---|
| 🟢 Green | 80–100 | Thriving | No alert |
| 🟡 Yellow | 55–79 | Mild Strain | WhatsApp nudge |
| 🟠 Orange | 30–54 | Elevated Risk | WhatsApp + vibration buzz |
| 🔴 Red | 0–29 | Critical Strain | WhatsApp + vibration + urgent message |

### Scoring Weights

| Component | Weight | Why |
|---|---|---|
| HRV (RMSSD) | **40%** | Strongest non-invasive predictor of cardiac autonomic health |
| Heart Rate | **25%** | Direct indicator of cardiovascular load |
| SpO₂ | **20%** | Blood oxygenation — safety check for respiratory distress |
| Skin Temperature | **15%** | Correlates with stress response and inflammation |

### How It Works
1. **Baseline Calibration (first 30s):** Records resting HR, HRV, SpO₂, and temperature as personal reference
2. **Real-Time Scoring (every 2s):** Compares incoming data against baseline, calculates weighted composite
3. **Pattern Detection (over sessions):** Identifies personal risk patterns over time

---

## 6. Hardware Specification

### Station Design (Not a wearable — by design)

The MAX30102 requires firm, stable skin contact and minimal motion for accurate PPG readings. A station-based finger sensor gives **clinical-grade accuracy** every time, eliminates motion artifact risk, and avoids demo failures.

> During the pitch, frame the wearable as the v2 vision: *"The algorithm is built. The form factor evolves."*

### Components

| Component | Purpose | Est. Cost |
|---|---|---|
| ESP32-WROOM-32 | Microcontroller + WiFi | ~₦3,500 |
| MAX30102 | Heart Rate, HRV, SpO₂ | ~₦2,000 |
| 10kΩ NTC Thermistor | Skin Temperature | ~₦300 |
| 10kΩ Resistor | Voltage divider for NTC | ~₦50 |
| Mini Vibration Motor (3V) | Tactile alert | ~₦500 |
| 2N2222 NPN Transistor + 1kΩ Resistor | Motor driver | ~₦100 |
| Breadboard + Jumper Wires | Assembly | ~₦800 |
| Micro-USB Cable | Power + programming | ~₦500 |
| **TOTAL** | | **~₦7,750 (~$10)** |

### Wiring Reference

```
ESP32 PIN           →    COMPONENT
──────────────────────────────────────────
3.3V                →    MAX30102 VIN
GND                 →    MAX30102 GND
GPIO 21 (SDA)       →    MAX30102 SDA
GPIO 22 (SCL)       →    MAX30102 SCL
3.3V                →    10kΩ Resistor ──┐
GPIO 34 (ADC)       →    Junction ───────┤
GND                 →    NTC Thermistor ─┘
GPIO 25             →    1kΩ → 2N2222 Base
                         Collector → Motor → 3.3V
                         Emitter → GND
```

### Station Enclosure

Simple cardboard/foam box with a hole for the MAX30102 sensor on top. Labeled "Place Finger Here ☝️". Sensor MUST be secured firmly (hot glue) to prevent wobble during demo.

---

## 7. API Contract

All endpoints served from: `https://cardiotwin.azurewebsites.net`

### `POST /api/session/start`
Starts a new measurement session.

**Request:**
```json
{ "session_id": "demo", "user_phone": "+2348012345678" }
```
**Response:**
```json
{ "status": "session_started", "session_id": "demo" }
```

### `POST /api/reading`
Receives biometric reading from ESP32. Called every 2 seconds.

**Request:**
```json
{
  "bpm": 72, "hrv": 42.3, "spo2": 98.1,
  "temperature": 36.4, "timestamp": 45000, "session_id": "demo"
}
```
**Response (calibrating):**
```json
{
  "status": "calibrating", "readings_collected": 8,
  "readings_needed": 15, "alert": false
}
```
**Response (scored):**
```json
{
  "status": "scored", "score": 86.2, "zone": "GREEN",
  "zone_label": "Thriving", "zone_emoji": "🟢",
  "alert": false, "nudge_sent": false,
  "components": {
    "heart_rate": { "value": 72, "score": 95.2 },
    "hrv": { "value": 42.3, "score": 88.1 },
    "spo2": { "value": 98.1, "score": 100.0 },
    "temperature": { "value": 36.4, "score": 93.5 }
  },
  "baseline": {
    "resting_bpm": 71.5, "resting_hrv": 43.1,
    "normal_spo2": 98.0, "normal_temp": 36.35
  }
}
```

### `GET /api/score/{session_id}`
Returns latest score for frontend polling.

### `GET /api/history/{session_id}`
Returns all scores for chart rendering. Array of score objects with timestamps.

### `POST /api/predict`
What-if risk projection.

**Request:**
```json
{ "session_id": "demo", "days": 90 }
```
**Response:**
```json
{
  "current_score": 41.0, "projected_score": 35.2,
  "projected_resting_hr_increase_bpm": 6.8,
  "current_risk_category": "Elevated Risk",
  "projected_risk_category": "Critical Strain",
  "disclaimer": "Statistical projection only. Not a medical diagnosis."
}
```

---

## 8. Tech Stack

| Layer | Technology | Source |
|---|---|---|
| Microcontroller | ESP32 | Off-the-shelf |
| Sensors | MAX30102 + NTC Thermistor | Off-the-shelf |
| Firmware | Arduino C++ | Open source |
| Backend | Python FastAPI | Open source |
| AI/ML | Scikit-learn, NumPy | Open source |
| Cloud | Azure App Service + Cosmos DB | **GitHub Student Dev Pack** |
| Frontend | Next.js 14 + Tailwind CSS + Recharts | Open source |
| Notifications | Twilio WhatsApp + SMS | **GitHub Student Dev Pack** |
| Version Control | GitHub + GitHub Copilot | **GitHub Student Dev Pack** |

---

## 9. Team Roles & Responsibilities

```
                   ┌──────────────┐
                   │  PERSON 5    │
                   │  PITCH LEAD  │
                   │  & PM        │
                   └──────┬───────┘
                          │
          ┌───────────────┼───────────────┐
          │               │               │
   ┌──────▼──────┐ ┌──────▼──────┐ ┌──────▼──────┐
   │  PERSON 1   │ │  PERSON 2   │ │  PERSON 4   │
   │  HARDWARE   │ │  AI ENGINE  │ │  FRONTEND   │
   │  ENGINEER   │ │  ENGINEER   │ │  DEVELOPER  │
   └─────────────┘ └──────┬──────┘ └─────────────┘
                          │
                   ┌──────▼──────┐
                   │  PERSON 3   │
                   │  BACKEND    │
                   │  DEVELOPER  │
                   └─────────────┘
```

### Person 1 — Hardware Engineer
| Deliverable | Priority |
|---|---|
| Wire ESP32 + MAX30102 + NTC + vibration motor | 🔴 Critical |
| Write firmware: read HR, HRV, SpO₂, temperature | 🔴 Critical |
| Implement WiFi + HTTP POST to backend every 2s | 🔴 Critical |
| Vibration motor trigger on API alert response | 🟡 Medium |
| Clean station enclosure with finger label | 🟡 Medium |
| Calibrate sensor accuracy + integration test | 🔴 Critical |

**Key Specs:**
- Send JSON via HTTP POST every 2 seconds
- Finger detection: IR > 50,000 = finger present
- Reject HR outside 30–220 BPM
- HRV = RMSSD from beat-to-beat intervals
- SpO₂ from RED/IR ratio (linear approximation)
- Vibrate when API response contains `"alert": true`

### Person 2 — AI Engineer
| Deliverable | Priority |
|---|---|---|
| Design CardioTwin Score algorithm (weighted composite) | 🔴 Critical |
| Implement baseline calibration (first 15 readings) | 🔴 Critical |
| Build zone classification (Green/Yellow/Orange/Red) | 🔴 Critical |
| Build anomaly detection for real-time alerts | 🟡 Medium |
| Build what-if projection engine (trend extrapolation) | 🟡 Medium |
| Write nudge message templates per zone | 🔴 Critical |
| Tune weights/thresholds during integration | 🟡 Medium |

### Person 3 — Backend Developer (Python)
| Deliverable | Priority |
|---|---|
| Scaffold FastAPI project, deploy to Azure | 🔴 Critical |
| Implement `/api/reading` endpoint | 🔴 Critical |
| Implement `/api/score` + `/api/history` endpoints | 🔴 Critical |
| Implement `/api/session/start` endpoint | 🔴 Critical |
| Integrate Person 2's scoring engine | 🔴 Critical |
| Set up Twilio WhatsApp integration | 🔴 Critical |
| Implement `/api/predict` endpoint | 🟡 Medium |
| Set up CORS for frontend access | 🔴 Critical |

### Person 4 — Frontend Developer
| Deliverable | Priority |
|---|---|
| Scaffold Next.js + Tailwind CSS project | 🔴 Critical |
| Build animated CardioTwin Score gauge (circular, color-coded) | 🔴 Critical |
| Build real-time biometric cards (HR, HRV, SpO₂, Temp) | 🔴 Critical |
| Build real-time score line chart (Recharts) | 🔴 Critical |
| Implement 2-second polling from backend API | 🔴 Critical |
| Build before/after comparison view | 🟡 Medium |
| Build what-if simulator panel | 🟡 Medium |
| Polish: animations, transitions, responsive design | 🟡 Medium |

### Person 5 — Pitch Lead & PM
| Deliverable | Priority |
|---|---|
| Write pitch script (3 minutes) | 🔴 Critical |
| Build slide deck (8 slides max) | 🔴 Critical |
| Coordinate integration between all members | 🔴 Critical |
| Record backup demo video | 🔴 Critical |
| Run 3+ dress rehearsals | 🔴 Critical |
| Prepare Q&A answers for judges | 🔴 Critical |
| Research Nigeria CVD stats for pitch | 🟡 Medium |

---

## 10. 24-Hour Sprint Timeline

```
HOUR    TASK                                         OWNER
─────   ──────────────────────────────────────────   ──────────
 0-1    Kickoff: scope lock, repo setup, Azure       ALL
        provisioning, agree on API contracts

 1-4    Hardware: wire + test raw sensor readings     Person 1
        AI: design + code score algorithm            Person 2
        Backend: scaffold FastAPI + deploy Azure     Person 3
        Frontend: scaffold Next.js + design UI       Person 4
        PM: draft pitch narrative + start deck       Person 5

 4-8    Hardware: implement WiFi streaming            Person 1
        AI: baseline calibration + zone logic        Person 2
        Backend: /api/reading + /api/score live      Person 3
        Frontend: score gauge + biometric cards      Person 4
        PM: coordinate, write demo script            Person 5

 8-12   Hardware: test continuous streaming           Person 1
        AI: what-if projection engine                Person 2
        Backend: Twilio WhatsApp + /api/predict      Person 3
        Frontend: live chart + what-if panel         Person 4
        PM: first end-to-end integration test        Person 5

12-14   🛑 MANDATORY REST — 2 HOURS                  ALL
        (You WILL make worse decisions without rest)

14-18   Full integration: hardware→backend→frontend   ALL
        Bug fixing + edge case handling              ALL
        PM: record backup demo video                 Person 5

18-21   Polish: UI animations, loading states        Person 4
        Calibrate score thresholds with real data    Person 2
        Build clean station enclosure                Person 1
        Finalize pitch deck                          Person 5

21-23   Full dress rehearsal (3 TIMES MINIMUM)       ALL
        Fix any demo-breaking bugs                   ALL

23-24   Final prep: charge devices, test venue       ALL
        WiFi, load backup video, deep breaths
```

---

## 11. Demo Script (3 Minutes)

### Act 1 — The Hook (30s)
*"Every 33 seconds, someone dies of cardiovascular disease. In Nigeria, 7 out of 10 of those people were never screened. What if your body could warn you — not your doctor, not a hospital — but your body, in real time, before it's too late?"*

### Act 2 — Live Demo (90s)
1. Volunteer places finger on CardioTwin Station
2. Dashboard shows data streaming live → Score: **🟢 86 — Thriving**
3. Volunteer does 30s of burpees (presenter narrates the AI engine)
4. Volunteer returns, places finger again
5. Score drops live: **🟠 41 — Elevated Risk**
6. Vibration motor buzzes on station
7. WhatsApp message arrives on volunteer's phone
8. Show What-If: *"If this pattern continues 90 days → risk category shifts"*

### Act 3 — The Vision (45s)
*"Today: one person, one station, one score. Tomorrow: community health workers across Nigeria, each with a ₦8,000 CardioTwin device, screening entire villages in hours. Population-level dashboards helping state health ministries allocate resources where risk is highest."*

### Act 4 — The Close (15s)
*"From data, to prevention, to partnership. This is CardioTwin AI — your heart's early warning system."*

### 🛡️ BACKUP PLAN
Pre-record a full demo video the night before. If hardware fails, play the video. **Never demo without a backup.**

---

## 12. Risk Register

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| WiFi fails at venue | High | Critical | Test venue WiFi early. Backup: mobile hotspot. Emergency: pre-recorded video |
| MAX30102 gives erratic readings | Medium | High | Station-based (not wearable) = stable contact. Calibrate before demo. Have backup recorded data |
| Azure deployment issues | Medium | High | Deploy by Hour 8. Test early. Fallback: run locally on laptop |
| Twilio WhatsApp fails | Medium | Medium | Pre-join Twilio sandbox. Test with real number. Fallback: show SMS or mock notification |
| Team member burns out | High | High | Mandatory 2-hour rest at Hour 12-14. No hero coding |
| Integration breaks at Hour 20 | Medium | Critical | Integrate early (Hour 8 first test). API contracts agreed at Hour 0 |
| Judges question "Digital Twin" claim | High | High | We DON'T call it a digital twin. It's an "Adaptive Risk Model" — honest and defensible |

---

## 13. Prepared Judge Q&A

**Q: "Is this medically accurate?"**
> "CardioTwin is a wellness screening tool, not a medical device. Our MAX30102 sensor provides research-grade PPG data, and our scoring algorithm is based on published clinical correlations between HRV and cardiovascular risk. We clearly disclaim this in the UI."

**Q: "Why not a wearable?"**
> "Clinical-grade PPG requires stable skin contact. Even Apple Watch uses motion compensation algorithms that took years to develop. Our station gives accurate data every time. The wearable is our v2 — the intelligence is built today."

**Q: "How is this different from a Fitbit?"**
> "Fitbit gives you data. We give you a decision. Our CardioTwin Score collapses complex biometrics into one actionable number, and our nudge system delivers guidance through WhatsApp — where 93 million Nigerians already live. No app download required."

**Q: "Can this scale?"**
> "The hardware costs ₦8,000. The backend runs on Azure free tier. Community health workers could screen a village of 500 in a single day. The data aggregates into population-level risk heatmaps for state health ministries."

---

## 14. Data Privacy & Ethics

| Principle | Implementation |
|---|---|
| Encryption | TLS 1.3 in transit, Azure managed keys at rest |
| Compliance | Follows NDPR (Nigeria Data Protection Regulation) |
| Consent | Explicit opt-in before data collection |
| No Diagnosis | Wellness tool — clearly disclaimed throughout |
| Data Ownership | Users can export or delete all data |

---

## 15. Business Model (For Pitch)

| Stream | Model |
|---|---|
| **B2C** | Freemium — free basic score, paid insights (₦2,000/mo) |
| **B2B** | Corporate wellness dashboards, HMO partnerships (Leadway, AXA Mansard) |
| **B2G** | State health ministry screening tools, population CVD heatmaps |

---

## 16. What Makes This Win

| Differentiator | Why It Matters |
|---|---|
| **Working hardware prototype** | 90% of teams are software-only |
| **CardioTwin Score (0-100)** | One number anyone understands |
| **WhatsApp delivery** | Shows deep understanding of Nigerian users |
| **$10 hardware cost** | Proves accessibility at scale |
| **Honest AI claims** | "Adaptive Risk Model" builds trust with judges |
| **Clear business model** | Shows maturity beyond a hackathon |
| **Backup demo video** | Professional risk management |

---

> **Remember: You're not building a product in 24 hours. You're building a *story* backed by a working prototype. The story wins. The prototype proves you can deliver.**

**Go build it. 🚀🇳🇬