def is_finger_up(landmarks, tip_id, pip_id):
    """
    Check whether a finger is extended.

    landmarks: MediaPipe hand landmarks
    tip_id: fingertip landmark number
    pip_id: middle joint landmark number
    """

    tip = landmarks[tip_id]
    pip = landmarks[pip_id]

    return tip.y < pip.y
def get_finger_states(landmarks):
    index_up = is_finger_up(landmarks, 8, 6)
    middle_up = is_finger_up(landmarks, 12, 10)
    ring_up = is_finger_up(landmarks, 16, 14)
    pinky_up = is_finger_up(landmarks, 20, 18)

    return {
        "index": index_up,
        "middle": middle_up,
        "ring": ring_up,
        "pinky": pinky_up
    }

def detect_gesture(landmarks):
    states = get_finger_states(landmarks)

    index = states["index"]
    middle = states["middle"]
    ring = states["ring"]
    pinky = states["pinky"]

    # Victory gesture ✌️ 
    if index and middle and not ring and not pinky:
        return "VICTORY"

    # Open palm ✋
    if index and middle and ring and pinky:
        return "OPEN_PALM"

    # Fist ✊
    if not index and not middle and not ring and not pinky:
        return "FIST"

    # Index finger only ☝️
    if index and not middle and not ring and not pinky:
        return "INDEX_UP"

    return "UNKNOWN"