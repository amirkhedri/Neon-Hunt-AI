# ==========================================
# Neon Hunt - Student AI Implementation
# ==========================================

STUDENT_ID = "4023613024"  

from neon_hunt.ai.student_support import (
    get_possible_moves,
    apply_move,
    is_terminal
)
import math

try:
    from neon_hunt.ai.student_support import bfs_distance, escape_routes
    _HAS_MAZE_HELPERS = True
except ImportError:
    _HAS_MAZE_HELPERS = False

try:
    from neon_hunt.ai.student_support import AGENT_PLAYER, AGENT_MONSTER
except ImportError:
    AGENT_PLAYER = "PLAYER"
    AGENT_MONSTER = "MONSTER"

# --- FLOOD-FILL TOXICITY MAP ---
_visit_counts = {}
_last_known_pos = None

# ------------------------------------------------------------------
# Distance / mobility helpers 
# ------------------------------------------------------------------
_UNREACHABLE = 500  

def get_manhattan_distance(pos1, pos2):
    if not pos1 or not pos2: return 999
    return abs(pos1[0] - pos2[0]) + abs(pos1[1] - pos2[1])

def safe_path_distance(state, start, goal):
    if not start or not goal: return _UNREACHABLE
    if _HAS_MAZE_HELPERS:
        try:
            d = bfs_distance(state, start, goal)
            if d is None or d < 0: return _UNREACHABLE
            return d
        except Exception:
            pass
    return get_manhattan_distance(start, goal)

def safe_escape_routes(state, position):
    if _HAS_MAZE_HELPERS:
        try:
            routes = escape_routes(state, position)
            if isinstance(routes, (list, tuple, set)): return len(routes)
            if isinstance(routes, (int, float)): return int(routes)
        except Exception:
            pass
    return len(get_possible_moves(state, AGENT_PLAYER))

# ------------------------------------------------------------------
# Evaluation
# ------------------------------------------------------------------
def evaluate(state, current_depth=0):
    terminal_status = is_terminal(state)

    # Depth Weighting: Win as fast as possible, delay losing as long as possible.
    if terminal_status == "PLAYER_WIN":
        return 100000.0 + (current_depth * 1000)
    elif terminal_status == "MONSTER_WIN":
        return -100000.0 - (current_depth * 1000)

    d_exit = safe_path_distance(state, state.player, state.exit)
    d_monster = safe_path_distance(state, state.player, state.monster)
    routes = safe_escape_routes(state, state.player)

    score = 0.0

    # 1. NON-LINEAR EXIT PULL
    # Closer = exponentially higher score. Breaks flat heuristic plateaus.
    if d_exit < _UNREACHABLE:
        score += (10000.0 / (d_exit + 1))
    else:
        score -= 20000

    # 2. MONSTER FEAR ZONES
    if d_monster <= 1:
        score -= 50000
    elif d_monster == 2:
        score -= 3000
    else:
        # Small reward for maintaining distance
        score += d_monster * 15

    # 3. CLAUSTROPHOBIA / DEAD-END AVOIDANCE
    # If in a 1-way tunnel and the exit isn't immediately inside it, panic.
    if routes <= 1 and d_exit > 2:
        score -= 4000

    # 4. DETERMINISTIC COORDINATE TIE-BREAKER
    score += (state.player[0] * 0.1) + (state.player[1] * 0.01)

    return score

# ------------------------------------------------------------------
# Minimax
# ------------------------------------------------------------------
def minimax(state, depth, maximizing_player, stats=None):
    if stats is not None:
        stats["states_explored"] = stats.get("states_explored", 0) + 1

    terminal_status = is_terminal(state)
    if depth == 0 or terminal_status != "ONGOING":
        return evaluate(state, depth)

    if maximizing_player:
        moves = get_possible_moves(state, AGENT_PLAYER)
        if not moves: return evaluate(state, depth)
        max_eval = -math.inf
        for move in moves:
            child_state = apply_move(state, move, AGENT_PLAYER)
            eval_score = minimax(child_state, depth - 1, False, stats)
            if eval_score > max_eval: max_eval = eval_score
        return max_eval
    else:
        moves = get_possible_moves(state, AGENT_MONSTER)
        if not moves: return evaluate(state, depth)
        min_eval = math.inf
        for move in moves:
            child_state = apply_move(state, move, AGENT_MONSTER)
            eval_score = minimax(child_state, depth - 1, True, stats)
            if eval_score < min_eval: min_eval = eval_score
        return min_eval

