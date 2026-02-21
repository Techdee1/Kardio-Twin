"""
CardioTwin AI Engine
====================

Main orchestration class that combines all AI components.
Entry point for the backend to process biometric readings.

Classes:
    - CardioTwinEngine: Main engine with session management
    - SessionData: Per-user session state
    - ProcessingResult: Result from processing a reading

Usage:
    engine = CardioTwinEngine()
    session_id = engine.create_session(user_id="user123")
    result = engine.process_reading(session_id, reading_data)
    projection = engine.project_risk(session_id, hours_ahead=24)
    nudge = await engine.generate_nudge(session_id)
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Any
from enum import Enum
import uuid

from .validation import validate_reading, sanitize_reading, detect_sensor_error
from .baseline import calibrate_baseline
from .scoring import (
    score_heart_rate,
    score_hrv,
    score_spo2,
    score_temperature,
    calculate_cardiotwin_score,
)
from .zones import Zone, classify_zone, get_zone_context, get_zone_info, ZoneInfo, ZoneTransition
from .anomaly import detect_anomalies, Alert, AlertType, AlertSeverity, AnomalyDetectionResult
from .nudges import generate_nudge, Language, NudgeConfig, Nudge
from .projection import (
    calculate_trend,
    project_risk,
    simulate_scenario,
    get_improvement_path,
    get_risk_trajectory,
    project_recovery_time,
    TrendDirection,
    TrendAnalysis,
    RiskProjection,
    WhatIfScenario,
)


class SessionStatus(Enum):
    """Session lifecycle status."""
    ACTIVE = "active"
    CALIBRATING = "calibrating"  # Collecting initial readings for baseline
    PAUSED = "paused"
    ENDED = "ended"


@dataclass
class ComponentScores:
    """Individual component scores."""
    heart_rate: float = 0.0
    hrv: float = 0.0
    spo2: float = 0.0
    temperature: float = 0.0
    cardiotwin_score: float = 0.0
    
    def to_dict(self) -> Dict[str, float]:
        """Convert to dictionary."""
        return {
            "heart_rate": self.heart_rate,
            "hrv": self.hrv,
            "spo2": self.spo2,
            "temperature": self.temperature,
            "cardiotwin_score": self.cardiotwin_score,
        }


@dataclass
class Reading:
    """Validated and timestamped reading."""
    timestamp: datetime
    heart_rate: float
    hrv: float
    spo2: float
    temperature: float
    raw_data: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "timestamp": self.timestamp.isoformat(),
            "heart_rate": self.heart_rate,
            "hrv": self.hrv,
            "spo2": self.spo2,
            "temperature": self.temperature,
        }


@dataclass
class SessionData:
    """Per-user session state."""
    session_id: str
    user_id: str
    status: SessionStatus = SessionStatus.CALIBRATING
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    # Readings history
    readings: List[Reading] = field(default_factory=list)
    
    # Computed baseline
    baseline: Optional[Dict[str, Any]] = None
    
    # Current state
    current_scores: ComponentScores = field(default_factory=ComponentScores)
    current_zone: Zone = Zone.GREEN
    previous_zone: Optional[Zone] = None
    
    # History tracking
    zone_history: List[Dict[str, Any]] = field(default_factory=list)
    score_history: List[Dict[str, Any]] = field(default_factory=list)
    
    # Alerts
    active_alerts: List[Alert] = field(default_factory=list)
    alert_history: List[Alert] = field(default_factory=list)
    
    # Configuration
    language: Language = Language.ENGLISH
    calibration_readings_required: int = 5
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert session to dictionary."""
        return {
            "session_id": self.session_id,
            "user_id": self.user_id,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "readings_count": len(self.readings),
            "baseline_calibrated": self.baseline is not None,
            "current_scores": self.current_scores.to_dict(),
            "current_zone": self.current_zone.value,
            "active_alerts_count": len(self.active_alerts),
            "language": self.language.value,
        }


