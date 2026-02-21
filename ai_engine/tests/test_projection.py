"""
Tests for What-If Risk Projection Engine
========================================
"""

import pytest
import numpy as np

from ai_engine.projection import (
    TrendDirection,
    TrendAnalysis,
    RiskProjection,
    WhatIfScenario,
    calculate_trend,
    project_risk,
    estimate_hr_impact,
    estimate_hrv_impact,
    simulate_scenario,
    get_improvement_path,
    get_risk_trajectory,
    project_recovery_time,
    INTERVENTION_EFFECTS,
    NEGATIVE_EFFECTS,
    _clamp_score,
)
from ai_engine.zones import Zone


class TestCalculateTrend:
    """Test trend calculation."""
    
    def test_insufficient_data_returns_stable(self):
        """With < 3 points, return stable trend."""
        result = calculate_trend([80, 85])
        assert result.direction == TrendDirection.STABLE
        assert result.confidence < 0.5
    
    def test_improving_trend(self):
        """Increasing scores show improving trend."""
        scores = [60, 65, 70, 75, 80]
        result = calculate_trend(scores)
        assert result.direction == TrendDirection.IMPROVING
        assert result.slope > 0
    
    def test_declining_trend(self):
        """Decreasing scores show declining trend."""
        scores = [90, 85, 80, 75, 70]
        result = calculate_trend(scores)
        assert result.direction == TrendDirection.DECLINING
        assert result.slope < 0
    
    def test_stable_trend(self):
        """Flat scores show stable trend."""
        scores = [80, 81, 79, 80, 80]
        result = calculate_trend(scores)
        assert result.direction == TrendDirection.STABLE
    
    def test_volatile_trend(self):
        """High variance shows volatile trend."""
        scores = [65, 95, 65, 95, 65]  # High oscillation with no net trend
        result = calculate_trend(scores)
        assert result.direction == TrendDirection.VOLATILE
    
    def test_projected_zone_1h(self):
        """Projects zone for 1 hour."""
        scores = [70, 75, 80, 85]
        result = calculate_trend(scores)
        assert result.projected_zone_1h is not None
    
    def test_projected_zone_24h(self):
        """Projects zone for 24 hours."""
        scores = [70, 75, 80, 85]
        result = calculate_trend(scores)
        assert result.projected_zone_24h is not None
    
    def test_readings_analyzed_count(self):
        """Tracks number of readings analyzed."""
        scores = [80, 82, 84, 86, 88]
        result = calculate_trend(scores)
        assert result.readings_analyzed == 5


class TestClampScore:
    """Test score clamping."""
    
    def test_clamp_above_100(self):
        """Scores above 100 clamped."""
        assert _clamp_score(110) == 100
    
    def test_clamp_below_0(self):
        """Scores below 0 clamped."""
        assert _clamp_score(-10) == 0
    
    def test_valid_score_unchanged(self):
        """Valid scores unchanged."""
        assert _clamp_score(75) == 75


class TestProjectRisk:
    """Test risk projection."""
    
    def test_basic_projection(self):
        """Basic projection works."""
        result = project_risk(80)
        assert result.current_score == 80
        assert result.current_zone == Zone.GREEN
        assert len(result.projected_scores) == 24
    
    def test_projection_with_history(self):
        """Projection with history uses trend."""
        history = [60, 65, 70, 75, 80]  # Improving
        result = project_risk(80, score_history=history)
        assert result.trend == TrendDirection.IMPROVING
    
    def test_declining_projection(self):
        """Declining trend projects lower scores."""
        history = [90, 85, 80, 75, 70]
        result = project_risk(70, score_history=history)
        assert result.trend == TrendDirection.DECLINING
        # Should flag risk factors
        assert len(result.risk_factors) > 0
    
    def test_zone_change_detection(self):
        """Detects time to zone change."""
        # Strong decline from GREEN
        history = [95, 90, 87, 84, 81]
        result = project_risk(81, score_history=history)
        # Might project zone change
        if result.time_to_zone_change is not None:
            assert result.time_to_zone_change > 0
    
    def test_recommendations_for_red_zone(self):
        """RED zone gets urgent recommendations."""
        result = project_risk(20)
        assert "Stop all activity" in result.recommendations[0]
    
    def test_recommendations_for_green_zone(self):
        """GREEN zone gets maintenance recommendations."""
        result = project_risk(90)
        assert any("maintain" in r.lower() for r in result.recommendations)
    
    def test_worst_best_case_bounds(self):
        """Worst/best case within bounds."""
        result = project_risk(50)
        assert 0 <= result.worst_case_score <= 100
        assert 0 <= result.best_case_score <= 100
    
    def test_custom_hours_ahead(self):
        """Custom projection window."""
        result = project_risk(80, hours_ahead=12)
        assert len(result.projected_scores) == 12


