import math
import time

def test_kinematics():
    t = 1.2
    is_female = True
    sh_w = 98.0 if is_female else 105.0
    
    # Base hotspots
    base = {
        "cuello":       (0, -135, 0, 22),
        "espalda_alta": (0, -68, -35, 23),
        "hombro_r":     (sh_w, -85, 0, 24),
        "hombro_l":     (-sh_w, -85, 0, 24),
        "codo_r":       (sh_w + 14, 15, 10, 23),
        "codo_l":       (-sh_w - 14, 15, 10, 23),
        "muñeca_r":     (sh_w + 15, 105, 16, 20),
        "muñeca_l":     (-sh_w - 15, 105, 16, 20),
        "mano_r":       (sh_w + 18, 155, 18, 19),
        "mano_l":       (-sh_w - 18, 155, 18, 19),
        "dedos_r":      (sh_w + 20, 205, 20, 18),
        "dedos_l":      (-sh_w - 20, 205, 20, 18),
    }

    # Breathing
    b_phase = t * 1.65
    b_dy = math.sin(b_phase) * 3.2
    sh_dy = -math.sin(b_phase) * 2.2
    
    # Work cycle
    w_phase = t * 2.0
    fold = (math.sin(w_phase) + 1.0) / 2.0
    
    modified = {}
    for k, (x, y, z, r) in base.items():
        nx, ny, nz = x, y, z
        if k in ["hombro_r", "hombro_l"]:
            ny += sh_dy
        elif k == "cuello":
            ny += sh_dy * 0.6
        elif k == "codo_r":
            nx += -fold * 12.0
            ny += -fold * 16.0 + sh_dy * 0.5
            nz += fold * 15.0
        elif k == "muñeca_r":
            nx += -fold * 32.0
            ny += -fold * 35.0 + sh_dy * 0.3
            nz += fold * 28.0
        elif k == "mano_r":
            nx += -fold * 36.0
            ny += -fold * 42.0 + sh_dy * 0.2
            nz += fold * 34.0
        elif k == "dedos_r":
            nx += -fold * 40.0
            ny += -fold * 46.0 + sh_dy * 0.2
            nz += fold * 38.0
        modified[k] = (nx, ny, nz, r)
        
    print(f"Fold factor: {fold:.2f}")
    print(f"Codo R base: {base['codo_r']} -> mod: {modified['codo_r']}")
    print(f"Dedos R base: {base['dedos_r']} -> mod: {modified['dedos_r']}")

test_kinematics()

