# CardioTwin API Documentation

**Base URL:** `https://cardiotwin-jqrct.ondigitalocean.app`

## Overview

CardioTwin is a real-time cardiac health monitoring API that calculates a personalized health score (0-100) from biometric data. The system requires a 15-reading calibration phase to establish the user's baseline before producing scores.

## Authentication

Currently no authentication required. Add `Authorization: Bearer <token>` header when auth is implemented.

---

## Endpoints

### 1. Health Check

```
GET /health
```

**Response:**
```json
{
  "status": "healthy"
}
```

---

### 2. Start Session

Start a new measurement session for a user.

```
POST /api/session/start
```

**Request Body:**
```json
{
  "session_id": "string",  // Unique session identifier
  "user_id": "string"      // User identifier
}
```

**Response:**
```json
{
  "status": "session_started",
  "session_id": "abc123"
}
```

**Example:**
```javascript
const response = await fetch('https://cardiotwin-jqrct.ondigitalocean.app/api/session/start', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    session_id: 'session-' + Date.now(),
    user_id: 'user-123'
  })
});
```

---

### 3. Submit Biometric Reading

Submit real-time biometric data from sensors. First 15 readings are used for calibration.

```
POST /api/reading
```

**Request Body:**
```json
{
  "session_id": "string",
  "bpm": 72.0,           // Heart rate (beats per minute)
  "hrv": 45.0,           // Heart rate variability (ms)
  "spo2": 98.0,          // Blood oxygen saturation (%)
  "temperature": 36.6    // Body temperature (°C)
}
```

**Response (Calibrating - readings 1-15):**
```json
{
  "status": "calibrating",
  "readings_collected": 5,
  "readings_needed": 15,
  "alert": false
}
```

**Response (Scored - readings 16+):**
```json
{
  "status": "scored",
  "score": 74.2,
  "zone": "YELLOW",
  "zone_label": "Mild Strain",
  "zone_emoji": "🟡",
  "alert": false,
  "nudge_sent": false,
  "components": {
    "heart_rate": { "value": 85.0, "score": 58.5 },
    "hrv": { "value": 35.0, "score": 65.6 },
    "spo2": { "value": 96.0, "score": 95.0 },
    "temperature": { "value": 37.0, "score": 96.0 }
  },
  "baseline": {
    "resting_bpm": 72.0,
    "resting_hrv": 45.0,
    "normal_spo2": 98.0,
    "normal_temp": 36.6
  }
}
```

**Example:**
```javascript
const response = await fetch('https://cardiotwin-jqrct.ondigitalocean.app/api/reading', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    session_id: 'session-123',
    bpm: 75,
    hrv: 42,
    spo2: 97,
    temperature: 36.7
  })
});
const data = await response.json();

if (data.status === 'calibrating') {
  // Show progress bar: data.readings_collected / data.readings_needed
} else {
  // Display score: data.score, zone: data.zone_label
}
```

---

### 4. Get Latest Score

Get the most recent score for a session.

```
GET /api/score/{session_id}
```

**Response (Calibrating):**
```json
{
  "status": "calibrating",
  "readings_collected": 8,
  "readings_needed": 15
}
```

**Response (Ready):**
```json
{
  "status": "scored",
  "score": 74.2,
  "zone": "YELLOW",
  "zone_label": "Mild Strain",
  "zone_emoji": "🟡"
}
```

**Example:**
```javascript
const response = await fetch('https://cardiotwin-jqrct.ondigitalocean.app/api/score/session-123');
const data = await response.json();
```

---

### 5. Get Score History

Get all scores for a session (for charts/graphs).

```
GET /api/history/{session_id}
```

**Response:**
```json
[
  {
    "index": 0,
    "score": 87.6,
    "zone": "GREEN",
    "zone_label": "Thriving",
    "timestamp": 0
  },
  {
    "index": 1,
    "score": 82.3,
    "zone": "GREEN",
    "zone_label": "Thriving",
    "timestamp": 2000
  },
  {
    "index": 2,
    "score": 74.2,
    "zone": "YELLOW",
    "zone_label": "Mild Strain",
    "timestamp": 4000
  }
]
```

