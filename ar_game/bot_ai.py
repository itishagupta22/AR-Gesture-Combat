"""Enemy bot: chase, melee sword, dodge, knockback stun."""
import math
import random
import time
from physics_engine import Sword, compute_velocity, AABB

STATE_IDLE = "IDLE"
STATE_ATTACK = "ATTACK"
STATE_DODGE = "DODGE"
STATE_STUNNED = "STUNNED"

CHASE_SPEED = 4.6
WANDER_SPEED = 1.4
DASH_SPEED = 14.0
DODGE_DURATION = 0.28
DODGE_COOLDOWN = 0.85
DODGE_CHANCE = 0.72
ATTACK_WINDUP = 0.28
ATTACK_SLASH = 0.18
ATTACK_RECOVER = 0.42
MELEE_ENGAGE = 205.0
HIT_STUN = 0.55
KNOCKBACK = 18.0


class Enemy:
    def __init__(self, x, y, max_hp=100, min_x=80, max_x=1020, min_y=80, max_y=640):
        self.x, self.y = float(x), float(y)
        self.min_x, self.max_x = min_x, max_x
        self.min_y, self.max_y = min_y, max_y
        self.max_hp = max_hp
        self.hp = max_hp
        self.state = STATE_IDLE
        self.state_timer = time.time()
        self.idle_duration = random.uniform(0.35, 0.8)
        self.stun_duration = HIT_STUN
        self.sword = Sword(length=160)
        self.sword.angle = math.pi
        self.vy = 0.0
        self.wander_dir = random.choice([-1, 1])
        self.dodge_ready_at = 0.0
        self.iframes_until = 0.0
        self.strike_ready_at = 0.0
        self.knock_until = 0.0
        self.knock_vx = 0.0
        self.knock_vy = 0.0
        self.swinging = False
        self.projectiles = []

    def update(self, target_pos, dt, incoming=None, melee_point=None):
        now = time.time()
        elapsed = now - self.state_timer
        tx, ty = target_pos
        incoming = incoming or []
        dist = compute_velocity(tx - self.x, ty - self.y)

        if now < self.knock_until:
            self.x += self.knock_vx
            self.y += self.knock_vy
            self.knock_vx *= 0.86
            self.knock_vy *= 0.86
            self.swinging = False
            self._face(tx, ty, dt)
            self._clamp()
            if elapsed >= self.stun_duration and self.state == STATE_STUNNED:
                self._transition(STATE_IDLE)
            return

        if self.state != STATE_STUNNED:
            self._try_dodge(incoming, now, melee_point)

        if self.state == STATE_IDLE:
            self._chase(tx, ty, dist)
            if dist <= MELEE_ENGAGE and elapsed >= self.idle_duration:
                self._transition(STATE_ATTACK)

        elif self.state == STATE_ATTACK:
            if dist > MELEE_ENGAGE + 40:
                self._chase(tx, ty, dist)
            else:
                self._aim_toward(ty)
            self._animate_swing(dt, tx, ty, elapsed)
            if elapsed >= ATTACK_WINDUP + ATTACK_SLASH + ATTACK_RECOVER:
                self._transition(STATE_IDLE)

        elif self.state == STATE_DODGE:
            self.y += self.vy
            self._clamp()
            self._face(tx, ty, dt)
            self.swinging = False
            if elapsed >= DODGE_DURATION:
                self._transition(STATE_IDLE)

        elif self.state == STATE_STUNNED:
            self.swinging = False
            if elapsed >= self.stun_duration:
                self._transition(STATE_IDLE)

    def _chase(self, tx, ty, dist):
        if dist > 95:
            nx = (tx - self.x) / max(dist, 1.0)
            ny = (ty - self.y) / max(dist, 1.0)
            self.x += nx * CHASE_SPEED
            self.y += ny * CHASE_SPEED
        self.y += self.wander_dir * WANDER_SPEED
        if self.y <= self.min_y or self.y >= self.max_y or random.random() < 0.01:
            self.wander_dir *= -1
        self._clamp()

    def _aim_toward(self, target_y):
        self.y += (target_y - self.y) * 0.07
        self._clamp()

    def _face(self, tx, ty, dt):
        target = math.atan2(ty - self.y, tx - self.x)
        self.sword.set_target_angle(target, dt)

    def _animate_swing(self, dt, tx, ty, elapsed):
        base = math.atan2(ty - self.y, tx - self.x)
        if elapsed < ATTACK_WINDUP:
            self.sword.set_target_angle(base + 0.95, dt)
            self.swinging = False
        elif elapsed < ATTACK_WINDUP + ATTACK_SLASH:
            t = (elapsed - ATTACK_WINDUP) / ATTACK_SLASH
            self.sword.set_target_angle(base + 0.95 - 1.9 * t, dt)
            self.swinging = True
        else:
            self._face(tx, ty, dt)
            self.swinging = False

    def _try_dodge(self, incoming, now, melee_point=None):
        if self.state in (STATE_DODGE, STATE_ATTACK):
            return
        if now < self.dodge_ready_at:
            return
        threat = self._melee_threat(melee_point)
        if threat is None:
            return
        if random.random() > DODGE_CHANCE:
            self.dodge_ready_at = now + DODGE_COOLDOWN * 0.4
            return
        go_up = threat[1] >= self.y
        if go_up and self.y - 80 < self.min_y:
            go_up = False
        if not go_up and self.y + 80 > self.max_y:
            go_up = True
        self.vy = -DASH_SPEED if go_up else DASH_SPEED
        self.iframes_until = now + DODGE_DURATION
        self.dodge_ready_at = now + DODGE_COOLDOWN
        self._transition(STATE_DODGE)

    def _melee_threat(self, melee_point):
        if melee_point is None:
            return None
        mx, my = melee_point
        dist = compute_velocity(self.x - mx, self.y - my)
        if dist > 95:
            return None
        return (mx, my)

    def _clamp(self):
        self.x = max(self.min_x, min(self.max_x, self.x))
        self.y = max(self.min_y, min(self.max_y, self.y))

    def _transition(self, new_state):
        self.state = new_state
        self.state_timer = time.time()
        self.swinging = False
        if new_state == STATE_IDLE:
            self.idle_duration = random.uniform(0.3, 0.75)
            self.wander_dir = random.choice([-1, 1])
        elif new_state != STATE_DODGE:
            self.vy = 0.0

    def apply_knockback(self, from_x, from_y, force=KNOCKBACK):
        dx = self.x - from_x
        dy = self.y - from_y
        dist = max(1.0, compute_velocity(dx, dy))
        self.knock_vx = (dx / dist) * force
        self.knock_vy = (dy / dist) * force
        now = time.time()
        self.knock_until = now + HIT_STUN
        self.iframes_until = now + HIT_STUN
        self.stun_duration = HIT_STUN
        self._transition(STATE_STUNNED)

    def take_damage(self, dmg):
        if time.time() < self.iframes_until:
            return False
        self.hp = max(0, self.hp - dmg)
        return True

    def can_strike(self, now):
        return self.swinging and now >= self.strike_ready_at and not self.is_invulnerable()

    def mark_strike(self, now, cooldown=0.45):
        self.strike_ready_at = now + cooldown

    def is_defeated(self):
        return self.hp <= 0

    def hp_ratio(self):
        return self.hp / self.max_hp

    def is_invulnerable(self):
        return time.time() < self.iframes_until

    def hurtbox(self, pad=52):
        return AABB(self.x - pad, self.y - pad, pad * 2, pad * 2)
