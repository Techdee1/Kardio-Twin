"""
Anomaly Detection Module
========================

Detects patterns that warrant user notification/alerts.

Alert Triggers:
    - Sudden score drop > 20 points
    - Zone downgrade (e.g., GREEN → YELLOW)
    - Critical threshold breach (score < 30)
    - Sustained decline (3+ consecutive drops)
    - SpO2 critical (<92%)
    - Sudden HRV drop (>30%)
    - Rapid HR increase (>40%)

Functions:
    - detect_anomalies: Check all alert conditions
    - get_alert_severity: Classify alert urgency
    - should_notify_user: Determine if notification needed
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime

from .zones import Zone, classify_zone


class AlertType(Enum):
    """Types of anomaly alerts."""
    SUDDEN_SCORE_DROP = "sudden_score_drop"
    ZONE_DOWNGRADE = "zone_downgrade"
    CRITICAL_THRESHOLD = "critical_threshold"
    SUSTAINED_DECLINE = "sustained_decline"
    SPO2_CRITICAL = "spo2_critical"
    HRV_SUDDEN_DROP = "hrv_sudden_drop"
    HR_RAPID_INCREASE = "hr_rapid_increase"
    MULTI_COMPONENT_DECLINE = "multi_component_decline"
    RECOVERY_NEEDED = "recovery_needed"


class AlertSeverity(Enum):
    """Alert urgency levels."""
    INFO = "info"           # FYI notification
    WARNING = "warning"     # Should take action soon
    URGENT = "urgent"       # Take action now
    CRITICAL = "critical"   # Immediate action required


@dataclass
class Alert:
    """Represents a detected anomaly alert."""
    alert_type: AlertType
    severity: AlertSeverity
    message: str
    details: Dict[str, Any] = field(default_factory=dict)
    timestamp: Optional[datetime] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert alert to dictionary."""
        return {
            "type": self.alert_type.value,
            "severity": self.severity.value,
            "message": self.message,
            "details": self.details,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
        }


# Alert thresholds (configurable)
ALERT_THRESHOLDS = {
    "sudden_score_drop": 20,        # Points
    "sustained_decline_count": 3,   # Consecutive readings
    "spo2_critical": 92,            # Percentage
    "spo2_warning": 94,             # Percentage
    "hrv_drop_percent": 30,         # Percentage drop
    "hr_increase_percent": 40,      # Percentage increase
    "critical_score": 30,           # Score threshold
    "recovery_time_minutes": 15,    # Time in warning zone
}


def detect_sudden_score_drop(
    current_score: float,
    previous_score: float,
    threshold: float = None
) -> Optional[Alert]:
    """
    Detect sudden large score drops.
    
    Args:
        current_score: Current CardioTwin score
        previous_score: Previous score
        threshold: Drop threshold (default: 20 points)
        
    Returns:
        Alert if significant drop detected, None otherwise
    """
    threshold = threshold or ALERT_THRESHOLDS["sudden_score_drop"]
    drop = previous_score - current_score
    
    if drop >= threshold:
        severity = AlertSeverity.URGENT if drop >= 30 else AlertSeverity.WARNING
        return Alert(
            alert_type=AlertType.SUDDEN_SCORE_DROP,
            severity=severity,
            message=f"Score dropped {drop:.0f} points",
            details={
                "previous_score": previous_score,
                "current_score": current_score,
                "drop": drop,
            }
        )
    return None


