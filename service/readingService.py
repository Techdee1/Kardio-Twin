from fastapi import HTTPException, status
from model import dataModel
from dtos import readingsDto
from config import settings
from typing import Dict, Any

CALIBRATION_THRESHOLD = settings.CALIBRATION_THRESHOLD

ZONE_THRESHOLDS = [
    (80, "GREEN", "Thriving", "🟢"),
    (55, "YELLOW", "Mild Strain", "🟡"),
    (30, "ORANGE", "Elevated Risk", "🟠"),
    (0, "RED", "Critical Strain", "🔴"),
]

# PRD-specified weights
COMPONENT_WEIGHTS = {'heart_rate': 0.25, 'hrv': 0.40, 'spo2': 0.20, 'temperature': 0.15}


def store_reading(data: readingsDto.BiometricReadingRequest, ai_result: Dict[str, Any], db):
    """
    Store biometric reading with AI Engine results in database.
    
    Args:
        data: Raw biometric data from ESP32
        ai_result: Processed result from CardioTwinAPI
        db: Database session
    """
    try:
        biometric_reading = dataModel.BiometricReading(
            bpm=data.bpm,
            hrv=data.hrv,
            spo2=data.spo2,
            temperature=data.temperature,
            timestamp=data.timestamp,
            session_id=data.session_id,
            score=ai_result.get("score"),
            zone=ai_result.get("zone"),
            alert=ai_result.get("alert", False),
        )
        db.add(biometric_reading)
        db.commit()
        db.refresh(biometric_reading)
        return biometric_reading
    except Exception as e:
        db.rollback()
        print(f"Error storing reading: {e}")
        return None


def process_reading(data: readingsDto.BiometricReadingRequest, db):
    """
    Legacy process_reading - kept for backwards compatibility.
    New code should use AI Engine via readingRouter.
    """
    biometric_reading = dataModel.BiometricReading(
        bpm=data.bpm,
        hrv=data.hrv,
        spo2=data.spo2,
        temperature=data.temperature,
        timestamp=data.timestamp,
        session_id=data.session_id,
    )
    db.add(biometric_reading)
    db.commit()
    db.refresh(biometric_reading)
    
    readings_collected = get_session_readings_count(data.session_id, db)
    
    if readings_collected < CALIBRATION_THRESHOLD:
        return readingsDto.CalibratingReadingResponse(
            status="calibrating",
            readings_collected=readings_collected,
            readings_needed=CALIBRATION_THRESHOLD,
            alert=False
        )
    
    # Use simple scoring if components not provided
    if data.components:
        overall_score = calculate_overall_score(data.components)
    else:
        overall_score = 75.0  # Default score
    
    zone, zone_label, zone_emoji = get_zone_info(overall_score)
    
    return {
        "status": "scored",
        "score": round(overall_score, 1),
        "zone": zone,
        "zone_label": zone_label,
        "zone_emoji": zone_emoji,
        "alert": overall_score < 30,
        "nudge_sent": False,
    }


def get_latest_score(session_id: str, db) -> Dict[str, Any]:
    """Returns the latest score for a session from database."""
    reading = (
        db.query(dataModel.BiometricReading)
        .filter(dataModel.BiometricReading.session_id == session_id)
        .order_by(dataModel.BiometricReading.id.desc())
        .first()
    )
    
    if not reading:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="No readings found for this session"
        )
    
    score = reading.score or 75.0
    zone, zone_label, zone_emoji = get_zone_info(score)
    
    return {
        "status": "scored",
        "score": round(score, 1),
        "zone": zone,
        "zone_label": zone_label,
        "zone_emoji": zone_emoji,
    }


def get_session_readings_count(session_id: str, db) -> int:
    """Returns the count of readings for a specific session."""
    return db.query(dataModel.BiometricReading).filter(
        dataModel.BiometricReading.session_id == session_id
    ).count()


def calculate_overall_score(components: readingsDto.ComponentsData) -> float:
    """Weighted composite score from individual components."""
    return (
        components.heart_rate.score * COMPONENT_WEIGHTS['heart_rate'] +
        components.hrv.score * COMPONENT_WEIGHTS['hrv'] +
        components.spo2.score * COMPONENT_WEIGHTS['spo2'] +
        components.temperature.score * COMPONENT_WEIGHTS['temperature']
    )


def get_zone_info(score: float) -> tuple:
    """Return zone, label, and emoji based on score."""
    for threshold, zone, label, emoji in ZONE_THRESHOLDS:
        if score >= threshold:
            return zone, label, emoji


def get_all_scores(session_id: str, db):
    """Returns all readings for chart rendering."""
    readings = (
        db.query(dataModel.BiometricReading)
        .filter(dataModel.BiometricReading.session_id == session_id)
        .order_by(dataModel.BiometricReading.id.asc())
        .all()
    )

    if not readings:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No readings found for this session")

    if len(readings) < CALIBRATION_THRESHOLD:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Still calibrating. {len(readings)}/{CALIBRATION_THRESHOLD} readings collected.")

    return [
        {
            "timestamp": r.timestamp,
            "bpm": r.bpm,
            "hrv": r.hrv,
            "spo2": r.spo2,
            "temperature": r.temperature
        }
        for r in readings
    ]


