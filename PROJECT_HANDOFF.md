# PROJECT HANDOFF DOCUMENT

## 1. Project Overview

- **Project name:** AR Gesture Combat (window title / menu: “AR GESTURE COMBAT”). Older unused prototype is titled “Human Interaction Combat”.
- **One-paragraph description:** A locally hosted 2D melee fighting game in Python/Pygame. A webcam plus MediaPipe tracks the player’s hands and body so gestures choose weapons/shield/pause, body lean moves and dodges the on-screen fighter, and a virtual sword/axe is swung with mouse or Q/E (stand-in for a future IMU sword). The player fights a rule-based melee enemy in an arena until one HP bar hits zero.
- **Problem statement:** Typical fighters are keyboard/controller-only. This project explores whether webcam pose/gesture input plus a later physical sword sensor can drive a close-range combat game without a game engine like Unity.
- **Main objective:** Playable local demo: vision-driven melee combat with shield, dodge, weapon lock, pause/exit, and a keyboard/mouse fallback. Physical IMU/ESP32 sword is the intended next hardware layer, not the current playable path.
- **What makes it different/useful:** Input is multimodal (vision + mouse/keys + optional serial). Combat is close-range melee with a virtual blade, not a generic “wave at the camera” toy. Designed so a real sword IMU can later replace the mouse-aim mock.
- **Intended users/use case:** Project teammates and demo/academic presentation. One player in front of a webcam, short 1v1 rounds. Not a shipped commercial game.

---

## 2. Final Project Concept

From the player’s perspective (intended + what the playable `ar_game` app actually does):

The player stands in front of a webcam. On screen they are a fighter (“TAIGA”) facing an AI fighter (“TSUNAMI”) in a ruins arena. They move by shifting their body; a sharp lean dashes (dodge with brief invulnerability). Open palm raises a full-block shield. V-sign locks a sword, fist locks an axe; the weapon stays until the other gesture. They swing by moving the mouse around the player (or Q/E). Hits only count in melee range with a fast enough swing. The enemy walks in, slashes, and can dodge vertically. HP is 100 each. Empty enemy bar = victory; empty player bar = defeat.

**How the player interacts**

- Webcam: gestures, body follow, dodge, pause pose, thumbs in pause menu.
- Mouse / Q-E: sword/axe angle (hardware mock).
- WASD / arrows: manual move (overrides body follow while held).
- B: shield. P / Y / N: pause menu keyboard backups. Enter: start / leave end screen. Esc: quit app.

**Webcam / computer vision:** OpenCV captures a mirrored 640×480 stream. MediaPipe Tasks HandLandmarker (up to 2 hands) and PoseLandmarker (1 pose) run in VIDEO mode. A picture-in-picture “TRACKING FEED” is drawn on the fight screen.

**Hand gestures (current intended mapping):**

| Gesture | Meaning |
|---|---|
| Open palm | Shield (full block) |
| V-sign | Lock sword |
| Fist | Lock axe |
| Arms crossed (pose) | Open pause menu (after hold) |
| Thumbs up | Resume, **only while paused** |
| Thumbs down | Exit to home, **only while paused** |

**Body movement:** Neutral pose is calibrated on first tracked frame of a round. Torso offset vs that reference lerps the fighter. Fast lean past thresholds fires a dash on that axis; player must return near center to dash again.

**Physical IoT controller/rod:** Intended = ESP32 + IMU on a prop sword, serial angle/swing into the game. **Not implemented as a working sword.** `HardwareInput` can open a COM port and collect text lines, but swing angle always comes from mouse/Q-E.

**Keyboard fallback:** Movement, shield, pause menu, weapon swing mock. No IMU required to play.

**Enemy:** FSM: IDLE (chase) → ATTACK (windup/slash/recover) → optional DODGE (vertical) or STUNNED on hit.

**Combat:** AABB hurtboxes; blade sample-points vs hurtbox; integer melee damage from swing speed; axe +3; shield = 0 damage if active; knockback + hit stun; floating “-N” / “BLOCK”, sparks, screen shake.

**Win/lose:** Enemy HP ≤ 0 → VICTORY. Player HP ≤ 0 → DEFEAT. Enter returns to menu. Thumbs-down from pause also ends the round and returns to menu (not a victory/defeat screen).

---

## 3. Current Implementation Status

