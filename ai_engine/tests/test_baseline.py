"""
Tests for Baseline Calibration Module
"""

import pytest
import numpy as np
from ai_engine.baseline import (
    remove_outliers,
    remove_outliers_all_params,
    calculate_variance,
    detect_motion_during_calibration,
    is_post_exercise,
    calibrate_baseline,
    update_baseline,
    MIN_CALIBRATION_READINGS,
    TARGET_CALIBRATION_READINGS
)


class TestRemoveOutliers:
    """Tests for outlier removal functions."""
    
    def test_remove_outliers_single_param(self):
        """Should remove outliers using IQR method."""
        readings = [
            {"bpm": 70}, {"bpm": 71}, {"bpm": 72}, {"bpm": 71},
            {"bpm": 150},  # Outlier
            {"bpm": 70}, {"bpm": 72}
        ]
        clean = remove_outliers(readings, "bpm")
        assert len(clean) == 6  # One outlier removed
        assert all(r["bpm"] < 100 for r in clean)
    
    def test_remove_outliers_insufficient_data(self):
        """Should return all readings if < 4 points."""
        readings = [{"bpm": 70}, {"bpm": 150}, {"bpm": 71}]
        clean = remove_outliers(readings, "bpm")
        assert len(clean) == 3  # All kept
    
    def test_remove_outliers_no_outliers(self):
        """Should keep all readings if no outliers."""
        readings = [
            {"bpm": 70}, {"bpm": 71}, {"bpm": 72}, {"bpm": 71}, {"bpm": 70}
        ]
        clean = remove_outliers(readings, "bpm")
        assert len(clean) == 5
    
    def test_remove_outliers_all_params(self):
        """Should remove readings with outliers in any parameter."""
        readings = [
            {"bpm": 70, "hrv": 45, "spo2": 98, "temperature": 36.4},
            {"bpm": 71, "hrv": 43, "spo2": 98, "temperature": 36.3},
            {"bpm": 72, "hrv": 44, "spo2": 98, "temperature": 36.4},
            {"bpm": 150, "hrv": 20, "spo2": 98, "temperature": 36.5},  # Outlier BPM
            {"bpm": 70, "hrv": 45, "spo2": 98, "temperature": 36.4},
        ]
        clean = remove_outliers_all_params(readings)
        assert len(clean) < len(readings)
        assert all(r["bpm"] < 100 for r in clean)


class TestCalculateVariance:
    """Tests for variance calculation."""
    
    def test_calculate_variance_normal(self):
        """Should calculate std dev for each parameter."""
        readings = [
            {"bpm": 70, "hrv": 45, "spo2": 98, "temperature": 36.4},
            {"bpm": 72, "hrv": 43, "spo2": 98, "temperature": 36.3},
            {"bpm": 71, "hrv": 44, "spo2": 98, "temperature": 36.4},
        ]
        var = calculate_variance(readings)
        assert "bpm" in var
        assert "hrv" in var
        assert var["bpm"] > 0
        assert var["bpm"] < 2  # Low variance for resting state
    
    def test_calculate_variance_insufficient_data(self):
        """Should return zeros if < 2 readings."""
        readings = [{"bpm": 70, "hrv": 45, "spo2": 98, "temperature": 36.4}]
        var = calculate_variance(readings)
        assert var["bpm"] == 0


