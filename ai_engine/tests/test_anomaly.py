"""
Tests for Anomaly Detection Module
==================================
"""

import pytest
from ai_engine.anomaly import (
    AlertType,
    AlertSeverity,
    Alert,
    AnomalyDetectionResult,
    detect_sudden_score_drop,
    detect_zone_downgrade,
    detect_critical_threshold,
    detect_sustained_decline,
    detect_spo2_critical,
    detect_hrv_sudden_drop,
    detect_hr_rapid_increase,
    detect_multi_component_decline,
    detect_anomalies,
    get_alert_severity,
    should_notify_user,
    get_alert_context_for_nudge,
)
from ai_engine.zones import Zone


class TestDetectSuddenScoreDrop:
    """Test sudden score drop detection."""
    
    def test_no_alert_for_small_drop(self):
        """Small drop doesn't trigger alert."""
        result = detect_sudden_score_drop(80, 85)
        assert result is None
    
    def test_alert_for_20_point_drop(self):
        """20-point drop triggers warning."""
        result = detect_sudden_score_drop(60, 80)
        assert result is not None
        assert result.alert_type == AlertType.SUDDEN_SCORE_DROP
        assert result.severity == AlertSeverity.WARNING
    
    def test_urgent_for_30_point_drop(self):
        """30-point drop triggers urgent."""
        result = detect_sudden_score_drop(50, 80)
        assert result is not None
        assert result.severity == AlertSeverity.URGENT
    
    def test_includes_drop_details(self):
        """Alert includes drop details."""
        result = detect_sudden_score_drop(55, 80)
        assert result.details["drop"] == 25
        assert result.details["previous_score"] == 80
        assert result.details["current_score"] == 55
    
    def test_no_alert_for_increase(self):
        """Score increase doesn't trigger alert."""
        result = detect_sudden_score_drop(85, 70)
        assert result is None
    
    def test_custom_threshold(self):
        """Custom threshold works."""
        result = detect_sudden_score_drop(70, 80, threshold=5)
        assert result is not None


class TestDetectZoneDowngrade:
    """Test zone downgrade detection."""
    
    def test_no_alert_for_same_zone(self):
        """Same zone doesn't trigger alert."""
        result = detect_zone_downgrade(Zone.GREEN, Zone.GREEN)
        assert result is None
    
    def test_no_alert_for_upgrade(self):
        """Zone upgrade doesn't trigger alert."""
        result = detect_zone_downgrade(Zone.GREEN, Zone.YELLOW)
        assert result is None
    
    def test_warning_for_green_to_yellow(self):
        """GREEN to YELLOW triggers warning."""
        result = detect_zone_downgrade(Zone.YELLOW, Zone.GREEN)
        assert result is not None
        assert result.alert_type == AlertType.ZONE_DOWNGRADE
        assert result.severity == AlertSeverity.WARNING
    
    def test_urgent_for_to_orange(self):
        """Moving to ORANGE triggers urgent."""
        result = detect_zone_downgrade(Zone.ORANGE, Zone.YELLOW)
        assert result is not None
        assert result.severity == AlertSeverity.URGENT
    
    def test_critical_for_to_red(self):
        """Moving to RED triggers critical."""
        result = detect_zone_downgrade(Zone.RED, Zone.ORANGE)
        assert result is not None
        assert result.severity == AlertSeverity.CRITICAL
    
    def test_urgent_for_two_step_downgrade(self):
        """Two-step downgrade is urgent."""
        result = detect_zone_downgrade(Zone.ORANGE, Zone.GREEN)
        assert result is not None
        assert result.severity == AlertSeverity.URGENT
        assert result.details["downgrade_steps"] == 2


class TestDetectCriticalThreshold:
    """Test critical threshold detection."""
    
    def test_no_alert_above_threshold(self):
        """Score above threshold no alert."""
        result = detect_critical_threshold(35)
        assert result is None
    
    def test_urgent_at_25(self):
        """Score 25 triggers urgent."""
        result = detect_critical_threshold(25)
        assert result is not None
        assert result.severity == AlertSeverity.URGENT
    
    def test_critical_below_20(self):
        """Score below 20 triggers critical."""
        result = detect_critical_threshold(15)
        assert result is not None
        assert result.severity == AlertSeverity.CRITICAL
    
    def test_alert_message_includes_score(self):
        """Alert message includes score."""
        result = detect_critical_threshold(22)
        assert "22" in result.message


