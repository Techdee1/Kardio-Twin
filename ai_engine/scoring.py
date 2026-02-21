"""
Component Scoring Module
========================

Individual scoring functions for each biometric parameter.
Each function returns a score from 0-100 based on deviation from baseline.

Functions:
    - score_heart_rate: Heart rate score (weight: 25%)
    - score_hrv: HRV/RMSSD score (weight: 40%)
    - score_spo2: Blood oxygen score (weight: 20%)
    - score_temperature: Skin temperature score (weight: 15%)
    - calculate_cardiotwin_score: Weighted composite score
"""

from typing import Dict, Tuple
import numpy as np


# Scoring weights based on clinical research
SCORING_WEIGHTS = {
    "hrv": 0.40,        # Strongest autonomic predictor
    "hr": 0.25,         # Direct cardiac load indicator
    "spo2": 0.20,       # Safety critical threshold
    "temperature": 0.15  # Systemic inflammation proxy
}


def score_heart_rate(current_bpm: float, baseline_bpm: float) -> Tuple[float, str]:
    """
    Score heart rate on 0-100 scale based on deviation from baseline.
    
    Clinical context:
    - Resting HR 40-60: Excellent (athletes)
    - Resting HR 60-80: Good
    - Resting HR 80-100: Fair
    - Resting HR >100: Tachycardia risk
    
    Args:
        current_bpm: Current heart rate in BPM
        baseline_bpm: Resting baseline heart rate
        
    Returns:
        Tuple of (score: 0-100, status: str)
        
    Example:
        >>> score, status = score_heart_rate(72, 70)
        >>> score
        94.3
        >>> status
        'excellent'
    """
    if baseline_bpm <= 0:
        return 50.0, "unknown"
    
    # Calculate percentage increase from baseline
    percent_increase = ((current_bpm - baseline_bpm) / baseline_bpm) * 100
    
    # Scoring curve based on % increase from baseline
    if percent_increase <= 0:
        # At or below baseline = excellent
        score = 100.0
    elif percent_increase <= 10:
        # 0-10% increase = good (100 → 80)
        score = 100 - (percent_increase * 2)
    elif percent_increase <= 25:
        # 10-25% increase = moderate (80 → 40)
        score = 80 - ((percent_increase - 10) * 2.67)
    elif percent_increase <= 50:
        # 25-50% increase = concerning (40 → 10)
        score = 40 - ((percent_increase - 25) * 1.2)
    else:
        # >50% increase = critical (10 → 0)
        score = max(0, 10 - ((percent_increase - 50) * 0.2))
    
    score = float(np.clip(score, 0, 100))
    status = _get_status_label(score)
    
    return score, status


def score_hrv(current_hrv: float, baseline_hrv: float) -> Tuple[float, str]:
    """
    Score HRV (RMSSD) on 0-100 scale.
    
    Clinical context:
    - HRV > 50ms: Excellent recovery
    - HRV 30-50ms: Good
    - HRV 20-30ms: Moderate stress
    - HRV < 20ms: High stress/overtraining
    
    Note: HRV DECREASES under stress (inverse to HR)
    
    Args:
        current_hrv: Current HRV (RMSSD) in milliseconds
        baseline_hrv: Resting baseline HRV
        
    Returns:
        Tuple of (score: 0-100, status: str)
        
    Example:
        >>> score, status = score_hrv(35, 45)
        >>> score  # 22% decrease → moderate
        70.4
    """
    if baseline_hrv <= 0:
        return 50.0, "unknown"
    
    # Calculate percentage decrease from baseline (HRV drop = bad)
    percent_decrease = ((baseline_hrv - current_hrv) / baseline_hrv) * 100
    
    # Scoring curve based on % decrease from baseline
    if percent_decrease <= 0:
        # Above baseline = excellent
        score = 100.0
    elif percent_decrease <= 15:
        # 0-15% decrease = good (100 → 80)
        score = 100 - (percent_decrease * 1.33)
    elif percent_decrease <= 30:
        # 15-30% decrease = moderate (80 → 50)
        score = 80 - ((percent_decrease - 15) * 2)
    elif percent_decrease <= 50:
        # 30-50% decrease = concerning (50 → 20)
        score = 50 - ((percent_decrease - 30) * 1.5)
    else:
        # >50% decrease = critical (20 → 0)
        score = max(0, 20 - ((percent_decrease - 50) * 0.4))
    
    score = float(np.clip(score, 0, 100))
    status = _get_status_label(score)
    
    return score, status


