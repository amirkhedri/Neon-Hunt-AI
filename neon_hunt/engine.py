from collections import deque
import random
from dataclasses import replace
from neon_hunt.config import DIRECTIONS, AGENT_PLAYER, AGENT_MONSTER


def in_bounds(state, pos):
    r, c = pos
    return 0 <= r < state.rows and 0 <= c < state.cols


def pos_after(pos, move):
    dr, dc = DIRECTIONS[move]
    return (pos[0] + dr, pos[1] + dc)


def legal_moves_basic(state, agent):
    pos = state.player if agent == AGENT_PLAYER else state.monster
    moves = []
    for move in DIRECTIONS:
        nxt = pos_after(pos, move)
        if in_bounds(state, nxt) and nxt not in state.walls:
            moves.append(move)
    return moves


def transition_basic(state, move, agent):
    if move not in DIRECTIONS:
        raise ValueError(f"Unknown move: {move}")
    if move not in legal_moves_basic(state, agent):
        raise ValueError(f"Illegal move {move} for {agent}")
    if agent == AGENT_PLAYER:
        return replace(state, player=pos_after(state.player, move), turn=AGENT_MONSTER, turn_count=state.turn_count + 1)
    if agent == AGENT_MONSTER:
        return replace(state, monster=pos_after(state.monster, move), turn=AGENT_PLAYER)
    raise ValueError("agent must be 'player' or 'monster'")


def terminal_result(state):
    if state.player == state.exit:
        return "PLAYER_WIN"
    if state.player == state.monster:
        return "MONSTER_WIN"
    return "ONGOING"


def bfs_distance(state, start, goal):
    if start == goal:
        return 0
    q = deque([(start, 0)])
    seen = {start}
    while q:
        pos, dist = q.popleft()
        for dr, dc in DIRECTIONS.values():
            nxt = (pos[0] + dr, pos[1] + dc)
            if nxt in seen or not in_bounds(state, nxt) or nxt in state.walls:
                continue
            if nxt == goal:
                return dist + 1
            seen.add(nxt)
            q.append((nxt, dist + 1))
    return 999


def escape_routes(state, pos=None):
    if pos is None:
        pos = state.player
    count = 0
    for dr, dc in DIRECTIONS.values():
        nxt = (pos[0] + dr, pos[1] + dc)
        if in_bounds(state, nxt) and nxt not in state.walls:
            count += 1
    return count


def greedy_player_move(state):
    moves = legal_moves_basic(state, AGENT_PLAYER)
    if not moves:
        return None
    best, best_score = None, -10**9
    for m in moves:
        ns = transition_basic(state, m, AGENT_PLAYER)
        # Player wants close exit, far monster, many escape routes.
        score = -2.7 * bfs_distance(ns, ns.player, ns.exit) + 2.0 * bfs_distance(ns, ns.player, ns.monster) + 1.5 * escape_routes(ns)
        if score > best_score:
            best, best_score = m, score
    return best


def random_player_move(state):
    moves = legal_moves_basic(state, AGENT_PLAYER)
    return random.choice(moves) if moves else None
