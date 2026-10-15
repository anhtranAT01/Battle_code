"""Rank tiers, glowing avatar frames, and player title utilities."""

from __future__ import annotations
from typing import Any, Dict


RANK_TIERS = {
    "bronze": {
        "id": "bronze",
        "name": "Đồng Kỳ Thủ",
        "name_en": "Bronze Challenger",
        "icon": "🥉",
        "min_elo": 0,
        "max_elo": 1199,
        "color": "#cd7f32",
        "gradient": "linear-gradient(135deg, #b45309, #d97706)",
        "frame_class": "frame-bronze",
        "glow": "rgba(217, 119, 6, 0.4)",
    },
    "silver": {
        "id": "silver",
        "name": "Bạc Tinh Anh",
        "name_en": "Silver Elite",
        "icon": "🥈",
        "min_elo": 1200,
        "max_elo": 1349,
        "color": "#cbd5e1",
        "gradient": "linear-gradient(135deg, #94a3b8, #e2e8f0)",
        "frame_class": "frame-silver",
        "glow": "rgba(203, 213, 225, 0.5)",
    },
    "gold": {
        "id": "gold",
        "name": "Vàng Dũng Sĩ",
        "name_en": "Gold Champion",
        "icon": "🥇",
        "min_elo": 1350,
        "max_elo": 1499,
        "color": "#fbbf24",
        "gradient": "linear-gradient(135deg, #f59e0b, #fbbf24)",
        "frame_class": "frame-gold",
        "glow": "rgba(251, 191, 36, 0.6)",
    },
    "diamond": {
        "id": "diamond",
        "name": "Kim Cương Bậc Thầy",
        "name_en": "Diamond Master",
        "icon": "💎",
        "min_elo": 1500,
        "max_elo": 1699,
        "color": "#38bdf8",
        "gradient": "linear-gradient(135deg, #0284c7, #38bdf8)",
        "frame_class": "frame-diamond",
        "glow": "rgba(56, 189, 248, 0.75)",
    },
    "mythic": {
        "id": "mythic",
        "name": "Thách Đấu Thần Thoại",
        "name_en": "Mythic Grandmaster",
        "icon": "👑",
        "min_elo": 1700,
        "max_elo": 9999,
        "color": "#ec4899",
        "gradient": "linear-gradient(135deg, #f43f5e, #a855f7)",
        "frame_class": "frame-mythic",
        "glow": "rgba(236, 72, 153, 0.85)",
    },
}


def get_rank_tier(elo: int) -> Dict[str, Any]:
    """Calculate the player's rank tier, progress bar, and visual frame styling."""
    if elo >= 1700:
        tier_data = RANK_TIERS["mythic"].copy()
        tier_data.update({
            "next_threshold": None,
            "next_tier_name": None,
            "next_tier_icon": None,
            "points_needed": 0,
            "progress_pct": 100,
        })
        return tier_data

    if elo >= 1500:
        tier_data = RANK_TIERS["diamond"].copy()
        next_thresh = 1700
        progress = int(((elo - 1500) / 200) * 100)
        tier_data.update({
            "next_threshold": next_thresh,
            "next_tier_name": RANK_TIERS["mythic"]["name"],
            "next_tier_icon": RANK_TIERS["mythic"]["icon"],
            "points_needed": max(0, next_thresh - elo),
            "progress_pct": min(100, max(5, progress)),
        })
        return tier_data

    if elo >= 1350:
        tier_data = RANK_TIERS["gold"].copy()
        next_thresh = 1500
        progress = int(((elo - 1350) / 150) * 100)
        tier_data.update({
            "next_threshold": next_thresh,
            "next_tier_name": RANK_TIERS["diamond"]["name"],
            "next_tier_icon": RANK_TIERS["diamond"]["icon"],
            "points_needed": max(0, next_thresh - elo),
            "progress_pct": min(100, max(5, progress)),
        })
        return tier_data

    if elo >= 1200:
        tier_data = RANK_TIERS["silver"].copy()
        next_thresh = 1350
        progress = int(((elo - 1200) / 150) * 100)
        tier_data.update({
            "next_threshold": next_thresh,
            "next_tier_name": RANK_TIERS["gold"]["name"],
            "next_tier_icon": RANK_TIERS["gold"]["icon"],
            "points_needed": max(0, next_thresh - elo),
            "progress_pct": min(100, max(5, progress)),
        })
        return tier_data

    # Bronze
    tier_data = RANK_TIERS["bronze"].copy()
    next_thresh = 1200
    progress = int((elo / 1200) * 100)
    tier_data.update({
        "next_threshold": next_thresh,
        "next_tier_name": RANK_TIERS["silver"]["name"],
        "next_tier_icon": RANK_TIERS["silver"]["icon"],
        "points_needed": max(0, next_thresh - elo),
        "progress_pct": min(100, max(5, progress)),
    })
    return tier_data


def get_player_title(elo: int, wins: int = 0) -> str:
    """Generate prestigious player honorific title based on Elo and victory count."""
    if elo >= 1700:
        return "🔥 Đại Tông Sư Vô Địch"
    if elo >= 1500:
        return "⚔️ Chiến Tướng Bất Bại"
    if elo >= 1350:
        return "🎯 Cao Thủ Chiến Thuật"
    if elo >= 1200 and wins >= 5:
        return "⚡ Kỳ Thủ Tinh Anh"
    if wins >= 3:
        return "🛡️ Tân Binh Tiềm Năng"
    return "🌱 Kỳ Thủ Nhập Môn"
