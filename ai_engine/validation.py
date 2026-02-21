"""
Input Validation Module
=======================

Validates and sanitizes incoming biometric readings from ESP32 sensors.
Ensures data quality before processing through the scoring pipeline.

Functions:
    - validate_reading: Check if reading is within physiological bounds
    - sanitize_reading: Clean and normalize input data
    - detect_sensor_error: Identify sensor malfunctions
"""

from typing import Dict, Optional, Tuple
import numpy as np

# Physiological bounds for each parameter
VALID_RANGES = {
    "bpm": (30, 220),           # Human heart rate range
    "hrv": (0, 200),            # HRV RMSSD in milliseconds
    "spo2": (70, 100),          # Blood oxygen saturation %
    "temperature": (30.0, 42.0) # Skin temperature in Celsius
}

# Required fields in a reading
REQUIRED_FIELDS = ["bpm", "hrv", "spo2", "temperature", "timestamp", "session_id"]


def validate_reading(reading: Dict) -> Tuple[bool, Optional[str]]:
    """
    Validate a biometric reading from the sensor.
    
    Args:
        reading: Dictionary containing biometric data
        
    Returns:
        Tuple of (is_valid, error_message)
        - (True, None) if valid
        - (False, "error description") if invalid
    """
    # Check for required fields
    for field in REQUIRED_FIELDS:
        if field not in reading:
            return False, f"Missing required field: {field}"
        if reading[field] is None:
            return False, f"Null value for field: {field}"
    
    # Check for NaN values
    for field in ["bpm", "hrv", "spo2", "temperature"]:
        if isinstance(reading[field], float) and np.isnan(reading[field]):
            return False, f"NaN value for field: {field}"
    
    # Validate ranges
    for field, (min_val, max_val) in VALID_RANGES.items():
        value = reading.get(field)
        if value is not None:
            if value < min_val or value > max_val:
                return False, f"{field} value {value} outside valid range [{min_val}, {max_val}]"
    
    # SpO2 critical threshold check
    if reading.get("spo2", 100) < 70:
        return False, "SpO2 critically low - possible sensor error or medical emergency"
    
    return True, None


def sanitize_reading(reading: Dict) -> Dict:
    """
    Clean and normalize a reading for processing.
    
    Args:
        reading: Raw reading dictionary
        
    Returns:
        Sanitized reading with proper types
    """
    sanitized = {}
    
    # Convert numeric fields to float
    for field in ["bpm", "hrv", "spo2", "temperature"]:
        value = reading.get(field)
        if value is not None:
            sanitized[field] = float(value)
    
    # Ensure timestamp is int
    sanitized["timestamp"] = int(reading.get("timestamp", 0))
    
    # Ensure session_id is string
    sanitized["session_id"] = str(reading.get("session_id", "default"))
    
    return sanitized


def detect_sensor_error(reading: Dict, previous_reading: Optional[Dict] = None) -> Tuple[bool, Optional[str]]:
    """
    Detect potential sensor errors or artifacts.
    
    Args:
        reading: Current reading
        previous_reading: Previous reading for comparison
        
    Returns:
        Tuple of (has_error, error_type)
    """
    # Check for stuck sensor (all zeros)
    if reading.get("bpm", 0) == 0 and reading.get("spo2", 0) == 0:
        return True, "sensor_disconnected"
    
    # Check for impossible sudden changes (motion artifact)
    if previous_reading:
        bpm_change = abs(reading.get("bpm", 0) - previous_reading.get("bpm", 0))
        if bpm_change > 40:
            return True, "motion_artifact"
    
    # Check for sensor saturation
    if reading.get("spo2", 0) == 100 and reading.get("bpm", 0) == 0:
        return True, "sensor_saturated"
    
    return False, None


def is_finger_present(ir_value: int) -> bool:
    """
    Check if finger is placed on sensor based on IR value.
    
    Args:
        ir_value: Infrared sensor reading
        
    Returns:
        True if finger detected, False otherwise
    """
    FINGER_THRESHOLD = 50000
    return ir_value > FINGER_THRESHOLD
