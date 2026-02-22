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


# Response models matching PRD API contract
@dataclass
class SessionStartResponse:
    status: str
    session_id: str


@dataclass 
class CalibratingResponse:
    status: str = "calibrating"
    readings_collected: int = 0
    readings_needed: int = 15
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
    
    def start_session(
        self, 
        session_id: str, 
        user_phone: Optional[str] = None,
        language: str = "en"
    ) -> Dict[str, Any]:
        """
        Start a new measurement session.
        
        PRD Endpoint: POST /api/session/start
        
        Args:
            session_id: Unique session identifier (e.g., "demo")
            user_phone: User's phone number for WhatsApp alerts
            language: Language code (en, pcm, yo, ig, ha)
        
        Returns:
            {"status": "session_started", "session_id": "demo"}
        """
        # Map language code to Language enum
        lang_map = {
            "en": Language.ENGLISH,
            "pcm": Language.PIDGIN,
            "yo": Language.YORUBA,
            "ig": Language.IGBO,
            "ha": Language.HAUSA,
        }
        lang = lang_map.get(language, Language.ENGLISH)
        
        # Create session in engine (use session_id as both user_id and session_id)
        self.engine.create_session(
            user_id=session_id, 
            language=lang,
            session_id=session_id,  # Use the same ID for simplicity
        )
        
        # Store phone number for alerts
        if user_phone:
            self._phone_numbers[session_id] = user_phone
        
        self._nudge_sent[session_id] = False
        
        return {
            "status": "session_started",
            "session_id": session_id,
        }
    
    def process_reading(self, reading: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a biometric reading from ESP32.
        
        PRD Endpoint: POST /api/reading
        Called every 2 seconds by hardware.
        
        Args:
            reading: {
                "bpm": 72,
                "hrv": 42.3,
                "spo2": 98.1,
                "temperature": 36.4,
                "timestamp": 45000,
                "session_id": "demo"
            }
        
        Returns:
            Calibrating response or scored response per PRD format.
        """
        session_id = reading.get("session_id", "demo")
        
        # Map PRD field names to engine field names
        engine_reading = {
            "heart_rate": reading.get("bpm", reading.get("heart_rate", 0)),
            "hrv": reading.get("hrv", 0),
            "spo2": reading.get("spo2", 0),
            "temperature": reading.get("temperature", 0),
        }
        
        # Process through engine
        result = self.engine.process_reading(session_id, engine_reading)
        
        if not result.success:
            return {"status": "error", "message": result.message}
        
        # Get session to check status
        session = self.engine.get_session(session_id)
        
        # If still calibrating
        if session.status == SessionStatus.CALIBRATING:
            readings_collected = len(session.readings)
            readings_needed = session.calibration_readings_required
            
            return {
                "status": "calibrating",
                "readings_collected": readings_collected,
                "readings_needed": readings_needed,
                "alert": False,
            }
        
        # Session is active - return full scored response
        zone = result.zone
        zone_info = self.ZONE_INFO.get(zone, {"label": "Unknown", "emoji": "⚪"})
        
        # Determine if alert should trigger (Orange or Red zone)
        should_alert = zone in [Zone.ORANGE, Zone.RED]
        
        # Build component scores
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
        
        # Get baseline data (baseline is a dict)
        baseline = session.baseline or {}
        baseline_data = {
            "resting_bpm": baseline.get("resting_bpm", 70),
            "resting_hrv": baseline.get("resting_hrv", 50),
            "normal_spo2": baseline.get("normal_spo2", 98),
            "normal_temp": baseline.get("normal_temp", 36.5),
        }
        
        # Track if nudge was sent this reading (for backend to trigger Twilio)
        nudge_sent = False
        if should_alert and not self._nudge_sent.get(session_id, False):
            nudge_sent = True
            self._nudge_sent[session_id] = True
        elif not should_alert:
            # Reset nudge flag when back to safe zone
            self._nudge_sent[session_id] = False
        
        return {
            "status": "scored",
            "score": round(result.scores.cardiotwin_score, 1) if result.scores else 0,
            "zone": zone.value.upper(),
            "zone_label": zone_info["label"],
            "zone_emoji": zone_info["emoji"],
            "alert": should_alert,
            "nudge_sent": nudge_sent,
            "components": components,
            "baseline": baseline_data,
        }
    
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
