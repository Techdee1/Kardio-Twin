# CardioTwin AI Engine

A real-time cardiac digital twin system that analyzes biometric data to provide personalized health insights, risk predictions, and wellness nudges.

## Features

- **Baseline Calibration**: Adaptive personalized baselines from 12+ readings
- **Multi-metric Scoring**: Heart rate, HRV, SpO2, and temperature analysis
- **CardioTwin Score**: Weighted composite health score (0-100)
- **Zone Classification**: GREEN/YELLOW/ORANGE/RED health zones with urgency levels
- **Anomaly Detection**: Real-time alerts for physiological irregularities
- **AI-Powered Nudges**: Contextual wellness messages via Groq LLM
- **Risk Projection**: Future health trajectory predictions
- **What-If Scenarios**: Simulate intervention impacts

## Installation

```bash
# Clone the repository
git clone https://github.com/Techdee1/Kardio-Twin.git
cd Kardio-Twin

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env and add your GROQ_API_KEY
```

### Requirements
- Python 3.10+
- NumPy, SciPy, scikit-learn
- httpx (for async HTTP)
- pytest (for testing)

## Quick Start

```python
from ai_engine.engine import CardioTwinEngine
from ai_engine.nudges import Language

# Initialize engine
engine = CardioTwinEngine({
    "calibration_readings": 15,
    "enable_anomaly_detection": True,
})

# Create a user session
session_id = engine.create_session("user_001", language=Language.ENGLISH)

# Process biometric readings (calibration: 15+ readings)
for _ in range(15):
    result = engine.process_reading(session_id, {
        "heart_rate": 70,
        "hrv": 50,
        "spo2": 98,
        "temperature": 36.6,
    })

# Session is now active - process readings for insights
result = engine.process_reading(session_id, {
    "heart_rate": 72,
    "hrv": 48,
    "spo2": 98,
    "temperature": 36.7,
})

print(f"Zone: {result.zone}")  # Zone.GREEN
print(f"Score: {result.scores.cardiotwin_score}")  # 85.5
print(f"Message: {result.message}")

# Generate AI nudge (async)
import asyncio
nudge = asyncio.run(engine.generate_nudge(session_id))
print(f"Nudge: {nudge}")

# Get risk projection
projection = engine.project_risk(session_id, hours_ahead=24)
print(f"Projected scores: {projection.projected_scores[:5]}")

# Simulate intervention
scenario = engine.simulate_scenario(session_id, "deep_breathing")
print(f"Expected improvement: +{scenario.score_change} points")
```

## API Reference

### CardioTwinEngine

Main orchestration class for the digital twin system.

#### Constructor

```python
CardioTwinEngine(config: dict = None)
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `calibration_readings` | int | 15 | Readings needed for baseline |
| `max_readings_history` | int | 1000 | Max readings to retain |
| `enable_anomaly_detection` | bool | True | Enable anomaly alerts |

#### Methods

| Method | Returns | Description |
|--------|---------|-------------|
| `create_session(user_id, language)` | `str` | Create new user session |
| `process_reading(session_id, reading)` | `ProcessingResult` | Process biometric data |
| `get_session(session_id)` | `Session` | Get session details |
| `get_current_score(session_id)` | `float` | Current CardioTwin Score |
| `get_current_zone(session_id)` | `Zone` | Current health zone |
| `get_active_alerts(session_id)` | `List[Alert]` | Active anomaly alerts |
| `generate_nudge(session_id)` | `str` (async) | Generate AI wellness nudge |
| `project_risk(session_id, hours_ahead)` | `RiskProjection` | Future risk projection |
| `simulate_scenario(session_id, name)` | `WhatIfScenario` | Simulate intervention |
| `get_improvement_suggestions(session_id)` | `dict` | Recovery recommendations |
| `estimate_recovery_time(session_id)` | `dict` | Estimated recovery time |
| `end_session(session_id)` | `bool` | End user session |

### ProcessingResult

Result object returned from `process_reading()`.

| Attribute | Type | Description |
|-----------|------|-------------|
| `success` | bool | Processing succeeded |
| `zone` | Zone | Current health zone |
| `zone_changed` | bool | Zone changed from previous |
| `scores` | ScoreBreakdown | Component scores |
| `alerts` | List[Alert] | Triggered alerts |
| `message` | str | Human-readable summary |

### ScoreBreakdown

Component scores from biometric analysis.

| Attribute | Type | Weight | Description |
|-----------|------|--------|-------------|
| `heart_rate` | float | 25% | Heart rate score |
| `hrv` | float | 40% | HRV score (primary) |
| `spo2` | float | 20% | Oxygen saturation score |
| `temperature` | float | 15% | Temperature score |
| `cardiotwin_score` | float | - | Weighted composite |

### Zone Classification

| Zone | Score Range | Urgency | Description |
|------|-------------|---------|-------------|
| GREEN | 80-100 | 0 | Optimal health state |
| YELLOW | 55-79 | 1 | Mild concern, monitor |
| ORANGE | 30-54 | 2 | Moderate concern, take action |
| RED | 0-29 | 3 | Critical, immediate attention |

### Language Support

Nudges are available in multiple languages:

```python
from ai_engine.nudges import Language

