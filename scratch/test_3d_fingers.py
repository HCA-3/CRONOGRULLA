import math
import numpy as np

def compute_hand_and_fingers(wrist_pos, hand_pos, is_right=True, fold_factor=0.0):
    wx, wy, wz = wrist_pos
    hx, hy, hz = hand_pos
    
    # Hand direction vector
    dx, dy, dz = hx - wx, hy - wy, hz - wz
    len_d = math.sqrt(dx*dx + dy*dy + dz*dz) or 1.0
    fx, fy, fz = dx/len_d, dy/len_d, dz/len_d
    
    # Lateral vector across palm (X/Z plane roughly)
    sign = 1.0 if is_right else -1.0
    # Right palm faces inward and down towards table
    rx, ry, rz = -sign * fz, 0, sign * fx
    len_r = math.sqrt(rx*rx + ry*ry + rz*rz) or 1.0
    rx, ry, rz = rx/len_r, ry/len_r, rz/len_r
    
    # Normal to palm
    nx = fy*rz - fz*ry
    ny = fz*rx - fx*rz
    nz = fx*ry - fy*rx

    # Palm perimeter ring (metacarpus)
    palm_pts = [
        (wx - rx*8, wy, wz - rz*8),
        (wx + rx*8, wy, wz + rz*8),
        (hx + rx*12, hy, hz + rz*12),
        (hx - rx*10, hy, hz - rz*10)
    ]
    
    # 5 Fingers definition
    # Finger lengths: thumb ~18, index ~22, middle ~25, ring ~22, pinky ~16
    fingers = {}
    
    # 1. Thumb (Pulgar): opposes other fingers
    # Moves inward towards index tip during fold_factor (pinch)
    pinch_curl = fold_factor * 12.0 if is_right else 0.0
    thumb_base = (wx - rx*6 + fx*6, wy + fy*6, wz - rz*6 + fz*6)
    thumb_mid  = (thumb_base[0] - rx*10 + fx*12 - nx*4, 
                  thumb_base[1] + fy*12, 
                  thumb_base[2] - rz*10 + fz*12 - nz*4)
    thumb_tip  = (thumb_mid[0] + rx*pinch_curl + fx*8 + nx*4, 
                  thumb_mid[1] + fy*8 + (fold_factor * 6.0), 
                  thumb_mid[2] + rz*pinch_curl + fz*8 + nz*4)
    fingers["pulgar"] = [thumb_base, thumb_mid, thumb_tip]
    
    # 2. Index (Índice): active pinch finger
    index_base = (hx - rx*6, hy, hz - rz*6)
    index_mid  = (index_base[0] + fx*12 - rx*(fold_factor*4.0), 
                  index_base[1] + fy*12 + (fold_factor*4.0), 
                  index_base[2] + fz*12 - rz*(fold_factor*4.0))
    index_tip  = (index_mid[0] + fx*10 - rx*(fold_factor*8.0), 
                  index_mid[1] + fy*10 + (fold_factor*8.0), 
                  index_mid[2] + fz*10 - rz*(fold_factor*8.0))
    fingers["indice"] = [index_base, index_mid, index_tip]
    
    # 3. Middle (Medio): longest, creases fold
    mid_base = (hx - rx*1, hy, hz - rz*1)
    mid_mid  = (mid_base[0] + fx*14, mid_base[1] + fy*14 + (fold_factor*5.0), mid_base[2] + fz*14)
    mid_tip  = (mid_mid[0] + fx*12, mid_mid[1] + fy*12 + (fold_factor*7.0), mid_mid[2] + fz*12)
    fingers["medio"] = [mid_base, mid_mid, mid_tip]
    
    # 4. Ring (Anular)
    ring_base = (hx + rx*4, hy, hz + rz*4)
    ring_mid  = (ring_base[0] + fx*12, ring_base[1] + fy*12 + (fold_factor*4.0), ring_base[2] + fz*12)
    ring_tip  = (ring_mid[0] + fx*10, ring_mid[1] + fy*10 + (fold_factor*5.0), ring_mid[2] + fz*10)
    fingers["anular"] = [ring_base, ring_mid, ring_tip]
    
    # 5. Pinky (Meñique)
    pinky_base = (hx + rx*8, hy, hz + rz*8)
    pinky_mid  = (pinky_base[0] + fx*9, pinky_base[1] + fy*9 + (fold_factor*3.0), pinky_base[2] + fz*9)
    pinky_tip  = (pinky_mid[0] + fx*7, pinky_mid[1] + fy*7 + (fold_factor*4.0), pinky_mid[2] + fz*7)
    fingers["menique"] = [pinky_base, pinky_mid, pinky_tip]
    
    return palm_pts, fingers

w_pos = (100, 100, 50)
h_pos = (80, 140, 70)
palm, fng = compute_hand_and_fingers(w_pos, h_pos, is_right=True, fold_factor=1.0)
print(f"Palm polygon points: {len(palm)}")
print(f"Fingers generated: {list(fng.keys())}")
for f_name, pts in fng.items():
    print(f"  {f_name}: base={pts[0]}, tip={pts[2]}")
print("Finger kinematics calculation succeeded!")

