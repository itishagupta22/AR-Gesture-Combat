import pygame
import sys

from game.player import Player
from game.input_handler import get_keyboard_action

# --------------------------------------------------
# 1. Initialize Pygame
# --------------------------------------------------

pygame.init()


# --------------------------------------------------
# 2. Game window
# --------------------------------------------------

WIDTH = 1000
HEIGHT = 600

screen = pygame.display.set_mode(
    (WIDTH, HEIGHT)
)

pygame.display.set_caption(
    "Human Interaction Combat"
)


# --------------------------------------------------
# 3. Colors
# --------------------------------------------------

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (200, 50, 50)
BLUE = (50, 100, 200)
GREEN = (50, 180, 80)
GRAY = (180, 180, 180)


# --------------------------------------------------
# 4. Clock
# --------------------------------------------------

clock = pygame.time.Clock()


# --------------------------------------------------
# 5. Player
# --------------------------------------------------


player = Player(200, 400)


# --------------------------------------------------
# 6. Enemy
# --------------------------------------------------

enemy_x = 720
enemy_y = 400

enemy_width = 80
enemy_height = 120

enemy_hp = 100


# --------------------------------------------------
# 7. Game loop
# --------------------------------------------------

running = True

while running:

    # --------------------------------------------------
    # Handle events
    # --------------------------------------------------

    for event in pygame.event.get():

        if event.type == pygame.QUIT:
            running = False

    action = get_keyboard_action()
    if action != "NONE":
        print("Game Action:", action)
        player.handle_action(action)

    player.update()
    # --------------------------------------------------
    # Draw background
    # --------------------------------------------------

    screen.fill(WHITE)


    # --------------------------------------------------
    # Draw player
    # --------------------------------------------------

    player.draw(screen)


    # --------------------------------------------------
    # Draw enemy
    # --------------------------------------------------

    pygame.draw.rect(
        screen,
        RED,
        (
            enemy_x,
            enemy_y,
            enemy_width,
            enemy_height
        )
    )


    # --------------------------------------------------
    # Draw player HP bar
    # --------------------------------------------------

    pygame.draw.rect(
        screen,
        GRAY,
        (150, 50, 300, 30)
    )

    pygame.draw.rect(
        screen,
        GREEN,
        (150, 50, 3 * player.hp, 30)
    )


    # --------------------------------------------------
    # Draw enemy HP bar
    # --------------------------------------------------

    pygame.draw.rect(
        screen,
        GRAY,
        (550, 50, 300, 30)
    )

    pygame.draw.rect(
        screen,
        GREEN,
        (550, 50, 3 * enemy_hp, 30)
    )


    # --------------------------------------------------
    # Update display
    # --------------------------------------------------

    pygame.display.flip()


    # --------------------------------------------------
    # FPS
    # --------------------------------------------------

    clock.tick(60)


# --------------------------------------------------
# Quit
# --------------------------------------------------

pygame.quit()
sys.exit()