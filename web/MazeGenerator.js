export class MazeGenerator {
  constructor(rows, cols, cellSize, offsetX, offsetY) {
    this.rows = rows;
    this.cols = cols;
    this.cellSize = cellSize;
    this.offsetX = offsetX;
    this.offsetY = offsetY;
    this.grid = [];
    this.startCell = { r: 0, c: 0 };
    this.endCell = { r: rows - 1, c: cols - 1 };
    this.walls = [];
    this.generateMaze();
  }

  generateMaze() {
    this.grid = Array.from({ length: this.rows }, () =>
      Array.from({ length: this.cols }, () => ({
        N: true, S: true, E: true, W: true, visited: false
      }))
    );

    const stack = [];
    let current = { r: 0, c: 0 };
    this.grid[0][0].visited = true;

    while (true) {
      const { r, c } = current;
      const neighbors = [];

      if (r > 0 && !this.grid[r - 1][c].visited) neighbors.push({ r: r - 1, c, dir1: 'N', dir2: 'S' });
      if (r < this.rows - 1 && !this.grid[r + 1][c].visited) neighbors.push({ r: r + 1, c, dir1: 'S', dir2: 'N' });
      if (c > 0 && !this.grid[r][c - 1].visited) neighbors.push({ r, c: c - 1, dir1: 'W', dir2: 'E' });
      if (c < this.cols - 1 && !this.grid[r][c + 1].visited) neighbors.push({ r, c: c + 1, dir1: 'E', dir2: 'W' });

      if (neighbors.length > 0) {
        const next = neighbors[Math.floor(Math.random() * neighbors.length)];
        stack.push(current);
        this.grid[r][c][next.dir1] = false;
        this.grid[next.r][next.c][next.dir2] = false;
        this.grid[next.r][next.c].visited = true;
        current = { r: next.r, c: next.c };
      } else if (stack.length > 0) {
        current = stack.pop();
      } else {
        break;
      }
    }

    // Braid maze (remove some dead ends)
    const removePercentage = 0.25;
    const dirs = ['N', 'S', 'E', 'W'];
    for (let r = 1; r < this.rows - 1; r++) {
      for (let c = 1; c < this.cols - 1; c++) {
        if (Math.random() < removePercentage) {
          const wallToRemove = dirs[Math.floor(Math.random() * dirs.length)];
          if (this.grid[r][c][wallToRemove]) {
            this.grid[r][c][wallToRemove] = false;
            if (wallToRemove === 'N') this.grid[r - 1][c]['S'] = false;
            else if (wallToRemove === 'S') this.grid[r + 1][c]['N'] = false;
            else if (wallToRemove === 'E') this.grid[r][c + 1]['W'] = false;
            else if (wallToRemove === 'W') this.grid[r][c - 1]['E'] = false;
          }
        }
      }
    }

    this.extractWalls();

    // Start on left col, End on right col
    this.startCell = { r: Math.floor(Math.random() * this.rows), c: 0 };
    this.endCell = { r: Math.floor(Math.random() * this.rows), c: this.cols - 1 };
  }

  extractWalls() {
    this.walls = [];
    for (let r = 0; r < this.rows; r++) {
      for (let c = 0; c < this.cols; c++) {
        const cell = this.grid[r][c];
        const x = this.offsetX + c * this.cellSize;
        const y = this.offsetY + r * this.cellSize;
        const cs = this.cellSize;

        if (cell.N) this.walls.push({ x1: x, y1: y, x2: x + cs, y2: y });
        if (cell.S) this.walls.push({ x1: x, y1: y + cs, x2: x + cs, y2: y + cs });
        if (cell.W) this.walls.push({ x1: x, y1: y, x2: x, y2: y + cs });
        if (cell.E) this.walls.push({ x1: x + cs, y1: y, x2: x + cs, y2: y + cs });
      }
    }
  }

  isWallBetween(r1, c1, r2, c2) {
    if (r2 === r1 - 1) return this.grid[r1][c1].N;
    if (r2 === r1 + 1) return this.grid[r1][c1].S;
    if (c2 === c1 - 1) return this.grid[r1][c1].W;
    if (c2 === c1 + 1) return this.grid[r1][c1].E;
    return true;
  }

  pixelToCell(px, py) {
    const col = Math.floor((px - this.offsetX) / this.cellSize);
    const row = Math.floor((py - this.offsetY) / this.cellSize);
    if (row >= 0 && row < this.rows && col >= 0 && col < this.cols) {
      return { r: row, c: col };
    }
    return null;
  }

  draw(ctx, config, playerCell, pathCells) {
    const cs = this.cellSize;

    // Draw path
    if (pathCells && pathCells.length > 0) {
      ctx.fillStyle = config.COLOR_PATH;
      for (const p of pathCells) {
        const vx = this.offsetX + p.c * cs;
        const vy = this.offsetY + p.r * cs;
        ctx.fillRect(vx + 2, vy + 2, cs - 4, cs - 4);
      }
    }

    // Draw start cell
    const sx = this.offsetX + this.startCell.c * cs;
    const sy = this.offsetY + this.startCell.r * cs;
    ctx.fillStyle = config.COLOR_START;
    ctx.fillRect(sx + 2, sy + 2, cs - 4, cs - 4);

    // Draw end cell
    const ex = this.offsetX + this.endCell.c * cs;
    const ey = this.offsetY + this.endCell.r * cs;
    ctx.fillStyle = config.COLOR_END;
    ctx.fillRect(ex + 2, ey + 2, cs - 4, cs - 4);

    // Draw player
    if (playerCell) {
      const px = this.offsetX + playerCell.c * cs;
      const py = this.offsetY + playerCell.r * cs;
      ctx.fillStyle = config.COLOR_PLAYER;
      ctx.fillRect(px + 6, py + 6, cs - 12, cs - 12);
    }

    // Draw walls
    ctx.strokeStyle = config.COLOR_WALL;
    ctx.lineWidth = 5;
    ctx.lineCap = 'round';
    ctx.beginPath();
    for (const w of this.walls) {
      ctx.moveTo(w.x1, w.y1);
      ctx.lineTo(w.x2, w.y2);
    }
    ctx.stroke();
  }
}
