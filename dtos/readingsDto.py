from typing import Union, Optional, List, Dict, Any
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
    systolic_bp: Optional[float] = None
    diastolic_bp: Optional[float] = None
    timestamp: Union[int, datetime] = 0
    session_id: str
    source: str = "hardware"  # "hardware" or "manual"
    components: Optional[ComponentsData] = None
    baseline: Optional[BaselineData] = None


class ManualReadingRequest(BaseModel):
    """Manual entry when hardware is unavailable."""
    session_id: str
    bpm: float
    hrv: Optional[float] = None
    spo2: Optional[float] = None
    temperature: Optional[float] = None
    systolic_bp: Optional[float] = None
    diastolic_bp: Optional[float] = None


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
    scenario: Optional[str] = None


class AlertFeedbackRequest(BaseModel):
    """User feedback on an alert."""
    session_id: str
    reading_id: Optional[int] = None
    alert_type: str
    feedback: str  # "helpful", "not_helpful", "false_alarm"
    comment: Optional[str] = None


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


class SafetyInfo(BaseModel):
    is_safe: bool
    escalation: str
    red_flags: List[str] = []
    safe_next_step: str = ""
    seek_help_message: Optional[str] = None


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
    source: str = "hardware"
    signal_quality: Optional[str] = None
    signal_confidence: Optional[float] = None
    safety: Optional[SafetyInfo] = None
    disclaimer: str = "This is a wellness screening tool, not a medical diagnosis."
