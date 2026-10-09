import cv2
import time
import mediapipe as mp

from cv.movement_detector import get_body_center, detect_dodge
from backend.action_manager import movement_to_action



# --------------------------------------------------
# 1. MediaPipe Pose Landmarker setup
# --------------------------------------------------

BaseOptions = mp.tasks.BaseOptions
PoseLandmarker = mp.tasks.vision.PoseLandmarker
PoseLandmarkerOptions = mp.tasks.vision.PoseLandmarkerOptions
VisionRunningMode = mp.tasks.vision.RunningMode

MODEL_PATH = "models/pose_landmarker.task"

options = PoseLandmarkerOptions(
    base_options=BaseOptions(model_asset_path=MODEL_PATH),
    running_mode=VisionRunningMode.VIDEO,
    num_poses=1
)


# --------------------------------------------------
# 2. Open webcam
# --------------------------------------------------

cap = cv2.VideoCapture(0)


# --------------------------------------------------
# 3. Start MediaPipe Pose Landmarker
# --------------------------------------------------

with PoseLandmarker.create_from_options(options) as landmarker:

    reference_x = None
    dodge_ready = True


    while True:

        success, frame = cap.read()

        if not success:
            print("Could not access webcam.")
            break

        # Mirror webcam
        frame = cv2.flip(frame, 1)

        # Convert BGR → RGB
        rgb_frame = cv2.cvtColor(
            frame,
            cv2.COLOR_BGR2RGB
        )

        # Convert to MediaPipe image
        mp_image = mp.Image(
            image_format=mp.ImageFormat.SRGB,
            data=rgb_frame
        )

        # Timestamp for VIDEO mode
        timestamp_ms = int(time.time() * 1000)

        # Detect pose
        result = landmarker.detect_for_video(
            mp_image,
            timestamp_ms
        )


        # --------------------------------------------------
        # 4. Process pose landmarks
        # --------------------------------------------------

        if result.pose_landmarks:

            for pose_landmarks in result.pose_landmarks:

                center_x, center_y = get_body_center(
                    pose_landmarks
                )

                # Set neutral position
                if reference_x is None:

                    reference_x = center_x
                    print("Neutral position set.")

                # Detect dodge
                dodge = detect_dodge(
                    reference_x,
                    center_x
                )

                if dodge_ready and dodge != "NONE":

                    action = movement_to_action(dodge)

                    print("Movement:", dodge)
                    print("Action:", action)

                    dodge_ready = False


                # Player has returned close to neutral
                if abs(center_x - reference_x) < 0.04:

                    dodge_ready = True

                # Convert body center to pixel coordinates
                center_pixel_x = int(
                    center_x * frame.shape[1]
                )

                center_pixel_y = int(
                    center_y * frame.shape[0]
                )

                # Draw body center
                cv2.circle(
                    frame,
                    (center_pixel_x, center_pixel_y),
                    10,
                    (0, 0, 255),
                    -1
                )

                points = []

                # Get all pose landmarks
                for index, landmark in enumerate(pose_landmarks):

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
                # 5. Pose connections
                # --------------------------------------------------

                connections = [

                    # Face
                    (0, 1),
                    (1, 2),
                    (2, 3),
                    (3, 7),
                    (0, 4),
                    (4, 5),
                    (5, 6),
                    (6, 8),

                    # Upper body
                    (11, 12),
                    (11, 13),
                    (13, 15),
                    (12, 14),
                    (14, 16),

                    # Torso
                    (11, 23),
                    (12, 24),
                    (23, 24),

                    # Left leg
                    (23, 25),
                    (25, 27),
                    (27, 29),
                    (29, 31),

                    # Right leg
                    (24, 26),
                    (26, 28),
                    (28, 30),
                    (30, 32)
                ]

                # Draw pose connections
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
            "Pose Tracking",
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