# CardioTwin AI Engine — Technical Specification Document

**Version:** 1.0  
**Date:** February 21, 2026  
**Owner:** AI Engineer (Person 2)  
**Status:** READY FOR IMPLEMENTATION

---

## 1. Executive Summary

This document specifies the complete AI/ML pipeline for the CardioTwin system. Your role as the AI Engineer is to build the **Adaptive Risk Scoring Engine** that transforms raw biometric sensor data into actionable cardiovascular risk insights.

**Your Deliverables:**
1. CardioTwin Score Algorithm (0-100 scale)
2. Baseline Calibration System
3. Zone Classification Logic
4. Anomaly Detection for Real-time Alerts
5. What-if Risk Projection Engine
6. **Grok AI-Powered Nudge System** (Dynamic, Personalized)
7. Component Scoring Functions
8. **Grok-Powered Conversational Insights**
9. **Natural Language Score Explanations**

**Technology Stack:**
- Python 3.10+
- NumPy for numerical computations
- SciPy for statistical functions
- Scikit-learn for data processing
- **Grok API (xAI)** for dynamic AI-powered messaging and insights
- Requests / httpx for API communication
- Pandas for data management (optional)

**Integration Point:** Your code will be imported as a Python module by the Backend Developer (Person 3) into their FastAPI application.

---

## 2. System Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    AI ENGINE PIPELINE                        │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  INPUT: Raw Biometric Reading                                │
│  ┌────────────────────────────────────────────────────┐     │
│  │ { bpm: 72, hrv: 42.3, spo2: 98.1, temp: 36.4 }    │     │
│  └───────────────────┬────────────────────────────────┘     │
│                      │                                       │
│  ┌───────────────────▼────────────────────────────────┐     │
│  │  STAGE 1: Data Validation & Sanitization           │     │
│  │  - Range checks (HR: 30-220, HRV: 0-200, etc.)     │     │
│  │  - Outlier detection (z-score > 3)                 │     │
│  │  - Missing value handling                          │     │
│  └───────────────────┬────────────────────────────────┘     │
│                      │                                       │
│  ┌───────────────────▼────────────────────────────────┐     │
│  │  STAGE 2: Baseline Calibration                     │     │
│  │  - First 15 readings → establish personal baseline │     │
│  │  - Calculate: mean HR, mean HRV, mean SpO₂, temp   │     │
│  │  - Store baseline in session state                 │     │
│  └───────────────────┬────────────────────────────────┘     │
│                      │                                       │
│  ┌───────────────────▼────────────────────────────────┐     │
│  │  STAGE 3: Component Scoring (4 components)         │     │
│  │  - Heart Rate Score (0-100)      → Weight: 25%     │     │
│  │  - HRV Score (0-100)              → Weight: 40%     │     │
│  │  - SpO₂ Score (0-100)             → Weight: 20%     │     │
│  │  - Temperature Score (0-100)      → Weight: 15%     │     │
│  └───────────────────┬────────────────────────────────┘     │
│                      │                                       │
│  ┌───────────────────▼────────────────────────────────┐     │
│  │  STAGE 4: Composite CardioTwin Score               │     │
│  │  Score = Σ(component_score × weight)               │     │
│  │  Result: 0-100 continuous score                    │     │
│  └───────────────────┬────────────────────────────────┘     │
│                      │                                       │
│  ┌───────────────────▼────────────────────────────────┐     │
│  │  STAGE 5: Zone Classification                      │     │
│  │  - GREEN: 80-100 (Thriving)                        │     │
│  │  - YELLOW: 55-79 (Mild Strain)                     │     │
│  │  - ORANGE: 30-54 (Elevated Risk)                   │     │
│  │  - RED: 0-29 (Critical Strain)                     │     │
│  └───────────────────┬────────────────────────────────┘     │
│                      │                                       │
│  ┌───────────────────▼────────────────────────────────┐     │
│  │  STAGE 6: Anomaly Detection & Alert Trigger        │     │
│  │  - Sudden score drop > 20 points                   │     │
│  │  - Zone transition downward                        │     │
│  │  - Critical threshold breach (score < 30)          │     │
│  └───────────────────┬────────────────────────────────┘     │
│                      │                                       │
│  ┌───────────────────▼────────────────────────────────┐     │
│  │  STAGE 7: Grok AI Message Generation               │     │
│  │  - Contextual nudge messages                       │     │
│  │  - Natural language score explanations            │     │
│  │  - Personalized recommendations                    │     │
│  └───────────────────┬────────────────────────────────┘     │
│                      │                                       │
│  OUTPUT: Scored Reading + Alert + AI Message                │
│  ┌────────────────────────────────────────────────────┐     │
│  │ { score: 86.2, zone: "GREEN", alert: false,       │     │
│  │   ai_message: "...", components: {...} }           │     │
│  └────────────────────────────────────────────────────┘     │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## 3. Input Data Specification

### 3.1 Raw Reading Format

Every 2 seconds, you'll receive a reading from the Hardware Engineer via the Backend:

```python
{
    "bpm": float,           # Heart rate in beats per minute
    "hrv": float,           # HRV (RMSSD) in milliseconds
    "spo2": float,          # Blood oxygen saturation percentage
    "temperature": float,   # Skin temperature in Celsius
    "timestamp": int,       # Milliseconds since session start
    "session_id": str       # Unique session identifier
}
```

### 3.2 Expected Ranges (Physiological Bounds)

| Parameter | Valid Range | Typical Resting | Post-Exercise | Units |
|-----------|-------------|-----------------|---------------|-------|
| **bpm** | 30 - 220 | 60 - 100 | 100 - 180 | beats/min |
| **hrv** | 0 - 200 | 20 - 100 | 10 - 50 | ms (RMSSD) |
| **spo2** | 80 - 100 | 95 - 100 | 90 - 97 | % |
| **temperature** | 30.0 - 42.0 | 35.5 - 37.5 | 36.0 - 38.0 | °C |

### 3.3 Data Quality Indicators

**Valid Reading Criteria:**
- All values within physiological bounds
- No `null` or `NaN` values
- `spo2 >= 85` (below this = sensor error or medical emergency)
- `bpm` not changing by > 40 BPM between consecutive readings (motion artifact)

---

## 4. Baseline Calibration System

### 4.1 Purpose

Establish a **personalized reference point** for each user. Two people with the same heart rate can have very different cardiovascular health states. Baseline calibration normalizes scores relative to each individual's resting state.

### 4.2 Calibration Process

**Duration:** First 15 readings (~30 seconds at 2-second intervals)

