"""
Tests for Groq-Powered Nudge System
===================================
"""

import pytest
import asyncio
from unittest.mock import patch, MagicMock, AsyncMock

from ai_engine.nudges import (
    Language,
    NudgeConfig,
    Nudge,
    generate_nudge,
    generate_nudge_sync,
    get_health_insight,
    format_whatsapp_message,
    get_nudge_for_alert,
    quick_nudge,
    _get_fallback_nudge,
    _build_prompt,
    _get_title_for_zone,
    _get_default_action,
    get_api_key,
    FALLBACK_TEMPLATES,
)
from ai_engine.zones import Zone, ZoneInfo, get_zone_info


class TestLanguageEnum:
    """Test Language enum."""
    
    def test_english_value(self):
        """English has correct value."""
        assert Language.ENGLISH.value == "english"
    
    def test_pidgin_value(self):
        """Pidgin has correct value."""
        assert Language.PIDGIN.value == "pidgin"
    
    def test_all_languages_have_values(self):
        """All languages have string values."""
        for lang in Language:
            assert isinstance(lang.value, str)
            assert len(lang.value) > 0


class TestNudgeConfig:
    """Test NudgeConfig dataclass."""
    
    def test_default_values(self):
        """Default config has sensible values."""
        config = NudgeConfig()
        assert config.language == Language.ENGLISH
        assert config.include_emoji is True
        assert config.max_length == 280
        assert config.tone == "supportive"
        assert config.include_action is True
    
    def test_custom_values(self):
        """Can set custom values."""
        config = NudgeConfig(
            language=Language.PIDGIN,
            include_emoji=False,
            max_length=160,
            tone="urgent"
        )
        assert config.language == Language.PIDGIN
        assert config.include_emoji is False
        assert config.max_length == 160


class TestNudgeDataclass:
    """Test Nudge dataclass."""
    
    def test_nudge_to_dict(self):
        """Nudge converts to dictionary."""
        nudge = Nudge(
            message="Test message",
            title="Test Title",
            action="Test action",
            severity="yellow",
            zone="yellow",
            language="english",
            generated_by="fallback"
        )
        d = nudge.to_dict()
        
        assert d["message"] == "Test message"
        assert d["title"] == "Test Title"
        assert d["action"] == "Test action"
        assert d["severity"] == "yellow"
        assert d["generated_by"] == "fallback"


class TestFallbackNudges:
    """Test fallback nudge templates."""
    
    def test_fallback_for_green_english(self):
        """GREEN zone has English fallbacks."""
        nudge = _get_fallback_nudge(Zone.GREEN, Language.ENGLISH)
        assert "🟢" in nudge
        assert len(nudge) > 20
    
    def test_fallback_for_yellow_english(self):
        """YELLOW zone has English fallbacks."""
        nudge = _get_fallback_nudge(Zone.YELLOW, Language.ENGLISH)
        assert "🟡" in nudge
    
    def test_fallback_for_orange_english(self):
        """ORANGE zone has English fallbacks."""
        nudge = _get_fallback_nudge(Zone.ORANGE, Language.ENGLISH)
        assert "🟠" in nudge
    
    def test_fallback_for_red_english(self):
        """RED zone has English fallbacks."""
        nudge = _get_fallback_nudge(Zone.RED, Language.ENGLISH)
        assert "🔴" in nudge
    
    def test_fallback_for_pidgin(self):
        """Pidgin fallbacks work."""
        nudge = _get_fallback_nudge(Zone.GREEN, Language.PIDGIN)
        assert len(nudge) > 10
        # Pidgin should have characteristic words
        assert any(word in nudge.lower() for word in ["dey", "well", "o", "kampe", "na"])
    
    def test_fallback_falls_back_to_english(self):
        """Unsupported language falls back to English."""
        # Hausa may not have all templates, should fall back
        nudge = _get_fallback_nudge(Zone.GREEN, Language.HAUSA)
        assert len(nudge) > 10
    
    def test_all_zones_have_templates(self):
        """All zones have fallback templates."""
        for zone in Zone:
            assert zone in FALLBACK_TEMPLATES
            templates = FALLBACK_TEMPLATES[zone]
            assert Language.ENGLISH in templates
            assert len(templates[Language.ENGLISH]) >= 1


