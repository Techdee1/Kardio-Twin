from sqlalchemy import Column, Integer, Float, String, Boolean, DateTime
from sqlalchemy.sql import func
from repository.database import Base

class Session(Base):
    __tablename__ = "sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, unique=True, index=True)
    user_phone = Column(String, nullable=True)
    created_at = Column(DateTime, server_default=func.now())

class BiometricReading(Base):
    __tablename__ = "biometric_readings"
    
    id = Column(Integer, primary_key=True, index=True)
    bpm = Column(Float, nullable=False)
    hrv = Column(Float, nullable=False)
    spo2 = Column(Float, nullable=False)
    temperature = Column(Float, nullable=False)
    timestamp = Column(Integer, nullable=False)
    session_id = Column(String, index=True, nullable=False)
    # AI Engine computed fields
    score = Column(Float, nullable=True)
    zone = Column(String, nullable=True)
    alert = Column(Boolean, default=False, nullable=True)
    created_at = Column(DateTime, server_default=func.now())