**Example (Chart.js integration):**
```javascript
const response = await fetch('https://cardiotwin-jqrct.ondigitalocean.app/api/history/session-123');
const history = await response.json();

// For Chart.js line chart
const chartData = {
  labels: history.map(h => h.index),
  datasets: [{
    label: 'CardioTwin Score',
    data: history.map(h => h.score),
    borderColor: history.map(h => getZoneColor(h.zone)),
    fill: false
  }]
};

function getZoneColor(zone) {
  return { GREEN: '#22c55e', YELLOW: '#eab308', ORANGE: '#f97316', RED: '#ef4444' }[zone];
}
```

---

### 6. Get AI Nudge

Get a personalized AI-generated health nudge based on current state.

```
GET /api/nudge/{session_id}
```

**Response:**
```json
{
  "message": "Heads up! Your CardioTwin Score shows mild strain. Consider taking a short break and some deep breaths. 💛",
  "zone": "YELLOW",
  "zone_label": "Mild Strain",
  "phone": null
}
```

**Example:**
```javascript
const response = await fetch('https://cardiotwin-jqrct.ondigitalocean.app/api/nudge/session-123');
const nudge = await response.json();
// Display nudge.message in a toast/notification
```

---

### 7. Risk Prediction

Get projected score over time (trend analysis).

```
POST /api/predict
```

**Request Body:**
```json
{
  "session_id": "string",
  "days": 30  // Prediction horizon (default: 90)
}
```

**Response:**
```json
{
  "current_score": 74.2,
  "projected_score": 60.6,
  "projected_resting_hr_increase_bpm": 2.0,
  "current_risk_category": "Mild Strain",
  "projected_risk_category": "Mild Strain",
  "disclaimer": "Statistical projection only. Not a medical diagnosis."
}
```

**Example:**
```javascript
const response = await fetch('https://cardiotwin-jqrct.ondigitalocean.app/api/predict', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    session_id: 'session-123',
    days: 30
  })
});
const prediction = await response.json();
```

---

### 8. Send Alert (Manual)

Manually trigger SMS/WhatsApp alert to emergency contact.

```
POST /api/alert
```

**Request Body:**
```json
{
  "session_id": "string",
  "phone": "+1234567890",     // Phone number with country code
  "channel": "whatsapp"       // "whatsapp" or "sms"
}
```

**Response:**
```json
{
  "status": "sent",
  "channel": "whatsapp",
  "message": "🚨 CardioTwin Alert: Your contact's score is 45.2 (High Strain). Please check on them."
}
```

---

## Zones Reference

| Zone | Score Range | Label | Color | Emoji |
|------|-------------|-------|-------|-------|
| GREEN | 80-100 | Thriving | `#22c55e` | 🟢 |
| YELLOW | 55-79 | Mild Strain | `#eab308` | 🟡 |
| ORANGE | 30-54 | Moderate Strain | `#f97316` | 🟠 |
| RED | 0-29 | High Strain | `#ef4444` | 🔴 |

---

## Score Components

The CardioTwin Score (0-100) is calculated from 4 weighted components:

| Component | Weight | Description |
|-----------|--------|-------------|
| HRV | 40% | Heart Rate Variability - primary stress indicator |
| Heart Rate | 25% | Deviation from personal resting baseline |
| SpO2 | 20% | Blood oxygen saturation |
| Temperature | 15% | Body temperature deviation |

---

## Typical Integration Flow

```
┌─────────────────────────────────────────────────────────────┐
│                    FRONTEND FLOW                            │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. User opens app                                          │
│     └── POST /api/session/start                             │
│                                                             │
│  2. Hardware sends biometrics (every 2 seconds)             │
│     └── POST /api/reading                                   │
│         ├── If calibrating: Show progress bar               │
│         └── If scored: Update dashboard                     │
│                                                             │
│  3. Dashboard displays:                                     │
│     ├── Current score (big number + zone color)             │
│     ├── Component breakdown (4 gauges)                      │
│     ├── Score history chart (GET /api/history)              │
│     └── AI nudge (GET /api/nudge)                           │
│                                                             │
│  4. Optional: Show 30-day projection                        │
│     └── POST /api/predict                                   │
│                                                             │
│  5. Emergency: Send alert to contact                        │
│     └── POST /api/alert                                     │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## React Hook Example

```javascript
import { useState, useEffect, useCallback } from 'react';

