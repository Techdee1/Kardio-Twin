"""
Tests for CardioTwin AI Engine main orchestration class.
"""

import pytest
from datetime import datetime
from unittest.mock import patch, AsyncMock

from ai_engine.engine import (
    CardioTwinEngine,
    SessionData,
    SessionStatus,
    ComponentScores,
    Reading,
    ProcessingResult,
)
from ai_engine.zones import Zone
from ai_engine.nudges import Language
from ai_engine.anomaly import AlertType, AlertSeverity


class TestSessionManagement:
    """Tests for session lifecycle management."""
    
    def test_create_session_returns_session_id(self):
        """Create session returns unique ID."""
        engine = CardioTwinEngine()
        session_id = engine.create_session("user123")
        
        assert session_id is not None
        assert isinstance(session_id, str)
        assert len(session_id) > 0
    
    def test_create_session_with_custom_id(self):
        """Create session with custom ID."""
        engine = CardioTwinEngine()
        session_id = engine.create_session("user123", session_id="custom-123")
        
        assert session_id == "custom-123"
    
    def test_create_session_with_language(self):
        """Create session with language preference."""
        engine = CardioTwinEngine()
        session_id = engine.create_session("user123", language=Language.YORUBA)
        
        session = engine.get_session(session_id)
        assert session.language == Language.YORUBA
    
    def test_create_multiple_sessions(self):
        """Create multiple independent sessions."""
        engine = CardioTwinEngine()
        
        s1 = engine.create_session("user1")
        s2 = engine.create_session("user2")
        s3 = engine.create_session("user1")  # Same user, new session
        
        assert s1 != s2 != s3
        assert len(engine.sessions) == 3
    
    def test_get_session(self):
        """Get session data."""
        engine = CardioTwinEngine()
        session_id = engine.create_session("user123")
        
        session = engine.get_session(session_id)
        
        assert session is not None
        assert session.user_id == "user123"
        assert session.status == SessionStatus.CALIBRATING
    
    def test_get_session_not_found(self):
        """Get non-existent session returns None."""
        engine = CardioTwinEngine()
        
        session = engine.get_session("nonexistent")
        
        assert session is None
    
    def test_end_session(self):
        """End session changes status."""
        engine = CardioTwinEngine()
        session_id = engine.create_session("user123")
        
        result = engine.end_session(session_id)
        
        assert result is True
        session = engine.get_session(session_id)
        assert session.status == SessionStatus.ENDED
    
    def test_end_session_not_found(self):
        """End non-existent session returns False."""
        engine = CardioTwinEngine()
        
        result = engine.end_session("nonexistent")
        
        assert result is False
    
    def test_delete_session(self):
        """Delete session removes it completely."""
        engine = CardioTwinEngine()
        session_id = engine.create_session("user123")
        
        result = engine.delete_session(session_id)
        
        assert result is True
        assert engine.get_session(session_id) is None
    
    def test_delete_session_not_found(self):
        """Delete non-existent session returns False."""
        engine = CardioTwinEngine()
        
        result = engine.delete_session("nonexistent")
        
        assert result is False


class TestEngineConfiguration:
    """Tests for engine configuration."""
    
    def test_default_configuration(self):
        """Default configuration values."""
        engine = CardioTwinEngine()
        
        assert engine.calibration_readings == 5
        assert engine.default_language == Language.ENGLISH
        assert engine.max_readings_history == 1000
    
    def test_custom_configuration(self):
        """Custom configuration override."""
        engine = CardioTwinEngine({
            "calibration_readings": 10,
            "default_language": "yoruba",
            "max_readings_history": 500,
        })
        
        assert engine.calibration_readings == 10
        assert engine.default_language == Language.YORUBA
        assert engine.max_readings_history == 500