class TestDetectMotionDuringCalibration:
    """Tests for motion detection."""
    
    def test_detect_motion_high_bpm_variance(self):
        """High BPM variance should indicate motion."""
        readings = [
            {"bpm": 60, "hrv": 45, "spo2": 98, "temperature": 36.4},
            {"bpm": 85, "hrv": 30, "spo2": 97, "temperature": 36.5},
            {"bpm": 65, "hrv": 42, "spo2": 98, "temperature": 36.4},
            {"bpm": 90, "hrv": 28, "spo2": 97, "temperature": 36.6},
            {"bpm": 62, "hrv": 43, "spo2": 98, "temperature": 36.4},
            {"bpm": 88, "hrv": 29, "spo2": 97, "temperature": 36.5},
        ]
        assert detect_motion_during_calibration(readings) is True
    
    def test_detect_motion_stable_readings(self):
        """Stable readings should not indicate motion."""
        readings = [
            {"bpm": 70, "hrv": 45, "spo2": 98, "temperature": 36.4},
            {"bpm": 71, "hrv": 44, "spo2": 98, "temperature": 36.4},
            {"bpm": 72, "hrv": 43, "spo2": 98, "temperature": 36.3},
            {"bpm": 71, "hrv": 45, "spo2": 98, "temperature": 36.4},
            {"bpm": 70, "hrv": 44, "spo2": 98, "temperature": 36.4},
        ]
        assert detect_motion_during_calibration(readings) is False


class TestIsPostExercise:
    """Tests for post-exercise detection."""
    
    def test_is_post_exercise_high_hr(self):
        """High heart rate indicates post-exercise."""
        readings = [
            {"bpm": 110, "hrv": 30, "spo2": 96, "temperature": 37.0},
            {"bpm": 105, "hrv": 28, "spo2": 96, "temperature": 37.1},
            {"bpm": 108, "hrv": 29, "spo2": 96, "temperature": 37.0},
        ]
        assert is_post_exercise(readings) is True
    
    def test_is_post_exercise_low_hrv(self):
        """Low HRV indicates post-exercise."""
        readings = [
            {"bpm": 88, "hrv": 20, "spo2": 96, "temperature": 36.8},
            {"bpm": 90, "hrv": 22, "spo2": 96, "temperature": 36.9},
            {"bpm": 87, "hrv": 21, "spo2": 96, "temperature": 36.8},
        ]
        assert is_post_exercise(readings) is True
    
    def test_is_post_exercise_resting(self):
        """Normal resting values should not indicate post-exercise."""
        readings = [
            {"bpm": 70, "hrv": 45, "spo2": 98, "temperature": 36.4},
            {"bpm": 72, "hrv": 43, "spo2": 98, "temperature": 36.3},
            {"bpm": 71, "hrv": 44, "spo2": 98, "temperature": 36.4},
        ]
        assert is_post_exercise(readings) is False


