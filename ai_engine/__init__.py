"""
CardioTwin AI Engine
====================

A real-time cardiometabolic risk scoring engine that transforms 
biometric sensor data into actionable cardiovascular risk insights.

Main Components:
- CardioTwinEngine: Main entry point for processing readings
- Scoring functions: HR, HRV, SpO2, Temperature
- Baseline calibration system
- Anomaly detection and alerts
- Grok-powered dynamic messaging
- What-if risk projections

Usage:
    from ai_engine import CardioTwinEngine
    
    engine = CardioTwinEngine()
    result = engine.process_reading({
        "bpm": 72,
        "hrv": 42.3,
        "spo2": 98.1,
        "temperature": 36.4,
        "timestamp": 45000,
        "session_id": "demo"
    })

Author: CardioTwin AI Team
Version: 1.0.0
Date: February 2026
"""

__version__ = "1.0.0"
__author__ = "CardioTwin AI Team"

# These will be imported as modules are built
# from .engine import CardioTwinEngine
# from .scoring import (
#     score_heart_rate,
#     score_hrv,
#     score_spo2,
#     score_temperature,
#     calculate_cardiotwin_score
# )
# from .baseline import calibrate_baseline
# from .zones import classify_zone
# from .anomaly import detect_anomaly
# from .projection import project_risk
# from .nudges import generate_nudge

__all__ = [
    "CardioTwinEngine",
    "__version__",
]