**Algorithm:**
```python
def calibrate_baseline(readings: List[Dict]) -> Dict:
    """
    Calculate baseline from first 15 valid readings.
    
    Args:
        readings: List of calibration readings
        
    Returns:
        {
            "resting_bpm": float,      # Mean HR
            "resting_hrv": float,      # Mean HRV
            "normal_spo2": float,      # Mean SpO₂
            "normal_temp": float,      # Mean temperature
            "calibration_complete": bool
        }
    """
    # Remove outliers using IQR method
    clean_readings = remove_outliers(readings)
    
    # Require at least 12 valid readings
    if len(clean_readings) < 12:
        return {"calibration_complete": False}
    
    baseline = {
        "resting_bpm": np.mean([r["bpm"] for r in clean_readings]),
        "resting_hrv": np.mean([r["hrv"] for r in clean_readings]),
        "normal_spo2": np.mean([r["spo2"] for r in clean_readings]),
        "normal_temp": np.mean([r["temperature"] for r in clean_readings]),
        "calibration_complete": True
    }
    
    return baseline
```

### 4.3 Outlier Removal (IQR Method)

```python
def remove_outliers(data: List[float], param: str) -> List[Dict]:
    """
    Remove statistical outliers using Interquartile Range method.
    """
    values = [d[param] for d in data]
    q1, q3 = np.percentile(values, [25, 75])
    iqr = q3 - q1
    lower_bound = q1 - (1.5 * iqr)
    upper_bound = q3 + (1.5 * iqr)
    
    return [d for d in data if lower_bound <= d[param] <= upper_bound]
```

### 4.4 Edge Cases

| Condition | Handling |
|-----------|----------|
| Fewer than 12 valid readings after 15 attempts | Extend calibration window to 20 readings |
| User moved during calibration | Flag high variance, restart calibration |
| All readings identical (sensor stuck) | Return error, require sensor check |
| First reading is post-exercise | Detect high HR (>100), warn user to rest |

---

## 5. Component Scoring Functions

Each biometric parameter gets scored 0-100 based on deviation from baseline and clinical risk thresholds.

### 5.1 Heart Rate Score (Weight: 25%)

**Principle:** Lower resting HR = better cardiovascular fitness. Elevated HR = increased cardiac load.

**Formula:**
```python
def score_heart_rate(current_bpm: float, baseline_bpm: float) -> float:
    """
    Score heart rate on 0-100 scale.
    
    Clinical context:
    - Resting HR 40-60: Excellent (athletes)
    - Resting HR 60-80: Good
    - Resting HR 80-100: Fair
    - Resting HR >100: Tachycardia risk
    """
    # Calculate percentage increase from baseline
    percent_increase = ((current_bpm - baseline_bpm) / baseline_bpm) * 100
    
    # Scoring curve
    if percent_increase <= 0:
        # Below baseline = excellent
        score = 100
    elif percent_increase <= 10:
        # 0-10% increase = good
        score = 100 - (percent_increase * 2)  # Linear decay: 100 → 80
    elif percent_increase <= 25:
        # 10-25% increase = moderate
        score = 80 - ((percent_increase - 10) * 2.67)  # 80 → 40
    elif percent_increase <= 50:
        # 25-50% increase = concerning
        score = 40 - ((percent_increase - 25) * 1.2)  # 40 → 10
    else:
        # >50% increase = critical
        score = max(0, 10 - ((percent_increase - 50) * 0.2))  # 10 → 0
    
    return np.clip(score, 0, 100)
```

**Rationale:**
- A 10% HR increase (e.g., 70→77 BPM) is normal variation
- A 25% increase (e.g., 70→87 BPM) indicates mild stress
- A 50% increase (e.g., 70→105 BPM) indicates significant cardiovascular load

### 5.2 HRV Score (Weight: 40%)

**Principle:** Higher HRV = better autonomic balance. Low HRV = stress, fatigue, or cardiac strain.

**Formula:**
```python
def score_hrv(current_hrv: float, baseline_hrv: float) -> float:
    """
    Score HRV (RMSSD) on 0-100 scale.
    
    Clinical context:
    - HRV > 50ms: Excellent recovery
    - HRV 30-50ms: Good
    - HRV 20-30ms: Moderate stress
    - HRV < 20ms: High stress/overtraining
    
    Note: HRV DECREASES under stress (inverse to HR)
    """
    # Calculate percentage decrease from baseline
    percent_decrease = ((baseline_hrv - current_hrv) / baseline_hrv) * 100
    
    # Scoring curve (HRV drop = bad)
    if percent_decrease <= 0:
        # Above baseline = excellent
        score = 100
    elif percent_decrease <= 15:
        # 0-15% decrease = good
        score = 100 - (percent_decrease * 1.33)  # 100 → 80
    elif percent_decrease <= 30:
        # 15-30% decrease = moderate
        score = 80 - ((percent_decrease - 15) * 2)  # 80 → 50
    elif percent_decrease <= 50:
        # 30-50% decrease = concerning
        score = 50 - ((percent_decrease - 30) * 1.5)  # 50 → 20
    else:
        # >50% decrease = critical
        score = max(0, 20 - ((percent_decrease - 50) * 0.4))  # 20 → 0
    
    return np.clip(score, 0, 100)
```

**Rationale:**
- HRV is the most sensitive non-invasive marker of cardiac autonomic function
- 40% weight because it's the best predictor of cardiovascular risk
- Decreases precede heart rate increases during stress response

### 5.3 SpO₂ Score (Weight: 20%)

**Principle:** Normal SpO₂ is 95-100%. Below 90% is hypoxemia.

**Formula:**
```python
def score_spo2(current_spo2: float, baseline_spo2: float) -> float:
    """
    Score blood oxygen saturation on 0-100 scale.
    
    Clinical context:
    - SpO₂ ≥ 95%: Normal
    - SpO₂ 90-94%: Mild hypoxemia
    - SpO₂ 85-89%: Moderate hypoxemia
    - SpO₂ < 85%: Severe (medical emergency)
    """
    # Absolute thresholds (more important than baseline)
    if current_spo2 >= 97:
        score = 100
    elif current_spo2 >= 95:
        # 95-97%: Excellent
        score = 100 - ((97 - current_spo2) * 5)  # 100 → 90
    elif current_spo2 >= 92:
        # 92-95%: Good
        score = 90 - ((95 - current_spo2) * 10)  # 90 → 60
    elif current_spo2 >= 88:
        # 88-92%: Concerning
        score = 60 - ((92 - current_spo2) * 10)  # 60 → 20
    else:
        # < 88%: Critical
        score = max(0, 20 - ((88 - current_spo2) * 2))  # 20 → 0
    
    return np.clip(score, 0, 100)
```

