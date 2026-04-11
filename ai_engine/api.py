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
    prediction_source: str = "engine_projection"
    prediction_horizon_days: int = 90
    prediction_horizon_hours: int = 2160
    confidence: float = 0.0
    best_case_score: Optional[float] = None
    worst_case_score: Optional[float] = None
    trend_direction: Optional[str] = None
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

    PREDICTION_DEFAULT_DAYS = 90
    PREDICTION_MIN_DAYS = 1
    PREDICTION_MAX_DAYS = 180
    
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

    def _confidence_bucket(self, signal_confidence: float) -> str:
        if signal_confidence >= 0.8:
            return "high"
        if signal_confidence >= 0.6:
            return "medium"
        return "low"

    def _confidence_score_from_level(self, level: str) -> float:
        if level == "high":
            return 0.9
        if level == "medium":
            return 0.65
        return 0.4

    def _normalize_prediction_days(self, days: Optional[int]) -> int:
        try:
            parsed_days = int(days) if days is not None else self.PREDICTION_DEFAULT_DAYS
        except (TypeError, ValueError):
            return self.PREDICTION_DEFAULT_DAYS

        if parsed_days < self.PREDICTION_MIN_DAYS:
            return self.PREDICTION_MIN_DAYS
        if parsed_days > self.PREDICTION_MAX_DAYS:
            return self.PREDICTION_MAX_DAYS
        return parsed_days

    def _risk_category_from_score(self, score: float) -> str:
        if score >= 80:
            return "Thriving"
        if score >= 55:
            return "Mild Strain"
        if score >= 30:
            return "Elevated Risk"
        return "Critical Strain"

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
        confidence_level = self._confidence_bucket(signal_confidence)

        quality_requires_retake = signal_quality == "poor" or (
            signal_quality == "ok" and signal_confidence < 0.6
        )

        if retake_required or quality_requires_retake:
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

        if confidence_level in {"low", "medium"}:
            resolved_why = f"Preliminary insight: {resolved_why}"
            if not next_step:
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
                "action_summary": {
                    "status": "Calibrating",
                    "why": "Building your baseline from initial readings.",
                    "next_step": "Stay still and continue collecting readings.",
                    "if_symptoms": self.DEFAULT_IF_SYMPTOMS,
                    "advice_strength": "calibration",
                    "confidence_level": "low",
                    "signal_quality": "unknown",
                    "signal_confidence": 0.0,
                    "drivers": [],
                },
            }
        
        score = self.engine.get_current_score(session_id)
        zone = self.engine.get_current_zone(session_id)
        zone_info = self.ZONE_INFO.get(zone, {"label": "Unknown", "emoji": "⚪"})

        latest_reading = session.readings[-1] if session.readings else None
        components = {
            "heart_rate": {
                "value": latest_reading.heart_rate if latest_reading else 0,
                "score": session.current_scores.heart_rate,
            },
            "hrv": {
                "value": latest_reading.hrv if latest_reading else 0,
                "score": session.current_scores.hrv,
            },
            "spo2": {
                "value": latest_reading.spo2 if latest_reading else 0,
                "score": session.current_scores.spo2,
            },
            "temperature": {
                "value": latest_reading.temperature if latest_reading else 0,
                "score": session.current_scores.temperature,
            },
        }

        baseline = session.baseline or {}
        baseline_data = {
            "resting_bpm": baseline.get("resting_bpm", 70),
            "resting_hrv": baseline.get("resting_hrv", 50),
            "normal_spo2": baseline.get("normal_spo2", 98),
            "normal_temp": baseline.get("normal_temp", 36.5),
        }

        safety_info = session.current_safety.to_dict() if session.current_safety else None
        confidence_level = (safety_info or {}).get("confidence", "medium")
        signal_confidence = self._confidence_score_from_level(confidence_level)
        signal_quality = "unknown"
        
        return {
            "status": "scored",
            "score": round(score, 1),
            "zone": zone.value.upper() if zone else "UNKNOWN",
            "zone_label": zone_info["label"],
            "zone_emoji": zone_info["emoji"],
            "components": components,
            "baseline": baseline_data,
            "signal_quality": signal_quality,
            "signal_confidence": signal_confidence,
            "safety": safety_info,
            "action_summary": self._build_action_summary(
                zone=zone,
                signal_quality=signal_quality,
                signal_confidence=signal_confidence,
                safety_info=safety_info,
                components=components,
            ),
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

            reading = session.readings[i] if i < len(session.readings) else None

            heart_rate_value = reading.heart_rate if reading else 0
            hrv_value = reading.hrv if reading else 0
            spo2_value = reading.spo2 if reading else 0
            temperature_value = reading.temperature if reading else 0

            if not timestamp and reading is not None:
                timestamp = reading.timestamp.isoformat()
            if not timestamp:
                timestamp = datetime.now().isoformat()
            
            history.append({
                "index": i,
                "score": round(score, 1),
                "zone": zone.value.upper(),
                "zone_label": zone_info["label"],
                "timestamp": timestamp,
                "components": {
                    "heart_rate": {
                        "value": heart_rate_value,
                        "score": round(scores_data.get("heart_rate", 0), 1) if isinstance(entry, dict) else 0,
                    },
                    "hrv": {
                        "value": hrv_value,
                        "score": round(scores_data.get("hrv", 0), 1) if isinstance(entry, dict) else 0,
                    },
                    "spo2": {
                        "value": spo2_value,
                        "score": round(scores_data.get("spo2", 0), 1) if isinstance(entry, dict) else 0,
                    },
                    "temperature": {
                        "value": temperature_value,
                        "score": round(scores_data.get("temperature", 0), 1) if isinstance(entry, dict) else 0,
                    },
                },
            })
        
        return history

    # ── Scenario keyword table ────────────────────────────────────────────────
    # Each entry: (keywords, score_impact, hr_delta, hrv_delta, spo2_delta, temp_delta, note)
    _SCENARIO_TABLE = [
        (["stop smoking","quit smoking","no cigarette","quit tobacco"],
         +15.0,-8,+12,+1.5,-0.2,
         "Quitting smoking is the single biggest cardiovascular intervention possible."),
        (["start smoking","smoke again","began smoking"],
         -18.0,+10,-15,-2.0,+0.3,
         "Smoking severely damages vascular endothelium and raises resting heart rate."),
        (["jog","jogging","run","running","cardio","aerobic"],
         +12.0,-5,+10,+0.5,-0.1,
         "Aerobic exercise is one of the most effective cardiovascular interventions."),
        (["gym","lift","weight training","strength training","resistance"],
         +9.0,-4,+8,+0.3,-0.1,
         "Resistance training improves cardiac output and reduces resting HR over time."),
        (["walk","walking","step","steps"],
         +7.0,-3,+6,+0.3,-0.1,
         "Even moderate daily walking significantly lowers cardiovascular risk."),
        (["yoga","pilates","stretch","meditat","mindful","deep breath","relax"],
         +5.5,-3,+6,+0.2,-0.1,
         "Mind-body practices reduce cortisol and support heart rate variability."),
        (["sedentary","sit all day","less active","stop exercising","couch"],
         -8.0,+5,-8,-0.5,+0.1,
         "Prolonged inactivity raises resting HR and reduces HRV."),
        (["oil","fried","fry","greasy","oily","fatty food","junk food","fast food"],
         -7.0,+4,-6,-0.5,+0.1,
         "Excessive saturated/trans fats raise LDL, promote inflammation and arterial stiffness."),
        (["reduce sugar","cut sugar","no sugar","less sugar","stop sugar"],
         +8.5,-4,+7,+0.4,-0.1,
         "Reducing added sugar lowers inflammation and improves metabolic cardiovascular risk."),
        (["sugar","sweet","candy","soda","fizzy","dessert"],
         -6.0,+3,-5,-0.3,+0.1,
         "High sugar intake drives insulin resistance and systemic inflammation."),
        (["reduce salt","less salt","low sodium","cut salt"],
         +5.0,-3,+4,+0.2,0.0,
         "Lower sodium intake directly reduces blood pressure."),
        (["salt","sodium","salty"],
         -5.0,+3,-4,-0.2,0.0,
         "Excess sodium raises blood pressure, increasing cardiac workload."),
        (["vegetable","fruit","fiber","plant-based","salad","whole grain"],
         +6.5,-3,+6,+0.3,-0.1,
         "Plant-rich diets reduce cardiovascular risk through fibre, antioxidants and potassium."),
        (["stop alcohol","quit alcohol","no alcohol","reduce drinking","sober"],
         +6.0,-3,+5,+0.3,-0.1,
         "Reducing alcohol lowers blood pressure and improves HRV within weeks."),
        (["alcohol","drink beer","wine","spirits","liquor"],
         -6.0,+3,-5,-0.3,+0.1,
         "Regular alcohol elevates blood pressure and disrupts heart rhythm."),
        (["water","hydrat","drink more water"],
         +4.0,-2,+3,+0.2,-0.1,
         "Proper hydration supports blood viscosity and cardiac efficiency."),
        (["sleep","rest","insomnia"],
         +7.0,-4,+7,+0.2,-0.1,
         "Adequate sleep is critical for autonomic nervous system recovery (HRV)."),
        (["stress","anxiet","overwork","burnout"],
         -7.0,+5,-8,-0.3,+0.2,
         "Chronic stress elevates cortisol, suppresses HRV and raises resting HR."),
        (["medication","medicine","drug","supplement"],
         0.0,0,0,0.0,0.0,
         "Medication effects vary widely — always consult your doctor about cardiovascular implications."),
    ]

    def _parse_scenario(self, scenario: str):
        sl = scenario.lower()
        for entry in self._SCENARIO_TABLE:
            keywords, si, hr, hrv_d, spo2, temp, note = entry
            if any(kw in sl for kw in keywords):
                return si, float(hr), float(hrv_d), float(spo2), float(temp), note, True
        return 0.0, 0.0, 0.0, 0.0, 0.0, "", False

    def _groq_scenario_review(self, scenario, current_score, current_hr,
                               current_hrv, current_spo2, current_temp, days,
                               score_impact) -> str:
        import os, httpx, asyncio

        api_key = os.environ.get("GROQ_API_KEY", "")
        if not api_key:
            return self._template_scenario_review(scenario, current_score, score_impact, days)

        system = (
            "You are a cardiovascular wellness AI. Provide educational, evidence-based guidance "
            "on how lifestyle factors affect heart health. RULES: Never diagnose. Never name diseases. "
            "Never recommend stopping medication. Frame everything as wellness education. "
            "Be specific and cite approximate timeframes. Keep under 250 words. "
            "Structure in 3 short sections: "
            "1) Impact Summary (2-3 sentences), "
            "2) Expected Vital Changes (bullet list: Heart Rate, HRV, SpO2), "
            "3) Practical Steps (2-3 bullets). No disclaimer."
        )
        direction = "positive" if score_impact >= 0 else "negative"
        user_msg = (
            f'User question: "{scenario}"\n\n'
            f"Current wellness: Score {current_score:.0f}/100 | "
            f"HR {current_hr:.0f} bpm | HRV {current_hrv:.0f} ms | "
            f"SpO₂ {current_spo2:.0f}% | Temp {current_temp:.1f}°C\n"
            f"Projection horizon: {days} days | "
            f"Estimated impact: {direction} ({abs(score_impact):.1f} pts)\n\n"
            "Write a comprehensive cardiovascular wellness review."
        )

        async def _call():
            async with httpx.AsyncClient(timeout=15.0) as client:
                r = await client.post(
                    "https://api.groq.com/openai/v1/chat/completions",
                    headers={"Authorization": f"Bearer {api_key}"},
                    json={
                        "model": "llama-3.1-8b-instant",
                        "messages": [
                            {"role": "system", "content": system},
                            {"role": "user", "content": user_msg},
                        ],
                        "max_tokens": 450,
                        "temperature": 0.5,
                    },
                )
                r.raise_for_status()
                return r.json()["choices"][0]["message"]["content"].strip()

        try:
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    import concurrent.futures
                    with concurrent.futures.ThreadPoolExecutor() as pool:
                        raw = pool.submit(asyncio.run, _call()).result(timeout=18)
                else:
                    raw = loop.run_until_complete(_call())
            except RuntimeError:
                raw = asyncio.run(_call())

            validated = validate_llm_output(raw)
            return validated if validated else self._template_scenario_review(scenario, current_score, score_impact, days)
        except Exception as exc:
            print(f"[CardioTwin] Scenario LLM failed: {exc}")
            return self._template_scenario_review(scenario, current_score, score_impact, days)

    def _template_scenario_review(self, scenario, current_score, score_impact, days) -> str:
        d = "improve" if score_impact > 0 else ("worsen" if score_impact < 0 else "not significantly change")
        m = "significantly" if abs(score_impact) >= 10 else ("moderately" if abs(score_impact) >= 5 else "mildly")
        return (
            f"**Impact Summary**\n"
            f"Based on cardiovascular research, this change is expected to {m} {d} your heart health "
            f"over {days} days.\n\n"
            f"**Expected Vital Changes**\n"
            f"- Heart Rate: {'↓ likely to decrease' if score_impact > 0 else '↑ may increase'}\n"
            f"- HRV: {'↑ likely to improve' if score_impact > 0 else '↓ may decrease'}\n"
            f"- SpO₂: {'Stable to slightly improved' if score_impact > 0 else 'Stable'}\n\n"
            f"**Practical Steps**\n"
            f"- Track your vitals daily to observe changes\n"
            f"- Combine this with adequate sleep (7-8 hrs) for best effect\n"
            f"- Consult a healthcare professional before major lifestyle changes"
        )

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
        prediction_days = self._normalize_prediction_days(days)
        horizon_hours = prediction_days * 24

        current_score = self.engine.get_current_score(session_id)

        if current_score is None or current_score == 0:
            return {
                "status": "error",
                "message": "Not enough data for projection",
            }

        # Project risk using engine
        projection = self.engine.project_risk(session_id, hours_ahead=horizon_hours)
        prediction_source = "engine_projection"
        confidence = 0.35
        trend_direction = "unknown"
        best_case_score = None
        worst_case_score = None

        if not projection:
            projected_score = max(0.0, current_score - (prediction_days * 0.1))
            prediction_source = "fallback_trend"
            best_case_score = min(100.0, projected_score + 5.0)
            worst_case_score = max(0.0, projected_score - 5.0)
            projected_score_average = projected_score
        else:
            horizon_index = max(0, min(len(projection.projected_scores) - 1, horizon_hours - 1))
            projected_score = projection.projected_scores[horizon_index]
            projected_score_average = sum(projection.projected_scores) / len(projection.projected_scores)
            confidence = projection.trend.confidence if hasattr(projection.trend, "confidence") else 0.7
            trend_direction = projection.trend.value if hasattr(projection.trend, "value") else str(projection.trend)
            best_case_score = projection.best_case_score
            worst_case_score = projection.worst_case_score

        # ── Get current vitals from latest reading for projection base ──
        current_hr, current_hrv, current_spo2, current_temp = 72.0, 50.0, 97.0, 36.6
        try:
            session = self.engine.get_session(session_id)
            if session and session.readings:
                r = session.readings[-1]
                current_hr = float(r.heart_rate) if r.heart_rate else current_hr
                current_hrv = float(r.hrv) if r.hrv else current_hrv
                current_spo2 = float(r.spo2) if r.spo2 else current_spo2
                current_temp = float(r.temperature) if r.temperature else current_temp
        except Exception:
            pass

        # ── Parse scenario ──
        scenario_impact = 0.0
        scenario_note = ""
        hr_delta = 0.0
        hrv_delta = 0.0
        spo2_delta = 0.0
        temp_delta = 0.0
        ai_review = None

        if scenario:
            si, hr_d, hrv_d, spo2_d, temp_d, note, matched = self._parse_scenario(scenario)
            if matched:
                scenario_impact = si
                hr_delta = hr_d
                hrv_delta = hrv_d
                spo2_delta = spo2_d
                temp_delta = temp_d
                scenario_note = note
            else:
                # Unknown scenario — still try LLM, use zero deltas
                scenario_note = f"Scenario: {scenario}"

            # Apply gradual impact based on time frame
            time_factor = min(prediction_days / 90.0, 1.0)
            projected_score = min(100.0, projected_score + (scenario_impact * time_factor))

            # Generate AI review
            ai_review = self._groq_scenario_review(
                scenario=scenario,
                current_score=float(current_score),
                current_hr=current_hr,
                current_hrv=current_hrv,
                current_spo2=current_spo2,
                current_temp=current_temp,
                days=prediction_days,
                score_impact=scenario_impact,
            )

        # ── Score delta ──
        score_delta = current_score - projected_score
        hr_increase = score_delta * 0.15  # approximate correlation

        # ── Build projected vitals ──
        time_factor = min(prediction_days / 90.0, 1.0)
        projected_hr = round(current_hr + hr_delta * time_factor, 1)
        projected_hrv = round(max(0.0, current_hrv + hrv_delta * time_factor), 1)
        projected_spo2 = round(min(100.0, max(70.0, current_spo2 + spo2_delta * time_factor)), 1)
        projected_temp = round(current_temp + temp_delta * time_factor, 1)

        response = {
            "current_score": round(float(current_score), 1),
            "projected_score": round(float(projected_score), 1),
            "projected_resting_hr_increase_bpm": round(float(hr_increase), 1),
            "current_risk_category": self._risk_category_from_score(float(current_score)),
            "projected_risk_category": self._risk_category_from_score(float(projected_score)),
            "prediction_source": prediction_source,
            "prediction_horizon_days": prediction_days,
            "prediction_horizon_hours": horizon_hours,
            "confidence": round(float(confidence), 2),
            "best_case_score": round(float(best_case_score), 1) if best_case_score is not None else None,
            "worst_case_score": round(float(worst_case_score), 1) if worst_case_score is not None else None,
            "projected_score_average": round(float(projected_score_average), 1),
            "trend_direction": trend_direction,
            "disclaimer": "Statistical projection only. Not a medical diagnosis.",
            "current_vitals": {
                "bpm": current_hr,
                "hrv": current_hrv,
                "spo2": current_spo2,
                "temperature": current_temp,
            },
            "projected_vitals": {
                "bpm": projected_hr,
                "hrv": projected_hrv,
                "spo2": projected_spo2,
                "temperature": projected_temp,
            },
            "projected_vitals_delta": {
                "bpm": round(hr_delta * time_factor, 1),
                "hrv": round(hrv_delta * time_factor, 1),
                "spo2": round(spo2_delta * time_factor, 1),
                "temperature": round(temp_delta * time_factor, 1),
            },
        }

        if scenario_note:
            response["scenario_note"] = scenario_note
        if ai_review:
            response["ai_review"] = ai_review

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
