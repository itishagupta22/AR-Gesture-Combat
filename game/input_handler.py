import pygame


def get_keyboard_action():

    keys = pygame.key.get_pressed()

    if keys[pygame.K_SPACE]:
        return "ATTACK"

    if keys[pygame.K_b]:
        return "BLOCK"

    if keys[pygame.K_LEFT]:
        return "DODGE_LEFT"

    if keys[pygame.K_RIGHT]:
        return "DODGE_RIGHT"

    if keys[pygame.K_1]:
        return "SELECT_SWORD"

    if keys[pygame.K_2]:
        return "SELECT_BOW"

    return "NONE"