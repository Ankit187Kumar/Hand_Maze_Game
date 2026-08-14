# screens/game_screen.py
"""
Game screen — cell-based green box navigation with redesigned HUD.

MOVEMENT:
  • Pinch + move hand → green box snaps to adjacent cells instantly
  • Forward (new cell) = +1 score  |  Backward (prev cell) = -1 score
  • Score cannot go below 0
  • Win = reach the BLUE end cell
"""

import cv2
import numpy as np
import time
import math
import config
from core.maze_generator import MazeGenerator
from utils.helpers import (
    draw_text, draw_text_centered, draw_panel, draw_neon_button,
    draw_neon_rect, draw_cursor, draw_scanlines, draw_star_bg,
    draw_hand_icon, draw_trophy_icon, draw_star, draw_target_icon,
    draw_shadow,
    format_time, ConfettiSystem, GestureButton,
    NEON_GREEN, NEON_PINK, NEON_GOLD, NEON_CYAN
)
import utils.user_manager as um
import mediapipe as mp


# ── HUD state badge colors ────────────────────────────────────────────────────
HUD_STATES = {
    "NO_HAND":    {"label": "NO HAND",       "sub": "SHOW YOUR HAND",  "color": (40, 40, 200),  "hand": None},
    "DETECTED":   {"label": "HAND DETECTED", "sub": "READY",           "color": NEON_GREEN,     "hand": "open"},
    "PINCH":      {"label": "PINCH ACTIVE",  "sub": "CONTROL MODE",    "color": NEON_GREEN,     "hand": "pinch"},
    "MOVING":     {"label": "MOVING",        "sub": "KEEP GOING",      "color": (255, 255, 255),"hand": "open"},
    "GOAL":       {"label": "GOAL REACHED",  "sub": "YOU DID IT!",     "color": NEON_CYAN,      "hand": "open"},
}


