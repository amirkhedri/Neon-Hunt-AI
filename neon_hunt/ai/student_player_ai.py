# ==========================================
# Neon Hunt - Student AI Implementation
# ==========================================

STUDENT_ID = "1234567890"  # Don't forget your ID

from neon_hunt.ai.student_support import (
    get_possible_moves,
    apply_move,
    is_terminal
)
import math

try:
    from neon_hunt.ai.student_support import AGENT_PLAYER, AGENT_MONSTER
except ImportError:
    AGENT_PLAYER = "PLAYER"
    AGENT_MONSTER = "MONSTER"

# --- GLOBAL MEMORY ---
real_visited_cells = {}
last_known_pos = None

def get_manhattan_distance(pos1, pos2):
    if not pos1 or not pos2: return 999
    return abs(pos1[0] - pos2[0]) + abs(pos1[1] - pos2[1])

def evaluate(state, current_depth=0):
    """
    Core Heuristic Evaluation.
    """
    terminal_status = is_terminal(state)
    
    # 1. Depth-weighted terminal states
    if terminal_status == "PLAYER_WIN":
        return 100000.0 + (current_depth * 1000)
    elif terminal_status == "MONSTER_WIN":
        return -100000.0 - (current_depth * 1000)

    d_exit = get_manhattan_distance(state.player, state.exit)
    d_monster = get_manhattan_distance(state.player, state.monster)
    
    score = 0.0

    # 2. Aggressive push to the exit
    score -= (d_exit * 100)

    # 3. Monster Avoidance (Tiered)
    if d_monster <= 1:
        score -= 50000  
    elif d_monster == 2:
        score -= 5000   
    elif d_monster == 3:
        score -= 500    
    else:
        # Slight reward for keeping distance
        score += (d_monster * 5) 

    # 4. Backup state penalty for the simulation itself
    global real_visited_cells
    if state.player in real_visited_cells:
        score -= 1000

    return score

def minimax(state, depth, maximizing_player, stats=None):
    if stats is not None:
        stats["states_explored"] = stats.get("states_explored", 0) + 1

    terminal_status = is_terminal(state)
    if depth == 0 or terminal_status != "ONGOING":
        return evaluate(state, depth)

    if maximizing_player:
        max_eval = -math.inf
        moves = get_possible_moves(state, AGENT_PLAYER)
        if not moves:
            return evaluate(state, depth)
            
        for move in moves:
            child_state = apply_move(state, move, AGENT_PLAYER)
            eval_score = minimax(child_state, depth - 1, False, stats)
            max_eval = max(max_eval, eval_score)
        return max_eval
        
    else:
        min_eval = math.inf
        moves = get_possible_moves(state, AGENT_MONSTER)
        if not moves:
            return evaluate(state, depth)
            
        for move in moves:
            child_state = apply_move(state, move, AGENT_MONSTER)
            eval_score = minimax(child_state, depth - 1, True, stats)
            min_eval = min(min_eval, eval_score)
        return min_eval

def alpha_beta(state, depth, alpha, beta, maximizing_player, stats=None):
    if stats is not None:
        stats["states_explored"] = stats.get("states_explored", 0) + 1

    terminal_status = is_terminal(state)
    if depth == 0 or terminal_status != "ONGOING":
        return evaluate(state, depth)

    if maximizing_player:
        max_eval = -math.inf
        moves = get_possible_moves(state, AGENT_PLAYER)
        if not moves:
            return evaluate(state, depth)
            
        for move in moves:
            child_state = apply_move(state, move, AGENT_PLAYER)
            eval_score = alpha_beta(child_state, depth - 1, alpha, beta, False, stats)
            max_eval = max(max_eval, eval_score)
            alpha = max(alpha, eval_score)
            if beta <= alpha:
                if stats is not None:
                    stats["pruned_branches"] = stats.get("pruned_branches", 0) + 1
                break
        return max_eval
        
    else:
        min_eval = math.inf
        moves = get_possible_moves(state, AGENT_MONSTER)
        if not moves:
            return evaluate(state, depth)
            
        for move in moves:
            child_state = apply_move(state, move, AGENT_MONSTER)
            eval_score = alpha_beta(child_state, depth - 1, alpha, beta, True, stats)
            min_eval = min(min_eval, eval_score)
            beta = min(beta, eval_score)
            if beta <= alpha:
                if stats is not None:
                    stats["pruned_branches"] = stats.get("pruned_branches", 0) + 1
                break
        return min_eval

def choose_player_move(state, depth, use_alpha_beta=True):
    global real_visited_cells
    global last_known_pos
    
    # 1. Update Global History
    # If the player teleports (new level or manual reset), wipe the history clean
    if last_known_pos is None or get_manhattan_distance(state.player, last_known_pos) > 1:
        real_visited_cells.clear()
        
    last_known_pos = state.player
    real_visited_cells[state.player] = real_visited_cells.get(state.player, 0) + 1

    stats = {
        "states_explored": 0,
        "pruned_branches": 0
    }
    
    moves = get_possible_moves(state, AGENT_PLAYER)
    best_move = None
    best_score = -math.inf
    scores = {}

    # Deterministic Tie-Breaker
    move_priority = {"UP": 0.04, "RIGHT": 0.03, "DOWN": 0.02, "LEFT": 0.01}

    for move in moves:
        child_state = apply_move(state, move, AGENT_PLAYER)
        
        # Calculate base future score
        if use_alpha_beta:
            score = alpha_beta(child_state, depth - 1, -math.inf, math.inf, False, stats)
        else:
            score = minimax(child_state, depth - 1, False, stats)

        # =======================================================
        # THE ULTIMATE LOOP BREAKER
        # Apply a massive penalty if the IMMEDIATE NEXT STEP has 
        # already been visited in the real game.
        # =======================================================
        if child_state.player in real_visited_cells:
            penalty = real_visited_cells[child_state.player] * 15000
            score -= penalty

        stable_score = score + move_priority.get(move, 0)
        scores[move] = stable_score
        
        if stable_score > best_score:
            best_score = stable_score
            best_move = move

    # Fallback to prevent crashes
    if best_move is None and moves:
        best_move = moves[0]

    return {
        "best_move": best_move,
        "scores": scores,
        "states_explored": stats["states_explored"],
        "pruned_branches": stats["pruned_branches"]
    }