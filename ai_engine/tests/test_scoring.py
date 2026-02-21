"""
Tests for Component Scoring Module
"""

import pytest
import numpy as np
from ai_engine.scoring import (
    score_heart_rate,
    score_hrv,
    score_spo2,
    score_temperature,
    calculate_cardiotwin_score,
    calculate_all_scores,
    get_scoring_weights,
    validate_weights,
    SCORING_WEIGHTS
)


class TestScoreHeartRate:
    """Tests for heart rate scoring function."""
    
    def test_hr_at_baseline(self):
        """HR at baseline should score 100."""
        score, status = score_heart_rate(70, 70)
        assert score == 100.0
        assert status == "excellent"
    
    def test_hr_below_baseline(self):
        """HR below baseline should still score 100."""
        score, status = score_heart_rate(65, 70)
        assert score == 100.0
        assert status == "excellent"
    
    def test_hr_10_percent_increase(self):
        """10% HR increase should score ~80."""
        score, status = score_heart_rate(77, 70)  # 10% increase
        assert 78 <= score <= 82
        assert status in ["excellent", "good"]
    
    def test_hr_25_percent_increase(self):
        """25% HR increase should score ~40."""
        score, status = score_heart_rate(87.5, 70)  # 25% increase
        assert 38 <= score <= 42
        assert status in ["fair", "concerning"]  # Borderline zone
    
    def test_hr_50_percent_increase(self):
        """50% HR increase should score ~10."""
        score, status = score_heart_rate(105, 70)  # 50% increase
        assert 8 <= score <= 12
        assert status == "concerning"
    
    def test_hr_extreme_increase(self):
        """Extreme HR increase should score near 0."""
        score, status = score_heart_rate(180, 70)  # Very high
        assert score <= 10
        assert status == "concerning"
    
    def test_hr_zero_baseline(self):
        """Zero baseline should return 50 (unknown)."""
        score, status = score_heart_rate(70, 0)
        assert score == 50.0
        assert status == "unknown"
    
    def test_hr_post_exercise_scenario(self):
        """Simulate post-exercise: 140 BPM from 70 baseline."""
        score, status = score_heart_rate(140, 70)  # 100% increase
        assert score < 10
        assert status == "concerning"


class TestScoreHRV:
    """Tests for HRV scoring function."""
    
    def test_hrv_at_baseline(self):
        """HRV at baseline should score 100."""
        score, status = score_hrv(45, 45)
        assert score == 100.0
        assert status == "excellent"
    
    def test_hrv_above_baseline(self):
        """HRV above baseline should score 100 (excellent recovery)."""
        score, status = score_hrv(50, 45)
        assert score == 100.0
        assert status == "excellent"
    
    def test_hrv_15_percent_decrease(self):
        """15% HRV decrease should score ~80."""
        score, status = score_hrv(38.25, 45)  # 15% decrease
        assert 78 <= score <= 82
        assert status in ["excellent", "good"]
    
    def test_hrv_30_percent_decrease(self):
        """30% HRV decrease should score ~50."""
        score, status = score_hrv(31.5, 45)  # 30% decrease
        assert 48 <= score <= 52
        assert status in ["fair", "good"]
    
    def test_hrv_50_percent_decrease(self):
        """50% HRV decrease should score ~20."""
        score, status = score_hrv(22.5, 45)  # 50% decrease
        assert 18 <= score <= 22
        assert status == "concerning"
    
    def test_hrv_extreme_decrease(self):
        """Extreme HRV decrease should score near 0."""
        score, status = score_hrv(10, 45)  # ~78% decrease
        assert score < 15
        assert status == "concerning"
    
    def test_hrv_zero_baseline(self):
        """Zero baseline should return 50 (unknown)."""
        score, status = score_hrv(45, 0)
        assert score == 50.0
        assert status == "unknown"
    
    def test_hrv_stress_scenario(self):
        """Simulate stress: HRV drops from 45 to 20."""
        score, status = score_hrv(20, 45)  # ~56% decrease
        assert score < 20
        assert status == "concerning"


class TestScoreSpO2:
    """Tests for SpO2 scoring function."""
    
    def test_spo2_optimal(self):
        """SpO2 >= 97% should score 100."""
        score, status = score_spo2(98)
        assert score == 100.0
        assert status == "excellent"
        
        score, status = score_spo2(99)
        assert score == 100.0
    
    def test_spo2_95_97(self):
        """SpO2 95-97% should score 90-100."""
        score, status = score_spo2(96)
        assert 90 <= score <= 100
        assert status == "excellent"
    
    def test_spo2_92_95(self):
        """SpO2 92-95% should score 60-90."""
        score, status = score_spo2(93)
        assert 60 <= score <= 90
        assert status in ["excellent", "good"]
    
    def test_spo2_88_92(self):
        """SpO2 88-92% should score 20-60."""
        score, status = score_spo2(90)
        assert 20 <= score <= 60
        assert status in ["fair", "good"]
    
    def test_spo2_critical(self):
        """SpO2 < 88% should score < 20."""
        score, status = score_spo2(85)
        assert score < 20
        assert status == "concerning"
    
    def test_spo2_very_low(self):
        """Very low SpO2 should score near 0."""
        score, status = score_spo2(80)
        assert score == 0
        assert status == "concerning"
    
    def test_spo2_baseline_less_important(self):
        """SpO2 scoring uses absolute values, baseline is secondary."""
        # Same SpO2 regardless of baseline should score similarly
        score1, _ = score_spo2(95, 98)
        score2, _ = score_spo2(95, 96)
        assert abs(score1 - score2) < 5


