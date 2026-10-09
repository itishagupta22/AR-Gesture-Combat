"""Physical sword/rod hardware interface with mouse + keyboard mock."""
import math
import threading
import time

try:
    import serial
    import serial.tools.list_ports
    SERIAL_AVAILABLE = True
except ImportError:
    SERIAL_AVAILABLE = False

import pygame

MODE_ROD = "ROD"
MODE_BOW = "BOW"
MODE_SWORD = "SWORD"

SWORD_ROTATE_SPEED = 0.11


class HardwareInput:
    def __init__(self, mode=MODE_SWORD, port=None, baud=9600):
        self.mode = mode
        self.port_name = port
        self.baud = baud
        self.serial_conn = None
        self.connected_hardware = False
        self.last_events = set()
        self._lock = threading.Lock()
        self._running = False
        self._thread = None
        self._kb_angle = 0.0

        if SERIAL_AVAILABLE:
            self._try_connect(port)

        if not self.connected_hardware:
            print("[HardwareInput] No physical sword detected. Mouse/Q-E mock enabled.")

    def _try_connect(self, port):
        candidate_ports = [port] if port else self._autodetect_ports()
        for p in candidate_ports:
            try:
                self.serial_conn = serial.Serial(p, self.baud, timeout=0.05)
                self.port_name = p
                self.connected_hardware = True
                self._start_listener()
                print(f"[HardwareInput] Connected to physical device on {p}")
                return
            except Exception:
                continue

    def _autodetect_ports(self):
        try:
            return [p.device for p in serial.tools.list_ports.comports()]
        except Exception:
            return []

    def _start_listener(self):
        self._running = True
        self._thread = threading.Thread(target=self._listen_loop, daemon=True)
        self._thread.start()

    def _listen_loop(self):
        while self._running:
            try:
                if self.serial_conn.in_waiting:
                    line = self.serial_conn.readline().decode(errors="ignore").strip()
                    if line:
                        with self._lock:
                            self.last_events.add(line.upper())
            except Exception:
                self.connected_hardware = False
                break
            time.sleep(0.01)

    def poll(self, pygame_keys=None):
        """Button-style events (legacy). Sword angle is poll_sword_angle()."""
        if self.connected_hardware:
            with self._lock:
                events = set(self.last_events)
                self.last_events.clear()
            return events
        return set()

    def poll_sword_angle(self, origin):
        """
        IMU mock: blade points toward the mouse from the player.
        Q / E rotate if you prefer keys. Returns angle in radians (0 = right).
        """
        ox, oy = origin
        keys = pygame.key.get_pressed()
        if keys[pygame.K_q]:
            self._kb_angle -= SWORD_ROTATE_SPEED
            return self._kb_angle
        if keys[pygame.K_e]:
            self._kb_angle += SWORD_ROTATE_SPEED
            return self._kb_angle

        mx, my = pygame.mouse.get_pos()
        angle = math.atan2(my - oy, mx - ox)
        self._kb_angle = angle
        return angle

    def set_mode(self, mode):
        self.mode = mode

    def shutdown(self):
        self._running = False
        if self.serial_conn:
            try:
                self.serial_conn.close()
            except Exception:
                pass


def select_hardware_mode_menu(screen, font, clock, colors):
    """Blocking startup menu. Returns chosen mode string."""
    selected = MODE_SWORD
    options = [MODE_SWORD, MODE_ROD, MODE_BOW]
    idx = 0
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                raise SystemExit
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_LEFT, pygame.K_RIGHT, pygame.K_UP, pygame.K_DOWN):
                    idx = (idx + 1) % len(options)
                elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    selected = options[idx]
                    running = False

        screen.fill(colors["bg"])
        title = font["title"].render("SELECT HARDWARE MODE", True, colors["neon_pink"])
        screen.blit(title, (screen.get_width() // 2 - title.get_width() // 2, 100))

        for i, opt in enumerate(options):
            is_sel = i == idx
            color = colors["neon_yellow"] if is_sel else colors["white"]
            box_color = colors["neon_cyan"] if is_sel else colors["border"]
            rect = pygame.Rect(screen.get_width() // 2 - 150, 200 + i * 110, 300, 90)
            pygame.draw.rect(screen, colors["bg2"], rect)
            pygame.draw.rect(screen, box_color, rect, 6)
            label = font["heading"].render(opt, True, color)
            screen.blit(
                label,
                (rect.centerx - label.get_width() // 2, rect.centery - label.get_height() // 2),
            )

        hint = font["body"].render("ARROW KEYS TO SELECT / ENTER TO CONFIRM", True, colors["neon_green"])
        screen.blit(hint, (screen.get_width() // 2 - hint.get_width() // 2, 540))

        pygame.display.flip()
        clock.tick(60)

    return selected
