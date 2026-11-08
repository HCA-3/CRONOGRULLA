import math
import numpy as np

def compute_hand_and_fingers(wrist_pos, hand_pos, is_right=True, fold_factor=0.0):
    wx, wy, wz = wrist_pos
    hx, hy, hz = hand_pos
    
    dx, dy, dz = hx - wx, hy - wy, hz - wz
    len_d = math.sqrt(dx*dx + dy*dy + dz*dz) or 1.0
    fx, fy, fz = dx/len_d, dy/len_d, dz/len_d
    
    sign = 1.0 if is_right else -1.0
    rx, ry, rz = -sign * fz, 0, sign * fx
    len_r = math.sqrt(rx*rx + ry*ry + rz*rz) or 1.0
    rx, ry, rz = rx/len_r, ry/len_r, rz/len_r
    
    nx = fy*rz - fz*ry
    ny = fz*rx - fx*rz
    nz = fx*ry - fy*rx

    # Palm perimeter ring (metacarpus)
    palm_pts = [
        (wx - rx*6, wy, wz - rz*6),
        (wx + rx*6, wy, wz + rz*6),
        (hx + rx*10, hy, hz + rz*10),
        (hx - rx*8, hy, hz - rz*8)
    ]
    
    fingers = {}
    
    # 1. Thumb (Pulgar)
    pinch_curl = fold_factor * 10.0 if is_right else 0.0
    thumb_base = (wx - rx*5 + fx*5, wy + fy*5, wz - rz*5 + fz*5)
    thumb_mid  = (thumb_base[0] - rx*8 + fx*10 - nx*3, 
                  thumb_base[1] + fy*10, 
                  thumb_base[2] - rz*8 + fz*10 - nz*3)
    thumb_tip  = (thumb_mid[0] + rx*pinch_curl + fx*7 + nx*3, 
                  thumb_mid[1] + fy*7 + (fold_factor * 5.0), 
                  thumb_mid[2] + rz*pinch_curl + fz*7 + nz*3)
    fingers["pulgar"] = [thumb_base, thumb_mid, thumb_tip]
    
    # 2. Index (Índice)
    index_base = (hx - rx*5, hy, hz - rz*5)
    index_mid  = (index_base[0] + fx*10 - rx*(fold_factor*3.0), 
                  index_base[1] + fy*10 + (fold_factor*3.0), 
                  index_base[2] + fz*10 - rz*(fold_factor*3.0))
    index_tip  = (index_mid[0] + fx*8 - rx*(fold_factor*6.0), 
                  index_mid[1] + fy*8 + (fold_factor*6.0), 
                  index_mid[2] + fz*8 - rz*(fold_factor*6.0))
    fingers["indice"] = [index_base, index_mid, index_tip]
    
    # 3. Middle (Medio)
    mid_base = (hx - rx*1, hy, hz - rz*1)
    mid_mid  = (mid_base[0] + fx*12, mid_base[1] + fy*12 + (fold_factor*4.0), mid_base[2] + fz*12)
    mid_tip  = (mid_mid[0] + fx*10, mid_mid[1] + fy*10 + (fold_factor*5.0), mid_mid[2] + fz*10)
    fingers["medio"] = [mid_base, mid_mid, mid_tip]
    
    # 4. Ring (Anular)
    ring_base = (hx + rx*3, hy, hz + rz*3)
    ring_mid  = (ring_base[0] + fx*10, ring_base[1] + fy*10 + (fold_factor*3.0), ring_base[2] + fz*10)
    ring_tip  = (ring_mid[0] + fx*8, ring_mid[1] + fy*8 + (fold_factor*4.0), ring_mid[2] + fz*8)
    fingers["anular"] = [ring_base, ring_mid, ring_tip]
    
    # 5. Pinky (Meñique)
    pinky_base = (hx + rx*7, hy, hz + rz*7)
    pinky_mid  = (pinky_base[0] + fx*8, pinky_base[1] + fy*8 + (fold_factor*2.0), pinky_base[2] + fz*8)
    pinky_tip  = (pinky_mid[0] + fx*6, pinky_mid[1] + fy*6 + (fold_factor*3.0), pinky_mid[2] + fz*6)
    fingers["menique"] = [pinky_base, pinky_mid, pinky_tip]
    
    return palm_pts, fingers

w_pos_r = (80, 160, 50)
h_pos_r = (65, 190, 60)
palm_r, fng_r = compute_hand_and_fingers(w_pos_r, h_pos_r, is_right=True, fold_factor=0.8)

# Dedicated hotspot position for dedos_r
pinch_center = (
    (fng_r["pulgar"][-1][0] + fng_r["indice"][-1][0]) / 2.0,
    (fng_r["pulgar"][-1][1] + fng_r["indice"][-1][1]) / 2.0,
    (fng_r["pulgar"][-1][2] + fng_r["indice"][-1][2]) / 2.0
)
print("Pinch center for dedos_r:", pinch_center)
print("Hand pos for mano_r:", h_pos_r)
print("Wrist pos for muñeca_r:", w_pos_r)

