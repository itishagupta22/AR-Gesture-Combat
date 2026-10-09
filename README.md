# AR Gesture Combat

Local 2D melee fighter controlled with a **webcam** (gestures + body movement) and a **mouse / keyboard** fallback. A physical IMU sword over serial is planned but **not wired yet**.

Playable game lives in `ar_game/`.  
Full context for teammates and other AIs: [`PROJECT_HANDOFF.md`](PROJECT_HANDOFF.md).

## Requirements

- **Python 3.10, 3.11, or 3.12** (64-bit). Do **not** use 3.13 — MediaPipe has no wheel for it.
- A **webcam** (laptop camera or USB). Default index is `0`.
- Internet on **first run** (MediaPipe `.task` models download into `ar_game/models/`).

## Setup

```bash
python -m venv venv
```

Windows:

```bat
venv\Scripts\activate
pip install -r requirements.txt
```

macOS / Linux:

```bash
source venv/bin/activate
pip install -r requirements.txt
```

## Run

```bash
cd ar_game
python main.py
```

Press **Enter** on the menu to start. **Esc** quits.

Typical console line with no hardware plugged in:

```
[HardwareInput] No physical sword detected. Mouse/Q-E mock enabled.
```

That is expected. Swing with the **mouse** (or **Q / E**).

## Controls

| Input | Action |
|---|---|
| Open palm / **B** | Shield (full block) |
| V-sign | Lock sword |
| Fist | Lock axe |
| Lean body | Move / dodge dash |
| Mouse or **Q / E** | Aim / swing weapon |
| WASD or arrows | Move (overrides body follow while held) |
| Arms crossed (hold) | Pause menu |
| Thumbs up (while paused) | Resume |
| Thumbs down (while paused) | Exit to home |
| **P** / **Y** / **N** | Pause / resume / exit (keyboard) |

## Repo layout

| Path | What it is |
|---|---|
| `ar_game/` | **Play this.** Current game. |
| `requirements.txt` | Python packages |
| `PROJECT_HANDOFF.md` | Architecture, status, known issues |
| `cv/`, `backend/`, `game/` | Unused early prototypes. Do not treat as the live app. |

Keep `ar_game/assets/` in git (arena, fighters, weapons). The game will not start without those JPEGs.

## Notes for teammates

- Weapon swing is **mouse/Q-E**, not the IMU, even if a COM port opens.
- `ar_game/models/` is gitignored; each machine downloads models itself.
- Never commit `venv/`.
- If GitHub upload is huge or includes personal files, the git root is wrong — it must be this `mini_project` folder only.
