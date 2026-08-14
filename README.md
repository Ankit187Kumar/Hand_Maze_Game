# Hand Maze Game

A complete, polished Python desktop game built with OpenCV, MediaPipe, and NumPy. The player uses hand gestures via a webcam to navigate through a procedurally generated maze.

## Features
- Real-time hand tracking and pinch detection using MediaPipe.
- Procedural maze generation ensuring a different layout every game.
- Advanced collision detection prevents bypassing walls.
- Dynamic scoring (+1 for moving, -1 for wall collision).
- Erase paths by moving backwards.
- User management with local storage (`users.json`).
- High scores and best times tracking.

## Project Structure
- `main.py` - Application entry point.
- `config.py` - Configuration constants.
- `core/` - Hand tracking, collision logic, maze generator, path manager.
- `screens/` - UI for Start, Login, Menu, Game, and High Scores.
- `utils/` - User data management and drawing helpers.

## Installation
1. Ensure you have Python 3.7+ installed.
2. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Requirements
- `opencv-python`
- `mediapipe`
- `numpy`
- A working webcam.

## How to Run
```bash
python main.py
```

## Controls & Rules
- **Navigate Menus**: Use keyboard as prompted (Space, Enter, 1-4).
- **Gameplay**:
  - Show ONE hand to the camera.
  - Pinch your thumb and any finger near the GREEN start box to begin.
  - Keep pinching and drag your hand to draw the red path.
  - Avoid touching the white maze walls. Wall collisions subtract 1 from your score.
  - Reaching the BLUE end box wins the game.
  - Move backward to erase path mistakes.
- **Hotkeys**:
  - `ESC` to return to the previous screen.
  - `R` to restart the current game with a new maze.

Enjoy the game!