def detect_zone_downgrade(
    current_zone: Zone,
    previous_zone: Zone
) -> Optional[Alert]:
    """
    Detect zone downgrades.
    
    Args:
        current_zone: Current zone
        previous_zone: Previous zone
        
    Returns:
        Alert if zone downgraded, None otherwise
    """
    zone_order = [Zone.GREEN, Zone.YELLOW, Zone.ORANGE, Zone.RED]
    current_idx = zone_order.index(current_zone)
    previous_idx = zone_order.index(previous_zone)
    
    # Current is worse (higher index)
    if current_idx > previous_idx:
        downgrade_steps = current_idx - previous_idx
        
        # Determine severity based on new zone and drop magnitude
        if current_zone == Zone.RED:
            severity = AlertSeverity.CRITICAL
        elif current_zone == Zone.ORANGE or downgrade_steps >= 2:
            severity = AlertSeverity.URGENT
        else:
            severity = AlertSeverity.WARNING
        
        return Alert(
            alert_type=AlertType.ZONE_DOWNGRADE,
            severity=severity,
            message=f"Status changed from {previous_zone.value.upper()} to {current_zone.value.upper()}",
            details={
                "previous_zone": previous_zone.value,
                "current_zone": current_zone.value,
                "downgrade_steps": downgrade_steps,
            }
        )
    return None


def detect_critical_threshold(score: float) -> Optional[Alert]:
    """
    Detect critical score threshold breach.
    
    Args:
        score: Current CardioTwin score
        
    Returns:
        Alert if score is critical, None otherwise
    """
    threshold = ALERT_THRESHOLDS["critical_score"]
    
    if score < threshold:
        severity = AlertSeverity.CRITICAL if score < 20 else AlertSeverity.URGENT
        return Alert(
            alert_type=AlertType.CRITICAL_THRESHOLD,
            severity=severity,
            message=f"Critical score: {score:.0f} - Immediate rest recommended",
            details={
                "score": score,
                "threshold": threshold,
            }
        )
    return None


def detect_sustained_decline(
    scores: List[float],
    min_consecutive: int = None
) -> Optional[Alert]:
    """
    Detect sustained decline pattern.
    
    Args:
        scores: Recent scores (newest last)
        min_consecutive: Minimum consecutive drops to trigger
        
    Returns:
        Alert if sustained decline detected, None otherwise
    """
    min_consecutive = min_consecutive or ALERT_THRESHOLDS["sustained_decline_count"]
    
    if len(scores) < min_consecutive + 1:
        return None
    
    # Check last N+1 scores for N consecutive declines
    recent = scores[-(min_consecutive + 1):]
    consecutive_drops = 0
    
    for i in range(1, len(recent)):
        if recent[i] < recent[i-1] - 2:  # Allow 2-point tolerance
            consecutive_drops += 1
        else:
            consecutive_drops = 0  # Reset if not declining
    
    if consecutive_drops >= min_consecutive:
        total_drop = recent[0] - recent[-1]
        severity = AlertSeverity.URGENT if total_drop > 25 else AlertSeverity.WARNING
        
        return Alert(
            alert_type=AlertType.SUSTAINED_DECLINE,
            severity=severity,
            message=f"{consecutive_drops} consecutive score declines detected",
            details={
                "consecutive_drops": consecutive_drops,
                "total_drop": total_drop,
                "starting_score": recent[0],
                "current_score": recent[-1],
            }
        )
    return None


def detect_spo2_critical(
    spo2: float,
    critical_threshold: float = None,
    warning_threshold: float = None
) -> Optional[Alert]:
    """
    Detect critical SpO2 levels.
    
    Args:
        spo2: Current SpO2 percentage
        critical_threshold: Critical level (default: 92%)
        warning_threshold: Warning level (default: 94%)
        
    Returns:
        Alert if SpO2 is concerning, None otherwise
    """
    critical_threshold = critical_threshold or ALERT_THRESHOLDS["spo2_critical"]
    warning_threshold = warning_threshold or ALERT_THRESHOLDS["spo2_warning"]
    
    if spo2 < critical_threshold:
        severity = AlertSeverity.CRITICAL if spo2 < 90 else AlertSeverity.URGENT
        return Alert(
            alert_type=AlertType.SPO2_CRITICAL,
            severity=severity,
            message=f"Low blood oxygen: {spo2:.0f}% - Consult healthcare provider if persists",
            details={
                "spo2": spo2,
                "critical_threshold": critical_threshold,
            }
        )
    elif spo2 < warning_threshold:
        return Alert(
            alert_type=AlertType.SPO2_CRITICAL,
            severity=AlertSeverity.WARNING,
            message=f"Blood oxygen slightly low: {spo2:.0f}%",
            details={
                "spo2": spo2,
                "warning_threshold": warning_threshold,
            }
        )
    return None