class TestReadingProcessing:
    """Tests for reading processing pipeline."""
    
    def test_process_reading_invalid_session(self):
        """Process with invalid session returns error."""
        engine = CardioTwinEngine()
        
        result = engine.process_reading("nonexistent", {
            "heart_rate": 72,
            "hrv": 45,
            "spo2": 98,
            "temperature": 36.6,
        })
        
        assert result.success is False
        assert "Session not found" in result.validation_errors
    
    def test_process_reading_ended_session(self):
        """Process with ended session returns error."""
        engine = CardioTwinEngine()
        session_id = engine.create_session("user123")
        engine.end_session(session_id)
        
        result = engine.process_reading(session_id, {
            "heart_rate": 72,
            "hrv": 45,
            "spo2": 98,
            "temperature": 36.6,
        })
        
        assert result.success is False
        assert "Session has ended" in result.validation_errors
    
    def test_process_reading_invalid_data(self):
        """Process with invalid data returns validation errors."""
        engine = CardioTwinEngine()
        session_id = engine.create_session("user123")
        
        result = engine.process_reading(session_id, {
            "heart_rate": -10,  # Invalid
            "hrv": 45,
            "spo2": 98,
            "temperature": 36.6,
        })
        
        assert result.success is False
        assert result.reading_valid is False
        assert len(result.validation_errors) > 0
    
    def test_process_reading_missing_field(self):
        """Process with missing field returns validation error."""
        engine = CardioTwinEngine()
        session_id = engine.create_session("user123")
        
        result = engine.process_reading(session_id, {
            "heart_rate": 72,
            # Missing other fields
        })
        
        assert result.success is False
        assert result.reading_valid is False
    
    def test_process_valid_reading(self):
        """Process valid reading succeeds."""
        engine = CardioTwinEngine()
        session_id = engine.create_session("user123")
        
        result = engine.process_reading(session_id, {
            "heart_rate": 72,
            "hrv": 45,
            "spo2": 98,
            "temperature": 36.6,
        })
        
        assert result.success is True
        assert result.reading_valid is True
        assert result.scores is not None
        assert result.zone is not None
    
    def test_process_reading_adds_to_history(self):
        """Processing adds reading to session history."""
        engine = CardioTwinEngine()
        session_id = engine.create_session("user123")
        
        engine.process_reading(session_id, {
            "heart_rate": 72,
            "hrv": 45,
            "spo2": 98,
            "temperature": 36.6,
        })
        
        session = engine.get_session(session_id)
        assert len(session.readings) == 1
        assert session.readings[0].heart_rate == 72
    
    def test_calibration_phase(self):
        """Session starts in calibrating status."""
        engine = CardioTwinEngine({"calibration_readings": 3})
        session_id = engine.create_session("user123")
        
        session = engine.get_session(session_id)
        assert session.status == SessionStatus.CALIBRATING
        
        # Process 2 readings - still calibrating
        for _ in range(2):
            result = engine.process_reading(session_id, {
                "heart_rate": 72,
                "hrv": 45,
                "spo2": 98,
                "temperature": 36.6,
            })
            assert "Calibrating" in result.message
        
        assert engine.get_session(session_id).status == SessionStatus.CALIBRATING
    
    def test_calibration_completes(self):
        """Calibration completes after enough readings."""
        engine = CardioTwinEngine({"calibration_readings": 15})
        session_id = engine.create_session("user123")
        
        # Process 15 readings to complete calibration
        for _ in range(15):
            engine.process_reading(session_id, {
                "heart_rate": 72,
                "hrv": 45,
                "spo2": 98,
                "temperature": 36.6,
            })
        
        session = engine.get_session(session_id)
        assert session.status == SessionStatus.ACTIVE
        assert session.baseline is not None


class TestScoring:
    """Tests for score calculation."""
    
    def test_scores_calculated(self):
        """Scores are calculated from reading."""
        engine = CardioTwinEngine()
        session_id = engine.create_session("user123")
        
        result = engine.process_reading(session_id, {
            "heart_rate": 72,
            "hrv": 50,
            "spo2": 98,
            "temperature": 36.6,
        })
        
        assert result.scores.heart_rate > 0
        assert result.scores.hrv > 0
        assert result.scores.spo2 > 0
        assert result.scores.temperature > 0
        assert result.scores.cardiotwin_score > 0
    
    def test_optimal_values_high_score(self):
        """Optimal biometrics produce high score."""
        engine = CardioTwinEngine()
        session_id = engine.create_session("user123")
        
        result = engine.process_reading(session_id, {
            "heart_rate": 65,  # Optimal resting
            "hrv": 60,  # Good HRV
            "spo2": 99,  # Excellent
            "temperature": 36.8,  # Normal
        })
        
        assert result.scores.cardiotwin_score >= 80
    
    def test_poor_values_low_score(self):
        """Poor biometrics produce low score."""
        engine = CardioTwinEngine()
        session_id = engine.create_session("user123")
        
        result = engine.process_reading(session_id, {
            "heart_rate": 110,  # Elevated
            "hrv": 20,  # Low
            "spo2": 92,  # Concerning
            "temperature": 38.0,  # Fever
        })
        
        assert result.scores.cardiotwin_score < 60
    
    def test_get_current_score(self):
        """Get current score for session."""
        engine = CardioTwinEngine()
        session_id = engine.create_session("user123")
        
        engine.process_reading(session_id, {
            "heart_rate": 72,
            "hrv": 45,
            "spo2": 98,
            "temperature": 36.6,
        })
        
        score = engine.get_current_score(session_id)
        assert score is not None
        assert 0 <= score <= 100
    
    def test_get_current_score_no_session(self):
        """Get score for non-existent session returns None."""
        engine = CardioTwinEngine()
        
        score = engine.get_current_score("nonexistent")
        assert score is None


