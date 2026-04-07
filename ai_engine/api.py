"""
CardioTwin AI Engine - Backend Integration Facade
=================================================

This module provides a simplified interface for Person 3 (Backend Developer)
to integrate the AI engine into FastAPI endpoints.

Usage in FastAPI:
    from ai_engine.api import CardioTwinAPI
    
    api = CardioTwinAPI()
    
    @app.post("/api/session/start")
    def start_session(request: SessionStartRequest):
        return api.start_session(request.session_id, request.user_phone)
    
    @app.post("/api/reading")
    def process_reading(request: ReadingRequest):
        return api.process_reading(request.dict())
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
from dataclasses import dataclass, asdict

from ai_engine.engine import CardioTwinEngine, SessionStatus
from ai_engine.zones import Zone
from ai_engine.nudges import Language
from ai_engine.safety import (
    should_alert_caregiver,
    get_caregiver_message,
    EscalationLevel,
    DISCLAIMERS,
    validate_llm_output,
    add_safety_wrapper,
)


# Response models matching PRD API contract
@dataclass
class SessionStartResponse:
    status: str
    session_id: str


@dataclass 
class CalibratingResponse:
    status: str = "calibrating"
    readings_collected: int = 0
    readings_needed: int = 5
    alert: bool = False


@dataclass
class ComponentScore:
    value: float
    score: float


@dataclass
class BaselineData:
    resting_bpm: float
    resting_hrv: float
    normal_spo2: float
    normal_temp: float


@dataclass
class ScoredResponse:
    status: str
    score: float
    zone: str
    zone_label: str
    zone_emoji: str
    alert: bool
    nudge_sent: bool
    components: Dict[str, Dict[str, float]]
    baseline: Dict[str, float]


@dataclass
class PredictionResponse:
    current_score: float
    projected_score: float
    projected_resting_hr_increase_bpm: float
    current_risk_category: str
    projected_risk_category: str
    disclaimer: str = "Statistical projection only. Not a medical diagnosis."


@dataclass
class ActionDriver:
    code: str
    label: str
    detail: str


@dataclass
class ActionSummary:
    status: str
    why: str
    next_step: str
    if_symptoms: str
    advice_strength: str
    confidence_level: str
    signal_quality: str
    signal_confidence: float
    drivers: List[Dict[str, str]]


class CardioTwinAPI:
    """
    Facade for integrating CardioTwin AI Engine into FastAPI backend.
    
    Maps the AI engine's internal API to the PRD-specified response formats.
    """
    
    # Zone display mappings per PRD
    ZONE_INFO = {
        Zone.GREEN: {"label": "Thriving", "emoji": "🟢"},
        Zone.YELLOW: {"label": "Mild Strain", "emoji": "🟡"},
        Zone.ORANGE: {"label": "Elevated Risk", "emoji": "🟠"},
        Zone.RED: {"label": "Critical Strain", "emoji": "🔴"},
    }

    ZONE_STATUS = {
        Zone.GREEN: "Stable",
        Zone.YELLOW: "Mild concern",
        Zone.ORANGE: "Elevated concern",
        Zone.RED: "High concern",
    }

    DEFAULT_NEXT_STEPS = {
        Zone.GREEN: "Continue your routine and keep monitoring.",
        Zone.YELLOW: "Sit, rest for 5 minutes, and retake your reading.",
        Zone.ORANGE: "Stop activity, rest, hydrate, and retake shortly.",
        Zone.RED: "Stop activity now and seek urgent support.",
    }

    DEFAULT_IF_SYMPTOMS = "If chest pain or shortness of breath occurs, seek help now."

    CAUTIOUS_NEXT_STEP = "Confidence is limited. Please stay still, rest briefly, and retake reading before acting on this result."

    REASON_DRIVER_LABELS = {
        "spo2_emergency": ("Critically low SpO2", "Blood oxygen is in a critical range."),
        "spo2_critical": ("Low SpO2", "Blood oxygen is below a safe threshold."),
        "spo2_warning": ("SpO2 lower than normal", "Blood oxygen is lower than expected."),
        "hr_very_high": ("Very high heart rate", "Heart rate is significantly above normal."),
        "hr_very_low": ("Very low heart rate", "Heart rate is significantly below normal."),
        "hr_high": ("Elevated heart rate", "Heart rate is above your expected range."),
        "temp_very_high": ("High temperature", "Temperature is in a high-risk range."),
        "temp_very_low": ("Low temperature", "Temperature is in a low-risk range."),
        "temp_high": ("Temperature elevated", "Temperature is above your expected range."),
        "hrv_critically_low": ("Very low HRV", "HRV indicates a high physiological strain state."),
    }

    COMPONENT_LABELS = {
        "heart_rate": "Heart rate strain",
        "hrv": "Low HRV",
        "spo2": "Low SpO2",
        "temperature": "Temperature deviation",
    }
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the API facade.
        
        Args:
            config: Optional engine configuration. Defaults to PRD specs.
        """
        default_config = {
            "calibration_readings": 5,  # Reduced for faster demo experience
            "enable_anomaly_detection": True,
        }
        if config:
            default_config.update(config)
        
        self.engine = CardioTwinEngine(default_config)
        self._phone_numbers: Dict[str, str] = {}  # session_id -> phone
        self._nudge_sent: Dict[str, bool] = {}  # Track nudge status per session

    def _confidence_bucket(self, signal_confidence: float, safety_confidence: Optional[str] = None) -> str:
        if safety_confidence in {"low", "medium", "high"}:
            return safety_confidence

        if signal_confidence >= 0.8:
            return "high"
        if signal_confidence >= 0.5:
            return "medium"
        return "low"

    def _build_action_summary(
        self,
        *,
        zone: Optional[Zone],
        signal_quality: str,
        signal_confidence: float,
        safety_info: Optional[Dict[str, Any]] = None,
        components: Optional[Dict[str, Dict[str, float]]] = None,
        why: Optional[str] = None,
        next_step: Optional[str] = None,
        retake_required: bool = False,
    ) -> Dict[str, Any]:
        safety_info = safety_info or {}
        safety_confidence = safety_info.get("confidence")
        confidence_level = self._confidence_bucket(signal_confidence, safety_confidence)

        if retake_required or confidence_level == "low":
            summary = ActionSummary(
                status="Retake needed",
                why=why or "Signal quality is too low to provide a reliable interpretation.",
                next_step=next_step or "Ensure proper sensor contact, stay still, and retake now.",
                if_symptoms=self.DEFAULT_IF_SYMPTOMS,
                advice_strength="retake_only",
                confidence_level="low",
                signal_quality=signal_quality,
                signal_confidence=round(signal_confidence, 2),
                drivers=[
                    asdict(
                        ActionDriver(
                            code="signal_quality_low",
                            label="Low signal quality",
                            detail="Reading confidence is below acceptable threshold.",
                        )
                    )
                ],
            )
            return asdict(summary)

        resolved_zone = zone or Zone.YELLOW

        driver_candidates: List[Dict[str, str]] = []

        reason_drivers = safety_info.get("reason_drivers") or []
        for reason_code in reason_drivers:
            label, detail = self.REASON_DRIVER_LABELS.get(
                reason_code,
                ("Detected risk factor", reason_code.replace("_", " ")),
            )
            driver_candidates.append(
                asdict(
                    ActionDriver(
                        code=reason_code,
                        label=label,
                        detail=detail,
                    )
                )
            )

        if components:
            component_rank = sorted(
                components.items(),
                key=lambda item: item[1].get("score", 100),
            )
            for component_name, component_data in component_rank:
                score_value = round(component_data.get("score", 0), 1)
                reading_value = component_data.get("value", 0)
                driver_candidates.append(
                    asdict(
                        ActionDriver(
                            code=f"component_{component_name}",
                            label=self.COMPONENT_LABELS.get(component_name, component_name.replace("_", " ").title()),
                            detail=f"Current value {reading_value}, component score {score_value}/100.",
                        )
                    )
                )

        unique_drivers: List[Dict[str, str]] = []
        seen_codes = set()
        for candidate in driver_candidates:
            code = candidate.get("code")
            if not code or code in seen_codes:
                continue
            seen_codes.add(code)
            unique_drivers.append(candidate)
            if len(unique_drivers) == 2:
                break

        resolved_why = why or "Based on your latest vitals and trend."
        resolved_next_step = (
            next_step
            or safety_info.get("safe_next_step")
            or self.DEFAULT_NEXT_STEPS.get(resolved_zone, "Retake reading in a few minutes.")
        )
        advice_strength = "full"

        if confidence_level == "medium":
            resolved_why = f"Preliminary insight: {resolved_why}"
            resolved_next_step = self.CAUTIOUS_NEXT_STEP
            advice_strength = "cautious"

        summary = ActionSummary(
            status=self.ZONE_STATUS.get(resolved_zone, "Monitor"),
            why=resolved_why,
            next_step=resolved_next_step,
            if_symptoms=safety_info.get("seek_help_message") or self.DEFAULT_IF_SYMPTOMS,
            advice_strength=advice_strength,
            confidence_level=confidence_level,
            signal_quality=signal_quality,
            signal_confidence=round(signal_confidence, 2),
            drivers=unique_drivers,
        )
        return asdict(summary)
    
    def start_session(
        self,
        session_id: str,
        user_phone: Optional[str] = None,
        language: str = "en",
        caregiver_phone: Optional[str] = None,
        caregiver_name: Optional[str] = None,
        medical_professional_phone: Optional[str] = None,
        medical_professional_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Start a new measurement session.

        PRD Endpoint: POST /api/session/start

        Args:
            session_id: Unique session identifier (e.g., "demo")
            user_phone: User's phone number for WhatsApp alerts
            language: Language code (en, pcm, yo, ig, ha)
            caregiver_phone: Emergency contact phone
            caregiver_name: Emergency contact name
            medical_professional_phone: Doctor phone
            medical_professional_name: Doctor name

        Returns:
            {"status": "session_started", "session_id": "demo"}
        """
        lang_map = {
            "en": Language.ENGLISH,
            "pcm": Language.PIDGIN,
            "yo": Language.YORUBA,
            "ig": Language.IGBO,
            "ha": Language.HAUSA,
        }
        lang = lang_map.get(language, Language.ENGLISH)

        self.engine.create_session(
            user_id=session_id,
            language=lang,
            session_id=session_id,
            caregiver_phone=caregiver_phone,
            caregiver_name=caregiver_name,
            medical_professional_phone=medical_professional_phone,
            medical_professional_name=medical_professional_name,
        )

        if user_phone:
            self._phone_numbers[session_id] = user_phone

        self._nudge_sent[session_id] = False

        return {
            "status": "session_started",
            "session_id": session_id,
        }
    
    def process_reading(self, reading: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a biometric reading from ESP32 or manual entry.

        PRD Endpoint: POST /api/reading
        Called every 2 seconds by hardware, or on-demand for manual entry.

        Args:
            reading: {
                "bpm": 72, "hrv": 42.3, "spo2": 98.1, "temperature": 36.4,
                "timestamp": 45000, "session_id": "demo",
                "source": "kardiotwin_hw" | "manual"  (optional)
            }

        Returns:
            Calibrating, retake-requested, or scored response.
        """
        session_id = reading.get("session_id", "demo")
        source = reading.get("source", "kardiotwin_hw")

        engine_reading = {
            "heart_rate": reading.get("bpm", reading.get("heart_rate", 0)),
            "hrv": reading.get("hrv", 0),
            "spo2": reading.get("spo2", 0),
            "temperature": reading.get("temperature", 0),
        }

        result = self.engine.process_reading(session_id, engine_reading)

        if not result.success:
            return {"status": "error", "message": result.message}

        # Signal quality: request retake
        if result.retake_requested:
            return {
                "status": "retake_requested",
                "message": result.retake_message,
                "signal_quality": result.signal_quality,
                "signal_confidence": result.signal_confidence,
                "action_summary": self._build_action_summary(
                    zone=None,
                    signal_quality=result.signal_quality,
                    signal_confidence=result.signal_confidence,
                    why=result.retake_message,
                    retake_required=True,
                ),
            }

        session = self.engine.get_session(session_id)

        # If still calibrating
        if session.status == SessionStatus.CALIBRATING:
            return {
                "status": "calibrating",
                "readings_collected": len(session.readings),
                "readings_needed": session.calibration_readings_required,
                "alert": False,
            }

        # Session is active — build scored response
        zone = result.zone
        zone_display = self.ZONE_INFO.get(zone, {"label": "Unknown", "emoji": "⚪"})

        should_alert = zone in [Zone.ORANGE, Zone.RED]

        components = {
            "heart_rate": {
                "value": engine_reading["heart_rate"],
                "score": result.scores.heart_rate if result.scores else 0,
            },
            "hrv": {
                "value": engine_reading["hrv"],
                "score": result.scores.hrv if result.scores else 0,
            },
            "spo2": {
                "value": engine_reading["spo2"],
                "score": result.scores.spo2 if result.scores else 0,
            },
            "temperature": {
                "value": engine_reading["temperature"],
                "score": result.scores.temperature if result.scores else 0,
            },
        }

        baseline = session.baseline or {}
        baseline_data = {
            "resting_bpm": baseline.get("resting_bpm", 70),
            "resting_hrv": baseline.get("resting_hrv", 50),
            "normal_spo2": baseline.get("normal_spo2", 98),
            "normal_temp": baseline.get("normal_temp", 36.5),
        }

        # Nudge tracking
        nudge_sent = False
        if should_alert and not self._nudge_sent.get(session_id, False):
            nudge_sent = True
            self._nudge_sent[session_id] = True
        elif not should_alert:
            self._nudge_sent[session_id] = False

        # Build safety info for response
        safety_info = None
        alert_caregiver = False
        if result.safety:
            safety_info = result.safety.to_dict()
            alert_caregiver = should_alert_caregiver(
                result.safety.escalation,
                zone.value.upper() if zone else "GREEN",
                session.consecutive_zone_count if zone in (Zone.ORANGE, Zone.RED) else 0,
            )

        response = {
            "status": "scored",
            "score": round(result.scores.cardiotwin_score, 1) if result.scores else 0,
            "zone": zone.value.upper(),
            "zone_label": zone_display["label"],
            "zone_emoji": zone_display["emoji"],
            "alert": should_alert,
            "nudge_sent": nudge_sent,
            "components": components,
            "baseline": baseline_data,
            "source": source,
            "signal_quality": result.signal_quality,
            "signal_confidence": result.signal_confidence,
            "safety": safety_info,
            "alert_caregiver": alert_caregiver,
            "action_summary": self._build_action_summary(
                zone=zone,
                signal_quality=result.signal_quality,
                signal_confidence=result.signal_confidence,
                safety_info=safety_info,
                components=components,
            ),
            "disclaimer": DISCLAIMERS["not_diagnostic"],
        }

        return response
    
    def get_score(self, session_id: str) -> Dict[str, Any]:
        """
        Get latest score for frontend polling.
        
        PRD Endpoint: GET /api/score/{session_id}
        """
        session = self.engine.get_session(session_id)
        
        if not session:
            return {"status": "error", "message": "Session not found"}
        
        if session.status == SessionStatus.CALIBRATING:
            return {
                "status": "calibrating",
                "readings_collected": len(session.readings),
                "readings_needed": session.calibration_readings_required,
            }
        
        score = self.engine.get_current_score(session_id)
        zone = self.engine.get_current_zone(session_id)
        zone_info = self.ZONE_INFO.get(zone, {"label": "Unknown", "emoji": "⚪"})
        
        return {
            "status": "scored",
            "score": round(score, 1),
            "zone": zone.value.upper() if zone else "UNKNOWN",
            "zone_label": zone_info["label"],
            "zone_emoji": zone_info["emoji"],
        }
    
    def get_history(self, session_id: str) -> List[Dict[str, Any]]:
        """
        Get all scores for chart rendering.
        
        PRD Endpoint: GET /api/history/{session_id}
        
        Returns:
            Array of score objects with timestamps for Recharts.
        """
        session = self.engine.get_session(session_id)
        
        if not session:
            return []
        
        history = []
        for i, entry in enumerate(session.score_history):
            # score_history contains dicts with "scores" sub-dict
            if isinstance(entry, dict):
                scores_data = entry.get("scores", {})
                score = scores_data.get("cardiotwin_score", 0)
                timestamp = entry.get("timestamp", "")
            else:
                score = float(entry) if entry else 0
                timestamp = ""
            
            # Get zone from zone_history
            zone = Zone.GREEN
            if i < len(session.zone_history):
                z_entry = session.zone_history[i]
                if isinstance(z_entry, dict):
                    z_val = z_entry.get("zone", "green")
                    try:
                        zone = Zone(z_val)
                    except ValueError:
                        zone = Zone.GREEN
                elif isinstance(z_entry, Zone):
                    zone = z_entry
            
            zone_info = self.ZONE_INFO.get(zone, {"label": "Unknown", "emoji": "⚪"})
            
            history.append({
                "index": i,
                "score": round(score, 1),
                "zone": zone.value.upper(),
                "zone_label": zone_info["label"],
                "timestamp": i * 2000,  # 2 seconds per reading (approx)
            })
        
        return history
    
    def predict(self, session_id: str, days: int = 90, scenario: str = None) -> Dict[str, Any]:
        """
        What-if risk projection.
        
        PRD Endpoint: POST /api/predict
        
        Args:
            session_id: Session to project from
            days: Days to project ahead (default 90)
            scenario: Optional lifestyle scenario (e.g., "stop taking sugar")
        
        Returns:
            Projection response per PRD format.
        """
        current_score = self.engine.get_current_score(session_id)
        
        if current_score is None or current_score == 0:
            return {
                "status": "error",
                "message": "Not enough data for projection",
            }
        
        # Project risk using engine
        projection = self.engine.project_risk(session_id, hours_ahead=days * 24)
        
        if not projection:
            # Fallback: simple trend extrapolation
            projected_score = max(0, current_score - (days * 0.1))
        else:
            # Use engine projection (average of projected scores)
            projected_score = sum(projection.projected_scores) / len(projection.projected_scores)
        
        # Apply scenario-based adjustments if provided
        scenario_impact = 0.0
        scenario_note = ""
        if scenario:
            scenario_lower = scenario.lower()
            
            # Parse scenario and estimate impact on score
            if any(word in scenario_lower for word in ['stop', 'quit', 'reduce', 'cut', 'avoid']):
                if any(word in scenario_lower for word in ['sugar', 'sweet', 'carb', 'soda', 'candy']):
                    scenario_impact = 8.5  # Positive impact from reducing sugar
                    scenario_note = "Reducing sugar intake typically improves metabolic health"
                elif any(word in scenario_lower for word in ['smoking', 'smoke', 'cigarette', 'tobacco']):
                    scenario_impact = 15.0  # Major positive impact from quitting smoking
                    scenario_note = "Quitting smoking has significant cardiovascular benefits"
                elif any(word in scenario_lower for word in ['alcohol', 'drink', 'beer', 'wine']):
                    scenario_impact = 6.0  # Positive impact from reducing alcohol
                    scenario_note = "Reducing alcohol improves heart health"
                elif any(word in scenario_lower for word in ['salt', 'sodium']):
                    scenario_impact = 5.0  # Positive impact from reducing salt
                    scenario_note = "Lower sodium intake reduces blood pressure"
            
            elif any(word in scenario_lower for word in ['start', 'begin', 'increase', 'add', 'more']):
                if any(word in scenario_lower for word in ['exercise', 'workout', 'gym', 'run', 'walk', 'jog']):
                    scenario_impact = 12.0  # Major positive impact from exercise
                    scenario_note = "Regular exercise significantly improves cardiovascular health"
                elif any(word in scenario_lower for word in ['sleep', 'rest']):
                    scenario_impact = 7.0  # Positive impact from better sleep
                    scenario_note = "Adequate sleep is crucial for heart health"
                elif any(word in scenario_lower for word in ['water', 'hydrat']):
                    scenario_impact = 4.0  # Moderate positive impact from hydration
                    scenario_note = "Proper hydration supports cardiovascular function"
                elif any(word in scenario_lower for word in ['vegetable', 'fruit', 'fiber']):
                    scenario_impact = 6.5  # Positive impact from better diet
                    scenario_note = "Plant-based foods reduce cardiovascular risk"
                elif any(word in scenario_lower for word in ['meditat', 'yoga', 'mindful']):
                    scenario_impact = 5.5  # Positive impact from stress reduction
                    scenario_note = "Stress management practices benefit heart health"
            
            # Apply gradual impact based on time frame
            time_factor = min(days / 90.0, 1.0)  # Full impact at 90 days
            projected_score += (scenario_impact * time_factor)
            projected_score = min(100, projected_score)  # Cap at 100
        
        # Calculate projected HR increase (rough estimate)
        score_delta = current_score - projected_score
        hr_increase = score_delta * 0.15  # Approximate correlation
        
        # Determine risk categories
        def get_category(score: float) -> str:
            if score >= 80:
                return "Thriving"
            elif score >= 55:
                return "Mild Strain"
            elif score >= 30:
                return "Elevated Risk"
            else:
                return "Critical Strain"
        
        response = {
            "current_score": round(current_score, 1),
            "projected_score": round(projected_score, 1),
            "projected_resting_hr_increase_bpm": round(hr_increase, 1),
            "current_risk_category": get_category(current_score),
            "projected_risk_category": get_category(projected_score),
            "disclaimer": "Statistical projection only. Not a medical diagnosis.",
        }
        
        # Add scenario note if applicable
        if scenario_note:
            response["scenario_note"] = scenario_note
        
        return response
    
    def get_nudge_message(self, session_id: str) -> Dict[str, Any]:
        """
        Get the nudge message for WhatsApp/SMS delivery.
        
        This is called by backend when nudge_sent=true to get message text.
        
        Returns:
            {"message": "...", "zone": "ORANGE", "phone": "+234..."}
        """
        import asyncio
        
        zone = self.engine.get_current_zone(session_id)
        zone_info = self.ZONE_INFO.get(zone, {"label": "Unknown", "emoji": "⚪"})
        
        # Try to get AI-generated nudge, fall back to template
        try:
            loop = asyncio.get_event_loop()
            nudge = loop.run_until_complete(self.engine.generate_nudge(session_id))
        except Exception:
            # Fallback template messages per zone
            templates = {
                Zone.GREEN: "Great job! Your CardioTwin Score is excellent. Keep up the healthy lifestyle! 💚",
                Zone.YELLOW: "Heads up! Your CardioTwin Score shows mild strain. Consider taking a short break and some deep breaths. 💛",
                Zone.ORANGE: "⚠️ Alert: Your CardioTwin Score indicates elevated risk. Please rest, hydrate, and consider speaking with a healthcare provider. 🧡",
                Zone.RED: "🚨 URGENT: Your CardioTwin Score is critically low. Stop physical activity immediately and seek medical attention if symptoms persist. ❤️",
            }
            nudge = templates.get(zone, "Check your CardioTwin dashboard for health insights.")
        
        return {
            "message": nudge,
            "zone": zone.value.upper() if zone else "UNKNOWN",
            "zone_label": zone_info["label"],
            "phone": self._phone_numbers.get(session_id),
        }
    
    def end_session(self, session_id: str) -> Dict[str, Any]:
        """
        End a measurement session.
        
        Returns:
            Session summary.
        """
        summary = self.engine.get_session_summary(session_id)
        self.engine.end_session(session_id)
        
        # Clean up
        self._phone_numbers.pop(session_id, None)
        self._nudge_sent.pop(session_id, None)
        
        return {
            "status": "session_ended",
            "session_id": session_id,
            "summary": summary,
        }


# Convenience function for quick integration
def create_api(config: Optional[Dict[str, Any]] = None) -> CardioTwinAPI:
    """Create a CardioTwinAPI instance with optional config."""
    return CardioTwinAPI(config)
