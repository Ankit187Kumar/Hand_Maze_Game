import { MazeGenerator } from './MazeGenerator.js';
import { HandTracker } from './HandTracker.js';

const CONFIG = {
  CAMERA_WIDTH: 1280,
  CAMERA_HEIGHT: 720,
  COLOR_BG: '#F8F9FA',
  COLOR_WALL: '#141414',
  COLOR_START: '#A0F0A0',
  COLOR_END: '#F5B464',
  COLOR_PLAYER: '#D28228',
  COLOR_PATH: '#EBD2F5',
  MAZE_ROWS: 9,
  MAZE_COLS: 13,
  MAZE_CELL_SIZE: 52,
};
CONFIG.MAZE_OFFSET_X = (CONFIG.CAMERA_WIDTH - (CONFIG.MAZE_COLS * CONFIG.MAZE_CELL_SIZE)) / 2;
CONFIG.MAZE_OFFSET_Y = 150;

let video;
let canvas;
let ctx;
let cursorCanvas;
let cursorCtx;
let handTracker;
let maze;
let gameState = 'START';
let playerName = 'ANKIT';

let playerCell = null;
let pathCells = [];
let score = 0;
let startTime = null;

let thumbDownStart = null;
const THUMB_DOWN_HOLD_MS = 1500;

let isCamOn = true;
let camOpacity = 0.35;

// Gesture Button Dwell State
const GESTURE_DWELL_MS = 1000;
let activeHoverBtn = null;
let hoverStartTime = null;
let gestureCooldownUntil = 0;

// Local stats
let stats = {
  bestScore: 0,
  bestTime: null,
  gamesPlayed: 0
};

function loadStats() {
  try {
    const saved = localStorage.getItem('hand_maze_stats');
    if (saved) {
      stats = JSON.parse(saved);
    }
  } catch (e) {
    console.error(e);
  }
}

function saveStats() {
  try {
    localStorage.setItem('hand_maze_stats', JSON.stringify(stats));
  } catch (e) {
    console.error(e);
  }
}

async function init() {
  loadStats();

  video = document.getElementById('webcam');
  canvas = document.getElementById('output_canvas');
  ctx = canvas.getContext('2d');
  canvas.width = CONFIG.CAMERA_WIDTH;
  canvas.height = CONFIG.CAMERA_HEIGHT;

  cursorCanvas = document.getElementById('cursor_canvas');
  cursorCtx = cursorCanvas.getContext('2d');
  cursorCanvas.width = CONFIG.CAMERA_WIDTH;
  cursorCanvas.height = CONFIG.CAMERA_HEIGHT;

  initGestureButtons();
  setupButtons();
  setupKeyboard();
  switchState('START');

  try {
    const stream = await navigator.mediaDevices.getUserMedia({ video: { width: 1280, height: 720 } });
    video.srcObject = stream;
    await new Promise(r => video.onloadedmetadata = r);
    video.play();

    handTracker = new HandTracker();
    await handTracker.initialize();
    
    requestAnimationFrame(gameLoop);
  } catch (err) {
    console.error("Camera error:", err);
  }
}

function initGestureButtons() {
  const buttons = document.querySelectorAll('.btn, .opt-btn');
  buttons.forEach(btn => {
    if (!btn.querySelector('.btn-progress')) {
      const prog = document.createElement('div');
      prog.className = 'btn-progress';
      btn.prepend(prog);
    }
  });
}

