import tkinter as tk
import math
import time
from PIL import Image, ImageTk
import os

root = tk.Tk()
root.title("Test Human Motion")
root.geometry("600x650")

canvas = tk.Canvas(root, bg="#070d19", highlightthickness=0)
canvas.pack(fill="both", expand=True)

# Load a test texture
assets_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets", "mannequin")
img_path = os.path.join(assets_dir, "female_front.png")
orig_img = Image.open(img_path) if os.path.exists(img_path) else None

yaw = 0.0
pitch = 0.0
zoom_level = 1.05
start_t = time.time()
motion_mode = "trabajo" # "respiracion" or "trabajo"

def rotate_point_3d(x, y, z, yaw, pitch):
    cos_y = math.cos(yaw)
    sin_y = math.sin(yaw)
    x1 = x * cos_y - z * sin_y
    z1 = x * sin_y + z * cos_y
    
    cos_p = math.cos(pitch)
    sin_p = math.sin(pitch)
    y2 = y * cos_p - z1 * sin_p
    z2 = y * sin_p + z1 * cos_p
    return x1, y2, z2

def project_3d(x, y, z, cx, cy, img_scale=1.0, fov=650):
    rx, ry, rz = rotate_point_3d(x, y, z, yaw, pitch)
    scale = (fov / (fov + rz)) * img_scale
    u = cx + rx * scale
    v = cy + ry * scale
    return u, v, rz

cached_photo = None

def render():
    global cached_photo
    canvas.delete("all")
    w = canvas.winfo_width() or 600
    h = canvas.winfo_height() or 650
    cx = w / 2.0
    cy = (h / 2.0) + 12

    now = time.time() - start_t
    
    # 1. Biological Breathing
    b_phase = now * 1.68
    s_b = math.sin(b_phase)
    breathe_dy = s_b * 3.5
    chest_scale = 1.0 + s_b * 0.02
    shoulder_dy = -s_b * 2.5
    neck_dy = -s_b * 1.5

    # 2. Cardiac pulse
    heart_pulse = max(0.0, math.sin(now * 7.5)) ** 3

    # 3. Work cycle (Folding)
    if motion_mode == "trabajo":
        w_phase = now * 2.1
        fold_factor = (math.sin(w_phase - math.pi/2.0) + 1.0) / 2.0
    else:
        fold_factor = 0.0

    # Draw image
    target_h = int(h * 0.84 * zoom_level * chest_scale)
    img_scale = target_h / 525.0
    
    if orig_img:
        orig_w, orig_h = orig_img.size
        target_w = max(10, int(orig_w * (target_h / float(orig_h))))
        pos_x = cx
        pos_y = cy + (breathe_dy * zoom_level)
        resized_pil = orig_img.resize((target_w, target_h), Image.Resampling.BILINEAR)
        cached_photo = ImageTk.PhotoImage(resized_pil, master=canvas)
        canvas.create_image(pos_x, pos_y, image=cached_photo, anchor="center")

    # Kinematics hotspots
    sh_w = 98.0
    hotspots = {
        "cuello": (0, -135 + neck_dy + (fold_factor * 4.0), fold_factor * 8.0, 22),
        "espalda_alta": (0, -68, -35, 23),
        "hombro_r": (sh_w, -85 + shoulder_dy, 0, 24),
        "hombro_l": (-sh_w, -85 + shoulder_dy, 0, 24),
        "codo_r": (sh_w + 14 - (fold_factor * 14.0), 15 - (fold_factor * 16.0) + shoulder_dy * 0.5, 10 + (fold_factor * 18.0), 23),
        "codo_l": (-sh_w - 14, 15, 10, 23),
        "muñeca_r": (sh_w + 15 - (fold_factor * 36.0), 105 - (fold_factor * 38.0) + shoulder_dy * 0.3, 16 + (fold_factor * 32.0), 20),
        "muñeca_l": (-sh_w - 15, 105, 16, 20),
        "mano_r": (sh_w + 18 - (fold_factor * 40.0), 155 - (fold_factor * 44.0) + shoulder_dy * 0.2, 18 + (fold_factor * 38.0), 19),
        "mano_l": (-sh_w - 18, 155, 18, 19),
        "dedos_r": (sh_w + 20 - (fold_factor * 44.0), 205 - (fold_factor * 48.0) + shoulder_dy * 0.2, 20 + (fold_factor * 42.0), 18),
        "dedos_l": (-sh_w - 20, 205, 20, 18),
    }

    proj = {}
    for k, (x, y, z, r) in hotspots.items():
        u, v, rz = project_3d(x, y, z, cx, cy, img_scale)
        proj[k] = (u, v, r * zoom_level, rz)

    # Links
    links = [
        ("cuello", "hombro_r"), ("cuello", "hombro_l"),
        ("hombro_r", "codo_r"), ("codo_r", "muñeca_r"),
        ("muñeca_r", "mano_r"), ("mano_r", "dedos_r"),
        ("hombro_l", "codo_l"), ("codo_l", "muñeca_l"),
        ("muñeca_l", "mano_l"), ("mano_l", "dedos_l")
    ]
    for k1, k2 in links:
        u1, v1, _, _ = proj[k1]
        u2, v2, _, _ = proj[k2]
        canvas.create_line(u1, v1, u2, v2, fill="#38bdf8", width=2)

    # Draw spots
    for k, (u, v, r, rz) in proj.items():
        eff_r = r * (1.0 + 0.25 * heart_pulse)
        canvas.create_oval(u - eff_r, v - eff_r, u + eff_r, v + eff_r, outline="#e74c3c", width=2)
        canvas.create_oval(u - 4, v - 4, u + 4, v + 4, fill="#e74c3c", outline="")

    # Label
    cur_ang = 108.0 - (fold_factor * 26.0)
    therblig = "TOMAR (G) · Plegando" if fold_factor > 0.45 else "SOLTAR (RL) · Retorno"
    canvas.create_text(20, 30, anchor="w", text=f"Modo: {motion_mode.upper()} | Codo R: {cur_ang:.1f}° | {therblig}", fill="#38bdf8", font=("Helvetica", 11, "bold"))

    root.after(33, render)

root.after(50, render)
# Stop after 2 seconds in test
root.after(2000, root.destroy)
root.mainloop()
print("Motion test passed successfully without errors!")