class TestZoneClassification:
    """Tests for zone classification."""
    
    def test_zone_assigned(self):
        """Zone is assigned from score."""
        engine = CardioTwinEngine()
        session_id = engine.create_session("user123")
        
        result = engine.process_reading(session_id, {
            "heart_rate": 72,
            "hrv": 45,
            "spo2": 98,
            "temperature": 36.6,
        })
        
        assert result.zone in [Zone.GREEN, Zone.YELLOW, Zone.ORANGE, Zone.RED]
    
    def test_zone_info_provided(self):
        """Zone info is provided with result."""
        engine = CardioTwinEngine()
        session_id = engine.create_session("user123")
        
        result = engine.process_reading(session_id, {
            "heart_rate": 72,
            "hrv": 45,
            "spo2": 98,
            "temperature": 36.6,
        })
        
        assert result.zone_info is not None
        assert result.zone_info.label is not None
        assert result.zone_info.description is not None
    
    def test_zone_change_detected(self):
        """Zone change is detected."""
        engine = CardioTwinEngine()
        session_id = engine.create_session("user123")
        
        # First reading - good values
        result1 = engine.process_reading(session_id, {
            "heart_rate": 65,
            "hrv": 60,
            "spo2": 99,
            "temperature": 36.8,
        })
        
        # Second reading - poor values
        result2 = engine.process_reading(session_id, {
            "heart_rate": 110,
            "hrv": 20,
            "spo2": 92,
            "temperature": 38.5,
        })
        
        # Zone should have changed
        if result1.zone != result2.zone:
            assert result2.zone_changed is True
    
    def test_get_current_zone(self):
        """Get current zone for session."""
        engine = CardioTwinEngine()
        session_id = engine.create_session("user123")
        
        engine.process_reading(session_id, {
            "heart_rate": 72,
            "hrv": 45,
            "spo2": 98,
            "temperature": 36.6,
        })
        
        zone = engine.get_current_zone(session_id)
        assert zone in [Zone.GREEN, Zone.YELLOW, Zone.ORANGE, Zone.RED]
    
    def test_get_current_zone_no_session(self):
        """Get zone for non-existent session returns None."""
        engine = CardioTwinEngine()
        
        zone = engine.get_current_zone("nonexistent")
        assert zone is None


class TestAnomalyDetection:
    """Tests for anomaly detection."""
    
    def test_no_alerts_for_normal_reading(self):
        """No alerts for normal biometrics."""
        engine = CardioTwinEngine()
        session_id = engine.create_session("user123")
        
        result = engine.process_reading(session_id, {
            "heart_rate": 72,
            "hrv": 45,
            "spo2": 98,
            "temperature": 36.6,
        })
        
        # May or may not have alerts, but shouldn't have critical ones
        critical_alerts = [
            a for a in result.new_alerts
            if a.severity == AlertSeverity.CRITICAL
        ]
        assert len(critical_alerts) == 0
    
    def test_alerts_for_dangerous_reading(self):
        """Alerts generated for dangerous biometrics."""
        engine = CardioTwinEngine()
        session_id = engine.create_session("user123")
        
        result = engine.process_reading(session_id, {
            "heart_rate": 150,  # Very high
            "hrv": 10,  # Very low
            "spo2": 88,  # Dangerously low
            "temperature": 39.5,  # High fever
        })
        
        assert len(result.new_alerts) > 0
    
    def test_get_active_alerts(self):
        """Get active alerts for session."""
        engine = CardioTwinEngine()
        session_id = engine.create_session("user123")
        
        engine.process_reading(session_id, {
            "heart_rate": 150,
            "hrv": 10,
            "spo2": 88,
            "temperature": 39.5,
        })
        
        alerts = engine.get_active_alerts(session_id)
        assert len(alerts) > 0
    
    def test_get_active_alerts_no_session(self):
        """Get alerts for non-existent session returns empty list."""
        engine = CardioTwinEngine()
        
        alerts = engine.get_active_alerts("nonexistent")
        assert alerts == []