**Rationale:**
- SpO₂ is a safety threshold, not a performance metric
- Absolute values matter more than baseline deviation
- Below 90% requires immediate medical attention

### 5.4 Temperature Score (Weight: 15%)

**Principle:** Elevated skin temperature correlates with inflammation and stress response.

**Formula:**
```python
def score_temperature(current_temp: float, baseline_temp: float) -> float:
    """
    Score skin temperature on 0-100 scale.
    
    Clinical context:
    - Skin temp 35.5-36.5°C: Normal
    - Increase > 1°C: Inflammation or stress
    - Decrease > 1°C: Poor circulation
    """
    # Calculate deviation from baseline
    deviation = abs(current_temp - baseline_temp)
    
    # Scoring curve (deviation = bad)
    if deviation <= 0.3:
        # ±0.3°C: Normal variation
        score = 100
    elif deviation <= 0.8:
        # 0.3-0.8°C: Mild
        score = 100 - ((deviation - 0.3) * 40)  # 100 → 80
    elif deviation <= 1.5:
        # 0.8-1.5°C: Moderate
        score = 80 - ((deviation - 0.8) * 42.86)  # 80 → 50
    else:
        # > 1.5°C: Significant
        score = max(0, 50 - ((deviation - 1.5) * 20))  # 50 → 0
    
    return np.clip(score, 0, 100)
```

**Rationale:**
- Skin temperature is a proxy for sympathetic nervous system activation
- Lowest weight (15%) because it's the least specific marker
- Both increases and decreases are concerning

---

## 6. CardioTwin Composite Score

### 6.1 Weighted Average Formula

```python
def calculate_cardiotwin_score(
    hr_score: float,
    hrv_score: float,
    spo2_score: float,
    temp_score: float
) -> float:
    """
    Calculate final CardioTwin Score as weighted composite.
    
    Weights based on clinical evidence for CVD risk prediction:
    - HRV: 40% (strongest autonomic predictor)
    - HR: 25% (direct cardiac load)
    - SpO₂: 20% (safety critical)
    - Temp: 15% (systemic inflammation proxy)
    """
    weights = {
        "hrv": 0.40,
        "hr": 0.25,
        "spo2": 0.20,
        "temp": 0.15
    }
    
    score = (
        hrv_score * weights["hrv"] +
        hr_score * weights["hr"] +
        spo2_score * weights["spo2"] +
        temp_score * weights["temp"]
    )
    
    return round(score, 1)  # Return to 1 decimal place
```

### 6.2 Score Interpretation Table

| Score Range | Zone | Label | Cardiovascular State |
|-------------|------|-------|---------------------|
| 80 - 100 | 🟢 GREEN | Thriving | Optimal autonomic balance, low cardiac load |
| 55 - 79 | 🟡 YELLOW | Mild Strain | Slight stress response, manageable |
| 30 - 54 | 🟠 ORANGE | Elevated Risk | Significant physiological stress, attention needed |
| 0 - 29 | 🔴 RED | Critical Strain | Severe stress/strain, immediate rest recommended |

---

## 7. Zone Classification

### 7.1 Zone Assignment Logic

```python
def classify_zone(score: float) -> Dict:
    """
    Assign risk zone based on CardioTwin Score.
    
    Returns:
        {
            "zone": str,           # "GREEN", "YELLOW", "ORANGE", "RED"
            "zone_label": str,     # Human-readable label
            "zone_emoji": str,     # Visual indicator
            "zone_color": str      # Hex color for UI
        }
    """
    if score >= 80:
        return {
            "zone": "GREEN",
            "zone_label": "Thriving",
            "zone_emoji": "🟢",
            "zone_color": "#10b981"
        }
    elif score >= 55:
        return {
            "zone": "YELLOW",
            "zone_label": "Mild Strain",
            "zone_emoji": "🟡",
            "zone_color": "#f59e0b"
        }
    elif score >= 30:
        return {
            "zone": "ORANGE",
            "zone_label": "Elevated Risk",
            "zone_emoji": "🟠",
            "zone_color": "#f97316"
        }
    else:
        return {
            "zone": "RED",
            "zone_label": "Critical Strain",
            "zone_emoji": "🔴",
            "zone_color": "#ef4444"
        }
```

### 7.2 Zone Thresholds Rationale

**Green (80-100):** Only 20% deviation from optimal. User is in recovery/resting state.

**Yellow (55-79):** Mild cardiovascular activation. Typical after light physical activity or mild mental stress.

**Orange (30-54):** Moderate-to-high stress. Seen after vigorous exercise or significant emotional stress. Requires attention.

**Red (0-29):** Severe physiological strain. Multiple parameters significantly deviated. Immediate rest recommended.

---

## 8. Anomaly Detection & Alert System

### 8.1 Alert Trigger Conditions

An **alert** should be triggered when ANY of the following occur:

```python
def detect_anomaly(
    current_score: float,
    previous_score: float,
    current_zone: str,
    previous_zone: str,
    session_history: List[float]
) -> Dict:
    """
    Detect anomalous patterns that warrant user notification.
    
    Returns:
        {
            "alert": bool,
            "alert_reason": str,
            "alert_severity": str  # "low", "medium", "high"
        }
    """
    alert_triggered = False
    reason = None
    severity = "low"
    
    # RULE 1: Sudden score drop > 20 points
    score_drop = previous_score - current_score
    if score_drop > 20:
        alert_triggered = True
        reason = "Sudden score drop detected"
        severity = "medium"
    
    # RULE 2: Zone downgrade (e.g., GREEN → YELLOW)
    zone_order = {"GREEN": 4, "YELLOW": 3, "ORANGE": 2, "RED": 1}
    if zone_order.get(current_zone, 0) < zone_order.get(previous_zone, 0):
        alert_triggered = True
        reason = f"Zone transition: {previous_zone} → {current_zone}"
        severity = "medium" if current_zone in ["YELLOW", "ORANGE"] else "high"
    
    # RULE 3: Critical threshold breach
    if current_score < 30:
        alert_triggered = True
        reason = "Critical strain threshold breached"
        severity = "high"
    
    # RULE 4: Sustained decline (3+ consecutive drops)
    if len(session_history) >= 4:
        recent = session_history[-4:]
        if all(recent[i] > recent[i+1] for i in range(len(recent)-1)):
            alert_triggered = True
            reason = "Sustained decline in score"
            severity = "medium"
    
    return {
        "alert": alert_triggered,
        "alert_reason": reason,
        "alert_severity": severity
    }
```

