# Escape Horror — 3D Survival Maze Game

A 3D survival horror maze game built with Python and OpenGL (PyOpenGL / GLUT). Navigate a dark maze, complete objectives in order, and escape before the ghost catches you!

---

## Game Overview

You are trapped inside a confined 3D maze and hunted by a ghost. Complete a chain of objectives to unlock the exit and escape — but the ghost never stops chasing you, and the clock is always ticking.

---

## Team Members

| Member | Responsibility |
|---|---|
| **Naimur Rahman Sifat** | Player System — Movement, Camera, Collision (Features 1–3) |
| **Rezowan Rashid Ovik** | Enemy & Game Logic — Ghost, Difficulty, State, Cheat Mode (Features 4–8) |
| **Junaid Islam Rafin** | Environment & Objectives — Items, HUD, Spawning, Flicker (Features 9–13) |

---

## Controls

| Key | Action |
|---|---|
| `W` / `S` | Move forward / backward |
| `A` / `D` | Rotate left / right |
| `E` | Interact with nearby object |
| `Z` | Toggle camera zoom (normal / zoomed-out) |
| `Right-click` | Toggle first-person / top-down camera |
| `Arrow Keys` | Orbit camera (top-down mode) |
| `R` | Restart / back to mode select |
| `C` | Toggle Cheat Mode (freeze timer + ghost can't catch you) |

---

## Objective (in order)

1. 🔋 **Collect all Power Cells** — glowing green, scattered around the maze
2. 🔘 **Activate all Switches** (2 total) — requires all power cells first
3. 🗝️ **Pick up the Key** — golden, spinning — requires all switches activated
4. 🔒 **Open the Safe** — located in the north-east corner
5. 🚪 **Reach the Exit** — north wall, now unlocked!

> ⚠️ Steps must be completed **in order**. Skipping ahead won't work.

---

## Difficulty Modes

| Mode | Time Limit | Power Cells | Ghost Speed |
|---|---|---|---|
| 🟢 **Easy** | 3:00 min | 2 | Slow |
| 🟡 **Normal** | 2:30 min | 3 | Normal |
| 🔴 **Hard** | 2:00 min | 4 | Fast |

The ghost also **accelerates over time**, so early game exploration is safer than late game.

---

## Features

### Player System
- Smooth movement with **wall sliding** (no awkward sticking)
- **First-person** (immersive) and **top-down** (strategic) camera modes, switchable anytime
- Proper **maze collision** detection against all inner and boundary walls

### Enemy System
- Ghost continuously **tracks the player's position**
- Speed **increases gradually** over time and gets a **proximity boost** when close
- Distinct **warning system** — screen flickers red and a message appears when the ghost is near

### Game Logic
- Three **difficulty modes** with different time limits, item counts, and ghost speeds
- Full **game state management** — game over on catch or timeout, win on escape
- **Cheat mode** — freezes the timer and disables ghost catching (for testing/exploration)

### Environment & Objectives
- **Step-by-step objective chain** enforced by the game
- **Randomized spawning** of power cells and the key each run — no two games are the same
- Interactive objects: power cells, switches, key, safe, and exit door all **change state on interaction**
- **HUD overlay** always shows time left, collected items, switch/key/safe/exit status, and the current goal

---

## Running the Game

```bash
python escape_horror.py
```

Select a difficulty on the start screen, then press **Enter** to begin.

---

## Technical Details

- **Engine:** Python + PyOpenGL (GLUT/GLU)
- **Rendering:** `glBegin/glEnd`, `GL_QUADS`, `gluSphere`, `gluCylinder`, `glutSolidCube`
- **Camera:** `gluPerspective` + `gluLookAt` (first-person & orbiting top-down)
- **Collision:** AABB segment intersection against all wall definitions
- **Spawning:** Constrained random placement — avoids walls, fixed objects, and player start
- **Ghost AI:** Vector-based pursuit with time-scaled acceleration

---

## Project Structure

```
escape_horror.py    # Single-file game — all logic, rendering, and input handling
README.md
```

---



## 📝 Course Info

> CSE 423 — Computer Graphics Lab Project  