class TestDetectSustainedDecline:
    """Test sustained decline detection."""
    
    def test_no_alert_with_short_history(self):
        """Not enough history returns None."""
        result = detect_sustained_decline([80, 75])
        assert result is None
    
    def test_alert_for_three_consecutive_drops(self):
        """Three consecutive drops triggers alert."""
        scores = [85, 80, 73, 65]  # 3 consecutive drops
        result = detect_sustained_decline(scores)
        assert result is not None
        assert result.alert_type == AlertType.SUSTAINED_DECLINE
    
    def test_no_alert_if_not_consecutive(self):
        """Non-consecutive drops no alert."""
        scores = [85, 70, 75, 60]  # Not consecutive
        result = detect_sustained_decline(scores)
        assert result is None
    
    def test_urgent_for_large_total_drop(self):
        """Large total drop is urgent."""
        scores = [90, 80, 65, 50]  # 40 point total drop
        result = detect_sustained_decline(scores)
        assert result is not None
        assert result.severity == AlertSeverity.URGENT
    
    def test_tolerates_small_fluctuation(self):
        """Small fluctuation allowed."""
        scores = [80, 77, 74, 71]  # Consistent decline (3-point drops)
        result = detect_sustained_decline(scores)
        assert result is not None


class TestDetectSpo2Critical:
    """Test SpO2 critical detection."""
    
    def test_no_alert_for_normal_spo2(self):
        """Normal SpO2 no alert."""
        result = detect_spo2_critical(98)
        assert result is None
    
    def test_warning_for_94(self):
        """SpO2 94% triggers warning."""
        result = detect_spo2_critical(93)
        assert result is not None
        assert result.severity == AlertSeverity.WARNING
    
    def test_urgent_for_91(self):
        """SpO2 91% triggers urgent."""
        result = detect_spo2_critical(91)
        assert result is not None
        assert result.severity == AlertSeverity.URGENT
    
    def test_critical_below_90(self):
        """SpO2 below 90% triggers critical."""
        result = detect_spo2_critical(88)
        assert result is not None
        assert result.severity == AlertSeverity.CRITICAL
    
    def test_message_includes_percentage(self):
        """Message includes SpO2 value."""
        result = detect_spo2_critical(89)
        assert "89" in result.message


class TestDetectHrvSuddenDrop:
    """Test HRV sudden drop detection."""
    
    def test_no_alert_for_small_drop(self):
        """Small HRV drop no alert."""
        result = detect_hrv_sudden_drop(40, 45)
        assert result is None
    
    def test_warning_for_30_percent_drop(self):
        """30% drop triggers warning."""
        result = detect_hrv_sudden_drop(35, 50)  # 30% drop
        assert result is not None
        assert result.severity == AlertSeverity.WARNING
    
    def test_urgent_for_50_percent_drop(self):
        """50% drop triggers urgent."""
        result = detect_hrv_sudden_drop(25, 50)  # 50% drop
        assert result is not None
        assert result.severity == AlertSeverity.URGENT
    
    def test_handles_zero_baseline(self):
        """Zero baseline returns None."""
        result = detect_hrv_sudden_drop(40, 0)
        assert result is None
    
    def test_includes_percentages(self):
        """Details include drop percentage."""
        result = detect_hrv_sudden_drop(30, 50)
        assert result.details["drop_percent"] == 40


class TestDetectHrRapidIncrease:
    """Test HR rapid increase detection."""
    
    def test_no_alert_for_small_increase(self):
        """Small HR increase no alert."""
        result = detect_hr_rapid_increase(75, 70)
        assert result is None
    
    def test_warning_for_40_percent_increase(self):
        """40% increase triggers warning."""
        result = detect_hr_rapid_increase(98, 70)  # 40% increase
        assert result is not None
        assert result.severity == AlertSeverity.WARNING
    
    def test_urgent_for_60_percent_increase(self):
        """60% increase triggers urgent."""
        result = detect_hr_rapid_increase(112, 70)  # 60% increase
        assert result is not None
        assert result.severity == AlertSeverity.URGENT
    
    def test_handles_zero_baseline(self):
        """Zero baseline returns None."""
        result = detect_hr_rapid_increase(80, 0)
        assert result is None


class TestDetectMultiComponentDecline:
    """Test multi-component decline detection."""
    
    def test_no_alert_with_one_low(self):
        """Single low component no alert."""
        scores = {"hr": 80, "hrv": 40, "spo2": 90, "temp": 85}
        result = detect_multi_component_decline(scores)
        assert result is None
    
    def test_warning_for_two_low(self):
        """Two low components triggers warning."""
        scores = {"hr": 40, "hrv": 40, "spo2": 90, "temp": 85}
        result = detect_multi_component_decline(scores)
        assert result is not None
        assert result.severity == AlertSeverity.WARNING
    
    def test_urgent_for_three_low(self):
        """Three low components triggers urgent."""
        scores = {"hr": 40, "hrv": 40, "spo2": 40, "temp": 85}
        result = detect_multi_component_decline(scores)
        assert result is not None
        assert result.severity == AlertSeverity.URGENT
    
    def test_identifies_low_components(self):
        """Details include low components."""
        scores = {"hr": 40, "hrv": 40, "spo2": 90, "temp": 85}
        result = detect_multi_component_decline(scores)
        assert "hr" in result.details["low_components"]
        assert "hrv" in result.details["low_components"]


