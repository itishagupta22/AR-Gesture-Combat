import cv2
import time
import mediapipe as mp

from cv.gesture_detector import detect_gesture
from backend.action_manager import gesture_to_action


# --------------------------------------------------
# 1. MediaPipe Hand Landmarker setup
# --------------------------------------------------

BaseOptions = mp.tasks.BaseOptions
HandLandmarker = mp.tasks.vision.HandLandmarker
HandLandmarkerOptions = mp.tasks.vision.HandLandmarkerOptions
VisionRunningMode = mp.tasks.vision.RunningMode

MODEL_PATH = "models/hand_landmarker.task"

options = HandLandmarkerOptions(
    base_options=BaseOptions(model_asset_path=MODEL_PATH),
    running_mode=VisionRunningMode.VIDEO,
    num_hands=2
)

# --------------------------------------------------
# 2. Open the webcam
# --------------------------------------------------

cap = cv2.VideoCapture(0)

# --------------------------------------------------
# 3. Start MediaPipe Hand Landmarker
# --------------------------------------------------

with HandLandmarker.create_from_options(options) as landmarker:

    while True:

        # Get a frame from webcam
        success, frame = cap.read()

        if not success:
            print("Could not access webcam.")
            break

        # Mirror the webcam
        frame = cv2.flip(frame, 1)

        # Convert BGR → RGB
        rgb_frame = cv2.cvtColor(
            frame,
            cv2.COLOR_BGR2RGB
        )

        # Convert OpenCV image into MediaPipe image
        mp_image = mp.Image(
            image_format=mp.ImageFormat.SRGB,
            data=rgb_frame
        )

        # Timestamp required for VIDEO mode
        timestamp_ms = int(time.time() * 1000)

        # Detect hands
        result = landmarker.detect_for_video(
            mp_image,
            timestamp_ms
        )

        # --------------------------------------------------
        # 4. Process detected hands
        # --------------------------------------------------

        if result.hand_landmarks:

            for hand_landmarks in result.hand_landmarks:

                gesture = detect_gesture(hand_landmarks)

                action = gesture_to_action(gesture)

                print("Gesture:", gesture)
                print("Action:", action)

                points = []

                # Get all 21 landmarks
                for index, landmark in enumerate(hand_landmarks):

                    x = int(
                        landmark.x * frame.shape[1]
                    )

                    y = int(
                        landmark.y * frame.shape[0]
                    )

                    points.append((x, y))

                    # Draw landmark
                    cv2.circle(
                        frame,
                        (x, y),
                        5,
                        (0, 255, 0),
                        -1
                    )

                    # Draw landmark number
                    cv2.putText(
                        frame,
                        str(index),
                        (x + 8, y - 8),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.5,
                        (255, 255, 255),
                        1
                    )

                # --------------------------------------------------
                # 5. Connect the landmarks
                # --------------------------------------------------

                connections = [

                    # Thumb
                    (0, 1),
                    (1, 2),
                    (2, 3),
                    (3, 4),

                    # Index finger
                    (0, 5),
                    (5, 6),
                    (6, 7),
                    (7, 8),

                    # Middle finger
                    (0, 9),
                    (9, 10),
                    (10, 11),
                    (11, 12),

                    # Ring finger
                    (0, 13),
                    (13, 14),
                    (14, 15),
                    (15, 16),

                    # Pinky
                    (0, 17),
                    (17, 18),
                    (18, 19),
                    (19, 20),

                    # Palm
                    (5, 9),
                    (9, 13),
                    (13, 17)
                ]

                # Draw connections
                for start, end in connections:

                    cv2.line(
                        frame,
                        points[start],
                        points[end],
                        (0, 255, 0),
                        2
                    )

        # --------------------------------------------------
        # 6. Display webcam
        # --------------------------------------------------

        cv2.imshow(
            "Hand Tracking",
            frame
        )

        # Press Q to quit
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

# --------------------------------------------------
# 7. Clean up
# --------------------------------------------------

cap.release()
cv2.destroyAllWindows()