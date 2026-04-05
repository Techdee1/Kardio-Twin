from sqlalchemy import Column, Integer, Float, String, Boolean, DateTime, Text
from sqlalchemy.sql import func
from repository.database import Base


class Session(Base):
    __tablename__ = "sessions"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, unique=True, index=True)
    user_phone = Column(String, nullable=True)
    # Caregiver / medical professional contacts
    caregiver_phone = Column(String, nullable=True)
    caregiver_name = Column(String, nullable=True)
    medical_professional_phone = Column(String, nullable=True)
    medical_professional_name = Column(String, nullable=True)
    created_at = Column(DateTime, server_default=func.now())


class BiometricReading(Base):
    __tablename__ = "biometric_readings"

    id = Column(Integer, primary_key=True, index=True)
    bpm = Column(Float, nullable=False)
    hrv = Column(Float, nullable=False)
    spo2 = Column(Float, nullable=False)
    temperature = Column(Float, nullable=False)
    # Optional manual-entry fields
    systolic_bp = Column(Float, nullable=True)
    diastolic_bp = Column(Float, nullable=True)
    timestamp = Column(Integer, nullable=False)
    session_id = Column(String, index=True, nullable=False)
    source = Column(String, default="hardware")  # "hardware" or "manual"
    # AI Engine computed fields
    score = Column(Float, nullable=True)
    zone = Column(String, nullable=True)
    alert = Column(Boolean, default=False, nullable=True)
    signal_quality = Column(String, nullable=True)
    signal_confidence = Column(Float, nullable=True)
    created_at = Column(DateTime, server_default=func.now())


class AlertFeedback(Base):
    __tablename__ = "alert_feedback"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, index=True, nullable=False)
    reading_id = Column(Integer, nullable=True)
    alert_type = Column(String, nullable=False)
    feedback = Column(String, nullable=False)  # "helpful", "not_helpful", "false_alarm"
    comment = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now())