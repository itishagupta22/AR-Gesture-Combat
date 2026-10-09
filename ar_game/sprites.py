"""Load and draw Shadow Fight-style arena, fighters, and swords."""
import math
import os
import numpy as np
import pygame

ASSETS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")
PLAYER_H = 210
ENEMY_H = 210
SWORD_LEN = 168
AXE_LEN = 150


def _chroma_key(path, key=(255, 0, 255), thresh=55):
    """Load a JPEG with magenta backdrop and return an RGBA pygame surface."""
    raw = pygame.image.load(path).convert()
    rgb = pygame.surfarray.array3d(raw).astype(np.int16)
    kr, kg, kb = key
    dist = np.abs(rgb[:, :, 0] - kr) + np.abs(rgb[:, :, 1] - kg) + np.abs(rgb[:, :, 2] - kb)
    alpha = np.where(dist < thresh * 3, 0, 255).astype(np.uint8)
    fringe = (dist >= thresh * 3) & (dist < thresh * 5)
    alpha = np.where(fringe, 80, alpha)
    surf = pygame.Surface(raw.get_size(), pygame.SRCALPHA)
    pygame.surfarray.blit_array(surf, pygame.surfarray.array3d(raw))
    alpha_px = pygame.surfarray.pixels_alpha(surf)
    alpha_px[:, :] = alpha
    del alpha_px
    return surf.convert_alpha()


def _scale_to_height(surf, height):
    w, h = surf.get_size()
    if h <= 0:
        return surf
    scale = height / float(h)
    return pygame.transform.smoothscale(surf, (max(1, int(w * scale)), height))


def _scale_to_width(surf, width):
    w, h = surf.get_size()
    if w <= 0:
        return surf
    scale = width / float(w)
    return pygame.transform.smoothscale(surf, (width, max(1, int(h * scale))))


def blit_rotate(screen, image, pivot, angle_rad, handle=(0.12, 0.55)):
    """Draw `image` (points right at angle 0) rotated so the handle stays on pivot."""
    degrees = -math.degrees(angle_rad)
    hx = image.get_width() * handle[0]
    hy = image.get_height() * handle[1]
    rotated = pygame.transform.rotate(image, degrees)
    rad = math.radians(degrees)
    cos_a, sin_a = math.cos(rad), math.sin(rad)
    # vector from image center to handle, then rotated
    cx, cy = image.get_width() / 2.0, image.get_height() / 2.0
    dx, dy = hx - cx, hy - cy
    rdx = dx * cos_a + dy * sin_a
    rdy = -dx * sin_a + dy * cos_a
    rect = rotated.get_rect()
    rect.center = (pivot[0] - rdx, pivot[1] - rdy)
    screen.blit(rotated, rect)


class Visuals:
    def __init__(self, screen_size):
        self.w, self.h = screen_size
        bg_path = os.path.join(ASSETS, "arena_ruins.jpg")
        bg = pygame.image.load(bg_path).convert()
        self.bg = pygame.transform.smoothscale(bg, screen_size)

        self.player = _scale_to_height(
            _chroma_key(os.path.join(ASSETS, "player_fighter.jpg")), PLAYER_H
        )
        self.enemy = _scale_to_height(
            _chroma_key(os.path.join(ASSETS, "enemy_fighter.jpg")), ENEMY_H
        )
        self.sword = _scale_to_width(
            _chroma_key(os.path.join(ASSETS, "sword.jpg"), thresh=48), SWORD_LEN
        )
        axe_path = os.path.join(ASSETS, "axe.jpg")
        if os.path.isfile(axe_path):
            self.axe = _scale_to_width(_chroma_key(axe_path, thresh=48), AXE_LEN)
        else:
            self.axe = self.sword

    def draw_bg(self, screen, ox=0, oy=0):
        if ox or oy:
            screen.blit(self.bg, (ox - 8, oy - 8))
        else:
            screen.blit(self.bg, (0, 0))

    def _shadow(self, screen, x, y, w=70):
        shadow = pygame.Surface((w * 2, 22), pygame.SRCALPHA)
        pygame.draw.ellipse(shadow, (0, 0, 0, 110), shadow.get_rect())
        screen.blit(shadow, (int(x - w), int(y + 78)))

    def draw_fighter(self, screen, sprite, x, y, flash_color=None):
        rect = sprite.get_rect()
        rect.centerx = int(x)
        rect.centery = int(y - 18)
        self._shadow(screen, x, y, w=rect.width // 3)
        screen.blit(sprite, rect)
        if flash_color:
            glow = pygame.Surface(sprite.get_size(), pygame.SRCALPHA)
            glow.fill((*flash_color, 70))
            screen.blit(glow, rect, special_flags=pygame.BLEND_RGBA_ADD)
        return rect

    def draw_weapon(self, screen, x, y, angle, weapon="SWORD", facing_left=False):
        hand = (x + (22 if not facing_left else -22), y - 6)
        img = self.axe if weapon == "AXE" else self.sword
        blit_rotate(screen, img, hand, angle, handle=(0.12, 0.55))
        return hand

    def draw_sword(self, screen, x, y, angle, facing_left=False):
        return self.draw_weapon(screen, x, y, angle, "SWORD", facing_left)
