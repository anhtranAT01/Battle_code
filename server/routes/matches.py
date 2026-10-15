"""Match challenge creation, listing, details, and replay routes."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import or_
from sqlalchemy.orm import Session

from server.database import get_db
from server.models import Bot, Match, TournamentSetting, User
from server.queue import execute_match_job
from server.routes.auth import get_current_user
from server.tournament import is_ffa_portal_open
from server.tournament_config import load_tournament_config

router = APIRouter(prefix="/matches", tags=["matches"])

# In-memory replay cache for blazing-fast 0ms replay loading
REPLAY_CACHE: Dict[int, Dict[str, Any]] = {}


class ChallengeRequest(BaseModel):
    """Pydantic payload for initiating an FFA challenge match."""
    opponent_id: int


class BossChallengeRequest(BaseModel):
    """Payload for challenging Boss AI bots."""
    difficulty: str = Field(default="hard", description="'easy', 'medium', or 'hard'")


def _is_portal_open_now(db: Session) -> bool:
    """Check if the FFA challenge portal is active based on settings and schedule.

    If TournamentSetting for 'is_portal_open' is explicitly present in the database,
    its value acts as an authoritative master override (True = open, False = closed).
    Only falls back to the time schedule window if no database setting exists.
    """
    setting = db.query(TournamentSetting).filter(TournamentSetting.key == "is_portal_open").first()
    if setting and setting.value is not None:
        return setting.value.strip().lower() in ("true", "1", "yes")

    config = load_tournament_config()
    return is_ffa_portal_open(config)


def _serialize_match(m: Match) -> Dict[str, Any]:
    """Serialize a Match SQLAlchemy entity to a dictionary."""
    is_done = bool(m.replay_path or getattr(m, "replay_data", None) or m.id in REPLAY_CACHE)
    has_err = bool(m.win_reason and "error" in m.win_reason.lower())
    match_status = "completed" if is_done else ("error" if has_err else "running")

    return {
        "id": m.id,
        "status": match_status,
        "player1_id": m.player1_id,
        "player2_id": m.player2_id,
        "player1": {
            "id": m.player1.id,
            "username": m.player1.username,
            "avatar": getattr(m.player1, "avatar", "ninja") or "ninja",
            "rank_tier": getattr(m.player1, "rank_tier", None),
        } if m.player1 else None,
        "player2": {
            "id": m.player2.id,
            "username": m.player2.username,
            "avatar": getattr(m.player2, "avatar", "ninja") or "ninja",
            "rank_tier": getattr(m.player2, "rank_tier", None),
        } if m.player2 else None,
        "bot1_id": m.bot1_id,
        "bot2_id": m.bot2_id,
        "winner_id": m.winner_id,
        "win_reason": m.win_reason,
        "total_turns": m.total_turns,
        "p1_elo_before": m.p1_elo_before,
        "p1_elo_after": m.p1_elo_after,
        "p2_elo_before": m.p2_elo_before,
        "p2_elo_after": m.p2_elo_after,
        "replay_path": m.replay_path,
        "is_bracket": m.is_bracket,
        "created_at": m.created_at.isoformat() if m.created_at else None,
    }



@router.post("/challenge", status_code=status.HTTP_201_CREATED)
def challenge_opponent(
    payload: ChallengeRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Create an FFA challenge match between the current user and target opponent."""
    if not _is_portal_open_now(db):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="FFA portal is currently closed for ranked matches.",
        )

    if current_user.id == payload.opponent_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot challenge yourself.",
        )

    opponent = db.query(User).filter(User.id == payload.opponent_id).first()
    if not opponent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Opponent user not found.",
        )

    # Verify both users have active bot submissions
    bot1 = (
        db.query(Bot)
        .filter(Bot.user_id == current_user.id, Bot.is_active == True)  # noqa: E712
        .first()
    )
    if not bot1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You do not have an active bot uploaded.",
        )

    bot2 = (
        db.query(Bot)
        .filter(Bot.user_id == opponent.id, Bot.is_active == True)  # noqa: E712
        .first()
    )
    if not bot2:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Opponent does not have an active bot uploaded.",
        )

    # Create pending Match record
    match = Match(
        player1_id=current_user.id,
        player2_id=opponent.id,
        bot1_id=bot1.id,
        bot2_id=bot2.id,
        p1_elo_before=current_user.elo,
        p2_elo_before=opponent.elo,
        is_bracket=False,
    )
    db.add(match)
    db.commit()
    db.refresh(match)

    # Queue async execution in background tasks
    background_tasks.add_task(
        execute_match_job,
        match.id,
        bot1.filepath,
        bot2.filepath,
    )

    return {
        "match_id": match.id,
        "status": "queued",
        "player1_id": current_user.id,
        "player2_id": opponent.id,
    }


