# screens/start_screen.py
"""
Start Screen — matches the "START SCREEN" panel in the reference image.
Redesigned with the light theme.
"""
import cv2
import numpy as np
import math
import time
import config
from utils.helpers import (draw_text, draw_text_centered, draw_panel,
                            draw_neon_button, draw_hand_icon,
                            draw_scanlines, draw_star_bg, NEON_GREEN, NEON_PINK, GestureButton, draw_cursor)

class StartScreen:
    def __init__(self):
        self._t0 = time.time()
        # ── Buttons ──
        h, w = config.CAMERA_HEIGHT, config.CAMERA_WIDTH
        cx = w // 2
        btn_w, btn_h = 340, 62
        btn_x = cx - btn_w // 2
        btn_y = h // 2 + 145
        self.start_btn = GestureButton("  START GAME",
                                       (btn_x, btn_y, btn_w, btn_h),
                                       border_color=NEON_GREEN,
                                       icon="> ")

    def update(self, frame, key, hand_results=None):
        h, w = frame.shape[:2]
        t = time.time() - self._t0

        # ── Background ──
        draw_star_bg(frame)

        # ── Outer panel ──
        px, py, pw, ph = 60, 40, w - 120, h - 80
        draw_panel(frame, px, py, pw, ph,
                   border_color=config.COLOR_UI_BORDER, label="START SCREEN")

        cx = w // 2

        # ── Animated HAND MAZE title (flat soft offset shadow) ──
        pulse = abs(math.sin(t * 2))
        title = "HAND MAZE"
        # Shadow
        cv2.putText(frame, title, (cx - 240 + 2, 155 + 2),
                    cv2.FONT_HERSHEY_DUPLEX, 3.2, (225, 220, 215), 3, cv2.LINE_AA)
        # Main text
        cv2.putText(frame, title, (cx - 240, 155),
                    cv2.FONT_HERSHEY_DUPLEX, 3.2, config.COLOR_PLAYER, 3, cv2.LINE_AA)

        # ── Subtitle: GESTURE ADVENTURE ──
        sub = "GESTURE ADVENTURE"
        (sw, _), _ = cv2.getTextSize(sub, cv2.FONT_HERSHEY_SIMPLEX, 1.0, 2)
        # Shadow
        cv2.putText(frame, sub, (cx - sw // 2 + 1, 195 + 1),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.0, (235, 230, 225), 2, cv2.LINE_AA)
        # Main text
        cv2.putText(frame, sub, (cx - sw // 2, 195),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.0, NEON_PINK, 2, cv2.LINE_AA)

        # ── Animated hand icon (open-palm vector style) ──
        hand_y       = h // 2 - 10
        float_offset = int(math.sin(t * 2.5) * 10)

        # ── Detailed open-palm hand icon ──
        oy = hand_y + float_offset   # origin Y (centre of palm)
        ox = cx                       # origin X
        c  = (60, 60, 60)            # dark charcoal outline colour
        lw = 3                        # line width

        # ── Palm body ──
        palm_pts = np.array([
            [ox - 55, oy + 10],   # left wrist
            [ox - 60, oy - 20],   # left palm
            [ox - 55, oy - 50],   # knuckle base left
            [ox - 38, oy - 52],
            [ox - 22, oy - 55],
            [ox,      oy - 57],
            [ox + 22, oy - 55],
            [ox + 38, oy - 52],
            [ox + 55, oy - 45],   # knuckle base right (pinky)
            [ox + 60, oy - 20],
            [ox + 55, oy + 10],   # right wrist
            [ox + 35, oy + 55],   # wrist curve right
            [ox,      oy + 65],   # wrist bottom
            [ox - 35, oy + 55],   # wrist curve left
        ], np.int32)
        cv2.fillPoly(frame, [palm_pts], (240, 240, 240))         # white fill
        cv2.polylines(frame, [palm_pts], True, c, lw, cv2.LINE_AA)

        # ── Thumb (angled left) ──
        thumb_pts = np.array([
            [ox - 55, oy - 10],
            [ox - 75, oy - 30],
            [ox - 85, oy - 55],
            [ox - 78, oy - 72],
            [ox - 63, oy - 68],
            [ox - 55, oy - 50],
            [ox - 50, oy - 20],
        ], np.int32)
        cv2.fillPoly(frame, [thumb_pts], (240, 240, 240))
        cv2.polylines(frame, [thumb_pts], True, c, lw, cv2.LINE_AA)
        # thumb knuckle crease
        cv2.line(frame, (ox - 72, oy - 42), (ox - 60, oy - 52), c, 1, cv2.LINE_AA)

        # Helper: draw one upright finger
        def draw_finger(fx, fy_base, fw, fh, tip_r):
            """Draw a rounded-top finger rectangle."""
            pts = np.array([
                [fx - fw,  fy_base],
                [fx - fw,  fy_base - fh + tip_r],
                [fx,       fy_base - fh - tip_r // 2],
                [fx + fw,  fy_base - fh + tip_r],
                [fx + fw,  fy_base],
            ], np.int32)
            cv2.fillPoly(frame, [pts], (240, 240, 240))
            cv2.polylines(frame, [pts], True, c, lw, cv2.LINE_AA)

        # ── Index finger ──
        draw_finger(ox - 28, oy - 52, 13, 70, 10)
        cv2.line(frame, (ox - 39, oy - 82), (ox - 17, oy - 82), c, 1, cv2.LINE_AA)  # knuckle
        cv2.line(frame, (ox - 39, oy - 96), (ox - 17, oy - 96), c, 1, cv2.LINE_AA)

        # ── Middle finger ──
        draw_finger(ox - 5,  oy - 56, 13, 80, 10)
        cv2.line(frame, (ox - 16, oy - 90), (ox + 6,  oy - 90), c, 1, cv2.LINE_AA)
        cv2.line(frame, (ox - 16, oy - 104), (ox + 6, oy - 104), c, 1, cv2.LINE_AA)

        # ── Ring finger ──
        draw_finger(ox + 18, oy - 53, 13, 74, 10)
        cv2.line(frame, (ox + 7,  oy - 85), (ox + 29, oy - 85), c, 1, cv2.LINE_AA)
        cv2.line(frame, (ox + 7,  oy - 99), (ox + 29, oy - 99), c, 1, cv2.LINE_AA)

        # ── Pinky finger ──
        draw_finger(ox + 40, oy - 46, 11, 58, 9)
        cv2.line(frame, (ox + 30, oy - 72), (ox + 50, oy - 72), c, 1, cv2.LINE_AA)
        cv2.line(frame, (ox + 30, oy - 83), (ox + 50, oy - 83), c, 1, cv2.LINE_AA)

        # ── Palm crease lines ──
        cv2.line(frame, (ox - 52, oy - 15), (ox + 30, oy + 5),  c, 1, cv2.LINE_AA)
        cv2.line(frame, (ox - 30, oy + 10), (ox + 45, oy + 20), c, 1, cv2.LINE_AA)
        cv2.line(frame, (ox - 10, oy + 20), (ox + 20, oy + 50), c, 1, cv2.LINE_AA)

        # Soft pulsing ring behind the hand
        ring_alpha = int(80 + 50 * abs(math.sin(t * 2)))
        cv2.circle(frame, (cx, hand_y + float_offset),
                   90, config.COLOR_UI_BORDER, 1, cv2.LINE_AA)

        # ── "SHOW ONE HAND TO BEGIN" ──
        show_text = "SHOW ONE HAND TO BEGIN"
        (stw, _), _ = cv2.getTextSize(show_text, cv2.FONT_HERSHEY_SIMPLEX, 0.9, 2)
        draw_text(frame, show_text,
                  (cx - stw // 2, h // 2 + 110),
                  font_scale=0.9, color=(120, 110, 100))

        # ── Cursor ──
        cursor_pos   = None
        pinch_active = False
        if hand_results and hand_results.multi_hand_landmarks:
            import mediapipe as mp
            lms   = hand_results.multi_hand_landmarks[0]
            mp_h  = mp.solutions.hands
            thumb = lms.landmark[mp_h.HandLandmark.THUMB_TIP]
            index = lms.landmark[mp_h.HandLandmark.INDEX_FINGER_TIP]
            tx = int(thumb.x * w); ty = int(thumb.y * h)
            ix = int(index.x * w); iy = int(index.y * h)
            dist = np.hypot(tx - ix, ty - iy) / w
            pinch_active = dist < config.PINCH_THRESHOLD
            cursor_pos   = ((tx + ix) // 2, (ty + iy) // 2)

        # ── START GAME button ──
        self.start_btn.draw(frame, cursor_pos, pinch_active)
        triggered, _ = self.start_btn.update(cursor_pos, pinch_active)
        if triggered:
            return "LOGIN"

        draw_cursor(frame, cursor_pos, pinch_active)

        # ── ESC hint ──
        draw_text_centered(frame, "Thumb Down to QUIT",
                           cx, h - 55,
                           font_scale=0.6, color=(140, 130, 120))

        # ── Key handling (fallback) ──
        if key not in (-1, 255):
            return "LOGIN"

        return "START"