class TestTitleAndAction:
    """Test title and action helpers."""
    
    def test_green_title(self):
        """GREEN zone has appropriate title."""
        title = _get_title_for_zone(Zone.GREEN)
        assert "Thriving" in title
    
    def test_red_title(self):
        """RED zone has appropriate title."""
        title = _get_title_for_zone(Zone.RED)
        assert "Rest" in title
    
    def test_green_action(self):
        """GREEN zone has appropriate action."""
        action = _get_default_action(Zone.GREEN)
        assert "maintain" in action.lower()
    
    def test_red_action(self):
        """RED zone has urgent action."""
        action = _get_default_action(Zone.RED)
        assert any(word in action.lower() for word in ["stop", "rest", "help"])


class TestBuildPrompt:
    """Test prompt building."""
    
    def test_includes_zone(self):
        """Prompt includes zone."""
        context = {"zone": "green", "score": 85}
        config = NudgeConfig()
        prompt = _build_prompt(context, config)
        
        assert "GREEN" in prompt
        assert "85" in prompt
    
    def test_includes_components(self):
        """Prompt includes component breakdown."""
        context = {
            "zone": "yellow",
            "score": 65,
            "components": {"hr": 70, "hrv": 50, "spo2": 90, "temp": 80},
            "weakest_component": "hrv",
            "weakest_score": 50,
        }
        config = NudgeConfig()
        prompt = _build_prompt(context, config)
        
        assert "HRV" in prompt
        assert "50" in prompt
        assert "weakest" in prompt.lower()
    
    def test_includes_language(self):
        """Prompt includes language preference."""
        context = {"zone": "yellow", "score": 65}
        config = NudgeConfig(language=Language.PIDGIN)
        prompt = _build_prompt(context, config)
        
        assert "pidgin" in prompt.lower()
    
    def test_includes_max_length(self):
        """Prompt includes max length."""
        context = {"zone": "green", "score": 85}
        config = NudgeConfig(max_length=160)
        prompt = _build_prompt(context, config)
        
        assert "160" in prompt


class TestGenerateNudgeWithoutAPI:
    """Test nudge generation without API key."""
    
    @pytest.fixture
    def mock_no_api_key(self):
        """Mock environment without API key."""
        with patch.dict('os.environ', {}, clear=True):
            yield
    
    @pytest.mark.asyncio
    async def test_generates_fallback_without_key(self, mock_no_api_key):
        """Generates fallback nudge when no API key."""
        zone_info = get_zone_info(85)
        nudge = await generate_nudge(zone_info)
        
        assert nudge is not None
        assert nudge.generated_by == "fallback"
        assert len(nudge.message) > 10
    
    @pytest.mark.asyncio
    async def test_fallback_matches_zone(self, mock_no_api_key):
        """Fallback nudge matches zone."""
        zone_info = get_zone_info(40)  # ORANGE
        nudge = await generate_nudge(zone_info)
        
        assert nudge.zone == "orange"
        assert "🟠" in nudge.message
    
    @pytest.mark.asyncio
    async def test_includes_action(self, mock_no_api_key):
        """Nudge includes action when configured."""
        zone_info = get_zone_info(70)
        config = NudgeConfig(include_action=True)
        nudge = await generate_nudge(zone_info, config=config)
        
        assert nudge.action is not None
        assert len(nudge.action) > 5
    
    @pytest.mark.asyncio
    async def test_respects_language(self, mock_no_api_key):
        """Nudge respects language preference."""
        zone_info = get_zone_info(85)
        config = NudgeConfig(language=Language.PIDGIN)
        nudge = await generate_nudge(zone_info, config=config)
        
        assert nudge.language == "pidgin"