### 8.2 Alert Response

When `alert: true`, the backend should:
1. Set `"alert": true` in API response (triggers vibration motor on hardware)
2. Send WhatsApp nudge message
3. Log alert in database for pattern analysis

---

## 9. Grok AI-Powered Nudge & Insights System

### 9.1 Overview

Instead of static templates, we use **Grok API** to generate dynamic, contextual, and personalized health messages. This enables:

✅ **Natural conversations** with users about their health  
✅ **Context-aware recommendations** based on full biometric history  
✅ **Adaptive tone** (supportive when stressed, motivational when thriving)  
✅ **Follow-up insights** that reference previous sessions  
✅ **Nigerian cultural context** (local idioms, appropriate medical advice)

### 9.2 Grok API Configuration

```python
import os
import requests
from typing import Dict, List

GROK_API_KEY = os.getenv("KARDIO_TWIN_API_KEY")
GROK_API_URL = "https://api.x.ai/v1/chat/completions"

class GrokClient:
    """
    Client for Grok API integration.
    """
    def __init__(self, api_key: str = GROK_API_KEY):
        self.api_key = api_key
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
    
    def generate_completion(
        self,
        messages: List[Dict],
        model: str = "grok-beta",
        temperature: float = 0.7,
        max_tokens: int = 500
    ) -> str:
        """
        Generate completion from Grok API.
        
        Args:
            messages: List of chat messages [{"role": "system/user", "content": "..."}]
            model: Grok model to use
            temperature: Creativity (0.0-1.0)
            max_tokens: Maximum response length
            
        Returns:
            Generated text response
        """
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        
        try:
            response = requests.post(
                GROK_API_URL,
                headers=self.headers,
                json=payload,
                timeout=10
            )
            response.raise_for_status()
            
            result = response.json()
            return result["choices"][0]["message"]["content"]
        
        except Exception as e:
            # Fallback to basic message on error
            return self._fallback_message()
    
    def _fallback_message(self) -> str:
        """Fallback message if API fails."""
        return "Your CardioTwin Score has been updated. Continue monitoring your health."
```

### 9.3 Dynamic Nudge Generation

```python
def generate_ai_nudge(
    score: float,
    zone: str,
    baseline: Dict,
    components: Dict,
    session_history: List[Dict] = None,
    previous_messages: List[str] = None
) -> Dict:
    """
    Generate personalized nudge message using Grok AI.
    
    Returns:
        {
            "title": str,
            "message": str,
            "action": str,
            "tone": str  # "urgent", "supportive", "motivational"
        }
    """
    grok = GrokClient()
    
    # Build context for Grok
    context = {
        "score": score,
        "zone": zone,
        "baseline": baseline,
        "components": components
    }
    
    # Identify key insights
    worst_component = min(
        components.items(),
        key=lambda x: x[1]["score"]
    )
    
    hr_change = components["heart_rate"]["value"] - baseline["resting_bpm"]
    hrv_change = components["hrv"]["value"] - baseline["resting_hrv"]
    
    # Build system prompt
    system_prompt = f"""
You are CardioTwin AI, a compassionate health companion for cardiovascular wellness in Nigeria.

Your role:
- Explain health metrics in simple, non-medical language
- Provide actionable recommendations based on biometric data
- Be culturally sensitive to Nigerian context
- Use supportive, non-alarmist tone (unless critical)
- Keep messages concise (3-4 sentences max)
- Use emojis appropriately

Current situation:
- CardioTwin Score: {score:.1f}/100 ({zone} zone)
- Heart Rate: {components['heart_rate']['value']:.0f} BPM (baseline: {baseline['resting_bpm']:.0f})
- HRV: {components['hrv']['value']:.1f}ms (baseline: {baseline['resting_hrv']:.1f})
- SpO₂: {components['spo2']['value']:.1f}%
- Temperature: {components['temperature']['value']:.1f}°C

Worst performing metric: {worst_component[0]} (score: {worst_component[1]['score']:.1f}/100)
"""
    
    # Build user prompt based on zone
    if zone == "RED":
        user_prompt = (
            f"The user's CardioTwin Score is {score:.1f} (Critical Strain). "
            f"Their heart rate increased by {hr_change:.0f} BPM and HRV dropped by {abs(hrv_change):.1f}ms. "
            "Generate an urgent but calm message with immediate action steps. "
            "Include when to seek medical attention."
        )
    elif zone == "ORANGE":
        user_prompt = (
            f"The user's CardioTwin Score is {score:.1f} (Elevated Risk). "
            f"They're under moderate cardiovascular stress. "
            "Provide supportive guidance to reduce strain and recover."
        )
    elif zone == "YELLOW":
        user_prompt = (
            f"The user's CardioTwin Score is {score:.1f} (Mild Strain). "
            "This is normal variation. Provide reassuring tips for recovery."
        )
    else:  # GREEN
        user_prompt = (
            f"The user's CardioTwin Score is {score:.1f} (Thriving). "
            "Celebrate their good health and encourage them to maintain it."
        )
    
    # Add historical context if available
    if session_history and len(session_history) > 5:
        trend = "improving" if session_history[-1] > session_history[-5] else "declining"
        user_prompt += f" Their score is {trend} over the session."
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]
    
    # Generate with Grok
    ai_message = grok.generate_completion(
        messages=messages,
        temperature=0.7,  # Balanced creativity
        max_tokens=300
    )
    
    # Determine action label
    action_map = {
        "RED": "REST NOW",
        "ORANGE": "SLOW DOWN",
        "YELLOW": "MONITOR",
        "GREEN": "KEEP GOING"
    }
    
    # Determine tone
    tone_map = {
        "RED": "urgent",
        "ORANGE": "supportive",
        "YELLOW": "reassuring",
        "GREEN": "motivational"
    }
    
    # Generate title using Grok (shorter prompt)
    title_messages = [
        {
            "role": "system",
            "content": "Generate a 3-5 word title for a health notification. Use appropriate emoji."
        },
        {
            "role": "user",
            "content": f"CardioTwin Score: {score:.1f}, Zone: {zone}"
        }
    ]
    
    ai_title = grok.generate_completion(
        messages=title_messages,
        temperature=0.5,
        max_tokens=20
    )
    
    return {
        "title": ai_title.strip(),
        "message": ai_message.strip(),
        "action": action_map[zone],
        "tone": tone_map[zone]
    }
```

### 9.4 Natural Language Score Explanation

