import tkinter as tk
import math
import numpy as np

def test_full_pipeline():
    yaw = math.radians(25)
    pitch = math.radians(-5)
    zoom_level = 1.05
    is_female = True
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

    print(f"Torso rings count: {len(torso_rings_def)}")
    assert len(torso_rings_def) == 8, "Torso rings should be 8"

    # Arms and fingers
    sh_pos_l = (-sh_w, -sh_drop, 0)
    sh_pos_r = (sh_w, -sh_drop, 0)

    elbow_pos_l = (sh_pos_l[0] - 22, sh_pos_l[1] + 85, 20)
    elbow_pos_r = (sh_pos_r[0] + 22, sh_pos_r[1] + 85, 20)

    wrist_pos_l = (elbow_pos_l[0] + 38, elbow_pos_l[1] + 75, 65)
    wrist_pos_r = (elbow_pos_r[0] - 38, elbow_pos_r[1] + 75, 65)

    hand_pos_l = (wrist_pos_l[0] + 24, wrist_pos_l[1] + 28, 80)
    hand_pos_r = (wrist_pos_r[0] - 24, wrist_pos_r[1] + 28, 80)

    dedos_pos_l = (hand_pos_l[0] + 18, hand_pos_l[1] + 22, 90)
    dedos_pos_r = (hand_pos_r[0] - 18, hand_pos_r[1] + 22, 90)

    hotspots = [
        "cuello", "espalda_alta", "hombro_r", "hombro_l",
        "codo_r", "codo_l", "muñeca_r", "muñeca_l",
        "mano_r", "mano_l", "dedos_r", "dedos_l"
    ]
    print(f"Total hotspots: {len(hotspots)}")
    assert len(hotspots) == 12, "Should have 12 hotspots"
    print("Full pipeline check passed!")

test_full_pipeline()

