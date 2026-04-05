"""
Safety System Module
====================

Non-negotiable safety guardrails for health monitoring.

Features:
    - Red-flag symptom detection and escalation
    - Allowed interventions list (what nudges can recommend)
    - LLM output validation (ensure Groq never diagnoses)
    - Seek-help escalation logic
    - Confidence-aware alert severity reduction

This module gates ALL outputs before they reach the user.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta


class EscalationLevel(Enum):
    """How urgently the user should seek help."""
    NONE = "none"
    SELF_CARE = "self_care"           # User can handle with simple actions
    MONITOR = "monitor"               # Watch closely, retake reading soon
    CONTACT_CAREGIVER = "contact_caregiver"  # Alert caregiver/family
    SEEK_HELP = "seek_help"           # See a doctor soon
    EMERGENCY = "emergency"           # Go to hospital / call emergency


@dataclass
class SafetyCheck:
    """Result of a safety evaluation."""
    is_safe: bool
    escalation: EscalationLevel
    red_flags: List[str]
    safe_next_step: str
    seek_help_message: Optional[str] = None
    confidence: str = "medium"  # low / medium / high
    reason_drivers: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "is_safe": self.is_safe,
            "escalation": self.escalation.value,
            "red_flags": self.red_flags,
            "safe_next_step": self.safe_next_step,
            "seek_help_message": self.seek_help_message,
            "confidence": self.confidence,
            "reason_drivers": self.reason_drivers,
        }


# --- Red Flag Thresholds ---
# These are absolute physiological limits that always trigger escalation
# regardless of baseline or context.

RED_FLAG_THRESHOLDS = {
    "spo2_emergency": 88.0,        # Sustained SpO2 below this = emergency
    "spo2_critical": 90.0,         # SpO2 below this = seek help
    "spo2_warning": 92.0,          # SpO2 below this = contact caregiver
    "hr_very_high": 150.0,         # Resting HR above this = seek help
    "hr_very_low": 40.0,           # HR below this = seek help
    "hr_high": 120.0,              # Resting HR above this = contact caregiver
    "temp_very_high": 39.5,        # Temp above this = seek help
    "temp_very_low": 35.0,         # Temp below this = seek help
    "temp_high": 38.5,             # Temp above this = contact caregiver
    "hrv_critically_low": 10.0,    # HRV below this = concerning
}

# --- Allowed Interventions ---
# These are the ONLY actions the system (including LLM) may recommend.
# Anything outside this list is blocked.

ALLOWED_INTERVENTIONS = [
    "rest",
    "sit_down",
    "lie_down",
    "deep_breathing",
    "drink_water",
    "take_a_walk",
    "reduce_activity",
    "cool_down",
    "warm_up",
    "eat_something",
    "take_medication_as_prescribed",
    "call_caregiver",
    "call_doctor",
    "go_to_hospital",
    "retake_reading",
    "stay_calm",
    "monitor_symptoms",
    "remove_tight_clothing",
    "get_fresh_air",
    "mindful_breathing",
]

# Phrases that indicate the LLM is diagnosing (must be blocked)
BLOCKED_LLM_PHRASES = [
    "you have",
    "you are suffering from",
    "diagnosed with",
    "this indicates",
    "this confirms",
    "you definitely",
    "heart attack",
    "stroke",
    "cardiac arrest",
    "arrhythmia",
    "atrial fibrillation",
    "myocardial",
    "angina",
    "take this medication",
    "take aspirin",
    "prescribe",
    "prescription",
    "stop taking your medication",
]

# Safe disclaimers that should accompany outputs
DISCLAIMERS = {
    "general": "This is a wellness screening tool, not a medical diagnosis. Always consult a healthcare professional for medical advice.",
    "alert": "If you feel unwell, trust your body. Seek medical attention if symptoms persist or worsen.",
    "emergency": "If you are experiencing chest pain, severe shortness of breath, fainting, or confusion, call emergency services immediately.",
    "not_diagnostic": "CardioTwin provides wellness insights only. It is not a substitute for professional medical advice, diagnosis, or treatment.",
}


def check_red_flags(
    heart_rate: float,
    hrv: float,
    spo2: float,
    temperature: float,
    sustained_readings: int = 1,
) -> SafetyCheck:
    """
    Check vitals against absolute red-flag thresholds.

    These checks are independent of baseline — they represent
    physiological limits that always warrant attention.

    Args:
        heart_rate: Current heart rate (BPM)
        hrv: Current HRV (ms)
        spo2: Current SpO2 (%)
        temperature: Current temperature (Celsius)
        sustained_readings: How many consecutive readings show this pattern

    Returns:
        SafetyCheck with escalation level and next steps
    """
    red_flags: List[str] = []
    reason_drivers: List[str] = []
    escalation = EscalationLevel.NONE
    safe_next_step = "Continue monitoring your vitals."
    seek_help_message = None

    # SpO2 checks (most critical)
    if spo2 < RED_FLAG_THRESHOLDS["spo2_emergency"]:
        red_flags.append(f"Very low blood oxygen: {spo2:.0f}%")
        reason_drivers.append("spo2_emergency")
        escalation = EscalationLevel.EMERGENCY
    elif spo2 < RED_FLAG_THRESHOLDS["spo2_critical"]:
        red_flags.append(f"Low blood oxygen: {spo2:.0f}%")
        reason_drivers.append("spo2_critical")
        escalation = max_escalation(escalation, EscalationLevel.SEEK_HELP)
    elif spo2 < RED_FLAG_THRESHOLDS["spo2_warning"]:
        red_flags.append(f"Blood oxygen slightly low: {spo2:.0f}%")
        reason_drivers.append("spo2_warning")
        escalation = max_escalation(escalation, EscalationLevel.CONTACT_CAREGIVER)

    # Heart rate checks
    if heart_rate > RED_FLAG_THRESHOLDS["hr_very_high"]:
        red_flags.append(f"Very high heart rate: {heart_rate:.0f} bpm")
        reason_drivers.append("hr_very_high")
        escalation = max_escalation(escalation, EscalationLevel.SEEK_HELP)
    elif heart_rate < RED_FLAG_THRESHOLDS["hr_very_low"]:
        red_flags.append(f"Very low heart rate: {heart_rate:.0f} bpm")
        reason_drivers.append("hr_very_low")
        escalation = max_escalation(escalation, EscalationLevel.SEEK_HELP)
    elif heart_rate > RED_FLAG_THRESHOLDS["hr_high"]:
        red_flags.append(f"Elevated heart rate: {heart_rate:.0f} bpm")
        reason_drivers.append("hr_high")
        escalation = max_escalation(escalation, EscalationLevel.CONTACT_CAREGIVER)

    # Temperature checks
    if temperature > RED_FLAG_THRESHOLDS["temp_very_high"]:
        red_flags.append(f"High temperature: {temperature:.1f}°C")
        reason_drivers.append("temp_very_high")
        escalation = max_escalation(escalation, EscalationLevel.SEEK_HELP)
    elif temperature < RED_FLAG_THRESHOLDS["temp_very_low"]:
        red_flags.append(f"Low temperature: {temperature:.1f}°C")
        reason_drivers.append("temp_very_low")
        escalation = max_escalation(escalation, EscalationLevel.SEEK_HELP)
    elif temperature > RED_FLAG_THRESHOLDS["temp_high"]:
        red_flags.append(f"Elevated temperature: {temperature:.1f}°C")
        reason_drivers.append("temp_high")
        escalation = max_escalation(escalation, EscalationLevel.CONTACT_CAREGIVER)

    # HRV check
    if hrv < RED_FLAG_THRESHOLDS["hrv_critically_low"] and hrv > 0:
        red_flags.append(f"Very low heart rate variability: {hrv:.0f} ms")
        reason_drivers.append("hrv_critically_low")
        escalation = max_escalation(escalation, EscalationLevel.MONITOR)

    # Sustained readings increase severity
    if sustained_readings >= 3 and escalation.value != "none":
        escalation = escalate_one_level(escalation)

    # Determine safe next step and seek-help message
    if escalation == EscalationLevel.EMERGENCY:
        safe_next_step = "Stop all activity. Sit or lie down immediately. Call emergency services or have someone take you to the nearest hospital."
        seek_help_message = DISCLAIMERS["emergency"]
    elif escalation == EscalationLevel.SEEK_HELP:
        safe_next_step = "Rest immediately. Contact your doctor or visit a clinic today. Do not ignore these readings."
        seek_help_message = "Your readings are outside normal ranges. Please consult a healthcare professional."
    elif escalation == EscalationLevel.CONTACT_CAREGIVER:
        safe_next_step = "Take a break and rest. Let your caregiver or family member know about these readings."
        seek_help_message = "Consider sharing these readings with your caregiver or doctor."
    elif escalation == EscalationLevel.MONITOR:
        safe_next_step = "Rest for a few minutes, then retake your reading. If readings don't improve, contact your caregiver."
    else:
        safe_next_step = "Continue monitoring. Your readings look normal."

    # Determine confidence
    confidence = "high" if sustained_readings >= 3 else "medium" if sustained_readings >= 2 else "low"

    return SafetyCheck(
        is_safe=escalation in (EscalationLevel.NONE, EscalationLevel.SELF_CARE),
        escalation=escalation,
        red_flags=red_flags,
        safe_next_step=safe_next_step,
        seek_help_message=seek_help_message,
        confidence=confidence,
        reason_drivers=reason_drivers,
    )


def validate_llm_output(message: str) -> Tuple[bool, str]:
    """
    Validate LLM-generated nudge text for safety.

    Ensures the LLM hasn't generated diagnostic language,
    medication recommendations, or other unsafe content.

    Args:
        message: The LLM-generated message

    Returns:
        Tuple of (is_valid, cleaned_message_or_reason)
    """
    message_lower = message.lower()

    for blocked in BLOCKED_LLM_PHRASES:
        if blocked in message_lower:
            return False, f"Blocked phrase detected: '{blocked}'"

    # Check message length (too long = probably hallucinating)
    if len(message) > 500:
        return False, "Message too long"

    return True, message


def add_safety_wrapper(
    message: str,
    escalation: EscalationLevel,
    include_disclaimer: bool = True,
) -> str:
    """
    Wrap a nudge message with appropriate safety context.

    Args:
        message: The nudge message
        escalation: Current escalation level
        include_disclaimer: Whether to add disclaimer

    Returns:
        Safety-wrapped message
    """
    parts = [message]

    if escalation in (EscalationLevel.EMERGENCY, EscalationLevel.SEEK_HELP):
        parts.append("")
        parts.append(DISCLAIMERS["emergency"])
    elif escalation == EscalationLevel.CONTACT_CAREGIVER:
        parts.append("")
        parts.append(DISCLAIMERS["alert"])
    elif include_disclaimer:
        parts.append("")
        parts.append(DISCLAIMERS["not_diagnostic"])

    return "\n".join(parts)


def should_alert_caregiver(
    escalation: EscalationLevel,
    zone: str,
    consecutive_orange_count: int = 0,
) -> bool:
    """
    Determine if caregiver should be alerted.

    Args:
        escalation: Current escalation level
        zone: Current zone (GREEN/YELLOW/ORANGE/RED)
        consecutive_orange_count: How many consecutive ORANGE readings

    Returns:
        True if caregiver should be notified
    """
    # Always alert on EMERGENCY or SEEK_HELP
    if escalation in (EscalationLevel.EMERGENCY, EscalationLevel.SEEK_HELP, EscalationLevel.CONTACT_CAREGIVER):
        return True

    # Alert on RED zone
    if zone.upper() == "RED":
        return True

    # Alert on persistent ORANGE (3+ consecutive readings)
    if zone.upper() == "ORANGE" and consecutive_orange_count >= 3:
        return True

    return False


def get_caregiver_message(
    zone: str,
    score: float,
    red_flags: List[str],
    escalation: EscalationLevel,
    user_name: str = "Your contact",
) -> str:
    """
    Generate a message for the caregiver.

    Args:
        zone: Current zone
        score: Current score
        red_flags: List of detected red flags
        escalation: Escalation level
        user_name: Name of the monitored person

    Returns:
        Caregiver-appropriate message
    """
    if escalation == EscalationLevel.EMERGENCY:
        msg = f"URGENT: {user_name} needs immediate help. "
        msg += f"Health score: {score:.0f}/100 (Zone: {zone}). "
        if red_flags:
            msg += f"Concerns: {', '.join(red_flags)}. "
        msg += "Please check on them immediately or call emergency services."
    elif escalation == EscalationLevel.SEEK_HELP:
        msg = f"ALERT: {user_name}'s health readings need attention. "
        msg += f"Score: {score:.0f}/100 (Zone: {zone}). "
        if red_flags:
            msg += f"Issues: {', '.join(red_flags)}. "
        msg += "Please help them see a doctor today."
    else:
        msg = f"Notice: {user_name}'s CardioTwin readings show {zone} zone (Score: {score:.0f}/100). "
        if red_flags:
            msg += f"Noted: {', '.join(red_flags)}. "
        msg += "Please check in on them when you can."

    msg += f"\n\n{DISCLAIMERS['not_diagnostic']}"
    return msg


# --- Alert Throttling ---

class AlertThrottle:
    """
    Prevents alert spam by tracking recent alerts per session.

    Rules:
    - Same alert type: max once per 10 minutes
    - Any alert: max 5 per 30 minutes
    - CRITICAL/EMERGENCY: never throttled
    """

    def __init__(
        self,
        same_type_cooldown_minutes: int = 10,
        max_alerts_per_window: int = 5,
        window_minutes: int = 30,
    ):
        self.same_type_cooldown = timedelta(minutes=same_type_cooldown_minutes)
        self.max_alerts = max_alerts_per_window
        self.window = timedelta(minutes=window_minutes)
        # session_id -> list of (alert_type, timestamp)
        self._history: Dict[str, List[Tuple[str, datetime]]] = {}

    def should_send(self, session_id: str, alert_type: str, severity: str) -> bool:
        """Check if an alert should be sent or throttled."""
        # Never throttle critical/emergency
        if severity in ("critical", "emergency"):
            self._record(session_id, alert_type)
            return True

        now = datetime.now()
        history = self._history.get(session_id, [])

        # Clean old entries
        history = [(t, ts) for t, ts in history if now - ts < self.window]
        self._history[session_id] = history

        # Check same-type cooldown
        for prev_type, prev_time in reversed(history):
            if prev_type == alert_type and now - prev_time < self.same_type_cooldown:
                return False

        # Check total alert count in window
        if len(history) >= self.max_alerts:
            return False

        self._record(session_id, alert_type)
        return True

    def _record(self, session_id: str, alert_type: str):
        if session_id not in self._history:
            self._history[session_id] = []
        self._history[session_id].append((alert_type, datetime.now()))


# --- Signal Quality Gating ---

def assess_signal_quality(
    heart_rate: float,
    hrv: float,
    spo2: float,
    temperature: float,
) -> Tuple[str, float, List[str]]:
    """
    Assess reading signal quality.

    Returns quality rating, confidence score, and any issues.

    Args:
        heart_rate: BPM reading
        hrv: HRV reading
        spo2: SpO2 reading
        temperature: Temperature reading

    Returns:
        Tuple of (quality: good/ok/poor, confidence: 0-1, issues: list)
    """
    issues: List[str] = []
    confidence = 1.0

    # Check for implausible values (likely sensor error)
    if heart_rate <= 0 or heart_rate > 250:
        issues.append("Heart rate reading appears invalid")
        confidence -= 0.4
    if hrv < 0 or hrv > 300:
        issues.append("HRV reading appears invalid")
        confidence -= 0.3
    if spo2 <= 0 or spo2 > 100:
        issues.append("SpO2 reading appears invalid")
        confidence -= 0.4
    if temperature < 30 or temperature > 43:
        issues.append("Temperature reading appears invalid")
        confidence -= 0.3

    # Check for suspiciously round/repeated values
    if heart_rate == 0 and spo2 == 0:
        issues.append("Multiple zero readings suggest sensor contact issue")
        confidence -= 0.5

    confidence = max(0.0, min(1.0, confidence))

    if confidence >= 0.8:
        quality = "good"
    elif confidence >= 0.5:
        quality = "ok"
    else:
        quality = "poor"

    return quality, confidence, issues


def should_request_retake(quality: str, confidence: float) -> Tuple[bool, str]:
    """
    Determine if user should retake the reading.

    Args:
        quality: Signal quality (good/ok/poor)
        confidence: Confidence score (0-1)

    Returns:
        Tuple of (should_retake, message)
    """
    if quality == "poor":
        return True, "Your reading quality is low. Please ensure the sensor is properly placed and try again."
    if quality == "ok" and confidence < 0.6:
        return True, "We got a partial reading. Please stay still and retake for better accuracy."
    return False, ""


# --- Baseline Confidence ---

def calculate_baseline_confidence(
    readings_count: int,
    calibration_quality: str,
    variance: Optional[Dict[str, float]] = None,
) -> Tuple[str, float]:
    """
    Calculate confidence in the current baseline.

    Used to reduce alert severity when baseline is uncertain.

    Args:
        readings_count: Number of calibration readings
        calibration_quality: Quality string from baseline module
        variance: Variance dict from baseline module

    Returns:
        Tuple of (confidence_level: low/medium/high, score: 0-1)
    """
    score = 0.0

    # Reading count factor
    if readings_count >= 20:
        score += 0.4
    elif readings_count >= 15:
        score += 0.3
    elif readings_count >= 12:
        score += 0.2
    else:
        score += 0.1

    # Quality factor
    quality_scores = {"excellent": 0.3, "good": 0.25, "fair": 0.15, "poor": 0.05}
    score += quality_scores.get(calibration_quality, 0.1)

    # Variance factor (lower is better)
    if variance:
        bpm_var = variance.get("bpm", 10)
        if bpm_var < 3:
            score += 0.3
        elif bpm_var < 6:
            score += 0.2
        elif bpm_var < 10:
            score += 0.1

    score = min(1.0, score)

    if score >= 0.7:
        level = "high"
    elif score >= 0.4:
        level = "medium"
    else:
        level = "low"

    return level, score


def adjust_alert_severity_for_confidence(
    alert_severity: str,
    baseline_confidence: str,
) -> str:
    """
    Reduce alert severity when baseline confidence is low.

    During early calibration, we don't want to scare users
    with alerts based on uncertain baselines.

    Args:
        alert_severity: Original severity (info/warning/urgent/critical)
        baseline_confidence: Baseline confidence (low/medium/high)

    Returns:
        Adjusted severity string
    """
    if baseline_confidence == "high":
        return alert_severity

    # Downgrade by one level for medium confidence
    if baseline_confidence == "medium":
        downgrades = {
            "critical": "urgent",
            "urgent": "warning",
            "warning": "info",
            "info": "info",
        }
        return downgrades.get(alert_severity, alert_severity)

    # Downgrade by two levels for low confidence
    downgrades = {
        "critical": "warning",
        "urgent": "info",
        "warning": "info",
        "info": "info",
    }
    return downgrades.get(alert_severity, alert_severity)


# --- Helpers ---

_ESCALATION_ORDER = [
    EscalationLevel.NONE,
    EscalationLevel.SELF_CARE,
    EscalationLevel.MONITOR,
    EscalationLevel.CONTACT_CAREGIVER,
    EscalationLevel.SEEK_HELP,
    EscalationLevel.EMERGENCY,
]


def max_escalation(a: EscalationLevel, b: EscalationLevel) -> EscalationLevel:
    """Return the higher escalation level."""
    return a if _ESCALATION_ORDER.index(a) >= _ESCALATION_ORDER.index(b) else b


def escalate_one_level(level: EscalationLevel) -> EscalationLevel:
    """Escalate by one level (capped at EMERGENCY)."""
    idx = _ESCALATION_ORDER.index(level)
    if idx < len(_ESCALATION_ORDER) - 1:
        return _ESCALATION_ORDER[idx + 1]
    return level