class TestScoreTemperature:
    """Tests for temperature scoring function."""
    
    def test_temp_at_baseline(self):
        """Temp at baseline should score 100."""
        score, status = score_temperature(36.4, 36.4)
        assert score == 100.0
        assert status == "excellent"
    
    def test_temp_small_deviation(self):
        """Small deviation (±0.3°C) should score 100."""
        score, status = score_temperature(36.6, 36.4)  # +0.2°C
        assert score == 100.0
        assert status == "excellent"
    
    def test_temp_mild_increase(self):
        """0.5°C increase should score ~90."""
        score, status = score_temperature(36.9, 36.4)  # +0.5°C
        assert 85 <= score <= 95
        assert status == "excellent"
    
    def test_temp_moderate_increase(self):
        """1.0°C increase should score ~70."""
        score, status = score_temperature(37.4, 36.4)  # +1.0°C
        assert 60 <= score <= 80
        assert status in ["excellent", "good"]
    
    def test_temp_significant_increase(self):
        """1.5°C increase should score ~50."""
        score, status = score_temperature(37.9, 36.4)  # +1.5°C
        assert 45 <= score <= 55
        assert status in ["fair", "good"]
    
    def test_temp_fever(self):
        """2.0°C increase (fever) should score < 50."""
        score, status = score_temperature(38.4, 36.4)  # +2.0°C
        assert score < 50
        assert status in ["fair", "concerning"]
    
    def test_temp_decrease(self):
        """Temp decrease is also concerning."""
        score, status = score_temperature(35.4, 36.4)  # -1.0°C
        assert 60 <= score <= 80  # Same as increase
    
    def test_temp_zero_baseline(self):
        """Zero baseline should return 50 (unknown)."""
        score, status = score_temperature(36.4, 0)
        assert score == 50.0
        assert status == "unknown"


class TestCalculateCardioTwinScore:
    """Tests for composite score calculation."""
    
    def test_all_perfect_scores(self):
        """All 100s should give 100."""
        score = calculate_cardiotwin_score(100, 100, 100, 100)
        assert score == 100.0
    
    def test_all_zero_scores(self):
        """All 0s should give 0."""
        score = calculate_cardiotwin_score(0, 0, 0, 0)
        assert score == 0.0
    
    def test_weighted_average(self):
        """Should correctly apply weights."""
        # HR=100 (25%), HRV=50 (40%), SpO2=100 (20%), Temp=100 (15%)
        # Expected: 0.25*100 + 0.40*50 + 0.20*100 + 0.15*100 = 25+20+20+15 = 80
        score = calculate_cardiotwin_score(100, 50, 100, 100)
        assert score == 80.0
    
    def test_hrv_weight_dominant(self):
        """HRV should have most influence (40% weight)."""
        # Only HRV is low
        score1 = calculate_cardiotwin_score(100, 0, 100, 100)  # HRV=0
        # Only HR is low
        score2 = calculate_cardiotwin_score(0, 100, 100, 100)  # HR=0
        
        # HRV=0 should have bigger impact (40% vs 25%)
        assert score1 < score2
    
    def test_custom_weights(self):
        """Should accept custom weights."""
        custom_weights = {
            "hrv": 0.25,
            "hr": 0.25,
            "spo2": 0.25,
            "temperature": 0.25
        }
        score = calculate_cardiotwin_score(80, 80, 80, 80, weights=custom_weights)
        assert score == 80.0
    
    def test_invalid_weights_sum(self):
        """Should raise error if weights don't sum to 1.0."""
        bad_weights = {
            "hrv": 0.5,
            "hr": 0.5,
            "spo2": 0.5,
            "temperature": 0.5
        }
        with pytest.raises(ValueError):
            calculate_cardiotwin_score(80, 80, 80, 80, weights=bad_weights)
    
    def test_returns_float_with_one_decimal(self):
        """Score should be rounded to 1 decimal place."""
        score = calculate_cardiotwin_score(72.345, 81.789, 95.123, 88.456)
        assert score == round(score, 1)