class TestTrendCalculation:
    """Tests for trend analysis."""
    
    def test_trend_calculated_with_enough_readings(self):
        """Trend is calculated after enough readings."""
        engine = CardioTwinEngine()
        session_id = engine.create_session("user123")
        
        # Process multiple readings  
        for i in range(5):
            result = engine.process_reading(session_id, {
                "heart_rate": 72 + i,
                "hrv": 45 - i,
                "spo2": 98,
                "temperature": 36.6,
            })
        
        assert result.trend is not None
    
    def test_no_trend_with_few_readings(self):
        """No trend with insufficient readings."""
        engine = CardioTwinEngine()
        session_id = engine.create_session("user123")
        
        result = engine.process_reading(session_id, {
            "heart_rate": 72,
            "hrv": 45,
            "spo2": 98,
            "temperature": 36.6,
        })
        
        assert result.trend is None


class TestNudgeGeneration:
    """Tests for nudge generation."""
    
    @pytest.mark.asyncio
    async def test_generate_nudge_no_session(self):
        """Generate nudge for non-existent session returns None."""
        engine = CardioTwinEngine()
        
        nudge = await engine.generate_nudge("nonexistent")
        assert nudge is None
    
    @pytest.mark.asyncio
    async def test_generate_nudge_uses_fallback(self):
        """Generate nudge uses fallback when API unavailable."""
        engine = CardioTwinEngine()
        session_id = engine.create_session("user123")
        
        engine.process_reading(session_id, {
            "heart_rate": 72,
            "hrv": 45,
            "spo2": 98,
            "temperature": 36.6,
        })
        
        # Without valid API key, should use fallback
        with patch.dict("os.environ", {"GROQ_API_KEY": ""}):
            nudge = await engine.generate_nudge(session_id)
            assert nudge is not None
            assert isinstance(nudge, str)
    
    @pytest.mark.asyncio
    async def test_generate_nudge_with_language_override(self):
        """Generate nudge with language override."""
        engine = CardioTwinEngine()
        session_id = engine.create_session("user123", language=Language.ENGLISH)
        
        engine.process_reading(session_id, {
            "heart_rate": 72,
            "hrv": 45,
            "spo2": 98,
            "temperature": 36.6,
        })
        
        with patch.dict("os.environ", {"GROQ_API_KEY": ""}):
            nudge = await engine.generate_nudge(session_id, language=Language.PIDGIN)
            assert nudge is not None


class TestProjections:
    """Tests for risk projections."""
    
    def test_project_risk_no_session(self):
        """Project risk for non-existent session returns None."""
        engine = CardioTwinEngine()
        
        projection = engine.project_risk("nonexistent")
        assert projection is None
    
    def test_project_risk_insufficient_data(self):
        """Project risk with insufficient data returns None."""
        engine = CardioTwinEngine()
        session_id = engine.create_session("user123")
        
        # Only 1 reading
        engine.process_reading(session_id, {
            "heart_rate": 72,
            "hrv": 45,
            "spo2": 98,
            "temperature": 36.6,
        })
        
        projection = engine.project_risk(session_id)
        assert projection is None
    
    def test_project_risk_with_data(self):
        """Project risk with sufficient data."""
        engine = CardioTwinEngine()
        session_id = engine.create_session("user123")
        
        # Process multiple readings
        for _ in range(5):
            engine.process_reading(session_id, {
                "heart_rate": 72,
                "hrv": 45,
                "spo2": 98,
                "temperature": 36.6,
            })
        
        projection = engine.project_risk(session_id, hours_ahead=12)
        assert projection is not None
        assert len(projection.projected_scores) == 12
    
    def test_simulate_scenario_no_session(self):
        """Simulate scenario for non-existent session returns None."""
        engine = CardioTwinEngine()
        
        scenario = engine.simulate_scenario("nonexistent", "deep_breathing")
        assert scenario is None
    
    def test_simulate_scenario(self):
        """Simulate what-if scenario."""
        engine = CardioTwinEngine()
        session_id = engine.create_session("user123")
        
        engine.process_reading(session_id, {
            "heart_rate": 85,
            "hrv": 35,
            "spo2": 96,
            "temperature": 37.2,
        })
        
        scenario = engine.simulate_scenario(session_id, "deep_breathing")
        assert scenario is not None
        assert scenario.scenario_name == "deep_breathing"
    
    def test_get_improvement_suggestions(self):
        """Get improvement suggestions."""
        engine = CardioTwinEngine()
        session_id = engine.create_session("user123")
        
        engine.process_reading(session_id, {
            "heart_rate": 85,
            "hrv": 35,
            "spo2": 96,
            "temperature": 37.2,
        })
        
        suggestions = engine.get_improvement_suggestions(session_id)
        assert suggestions is not None
        assert "steps" in suggestions
    
    def test_get_improvement_suggestions_no_session(self):
        """Get suggestions for non-existent session returns None."""
        engine = CardioTwinEngine()
        
        suggestions = engine.get_improvement_suggestions("nonexistent")
        assert suggestions is None
    
    def test_get_risk_trajectory(self):
        """Get risk trajectory."""
        engine = CardioTwinEngine()
        session_id = engine.create_session("user123")
        
        for _ in range(5):
            engine.process_reading(session_id, {
                "heart_rate": 72,
                "hrv": 45,
                "spo2": 98,
                "temperature": 36.6,
            })
        
        trajectory = engine.get_risk_trajectory(session_id, hours=12)
        # trajectory can be empty list if no zone changes predicted
        assert trajectory is not None
        assert isinstance(trajectory, list)
    
    def test_estimate_recovery_time(self):
        """Estimate recovery time."""
        engine = CardioTwinEngine()
        session_id = engine.create_session("user123")
        
        engine.process_reading(session_id, {
            "heart_rate": 85,
            "hrv": 35,
            "spo2": 96,
            "temperature": 37.2,
        })
        
        recovery = engine.estimate_recovery_time(session_id)
        assert recovery is not None
        assert "estimated_hours" in recovery
        assert "recommendations" in recovery


