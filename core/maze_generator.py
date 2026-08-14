# core/maze_generator.py
import random
import cv2
import numpy as np
import config

class MazeGenerator:
    def __init__(self, rows, cols, cell_size, offset_x, offset_y):
        self.rows = rows
        self.cols = cols
        self.cell_size = cell_size
        self.offset_x = offset_x
        self.offset_y = offset_y
        self.grid = []
        self.start_cell = (0, 0)
        self.end_cell = (rows - 1, cols - 1)
        self.walls = []  # Collision walls as line segments
        self.generate_maze()

    def generate_maze(self):
        # DFS maze generation
        self.grid = [
            [{'N': True, 'S': True, 'E': True, 'W': True, 'visited': False}
             for _ in range(self.cols)]
            for _ in range(self.rows)
        ]

        stack = []
        current = (0, 0)
        self.grid[0][0]['visited'] = True

        while True:
            r, c = current
            neighbors = []
            if r > 0 and not self.grid[r-1][c]['visited']:
                neighbors.append((r-1, c, 'N', 'S'))
            if r < self.rows - 1 and not self.grid[r+1][c]['visited']:
                neighbors.append((r+1, c, 'S', 'N'))
            if c > 0 and not self.grid[r][c-1]['visited']:
                neighbors.append((r, c-1, 'W', 'E'))
            if c < self.cols - 1 and not self.grid[r][c+1]['visited']:
                neighbors.append((r, c+1, 'E', 'W'))

            if neighbors:
                nr, nc, dir1, dir2 = random.choice(neighbors)
                stack.append(current)
                self.grid[r][c][dir1] = False
                self.grid[nr][nc][dir2] = False
                self.grid[nr][nc]['visited'] = True
                current = (nr, nc)
            elif stack:
                current = stack.pop()
            else:
                break

        # Make it a braid maze (more difficult, multiple paths)
        # Randomly remove some internal walls to create loops
        remove_percentage = 0.25 # Remove 25% of the walls that could be removed
        for r in range(1, self.rows - 1):
            for c in range(1, self.cols - 1):
                if random.random() < remove_percentage:
                    # Pick a random wall to remove if it exists
                    wall_to_remove = random.choice(['N', 'S', 'E', 'W'])
                    if self.grid[r][c][wall_to_remove]:
                        self.grid[r][c][wall_to_remove] = False
                        if wall_to_remove == 'N':
                            self.grid[r-1][c]['S'] = False
                        elif wall_to_remove == 'S':
                            self.grid[r+1][c]['N'] = False
                        elif wall_to_remove == 'E':
                            self.grid[r][c+1]['W'] = False
                        elif wall_to_remove == 'W':
                            self.grid[r][c-1]['E'] = False

        self.extract_walls()

        # Start on left column, End on right column
        self.start_cell = (random.randint(0, self.rows - 1), 0)
        self.end_cell   = (random.randint(0, self.rows - 1), self.cols - 1)

    def extract_walls(self):
        self.walls = []
        for r in range(self.rows):
            for c in range(self.cols):
                cell = self.grid[r][c]
                x  = self.offset_x + c * self.cell_size
                y  = self.offset_y + r * self.cell_size
                cs = self.cell_size
                if cell['N']:
                    self.walls.append(((x, y), (x + cs, y)))
                if cell['S']:
                    self.walls.append(((x, y + cs), (x + cs, y + cs)))
                if cell['W']:
                    self.walls.append(((x, y), (x, y + cs)))
                if cell['E']:
                    self.walls.append(((x + cs, y), (x + cs, y + cs)))

    def is_wall_between(self, r1, c1, r2, c2):
        """Check if there is a wall between two adjacent cells."""
        if r2 == r1 - 1:  # Moving North
            return self.grid[r1][c1]['N']
        if r2 == r1 + 1:  # Moving South
            return self.grid[r1][c1]['S']
        if c2 == c1 - 1:  # Moving West
            return self.grid[r1][c1]['W']
        if c2 == c1 + 1:  # Moving East
            return self.grid[r1][c1]['E']
        return True  # Non-adjacent = treat as wall

    def cell_center(self, r, c):
        """Pixel center of a maze cell."""
        cx = self.offset_x + c * self.cell_size + self.cell_size // 2
        cy = self.offset_y + r * self.cell_size + self.cell_size // 2
        return (cx, cy)

    def pixel_to_cell(self, px, py):
        """Convert pixel coords to (row, col). Returns None if outside maze."""
        col = (px - self.offset_x) // self.cell_size
        row = (py - self.offset_y) // self.cell_size
        if 0 <= row < self.rows and 0 <= col < self.cols:
            return (row, col)
        return None

    def draw(self, img, color_wall, color_start, color_end,
             player_cell=None, visited_cells=None):
        cs = self.cell_size

        # Draw visited trail
        if visited_cells:
            for (vr, vc) in visited_cells:
                vx = self.offset_x + vc * cs
                vy = self.offset_y + vr * cs
                overlay = img.copy()
                cv2.rectangle(overlay, (vx + 2, vy + 2),
                              (vx + cs - 2, vy + cs - 2), config.COLOR_PATH, -1)
                cv2.addWeighted(overlay, 0.4, img, 0.6, 0, img)

        # Draw walls
        for wall in self.walls:
            pt1, pt2 = wall
            cv2.line(img, pt1, pt2, color_wall, 5, cv2.LINE_AA)

        # Draw start cell
        sr, sc = self.start_cell
        sx = self.offset_x + sc * cs
        sy = self.offset_y + sr * cs
        cv2.rectangle(img, (sx + 2, sy + 2), (sx + cs - 2, sy + cs - 2), color_start, -1)
        draw_label(img, "START", (sx + cs // 2, sy + cs // 2), scale=0.4)

        # Draw end cell
        er, ec = self.end_cell
        ex = self.offset_x + ec * cs
        ey = self.offset_y + er * cs
        cv2.rectangle(img, (ex + 2, ey + 2), (ex + cs - 2, ey + cs - 2), color_end, -1)
        draw_label(img, "END", (ex + cs // 2, ey + cs // 2), scale=0.45)

        # Draw player (modern slate-blue box)
        if player_cell:
            pr, pc = player_cell
            px = self.offset_x + pc * cs
            py = self.offset_y + pr * cs
            pad = 6
            cv2.rectangle(img,
                          (px + pad, py + pad),
                          (px + cs - pad, py + cs - pad),
                          config.COLOR_PLAYER, -1)
            # Subtle inner border
            cv2.rectangle(img,
                          (px + pad, py + pad),
                          (px + cs - pad, py + cs - pad),
                          (255, 255, 255), 1, cv2.LINE_AA)

    def get_start_rect(self):
        sr, sc = self.start_cell
        sx = self.offset_x + sc * self.cell_size
        sy = self.offset_y + sr * self.cell_size
        return (sx, sy, self.cell_size, self.cell_size)

    def get_end_rect(self):
        er, ec = self.end_cell
        ex = self.offset_x + ec * self.cell_size
        ey = self.offset_y + er * self.cell_size
        return (ex, ey, self.cell_size, self.cell_size)


def draw_label(img, text, center, scale=0.4, color=(0, 0, 0)):
    font = cv2.FONT_HERSHEY_SIMPLEX
    tw, th = cv2.getTextSize(text, font, scale, 1)[0]
    tx = center[0] - tw // 2
    ty = center[1] + th // 2
    cv2.putText(img, text, (tx, ty), font, scale, color, 1, cv2.LINE_AA)
