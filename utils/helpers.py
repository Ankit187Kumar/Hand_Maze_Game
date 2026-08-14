# utils/helpers.py
import cv2
import numpy as np
import math, time, random

# ── Colour palette (BGR) ──────────────────────────────────────────────────────
NEON_GREEN   = (120, 180, 40)    # Soft slate green / teal
NEON_PINK    = (180, 80, 130)    # Rose pink
NEON_CYAN    = (220, 160, 50)    # Soft sky blue
NEON_GOLD    = (50, 150, 220)    # Soft gold/orange
NEON_RED     = (80, 60, 230)     # Rose red
DIM_GREEN    = (90, 140, 30)
DIM_PINK     = (130, 60, 100)
PANEL_BG     = (255, 255, 255)   # Pure white
PANEL_BORDER = (225, 220, 215)   # Soft grey-blue border


# ── Text drawing ──────────────────────────────────────────────────────────────

def draw_text(img, text, pos, font_scale=1, thickness=2,
              color=(45, 40, 35), outline_color=None,
              font=cv2.FONT_HERSHEY_SIMPLEX):
    """Draw clean text with optional outline."""
    if outline_color is not None:
        cv2.putText(img, text, pos, font, font_scale, outline_color, thickness + 2, cv2.LINE_AA)
    cv2.putText(img, text, pos, font, font_scale, color, thickness, cv2.LINE_AA)


