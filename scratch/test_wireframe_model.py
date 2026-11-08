import tkinter as tk
import math
import numpy as np

root = tk.Tk()
root.title("Test Wireframe Mannequin")
root.geometry("600x700")

canvas = tk.Canvas(root, bg="#070d19", highlightthickness=0)
canvas.pack(fill="both", expand=True)

yaw = math.radians(25)
pitch = math.radians(-5)
zoom_level = 1.05
is_female = True
pan_x = 0
pan_y = 0

def rotate_point_3d(x, y, z, curr_yaw=None, curr_pitch=None):
    y_rot = yaw if curr_yaw is None else curr_yaw
    p_rot = pitch if curr_pitch is None else curr_pitch
    cos_y = math.cos(y_rot)
    sin_y = math.sin(y_rot)
    x1 = x * cos_y - z * sin_y
    z1 = x * sin_y + z * cos_y
    
    cos_p = math.cos(p_rot)
    sin_p = math.sin(p_rot)
    y2 = y * cos_p - z1 * sin_p
    z2 = y * sin_p + z1 * cos_p
    return x1, y2, z2

def project_3d(x, y, z, cx, cy, fov=650, curr_yaw=None, curr_pitch=None):
    rx, ry, rz = rotate_point_3d(x, y, z, curr_yaw, curr_pitch)
    scale = (fov / (fov + rz)) * zoom_level
    u = cx + rx * scale + pan_x
    v = cy + ry * scale + pan_y
    return u, v, rz

