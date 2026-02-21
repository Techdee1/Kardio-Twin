"""
CardioTwin Backend - FastAPI Reference Implementation
=====================================================

This is a complete FastAPI backend for Person 3 to use.
Either use this directly or copy the patterns into your own app.

Run locally:
    uvicorn ai_engine.fastapi_app:app --reload --port 8000

Deploy to Azure:
    - Set GROQ_API_KEY environment variable
    - Deploy this file as the entry point

Endpoints match PRD API contract exactly.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import os

from ai_engine.api import CardioTwinAPI

# Initialize FastAPI
app = FastAPI(
    title="CardioTwin AI API",
    description="Real-time cardiometabolic risk scoring from biometric sensors",
    version="1.0.0",
)

# CORS for frontend access (PRD requirement)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict to your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize AI engine API
api = CardioTwinAPI()


# ============== Request Models (matching PRD) ==============

class SessionStartRequest(BaseModel):
    session_id: str
    user_phone: Optional[str] = None
    language: Optional[str] = "en"


class ReadingRequest(BaseModel):
    bpm: float
    hrv: float
    spo2: float
    temperature: float
    timestamp: Optional[int] = 0
    session_id: str = "demo"


class PredictRequest(BaseModel):
    session_id: str
    days: int = 90


# ============== Endpoints (matching PRD API contract) ==============

@app.get("/")
def root():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "CardioTwin AI",
        "version": "1.0.0",
    }


@app.post("/api/session/start")
def start_session(request: SessionStartRequest):
    """
    Start a new measurement session.
    
    PRD: POST /api/session/start
    """
    return api.start_session(
        session_id=request.session_id,
        user_phone=request.user_phone,
        language=request.language or "en",
    )


@app.post("/api/reading")
def process_reading(request: ReadingRequest):
    """
    Process biometric reading from ESP32.
    Called every 2 seconds by hardware.
    
    PRD: POST /api/reading
    
    Returns calibrating response until 15 readings collected,
    then returns scored response with CardioTwin Score.
    """
    result = api.process_reading(request.dict())
    
    # If nudge should be sent, you can trigger Twilio here
    if result.get("nudge_sent"):
        nudge_info = api.get_nudge_message(request.session_id)
        # TODO: Person 3 - Add Twilio WhatsApp integration here
        # send_whatsapp_message(nudge_info["phone"], nudge_info["message"])
        print(f"📱 NUDGE TRIGGERED: {nudge_info['message'][:50]}...")
    
    return result


@app.get("/api/score/{session_id}")
def get_score(session_id: str):
    """
    Get latest score for frontend polling.
    
    PRD: GET /api/score/{session_id}
    """
    result = api.get_score(session_id)
    if result.get("status") == "error":
        raise HTTPException(status_code=404, detail=result["message"])
    return result


@app.get("/api/history/{session_id}")
def get_history(session_id: str):
    """
    Get all scores for chart rendering.
    
    PRD: GET /api/history/{session_id}
    Returns array of score objects for Recharts.
    """
    return api.get_history(session_id)


@app.post("/api/predict")
def predict(request: PredictRequest):
    """
    What-if risk projection.
    
    PRD: POST /api/predict
    """
    result = api.predict(request.session_id, request.days)
    if result.get("status") == "error":
        raise HTTPException(status_code=400, detail=result["message"])
    return result


@app.get("/api/nudge/{session_id}")
def get_nudge(session_id: str):
    """
    Get nudge message for manual trigger.
    
    Use this to get the message text for WhatsApp delivery.
    """
    return api.get_nudge_message(session_id)


@app.post("/api/session/end/{session_id}")
def end_session(session_id: str):
    """End a measurement session and get summary."""
    return api.end_session(session_id)


# ============== Twilio Integration Hooks ==============
# Person 3: Implement these functions

def send_whatsapp_message(phone: str, message: str) -> bool:
    """
    Send WhatsApp message via Twilio.
    
    Person 3: Implement this with Twilio SDK:
    
    from twilio.rest import Client
    
    client = Client(
        os.environ.get("TWILIO_ACCOUNT_SID"),
        os.environ.get("TWILIO_AUTH_TOKEN")
    )
    
    message = client.messages.create(
        body=message,
        from_='whatsapp:+14155238886',  # Twilio sandbox number
        to=f'whatsapp:{phone}'
    )
    return True
    """
    # TODO: Implement Twilio integration
    print(f"[TWILIO STUB] Would send to {phone}: {message[:50]}...")
    return False


def trigger_vibration(session_id: str) -> bool:
    """
    Trigger vibration motor on ESP32.
    
    The ESP32 firmware should check the `alert` field in the 
    /api/reading response. If alert=true, vibrate.
    
    This function is for server-initiated vibration if needed.
    """
    # The alert field in process_reading response handles this
    return True


# ============== Run Server ==============

if __name__ == "__main__":
    import uvicorn
    
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
