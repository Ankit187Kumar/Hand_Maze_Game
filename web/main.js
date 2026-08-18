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

// Leaderboard & Stats (Time-Based: Lowest time = Rank 1)
let leaderboard = [];

function loadLeaderboard() {
  try {
    const saved = localStorage.getItem('hand_maze_leaderboard');
    if (saved) {
      leaderboard = JSON.parse(saved);
      // Sort ascending by time (fastest first)
      leaderboard.sort((a, b) => a.time - b.time);
    } else {
      // Default sample records
      leaderboard = [
        { name: 'ANKIT', time: 14.8, score: 22, date: 'Recent' },
        { name: 'PRO_PLAYER', time: 19.5, score: 28, date: 'Recent' },
        { name: 'CHAMPION', time: 24.2, score: 30, date: 'Recent' }
      ];
    }
  } catch (e) {
    console.error(e);
  }
}

function saveLeaderboard() {
  try {
    localStorage.setItem('hand_maze_leaderboard', JSON.stringify(leaderboard));
  } catch (e) {
    console.error(e);
  }
}

function getBestTime() {
  if (leaderboard.length > 0) {
    return leaderboard[0].time;
  }
  return null;
}

// Floating Bubbles Background (Matches Python draw_star_bg)
class FloatingBubble {
  constructor(w, h) {
    this.w = w;
    this.h = h;
    this.r = Math.random() * 50 + 35;
    this.x = Math.random() * w;
    this.y = Math.random() * h;
    this.vx = (Math.random() - 0.5) * 0.7;
    this.vy = (Math.random() - 0.5) * 0.7;
    const colors = [
      'rgba(245, 220, 220, 0.55)',
      'rgba(220, 245, 220, 0.55)',
      'rgba(220, 235, 245, 0.55)',
      'rgba(245, 245, 220, 0.55)',
      'rgba(235, 220, 245, 0.55)'
    ];
    this.color = colors[Math.floor(Math.random() * colors.length)];
  }
  update() {
    this.x += this.vx;
    this.y += this.vy;
    if (this.x - this.r < 0 || this.x + this.r > this.w) this.vx *= -1;
    if (this.y - this.r < 0 || this.y + this.r > this.h) this.vy *= -1;
  }
  draw(bCtx) {
    bCtx.beginPath();
    bCtx.arc(this.x, this.y, this.r, 0, Math.PI * 2);
    bCtx.fillStyle = this.color;
    bCtx.fill();
  }
}

let bubblesPool = [];
function initBubbles(count = 16) {
  bubblesPool = [];
  for (let i = 0; i < count; i++) {
    bubblesPool.push(new FloatingBubble(CONFIG.CAMERA_WIDTH, CONFIG.CAMERA_HEIGHT));
  }
}

function drawStarBackground(bgCtx) {
  bgCtx.fillStyle = '#F8F9FA';
  bgCtx.fillRect(0, 0, CONFIG.CAMERA_WIDTH, CONFIG.CAMERA_HEIGHT);

  // Dot grid
  bgCtx.fillStyle = '#E8E3DE';
  const gridGap = 40;
  for (let x = gridGap; x < CONFIG.CAMERA_WIDTH; x += gridGap) {
    for (let y = gridGap; y < CONFIG.CAMERA_HEIGHT; y += gridGap) {
      bgCtx.beginPath();
      bgCtx.arc(x, y, 1.5, 0, Math.PI * 2);
      bgCtx.fill();
    }
  }

  // Floating bubbles
  for (const b of bubblesPool) {
    b.update();
    b.draw(bgCtx);
  }
}

// Confetti & Sparkles Particle System
class ConfettiParticle {
  constructor(w, h, burst = false) {
    this.w_bounds = w;
    this.h_bounds = h;
    this.reset(burst);
  }