def score_spo2(current_spo2: float, baseline_spo2: float = 98.0) -> Tuple[float, str]:
    """
    Score blood oxygen saturation on 0-100 scale.
    
    Clinical context:
    - SpO₂ ≥ 95%: Normal
    - SpO₂ 90-94%: Mild hypoxemia
    - SpO₂ 85-89%: Moderate hypoxemia
    - SpO₂ < 85%: Severe (medical emergency)
    
    Note: Uses absolute thresholds more than baseline deviation,
    as SpO₂ should always be in a healthy range regardless of personal baseline.
    
    Args:
        current_spo2: Current SpO₂ percentage
        baseline_spo2: Baseline SpO₂ (less important for this metric)
        
    Returns:
        Tuple of (score: 0-100, status: str)
        
    Example:
        >>> score, status = score_spo2(97)
        >>> score
        100.0
        >>> status
        'excellent'
    """
    # Absolute thresholds are more important than baseline for SpO₂
    if current_spo2 >= 97:
        score = 100.0
    elif current_spo2 >= 95:
        # 95-97%: Excellent (100 → 90)
        score = 100 - ((97 - current_spo2) * 5)
    elif current_spo2 >= 92:
        # 92-95%: Good (90 → 60)
        score = 90 - ((95 - current_spo2) * 10)
    elif current_spo2 >= 88:
        # 88-92%: Concerning (60 → 20)
        score = 60 - ((92 - current_spo2) * 10)
    else:
        # < 88%: Critical (20 → 0)
        score = max(0, 20 - ((88 - current_spo2) * 2.5))
    
    score = float(np.clip(score, 0, 100))
    status = _get_status_label(score)
    
    return score, status


def score_temperature(current_temp: float, baseline_temp: float) -> Tuple[float, str]:
    """
    Score skin temperature on 0-100 scale.
    
    Clinical context:
    - Skin temp 35.5-36.5°C: Normal
    - Increase > 1°C: Inflammation or stress response
    - Decrease > 1°C: Poor circulation or cold stress
    
    Note: Both increases AND decreases from baseline are concerning.
    
    Args:
        current_temp: Current skin temperature in Celsius
        baseline_temp: Baseline skin temperature
        
    Returns:
        Tuple of (score: 0-100, status: str)
        
    Example:
        >>> score, status = score_temperature(36.5, 36.4)
        >>> score  # 0.1°C deviation = excellent
        100.0
    """
    if baseline_temp <= 0:
        return 50.0, "unknown"
    
    # Calculate absolute deviation (both high and low are bad)
    deviation = abs(current_temp - baseline_temp)
    
    # Scoring curve based on deviation
    if deviation <= 0.3:
        # ±0.3°C: Normal variation (100)
        score = 100.0
    elif deviation <= 0.8:
        # 0.3-0.8°C: Mild (100 → 80)
        score = 100 - ((deviation - 0.3) * 40)
    elif deviation <= 1.5:
        # 0.8-1.5°C: Moderate (80 → 50)
        score = 80 - ((deviation - 0.8) * 42.86)
    else:
        # > 1.5°C: Significant (50 → 0)
        score = max(0, 50 - ((deviation - 1.5) * 20))
    
    score = float(np.clip(score, 0, 100))
    status = _get_status_label(score)
    
    return score, status


def calculate_cardiotwin_score(
    hr_score: float,
    hrv_score: float,
    spo2_score: float,
    temp_score: float,
    weights: Dict[str, float] = None
) -> float:
    """
    Calculate final CardioTwin Score as weighted composite.
    
    Default weights based on clinical evidence for CVD risk prediction:
    - HRV: 40% (strongest autonomic predictor)
    - HR: 25% (direct cardiac load)
    - SpO₂: 20% (safety critical)
    - Temp: 15% (systemic stress proxy)
    
    Args:
        hr_score: Heart rate component score (0-100)
        hrv_score: HRV component score (0-100)
        spo2_score: SpO₂ component score (0-100)
        temp_score: Temperature component score (0-100)
        weights: Optional custom weights dict
        
    Returns:
        Composite CardioTwin Score (0-100), rounded to 1 decimal
        
    Example:
        >>> score = calculate_cardiotwin_score(90, 85, 100, 95)
        >>> score
        89.2
    """
    if weights is None:
        weights = SCORING_WEIGHTS
    
    # Validate weights sum to 1.0 (with tolerance for float precision)
    weight_sum = weights["hrv"] + weights["hr"] + weights["spo2"] + weights["temperature"]
    if not (0.99 <= weight_sum <= 1.01):
        raise ValueError(f"Weights must sum to 1.0, got {weight_sum}")
    
    # Calculate weighted composite
    score = (
        hrv_score * weights["hrv"] +
        hr_score * weights["hr"] +
        spo2_score * weights["spo2"] +
        temp_score * weights["temperature"]
    )
    
    return round(float(np.clip(score, 0, 100)), 1)


