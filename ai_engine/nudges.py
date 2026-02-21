"""
Groq-Powered Nudge System
=========================

Generates personalized health nudges using Groq AI API.
Replaces static templates with dynamic, context-aware messages.

Features:
    - Dynamic message generation based on biometrics
    - Personalized recommendations
    - Culturally-aware messaging for Nigerian context
    - Multi-language support (English, Pidgin, Yoruba, Igbo, Hausa)

Functions:
    - generate_nudge: Create personalized nudge message
    - get_health_insight: Generate detailed health insight
    - format_whatsapp_message: Format for WhatsApp delivery
"""

import os
import json
import asyncio
from typing import Dict, Optional, Any, List
from dataclasses import dataclass
from enum import Enum
import httpx

from .zones import Zone, ZoneInfo


# Groq API configuration
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL = "llama-3.3-70b-versatile"


class Language(Enum):
    """Supported languages for nudges."""
    ENGLISH = "english"
    PIDGIN = "pidgin"
    YORUBA = "yoruba"
    IGBO = "igbo"
    HAUSA = "hausa"


@dataclass
class NudgeConfig:
    """Configuration for nudge generation."""
    language: Language = Language.ENGLISH
    include_emoji: bool = True
    max_length: int = 280  # WhatsApp-friendly length
    tone: str = "supportive"  # supportive, urgent, celebratory
    include_action: bool = True


@dataclass
class Nudge:
    """A generated health nudge."""
    message: str
    title: str
    action: Optional[str]
    severity: str
    zone: str
    language: str
    generated_by: str  # "grok" or "fallback"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "message": self.message,
            "title": self.title,
            "action": self.action,
            "severity": self.severity,
            "zone": self.zone,
            "language": self.language,
            "generated_by": self.generated_by,
        }


# System prompt for Grok
SYSTEM_PROMPT = """You are CardioTwin AI, a friendly health companion embedded in a smartwatch app for Nigerian users.

Your role is to generate short, supportive health nudges based on real-time biometric data.

Guidelines:
- Be warm, encouraging, and culturally aware
- Keep messages concise (under 280 characters for WhatsApp)
- Use the user's health zone (GREEN/YELLOW/ORANGE/RED) to adjust tone
- GREEN: Celebrate and encourage maintenance
- YELLOW: Gently suggest small improvements
- ORANGE: Express concern and recommend specific actions
- RED: Urgent but calm, recommend immediate rest

When given component scores, identify the weakest area and give targeted advice.

Never be alarmist. Always be supportive. You're a health friend, not a doctor."""


# Fallback templates for when API is unavailable
FALLBACK_TEMPLATES = {
    Zone.GREEN: {
        Language.ENGLISH: [
            "🟢 You're doing great! Your heart is in excellent condition. Keep up the healthy habits!",
            "🟢 Thriving! Your cardiovascular health looks fantastic today.",
            "🟢 Excellent! Your vitals show you're taking great care of yourself.",
        ],
        Language.PIDGIN: [
            "🟢 E sweet! Your heart dey kampe well well. Continue like this o!",
            "🟢 Na correct! Your body dey work well. Maintain am!",
        ],
    },
    Zone.YELLOW: {
        Language.ENGLISH: [
            "🟡 A little attention needed. Consider taking a short break and some deep breaths.",
            "🟡 Mild strain detected. How about a quick stretch or a glass of water?",
            "🟡 Your body is asking for a small rest. Take 5 minutes for yourself.",
        ],
        Language.PIDGIN: [
            "🟡 Small attention dey needed. Try rest small and breathe well well.",
            "🟡 E be like say your body wan rest small. Drink water, relax small.",
        ],
    },
    Zone.ORANGE: {
        Language.ENGLISH: [
            "🟠 Elevated stress detected. Please take a break and practice deep breathing for 5 minutes.",
            "🟠 Your body needs rest. Stop current activity and find a calm place to sit.",
            "🟠 Significant strain showing. Prioritize rest now - your health matters.",
        ],
        Language.PIDGIN: [
            "🟠 Wahala dey o. Abeg rest well well, breathe deep for 5 minutes.",
            "🟠 Your body don tire. Stop wetin you dey do, go sit down rest.",
        ],
    },
    Zone.RED: {
        Language.ENGLISH: [
            "🔴 Critical: Please stop all activity immediately and rest. Consider contacting someone if you feel unwell.",
            "🔴 Your body needs immediate rest. Please sit down in a calm environment.",
            "🔴 High strain detected. Stop, rest, and monitor how you feel. Seek help if symptoms persist.",
        ],
        Language.PIDGIN: [
            "🔴 Abeg stop everything now now, go rest. If you no dey feel well, call person.",
            "🔴 E don serious o. Stop, rest, drink water. If e no better, find help.",
        ],
    },
}