class TestEstimateHrImpact:
    """Test HR impact estimation."""
    
    def test_score_drop_increases_hr(self):
        """Score drop increases heart rate."""
        projected_hr = estimate_hr_impact(70, -10)
        assert projected_hr > 70
    
    def test_score_increase_decreases_hr(self):
        """Score increase decreases heart rate."""
        projected_hr = estimate_hr_impact(80, 10)
        assert projected_hr < 80
    
    def test_hr_clamped_to_bounds(self):
        """HR clamped to physiological bounds."""
        # Extreme case
        projected_hr = estimate_hr_impact(190, -50)
        assert projected_hr <= 200
        
        projected_hr = estimate_hr_impact(50, 50)
        assert projected_hr >= 40


class TestEstimateHrvImpact:
    """Test HRV impact estimation."""
    
    def test_score_drop_decreases_hrv(self):
        """Score drop decreases HRV."""
        projected_hrv = estimate_hrv_impact(45, -20)
        assert projected_hrv < 45
    
    def test_score_increase_increases_hrv(self):
        """Score increase improves HRV."""
        projected_hrv = estimate_hrv_impact(30, 20)
        assert projected_hrv > 30
    
    def test_hrv_clamped_to_bounds(self):
        """HRV clamped to physiological bounds."""
        projected_hrv = estimate_hrv_impact(10, -50)
        assert projected_hrv >= 5


class TestSimulateScenario:
    """Test what-if scenario simulation."""
    
    def test_deep_breathing_improves_score(self):
        """Deep breathing improves score."""
        result = simulate_scenario("deep_breathing_5min", 60, "1h")
        assert result.score_change > 0
        assert result.projected_score > 60
    
    def test_rest_15min_improves_score(self):
        """15 minute rest improves score."""
        result = simulate_scenario("rest_15min", 50)
        assert result.score_change > 0
    
    def test_continued_stress_worsens_score(self):
        """Continued stress worsens score."""
        result = simulate_scenario("continued_stress", 70, "1h")
        assert result.score_change < 0
        assert result.projected_score < 70
    
    def test_unknown_scenario_handled(self):
        """Unknown scenario returns neutral result."""
        result = simulate_scenario("unknown_thing", 70)
        assert result.score_change == 0
        assert result.confidence < 0.5
    
    def test_zone_change_detection(self):
        """Detects when intervention changes zone."""
        # From ORANGE (40) with rest
        result = simulate_scenario("rest_30min", 52, "1h")
        # 12 point improvement could push to YELLOW (55+)
        if result.projected_score >= 55:
            assert result.zone_changed is True
            assert result.new_zone == Zone.YELLOW
    
    def test_confidence_varies_by_time(self):
        """Confidence decreases with longer time horizon."""
        immediate = simulate_scenario("rest_15min", 60, "immediate")
        one_hour = simulate_scenario("rest_15min", 60, "1h")
        day = simulate_scenario("rest_15min", 60, "24h")
        
        assert immediate.confidence > one_hour.confidence
        assert one_hour.confidence > day.confidence
    
    def test_explanation_generated(self):
        """Scenarios include explanation."""
        result = simulate_scenario("meditation", 60, "1h")
        assert len(result.explanation) > 10


class TestGetImprovementPath:
    """Test improvement path recommendations."""
    
    def test_no_recommendations_for_green(self):
        """GREEN zone needs no improvement."""
        result = get_improvement_path(90, Zone.GREEN)
        assert len(result) == 0
    
    def test_recommendations_for_orange(self):
        """ORANGE zone gets improvement recommendations."""
        result = get_improvement_path(40)
        assert len(result) > 0
        # Sorted by effectiveness
        if len(result) >= 2:
            assert result[0].score_change >= result[1].score_change
    
    def test_max_5_recommendations(self):
        """Returns at most 5 recommendations."""
        result = get_improvement_path(30)
        assert len(result) <= 5