function setupButtons() {
  document.getElementById('btn-start-game').onclick = () => switchState('LOGIN');
  
  document.getElementById('btn-continue').onclick = () => {
    const inputVal = document.getElementById('player-name').value.trim();
    if (!inputVal) {
      alert("Please enter a name before continuing!");
      return;
    }
    playerName = inputVal;
    document.getElementById('menu-player-name').innerText = playerName.toUpperCase();
    document.getElementById('hud-player').innerText = playerName.toUpperCase();
    document.getElementById('hs-player').innerText = playerName.toUpperCase();
    switchState('MENU');
  };

  document.getElementById('btn-play-game').onclick = () => {
    resetGame();
    switchState('GAME');
  };

  document.getElementById('btn-how-to-play').onclick = () => switchState('HOW_TO_PLAY');
  document.getElementById('btn-back-how').onclick = () => switchState('MENU');
  
  document.getElementById('btn-high-scores').onclick = () => {
    updateHighScoresScreen();
    switchState('HIGH_SCORES');
  };
  document.getElementById('btn-back-hs').onclick = () => switchState('MENU');

  document.getElementById('btn-quit').onclick = () => switchState('START');

  document.getElementById('btn-play-again').onclick = () => {
    resetGame();
    switchState('GAME');
  };

  document.getElementById('btn-win-menu').onclick = () => switchState('MENU');
  
  // Options Panel Buttons
  document.getElementById('opt-cam').onclick = () => {
    isCamOn = !isCamOn;
    updateHUD();
  };
  
  document.getElementById('opt-fs').onclick = () => {
    if (!document.fullscreenElement) {
      document.documentElement.requestFullscreen().catch(err => console.log(err));
    } else {
      document.exitFullscreen().catch(err => console.log(err));
    }
  };

  document.getElementById('opt-op-plus').onclick = () => {
    camOpacity = Math.min(1.0, camOpacity + 0.1);
    updateHUD();
  };
  
  document.getElementById('opt-op-minus').onclick = () => {
    camOpacity = Math.max(0.0, camOpacity - 0.1);
    updateHUD();
  };
}

function setupKeyboard() {
  window.addEventListener('keydown', (e) => {
    if (e.key === 'r' || e.key === 'R') {
      if (gameState === 'GAME') {
        resetGame();
      }
    } else if (e.key === 'Escape') {
      if (gameState === 'LOGIN') switchState('START');
      else if (gameState === 'MENU') switchState('LOGIN');
      else if (gameState === 'HOW_TO_PLAY' || gameState === 'HIGH_SCORES' || gameState === 'GAME' || gameState === 'WIN') switchState('MENU');
    } else if (e.key === ' ') {
      if (gameState === 'WIN') {
        resetGame();
        switchState('GAME');
      }
    } else if (gameState === 'GAME') {
      // Keyboard fallback movement
      let moveDir = null;
      if (e.key === 'ArrowUp' || e.key === 'w' || e.key === 'W') moveDir = [-1, 0];
      if (e.key === 'ArrowDown' || e.key === 's' || e.key === 'S') moveDir = [1, 0];
      if (e.key === 'ArrowLeft' || e.key === 'a' || e.key === 'A') moveDir = [0, -1];
      if (e.key === 'ArrowRight' || e.key === 'd' || e.key === 'D') moveDir = [0, 1];

      if (moveDir && maze && playerCell) {
        const tr = playerCell.r + moveDir[0];
        const tc = playerCell.c + moveDir[1];
        if (tr >= 0 && tr < maze.rows && tc >= 0 && tc < maze.cols) {
          if (!maze.isWallBetween(playerCell.r, playerCell.c, tr, tc)) {
            movePlayerTo({ r: tr, c: tc });
          }
        }
      }
    }
  });
}

function updateHighScoresScreen() {
  document.getElementById('hs-player').innerText = playerName.toUpperCase();
  document.getElementById('hs-score').innerText = stats.bestScore;
  document.getElementById('hs-time').innerText = stats.bestTime ? stats.bestTime.toFixed(1) + 's' : '--';
  document.getElementById('hs-games').innerText = stats.gamesPlayed;
}