def draw_text_centered(img, text, cx, y, font_scale=1, thickness=2,
                        color=(45, 40, 35), font=cv2.FONT_HERSHEY_SIMPLEX):
    """Draw horizontally-centred text."""
    (tw, _), _ = cv2.getTextSize(text, font, font_scale, thickness)
    draw_text(img, text, (cx - tw // 2, y), font_scale, thickness, color, font=font)


def format_time(seconds):
    mins = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{mins:02d}:{secs:02d}"


# ── Modern UI drawing ─────────────────────────────────────────────────────────

def draw_shadow(img, x, y, w, h, offset=8, opacity=0.06):
    """Draw a soft drop shadow for cards and buttons using alpha blending."""
    sh_x1, sh_y1 = x + offset, y + offset
    sh_x2, sh_y2 = x + w + offset, y + h + offset
    H, W = img.shape[:2]
    sh_x1 = max(0, min(sh_x1, W))
    sh_y1 = max(0, min(sh_y1, H))
    sh_x2 = max(0, min(sh_x2, W))
    sh_y2 = max(0, min(sh_y2, H))
    if sh_x2 > sh_x1 and sh_y2 > sh_y1:
        sub = img[sh_y1:sh_y2, sh_x1:sh_x2]
        overlay = np.zeros_like(sub)  # black
        cv2.addWeighted(overlay, opacity, sub, 1.0 - opacity, 0, sub)


def draw_neon_rect(img, pt1, pt2, color, thickness=2, glow_layers=3):
    """Draw a clean rectangle, with a minimal soft border glow."""
    cv2.rectangle(img, pt1, pt2, color, thickness, cv2.LINE_AA)


def draw_panel(img, x, y, w, h, border_color=(225, 220, 215),
               label="", bg_alpha=0.95, corner_label_color=(120, 110, 100)):
    """Modern light panel/card with soft drop shadow and thin border."""
    draw_shadow(img, x, y, w, h, offset=8, opacity=0.06)
    
    overlay = img.copy()
    cv2.rectangle(overlay, (x, y), (x + w, y + h), (255, 255, 255), -1)
    cv2.addWeighted(overlay, bg_alpha, img, 1.0 - bg_alpha, 0, img)
    
    cv2.rectangle(img, (x, y), (x + w, y + h), border_color, 1, cv2.LINE_AA)
    if label:
        draw_text(img, label, (x + 10, y + 16), font_scale=0.38,
                  thickness=1, color=corner_label_color, outline_color=None)


def draw_neon_button(img, text, rect, border_color=(210, 130, 40),
                     text_color=(45, 40, 35), hover=False,
                     progress=0.0, icon="", subtitle="",
                     bg_color=None):
    """Modern clean button for the light theme, replaces retro-neon styling."""
    x, y, w, h = rect

    # Shadow
    draw_shadow(img, x, y, w, h, offset=4, opacity=0.05)

    # Background Color
    if bg_color is None:
        bg_color = (250, 243, 238) if hover else (255, 255, 255)
    else:
        if hover:
            bg_color = tuple(min(c + 20, 255) for c in bg_color)

    # Draw BG
    cv2.rectangle(img, (x, y), (x + w, y + h), bg_color, -1)

    # Border
    b_thick = 2 if hover else 1
    cv2.rectangle(img, (x, y), (x + w, y + h), border_color, b_thick, cv2.LINE_AA)

    # Progress bar fill from left
    if progress > 0:
        bar_w = int(w * progress)
        sub = img[y:y+h, x:x+bar_w]
        overlay = np.full_like(sub, border_color)
        cv2.addWeighted(overlay, 0.15, sub, 0.85, 0, sub)
        cv2.rectangle(img, (x, y + h - 4), (x + bar_w, y + h), border_color, -1)

    # Text rendering
    font = cv2.FONT_HERSHEY_DUPLEX
    fscale = 0.72
    clean_text = icon + text

    # Set text color
    cur_text_col = text_color
    if bg_color in [(255, 255, 255), (250, 243, 238)]:
        cur_text_col = (45, 40, 35)

    (tw, th), _ = cv2.getTextSize(clean_text, font, fscale, 1)

    if subtitle:
        ty_main = y + h // 2 - 2
        ty_sub  = y + h // 2 + 16
        draw_text(img, clean_text, (x + 20, ty_main),
                  font_scale=fscale, thickness=1, color=cur_text_col, font=font)
        draw_text(img, subtitle, (x + 20, ty_sub),
                  font_scale=0.42, thickness=1, color=(140, 130, 120))
    else:
        tx = x + (w - tw) // 2
        ty = y + (h + th) // 2
        draw_text(img, clean_text, (tx, ty),
                  font_scale=fscale, thickness=1, color=cur_text_col, font=font)


def draw_button(img, text, rect, color=(210, 130, 40),
                text_color=(45, 40, 35), hover=False, progress=0.0):
    draw_neon_button(img, text, rect, border_color=color,
                     text_color=text_color, hover=hover, progress=progress)


# ── Hand silhouette icon ──────────────────────────────────────────────────────

def draw_hand_icon(img, cx, cy, size=40, color=NEON_GREEN,
                   style="open", alpha=1.0):
    """
    Draw a simple hand icon (open palm or pinch) centred at (cx, cy).
    style: "open" | "pinch" | "fist"
    """
    s = size
    # Palm body (rounded rect approximation)
    pts_palm = np.array([
        [cx - s//2, cy + s//4],
        [cx - s//2, cy - s//4],
        [cx - s//4, cy - s//3],
        [cx,        cy - s//2],
        [cx + s//4, cy - s//3],
        [cx + s//2, cy - s//4],
        [cx + s//2, cy + s//4],
        [cx + s//3, cy + s//2],
        [cx - s//3, cy + s//2],
    ], np.int32)

    if style == "open":
        cv2.polylines(img, [pts_palm], True, color, 2, cv2.LINE_AA)
        # Fingers
        finger_tops = [
            (cx - s//3, cy - s//3),
            (cx - s//8, cy - s//2 - s//8),
            (cx + s//8, cy - s//2 - s//8),
            (cx + s//3, cy - s//3),
        ]
        for fx, fy in finger_tops:
            cv2.line(img, (fx, cy - s//4), (fx, fy), color, 2, cv2.LINE_AA)
        # Thumb
        cv2.line(img, (cx - s//2, cy - s//6),
                 (cx - s//2 - s//4, cy - s//2 + s//8), color, 2, cv2.LINE_AA)

    elif style == "pinch":
        # Draw thumb and index finger coming together
        cv2.circle(img, (cx - s//5, cy - s//6), s//6, color, 2)
        cv2.circle(img, (cx + s//5, cy - s//6), s//6, color, 2)
        cv2.line(img, (cx - s//5, cy - s//6),
                 (cx + s//5, cy - s//6), color, 2)
        # Rest of hand
        cv2.ellipse(img, (cx, cy + s//6), (s//3, s//4), 0, 0, 180, color, 2)

    elif style == "fist":
        cv2.rectangle(img, (cx - s//3, cy - s//4),
                      (cx + s//3, cy + s//3), color, 2)
        cv2.rectangle(img, (cx - s//2, cy - s//6),
                      (cx + s//2, cy + s//4), color, 2)


# ── Cursor ────────────────────────────────────────────────────────────────────

def draw_cursor(img, pos, pinch_active):
    """Draw a clean, modern, light-theme cursor."""
    if pos is None:
        return
    t = time.time()
    pulse = int(abs(math.sin(t * 3.5)) * 4)

    if pinch_active:
        cv2.circle(img, pos, 15 + pulse, (160, 200, 100), 2, cv2.LINE_AA)
        cv2.circle(img, pos, 6, (120, 180, 40), -1, cv2.LINE_AA)
    else:
        cv2.circle(img, pos, 12 + pulse, (210, 130, 40), 1, cv2.LINE_AA)
        cv2.circle(img, pos, 3, (210, 130, 40), -1, cv2.LINE_AA)


# ── Scanline overlay ──────────────────────────────────────────────────────────

def draw_scanlines(img, alpha=0.04):
    """Deprecated scanline overlay. Replaced by grid background for cleaner look."""
    pass


# ── Star background ───────────────────────────────────────────────────────────

_BUBBLES = None

def _init_bubbles(w, h, n=15):
    global _BUBBLES
    _BUBBLES = []
    for _ in range(n):
        _BUBBLES.append({
            'x': random.randint(0, w),
            'y': random.randint(0, h),
            'r': random.randint(30, 90),
            'vx': random.uniform(-0.4, 0.4),
            'vy': random.uniform(-0.4, 0.4),
            'color': random.choice([
                (245, 220, 220), # light rose
                (220, 245, 220), # light mint
                (220, 235, 245), # light sky-blue
                (245, 245, 220), # light yellow
                (235, 220, 245), # light lavender
            ]),
        })

def draw_star_bg(img):
    """Clean light-theme animated background with dot grid and floating bubbles."""
    h, w = img.shape[:2]
    img[:] = (248, 249, 250)  # off-white canvas
    
    # 1. Draw dot grid
    grid_gap = 40
    grid_color = (235, 230, 225)
    for x in range(grid_gap, w, grid_gap):
        for y in range(grid_gap, h, grid_gap):
            cv2.circle(img, (x, y), 1, grid_color, -1)
            
    # 2. Floating bubbles
    global _BUBBLES
    if _BUBBLES is None:
        _init_bubbles(w, h)
        
    overlay = img.copy()
    for b in _BUBBLES:
        b['x'] += b['vx']
        b['y'] += b['vy']
        
        # bounce
        if b['x'] - b['r'] < 0 or b['x'] + b['r'] > w:
            b['vx'] *= -1
        if b['y'] - b['r'] < 0 or b['y'] + b['r'] > h:
            b['vy'] *= -1
            
        cx, cy = int(b['x']), int(b['y'])
        cv2.circle(overlay, (cx, cy), b['r'], b['color'], -1)
        
    cv2.addWeighted(overlay, 0.22, img, 0.78, 0, img)


# ── Star / Trophy / Target icon helpers ──────────────────────────────────────

def draw_star(img, cx, cy, r_outer, r_inner, color, thickness=-1):
    pts = []
    for k in range(5):
        a1 = math.radians(k * 72 - 90)
        pts.append([cx + int(r_outer * math.cos(a1)),
                    cy + int(r_outer * math.sin(a1))])
        a2 = math.radians(k * 72 - 90 + 36)
        pts.append([cx + int(r_inner * math.cos(a2)),
                    cy + int(r_inner * math.sin(a2))])
    pts = np.array(pts, np.int32)
    if thickness == -1:
        cv2.fillPoly(img, [pts], color)
    else:
        cv2.polylines(img, [pts], True, color, thickness)


def draw_trophy_icon(img, cx, cy, size=22, color=(0, 200, 255)):
    s = size
    # Cup body
    cv2.ellipse(img, (cx, cy - s//4), (s//2, s//2), 0, 0, 180, color, 2)
    # Stem
    cv2.line(img, (cx, cy + s//4), (cx, cy + s//2), color, 3)
    # Base
    cv2.line(img, (cx - s//2, cy + s//2), (cx + s//2, cy + s//2), color, 3)
    # Handles
    cv2.line(img, (cx - s//2, cy - s//4), (cx - s//2 - s//6, cy), color, 2)
    cv2.line(img, (cx + s//2, cy - s//4), (cx + s//2 + s//6, cy), color, 2)


def draw_target_icon(img, cx, cy, size=22, color=(255, 200, 0)):
    for r in [size, size * 2 // 3, size // 3]:
        cv2.circle(img, (cx, cy), r, color, 1)
    cv2.circle(img, (cx, cy), 4, color, -1)


# ── Confetti particle system ──────────────────────────────────────────────────

class ConfettiSystem:
    COLORS = [
        (120, 180, 40), (220, 160, 50), (180, 80, 130),
        (50, 150, 220), (80, 60, 230), (180, 110, 50),
        (220, 110, 150), (100, 180, 160)
    ]

    def __init__(self, n=160):
        self.n = n
        self.particles = []
        self._spawn()

    def _spawn(self):
        self.particles = []
        W, H = 1280, 720
        for _ in range(self.n):
            self.particles.append({
                'x':    float(np.random.randint(0, W)),
                'y':    float(np.random.randint(-H, 0)),
                'vx':   float(np.random.uniform(-2.5, 2.5)),
                'vy':   float(np.random.uniform(3, 9)),
                'rot':  float(np.random.uniform(0, 360)),
                'vrot': float(np.random.uniform(-8, 8)),
                'w':    int(np.random.randint(6, 16)),
                'h':    int(np.random.randint(4, 10)),
                'col':  self.COLORS[int(np.random.randint(0, len(self.COLORS)))],
                'shape': random.choice(['rect', 'circle', 'star']),
            })

    def reset(self):
        self._spawn()

    def update_and_draw(self, frame):
        H = frame.shape[0]
        all_done = True
        for p in self.particles:
            p['x']   += p['vx']
            p['y']   += p['vy']
            p['rot'] += p['vrot']
            p['vy']   = min(p['vy'] + 0.15, 12)

            if p['y'] < H:
                all_done = False
                cx, cy = int(p['x']), int(p['y'])
                if p['shape'] == 'circle':
                    cv2.circle(frame, (cx, cy), p['w'] // 2, p['col'], -1)
                elif p['shape'] == 'star':
                    pts = np.array([
                        [cx, cy - p['h']],
                        [cx + p['w']//2, cy],
                        [cx, cy + p['h']],
                        [cx - p['w']//2, cy],
                    ], np.int32)
                    cv2.fillPoly(frame, [pts], p['col'])
                else:
                    angle = math.radians(p['rot'])
                    cos_a, sin_a = math.cos(angle), math.sin(angle)
                    hw, hh = p['w'] / 2, p['h'] / 2
                    corners = [(-hw, -hh), (hw, -hh), (hw, hh), (-hw, hh)]
                    pts = []
                    for dx, dy in corners:
                        rx = int(cx + dx * cos_a - dy * sin_a)
                        ry = int(cy + dx * sin_a + dy * cos_a)
                        pts.append([rx, ry])
                    pts = np.array(pts, np.int32)
                    cv2.fillPoly(frame, [pts], p['col'])

        if all_done:
            self._spawn()


def point_in_rect(pt, rect):
    """rect = (x, y, w, h)"""
    x, y, w, h = rect
    return x <= pt[0] <= x + w and y <= pt[1] <= y + h


class GestureButton:
    DWELL_TIME = 1.0

    def __init__(self, label, rect, border_color=(120, 180, 40),
                 icon="", subtitle="", bg_color=None):
        self.label        = label
        self.rect         = rect
        self.border_color = border_color
        self.icon         = icon
        self.subtitle     = subtitle
        self.bg_color     = bg_color
        self._hover_start = None

    def update(self, cursor_pos, pinch_active):
        if cursor_pos is None:
            self._hover_start = None
            return False, 0.0
        hovered = point_in_rect(cursor_pos, self.rect)
        if hovered and pinch_active:
            if self._hover_start is None:
                self._hover_start = time.time()
            elapsed  = time.time() - self._hover_start
            progress = min(elapsed / self.DWELL_TIME, 1.0)
            if elapsed >= self.DWELL_TIME:
                self._hover_start = None
                return True, 1.0
            return False, progress
        else:
            self._hover_start = None
            return False, 0.0

    def draw(self, img, cursor_pos, pinch_active):
        hovered = cursor_pos and point_in_rect(cursor_pos, self.rect)
        prog = 0.0
        if hovered and pinch_active and self._hover_start:
            prog = min((time.time() - self._hover_start) / self.DWELL_TIME, 1.0)
        draw_neon_button(img, self.label, self.rect,
                         border_color=self.border_color,
                         text_color=(45, 40, 35),
                         hover=bool(hovered),
                         progress=prog,
                         icon=self.icon,
                         subtitle=self.subtitle,
                         bg_color=self.bg_color)