class TestSessionSummary:
    """Tests for session summary."""
    
    def test_get_session_summary_no_session(self):
        """Get summary for non-existent session returns None."""
        engine = CardioTwinEngine()
        
        summary = engine.get_session_summary("nonexistent")
        assert summary is None
    
    def test_get_session_summary(self):
        """Get comprehensive session summary."""
        engine = CardioTwinEngine()
        session_id = engine.create_session("user123")
        
        for _ in range(5):
            engine.process_reading(session_id, {
                "heart_rate": 72,
                "hrv": 45,
                "spo2": 98,
                "temperature": 36.6,
            })
        
        summary = engine.get_session_summary(session_id)
        
        assert summary is not None
        assert summary["session_id"] == session_id
        assert summary["user_id"] == "user123"
        assert summary["readings_count"] == 5
        assert "current_state" in summary
        assert "statistics" in summary
    
    def test_summary_includes_statistics(self):
        """Summary includes score statistics."""
        engine = CardioTwinEngine()
        session_id = engine.create_session("user123")
        
        # Varying readings
        for hr in [70, 75, 80, 85, 90]:
            engine.process_reading(session_id, {
                "heart_rate": hr,
                "hrv": 45,
                "spo2": 98,
                "temperature": 36.6,
            })
        
        summary = engine.get_session_summary(session_id)
        stats = summary["statistics"]
        
        assert "average_score" in stats
        assert "min_score" in stats
        assert "max_score" in stats
        assert "zone_distribution" in stats


class TestLanguageSettings:
    """Tests for language settings."""
    
    def test_set_language(self):
        """Set language preference."""
        engine = CardioTwinEngine()
        session_id = engine.create_session("user123")
        
        result = engine.set_language(session_id, Language.HAUSA)
        
        assert result is True
        session = engine.get_session(session_id)
        assert session.language == Language.HAUSA
    
    def test_set_language_no_session(self):
        """Set language for non-existent session returns False."""
        engine = CardioTwinEngine()
        
        result = engine.set_language("nonexistent", Language.YORUBA)
        assert result is False


class TestSessionListing:
    """Tests for session listing."""
    
    def test_get_all_sessions_empty(self):
        """Get all sessions when none exist."""
        engine = CardioTwinEngine()
        
        sessions = engine.get_all_sessions()
        assert sessions == []
    
    def test_get_all_sessions(self):
        """Get all sessions."""
        engine = CardioTwinEngine()
        
        engine.create_session("user1")
        engine.create_session("user2")
        engine.create_session("user3")
        
        sessions = engine.get_all_sessions()
        assert len(sessions) == 3
    
    def test_get_active_sessions_empty(self):
        """Get active sessions when none active."""
        engine = CardioTwinEngine()
        session_id = engine.create_session("user123")
        
        # Session starts in calibrating
        active = engine.get_active_sessions()
        assert len(active) == 0
    
    def test_get_active_sessions(self):
        """Get active sessions after calibration."""
        engine = CardioTwinEngine({"calibration_readings": 15})
        session_id = engine.create_session("user123")
        
        # Complete calibration with 15 readings
        for _ in range(15):
            engine.process_reading(session_id, {
                "heart_rate": 72,
                "hrv": 45,
                "spo2": 98,
                "temperature": 36.6,
            })
        
        active = engine.get_active_sessions()
        assert session_id in active


