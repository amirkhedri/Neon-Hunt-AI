
<h1 align="center">🕹️ Neon Hunt AI Agent</h1>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python" />
  <img src="https://img.shields.io/badge/Algorithm-Minimax-FF6F00?style=for-the-badge" alt="Minimax" />
  <img src="https://img.shields.io/badge/Optimization-Alpha--Beta_Pruning-4285F4?style=for-the-badge" alt="Alpha Beta Pruning" />
  <img src="https://img.shields.io/badge/Domain-Game_AI-82C341?style=for-the-badge&logo=openai&logoColor=white" alt="Game AI" />
</p>

> An advanced, search-based artificial intelligence agent designed to conquer the **Neon Hunt** environment. This project implements a highly optimized Minimax algorithm with Alpha-Beta pruning to control a Hacker escaping a grid-based maze while actively evading a hostile Cyber Beast.

---

## 🎮 The Game: Neon Hunt

**Neon Hunt** is a turn-based, grid survival puzzle game where logic and foresight are the only paths to survival. 

### Core Mechanics
* 🏃 **The Hacker (Player):** Starts at a designated spawn point. The objective is to navigate the maze and safely reach the **Exit** tile. Can move Up, Down, Left, or Right.
* 👹 **The Cyber Beast (Monster):** A hostile entity that hunts the Hacker. It moves immediately after the Hacker makes a decision. It features multiple difficulty tiers (Easy, Normal, Hard, Boss), dictating the intelligence and aggression of its tracking.
* 🧱 **The Grid:** A dynamic maze filled with impassable walls. Navigating the grid requires anticipating the Cyber Beast's movements to avoid getting cornered in one-way corridors.

---

## 🧠 AI Architecture & Decision Engine

To survive the higher difficulty tiers, the AI cannot simply move toward the exit—it must calculate risk, anticipate traps, and manipulate the Cyber Beast's pathing. 

### 1. The Search Algorithms
* **Minimax Engine:** The core decision tree. The AI simulates future turns, assuming the Hacker will play optimally to maximize their survival score, while the Cyber Beast will play optimally to minimize it.
* **Alpha-Beta Pruning:** A mathematical optimization that drastically cuts down the processing time. By tracking the best guaranteed scores for both entities ($\alpha$ and $\beta$), the AI actively abandons calculating branches of the decision tree that are mathematically proven to be worse than previously found paths. 

### 2. Advanced Evaluation Heuristics
The evaluation function assigns a strict numerical value to any given board state, balancing aggressive progression with absolute survival.

* **Non-Linear Exit Pull:** Prevents "heuristic plateaus" (where the AI gets confused by distant paths). It applies an exponential gravity pull toward the exit, allowing the AI to easily overcome minor localized penalties like narrow corridors.
  
  $$Score += \left(\frac{10000.0}{d\_exit + 1}\right)$$

* **Tiered Threat Zones:** Distance to the Cyber Beast is heavily weighted. Imminent death triggers a massive penalty (`-50,000`) acting as a hard boundary. Critical proximity triggers a moderate penalty (`-3,000`), forcing evasive action without completely paralyzing the agent.
* **Contextual Claustrophobia:** The AI actively analyzes escape routes. If it detects it is entering a one-way dead-end without an exit, it applies a massive penalty to prevent self-entrapment.

---

## 🛡️ Anti-Looping & Boss Strategies

### The Flood-Fill Toxicity Map
A common failure in grid-based AI is "Horizon Blindness"—pacing infinitely back and forth when the fear of the monster perfectly balances the reward of the exit. 
* This AI utilizes short-term memory to log visited coordinates.
* It applies a cumulative, dynamic penalty to over-visited cells: $Score -= (visits \times 500)$.
* This forces the AI to break its own fear boundaries and push past the Cyber Beast into fresh corridors rather than pacing in "toxic" corners.

### Depth-Weighted Survival (Boss Strategy)
The Level 4 "Boss" is extremely fast and aggressive. Standard AI treats a loss in 2 steps the same as a loss in 10 steps. This agent fundamentally alters its survival instinct by passing the search depth directly into terminal state evaluations:
* **Winning State:** $100000 + (depth \times 1000)$
* **Losing State:** $-100000 - (depth \times 1000)$

If a loss is mathematically inevitable, the AI explicitly chooses the path that delays death the longest. This stall tactic frequently causes the fast-moving Boss to get snagged behind maze geometry, generating the exact window needed for the Hacker to escape.

---

## ⚙️ Requirements & Execution

### Tech Stack
* **Python 3.x**

### Quick Start
1. **Clone the repository:**
 ```bash
 git clone https://github.com/amirkhedri/Neon-Hunt-AI.git

```
2. **Run the game environment:**
```bash
python main.py

```


3. **Configure the AI:** Inside the `Escape Scanner` UI on the right side of the screen:
* Set Player to **Student AI**.
* Adjust your preferred Search Depth and Monster Difficulty.
* Click **Auto** or **Round** at the bottom to watch the agent navigate.



---

## 🎓 Academic Context

This project was developed as Project 3 for the **Fundamentals and Applications of Artificial Intelligence** course.

* **University:** Faculty of Computer Engineering, University of Isfahan
* **Semester:** Spring 2026 (1404-1405)
* **Author:** Amir Khedri
