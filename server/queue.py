"""Asynchronous match execution queue and worker jobs.

This module processes queued matches by executing bot matches in isolated
subprocesses via engine.runner, saving replay logs, updating user Elo ratings
and match statistics, and committing outcomes to the database.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Callable

from engine.runner import run_match, save_replay
from server.database import SessionLocal
from server.models import Bot, Match, TournamentSetting, User
from server.tournament import apply_elo_change, calculate_elo_delta
from server.tournament_config import load_tournament_config

logger = logging.getLogger(__name__)


def resolve_bot_filepath(bot: Bot | None, fallback_path: str) -> str:
    """Resolve a valid, executable file path on disk for a bot.

    If the provided path or bot record does not point to an existing file,
    searches known starter_kit/ and bots/ directories, or restores from source_code.
    """
    repo_root = Path(__file__).resolve().parent.parent

    # 1. Check fallback_path if it exists
    if fallback_path and Path(fallback_path).is_file():
        return str(Path(fallback_path).resolve())

    # 2. Check bot.filepath if available
    if bot and bot.filepath and Path(bot.filepath).is_file():
        return str(Path(bot.filepath).resolve())

    filename = bot.filename if bot else Path(fallback_path).name

    # 3. Check starter_kit by filename
    if filename:
        starter_cand = repo_root / "starter_kit" / filename
        if starter_cand.is_file():
            return str(starter_cand.resolve())

    # 4. Check bots/ directory by filename
    if filename:
        bots_cand = repo_root / "bots" / filename
        if bots_cand.is_file():
            return str(bots_cand.resolve())

    # 5. Check relative to repo_root
    if fallback_path:
        rel_cand = repo_root / fallback_path
        if rel_cand.is_file():
            return str(rel_cand.resolve())

    # 6. Recreate from source_code if available
    if bot and getattr(bot, "source_code", None):
        bots_dir = repo_root / "bots"
        bots_dir.mkdir(parents=True, exist_ok=True)
        safe_name = f"bot_{bot.id}_{Path(filename or 'bot.py').name}"
        recreated = bots_dir / safe_name
        recreated.write_text(bot.source_code, encoding="utf-8")
        return str(recreated.resolve())

    return fallback_path


def _get_setting_value(db, key: str, default: Any, caster: Callable[[str], Any]) -> Any:
    """Retrieve and cast a tournament setting value from the database with a default fallback."""
    try:
        setting = db.query(TournamentSetting).filter(TournamentSetting.key == key).first()
        if setting and setting.value is not None:
            return caster(setting.value)
    except Exception:
        pass
    return default


def execute_match_job(
    match_id: int,
    bot1_path: str,
    bot2_path: str,
    db_factory: Callable[[], Any] | None = None,
) -> dict[str, Any] | None:
    """Execute a queued match job, calculate Elo changes, and save replay artifacts.

    Args:
        match_id: Primary key of the Match record to execute.
        bot1_path: File system path to the Player 1 Python bot script.
        bot2_path: File system path to the Player 2 Python bot script.
        db_factory: Optional callable yielding a SQLAlchemy Session (defaults to SessionLocal).

    Returns:
        The completed match result dictionary, or None if execution failed.
    """
    session_factory = db_factory or SessionLocal
    db = session_factory()

    try:
        match = db.query(Match).filter(Match.id == match_id).first()
        if not match:
            logger.error("Match with id %d not found in database.", match_id)
            return None

        player1 = db.query(User).filter(User.id == match.player1_id).first()
        player2 = db.query(User).filter(User.id == match.player2_id).first()

        if not player1 or not player2:
            logger.error("Players for match %d not found.", match_id)
            return None

        # Load configuration parameters and database overrides
        config = load_tournament_config()
        t_cfg = config.get("tournament", {})
        elo_cfg = t_cfg.get("elo", {})
        rules_cfg = t_cfg.get("match_rules", {})

        multiplier_x = _get_setting_value(
            db, "daily_multiplier_x", elo_cfg.get("daily_multiplier_x", 1.5), float
        )
        k_factor = _get_setting_value(
            db, "k_factor", elo_cfg.get("k_factor", 32), int
        )
        max_turns = _get_setting_value(
            db, "max_turns", rules_cfg.get("max_turns", 200), int
        )
        timeout_seconds = _get_setting_value(
            db, "turn_timeout_seconds", rules_cfg.get("turn_timeout_seconds", 1.0), float
        )

        p1_meta = {
            "id": player1.id,
            "username": player1.username,
            "match_id": match_id,
        }
        p2_meta = {
            "id": player2.id,
            "username": player2.username,
            "match_id": match_id,
        }

        bot1 = db.query(Bot).filter(Bot.id == match.bot1_id).first() if match.bot1_id else None
        bot2 = db.query(Bot).filter(Bot.id == match.bot2_id).first() if match.bot2_id else None

        actual_bot1_path = resolve_bot_filepath(bot1, bot1_path)
        actual_bot2_path = resolve_bot_filepath(bot2, bot2_path)

        # Run match in isolated worker processes
        match_result = run_match(
            bot1_path=actual_bot1_path,
            bot2_path=actual_bot2_path,
            max_turns=max_turns,
            timeout_per_turn=timeout_seconds,
            player1_info=p1_meta,
            player2_info=p2_meta,
        )

        # Save replay JSON
        replays_dir = Path("replays").resolve()
        replays_dir.mkdir(parents=True, exist_ok=True)
        replay_filepath = str(replays_dir / f"match_{match_id}.json")
        save_replay(match_result, replay_filepath)

        # Update Match record
        winner_code = match_result.get("winner")  # 1, 2, or None
        win_reason = match_result.get("win_reason")
        total_turns = match_result.get("total_turns", 0)

        match.replay_path = replay_filepath
        match.replay_data = json.dumps(match_result, ensure_ascii=False)
        match.win_reason = win_reason
        match.total_turns = total_turns

        if winner_code == 1:
            match.winner_id = player1.id
        elif winner_code == 2:
            match.winner_id = player2.id
        else:
            match.winner_id = None

        # Record pre-match Elo ratings
        r1 = player1.elo
        r2 = player2.elo
        match.p1_elo_before = r1
        match.p2_elo_before = r2

        # Update Elo ratings for non-bracket matches
        if not match.is_bracket:
            if winner_code == 1:
                score_1 = 1.0
            elif winner_code == 2:
                score_1 = 0.0
            else:
                score_1 = 0.5

            delta_1, delta_2 = calculate_elo_delta(
                r1, r2, score=score_1, multiplier=multiplier_x, k=k_factor
            )
            new_r1 = apply_elo_change(r1, delta_1)
            new_r2 = apply_elo_change(r2, delta_2)

            player1.elo = new_r1
            player2.elo = new_r2
            match.p1_elo_after = new_r1
            match.p2_elo_after = new_r2
        else:
            match.p1_elo_after = r1
            match.p2_elo_after = r2

        # Update player win/loss/draw records
        if winner_code == 1:
            player1.wins += 1
            player2.losses += 1
        elif winner_code == 2:
            player2.wins += 1
            player1.losses += 1
        else:
            player1.draws += 1
            player2.draws += 1

        db.commit()
        return match_result

    except Exception as exc:
        logger.exception("Error executing match %d: %s", match_id, exc)
        try:
            match = db.query(Match).filter(Match.id == match_id).first()
            if match:
                match.win_reason = f"Execution error: {exc}"
                error_payload = {
                    "match_id": str(match_id),
                    "status": "error",
                    "error": str(exc),
                    "win_reason": f"Execution error: {exc}",
                    "winner": None,
                    "total_turns": 0,
                    "moves": [],
                    "initial_board": [],
                }
                match.replay_data = json.dumps(error_payload, ensure_ascii=False)
                db.commit()
        except Exception:
            pass
        return None
    finally:
        db.close()

