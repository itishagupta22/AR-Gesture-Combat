def get_body_center(landmarks):

    left_shoulder = landmarks[11]
    right_shoulder = landmarks[12]

    left_hip = landmarks[23]
    right_hip = landmarks[24]

    center_x = (
        left_shoulder.x
        + right_shoulder.x
        + left_hip.x
        + right_hip.x
    ) / 4

    center_y = (
        left_shoulder.y
        + right_shoulder.y
        + left_hip.y
        + right_hip.y
    ) / 4

    return center_x, center_y


def detect_dodge(reference_x, current_x, threshold=0.08):

    displacement = current_x - reference_x

    if displacement < -threshold:
        return "DODGE_LEFT"

    if displacement > threshold:
        return "DODGE_RIGHT"

    return "NONE"