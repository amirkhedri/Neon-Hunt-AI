"""Student-facing helper functions for Neon Hunt Track B.

Students do NOT need to re-implement these game-rule helpers. They may import
and use them in student_player_ai.py while focusing on:
- evaluate
- minimax
- alpha_beta
- choose_player_move
"""
from dataclasses import replace

from neon_hunt.config import DIRECTIONS, AGENT_PLAYER, AGENT_MONSTER
from neon_hunt.engine import in_bounds, pos_after


def get_possible_moves(state, agent):
    """Return legal moves for player or monster."""
    pos = state.player if agent == AGENT_PLAYER else state.monster
    moves = []
    for move in DIRECTIONS:
        nxt = pos_after(pos, move)
        if in_bounds(state, nxt) and nxt not in state.walls:
            moves.append(move)
    return moves


def apply_move(state, move, agent):
    """Return a new state after applying a legal move.

    This function does not mutate the original state.
    """
    if move not in get_possible_moves(state, agent):
        raise ValueError(f"Illegal move {move!r} for {agent!r}")

    if agent == AGENT_PLAYER:
        return replace(
            state,
            player=pos_after(state.player, move),
            turn=AGENT_MONSTER,
            turn_count=state.turn_count + 1,
        )

    if agent == AGENT_MONSTER:
        return replace(
            state,
            monster=pos_after(state.monster, move),
            turn=AGENT_PLAYER,
        )

    raise ValueError("agent must be AGENT_PLAYER or AGENT_MONSTER")


def is_terminal(state):
    """Return PLAYER_WIN, MONSTER_WIN, or ONGOING."""
    if state.player == state.exit:
        return "PLAYER_WIN"
    if state.player == state.monster:
        return "MONSTER_WIN"
    return "ONGOING"