```python
def explain_score_with_ai(
    score: float,
    zone: str,
    components: Dict,
    baseline: Dict
) -> str:
    """
    Generate natural language explanation of CardioTwin Score.
    
    Example output:
    "Your CardioTwin Score of 86 means your heart is in excellent shape right now. 
    Your heart rate variability is especially strong, showing good recovery capacity. 
    Your heart is beating calmly at 72 BPM, just slightly above your normal resting rate."
    """
    grok = GrokClient()
    
    system_prompt = """
You are a health educator explaining cardiovascular metrics to everyday Nigerians.

Guidelines:
- Explain what the CardioTwin Score means in practical terms
- Translate medical terms into everyday language
- Make it personal (use "your heart", "your body")
- Be encouraging and educational
- Keep it 2-3 sentences
- Avoid medical jargon
"""
    
    user_prompt = f"""
Explain this CardioTwin Score:

Score: {score:.1f}/100 ({zone} zone)

Breakdown:
- Heart Rate: {components['heart_rate']['value']:.0f} BPM (normal: {baseline['resting_bpm']:.0f}) - Score: {components['heart_rate']['score']:.1f}/100
- HRV: {components['hrv']['value']:.1f}ms (normal: {baseline['resting_hrv']:.1f}) - Score: {components['hrv']['score']:.1f}/100
- Blood Oxygen: {components['spo2']['value']:.1f}% - Score: {components['spo2']['score']:.1f}/100
- Temperature: {components['temperature']['value']:.1f}°C - Score: {components['temperature']['score']:.1f}/100

What does this mean for the user's cardiovascular health?
"""
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]
    
    explanation = grok.generate_completion(
        messages=messages,
        temperature=0.6,
        max_tokens=200
    )
    
    return explanation.strip()
```

### 9.5 Conversational Q&A Support

```python
def ask_cardiotwin_ai(
    user_question: str,
    current_score: float,
    session_data: Dict
) -> str:
    """
    Answer user questions about their health data conversationally.
    
    Examples:
    - "Why did my score drop?"
    - "What is HRV?"
    - "Should I be worried?"
    - "How can I improve my score?"
    """
    grok = GrokClient()
    
    system_prompt = f"""
You are CardioTwin AI, answering questions about the user's cardiovascular health.

User's current data:
- CardioTwin Score: {current_score:.1f}/100
- Recent biometrics: {session_data}

Guidelines:
- Answer directly and concisely
- Reference their actual data when relevant
- Educate without overwhelming
- Always include disclaimer if medical advice is asked
- Be warm and supportive
"""
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_question}
    ]
    
    answer = grok.generate_completion(
        messages=messages,
        temperature=0.5,
        max_tokens=250
    )
    
    return answer.strip()
```

### 9.6 Fallback Templates (Backup)

In case Grok API fails, maintain minimal fallback templates:

```python
FALLBACK_TEMPLATES = {
    "RED": "⚠️ Your CardioTwin Score is {score:.1f} (Critical). Please rest immediately.",
    "ORANGE": "🟠 Your score is {score:.1f} (Elevated Risk). Consider taking a break.",
    "YELLOW": "🟡 Your score is {score:.1f} (Mild Strain). You're doing okay.",
    "GREEN": "🟢 Your score is {score:.1f} (Thriving). Excellent!"
}
```

---

## 10. What-If Risk Projection Engine

### 10.1 Purpose

Show users the consequence of sustained behavioral patterns: *"If your current cardiovascular load continues for 90 days, here's your projected risk."*

### 10.2 Projection Algorithm

```python
def project_risk(
    current_score: float,
    session_history: List[float],
    projection_days: int = 90
) -> Dict:
    """
    Project future risk based on current trend.
    
    Algorithm:
    1. Calculate trend from recent session history
    2. Extrapolate linearly (conservative)
    3. Apply physiological bounds (score can't go < 0 or > 100)
    4. Estimate secondary effects (resting HR increase)
    
    Args:
        current_score: Most recent CardioTwin Score
        session_history: List of historical scores
        projection_days: Forecast horizon (default: 90 days)
        
    Returns:
        {
            "current_score": float,
            "projected_score": float,
            "projected_resting_hr_increase_bpm": float,
            "current_risk_category": str,
            "projected_risk_category": str,
            "projection_days": int,
            "disclaimer": str
        }
    """
    # Calculate trend from last 10 readings (or all if fewer)
    recent = session_history[-10:] if len(session_history) >= 10 else session_history
    
    if len(recent) < 3:
        # Not enough data for projection
        return {
            "error": "Insufficient data for projection",
            "current_score": current_score
        }
    
    # Linear regression to find trend
    x = np.arange(len(recent))
    y = np.array(recent)
    slope, intercept = np.polyfit(x, y, 1)
    
    # Project forward (1 reading per 2 seconds, 43,200 readings per day)
    readings_per_day = 43200
    future_readings = projection_days * readings_per_day
    projected_score = intercept + slope * (len(recent) + future_readings)
    
    # Apply bounds
    projected_score = np.clip(projected_score, 0, 100)
    
    # Estimate resting HR increase based on score decline
    # Rule of thumb: 10-point score drop ≈ 2-3 BPM resting HR increase
    score_decline = current_score - projected_score
    hr_increase = (score_decline / 10) * 2.5 if score_decline > 0 else 0
    
    # Classify zones
    current_zone = classify_zone(current_score)["zone_label"]
    projected_zone = classify_zone(projected_score)["zone_label"]
    
    return {
        "current_score": round(current_score, 1),
        "projected_score": round(projected_score, 1),
        "projected_resting_hr_increase_bpm": round(hr_increase, 1),
        "current_risk_category": current_zone,
        "projected_risk_category": projected_zone,
        "projection_days": projection_days,
        "trend_direction": "declining" if slope < 0 else "stable" if abs(slope) < 0.1 else "improving",
        "disclaimer": (
            "This is a statistical projection based on your recent pattern. "
            "It assumes no behavior change. Actual outcomes depend on lifestyle, "
            "stress, sleep, and other factors. Not a medical diagnosis."
        )
    }
```

### 10.3 Projection Limitations

**Honest disclaimers to include:**
- Linear extrapolation is simplistic (real physiology is non-linear)
- Short-term data (hackathon demo) limits accuracy
- Doesn't account for interventions (exercise, diet changes, medication)
- Not a medical prediction — educational tool only

---

## 11. Complete API Response Format

### 11.1 During Calibration

```python
{
    "status": "calibrating",
    "readings_collected": 8,
    "readings_needed": 15,
    "alert": False,
    "message": "Establishing your baseline... Please remain still."
}
```

### 11.2 After Calibration (Scored)

