from typing import Union, Optional
from pydantic import BaseModel
from datetime import datetime

# Component and Baseline DTOs
class ComponentScore(BaseModel):
    value: float
    score: float

class ComponentsData(BaseModel):
    heart_rate: ComponentScore
    hrv: ComponentScore
    spo2: ComponentScore
    temperature: ComponentScore

class BaselineData(BaseModel):
    resting_bpm: float
    resting_hrv: float
    normal_spo2: float
    normal_temp: float

# Request DTOs
class BiometricReadingRequest(BaseModel):
    bpm: float
    hrv: float
    spo2: float
    temperature: float
    timestamp: Union[int, datetime] = 0
    session_id: str
    components: Optional[ComponentsData] = None  # Optional - AI engine computes if not provided
    baseline: Optional[BaselineData] = None      # Optional - AI engine computes if not provided

class PredictionsRequest(BaseModel):
    bpm: float
    hrv: float
    spo2: float
    temperature: float
    timestamp: int
    session_id: str
    days: int

class PredictRequest(BaseModel):
    """Request for risk prediction."""
    session_id: str
    days: int = 90

# Response DTOs
class CalibratingReadingResponse(BaseModel):
    status: str = "calibrating"
    readings_collected: int
    readings_needed: int
    alert: bool = False
    
# -----------------------------
# Request Model
# -----------------------------

class MessageRequest(BaseModel):
    to_phone: str        # Format: +1234567890
    message: str
    channel: str         # "sms" or "whatsapp"


class ScoredReadingResponse(BaseModel):
    status: str = "scored"
    score: float
    zone: str
    zone_label: str
    zone_emoji: str
    alert: bool = False
    nudge_sent: bool = False
    components: ComponentsData
    baseline: BaselineData
