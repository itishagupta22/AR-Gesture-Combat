"""AABB collision detection and dynamic hitpoint/damage calculation."""
import math

# Tunable constants
BASE_DAMAGE_COEFF = 0.9
FALLOFF_RATE = 0.0025       # damage lost per pixel traveled
MIN_DAMAGE_FLOOR = 2.0
SHIELD_MITIGATION_CAP = 0.85  # max 85% damage block regardless of shield size
SHIELD_AREA_SCALE = 40.0      # scales normalized hand-spread area to mitigation %


class AABB:
    __slots__ = ("x", "y", "w", "h")

    def __init__(self, x, y, w, h):
        self.x, self.y, self.w, self.h = x, y, w, h

    @property
    def rect(self):
        return (self.x, self.y, self.x + self.w, self.y + self.h)

    def intersects(self, other):
        ax1, ay1, ax2, ay2 = self.rect
        bx1, by1, bx2, by2 = other.rect
        return ax1 < bx2 and ax2 > bx1 and ay1 < by2 and ay2 > by1


def check_collision(box_a: AABB, box_b: AABB) -> bool:
    """Pure AABB overlap test."""
    return box_a.intersects(box_b)


def calculate_hitpoints(velocity: float, distance_traveled: float, shield_area: float = 0.0) -> float:
    """
    Dynamic damage calculation.
    velocity: px/frame speed of the projectile at impact
    distance_traveled: total px traveled since spawn (for falloff)
    shield_area: normalized hand-spread (0.0 - ~0.5) if SHIELD gesture is active; 0 if none.

    Returns final damage (float, never negative, floored at MIN_DAMAGE_FLOOR
    unless fully mitigated by shield).
    """
    # 1) Raw kinetic damage scales with velocity^2 (kinetic energy analogy)
    raw_damage = BASE_DAMAGE_COEFF * (velocity ** 1.5)

    # 2) Falloff over distance traveled (projectiles weaken over range)
    falloff_multiplier = max(0.15, 1.0 - (distance_traveled * FALLOFF_RATE))
    damage_after_falloff = raw_damage * falloff_multiplier

    # 3) Shield mitigation based on physical hand spread
    mitigation = 0.0
    if shield_area > 0:
        mitigation = min(SHIELD_MITIGATION_CAP, (shield_area * SHIELD_AREA_SCALE) / 100.0)

    final_damage = damage_after_falloff * (1.0 - mitigation)

    if mitigation >= SHIELD_MITIGATION_CAP * 0.999:
        return max(0.0, final_damage)  # near-full block can go below floor

    return max(MIN_DAMAGE_FLOOR, final_damage)


def compute_velocity(dx: float, dy: float) -> float:
    return math.hypot(dx, dy)


def point_in_aabb(px: float, py: float, box: AABB) -> bool:
    x1, y1, x2, y2 = box.rect
    return x1 <= px <= x2 and y1 <= py <= y2


WEAPON_LENGTH = {"SWORD": 160, "AXE": 138}


def calculate_melee_damage(swing_speed: float, shield_area: float = 0.0, weapon="SWORD") -> int:
    """Integer melee damage. Light hit = 5; axe hits a bit harder."""
    if shield_area > 0:
        return 0
    speed = abs(swing_speed)
    if speed < 5.0:
        dmg = 5
    elif speed < 9.0:
        dmg = 8
    elif speed < 14.0:
        dmg = 12
    else:
        dmg = 15
    if weapon == "AXE":
        dmg += 3
    return dmg


def shortest_angle_delta(from_a: float, to_a: float) -> float:
    return (to_a - from_a + math.pi) % (2 * math.pi) - math.pi


class Sword:
    """Virtual blade attached to the player. Angle 0 points right (toward the enemy)."""

    def __init__(self, length=160, thickness=14):
        self.length = length
        self.thickness = thickness
        self.angle = 0.0
        self.omega = 0.0

    def tip(self, x, y):
        return (
            x + math.cos(self.angle) * self.length,
            y + math.sin(self.angle) * self.length,
        )

    def sample_points(self, x, y, n=6):
        pts = []
        for i in range(2, n + 1):
            t = i / float(n)
            pts.append((
                x + math.cos(self.angle) * self.length * t,
                y + math.sin(self.angle) * self.length * t,
            ))
        return pts

    def hits_hurtbox(self, x, y, box: AABB) -> bool:
        for px, py in self.sample_points(x, y):
            if point_in_aabb(px, py, box):
                return True
        return False

    def set_target_angle(self, target, dt):
        dt = max(dt, 1.0 / 120.0)
        delta = shortest_angle_delta(self.angle, target)
        follow = min(1.0, 18.0 * dt)
        self.omega = delta / dt
        self.angle += delta * follow


class Projectile:
    def __init__(self, x, y, vx, vy, owner="enemy", proj_type="FIREBALL", size=18):
        self.x, self.y = x, y
        self.vx, self.vy = vx, vy
        self.owner = owner
        self.proj_type = proj_type
        self.size = size
        self.spawn_x, self.spawn_y = x, y
        self.alive = True

    def update(self):
        self.x += self.vx
        self.y += self.vy

    def distance_traveled(self):
        return math.hypot(self.x - self.spawn_x, self.y - self.spawn_y)

    def velocity(self):
        return compute_velocity(self.vx, self.vy)

    def get_aabb(self):
        return AABB(self.x - self.size / 2, self.y - self.size / 2, self.size, self.size)

    def offscreen(self, w, h, margin=60):
        return (self.x < -margin or self.x > w + margin or
                self.y < -margin or self.y > h + margin)