@dataclass
class ProcessingResult:
    """Result from processing a reading."""
    success: bool
    session_id: str
    timestamp: datetime
    
    # Validation
    reading_valid: bool = True
    validation_errors: List[str] = field(default_factory=list)
    sensor_errors: List[str] = field(default_factory=list)
    
    # Scores
    scores: Optional[ComponentScores] = None
    
    # Zone
    zone: Optional[Zone] = None
    zone_changed: bool = False
    zone_info: Optional[ZoneInfo] = None
    
    # Alerts
    new_alerts: List[Alert] = field(default_factory=list)
    
    # Trend
    trend: Optional[TrendAnalysis] = None
    
    # Message
    message: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary."""
        return {
            "success": self.success,
            "session_id": self.session_id,
            "timestamp": self.timestamp.isoformat(),
            "reading_valid": self.reading_valid,
            "validation_errors": self.validation_errors,
            "sensor_errors": self.sensor_errors,
            "scores": self.scores.to_dict() if self.scores else None,
            "zone": self.zone.value if self.zone else None,
            "zone_changed": self.zone_changed,
            "zone_info": {
                "label": self.zone_info.label,
                "description": self.zone_info.description,
                "color": self.zone_info.color_hex,
                "urgency": self.zone_info.urgency,
            } if self.zone_info else None,
            "new_alerts": [
                {
                    "type": a.alert_type.value,
                    "severity": a.severity.value,
                    "message": a.message,
                }
                for a in self.new_alerts
            ],
            "trend": {
                "direction": self.trend.direction.value,
                "confidence": self.trend.confidence,
            } if self.trend else None,
            "message": self.message,
        }


class CardioTwinEngine:
    """
    Main CardioTwin AI Engine.
    
    Orchestrates all AI components to process biometric readings
    and provide health insights.
    
    Attributes:
        sessions: Dictionary of active sessions
        config: Engine configuration
    
    Example:
        engine = CardioTwinEngine()
        session_id = engine.create_session("user123")
        
        # Process readings
        result = engine.process_reading(session_id, {
            "heart_rate": 72,
            "hrv": 45,
            "spo2": 98,
            "temperature": 36.6
        })
        
        # Get insights
        nudge = await engine.generate_nudge(session_id)
        projection = engine.project_risk(session_id, hours_ahead=24)
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the CardioTwin engine.
        
        Args:
            config: Optional configuration dictionary
                - calibration_readings: Number of readings for baseline (default: 5)
                - default_language: Default language for nudges (default: "english")
                - max_readings_history: Max readings to keep per session (default: 1000)
        """
        self.config = config or {}
        self.sessions: Dict[str, SessionData] = {}
        
        # Default configuration
        self.calibration_readings = self.config.get("calibration_readings", 5)
        self.default_language = Language(
            self.config.get("default_language", "english")
        )
        self.max_readings_history = self.config.get("max_readings_history", 1000)
    
    def _normalize_reading_data(
        self,
        reading_data: Dict[str, Any],
        session_id: str,
        timestamp: datetime,
    ) -> Dict[str, Any]:
        """
        Normalize reading data to match validation requirements.
        
        Supports both heart_rate and bpm field names.
        Adds timestamp and session_id if missing.
        
        Args:
            reading_data: Raw reading data
            session_id: Session identifier
            timestamp: Timestamp for reading
            
        Returns:
            Normalized reading data dict
        """
        normalized = dict(reading_data)
        
        # Support both heart_rate and bpm
        if "heart_rate" in normalized and "bpm" not in normalized:
            normalized["bpm"] = normalized["heart_rate"]
        elif "bpm" in normalized and "heart_rate" not in normalized:
            normalized["heart_rate"] = normalized["bpm"]
        
        # Add timestamp as unix timestamp (int) if missing
        if "timestamp" not in normalized:
            normalized["timestamp"] = int(timestamp.timestamp())
        elif isinstance(normalized["timestamp"], str):
            # Convert ISO format string to unix timestamp
            normalized["timestamp"] = int(datetime.fromisoformat(normalized["timestamp"]).timestamp())
        
        # Add session_id if missing
        if "session_id" not in normalized:
            normalized["session_id"] = session_id
        
        return normalized
    
    def create_session(
        self,
        user_id: str,
        language: Optional[Language] = None,
        session_id: Optional[str] = None,
    ) -> str:
        """
        Create a new user session.
        
        Args:
            user_id: Unique user identifier
            language: Preferred language for nudges
            session_id: Optional custom session ID
            
        Returns:
            Session ID string
        """
        sid = session_id or str(uuid.uuid4())
        
        self.sessions[sid] = SessionData(
            session_id=sid,
            user_id=user_id,
            language=language or self.default_language,
            calibration_readings_required=self.calibration_readings,
        )
        
        return sid
    
    def get_session(self, session_id: str) -> Optional[SessionData]:
        """
        Get session data.
        
        Args:
            session_id: Session identifier
            
        Returns:
            SessionData or None if not found
        """
        return self.sessions.get(session_id)
    
    def end_session(self, session_id: str) -> bool:
        """
        End a session.
        
        Args:
            session_id: Session identifier
            
        Returns:
            True if session was ended, False if not found
        """
        session = self.sessions.get(session_id)
        if session:
            session.status = SessionStatus.ENDED
            session.updated_at = datetime.now()
            return True
        return False
    
    def delete_session(self, session_id: str) -> bool:
        """
        Delete a session completely.
        
        Args:
            session_id: Session identifier
            
        Returns:
            True if deleted, False if not found
        """
        if session_id in self.sessions:
            del self.sessions[session_id]
            return True
        return False
    
    def process_reading(
        self,
        session_id: str,
        reading_data: Dict[str, Any],
    ) -> ProcessingResult:
        """
        Process a single biometric reading through the full pipeline.
        
        Pipeline:
        1. Validate reading data
        2. Sanitize values
        3. Check for sensor errors
        4. Update baseline (if calibrating)
        5. Calculate component scores
        6. Classify zone
        7. Detect anomalies
        8. Calculate trend
        
        Args:
            session_id: Session identifier
            reading_data: Dictionary with heart_rate, hrv, spo2, temperature
            
        Returns:
            ProcessingResult with all computed data
        """
        now = datetime.now()
        
        # Get session
        session = self.sessions.get(session_id)
        if not session:
            return ProcessingResult(
                success=False,
                session_id=session_id,
                timestamp=now,
                reading_valid=False,
                validation_errors=["Session not found"],
                message="Invalid session",
            )
        
        if session.status == SessionStatus.ENDED:
            return ProcessingResult(
                success=False,
                session_id=session_id,
                timestamp=now,
                reading_valid=False,
                validation_errors=["Session has ended"],
                message="Session ended",
            )
        
        # Normalize field names (support both heart_rate and bpm)
        normalized_data = self._normalize_reading_data(reading_data, session_id, now)
        
        # Step 1: Validate reading
        is_valid, errors = validate_reading(normalized_data)
        if not is_valid:
            return ProcessingResult(
                success=False,
                session_id=session_id,
                timestamp=now,
                reading_valid=False,
                validation_errors=[errors] if errors else [],
                message="Invalid reading data",
            )
        
        # Step 2: Sanitize values
        sanitized = sanitize_reading(normalized_data)
        
        # Step 3: Check for sensor errors
        has_sensor_error, sensor_error_type = detect_sensor_error(sanitized)
        sensor_errors = [sensor_error_type] if has_sensor_error and sensor_error_type else []
        
        # Create reading object (sanitized uses 'bpm', we use 'heart_rate')
        reading = Reading(
            timestamp=now,
            heart_rate=sanitized["bpm"],
            hrv=sanitized["hrv"],
            spo2=sanitized["spo2"],
            temperature=sanitized["temperature"],
            raw_data=reading_data,
        )
        
        # Add to history
        session.readings.append(reading)
        
        # Trim history if needed
        if len(session.readings) > self.max_readings_history:
            session.readings = session.readings[-self.max_readings_history:]
        
        session.updated_at = now
        
        # Step 4: Update baseline if calibrating
        if session.status == SessionStatus.CALIBRATING:
            if len(session.readings) >= session.calibration_readings_required:
                # Calibrate baseline - convert readings to expected format
                calibration_readings = [
                    {
                        "bpm": r.heart_rate,
                        "hrv": r.hrv,
                        "spo2": r.spo2,
                        "temperature": r.temperature,
                    }
                    for r in session.readings
                ]
                
                baseline_result = calibrate_baseline(calibration_readings)
                
                # Check if calibration completed successfully
                if baseline_result.get("calibration_complete", False):
                    session.baseline = baseline_result
                    session.status = SessionStatus.ACTIVE
        
        # Use baseline or defaults for scoring
        baseline = session.baseline
        
        # Default baseline values if not yet calibrated
        baseline_hr = baseline.get("resting_bpm", 70.0) if baseline else 70.0
        baseline_hrv = baseline.get("resting_hrv", 50.0) if baseline else 50.0
        baseline_spo2 = baseline.get("normal_spo2", 98.0) if baseline else 98.0
        baseline_temp = baseline.get("normal_temp", 36.6) if baseline else 36.6
        
        # Step 5: Calculate component scores (functions return Tuple[score, description])
        hr_score, _ = score_heart_rate(reading.heart_rate, baseline_hr)
        hrv_score, _ = score_hrv(reading.hrv, baseline_hrv)
        spo2_score, _ = score_spo2(reading.spo2, baseline_spo2)
        temp_score, _ = score_temperature(reading.temperature, baseline_temp)
        
        cardiotwin_score = calculate_cardiotwin_score(
            hr_score, hrv_score, spo2_score, temp_score
        )
        
        scores = ComponentScores(
            heart_rate=hr_score,
            hrv=hrv_score,
            spo2=spo2_score,
            temperature=temp_score,
            cardiotwin_score=cardiotwin_score,
        )
        
        session.current_scores = scores
        session.score_history.append({
            "timestamp": now.isoformat(),
            "scores": scores.to_dict(),
        })
        
        # Step 6: Classify zone
        previous_zone = session.current_zone
        zone = classify_zone(cardiotwin_score)
        zone_info = get_zone_info(cardiotwin_score)
        zone_changed = zone != previous_zone
        
        session.previous_zone = previous_zone
        session.current_zone = zone
        session.zone_history.append({
            "timestamp": now.isoformat(),
            "zone": zone.value,
            "score": cardiotwin_score,
        })
        
        # Step 7: Detect anomalies
        # Build current reading dict for anomaly detection
        current_reading_dict = {
            "hr": reading.heart_rate,
            "hrv": reading.hrv,
            "spo2": reading.spo2,
            "temp": reading.temperature,
        }
        
        # Build baseline dict for anomaly detection
        baseline_dict = None
        if session.baseline:
            baseline_dict = {
                "hr": session.baseline.get("resting_bpm", 70.0),
                "hrv": session.baseline.get("resting_hrv", 50.0),
                "spo2": session.baseline.get("normal_spo2", 98.0),
                "temp": session.baseline.get("normal_temp", 36.6),
            }
        
        # Get previous score for anomaly detection
        previous_score = None
        if len(session.score_history) > 0:
            previous_score = session.score_history[-1]["scores"]["cardiotwin_score"]
        
        anomaly_result = detect_anomalies(
            current_score=cardiotwin_score,
            previous_score=previous_score,
            score_history=[h["scores"]["cardiotwin_score"] for h in session.score_history[-10:]],
            current_zone=zone,
            previous_zone=previous_zone,
            baseline=baseline_dict,
            current_reading=current_reading_dict,
            component_scores={
                "heart_rate": hr_score,
                "hrv": hrv_score,
                "spo2": spo2_score,
                "temperature": temp_score,
            },
        )
        
        alerts = anomaly_result.alerts
        
        if alerts:
            session.active_alerts = alerts
            session.alert_history.extend(alerts)
        
        # Step 8: Calculate trend
        trend = None
        if len(session.score_history) >= 3:
            recent_scores = [
                h["scores"]["cardiotwin_score"]
                for h in session.score_history[-10:]
            ]
            trend = calculate_trend(recent_scores)
        
        # Build result message
        if session.status == SessionStatus.CALIBRATING:
            remaining = session.calibration_readings_required - len(session.readings)
            message = f"Calibrating baseline: {remaining} more readings needed"
        elif alerts:
            high_severity = [a for a in alerts if a.severity in [AlertSeverity.URGENT, AlertSeverity.CRITICAL]]
            if high_severity:
                message = f"⚠️ Alert: {high_severity[0].message}"
            else:
                message = f"Notice: {alerts[0].message}"
        elif zone_changed:
            message = f"Zone changed: {previous_zone.value} → {zone.value}"
        else:
            message = f"Zone: {zone.value} | Score: {cardiotwin_score:.1f}"
        
        return ProcessingResult(
            success=True,
            session_id=session_id,
            timestamp=now,
            reading_valid=True,
            sensor_errors=sensor_errors,
            scores=scores,
            zone=zone,
            zone_changed=zone_changed,
            zone_info=zone_info,
            new_alerts=alerts,
            trend=trend,
            message=message,
        )
    
    def get_current_score(self, session_id: str) -> Optional[float]:
        """
        Get current CardioTwin score for a session.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Current score or None if not found
        """
        session = self.sessions.get(session_id)
        if session:
            return session.current_scores.cardiotwin_score
        return None
    
    def get_current_zone(self, session_id: str) -> Optional[Zone]:
        """
        Get current zone for a session.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Current zone or None if not found
        """
        session = self.sessions.get(session_id)
        if session:
            return session.current_zone
        return None
    
    def get_active_alerts(self, session_id: str) -> List[Alert]:
        """
        Get active alerts for a session.
        
        Args:
            session_id: Session identifier
            
        Returns:
            List of active alerts
        """
        session = self.sessions.get(session_id)
        if session:
            return session.active_alerts
        return []
    
    async def generate_nudge(
        self,
        session_id: str,
        language: Optional[Language] = None,
    ) -> Optional[str]:
        """
        Generate a personalized health nudge using Groq API.
        
        Args:
            session_id: Session identifier
            language: Override language for this nudge
            
        Returns:
            Nudge message string or None if session not found
        """
        session = self.sessions.get(session_id)
        if not session:
            return None
        
        lang = language or session.language
        
        # Get zone info for the current score
        zone_info = get_zone_info(session.current_scores.cardiotwin_score)
        
        # Create nudge config with language preference
        config = NudgeConfig(language=lang)
        
        # Generate the nudge
        nudge = await generate_nudge(zone_info, config=config)
        
        return nudge.message
    
    def project_risk(
        self,
        session_id: str,
        hours_ahead: int = 24,
    ) -> Optional[RiskProjection]:
        """
        Project future risk for a session.
        
        Args:
            session_id: Session identifier
            hours_ahead: Hours to project ahead
            
        Returns:
            RiskProjection or None if insufficient data
        """
        session = self.sessions.get(session_id)
        if not session or len(session.score_history) < 3:
            return None
        
        recent_scores = [
            h["scores"]["cardiotwin_score"]
            for h in session.score_history[-10:]
        ]
        
        return project_risk(
            current_score=session.current_scores.cardiotwin_score,
            score_history=recent_scores,
            current_zone=session.current_zone,
            hours_ahead=hours_ahead,
        )
    
    def simulate_scenario(
        self,
        session_id: str,
        scenario_name: str,
    ) -> Optional[WhatIfScenario]:
        """
        Simulate a what-if scenario for a session.
        
        Args:
            session_id: Session identifier
            scenario_name: Name of scenario (e.g., "deep_breathing", "continued_stress")
            
        Returns:
            WhatIfScenario or None if session not found
        """
        session = self.sessions.get(session_id)
        if not session:
            return None
        
        return simulate_scenario(
            scenario_name,
            session.current_scores.cardiotwin_score,
        )
    
    def get_improvement_suggestions(
        self,
        session_id: str,
    ) -> Optional[Dict[str, Any]]:
        """
        Get personalized improvement suggestions.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Dictionary with improvement path or None if not found
        """
        session = self.sessions.get(session_id)
        if not session:
            return None
        
        current_score = session.current_scores.cardiotwin_score
        scenarios = get_improvement_path(current_score)
        
        # Build improvement suggestions from scenario list
        steps = [s.explanation for s in scenarios]
        
        return {
            "current_score": current_score,
            "current_zone": session.current_zone.value,
            "target_score": 80,  # Green zone threshold
            "steps": steps,
            "expected_time_hours": len(scenarios) * 2 if scenarios else 0,
        }
    
    def get_risk_trajectory(
        self,
        session_id: str,
        hours: int = 24,
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Get hourly risk trajectory.
        
        Args:
            session_id: Session identifier
            hours: Number of hours to project
            
        Returns:
            List of hourly projections or None if insufficient data
        """
        session = self.sessions.get(session_id)
        if not session or len(session.score_history) < 3:
            return None
        
        current_score = session.current_scores.cardiotwin_score
        trajectory = get_risk_trajectory(current_score, "no_change", hours)
        
        # Return hourly projections list
        return trajectory.get("hourly_projections", [])
    
    def estimate_recovery_time(
        self,
        session_id: str,
    ) -> Optional[Dict[str, Any]]:
        """
        Estimate time to reach green zone.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Recovery estimate or None if not found
        """
        session = self.sessions.get(session_id)
        if not session:
            return None
        
        recovery = project_recovery_time(
            session.current_scores.cardiotwin_score,
            80,  # Green zone threshold
            "rest_15min",
        )
        
        # Get improvement recommendations
        scenarios = get_improvement_path(session.current_scores.cardiotwin_score)
        recommendations = [s.explanation for s in scenarios]
        
        return {
            "current_zone": session.current_zone.value,
            "target_zone": "green",
            "estimated_hours": recovery.get("estimated_hours", 0),
            "recommendations": recommendations,
        }
    
    def get_session_summary(
        self,
        session_id: str,
    ) -> Optional[Dict[str, Any]]:
        """
        Get comprehensive session summary.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Dictionary with full session summary or None if not found
        """
        session = self.sessions.get(session_id)
        if not session:
            return None
        
        # Calculate statistics
        readings_count = len(session.readings)
        
        # Zone distribution
        zone_counts = {}
        for zh in session.zone_history:
            zone = zh["zone"]
            zone_counts[zone] = zone_counts.get(zone, 0) + 1
        
        # Score statistics
        scores = [h["scores"]["cardiotwin_score"] for h in session.score_history]
        avg_score = sum(scores) / len(scores) if scores else 0
        min_score = min(scores) if scores else 0
        max_score = max(scores) if scores else 0
        
        # Trend
        trend = None
        if len(scores) >= 3:
            trend_analysis = calculate_trend(scores[-10:])
            trend = trend_analysis.direction.value
        
        return {
            "session_id": session.session_id,
            "user_id": session.user_id,
            "status": session.status.value,
            "duration_minutes": (
                session.updated_at - session.created_at
            ).total_seconds() / 60,
            "readings_count": readings_count,
            "baseline_calibrated": session.baseline is not None,
            "current_state": {
                "zone": session.current_zone.value,
                "scores": session.current_scores.to_dict(),
            },
            "statistics": {
                "average_score": round(avg_score, 1),
                "min_score": round(min_score, 1),
                "max_score": round(max_score, 1),
                "zone_distribution": zone_counts,
            },
            "trend": trend,
            "alerts_count": len(session.alert_history),
            "active_alerts": len(session.active_alerts),
        }
    
    def set_language(self, session_id: str, language: Language) -> bool:
        """
        Set preferred language for a session.
        
        Args:
            session_id: Session identifier
            language: Language preference
            
        Returns:
            True if set, False if session not found
        """
        session = self.sessions.get(session_id)
        if session:
            session.language = language
            return True
        return False
    
    def get_all_sessions(self) -> List[Dict[str, Any]]:
        """
        Get summary of all sessions.
        
        Returns:
            List of session summaries
        """
        return [session.to_dict() for session in self.sessions.values()]
    
    def get_active_sessions(self) -> List[str]:
        """
        Get IDs of all active sessions.
        
        Returns:
            List of session IDs
        """
        return [
            sid for sid, session in self.sessions.items()
            if session.status == SessionStatus.ACTIVE
        ]
