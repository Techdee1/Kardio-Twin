"""
CardioTwin Reading Router - Integrates AI Engine with Backend
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from dtos import readingsDto
from service import readingService, sessionService
from repository.database import get_db
from dotenv import load_dotenv
import os
import time
from ai_engine.api import CardioTwinAPI
from ai_engine.safety import should_alert_caregiver, get_caregiver_message, EscalationLevel, DISCLAIMERS

load_dotenv()

# Load Twilio credentials
ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
SMS_NUMBER = os.getenv("TWILIO_SMS_NUMBER")
WHATSAPP_NUMBER = os.getenv("TWILIO_WHATSAPP_NUMBER")

# Initialize Twilio client (only if credentials are set)
twilio_client = None
try:
    if ACCOUNT_SID and AUTH_TOKEN:
        from twilio.rest import Client
        twilio_client = Client(ACCOUNT_SID, AUTH_TOKEN)
except Exception as e:
    print(f"Twilio not configured: {e}")

# Initialize AI Engine
ai = CardioTwinAPI()

router = APIRouter(
    prefix="/api",
    tags=["Reading"]
)


def send_whatsapp_alert(phone: str, message: str) -> bool:
    """Send WhatsApp alert via Twilio."""
    if not twilio_client or not WHATSAPP_NUMBER:
        print(f"[TWILIO STUB] Would send to {phone}: {message[:50]}...")
        return False
    
    try:
        msg = twilio_client.messages.create(
            body=message,
            from_=WHATSAPP_NUMBER,
            to=f"whatsapp:{phone}"
        )
        print(f"WhatsApp sent: {msg.sid}")
        return True
    except Exception as e:
        print(f"WhatsApp failed: {e}")
        return False


def send_sms_alert(phone: str, message: str) -> bool:
    """Send SMS alert via Twilio."""
    if not twilio_client or not SMS_NUMBER:
        print(f"[SMS STUB] Would send to {phone}: {message[:50]}...")
        return False
    
    try:
        msg = twilio_client.messages.create(
            body=message,
            from_=SMS_NUMBER,
            to=phone
        )
        print(f"SMS sent: {msg.sid}")
        return True
    except Exception as e:
        print(f"SMS failed: {e}")
        return False


@router.post("/reading")
def receive_biometric_reading(
    data: readingsDto.BiometricReadingRequest,
    db: Session = Depends(get_db)
):
    """
    Receives biometric reading from ESP32. Called every 2 seconds.
    
    Uses AI Engine for:
    - Baseline calibration (first 15 readings)
    - CardioTwin Score calculation
    - Zone classification
    - Anomaly detection
    - Alert triggers
    
    Returns calibrating response until 15 readings collected,
    then returns scored response with AI-powered insights.
    """
    session_id = data.session_id
    db_session = sessionService.fetch_session(session_id, db)

    # Ensure AI session exists
    session = ai.engine.get_session(session_id)
    if not session:
        phone = db_session.user_phone if db_session else None
        caregiver_phone = db_session.caregiver_phone if db_session else None
        caregiver_name = db_session.caregiver_name if db_session else None
        med_phone = db_session.medical_professional_phone if db_session else None
        med_name = db_session.medical_professional_name if db_session else None
        ai.start_session(
            session_id,
            user_phone=phone,
            caregiver_phone=caregiver_phone,
            caregiver_name=caregiver_name,
            medical_professional_phone=med_phone,
            medical_professional_name=med_name,
        )

    # Process through AI Engine
    result = ai.process_reading({
        "bpm": data.bpm,
        "hrv": data.hrv,
        "spo2": data.spo2,
        "temperature": data.temperature,
        "session_id": session_id,
        "source": getattr(data, "source", "hardware"),
    })

    # Store reading in database
    readingService.store_reading(data, result, db)

    # Send WhatsApp alert to user if nudge triggered
    if result.get("nudge_sent") and db_session and db_session.user_phone:
        nudge = ai.get_nudge_message(session_id)
        send_whatsapp_alert(db_session.user_phone, nudge["message"])

    # Alert caregiver if safety escalation warrants it
    safety = result.get("safety", {})
    if safety and db_session:
        escalation_str = safety.get("escalation", "none") if isinstance(safety, dict) else "none"
        try:
            escalation = EscalationLevel(escalation_str)
        except ValueError:
            escalation = EscalationLevel.NONE

        zone = result.get("zone", "GREEN")
        if should_alert_caregiver(escalation, zone):
            score = result.get("score", 0)
            red_flags = safety.get("red_flags", []) if isinstance(safety, dict) else []
            # Alert caregiver
            if db_session.caregiver_phone:
                cg_msg = get_caregiver_message(zone, score, red_flags, escalation, db_session.caregiver_name or "Your contact")
                send_whatsapp_alert(db_session.caregiver_phone, cg_msg)
            # Alert medical professional for SEEK_HELP or EMERGENCY
            if db_session.medical_professional_phone and escalation in (EscalationLevel.SEEK_HELP, EscalationLevel.EMERGENCY):
                med_msg = get_caregiver_message(zone, score, red_flags, escalation, db_session.medical_professional_name or "Your patient")
                send_whatsapp_alert(db_session.medical_professional_phone, med_msg)

    return result


@router.get("/score/{session_id}")
def get_latest_score(session_id: str, db: Session = Depends(get_db)):
    """
    Returns the latest score for frontend polling.
    Uses AI Engine for real-time score.
    """
    result = ai.get_score(session_id)
    
    if result.get("status") == "error":
        # Fallback to DB
        return readingService.get_latest_score(session_id, db)
    
    return result


@router.get("/history/{session_id}")
def get_score_history(session_id: str, db: Session = Depends(get_db)):
    """
    Returns all scores for chart rendering.
    Combines AI Engine history with DB records.
    """
    # Try AI Engine first
    history = ai.get_history(session_id)
    
    if history:
        return history
    
    # Fallback to DB
    return readingService.get_all_scores(session_id, db)


@router.post("/predict")
def predict_risk(
    request: readingsDto.PredictRequest,
    db: Session = Depends(get_db)
):
    """
    What-if risk projection.
    
    PRD: POST /api/predict
    Projects future health trajectory based on current patterns.
    Supports optional scenario param for lifestyle-based projections.
    """
    result = ai.predict(
        request.session_id, 
        request.days, 
        scenario=request.scenario
    )
    
    if result.get("status") == "error":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.get("message", "Prediction failed")
        )
    
    return result


@router.get("/nudge/{session_id}")
def get_nudge(session_id: str):
    """
    Get nudge message for manual trigger or display.
    """
    return ai.get_nudge_message(session_id)


@router.post("/alert")
def send_alert(request: readingsDto.MessageRequest):
    """
    Manually send SMS or WhatsApp alert.
    """
    if request.channel.lower() == "sms":
        success = send_sms_alert(request.to_phone, request.message)
    elif request.channel.lower() == "whatsapp":
        success = send_whatsapp_alert(request.to_phone, request.message)
    else:
        raise HTTPException(
            status_code=400,
            detail="Invalid channel. Use 'sms' or 'whatsapp'."
        )

    return {
        "status": "sent" if success else "failed",
        "channel": request.channel
    }


@router.post("/reading/manual")
def receive_manual_reading(
    data: readingsDto.ManualReadingRequest,
    db: Session = Depends(get_db)
):
    """
    Manual biometric entry for when hardware is unavailable.

    Accepts partial readings — missing fields default to safe mid-range values.
    """
    # Fill in defaults for missing optional fields
    bpm = data.bpm
    hrv = data.hrv if data.hrv is not None else 50.0
    spo2 = data.spo2 if data.spo2 is not None else 97.0
    temperature = data.temperature if data.temperature is not None else 36.6

    # Convert to standard BiometricReadingRequest
    reading_data = readingsDto.BiometricReadingRequest(
        bpm=bpm,
        hrv=hrv,
        spo2=spo2,
        temperature=temperature,
        systolic_bp=data.systolic_bp,
        diastolic_bp=data.diastolic_bp,
        timestamp=int(time.time()),
        session_id=data.session_id,
        source="manual",
    )

    # Process through the same pipeline
    return receive_biometric_reading(reading_data, db)


@router.post("/feedback")
def submit_alert_feedback(
    data: readingsDto.AlertFeedbackRequest,
    db: Session = Depends(get_db)
):
    """
    Submit feedback on an alert (helpful, not helpful, false alarm).
    Helps improve alert quality over time.
    """
    if data.feedback not in ("helpful", "not_helpful", "false_alarm"):
        raise HTTPException(
            status_code=400,
            detail="feedback must be 'helpful', 'not_helpful', or 'false_alarm'"
        )

    result = readingService.store_alert_feedback(data, db)
    if not result:
        raise HTTPException(
            status_code=500,
            detail="Failed to store feedback"
        )

    return {"status": "ok", "message": "Feedback recorded. Thank you."}