| Feature | Status | Implementation | Notes |
|---|---|---|---|
| Pygame window, 1100×720, 60 FPS | WORKING | `ar_game/main.py` | Main loop + states |
| Menu / Playing / Victory / Defeat | WORKING | `Game.handle_*` | End screens are plain fill, not arena art |
| Webcam capture + PIP | WORKING | `VisionTracker.read_frame`, `draw_pip` | Camera 0; fails silently if no frame |
| MediaPipe Hands + Pose (Tasks API) | WORKING | `vision_tracker.py` | Auto-downloads `.task` models |
| Open palm → shield | WORKING | gesture registry + `shield_active` | Full block, not partial mitigation |
| V-sign → lock sword | WORKING | `_lock_weapon` | Stays locked until fist |
| Fist → lock axe | WORKING | `_lock_weapon` | Thumbs-down can look like a fist in play |
| Body follow (X/Y) | WORKING | `_update_body_movement` | Skipped while WASD/arrows held |
| Dodge dash L/R/U/D + i-frames | WORKING / NEEDS TESTING | pose thresholds + dash | Vertical dodge was previously wrong; later recoded |
| Mouse/Q-E virtual blade | WORKING | `poll_sword_angle` + `Sword` | This is the live “hardware” path |
| Melee hit detection | WORKING | `Sword.hits_hurtbox` | Sample points along blade |
| Integer melee damage + axe bonus | WORKING | `calculate_melee_damage` | 5/8/12/15, axe +3 |
| Enemy chase / slash / stun | WORKING | `bot_ai.Enemy` | Melee only |
| Enemy vertical dodge | WORKING / NEEDS TESTING | `_try_dodge` | Only vs player melee tip, 72% chance |
| Knockback both sides | WORKING | `_knock_player`, `apply_knockback` | 0.55s stun |
| Floating damage / BLOCK / sparks / shake | WORKING | `FloatText`, `Spark` | Cosmetic |
| Arena + fighter + weapon sprites | WORKING | `sprites.Visuals` | Magenta chroma-key JPEGs |
| Pause via crossed arms | NEEDS TESTING | `_detect_arm_command` | Tightened after false positives; not reconfirmed by user |
| Pause popup Resume/Exit | NEEDS TESTING | `_draw_pause_popup` | Hold bar uses 0.35s; logic uses 0.55s |
| Thumbs up/down in pause | NEEDS TESTING | `thumb` field | Ignored unless `paused` |
| Keyboard pause P / Y / N | WORKING | `handle_playing` | Reliable fallback |
| Serial port autodetect | PARTIALLY WORKING | `HardwareInput._try_connect` | Opens first COM port that doesn’t throw; lines unused for angle |
| IMU sword angle | PLANNED | not in `poll_sword_angle` | Mouse always used for angle |
| ESP32 firmware / protocol spec | PLANNED | **no firmware in repo** | Baud 9600, newline text only |
| Projectile combat (fireball/arrow) | UNUSED/LEGACY | `Projectile`, `calculate_hitpoints` | Not spawned in `main.py` |
| ROD/BOW hardware modes | UNUSED/LEGACY | `MODE_ROD/BOW`, `select_hardware_mode_menu` | Menu never shown; game forces `MODE_SWORD` |
| `cv/`, `backend/`, `game/` prototype | UNUSED/LEGACY | separate scripts | Not imported by `ar_game` |
| Automated tests | PLANNED | none | No pytest/unittest |
| README accuracy | UNUSED/LEGACY | `ar_game/README.md` | Describes fireballs, ROD/BOW, old keys — **conflicts with code** |

---

## 4. Complete Architecture

**Intended / logical pipeline**

```
Webcam                 Mouse/Keys              Serial (planned IMU)
   |                       |                          |
   v                       v                          v
OpenCV frame          Pygame events            COM readline
   |                       |                          |
   v                       v                          v
MediaPipe Hands/Pose   HardwareInput mock      (not mapped to angle)
   |                       |                          |
   +-----------+-----------+-----------+--------------+
               v
     vision_data dict + sword angle + keys
               v
     Game.handle_playing  (NO Action Manager)
               |
     +---------+---------+
     v                   v
 pause / weapon lock   movement / shield / swing
     |                   |
     v                   v
                  combat + Enemy FSM
                         |
                         v
              physics_engine (AABB, Sword, melee dmg)
                         |
                         v
              sprites + HUD + PIP + pause popup
                         |
                         v
                   Pygame display
```

**Step-by-step data flow (actual `ar_game`)**

1. `Game.run` → MENU / PLAYING / VICTORY / DEFEAT.
2. PLAYING: `VisionTracker.read_frame()` (flip horizontal).
3. `VisionTracker.process(frame)` → dict: `gesture`, `shield_area`, `dodge`, `dodge_v`, `arm_command`, `thumb`, `body_dx/dy`, `pose_tracked`, landmarks.
4. Keys: pause, movement, B shield.
5. `hardware.poll()` — **return value discarded**.
6. `hardware.poll_sword_angle(player pos)` — **mouse/Q-E only**.
7. If not paused: lock weapon, move, update sword, `enemy.update`, `_resolve_melee`.
8. FX + `_render_game`.

