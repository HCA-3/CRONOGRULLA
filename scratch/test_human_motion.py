import math
import time

def simulate_kinematics(t, mode="trabajo"):
    # Breathing: ~16 breaths/min (freq = 2*pi * 16/60 = 1.67 rad/s)
    b_phase = t * 1.65
    breathe_y = math.sin(b_phase) * 3.0
    chest_scale = 1.0 + math.sin(b_phase) * 0.02
    
    # Heartbeat pulse (approx 70 bpm = 1.16 Hz -> omega = 7.3 rad/s)
    heart_pulse = 0.5 + 0.5 * math.sin(t * 7.3)
    
    if mode == "trabajo":
        # Folding cycle: 1 fold every ~2.5 seconds (omega = 2.5 rad/s)
        w_phase = t * 2.5
        # Cycle: 0 -> Reach, pi/2 -> Pinch/Grip, pi -> Press crease, 3pi/2 -> Release
        fold_factor = (math.sin(w_phase) + 1.0) / 2.0 # 0.0 to 1.0
        
        # Elbow flexes from 110 (open) to 82 (creasing)
        elbow_ang_r = 110.0 - (fold_factor * 28.0)
        # Wrist moves towards table center
        wrist_inward = fold_factor * 22.0
        wrist_forward = fold_factor * 35.0
        finger_pinch = fold_factor # 1.0 = closed pinch
        therblig_label = "TOMAR (G) - Asentando doblez" if fold_factor > 0.5 else "MOVER (M) / SOLTAR (RL)"
    else:
        elbow_ang_r = 103.5
        wrist_inward = 0.0
        wrist_forward = 0.0
        finger_pinch = 0.0
        therblig_label = "Reposo Postural"

    return {
        "breathe_y": breathe_y,
        "chest_scale": chest_scale,
        "heart_pulse": heart_pulse,
        "elbow_ang_r": elbow_ang_r,
        "wrist_inward": wrist_inward,
        "wrist_forward": wrist_forward,
        "finger_pinch": finger_pinch,
        "therblig": therblig_label
    }

for sec in [0.0, 0.5, 1.0, 1.5, 2.0, 2.5]:
    k = simulate_kinematics(sec, "trabajo")
    print(f"t={sec:.1f}s | Breathe Y: {k['breathe_y']:+4.1f}px | Codo R: {k['elbow_ang_r']:5.1f}° | Pinza: {k['finger_pinch']*100:3.0f}% | {k['therblig']}")