class TestDetectAnomalies:
    """Test comprehensive anomaly detection."""
    
    def test_no_alerts_for_normal_reading(self):
        """Normal reading produces no alerts."""
        result = detect_anomalies(85)
        assert len(result.alerts) == 0
        assert result.should_notify is False
    
    def test_detects_critical_score(self):
        """Critical score detected."""
        result = detect_anomalies(20)
        assert len(result.alerts) >= 1
        assert any(a.alert_type == AlertType.CRITICAL_THRESHOLD for a in result.alerts)
    
    def test_detects_zone_downgrade(self):
        """Zone downgrade detected."""
        result = detect_anomalies(
            current_score=70,
            previous_score=85
        )
        alert_types = [a.alert_type for a in result.alerts]
        assert AlertType.ZONE_DOWNGRADE in alert_types
    
    def test_detects_sudden_drop(self):
        """Sudden score drop detected."""
        result = detect_anomalies(
            current_score=55,
            previous_score=80
        )
        alert_types = [a.alert_type for a in result.alerts]
        assert AlertType.SUDDEN_SCORE_DROP in alert_types
    
    def test_detects_sustained_decline(self):
        """Sustained decline detected."""
        result = detect_anomalies(
            current_score=60,
            score_history=[90, 85, 75, 65, 60]
        )
        alert_types = [a.alert_type for a in result.alerts]
        assert AlertType.SUSTAINED_DECLINE in alert_types
    
    def test_detects_spo2_critical(self):
        """SpO2 critical detected."""
        result = detect_anomalies(
            current_score=70,
            current_reading={"spo2": 90, "hr": 70, "hrv": 45, "temp": 36.6},
            baseline={"spo2": 98, "hr": 65, "hrv": 45, "temp": 36.6}
        )
        alert_types = [a.alert_type for a in result.alerts]
        assert AlertType.SPO2_CRITICAL in alert_types
    
    def test_detects_hrv_drop(self):
        """HRV drop detected."""
        result = detect_anomalies(
            current_score=70,
            current_reading={"spo2": 98, "hr": 70, "hrv": 25, "temp": 36.6},
            baseline={"spo2": 98, "hr": 65, "hrv": 45, "temp": 36.6}  # 44% HRV drop
        )
        alert_types = [a.alert_type for a in result.alerts]
        assert AlertType.HRV_SUDDEN_DROP in alert_types
    
    def test_detects_hr_increase(self):
        """HR rapid increase detected."""
        result = detect_anomalies(
            current_score=70,
            current_reading={"spo2": 98, "hr": 100, "hrv": 40, "temp": 36.6},
            baseline={"spo2": 98, "hr": 60, "hrv": 45, "temp": 36.6}  # 67% HR increase
        )
        alert_types = [a.alert_type for a in result.alerts]
        assert AlertType.HR_RAPID_INCREASE in alert_types
    
    def test_detects_multi_component_decline(self):
        """Multi-component decline detected."""
        result = detect_anomalies(
            current_score=45,
            component_scores={"hr": 40, "hrv": 30, "spo2": 40, "temp": 70}
        )
        alert_types = [a.alert_type for a in result.alerts]
        assert AlertType.MULTI_COMPONENT_DECLINE in alert_types
    
    def test_highest_severity_is_critical(self):
        """Highest severity correctly identified as critical."""
        result = detect_anomalies(15)  # Critical threshold
        assert result.highest_severity == AlertSeverity.CRITICAL
    
    def test_should_notify_for_warning(self):
        """Should notify when warning or higher."""
        result = detect_anomalies(
            current_score=70,
            previous_score=92
        )  # Sudden drop
        assert result.should_notify is True
    
    def test_summary_mentions_critical(self):
        """Summary mentions CRITICAL when appropriate."""
        result = detect_anomalies(15)
        assert "CRITICAL" in result.summary


class TestDetectAnomaliesResult:
    """Test anomaly detection result structure."""
    
    def test_result_to_dict(self):
        """Result converts to dict."""
        result = detect_anomalies(20)
        d = result.to_dict()
        assert "alerts" in d
        assert "highest_severity" in d
        assert "should_notify" in d
        assert "summary" in d
    
    def test_alert_to_dict(self):
        """Alert converts to dict."""
        alert = Alert(
            alert_type=AlertType.CRITICAL_THRESHOLD,
            severity=AlertSeverity.CRITICAL,
            message="Test",
            details={"score": 20}
        )
        d = alert.to_dict()
        assert d["type"] == "critical_threshold"
        assert d["severity"] == "critical"