  reset(burst = false) {
    this.x = burst ? this.w_bounds / 2 + (Math.random() * 400 - 200) : Math.random() * this.w_bounds;
    this.y = burst ? this.h_bounds / 2 + (Math.random() * 200 - 100) : Math.random() * -this.h_bounds;
    this.size = Math.random() * 9 + 5;
    this.vx = (Math.random() - 0.5) * (burst ? 9 : 3.5);
    this.vy = burst ? -(Math.random() * 7 + 4) : Math.random() * 3.5 + 2.5;
    this.rot = Math.random() * 360;
    this.vrot = (Math.random() - 0.5) * 12;
    this.colors = ['#2ecc71', '#3498db', '#e74c3c', '#f1c40f', '#9b59b6', '#e67e22', '#1abc9c', '#e91e63'];
    this.color = this.colors[Math.floor(Math.random() * this.colors.length)];
    this.shape = Math.random() > 0.4 ? 'rect' : (Math.random() > 0.4 ? 'circle' : 'star');
  }

  update() {
    this.x += this.vx;
    this.y += this.vy;
    this.rot += this.vrot;
    this.vy += 0.08; // gravity

    if (this.y > this.h_bounds) {
      this.reset(false);
    }
  }

  draw(cCtx) {
    cCtx.save();
    cCtx.translate(this.x, this.y);
    cCtx.rotate((this.rot * Math.PI) / 180);
    cCtx.fillStyle = this.color;

    if (this.shape === 'rect') {
      cCtx.fillRect(-this.size / 2, -this.size / 4, this.size, this.size / 2);
    } else if (this.shape === 'circle') {
      cCtx.beginPath();
      cCtx.arc(0, 0, this.size / 2, 0, Math.PI * 2);
      cCtx.fill();
    } else {
      // Star sparkle
      cCtx.beginPath();
      for (let i = 0; i < 5; i++) {
        cCtx.lineTo(Math.cos((18 + i * 72) * 0.01745) * this.size, -Math.sin((18 + i * 72) * 0.01745) * this.size);
        cCtx.lineTo(Math.cos((54 + i * 72) * 0.01745) * (this.size / 2), -Math.sin((54 + i * 72) * 0.01745) * (this.size / 2));
      }
      cCtx.closePath();
      cCtx.fill();
    }
    cCtx.restore();
  }
}

let confettiPool = [];
function initConfetti(count = 120) {
  confettiPool = [];
  for (let i = 0; i < count; i++) {
    confettiPool.push(new ConfettiParticle(CONFIG.CAMERA_WIDTH, CONFIG.CAMERA_HEIGHT, true));
  }
}

function updateAndDrawConfetti(cCtx) {
  for (const p of confettiPool) {
    p.update();
    p.draw(cCtx);
  }
}

// ── Fullscreen Support (Works with both Hand Gesture & Mouse) ─────────────────

function toggleFullscreen() {
  const isFull = document.body.classList.toggle('app-full-screen');
  const fsBtn = document.getElementById('opt-fs');
  if (fsBtn) {
    fsBtn.innerText = isFull ? 'WINDOWED' : 'FULLSCREEN';
  }

  const elem = document.documentElement;
  // Try native browser fullscreen if allowed by user activation
  if (isFull) {
    if (!document.fullscreenElement && !document.webkitFullscreenElement) {
      if (elem.requestFullscreen) {
        elem.requestFullscreen().catch(() => {});
      } else if (elem.webkitRequestFullscreen) {
        elem.webkitRequestFullscreen();
      }
    }
  } else {
    if (document.fullscreenElement || document.webkitFullscreenElement) {
      if (document.exitFullscreen) {
        document.exitFullscreen().catch(() => {});
      } else if (document.webkitExitFullscreen) {
        document.webkitExitFullscreen();
      }
    }
  }
}

// ── App Init ────────────────────────────────────────────────────────────────

