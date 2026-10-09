"""MediaPipe Tasks-based gesture and pose tracker."""
import math
import os
import time
import urllib.request

import cv2
import mediapipe as mp
import numpy as np

BaseOptions = mp.tasks.BaseOptions
HandLandmarker = mp.tasks.vision.HandLandmarker
HandLandmarkerOptions = mp.tasks.vision.HandLandmarkerOptions
PoseLandmarker = mp.tasks.vision.PoseLandmarker
PoseLandmarkerOptions = mp.tasks.vision.PoseLandmarkerOptions
VisionRunningMode = mp.tasks.vision.RunningMode
PoseLandmark = mp.tasks.vision.PoseLandmark

FINGER_TIPS = [4, 8, 12, 16, 20]
FINGER_PIPS = [3, 6, 10, 14, 18]

_MODELS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "models")
_HAND_MODEL = os.path.join(_MODELS_DIR, "hand_landmarker.task")
_POSE_MODEL = os.path.join(_MODELS_DIR, "pose_landmarker.task")
_MODEL_URLS = {
    _HAND_MODEL: (
        "https://storage.googleapis.com/mediapipe-models/"
        "hand_landmarker/hand_landmarker/float16/latest/hand_landmarker.task"
    ),
    _POSE_MODEL: (
        "https://storage.googleapis.com/mediapipe-models/"
        "pose_landmarker/pose_landmarker_lite/float16/latest/pose_landmarker_lite.task"
    ),
}


def _ensure_models():
    os.makedirs(_MODELS_DIR, exist_ok=True)
    for path, url in _MODEL_URLS.items():
        if os.path.isfile(path) and os.path.getsize(path) > 0:
            continue
        urllib.request.urlretrieve(url, path)


