
<h1 align="center">🕹️ Neon Hunt AI Agent</h1>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python" />
  <img src="https://img.shields.io/badge/Minimax-FF6F00?style=for-the-badge" alt="Minimax" />
  <img src="https://img.shields.io/badge/Alpha--Beta_Pruning-4285F4?style=for-the-badge" alt="Alpha Beta Pruning" />
  <img src="https://img.shields.io/badge/Game_AI-82C341?style=for-the-badge&logo=openai&logoColor=white" alt="Game AI" />
</p>

> An advanced, search-based artificial intelligence agent designed for the **Neon Hunt** environment. This project implements a highly optimized Minimax algorithm with Alpha-Beta pruning to control a "Hacker" escaping a grid-based maze while actively evading a hostile "Cyber Beast."

---

## 🧠 Core AI Architecture

The agent is driven by a custom evaluation engine designed to balance aggressive progression toward the exit with robust survival instincts.

### 1. The Minimax & Alpha-Beta Engine
* **Decision Core:** Explores future game states utilizing a depth-limited Minimax algorithm.
* **Alpha-Beta Pruning:** Drastically reduces the number of explored states by pruning branches where the minimum guaranteed score falls below the maximum guaranteed baseline, returning the exact optimum move in a fraction of the time.

### 2. Advanced Evaluation Heuristics
* **Non-Linear Exit Pull:** Prevents "heuristic plateaus" by applying exponential gravity toward the exit. Overcomes minor localized penalties (like narrow corridors) utilizing the formula:
  $Score += (\frac{10000.0}{d\_exit + 1})$
* **Contextual Claustrophobia:** Actively analyzes escape routes. If the agent detects it is entering a one-way dead-end tunnel without an exit, it applies a massive penalty, preventing self-entrapment.
* **Tiered Threat Zones:** Imminent death is penalized severely (-50,000) as an absolute boundary, while critical proximity triggers a lesser penalty (-3,000) to force evasive action without paralyzing the agent's movement.

### 3. Anti-Loop Toxicity Map
To cure "Horizon Blindness"—where the agent paces infinitely due to perfectly balanced fear and goal rewards—a global **Flood-Fill Toxicity Map** is implemented. 
* Uses short-term memory to log visited coordinates.
* Applies a cumulative penalty dynamically: $Score -= (visits \times 500)$.
* Forces the AI to break its own fear boundaries and push past the monster into fresh corridors rather than pacing in toxic, over-visited corners.

### 4. Boss-Level Survival Strategy
Securing victory against the high-speed Boss requires stalling tactics. The heuristic modifies terminal states by passing the current search depth into the evaluation:
* **Winning State:** $100000 + (depth \times 1000)$
* **Losing State:** $-100000 - (depth \times 1000)$

By weighting the depth, the AI fundamentally alters its survival instinct: if a loss is mathematically inevitable in the search tree, it will explicitly choose the path that delays death the longest. This frequently causes the fast-moving Boss to get caught behind maze geometry, generating the exact window needed to escape.

---

## ⚙️ Requirements & Execution

### Tech Stack
* **Python 3.x**

### Quick Start
1. Clone this repository:
   ```bash
   git clone [https://github.com/amirkhedri/Neon-Hunt-AI.git](https://github.com/amirkhedri/Neon-Hunt-AI.git)
   cd Neon-Hunt-AI

```

2. Run the game environment:
```bash
python main.py

```


3. Inside the `Escape Scanner` UI, set the Player to **Student AI**, adjust your preferred depth and monster difficulty, and click **Auto** or **Round** to watch the agent navigate.

---

## 🎓 Academic Context

This project was developed as Project 3 for the **Fundamentals and Applications of Artificial Intelligence** course.

* **University:** Faculty of Computer Engineering, University of Isfahan
* **Semester:** Spring 2026 (1404-1405)
* **Instructor:** Dr. Marzieh Hosseini
* **Authors:** Amir Khedri & Saman Sheikhalishahi

```

```
