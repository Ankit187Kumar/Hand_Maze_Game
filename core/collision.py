# core/collision.py
import numpy as np

def point_in_rect(pt, rect):
    x, y = pt
    rx, ry, rw, rh = rect
    return rx <= x <= rx + rw and ry <= y <= ry + rh

def line_intersection(p1, p2, p3, p4):
    # Returns True if line segment p1-p2 intersects p3-p4
    # Using cross products
    def ccw(A, B, C):
        return (C[1]-A[1]) * (B[0]-A[0]) > (B[1]-A[1]) * (C[0]-A[0])
    
    return ccw(p1, p3, p4) != ccw(p2, p3, p4) and ccw(p1, p2, p3) != ccw(p1, p2, p4)

def check_segment_wall_collision(p1, p2, walls):
    for wall in walls:
        wp1, wp2 = wall
        if line_intersection(p1, p2, wp1, wp2):
            return True
    return False
