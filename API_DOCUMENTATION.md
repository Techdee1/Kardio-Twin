# CardioTwin API Documentation

Base URL: https://cardiotwin-jqrct.ondigitalcean.app

## Overview

CardioTwin provides real-time wellness scoring from biometric readings. A session starts in calibration mode, then transitions to scored responses after baseline is established.

Current implementation defaults to 5 calibration readings for a faster demo cycle. This is configurable in engine settings.

## Authentication

No authentication is currently required.

## Endpoints

### 1. Health Check

GET /health

Response

```json
{
  "status": "healthy"
}
```

### 2. Start Session

POST /api/session/start

Request body

```json
{
  "session_id": "session-123",
  "user_phone": "+2348000000000",
  "caregiver_phone": "+2348000000001",
  "caregiver_name": "Ada",
  "medical_professional_phone": "+2348000000002",
  "medical_professional_name": "Dr. Musa"
}
```

Notes

- Only `session_id` is required.
- Contact fields are optional and used for safety escalation workflows.

Response

```json
{
  "status": "session_started",
  "session_id": "session-123"
}
```

### 3. Submit Biometric Reading

POST /api/reading

Request body

```json
{
  "session_id": "session-123",
  "bpm": 72,
  "hrv": 45,
  "spo2": 98,
  "temperature": 36.6,
  "systolic_bp": 120,
  "diastolic_bp": 80,
  "source": "hardware"
}
```

Notes

- `source` is optional and typically `hardware` or `manual`.
- `systolic_bp` and `diastolic_bp` are optional.

Response (calibrating)

```json
{
  "status": "calibrating",
  "readings_collected": 3,
  "readings_needed": 5,
  "alert": false
}
```

Response (retake requested)

```json
{
  "status": "retake_requested",
  "message": "Signal quality too low. Please retake reading.",
  "signal_quality": "poor",
  "signal_confidence": 0.41
}
```

Response (scored)

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
    "heart_rate": { "value": 85, "score": 58.5 },
    "hrv": { "value": 35, "score": 65.6 },
    "spo2": { "value": 96, "score": 95.0 },
    "temperature": { "value": 37.0, "score": 96.0 }
  },
  "baseline": {
    "resting_bpm": 72.0,
    "resting_hrv": 45.0,
    "normal_spo2": 98.0,
    "normal_temp": 36.6
  },
  "source": "hardware",
  "signal_quality": "good",
  "signal_confidence": 0.92,
  "safety": {
    "is_safe": true,
    "escalation": "none",
    "red_flags": [],
    "safe_next_step": "Continue monitoring"
  },
  "alert_caregiver": false,
  "disclaimer": "This is a wellness screening tool, not a medical diagnosis."
}
```

### 4. Submit Manual Reading

POST /api/reading/manual

Request body

```json
{
  "session_id": "session-123",
  "bpm": 72,
  "hrv": 45,
  "spo2": 98,
  "temperature": 36.6,
  "systolic_bp": 120,
  "diastolic_bp": 80
}
```

Notes

- Only `session_id` and `bpm` are required.
- Missing `hrv`, `spo2`, and `temperature` are auto-filled with safe defaults by the backend.
- Response shape is identical to `POST /api/reading`.

### 5. Get Latest Score

GET /api/score/{session_id}

Response (calibrating)

```json
{
  "status": "calibrating",
  "readings_collected": 4,
  "readings_needed": 5
}
```

Response (scored)

```json
{
  "status": "scored",
  "score": 74.2,
  "zone": "YELLOW",
  "zone_label": "Mild Strain",
  "zone_emoji": "🟡"
}
```

### 6. Get Score History

GET /api/history/{session_id}

Response

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
  }
]
```

### 7. Get AI Nudge

GET /api/nudge/{session_id}

Response

```json
{
  "message": "Heads up! Your score shows mild strain. Consider a short break.",
  "zone": "YELLOW",
  "zone_label": "Mild Strain",
  "phone": null
}
```

### 8. Risk Prediction

POST /api/predict

Request body

```json
{
  "session_id": "session-123",
  "days": 30,
  "scenario": "deep_breathing"
}
```

Response

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

### 9. Send Alert

POST /api/alert

Request body

```json
{
  "to_phone": "+2348000000000",
  "message": "Please check on me.",
  "channel": "whatsapp"
}
```

Response

```json
{
  "status": "sent",
  "channel": "whatsapp"
}
```

### 10. Submit Alert Feedback

POST /api/feedback

Request body

```json
{
  "session_id": "session-123",
  "reading_id": 42,
  "alert_type": "tachycardia",
  "feedback": "helpful",
  "comment": "Matched how I felt"
}
```

Valid `feedback` values

- `helpful`
- `not_helpful`
- `false_alarm`

Response

```json
{
  "status": "ok",
  "message": "Feedback recorded. Thank you."
}
```

## Zones

| Zone | Score Range | Label |
|---|---|---|
| GREEN | 80-100 | Thriving |
| YELLOW | 55-79 | Mild Strain |
| ORANGE | 30-54 | Elevated Risk |
| RED | 0-29 | Critical Strain |

## Status Codes

| Code | Meaning |
|---|---|
| 200 | Success |
| 400 | Invalid request payload or domain validation error |
| 404 | Session not found |
| 422 | Schema validation error |
| 500 | Internal server error |

## Local Development Quick Check

```bash
# Start backend
python -m uvicorn main:app --host 0.0.0.0 --port 8000

# Health check
curl http://localhost:8000/health
```

OpenAPI docs are available at /docs when the API is running.
