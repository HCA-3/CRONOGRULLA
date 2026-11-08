import math
import numpy as np

def test_projection():
    yaw = 0
    pitch = 0
    zoom = 1.05
    cx = 250
    cy = 250
    fov = 650
    h = 500
    target_h = int(h * 0.88 * zoom) # ~462 px
    print(f"Canvas size: 500x500, target_h={target_h}")
    # Image top: cy - target_h/2 = 250 - 231 = 19
    # Image bottom: cy + target_h/2 = 250 + 231 = 481
    
    # Proportions from image:
    # Neck: 22% of height -> y_px = 19 + 462*0.22 = 120.6 -> offset from cy = -129.4
    # Shoulders: 27% -> y_px = 19 + 462*0.27 = 143.7 -> offset from cy = -106.3
    # Elbows: 51% -> y_px = 19 + 462*0.51 = 254.6 -> offset from cy = +4.6
    # Wrists: 72% -> y_px = 19 + 462*0.72 = 351.6 -> offset from cy = +101.6
    
    # In project_3d:
    # scale = (fov / (fov + rz)) * zoom
    # v = cy + ry * scale
    # ry = (v - cy) / zoom
    print("Derived 3D y coordinates:")
    print("Neck y:", (-129.4) / zoom)
    print("Shoulders y:", (-106.3) / zoom)
    print("Elbows y:", (4.6) / zoom)
    print("Wrists y:", (101.6) / zoom)

test_projection()