const API_BASE = 'https://cardiotwin-jqrct.ondigitalocean.app';

export function useCardioTwin(userId) {
  const [sessionId, setSessionId] = useState(null);
  const [status, setStatus] = useState('idle'); // idle, calibrating, ready
  const [score, setScore] = useState(null);
  const [zone, setZone] = useState(null);
  const [calibrationProgress, setCalibrationProgress] = useState(0);
  const [history, setHistory] = useState([]);

  // Start session
  const startSession = useCallback(async () => {
    const newSessionId = `session-${Date.now()}`;
    await fetch(`${API_BASE}/api/session/start`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ session_id: newSessionId, user_id: userId })
    });
    setSessionId(newSessionId);
    setStatus('calibrating');
    return newSessionId;
  }, [userId]);

  // Submit reading
  const submitReading = useCallback(async (bpm, hrv, spo2, temperature) => {
    if (!sessionId) return;
    
    const response = await fetch(`${API_BASE}/api/reading`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ session_id: sessionId, bpm, hrv, spo2, temperature })
    });
    const data = await response.json();

    if (data.status === 'calibrating') {
      setStatus('calibrating');
      setCalibrationProgress(data.readings_collected / data.readings_needed);
    } else {
      setStatus('ready');
      setScore(data.score);
      setZone({ code: data.zone, label: data.zone_label, emoji: data.zone_emoji });
    }
    return data;
  }, [sessionId]);

  // Fetch history
  const fetchHistory = useCallback(async () => {
    if (!sessionId) return;
    const response = await fetch(`${API_BASE}/api/history/${sessionId}`);
    const data = await response.json();
    setHistory(data);
    return data;
  }, [sessionId]);

  // Get nudge
  const getNudge = useCallback(async () => {
    if (!sessionId) return;
    const response = await fetch(`${API_BASE}/api/nudge/${sessionId}`);
    return response.json();
  }, [sessionId]);

  return {
    sessionId,
    status,
    score,
    zone,
    calibrationProgress,
    history,
    startSession,
    submitReading,
    fetchHistory,
    getNudge
  };
}
```

---

## Error Handling

All endpoints return standard HTTP status codes:

| Status | Meaning |
|--------|---------|
| 200 | Success |
| 400 | Bad request (invalid data) |
| 404 | Session not found |
| 422 | Validation error (check response body for details) |
| 500 | Server error |

**Validation Error Response:**
```json
{
  "detail": [
    {
      "type": "missing",
      "loc": ["body", "bpm"],
      "msg": "Field required",
      "input": { ... }
    }
  ]
}
```

---

## TypeScript Types

```typescript
interface BiometricReading {
  session_id: string;
  bpm: number;
  hrv: number;
  spo2: number;
  temperature: number;
}

interface CalibratingResponse {
  status: 'calibrating';
  readings_collected: number;
  readings_needed: number;
  alert: boolean;
}

interface ScoredResponse {
  status: 'scored';
  score: number;
  zone: 'GREEN' | 'YELLOW' | 'ORANGE' | 'RED';
  zone_label: string;
  zone_emoji: string;
  alert: boolean;
  nudge_sent: boolean;
  components: {
    heart_rate: { value: number; score: number };
    hrv: { value: number; score: number };
    spo2: { value: number; score: number };
    temperature: { value: number; score: number };
  };
  baseline: {
    resting_bpm: number;
    resting_hrv: number;
    normal_spo2: number;
    normal_temp: number;
  };
}

interface ScoreResponse {
  status: 'calibrating' | 'scored';
  score?: number;
  zone?: string;
  zone_label?: string;
  zone_emoji?: string;
  readings_collected?: number;
  readings_needed?: number;
}

interface HistoryEntry {
  index: number;
  score: number;
  zone: string;
  zone_label: string;
  timestamp: number;
}

interface NudgeResponse {
  message: string;
  zone: string;
  zone_label: string;
  phone: string | null;
}

interface PredictionResponse {
  current_score: number;
  projected_score: number;
  projected_resting_hr_increase_bpm: number;
  current_risk_category: string;
  projected_risk_category: string;
  disclaimer: string;
}
```

---

## Contact

Backend deployed at: https://cardiotwin-jqrct.ondigitalocean.app

OpenAPI docs: https://cardiotwin-jqrct.ondigitalocean.app/docs
