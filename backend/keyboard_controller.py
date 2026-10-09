import keyboard
from backend.action_manager import gesture_to_action, movement_to_action


def get_keyboard_action():

    if keyboard.is_pressed("space"):
        return "ATTACK"

    if keyboard.is_pressed("b"):
        return "BLOCK"

    if keyboard.is_pressed("left"):
        return "DODGE_LEFT"

    if keyboard.is_pressed("right"):
        return "DODGE_RIGHT"

    if keyboard.is_pressed("1"):
        return "SELECT_SWORD"

    if keyboard.is_pressed("2"):
        return "SELECT_SHIELD"

    return "NONE"


if __name__ == "__main__":

    print("Keyboard controller running.")
    print("SPACE = Attack")
    print("B = Block")
    print("LEFT = Dodge Left")
    print("RIGHT = Dodge Right")
    print("1 = Sword")
    print("2 = Shield")
    print("ESC = Exit")

    while True:

        if keyboard.is_pressed("esc"):
            break

        action = get_keyboard_action()

        if action != "NONE":
            print("Action:", action)
