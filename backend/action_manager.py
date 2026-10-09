# -----------------------------------------
# Action Manager
# Converts input signals into game actions
# -----------------------------------------


GESTURE_ACTIONS = {

    "FIST": "ATTACK",

    "OPEN_PALM": "BLOCK",

    "VICTORY": "SELECT_BOW",

    "INDEX_UP": "SELECT_SWORD",

}


MOVEMENT_ACTIONS = {

    "DODGE_LEFT": "DODGE_LEFT",

    "DODGE_RIGHT": "DODGE_RIGHT",

}


def gesture_to_action(gesture):

    return GESTURE_ACTIONS.get(
        gesture,
        "NONE"
    )


def movement_to_action(movement):

    return MOVEMENT_ACTIONS.get(
        movement,
        "NONE"
    )