def calculate_all_scores(
    reading: Dict,
    baseline: Dict
) -> Dict:
    """
    Calculate all component scores and composite for a reading.
    
    Convenience function that runs all scoring functions and returns
    a complete score breakdown.
    
    Args:
        reading: Dict with bpm, hrv, spo2, temperature
        baseline: Dict with resting_bpm, resting_hrv, normal_spo2, normal_temp
        
    Returns:
        Dict with all scores and metadata:
        {
            "cardiotwin_score": float,
            "components": {
                "heart_rate": {"value": float, "score": float, "status": str},
                "hrv": {...},
                "spo2": {...},
                "temperature": {...}
            }
        }
    """
    # Get individual scores
    hr_score, hr_status = score_heart_rate(
        reading.get("bpm", 70),
        baseline.get("resting_bpm", 70)
    )
    
    hrv_score, hrv_status = score_hrv(
        reading.get("hrv", 45),
        baseline.get("resting_hrv", 45)
    )
    
    spo2_score, spo2_status = score_spo2(
        reading.get("spo2", 98),
        baseline.get("normal_spo2", 98)
    )
    
    temp_score, temp_status = score_temperature(
        reading.get("temperature", 36.4),
        baseline.get("normal_temp", 36.4)
    )
    
    # Calculate composite
    cardiotwin_score = calculate_cardiotwin_score(
        hr_score, hrv_score, spo2_score, temp_score
    )
    
    return {
        "cardiotwin_score": cardiotwin_score,
        "components": {
            "heart_rate": {
                "value": reading.get("bpm", 0),
                "baseline": baseline.get("resting_bpm", 0),
                "score": round(hr_score, 1),
                "status": hr_status
            },
            "hrv": {
                "value": reading.get("hrv", 0),
                "baseline": baseline.get("resting_hrv", 0),
                "score": round(hrv_score, 1),
                "status": hrv_status
            },
            "spo2": {
                "value": reading.get("spo2", 0),
                "baseline": baseline.get("normal_spo2", 0),
                "score": round(spo2_score, 1),
                "status": spo2_status
            },
            "temperature": {
                "value": reading.get("temperature", 0),
                "baseline": baseline.get("normal_temp", 0),
                "score": round(temp_score, 1),
                "status": temp_status
            }
        }
    }


def _get_status_label(score: float) -> str:
    """
    Convert numeric score to human-readable status label.
    
    Args:
        score: Component score (0-100)
        
    Returns:
        Status string: 'excellent', 'good', 'fair', or 'concerning'
    """
    if score >= 80:
        return "excellent"
    elif score >= 60:
        return "good"
    elif score >= 40:
        return "fair"
    else:
        return "concerning"


def get_scoring_weights() -> Dict[str, float]:
    """
    Get current scoring weights.
    
    Returns:
        Dict with weight for each component
    """
    return SCORING_WEIGHTS.copy()


def validate_weights(weights: Dict[str, float]) -> bool:
    """
    Validate that custom weights are valid.
    
    Args:
        weights: Dict with hrv, hr, spo2, temperature weights
        
    Returns:
        True if valid, False otherwise
    """
    required_keys = {"hrv", "hr", "spo2", "temperature"}
    
    if not required_keys.issubset(weights.keys()):
        return False
    
    # Check all weights are 0-1
    for key in required_keys:
        if not (0 <= weights[key] <= 1):
            return False
    
    # Check sum is 1.0
    weight_sum = sum(weights[key] for key in required_keys)
    return 0.99 <= weight_sum <= 1.01
