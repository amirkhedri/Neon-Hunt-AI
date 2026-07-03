[![Review Assignment Due Date](https://classroom.github.com/assets/deadline-readme-button-22041afd0340ce965d47ae6ef1cefeee28c7c493a6346c4f15d667ab976d596c.svg)](https://classroom.github.com/a/TwWpR3sR)
# Neon Hunt

Neon Hunt is a grid-based escape AI project for Track B. The player controls the Hacker, who must reach the exit or survive while the Cyber Beast tries to catch them.

## Run

```bash
python main.py
```

On Windows, you can also run:

```bash
run_windows.bat
```

## Student Task

Complete the AI in:

```text
neon_hunt/ai/student_player_ai.py
```

Implement these functions:

- `evaluate(state)`
- `minimax(state, depth, maximizing_player, stats=None)`
- `alpha_beta(state, depth, alpha, beta, maximizing_player, stats=None)`
- `choose_player_move(state, depth, use_alpha_beta=True)`

Also set your 10-digit student ID:

```python
STUDENT_ID = "1234567890"
```

The full Persian assignment guide is available at:

```text
docs/Neon_Hunt_Student_Guide.pdf
```
