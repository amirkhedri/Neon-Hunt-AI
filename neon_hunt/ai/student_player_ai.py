"""Student AI Template — Neon Hunt

IMPORTANT: Replace STUDENT_ID with your own 10-digit numeric student code.

Only these four functions are TODO for students:
1. evaluate
2. minimax
3. alpha_beta
4. choose_player_move

The game-rule helpers are already provided:
- get_possible_moves
- apply_move
- is_terminal
"""
# TODO: write your own 10-digit numeric student code here.
# Example: STUDENT_ID = "4021234567"
STUDENT_ID = "0000000000"

from math import inf

from neon_hunt.config import AGENT_PLAYER, AGENT_MONSTER
from neon_hunt.engine import bfs_distance, escape_routes
from neon_hunt.ai.student_support import get_possible_moves, apply_move, is_terminal


def evaluate(state):
    """Return a score from the Player/Hacker perspective.

    Higher is better for the player.

    Suggested ideas:
    - PLAYER_WIN should be a very large positive score.
    - MONSTER_WIN should be a very large negative score.
    - Being closer to the exit is good.
    - Being farther from the monster is good.
    - Having more escape routes is good.
    """
    result = is_terminal(state)
    if result == "PLAYER_WIN":
        return 100000.0
    if result == "MONSTER_WIN":
        return -100000.0

    d_exit = bfs_distance(state, state.player, state.exit)
    d_monster = bfs_distance(state, state.player, state.monster)
    routes = escape_routes(state, state.player)

    # TODO: improve this heuristic.
    return float(-6.0 * d_exit + 4.0 * d_monster + 2.0 * routes)


def minimax(state, depth, maximizing_player, stats=None):
    """Depth-limited Minimax from the Player's perspective."""
    # TODO: implement minimax.
    raise NotImplementedError("Implement minimax(state, depth, maximizing_player, stats=None)")


def alpha_beta(state, depth, alpha, beta, maximizing_player, stats=None):
    """Minimax with alpha-beta pruning from the Player's perspective."""
    # TODO: implement alpha-beta pruning.
    raise NotImplementedError("Implement alpha_beta(state, depth, alpha, beta, maximizing_player, stats=None)")


def choose_player_move(state, depth, use_alpha_beta=True):
    """Choose the Player/Hacker move using minimax or alpha-beta.

    Return format:
    {
        "best_move": "UP",
        "scores": {"UP": 1.2, "DOWN": -5.0},
        "states_explored": 42,
        "pruned_branches": 7,
        "principal_variation": []
    }
    """
    moves = get_possible_moves(state, AGENT_PLAYER)
    if not moves:
        return {
            "best_move": None,
            "scores": {},
            "states_explored": 0,
            "pruned_branches": 0,
            "principal_variation": [],
        }

    # TODO: call alpha_beta or minimax for each candidate move and return best.
    raise NotImplementedError("Implement choose_player_move(state, depth, use_alpha_beta=True)")
