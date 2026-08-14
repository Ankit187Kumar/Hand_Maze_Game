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

// Calculate offsets to center the maze
CONFIG.MAZE_OFFSET_X = (CONFIG.CAMERA_WIDTH - (CONFIG.MAZE_COLS * CONFIG.MAZE_CELL_SIZE)) / 2;
CONFIG.MAZE_OFFSET_Y = 150;

let video;
let canvas;
let ctx;
let handTracker;
let maze;
let gameState = 'START'; // START, LOADING, GAME, WIN
let playerCell = null;
let pathCells = [];
let score = 0;

async function init() {
  video = document.getElementById('webcam');
  canvas = document.getElementById('output_canvas');
  ctx = canvas.getContext('2d');
  
  // Set canvas size
  canvas.width = CONFIG.CAMERA_WIDTH;
  canvas.height = CONFIG.CAMERA_HEIGHT;
  
  showStartScreen();
}

function showStartScreen() {
  const ui = document.getElementById('ui-layer');
  ui.innerHTML = `
    <div class="screen">
      <h1>Hand Maze Game</h1>
      <p>Pinch your fingers to control the green box and reach the goal!</p>
      <button id="start-btn">Start Game</button>
    </div>
  `;
  document.getElementById('start-btn').addEventListener('click', startGameSequence);
}

async function startGameSequence() {
  const ui = document.getElementById('ui-layer');
  ui.innerHTML = `
    <div class="screen">
      <h2>Loading AI Model...</h2>
      <div class="loader"></div>
      <p style="margin-top:20px;font-size:0.9rem;">Please allow camera access</p>
    </div>
  `;

  try {
    const stream = await navigator.mediaDevices.getUserMedia({ video: { width: 1280, height: 720 } });
    video.srcObject = stream;
    
    await new Promise((resolve) => {
      video.onloadedmetadata = () => resolve();
    });
    video.play();

    handTracker = new HandTracker();
    await handTracker.initialize();

    resetGame();
    gameState = 'GAME';
    ui.innerHTML = ''; // Clear UI for game
    requestAnimationFrame(gameLoop);
  } catch (err) {
    ui.innerHTML = `
      <div class="screen">
        <h2 style="color:red;">Error accessing camera</h2>
        <p>${err.message}</p>
        <button onclick="location.reload()">Retry</button>
      </div>
    `;
  }
}

function resetGame() {
  maze = new MazeGenerator(CONFIG.MAZE_ROWS, CONFIG.MAZE_COLS, CONFIG.MAZE_CELL_SIZE, CONFIG.MAZE_OFFSET_X, CONFIG.MAZE_OFFSET_Y);
  playerCell = { ...maze.startCell };
  pathCells = [{ ...maze.startCell }];
  score = 0;
}

let lastMoveTime = 0;

function gameLoop() {
  if (gameState !== 'GAME' && gameState !== 'WIN') return;

  // Clear canvas
  ctx.fillStyle = CONFIG.COLOR_BG;
  ctx.fillRect(0, 0, canvas.width, canvas.height);

  // Draw camera feed with opacity (mirrored)
  ctx.save();
  ctx.globalAlpha = 0.3;
  ctx.translate(canvas.width, 0);
  ctx.scale(-1, 1);
  ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
  ctx.restore();

  maze.draw(ctx, CONFIG, playerCell, pathCells);

  const handInfo = handTracker.getHandInfo(video, canvas.width, canvas.height);
  
  if (handInfo) {
    handTracker.drawLandmarks(ctx, handInfo.landmarks, canvas.width, canvas.height);
    
    // Draw cursor
    ctx.fillStyle = handInfo.pinchActive ? '#A0F0A0' : '#FFFFFF';
    ctx.beginPath();
    ctx.arc(handInfo.pos.x, handInfo.pos.y, 10, 0, Math.PI*2);
    ctx.fill();

    // Game Logic
    if (gameState === 'GAME' && handInfo.pinchActive) {
      const now = performance.now();
      if (now - lastMoveTime > 150) { // Cooldown
        const targetCell = maze.pixelToCell(handInfo.pos.x, handInfo.pos.y);
        
        if (targetCell && (targetCell.r !== playerCell.r || targetCell.c !== playerCell.c)) {
          // Check adjacency
          const dr = Math.abs(targetCell.r - playerCell.r);
          const dc = Math.abs(targetCell.c - playerCell.c);
          
          if (dr + dc === 1) { // Adjacent
            if (!maze.isWallBetween(playerCell.r, playerCell.c, targetCell.r, targetCell.c)) {
              // Move valid
              playerCell = targetCell;
              lastMoveTime = now;
              
              // Check if backward
              if (pathCells.length >= 2 && pathCells[pathCells.length-2].r === targetCell.r && pathCells[pathCells.length-2].c === targetCell.c) {
                pathCells.pop();
                score = Math.max(0, score - 1);
              } else {
                pathCells.push(targetCell);
                score++;
              }

              // Win Condition
              if (playerCell.r === maze.endCell.r && playerCell.c === maze.endCell.c) {
                gameState = 'WIN';
                showWinScreen();
              }
            }
          }
        }
      }
    }
  }

  // Draw HUD
  ctx.fillStyle = '#2d2823';
  ctx.font = '24px Inter, sans-serif';
  ctx.fillText(`Score: ${score}`, 40, 50);

  requestAnimationFrame(gameLoop);
}

function showWinScreen() {
  const ui = document.getElementById('ui-layer');
  ui.innerHTML = `
    <div class="screen" style="border-color: #F5B464;">
      <h1 style="font-size: 3.5rem;">YOU WIN!</h1>
      <p style="font-size: 1.5rem;">Score: <strong>${score}</strong></p>
      <button id="restart-btn" style="background:#F5B464;">Play Again</button>
    </div>
  `;
  document.getElementById('restart-btn').addEventListener('click', () => {
    resetGame();
    gameState = 'GAME';
    ui.innerHTML = '';
  });
}

// Start app
init();