function switchState(newState) {
  gameState = newState;
  document.querySelectorAll('.screen, .game-hud').forEach(el => el.classList.remove('active'));
  
  // Clear any existing progress bar
  document.querySelectorAll('.btn-progress').forEach(p => p.style.width = '0%');
  activeHoverBtn = null;
  hoverStartTime = null;

  if (newState === 'START') document.getElementById('screen-start').classList.add('active');
  else if (newState === 'LOGIN') {
    document.getElementById('screen-login').classList.add('active');
    setTimeout(() => {
      const inp = document.getElementById('player-name');
      if (inp) inp.focus();
    }, 100);
  }
  else if (newState === 'MENU') document.getElementById('screen-menu').classList.add('active');
  else if (newState === 'HOW_TO_PLAY') document.getElementById('screen-how-to-play').classList.add('active');
  else if (newState === 'HIGH_SCORES') document.getElementById('screen-high-scores').classList.add('active');
  else if (newState === 'WIN') document.getElementById('screen-win').classList.add('active');
  else if (newState === 'GAME') document.getElementById('screen-game').classList.add('active');
}

function resetGame() {
  maze = new MazeGenerator(CONFIG.MAZE_ROWS, CONFIG.MAZE_COLS, CONFIG.MAZE_CELL_SIZE, CONFIG.MAZE_OFFSET_X, CONFIG.MAZE_OFFSET_Y);
  playerCell = { ...maze.startCell };
  pathCells = [{ ...maze.startCell }];
  score = 0;
  startTime = null;
  updateHUD();
}

function updateHUD() {
  document.getElementById('hud-score').innerText = score;
  document.getElementById('hud-best').innerText = stats.bestTime ? stats.bestTime.toFixed(1) + 's' : '--';
  document.querySelector('.opt-status').innerHTML = `Opacity: ${Math.round(camOpacity * 100)}%<br>CAM: ${isCamOn ? 'ON' : 'OFF'}`;
}

function movePlayerTo(targetCell) {
  if (!startTime) startTime = performance.now();
  
  if (pathCells.length >= 2 && pathCells[pathCells.length - 2].r === targetCell.r && pathCells[pathCells.length - 2].c === targetCell.c) {
    pathCells.pop();
    score = Math.max(0, score - 1);
  } else {
    pathCells.push(targetCell);
    score++;
  }
  playerCell = targetCell;
  updateHUD();

  // Check Win Condition
  if (playerCell.r === maze.endCell.r && playerCell.c === maze.endCell.c) {
    handleWin();
  }
}

function handleWin() {
  const finalTimeSec = startTime ? (performance.now() - startTime) / 1000 : 0;
  stats.gamesPlayed++;
  if (score > stats.bestScore) stats.bestScore = score;
  if (!stats.bestTime || finalTimeSec < stats.bestTime) stats.bestTime = finalTimeSec;
  saveStats();

  document.getElementById('win-score').innerText = score;
  const m = String(Math.floor(finalTimeSec / 60)).padStart(2, '0');
  const s = String(Math.floor(finalTimeSec % 60)).padStart(2, '0');
  document.getElementById('win-time').innerText = `${m}:${s} (${finalTimeSec.toFixed(1)}s)`;

  switchState('WIN');
}

// ── Gesture Button Interaction Engine ───────────────────────────────────────

