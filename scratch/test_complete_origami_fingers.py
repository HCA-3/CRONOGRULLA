import tkinter as tk
import math
import numpy as np

root = tk.Tk()
root.title("Verification - 5 Fingers + Coordinated Origami Kinematics")
root.geometry("750x800")

canvas = tk.Canvas(root, bg="#070d19", highlightthickness=0)
canvas.pack(fill="both", expand=True)

yaw = math.radians(28)
pitch = math.radians(-6)
zoom_level = 1.05

def rotate_point_3d(x, y, z):
    cos_y = math.cos(yaw)
    sin_y = math.sin(yaw)
    x1 = x * cos_y - z * sin_y
    z1 = x * sin_y + z * cos_y
    
    cos_p = math.cos(pitch)
    sin_p = math.sin(pitch)
    y2 = y * cos_p - z1 * sin_p
    z2 = y * sin_p + z1 * cos_p
    return x1, y2, z2

def project_3d(x, y, z, cx, cy, fov=650):
    rx, ry, rz = rotate_point_3d(x, y, z)
    scale = (fov / (fov + rz)) * zoom_level
    u = cx + rx * scale
    v = cy + ry * scale
    return u, v, rz

def compute_hand_and_fingers(wrist_pos, hand_pos, is_right=True, fold_factor=0.0):
    wx, wy, wz = wrist_pos
    hx, hy, hz = hand_pos
    
    dx, dy, dz = hx - wx, hy - wy, hz - wz
    len_d = math.sqrt(dx*dx + dy*dy + dz*dz) or 1.0
    fx, fy, fz = dx / len_d, dy / len_d, dz / len_d
    
    sign = 1.0 if is_right else -1.0
    rx, ry, rz = -sign * fz, 0.0, sign * fx
    len_r = math.sqrt(rx*rx + ry*ry + rz*rz) or 1.0
    rx, ry, rz = rx / len_r, ry / len_r, rz / len_r
    
    nx = fy * rz - fz * ry
    ny = fz * rx - fx * rz
    nz = fx * ry - fy * rx
    len_n = math.sqrt(nx*nx + ny*ny + nz*nz) or 1.0
    nx, ny, nz = nx / len_n, ny / len_n, nz / len_n

    palm_pts = [
        (wx - rx * 6.0, wy, wz - rz * 6.0),
        (wx + rx * 6.0, wy, wz + rz * 6.0),
        (hx + rx * 10.0, hy, hz + rz * 10.0),
        (hx - rx * 8.0, hy, hz - rz * 8.0)
    ]
    
    fingers = {}
    
    # 1. Pulgar (Thumb)
    pinch_curl = fold_factor * 11.0 if is_right else 0.0
    thumb_base = (wx - rx * 5.0 + fx * 5.0, wy + fy * 5.0, wz - rz * 5.0 + fz * 5.0)
    thumb_mid  = (thumb_base[0] - rx * 8.0 + fx * 10.0 - nx * 3.0, 
                  thumb_base[1] + fy * 10.0, 
                  thumb_base[2] - rz * 8.0 + fz * 10.0 - nz * 3.0)
    thumb_tip  = (thumb_mid[0] + rx * pinch_curl + fx * 7.0 + nx * (3.0 if is_right else 0.0), 
                  thumb_mid[1] + fy * 7.0 + (fold_factor * 5.0 if is_right else 0.0), 
                  thumb_mid[2] + rz * pinch_curl + fz * 7.0 + nz * (3.0 if is_right else 0.0))
    fingers["pulgar"] = [thumb_base, thumb_mid, thumb_tip]
    
    # 2. Índice (Index)
    curl_idx = fold_factor * 6.0 if is_right else 0.0
    idx_base = (hx - rx * 5.0, hy, hz - rz * 5.0)
    idx_mid  = (idx_base[0] + fx * 10.0 - rx * (curl_idx * 0.5), 
                idx_base[1] + fy * 10.0 + (curl_idx * 0.5), 
                idx_base[2] + fz * 10.0 - rz * (curl_idx * 0.5))
    idx_tip  = (idx_mid[0] + fx * 8.0 - rx * curl_idx, 
                idx_mid[1] + fy * 8.0 + (curl_idx * 1.1), 
                idx_mid[2] + fz * 8.0 - rz * curl_idx)
    fingers["indice"] = [idx_base, idx_mid, idx_tip]
    
    # 3. Medio (Middle)
    mid_base = (hx - rx * 1.0, hy, hz - rz * 1.0)
    mid_mid  = (mid_base[0] + fx * 12.0, mid_base[1] + fy * 12.0 + (fold_factor * 3.5 if is_right else 0.0), mid_base[2] + fz * 12.0)
    mid_tip  = (mid_mid[0] + fx * 10.0, mid_mid[1] + fy * 10.0 + (fold_factor * 4.5 if is_right else 0.0), mid_mid[2] + fz * 10.0)
    fingers["medio"] = [mid_base, mid_mid, mid_tip]
    
    # 4. Anular (Ring)
    ring_base = (hx + rx * 3.0, hy, hz + rz * 3.0)
    ring_mid  = (ring_base[0] + fx * 10.0, ring_base[1] + fy * 10.0 + (fold_factor * 2.8 if is_right else 0.0), ring_base[2] + fz * 10.0)
    ring_tip  = (ring_mid[0] + fx * 8.0, ring_mid[1] + fy * 8.0 + (fold_factor * 3.8 if is_right else 0.0), ring_mid[2] + fz * 8.0)
    fingers["anular"] = [ring_base, ring_mid, ring_tip]
    
    # 5. Meñique (Pinky)
    pinky_base = (hx + rx * 7.0, hy, hz + rz * 7.0)
    pinky_mid  = (pinky_base[0] + fx * 8.0, pinky_base[1] + fy * 8.0 + (fold_factor * 2.0 if is_right else 0.0), pinky_base[2] + fz * 8.0)
    pinky_tip  = (pinky_mid[0] + fx * 6.0, pinky_mid[1] + fy * 6.0 + (fold_factor * 2.5 if is_right else 0.0), pinky_mid[2] + fz * 6.0)
    fingers["menique"] = [pinky_base, pinky_mid, pinky_tip]
    
    return palm_pts, fingers