def detect_hrv_sudden_drop(
    current_hrv: float,
    baseline_hrv: float,
    threshold_percent: float = None
) -> Optional[Alert]:
    """
    Detect sudden HRV drops.
    
    Args:
        current_hrv: Current HRV/RMSSD value
        baseline_hrv: Baseline HRV value
        threshold_percent: Percent drop threshold (default: 30%)
        
    Returns:
        Alert if sudden HRV drop, None otherwise
    """
    threshold_percent = threshold_percent or ALERT_THRESHOLDS["hrv_drop_percent"]
    
    if baseline_hrv <= 0:
        return None
    
    drop_percent = ((baseline_hrv - current_hrv) / baseline_hrv) * 100
    
    if drop_percent >= threshold_percent:
        severity = AlertSeverity.URGENT if drop_percent >= 50 else AlertSeverity.WARNING
        return Alert(
            alert_type=AlertType.HRV_SUDDEN_DROP,
            severity=severity,
            message=f"Heart rate variability dropped {drop_percent:.0f}%",
            details={
                "current_hrv": current_hrv,
                "baseline_hrv": baseline_hrv,
                "drop_percent": drop_percent,
            }
        )
    return None


def detect_hr_rapid_increase(
    current_hr: float,
    baseline_hr: float,
    threshold_percent: float = None
) -> Optional[Alert]:
    """
    Detect rapid heart rate increases.
    
    Args:
        current_hr: Current heart rate (BPM)
        baseline_hr: Baseline heart rate
        threshold_percent: Percent increase threshold (default: 40%)
        
    Returns:
        Alert if rapid HR increase, None otherwise
    """
    threshold_percent = threshold_percent or ALERT_THRESHOLDS["hr_increase_percent"]
    
    if baseline_hr <= 0:
        return None
    
    increase_percent = ((current_hr - baseline_hr) / baseline_hr) * 100
    
    if increase_percent >= threshold_percent:
        severity = AlertSeverity.URGENT if increase_percent >= 60 else AlertSeverity.WARNING
        return Alert(
            alert_type=AlertType.HR_RAPID_INCREASE,
            severity=severity,
            message=f"Heart rate increased {increase_percent:.0f}% from baseline",
            details={
                "current_hr": current_hr,
                "baseline_hr": baseline_hr,
                "increase_percent": increase_percent,
            }
        )
    return None


def detect_multi_component_decline(
    component_scores: Dict[str, float],
    threshold: float = 50
) -> Optional[Alert]:
    """
    Detect when multiple components are declining.
    
    Args:
        component_scores: Dict with hr, hrv, spo2, temp scores
        threshold: Score below which component is "low"
        
    Returns:
        Alert if multiple components are low, None otherwise
    """
    low_components = [k for k, v in component_scores.items() if v < threshold]
    
    if len(low_components) >= 3:
        severity = AlertSeverity.URGENT
        return Alert(
            alert_type=AlertType.MULTI_COMPONENT_DECLINE,
            severity=severity,
            message=f"Multiple health metrics declining: {', '.join(low_components)}",
            details={
                "low_components": low_components,
                "component_scores": component_scores,
            }
        )
    elif len(low_components) >= 2:
        return Alert(
            alert_type=AlertType.MULTI_COMPONENT_DECLINE,
            severity=AlertSeverity.WARNING,
            message=f"Two health metrics need attention: {', '.join(low_components)}",
            details={
                "low_components": low_components,
                "component_scores": component_scores,
            }
        )
    return None