class TestCalculateAllScores:
    """Tests for convenience function that calculates all scores."""
    
    def test_returns_all_components(self):
        """Should return cardiotwin_score and all component scores."""
        reading = {"bpm": 72, "hrv": 42, "spo2": 98, "temperature": 36.5}
        baseline = {
            "resting_bpm": 70,
            "resting_hrv": 45,
            "normal_spo2": 98,
            "normal_temp": 36.4
        }
        
        result = calculate_all_scores(reading, baseline)
        
        assert "cardiotwin_score" in result
        assert "components" in result
        assert "heart_rate" in result["components"]
        assert "hrv" in result["components"]
        assert "spo2" in result["components"]
        assert "temperature" in result["components"]
    
    def test_component_structure(self):
        """Each component should have value, baseline, score, status."""
        reading = {"bpm": 72, "hrv": 42, "spo2": 98, "temperature": 36.5}
        baseline = {
            "resting_bpm": 70,
            "resting_hrv": 45,
            "normal_spo2": 98,
            "normal_temp": 36.4
        }
        
        result = calculate_all_scores(reading, baseline)
        
        for component in result["components"].values():
            assert "value" in component
            assert "baseline" in component
            assert "score" in component
            assert "status" in component
    
    def test_resting_scenario(self):
        """Resting state should produce high score."""
        reading = {"bpm": 70, "hrv": 45, "spo2": 98, "temperature": 36.4}
        baseline = {
            "resting_bpm": 70,
            "resting_hrv": 45,
            "normal_spo2": 98,
            "normal_temp": 36.4
        }
        
        result = calculate_all_scores(reading, baseline)
        
        assert result["cardiotwin_score"] >= 95
    
    def test_stressed_scenario(self):
        """Stress state should produce lower score."""
        reading = {"bpm": 110, "hrv": 22, "spo2": 95, "temperature": 37.2}
        baseline = {
            "resting_bpm": 70,
            "resting_hrv": 45,
            "normal_spo2": 98,
            "normal_temp": 36.4
        }
        
        result = calculate_all_scores(reading, baseline)
        
        assert result["cardiotwin_score"] < 60


class TestScoringWeights:
    """Tests for weight validation and retrieval."""
    
    def test_get_scoring_weights(self):
        """Should return copy of weights."""
        weights = get_scoring_weights()
        assert weights == SCORING_WEIGHTS
        
        # Should be a copy, not reference
        weights["hrv"] = 0.99
        assert get_scoring_weights()["hrv"] == 0.40
    
    def test_validate_weights_valid(self):
        """Valid weights should pass."""
        valid = {
            "hrv": 0.25,
            "hr": 0.25,
            "spo2": 0.25,
            "temperature": 0.25
        }
        assert validate_weights(valid) is True
    
    def test_validate_weights_missing_key(self):
        """Missing key should fail."""
        invalid = {
            "hrv": 0.50,
            "hr": 0.50,
            # Missing spo2 and temperature
        }
        assert validate_weights(invalid) is False
    
    def test_validate_weights_bad_sum(self):
        """Weights not summing to 1.0 should fail."""
        invalid = {
            "hrv": 0.50,
            "hr": 0.50,
            "spo2": 0.50,
            "temperature": 0.50
        }
        assert validate_weights(invalid) is False
    
    def test_validate_weights_negative(self):
        """Negative weights should fail."""
        invalid = {
            "hrv": -0.1,
            "hr": 0.4,
            "spo2": 0.4,
            "temperature": 0.3
        }
        assert validate_weights(invalid) is False


class TestIntegrationScenarios:
    """Integration tests for realistic scenarios."""
    
    def test_demo_resting_to_exercise_transition(self):
        """Simulate the hackathon demo: resting → post-exercise."""
        baseline = {
            "resting_bpm": 70,
            "resting_hrv": 45,
            "normal_spo2": 98,
            "normal_temp": 36.4
        }
        
        # Resting state
        resting = {"bpm": 72, "hrv": 43, "spo2": 98, "temperature": 36.4}
        resting_result = calculate_all_scores(resting, baseline)
        
        # Post-exercise state (after burpees)
        exercise = {"bpm": 135, "hrv": 22, "spo2": 94, "temperature": 37.1}
        exercise_result = calculate_all_scores(exercise, baseline)
        
        # Score should drop significantly
        assert resting_result["cardiotwin_score"] >= 80  # GREEN zone
        assert exercise_result["cardiotwin_score"] < 50  # ORANGE zone
        assert resting_result["cardiotwin_score"] - exercise_result["cardiotwin_score"] > 30
    
    def test_gradual_recovery(self):
        """Test gradual recovery from exercise."""
        baseline = {
            "resting_bpm": 70,
            "resting_hrv": 45,
            "normal_spo2": 98,
            "normal_temp": 36.4
        }
        
        # Recovery progression
        readings = [
            {"bpm": 130, "hrv": 20, "spo2": 94, "temperature": 37.2},  # Post-exercise
            {"bpm": 105, "hrv": 28, "spo2": 96, "temperature": 36.9},  # 1 min recovery
            {"bpm": 88, "hrv": 35, "spo2": 97, "temperature": 36.6},   # 2 min recovery
            {"bpm": 75, "hrv": 42, "spo2": 98, "temperature": 36.4},   # 3 min recovery
        ]
        
        scores = [calculate_all_scores(r, baseline)["cardiotwin_score"] for r in readings]
        
        # Each score should be higher than the previous
        for i in range(len(scores) - 1):
            assert scores[i+1] > scores[i], f"Score {i+1} should be > score {i}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
