# core/hand_tracker.py
import cv2
import mediapipe as mp
import numpy as np
import time

class HandTracker:
    def __init__(self, pinch_threshold=0.05, smoothing_factor=0.4):
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=2,
            min_detection_confidence=0.7,
            min_tracking_confidence=0.7
        )
        self.mp_draw = mp.solutions.drawing_utils
        self.pinch_threshold = pinch_threshold
        self.smoothing_factor = smoothing_factor
        self.prev_pos = None

        # Pinch click state (for menu/button interaction)
        self.was_pinching = False
        self.pinch_click_fired = False

    def process_frame(self, frame):
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.hands.process(frame_rgb)
        return results

    def get_hand_info(self, results, frame_width, frame_height):
        """Returns: (num_hands, pinch_active, smoothed_pos, thumb_down, error_msg)"""
        if not results or not results.multi_hand_landmarks:
            self.prev_pos = None
            self.was_pinching = False
            return 0, False, None, False, ""

        num_hands = len(results.multi_hand_landmarks)
        if num_hands > 1:
            self.prev_pos = None
            return num_hands, False, None, False, "USE ONE HAND ONLY"

        hand_lms = results.multi_hand_landmarks[0]

        # Extract landmarks
        landmarks = []
        for lm in hand_lms.landmark:
            x = int(lm.x * frame_width)
            y = int(lm.y * frame_height)
            landmarks.append((x, y))

        thumb_tip  = landmarks[self.mp_hands.HandLandmark.THUMB_TIP]
        index_tip  = landmarks[self.mp_hands.HandLandmark.INDEX_FINGER_TIP]
        middle_tip = landmarks[self.mp_hands.HandLandmark.MIDDLE_FINGER_TIP]
        ring_tip   = landmarks[self.mp_hands.HandLandmark.RING_FINGER_TIP]
        pinky_tip  = landmarks[self.mp_hands.HandLandmark.PINKY_TIP]

        fingertips = [index_tip, middle_tip, ring_tip, pinky_tip]

        wrist = landmarks[self.mp_hands.HandLandmark.WRIST]
        thumb_mcp = landmarks[self.mp_hands.HandLandmark.THUMB_MCP]
        middle_mcp = landmarks[self.mp_hands.HandLandmark.MIDDLE_FINGER_MCP]
        hand_size = max(1.0, np.hypot(wrist[0] - middle_mcp[0], wrist[1] - middle_mcp[1]))

        # Thumb down detection (Y increases downwards in OpenCV)
        # If thumb tip is significantly below the wrist, it's pointing down.
        thumb_down = (thumb_tip[1] > wrist[1] + (hand_size * 0.2))

        # Check pinch: thumb vs any finger
        min_dist = float('inf')
        for tip in fingertips:
            dist = np.hypot(thumb_tip[0] - tip[0], thumb_tip[1] - tip[1])
            min_dist = min(min_dist, dist)

        # Normalise by hand size instead of frame width so it works when hand is close
        normalized_dist = min_dist / hand_size
        # The threshold for this ratio should be around 0.3 or 0.4
        pinch_active = normalized_dist < (self.pinch_threshold * 4)

        # Use midpoint of thumb and index as cursor (more stable)
        raw_x = (thumb_tip[0] + index_tip[0]) // 2
        raw_y = (thumb_tip[1] + index_tip[1]) // 2
        raw_pos = (raw_x, raw_y)

        # Apply EMA smoothing
        if self.prev_pos is None:
            self.prev_pos = raw_pos
            smoothed_pos = raw_pos
        else:
            smoothed_pos = (
                int(self.prev_pos[0] * (1 - self.smoothing_factor) + raw_pos[0] * self.smoothing_factor),
                int(self.prev_pos[1] * (1 - self.smoothing_factor) + raw_pos[1] * self.smoothing_factor)
            )
            self.prev_pos = smoothed_pos

        return 1, pinch_active, smoothed_pos, thumb_down, ""

    def get_pinch_click(self, results, frame_width, frame_height):
        """Returns (pos, just_clicked, pinch_active, thumb_down)"""
        num_hands, pinch_active, pos, thumb_down, _ = self.get_hand_info(results, frame_width, frame_height)

        just_clicked = False
        if pinch_active and not self.was_pinching:
            just_clicked = True
        self.was_pinching = pinch_active

        return pos, just_clicked, pinch_active, thumb_down

    def draw_landmarks(self, frame, results):
        if results and results.multi_hand_landmarks:
            for hand_lms in results.multi_hand_landmarks:
                self.mp_draw.draw_landmarks(frame, hand_lms, self.mp_hands.HAND_CONNECTIONS)