@router.post("/boss", status_code=status.HTTP_201_CREATED)
def challenge_boss(
    payload: BossChallengeRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Challenge one of the built-in AI Bosses (Easy, Medium, Hard Alpha-Beta)."""
    user_bot = (
        db.query(Bot)
        .filter(Bot.user_id == current_user.id, Bot.is_active == True)  # noqa: E712
        .first()
    )
    if not user_bot:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Bạn chưa có bot nào đang hoạt động. Hãy tải lên hoặc kích hoạt bot trước khi đấu Boss!",
        )

    diff = payload.difficulty.lower().strip()
    repo_root = Path(__file__).resolve().parent.parent.parent
    if diff == "easy":
        boss_name = "🤖 Tập sự AI (Novice)"
        boss_file = repo_root / "starter_kit" / "bot_template.py"
        boss_avatar = "mecha"
        boss_elo = 1000
    elif diff == "medium":
        boss_name = "🦊 Bậc thầy Heuristic"
        boss_file = repo_root / "starter_kit" / "heuristic_bot.py"
        boss_avatar = "kitsune"
        boss_elo = 1400
    else:  # hard
        boss_name = "🐉 Trùm Cuối Alpha-Beta (Nightmare)"
        boss_file = repo_root / "starter_kit" / "boss_ai.py"
        boss_avatar = "dragon"
        boss_elo = 1800

    boss_user = db.query(User).filter(User.username == boss_name).first()
    if not boss_user:
        boss_user = User(
            username=boss_name,
            password_hash="boss_nopassword",
            is_admin=False,
            elo=boss_elo,
            avatar=boss_avatar,
        )
        db.add(boss_user)
        db.commit()
        db.refresh(boss_user)

    match = Match(
        player1_id=current_user.id,
        player2_id=boss_user.id,
        bot1_id=user_bot.id,
        bot2_id=None,
        p1_elo_before=current_user.elo,
        p2_elo_before=boss_user.elo,
        is_bracket=False,
    )
    db.add(match)
    db.commit()
    db.refresh(match)

    background_tasks.add_task(
        execute_match_job,
        match.id,
        user_bot.filepath,
        str(boss_file.resolve()),
    )

    return {
        "match_id": match.id,
        "status": "queued",
        "boss_name": boss_name,
        "difficulty": diff,
    }


@router.get("", response_model=List[Dict[str, Any]])
def list_matches(
    user_id: Optional[int] = Query(None, description="Filter by participant user ID"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
) -> List[Dict[str, Any]]:
    """List recent matches with pagination and optional user filtering."""
    query = db.query(Match)
    if user_id is not None:
        query = query.filter(or_(Match.player1_id == user_id, Match.player2_id == user_id))

    matches = query.order_by(Match.created_at.desc()).offset(offset).limit(limit).all()
    return [_serialize_match(m) for m in matches]


@router.get("/{match_id}")
def get_match_detail(
    match_id: int,
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Retrieve match execution details and outcome statistics by match ID."""
    match = db.query(Match).filter(Match.id == match_id).first()
    if not match:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Match not found.",
        )
    return _serialize_match(match)


@router.get("/{match_id}/replay")
def get_match_replay(
    match_id: int,
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Retrieve full replay JSON data for visualization."""
    match = db.query(Match).filter(Match.id == match_id).first()
    if not match:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Match not found.",
        )

    # If match is still pending or executing, ensure it is not served from stale cache
    if match.winner_id is None and not match.win_reason and match.total_turns == 0 and not match.replay_path and not getattr(match, "replay_data", None):
        REPLAY_CACHE.pop(match_id, None)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Replay is not yet available or match is still running.",
        )

    # 0. Check in-memory instant cache (0ms)
    if match_id in REPLAY_CACHE:
        return REPLAY_CACHE[match_id]

    # 1. Check replay_data stored directly in database
    if getattr(match, "replay_data", None):
        try:
            parsed = json.loads(match.replay_data)
            REPLAY_CACHE[match_id] = parsed
            return parsed
        except Exception:
            pass

    # 2. Check replay file on disk with resilient multi-path discovery
    candidates: List[Optional[Path]] = []

    if match.replay_path:
        candidates.append(Path(match.replay_path))
        candidates.append(Path(match.replay_path).resolve())

    repo_root = Path(__file__).resolve().parent.parent.parent
    candidates.append(repo_root / "replays" / f"match_{match_id}.json")
    candidates.append(Path("replays").resolve() / f"match_{match_id}.json")
    if match.replay_path:
        candidates.append(Path("replays").resolve() / Path(match.replay_path).name)

    for c in candidates:
        if c and c.is_file():
            try:
                data = json.loads(c.read_text(encoding="utf-8"))
                # Cache into database for future requests
                try:
                    match.replay_data = json.dumps(data, ensure_ascii=False)
                    db.commit()
                except Exception:
                    pass
                return data
            except Exception as exc:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to read replay data: {exc}",
                )

    # 3. Check if match has concluded with an execution error
    if match.win_reason and ("error" in match.win_reason.lower() or "forfeit" in match.win_reason.lower()):
        return {
            "match_id": str(match.id),
            "status": "error",
            "error": match.win_reason,
            "win_reason": match.win_reason,
            "winner": match.winner_id,
            "total_turns": match.total_turns or 0,
            "moves": [],
            "initial_board": [],
        }

    # 4. Match is still queued or running in background
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Replay is not yet available or match is still running.",
    )