Language.ENGLISH  # English
Language.PIDGIN   # Nigerian Pidgin
Language.YORUBA   # Yoruba
Language.IGBO     # Igbo
Language.HAUSA    # Hausa
```

## Module Reference

### ai_engine/validation.py
Input validation and sanitization for biometric readings.

```python
from ai_engine.validation import validate_reading, sanitize_reading

result = validate_reading({"heart_rate": 70, "hrv": 50})
# Returns: ValidationResult(valid=True, missing_fields=[], invalid_fields=[])

clean_data = sanitize_reading({"heart_rate": 70.5})
# Returns: {"heart_rate": 70.5, "hrv": 0.0, "spo2": 0.0, "temperature": 0.0}
```

### ai_engine/baseline.py
Personalized baseline calibration algorithm.

```python
from ai_engine.baseline import calibrate_baseline

readings = [{"bpm": 70, "hrv": 50, "spo2": 98, "temperature": 36.6}] * 12
baseline = calibrate_baseline(readings)
# Returns: PersonalBaseline with personalized reference values
```

### ai_engine/scoring.py
Component scoring functions with medical thresholds.

```python
from ai_engine.scoring import (
    score_heart_rate,
    score_hrv,
    score_spo2,
    score_temperature,
    compute_cardiotwin_score,
)

hr_score, hr_desc = score_heart_rate(70, baseline)  # (95.0, "Excellent")
hrv_score, hrv_desc = score_hrv(50, baseline)        # (85.0, "Good")
spo2_score, spo2_desc = score_spo2(98, baseline)     # (100.0, "Optimal")
temp_score, temp_desc = score_temperature(36.6, baseline)  # (100.0, "Normal")

composite = compute_cardiotwin_score(hr=70, hrv=50, spo2=98, temp=36.6, baseline=baseline)
# Returns: (90.25, "Excellent overall wellness")
```

### ai_engine/zones.py
Health zone classification and context.

```python
from ai_engine.zones import classify_zone, get_zone_info, Zone

zone = classify_zone(85.0)  # Zone.GREEN
info = get_zone_info(85.0)
# Returns: ZoneInfo(zone=GREEN, label="Optimal", urgency=0, ...)
```

### ai_engine/anomaly.py
Anomaly detection and alert generation.

```python
from ai_engine.anomaly import detect_anomalies

result = detect_anomalies(
    current={"heart_rate": 140, "hrv": 15, "spo2": 92, "temperature": 38.5},
    baseline=baseline,
    history=reading_history,
)
# Returns: AnomalyDetectionResult with alerts
```

### ai_engine/nudges.py
AI-powered wellness nudge generation via Groq.

```python
from ai_engine.nudges import generate_nudge, NudgeConfig
from ai_engine.zones import get_zone_info