@dataclass
class AnomalyDetectionResult:
    """Complete result of anomaly detection."""
    alerts: List[Alert]
    highest_severity: Optional[AlertSeverity]
    should_notify: bool
    summary: str
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary."""
        return {
            "alerts": [a.to_dict() for a in self.alerts],
            "highest_severity": self.highest_severity.value if self.highest_severity else None,
            "should_notify": self.should_notify,
            "summary": self.summary,
        }


def detect_anomalies(
    current_score: float,
    previous_score: Optional[float] = None,
    score_history: Optional[List[float]] = None,
    current_zone: Optional[Zone] = None,
    previous_zone: Optional[Zone] = None,
    baseline: Optional[Dict[str, float]] = None,
    current_reading: Optional[Dict[str, float]] = None,
    component_scores: Optional[Dict[str, float]] = None,
) -> AnomalyDetectionResult:
    """
    Run all anomaly detection checks.
    
    Args:
        current_score: Current CardioTwin score
        previous_score: Previous score (optional)
        score_history: List of recent scores (optional)
        current_zone: Current zone (calculated if not provided)
        previous_zone: Previous zone (calculated from previous_score if not provided)
        baseline: Baseline readings dict with hr, hrv, spo2, temp
        current_reading: Current readings dict with hr, hrv, spo2, temp
        component_scores: Individual component scores
        
    Returns:
        AnomalyDetectionResult with all alerts
    """
    alerts: List[Alert] = []
    
    # Calculate zones if not provided
    if current_zone is None:
        current_zone = classify_zone(current_score)
    if previous_zone is None and previous_score is not None:
        previous_zone = classify_zone(previous_score)
    
    # Check critical threshold
    critical_alert = detect_critical_threshold(current_score)
    if critical_alert:
        alerts.append(critical_alert)
    
    # Check sudden score drop
    if previous_score is not None:
        drop_alert = detect_sudden_score_drop(current_score, previous_score)
        if drop_alert:
            alerts.append(drop_alert)
    
    # Check zone downgrade
    if previous_zone is not None:
        zone_alert = detect_zone_downgrade(current_zone, previous_zone)
        if zone_alert:
            alerts.append(zone_alert)
    
    # Check sustained decline
    if score_history is not None and len(score_history) >= 4:
        decline_alert = detect_sustained_decline(score_history)
        if decline_alert:
            alerts.append(decline_alert)
    
    # Check raw metric alerts if baseline and current readings provided
    if baseline is not None and current_reading is not None:
        # SpO2 critical (uses absolute threshold, not baseline)
        if "spo2" in current_reading:
            spo2_alert = detect_spo2_critical(current_reading["spo2"])
            if spo2_alert:
                alerts.append(spo2_alert)
        
        # HRV sudden drop
        if "hrv" in baseline and "hrv" in current_reading:
            hrv_alert = detect_hrv_sudden_drop(
                current_reading["hrv"],
                baseline["hrv"]
            )
            if hrv_alert:
                alerts.append(hrv_alert)
        
        # HR rapid increase
        if "hr" in baseline and "hr" in current_reading:
            hr_alert = detect_hr_rapid_increase(
                current_reading["hr"],
                baseline["hr"]
            )
            if hr_alert:
                alerts.append(hr_alert)
    
    # Check multi-component decline
    if component_scores is not None:
        multi_alert = detect_multi_component_decline(component_scores)
        if multi_alert:
            alerts.append(multi_alert)
    
    # Determine highest severity and notification decision
    highest_severity = None
    if alerts:
        severity_order = [
            AlertSeverity.INFO,
            AlertSeverity.WARNING,
            AlertSeverity.URGENT,
            AlertSeverity.CRITICAL,
        ]
        highest_severity = max(
            [a.severity for a in alerts],
            key=lambda s: severity_order.index(s)
        )
    
    # Should notify if any alert is WARNING or higher
    should_notify = highest_severity in (
        AlertSeverity.WARNING,
        AlertSeverity.URGENT,
        AlertSeverity.CRITICAL,
    ) if highest_severity else False
    
    # Generate summary
    if not alerts:
        summary = "No anomalies detected"
    elif highest_severity == AlertSeverity.CRITICAL:
        summary = f"CRITICAL: {len(alerts)} alert(s) require immediate attention"
    elif highest_severity == AlertSeverity.URGENT:
        summary = f"URGENT: {len(alerts)} alert(s) detected - action recommended"
    else:
        summary = f"{len(alerts)} alert(s) detected"
    
    return AnomalyDetectionResult(
        alerts=alerts,
        highest_severity=highest_severity,
        should_notify=should_notify,
        summary=summary,
    )


def get_alert_severity(alert_type: AlertType, details: Dict[str, Any] = None) -> AlertSeverity:
    """
    Get appropriate severity for an alert type.
    
    Args:
        alert_type: Type of alert
        details: Additional details to determine severity
        
    Returns:
        AlertSeverity level
    """
    # Base severity by type
    base_severity = {
        AlertType.SUDDEN_SCORE_DROP: AlertSeverity.WARNING,
        AlertType.ZONE_DOWNGRADE: AlertSeverity.WARNING,
        AlertType.CRITICAL_THRESHOLD: AlertSeverity.CRITICAL,
        AlertType.SUSTAINED_DECLINE: AlertSeverity.WARNING,
        AlertType.SPO2_CRITICAL: AlertSeverity.URGENT,
        AlertType.HRV_SUDDEN_DROP: AlertSeverity.WARNING,
        AlertType.HR_RAPID_INCREASE: AlertSeverity.WARNING,
        AlertType.MULTI_COMPONENT_DECLINE: AlertSeverity.WARNING,
        AlertType.RECOVERY_NEEDED: AlertSeverity.INFO,
    }
    
    return base_severity.get(alert_type, AlertSeverity.INFO)


def should_notify_user(result: AnomalyDetectionResult) -> Tuple[bool, str]:
    """
    Determine if user should be notified and how.
    
    Args:
        result: Anomaly detection result
        
    Returns:
        Tuple of (should_notify, notification_type)
    """
    if not result.should_notify:
        return False, "none"
    
    if result.highest_severity == AlertSeverity.CRITICAL:
        return True, "immediate_alert"
    elif result.highest_severity == AlertSeverity.URGENT:
        return True, "prominent_alert"
    elif result.highest_severity == AlertSeverity.WARNING:
        return True, "nudge"
    else:
        return False, "log_only"


def get_alert_context_for_nudge(alerts: List[Alert]) -> Dict[str, Any]:
    """
    Prepare alert context for nudge generation.
    
    Args:
        alerts: List of detected alerts
        
    Returns:
        Context dictionary for Grok API nudge generation
    """
    if not alerts:
        return {"has_alerts": False}
    
    # Sort by severity (most severe first)
    severity_order = [
        AlertSeverity.CRITICAL,
        AlertSeverity.URGENT,
        AlertSeverity.WARNING,
        AlertSeverity.INFO,
    ]
    sorted_alerts = sorted(
        alerts,
        key=lambda a: severity_order.index(a.severity)
    )
    
    primary_alert = sorted_alerts[0]
    
    return {
        "has_alerts": True,
        "alert_count": len(alerts),
        "primary_alert": {
            "type": primary_alert.alert_type.value,
            "severity": primary_alert.severity.value,
            "message": primary_alert.message,
        },
        "all_alert_types": [a.alert_type.value for a in alerts],
        "requires_immediate_action": primary_alert.severity in (
            AlertSeverity.CRITICAL,
            AlertSeverity.URGENT,
        ),
    }
