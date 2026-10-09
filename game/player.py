import pygame


class Player:

    def __init__(self, x, y):

        self.x = x
        self.y = y

        self.width = 80
        self.height = 120

        self.hp = 100

        self.speed = 20

        self.is_blocking = False

        self.weapon = "SWORD"

    def handle_action(self, action):

        if action == "DODGE_LEFT":
            self.x -= self.speed

        elif action == "DODGE_RIGHT":
            self.x += self.speed

        elif action == "ATTACK":
            print("Player attacks!")

        elif action == "BLOCK":
            self.is_blocking = True

        elif action == "SELECT_SWORD":
            self.weapon = "SWORD"
            print("Weapon: SWORD")

        elif action == "SELECT_BOW":
            self.weapon = "BOW"
            print("Weapon: BOW")

    def update(self):

        # Keep player inside the screen
        if self.x < 0:
            self.x = 0

        if self.x > 1000 - self.width:
            self.x = 1000 - self.width

    def draw(self, screen):

        pygame.draw.rect(
            screen,
            (50, 100, 200),
            (self.x, self.y, self.width, self.height)
        )