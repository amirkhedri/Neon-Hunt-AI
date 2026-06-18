"""Instructor-owned monster AI. Students should not edit this file.

The grader imports a private copy of this logic, so modifying this file does not help submissions.

V14 monster policy:
- uses stronger Alpha-Beta search,
- orders moves to improve pruning,
- prioritizes immediate capture,
- pressures the exit and reduces the player's mobility,
- adds a tactical one-ply trap bonus.
"""
from math import inf
from neon_hunt.config import AGENT_PLAYER, AGENT_MONSTER
from neon_hunt.engine import legal_moves_basic, transition_basic, terminal_result, bfs_distance, escape_routes


def _safe_distance(state, start, goal):
    d = bfs_distance(state, start, goal)
    return 999 if d is None else d


def _player_escape_options(state):
    """Number of player moves that do not get captured immediately next turn."""
    count = 0
    for pm in legal_moves_basic(state, AGENT_PLAYER):
        ps = transition_basic(state, pm, AGENT_PLAYER)
        if terminal_result(ps) == "PLAYER_WIN":
            count += 2
            continue
        unsafe = False
        for mm in legal_moves_basic(ps, AGENT_MONSTER):
            ms = transition_basic(ps, mm, AGENT_MONSTER)
            if terminal_result(ms) == "MONSTER_WIN":
                unsafe = True
                break
        if not unsafe:
            count += 1
    return count


def _capture_threats(state):
    """How many monster moves would capture on the next monster turn."""
    threats = 0
    for mm in legal_moves_basic(state, AGENT_MONSTER):
        ms = transition_basic(state, mm, AGENT_MONSTER)
        if terminal_result(ms) == "MONSTER_WIN":
            threats += 1
    return threats


def evaluate_for_monster(state):
    """Higher is better for the monster.

    The heuristic is not just 'distance to player'. It also:
    - punishes player progress toward the exit,
    - rewards blocking the exit route,
    - rewards positions that reduce the player's legal safe options,
    - rewards immediate capture threats and fork/trap situations.
    """
    result = terminal_result(state)
    if result == "MONSTER_WIN":
        return 100000.0
    if result == "PLAYER_WIN":
        return -100000.0

    mp = _safe_distance(state, state.monster, state.player)  # monster -> player
    pe = _safe_distance(state, state.player, state.exit)     # player -> exit
    me = _safe_distance(state, state.monster, state.exit)    # monster -> exit

    routes = escape_routes(state, state.player)
    safe_opts = _player_escape_options(state)
    threats = _capture_threats(state)

    # Exit pressure: if the monster is near the exit while the player is also
    # approaching it, the monster should guard/ambush rather than chase blindly.
    exit_pressure = max(0, 12 - me) + max(0, 8 - pe)

    score = (
        8.8 * pe
        - 10.5 * mp
        - 7.0 * routes
        - 8.0 * safe_opts
        + 18.0 * threats
        + 2.2 * exit_pressure
    )

    if mp <= 1:
        score += 160
    elif mp == 2:
        score += 55
    elif mp == 3:
        score += 18

    if pe <= 2:
        score -= 80
    elif pe <= 4:
        score -= 25

    if safe_opts == 0:
        score += 90
    elif safe_opts == 1:
        score += 35

    return float(score)


def _ordered_moves(state, agent, maximizing):
    moves = legal_moves_basic(state, agent)
    def score_move(m):
        child = transition_basic(state, m, agent)
        return evaluate_for_monster(child)
    return sorted(moves, key=score_move, reverse=maximizing)


def _alphabeta(state, depth, alpha, beta, maximizing, stats):
    stats["states_explored"] += 1
    result = terminal_result(state)
    if result != "ONGOING" or depth == 0:
        return evaluate_for_monster(state)

    agent = AGENT_MONSTER if maximizing else AGENT_PLAYER
    moves = _ordered_moves(state, agent, maximizing)
    if not moves:
        return evaluate_for_monster(state)

    if maximizing:
        value = -inf
        for m in moves:
            value = max(value, _alphabeta(transition_basic(state, m, agent), depth - 1, alpha, beta, False, stats))
            alpha = max(alpha, value)
            if alpha >= beta:
                stats["pruned_branches"] += 1
                break
        return value

    value = inf
    for m in moves:
        value = min(value, _alphabeta(transition_basic(state, m, agent), depth - 1, alpha, beta, True, stats))
        beta = min(beta, value)
        if alpha >= beta:
            stats["pruned_branches"] += 1
            break
    return value


def _principal_variation(state, first_move, depth):
    pv = []
    try:
        s = transition_basic(state, first_move, AGENT_MONSTER)
        pv.append({"agent": "monster", "position": s.monster, "move": first_move})
        maximizing = False
        remaining = depth - 1
        while remaining > 0 and terminal_result(s) == "ONGOING" and len(pv) < 8:
            agent = AGENT_MONSTER if maximizing else AGENT_PLAYER
            moves = _ordered_moves(s, agent, maximizing)
            if not moves:
                break
            scored = []
            for m in moves:
                child = transition_basic(s, m, agent)
                stats = {"states_explored": 0, "pruned_branches": 0}
                val = _alphabeta(child, remaining - 1, -inf, inf, not maximizing, stats)
                scored.append((val, m, child))
            if maximizing:
                _, m, s = max(scored, key=lambda x: x[0])
                pv.append({"agent": "monster", "position": s.monster, "move": m})
            else:
                _, m, s = min(scored, key=lambda x: x[0])
                pv.append({"agent": "player", "position": s.player, "move": m})
            maximizing = not maximizing
            remaining -= 1
    except Exception:
        return []
    return pv


def choose_monster_move(state, difficulty="Normal"):
    settings = {
        "Easy": ("Alpha-Beta", 2),
        "Normal": ("Alpha-Beta", 4),
        "Hard": ("Alpha-Beta", 6),
        "Boss": ("Alpha-Beta", 7),
    }
    mode, depth = settings.get(difficulty, settings["Normal"])
    moves = legal_moves_basic(state, AGENT_MONSTER)
    if not moves:
        return {"best_move": None, "scores": {}, "states_explored": 0, "pruned_branches": 0, "depth": depth, "mode": mode, "principal_variation": []}

    # Immediate capture always wins.
    for m in moves:
        ns = transition_basic(state, m, AGENT_MONSTER)
        if terminal_result(ns) == "MONSTER_WIN":
            return {
                "best_move": m,
                "scores": {move: (100000.0 if move == m else evaluate_for_monster(transition_basic(state, move, AGENT_MONSTER))) for move in moves},
                "states_explored": 1,
                "pruned_branches": 0,
                "depth": depth,
                "mode": mode,
                "principal_variation": _principal_variation(state, m, depth),
            }

    stats = {"states_explored": 0, "pruned_branches": 0}
    scores = {}
    best_move, best_score = None, -inf

    for m in _ordered_moves(state, AGENT_MONSTER, True):
        ns = transition_basic(state, m, AGENT_MONSTER)
        val = _alphabeta(ns, depth - 1, -inf, inf, False, stats)
        # Small tie-breaker: prefer moves that get closer to the player.
        val += 0.01 * (100 - _safe_distance(ns, ns.monster, ns.player))
        scores[m] = val
        if val > best_score:
            best_move, best_score = m, val

    return {
        "best_move": best_move,
        "scores": scores,
        "states_explored": stats["states_explored"],
        "pruned_branches": stats["pruned_branches"],
        "depth": depth,
        "mode": mode,
        "principal_variation": _principal_variation(state, best_move, depth),
    }