class TestGenerateNudgeSync:
    """Test synchronous nudge generation."""
    
    def test_sync_wrapper_works(self):
        """Sync wrapper generates nudge."""
        with patch.dict('os.environ', {}, clear=True):
            zone_info = get_zone_info(75)
            nudge = generate_nudge_sync(zone_info)
            
            assert nudge is not None
            assert nudge.message is not None


class TestFormatWhatsappMessage:
    """Test WhatsApp formatting."""
    
    def test_includes_title(self):
        """Formatted message includes title."""
        nudge = Nudge(
            message="Test message",
            title="Test Title",
            action="Test action",
            severity="yellow",
            zone="yellow",
            language="english",
            generated_by="fallback"
        )
        formatted = format_whatsapp_message(nudge)
        
        assert "*" in formatted  # WhatsApp bold markers
        assert "Test Title" in formatted
    
    def test_includes_emoji(self):
        """Formatted message includes zone emoji."""
        nudge = Nudge(
            message="Test",
            title="Title",
            action="Action",
            severity="green",
            zone="green",
            language="english",
            generated_by="fallback"
        )
        formatted = format_whatsapp_message(nudge)
        
        assert "🟢" in formatted
    
    def test_includes_action(self):
        """Formatted message includes action."""
        nudge = Nudge(
            message="Message",
            title="Title",
            action="Take a break",
            severity="yellow",
            zone="yellow",
            language="english",
            generated_by="fallback"
        )
        formatted = format_whatsapp_message(nudge)
        
        assert "Take a break" in formatted
        assert "Action" in formatted


class TestGetNudgeForAlert:
    """Test alert-specific nudges."""
    
    def test_spo2_critical_message(self):
        """SpO2 critical has specific message."""
        msg = get_nudge_for_alert(
            "spo2_critical",
            "critical",
            {"spo2": 89},
            Language.ENGLISH
        )
        
        assert "89" in msg
        assert "oxygen" in msg.lower()
        assert "🔴" in msg
    
    def test_hrv_drop_message(self):
        """HRV drop has specific message."""
        msg = get_nudge_for_alert(
            "hrv_sudden_drop",
            "urgent",
            {},
            Language.ENGLISH
        )
        
        assert "stress" in msg.lower() or "rest" in msg.lower()
    
    def test_pidgin_alert_message(self):
        """Alert messages work in Pidgin."""
        msg = get_nudge_for_alert(
            "hrv_sudden_drop",
            "urgent",
            {},
            Language.PIDGIN
        )
        
        assert any(word in msg.lower() for word in ["dey", "stress", "rest"])
    
    def test_unknown_alert_fallback(self):
        """Unknown alert type uses fallback."""
        msg = get_nudge_for_alert(
            "unknown_alert_type",
            "warning",
            {},
            Language.ENGLISH
        )
        
        assert len(msg) > 5


class TestQuickNudge:
    """Test quick nudge function."""
    
    def test_quick_nudge_green(self):
        """Quick nudge for high score."""
        msg = quick_nudge(90)
        assert "🟢" in msg
    
    def test_quick_nudge_red(self):
        """Quick nudge for low score."""
        msg = quick_nudge(20)
        assert "🔴" in msg
    
    def test_quick_nudge_pidgin(self):
        """Quick nudge in Pidgin."""
        msg = quick_nudge(85, "pidgin")
        assert len(msg) > 10


