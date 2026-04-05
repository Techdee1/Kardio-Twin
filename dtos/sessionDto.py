from pydantic import BaseModel
from typing import Optional


class SessionStartRequest(BaseModel):
    session_id: str
    user_phone: Optional[str] = None
    caregiver_phone: Optional[str] = None
    caregiver_name: Optional[str] = None
    medical_professional_phone: Optional[str] = None
    medical_professional_name: Optional[str] = None


class SessionStartResponse(BaseModel):
    status: str = "session_started"
    session_id: str
