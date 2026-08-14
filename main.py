# main.py
"""
Hand Maze Game — Main entry point.
"""

import traceback
import time
import numpy as np
import cv2
import config
from core.hand_tracker import HandTracker
from screens.start_screen import StartScreen
from screens.login_screen import LoginScreen
from screens.menu_screen import MenuScreen, HowToPlayScreen, HighScoreScreen
from screens.game_screen import GameScreen
from utils.helpers import draw_text_centered


def main():
    cv2.namedWindow("Hand Maze Game", cv2.WINDOW_NORMAL)
    cv2.resizeWindow("Hand Maze Game", config.CAMERA_WIDTH, config.CAMERA_HEIGHT)

    has_camera = True
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("[WARN] Cannot open webcam. Running in offline/no-webcam mode.")
        has_camera = False
    else:
        cap.set(cv2.CAP_PROP_FRAME_WIDTH,  config.CAMERA_WIDTH)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, config.CAMERA_HEIGHT)

    hand_tracker = HandTracker(config.PINCH_THRESHOLD, config.SMOOTHING_FACTOR)

    current_state    = "START"
    username         = "Player"
    fullscreen_state = False

    start_screen = StartScreen()
    login_screen = LoginScreen()
    how_to_play  = HowToPlayScreen()
    high_score   = HighScoreScreen()
    game_screen  = None

    # Pre-create MenuScreen with default username — avoids first-time init crash
    try:
        menu_screen = MenuScreen(username)
    except Exception:
        print(f"[MenuScreen pre-init error]\n{traceback.format_exc()}")
        menu_screen = None

    # States that need hand tracking
    HAND_STATES = {"START", "LOGIN", "GAME", "MENU", "HOW_TO_PLAY", "HIGH_SCORES"}

    # Cooldown for thumb down to prevent multiple triggers
    thumb_down_cooldown  = 0
    thumb_down_start     = None   # timestamp when thumb-down gesture began
    THUMB_DOWN_HOLD_SECS = 2.0   # seconds user must hold thumb-down before back nav
    
    while True:
        frame = None
        if has_camera and cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                print("[WARN] Frame read failed, retrying...")
                time.sleep(0.01)
                continue
            frame = cv2.flip(frame, 1)   # Mirror
            # Scale frame to match game config if camera resolution differs
            if frame.shape[1] != config.CAMERA_WIDTH or frame.shape[0] != config.CAMERA_HEIGHT:
                frame = cv2.resize(frame, (config.CAMERA_WIDTH, config.CAMERA_HEIGHT))
        else:
            # Simulated blank canvas frame for offline play
            frame = np.full((config.CAMERA_HEIGHT, config.CAMERA_WIDTH, 3), config.COLOR_BG, dtype=np.uint8)

        # Pass camera status to screen if it supports it
        if game_screen is not None:
            game_screen.has_camera = has_camera

        # --- Hand tracking ---
        hand_results = None
        thumb_down_global = False
        if has_camera and current_state in HAND_STATES:
            try:
                hand_results = hand_tracker.process_frame(frame)
                if hand_results:
                    _, _, _, thumb_down_global, _ = hand_tracker.get_hand_info(
                        hand_results, config.CAMERA_WIDTH, config.CAMERA_HEIGHT)
            except Exception as e:
                print(f"[hand_tracker] {e}")

        if thumb_down_cooldown > 0:
            thumb_down_cooldown -= 1
            thumb_down_global = False

        # --- Key input ---
        raw_key = cv2.waitKey(1)
        # Normalise: cv2.waitKey returns -1 on no-press (& 0xFF → 255)
        key = raw_key & 0xFF if raw_key != -1 else -1
        if key == 255:
            key = -1

        # Check for fullscreen toggle (f / F)
        if key == ord('f') or key == ord('F'):
            fullscreen_state = not fullscreen_state
            if fullscreen_state:
                cv2.setWindowProperty("Hand Maze Game", cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
            else:
                cv2.setWindowProperty("Hand Maze Game", cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_NORMAL)

        next_state = current_state

        try:
            # Always render the current screen (pass key=-1 while thumb held so
            # buttons/gestures inside the screen don't fire during countdown)
            _k = -1 if thumb_down_global else key

            if current_state == "START":
                _ret = start_screen.update(frame, _k, hand_results)
                if not thumb_down_global:
                    next_state = _ret

            elif current_state == "LOGIN":
                _ret = login_screen.update(frame, _k, hand_results)
                if not thumb_down_global:
                    next_state = _ret
                    if next_state == "MENU":
                        username = login_screen.username.strip() or "Player"
                        print(f"[login] username='{username}' -> MENU")
                        if menu_screen is None:
                            menu_screen = MenuScreen(username)
                        else:
                            try:
                                menu_screen.set_username(username)
                            except Exception:
                                menu_screen = MenuScreen(username)

            elif current_state == "MENU":
                if menu_screen is None:
                    menu_screen = MenuScreen(username)
                _ret = menu_screen.update(frame, _k, hand_results)
                if not thumb_down_global:
                    next_state = _ret
                    if next_state == "GAME":
                        try:
                            game_screen = GameScreen(hand_tracker, username)
                            game_screen.has_camera = has_camera
                        except Exception:
                            print(f"[GameScreen init error]\n{traceback.format_exc()}")
                            next_state = "MENU"

            elif current_state == "HOW_TO_PLAY":
                _ret = how_to_play.update(frame, _k, hand_results)
                if not thumb_down_global:
                    next_state = _ret

            elif current_state == "HIGH_SCORES":
                _ret = high_score.update(frame, _k, hand_results)
                if not thumb_down_global:
                    next_state = _ret

            elif current_state == "GAME":
                _ret = game_screen.update(frame, _k, hand_results)
                if not thumb_down_global:
                    next_state = _ret
                    if next_state == "MENU":
                        key = -1

            elif current_state == "QUIT":
                break

        except Exception:
            print(f"[FATAL in state {current_state}]\n{traceback.format_exc()}")
            next_state = current_state

        # -- Thumb-down countdown overlay (drawn ON TOP of the screen) ----------
        if thumb_down_global:
            if thumb_down_start is None:
                thumb_down_start = time.time()
            held_secs = time.time() - thumb_down_start
            progress  = min(held_secs / THUMB_DOWN_HOLD_SECS, 1.0)

            H_f, W_f  = frame.shape[:2]
            arc_cx    = W_f // 2
            arc_cy    = H_f - 60

            # Dark semi-transparent pill background
            overlay = frame.copy()
            cv2.rectangle(overlay,
                          (arc_cx - 140, arc_cy - 58),
                          (arc_cx + 140, arc_cy + 44),
                          (15, 15, 15), -1)
            cv2.addWeighted(overlay, 0.55, frame, 0.45, 0, frame)

            # Grey track ring
            cv2.ellipse(frame, (arc_cx, arc_cy), (28, 28), -90,
                        0, 360, (55, 55, 55), 4, cv2.LINE_AA)
            # Green progress arc
            if progress > 0:
                cv2.ellipse(frame, (arc_cx, arc_cy), (28, 28), -90,
                            0, int(360 * progress), (80, 220, 80), 4, cv2.LINE_AA)

            draw_text_centered(frame, "Hold Thumb Down...",
                               arc_cx, arc_cy - 42,
                               font_scale=0.60, color=(80, 220, 80))

            if held_secs >= THUMB_DOWN_HOLD_SECS:
                thumb_down_cooldown = 30
                thumb_down_start    = None
                if current_state == "START":
                    next_state = "QUIT"
                elif current_state == "LOGIN":
                    next_state = "START"
                elif current_state == "MENU":
                    next_state = "LOGIN"
                elif current_state in ("HOW_TO_PLAY", "HIGH_SCORES", "GAME"):
                    next_state = "MENU"
                    if current_state == "GAME" and game_screen:
                        game_screen.game_active = False
        else:
            thumb_down_start = None

        # Reset login fields when entering login fresh
        if next_state == "LOGIN" and current_state != "LOGIN":
            login_screen.reset()

        current_state = next_state
        cv2.imshow("Hand Maze Game", frame)


    if cap.isOpened():
        cap.release()
    cv2.destroyAllWindows()
    print("[game] Exited cleanly.")


if __name__ == "__main__":
    main()
