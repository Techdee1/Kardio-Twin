"""
Tests for Zone Classification Module
====================================
"""

import pytest
from ai_engine.zones import (
    Zone,
    ZoneInfo,
    ZoneTransition,
    classify_zone,
    get_zone_metadata,
    get_zone_info,
    get_zone_boundaries,
    detect_zone_transition,
    get_zone_context,
    get_zone_trend,
    format_zone_display,
    is_zone_critical,
    is_zone_healthy,
)


class TestClassifyZone:
    """Test zone classification logic."""
    
    def test_green_zone_at_100(self):
        """Score 100 -> GREEN."""
        assert classify_zone(100) == Zone.GREEN
    
    def test_green_zone_at_80(self):
        """Score 80 -> GREEN (boundary)."""
        assert classify_zone(80) == Zone.GREEN
    
    def test_green_zone_at_85(self):
        """Score 85 -> GREEN."""
        assert classify_zone(85) == Zone.GREEN
    
    def test_yellow_zone_at_79(self):
        """Score 79 -> YELLOW (boundary)."""
        assert classify_zone(79) == Zone.YELLOW
    
    def test_yellow_zone_at_55(self):
        """Score 55 -> YELLOW (boundary)."""
        assert classify_zone(55) == Zone.YELLOW
    
    def test_yellow_zone_at_65(self):
        """Score 65 -> YELLOW."""
        assert classify_zone(65) == Zone.YELLOW
    
    def test_orange_zone_at_54(self):
        """Score 54 -> ORANGE (boundary)."""
        assert classify_zone(54) == Zone.ORANGE
    
    def test_orange_zone_at_30(self):
        """Score 30 -> ORANGE (boundary)."""
        assert classify_zone(30) == Zone.ORANGE
    
    def test_orange_zone_at_40(self):
        """Score 40 -> ORANGE."""
        assert classify_zone(40) == Zone.ORANGE
    
    def test_red_zone_at_29(self):
        """Score 29 -> RED (boundary)."""
        assert classify_zone(29) == Zone.RED
    
    def test_red_zone_at_0(self):
        """Score 0 -> RED."""
        assert classify_zone(0) == Zone.RED
    
    def test_red_zone_at_15(self):
        """Score 15 -> RED."""
        assert classify_zone(15) == Zone.RED
    
    def test_clamps_above_100(self):
        """Score > 100 clamped to GREEN."""
        assert classify_zone(110) == Zone.GREEN
    
    def test_clamps_below_0(self):
        """Score < 0 clamped to RED."""
        assert classify_zone(-5) == Zone.RED


class TestGetZoneMetadata:
    """Test zone metadata retrieval."""
    
    def test_green_metadata(self):
        """GREEN zone has correct metadata."""
        meta = get_zone_metadata(Zone.GREEN)
        assert meta["label"] == "Thriving"
        assert meta["emoji"] == "🟢"
        assert meta["urgency"] == 0
    
    def test_yellow_metadata(self):
        """YELLOW zone has correct metadata."""
        meta = get_zone_metadata(Zone.YELLOW)
        assert meta["label"] == "Mild Strain"
        assert meta["emoji"] == "🟡"
        assert meta["urgency"] == 1
    
    def test_orange_metadata(self):
        """ORANGE zone has correct metadata."""
        meta = get_zone_metadata(Zone.ORANGE)
        assert meta["label"] == "Elevated Risk"
        assert meta["emoji"] == "🟠"
        assert meta["urgency"] == 2
    
    def test_red_metadata(self):
        """RED zone has correct metadata."""
        meta = get_zone_metadata(Zone.RED)
        assert meta["label"] == "Critical Strain"
        assert meta["emoji"] == "🔴"
        assert meta["urgency"] == 3
    
    def test_all_zones_have_description(self):
        """All zones have descriptions."""
        for zone in Zone:
            meta = get_zone_metadata(zone)
            assert "description" in meta
            assert len(meta["description"]) > 10
    
    def test_all_zones_have_color_hex(self):
        """All zones have valid hex colors."""
        for zone in Zone:
            meta = get_zone_metadata(zone)
            assert meta["color_hex"].startswith("#")
            assert len(meta["color_hex"]) == 7