function updateGestureButtons(handPos, pinchActive) {
  const now = performance.now();
  if (now < gestureCooldownUntil) return;

  // Convert canvas coordinates to browser screen coordinates
  const screenX = (handPos.x / canvas.width) * window.innerWidth;
  const screenY = (handPos.y / canvas.height) * window.innerHeight;

  // Check interactive elements on active screen or options panel
  const activeContainer = document.querySelector('.screen.active') || document.querySelector('.game-hud.active');
  if (!activeContainer) return;

  const buttons = Array.from(activeContainer.querySelectorAll('.btn, .opt-btn'));
  let currentlyHovered = null;

  for (const btn of buttons) {
    const rect = btn.getBoundingClientRect();
    if (screenX >= rect.left && screenX <= rect.right && screenY >= rect.top && screenY <= rect.bottom) {
      currentlyHovered = btn;
      break;
    }
  }

  // Handle name input gesture focus
  if (gameState === 'LOGIN') {
    const nameInp = document.getElementById('player-name');
    if (nameInp) {
      const iRect = nameInp.getBoundingClientRect();
      if (screenX >= iRect.left && screenX <= iRect.right && screenY >= iRect.top && screenY <= iRect.bottom) {
        if (pinchActive) nameInp.focus();
      }
    }
  }

  // Update hover and progress
  if (currentlyHovered && pinchActive) {
    if (activeHoverBtn !== currentlyHovered) {
      // Switched to a new button
      if (activeHoverBtn) {
        const oldProg = activeHoverBtn.querySelector('.btn-progress');
        if (oldProg) oldProg.style.width = '0%';
      }
      activeHoverBtn = currentlyHovered;
      hoverStartTime = now;
    }

    const elapsed = now - hoverStartTime;
    const progress = Math.min(1.0, elapsed / GESTURE_DWELL_MS);

    const progEl = currentlyHovered.querySelector('.btn-progress');
    if (progEl) {
      progEl.style.width = `${progress * 100}%`;
    }

    if (progress >= 1.0) {
      // Trigger Button Click Action!
      if (progEl) progEl.style.width = '0%';
      hoverStartTime = null;
      activeHoverBtn = null;
      gestureCooldownUntil = now + 600; // Cooldown to avoid double clicks
      currentlyHovered.click();
    }
  } else {
    // Not pinching or not hovering on any button
    if (activeHoverBtn) {
      const progEl = activeHoverBtn.querySelector('.btn-progress');
      if (progEl) progEl.style.width = '0%';
      activeHoverBtn = null;
      hoverStartTime = null;
    }
  }
}

// ── Main Game Loop ──────────────────────────────────────────────────────────

let lastMoveTime = 0;

