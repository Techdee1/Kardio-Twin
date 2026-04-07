"""Tests for CardioTwin API facade response contracts."""

from datetime import datetime

from ai_engine.api import CardioTwinAPI
from ai_engine.engine import ProcessingResult


def test_process_reading_scored_has_action_summary_and_drivers():
    api = CardioTwinAPI({"calibration_readings": 1})
    session_id = "api-scored-contract"
    api.start_session(session_id)

    result = api.process_reading(
        {
            "session_id": session_id,
            "bpm": 72,
            "hrv": 45,
            "spo2": 98,
            "temperature": 36.6,
            "source": "manual",
        }
    )

    assert result["status"] == "scored"
    assert "action_summary" in result
    summary = result["action_summary"]

    assert summary["status"]
    assert summary["why"]
    assert summary["next_step"]
    assert summary["if_symptoms"]
    assert summary["advice_strength"] in {"retake_only", "cautious", "full"}
    assert summary["confidence_level"] in {"low", "medium", "high"}
    assert isinstance(summary["drivers"], list)
    assert len(summary["drivers"]) <= 2


def test_get_score_calibrating_has_action_summary():
    api = CardioTwinAPI({"calibration_readings": 5})
    session_id = "api-calibrating-contract"
    api.start_session(session_id)

    result = api.get_score(session_id)

    assert result["status"] == "calibrating"
    assert "action_summary" in result
    assert result["action_summary"]["status"] == "Calibrating"


def test_get_score_scored_has_action_summary():
    api = CardioTwinAPI({"calibration_readings": 1})
    session_id = "api-score-contract"
    api.start_session(session_id)

    api.process_reading(
        {
            "session_id": session_id,
            "bpm": 70,
            "hrv": 50,
            "spo2": 98,
            "temperature": 36.6,
            "source": "hardware",
        }
    )

    result = api.get_score(session_id)

    assert result["status"] == "scored"
    assert "action_summary" in result
    assert "signal_quality" in result
    assert "signal_confidence" in result
    assert isinstance(result.get("components"), dict)


def test_process_reading_retake_has_action_summary(monkeypatch):
    api = CardioTwinAPI({"calibration_readings": 1})
    session_id = "api-retake-contract"
    api.start_session(session_id)

    def fake_process_reading(_session_id, _reading):
        return ProcessingResult(
            success=True,
            session_id=session_id,
            timestamp=datetime.now(),
            signal_quality="poor",
            signal_confidence=0.35,
            retake_requested=True,
            retake_message="Please retake this reading.",
        )

    monkeypatch.setattr(api.engine, "process_reading", fake_process_reading)

    result = api.process_reading(
        {
            "session_id": session_id,
            "bpm": 72,
            "hrv": 45,
            "spo2": 98,
            "temperature": 36.6,
        }
    )

    assert result["status"] == "retake_requested"
    assert "action_summary" in result
    assert result["action_summary"]["status"] == "Retake needed"
    assert result["action_summary"]["advice_strength"] == "retake_only"