def get_api_key() -> Optional[str]:
    """Get Groq API key from environment."""
    return os.environ.get("GROQ_API_KEY")


def _build_prompt(context: Dict[str, Any], config: NudgeConfig) -> str:
    """Build the prompt for Groq based on context."""
    prompt_parts = []
    
    # Zone information
    zone = context.get("zone", "unknown")
    score = context.get("score", 0)
    prompt_parts.append(f"User's current health zone: {zone.upper()} (score: {score:.0f}/100)")
    
    # Zone description
    if "description" in context:
        prompt_parts.append(f"Zone meaning: {context['description']}")
    
    # Component scores if available
    if "components" in context:
        components = context["components"]
        prompt_parts.append(f"\nComponent breakdown:")
        for comp, score in components.items():
            prompt_parts.append(f"  - {comp.upper()}: {score:.0f}/100")
        
        if "weakest_component" in context:
            prompt_parts.append(f"\nWeakest area: {context['weakest_component'].upper()} ({context['weakest_score']:.0f}/100)")
    
    # Transition information if available
    if "transition" in context:
        trans = context["transition"]
        if trans.get("is_significant"):
            prev_zone = trans.get("previous_zone", "unknown")
            prompt_parts.append(f"\nRecent change: Moved from {prev_zone.upper()} to {zone.upper()}")
            prompt_parts.append(f"Direction: {trans.get('direction', 'unknown')}")
    
    # Alert information if available
    if "alerts" in context and context["alerts"]:
        prompt_parts.append(f"\nAlerts detected: {len(context['alerts'])}")
        for alert in context["alerts"][:2]:  # Limit to first 2
            prompt_parts.append(f"  - {alert.get('type', 'unknown')}: {alert.get('message', '')}")
    
    # Language preference
    prompt_parts.append(f"\nLanguage: {config.language.value}")
    
    # Tone
    prompt_parts.append(f"Tone: {config.tone}")
    
    # Instructions
    prompt_parts.append(f"\nGenerate a single health nudge message. Max {config.max_length} characters.")
    if config.include_action:
        prompt_parts.append("Include a specific actionable recommendation.")
    if config.include_emoji:
        prompt_parts.append("Start with the appropriate zone emoji (🟢/🟡/🟠/🔴).")
    
    return "\n".join(prompt_parts)


async def _call_groq_api(
    prompt: str,
    api_key: str,
    timeout: float = 10.0
) -> Optional[str]:
    """
    Call Groq API to generate nudge.
    
    Args:
        prompt: The prompt to send
        api_key: Grok API key
        timeout: Request timeout in seconds
        
    Returns:
        Generated message or None if failed
    """
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    
    payload = {
        "model": GROQ_MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        "max_tokens": 300,
        "temperature": 0.7,
    }
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                GROQ_API_URL,
                headers=headers,
                json=payload,
                timeout=timeout,
            )
            response.raise_for_status()
            
            data = response.json()
            return data["choices"][0]["message"]["content"].strip()
            
    except httpx.TimeoutException:
        return None
    except httpx.HTTPStatusError:
        return None
    except (KeyError, IndexError, json.JSONDecodeError):
        return None
    except Exception:
        return None


def _get_fallback_nudge(zone: Zone, language: Language) -> str:
    """Get a fallback nudge when API is unavailable."""
    import random
    
    zone_templates = FALLBACK_TEMPLATES.get(zone, FALLBACK_TEMPLATES[Zone.YELLOW])
    lang_templates = zone_templates.get(language, zone_templates[Language.ENGLISH])
    
    return random.choice(lang_templates)


def _get_title_for_zone(zone: Zone) -> str:
    """Get appropriate title for zone."""
    titles = {
        Zone.GREEN: "Thriving",
        Zone.YELLOW: "Attention Needed",
        Zone.ORANGE: "Take Care",
        Zone.RED: "Rest Now",
    }
    return titles.get(zone, "Health Update")