class TestGetRiskTrajectory:
    """Test trajectory data generation."""
    
    def test_trajectory_structure(self):
        """Trajectory has correct structure."""
        result = get_risk_trajectory(80)
        assert "timestamps" in result
        assert "scores" in result
        assert "zones" in result
        assert "zone_boundaries" in result
    
    def test_trajectory_length(self):
        """Trajectory has correct length."""
        result = get_risk_trajectory(80, hours=12)
        assert len(result["timestamps"]) == 13  # 0 to 12 inclusive
        assert len(result["scores"]) == 13
    
    def test_positive_behavior_trajectory(self):
        """Positive behavior shows improvement."""
        result = get_risk_trajectory(60, "positive", hours=10)
        # Should generally improve (allowing for noise)
        avg_later = np.mean(result["scores"][-3:])
        avg_earlier = np.mean(result["scores"][:3])
        # Positive behavior should trend upward
        assert avg_later >= avg_earlier - 5  # Allow some noise
    
    def test_negative_behavior_trajectory(self):
        """Negative behavior shows decline."""
        result = get_risk_trajectory(80, "negative", hours=10)
        # Should generally decline
        avg_later = np.mean(result["scores"][-3:])
        avg_earlier = np.mean(result["scores"][:3])
        assert avg_later <= avg_earlier + 5  # Allow some noise


class TestProjectRecoveryTime:
    """Test recovery time estimation."""
    
    def test_already_at_target(self):
        """Already at target returns 0 hours."""
        result = project_recovery_time(85, target_score=80)
        assert result["estimated_hours"] == 0
        assert "Already" in result["message"]
    
    def test_recovery_estimate(self):
        """Estimates recovery time."""
        result = project_recovery_time(50, target_score=80)
        assert result["estimated_hours"] > 0
        assert result["confidence"] > 0
    
    def test_includes_intervention(self):
        """Response includes intervention name."""
        result = project_recovery_time(60, intervention="meditation")
        assert "meditation" in result["message"]


class TestInterventionEffects:
    """Test intervention effect definitions."""
    
    def test_all_interventions_have_effects(self):
        """All interventions have defined effects."""
        for intervention in INTERVENTION_EFFECTS:
            effects = INTERVENTION_EFFECTS[intervention]
            assert any(k in effects for k in ["immediate", "1h", "24h"])
    
    def test_negative_effects_defined(self):
        """Negative effects are defined."""
        assert len(NEGATIVE_EFFECTS) > 0
        for behavior in NEGATIVE_EFFECTS:
            effects = NEGATIVE_EFFECTS[behavior]
            # Negative effects should be negative
            assert any(v < 0 for v in effects.values())


class TestDemoScenarios:
    """Test demo scenario projections."""
    
    def test_resting_state_projection(self):
        """Resting state (86) projects well."""
        result = project_risk(86)
        assert result.current_zone == Zone.GREEN
        # Should have positive trajectory
        assert result.worst_case_score > 50
    
    def test_post_exercise_projection(self):
        """Post-exercise (41) shows recovery path."""
        result = project_risk(41)
        assert result.current_zone == Zone.ORANGE
        # Should have recommendations
        assert len(result.recommendations) > 0
        assert any("rest" in r.lower() for r in result.recommendations)
    
    def test_recovery_simulation(self):
        """Simulate recovery from exercise state."""
        # Start at 41 (ORANGE), simulate rest
        result = simulate_scenario("rest_30min", 41, "1h")
        # Should improve
        assert result.score_change > 0
        assert result.projected_score > 41
    
    def test_improvement_path_from_orange(self):
        """Get improvement path from ORANGE zone."""
        result = get_improvement_path(41)
        assert len(result) > 0
        # Rest should be recommended
        intervention_names = [s.scenario_name for s in result]
        assert any("rest" in name for name in intervention_names)


class TestEdgeCases:
    """Test edge cases."""
    
    def test_empty_history(self):
        """Empty history handled."""
        result = calculate_trend([])
        # Should return stable with low confidence
        assert result.direction == TrendDirection.STABLE
    
    def test_single_reading(self):
        """Single reading handled."""
        result = calculate_trend([75])
        assert result.projected_score_1h == 75
    
    def test_extreme_scores(self):
        """Extreme scores clamped properly."""
        result = project_risk(5)  # Very low
        assert all(0 <= s <= 100 for s in result.projected_scores)
        
        result = project_risk(99)  # Very high
        assert all(0 <= s <= 100 for s in result.projected_scores)
    
    def test_negative_slope_handling(self):
        """Negative slopes handled."""
        scores = [100, 90, 80, 70, 60]  # Strong decline
        result = calculate_trend(scores)
        assert result.slope < 0
        assert result.projected_score_24h < 60