function gameLoop() {
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  cursorCtx.clearRect(0, 0, cursorCanvas.width, cursorCanvas.height);

  // Background camera feed
  if (isCamOn && video.readyState === 4) {
    ctx.save();
    ctx.globalAlpha = camOpacity;
    ctx.translate(canvas.width, 0);
    ctx.scale(-1, 1);
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
    ctx.restore();
  }

  // Draw maze & HUD time in game mode
  if (gameState === 'GAME' && maze) {
    maze.draw(ctx, CONFIG, playerCell, pathCells);
    
    if (startTime) {
      const elapsed = Math.floor((performance.now() - startTime) / 1000);
      const m = String(Math.floor(elapsed / 60)).padStart(2, '0');
      const s = String(elapsed % 60).padStart(2, '0');
      document.getElementById('hud-time').innerText = `${m}:${s}`;
    }
  }

  // Hand Tracking processing
  const handInfo = handTracker ? handTracker.getHandInfo(video, canvas.width, canvas.height) : null;
  
  if (handInfo) {
    // Draw landmarks if camera is active
    if (isCamOn) {
      handTracker.drawLandmarks(cursorCtx, handInfo.landmarks, cursorCanvas.width, cursorCanvas.height);
    }
    
    // Draw pulsing gesture cursor
    const t = performance.now() * 0.0035;
    const pulse = Math.abs(Math.sin(t)) * 4;

    if (handInfo.pinchActive) {
      // Outer green ring
      cursorCtx.strokeStyle = '#2ecc71';
      cursorCtx.lineWidth = 2.5;
      cursorCtx.beginPath();
      cursorCtx.arc(handInfo.pos.x, handInfo.pos.y, 16 + pulse, 0, Math.PI * 2);
      cursorCtx.stroke();

      // Inner solid green dot
      cursorCtx.fillStyle = '#2ecc71';
      cursorCtx.beginPath();
      cursorCtx.arc(handInfo.pos.x, handInfo.pos.y, 6, 0, Math.PI * 2);
      cursorCtx.fill();
    } else {
      // Outer blue/slate ring
      cursorCtx.strokeStyle = '#3498db';
      cursorCtx.lineWidth = 1.5;
      cursorCtx.beginPath();
      cursorCtx.arc(handInfo.pos.x, handInfo.pos.y, 13 + pulse, 0, Math.PI * 2);
      cursorCtx.stroke();

      // Inner solid blue dot
      cursorCtx.fillStyle = '#3498db';
      cursorCtx.beginPath();
      cursorCtx.arc(handInfo.pos.x, handInfo.pos.y, 3.5, 0, Math.PI * 2);
      cursorCtx.fill();
    }

    // Line from cursor to player box during maze gameplay
    if (gameState === 'GAME' && handInfo.pinchActive && playerCell) {
      const pCx = CONFIG.MAZE_OFFSET_X + playerCell.c * CONFIG.MAZE_CELL_SIZE + CONFIG.MAZE_CELL_SIZE / 2;
      const pCy = CONFIG.MAZE_OFFSET_Y + playerCell.r * CONFIG.MAZE_CELL_SIZE + CONFIG.MAZE_CELL_SIZE / 2;
      cursorCtx.strokeStyle = 'rgba(120, 110, 100, 0.6)';
      cursorCtx.lineWidth = 2;
      cursorCtx.beginPath();
      cursorCtx.moveTo(handInfo.pos.x, handInfo.pos.y);
      cursorCtx.lineTo(pCx, pCy);
      cursorCtx.stroke();
    }

    // Update HUD Status Badge
    if (gameState === 'GAME') {
      const statusEl = document.getElementById('hud-status');
      if (statusEl) {
        statusEl.innerText = handInfo.pinchActive ? 'PINCH ACTIVE' : 'HAND DETECTED';
        statusEl.style.color = handInfo.pinchActive ? '#2ecc71' : '#3498db';
      }
    }

    // Interactive Button Hover & Dwell
    updateGestureButtons(handInfo.pos, handInfo.pinchActive);

    // Thumb Down to go back
    const tdOverlay = document.getElementById('thumb-down-overlay');
    const tdBar = document.getElementById('td-bar');
    if (handInfo.thumbDown) {
      if (!thumbDownStart) thumbDownStart = performance.now();
      const holdTime = performance.now() - thumbDownStart;
      const progress = Math.min(100, (holdTime / THUMB_DOWN_HOLD_MS) * 100);
      
      if (tdOverlay) tdOverlay.style.display = 'flex';
      if (tdBar) tdBar.style.width = `${progress}%`;

      if (progress >= 100) {
        thumbDownStart = null;
        if (tdOverlay) tdOverlay.style.display = 'none';
        
        // Navigation hierarchy
        if (gameState === 'LOGIN') switchState('START');
        else if (gameState === 'MENU') switchState('LOGIN');
        else if (gameState === 'HOW_TO_PLAY' || gameState === 'HIGH_SCORES' || gameState === 'GAME' || gameState === 'WIN') switchState('MENU');
      }
    } else {
      thumbDownStart = null;
      if (tdOverlay) tdOverlay.style.display = 'none';
    }

    // Maze Movement Control
    if (gameState === 'GAME' && handInfo.pinchActive && playerCell && maze) {
      const now = performance.now();
      if (now - lastMoveTime > 130) {
        const targetCell = maze.pixelToCell(handInfo.pos.x, handInfo.pos.y);
        if (targetCell && (targetCell.r !== playerCell.r || targetCell.c !== playerCell.c)) {
          const dr = Math.abs(targetCell.r - playerCell.r);
          const dc = Math.abs(targetCell.c - playerCell.c);
          if (dr + dc === 1) {
            if (!maze.isWallBetween(playerCell.r, playerCell.c, targetCell.r, targetCell.c)) {
              lastMoveTime = now;
              movePlayerTo(targetCell);
            }
          }
        }
      }
    }
  } else {
    // No hand detected
    if (gameState === 'GAME') {
      const statusEl = document.getElementById('hud-status');
      if (statusEl) {
        statusEl.innerText = 'NO HAND';
        statusEl.style.color = '#e74c3c';
      }
    }
    const tdOverlay = document.getElementById('thumb-down-overlay');
    if (tdOverlay) tdOverlay.style.display = 'none';
    thumbDownStart = null;

    if (activeHoverBtn) {
      const progEl = activeHoverBtn.querySelector('.btn-progress');
      if (progEl) progEl.style.width = '0%';
      activeHoverBtn = null;
      hoverStartTime = null;
    }
  }

  requestAnimationFrame(gameLoop);
}

init();
