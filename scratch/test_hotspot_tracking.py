import math
from PIL import Image

def test_hotspot_tracking():
    w, h = 500, 500
    cx, cy = 250, 250
    pan_x, pan_y = 0, 0
    zoom = 1.05
    target_h = int(h * 0.84 * zoom)
    img_scale = target_h / 525.0
    fov = 650

    sh_w = 95.0
    hotspots = {
        "cuello": (0, -135, 0),
        "hombro_r": (sh_w, -85, 0),
        "hombro_l": (-sh_w, -85, 0),
        "codo_r": (sh_w + 12, 15, 10),
        "codo_l": (-sh_w - 12, 15, 10),
        "muñeca_r": (sh_w + 5, 115, 20),
        "muñeca_l": (-sh_w - 5, 115, 20),
        "espalda_alta": (0, -65, -35),
    }

    for yaw_deg in [0, 90, 180, 270]:
        yaw = math.radians(yaw_deg)
        print(f"\n--- YAW = {yaw_deg} deg ---")
        for k, (x, y, z) in hotspots.items():
            # rotate
            cos_y = math.cos(yaw)
            sin_y = math.sin(yaw)
            rx = x * cos_y - z * sin_y
            rz = x * sin_y + z * cos_y
            
            scale = (fov / (fov + rz)) * img_scale
            u = cx + rx * scale + pan_x
            v = cy + y * scale + pan_y
            print(f"{k:12s} -> screen u={u:.1f}, v={v:.1f}, rz={rz:.1f} ({'FRONT' if rz >= 0 else 'BACK'})")

test_hotspot_tracking()

