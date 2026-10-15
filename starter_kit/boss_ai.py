"""Alpha-Beta Minimax Boss AI for 9x9 Rock-Paper-Scissors Chess.

This high-performance AI uses Alpha-Beta Pruning Minimax with deep heuristic evaluation:
- Goal distance minimization and goal-rush defense.
- Wipeout prevention and opportunistic wipeout attacks.
- Combat advantage matrix (Rock > Scissors > Paper > Rock).
- King-like 8-directional tactical mobility.
"""

from __future__ import annotations

import copy
import math
from typing import Any

DIRECTIONS = [
    (-1, -1), (-1, 0), (-1, 1),
    (0, -1),           (0, 1),
    (1, -1),  (1, 0),  (1, 1),
]

GOALS = {
    1: (8, 8),
    2: (0, 0),
}


def beats(attacker: str, defender: str) -> bool:
    """Check Rock-Paper-Scissors superiority."""
    return (
        (attacker == "R" and defender == "S")
        or (attacker == "S" and defender == "P")
        or (attacker == "P" and defender == "R")
    )


def chebyshev_dist(p1: tuple[int, int], p2: tuple[int, int]) -> int:
    """Chebyshev (King-move) distance on a chessboard."""
    return max(abs(p1[0] - p2[0]), abs(p1[1] - p2[1]))


def get_all_valid_moves(board: list[list[dict[str, Any] | None]], player: int) -> list[tuple[tuple[int, int], tuple[int, int]]]:
    """Generate all legal moves for the given player."""
    moves: list[tuple[tuple[int, int], tuple[int, int]]] = []
    for r in range(9):
        for c in range(9):
            piece = board[r][c]
            if piece and piece.get("player") == player:
                p_type = piece.get("type", "")
                for dr, dc in DIRECTIONS:
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < 9 and 0 <= nc < 9:
                        dest = board[nr][nc]
                        if dest is None:
                            moves.append(((r, c), (nr, nc)))
                        elif dest.get("player") != player:
                            if beats(p_type, dest.get("type", "")):
                                moves.append(((r, c), (nr, nc)))
    return moves


def evaluate_board(board: list[list[dict[str, Any] | None]], player: int) -> float:
    """Heuristic static evaluation of board state from the perspective of player."""
    opp = 2 if player == 1 else 1
    my_goal = GOALS[player]
    opp_goal = GOALS[opp]

    my_counts = {"R": 0, "P": 0, "S": 0}
    opp_counts = {"R": 0, "P": 0, "S": 0}

    my_min_goal_dist = 99
    opp_min_goal_dist = 99

    my_pieces_pos: list[tuple[int, int, str]] = []
    opp_pieces_pos: list[tuple[int, int, str]] = []

    for r in range(9):
        for c in range(9):
            cell = board[r][c]
            if cell:
                t = cell.get("type", "")
                owner = cell.get("player")
                if owner == player:
                    my_counts[t] += 1
                    d = chebyshev_dist((r, c), my_goal)
                    if d < my_min_goal_dist:
                        my_min_goal_dist = d
                    my_pieces_pos.append((r, c, t))
                else:
                    opp_counts[t] += 1
                    d = chebyshev_dist((r, c), opp_goal)
                    if d < opp_min_goal_dist:
                        opp_min_goal_dist = d
                    opp_pieces_pos.append((r, c, t))

    # Check terminal conditions
    if my_min_goal_dist == 0:
        return 10000.0
    if opp_min_goal_dist == 0:
        return -10000.0

    # Check wipeout conditions
    if any(count == 0 for count in opp_counts.values()):
        return 8000.0
    if any(count == 0 for count in my_counts.values()):
        return -8000.0

    score = 0.0

    # Material balance
    score += (sum(my_counts.values()) - sum(opp_counts.values())) * 120.0

    # Wipeout pressure (penalize enemy types down to 1 piece)
    for t in ("R", "P", "S"):
        if opp_counts[t] == 1:
            score += 350.0
        elif opp_counts[t] == 2:
            score += 80.0

        # Protect our endangered piece types
        if my_counts[t] == 1:
            score -= 400.0
        elif my_counts[t] == 2:
            score -= 90.0

    # Goal distance pressure (closer to goal is better)
    score += (8 - my_min_goal_dist) * 45.0
    score -= (8 - opp_min_goal_dist) * 55.0  # defense is slightly favored

    # Center control (rows 3..5, cols 3..5)
    for r, c, _ in my_pieces_pos:
        if 3 <= r <= 5 and 3 <= c <= 5:
            score += 15.0

    return score