**Does the code follow a clean Action Manager architecture?**  
**No.** `backend/action_manager.py` exists but is **not used** by `ar_game`. Gestures are interpreted inside `VisionTracker` and consumed directly in `Game`. That is a documented deviation from the older `cv/` + `backend/` + `game/` design.

**Other deviations**

- Serial events never become sword angle.
- Projectile physics remain in `physics_engine.py` but combat is melee-only.
- Enemy `incoming` projectile list is unused; dodge is melee-tip only.
- Pause popup fill duration (0.35) ≠ pause hold (0.55).

---

## 5. Complete File Structure

Observed layout (assets/models may not list in search if ignored; `sprites.py` / `vision_tracker.py` require them):

```
mini_project/
├── requirements.txt
├── PROJECT_HANDOFF.md
├── ar_game/                    ← PLAYABLE APPLICATION
│   ├── main.py
│   ├── vision_tracker.py
│   ├── physics_engine.py
│   ├── bot_ai.py
│   ├── hardware_input.py
│   ├── sprites.py
│   ├── README.md               ← outdated
│   ├── assets/                 ← expected JPEGs (see sprites.py)
│   │   ├── arena_ruins.jpg
│   │   ├── player_fighter.jpg
│   │   ├── enemy_fighter.jpg
│   │   ├── sword.jpg
│   │   └── axe.jpg             ← optional; falls back to sword
│   └── models/                 ← auto-downloaded on first run
│       ├── hand_landmarker.task
│       └── pose_landmarker.task
├── cv/                         ← UNUSED webcam prototype
│   ├── hand_tracking.py
│   ├── pose_tracking.py
│   ├── gesture_detector.py
│   └── movement_detector.py
├── backend/                    ← UNUSED
│   ├── action_manager.py
│   └── keyboard_controller.py
└── game/                       ← UNUSED pygame prototype
    ├── game.py
    ├── player.py
    └── input_handler.py
```

### Playable (`ar_game`) — used by `python main.py`

**`main.py`**  
Entry point. `Game`, HUD helpers, pause popup, melee resolve. Imports vision, hardware, physics, enemy, sprites. **Used.**

Important: `Game`, `FloatText`, `Spark`, `draw_menu`, `draw_end_screen`, `draw_pip`. States `STATE_MENU/PLAYING/VICTORY/DEFEAT`.

**`vision_tracker.py`**  
CV pipeline. `VisionTracker`. **Used.**

**`physics_engine.py`**  
`AABB`, `Sword`, `calculate_melee_damage`, `WEAPON_LENGTH`. Also leftover `Projectile` + `calculate_hitpoints` (**not called from main**). **Partially used.**

**`bot_ai.py`**  
`Enemy` FSM. **Used.** `self.projectiles` unused.

**`hardware_input.py`**  
`HardwareInput`, `poll_sword_angle`. `select_hardware_mode_menu` **never called**. **Partially used.**

**`sprites.py`**  
`Visuals`. **Used.** Missing required JPEGs will crash at startup.

**`README.md`**  
**Not used at runtime.** Conflicts with current game (see §17).

**`requirements.txt` (repo root)**  
Install list. **Used for setup, not imported.**

### Unused / experimental

| File | What it does | Used by main app? |
|---|---|---|
| `cv/hand_tracking.py` | Standalone OpenCV window, prints gestures | No |
| `cv/pose_tracking.py` | Standalone pose + dodge print | No |
| `cv/gesture_detector.py` | VICTORY / OPEN_PALM / FIST / INDEX_UP | No (`ar_game` has its own detectors) |
| `cv/movement_detector.py` | Horizontal dodge only | No |
| `backend/action_manager.py` | Maps FIST→ATTACK, VICTORY→SELECT_BOW, etc. | No |
| `backend/keyboard_controller.py` | `keyboard` lib CLI | No; `keyboard` not in requirements |
| `game/game.py` | 1000×600 rectangles, keyboard only | No |
| `game/player.py` | Rect player, SWORD/BOW | No |
| `game/input_handler.py` | Space/B/arrows/1/2 | No |

---

## 6. Computer Vision System

**OpenCV:** `VideoCapture(0)`, 640×480, `flip(1)` mirror, BGR→RGB, PIP via `cv2_frame_to_surface`.

**MediaPipe:** Tasks API (`mp.tasks.vision`), **not** the old `mp.solutions` Holistic API.

- Hands: `HandLandmarker`, VIDEO, `num_hands=2`, conf 0.6. Combat gestures use **hand 0 only**. Thumbs scan **all detected hands**.
- Pose: `PoseLandmarker` lite, VIDEO, `num_poses=1`, conf 0.6.

**Models** (`ar_game/models/`, downloaded if missing):

- `hand_landmarker.task` ← Google `hand_landmarker/float16/latest`
- `pose_landmarker.task` ← `pose_landmarker_lite/float16/latest`