class GameScreen:
    def __init__(self, hand_tracker, username):
        self.hand_tracker = hand_tracker
        self.username     = username
        self._confetti    = ConfettiSystem(180)
        self._win_time    = None
        self._hud_state   = "NO_HAND"
        self._is_moving   = False
        self.has_camera   = True
        self.show_camera  = True
        self.camera_opacity = config.DEFAULT_CAMERA_OPACITY
        self.fullscreen_state = False

        # Camera / System Controls
        W = config.CAMERA_WIDTH
        cx_btn_w, cx_btn_h = 136, 40
        btn_x = W - 146
        self._cam_toggle_btn = GestureButton("CAM ON/OFF", (btn_x, 140, cx_btn_w, cx_btn_h), border_color=(50, 150, 220))
        self._fs_toggle_btn  = GestureButton("FULLSCREEN", (btn_x, 190, cx_btn_w, cx_btn_h), border_color=(180, 80, 130))
        self._opacity_up_btn = GestureButton("OPACITY +", (btn_x, 240, cx_btn_w, cx_btn_h), border_color=(120, 180, 40))
        self._opacity_dn_btn = GestureButton("OPACITY -", (btn_x, 290, cx_btn_w, cx_btn_h), border_color=(120, 180, 40))

        # Win screen buttons
        btn_w, btn_h = 240, 54
        W_cx = config.CAMERA_WIDTH // 2
        b1_x = W_cx - btn_w - 16 + 50
        b2_x = W_cx + 16 + 50
        by = (config.CAMERA_HEIGHT // 2) - 180 - 20 # from _draw_win_screen py
        ph = 360
        btn_y = by + ph - 68
        
        self.play_again_btn = GestureButton("  PLAY AGAIN",
                                         (b1_x, btn_y, btn_w, btn_h),
                                         border_color=NEON_GREEN,
                                         icon="@ ")
                                         
        self.main_menu_btn = GestureButton("  MAIN MENU",
                                        (b2_x, btn_y, btn_w, btn_h),
                                        border_color=NEON_PINK,
                                        icon="~ ")

        self.reset_game()

    # ── Reset ─────────────────────────────────────────────────────────────────

    def reset_game(self):
        self.maze        = MazeGenerator(config.MAZE_ROWS, config.MAZE_COLS,
                                         config.MAZE_CELL_SIZE,
                                         config.MAZE_OFFSET_X, config.MAZE_OFFSET_Y)
        self.score       = 0
        self.start_time  = None
        self.end_time    = None
        self.game_active = False
        self.game_won    = False

        self.player_cell = self.maze.start_cell
        self.path_cells  = [self.maze.start_cell]

        self._last_move_t = 0.0
        self._move_cd     = config.MOVE_COOLDOWN

        self._msg       = ""
        self._msg_color = (255, 255, 255)
        self._msg_time  = 0.0

        self._prev_pos  = None
        self._sf        = config.SMOOTHING_FACTOR
        self._hud_state = "NO_HAND"
        self._is_moving = False

        if self._confetti:
            self._confetti.reset()
        self._win_time = None

    # ── Main update ───────────────────────────────────────────────────────────

    def update(self, frame, key, hand_results):
        if key == ord('r') or key == ord('R'):
            self.reset_game()
            return "GAME"

        # Webcam settings keys
        if key == ord('c') or key == ord('C'):
            self.show_camera = not self.show_camera
        elif key == ord('['):
            self.camera_opacity = min(1.0, self.camera_opacity + 0.05) # less camera
        elif key == ord(']'):
            self.camera_opacity = max(0.0, self.camera_opacity - 0.05) # more camera

        # Keyboard movement fallback
        move_dir = None
        if key in [ord('w'), ord('W'), 82, 63232]: # Up
            move_dir = (-1, 0)
        elif key in [ord('s'), ord('S'), 84, 63233]: # Down
            move_dir = (1, 0)
        elif key in [ord('a'), ord('A'), 81, 63234]: # Left
            move_dir = (0, -1)
        elif key in [ord('d'), ord('D'), 83, 63235]: # Right
            move_dir = (0, 1)

        if move_dir and not self.game_won:
            pr, pc = self.player_cell
            tr, tc = pr + move_dir[0], pc + move_dir[1]
            if 0 <= tr < self.maze.rows and 0 <= tc < self.maze.cols:
                if not self.maze.is_wall_between(pr, pc, tr, tc):
                    self._do_move((tr, tc), time.time())

        # Win screen
        if self.game_won:
            self._draw_win_screen(frame, hand_results)
            cursor_pos, pinch_active = self._get_cursor(hand_results, frame.shape[1], frame.shape[0])
            if cursor_pos:
                play_again_triggered, _ = self.play_again_btn.update(cursor_pos, pinch_active)
                if play_again_triggered:
                    self.reset_game()
                    return "GAME"
                main_menu_triggered, _ = self.main_menu_btn.update(cursor_pos, pinch_active)
                if main_menu_triggered:
                    return "MENU"
            if key == 32:
                self.reset_game()
                return "GAME"
            return "GAME"

        # ── Background ──
        if self.has_camera and self.show_camera:
            # frame already has camera pixels. Wash with BGR light background color.
            bg = np.full_like(frame, (248, 249, 250))
            cv2.addWeighted(bg, self.camera_opacity, frame, 1.0 - self.camera_opacity, 0, frame)
        else:
            draw_star_bg(frame)

        # ── Draw maze ──
        self.maze.draw(frame, config.COLOR_WALL, config.COLOR_START, config.COLOR_END,
                       player_cell=self.player_cell,
                       visited_cells=self.path_cells[:-1])

        # ── Hand info ──
        cursor_pos, pinch_active = self._get_cursor(hand_results, frame.shape[1], frame.shape[0])

        # Draw the hand skeleton if camera is visible
        if self.has_camera and self.show_camera and hand_results:
            self.hand_tracker.draw_landmarks(frame, hand_results)

        # ── Determine HUD state ──
        if not cursor_pos:
            self._hud_state = "NO_HAND"
            self._is_moving = False
        elif self.player_cell == self.maze.end_cell:
            self._hud_state = "GOAL"
        elif pinch_active and self._is_moving:
            self._hud_state = "MOVING"
        elif pinch_active:
            self._hud_state = "PINCH"
        else:
            self._hud_state = "DETECTED"

        # ── HUD ──
        self._draw_hud(frame, pinch_active, cursor_pos)

        # ── Options Panel on the Right ──
        W = config.CAMERA_WIDTH
        draw_panel(frame, W - 156, 100, 148, 280, border_color=config.COLOR_UI_BORDER, label="OPTIONS", corner_label_color=(120, 110, 100))

        self._cam_toggle_btn.draw(frame, cursor_pos, pinch_active)
        self._fs_toggle_btn.draw(frame, cursor_pos, pinch_active)
        self._opacity_up_btn.draw(frame, cursor_pos, pinch_active)
        self._opacity_dn_btn.draw(frame, cursor_pos, pinch_active)

        # Draw details status
        draw_text(frame, f"Opacity: {int((1.0 - self.camera_opacity) * 100)}%", (W - 142, 350), font_scale=0.45, color=config.COLOR_TEXT)
        draw_text(frame, "CAM: " + ("ON" if self.show_camera else "OFF"), (W - 142, 368), font_scale=0.45, color=config.COLOR_TEXT)

        # Dwell triggers
        cam_triggered, _ = self._cam_toggle_btn.update(cursor_pos, pinch_active)
        if cam_triggered:
            self.show_camera = not self.show_camera
            time.sleep(0.08)

        fs_triggered, _ = self._fs_toggle_btn.update(cursor_pos, pinch_active)
        if fs_triggered:
            self.fullscreen_state = not getattr(self, 'fullscreen_state', False)
            if self.fullscreen_state:
                cv2.setWindowProperty("Hand Maze Game", cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
            else:
                cv2.setWindowProperty("Hand Maze Game", cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_NORMAL)
            time.sleep(0.08)

        op_up_triggered, _ = self._opacity_up_btn.update(cursor_pos, pinch_active)
        if op_up_triggered:
            self.camera_opacity = max(0.0, self.camera_opacity - 0.1) # more webcam
            time.sleep(0.08)

        op_dn_triggered, _ = self._opacity_dn_btn.update(cursor_pos, pinch_active)
        if op_dn_triggered:
            self.camera_opacity = min(1.0, self.camera_opacity + 0.1) # less webcam
            time.sleep(0.08)

        # ── Camera warning banner ──
        if not self.has_camera:
            alert_x, alert_y, alert_w, alert_h = 302, 10, 676, 36
            draw_panel(frame, alert_x, alert_y, alert_w, alert_h, border_color=(80, 60, 230), bg_alpha=0.9)
            draw_text_centered(frame, "WEBCAM OFFLINE - KEYBOARD MODE (WASD / Arrows) ACTIVE", alert_x + alert_w // 2, alert_y + 24, font_scale=0.48, color=(80, 60, 230))

        # ── Cursor ──
        draw_cursor(frame, cursor_pos, pinch_active)

        # ── Visual alignment line helper ──
        if pinch_active and cursor_pos:
            target_cell = self.maze.pixel_to_cell(cursor_pos[0], cursor_pos[1])
            if target_cell != self.player_cell:
                play_cx, play_cy = self.maze.cell_center(self.player_cell[0], self.player_cell[1])
                cv2.line(frame, cursor_pos, (play_cx, play_cy), (120, 110, 100), 1, cv2.LINE_AA)
                draw_text(frame, "Drag to Player", (cursor_pos[0] + 12, cursor_pos[1] - 8), font_scale=0.4, color=(120, 110, 100))

        # ── Movement ──
        now = time.time()
        if pinch_active and cursor_pos and now - self._last_move_t > self._move_cd:
            target_cell = self.maze.pixel_to_cell(cursor_pos[0], cursor_pos[1])
            if target_cell and target_cell != self.player_cell:
                pr, pc = self.player_cell
                tr, tc = target_cell
                if abs(tr - pr) + abs(tc - pc) == 1:
                    if not self.maze.is_wall_between(pr, pc, tr, tc):
                        self._do_move(target_cell, now)
                        self._is_moving = True

        # ── Check win ──
        if self.player_cell == self.maze.end_cell and self.game_active:
            self.game_won    = True
            self.end_time    = time.time()
            self.game_active = False
            self._win_time   = time.time()
            self._confetti.reset()
            um.update_user_stats(self.username, self.score, self.end_time - self.start_time)

        # ── Score flash ──
        if self._msg and now - self._msg_time < 0.8:
            tw, _ = cv2.getTextSize(self._msg, cv2.FONT_HERSHEY_DUPLEX, 1.4, 3)[0]
            pulse  = 1.4 + abs(math.sin((now - self._msg_time) * 10)) * 0.2
            draw_text(frame, self._msg,
                      (config.CAMERA_WIDTH // 2 - tw // 2, 130),
                      font_scale=pulse, color=self._msg_color, thickness=3,
                      font=cv2.FONT_HERSHEY_DUPLEX)

        draw_scanlines(frame)
        return "GAME"

    # ── Move logic ────────────────────────────────────────────────────────────

    def _do_move(self, target_cell, now):
        self._last_move_t = now
        if len(self.path_cells) >= 2 and target_cell == self.path_cells[-2]:
            self.path_cells.pop()
            self.player_cell = target_cell
            self.score = max(0, self.score - 1)
            self._show_msg("-1", (60, 60, 255))
        else:
            self.player_cell = target_cell
            if target_cell not in self.path_cells:
                self.path_cells.append(target_cell)
            else:
                idx = self.path_cells.index(target_cell)
                self.path_cells = self.path_cells[:idx + 1]
            self.score += 1
            self._show_msg("+1", NEON_GREEN)

        if not self.game_active and self.player_cell != self.maze.start_cell:
            self.game_active = True
            self.start_time  = time.time()

    def _show_msg(self, text, color):
        self._msg       = text
        self._msg_color = color
        self._msg_time  = time.time()

    # ── Cursor ────────────────────────────────────────────────────────────────

    def _get_cursor(self, hand_results, fw, fh):
        if not hand_results or not hand_results.multi_hand_landmarks:
            self._prev_pos = None
            return None, False
        if len(hand_results.multi_hand_landmarks) > 1:
            self._prev_pos = None
            return None, False

        lms   = hand_results.multi_hand_landmarks[0]
        mp_h  = mp.solutions.hands
        thumb = lms.landmark[mp_h.HandLandmark.THUMB_TIP]
        index = lms.landmark[mp_h.HandLandmark.INDEX_FINGER_TIP]

        tx = int(thumb.x * fw); ty = int(thumb.y * fh)
        ix = int(index.x * fw); iy = int(index.y * fh)

        dist = np.hypot(tx - ix, ty - iy) / fw
        pinch_active = dist < config.PINCH_THRESHOLD
        raw = ((tx + ix) // 2, (ty + iy) // 2)

        if self._prev_pos is None:
            self._prev_pos = raw
            return raw, pinch_active

        sx = int(self._prev_pos[0] * (1 - self._sf) + raw[0] * self._sf)
        sy = int(self._prev_pos[1] * (1 - self._sf) + raw[1] * self._sf)
        self._prev_pos = (sx, sy)
        return (sx, sy), pinch_active

    # ── HUD ───────────────────────────────────────────────────────────────────

    def _draw_hud(self, frame, pinch_active, cursor_pos):
        W = config.CAMERA_WIDTH
        H = config.CAMERA_HEIGHT

        # ── Top HUD bar ──
        draw_shadow(frame, 0, 0, W, 90, offset=4, opacity=0.04)
        cv2.rectangle(frame, (0, 0), (W, 90), (255, 255, 255), -1)
        cv2.line(frame, (0, 90), (W, 90), config.COLOR_UI_BORDER, 1)

        # Player avatar icon
        cv2.circle(frame, (40, 45), 22, (240, 235, 230), -1)
        cv2.circle(frame, (40, 45), 22, config.COLOR_UI_BORDER, 1, cv2.LINE_AA)
        cv2.circle(frame, (40, 32), 9, (180, 140, 120), -1)
        cv2.ellipse(frame, (40, 52), (14, 8), 0, 0, 180, (180, 140, 120), -1)

        # Player label + name
        draw_text(frame, "PLAYER", (72, 28), font_scale=0.52, color=(140, 130, 120))
        draw_text(frame, self.username.upper(), (72, 60),
                  font_scale=0.85, color=config.COLOR_TEXT, thickness=2)

        # Divider
        cv2.line(frame, (230, 12), (230, 78), config.COLOR_UI_BORDER, 1)

        # Score with star icon
        draw_star(frame, 258, 30, 10, 5, NEON_GOLD, -1)
        sc_col = NEON_GREEN if self.score > 0 else (120, 110, 100)
        draw_text(frame, "SCORE", (274, 28), font_scale=0.52, color=(140, 130, 120))
        draw_text(frame, str(self.score), (258, 64),
                  font_scale=1.1, color=sc_col, thickness=2)

        # Divider
        cv2.line(frame, (390, 12), (390, 78), config.COLOR_UI_BORDER, 1)

        # Timer with clock icon
        t_str = "00:00"
        if self.game_active and self.start_time:
            t_str = format_time(time.time() - self.start_time)
        elif self.game_won and self.start_time and self.end_time:
            t_str = format_time(self.end_time - self.start_time)
        cv2.circle(frame, (416, 28), 10, (140, 130, 120), 1, cv2.LINE_AA)
        cv2.line(frame, (416, 28), (416, 20), (140, 130, 120), 1)
        cv2.line(frame, (416, 28), (421, 31), (140, 130, 120), 1)
        draw_text(frame, "TIME", (432, 28), font_scale=0.52, color=(140, 130, 120))
        draw_text(frame, t_str, (412, 64),
                  font_scale=0.95, color=(50, 150, 220), thickness=2)

        # Divider
        cv2.line(frame, (560, 12), (560, 78), config.COLOR_UI_BORDER, 1)

        # Best time
        user_data = um.get_or_create_user(self.username)
        bt = user_data.get('best_time', None)
        bt_str = f"{bt:.1f}s" if bt else "--"
        draw_trophy_icon(frame, 583, 26, size=14, color=NEON_GOLD)
        draw_text(frame, "BEST TIME", (600, 28), font_scale=0.52, color=(140, 130, 120))
        draw_text(frame, bt_str, (575, 64),
                  font_scale=0.88, color=NEON_GOLD, thickness=2)

        # Divider
        cv2.line(frame, (730, 12), (730, 78), config.COLOR_UI_BORDER, 1)

        # ── STATUS badge ──
        state = HUD_STATES.get(self._hud_state, HUD_STATES["NO_HAND"])
        sc = state["color"]
        s_label = state["label"]
        s_sub   = state["sub"]

        badge_x = 748
        draw_text(frame, "STATUS", (badge_x, 28), font_scale=0.52, color=(140, 130, 120))

        # Status pill
        pl_x1, pl_y1 = badge_x - 4, 38
        pl_x2, pl_y2 = badge_x + 190, 72
        cv2.rectangle(frame, (pl_x1, pl_y1), (pl_x2, pl_y2), (250, 248, 245), -1)
        cv2.rectangle(frame, (pl_x1, pl_y1), (pl_x2, pl_y2), config.COLOR_UI_BORDER, 1, cv2.LINE_AA)
        # Dot indicator
        cv2.circle(frame, (badge_x + 8, 55), 5, sc, -1, cv2.LINE_AA)
        draw_text(frame, s_label, (badge_x + 20, 60),
                  font_scale=0.62, color=sc, thickness=2)

        # Controls (right side)
        cv2.line(frame, (W - 290, 12), (W - 290, 78), config.COLOR_UI_BORDER, 1)
        draw_text(frame, "[R] RESTART", (W - 278, 36),
                  font_scale=0.58, color=(140, 130, 120))
        draw_text(frame, "ESC/Thumb Down MENU",  (W - 278, 62),
                  font_scale=0.58, color=(140, 130, 120))

        # ── Left side hand status panel ──
        hp_x, hp_y, hp_w, hp_h = 8, 100, 120, 200
        draw_panel(frame, hp_x, hp_y, hp_w, hp_h,
                   border_color=config.COLOR_UI_BORDER, label="HAND STATUS",
                   corner_label_color=(120, 110, 100))

        hs_cx = hp_x + hp_w // 2
        draw_hand_icon(frame, hs_cx, hp_y + 80, size=52,
                       color=sc,
                       style="pinch" if pinch_active else ("open" if cursor_pos else "open"))
        draw_text_centered(frame, s_sub, hs_cx, hp_y + 150,
                           font_scale=0.42, color=sc)

        # ── Pinch status badge ──
        pinch_col = NEON_GREEN if pinch_active else (140, 130, 120)
        px1, py1  = hp_x + 8, hp_y + hp_h + 10
        px2, py2  = hp_x + hp_w - 8, hp_y + hp_h + 52
        cv2.rectangle(frame, (px1, py1), (px2, py2), (250, 248, 245), -1)
        cv2.rectangle(frame, (px1, py1), (px2, py2), config.COLOR_UI_BORDER, 1, cv2.LINE_AA)
        draw_hand_icon(frame, hs_cx, (py1 + py2) // 2,
                       size=20, color=pinch_col, style="pinch")
        pinch_lbl = "ACTIVE" if pinch_active else "INACTIVE"
        draw_text_centered(frame, pinch_lbl,
                           hs_cx, py2 + 18,
                           font_scale=0.42, color=pinch_col)

        # ── Bottom action bar ──
        bar_h = 36
        draw_shadow(frame, 0, H - bar_h, W, bar_h, offset=-4, opacity=0.04)
        cv2.rectangle(frame, (0, H - bar_h), (W, H), (255, 255, 255), -1)
        cv2.line(frame, (0, H - bar_h), (W, H - bar_h), config.COLOR_UI_BORDER, 1)

        segments = [
            ("MOVE FORWARD", "+1", NEON_GREEN),
            ("MOVE BACKWARD", "-1", (80, 80, 240)),
            ("REACH GOAL",   "WIN", NEON_CYAN),
        ]
        seg_x = 160
        for label, val, col in segments:
            draw_text(frame, label, (seg_x, H - 22),
                      font_scale=0.5, color=(140, 130, 120))
            draw_text(frame, val,   (seg_x, H - 7),
                      font_scale=0.62, color=col, thickness=2)
            seg_x += 220
            cv2.line(frame, (seg_x - 80, H - bar_h + 4), (seg_x - 80, H - 4),
                     config.COLOR_UI_BORDER, 1)

        # R / ESC indicators
        r_x = W - 260
        cv2.rectangle(frame, (r_x, H - 28), (r_x + 24, H - 8),
                      (250, 245, 240), -1)
        cv2.rectangle(frame, (r_x, H - 28), (r_x + 24, H - 8),
                      config.COLOR_UI_BORDER, 1, cv2.LINE_AA)
        draw_text(frame, "R", (r_x + 7, H - 13),
                  font_scale=0.52, color=config.COLOR_TEXT)
        draw_text(frame, "RESTART", (r_x + 30, H - 13),
                  font_scale=0.52, color=(120, 110, 100))

        esc_x = W - 140
        cv2.rectangle(frame, (esc_x, H - 28), (esc_x + 38, H - 8),
                      (250, 245, 240), -1)
        cv2.rectangle(frame, (esc_x, H - 28), (esc_x + 38, H - 8),
                      config.COLOR_UI_BORDER, 1, cv2.LINE_AA)
        draw_text(frame, "TD", (esc_x + 4, H - 13),
                  font_scale=0.52, color=config.COLOR_TEXT)
        draw_text(frame, "MENU", (esc_x + 46, H - 13),
                  font_scale=0.52, color=(120, 110, 100))

        # ── "Start" hint when not playing ──
        if not self.game_active and not self.game_won:
            hint  = "PINCH & MOVE TO START"
            t_now = time.time()
            alpha = int(180 + abs(math.sin(t_now * 3)) * 75)
            col   = (0, alpha, alpha)
            (hw, _), _ = cv2.getTextSize(hint, cv2.FONT_HERSHEY_SIMPLEX, 0.9, 2)
            draw_text(frame, hint,
                      (W // 2 - hw // 2, 118),
                      font_scale=0.9, color=col, thickness=2)

    # ── WIN SCREEN ────────────────────────────────────────────────────────────

    def _draw_win_screen(self, frame, hand_results=None):
        frame[:] = (248, 249, 250)
        draw_star_bg(frame)

        self._confetti.update_and_draw(frame)

        W, H = config.CAMERA_WIDTH, config.CAMERA_HEIGHT
        cx, cy = W // 2, H // 2

        t = time.time() - (self._win_time or time.time())

        # ── Full win panel ──
        pw, ph = 780, 360
        bx, by = cx - pw // 2, cy - ph // 2 - 20
        draw_panel(frame, bx, by, pw, ph,
                   border_color=config.COLOR_UI_BORDER, label="YOU WIN SCREEN",
                   corner_label_color=(120, 110, 100))

        # ── Trophy icon (left) ──
        trophy_cx = bx + 110
        trophy_cy = by + ph // 2 + 10
        
        # Soft glow
        for r in range(70, 40, -10):
            cv2.circle(frame, (trophy_cx, trophy_cy), r,
                       (220, 240, 255), 1, cv2.LINE_AA)
        draw_trophy_icon(frame, trophy_cx, trophy_cy, size=55, color=NEON_GOLD)

        # ── "YOU WIN!" title ──
        pulse     = abs(math.sin(t * 3)) * 0.3
        t_scale   = 2.5 + pulse
        title     = "YOU WIN!"
        (tw, _), _ = cv2.getTextSize(title, cv2.FONT_HERSHEY_DUPLEX, t_scale, 3)
        tx = cx - tw // 2 + 50
        ty = by + 72
        
        # Shadow
        cv2.putText(frame, title, (tx + 2, ty + 2),
                    cv2.FONT_HERSHEY_DUPLEX, t_scale, (225, 220, 215), 3, cv2.LINE_AA)
        
        # Rainbow cycle
        hue       = int((t * 60) % 180)
        hsv_arr   = np.uint8([[[hue, 220, 240]]])
        bgr_arr   = cv2.cvtColor(hsv_arr, cv2.COLOR_HSV2BGR)[0][0]
        t_col     = (int(bgr_arr[0]), int(bgr_arr[1]), int(bgr_arr[2]))
        cv2.putText(frame, title, (tx, ty),
                    cv2.FONT_HERSHEY_DUPLEX, t_scale, t_col, 3, cv2.LINE_AA)

        # Separator line
        sep_x = bx + 210
        cv2.line(frame, (sep_x, by + 88), (bx + pw - 30, by + 88),
                 config.COLOR_UI_BORDER, 1)

        # ── Stats ──
        user_data = um.get_or_create_user(self.username)
        sc_str    = str(self.score)
        t_str     = format_time(self.end_time - self.start_time) if self.start_time else "--:--"
        bs        = user_data.get('best_score', 0)
        bt        = user_data.get('best_time', None)
        bt_str    = f"{bt:.1f}s" if bt else "N/A"
        is_new_bs = (self.score >= bs)
        is_new_bt = (bt and self.start_time and
                     (self.end_time - self.start_time) <= bt)

        lx = sep_x + 10
        ry = by + 118

        rows = [
            ("PLAYER",     self.username.upper(),     (50, 150, 220),  False),
            ("SCORE",      sc_str,                    NEON_GREEN,     False),
            ("TIME",       t_str,                     (220, 160, 50), False),
            ("BEST SCORE", str(bs),                   (120, 110, 100), is_new_bs),
            ("BEST TIME",  bt_str,                    (120, 110, 100), is_new_bt),
        ]

        for label, val, val_col, is_new in rows:
            draw_text(frame, label, (lx, ry),
                      font_scale=0.65, color=(140, 130, 120))
            draw_text(frame, val, (lx + 190, ry),
                      font_scale=0.78, color=val_col, thickness=2)
            if is_new:
                draw_text(frame, "NEW BEST!",
                          (lx + 330, ry),
                          font_scale=0.55, color=NEON_GOLD, thickness=1)
            ry += 42

        # ── Buttons ──
        cursor_pos, pinch_active = self._get_cursor(hand_results, W, H)
        self.play_again_btn.draw(frame, cursor_pos, pinch_active)
        self.main_menu_btn.draw(frame, cursor_pos, pinch_active)
        draw_cursor(frame, cursor_pos, pinch_active)

        # Instructions
        draw_text_centered(frame,
                           "[ SPACE ] Play Again          [ Thumb Down ] Main Menu",
                           W // 2 + 50, by + ph + 28,
                           font_scale=0.68, color=(120, 110, 100))

        draw_scanlines(frame)