def minimax(
    board: list[list[dict[str, Any] | None]],
    depth: int,
    alpha: float,
    beta: float,
    is_maximizing: bool,
    active_player: int,
    bot_player: int,
) -> float:
    """Minimax search with Alpha-Beta pruning."""
    if depth == 0:
        return evaluate_board(board, bot_player)

    valid_moves = get_all_valid_moves(board, active_player)
    if not valid_moves:
        return evaluate_board(board, bot_player)

    next_player = 2 if active_player == 1 else 1

    if is_maximizing:
        max_eval = -math.inf
        for (fr, fc), (tr, tc) in valid_moves:
            # Immediate win check
            if (tr, tc) == GOALS[active_player]:
                return 9500.0 + depth

            orig_dest = board[tr][tc]
            board[tr][tc] = board[fr][fc]
            board[fr][fc] = None

            eval_score = minimax(board, depth - 1, alpha, beta, False, next_player, bot_player)

            board[fr][fc] = board[tr][tc]
            board[tr][tc] = orig_dest

            max_eval = max(max_eval, eval_score)
            alpha = max(alpha, eval_score)
            if beta <= alpha:
                break
        return max_eval
    else:
        min_eval = math.inf
        for (fr, fc), (tr, tc) in valid_moves:
            if (tr, tc) == GOALS[active_player]:
                return -9500.0 - depth

            orig_dest = board[tr][tc]
            board[tr][tc] = board[fr][fc]
            board[fr][fc] = None

            eval_score = minimax(board, depth - 1, alpha, beta, True, next_player, bot_player)

            board[fr][fc] = board[tr][tc]
            board[tr][tc] = orig_dest

            min_eval = min(min_eval, eval_score)
            beta = min(beta, eval_score)
            if beta <= alpha:
                break
        return min_eval


def get_move(
    board: list[list[dict[str, Any] | None]],
    my_player: int,
    history: list[dict[str, Any]],
) -> tuple[tuple[int, int], tuple[int, int]] | None:
    """Entrypoint function called by engine to decide the next move.

    Args:
        board: 9x9 matrix of pieces.
        my_player: 1 or 2.
        history: Previous moves list.

    Returns:
        ((from_row, from_col), (to_row, to_col))
    """
    valid_moves = get_all_valid_moves(board, my_player)
    if not valid_moves:
        return None

    # Priority 1: Instant goal win
    my_goal = GOALS[my_player]
    for move in valid_moves:
        if move[1] == my_goal:
            return move

    # Priority 2: Instant wipeout win
    opp_player = 2 if my_player == 1 else 1
    for move in valid_moves:
        fr, fc = move[0]
        tr, tc = move[1]
        dest = board[tr][tc]
        if dest and dest.get("player") == opp_player:
            cap_type = dest.get("type")
            # Count surviving pieces of this type
            count = sum(
                1 for r in range(9) for c in range(9)
                if board[r][c] and board[r][c].get("player") == opp_player and board[r][c].get("type") == cap_type
            )
            if count == 1:
                return move  # Last piece of this type! Instant wipeout!

    # Priority 3: Alpha-Beta search at depth 2 (depth 2 gives instant <20ms move with high tactical strength)
    best_move = valid_moves[0]
    best_val = -math.inf
    alpha = -math.inf
    beta = math.inf

    # Sort moves by immediate capture heuristic for better pruning
    def move_order_score(m: tuple[tuple[int, int], tuple[int, int]]) -> int:
        dest_cell = board[m[1][0]][m[1][1]]
        if dest_cell is not None:
            return 100 - chebyshev_dist(m[1], my_goal)
        return -chebyshev_dist(m[1], my_goal)

    sorted_moves = sorted(valid_moves, key=move_order_score, reverse=True)

    for (fr, fc), (tr, tc) in sorted_moves:
        orig_dest = board[tr][tc]
        board[tr][tc] = board[fr][fc]
        board[fr][fc] = None

        val = minimax(board, depth=2, alpha=alpha, beta=beta, is_maximizing=False, active_player=opp_player, bot_player=my_player)

        board[fr][fc] = board[tr][tc]
        board[tr][tc] = orig_dest

        if val > best_val:
            best_val = val
            best_move = ((fr, fc), (tr, tc))
        alpha = max(alpha, val)

    return best_move
