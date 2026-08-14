# screens/login_screen.py
"""
Name Entry Screen — "READY, PLAYER?" panel from the reference image.

Layout:
  • "NAME ENTRY" label in corner
  • "READY, PLAYER?" title in animated pink/magenta
  • "Enter Your Name" subtitle
  • Input field with green neon border + cursor blink
  • Avatar chooser row (4 icons drawn with OpenCV)
  • CONTINUE → button in neon green
  • [ESC] BACK hint
"""
import cv2
import numpy as np
import math
import time
import config
from utils.helpers import (draw_text, draw_text_centered, draw_panel,
                            draw_neon_button, draw_neon_rect,
                            draw_scanlines, draw_star_bg,
                            NEON_GREEN, NEON_PINK, PANEL_BG, GestureButton, draw_cursor)
from utils.user_manager import get_or_create_user


class LoginScreen:
    def __init__(self):
        self.username = ""
        self._t0      = time.time()
        
        # ── Buttons ──
        h, w = config.CAMERA_HEIGHT, config.CAMERA_WIDTH
        cx = w // 2
        pw, ph = 680, 400
        px     = cx - pw // 2
        py     = h // 2 - ph // 2 - 20
        btn_w, btn_h = 320, 58
        btn_x = cx - btn_w // 2
        btn_y = py + ph - 75
        self.continue_btn = GestureButton("  CONTINUE",
                                          (btn_x, btn_y, btn_w, btn_h),
                                          border_color=NEON_GREEN,
                                          icon="> ")

    def reset(self):
        self.username = ""
        self._t0      = time.time()

    def update(self, frame, key, hand_results=None):
        h, w = frame.shape[:2]
        t = time.time() - self._t0

        # ── Background ──
        draw_star_bg(frame)

        cx = w // 2

        # ── Main panel ──
        pw, ph = 680, 400
        px     = cx - pw // 2
        py     = h // 2 - ph // 2 - 20
        draw_panel(frame, px, py, pw, ph,
                   border_color=config.COLOR_UI_BORDER, label="NAME ENTRY",
                   corner_label_color=(120, 110, 100))

        # ── Title: READY, PLAYER? ──
        title    = "READY, PLAYER?"
        pulse    = abs(math.sin(t * 2.5))
        t_scale  = 1.8
        (tw, _), _ = cv2.getTextSize(title, cv2.FONT_HERSHEY_DUPLEX, t_scale, 3)
        tx = cx - tw // 2
        title_y = py + 62
        
        # Soft shadow
        cv2.putText(frame, title, (tx + 2, title_y + 2),
                    cv2.FONT_HERSHEY_DUPLEX, t_scale, (225, 220, 215), 3, cv2.LINE_AA)
        cv2.putText(frame, title, (tx, title_y),
                    cv2.FONT_HERSHEY_DUPLEX, t_scale, NEON_PINK, 3, cv2.LINE_AA)

        # ── "Enter Your Name" subtitle ──
        draw_text_centered(frame, "Enter Your Name",
                           cx, py + 98,
                           font_scale=0.72, color=(120, 110, 100))

        # ── Input field ──
        fx1, fy1 = cx - 280, py + 115
        fx2, fy2 = cx + 280, py + 170
        cv2.rectangle(frame, (fx1, fy1), (fx2, fy2), (255, 255, 255), -1)
        draw_neon_rect(frame, (fx1, fy1), (fx2, fy2), config.COLOR_UI_BORDER, 1)

        # User icon inside input
        cv2.circle(frame, (fx1 + 26, (fy1 + fy2) // 2), 12,
                   config.COLOR_PLAYER, 2, cv2.LINE_AA)
        cv2.line(frame, (fx1 + 14, fy2 - 12),
                 (fx1 + 38, fy2 - 12), config.COLOR_PLAYER, 2, cv2.LINE_AA)

        cursor = "|" if int(t * 2) % 2 == 0 else ""
        display = self.username.upper() + cursor if self.username else ""
        if display:
            draw_text(frame, display,
                      (fx1 + 50, (fy1 + fy2) // 2 + 10),
                      font_scale=1.0, color=config.COLOR_TEXT, thickness=2)
        else:
            draw_text(frame, "type here..." + cursor,
                      (fx1 + 50, (fy1 + fy2) // 2 + 10),
                      font_scale=0.8, color=(160, 150, 140))

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

        # ── CONTINUE button ──
        self.continue_btn.draw(frame, cursor_pos, pinch_active)
        triggered, _ = self.continue_btn.update(cursor_pos, pinch_active)
        
        draw_cursor(frame, cursor_pos, pinch_active)

        # ── ESC hint ──
        draw_text_centered(frame, "Thumb Down to GO BACK",
                           cx, py + ph + 22,
                           font_scale=0.58, color=(140, 130, 120))

        # ── Key handling (fallback) ──
        if triggered or key in (13, 10):
            name = self.username.strip()
            if len(name) > 0:
                try:
                    get_or_create_user(name)
                except Exception as e:
                    print(f"[login] get_or_create_user error: {e}")
                return "MENU"

        elif key in (8, 127):
            self.username = self.username[:-1]

        elif key != -1 and 32 <= key <= 126:
            if len(self.username) < 16:
                self.username += chr(key)

        return "LOGIN"