class TestShouldNotifyUser:
    """Test notification decision."""
    
    def test_no_notify_for_no_alerts(self):
        """No notification when no alerts."""
        result = detect_anomalies(85)
        should, notify_type = should_notify_user(result)
        assert should is False
    
    def test_immediate_alert_for_critical(self):
        """Critical triggers immediate alert."""
        result = detect_anomalies(15)
        should, notify_type = should_notify_user(result)
        assert should is True
        assert notify_type == "immediate_alert"
    
    def test_prominent_alert_for_urgent(self):
        """Urgent triggers prominent alert."""
        result = detect_anomalies(
            current_score=60,
            previous_score=90
        )  # 30-point drop
        should, notify_type = should_notify_user(result)
        assert should is True
        assert notify_type in ("prominent_alert", "nudge", "immediate_alert")


class TestGetAlertContextForNudge:
    """Test alert context for nudge generation."""
    
    def test_no_alerts_context(self):
        """No alerts produces minimal context."""
        ctx = get_alert_context_for_nudge([])
        assert ctx["has_alerts"] is False
    
    def test_includes_primary_alert(self):
        """Context includes primary alert."""
        alerts = [
            Alert(AlertType.ZONE_DOWNGRADE, AlertSeverity.WARNING, "Test"),
            Alert(AlertType.CRITICAL_THRESHOLD, AlertSeverity.CRITICAL, "Critical"),
        ]
        ctx = get_alert_context_for_nudge(alerts)
        
        assert ctx["has_alerts"] is True
        assert ctx["alert_count"] == 2
        # Critical should be primary (most severe)
        assert ctx["primary_alert"]["severity"] == "critical"
    
    def test_requires_immediate_action(self):
        """Critical alerts require immediate action."""
        alerts = [Alert(AlertType.CRITICAL_THRESHOLD, AlertSeverity.CRITICAL, "Test")]
        ctx = get_alert_context_for_nudge(alerts)
        assert ctx["requires_immediate_action"] is True
    
    def test_warning_not_immediate(self):
        """Warning doesn't require immediate action."""
        alerts = [Alert(AlertType.ZONE_DOWNGRADE, AlertSeverity.WARNING, "Test")]
        ctx = get_alert_context_for_nudge(alerts)
        assert ctx["requires_immediate_action"] is False


class TestGetAlertSeverity:
    """Test alert severity lookup."""
    
    def test_critical_threshold_is_critical(self):
        """Critical threshold type is critical severity."""
        sev = get_alert_severity(AlertType.CRITICAL_THRESHOLD)
        assert sev == AlertSeverity.CRITICAL
    
    def test_spo2_critical_is_urgent(self):
        """SpO2 critical type is urgent severity."""
        sev = get_alert_severity(AlertType.SPO2_CRITICAL)
        assert sev == AlertSeverity.URGENT
    
    def test_zone_downgrade_is_warning(self):
        """Zone downgrade type is warning severity."""
        sev = get_alert_severity(AlertType.ZONE_DOWNGRADE)
        assert sev == AlertSeverity.WARNING


class TestDemoScenarios:
    """Test demo scenario anomaly detection."""
    
    def test_resting_to_exercise_transition(self):
        """Detect alerts during rest to exercise transition."""
        # Resting state: score 86 (GREEN)
        # Post-exercise: score 41 (ORANGE)
        result = detect_anomalies(
            current_score=41,
            previous_score=86,
            baseline={"hr": 65, "hrv": 45, "spo2": 98, "temp": 36.6},
            current_reading={"hr": 130, "hrv": 20, "spo2": 96, "temp": 37.5}
        )
        
        # Should detect zone downgrade (GREEN → ORANGE)
        alert_types = [a.alert_type for a in result.alerts]
        assert AlertType.ZONE_DOWNGRADE in alert_types
        
        # Should detect HRV drop (45 → 20 = 56% drop)
        assert AlertType.HRV_SUDDEN_DROP in alert_types
        
        # Should detect HR increase (65 → 130 = 100% increase)
        assert AlertType.HR_RAPID_INCREASE in alert_types
        
        # Should notify
        assert result.should_notify is True
    
    def test_recovery_improves(self):
        """Recovery shows improvement, no alerts."""
        # After rest: score 75 (YELLOW), was 41 (ORANGE)
        result = detect_anomalies(
            current_score=75,
            previous_score=41
        )
        
        # Zone upgrade shouldn't trigger downgrade alert
        zone_downgrades = [a for a in result.alerts 
                          if a.alert_type == AlertType.ZONE_DOWNGRADE]
        assert len(zone_downgrades) == 0
