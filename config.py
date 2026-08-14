# config.py
CAMERA_WIDTH  = 1280
CAMERA_HEIGHT = 720
FPS = 30

# Colors (BGR)
COLOR_BG         = (248, 249, 250)      # Off-white
COLOR_WALL       = (20, 20, 20)         # Charcoal walls (dark, high-contrast)
COLOR_FLOOR      = (255, 255, 255)      # White cell floors
COLOR_START      = (160, 240, 160)      # Soft pastel green start cell
COLOR_END        = (245, 180, 100)      # Soft blue/sky-blue end cell
COLOR_PLAYER     = (210, 130, 40)       # Deep slate blue player box
COLOR_PATH       = (235, 210, 245)      # Soft pastel lavender visited trail
COLOR_TEXT       = (45, 40, 35)         # Dark charcoal text
COLOR_UI_BG      = (255, 255, 255)      # Pure white UI backgrounds
COLOR_UI_BORDER  = (225, 220, 215)      # Soft grey-blue border
DEFAULT_CAMERA_OPACITY = 0.35           # Alpha of light overlay over the camera feed (0.0 to 1.0)

# Maze Config
MAZE_ROWS      = 9
MAZE_COLS      = 13
MAZE_CELL_SIZE = 52
MAZE_OFFSET_X  = (CAMERA_WIDTH - (MAZE_COLS * MAZE_CELL_SIZE)) // 2
MAZE_OFFSET_Y  = 100

# Gameplay Parameters
PINCH_THRESHOLD      = 0.09   # Normalised distance for pinch detection
SMOOTHING_FACTOR     = 0.7    # Higher = less smoothing = more responsive

# Hand gesture button click
HOVER_DWELL_TIME     = 1.2
PINCH_CLICK_COOLDOWN = 0.8

# Player movement — very fast, cell snaps instantly
MOVE_COOLDOWN        = 0.02   # Nearly instant
CELL_ENTER_THRESHOLD = 14
