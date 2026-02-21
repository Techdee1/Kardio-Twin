"""
What-If Risk Projection Engine
==============================

Projects future cardiovascular risk based on current trends.
Shows users consequences of sustained behavioral patterns.

Features:
    - Linear trend extrapolation
    - Physiological bounds enforcement
    - Secondary effect estimation (HR increase)
    - Risk trajectory visualization data
    - What-if scenario simulation

Functions:
    - project_risk: Calculate future risk projection
    - calculate_trend: Determine score trend direction
    - estimate_hr_impact: Project resting HR changes
    - simulate_scenario: Model "what if" lifestyle changes
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Tuple
from enum import Enum
import numpy as np

from .zones import Zone, classify_zone


class TrendDirection(Enum):
    """Direction of health trend."""
    IMPROVING = "improving"
    STABLE = "stable"
    DECLINING = "declining"
    VOLATILE = "volatile"


@dataclass
class TrendAnalysis:
    """Result of trend analysis."""
    direction: TrendDirection
    slope: float  # Points per reading
    confidence: float  # 0-1
    projected_score_1h: float  # Score in 1 hour
    projected_score_24h: float  # Score in 24 hours
    projected_zone_1h: Zone
    projected_zone_24h: Zone
    readings_analyzed: int


@dataclass
class RiskProjection:
    """Risk projection result."""
    current_score: float
    current_zone: Zone
    projected_scores: List[float]  # Hourly projections
    projected_zones: List[Zone]
    time_to_zone_change: Optional[int]  # Hours until zone change
    worst_case_score: float
    best_case_score: float
    trend: TrendDirection
    risk_factors: List[str]
    recommendations: List[str]


@dataclass
class WhatIfScenario:
    """Result of a what-if simulation."""
    scenario_name: str
    baseline_score: float
    projected_score: float
    score_change: float
    new_zone: Zone
    zone_changed: bool
    time_to_effect: str  # "immediate", "1 hour", "24 hours"
    confidence: float
    explanation: str


# Physiological bounds
PHYSIOLOGICAL_BOUNDS = {
    "min_score": 0,
    "max_score": 100,
    "min_hr": 40,
    "max_hr": 200,
    "min_hrv": 5,
    "max_hrv": 150,
    "min_spo2": 70,
    "max_spo2": 100,
    "min_temp": 35.0,
    "max_temp": 42.0,
}

# Intervention effects (estimated score improvements)
INTERVENTION_EFFECTS = {
    "deep_breathing_5min": {"immediate": 3, "1h": 5, "24h": 2},
    "rest_15min": {"immediate": 5, "1h": 8, "24h": 3},
    "rest_30min": {"immediate": 8, "1h": 12, "24h": 5},
    "hydration": {"immediate": 2, "1h": 4, "24h": 6},
    "light_walk": {"immediate": -2, "1h": 3, "24h": 5},
    "meditation": {"immediate": 4, "1h": 6, "24h": 8},
    "sleep_7h": {"immediate": 0, "1h": 0, "24h": 15},
    "reduce_caffeine": {"immediate": 0, "1h": 2, "24h": 5},
    "stress_reduction": {"immediate": 3, "1h": 5, "24h": 10},
}

# Negative behavior effects (estimated score decreases)
NEGATIVE_EFFECTS = {
    "continued_stress": {"1h": -5, "24h": -15},
    "no_rest": {"1h": -3, "24h": -10},
    "dehydration": {"1h": -2, "24h": -8},
    "poor_sleep": {"1h": 0, "24h": -12},
    "high_caffeine": {"1h": -2, "24h": -5},
    "intense_exercise": {"1h": -10, "24h": -5},
}


def calculate_trend(
    scores: List[float],
    min_points: int = 3
) -> TrendAnalysis:
    """
    Calculate trend from recent scores.
    
    Args:
        scores: Recent scores (newest last)
        min_points: Minimum points needed for analysis
        
    Returns:
        TrendAnalysis with direction and projections
    """
    if len(scores) < min_points:
        # Not enough data - return stable
        current = scores[-1] if scores else 50
        return TrendAnalysis(
            direction=TrendDirection.STABLE,
            slope=0,
            confidence=0.3,
            projected_score_1h=current,
            projected_score_24h=current,
            projected_zone_1h=classify_zone(current),
            projected_zone_24h=classify_zone(current),
            readings_analyzed=len(scores),
        )
    
    # Use numpy for linear regression
    x = np.arange(len(scores))
    y = np.array(scores)
    
    # Calculate linear fit
    coefficients = np.polyfit(x, y, 1)
    slope = coefficients[0]
    
    # Calculate R² for confidence
    y_pred = np.polyval(coefficients, x)
    ss_res = np.sum((y - y_pred) ** 2)
    ss_tot = np.sum((y - np.mean(y)) ** 2)
    r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0
    
    # Determine direction
    if slope > 1.5:
        direction = TrendDirection.IMPROVING
    elif slope < -1.5:
        direction = TrendDirection.DECLINING
    else:
        # Check for volatility
        std_dev = np.std(y)
        if std_dev > 10:
            direction = TrendDirection.VOLATILE
        else:
            direction = TrendDirection.STABLE
    
    # Project future scores (assuming hourly readings)
    current_score = scores[-1]
    projected_1h = _clamp_score(current_score + slope * 1)
    projected_24h = _clamp_score(current_score + slope * 24)
    
    return TrendAnalysis(
        direction=direction,
        slope=slope,
        confidence=max(0.3, min(0.95, r_squared)),
        projected_score_1h=projected_1h,
        projected_score_24h=projected_24h,
        projected_zone_1h=classify_zone(projected_1h),
        projected_zone_24h=classify_zone(projected_24h),
        readings_analyzed=len(scores),
    )


def _clamp_score(score: float) -> float:
    """Clamp score to valid range."""
    return max(PHYSIOLOGICAL_BOUNDS["min_score"], 
               min(PHYSIOLOGICAL_BOUNDS["max_score"], score))


def project_risk(
    current_score: float,
    score_history: Optional[List[float]] = None,
    current_zone: Optional[Zone] = None,
    hours_ahead: int = 24,
) -> RiskProjection:
    """
    Project cardiovascular risk over time.
    
    Args:
        current_score: Current CardioTwin score
        score_history: Recent score history
        current_zone: Current zone (calculated if not provided)
        hours_ahead: Hours to project
        
    Returns:
        RiskProjection with trajectory and recommendations
    """
    if current_zone is None:
        current_zone = classify_zone(current_score)
    
    # Build score history if not provided
    if score_history is None:
        score_history = [current_score]
    
    # Calculate trend
    trend_analysis = calculate_trend(score_history)
    slope = trend_analysis.slope
    
    # Project hourly scores
    projected_scores = []
    projected_zones = []
    time_to_zone_change = None
    
    for hour in range(1, hours_ahead + 1):
        # Apply dampening for longer projections (less confident)
        dampening = 1.0 / (1.0 + hour * 0.05)
        projected = _clamp_score(current_score + slope * hour * dampening)
        projected_scores.append(projected)
        
        zone = classify_zone(projected)
        projected_zones.append(zone)
        
        # Track first zone change
        if time_to_zone_change is None and zone != current_zone:
            time_to_zone_change = hour
    
    # Calculate confidence intervals
    confidence = trend_analysis.confidence
    uncertainty = (1 - confidence) * 20  # Max 20 points uncertainty
    worst_case = _clamp_score(min(projected_scores) - uncertainty)
    best_case = _clamp_score(max(projected_scores) + uncertainty)
    
    # Identify risk factors
    risk_factors = _identify_risk_factors(
        current_score, current_zone, trend_analysis
    )
    
    # Generate recommendations
    recommendations = _generate_recommendations(
        current_zone, trend_analysis, risk_factors
    )
    
    return RiskProjection(
        current_score=current_score,
        current_zone=current_zone,
        projected_scores=projected_scores,
        projected_zones=projected_zones,
        time_to_zone_change=time_to_zone_change,
        worst_case_score=worst_case,
        best_case_score=best_case,
        trend=trend_analysis.direction,
        risk_factors=risk_factors,
        recommendations=recommendations,
    )


def _identify_risk_factors(
    score: float,
    zone: Zone,
    trend: TrendAnalysis
) -> List[str]:
    """Identify current risk factors."""
    factors = []
    
    if zone == Zone.RED:
        factors.append("Critical cardiovascular strain")
    elif zone == Zone.ORANGE:
        factors.append("Elevated cardiovascular stress")
    
    if trend.direction == TrendDirection.DECLINING:
        factors.append("Declining health trend")
    elif trend.direction == TrendDirection.VOLATILE:
        factors.append("Unstable readings")
    
    if score < 50:
        factors.append("Low overall score")
    
    if trend.projected_zone_24h in (Zone.RED, Zone.ORANGE):
        factors.append("Projected to remain in warning zone")
    
    return factors


def _generate_recommendations(
    zone: Zone,
    trend: TrendAnalysis,
    risk_factors: List[str]
) -> List[str]:
    """Generate recommendations based on risk."""
    recommendations = []
    
    if zone == Zone.RED:
        recommendations.append("Stop all activity immediately")
        recommendations.append("Rest in a calm environment")
        recommendations.append("Seek medical attention if symptoms persist")
    elif zone == Zone.ORANGE:
        recommendations.append("Take a 15-30 minute rest break")
        recommendations.append("Practice deep breathing exercises")
        recommendations.append("Stay hydrated")
    elif zone == Zone.YELLOW:
        recommendations.append("Consider a short break")
        recommendations.append("Reduce stress if possible")
    else:  # GREEN
        recommendations.append("Maintain current healthy habits")
        recommendations.append("Keep monitoring regularly")
    
    if trend.direction == TrendDirection.DECLINING:
        recommendations.append("Address declining trend with immediate rest")
    
    return recommendations


def estimate_hr_impact(
    current_hr: float,
    score_change: float,
    baseline_hr: float = 70
) -> float:
    """
    Estimate heart rate impact from score changes.
    
    Lower scores typically correlate with elevated HR.
    
    Args:
        current_hr: Current heart rate
        score_change: Projected score change
        baseline_hr: Normal resting HR
        
    Returns:
        Projected heart rate
    """
    # Negative score change typically increases HR
    # Approximate: 5 point score drop → 3 BPM HR increase
    hr_change = -score_change * 0.6
    
    projected_hr = current_hr + hr_change
    
    # Clamp to physiological bounds
    return max(PHYSIOLOGICAL_BOUNDS["min_hr"],
               min(PHYSIOLOGICAL_BOUNDS["max_hr"], projected_hr))


def estimate_hrv_impact(
    current_hrv: float,
    score_change: float,
    baseline_hrv: float = 45
) -> float:
    """
    Estimate HRV impact from score changes.
    
    Lower scores correlate with decreased HRV.
    
    Args:
        current_hrv: Current HRV (RMSSD)
        score_change: Projected score change
        baseline_hrv: Normal HRV
        
    Returns:
        Projected HRV
    """
    # Score change directly affects HRV
    # 10 point score drop → ~5ms HRV decrease
    hrv_change = score_change * 0.5
    
    projected_hrv = current_hrv + hrv_change
    
    return max(PHYSIOLOGICAL_BOUNDS["min_hrv"],
               min(PHYSIOLOGICAL_BOUNDS["max_hrv"], projected_hrv))


def simulate_scenario(
    scenario_name: str,
    current_score: float,
    time_horizon: str = "1h",
) -> WhatIfScenario:
    """
    Simulate a what-if scenario.
    
    Args:
        scenario_name: Name of intervention/behavior
        current_score: Current CardioTwin score
        time_horizon: "immediate", "1h", or "24h"
        
    Returns:
        WhatIfScenario with projected outcome
    """
    current_zone = classify_zone(current_score)
    
    # Check for positive intervention
    if scenario_name in INTERVENTION_EFFECTS:
        effects = INTERVENTION_EFFECTS[scenario_name]
        score_change = effects.get(time_horizon, effects.get("1h", 0))
        is_positive = True
    # Check for negative behavior
    elif scenario_name in NEGATIVE_EFFECTS:
        effects = NEGATIVE_EFFECTS[scenario_name]
        score_change = effects.get(time_horizon, effects.get("1h", 0))
        is_positive = False
    else:
        # Unknown scenario
        return WhatIfScenario(
            scenario_name=scenario_name,
            baseline_score=current_score,
            projected_score=current_score,
            score_change=0,
            new_zone=current_zone,
            zone_changed=False,
            time_to_effect=time_horizon,
            confidence=0.3,
            explanation=f"Unknown scenario: {scenario_name}",
        )
    
    # Calculate projected score
    projected_score = _clamp_score(current_score + score_change)
    new_zone = classify_zone(projected_score)
    zone_changed = new_zone != current_zone
    
    # Generate explanation
    if is_positive:
        if zone_changed and new_zone.value in ["green", "yellow"]:
            explanation = f"This could improve your score by {abs(score_change):.0f} points and move you to {new_zone.value.upper()} zone!"
        elif score_change > 0:
            explanation = f"This could improve your score by {score_change:.0f} points."
        else:
            explanation = "Limited immediate effect, but beneficial long-term."
    else:
        if zone_changed:
            explanation = f"Warning: This could drop your score by {abs(score_change):.0f} points to {new_zone.value.upper()} zone."
        else:
            explanation = f"This could decrease your score by {abs(score_change):.0f} points."
    
    # Confidence based on time horizon
    confidence_map = {"immediate": 0.8, "1h": 0.7, "24h": 0.5}
    confidence = confidence_map.get(time_horizon, 0.6)
    
    return WhatIfScenario(
        scenario_name=scenario_name,
        baseline_score=current_score,
        projected_score=projected_score,
        score_change=score_change,
        new_zone=new_zone,
        zone_changed=zone_changed,
        time_to_effect=time_horizon,
        confidence=confidence,
        explanation=explanation,
    )


def get_improvement_path(
    current_score: float,
    target_zone: Zone = Zone.GREEN,
) -> List[WhatIfScenario]:
    """
    Get recommended interventions to reach target zone.
    
    Args:
        current_score: Current score
        target_zone: Target zone to reach
        
    Returns:
        List of scenarios ordered by effectiveness
    """
    current_zone = classify_zone(current_score)
    
    # If already in target zone, return empty
    zone_order = [Zone.GREEN, Zone.YELLOW, Zone.ORANGE, Zone.RED]
    if zone_order.index(current_zone) <= zone_order.index(target_zone):
        return []
    
    # Simulate all positive interventions
    scenarios = []
    for intervention in INTERVENTION_EFFECTS:
        scenario = simulate_scenario(intervention, current_score, "1h")
        if scenario.score_change > 0:
            scenarios.append(scenario)
    
    # Sort by effectiveness (score change)
    scenarios.sort(key=lambda s: s.score_change, reverse=True)
    
    # Return top recommendations
    return scenarios[:5]


def get_risk_trajectory(
    current_score: float,
    behavior: str = "no_change",
    hours: int = 24,
) -> Dict[str, Any]:
    """
    Get risk trajectory for visualization.
    
    Args:
        current_score: Current score
        behavior: Behavior pattern ("no_change", "positive", "negative")
        hours: Hours to project
        
    Returns:
        Dictionary with trajectory data for charting
    """
    current_zone = classify_zone(current_score)
    
    # Determine slope based on behavior
    if behavior == "positive":
        base_slope = 2.0  # Improving
    elif behavior == "negative":
        base_slope = -2.0  # Declining
    else:
        base_slope = 0.0  # Stable
    
    # Generate hourly data points
    timestamps = list(range(hours + 1))
    scores = []
    zones = []
    
    for hour in timestamps:
        # Apply dampening and noise
        dampening = 1.0 / (1.0 + hour * 0.03)
        noise = np.random.normal(0, 1)
        projected = _clamp_score(
            current_score + base_slope * hour * dampening + noise
        )
        scores.append(round(projected, 1))
        zones.append(classify_zone(projected).value)
    
    return {
        "timestamps": timestamps,
        "scores": scores,
        "zones": zones,
        "current_score": current_score,
        "current_zone": current_zone.value,
        "behavior": behavior,
        "zone_boundaries": {
            "green": 80,
            "yellow": 55,
            "orange": 30,
            "red": 0,
        },
    }


def project_recovery_time(
    current_score: float,
    target_score: float = 80,
    intervention: str = "rest_15min",
) -> Dict[str, Any]:
    """
    Estimate recovery time to reach target score.
    
    Args:
        current_score: Current score
        target_score: Target score to reach
        intervention: Recovery intervention
        
    Returns:
        Recovery time estimate
    """
    if current_score >= target_score:
        return {
            "current_score": current_score,
            "target_score": target_score,
            "estimated_hours": 0,
            "confidence": 1.0,
            "message": "Already at or above target score!",
        }
    
    # Get intervention effect
    effects = INTERVENTION_EFFECTS.get(intervention, {"1h": 5})
    hourly_improvement = effects.get("1h", 5)
    
    if hourly_improvement <= 0:
        return {
            "current_score": current_score,
            "target_score": target_score,
            "estimated_hours": None,
            "confidence": 0.3,
            "message": "Cannot estimate recovery with this intervention.",
        }
    
    # Calculate hours needed
    points_needed = target_score - current_score
    hours_needed = points_needed / hourly_improvement
    
    # Add buffer for uncertainty
    hours_needed = int(np.ceil(hours_needed * 1.2))
    
    return {
        "current_score": current_score,
        "target_score": target_score,
        "estimated_hours": hours_needed,
        "intervention": intervention,
        "confidence": 0.6,
        "message": f"With {intervention.replace('_', ' ')}, estimated recovery: {hours_needed} hours",
    }
