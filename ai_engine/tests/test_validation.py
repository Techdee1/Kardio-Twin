"""
Tests for Input Validation Module
"""

import pytest
import numpy as np
from ai_engine.validation import (
    validate_reading,
    sanitize_reading,
    detect_sensor_error,
    is_finger_present,
    VALID_RANGES,
    REQUIRED_FIELDS
)


class TestValidateReading:
    """Tests for validate_reading function."""
    
    def test_valid_reading(self):
        """Valid reading should pass validation."""
        reading = {
            "bpm": 72,
            "hrv": 42.3,
            "spo2": 98.1,
            "temperature": 36.4,
            "timestamp": 45000,
            "session_id": "demo"
        }
        is_valid, error = validate_reading(reading)
        assert is_valid is True
        assert error is None
    
    def test_missing_required_field(self):
        """Missing required field should fail validation."""
        reading = {
            "bpm": 72,
            "hrv": 42.3,
            # Missing spo2
            "temperature": 36.4,
            "timestamp": 45000,
            "session_id": "demo"
        }
        is_valid, error = validate_reading(reading)
        assert is_valid is False
        assert "Missing required field" in error
    
    def test_null_value(self):
        """Null value should fail validation."""
        reading = {
            "bpm": 72,
            "hrv": None,
            "spo2": 98.1,
            "temperature": 36.4,
            "timestamp": 45000,
            "session_id": "demo"
        }
        is_valid, error = validate_reading(reading)
        assert is_valid is False
        assert "Null value" in error
    
    def test_nan_value(self):
        """NaN value should fail validation."""
        reading = {
            "bpm": float('nan'),
            "hrv": 42.3,
            "spo2": 98.1,
            "temperature": 36.4,
            "timestamp": 45000,
            "session_id": "demo"
        }
        is_valid, error = validate_reading(reading)
        assert is_valid is False
        assert "NaN value" in error
    
    def test_bpm_below_range(self):
        """BPM below valid range should fail."""
        reading = {
            "bpm": 25,  # Below 30
            "hrv": 42.3,
            "spo2": 98.1,
            "temperature": 36.4,
            "timestamp": 45000,
            "session_id": "demo"
        }
        is_valid, error = validate_reading(reading)
        assert is_valid is False
        assert "bpm" in error
    
    def test_bpm_above_range(self):
        """BPM above valid range should fail."""
        reading = {
            "bpm": 250,  # Above 220
            "hrv": 42.3,
            "spo2": 98.1,
            "temperature": 36.4,
            "timestamp": 45000,
            "session_id": "demo"
        }
        is_valid, error = validate_reading(reading)
        assert is_valid is False
        assert "bpm" in error
    
    def test_spo2_critical(self):
        """Critically low SpO2 should fail validation."""
        reading = {
            "bpm": 72,
            "hrv": 42.3,
            "spo2": 65,  # Below 70 - outside valid range
            "temperature": 36.4,
            "timestamp": 45000,
            "session_id": "demo"
        }
        is_valid, error = validate_reading(reading)
        assert is_valid is False
        assert "spo2" in error.lower()


class TestSanitizeReading:
    """Tests for sanitize_reading function."""
    
    def test_converts_to_float(self):
        """Should convert numeric values to float."""
        reading = {
            "bpm": 72,  # int
            "hrv": "42.3",  # string (edge case)
            "spo2": 98,
            "temperature": 36,
            "timestamp": 45000,
            "session_id": "demo"
        }
        sanitized = sanitize_reading(reading)
        assert isinstance(sanitized["bpm"], float)
        assert isinstance(sanitized["spo2"], float)
        assert isinstance(sanitized["temperature"], float)
    
    def test_preserves_values(self):
        """Should preserve actual values."""
        reading = {
            "bpm": 72,
            "hrv": 42.3,
            "spo2": 98.1,
            "temperature": 36.4,
            "timestamp": 45000,
            "session_id": "demo"
        }
        sanitized = sanitize_reading(reading)
        assert sanitized["bpm"] == 72.0
        assert sanitized["hrv"] == 42.3
        assert sanitized["spo2"] == 98.1
        assert sanitized["temperature"] == 36.4
    
    def test_timestamp_is_int(self):
        """Timestamp should be converted to int."""
        reading = {
            "bpm": 72,
            "hrv": 42.3,
            "spo2": 98.1,
            "temperature": 36.4,
            "timestamp": 45000.5,
            "session_id": "demo"
        }
        sanitized = sanitize_reading(reading)
        assert isinstance(sanitized["timestamp"], int)


class TestDetectSensorError:
    """Tests for detect_sensor_error function."""
    
    def test_no_error(self):
        """Normal reading should not trigger error."""
        reading = {
            "bpm": 72,
            "hrv": 42.3,
            "spo2": 98.1,
            "temperature": 36.4
        }
        has_error, error_type = detect_sensor_error(reading)
        assert has_error is False
        assert error_type is None
    
    def test_sensor_disconnected(self):
        """Zero values indicate disconnected sensor."""
        reading = {
            "bpm": 0,
            "hrv": 0,
            "spo2": 0,
            "temperature": 36.4
        }
        has_error, error_type = detect_sensor_error(reading)
        assert has_error is True
        assert error_type == "sensor_disconnected"
    
    def test_motion_artifact(self):
        """Large BPM change indicates motion artifact."""
        current = {"bpm": 150, "hrv": 20, "spo2": 95, "temperature": 36.5}
        previous = {"bpm": 70, "hrv": 45, "spo2": 98, "temperature": 36.4}
        has_error, error_type = detect_sensor_error(current, previous)
        assert has_error is True
        assert error_type == "motion_artifact"
    
    def test_normal_bpm_change(self):
        """Normal BPM change should not trigger error."""
        current = {"bpm": 85, "hrv": 35, "spo2": 97, "temperature": 36.5}
        previous = {"bpm": 72, "hrv": 42, "spo2": 98, "temperature": 36.4}
        has_error, error_type = detect_sensor_error(current, previous)
        assert has_error is False


class TestIsFingerPresent:
    """Tests for is_finger_present function."""
    
    def test_finger_present(self):
        """IR value above threshold indicates finger present."""
        assert is_finger_present(60000) is True
        assert is_finger_present(100000) is True
    
    def test_finger_absent(self):
        """IR value below threshold indicates no finger."""
        assert is_finger_present(40000) is False
        assert is_finger_present(1000) is False
    
    def test_threshold_boundary(self):
        """Test exact threshold value."""
        assert is_finger_present(50001) is True
        assert is_finger_present(49999) is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
