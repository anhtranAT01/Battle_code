"""Unit tests for ranks, glowing avatar frames, and prestige titles."""

from __future__ import annotations

import pytest
from server.models import User
from server.ranks import RANK_TIERS, get_player_title, get_rank_tier


def test_rank_tier_thresholds():
    """Verify tier assignment across Elo thresholds."""
    bronze = get_rank_tier(1050)
    assert bronze["id"] == "bronze"
    assert bronze["frame_class"] == "frame-bronze"
    assert bronze["points_needed"] == 150
    assert bronze["next_threshold"] == 1200
    assert bronze["next_tier_name"] == "Bạc Tinh Anh"

    silver = get_rank_tier(1200)
    assert silver["id"] == "silver"
    assert silver["frame_class"] == "frame-silver"
    assert silver["points_needed"] == 150
    assert silver["next_threshold"] == 1350

    gold = get_rank_tier(1400)
    assert gold["id"] == "gold"
    assert gold["frame_class"] == "frame-gold"
    assert gold["points_needed"] == 100
    assert gold["next_threshold"] == 1500

    diamond = get_rank_tier(1550)
    assert diamond["id"] == "diamond"
    assert diamond["frame_class"] == "frame-diamond"
    assert diamond["points_needed"] == 150
    assert diamond["next_threshold"] == 1700

    mythic = get_rank_tier(1800)
    assert mythic["id"] == "mythic"
    assert mythic["frame_class"] == "frame-mythic"
    assert mythic["points_needed"] == 0
    assert mythic["next_threshold"] is None


def test_player_prestige_titles():
    """Verify honorific player titles based on Elo and victory count."""
    assert "Nhập Môn" in get_player_title(1100, 0)
    assert "Tân Binh" in get_player_title(1150, 3)
    assert "Tinh Anh" in get_player_title(1250, 6)
    assert "Chiến Thuật" in get_player_title(1380, 10)
    assert "Chiến Tướng" in get_player_title(1550, 15)
    assert "Đại Tông Sư" in get_player_title(1750, 20)


def test_user_model_rank_properties():
    """Verify User model integrates rank_tier and title properties seamlessly."""
    user = User(username="hero", elo=1620, wins=12, losses=3, draws=1)
    tier = user.rank_tier
    assert tier["id"] == "diamond"
    assert tier["icon"] == "💎"
    assert tier["frame_class"] == "frame-diamond"
    assert user.title == "⚔️ Chiến Tướng Bất Bại"
