"""AR Gesture Combat — Main Game Loop. Maximalist neon UI."""
import sys
import time
import math
import random
import cv2
import pygame
import numpy as np

from vision_tracker import VisionTracker
from hardware_input import HardwareInput, MODE_SWORD
from physics_engine import (
    AABB, compute_velocity, Sword, calculate_melee_damage, WEAPON_LENGTH,
)
from bot_ai import Enemy
from sprites import Visuals

# ---------------- CONFIG ----------------
SCREEN_W, SCREEN_H = 1100, 720
PIP_W, PIP_H = 240, 180
PIP_MARGIN = 24
FPS = 60
PLAYER_MAX_HP = 100
PLAYER_HOME_X, PLAYER_HOME_Y = SCREEN_W // 2 - 90, SCREEN_H // 2
ENEMY_HOME_X, ENEMY_HOME_Y = SCREEN_W // 2 + 90, SCREEN_H // 2
ARENA_MIN_X, ARENA_MAX_X = 80, SCREEN_W - 80
PLAYER_MIN_X, PLAYER_MAX_X = ARENA_MIN_X, ARENA_MAX_X
PLAYER_MIN_Y, PLAYER_MAX_Y = 80, SCREEN_H - 80
BODY_MOVE_GAIN_X = 720.0
BODY_MOVE_GAIN_Y = 640.0
BODY_FOLLOW_LERP = 0.28
KEY_MOVE_SPEED = 7.0
DASH_SPEED = 16.0
DASH_DURATION = 0.18
DODGE_COOLDOWN = 0.55
DODGE_IFRAMES = 0.28
MELEE_RANGE = 210.0
SWING_MIN_OMEGA = 3.2
SWORD_HIT_COOLDOWN = 0.45
ENEMY_HURTBOX = 52
PLAYER_HURTBOX = 40
HIT_STUN = 0.55
KNOCKBACK = 18.0
SHAKE_TIME = 0.22
FLOAT_TEXT_LIFE = 0.9

COLORS = {
    "bg": (10, 8, 20),
    "bg2": (20, 16, 36),
    "white": (245, 245, 245),
    "neon_pink": (255, 25, 130),
    "neon_cyan": (30, 245, 220),
    "neon_yellow": (245, 235, 20),
    "neon_green": (60, 250, 120),
    "neon_purple": (170, 60, 255),
    "border": (255, 255, 255),
    "danger": (255, 40, 40),
}

STATE_MENU = "MENU"
STATE_PLAYING = "PLAYING"
STATE_VICTORY = "VICTORY"
STATE_DEFEAT = "DEFEAT"


def build_fonts():
    pygame.font.init()
    return {
        "title": pygame.font.SysFont("arialblack,impact,sans-serif", 64, bold=True),
        "heading": pygame.font.SysFont("arialblack,impact,sans-serif", 36, bold=True),
        "body": pygame.font.SysFont("consolas,couriernew,monospace", 22, bold=True),
        "small": pygame.font.SysFont("consolas,couriernew,monospace", 16, bold=True),
        "damage": pygame.font.SysFont("arialblack,impact,sans-serif", 40, bold=True),
        "hpnum": pygame.font.SysFont("consolas,couriernew,monospace", 18, bold=True),
    }


def draw_brutalist_panel(screen, rect, fill, border_color, border_w=6, shadow=True):
    x, y, w, h = rect
    if shadow:
        pygame.draw.rect(screen, (0, 0, 0), (x + 8, y + 8, w, h))
    pygame.draw.rect(screen, fill, (x, y, w, h))
    pygame.draw.rect(screen, border_color, (x, y, w, h), border_w)


def draw_hp_bar(screen, font, x, y, w, h, ratio, label, color, bg_color):
    draw_brutalist_panel(screen, (x, y, w, h), bg_color, COLORS["border"], 4, shadow=False)
    fill_w = int((w - 8) * max(0, min(1, ratio)))
    pygame.draw.rect(screen, color, (x + 4, y + 4, fill_w, h - 8))
    txt = font["small"].render(label, True, COLORS["white"])
    screen.blit(txt, (x + 8, y - 22))