class TestGenerateNudgeWithMockedAPI:
    """Test nudge generation with mocked API."""
    
    @pytest.mark.asyncio
    async def test_uses_api_when_available(self):
        """Uses API when key is available."""
        mock_response = "🟢 Test API response message"
        
        with patch.dict('os.environ', {'GROQ_API_KEY': 'test-key'}), \
             patch('ai_engine.nudges._call_groq_api', new_callable=AsyncMock) as mock_api:
            
            mock_api.return_value = mock_response
            
            zone_info = get_zone_info(85)
            nudge = await generate_nudge(zone_info)
            
            assert nudge.generated_by == "groq"
            assert nudge.message == mock_response
    
    @pytest.mark.asyncio
    async def test_falls_back_on_api_failure(self):
        """Falls back to template when API fails."""
        with patch.dict('os.environ', {'GROQ_API_KEY': 'test-key'}), \
             patch('ai_engine.nudges._call_groq_api', new_callable=AsyncMock) as mock_api:
            
            mock_api.return_value = None  # API failed
            
            zone_info = get_zone_info(85)
            nudge = await generate_nudge(zone_info)
            
            assert nudge.generated_by == "fallback"
            assert "🟢" in nudge.message


class TestGetHealthInsight:
    """Test health insight generation."""
    
    @pytest.mark.asyncio
    async def test_returns_insight_without_api(self):
        """Returns insight even without API."""
        with patch.dict('os.environ', {}, clear=True):
            zone_info = get_zone_info(70)
            components = {"hr": 80, "hrv": 50, "spo2": 90, "temp": 85}
            
            result = await get_health_insight(zone_info, components)
            
            assert "insight" in result
            assert "zone" in result
            assert result["zone"] == "yellow"
            assert result["weakest_area"] == "hrv"
    
    @pytest.mark.asyncio
    async def test_calculates_trend(self):
        """Calculates trend from history."""
        with patch.dict('os.environ', {}, clear=True):
            zone_info = get_zone_info(85)
            components = {"hr": 90, "hrv": 80, "spo2": 95, "temp": 90}
            history = [60, 65, 70, 75, 80, 85]  # Improving
            
            result = await get_health_insight(zone_info, components, history)
            
            assert result["trend"] == "improving"


class TestDemoScenarios:
    """Test demo scenario nudge generation."""
    
    @pytest.mark.asyncio
    async def test_resting_state_nudge(self):
        """Resting state generates encouraging nudge."""
        with patch.dict('os.environ', {}, clear=True):
            zone_info = get_zone_info(86)  # GREEN
            nudge = await generate_nudge(zone_info)
            
            assert nudge.zone == "green"
            assert nudge.severity == "green"
            assert "🟢" in nudge.message
    
    @pytest.mark.asyncio
    async def test_post_exercise_nudge(self):
        """Post-exercise generates appropriate nudge."""
        with patch.dict('os.environ', {}, clear=True):
            zone_info = get_zone_info(41)  # ORANGE
            context = {
                "components": {"hr": 30, "hrv": 20, "spo2": 85, "temp": 50},
                "weakest_component": "hrv",
                "weakest_score": 20,
            }
            nudge = await generate_nudge(zone_info, context=context)
            
            assert nudge.zone == "orange"
            assert "🟠" in nudge.message
            assert nudge.action is not None
    
    @pytest.mark.asyncio
    async def test_recovery_nudge(self):
        """Recovery generates supportive nudge."""
        with patch.dict('os.environ', {}, clear=True):
            zone_info = get_zone_info(75)  # YELLOW
            context = {
                "transition": {
                    "is_significant": True,
                    "direction": "improved",
                    "previous_zone": "orange",
                }
            }
            nudge = await generate_nudge(zone_info, context=context)
            
            assert nudge.zone == "yellow"


class TestAPIKeyHandling:
    """Test API key handling."""
    
    def test_get_api_key_when_set(self):
        """Returns API key when set."""
        with patch.dict('os.environ', {'GROQ_API_KEY': 'test-key-123'}):
            assert get_api_key() == 'test-key-123'
    
    def test_get_api_key_when_not_set(self):
        """Returns None when not set."""
        with patch.dict('os.environ', {}, clear=True):
            assert get_api_key() is None