```python
{
    "status": "scored",
    "score": 86.2,
    "zone": "GREEN",
    "zone_label": "Thriving",
    "zone_emoji": "🟢",
    "zone_color": "#10b981",
    "alert": False,
    "alert_reason": None,
    "alert_severity": None,
    "nudge_sent": False,
    "components": {
        "heart_rate": {
            "value": 72,
            "score": 95.2,
            "status": "excellent"
        },
        "hrv": {
            "value": 42.3,
            "score": 88.1,
            "status": "good"
        },
        "spo2": {
            "value": 98.1,
            "score": 100.0,
            "status": "optimal"
        },
        "temperature": {
            "value": 36.4,
            "score": 93.5,
            "status": "normal"
        }
    },
    "baseline": {
        "resting_bpm": 71.5,
        "resting_hrv": 43.1,
        "normal_spo2": 98.0,
        "normal_temp": 36.35
    },
    "timestamp": 45000
}
```

---

## 12. Implementation Requirements

### 12.1 Code Structure

Your deliverable should be a Python module with this structure:

```
ai_engine/
├── __init__.py
├── scoring.py           # Core scoring functions
├── baseline.py          # Calibration logic
├── anomaly.py           # Alert detection
├── projection.py        # What-if engine
├── nudges.py            # Message templates
├── validation.py        # Input validation
└── tests/
    ├── test_scoring.py
    ├── test_baseline.py
    └── test_integration.py
```

### 12.2 Main Entry Point

```python
# In ai_engine/__init__.py

class CardioTwinEngine:
    """
    Main AI engine class.
    """
    def __init__(self):
        self.sessions = {}  # Store session state
    
    def process_reading(self, reading: Dict) -> Dict:
        """
        Main entry point: process a raw reading and return scored result.
        """
        session_id = reading["session_id"]
        
        # Initialize session if new
        if session_id not in self.sessions:
            self.sessions[session_id] = {
                "calibration_readings": [],
                "baseline": None,
                "history": [],
                "previous_score": None,
                "previous_zone": None
            }
        
        session = self.sessions[session_id]
        
        # Validate reading
        if not validate_reading(reading):
            return {"error": "Invalid reading data"}
        
        # CALIBRATION PHASE
        if session["baseline"] is None:
            session["calibration_readings"].append(reading)
            
            if len(session["calibration_readings"]) >= 15:
                session["baseline"] = calibrate_baseline(
                    session["calibration_readings"]
                )
                if not session["baseline"]["calibration_complete"]:
                    return {
                        "status": "calibrating",
                        "readings_collected": len(session["calibration_readings"]),
                        "readings_needed": 20,
                        "alert": False
                    }
            else:
                return {
                    "status": "calibrating",
                    "readings_collected": len(session["calibration_readings"]),
                    "readings_needed": 15,
                    "alert": False
                }
        
        # SCORING PHASE
        baseline = session["baseline"]
        
        # Score each component
        hr_score = score_heart_rate(reading["bpm"], baseline["resting_bpm"])
        hrv_score = score_hrv(reading["hrv"], baseline["resting_hrv"])
        spo2_score = score_spo2(reading["spo2"], baseline["normal_spo2"])
        temp_score = score_temperature(reading["temperature"], baseline["normal_temp"])
        
        # Calculate composite score
        cardiotwin_score = calculate_cardiotwin_score(
            hr_score, hrv_score, spo2_score, temp_score
        )
        
        # Classify zone
        zone_info = classify_zone(cardiotwin_score)
        
        # Detect anomalies
        session["history"].append(cardiotwin_score)
        anomaly_info = detect_anomaly(
            cardiotwin_score,
            session["previous_score"] or cardiotwin_score,
            zone_info["zone"],
            session["previous_zone"] or "GREEN",
            session["history"]
        )
        
        # Store for next iteration
        session["previous_score"] = cardiotwin_score
        session["previous_zone"] = zone_info["zone"]
        
        # Build response
        response = {
            "status": "scored",
            "score": cardiotwin_score,
            "zone": zone_info["zone"],
            "zone_label": zone_info["zone_label"],
            "zone_emoji": zone_info["zone_emoji"],
            "zone_color": zone_info["zone_color"],
            "alert": anomaly_info["alert"],
            "alert_reason": anomaly_info.get("alert_reason"),
            "alert_severity": anomaly_info.get("alert_severity"),
            "nudge_sent": False,  # Backend will set this after sending
            "components": {
                "heart_rate": {
                    "value": reading["bpm"],
                    "score": hr_score,
                    "status": self._get_status_label(hr_score)
                },
                "hrv": {
                    "value": reading["hrv"],
                    "score": hrv_score,
                    "status": self._get_status_label(hrv_score)
                },
                "spo2": {
                    "value": reading["spo2"],
                    "score": spo2_score,
                    "status": self._get_status_label(spo2_score)
                },
                "temperature": {
                    "value": reading["temperature"],
                    "score": temp_score,
                    "status": self._get_status_label(temp_score)
                }
            },
            "baseline": baseline,
            "timestamp": reading["timestamp"]
        }
        
        return response
    
    def _get_status_label(self, score: float) -> str:
        """Convert numeric score to status label."""
        if score >= 80:
            return "excellent"
        elif score >= 60:
            return "good"
        elif score >= 40:
            return "fair"
        else:
            return "concerning"
```

### 12.3 Dependencies

```python
# requirements.txt for AI module
numpy>=1.24.0
scipy>=1.10.0
scikit-learn>=1.2.0
```

---

## 13. Testing & Validation

### 13.1 Unit Test Checklist

- [ ] `score_heart_rate()` returns 100 when HR = baseline
- [ ] `score_heart_rate()` returns ~40 when HR = baseline * 1.25
- [ ] `score_hrv()` returns 100 when HRV >= baseline
- [ ] `score_hrv()` decreases as HRV drops
- [ ] `score_spo2()` returns 100 when SpO₂ >= 97%
- [ ] `score_spo2()` returns < 30 when SpO₂ < 90%
- [ ] `score_temperature()` handles both increases and decreases
- [ ] `calculate_cardiotwin_score()` weights sum to 1.0
- [ ] `classify_zone()` boundaries are correct (80, 55, 30)
- [ ] `detect_anomaly()` triggers on >20 point drop
- [ ] `calibrate_baseline()` requires 12+ valid readings
- [ ] `remove_outliers()` removes IQR extremes

### 13.2 Integration Test Scenarios

**Scenario 1: Resting Baseline**
```python
# Input: 15 readings at rest (HR=70, HRV=45, SpO2=98, Temp=36.2)
# Expected: Baseline established, score ≈ 95-100 (Thriving)
```

