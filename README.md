# Hand Maze Game

A complete Python desktop game built with **OpenCV, MediaPipe, and NumPy**. The player uses hand gestures through a webcam to navigate a procedurally generated maze.

## 🎮 Try the Game

Play the web version directly in your browser:

**[Play Hand Maze Game](https://hand-maze-game.vercel.app/)**

> Allow camera access and use **one hand** to interact with the game.

## Features

* Real-time hand tracking and pinch detection using MediaPipe.
* Procedural maze generation with a different layout for each game.
* Collision detection prevents bypassing maze walls.
* Dynamic scoring (+1 for moving, -1 for wall collision).
* Move backward to erase the path.
* User management using local storage (`users.json`).
* High scores and best-time tracking.
* Webcam-based hand gesture controls.

## Project Structure

```text
Hand Maze Game/
│
├── main.py              # Application entry point
├── config.py            # Configuration constants
├── requirements.txt     # Python dependencies
├── users.json           # Local user and score data
│
├── core/
│   ├── hand_tracker.py  # Hand tracking and gestures
│   ├── collision.py     # Collision detection
│   ├── maze_generator.py# Maze generation
│   └── path_manager.py  # Player path management
│
├── screens/
│   ├── start_screen.py
│   ├── login_screen.py
│   ├── menu_screen.py
│   ├── game_screen.py
│   └── high_scores.py
│
└── utils/
    ├── helpers.py
    └── user_manager.py
```

## Installation

Make sure **Python 3.7+** is installed.

Install the required dependencies:

```bash
pip install -r requirements.txt
```

## Requirements

* Python 3.7+
* OpenCV
* MediaPipe
* NumPy
* Working webcam

## How to Run

```bash
python main.py
```

## Hand Gesture Controls

* 🖐️ Show **ONE hand** to the camera.
* 🤏 Pinch your **thumb and finger** near the green Start box to begin.
* Move your hand while pinching to navigate through the maze.
* Avoid the **white maze walls**.
* Reach the **blue End box** to win.
* Move backward to erase path mistakes.

## Scoring

* **+1** for a valid movement.
* **-1** for hitting a maze wall.
* Moving backward removes the previous path.

## Hotkeys

| Key               | Action                    |
| ----------------- | ------------------------- |
| `ESC`             | Return to previous screen |
| `R`               | Restart with a new maze   |
| `SPACE` / `ENTER` | Menu selection            |

## How the Maze Works

The maze is generated **procedurally**, so a new layout is created for each game.

The main systems are:

```text
Hand Tracking
     ↓
MediaPipe
     ↓
Hand Gesture Detection
     ↓
Player Movement
     ↓
Maze Collision Detection
     ↓
Score & Path Tracking
```

Maze generation:

```text
Grid
 ↓
Random Maze Generation
 ↓
Remove Walls
 ↓
Create Paths
 ↓
Start + End
 ↓
Playable Maze
```

## Web Version

The project also has a browser version that can be played without installing Python:

**https://hand-maze-game.vercel.app/**

The web version uses the webcam and hand tracking directly in the browser.

---

Enjoy the **Hand Maze Game!** 🖐️🧩