class VisionTracker:
    def __init__(self, cam_index=0, width=640, height=480):
        _ensure_models()
        self.cap = cv2.VideoCapture(cam_index)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
        self.hands = HandLandmarker.create_from_options(
            HandLandmarkerOptions(
                base_options=BaseOptions(model_asset_path=_HAND_MODEL),
                running_mode=VisionRunningMode.VIDEO,
                num_hands=2,
                min_hand_detection_confidence=0.6,
                min_tracking_confidence=0.6,
            )
        )
        self.pose = PoseLandmarker.create_from_options(
            PoseLandmarkerOptions(
                base_options=BaseOptions(model_asset_path=_POSE_MODEL),
                running_mode=VisionRunningMode.VIDEO,
                num_poses=1,
                min_pose_detection_confidence=0.6,
                min_tracking_confidence=0.6,
            )
        )
        self._timestamp_ms = 0

        # Registry: name -> callable(landmarks_list) -> bool
        self.gesture_registry = {
            "SHIELD": self._is_open_palm,
            "SWORD": self._is_victory_sign,
            "AXE": self._is_closed_fist,
        }

        self.center_x_ref = None
        self.center_y_ref = None
        self.torso_ref = None
        self.dodge_ready_x = True
        self.dodge_ready_y = True
        self.dodge_threshold_x = 0.07
        self.dodge_threshold_y = 0.045
        self.dodge_reset_threshold = 0.03

    # ---------- Public API ----------
    def read_frame(self):
        ok, frame = self.cap.read()
        if not ok:
            return None
        return cv2.flip(frame, 1)

    def process(self, frame):
        """Returns dict: {gesture, shield_area, dodge, body_dx, body_dy, pose_tracked, ...}"""
        rgb = np.ascontiguousarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
        now_ms = int(time.time() * 1000)
        if now_ms <= self._timestamp_ms:
            now_ms = self._timestamp_ms + 1
        self._timestamp_ms = now_ms

        hand_results = self.hands.detect_for_video(mp_image, now_ms)
        pose_results = self.pose.detect_for_video(mp_image, now_ms)

        result = {
            "gesture": None,
            "shield_area": 0.0,
            "dodge": None,
            "dodge_v": None,
            "arm_command": None,
            "thumb": None,
            "body_dx": 0.0,
            "body_dy": 0.0,
            "pose_tracked": False,
            "hand_landmarks": None,
            "pose_landmarks": None,
        }

        if hand_results.hand_landmarks:
            lm = hand_results.hand_landmarks[0]
            result["hand_landmarks"] = lm
            for hand in hand_results.hand_landmarks:
                if self._is_thumbs_up(hand):
                    result["thumb"] = "UP"
                    break
                if self._is_thumbs_down(hand):
                    result["thumb"] = "DOWN"
                    break
            for name, fn in self.gesture_registry.items():
                if fn(lm):
                    result["gesture"] = name
                    break
            if result["gesture"] == "SHIELD":
                result["shield_area"] = self._compute_hand_spread(lm)

        if pose_results.pose_landmarks:
            plm = pose_results.pose_landmarks[0]
            result["pose_landmarks"] = plm
            result["pose_tracked"] = True
            body_dx, body_dy, dodge, dodge_v = self._track_body(plm)
            result["body_dx"] = body_dx
            result["body_dy"] = body_dy
            result["dodge"] = dodge
            result["dodge_v"] = dodge_v
            result["arm_command"] = self._detect_arm_command(plm)

        return result

    def release(self):
        self.cap.release()
        self.hands.close()
        self.pose.close()

    def register_gesture(self, name, detector_fn):
        """Plug in new gestures: detector_fn(hand_landmarks) -> bool"""
        self.gesture_registry[name] = detector_fn

    # ---------- Gesture detectors ----------
    def _fingers_extended(self, lm):
        extended = []
        for tip, pip in zip(FINGER_TIPS, FINGER_PIPS):
            extended.append(lm[tip].y < lm[pip].y)
        return extended

    def _is_open_palm(self, lm):
        ext = self._fingers_extended(lm)
        return sum(ext) >= 4

    def _is_closed_fist(self, lm):
        ext = self._fingers_extended(lm)
        return sum(ext) == 0

    def _is_victory_sign(self, lm):
        ext = self._fingers_extended(lm)
        # index + middle up, ring + pinky down
        return ext[1] and ext[2] and not ext[3] and not ext[4]

    def _other_fingers_curled(self, lm):
        ext = self._fingers_extended(lm)
        return sum(1 for i in range(1, 5) if ext[i]) <= 1

    def _is_thumbs_up(self, lm):
        if not self._other_fingers_curled(lm):
            return False
        wrist, thumb_tip = lm[0], lm[4]
        other_tips = (lm[8], lm[12], lm[16], lm[20])
        return thumb_tip.y < wrist.y - 0.03 and all(thumb_tip.y < t.y - 0.02 for t in other_tips)

    def _is_thumbs_down(self, lm):
        if not self._other_fingers_curled(lm):
            return False
        wrist, thumb_tip = lm[0], lm[4]
        other_tips = (lm[8], lm[12], lm[16], lm[20])
        return thumb_tip.y > wrist.y + 0.03 and all(thumb_tip.y > t.y + 0.02 for t in other_tips)

    def _compute_hand_spread(self, lm):
        pts = [(lm[t].x, lm[t].y) for t in FINGER_TIPS]
        max_d = 0.0
        for i in range(len(pts)):
            for j in range(i + 1, len(pts)):
                d = math.dist(pts[i], pts[j])
                max_d = max(max_d, d)
        return max_d  # normalized 0..~0.5, larger spread = bigger shield

    def _body_signals(self, plm):
        """Horizontal = torso x. Vertical = nose + shoulders so crouch/stand is obvious."""
        left_sh = plm[PoseLandmark.LEFT_SHOULDER]
        right_sh = plm[PoseLandmark.RIGHT_SHOULDER]
        left_hip = plm[PoseLandmark.LEFT_HIP]
        right_hip = plm[PoseLandmark.RIGHT_HIP]
        nose = plm[PoseLandmark.NOSE]
        cx = (left_sh.x + right_sh.x + left_hip.x + right_hip.x) / 4.0
        shoulder_y = (left_sh.y + right_sh.y) / 2.0
        hip_y = (left_hip.y + right_hip.y) / 2.0
        cy = nose.y * 0.45 + shoulder_y * 0.55
        torso = max(0.1, abs(hip_y - shoulder_y))
        return cx, cy, torso

    def _track_body(self, plm):
        """
        Returns (body_dx, body_dy, dodge, dodge_v).
        Offsets are scaled by torso size so up/down still reads when you are far from the camera.
        Each axis dashes once per lean; return near center to dash again.
        """
        cx, cy, torso = self._body_signals(plm)

        if self.center_x_ref is None or self.center_y_ref is None:
            self.center_x_ref = cx
            self.center_y_ref = cy
            self.torso_ref = torso
            return 0.0, 0.0, None, None

        scale = max(self.torso_ref or torso, 0.1)
        body_dx = (cx - self.center_x_ref) / scale
        body_dy = (cy - self.center_y_ref) / scale

        dodge = None
        if self.dodge_ready_x:
            if body_dx > self.dodge_threshold_x:
                dodge = "DODGE_RIGHT"
                self.dodge_ready_x = False
            elif body_dx < -self.dodge_threshold_x:
                dodge = "DODGE_LEFT"
                self.dodge_ready_x = False
        elif abs(body_dx) < self.dodge_reset_threshold:
            self.dodge_ready_x = True

        dodge_v = None
        if self.dodge_ready_y:
            if body_dy > self.dodge_threshold_y:
                dodge_v = "DODGE_DOWN"
                self.dodge_ready_y = False
            elif body_dy < -self.dodge_threshold_y:
                dodge_v = "DODGE_UP"
                self.dodge_ready_y = False
        elif abs(body_dy) < self.dodge_reset_threshold:
            self.dodge_ready_y = True

        return body_dx, body_dy, dodge, dodge_v

    def _landmark_ok(self, lm, min_vis=0.45):
        vis = getattr(lm, "visibility", 1.0)
        if vis is None:
            vis = 1.0
        return vis >= min_vis

    def _detect_arm_command(self, plm):
        """PAUSE: clearly folded/crossed arms. Fighting stance and arms-at-sides must not match."""
        lw = plm[PoseLandmark.LEFT_WRIST]
        rw = plm[PoseLandmark.RIGHT_WRIST]
        le = plm[PoseLandmark.LEFT_ELBOW]
        re = plm[PoseLandmark.RIGHT_ELBOW]
        ls = plm[PoseLandmark.LEFT_SHOULDER]
        rs = plm[PoseLandmark.RIGHT_SHOULDER]
        lh = plm[PoseLandmark.LEFT_HIP]
        rh = plm[PoseLandmark.RIGHT_HIP]
        if not all(self._landmark_ok(p) for p in (lw, rw, le, re, ls, rs)):
            return None

        mid_x = (ls.x + rs.x) / 2.0
        hip_y = (lh.y + rh.y) / 2.0
        sh_y = (ls.y + rs.y) / 2.0
        span = max(0.08, abs(rs.x - ls.x))
        torso = max(0.1, abs(hip_y - sh_y))

        chest_top = sh_y - torso * 0.08
        chest_bot = sh_y + torso * 0.62
        if not (chest_top <= lw.y <= chest_bot and chest_top <= rw.y <= chest_bot):
            return None
        if abs(lw.y - rw.y) > torso * 0.28:
            return None

        # Each wrist must travel onto the opposite side of the chest.
        if not (lw.x > mid_x + span * 0.28 and rw.x < mid_x - span * 0.28):
            return None

        # Folded: wrists stacked near each other, not a wide guard.
        wrist_dist = math.hypot(lw.x - rw.x, lw.y - rw.y)
        if wrist_dist > span * 0.7:
            return None

        # Elbows stay out while the hands cross in front.
        if not (le.x < mid_x - span * 0.12 and re.x > mid_x + span * 0.12):
            return None
        if lw.x <= le.x or rw.x >= re.x:
            return None
        return "PAUSE"

    def recalibrate(self):
        self.center_x_ref = None
        self.center_y_ref = None
        self.torso_ref = None
        self.dodge_ready_x = True
        self.dodge_ready_y = True