class TestGetZoneInfo:
    """Test complete zone info retrieval."""
    
    def test_returns_zone_info_dataclass(self):
        """Returns ZoneInfo dataclass."""
        info = get_zone_info(85)
        assert isinstance(info, ZoneInfo)
    
    def test_includes_score(self):
        """Includes original score."""
        info = get_zone_info(72.5)
        assert info.score == 72.5
    
    def test_green_zone_info(self):
        """GREEN zone info is complete."""
        info = get_zone_info(90)
        assert info.zone == Zone.GREEN
        assert info.label == "Thriving"
        assert info.emoji == "🟢"
        assert info.urgency == 0
    
    def test_red_zone_info(self):
        """RED zone info is complete."""
        info = get_zone_info(20)
        assert info.zone == Zone.RED
        assert info.label == "Critical Strain"
        assert info.urgency == 3


class TestGetZoneBoundaries:
    """Test zone boundary retrieval."""
    
    def test_green_boundaries(self):
        """GREEN zone is 80-100."""
        lower, upper = get_zone_boundaries(Zone.GREEN)
        assert lower == 80
        assert upper == 100
    
    def test_yellow_boundaries(self):
        """YELLOW zone is 55-79."""
        lower, upper = get_zone_boundaries(Zone.YELLOW)
        assert lower == 55
        assert upper == 79
    
    def test_orange_boundaries(self):
        """ORANGE zone is 30-54."""
        lower, upper = get_zone_boundaries(Zone.ORANGE)
        assert lower == 30
        assert upper == 54
    
    def test_red_boundaries(self):
        """RED zone is 0-29."""
        lower, upper = get_zone_boundaries(Zone.RED)
        assert lower == 0
        assert upper == 29


class TestDetectZoneTransition:
    """Test zone transition detection."""
    
    def test_first_reading_no_transition(self):
        """First reading shows no transition."""
        trans = detect_zone_transition(85)
        assert trans.previous_zone is None
        assert trans.current_zone == Zone.GREEN
        assert trans.is_significant is False
    
    def test_same_zone_stable(self):
        """Same zone is not significant."""
        trans = detect_zone_transition(85, previous_score=90)
        assert trans.current_zone == Zone.GREEN
        assert trans.previous_zone == Zone.GREEN
        assert trans.is_significant is False
    
    def test_green_to_yellow_significant(self):
        """GREEN -> YELLOW is significant."""
        trans = detect_zone_transition(75, previous_score=85)
        assert trans.previous_zone == Zone.GREEN
        assert trans.current_zone == Zone.YELLOW
        assert trans.is_significant is True
        assert trans.severity_change == 1  # Got worse
        assert trans.direction == "declined"
    
    def test_yellow_to_green_improvement(self):
        """YELLOW -> GREEN is improvement."""
        trans = detect_zone_transition(85, previous_score=70)
        assert trans.previous_zone == Zone.YELLOW
        assert trans.current_zone == Zone.GREEN
        assert trans.is_significant is True
        assert trans.severity_change == -1  # Got better
        assert trans.direction == "improved"
    
    def test_orange_to_red_critical(self):
        """ORANGE -> RED is critical transition."""
        trans = detect_zone_transition(25, previous_score=40)
        assert trans.previous_zone == Zone.ORANGE
        assert trans.current_zone == Zone.RED
        assert trans.severity_change == 1
    
    def test_red_to_green_recovery(self):
        """RED -> GREEN is major recovery."""
        trans = detect_zone_transition(85, previous_score=20)
        assert trans.severity_change == -3  # Major improvement
        assert trans.direction == "improved"
    
    def test_small_score_change_stable(self):
        """Small score change within zone is stable."""
        trans = detect_zone_transition(86, previous_score=85)
        assert trans.direction == "stable"
    
    def test_accepts_previous_zone_directly(self):
        """Can provide previous zone directly."""
        trans = detect_zone_transition(75, previous_zone=Zone.GREEN)
        assert trans.previous_zone == Zone.GREEN
        assert trans.is_significant is True