First run needs network. Models may not be committed to git.

**Frame pipeline**

1. Read + mirror
2. RGB `mp.Image`
3. Monotonic `timestamp_ms`
4. `detect_for_video` hands then pose
5. Fill result dict

**Finger logic:** tip.y < pip.y ⇒ extended (camera Y down). Tips 4,8,12,16,20 vs PIPs 3,6,10,14,18.

**Play registry (order matters):**

1. `SHIELD` — ≥4 fingers extended (`_is_open_palm`)
2. `SWORD` — index+middle up, ring+pinky down (`_is_victory_sign`; thumb ignored)
3. `AXE` — 0 fingers extended (`_is_closed_fist`)

**Thumbs (not in registry):** other fingers mostly curled; thumb tip vs wrist and other tips. `thumb`: `"UP"` / `"DOWN"` / `None`.

**Pause pose:** wrists at chest, each past midline by `0.28 * shoulder_span`, wrists close, elbows out, wrist beyond own elbow, visibility ≥ 0.45. Returns `"PAUSE"` only.

**Dodge / body**

- Center: shoulders+hips X; Y = 0.45×nose + 0.55×shoulders; scale = torso height.
- First pose frame sets `center_x_ref`, `center_y_ref`, `torso_ref`.
- `body_dx/dy` = (current − ref) / torso.
- Dash X if `|body_dx| > 0.07`; Y if `|body_dy| > 0.045`; reset when `|offset| < 0.03`.
- Recalibrated on `reset_game()`.

**Exact current vision vocabulary**

| Detector output | Values |
|---|---|
| `gesture` | `SHIELD`, `SWORD`, `AXE`, or `None` |
| `thumb` | `UP`, `DOWN`, or `None` |
| `arm_command` | `PAUSE` or `None` |
| `dodge` | `DODGE_LEFT`, `DODGE_RIGHT`, or `None` |
| `dodge_v` | `DODGE_UP`, `DODGE_DOWN`, or `None` |

**Conflicts vs design**

- Thumbs should do nothing in play; thumbs-down often matches **fist → AXE lock**.
- README still says fist = fireball, V-sign = arrow.
- Legacy `cv/gesture_detector.py` uses `VICTORY`/`OPEN_PALM`/`FIST`/`INDEX_UP` — different names, unused.
- Pause was originally “parallel arms”; **current code is crossed arms**, not parallel.

---

## 7. Input and Action System

There is **no** live Action Manager. Live mapping:

| Input | Intermediate | Game action |
|---|---|---|
| Open palm | `gesture=SHIELD` | Shield on (or key B) |
| V-sign | `gesture=SWORD` | Lock sword if not already |
| Fist | `gesture=AXE` | Lock axe if not already |
| Crossed arms held 0.55s (after 1.4s round grace) | `arm_command=PAUSE` | `paused=True`, popup |
| Thumbs up held 0.55s while paused | `thumb=UP` | Unpause, keep fight |
| Thumbs down held 0.55s while paused | `thumb=DOWN` | `STATE_MENU` |
| Lean | `dodge` / `dodge_v` | Dash + 0.28s i-frames, 0.55s CD |
| Continuous pose offset | `body_dx/dy` | Lerp fighter unless keys held |
| Mouse vs player | angle rad | Blade follow |
| Q / E | `_kb_angle` | Rotate blade |
| WASD / arrows | keys | Move 7 px/frame |
| B | key | Shield |
| P | key | Open pause |
| Y / Enter while paused | key | Resume |
| N / Backspace while paused | key | Menu |
| Enter on menu | key | Start round |
| Enter on end | key | Menu |
| Esc / window close | event | Quit process |
| Serial line | `last_events` set | **Not applied** |

`Game.hardware.poll()` is called every frame and **ignored**.

---

## 8. Hardware / IoT

**ESP32 role:** Planned MCU for IMU (and maybe buttons). **No firmware, wiring diagram, or pinout in this repo.**

**Sensors:** Intended IMU (e.g. MPU-6050 / BNO055) discussed for purchasing. **Not in software.**

**Communication:** Optional `pyserial`, baud **9600**, timeout 0.05s. Autodetects **all COM ports** and uses the first that opens.

**Protocol (as coded):** newline-terminated strings, decoded, `.upper()`, stored in a set. **No JSON, no angle fields, no checksum.**

**Expected messages:** Unspecified. Legacy comments (README) mention TRIGGER / CHARGE / RELOAD — **those keys are not in `main.py`.**

**Hardware modes:** `MODE_SWORD`, `MODE_ROD`, `MODE_BOW` exist. Live game **always** `MODE_SWORD`. Mode does not change `poll_sword_angle`.

**Fallback:** If no serial: print mock enabled; mouse + Q/E.

**Implemented vs remaining**

