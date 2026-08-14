# screens/menu_screen.py
"""
Menu, How-To-Play, and Leaderboard screens.
Redesigned to match the reference image's neon arcade aesthetic.
"""
import cv2
import numpy as np
import time
import math
import random
import config
from utils.helpers import (
    draw_text, draw_text_centered, draw_panel, draw_neon_button,
    draw_neon_rect, draw_cursor, draw_scanlines, draw_star_bg,
    draw_hand_icon, draw_trophy_icon, draw_star, draw_target_icon,
    point_in_rect, NEON_GREEN, NEON_PINK, NEON_CYAN, NEON_GOLD,
    GestureButton
)
from utils.user_manager import get_or_create_user


# ─── Menu Screen ──────────────────────────────────────────────────────────────

class MenuScreen:
    def __init__(self, username):
        self.username   = username
        self.user_data  = get_or_create_user(username)
        self._t0        = time.time()
        self._build_buttons()

    def _build_buttons(self):
        W   = config.CAMERA_WIDTH
        H   = config.CAMERA_HEIGHT
        cx  = W // 2

        # ── PLAY GAME — large primary button ──
        pb_w, pb_h = 620, 90
        pb_x = cx - pb_w // 2
        pb_y = H // 2 - 120

        # ── Three smaller secondary buttons ──
        sb_w, sb_h = 188, 64
        sb_gap     = 18
        sb_total   = 3 * sb_w + 2 * sb_gap
        sb_x       = cx - sb_total // 2
        sb_y       = pb_y + pb_h + 24

        self.buttons = [
            GestureButton("  PLAY GAME",
                          (pb_x, pb_y, pb_w, pb_h),
                          border_color=NEON_GREEN,
                          icon="> ",
                          subtitle="Start a new maze"),
            GestureButton("HOW TO PLAY",
                          (sb_x, sb_y, sb_w, sb_h),
                          border_color=(255, 180, 0),
                          icon="? "),
            GestureButton("HIGH SCORES",
                          (sb_x + sb_w + sb_gap, sb_y, sb_w, sb_h),
                          border_color=NEON_GOLD,
                          icon="* "),
            GestureButton("  QUIT",
                          (sb_x + 2*(sb_w + sb_gap), sb_y, sb_w, sb_h),
                          border_color=(40, 40, 200),
                          icon="x "),
        ]
        self._actions = ["GAME", "HOW_TO_PLAY", "HIGH_SCORES", "QUIT"]

    def set_username(self, username):
        self.username  = username
        self.user_data = get_or_create_user(username)
        self._build_buttons()

    def _draw_background(self, frame):
        draw_star_bg(frame)

    def update(self, frame, key, hand_results=None):
        self.user_data = get_or_create_user(self.username)
        self._draw_background(frame)

        W, H = config.CAMERA_WIDTH, config.CAMERA_HEIGHT
        cx = W // 2
        t  = time.time() - self._t0

        # ── Outer panel ──
        draw_panel(frame, 40, 30, W - 80, H - 60,
                   border_color=config.COLOR_UI_BORDER, label="MAIN MENU")

        # ── "WELCOME BACK," ──
        draw_text(frame, "WELCOME BACK,", (cx - 140, 85),
                  font_scale=0.7, color=(120, 110, 100))

        # ── Username title ──
        uname_display = self.username.upper()
        pulse = abs(math.sin(t * 2))
        u_scale = 1.6
        (uw, _), _ = cv2.getTextSize(uname_display, cv2.FONT_HERSHEY_DUPLEX, u_scale, 3)
        ux = cx - uw // 2
        # Shadow
        cv2.putText(frame, uname_display, (ux + 2, 130 + 2),
                    cv2.FONT_HERSHEY_DUPLEX, u_scale, (225, 220, 215), 3, cv2.LINE_AA)
        cv2.putText(frame, uname_display, (ux, 130),
                    cv2.FONT_HERSHEY_DUPLEX, u_scale, config.COLOR_PLAYER, 3, cv2.LINE_AA)
        
        # Wave emoji replacement: small hand icon
        draw_hand_icon(frame, ux + uw + 28, 115, size=28,
                       color=NEON_GREEN, style="open")

        # ── Separator ──
        cv2.line(frame, (80, 148), (W - 80, 148), config.COLOR_UI_BORDER, 1)

        # ── Cursor ──
        cursor_pos   = None
        pinch_active = False
        if hand_results and hand_results.multi_hand_landmarks:
            import mediapipe as mp
            lms   = hand_results.multi_hand_landmarks[0]
            mp_h  = mp.solutions.hands
            thumb = lms.landmark[mp_h.HandLandmark.THUMB_TIP]
            index = lms.landmark[mp_h.HandLandmark.INDEX_FINGER_TIP]
            tx = int(thumb.x * W); ty = int(thumb.y * H)
            ix = int(index.x * W); iy = int(index.y * H)
            dist = np.hypot(tx - ix, ty - iy) / W
            pinch_active = dist < config.PINCH_THRESHOLD
            cursor_pos   = ((tx + ix) // 2, (ty + iy) // 2)

        # ── Buttons ──
        for btn, action in zip(self.buttons, self._actions):
            btn.draw(frame, cursor_pos, pinch_active)
            triggered, _ = btn.update(cursor_pos, pinch_active)
            if triggered:
                return action

        draw_cursor(frame, cursor_pos, pinch_active)

        # ── Stats bar ──
        stats_y = H - 62
        cv2.line(frame, (80, stats_y - 12), (W - 80, stats_y - 12), config.COLOR_UI_BORDER, 1)
        bs   = self.user_data.get('best_score', 0)
        gp   = self.user_data.get('games_played', 0)

        draw_star(frame, 100, stats_y + 4, 10, 5, NEON_GOLD, -1)
        draw_text(frame, f"BEST SCORE  {bs}",
                  (118, stats_y + 10), font_scale=0.72, color=config.COLOR_TEXT)

        # Games icon (simple controller shape)
        gx = W - 280
        cv2.rectangle(frame, (gx, stats_y - 4), (gx + 22, stats_y + 14),
                      config.COLOR_PLAYER, 1, cv2.LINE_AA)
        draw_text(frame, f"GAMES PLAYED  {gp}",
                  (gx + 28, stats_y + 10), font_scale=0.72, color=config.COLOR_TEXT)

        # ── Bottom hint ──
        draw_text_centered(frame,
                           "Pinch & hold on a button for 1 sec  |  Keys: 1-4",
                           cx, H - 30, font_scale=0.56, color=(140, 130, 120))

        if key == ord('1'):  return "GAME"
        elif key == ord('2'):  return "HOW_TO_PLAY"
        elif key == ord('3'):  return "HIGH_SCORES"
        elif key == ord('4'):  return "QUIT"

        return "MENU"


# ─── How To Play ─────────────────────────────────────────────────────────────

class HowToPlayScreen:
    STEPS = [
        ("1", "Show ONE hand to the camera.",             (120, 180, 40),  "open"),
        ("2", "Pinch thumb + index finger to control.",   (120, 180, 40),  "pinch"),
        ("3", "Thumb Down to go BACK (ESC).",             (250, 100, 100), "open"),
        ("4", "Reach the BLUE cell to win!",              (245, 180, 100), "open"),
    ]

    def update(self, frame, key, hand_results=None):
        W, H = config.CAMERA_WIDTH, config.CAMERA_HEIGHT
        cx   = W // 2

        # Background
        draw_star_bg(frame)

        # Panel
        px, py, pw, ph = 80, 40, W - 160, H - 80
        draw_panel(frame, px, py, pw, ph,
                   border_color=config.COLOR_UI_BORDER, label="HOW TO PLAY",
                   corner_label_color=(120, 110, 100))

        # Title
        title = "HOW TO PLAY"
        (tw, _), _ = cv2.getTextSize(title, cv2.FONT_HERSHEY_DUPLEX, 1.8, 3)
        # Shadow
        cv2.putText(frame, title, (cx - tw // 2 + 2, py + 62 + 2),
                    cv2.FONT_HERSHEY_DUPLEX, 1.8, (225, 220, 215), 3, cv2.LINE_AA)
        cv2.putText(frame, title, (cx - tw // 2, py + 62),
                    cv2.FONT_HERSHEY_DUPLEX, 1.8, NEON_PINK, 3, cv2.LINE_AA)

        cv2.line(frame, (px + 40, py + 80), (px + pw - 40, py + 80),
                 config.COLOR_UI_BORDER, 1)

        # Steps
        step_y = py + 120
        for num, text, col, hand_style in self.STEPS:
            # Step badge circle
            badge_cx = px + 75
            cv2.circle(frame, (badge_cx, step_y + 8), 22,
                       (250, 245, 240), -1)
            cv2.circle(frame, (badge_cx, step_y + 8), 22,
                       config.COLOR_UI_BORDER, 1, cv2.LINE_AA)
            draw_text_centered(frame, num, badge_cx, step_y + 14,
                               font_scale=0.85, color=config.COLOR_TEXT,
                               font=cv2.FONT_HERSHEY_DUPLEX)

            # Hand icon next to badge
            draw_hand_icon(frame, badge_cx + 55, step_y + 8,
                           size=32, color=col, style=hand_style)

            # Step text
            draw_text(frame, text, (badge_cx + 95, step_y + 14),
                      font_scale=0.78, color=col)

            step_y += 72

        draw_text_centered(frame, "Thumb Down to GO BACK",
                           cx, py + ph + 22,
                           font_scale=0.58, color=(100, 100, 140))

        return "HOW_TO_PLAY"


# ─── Leaderboard ─────────────────────────────────────────────────────────────

class HighScoreScreen:

    def update(self, frame, key, hand_results=None):
        import utils.user_manager as um
        users        = um.load_users()
        sorted_users = sorted(users.items(),
                              key=lambda x: x[1].get('best_score', 0),
                              reverse=True)

        W, H = config.CAMERA_WIDTH, config.CAMERA_HEIGHT
        cx   = W // 2

        # Background
        draw_star_bg(frame)

        # Panel
        px, py, pw, ph = 60, 30, W - 120, H - 60
        draw_panel(frame, px, py, pw, ph,
                   border_color=config.COLOR_UI_BORDER, label="LEADERBOARD",
                   corner_label_color=(120, 110, 100))

        # Trophy + Title
        draw_trophy_icon(frame, px + 60, py + 52, size=30, color=NEON_GOLD)
        cv2.putText(frame, "LEADERBOARD", (px + 95, py + 62),
                    cv2.FONT_HERSHEY_DUPLEX, 1.5, NEON_GOLD, 2, cv2.LINE_AA)

        cv2.line(frame, (px + 30, py + 80), (px + pw - 30, py + 80),
                 config.COLOR_UI_BORDER, 1)

        # ── TOP 3 Podium ──
        podium_y = py + 100
        podium_h = 110
        podium_configs = [
            # (rank_in_sorted, x_offset, height_extra, border_col, rank_label, rank_col)
            (1, -250, 0,  (180, 185, 190), "2",   (130, 135, 140)),   # 2nd – left
            (0,    0, 30, (50, 180, 240),  "1",   (20, 150, 220)),     # 1st – centre
            (2,  250, 0,  (80, 120, 180),  "3",   (60, 100, 160)),    # 3rd – right
        ]
        for rank_idx, xoff, hex, bdr, rnk_lbl, rnk_col in podium_configs:
            if rank_idx >= len(sorted_users):
                continue
            uname, data = sorted_users[rank_idx]
            bs   = data.get('best_score', 0)
            pw2  = 175
            ph2  = podium_h + hex
            bx2  = cx + xoff - pw2 // 2
            by2  = podium_y + (0 if hex else 30)

            # Card
            draw_panel(frame, bx2, by2, pw2, ph2, border_color=bdr)

            # Rank badge
            draw_text_centered(frame, rnk_lbl,
                               bx2 + pw2 // 2, by2 + 30,
                               font_scale=1.1, color=rnk_col,
                               font=cv2.FONT_HERSHEY_DUPLEX)

            # Name
            draw_text_centered(frame, uname[:12].upper(),
                               bx2 + pw2 // 2, by2 + 60,
                               font_scale=0.72, color=config.COLOR_TEXT)

            # Score
            draw_star(frame, bx2 + pw2 // 2 - 26, by2 + 82, 8, 4,
                      NEON_GOLD, -1)
            draw_text_centered(frame, str(bs),
                               bx2 + pw2 // 2 + 10, by2 + 88,
                               font_scale=0.8, color=rnk_col)

        # ── Table header ──
        tbl_y  = podium_y + podium_h + 60
        cols   = [px + 30, px + 70, px + 240, px + 440, px + 600, px + 740]
        heads  = ["#", "PLAYER", "BEST SCORE", "BEST TIME", "GAMES"]
        for col_x, h2 in zip(cols, heads):
            draw_text(frame, h2, (col_x, tbl_y),
                      font_scale=0.6, color=(140, 130, 120))
        tbl_y += 6
        cv2.line(frame, (px + 20, tbl_y), (px + pw - 20, tbl_y),
                 config.COLOR_UI_BORDER, 1)
        tbl_y += 22

        for i, (uname, data) in enumerate(sorted_users[:8]):
            t_str = f"{data.get('best_time', 0) or 0:.1f}s" if data.get('best_time') else "--"
            bs    = data.get('best_score', 0)

            # Alternating row
            row_col = (250, 248, 245) if i % 2 == 0 else (255, 255, 255)
            cv2.rectangle(frame, (px + 14, tbl_y - 16),
                          (px + pw - 14, tbl_y + 8), row_col, -1)
            cv2.line(frame, (px + 14, tbl_y + 8), (px + pw - 14, tbl_y + 8), (240, 235, 230), 1)

            rank_col = config.COLOR_TEXT
            if i == 0:
                rank_col = (20, 150, 220)
            elif i == 1:
                rank_col = (130, 135, 140)
            elif i == 2:
                rank_col = (60, 100, 160)

            draw_text(frame, str(i + 1),       (cols[0], tbl_y), 0.65, 1, rank_col)
            draw_text(frame, uname[:16],        (cols[1], tbl_y), 0.65, 1, rank_col)
            draw_text(frame, str(bs),           (cols[2], tbl_y), 0.65, 1, rank_col)
            draw_text(frame, t_str,             (cols[3], tbl_y), 0.65, 1, rank_col)
            draw_text(frame, str(data.get('games_played', 0)),
                      (cols[4], tbl_y), 0.65, 1, rank_col)
            tbl_y += 30

        # ── Your best row ──
        cv2.line(frame, (px + 20, tbl_y + 4), (px + pw - 20, tbl_y + 4),
                 (70, 55, 110), 1)
        # Try to get current user — stored externally via set_username or fallback
        draw_text_centered(frame, "Thumb Down to GO BACK",
                           cx, py + ph + 20,
                           font_scale=0.58, color=(100, 100, 140))

        return "HIGH_SCORES"