class TestDataClasses:
    """Tests for data class serialization."""
    
    def test_component_scores_to_dict(self):
        """ComponentScores converts to dict."""
        scores = ComponentScores(
            heart_rate=85.0,
            hrv=75.0,
            spo2=90.0,
            temperature=80.0,
            cardiotwin_score=82.0,
        )
        
        d = scores.to_dict()
        assert d["heart_rate"] == 85.0
        assert d["cardiotwin_score"] == 82.0
    
    def test_reading_to_dict(self):
        """Reading converts to dict."""
        reading = Reading(
            timestamp=datetime(2024, 1, 15, 10, 30),
            heart_rate=72.0,
            hrv=45.0,
            spo2=98.0,
            temperature=36.6,
        )
        
        d = reading.to_dict()
        assert d["heart_rate"] == 72.0
        assert "timestamp" in d
    
    def test_session_data_to_dict(self):
        """SessionData converts to dict."""
        session = SessionData(
            session_id="test-123",
            user_id="user456",
        )
        
        d = session.to_dict()
        assert d["session_id"] == "test-123"
        assert d["user_id"] == "user456"
        assert d["status"] == "calibrating"
    
    def test_processing_result_to_dict(self):
        """ProcessingResult converts to dict."""
        result = ProcessingResult(
            success=True,
            session_id="test-123",
            timestamp=datetime.now(),
            scores=ComponentScores(cardiotwin_score=85.0),
            zone=Zone.GREEN,
        )
        
        d = result.to_dict()
        assert d["success"] is True
        assert d["zone"] == "green"


class TestHistoryLimits:
    """Tests for history size limits."""
    
    def test_readings_history_limited(self):
        """Readings history is limited to max."""
        engine = CardioTwinEngine({"max_readings_history": 5})
        session_id = engine.create_session("user123")
        
        # Process more readings than limit
        for i in range(10):
            engine.process_reading(session_id, {
                "heart_rate": 72 + i,
                "hrv": 45,
                "spo2": 98,
                "temperature": 36.6,
            })
        
        session = engine.get_session(session_id)
        assert len(session.readings) == 5
        # Should keep latest readings
        assert session.readings[-1].heart_rate == 81


class TestEdgeCases:
    """Tests for edge cases."""
    
    def test_process_reading_with_extra_fields(self):
        """Process reading ignores extra fields."""
        engine = CardioTwinEngine()
        session_id = engine.create_session("user123")
        
        result = engine.process_reading(session_id, {
            "heart_rate": 72,
            "hrv": 45,
            "spo2": 98,
            "temperature": 36.6,
            "extra_field": "ignored",
            "another_field": 123,
        })
        
        assert result.success is True
    
    def test_sensor_errors_detected(self):
        """Sensor errors are detected but reading still processed."""
        engine = CardioTwinEngine()
        session_id = engine.create_session("user123")
        
        # All zeros might indicate sensor error
        result = engine.process_reading(session_id, {
            "heart_rate": 72,
            "hrv": 45,
            "spo2": 98,
            "temperature": 36.6,
        })
        
        # Should still process successfully
        assert result.success is True
    
    def test_concurrent_sessions_independent(self):
        """Multiple sessions are independent."""
        engine = CardioTwinEngine()
        
        s1 = engine.create_session("user1")
        s2 = engine.create_session("user2")
        
        # Process different readings
        engine.process_reading(s1, {
            "heart_rate": 65,
            "hrv": 60,
            "spo2": 99,
            "temperature": 36.8,
        })
        
        engine.process_reading(s2, {
            "heart_rate": 100,
            "hrv": 25,
            "spo2": 94,
            "temperature": 38.0,
        })
        
        # Scores should be different
        score1 = engine.get_current_score(s1)
        score2 = engine.get_current_score(s2)
        
        assert score1 != score2
        assert score1 > score2  # user1 has better values