def render(t=0.0):
    canvas.delete("all")
    w, h = 750, 800
    cx, cy = w / 2.0, h / 2.0 - 20
    
    for x in range(0, w, 40): canvas.create_line(x, 0, x, h, fill="#0c1626")
    for y in range(0, h, 40): canvas.create_line(0, y, w, y, fill="#0c1626")
    
    fold_factor = (math.sin(t * 2.2) + 1.0) / 2.0
    sh_w = 100.0
    sh_drop = 65.0
    
    # 1. Hombro derecho se mueve en X, Y, Z
    sh_delta_x = -fold_factor * 14.0
    sh_delta_y = fold_factor * 7.0
    sh_delta_z = fold_factor * 16.0
    
    sh_pos_l = (-sh_w, -sh_drop, 0)
    sh_pos_r = (sh_w + sh_delta_x, -sh_drop + sh_delta_y, sh_delta_z)
    
    # 2. Codo derecho se mueve
    cur_ang_r = 108.0 - (fold_factor * 28.0)
    rad_r = math.radians(cur_ang_r)
    elbow_pos_l = (sh_pos_l[0] - 22, sh_pos_l[1] + 85, 20)
    elbow_pos_r = (sh_pos_r[0] + 20.0 - (fold_factor * 16.0), 
                   sh_pos_r[1] + 85.0 - (fold_factor * 14.0), 
                   15.0 + math.cos(rad_r) * 20.0 + (fold_factor * 22.0))
    
    # 3. Muñeca derecha se mueve
    wrist_pos_l = (elbow_pos_l[0] + 38, elbow_pos_l[1] + 75, 65)
    wrist_pos_r = (elbow_pos_r[0] - 38.0 - (fold_factor * 28.0), 
                   elbow_pos_r[1] + 75.0 - (fold_factor * 22.0), 
                   elbow_pos_r[2] + 45.0 + (fold_factor * 28.0))
    
    # 4. Mano derecha se mueve
    hand_pos_l = (wrist_pos_l[0] + 24, wrist_pos_l[1] + 28, 80)
    hand_pos_r = (wrist_pos_r[0] - 24.0 - (fold_factor * 12.0), 
                  wrist_pos_r[1] + 28.0 - (fold_factor * 10.0), 
                  wrist_pos_r[2] + 15.0 + (fold_factor * 16.0))
    
    # 5. Brazos
    for p1, p2, width in [
        (sh_pos_l, elbow_pos_l, 4), (sh_pos_r, elbow_pos_r, 4),
        (elbow_pos_l, wrist_pos_l, 3), (elbow_pos_r, wrist_pos_r, 3),
        (wrist_pos_l, hand_pos_l, 2), (wrist_pos_r, hand_pos_r, 2)
    ]:
        u1, v1, _ = project_3d(*p1, cx, cy)
        u2, v2, _ = project_3d(*p2, cx, cy)
        canvas.create_line(u1, v1, u2, v2, fill="#38bdf8", width=width)
        
    # 6. Manos y Dedos
    all_fngs = {}
    for w_pos, h_pos, is_r in [(wrist_pos_l, hand_pos_l, False), (wrist_pos_r, hand_pos_r, True)]:
        f_factor = fold_factor if is_r else 0.0
        palm, fingers = compute_hand_and_fingers(w_pos, h_pos, is_right=is_r, fold_factor=f_factor)
        all_fngs["r" if is_r else "l"] = fingers
        
        # Palma
        pts_palm = []
        for p in palm:
            u, v, _ = project_3d(*p, cx, cy)
            pts_palm.extend([u, v])
        canvas.create_polygon(pts_palm, fill="#0f233d", outline="#38bdf8", width=1, smooth=True)
        
        # 5 Dedos
        for f_name, f_pts in fingers.items():
            is_active_pinch = (is_r and f_name in ["pulgar", "indice"])
            col = "#38bdf8" if is_r else "#1e3a5f"
            if is_active_pinch:
                col = "#f43f5e" if fold_factor > 0.6 else "#fbbf24"
            pts_line = []
            for p in f_pts:
                u, v, _ = project_3d(*p, cx, cy)
                pts_line.extend([u, v])
            canvas.create_line(pts_line, fill=col, width=2 if is_active_pinch else 1, smooth=True)
            u_tip, v_tip, _ = project_3d(*f_pts[-1], cx, cy)
            canvas.create_oval(u_tip - 2.5, v_tip - 2.5, u_tip + 2.5, v_tip + 2.5, fill=col, outline="")

    # 7. Hotspots articulados (incluyendo dedos en la pinza exacta)
    t_tip = all_fngs["r"]["pulgar"][-1]
    i_tip = all_fngs["r"]["indice"][-1]
    pinch_pt = ((t_tip[0] + i_tip[0])/2.0, (t_tip[1] + i_tip[1])/2.0, (t_tip[2] + i_tip[2])/2.0)
    
    hotspots = [
        (sh_pos_r, "#2ecc71", "Hombro R"),
        (elbow_pos_r, "#2ecc71", "Codo R"),
        (wrist_pos_r, "#f1c40f", "Muñeca R"),
        (hand_pos_r, "#e67e22", "Mano R"),
        (pinch_pt, "#e74c3c", "Dedos R (Pinza)")
    ]
    for pt, col, name in hotspots:
        u, v, _ = project_3d(*pt, cx, cy)
        canvas.create_oval(u-14, v-14, u+14, v+14, outline=col, width=1, dash=(3, 3))
        canvas.create_oval(u-8, v-8, u+8, v+8, outline=col, width=2)
        canvas.create_oval(u-3, v-3, u+3, v+3, fill=col, outline="")
        canvas.create_text(u + 18, v, anchor="w", text=name, fill="#ffffff", font=("Helvetica", 8, "bold"))
        
    canvas.create_text(20, 25, anchor="w", 
                       text=f"Cinemática Coordinada | Plegado: {int(fold_factor*100)}% | Hombro R: ({sh_pos_r[0]:.1f}, {sh_pos_r[1]:.1f}, {sh_pos_r[2]:.1f})", 
                       fill="#38bdf8", font=("Helvetica", 10, "bold"))

render(0.0)
root.after(1500, root.destroy)
root.mainloop()
print("Verification test passed successfully!")

