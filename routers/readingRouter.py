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
from ai_engine.api import CardioTwinAPI

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
    
    # Ensure AI session exists
    session = ai.engine.get_session(session_id)
    if not session:
        # Get phone number from DB session if exists
        db_session = sessionService.fetch_session(session_id, db)
        phone = db_session.user_phone if db_session else None
        ai.start_session(session_id, user_phone=phone)
    
    # Process through AI Engine
    result = ai.process_reading({
        "bpm": data.bpm,
        "hrv": data.hrv,
        "spo2": data.spo2,
        "temperature": data.temperature,
        "session_id": session_id,
    })
    
    # Store reading in database
    readingService.store_reading(data, result, db)
    
    # Send WhatsApp alert if nudge triggered
    if result.get("nudge_sent"):
        db_session = sessionService.fetch_session(session_id, db)
        if db_session and db_session.user_phone:
            nudge = ai.get_nudge_message(session_id)
            send_whatsapp_alert(db_session.user_phone, nudge["message"])
    
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