class TestCalibrateBaseline:
    """Tests for main calibration function."""
    
    def test_calibrate_baseline_empty(self):
        """Empty readings should return incomplete status."""
        result = calibrate_baseline([])
        assert result["calibration_complete"] is False
        assert result["readings_collected"] == 0
    
    def test_calibrate_baseline_insufficient(self):
        """Insufficient readings should return incomplete status."""
        readings = [
            {"bpm": 70, "hrv": 45, "spo2": 98, "temperature": 36.4},
            {"bpm": 71, "hrv": 44, "spo2": 98, "temperature": 36.3},
        ]
        result = calibrate_baseline(readings)
        assert result["calibration_complete"] is False
        assert result["readings_collected"] == len(readings)
    
    def test_calibrate_baseline_success(self):
        """Should successfully calibrate with enough valid readings."""
        # Create 15 good readings
        readings = []
        for i in range(15):
            readings.append({
                "bpm": 70 + np.random.randint(-2, 3),
                "hrv": 45 + np.random.randint(-3, 4),
                "spo2": 98 + np.random.uniform(-0.5, 0.5),
                "temperature": 36.4 + np.random.uniform(-0.1, 0.1)
            })
        
        result = calibrate_baseline(readings)
        assert result["calibration_complete"] is True
        assert "resting_bpm" in result
        assert "resting_hrv" in result
        assert "normal_spo2" in result
        assert "normal_temp" in result
        assert 68 <= result["resting_bpm"] <= 73
        assert 40 <= result["resting_hrv"] <= 50
    
    def test_calibrate_baseline_with_outliers(self):
        """Should handle outliers gracefully."""
        readings = []
        # 15 good readings
        for i in range(15):
            readings.append({
                "bpm": 70 + np.random.randint(-2, 3),
                "hrv": 45 + np.random.randint(-2, 3),
                "spo2": 98,
                "temperature": 36.4
            })
        # Add 3 outliers
        readings.extend([
            {"bpm": 150, "hrv": 20, "spo2": 92, "temperature": 38.0},
            {"bpm": 160, "hrv": 18, "spo2": 91, "temperature": 38.2},
            {"bpm": 155, "hrv": 19, "spo2": 93, "temperature": 38.1},
        ])
        
        result = calibrate_baseline(readings)
        assert result["calibration_complete"] is True
        assert result["outliers_removed"] > 0
        # Baseline should not be affected by outliers
        assert result["resting_bpm"] < 80
    
    def test_calibrate_baseline_quality_metrics(self):
        """Should include quality metrics."""
        readings = []
        for i in range(15):
            readings.append({
                "bpm": 70,
                "hrv": 45,
                "spo2": 98,
                "temperature": 36.4
            })
        
        result = calibrate_baseline(readings)
        assert "calibration_quality" in result
        assert result["calibration_quality"] in ["excellent", "good", "fair", "poor"]
        assert "variance" in result
    
    def test_calibrate_baseline_motion_warning(self):
        """Should warn about motion detected."""
        readings = []
        for i in range(15):
            # Create high variance
            readings.append({
                "bpm": 70 + (i % 2) * 15,  # Alternating high variance
                "hrv": 45 - (i % 2) * 10,
                "spo2": 98,
                "temperature": 36.4
            })
        
        result = calibrate_baseline(readings)
        if "warnings" in result:
            assert any("variability" in w.lower() for w in result["warnings"])
    
    def test_calibrate_baseline_post_exercise_warning(self):
        """Should warn about post-exercise state."""
        readings = []
        for i in range(15):
            readings.append({
                "bpm": 110,  # Elevated
                "hrv": 22,   # Low
                "spo2": 96,
                "temperature": 37.0
            })
        
        result = calibrate_baseline(readings)
        assert "warnings" in result
        assert any("heart rate" in w.lower() or "rest" in w.lower() for w in result["warnings"])


class TestUpdateBaseline:
    """Tests for baseline adaptation (v2 feature)."""
    
    def test_update_baseline_not_calibrated(self):
        """Should not update if baseline not complete."""
        baseline = {"calibration_complete": False}
        recent = [{"bpm": 75, "hrv": 40, "spo2": 98, "temperature": 36.5}] * 10
        updated = update_baseline(baseline, recent)
        assert updated == baseline
    
    def test_update_baseline_insufficient_data(self):
        """Should not update with < 10 recent readings."""
        baseline = {
            "calibration_complete": True,
            "resting_bpm": 70.0,
            "resting_hrv": 45.0,
            "normal_spo2": 98.0,
            "normal_temp": 36.4
        }
        recent = [{"bpm": 75, "hrv": 40, "spo2": 98, "temperature": 36.5}] * 5
        updated = update_baseline(baseline, recent)
        assert updated["resting_bpm"] == 70.0  # Unchanged
    
    def test_update_baseline_gradual_adaptation(self):
        """Should gradually adapt baseline toward new values."""
        baseline = {
            "calibration_complete": True,
            "resting_bpm": 70.0,
            "resting_hrv": 45.0,
            "normal_spo2": 98.0,
            "normal_temp": 36.4
        }
        # Recent readings show improved fitness (lower HR, higher HRV)
        recent = [{"bpm": 65, "hrv": 50, "spo2": 98, "temperature": 36.4}] * 15
        
        updated = update_baseline(baseline, recent, adaptation_rate=0.1)
        
        # Should move toward new values but not jump completely
        assert 69 < updated["resting_bpm"] < 70  # Decreased slightly
        assert 45 < updated["resting_hrv"] < 46  # Increased slightly


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