def _get_default_action(zone: Zone) -> str:
    """Get default action for zone."""
    actions = {
        Zone.GREEN: "Keep maintaining your healthy habits!",
        Zone.YELLOW: "Take a 5-minute break and drink water.",
        Zone.ORANGE: "Stop current activity and rest for 15 minutes.",
        Zone.RED: "Stop immediately. Rest and seek help if symptoms persist.",
    }
    return actions.get(zone, "Monitor your health.")


async def generate_nudge(
    zone_info: ZoneInfo,
    context: Optional[Dict[str, Any]] = None,
    config: Optional[NudgeConfig] = None,
) -> Nudge:
    """
    Generate a personalized health nudge.
    
    Args:
        zone_info: Current zone information
        context: Additional context (components, transition, alerts)
        config: Nudge configuration
        
    Returns:
        Nudge object with generated message
    """
    config = config or NudgeConfig()
    context = context or {}
    
    # Merge zone info into context
    full_context = {
        "zone": zone_info.zone.value,
        "score": zone_info.score,
        "description": zone_info.description,
        "urgency": zone_info.urgency,
        **context,
    }
    
    # Try Groq API first
    api_key = get_api_key()
    message = None
    generated_by = "fallback"
    
    if api_key:
        prompt = _build_prompt(full_context, config)
        message = await _call_groq_api(prompt, api_key)
        if message:
            generated_by = "groq"
    
    # Fallback to templates if API fails or no key
    if not message:
        message = _get_fallback_nudge(zone_info.zone, config.language)
    
    # Determine action
    action = None
    if config.include_action:
        action = _get_default_action(zone_info.zone)
    
    return Nudge(
        message=message,
        title=_get_title_for_zone(zone_info.zone),
        action=action,
        severity=zone_info.zone.value,
        zone=zone_info.zone.value,
        language=config.language.value,
        generated_by=generated_by,
    )


def generate_nudge_sync(
    zone_info: ZoneInfo,
    context: Optional[Dict[str, Any]] = None,
    config: Optional[NudgeConfig] = None,
) -> Nudge:
    """
    Synchronous wrapper for generate_nudge.
    
    Args:
        zone_info: Current zone information
        context: Additional context
        config: Nudge configuration
        
    Returns:
        Nudge object
    """
    return asyncio.run(generate_nudge(zone_info, context, config))


async def get_health_insight(
    zone_info: ZoneInfo,
    component_scores: Dict[str, float],
    history: Optional[List[float]] = None,
) -> Dict[str, Any]:
    """
    Generate a detailed health insight using Groq.
    
    Args:
        zone_info: Current zone information
        component_scores: Individual component scores
        history: Recent score history
        
    Returns:
        Dictionary with insight, trends, and recommendations
    """
    context = {
        "zone": zone_info.zone.value,
        "score": zone_info.score,
        "components": component_scores,
    }
    
    # Find weakest component
    if component_scores:
        weakest = min(component_scores, key=component_scores.get)
        context["weakest_component"] = weakest
        context["weakest_score"] = component_scores[weakest]
    
    # Add trend if history available
    if history and len(history) >= 3:
        recent_avg = sum(history[-3:]) / 3
        older_avg = sum(history[:3]) / 3 if len(history) >= 6 else history[0]
        
        if recent_avg > older_avg + 5:
            context["trend"] = "improving"
        elif recent_avg < older_avg - 5:
            context["trend"] = "declining"
        else:
            context["trend"] = "stable"
    
    # Try to get Groq insight
    api_key = get_api_key()
    insight_text = None
    
    if api_key:
        prompt = f"""Provide a brief health insight (3-4 sentences) based on:
        
Zone: {context['zone'].upper()} (Score: {zone_info.score:.0f})
Components: {json.dumps(component_scores, indent=2)}
Weakest: {context.get('weakest_component', 'N/A')} ({context.get('weakest_score', 0):.0f})
Trend: {context.get('trend', 'unknown')}

Focus on:
1. What the numbers mean in simple terms
2. The most important area to improve
3. One specific recommendation"""
        
        insight_text = await _call_groq_api(prompt, api_key)
    
    # Fallback insight
    if not insight_text:
        weakest = context.get("weakest_component", "overall health")
        insight_text = f"Your {weakest.upper()} score needs the most attention. "
        insight_text += f"Current zone: {zone_info.zone.value.upper()}. "
        insight_text += zone_info.recommended_action
    
    return {
        "insight": insight_text,
        "zone": zone_info.zone.value,
        "score": zone_info.score,
        "weakest_area": context.get("weakest_component"),
        "trend": context.get("trend", "unknown"),
        "recommendation": zone_info.recommended_action,
    }