| Done | Not done |
|---|---|
| pyserial import, port open, listener thread | Parse IMU yaw/pitch into `poll_sword_angle` |
| Mouse/Q-E angle | ESP32 sketch |
| | Device filter (VID/PID); currently any COM port |
| | Calibration, wireless, hilt buttons, haptic |

---

## 9. Game Engine / Pygame

- **Size:** 1100×720. **FPS:** 60. **Caption:** AR Gesture Combat.
- **States:** MENU → PLAYING → VICTORY or DEFEAT → MENU. Pause is a flag inside PLAYING, not a state.
- **Menu:** Arena background dimmed, gesture list, “PRESS ENTER TO START”.
- **Gameplay:** Arena, fighters, weapons, HP, PIP, status panel, optional pause card.
- **Victory/Defeat:** Solid bg, title, “PRESS ENTER TO RETURN TO MENU”.
- **Player:** Sprite + `player_x/y`, not a class. HUD name **TAIGA**. HP 100.
- **Enemy:** `Enemy` + sprite. HUD name **TSUNAMI**. HP 100. Always drawn with sword (even if player has axe).
- **HUD:** HP bars, weapon lock line, enemy state, GESTURE/DODGE/range panel.
- **PIP:** 240×180, bottom-right; green border if tracked, red otherwise.
- **Render:** Background (shake offset) → HUD → fighters/weapons → shield circle → melee-range ring on enemy → sparks/text → flash → PIP → pause overlay.
- **Input:** Pygame events + `key.get_pressed` + vision dict + mouse.

---

## 10. Enemy AI

**Architecture:** Finite state machine in `bot_ai.py`.

**States:** `IDLE`, `ATTACK`, `DODGE`, `STUNNED`.

**Transitions**

- IDLE: chase; if dist ≤ 205 and idle timer elapsed → ATTACK.
- ATTACK: windup 0.28s, slash 0.18s, recover 0.42s → IDLE. If player farther than 245, chase during attack. No dodge while ATTACK.
- DODGE: vertical dash 0.28s → IDLE. Trigger: player melee tip within 95 px, 72% chance, cooldown 0.85s (0.4× if roll fails).
- Hit: `apply_knockback` → STUNNED 0.55s with i-frames.
- STUNNED → IDLE after stun.

**Attack:** One sword slash toward player. Damage resolved in `Game._resolve_melee` if `can_strike` and blade hits player AABB.

**Projectiles:** `Enemy.projectiles = []` unused. `incoming` unused for threats.

**Difficulty knobs:** `CHASE_SPEED=4.6`, `WANDER_SPEED=1.4`, `DASH_SPEED=14`, `DODGE_CHANCE=0.72`, `MELEE_ENGAGE=205`, `HIT_STUN=0.55`. No difficulty enum.

---

## 11. Physics and Combat

**Projectile system:** Class + `calculate_hitpoints` (velocity^1.5, distance falloff, shield up to 85%) exist **but current combat does not spawn projectiles.** `Game.player_projectiles` is always `[]`.

**Collision:** AABB overlap; melee uses **point-in-AABB** on 5 sample points along the blade (i=2..n, n=6).

**Melee damage (`calculate_melee_damage`)**

| `abs(omega)` | Base | Axe |
|---|---|---|
| < 5 | 5 | 8 |
| < 9 | 8 | 11 |
| < 14 | 12 | 15 |
| ≥ 14 | 15 | 18 |

If `shield_area > 0`, function returns 0 — **player hits do not pass shield_area**; enemy hits are skipped entirely when `shield_active` (binary full block). Visual shield radius uses hand spread; **block strength does not**.

**Distance falloff:** Projectile-only leftover. Melee uses `MELEE_RANGE = 210` (player) vs enemy engage 205.

**Velocity:** `Sword.omega` = angle delta / dt. Swing if `|omega| ≥ 3.2`. Enemy strike uses `max(|omega|, 6.0)` as sword.

**HP:** Player `PLAYER_MAX_HP=100`; enemy 100. Win/lose on ≤ 0.

**Other constants:** hurtboxes 40 / 52; knockback 18; hit stun 0.55; sword hit CD 0.45; dash 16 px/frame × 0.18s; dodge CD 0.55; i-frames 0.28.

---

## 12. Weapons / Combat Mechanics

| Weapon | Select | Attack | Behavior | Damage | Block/dodge | Status |
|---|---|---|---|---|---|---|
| **SWORD** | Default; V-sign | Mouse/Q-E swing | Length 160, sprite sword | 5–15 | Shield full-blocks enemy; dodge i-frames | WORKING |
| **AXE** | Fist lock | Same swing | Length 138, sprite axe | sword +3 | Same | WORKING |
| **Shield** | Palm or B | Hold | Circle visual; no HP loss | 0 incoming | Binary; size is visual only | WORKING |
| **Fireball / Arrow / Bow / Rod** | — | — | Projectile leftovers / README / unused modes | — | — | UNUSED/LEGACY |