zone_info = get_zone_info(75.0)
config = NudgeConfig(
    language=Language.ENGLISH,
    include_recommendations=True,
)

# Async function
nudge = await generate_nudge(zone_info, config=config)
# Returns: Nudge with personalized message
```

### ai_engine/projection.py
Risk projection and what-if scenario simulation.

```python
from ai_engine.projection import (
    project_risk,
    simulate_scenario,
    get_improvement_path,
)

# Project future risk
projection = project_risk(score_history, hours_ahead=24)

# Simulate intervention
scenario = simulate_scenario("meditation", current_score=65.0)
# Returns: WhatIfScenario with expected improvement

# Get improvement recommendations
steps = get_improvement_path(current_score=55.0)
# Returns: List[WhatIfScenario] prioritized by impact
```

## Configuration

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `GROQ_API_KEY` | Yes* | Groq API key for LLM nudges |

*Required for AI-powered nudges. Falls back to template-based nudges if not set.

### Engine Configuration

```python
config = {
    # Calibration
    "calibration_readings": 15,      # Readings for baseline (min: 12)
    
    # History
    "max_readings_history": 1000,    # Max readings to retain
    
    # Features
    "enable_anomaly_detection": True,
    "enable_projections": True,
    
    # Scoring weights
    "weights": {
        "hrv": 0.40,        # Primary indicator
        "heart_rate": 0.25,
        "spo2": 0.20,
        "temperature": 0.15,
    },
}

engine = CardioTwinEngine(config)
```

## Testing

```bash
# Run all tests
pytest ai_engine/tests/ -v

# Run specific test module
pytest ai_engine/tests/test_engine.py -v

# Run integration tests
pytest ai_engine/tests/test_integration.py -v

# Run with coverage
pytest ai_engine/tests/ --cov=ai_engine --cov-report=html
```

### Test Coverage

| Module | Tests | Coverage |
|--------|-------|----------|
| validation.py | 17 | 100% |
| baseline.py | 21 | 100% |
| scoring.py | 49 | 100% |
| zones.py | 69 | 100% |
| anomaly.py | 65 | 100% |
| nudges.py | 45 | 100% |
| projection.py | 52 | 100% |
| engine.py | 65 | 100% |
| integration | 27 | - |
| **Total** | **410** | - |

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    CardioTwinEngine                          │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │   Session   │  │  Baseline   │  │   History   │         │
│  │  Management │  │ Calibration │  │   Tracker   │         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
└─────────────────────────────────────────────────────────────┘
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                   Processing Pipeline                        │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │Validation│→ │ Scoring  │→ │  Zones   │→ │ Anomaly  │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │
└─────────────────────────────────────────────────────────────┘
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                    Output Generation                         │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐                  │
│  │  Nudges  │  │Projection│  │  Alerts  │                  │
│  │ (Groq)   │  │  Engine  │  │          │                  │
│  └──────────┘  └──────────┘  └──────────┘                  │
└─────────────────────────────────────────────────────────────┘
```

## CardioTwin Score Algorithm

The CardioTwin Score is a weighted composite health metric:

```
CardioTwin Score = (HRV × 0.40) + (HR × 0.25) + (SpO2 × 0.20) + (Temp × 0.15)
```

**Weight Rationale:**
- **HRV (40%)**: Primary indicator of autonomic nervous system health
- **Heart Rate (25%)**: Primary cardiovascular metric
- **SpO2 (20%)**: Critical oxygen saturation levels  
- **Temperature (15%)**: Regulatory health indicator

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Write tests for new functionality
4. Ensure all tests pass (`pytest ai_engine/tests/`)
5. Commit changes (`git commit -m 'Add amazing feature'`)
6. Push to branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

## License

This project is part of the Hackathon submission for CardioTwin.

## Acknowledgments

- Groq for LLM API access
- Medical reference ranges based on established clinical guidelines