from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from dtos import sessionDto
from service import sessionService
from repository.database import get_db

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
    """
    return sessionService.start_session(data, db)