Enemy always uses a virtual **sword**, not axe.

---

## 13. Current Controls

| Input | Action | Current behavior |
|---|---|---|
| Open palm | Shield | Full block while held |
| V-sign | Lock sword | Switches if current weapon is axe |
| Fist | Lock axe | Switches if current weapon is sword |
| Arms crossed (hold ~0.55s) | Pause | Popup; combat frozen |
| Thumbs up (paused, hold) | Resume | Same round continues |
| Thumbs down (paused, hold) | Exit | Menu; round discarded |
| Lean L/R/U/D | Dodge dash | i-frames; must recenter to repeat |
| Shift body (slow) | Move fighter | Lerp vs calibrated center |
| Mouse | Aim blade | Angle from player to cursor |
| Q / E | Rotate blade | ±0.11 rad/frame; overrides mouse while held |
| WASD / arrows | Move | 7 px/frame; disables body follow |
| B | Shield | Same as palm |
| P | Pause | Opens menu only (does not toggle off) |
| Y / Enter (paused) | Resume | Keyboard |
| N / Backspace (paused) | Exit to menu | Keyboard |
| Enter (menu) | Start | Reset + PLAYING |
| Enter (end) | Menu | No auto-restart |
| Esc | Quit app | Full exit |
| ESP32/serial | — | Lines stored, **not bound to combat** |

---

## 14. Installation

**Python:** 3.10, 3.11, or 3.12 **64-bit**. Avoid 3.13 (no MediaPipe wheel). Stated in `requirements.txt`; not pinned by a lockfile.

**From a fresh copy (Windows):**