**Scenario 2: Post-Exercise**
```python
# Input: After 30s burpees (HR=140, HRV=22, SpO2=94, Temp=37.1)
# Expected: Score ≈ 35-45 (Elevated Risk), alert=True, vibration triggered
```

**Scenario 3: Gradual Recovery**
```python
# Input: 5 minutes of readings showing HR declining, HRV increasing
# Expected: Score trending upward, zone transitions ORANGE → YELLOW → GREEN
```

**Scenario 4: Sensor Error**
```python
# Input: SpO2=82% (below valid threshold)
# Expected: Validation error or critical alert
```

### 13.3 Real-World Validation

During integration with hardware:

1. **Baseline accuracy:** Record your own resting vitals with medical-grade device, compare to our baseline
2. **Exercise response:** Do jumping jacks, verify score drops appropriately
3. **Recovery tracking:** Rest for 5 minutes, verify score returns to baseline
4. **Edge cases:** Test with motion artifacts, finger removal, extreme values

---

## 14. Performance Requirements

| Metric | Target | Critical? |
|--------|--------|-----------|
| **Processing latency** | < 50ms per reading | ✅ Yes |
| **Memory footprint** | < 100 MB for 1000 sessions | 🟡 Nice-to-have |
| **Score stability** | No wild swings (±5 points/reading max in steady state) | ✅ Yes |
| **Calibration time** | 30 seconds (15 readings × 2s) | ✅ Yes |
| **Alert false positive rate** | < 10% | 🟡 Nice-to-have |

---

## 15. Scientific References

Your algorithm is based on established clinical research:

### 15.1 HRV and Cardiovascular Risk

> **Tsuji et al. (1996):** "Reduced heart rate variability and mortality risk in an elderly cohort." *Circulation*, 90(2), 878-883.
> - Found: HRV (RMSSD) < 20ms associated with 2x mortality risk

> **Task Force of ESC/NASPE (1996):** "Heart rate variability: Standards of measurement, physiological interpretation, and clinical use."
> - Established RMSSD as gold standard for short-term HRV assessment

### 15.2 Resting Heart Rate

> **Kumar et al. (2017):** "Resting heart rate as a cardiovascular risk factor." *Cardiology Research and Practice*.
> - Each 10 BPM increase in resting HR → 18% higher CV mortality

### 15.3 SpO₂ Thresholds

> **WHO Guidelines (2011):** "Pulse oximetry training manual."
> - SpO₂ 90-94%: Mild hypoxemia
> - SpO₂ < 90%: Requires medical intervention

---

## 16. Edge Cases & Error Handling

### 16.1 Data Quality Issues

| Issue | Detection | Handling |
|-------|-----------|----------|
| **Finger removed mid-session** | SpO₂ drops to 0, IR value < 50000 | Pause scoring, prompt user to replace finger |
| **Motion artifact** | HR jumps > 40 BPM between readings | Reject reading, don't update score |
| **Sensor saturated** | All values identical for 5+ readings | Flag error, restart session |
| **Unrealistic values** | HR > 220 or < 30 BPM | Reject reading, log warning |

### 16.2 Session Management

| Scenario | Handling |
|----------|----------|
| **Session timeout** | After 10 min inactivity, archive session |
| **User restarts during calibration** | Clear partial calibration, start fresh |
| **Multiple concurrent sessions** | Each session_id maintains independent state |

---

## 17. Calibration & Tuning Guide

### 17.1 Weight Adjustment

The initial weights (HRV 40%, HR 25%, SpO₂ 20%, Temp 15%) are based on clinical literature. However, during integration testing, you may need to adjust.

**Tuning process:**
1. Collect 10+ test sessions (resting + post-exercise)
2. Manually label each as "Green", "Yellow", "Orange", or "Red" based on subjective state
3. Calculate confusion matrix
4. If misclassifications occur, adjust weights by ±5%
5. Re-validate

**Example:** If scores are too sensitive to temperature changes, reduce temp weight from 15% to 10%, distribute to other components.

### 17.2 Zone Threshold Adjustment

Current thresholds:
- Green/Yellow: 80
- Yellow/Orange: 55
- Orange/Red: 30

If you find too many false alarms in yellow zone, lower the threshold to 50. If critical alerts are missed, raise red threshold to 35.

**Rule of thumb:** Optimize for minimizing false negatives in RED zone (missing a real problem is worse than a false alarm).

---

## 18. Integration Checklist

Before handing off to Backend Developer:

- [ ] All component scoring functions implemented and tested
- [ ] Baseline calibration handles edge cases (outliers, insufficient data)
- [ ] CardioTwin Score calculation matches specification
- [ ] Zone classification boundaries correct
- [ ] Anomaly detection triggers appropriately
- [ ] Nudge message templates populated
- [ ] What-if projection engine functional
- [ ] Input validation catches bad data
- [ ] API response format matches specification
- [ ] Unit tests pass (>80% coverage)
- [ ] Integration test with synthetic data successful
- [ ] Code documented with docstrings
- [ ] Dependencies listed in requirements.txt
- [ ] Module can be imported: `from ai_engine import CardioTwinEngine`

---

## 19. Timeline (Your 24-Hour Sprint)

### Hours 1-4: Core Algorithm
- [ ] Set up Python environment
- [ ] Implement 4 component scoring functions
- [ ] Implement CardioTwin composite score
- [ ] Write unit tests for scoring
- [ ] **Deliverable:** Scoring module working with hardcoded baseline

### Hours 4-8: Calibration & Classification
- [ ] Implement baseline calibration
- [ ] Implement zone classification
- [ ] Implement anomaly detection
- [ ] Test with synthetic reading sequences
- [ ] **Deliverable:** Complete pipeline (input → baseline → score → zone → alert)

### Hours 8-12: Projections & Nudges
- [ ] Implement what-if projection engine
- [ ] Write nudge message templates
- [ ] Create main `CardioTwinEngine` class
- [ ] Integration test with Backend Developer (first handoff)
- [ ] **Deliverable:** Complete AI module ready for backend integration

### Hours 12-14: 🛑 MANDATORY REST

### Hours 14-18: Integration & Tuning
- [ ] Fix bugs discovered during hardware integration
- [ ] Tune weights/thresholds with real sensor data
- [ ] Validate scoring accuracy with test subjects
- [ ] **Deliverable:** Calibrated, production-ready AI engine

### Hours 18-21: Polish & Edge Cases
- [ ] Add error handling for all edge cases
- [ ] Write comprehensive docstrings
- [ ] Final validation with Frontend (check score display)
- [ ] **Deliverable:** Bulletproof system ready for demo

