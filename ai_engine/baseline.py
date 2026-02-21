"""
Baseline Calibration Module
===========================

Establishes personalized reference points for each user session.
Calibrates baseline from first 15 readings (~30 seconds).

Functions:
    - calibrate_baseline: Calculate baseline from initial readings
    - remove_outliers: Remove statistical outliers using IQR
    - update_baseline: Adapt baseline over time (v2 feature)
"""

from typing import Dict, List, Optional
import numpy as np
from scipy import stats


# Minimum readings required for calibration
MIN_CALIBRATION_READINGS = 12
TARGET_CALIBRATION_READINGS = 15
EXTENDED_CALIBRATION_READINGS = 20

# IQR multiplier for outlier detection
IQR_MULTIPLIER = 1.5


def remove_outliers(readings: List[Dict], param: str) -> List[Dict]:
    """
    Remove statistical outliers using Interquartile Range (IQR) method.
    
    The IQR method identifies outliers as values that fall outside:
    [Q1 - 1.5*IQR, Q3 + 1.5*IQR]
    
    Args:
        readings: List of reading dictionaries
        param: Parameter name to check for outliers (e.g., 'bpm', 'hrv')
        
    Returns:
        List of readings with outliers removed for specified parameter
        
    Example:
        >>> readings = [{"bpm": 70}, {"bpm": 72}, {"bpm": 150}, {"bpm": 71}]
        >>> clean = remove_outliers(readings, "bpm")
        >>> len(clean)  # 150 is outlier, removed
        3
    """
    if len(readings) < 4:
        # Need at least 4 points for IQR calculation
        return readings
    
    values = np.array([r.get(param, 0) for r in readings])
    
    # Calculate quartiles
    q1, q3 = np.percentile(values, [25, 75])
    iqr = q3 - q1
    
    # Define outlier bounds
    lower_bound = q1 - (IQR_MULTIPLIER * iqr)
    upper_bound = q3 + (IQR_MULTIPLIER * iqr)
    
    # Filter readings
    clean_readings = [
        r for r in readings 
        if lower_bound <= r.get(param, 0) <= upper_bound
    ]
    
    return clean_readings


def remove_outliers_all_params(readings: List[Dict]) -> List[Dict]:
    """
    Remove outliers across all biometric parameters.
    
    A reading is kept only if ALL its parameters are within IQR bounds.
    
    Args:
        readings: List of reading dictionaries
        
    Returns:
        List of readings with no outliers in any parameter
    """
    if len(readings) < 4:
        return readings
    
    params = ["bpm", "hrv", "spo2", "temperature"]
    clean_readings = readings.copy()
    
    # Apply outlier removal for each parameter
    for param in params:
        clean_readings = remove_outliers(clean_readings, param)
    
    return clean_readings


def calculate_variance(readings: List[Dict]) -> Dict[str, float]:
    """
    Calculate variance (standard deviation) for each parameter.
    
    High variance during calibration indicates motion or unstable readings.
    
    Args:
        readings: List of reading dictionaries
        
    Returns:
        Dictionary of standard deviations for each parameter
    """
    if len(readings) < 2:
        return {"bpm": 0, "hrv": 0, "spo2": 0, "temperature": 0}
    
    params = ["bpm", "hrv", "spo2", "temperature"]
    variances = {}
    
    for param in params:
        values = [r.get(param, 0) for r in readings]
        variances[param] = float(np.std(values))
    
    return variances


def detect_motion_during_calibration(readings: List[Dict]) -> bool:
    """
    Detect if user was moving during calibration (high variance).
    
    Thresholds based on typical resting state variability:
    - BPM std dev > 10: Too much variation
    - HRV std dev > 15: Too much variation
    
    Args:
        readings: List of calibration readings
        
    Returns:
        True if excessive motion detected, False otherwise
    """
    if len(readings) < 5:
        return False
    
    variances = calculate_variance(readings)
    
    # Check for excessive variance
    if variances["bpm"] > 10 or variances["hrv"] > 15:
        return True
    
    return False


def is_post_exercise(readings: List[Dict]) -> bool:
    """
    Detect if user started calibration while still recovering from exercise.
    
    Indicators:
    - Average BPM > 100
    - Low HRV (< 25)
    
    Args:
        readings: List of calibration readings
        
    Returns:
        True if post-exercise state detected
    """
    if len(readings) < 3:
        return False
    
    avg_bpm = np.mean([r.get("bpm", 70) for r in readings])
    avg_hrv = np.mean([r.get("hrv", 50) for r in readings])
    
    return bool(avg_bpm > 100 or avg_hrv < 25)