def cv2_frame_to_surface(frame):
    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    frame_rgb = np.rot90(frame_rgb)
    surf = pygame.surfarray.make_surface(frame_rgb)
    return pygame.transform.flip(surf, True, False)


def draw_pip(screen, cam_frame, font, tracked=False):
    """Picture-in-picture webcam feed bottom-right showing physical tracking area."""
    px = SCREEN_W - PIP_W - PIP_MARGIN
    py = SCREEN_H - PIP_H - PIP_MARGIN
    surf = cv2_frame_to_surface(cam_frame)
    surf = pygame.transform.scale(surf, (PIP_W, PIP_H))
    border_color = COLORS["neon_green"] if tracked else COLORS["danger"]
    pygame.draw.rect(screen, (0, 0, 0), (px - 6, py - 6, PIP_W + 12, PIP_H + 12))
    screen.blit(surf, (px, py))
    pygame.draw.rect(screen, border_color, (px, py, PIP_W, PIP_H), 5)
    label = font["small"].render("TRACKING FEED", True, border_color)
    screen.blit(label, (px, py - 22))


def draw_menu(screen, fonts, visuals=None):
    if visuals is not None:
        visuals.draw_bg(screen)
        dim = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        dim.fill((8, 6, 16, 120))
        screen.blit(dim, (0, 0))
    else:
        screen.fill(COLORS["bg"])
        for i in range(0, SCREEN_W, 40):
            pygame.draw.line(screen, COLORS["bg2"], (i, 0), (i, SCREEN_H), 1)
    title = fonts["title"].render("AR GESTURE COMBAT", True, COLORS["neon_pink"])
    screen.blit(title, (SCREEN_W // 2 - title.get_width() // 2, 36))

    box = pygame.Rect(SCREEN_W // 2 - 320, 130, 640, 280)
    draw_brutalist_panel(screen, box, COLORS["bg2"], COLORS["neon_yellow"], 6)
    lines = [
        "V-SIGN          -> LOCK SWORD",
        "FIST            -> LOCK AXE",
        "OPEN PALM / B   -> SHIELD (FULL BLOCK)",
        "ARMS CROSSED    -> PAUSE MENU",
        "THUMBS UP       -> RESUME (IN PAUSE)",
        "THUMBS DOWN     -> EXIT TO HOME (IN PAUSE)",
        "MOUSE / Q-E     -> SWING WEAPON",
    ]
    for i, line in enumerate(lines):
        t = fonts["body"].render(line, True, COLORS["white"])
        screen.blit(t, (box.x + 28, box.y + 18 + i * 36))

    sub = fonts["heading"].render(">> PRESS ENTER TO START <<", True, COLORS["neon_cyan"])
    screen.blit(sub, (SCREEN_W // 2 - sub.get_width() // 2, box.bottom + 28))
    pygame.display.flip()


def draw_end_screen(screen, fonts, victory):
    screen.fill(COLORS["bg"])
    text = "VICTORY" if victory else "DEFEAT"
    color = COLORS["neon_green"] if victory else COLORS["danger"]
    title = fonts["title"].render(text, True, color)
    screen.blit(title, (SCREEN_W // 2 - title.get_width() // 2, 280))
    sub = fonts["body"].render("PRESS ENTER TO RETURN TO MENU", True, COLORS["neon_cyan"])
    screen.blit(sub, (SCREEN_W // 2 - sub.get_width() // 2, 380))
    pygame.display.flip()


class FloatText:
    def __init__(self, x, y, text, color, life=FLOAT_TEXT_LIFE):
        self.x, self.y = float(x), float(y)
        self.text = text
        self.color = color
        self.born = time.time()
        self.life = life

    def update(self, dt):
        self.y -= 70.0 * dt

    def alive(self):
        return (time.time() - self.born) < self.life


class Spark:
    def __init__(self, x, y, color):
        self.x, self.y = float(x), float(y)
        ang = random.uniform(0.0, math.tau)
        spd = random.uniform(90, 240)
        self.vx = math.cos(ang) * spd
        self.vy = math.sin(ang) * spd - 80
        self.color = color
        self.born = time.time()
        self.life = random.uniform(0.18, 0.35)

    def update(self, dt):
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.vy += 420 * dt

    def alive(self):
        return (time.time() - self.born) < self.life


class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
        pygame.display.set_caption("AR Gesture Combat")
        self.clock = pygame.time.Clock()
        self.fonts = build_fonts()

        self.vision = VisionTracker()
        self.visuals = Visuals((SCREEN_W, SCREEN_H))
        self.hw_mode = MODE_SWORD
        self.hardware = HardwareInput(mode=self.hw_mode)

        self.state = STATE_MENU
        self.reset_game()

    def reset_game(self):
        self.player_hp = PLAYER_MAX_HP
        self.player_x, self.player_y = float(PLAYER_HOME_X), float(PLAYER_HOME_Y)
        self.player_projectiles = []
        self.weapon = "SWORD"
        self.sword = Sword(length=WEAPON_LENGTH["SWORD"])
        self.paused = False
        self._cmd_hold = {"PAUSE": 0.0, "UP": 0.0, "DOWN": 0.0}
        self.pause_choice = None
        self.pause_ready_at = time.time() + 1.4
        self.sword_hit_ready_at = 0.0
        self.in_melee_range = False
        self.sword_swinging = False
        self.knock_until = 0.0
        self.knock_vx = 0.0
        self.knock_vy = 0.0
        self.enemy = Enemy(
            ENEMY_HOME_X, ENEMY_HOME_Y, max_hp=100,
            min_x=ARENA_MIN_X, max_x=ARENA_MAX_X,
            min_y=PLAYER_MIN_Y, max_y=PLAYER_MAX_Y,
        )
        self.last_gesture = None
        self.shield_active = False
        self.shield_area = 0.0
        self.dash_vx = 0.0
        self.dash_vy = 0.0
        self.dash_until = 0.0
        self.dodge_ready_at = 0.0
        self.iframes_until = 0.0
        self.last_dodge = None
        self.float_texts = []
        self.sparks = []
        self.shake_until = 0.0
        self.shake_mag = 0.0
        self.flash_until = 0.0
        self.flash_color = COLORS["white"]
        self.vision.recalibrate()

    # ---------------- STATE HANDLERS ----------------
    def handle_menu(self, events):
        for e in events:
            if e.type == pygame.KEYDOWN and e.key == pygame.K_RETURN:
                self.hw_mode = MODE_SWORD
                self.hardware.set_mode(self.hw_mode)
                self.reset_game()
                self.state = STATE_PLAYING
        draw_menu(self.screen, self.fonts, self.visuals)

    def handle_end(self, events, victory):
        for e in events:
            if e.type == pygame.KEYDOWN and e.key == pygame.K_RETURN:
                self.state = STATE_MENU
        draw_end_screen(self.screen, self.fonts, victory)

    def handle_playing(self, events):
        cam_frame = self.vision.read_frame()
        tracked = False
        vision_data = {
            "gesture": None,
            "shield_area": 0.0,
            "dodge": None,
            "dodge_v": None,
            "arm_command": None,
            "thumb": None,
            "body_dx": 0.0,
            "body_dy": 0.0,
            "pose_tracked": False,
        }
        if cam_frame is not None:
            vision_data = self.vision.process(cam_frame)
            tracked = (
                vision_data.get("pose_tracked")
                or vision_data["gesture"] is not None
                or vision_data["dodge"] is not None
                or vision_data.get("dodge_v") is not None
            )

        for e in events:
            if e.type != pygame.KEYDOWN:
                continue
            if not self.paused and e.key == pygame.K_p:
                self.paused = True
                self.pause_choice = None
                self._cmd_hold = {"PAUSE": 0.0, "UP": 0.0, "DOWN": 0.0}
            elif self.paused and e.key in (pygame.K_y, pygame.K_RETURN):
                self.paused = False
                self.pause_choice = None
                self._cmd_hold = {"PAUSE": 0.0, "UP": 0.0, "DOWN": 0.0}
            elif self.paused and e.key in (pygame.K_n, pygame.K_BACKSPACE):
                self.paused = False
                self.pause_choice = None
                self._cmd_hold = {"PAUSE": 0.0, "UP": 0.0, "DOWN": 0.0}
                self.state = STATE_MENU

        self.hardware.poll()
        now = time.time()
        dt = self.clock.get_time() / 1000.0
        self._update_pause(vision_data, dt)
        if not self.paused:
            self._lock_weapon(vision_data)

        keys = pygame.key.get_pressed()
        self.shield_active = (not self.paused) and (
            vision_data["gesture"] == "SHIELD" or keys[pygame.K_b]
        )
        self.shield_area = vision_data["shield_area"] if vision_data["gesture"] == "SHIELD" else (0.35 if self.shield_active else 0.0)
        self.last_gesture = vision_data["gesture"]

        if not self.paused:
            stunned = now < self.knock_until
            if stunned:
                self._apply_player_knock_motion()
            else:
                self._update_body_movement(vision_data, now)
                self._update_keyboard_move()

            self._update_sword(now, dt)

            melee_point = None
            if self.in_melee_range and self.sword_swinging:
                melee_point = self.sword.tip(self.player_x, self.player_y)
            self.enemy.update(
                (self.player_x, self.player_y),
                dt,
                melee_point=melee_point,
            )
            self._resolve_melee(now)

            if self.enemy.is_defeated():
                self.state = STATE_VICTORY
            elif self.player_hp <= 0:
                self.state = STATE_DEFEAT

        self._update_fx(dt)
        self._render_game(cam_frame, tracked, vision_data)

    # ---------------- LOGIC ----------------
    def _clamp_player(self):
        self.player_x = max(PLAYER_MIN_X, min(PLAYER_MAX_X, self.player_x))
        self.player_y = max(PLAYER_MIN_Y, min(PLAYER_MAX_Y, self.player_y))

    def _update_pause(self, vision_data, dt):
        hold_need = 0.55
        if not self.paused:
            if time.time() < self.pause_ready_at:
                self._cmd_hold["PAUSE"] = 0.0
                return
            if vision_data.get("arm_command") == "PAUSE":
                self._cmd_hold["PAUSE"] += dt
                if self._cmd_hold["PAUSE"] >= hold_need:
                    self.paused = True
                    self.pause_choice = None
                    self._cmd_hold = {"PAUSE": 0.0, "UP": 0.0, "DOWN": 0.0}
            else:
                self._cmd_hold["PAUSE"] = 0.0
            return

        thumb = vision_data.get("thumb")
        self.pause_choice = thumb
        if thumb == "UP":
            self._cmd_hold["UP"] += dt
            self._cmd_hold["DOWN"] = 0.0
            if self._cmd_hold["UP"] >= hold_need:
                self.paused = False
                self.pause_choice = None
                self._cmd_hold = {"PAUSE": 0.0, "UP": 0.0, "DOWN": 0.0}
        elif thumb == "DOWN":
            self._cmd_hold["DOWN"] += dt
            self._cmd_hold["UP"] = 0.0
            if self._cmd_hold["DOWN"] >= hold_need:
                self.paused = False
                self.pause_choice = None
                self._cmd_hold = {"PAUSE": 0.0, "UP": 0.0, "DOWN": 0.0}
                self.state = STATE_MENU
        else:
            self._cmd_hold["UP"] = 0.0
            self._cmd_hold["DOWN"] = 0.0

    def _lock_weapon(self, vision_data):
        gesture = vision_data.get("gesture")
        if gesture not in ("SWORD", "AXE") or gesture == self.weapon:
            return
        self.weapon = gesture
        self.sword.length = WEAPON_LENGTH[self.weapon]
        self.float_texts.append(FloatText(
            self.player_x, self.player_y - 90,
            f"{self.weapon} LOCKED", COLORS["neon_cyan"],
        ))

    def _update_body_movement(self, vision_data, now):
        dodge = vision_data.get("dodge")
        dodge_v = vision_data.get("dodge_v")
        started_dash = False
        if dodge in ("DODGE_LEFT", "DODGE_RIGHT") and now >= self.dodge_ready_at:
            self.dash_vx = -DASH_SPEED if dodge == "DODGE_LEFT" else DASH_SPEED
            started_dash = True
            self.last_dodge = dodge
        if dodge_v in ("DODGE_UP", "DODGE_DOWN") and now >= self.dodge_ready_at:
            self.dash_vy = -DASH_SPEED if dodge_v == "DODGE_UP" else DASH_SPEED
            started_dash = True
            self.last_dodge = dodge_v
        if started_dash:
            if dodge not in ("DODGE_LEFT", "DODGE_RIGHT"):
                self.dash_vx = 0.0
            if dodge_v not in ("DODGE_UP", "DODGE_DOWN"):
                self.dash_vy = 0.0
            self.dash_until = now + DASH_DURATION
            self.iframes_until = now + DODGE_IFRAMES
            self.dodge_ready_at = now + DODGE_COOLDOWN
        elif now >= self.dash_until:
            self.dash_vx = 0.0
            self.dash_vy = 0.0

        dashing = now < self.dash_until
        if dashing:
            self.player_x += self.dash_vx
            self.player_y += self.dash_vy

        if vision_data.get("pose_tracked") and not self._manual_move_held():
            target_x = PLAYER_HOME_X + vision_data.get("body_dx", 0.0) * BODY_MOVE_GAIN_X
            target_y = PLAYER_HOME_Y + vision_data.get("body_dy", 0.0) * BODY_MOVE_GAIN_Y
            follow = 0.08 if dashing else BODY_FOLLOW_LERP
            if abs(self.dash_vx) < 0.01:
                self.player_x += (target_x - self.player_x) * follow
            if abs(self.dash_vy) < 0.01:
                self.player_y += (target_y - self.player_y) * follow
        self._clamp_player()

    def _manual_move_held(self):
        keys = pygame.key.get_pressed()
        return any((
            keys[pygame.K_a], keys[pygame.K_d], keys[pygame.K_w], keys[pygame.K_s],
            keys[pygame.K_LEFT], keys[pygame.K_RIGHT], keys[pygame.K_UP], keys[pygame.K_DOWN],
        ))

    def _apply_player_knock_motion(self):
        self.player_x += self.knock_vx
        self.player_y += self.knock_vy
        self.knock_vx *= 0.86
        self.knock_vy *= 0.86
        self._clamp_player()

    def _knock_player(self, from_x, from_y, now):
        dx = self.player_x - from_x
        dy = self.player_y - from_y
        dist = max(1.0, compute_velocity(dx, dy))
        self.knock_vx = (dx / dist) * KNOCKBACK
        self.knock_vy = (dy / dist) * KNOCKBACK
        self.knock_until = now + HIT_STUN
        self.iframes_until = now + HIT_STUN
        self.sword_hit_ready_at = now + SWORD_HIT_COOLDOWN

    def _spawn_impact(self, x, y, amount=None, blocked=False):
        now = time.time()
        if blocked:
            self.float_texts.append(FloatText(x, y - 40, "BLOCK", COLORS["neon_yellow"]))
            color = COLORS["neon_yellow"]
            self.shake_mag = 6
        else:
            dmg = int(round(amount or 5))
            self.float_texts.append(FloatText(x, y - 50, f"-{dmg}", COLORS["danger"]))
            color = COLORS["white"]
            self.shake_mag = 10 + min(8, dmg)
        for _ in range(14 if not blocked else 8):
            self.sparks.append(Spark(x, y, color))
        self.shake_until = now + SHAKE_TIME
        self.flash_until = now + 0.08
        self.flash_color = COLORS["neon_yellow"] if blocked else COLORS["white"]

    def _update_fx(self, dt):
        for item in self.float_texts:
            item.update(dt)
        for item in self.sparks:
            item.update(dt)
        self.float_texts = [t for t in self.float_texts if t.alive()]
        self.sparks = [s for s in self.sparks if s.alive()]

    def _shake_offset(self, now):
        if now >= self.shake_until:
            return 0, 0
        t = (self.shake_until - now) / SHAKE_TIME
        mag = int(self.shake_mag * t)
        if mag <= 0:
            return 0, 0
        return random.randint(-mag, mag), random.randint(-mag, mag)

    def _update_keyboard_move(self):
        keys = pygame.key.get_pressed()
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            self.player_x -= KEY_MOVE_SPEED
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            self.player_x += KEY_MOVE_SPEED
        if keys[pygame.K_w] or keys[pygame.K_UP]:
            self.player_y -= KEY_MOVE_SPEED
        if keys[pygame.K_s] or keys[pygame.K_DOWN]:
            self.player_y += KEY_MOVE_SPEED
        self._clamp_player()

    def _update_sword(self, now, dt):
        target = self.hardware.poll_sword_angle((self.player_x, self.player_y))
        self.sword.set_target_angle(target, dt)
        dist = compute_velocity(self.enemy.x - self.player_x, self.enemy.y - self.player_y)
        self.in_melee_range = dist <= MELEE_RANGE
        self.sword_swinging = abs(self.sword.omega) >= SWING_MIN_OMEGA

        if not (self.in_melee_range and self.sword_swinging):
            return
        if now < self.sword_hit_ready_at or now < self.knock_until:
            return
        if self.enemy.is_invulnerable():
            return
        if self.sword.hits_hurtbox(self.player_x, self.player_y, self.enemy.hurtbox(ENEMY_HURTBOX)):
            dmg = calculate_melee_damage(abs(self.sword.omega), weapon=self.weapon)
            if self.enemy.take_damage(dmg):
                self.enemy.apply_knockback(self.player_x, self.player_y)
                self._spawn_impact(self.enemy.x, self.enemy.y - 20, amount=dmg)
            self.sword_hit_ready_at = now + SWORD_HIT_COOLDOWN

    def _resolve_melee(self, now):
        if not self.enemy.can_strike(now):
            return
        if now < self.iframes_until or now < self.knock_until:
            return
        player_box = AABB(
            self.player_x - PLAYER_HURTBOX,
            self.player_y - PLAYER_HURTBOX,
            PLAYER_HURTBOX * 2,
            PLAYER_HURTBOX * 2,
        )
        if not self.enemy.sword.hits_hurtbox(self.enemy.x, self.enemy.y, player_box):
            return
        self.enemy.mark_strike(now, SWORD_HIT_COOLDOWN)
        if self.shield_active:
            self._spawn_impact(self.player_x, self.player_y - 10, blocked=True)
            return
        dmg = calculate_melee_damage(max(abs(self.enemy.sword.omega), 6.0), weapon="SWORD")
        self.player_hp = max(0, self.player_hp - dmg)
        self._knock_player(self.enemy.x, self.enemy.y, now)
        self._spawn_impact(self.player_x, self.player_y - 10, amount=dmg)

    # ---------------- RENDER ----------------
    def _render_game(self, cam_frame, tracked, vision_data):
        screen = self.screen
        now = time.time()
        ox, oy = self._shake_offset(now)
        self.visuals.draw_bg(screen, ox, oy)

        # HUD panels (brutalist) — stay put while the fight shakes
        draw_hp_bar(screen, self.fonts, 40, 40, 320, 34,
                    self.player_hp / PLAYER_MAX_HP, "TAIGA", COLORS["neon_green"], COLORS["bg2"])
        php = self.fonts["hpnum"].render(str(int(self.player_hp)), True, COLORS["white"])
        screen.blit(php, (40 + 320 - php.get_width() - 10, 46))
        draw_hp_bar(screen, self.fonts, SCREEN_W - 360, 40, 320, 34,
                    self.enemy.hp_ratio(), "TSUNAMI", COLORS["neon_pink"], COLORS["bg2"])
        ehp = self.fonts["hpnum"].render(str(int(self.enemy.hp)), True, COLORS["white"])
        screen.blit(ehp, (SCREEN_W - 360 + 320 - ehp.get_width() - 10, 46))

        mode_txt = self.fonts["small"].render(
            f"WEAPON: {self.weapon} LOCKED  |  V-SIGN/FIST TO SWITCH", True, COLORS["neon_yellow"]
        )
        screen.blit(mode_txt, (40, 84))
        state_txt = self.fonts["small"].render(f"ENEMY STATE: {self.enemy.state}", True, COLORS["neon_purple"])
        screen.blit(state_txt, (SCREEN_W - 360, 84))

        # Fighters + swords
        px, py = int(self.player_x) + ox, int(self.player_y) + oy
        ex, ey = int(self.enemy.x) + ox, int(self.enemy.y) + oy
        p_flash = None
        if now < self.knock_until:
            p_flash = COLORS["white"]
        elif self.shield_active:
            p_flash = COLORS["neon_yellow"]
        e_flash = None
        if self.enemy.state == "STUNNED":
            e_flash = COLORS["white"]
        elif self.enemy.state == "ATTACK":
            e_flash = COLORS["danger"]

        self.visuals.draw_fighter(screen, self.visuals.player, px, py, p_flash)
        self.visuals.draw_fighter(screen, self.visuals.enemy, ex, ey, e_flash)
        self.visuals.draw_weapon(screen, px, py, self.sword.angle, self.weapon, facing_left=False)
        self.visuals.draw_weapon(screen, ex, ey, self.enemy.sword.angle, "SWORD", facing_left=True)

        if self.shield_active:
            shield_r = 70 + int(self.shield_area * 80)
            pygame.draw.circle(screen, COLORS["neon_yellow"], (px, py - 10), shield_r, 6)
            pygame.draw.circle(screen, (245, 235, 20), (px, py - 10), shield_r + 10, 2)

        range_color = COLORS["neon_yellow"] if self.in_melee_range else (70, 60, 30)
        pygame.draw.circle(screen, range_color, (ex, ey), int(MELEE_RANGE), 2)

        for spark in self.sparks:
            pygame.draw.circle(screen, spark.color, (int(spark.x) + ox, int(spark.y) + oy), 3)
        for txt in self.float_texts:
            label = self.fonts["damage"].render(txt.text, True, txt.color)
            screen.blit(label, (int(txt.x) - label.get_width() // 2 + ox, int(txt.y) + oy))

        if now < self.flash_until:
            flash = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
            flash.fill((*self.flash_color, 50))
            screen.blit(flash, (0, 0))

        # Gesture / melee readout panel
        gtxt = "SHIELD" if self.shield_active else (vision_data["gesture"] or "NONE")
        if now < self.knock_until:
            dodge_txt = "HIT STUN"
        elif now < self.dash_until:
            if abs(self.dash_vy) >= abs(self.dash_vx):
                dodge_txt = "DASH UP" if self.dash_vy < 0 else "DASH DOWN"
            else:
                dodge_txt = "DASH LEFT" if self.dash_vx < 0 else "DASH RIGHT"
        elif now < self.dodge_ready_at:
            dodge_txt = "COOLDOWN"
        elif vision_data.get("pose_tracked"):
            dodge_txt = "READY"
        else:
            dodge_txt = "NO POSE"
        if self.shield_active:
            range_txt = "SHIELD: BLOCKING"
        elif self.in_melee_range:
            range_txt = "IN RANGE" if self.sword_swinging else "IN RANGE - SWING"
        else:
            range_txt = "TOO FAR"
        panel = pygame.Rect(40, SCREEN_H - 140, 380, 100)
        draw_brutalist_panel(screen, panel, COLORS["bg2"], COLORS["neon_cyan"], 4, shadow=False)
        gesture_label = self.fonts["body"].render(f"GESTURE: {gtxt}", True, COLORS["white"])
        dodge_color = COLORS["neon_green"] if dodge_txt == "READY" else COLORS["neon_yellow"]
        if dodge_txt == "NO POSE":
            dodge_color = COLORS["danger"]
        dodge_label = self.fonts["small"].render(f"DODGE: {dodge_txt}", True, dodge_color)
        range_color = COLORS["neon_green"] if (self.in_melee_range or self.shield_active) else COLORS["danger"]
        range_label = self.fonts["small"].render(f"{self.weapon}: {range_txt}", True, range_color)
        screen.blit(gesture_label, (panel.x + 12, panel.y + 8))
        screen.blit(dodge_label, (panel.x + 12, panel.y + 40))
        screen.blit(range_label, (panel.x + 12, panel.y + 66))

        if cam_frame is not None:
            draw_pip(screen, cam_frame, self.fonts, tracked)

        if self.paused:
            self._draw_pause_popup()

        pygame.display.flip()

    def _draw_pause_popup(self):
        veil = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        veil.fill((8, 6, 16, 90))
        self.screen.blit(veil, (0, 0))

        card_w, card_h = 440, 268
        cx = SCREEN_W // 2 - card_w // 2
        cy = SCREEN_H // 2 - card_h // 2
        draw_brutalist_panel(
            self.screen, (cx, cy, card_w, card_h),
            COLORS["bg2"], COLORS["neon_yellow"], 5,
        )
        title = self.fonts["heading"].render("PAUSED", True, COLORS["neon_yellow"])
        self.screen.blit(title, (SCREEN_W // 2 - title.get_width() // 2, cy + 16))
        prompt = self.fonts["body"].render("WHAT DO YOU WANT TO DO?", True, COLORS["white"])
        self.screen.blit(prompt, (SCREEN_W // 2 - prompt.get_width() // 2, cy + 58))

        hold_need = 0.35
        options = [
            ("UP", "RESUME", "THUMBS UP", COLORS["neon_green"]),
            ("DOWN", "EXIT", "THUMBS DOWN", COLORS["danger"]),
        ]
        for i, (key, label, hint, accent) in enumerate(options):
            ox, oy = cx + 28, cy + 100 + i * 72
            ow, oh = card_w - 56, 62
            selected = self.pause_choice == key
            border = accent if selected else COLORS["border"]
            draw_brutalist_panel(
                self.screen, (ox, oy, ow, oh), COLORS["bg"], border, 4, shadow=False,
            )
            fill = min(1.0, self._cmd_hold.get(key, 0.0) / hold_need) if selected else 0.0
            if fill > 0:
                pygame.draw.rect(
                    self.screen, accent,
                    (ox + 4, oy + 4, int((ow - 8) * fill), oh - 8),
                )
            name = self.fonts["body"].render(label, True, COLORS["white"])
            sub = self.fonts["small"].render(hint, True, accent)
            self.screen.blit(name, (ox + 16, oy + 8))
            self.screen.blit(sub, (ox + 16, oy + 34))

    # ---------------- MAIN LOOP ----------------
    def run(self):
        running = True
        while running:
            events = pygame.event.get()
            for e in events:
                if e.type == pygame.QUIT:
                    running = False
                if e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
                    running = False

            if self.state == STATE_MENU:
                self.handle_menu(events)
            elif self.state == STATE_PLAYING:
                self.handle_playing(events)
            elif self.state == STATE_VICTORY:
                self.handle_end(events, True)
            elif self.state == STATE_DEFEAT:
                self.handle_end(events, False)

            self.clock.tick(FPS)

        self.vision.release()
        self.hardware.shutdown()
        pygame.quit()
        sys.exit()


if __name__ == "__main__":
    Game().run()