# ------------------------------------------------------------------
# Alpha-Beta 
# ------------------------------------------------------------------
def alpha_beta(state, depth, alpha, beta, maximizing_player, stats=None):
    if stats is not None:
        stats["states_explored"] = stats.get("states_explored", 0) + 1

    terminal_status = is_terminal(state)
    if depth == 0 or terminal_status != "ONGOING":
        return evaluate(state, depth)

    if maximizing_player:
        moves = get_possible_moves(state, AGENT_PLAYER)
        if not moves: return evaluate(state, depth)
        max_eval = -math.inf
        for move in moves:
            child_state = apply_move(state, move, AGENT_PLAYER)
            eval_score = alpha_beta(child_state, depth - 1, alpha, beta, False, stats)
            if eval_score > max_eval: max_eval = eval_score
            if max_eval > alpha: alpha = max_eval
            if alpha >= beta:
                if stats is not None: stats["pruned_branches"] = stats.get("pruned_branches", 0) + 1
                break
        return max_eval
    else:
        moves = get_possible_moves(state, AGENT_MONSTER)
        if not moves: return evaluate(state, depth)
        min_eval = math.inf
        for move in moves:
            child_state = apply_move(state, move, AGENT_MONSTER)
            eval_score = alpha_beta(child_state, depth - 1, alpha, beta, True, stats)
            if eval_score < min_eval: min_eval = eval_score
            if min_eval < beta: beta = min_eval
            if alpha >= beta:
                if stats is not None: stats["pruned_branches"] = stats.get("pruned_branches", 0) + 1
                break
        return min_eval

# ------------------------------------------------------------------
# Root move selection
# ------------------------------------------------------------------
def choose_player_move(state, depth, use_alpha_beta=True):
    global _visit_counts
    global _last_known_pos

    # Wipe the toxicity map if a new level loads
    if _last_known_pos is None or get_manhattan_distance(state.player, _last_known_pos) > 1:
        _visit_counts.clear()
        
    _last_known_pos = state.player
    _visit_counts[state.player] = _visit_counts.get(state.player, 0) + 1

    stats = {"states_explored": 0, "pruned_branches": 0}
    moves = get_possible_moves(state, AGENT_PLAYER)
    best_move = None
    best_score = -math.inf
    scores = {}

    move_priority = {"UP": 0.04, "RIGHT": 0.03, "DOWN": 0.02, "LEFT": 0.01}
    principal_variation = []

    for move in moves:
        child_state = apply_move(state, move, AGENT_PLAYER)

        if use_alpha_beta:
            score = alpha_beta(child_state, depth - 1, -math.inf, math.inf, False, stats)
        else:
            score = minimax(child_state, depth - 1, False, stats)

        # 5. FLOOD-FILL PROGRESSION (The absolute loop breaker)
        # Every visit to a cell makes it permanently more toxic by 500 points.
        # It guarantees the AI will eventually break out of ANY trap.
        visits = _visit_counts.get(child_state.player, 0)
        score -= (visits * 500)

        stable_score = score + move_priority.get(move, 0)
        scores[move] = stable_score

        if stable_score > best_score:
            best_score = stable_score
            best_move = move
            principal_variation = [move]

    if best_move is None and moves:
        best_move = moves[0]
        principal_variation = [best_move]

    return {
        "best_move": best_move,
        "scores": scores,
        "states_explored": stats["states_explored"],
        "pruned_branches": stats["pruned_branches"],
        "principal_variation": principal_variation
    }