### Hours 21-24: Demo Prep
- [ ] Help PM with pitch script (explain algorithm simply)
- [ ] Prepare to answer technical questions from judges
- [ ] Test full end-to-end flow 3+ times

---

## 20. Communication with Backend Developer (Person 3)

### 20.1 What Backend Needs from You

1. **Python module they can import:**
   ```python
   from ai_engine import CardioTwinEngine
   engine = CardioTwinEngine()
   result = engine.process_reading(reading_data)
   ```

2. **Clear API:** Your `process_reading()` function should accept a dict and return a dict (no complex objects)

3. **Session state management:** Your engine tracks session state internally

4. **What-if endpoint:** Provide a separate function:
   ```python
   projection = engine.project_risk(session_id, days=90)
   ```

5. **Nudge message generation:**
   ```python
   message = engine.generate_nudge(session_id)
   ```

### 20.2 What You Need from Backend

1. **Valid input data:** Backend validates input before passing to you
2. **Session ID:** Unique identifier for each user session
3. **Persistent storage:** Backend stores baseline and history (you keep in memory for active sessions)
4. **Alert delivery:** Backend sends WhatsApp when you return `alert: true`

### 20.3 Integration Meeting (Hour 8)

At Hour 8, sit down with Backend Developer and:
- Test your module with their FastAPI endpoint
- Verify response format matches frontend expectations
- Test alert triggering end-to-end (reading → your code → backend → WhatsApp)
- Fix any interface mismatches

---

## 21. Judge Q&A Prep (Technical)

**Q: "Why these specific weights?"**
> "We used clinical evidence: HRV has the strongest correlation with cardiovascular outcomes (0.7-0.8 in meta-analyses), so it gets 40%. Heart rate is a direct load indicator (25%). SpO₂ is a critical safety threshold (20%). Temperature is the least specific but correlates with systemic stress (15%)."

**Q: "Is this machine learning?"**
> "It's adaptive in that it personalizes to each user's baseline, but it's not a trained ML model. We're using clinical rules-based algorithms. For a 24-hour hackathon, this is more reliable than training a model on limited data. The architecture is designed to incorporate ML in v2 once we have population-scale data."

**Q: "How accurate is HRV from a MAX30102?"**
> "MAX30102 provides millisecond-resolution PPG, sufficient for RMSSD calculation. Academic studies show consumer PPG sensors achieve 85-95% agreement with ECG for HRV. Our station-based design eliminates motion artifact, the main error source."

**Q: "What if someone has a medical condition?"**
> "We clearly disclaim this is not diagnostic. Users with known conditions should consult their physician. Our baseline calibration personalizes to their physiology, so the system tracks *their* normal vs. abnormal, not a population average."

**Q: "Can this detect heart attacks?"**
> "No. We detect stress and strain, not acute coronary events. If someone has chest pain or severe symptoms, we tell them to seek immediate medical care. This is a wellness tool, not a diagnostic device."

---

## 22. Success Criteria

By the end of 24 hours, you should have:

✅ **Working code:** AI engine processes readings and returns valid scores  
✅ **Accurate scoring:** Before/after demo shows clear score difference  
✅ **Alert system functional:** Vibration + WhatsApp trigger on threshold breach  
✅ **What-if projections:** Realistic extrapolations based on trends  
✅ **Zero crashes:** Handles all edge cases gracefully  
✅ **Judge-ready explanations:** Can explain every algorithm decision in 30 seconds

---

## 23. Final Checklist

**Before Demo:**
- [ ] Test with 3+ volunteers (different body types, fitness levels)
- [ ] Verify score drops significantly after exercise
- [ ] Verify score recovers during rest
- [ ] Confirm alerts trigger appropriately
- [ ] Practice explaining algorithm to non-technical person in <60 seconds
- [ ] Pre-calculate example what-if scenarios for pitch

**During Demo:**
- [ ] Have backup data ready if live scoring fails
- [ ] Be prepared to explain any score that seems "wrong"
- [ ] Emphasize personalization (baseline calibration)
- [ ] Highlight safety (SpO₂ thresholds)

**Backup Plan:**
- [ ] Pre-recorded score sequence if hardware fails
- [ ] Slide with algorithm flowchart
- [ ] Printed example calculations

---

## 24. Resources & References

### Code Examples
- HRV calculation: https://github.com/Aura-healthcare/hrv-analysis
- Z-score anomaly detection: `scipy.stats.zscore`
- Linear regression: `numpy.polyfit`

### Clinical References
- Heart Rate Variability Standards: https://doi.org/10.1161/01.CIR.93.5.1043
- WHO Pulse Oximetry Manual: https://www.who.int/publications/i/item/9789241547758
- CVD Risk Prediction: Framingham Study guidelines

### Nigerian Context
- Nigeria CVD Statistics: WHO Global Health Observatory
- NDPR Compliance: https://ndpr.nitda.gov.ng

---

## 25. Contact & Escalation

**If you get stuck:**

1. **Algorithm questions:** Review clinical references in Section 15
2. **Integration issues:** Sync with Backend Developer (Person 3)
3. **Demo concerns:** Alert PM (Person 5) immediately
4. **Sensor data quality:** Coordinate with Hardware Engineer (Person 1)

**Critical blockers:**
- If scoring doesn't correlate with subjective state → Tune weights (Section 17.1)
- If too many false alerts → Adjust zone thresholds (Section 17.2)
- If calibration takes too long → Reduce required readings to 10 (but test accuracy)

---

## 26. Post-Hackathon Vision (v2 Ideas)

Once you have real data and more time:

1. **Train ML model:** Use collected data to train XGBoost or Random Forest for better personalization
2. **Pattern recognition:** Detect sleep debt, overtraining, chronic stress
3. **Multi-session learning:** Track baselines over weeks/months, detect degradation
4. **Population-level insights:** Aggregate anonymized data for public health heatmaps
5. **Intervention A/B testing:** Recommend breathing exercises, measure efficacy

---

> **Remember:** You're building the brain of the CardioTwin system. The hardware captures data, the frontend displays it beautifully, but YOU transform noise into insight. Your algorithm is what makes this "AI" and not just a fancy sensor dashboard.

> **The goal isn't perfection—it's a compelling demo that shows THIS WORKS. Make the score VISIBLY react to exercise. Make the alerts FEEL urgent. Make the what-if projection MOTIVATE behavior change.**

**Now go build the intelligence. 🧠🚀**

---

**END OF AI ENGINE PRD**
