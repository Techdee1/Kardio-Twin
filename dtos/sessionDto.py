from pydantic import BaseModel
from typing import Optional

class SessionStartRequest(BaseModel):
    session_id: str
    user_phone: Optional[str] = None

class SessionStartResponse(BaseModel):
    status: str = "session_started"
    session_id: str