def format_whatsapp_message(nudge: Nudge, include_score: bool = True) -> str:
    """
    Format a nudge for WhatsApp delivery.
    
    Args:
        nudge: The nudge to format
        include_score: Whether to include numerical data
        
    Returns:
        WhatsApp-formatted message string
    """
    parts = []
    
    # Title with emoji
    zone_emoji = {"green": "🟢", "yellow": "🟡", "orange": "🟠", "red": "🔴"}
    emoji = zone_emoji.get(nudge.zone, "💚")
    parts.append(f"*{emoji} CardioTwin: {nudge.title}*")
    parts.append("")
    
    # Main message
    parts.append(nudge.message)
    
    # Action if present
    if nudge.action:
        parts.append("")
        parts.append(f"💡 *Action:* {nudge.action}")
    
    return "\n".join(parts)


def get_nudge_for_alert(
    alert_type: str,
    severity: str,
    details: Dict[str, Any],
    language: Language = Language.ENGLISH,
) -> str:
    """
    Get immediate nudge for specific alert.
    
    Args:
        alert_type: Type of alert
        severity: Alert severity
        details: Alert details
        language: Preferred language
        
    Returns:
        Alert-specific nudge message
    """
    # Alert-specific messages
    alert_messages = {
        "spo2_critical": {
            Language.ENGLISH: "🔴 Your blood oxygen is low ({spo2:.0f}%). Sit down, take slow deep breaths. If symptoms persist, seek medical attention.",
            Language.PIDGIN: "🔴 Your blood oxygen don low ({spo2:.0f}%). Sit down, breathe well well. If e no better, find doctor.",
        },
        "hrv_sudden_drop": {
            Language.ENGLISH: "🟠 Sudden stress detected. Your body needs immediate rest. Find a quiet place and take 10 slow, deep breaths.",
            Language.PIDGIN: "🟠 E be like stress don catch you. Rest now now. Find quiet place, breathe slowly.",
        },
        "hr_rapid_increase": {
            Language.ENGLISH: "🟠 Your heart rate has increased significantly. Stop activity, sit down, and rest for at least 10 minutes.",
            Language.PIDGIN: "🟠 Your heart don dey beat fast well well. Stop, sit down, rest for 10 minutes.",
        },
        "zone_downgrade": {
            Language.ENGLISH: "🟡 Your health status has changed. Pay attention to how you're feeling and consider taking a break.",
            Language.PIDGIN: "🟡 Your health status don change. Check how you dey feel, rest small if you need am.",
        },
        "sustained_decline": {
            Language.ENGLISH: "🟠 We've noticed a declining trend. Please prioritize rest and hydration over the next hour.",
            Language.PIDGIN: "🟠 We notice say things dey go down. Rest well, drink water for the next hour.",
        },
    }
    
    # Get message template
    templates = alert_messages.get(alert_type, {})
    template = templates.get(language, templates.get(Language.ENGLISH, ""))
    
    if not template:
        # Generic fallback
        if severity == "critical":
            return "🔴 Please stop activity and rest immediately."
        elif severity == "urgent":
            return "🟠 Your body needs attention. Please take a break."
        else:
            return "🟡 Consider taking a short rest."
    
    # Format with details
    try:
        return template.format(**details)
    except (KeyError, ValueError):
        return template


# Convenience function for quick nudge generation
def quick_nudge(score: float, language: str = "english") -> str:
    """
    Generate a quick nudge from just a score.
    
    Args:
        score: CardioTwin score (0-100)
        language: Language code
        
    Returns:
        Nudge message string
    """
    from .zones import get_zone_info
    
    zone_info = get_zone_info(score)
    lang = Language(language) if language in [l.value for l in Language] else Language.ENGLISH
    
    return _get_fallback_nudge(zone_info.zone, lang)
