from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from dtos import sessionDto
from service import sessionService
from repository.database import get_db
from ai_engine.api import CardioTwinAPI

ai = CardioTwinAPI()

session_router = APIRouter(
    prefix="/api/session",
    tags=["Session"]
)


@session_router.post("/start")
def start_session(
    data: sessionDto.SessionStartRequest,
    db: Session = Depends(get_db)
):
    """
    Starts a new measurement session.
    Accepts optional caregiver and medical professional contacts.
    """
    result = sessionService.start_session(data, db)

    # Also initialize AI engine session with caregiver info
    ai.start_session(
        data.session_id,
        user_phone=data.user_phone,
        caregiver_phone=data.caregiver_phone,
        caregiver_name=data.caregiver_name,
        medical_professional_phone=data.medical_professional_phone,
        medical_professional_name=data.medical_professional_name,
    )

    return result

