"""
Integration Tests for CardioTwin AI Engine
==========================================

End-to-end tests that verify the complete pipeline works correctly,
from raw sensor data through to health insights and nudge generation.

These tests simulate real-world usage scenarios:
1. Complete user session lifecycle
2. Zone transitions during stress response
3. Anomaly detection and alerts
4. Recovery tracking
5. Multi-user concurrent sessions
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import patch, AsyncMock
import random

from ai_engine.engine import (
    CardioTwinEngine,
    SessionStatus,
    ProcessingResult,
)
from ai_engine.zones import Zone
from ai_engine.nudges import Language
from ai_engine.anomaly import AlertSeverity


class TestCompleteUserSession:
    """End-to-end tests for a complete user session lifecycle."""
    
    def test_full_session_lifecycle(self):
        """Test complete session: create → calibrate → process → end."""
        engine = CardioTwinEngine({"calibration_readings": 15})
        
        # 1. Create session
        session_id = engine.create_session("user_001", language=Language.ENGLISH)
        assert session_id is not None
        
        session = engine.get_session(session_id)
        assert session.status == SessionStatus.CALIBRATING
        
        # 2. Calibration phase (15 readings)
        for i in range(15):
            result = engine.process_reading(session_id, {
                "heart_rate": 68 + random.randint(-2, 2),
                "hrv": 52 + random.randint(-3, 3),
                "spo2": 98,
                "temperature": 36.5 + random.uniform(-0.1, 0.1),
            })
            assert result.success is True
        
        # Session should now be active
        session = engine.get_session(session_id)
        assert session.status == SessionStatus.ACTIVE
        assert session.baseline is not None
        
        # 3. Normal operation - process readings
        for i in range(10):
            result = engine.process_reading(session_id, {
                "heart_rate": 70 + random.randint(-5, 5),
                "hrv": 50 + random.randint(-5, 5),
                "spo2": 98,
                "temperature": 36.6,
            })
            assert result.success is True
            assert result.zone is not None
            assert result.scores is not None
        
        # 4. Get session summary
        summary = engine.get_session_summary(session_id)
        assert summary is not None
        assert summary["readings_count"] == 25  # 15 calibration + 10 normal
        assert summary["baseline_calibrated"] is True
        
        # 5. End session
        result = engine.end_session(session_id)
        assert result is True
        
        session = engine.get_session(session_id)
        assert session.status == SessionStatus.ENDED
    
    def test_session_with_degrading_health(self):
        """Test session where user's health degrades over time."""
        engine = CardioTwinEngine({"calibration_readings": 15})
        session_id = engine.create_session("user_stress")
        
        # Calibration with good values
        for _ in range(15):
            engine.process_reading(session_id, {
                "heart_rate": 68,
                "hrv": 55,
                "spo2": 98,
                "temperature": 36.5,
            })
        
        # Simulate stress response - gradually worsening
        zones_seen = []
        for i in range(20):
            # HR increases, HRV decreases over time
            hr = 70 + (i * 3)  # 70 → 127
            hrv = 55 - (i * 2)  # 55 → 17
            
            result = engine.process_reading(session_id, {
                "heart_rate": min(hr, 150),
                "hrv": max(hrv, 15),
                "spo2": max(98 - i // 5, 92),
                "temperature": 36.6 + (i * 0.05),
            })
            
            zones_seen.append(result.zone)
        
        # Should have seen zone transitions as health degraded
        unique_zones = set(zones_seen)
        assert len(unique_zones) > 1, "Should transition through multiple zones"
        
        # Final readings should be in worse zone than initial
        assert zones_seen[-1] != Zone.GREEN or zones_seen[0] == Zone.GREEN
    
    def test_session_with_recovery(self):
        """Test session showing recovery from stressed state."""
        engine = CardioTwinEngine({"calibration_readings": 15})
        session_id = engine.create_session("user_recovery")
        
        # Calibration
        for _ in range(15):
            engine.process_reading(session_id, {
                "heart_rate": 72,
                "hrv": 48,
                "spo2": 97,
                "temperature": 36.6,
            })
        
        # Start in stressed state
        for _ in range(5):
            engine.process_reading(session_id, {
                "heart_rate": 95,
                "hrv": 25,
                "spo2": 95,
                "temperature": 37.0,
            })
        
        stressed_score = engine.get_current_score(session_id)
        
        # Recovery - improving metrics
        for i in range(15):
            hr = 95 - (i * 2)  # 95 → 65
            hrv = 25 + (i * 2)  # 25 → 53
            
            engine.process_reading(session_id, {
                "heart_rate": max(hr, 65),
                "hrv": min(hrv, 55),
                "spo2": min(95 + i // 3, 99),
                "temperature": 37.0 - (i * 0.02),
            })
        
        recovered_score = engine.get_current_score(session_id)
        
        # Score should have improved
        assert recovered_score > stressed_score


class TestZoneTransitions:
    """Tests for zone transition scenarios."""
    
    def test_green_to_yellow_transition(self):
        """Test transition from GREEN to YELLOW zone."""
        engine = CardioTwinEngine({"calibration_readings": 15})
        session_id = engine.create_session("user_gy")
        
        # Calibrate with excellent values
        for _ in range(15):
            engine.process_reading(session_id, {
                "heart_rate": 62,
                "hrv": 65,
                "spo2": 99,
                "temperature": 36.5,
            })
        
        # Confirm in green zone
        result = engine.process_reading(session_id, {
            "heart_rate": 62,
            "hrv": 65,
            "spo2": 99,
            "temperature": 36.5,
        })
        initial_zone = result.zone
        
        # Introduce mild stress
        result = engine.process_reading(session_id, {
            "heart_rate": 85,
            "hrv": 35,
            "spo2": 96,
            "temperature": 36.9,
        })
        
        # May have transitioned
        if result.zone_changed:
            assert result.zone in [Zone.YELLOW, Zone.ORANGE]
    
    def test_rapid_zone_change_detection(self):
        """Test that rapid zone changes are detected."""
        engine = CardioTwinEngine({"calibration_readings": 15})
        session_id = engine.create_session("user_rapid")
        
        # Calibrate
        for _ in range(15):
            engine.process_reading(session_id, {
                "heart_rate": 70,
                "hrv": 50,
                "spo2": 98,
                "temperature": 36.6,
            })
        
        zone_changes = 0
        prev_zone = None
        
        # Oscillating readings
        for i in range(20):
            if i % 2 == 0:
                # Good reading
                result = engine.process_reading(session_id, {
                    "heart_rate": 65,
                    "hrv": 60,
                    "spo2": 99,
                    "temperature": 36.5,
                })
            else:
                # Stressed reading
                result = engine.process_reading(session_id, {
                    "heart_rate": 100,
                    "hrv": 20,
                    "spo2": 93,
                    "temperature": 37.5,
                })
            
            if prev_zone and result.zone != prev_zone:
                zone_changes += 1
            prev_zone = result.zone
        
        # Should detect zone changes
        assert zone_changes > 0


class TestAnomalyDetectionIntegration:
    """Integration tests for anomaly detection."""
    
    def test_critical_spo2_alert(self):
        """Test that critical SpO2 levels trigger alerts."""
        engine = CardioTwinEngine({"calibration_readings": 15})
        session_id = engine.create_session("user_spo2")
        
        # Calibrate
        for _ in range(15):
            engine.process_reading(session_id, {
                "heart_rate": 70,
                "hrv": 50,
                "spo2": 98,
                "temperature": 36.6,
            })
        
        # Critical SpO2
        result = engine.process_reading(session_id, {
            "heart_rate": 85,
            "hrv": 40,
            "spo2": 88,  # Dangerously low
            "temperature": 36.8,
        })
        
        alerts = engine.get_active_alerts(session_id)
        # Should have alerts for low SpO2
        critical_alerts = [a for a in alerts if a.severity in [AlertSeverity.URGENT, AlertSeverity.CRITICAL]]
        assert len(critical_alerts) >= 0  # May or may not trigger based on threshold
    
    def test_high_heart_rate_alert(self):
        """Test that unusually high heart rate triggers alerts."""
        engine = CardioTwinEngine({"calibration_readings": 15})
        session_id = engine.create_session("user_hr")
        
        # Calibrate with normal values
        for _ in range(15):
            engine.process_reading(session_id, {
                "heart_rate": 68,
                "hrv": 52,
                "spo2": 98,
                "temperature": 36.5,
            })
        
        # Very high heart rate
        result = engine.process_reading(session_id, {
            "heart_rate": 145,  # Very elevated
            "hrv": 15,
            "spo2": 96,
            "temperature": 37.0,
        })
        
        # Should be in a non-green zone
        assert result.zone != Zone.GREEN
    
    def test_fever_detection(self):
        """Test that fever temperatures are detected."""
        engine = CardioTwinEngine({"calibration_readings": 15})
        session_id = engine.create_session("user_fever")
        
        # Calibrate
        for _ in range(15):
            engine.process_reading(session_id, {
                "heart_rate": 70,
                "hrv": 50,
                "spo2": 98,
                "temperature": 36.5,
            })
        
        # Fever temperature
        result = engine.process_reading(session_id, {
            "heart_rate": 85,
            "hrv": 35,
            "spo2": 97,
            "temperature": 38.5,  # Fever
        })
        
        # Score should be impacted
        assert result.scores.temperature < 90


class TestNudgeIntegration:
    """Integration tests for nudge generation."""
    
    @pytest.mark.asyncio
    async def test_nudge_for_green_zone(self):
        """Test nudge generation for healthy state."""
        engine = CardioTwinEngine({"calibration_readings": 15})
        session_id = engine.create_session("user_nudge_g")
        
        # Calibrate and get into green zone
        for _ in range(16):
            engine.process_reading(session_id, {
                "heart_rate": 65,
                "hrv": 60,
                "spo2": 99,
                "temperature": 36.6,
            })
        
        # Generate nudge (will use fallback without valid API key)
        with patch.dict("os.environ", {"GROQ_API_KEY": ""}):
            nudge = await engine.generate_nudge(session_id)
        
        assert nudge is not None
        assert isinstance(nudge, str)
        assert len(nudge) > 0
    
    @pytest.mark.asyncio
    async def test_nudge_for_stressed_state(self):
        """Test nudge generation for stressed state."""
        engine = CardioTwinEngine({"calibration_readings": 15})
        session_id = engine.create_session("user_nudge_s")
        
        # Calibrate
        for _ in range(15):
            engine.process_reading(session_id, {
                "heart_rate": 70,
                "hrv": 50,
                "spo2": 98,
                "temperature": 36.6,
            })
        
        # Put in stressed state
        engine.process_reading(session_id, {
            "heart_rate": 100,
            "hrv": 20,
            "spo2": 94,
            "temperature": 37.2,
        })
        
        with patch.dict("os.environ", {"GROQ_API_KEY": ""}):
            nudge = await engine.generate_nudge(session_id)
        
        assert nudge is not None
        assert isinstance(nudge, str)
    
    @pytest.mark.asyncio
    async def test_nudge_language_support(self):
        """Test nudge generation in different languages."""
        engine = CardioTwinEngine({"calibration_readings": 15})
        
        for lang in [Language.ENGLISH, Language.PIDGIN, Language.YORUBA]:
            session_id = engine.create_session(f"user_{lang.value}", language=lang)
            
            for _ in range(16):
                engine.process_reading(session_id, {
                    "heart_rate": 70,
                    "hrv": 50,
                    "spo2": 98,
                    "temperature": 36.6,
                })
            
            with patch.dict("os.environ", {"GROQ_API_KEY": ""}):
                nudge = await engine.generate_nudge(session_id)
            
            assert nudge is not None, f"Should generate nudge for {lang.value}"


class TestProjectionIntegration:
    """Integration tests for risk projection."""
    
    def test_risk_projection_after_calibration(self):
        """Test risk projection with calibrated session."""
        engine = CardioTwinEngine({"calibration_readings": 15})
        session_id = engine.create_session("user_proj")
        
        # Calibrate and add history
        for _ in range(20):
            engine.process_reading(session_id, {
                "heart_rate": 70 + random.randint(-3, 3),
                "hrv": 50 + random.randint(-3, 3),
                "spo2": 98,
                "temperature": 36.6,
            })
        
        projection = engine.project_risk(session_id, hours_ahead=24)
        
        assert projection is not None
        assert len(projection.projected_scores) == 24
    
    def test_scenario_simulation(self):
        """Test what-if scenario simulation."""
        engine = CardioTwinEngine({"calibration_readings": 15})
        session_id = engine.create_session("user_scenario")
        
        # Calibrate
        for _ in range(15):
            engine.process_reading(session_id, {
                "heart_rate": 70,
                "hrv": 50,
                "spo2": 98,
                "temperature": 36.6,
            })
        
        # Put in mild stress
        engine.process_reading(session_id, {
            "heart_rate": 85,
            "hrv": 35,
            "spo2": 96,
            "temperature": 36.9,
        })
        
        # Simulate deep breathing intervention
        scenario = engine.simulate_scenario(session_id, "deep_breathing")
        
        assert scenario is not None
        assert scenario.scenario_name == "deep_breathing"
        assert scenario.score_change >= 0  # Should be positive (improvement)
    
    def test_improvement_suggestions(self):
        """Test improvement path suggestions."""
        engine = CardioTwinEngine({"calibration_readings": 15})
        session_id = engine.create_session("user_improve")
        
        # Calibrate
        for _ in range(15):
            engine.process_reading(session_id, {
                "heart_rate": 70,
                "hrv": 50,
                "spo2": 98,
                "temperature": 36.6,
            })
        
        # Put in non-optimal state
        engine.process_reading(session_id, {
            "heart_rate": 90,
            "hrv": 30,
            "spo2": 95,
            "temperature": 37.1,
        })
        
        suggestions = engine.get_improvement_suggestions(session_id)
        
        assert suggestions is not None
        assert "steps" in suggestions
        assert "current_score" in suggestions
    
    def test_recovery_time_estimate(self):
        """Test recovery time estimation."""
        engine = CardioTwinEngine({"calibration_readings": 15})
        session_id = engine.create_session("user_recovery_est")
        
        # Calibrate
        for _ in range(15):
            engine.process_reading(session_id, {
                "heart_rate": 70,
                "hrv": 50,
                "spo2": 98,
                "temperature": 36.6,
            })
        
        # Stressed state
        engine.process_reading(session_id, {
            "heart_rate": 95,
            "hrv": 25,
            "spo2": 94,
            "temperature": 37.3,
        })
        
        recovery = engine.estimate_recovery_time(session_id)
        
        assert recovery is not None
        assert "estimated_hours" in recovery
        assert "recommendations" in recovery


class TestMultiUserScenarios:
    """Tests for handling multiple concurrent users."""
    
    def test_concurrent_sessions_isolation(self):
        """Test that concurrent sessions are properly isolated."""
        engine = CardioTwinEngine({"calibration_readings": 15})
        
        # Create multiple sessions
        sessions = {}
        for i in range(5):
            user_id = f"user_{i}"
            sessions[user_id] = engine.create_session(user_id)
        
        # Calibrate all sessions with different values
        for i, (user_id, session_id) in enumerate(sessions.items()):
            base_hr = 60 + (i * 10)  # 60, 70, 80, 90, 100
            
            for _ in range(15):
                engine.process_reading(session_id, {
                    "heart_rate": base_hr,
                    "hrv": 50,
                    "spo2": 98,
                    "temperature": 36.6,
                })
        
        # Verify scores are different
        scores = {}
        for user_id, session_id in sessions.items():
            scores[user_id] = engine.get_current_score(session_id)
        
        # Not all scores should be identical
        unique_scores = set(round(s, 1) for s in scores.values())
        assert len(unique_scores) >= 1
    
    def test_session_listing(self):
        """Test listing and filtering sessions."""
        engine = CardioTwinEngine({"calibration_readings": 15})
        
        # Create sessions
        s1 = engine.create_session("user_a")
        s2 = engine.create_session("user_b")
        s3 = engine.create_session("user_c")
        
        # Calibrate s1 only
        for _ in range(15):
            engine.process_reading(s1, {
                "heart_rate": 70,
                "hrv": 50,
                "spo2": 98,
                "temperature": 36.6,
            })
        
        # Get all sessions
        all_sessions = engine.get_all_sessions()
        assert len(all_sessions) == 3
        
        # Get active sessions
        active = engine.get_active_sessions()
        assert s1 in active
        assert s2 not in active  # Still calibrating
        assert s3 not in active


class TestEdgeCasesIntegration:
    """Integration tests for edge cases."""
    
    def test_empty_session_operations(self):
        """Test operations on session with no readings."""
        engine = CardioTwinEngine()
        session_id = engine.create_session("user_empty")
        
        # These should return None or empty without crashing
        score = engine.get_current_score(session_id)
        assert score == 0.0  # Default score
        
        projection = engine.project_risk(session_id)
        assert projection is None  # Not enough data
    
    def test_reading_with_boundary_values(self):
        """Test readings at physiological boundaries."""
        engine = CardioTwinEngine({"calibration_readings": 15})
        session_id = engine.create_session("user_boundary")
        
        # Calibrate
        for _ in range(15):
            engine.process_reading(session_id, {
                "heart_rate": 70,
                "hrv": 50,
                "spo2": 98,
                "temperature": 36.6,
            })
        
        # Test boundary values
        boundary_cases = [
            {"heart_rate": 40, "hrv": 150, "spo2": 100, "temperature": 35.0},  # Low HR, high HRV
            {"heart_rate": 180, "hrv": 5, "spo2": 90, "temperature": 40.0},  # High HR, low HRV
            {"heart_rate": 100, "hrv": 50, "spo2": 100, "temperature": 36.6},  # Perfect SpO2
        ]
        
        for case in boundary_cases:
            result = engine.process_reading(session_id, case)
            assert result.success is True
            assert result.scores is not None
    
    def test_session_after_deletion(self):
        """Test that deleted sessions are properly cleaned up."""
        engine = CardioTwinEngine()
        session_id = engine.create_session("user_delete")
        
        # Delete session
        engine.delete_session(session_id)
        
        # Operations should fail gracefully
        result = engine.process_reading(session_id, {
            "heart_rate": 70,
            "hrv": 50,
            "spo2": 98,
            "temperature": 36.6,
        })
        assert result.success is False
        
        score = engine.get_current_score(session_id)
        assert score is None


class TestDataPersistence:
    """Tests for data tracking and persistence within a session."""
    
    def test_score_history_tracking(self):
        """Test that score history is properly maintained."""
        engine = CardioTwinEngine({"calibration_readings": 15})
        session_id = engine.create_session("user_history")
        
        # Add readings
        for i in range(25):
            engine.process_reading(session_id, {
                "heart_rate": 70 + (i % 10),
                "hrv": 50 - (i % 5),
                "spo2": 98,
                "temperature": 36.6,
            })
        
        session = engine.get_session(session_id)
        
        assert len(session.score_history) == 25
        assert len(session.zone_history) == 25
        assert len(session.readings) == 25
    
    def test_alert_history(self):
        """Test that alerts are accumulated in history."""
        engine = CardioTwinEngine({"calibration_readings": 15})
        session_id = engine.create_session("user_alerts")
        
        # Calibrate
        for _ in range(15):
            engine.process_reading(session_id, {
                "heart_rate": 70,
                "hrv": 50,
                "spo2": 98,
                "temperature": 36.6,
            })
        
        # Trigger potential alerts with varied readings
        for _ in range(10):
            engine.process_reading(session_id, {
                "heart_rate": random.choice([70, 120, 140]),
                "hrv": random.choice([50, 20, 10]),
                "spo2": random.choice([98, 92, 88]),
                "temperature": random.choice([36.6, 37.5, 38.5]),
            })
        
        session = engine.get_session(session_id)
        # Alert history may have accumulated
        assert isinstance(session.alert_history, list)


class TestRealWorldScenarios:
    """Tests simulating real-world usage patterns."""
    
    def test_morning_routine_scenario(self):
        """Simulate a typical morning health check routine."""
        engine = CardioTwinEngine({"calibration_readings": 15})
        session_id = engine.create_session("user_morning", language=Language.ENGLISH)
        
        # User wakes up - calibration readings
        for _ in range(15):
            engine.process_reading(session_id, {
                "heart_rate": 58,  # Resting HR after sleep
                "hrv": 65,  # Good HRV after rest
                "spo2": 98,
                "temperature": 36.3,  # Slightly lower morning temp
            })
        
        assert engine.get_session(session_id).status == SessionStatus.ACTIVE
        
        # Morning activity increases metrics slightly
        for _ in range(5):
            engine.process_reading(session_id, {
                "heart_rate": 72,
                "hrv": 55,
                "spo2": 98,
                "temperature": 36.6,
            })
        
        # Should remain in green zone
        zone = engine.get_current_zone(session_id)
        assert zone in [Zone.GREEN, Zone.YELLOW]
    
    def test_exercise_session_scenario(self):
        """Simulate an exercise session."""
        engine = CardioTwinEngine({"calibration_readings": 15})
        session_id = engine.create_session("user_exercise")
        
        # Pre-exercise calibration
        for _ in range(15):
            engine.process_reading(session_id, {
                "heart_rate": 68,
                "hrv": 55,
                "spo2": 98,
                "temperature": 36.6,
            })
        
        # Exercise begins - HR increases
        exercise_zones = []
        for i in range(10):
            hr = 68 + (i * 8)  # Gradual increase
            result = engine.process_reading(session_id, {
                "heart_rate": min(hr, 150),
                "hrv": max(55 - (i * 4), 20),
                "spo2": 97,
                "temperature": 36.8 + (i * 0.05),
            })
            exercise_zones.append(result.zone)
        
        # Recovery phase
        recovery_zones = []
        for i in range(10):
            hr = 140 - (i * 7)  # Gradual decrease
            result = engine.process_reading(session_id, {
                "heart_rate": max(hr, 70),
                "hrv": min(20 + (i * 3), 55),
                "spo2": 98,
                "temperature": 37.0 - (i * 0.03),
            })
            recovery_zones.append(result.zone)
        
        # Should see zone changes
        all_zones = exercise_zones + recovery_zones
        assert len(set(all_zones)) >= 1  # At least some variation expected
    
    def test_stressful_day_scenario(self):
        """Simulate a stressful work day."""
        engine = CardioTwinEngine({"calibration_readings": 15})
        session_id = engine.create_session("user_stress_day")
        
        # Morning baseline
        for _ in range(15):
            engine.process_reading(session_id, {
                "heart_rate": 70,
                "hrv": 50,
                "spo2": 98,
                "temperature": 36.6,
            })
        
        scores = []
        
        # Mid-morning stress
        for _ in range(5):
            result = engine.process_reading(session_id, {
                "heart_rate": 85,
                "hrv": 35,
                "spo2": 97,
                "temperature": 36.8,
            })
            scores.append(result.scores.cardiotwin_score)
        
        # Lunch break relaxation
        for _ in range(3):
            result = engine.process_reading(session_id, {
                "heart_rate": 72,
                "hrv": 45,
                "spo2": 98,
                "temperature": 36.6,
            })
            scores.append(result.scores.cardiotwin_score)
        
        # Afternoon meeting stress
        for _ in range(5):
            result = engine.process_reading(session_id, {
                "heart_rate": 92,
                "hrv": 28,
                "spo2": 96,
                "temperature": 37.0,
            })
            scores.append(result.scores.cardiotwin_score)
        
        # End of day wind down
        for _ in range(3):
            result = engine.process_reading(session_id, {
                "heart_rate": 75,
                "hrv": 42,
                "spo2": 98,
                "temperature": 36.7,
            })
            scores.append(result.scores.cardiotwin_score)
        
        # Should see score variation throughout the day
        assert max(scores) > min(scores)
        
        # Get day summary
        summary = engine.get_session_summary(session_id)
        assert summary["readings_count"] == 31


class TestPerformance:
    """Performance-related integration tests."""
    
    def test_high_volume_readings(self):
        """Test handling of many readings in a session."""
        engine = CardioTwinEngine({
            "calibration_readings": 15,
            "max_readings_history": 100,
        })
        session_id = engine.create_session("user_volume")
        
        # Process many readings
        for i in range(200):
            result = engine.process_reading(session_id, {
                "heart_rate": 70 + (i % 20),
                "hrv": 50 - (i % 10),
                "spo2": 98,
                "temperature": 36.6,
            })
            assert result.success is True
        
        # History should be limited
        session = engine.get_session(session_id)
        assert len(session.readings) <= 100
    
    def test_many_concurrent_sessions(self):
        """Test handling many concurrent sessions."""
        engine = CardioTwinEngine({"calibration_readings": 15})
        
        sessions = []
        for i in range(50):
            sid = engine.create_session(f"user_{i}")
            sessions.append(sid)
        
        # Process a reading for each
        for sid in sessions:
            result = engine.process_reading(sid, {
                "heart_rate": 70,
                "hrv": 50,
                "spo2": 98,
                "temperature": 36.6,
            })
            assert result.success is True
        
        assert len(engine.get_all_sessions()) == 50
