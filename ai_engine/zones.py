"""
Zone Classification Module
==========================

Assigns CardioTwin Score to risk zones and tracks transitions.

Zones:
    - GREEN (80-100): Thriving - Optimal cardiovascular state
    - YELLOW (55-79): Mild Strain - Slight stress response
    - ORANGE (30-54): Elevated Risk - Significant stress
    - RED (0-29): Critical Strain - Immediate rest recommended

Functions:
    - classify_zone: Assign zone based on score
    - get_zone_metadata: Get zone color, label, emoji, description
    - detect_zone_transition: Track zone changes over time
    - get_zone_context: Get contextual info for nudge generation
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional, Dict, Any, List, Tuple


class Zone(Enum):
    """CardioTwin health zones."""
    GREEN = "green"
    YELLOW = "yellow"
    ORANGE = "orange"
    RED = "red"


@dataclass
class ZoneInfo:
    """Complete zone metadata."""
    zone: Zone
    score: float
    label: str
    emoji: str
    color_hex: str
    description: str
    urgency: int  # 0-3, 0=none, 3=critical
    recommended_action: str


# Zone boundary definitions (inclusive lower, exclusive upper except RED)
ZONE_BOUNDARIES = {
    Zone.GREEN: (80, 101),   # 80-100
    Zone.YELLOW: (55, 80),   # 55-79
    Zone.ORANGE: (30, 55),   # 30-54
    Zone.RED: (0, 30),       # 0-29
}


ZONE_METADATA = {
    Zone.GREEN: {
        "label": "Thriving",
        "emoji": "🟢",
        "color_hex": "#22C55E",
        "description": "Optimal cardiovascular state. Your heart is performing excellently.",
        "urgency": 0,
        "recommended_action": "Maintain current lifestyle. Great job!"
    },
    Zone.YELLOW: {
        "label": "Mild Strain",
        "emoji": "🟡",
        "color_hex": "#EAB308",
        "description": "Slight stress response detected. Minor attention recommended.",
        "urgency": 1,
        "recommended_action": "Consider a short break or relaxation technique."
    },
    Zone.ORANGE: {
        "label": "Elevated Risk",
        "emoji": "🟠",
        "color_hex": "#F97316",
        "description": "Significant cardiovascular stress detected. Active intervention suggested.",
        "urgency": 2,
        "recommended_action": "Take a break, practice deep breathing, stay hydrated."
    },
    Zone.RED: {
        "label": "Critical Strain",
        "emoji": "🔴",
        "color_hex": "#EF4444",
        "description": "High cardiovascular strain. Immediate rest strongly recommended.",
        "urgency": 3,
        "recommended_action": "Stop activity immediately. Rest and monitor closely."
    },
}


def classify_zone(score: float) -> Zone:
    """
    Classify a CardioTwin score into a health zone.
    
    Args:
        score: CardioTwin score (0-100)
        
    Returns:
        Zone enum value
        
    Examples:
        >>> classify_zone(85)
        <Zone.GREEN: 'green'>
        >>> classify_zone(60)
        <Zone.YELLOW: 'yellow'>
        >>> classify_zone(40)
        <Zone.ORANGE: 'orange'>
        >>> classify_zone(15)
        <Zone.RED: 'red'>
    """
    # Clamp score to valid range
    score = max(0, min(100, score))
    
    if score >= 80:
        return Zone.GREEN
    elif score >= 55:
        return Zone.YELLOW
    elif score >= 30:
        return Zone.ORANGE
    else:
        return Zone.RED


def get_zone_metadata(zone: Zone) -> Dict[str, Any]:
    """
    Get metadata for a specific zone.
    
    Args:
        zone: Zone enum value
        
    Returns:
        Dictionary with label, emoji, color_hex, description, urgency, recommended_action
    """
    return ZONE_METADATA[zone].copy()


def get_zone_info(score: float) -> ZoneInfo:
    """
    Get complete zone information for a score.
    
    Args:
        score: CardioTwin score (0-100)
        
    Returns:
        ZoneInfo dataclass with all zone metadata
    """
    zone = classify_zone(score)
    metadata = get_zone_metadata(zone)
    
    return ZoneInfo(
        zone=zone,
        score=score,
        label=metadata["label"],
        emoji=metadata["emoji"],
        color_hex=metadata["color_hex"],
        description=metadata["description"],
        urgency=metadata["urgency"],
        recommended_action=metadata["recommended_action"]
    )


def get_zone_boundaries(zone: Zone) -> Tuple[int, int]:
    """
    Get the score boundaries for a zone.
    
    Args:
        zone: Zone enum value
        
    Returns:
        Tuple of (min_score, max_score) inclusive
    """
    lower, upper = ZONE_BOUNDARIES[zone]
    # Adjust for inclusive max
    return (lower, upper - 1 if zone != Zone.GREEN else 100)


@dataclass
class ZoneTransition:
    """Represents a zone transition event."""
    previous_zone: Optional[Zone]
    current_zone: Zone
    previous_score: Optional[float]
    current_score: float
    direction: str  # "improved", "declined", "stable"
    severity_change: int  # Positive = worse, negative = better
    is_significant: bool  # Crossed zone boundary


def detect_zone_transition(
    current_score: float,
    previous_score: Optional[float] = None,
    previous_zone: Optional[Zone] = None
) -> ZoneTransition:
    """
    Detect zone transitions between readings.
    
    Args:
        current_score: Current CardioTwin score
        previous_score: Previous score (optional)
        previous_zone: Previous zone (optional, calculated from previous_score if not provided)
        
    Returns:
        ZoneTransition with transition details
    """
    current_zone = classify_zone(current_score)
    
    # Handle first reading (no previous)
    if previous_score is None and previous_zone is None:
        return ZoneTransition(
            previous_zone=None,
            current_zone=current_zone,
            previous_score=None,
            current_score=current_score,
            direction="stable",
            severity_change=0,
            is_significant=False
        )
    
    # Calculate previous zone if not provided
    if previous_zone is None and previous_score is not None:
        previous_zone = classify_zone(previous_score)
    
    # Determine direction
    if previous_score is not None:
        score_diff = current_score - previous_score
        if score_diff > 2:
            direction = "improved"
        elif score_diff < -2:
            direction = "declined"
        else:
            direction = "stable"
    else:
        direction = "stable"
    
    # Calculate severity change (zone ordinal difference)
    zone_order = [Zone.GREEN, Zone.YELLOW, Zone.ORANGE, Zone.RED]
    if previous_zone is not None:
        current_idx = zone_order.index(current_zone)
        previous_idx = zone_order.index(previous_zone)
        severity_change = current_idx - previous_idx  # Positive = got worse
    else:
        severity_change = 0
    
    # Significant if zone changed
    is_significant = previous_zone != current_zone
    
    return ZoneTransition(
        previous_zone=previous_zone,
        current_zone=current_zone,
        previous_score=previous_score,
        current_score=current_score,
        direction=direction,
        severity_change=severity_change,
        is_significant=is_significant
    )


def get_zone_context(
    zone_info: ZoneInfo,
    transition: Optional[ZoneTransition] = None,
    component_scores: Optional[Dict[str, float]] = None
) -> Dict[str, Any]:
    """
    Get comprehensive context for nudge generation.
    
    This provides all the information the Grok API needs to generate
    personalized, contextual health nudges.
    
    Args:
        zone_info: Current zone information
        transition: Optional zone transition data
        component_scores: Optional dict with hr, hrv, spo2, temp scores
        
    Returns:
        Context dictionary for nudge generation
    """
    context = {
        "zone": zone_info.zone.value,
        "zone_label": zone_info.label,
        "zone_emoji": zone_info.emoji,
        "score": zone_info.score,
        "urgency": zone_info.urgency,
        "description": zone_info.description,
        "default_action": zone_info.recommended_action,
    }
    
    # Add transition context if available
    if transition is not None:
        context["transition"] = {
            "direction": transition.direction,
            "is_significant": transition.is_significant,
            "severity_change": transition.severity_change,
            "previous_zone": transition.previous_zone.value if transition.previous_zone else None,
            "previous_score": transition.previous_score,
        }
        
        # Add transition-specific messaging hints
        if transition.is_significant:
            if transition.severity_change > 0:
                context["transition_message"] = f"Your status moved from {transition.previous_zone.value.upper()} to {zone_info.zone.value.upper()}"
            else:
                context["transition_message"] = f"Great improvement! Moved to {zone_info.zone.value.upper()} zone"
    
    # Add component breakdown if available
    if component_scores is not None:
        context["components"] = component_scores
        
        # Identify weakest component for targeted advice
        if component_scores:
            weakest = min(component_scores, key=component_scores.get)
            context["weakest_component"] = weakest
            context["weakest_score"] = component_scores[weakest]
    
    return context


def get_zone_trend(scores: List[float], window: int = 5) -> Dict[str, Any]:
    """
    Analyze zone trend over recent readings.
    
    Args:
        scores: List of recent CardioTwin scores (newest last)
        window: Number of readings to analyze
        
    Returns:
        Trend analysis dictionary
    """
    if not scores:
        return {"trend": "unknown", "stability": "unknown", "zone_changes": 0}
    
    # Take last N scores
    recent = scores[-window:] if len(scores) >= window else scores
    
    # Classify zones for all readings
    zones = [classify_zone(s) for s in recent]
    
    # Count zone changes
    zone_changes = sum(1 for i in range(1, len(zones)) if zones[i] != zones[i-1])
    
    # Calculate average score change
    if len(recent) >= 2:
        avg_change = (recent[-1] - recent[0]) / len(recent)
        if avg_change > 2:
            trend = "improving"
        elif avg_change < -2:
            trend = "declining"
        else:
            trend = "stable"
    else:
        trend = "stable"
    
    # Assess stability
    if zone_changes == 0:
        stability = "stable"
    elif zone_changes == 1:
        stability = "minor_fluctuation"
    else:
        stability = "volatile"
    
    return {
        "trend": trend,
        "stability": stability,
        "zone_changes": zone_changes,
        "current_zone": zones[-1].value if zones else None,
        "dominant_zone": max(set(zones), key=zones.count).value if zones else None,
        "score_range": (min(recent), max(recent)) if recent else (0, 0),
    }


def format_zone_display(zone_info: ZoneInfo, include_score: bool = True) -> str:
    """
    Format zone information for display.
    
    Args:
        zone_info: ZoneInfo object
        include_score: Whether to include numerical score
        
    Returns:
        Formatted string for UI display
    """
    if include_score:
        return f"{zone_info.emoji} {zone_info.label} ({zone_info.score:.0f})"
    else:
        return f"{zone_info.emoji} {zone_info.label}"


def is_zone_critical(zone: Zone) -> bool:
    """Check if a zone requires immediate attention."""
    return zone in (Zone.RED, Zone.ORANGE)


def is_zone_healthy(zone: Zone) -> bool:
    """Check if a zone indicates healthy status."""
    return zone == Zone.GREEN