```bat
cd mini_project
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

**macOS/Linux:** `source venv/bin/activate` instead.

**Dependencies (ranges, not frozen):**

- `pygame>=2.5.0,<3`
- `opencv-python>=4.8.0,<4.12`
- `mediapipe>=0.10.14,<1.1`
- `numpy>=1.26.0`
- `pyserial>=3.5`

No exact installed versions are recorded in-repo.

**Models:** First `VisionTracker()` download into `ar_game/models/`. Needs internet once.

**Assets:** `ar_game/assets/*.jpg` required except `axe.jpg` (falls back to sword).

**Hardware:** Optional. Webcam required for vision; mouse/keys work without it (no pose). Serial device optional and currently unused for swinging.

**Extra:** Unused `backend/keyboard_controller.py` needs `keyboard` (not in requirements).

---

## 15. Running the Project

```bat
cd ar_game
python main.py
```

**After launch**

1. Window opens; camera starts; models load/download.
2. Console: `[HardwareInput] No physical sword detected. Mouse/Q-E mock enabled.` (typical).
3. Menu: gestures + Enter to start.
4. Fight: vision + mouse swing. Esc quits.

**Do not** follow `ar_game/README.md` for ROD/BOW/fireball — it is stale.

**Legacy (not the demo):** `python game/game.py` or `python cv/hand_tracking.py` from a PYTHONPATH that includes the repo root; separate from the real game.

---

## 16. Testing Already Performed

No automated tests. Evidence is interactive play from development:

**Confirmed in play (then iterated)**

- Melee arena, enemy walk-in slash, knockback, damage numbers, shield, sprites, weapon lock — user played these.
- Dodge originally moved “front/back” instead of up/down — **fixed in code**; later confirmation not documented in-repo.
- Pause originally wrong pose / full-screen overlay / false opens — **recoded**; last “too sensitive” fix **not confirmed** by a later user message.
- `python -m py_compile main.py vision_tracker.py` succeeded after pause work.

**Not evidenced**

- ESP32/IMU.
- Teammate install on a clean machine.
- Quantitative accuracy (gesture precision/recall, FPS on other PCs).
- Pause thumbs + crossed arms after the latest detector tighten.

---

## 17. Known Issues / Bugs / Limitations

- **`ar_game/README.md` contradicts the game** (fireballs, ROD/BOW, Space/Shift/R).
- **Pause UI vs logic:** popup fill 0.35s, hold 0.55s.
- **Thumbs-down ≈ fist** can lock axe while playing.
- **Pause false positives** were reported; detector was tightened — may now **miss** real crossed arms (unverified).
- **Serial autodetect** may grab a random COM port; even then angle is still mouse.
- **`poll()` discarded.**
- **Webcam index hardcoded to 0.**
- **No camera:** PIP missing; pose/gestures None; mouse/keys still work.
- **CV:** lighting, distance, occlusion, similar gestures (fist vs thumbs, palm vs five-finger swing).
- **MediaPipe VIDEO timestamps** from wall clock; can skip/jitter.
- **Enemy** only dodges vertically; unused `incoming`.
- **Dead code:** projectiles, `player_projectiles`, `calculate_hitpoints`, ROD/BOW menu, `cv/`/`backend/`/`game/`.
- **Naming:** `calculate_hitpoints` is damage; HUD Taiga/Tsunami vs generic “player/enemy”; `arm_command` only PAUSE.
- **End screens** ignore arena art.
- **Performance:** Hands + Pose every frame + pygame; no FPS HUD; weak laptops may drop below 60.
- **Windows MediaPipe** install is a common teammate failure (wrong Python).
- **Chroma-key** depends on magenta JPEG backdrops.
- **No tests / CI / lockfile.**

---

## 18. Technical Decisions

| Decision | Reason (only where known) |
|---|---|
| Pygame, not Unity | Local Python mini-project; CV already in Python |
| Dual folders `ar_game` vs `cv/backend/game` | Prototype then a second playable app; old tree left in place |
| MediaPipe **Tasks** VIDEO landmarkers | Matches `cv/` scripts; `.task` models |
| Game consumes vision dict directly | No action_manager integration in the live app |
| Melee instead of projectiles | Explicit pivot to Shadow Fight 3–style close combat + future IMU sword |
| Mouse/Q-E mock | IMU not built; `poll_sword_angle` docstring says “IMU mock” |
| Rule-based enemy FSM | Implemented that way; no ML |
| Integer melee damage | SF3-like floating -5/-8/… |
| Full shield block | Design: open palm ⇒ no HP loss |
| Weapon lock until opposite gesture | Avoid flicker while swinging |
| Crossed arms pause + thumbs only in menu | After parallel-arm pause failed in testing |
| AABB + blade samples | Simple 2D melee |
| JPEG + magenta key | Photo assets, not PNG alpha |
| pyserial optional try/import | Game runs without serial |

Do not invent Unity-vs-Unreal or “research-proven” claims beyond this.

---

## 19. Development History

Established from repo layers + implementation chat (not a formal changelog):

1. **Initial concept:** Webcam HCI combat; keyboard prototype `game/` + `backend/action_manager` (FIST=ATTACK, VICTORY=BOW, INDEX_UP=SWORD).
2. **CV scripts:** Standalone `cv/hand_tracking.py` / `pose_tracking.py` printing gestures/dodges.
3. **Playable `ar_game`:** Pygame + MediaPipe; README describes **projectile** era (fist fireball, V-sign arrow, rod/bow).
4. **Physics leftovers:** `Projectile`, `calculate_hitpoints` remain from that era.
5. **Pivot to melee:** Virtual `Sword`, close range, mouse mock, enemy chase/slash.
6. **Body dodge** added; vertical axis corrected after user report.
7. **SF3-like combat:** stun, knockback, floating HP, full palm shield.
8. **Visuals:** arena/fighter/weapon sprites.
9. **Weapon lock:** V-sign sword, fist axe; projectiles removed from play.
10. **Pause UX:** crossed arms → small popup; thumbs up/down; false-pause tightened.
11. **`requirements.txt`** added for teammates. **IMU still planned.**

---

## 20. Current TODO / Next Steps

### Critical

- Verify pause (cross / thumbs / no false open) on a real webcam.
- Fix thumbs-down vs fist stealing axe in play, or document it.
- Sync pause hold times (0.35 vs 0.55).
- Replace or delete stale `README.md`.
- Confirm `assets/` and first-run model download on a teammate PC.

### Important

- Map serial IMU into `poll_sword_angle`; stop using a random COM port.
- Add ESP32 firmware + a one-page protocol.
- Ignore `hardware.poll()` or actually use it.
- Camera index / no-camera message.
- Demo script (gestures, pause, melee, fallback).
- PPT/report from this handoff without claiming unmeasured results.

### Optional

- Delete or archive `cv/`, `backend/`, `game/`.
- Remove dead projectile code or restore ranged as a mode.
- Difficulty levels, more enemy tells, audio.
- PNG assets; FPS overlay; landmark debug PIP.
- Automated smoke tests (headless pygame is hard; at least import/compile).

---

## 21. Research Context

Literature-relevant **aspects of this codebase** (not claimed gaps or results):

- **Gesture HCI:** discrete hand poses (palm, V, fist, thumbs) as game commands.
- **Vision-based play:** webcam as primary controller vs keyboard fallback.
- **Pose interaction:** torso-relative locomotion and dodge.
- **Multimodal input:** vision + mouse/keys + planned IMU.
- **Real-time CV:** MediaPipe Tasks in a 60 FPS loop; latency/robustness.
- **IoT–game coupling:** serial IMU as a physical blade (designed, not measured).
- **Human-centered fighting games:** full-body shield/dodge vs button block.

Any “research gap” slide must come from a **separate literature review**. This repo has **no papers, no user study, no accuracy tables**.

---

## 22. PPT / Academic Presentation Context

Use this as source material; **do not fabricate numbers**.

- **Problem statement:** Standard fighters ignore body/gesture/physical weapon input; this demo explores webcam + (future) IMU melee control.
- **Objectives:** Real-time gesture/pose combat; melee AI; keyboard/mouse fallback; path to ESP32 IMU.
- **Methodology:** Python prototype; MediaPipe landmarks → rules; Pygame loop; FSM enemy; AABB melee; iterative playtesting (dodge axis, pause pose).
- **Architecture:** Diagram in §4. Stress: **no live Action Manager**.
- **Stack:** Python 3.10–3.12, Pygame, OpenCV, MediaPipe Tasks, NumPy, pyserial; planned ESP32+IMU.
- **Literature review:** Must be done outside this repo (gesture games, MediaPipe, exergames, IMU weapons).
- **Research gap:** Only after reading papers; e.g. many gesture demos are ranged/UI, while this targets melee + planned tangible sword — **as a positioning claim, not a proven finding**.
- **Proposed solution:** Local AR-style 2D fighter with vision + virtual blade mock.
- **Results:** Qualitative only: playable melee loop, vision HUD, fallback without hardware. **No FPS, accuracy, or user-study data in-repo.**
- **Limitations:** Lighting/camera; gesture confusion; IMU not integrated; README drift; dual dead codebases; pause still under test.
- **Future scope:** IMU sword, protocol, studies, polish, cleanup.

---

## 23. Important Terminology

| Term | Meaning |
|---|---|
| AR Gesture Combat | Playable app in `ar_game/` |
| TAIGA / TSUNAMI | HUD names for player / enemy |
| `VisionTracker` | Hands + pose wrapper |
| `gesture_registry` | SHIELD / SWORD / AXE detectors |
| `arm_command` | Currently only `PAUSE` |
| `thumb` | `UP`/`DOWN` for pause menu |
| Weapon lock | SWORD/AXE until opposite sign |
| `Sword` | Virtual blade: `angle`, `omega`, sample hits |
| `omega` | Angular velocity (rad/s-ish via delta/dt) |
| AABB | Axis-aligned hurtbox |
| PIP | Webcam inset |
| FSM | Enemy IDLE/ATTACK/DODGE/STUNNED |
| i-frames | Invulnerable until timestamp |
| IMU mock | Mouse/Q-E aiming |
| Tasks API | MediaPipe `mp.tasks` landmarkers |
| Action Manager | Unused `backend/action_manager.py` |
| Legacy tree | `cv/`, `backend/`, `game/` |
| `MODE_ROD` / `MODE_BOW` | Unused hardware enums |

---

# Instructions for AI Assistants Continuing This Project

- Inspect **current `ar_game/` code** before any architecture rewrite.
- Do **not** assume Action Manager, projectiles, ROD/BOW, or IMU aiming are live.
- Preserve working melee, shield, weapon lock, sprites, and keyboard/mouse fallback.
- Treat **README vs code** as a conflict; prefer code.
- Make **incremental** changes; don’t rebuild Unity-style layers without a request.
- Say where a change sits (vision dict, `Game.handle_playing`, `Enemy`, `HardwareInput.poll_sword_angle`).
- Do **not** invent papers, metrics, or “tested on N users”.
- Ask if pause vs IMU vs deleting legacy folders is ambiguous.
- Label **current vs proposed** clearly.
- Do not put secrets in docs (none are in this repo).
- Prefer fixing `poll_sword_angle` over new input frameworks when adding IMU.
- Don’t revive fireballs unless the user asks; combat was explicitly moved to melee.

---

## PROJECT SNAPSHOT

```
AR Gesture Combat = Python/Pygame 1100x720 melee fighter in mini_project/ar_game/.
Play: python main.py from ar_game after pip install -r requirements.txt (Python 3.10–3.12).
Vision: OpenCV cam0 + MediaPipe Tasks Hands(2) + Pose(1). Gestures: palm=shield, V=lock sword, fist=lock axe.
Pose: body follow + dodge dashes. Pause: crossed arms → popup; thumbs up=resume, thumbs down=menu (pause only).
Combat: virtual Sword/Axe, mouse/Q-E aim (IMU NOT wired), AABB blade samples, integer dmg, full shield block, knockback.
Enemy FSM: chase, slash, vertical dodge, stun. HP 100. No live projectiles.
HardwareInput may open a COM port but poll() is unused and angle is always mouse/Q-E. No ESP32 firmware in repo.
IGNORE cv/, backend/, game/, and ar_game/README.md (stale fireball/ROD/BOW docs). There is no Action Manager in the live path.
Pause thumbs/cross recently retuned and need webcam retest. Thumbs-down can look like fist/axe while playing.
```
