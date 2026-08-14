# core/path_manager.py
import cv2
import numpy as np

class PathManager:
    def __init__(self, color, min_dist, backward_thresh):
        self.path = []
        self.color = color
        self.min_dist = min_dist
        self.backward_thresh = backward_thresh

    def add_point(self, pt):
        if not self.path:
            self.path.append(pt)
            return True
            
        last_pt = self.path[-1]
        dist = np.hypot(pt[0] - last_pt[0], pt[1] - last_pt[1])
        
        if dist >= self.min_dist:
            # Check for backward movement
            # We look back in the path to see if the new point is very close to an older point
            for i in range(len(self.path) - 2, -1, -1):
                old_pt = self.path[i]
                d = np.hypot(pt[0] - old_pt[0], pt[1] - old_pt[1])
                if d < self.backward_thresh:
                    # Erase path up to this point
                    self.path = self.path[:i+1]
                    return False # No new point added, but path modified
            
            self.path.append(pt)
            return True
            
        return False

    def clear(self):
        self.path = []

    def draw(self, img):
        if len(self.path) > 1:
            pts = np.array(self.path, np.int32)
            pts = pts.reshape((-1, 1, 2))
            cv2.polylines(img, [pts], False, self.color, 4)
            
        if self.path:
            cv2.circle(img, self.path[-1], 6, self.color, -1)