class TestGetZoneContext:
    """Test context generation for nudges."""
    
    def test_basic_context(self):
        """Basic context includes zone info."""
        info = get_zone_info(85)
        ctx = get_zone_context(info)
        
        assert ctx["zone"] == "green"
        assert ctx["zone_label"] == "Thriving"
        assert ctx["score"] == 85
        assert ctx["urgency"] == 0
    
    def test_context_with_transition(self):
        """Context includes transition data."""
        info = get_zone_info(70)
        trans = detect_zone_transition(70, previous_score=85)
        ctx = get_zone_context(info, transition=trans)
        
        assert "transition" in ctx
        assert ctx["transition"]["direction"] == "declined"
        assert ctx["transition"]["is_significant"] is True
        assert "transition_message" in ctx
    
    def test_context_with_components(self):
        """Context includes component breakdown."""
        info = get_zone_info(75)
        components = {"hr": 80, "hrv": 60, "spo2": 90, "temp": 85}
        ctx = get_zone_context(info, component_scores=components)
        
        assert "components" in ctx
        assert ctx["weakest_component"] == "hrv"
        assert ctx["weakest_score"] == 60
    
    def test_improvement_transition_message(self):
        """Improvement transition has positive message."""
        info = get_zone_info(85)
        trans = detect_zone_transition(85, previous_score=70)
        ctx = get_zone_context(info, transition=trans)
        
        assert "improvement" in ctx.get("transition_message", "").lower() or \
               "moved to green" in ctx.get("transition_message", "").lower()


class TestGetZoneTrend:
    """Test zone trend analysis."""
    
    def test_empty_scores(self):
        """Empty scores returns unknown."""
        trend = get_zone_trend([])
        assert trend["trend"] == "unknown"
    
    def test_single_score(self):
        """Single score is stable."""
        trend = get_zone_trend([85])
        assert trend["trend"] == "stable"
    
    def test_improving_trend(self):
        """Increasing scores show improving trend."""
        scores = [60, 65, 70, 75, 80]
        trend = get_zone_trend(scores)
        assert trend["trend"] == "improving"
    
    def test_declining_trend(self):
        """Decreasing scores show declining trend."""
        scores = [90, 85, 75, 65, 55]
        trend = get_zone_trend(scores)
        assert trend["trend"] == "declining"
    
    def test_stable_trend(self):
        """Flat scores show stable trend."""
        scores = [80, 81, 79, 80, 80]
        trend = get_zone_trend(scores)
        assert trend["trend"] == "stable"
    
    def test_zone_changes_count(self):
        """Counts zone boundary crossings."""
        scores = [85, 75, 85, 75, 85]  # GREEN-YELLOW-GREEN-YELLOW-GREEN
        trend = get_zone_trend(scores)
        assert trend["zone_changes"] == 4
    
    def test_stable_no_zone_changes(self):
        """No zone changes = stable."""
        scores = [85, 88, 86, 90, 82]  # All GREEN
        trend = get_zone_trend(scores)
        assert trend["stability"] == "stable"
        assert trend["zone_changes"] == 0
    
    def test_volatile_many_changes(self):
        """Many zone changes = volatile."""
        scores = [85, 50, 75, 40, 85]
        trend = get_zone_trend(scores)
        assert trend["stability"] == "volatile"
    
    def test_returns_score_range(self):
        """Returns min/max score range."""
        scores = [60, 70, 80, 65, 75]
        trend = get_zone_trend(scores)
        assert trend["score_range"] == (60, 80)
    
    def test_dominant_zone(self):
        """Identifies most common zone."""
        scores = [85, 86, 87, 70, 88]  # 4 GREEN, 1 YELLOW
        trend = get_zone_trend(scores)
        assert trend["dominant_zone"] == "green"