def draw():
    canvas.delete("all")
    w = 600
    h = 700
    cx = w / 2.0
    cy = (h / 2.0) - 20

    # Grid
    for x in range(0, w, 40):
        canvas.create_line(x, 0, x, h, fill="#0c1626", width=1)
    for y in range(0, h, 40):
        canvas.create_line(0, y, w, y, fill="#0c1626", width=1)

    # Parametros antropométricos
    sh_w = 98.0 if is_female else 125.0
    sh_drop = 65.0
    waist_w = 48.0 if is_female else 68.0
    hip_w = 78.0 if is_female else 74.0
    neck_r = 16.0 if is_female else 22.0
    bust_z = 32.0 if is_female else 16.0

    torso_rings_def = [
        (-85, neck_r * 1.5, neck_r * 1.3, -4),
        (-65, sh_w * 0.75, 34, 0),
        (-35, 74 if is_female else 92, 42, bust_z * 0.8),
        (-5, 68 if is_female else 86, 38, bust_z),
        (25, 58 if is_female else 78, 34, 4),
        (65, waist_w, 28 if is_female else 34, 0),
        (95, waist_w + 12, 32 if is_female else 36, 0),
        (130, hip_w, 36 if is_female else 40, -2)
    ]

    render_queue = []

    # Torso rings
    for y_lvl, rx, rz, off_z in torso_rings_def:
        pts_ring = []
        num_pts = 18
        for i in range(num_pts):
            theta = 2 * math.pi * i / num_pts
            px = rx * math.cos(theta)
            pz = rz * math.sin(theta) + off_z
            pts_ring.append((px, y_lvl, pz))
        avg_z = np.mean([rotate_point_3d(px, py, pz)[2] for px, py, pz in pts_ring])
        render_queue.append({
            "type": "ring",
            "points": pts_ring,
            "z": avg_z,
            "color": "#1e3a5f" if avg_z < 0 else "#38bdf8",
            "width": 1 if avg_z < 0 else 2
        })

    # Bust / Pectorals
    if is_female:
        for side in [-1, 1]:
            bx = side * 28.0
            by = -20.0
            bz = 38.0
            pts_bust = []
            for a in np.linspace(0, 2*math.pi, 14):
                pts_bust.append((bx + 16*math.cos(a), by + 16*math.sin(a), bz + 10*math.sin(a)))
            avg_z = np.mean([rotate_point_3d(px, py, pz)[2] for px, py, pz in pts_bust])
            render_queue.append({
                "type": "polygon",
                "points": pts_bust,
                "z": avg_z,
                "fill": "#0f233d" if avg_z > 0 else "#091424",
                "outline": "#38bdf8" if avg_z > 0 else "#1e3a5f",
                "width": 2 if avg_z > 0 else 1
            })
    else:
        for side in [-1, 1]:
            pts_pec = [
                (side * 8, -45, 28),
                (side * 52, -45, 28),
                (side * 48, -8, 30),
                (side * 8, -8, 28)
            ]
            avg_z = np.mean([rotate_point_3d(px, py, pz)[2] for px, py, pz in pts_pec])
            render_queue.append({
                "type": "polygon",
                "points": pts_pec,
                "z": avg_z,
                "fill": "#0f233d" if avg_z > 0 else "#091424",
                "outline": "#38bdf8" if avg_z > 0 else "#1e3a5f",
                "width": 2 if avg_z > 0 else 1
            })

    # Head rings
    head_cy = -145.0
    head_rx = 28.0 if is_female else 34.0
    head_ry = 38.0
    head_rz = 30.0
    for h_step in [-22, -8, 8, 22]:
        rad_fac = math.cos(h_step / 35.0)
        pts_head_ring = []
        for i in range(16):
            theta = 2 * math.pi * i / 16
            px = head_rx * rad_fac * math.cos(theta)
            pz = head_rz * rad_fac * math.sin(theta)
            pts_head_ring.append((px, head_cy + h_step, pz))
        avg_z = np.mean([rotate_point_3d(px, py, pz)[2] for px, py, pz in pts_head_ring])
        render_queue.append({
            "type": "ring",
            "points": pts_head_ring,
            "z": avg_z,
            "color": "#60a5fa" if avg_z > 0 else "#1e3a5f",
            "width": 1 if avg_z < 0 else 2
        })

    # Face visor line
    face_pts = [
        (0, head_cy - head_ry * 0.7, head_rz * 0.8),
        (0, head_cy - 4, head_rz * 1.1),
        (0, head_cy + head_ry * 0.5, head_rz * 0.7),
        (0, head_cy + head_ry * 0.8, 0)
    ]
    avg_z = np.mean([rotate_point_3d(px, py, pz)[2] for px, py, pz in face_pts])
    render_queue.append({
        "type": "line_strip",
        "points": face_pts,
        "z": avg_z,
        "color": "#93c5fd" if avg_z > 0 else "#1e3a5f",
        "width": 2
    })

    # Spine
    spine_pts = [
        (0, -95, -12),
        (0, -65, -28),
        (0, -30, -32),
        (0, 10, -34),
        (0, 50, -30),
        (0, 90, -25),
        (0, 130, -18)
    ]
    avg_z = np.mean([rotate_point_3d(px, py, pz)[2] for px, py, pz in spine_pts])
    render_queue.append({
        "type": "line_strip",
        "points": spine_pts,
        "z": avg_z,
        "color": "#38bdf8" if avg_z > 0 else "#1e293b",
        "width": 3 if avg_z > 0 else 1,
        "dash": (4, 3)
    })

    # Limbs
    sh_pos_l = (-sh_w, -sh_drop, 0)
    sh_pos_r = (sh_w, -sh_drop, 0)

    ang_r = 98.0
    ang_l = 95.0
    rad_r = math.radians(ang_r)
    rad_l = math.radians(ang_l)

    elbow_pos_l = (sh_pos_l[0] - 22, sh_pos_l[1] + 85, 12 + math.cos(rad_l)*20)
    elbow_pos_r = (sh_pos_r[0] + 22, sh_pos_r[1] + 85, 12 + math.cos(rad_r)*20)

    wrist_pos_l = (elbow_pos_l[0] + 38, elbow_pos_l[1] + 75, elbow_pos_l[2] + 45)
    wrist_pos_r = (elbow_pos_r[0] - 38, elbow_pos_r[1] + 75, elbow_pos_r[2] + 45)

    hand_pos_l = (wrist_pos_l[0] + 24, wrist_pos_l[1] + 28, wrist_pos_l[2] + 15)
    hand_pos_r = (wrist_pos_r[0] - 24, wrist_pos_r[1] + 28, wrist_pos_r[2] + 15)

    dedos_pos_l = (hand_pos_l[0] + 18, hand_pos_l[1] + 22, hand_pos_l[2] + 10)
    dedos_pos_r = (hand_pos_r[0] - 18, hand_pos_r[1] + 22, hand_pos_r[2] + 10)

    # Arm segments
    segments = [
        (sh_pos_l, elbow_pos_l, 4), (sh_pos_r, elbow_pos_r, 4),
        (elbow_pos_l, wrist_pos_l, 3), (elbow_pos_r, wrist_pos_r, 3),
        (wrist_pos_l, hand_pos_l, 2), (wrist_pos_r, hand_pos_r, 2),
        (hand_pos_l, dedos_pos_l, 2), (hand_pos_r, dedos_pos_r, 2),
    ]
    for p1, p2, w_seg in segments:
        avg_z = (rotate_point_3d(*p1)[2] + rotate_point_3d(*p2)[2]) / 2.0
        render_queue.append({
            "type": "segment", "p1": p1, "p2": p2, "z": avg_z,
            "color": "#38bdf8" if avg_z > 0 else "#1e3a5f", "width": w_seg if avg_z > 0 else 1
        })

    # Hotspots
    hotspots_3d = {
        "cuello":       (0, -90, -5, 22),
        "hombro_l":     (sh_pos_l[0], sh_pos_l[1], sh_pos_l[2], 24),
        "hombro_r":     (sh_pos_r[0], sh_pos_r[1], sh_pos_r[2], 24),
        "codo_l":       (elbow_pos_l[0], elbow_pos_l[1], elbow_pos_l[2], 22),
        "codo_r":       (elbow_pos_r[0], elbow_pos_r[1], elbow_pos_r[2], 22),
        "muñeca_l":     (wrist_pos_l[0], wrist_pos_l[1], wrist_pos_l[2], 20),
        "muñeca_r":     (wrist_pos_r[0], wrist_pos_r[1], wrist_pos_r[2], 20),
        "mano_l":       (hand_pos_l[0], hand_pos_l[1], hand_pos_l[2], 18),
        "mano_r":       (hand_pos_r[0], hand_pos_r[1], hand_pos_r[2], 18),
        "dedos_l":      (dedos_pos_l[0], dedos_pos_l[1], dedos_pos_l[2], 17),
        "dedos_r":      (dedos_pos_r[0], dedos_pos_r[1], dedos_pos_r[2], 17),
        "espalda_alta": (0, -25, -34, 23)
    }

    for z_key, (hx, hy, hz, hr) in hotspots_3d.items():
        u, v, rz = project_3d(hx, hy, hz, cx, cy)
        is_active = (z_key == "codo_r")
        col = "#2ecc71" if "l" in z_key or "cuello" in z_key else "#f1c40f" if "muñeca" in z_key or "mano" in z_key else "#e74c3c"
        render_queue.append({
            "type": "hotspot",
            "u": u, "v": v, "r": hr * zoom_level, "z": rz,
            "color": col, "key": z_key, "active": is_active
        })

    # Render sorted by depth Z
    render_queue.sort(key=lambda item: item["z"])

    for item in render_queue:
        t = item["type"]
        if t == "ring":
            proj_pts = []
            for pt in item["points"]:
                u, v, _ = project_3d(*pt, cx, cy)
                proj_pts.extend([u, v])
            if len(proj_pts) >= 4:
                canvas.create_polygon(proj_pts, fill="", outline=item["color"], width=item["width"], smooth=True)
        elif t == "polygon":
            proj_pts = []
            for pt in item["points"]:
                u, v, _ = project_3d(*pt, cx, cy)
                proj_pts.extend([u, v])
            if len(proj_pts) >= 6:
                canvas.create_polygon(proj_pts, fill=item["fill"], outline=item["outline"], width=item["width"], smooth=True)
        elif t == "line_strip":
            proj_pts = []
            for pt in item["points"]:
                u, v, _ = project_3d(*pt, cx, cy)
                proj_pts.extend([u, v])
            if len(proj_pts) >= 4:
                dash = item.get("dash")
                canvas.create_line(proj_pts, fill=item["color"], width=item["width"], dash=dash, smooth=True)
        elif t == "segment":
            u1, v1, _ = project_3d(*item["p1"], cx, cy)
            u2, v2, _ = project_3d(*item["p2"], cx, cy)
            canvas.create_line(u1, v1, u2, v2, fill=item["color"], width=item["width"], capstyle="round")
        elif t == "hotspot":
            u, v, hr, rz = item["u"], item["v"], item["r"], item["z"]
            col = item["color"]
            depth_alpha = max(0.4, min(1.0, (rz + 200) / 400.0))
            eff_r = hr * depth_alpha

            # Outer ring dashed
            canvas.create_oval(u - eff_r * 1.5, v - eff_r * 1.5, u + eff_r * 1.5, v + eff_r * 1.5,
                               outline=col, fill="", width=1, dash=(3, 3))
            # Middle ring solid
            canvas.create_oval(u - eff_r * 1.0, v - eff_r * 1.0, u + eff_r * 1.0, v + eff_r * 1.0,
                               outline=col, fill="", width=2)
            # Center dot
            canvas.create_oval(u - eff_r * 0.5, v - eff_r * 0.5, u + eff_r * 0.5, v + eff_r * 0.5,
                               outline="", fill=col)

            # Active inspection tag (just like in user's image!)
            if item["active"]:
                canvas.create_oval(u - eff_r * 1.9, v - eff_r * 1.9, u + eff_r * 1.9, v + eff_r * 1.9,
                                   outline="#ffffff", width=2)
                canvas.create_rectangle(u - 4, v - 11, u + 82, v + 9, fill="#070d19", outline="", width=0)
                canvas.create_text(u + 40, v - 1, text="▶ INSPECCIÓN", fill="#ffffff", font=("Helvetica", 9, "bold"))

    canvas.create_text(20, h - 30, anchor="w", text="Operario: Diego", fill="#64748b", font=("Helvetica", 10))

draw()
root.after(1500, root.destroy)
root.mainloop()
print("Wireframe test executed perfectly!")

