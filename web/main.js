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
let bestTime = null;

let playerCell = null;
let pathCells = [];
let score = 0;
let startTime = null;

let thumbDownStart = null;
const THUMB_DOWN_HOLD_MS = 1500;

let isCamOn = true;
let camOpacity = 0.35;

async function init() {
  video = document.getElementById('webcam');
  canvas = document.getElementById('output_canvas');
  ctx = canvas.getContext('2d');
  canvas.width = CONFIG.CAMERA_WIDTH;
  canvas.height = CONFIG.CAMERA_HEIGHT;

  cursorCanvas = document.getElementById('cursor_canvas');
  cursorCtx = cursorCanvas.getContext('2d');
  cursorCanvas.width = CONFIG.CAMERA_WIDTH;
  cursorCanvas.height = CONFIG.CAMERA_HEIGHT;

  setupButtons();
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
    switchState('MENU');
  };
  document.getElementById('btn-play-game').onclick = () => {
    resetGame();
    switchState('GAME');
  };
  document.getElementById('btn-how-to-play').onclick = () => switchState('HOW_TO_PLAY');
  
  // Options
  document.getElementById('opt-cam').onclick = () => isCamOn = !isCamOn;
  document.getElementById('opt-op-plus').onclick = () => camOpacity = Math.min(1.0, camOpacity + 0.1);
  document.getElementById('opt-op-minus').onclick = () => camOpacity = Math.max(0.0, camOpacity - 0.1);
}

function switchState(newState) {
  gameState = newState;
  document.querySelectorAll('.screen, .game-hud').forEach(el => el.classList.remove('active'));
  
  if (newState === 'START') document.getElementById('screen-start').classList.add('active');
  else if (newState === 'LOGIN') document.getElementById('screen-login').classList.add('active');
  else if (newState === 'MENU') document.getElementById('screen-menu').classList.add('active');
  else if (newState === 'HOW_TO_PLAY') document.getElementById('screen-how-to-play').classList.add('active');
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

let lastMoveTime = 0;

function updateHUD() {
  document.getElementById('hud-score').innerText = score;
  document.getElementById('hud-best').innerText = bestTime ? bestTime.toFixed(1) + 's' : '--';
  document.querySelector('.opt-status').innerHTML = `Opacity: ${Math.round(camOpacity * 100)}%<br>CAM: ${isCamOn ? 'ON' : 'OFF'}`;
}

function gameLoop() {
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  cursorCtx.clearRect(0, 0, cursorCanvas.width, cursorCanvas.height);

  if (isCamOn && video.readyState === 4) {
    ctx.save();
    ctx.globalAlpha = camOpacity;
    ctx.translate(canvas.width, 0);
    ctx.scale(-1, 1);
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
    ctx.restore();
  }

  if (gameState === 'GAME' && maze) {
    maze.draw(ctx, CONFIG, playerCell, pathCells);
    
    if (startTime) {
      const elapsed = Math.floor((performance.now() - startTime) / 1000);
      const m = String(Math.floor(elapsed / 60)).padStart(2, '0');
      const s = String(elapsed % 60).padStart(2, '0');
      document.getElementById('hud-time').innerText = `${m}:${s}`;
    }
  }

  const handInfo = handTracker ? handTracker.getHandInfo(video, canvas.width, canvas.height) : null;
  
  if (handInfo) {
    if (isCamOn) {
      handTracker.drawLandmarks(cursorCtx, handInfo.landmarks, cursorCanvas.width, cursorCanvas.height);
    }
    
    // Draw cursor
    cursorCtx.fillStyle = handInfo.pinchActive ? '#2ecc71' : '#3498db';
    cursorCtx.beginPath();
    cursorCtx.arc(handInfo.pos.x, handInfo.pos.y, 10, 0, Math.PI*2);
    cursorCtx.fill();

    // Line to player if in game
    if (gameState === 'GAME' && handInfo.pinchActive) {
      const pCx = CONFIG.MAZE_OFFSET_X + playerCell.c * CONFIG.MAZE_CELL_SIZE + CONFIG.MAZE_CELL_SIZE/2;
      const pCy = CONFIG.MAZE_OFFSET_Y + playerCell.r * CONFIG.MAZE_CELL_SIZE + CONFIG.MAZE_CELL_SIZE/2;
      cursorCtx.strokeStyle = 'rgba(120, 110, 100, 0.5)';
      cursorCtx.lineWidth = 2;
      cursorCtx.beginPath();
      cursorCtx.moveTo(handInfo.pos.x, handInfo.pos.y);
      cursorCtx.lineTo(pCx, pCy);
      cursorCtx.stroke();
    }

    if (gameState === 'GAME') {
      document.getElementById('hud-status').innerText = handInfo.pinchActive ? 'PINCH ACTIVE' : 'HAND DETECTED';
      document.getElementById('hud-status').style.color = handInfo.pinchActive ? '#2ecc71' : '#3498db';
    }

    // Thumb down logic
    const tdOverlay = document.getElementById('thumb-down-overlay');
    const tdBar = document.getElementById('td-bar');
    if (handInfo.thumbDown) {
      if (!thumbDownStart) thumbDownStart = performance.now();
      const holdTime = performance.now() - thumbDownStart;
      const progress = Math.min(100, (holdTime / THUMB_DOWN_HOLD_MS) * 100);
      
      tdOverlay.style.display = 'flex';
      tdBar.style.width = `${progress}%`;

      if (progress >= 100) {
        thumbDownStart = null;
        tdOverlay.style.display = 'none';
        
        // Go back logic
        if (gameState === 'LOGIN') switchState('START');
        else if (gameState === 'MENU') switchState('LOGIN');
        else if (gameState === 'HOW_TO_PLAY' || gameState === 'GAME') switchState('MENU');
      }
    } else {
      thumbDownStart = null;
      tdOverlay.style.display = 'none';
    }

    // Game Movement
    if (gameState === 'GAME' && handInfo.pinchActive) {
      if (!startTime) startTime = performance.now();
      const now = performance.now();
      if (now - lastMoveTime > 150) {
        const targetCell = maze.pixelToCell(handInfo.pos.x, handInfo.pos.y);
        if (targetCell && (targetCell.r !== playerCell.r || targetCell.c !== playerCell.c)) {
          const dr = Math.abs(targetCell.r - playerCell.r);
          const dc = Math.abs(targetCell.c - playerCell.c);
          if (dr + dc === 1) {
            if (!maze.isWallBetween(playerCell.r, playerCell.c, targetCell.r, targetCell.c)) {
              playerCell = targetCell;
              lastMoveTime = now;
              
              if (pathCells.length >= 2 && pathCells[pathCells.length-2].r === targetCell.r && pathCells[pathCells.length-2].c === targetCell.c) {
                pathCells.pop();
                score = Math.max(0, score - 1);
              } else {
                pathCells.push(targetCell);
                score++;
              }
              
              updateHUD();

              if (playerCell.r === maze.endCell.r && playerCell.c === maze.endCell.c) {
                const finalTime = (performance.now() - startTime) / 1000;
                if (!bestTime || finalTime < bestTime) bestTime = finalTime;
                alert(`YOU WIN! Score: ${score}, Time: ${finalTime.toFixed(1)}s`);
                switchState('MENU');
              }
            }
          }
        }
      }
    }
  } else {
    if (gameState === 'GAME') {
      document.getElementById('hud-status').innerText = 'NO HAND';
      document.getElementById('hud-status').style.color = '#e74c3c';
    }
    document.getElementById('thumb-down-overlay').style.display = 'none';
    thumbDownStart = null;
  }

  requestAnimationFrame(gameLoop);
}

init();