async function init() {
  loadLeaderboard();
  initBubbles(18);

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
    toggleFullscreen();
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
    } else if (e.key === 'f' || e.key === 'F') {
      toggleFullscreen();
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
  const tbody = document.getElementById('leaderboard-rows');
  if (!tbody) return;
  tbody.innerHTML = '';

  // Sort by lowest time (Fastest completion)
  leaderboard.sort((a, b) => a.time - b.time);

  if (leaderboard.length === 0) {
    tbody.innerHTML = '<tr><td colspan="5" style="text-align:center; padding: 20px; color:#888;">No games completed yet. Be the first!</td></tr>';
    return;
  }

  leaderboard.slice(0, 8).forEach((item, index) => {
    const tr = document.createElement('tr');
    let rankBadgeClass = 'rank-badge';
    let medal = `${index + 1}`;
    if (index === 0) { rankBadgeClass += ' rank-1'; medal = '🥇 1'; }
    else if (index === 1) { rankBadgeClass += ' rank-2'; medal = '🥈 2'; }
    else if (index === 2) { rankBadgeClass += ' rank-3'; medal = '🥉 3'; }

    const isCurrent = item.name.toUpperCase() === playerName.toUpperCase();
    if (isCurrent) tr.style.background = 'rgba(46, 204, 113, 0.08)';

    tr.innerHTML = `
      <td><span class="${rankBadgeClass}">${medal}</span></td>
      <td><strong>${item.name.toUpperCase()}</strong> ${isCurrent ? '<span style="font-size:0.75rem; color:#2ecc71;">(You)</span>' : ''}</td>
      <td class="green-text" style="font-weight:800; font-size:1.1rem;">${item.score !== undefined ? item.score : 0}</td>
      <td class="blue-text" style="font-weight:800;">${item.time ? item.time.toFixed(1) + 's' : '--'} ${index === 0 ? '⚡ (FASTEST)' : ''}</td>
      <td style="color:#888; font-size:0.85rem;">${item.date || 'Today'}</td>
    `;
    tbody.appendChild(tr);
  });
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
  else if (newState === 'WIN') {
    document.getElementById('screen-win').classList.add('active');
    initConfetti(100);
  }
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
  const best = getBestTime();
  document.getElementById('hud-best').innerText = best ? best.toFixed(1) + 's' : '--';
  document.querySelector('.opt-status').innerHTML = `Opacity: ${Math.round(camOpacity * 100)}%<br>USER PREVIEW: ${isCamOn ? 'ON' : 'OFF'}`;
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
  const prevBest = getBestTime();
  const isNewRecord = !prevBest || finalTimeSec < prevBest;

  // Add record to leaderboard
  const now = new Date();
  const dateStr = `${now.getMonth() + 1}/${now.getDate()}`;
  leaderboard.push({
    name: playerName.toUpperCase(),
    time: finalTimeSec,
    score: score,
    date: dateStr
  });
  leaderboard.sort((a, b) => a.time - b.time);
  saveLeaderboard();

  // Display Win Board details matching Python layout
  const m = String(Math.floor(finalTimeSec / 60)).padStart(2, '0');
  const s = String(Math.floor(finalTimeSec % 60)).padStart(2, '0');
  
  const pEl = document.getElementById('win-player');
  if (pEl) pEl.innerText = playerName.toUpperCase();
  
  const scEl = document.getElementById('win-score');
  if (scEl) scEl.innerText = score;
  
  const tEl = document.getElementById('win-time');
  if (tEl) tEl.innerText = `${m}:${s}`;
  
  const bestScEl = document.getElementById('win-best-score');
  if (bestScEl) {
    const highestScore = Math.max(...leaderboard.map(item => item.score || 0), score);
    bestScEl.innerText = highestScore;
  }
  
  const bestTimeEl = document.getElementById('win-best-time');
  if (bestTimeEl) {
    bestTimeEl.innerText = leaderboard[0].time.toFixed(1) + 's';
  }

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

  if (gameState === 'WIN') {
    // Draw animated floating bubbles and grid background
    drawStarBackground(ctx);
    // Draw continuous confetti & sparkles in a loop
    updateAndDrawConfetti(cursorCtx);
  } else if (isCamOn && video.readyState === 4) {
    // Background camera feed with opacity
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