class TestFormatZoneDisplay:
    """Test zone display formatting."""
    
    def test_format_with_score(self):
        """Format includes score by default."""
        info = get_zone_info(85)
        display = format_zone_display(info)
        assert "🟢" in display
        assert "Thriving" in display
        assert "85" in display
    
    def test_format_without_score(self):
        """Format can exclude score."""
        info = get_zone_info(85)
        display = format_zone_display(info, include_score=False)
        assert "🟢" in display
        assert "Thriving" in display
        assert "85" not in display
    
    def test_format_red_zone(self):
        """RED zone format is correct."""
        info = get_zone_info(20)
        display = format_zone_display(info)
        assert "🔴" in display
        assert "Critical" in display


class TestZoneUtilities:
    """Test utility functions."""
    
    def test_red_is_critical(self):
        """RED zone is critical."""
        assert is_zone_critical(Zone.RED) is True
    
    def test_orange_is_critical(self):
        """ORANGE zone is critical."""
        assert is_zone_critical(Zone.ORANGE) is True
    
    def test_yellow_not_critical(self):
        """YELLOW zone is not critical."""
        assert is_zone_critical(Zone.YELLOW) is False
    
    def test_green_not_critical(self):
        """GREEN zone is not critical."""
        assert is_zone_critical(Zone.GREEN) is False
    
    def test_green_is_healthy(self):
        """GREEN zone is healthy."""
        assert is_zone_healthy(Zone.GREEN) is True
    
    def test_yellow_not_healthy(self):
        """YELLOW zone is not fully healthy."""
        assert is_zone_healthy(Zone.YELLOW) is False
    
    def test_red_not_healthy(self):
        """RED zone is not healthy."""
        assert is_zone_healthy(Zone.RED) is False


class TestDemoScenarios:
    """Test demo scenario zone classifications."""
    
    def test_resting_state_green(self):
        """Resting state score 86 -> GREEN."""
        zone = classify_zone(86)
        assert zone == Zone.GREEN
        info = get_zone_info(86)
        assert info.label == "Thriving"
    
    def test_post_exercise_orange(self):
        """Post-exercise score 41 -> ORANGE."""
        zone = classify_zone(41)
        assert zone == Zone.ORANGE
        info = get_zone_info(41)
        assert info.label == "Elevated Risk"
    
    def test_recovery_transition(self):
        """Recovery transition from ORANGE to YELLOW."""
        trans = detect_zone_transition(60, previous_score=41)
        assert trans.previous_zone == Zone.ORANGE
        assert trans.current_zone == Zone.YELLOW
        assert trans.direction == "improved"
        assert trans.severity_change == -1


class TestEdgeCases:
    """Test edge cases and boundaries."""
    
    def test_exact_boundary_80(self):
        """Score exactly 80 is GREEN."""
        assert classify_zone(80) == Zone.GREEN
    
    def test_just_below_boundary_79_99(self):
        """Score 79.99 rounds to YELLOW."""
        assert classify_zone(79.99) == Zone.YELLOW
    
    def test_exact_boundary_55(self):
        """Score exactly 55 is YELLOW."""
        assert classify_zone(55) == Zone.YELLOW
    
    def test_exact_boundary_30(self):
        """Score exactly 30 is ORANGE."""
        assert classify_zone(30) == Zone.ORANGE
    
    def test_negative_score_handling(self):
        """Negative scores clamp to RED."""
        assert classify_zone(-10) == Zone.RED
        info = get_zone_info(-10)
        assert info.score == -10
        assert info.zone == Zone.RED
    
    def test_over_100_handling(self):
        """Scores over 100 clamp to GREEN."""
        assert classify_zone(150) == Zone.GREEN