def calibrate_baseline(readings: List[Dict]) -> Dict:
    """
    Calculate baseline from initial calibration readings.
    
    Process:
    1. Remove statistical outliers (IQR method)
    2. Check for sufficient valid readings (min 12)
    3. Detect motion artifacts or post-exercise state
    4. Calculate mean values for each parameter
    5. Return baseline or calibration status
    
    Args:
        readings: List of calibration reading dictionaries
                 Each must contain: bpm, hrv, spo2, temperature
        
    Returns:
        Dictionary with:
        - calibration_complete: bool
        - resting_bpm: float (if complete)
        - resting_hrv: float (if complete)
        - normal_spo2: float (if complete)
        - normal_temp: float (if complete)
        - readings_collected: int
        - readings_required: int
        - calibration_quality: str (excellent/good/fair/poor)
        - warnings: List[str] (optional)
        
    Example:
        >>> readings = [
        ...     {"bpm": 72, "hrv": 45, "spo2": 98, "temperature": 36.4},
        ...     {"bpm": 71, "hrv": 43, "spo2": 98, "temperature": 36.3},
        ...     # ... 13 more readings
        ... ]
        >>> baseline = calibrate_baseline(readings)
        >>> baseline["calibration_complete"]
        True
        >>> baseline["resting_bpm"]
        71.5
    """
    if not readings:
        return {
            "calibration_complete": False,
            "readings_collected": 0,
            "readings_required": TARGET_CALIBRATION_READINGS,
            "message": "No readings collected yet"
        }
    
    # Remove outliers
    clean_readings = remove_outliers_all_params(readings)
    
    # Check if we have enough valid readings
    num_clean = len(clean_readings)
    num_total = len(readings)
    
    warnings = []
    
    # Insufficient readings
    if num_clean < MIN_CALIBRATION_READINGS:
        # Check if we should extend calibration window
        if num_total >= TARGET_CALIBRATION_READINGS:
            return {
                "calibration_complete": False,
                "readings_collected": num_total,
                "readings_required": EXTENDED_CALIBRATION_READINGS,
                "message": f"Too many outliers detected. Need {EXTENDED_CALIBRATION_READINGS - num_total} more readings."
            }
        else:
            return {
                "calibration_complete": False,
                "readings_collected": num_total,
                "readings_required": TARGET_CALIBRATION_READINGS,
                "message": f"Collecting baseline... {TARGET_CALIBRATION_READINGS - num_total} readings remaining."
            }
    
    # Check for motion during calibration
    if detect_motion_during_calibration(clean_readings):
        warnings.append("High variability detected. Please remain still during calibration.")
    
    # Check for post-exercise state
    if is_post_exercise(clean_readings):
        warnings.append("Elevated heart rate detected. Consider resting for 2-3 minutes before calibration.")
    
    # Calculate baseline values
    resting_bpm = float(np.mean([r["bpm"] for r in clean_readings]))
    resting_hrv = float(np.mean([r["hrv"] for r in clean_readings]))
    normal_spo2 = float(np.mean([r["spo2"] for r in clean_readings]))
    normal_temp = float(np.mean([r["temperature"] for r in clean_readings]))
    
    # Calculate confidence/quality metrics
    variances = calculate_variance(clean_readings)
    
    # Determine calibration quality
    outlier_rate = 1 - (num_clean / num_total)
    
    if outlier_rate < 0.1 and variances["bpm"] < 5:
        quality = "excellent"
    elif outlier_rate < 0.2 and variances["bpm"] < 8:
        quality = "good"
    elif outlier_rate < 0.3:
        quality = "fair"
    else:
        quality = "poor"
        warnings.append("Calibration quality is low. Results may be less accurate.")
    
    baseline = {
        "calibration_complete": True,
        "resting_bpm": round(resting_bpm, 1),
        "resting_hrv": round(resting_hrv, 1),
        "normal_spo2": round(normal_spo2, 1),
        "normal_temp": round(normal_temp, 2),
        "readings_collected": num_total,
        "readings_used": num_clean,
        "outliers_removed": num_total - num_clean,
        "calibration_quality": quality,
        "variance": {
            "bpm": round(variances["bpm"], 2),
            "hrv": round(variances["hrv"], 2),
            "spo2": round(variances["spo2"], 2),
            "temperature": round(variances["temperature"], 3)
        }
    }
    
    if warnings:
        baseline["warnings"] = warnings
    
    return baseline


def update_baseline(
    current_baseline: Dict,
    recent_readings: List[Dict],
    adaptation_rate: float = 0.1
) -> Dict:
    """
    Gradually adapt baseline based on recent readings (v2 feature).
    
    Uses exponential moving average to slowly adjust baseline
    if user's physiology changes over time (fitness improvements, etc.)
    
    Args:
        current_baseline: Current baseline dictionary
        recent_readings: Recent readings to incorporate
        adaptation_rate: How quickly to adapt (0-1, default 0.1 = 10%)
        
    Returns:
        Updated baseline dictionary
        
    Note:
        This is a v2 feature. For hackathon demo, baseline is fixed per session.
    """
    if not current_baseline.get("calibration_complete"):
        return current_baseline
    
    if len(recent_readings) < 10:
        # Need enough data to establish new trend
        return current_baseline
    
    # Calculate recent averages
    recent_bpm = np.mean([r["bpm"] for r in recent_readings])
    recent_hrv = np.mean([r["hrv"] for r in recent_readings])
    recent_spo2 = np.mean([r["spo2"] for r in recent_readings])
    recent_temp = np.mean([r["temperature"] for r in recent_readings])
    
    # Exponential moving average update
    updated_baseline = current_baseline.copy()
    updated_baseline["resting_bpm"] = (
        (1 - adaptation_rate) * current_baseline["resting_bpm"] +
        adaptation_rate * recent_bpm
    )
    updated_baseline["resting_hrv"] = (
        (1 - adaptation_rate) * current_baseline["resting_hrv"] +
        adaptation_rate * recent_hrv
    )
    updated_baseline["normal_spo2"] = (
        (1 - adaptation_rate) * current_baseline["normal_spo2"] +
        adaptation_rate * recent_spo2
    )
    updated_baseline["normal_temp"] = (
        (1 - adaptation_rate) * current_baseline["normal_temp"] +
        adaptation_rate * recent_temp
    )
    
    return updated_baseline
