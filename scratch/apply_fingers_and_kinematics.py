import re
import os

filepath = r"views\view_lesiones_3d.py"
with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

# 1. Update combo_motion values and width
old_combo = '''        # Selector de Cinemática Humana (Respiración / Plegado / Estático)
        ctk.CTkLabel(controls_f, text="Movimiento:", font=ctk.CTkFont(size=11, weight="bold")).pack(side="left", padx=(0, 4))
        self.combo_motion = ctk.CTkOptionMenu(
            controls_f,
            values=["🫁 Respiración", "⚙️ Plegado (Trabajo)", "⏸ Estático"],
            command=self.on_motion_mode_changed,
            width=135, height=28,
            font=ctk.CTkFont(size=10, weight="bold"),
            fg_color="#059669", button_color="#047857", button_hover_color="#065f46"
        )
        self.combo_motion.set("🫁 Respiración")
        self.combo_motion.pack(side="left", padx=(0, 8))'''

new_combo = '''        # Selector de Cinemática Humana (Respiración / Plegado Completo / Articular Zona / Estático)
        ctk.CTkLabel(controls_f, text="Movimiento:", font=ctk.CTkFont(size=11, weight="bold")).pack(side="left", padx=(0, 4))
        self.combo_motion = ctk.CTkOptionMenu(
            controls_f,
            values=["🫁 Respiración", "⚙️ Plegado Completo (Hombro-Codo-Mano-Dedos)", "🎯 Articular Zona Seleccionada", "⏸ Estático"],
            command=self.on_motion_mode_changed,
            width=190, height=28,
            font=ctk.CTkFont(size=10, weight="bold"),
            fg_color="#059669", button_color="#047857", button_hover_color="#065f46"
        )
        self.combo_motion.set("🫁 Respiración")
        self.combo_motion.pack(side="left", padx=(0, 8))'''

assert old_combo in content, "old_combo not found!"
content = content.replace(old_combo, new_combo, 1)

# 2. Update on_motion_mode_changed
old_motion_handler = '''    def on_motion_mode_changed(self, val):
        self.human_motion_mode.set(val)
        if val == "🫁 Respiración":
            self.combo_motion.configure(fg_color="#059669", button_color="#047857", button_hover_color="#065f46")
            self._start_animation_loop()
        elif "Trabajo" in val or "Plegado" in val:
            self.combo_motion.configure(fg_color="#7c3aed", button_color="#6d28d9", button_hover_color="#5b21b6")
            self._start_animation_loop()
        else:
            self.combo_motion.configure(fg_color="#475569", button_color="#334155", button_hover_color="#1e293b")
            if not self.auto_rotate and self.anim_timer_id:
                try:
                    self.after_cancel(self.anim_timer_id)
                except Exception:
                    pass
                self.anim_timer_id = None
                self.is_animating = False
            self.draw_mannequin_3d()'''

new_motion_handler = '''    def on_motion_mode_changed(self, val):
        self.human_motion_mode.set(val)
        if "Respiración" in val:
            self.combo_motion.configure(fg_color="#059669", button_color="#047857", button_hover_color="#065f46")
            self._start_animation_loop()
        elif "Plegado" in val or "Trabajo" in val:
            self.combo_motion.configure(fg_color="#7c3aed", button_color="#6d28d9", button_hover_color="#5b21b6")
            self._start_animation_loop()
        elif "Articular" in val or "Zona" in val:
            self.combo_motion.configure(fg_color="#d97706", button_color="#b45309", button_hover_color="#92400e")
            self._start_animation_loop()
        else:
            self.combo_motion.configure(fg_color="#475569", button_color="#334155", button_hover_color="#1e293b")
            if not self.auto_rotate and self.anim_timer_id:
                try:
                    self.after_cancel(self.anim_timer_id)
                except Exception:
                    pass
                self.anim_timer_id = None
                self.is_animating = False
            self.draw_mannequin_3d()'''

assert old_motion_handler in content, "old_motion_handler not found!"
content = content.replace(old_motion_handler, new_motion_handler, 1)

# 3. Add _compute_hand_and_fingers before draw_mannequin_3d
marker_draw = "    # ── DIBUJO DEL MANIQUÍ ANATÓMICO 3D (HOLOGRÁFICO DE ANILLOS / ASTRA AI) ────"

hand_calc_func = '''    def _compute_hand_and_fingers(self, wrist_pos, hand_pos, is_right=True, fold_factor=0.0):
        """
        Calcula la anatomía 3D realista de la mano con 5 dedos articulados (Pulgar, Índice, Medio, Anular, Meñique)
        y el polígono metacarpiano de la palma. En modo plegado, el pulgar y el índice ejecutan la pinza digital (TOMAR G).
        """
        wx, wy, wz = wrist_pos
        hx, hy, hz = hand_pos
        
        # Vector longitudinal del carpo a la palma
        dx, dy, dz = hx - wx, hy - wy, hz - wz
        len_d = math.sqrt(dx*dx + dy*dy + dz*dz) or 1.0
        fx, fy, fz = dx / len_d, dy / len_d, dz / len_d
        
        # Vector lateral (perpendicular en el plano palmar)
        sign = 1.0 if is_right else -1.0
        rx, ry, rz = -sign * fz, 0.0, sign * fx
        len_r = math.sqrt(rx*rx + ry*ry + rz*rz) or 1.0
        rx, ry, rz = rx / len_r, ry / len_r, rz / len_r
        
        # Vector normal a la palma (dorsal / volar)
        nx = fy * rz - fz * ry
        ny = fz * rx - fx * rz
        nz = fx * ry - fy * rx
        len_n = math.sqrt(nx*nx + ny*ny + nz*nz) or 1.0
        nx, ny, nz = nx / len_n, ny / len_n, nz / len_n

        # Contorno perimetral del carpo / metacarpo (palma 3D)
        palm_pts = [
            (wx - rx * 6.0, wy, wz - rz * 6.0),
            (wx + rx * 6.0, wy, wz + rz * 6.0),
            (hx + rx * 10.0, hy, hz + rz * 10.0),
            (hx - rx * 8.0, hy, hz - rz * 8.0)
        ]
        
        fingers = {}
        
        # 1. Pulgar (Thumb - 3 articulaciones con oposición activa hacia el índice)
        pinch_curl = fold_factor * 11.0 if is_right else 0.0
        thumb_base = (wx - rx * 5.0 + fx * 5.0, wy + fy * 5.0, wz - rz * 5.0 + fz * 5.0)
        thumb_mid  = (thumb_base[0] - rx * 8.0 + fx * 10.0 - nx * 3.0, 
                      thumb_base[1] + fy * 10.0, 
                      thumb_base[2] - rz * 8.0 + fz * 10.0 - nz * 3.0)
        thumb_tip  = (thumb_mid[0] + rx * pinch_curl + fx * 7.0 + nx * (3.0 if is_right else 0.0), 
                      thumb_mid[1] + fy * 7.0 + (fold_factor * 5.0 if is_right else 0.0), 
                      thumb_mid[2] + rz * pinch_curl + fz * 7.0 + nz * (3.0 if is_right else 0.0))
        fingers["pulgar"] = [thumb_base, thumb_mid, thumb_tip]
        
        # 2. Índice (Index - articulación de flexión hacia el pulgar para cierre de pinza de precisión)
        curl_idx = fold_factor * 6.0 if is_right else 0.0
        idx_base = (hx - rx * 5.0, hy, hz - rz * 5.0)
        idx_mid  = (idx_base[0] + fx * 10.0 - rx * (curl_idx * 0.5), 
                    idx_base[1] + fy * 10.0 + (curl_idx * 0.5), 
                    idx_base[2] + fz * 10.0 - rz * (curl_idx * 0.5))
        idx_tip  = (idx_mid[0] + fx * 8.0 - rx * curl_idx, 
                    idx_mid[1] + fy * 8.0 + (curl_idx * 1.1), 
                    idx_mid[2] + fz * 8.0 - rz * curl_idx)
        fingers["indice"] = [idx_base, idx_mid, idx_tip]
        
        # 3. Medio (Middle - soporte lateral de pinza)
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

'''

assert marker_draw in content, "marker_draw not found!"
content = content.replace(marker_draw, hand_calc_func + marker_draw, 1)

# 4. Now replace the kinematics block in draw_mannequin_3d up to the end of render loop
# Let's find the start of kinematics in draw_mannequin_3d
start_kin_marker = "        # ── CÁLCULOS DE CINEMÁTICA HUMANA VIVA (RESPIRACIÓN, PULSO Y TRABAJO) ──"
end_render_marker = "        # ── 4. Badges de Información 3D, Operario y Estado ────────────────"

assert start_kin_marker in content, "start_kin_marker not found!"
assert end_render_marker in content, "end_render_marker not found!"

new_kin_and_render = '''        # ── CÁLCULOS DE CINEMÁTICA HUMANA VIVA (RESPIRACIÓN, PULSO, PLEGADO Y ARTICULACIÓN) ──
        now = time.time() - self.anim_start_time
        mode_val = self.human_motion_mode.get()
        is_motion = (mode_val != "⏸ Estático")
        is_work = ("Plegado" in mode_val or "Trabajo" in mode_val)
        is_artic = ("Articular" in mode_val or "Zona" in mode_val)
        sel_zone = self.selected_zone.get()

        # 1. Respiración biológica (~16 rpm) y micro-balance postural fisiológico
        if is_motion:
            b_phase = now * 1.68
            s_b = math.sin(b_phase)
            breathe_dy = s_b * 3.2
            chest_scale = 1.0 + (s_b * 0.022)
            shoulder_dy = -s_b * 2.4
            neck_dy = -s_b * 1.4
            
            # Micro-oscilación postural natural (involuntaria, viva)
            sway_yaw = math.sin(now * 0.75) * math.radians(0.7)
            sway_pitch = math.cos(now * 0.55) * math.radians(0.4)
            heart_pulse = max(0.0, math.sin(now * 7.5)) ** 3
        else:
            breathe_dy = 0.0
            chest_scale = 1.0
            shoulder_dy = 0.0
            neck_dy = 0.0
            sway_yaw = 0.0
            sway_pitch = 0.0
            heart_pulse = 0.0

        # Ciclos rítmicos de movimiento
        w_phase = now * 2.1 # Ciclo de ~3.0 seg por plegado
        fold_cycle = (math.sin(w_phase - math.pi / 2.0) + 1.0) / 2.0  # 0.0 a 1.0
        artic_cycle = (math.sin(now * 2.8) + 1.0) / 2.0             # 0.0 a 1.0 para zona seleccionada

        # Factor de trabajo para todo el brazo en modo Plegado
        fold_factor = fold_cycle if is_work else 0.0
        neck_tilt = fold_factor * 4.0 if is_work else (artic_cycle * 8.0 if (is_artic and sel_zone == "cuello") else 0.0)

        eff_yaw = self.yaw + sway_yaw
        eff_pitch = self.pitch + sway_pitch

        # 1. Rejilla de Fondo 3D y Brújula de Orientación
        self._draw_background_grid(c, w, h)
        self._draw_compass_3d(c, 45, h - 45, eff_yaw)

        # 2. Definición Geométrica del Maniquí Holográfico 3D (Tronco Superior Waist-Up)
        sh_w = 98.0 if is_female else 125.0
        sh_drop = 65.0
        waist_w = 48.0 if is_female else 68.0
        hip_w = 78.0 if is_female else 74.0
        neck_r = 16.0 if is_female else 22.0
        bust_z = 32.0 if is_female else 16.0

        # Anillos transversales del torso (Y, Radio X, Radio Z, Offset Z) con modulación respiratoria
        torso_rings_def = [
            (-85 + neck_dy, (neck_r * 1.5) * chest_scale, (neck_r * 1.3) * chest_scale, -4),
            (-65 + shoulder_dy * 0.7, (sh_w * 0.75) * chest_scale, 34 * chest_scale, 0),
            (-35 + breathe_dy * 0.5, (74 if is_female else 92) * chest_scale, 42 * chest_scale, bust_z * 0.8),
            (-5 + breathe_dy * 0.3, (68 if is_female else 86) * chest_scale, 38 * chest_scale, bust_z),
            (25 + breathe_dy * 0.2, (58 if is_female else 78) * chest_scale, 34 * chest_scale, 4),
            (65, waist_w, 28 if is_female else 34, 0),
            (95, waist_w + 12, 32 if is_female else 36, 0),
            (130, hip_w, 36 if is_female else 40, -2)
        ]

        render_queue = []

        # ── A. Anillos de sección del torso ────────────────────────────────
        for y_lvl, rx, rz, off_z in torso_rings_def:
            pts_ring = []
            num_pts = 18
            for i in range(num_pts):
                theta = 2 * math.pi * i / num_pts
                px = rx * math.cos(theta)
                pz = rz * math.sin(theta) + off_z
                pts_ring.append((px, y_lvl, pz))
            
            avg_z = np.mean([self.rotate_point_3d(px, py, pz, eff_yaw, eff_pitch)[2] for px, py, pz in pts_ring])
            render_queue.append({
                "type": "ring",
                "points": pts_ring,
                "z": avg_z,
                "color": "#1e3a5f" if avg_z < 0 else "#38bdf8",
                "width": 1 if avg_z < 0 else 2
            })

        # ── B. Contornos de Busto (Mujer) o Pectorales (Hombre) ────────────
        if is_female:
            for side in [-1, 1]:
                bx = side * 28.0
                by = -20.0 + (breathe_dy * 0.4)
                bz = 38.0 * chest_scale
                pts_bust = []
                for a in np.linspace(0, 2*math.pi, 14):
                    pts_bust.append((bx + 16*math.cos(a), by + 16*math.sin(a), bz + 10*math.sin(a)))
                avg_z = np.mean([self.rotate_point_3d(px, py, pz, eff_yaw, eff_pitch)[2] for px, py, pz in pts_bust])
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
                    (side * 8, -45 + shoulder_dy * 0.5, 28 * chest_scale),
                    (side * 52, -45 + shoulder_dy * 0.5, 28 * chest_scale),
                    (side * 48, -8, 30 * chest_scale),
                    (side * 8, -8, 28 * chest_scale)
                ]
                avg_z = np.mean([self.rotate_point_3d(px, py, pz, eff_yaw, eff_pitch)[2] for px, py, pz in pts_pec])
                render_queue.append({
                    "type": "polygon",
                    "points": pts_pec,
                    "z": avg_z,
                    "fill": "#0f233d" if avg_z > 0 else "#091424",
                    "outline": "#38bdf8" if avg_z > 0 else "#1e3a5f",
                    "width": 2 if avg_z > 0 else 1
                })

        # ── C. Cabeza de Maniquí 3D (Anillos de latitud y visor) ───────────
        head_cy = -145.0 + neck_dy + neck_tilt
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
            avg_z = np.mean([self.rotate_point_3d(px, py, pz, eff_yaw, eff_pitch)[2] for px, py, pz in pts_head_ring])
            render_queue.append({
                "type": "ring",
                "points": pts_head_ring,
                "z": avg_z,
                "color": "#60a5fa" if avg_z > 0 else "#1e3a5f",
                "width": 1 if avg_z < 0 else 2
            })

        # Línea central facial / visor
        face_pts = [
            (0, head_cy - head_ry * 0.7, head_rz * 0.8),
            (0, head_cy - 4, head_rz * 1.1),
            (0, head_cy + head_ry * 0.5, head_rz * 0.7),
            (0, head_cy + head_ry * 0.8, 0)
        ]
        avg_z = np.mean([self.rotate_point_3d(px, py, pz, eff_yaw, eff_pitch)[2] for px, py, pz in face_pts])
        render_queue.append({
            "type": "line_strip",
            "points": face_pts,
            "z": avg_z,
            "color": "#93c5fd" if avg_z > 0 else "#1e3a5f",
            "width": 2
        })

        # ── D. Columna Vertebral y Escápulas ───────────────────────────────
        spine_pts = [
            (0, -95 + neck_dy, -12),
            (0, -65 + shoulder_dy * 0.5, -28),
            (0, -30, -32),
            (0, 10, -34),
            (0, 50, -30),
            (0, 90, -25),
            (0, 130, -18)
        ]
        avg_z = np.mean([self.rotate_point_3d(px, py, pz, eff_yaw, eff_pitch)[2] for px, py, pz in spine_pts])
        render_queue.append({
            "type": "line_strip",
            "points": spine_pts,
            "z": avg_z,
            "color": "#38bdf8" if avg_z > 0 else "#1e293b",
            "width": 3 if avg_z > 0 else 1,
            "dash": (4, 3)
        })

        for side in [-1, 1]:
            scap_pts = [
                (side * 20, -55 + shoulder_dy * 0.6, -28),
                (side * 52, -50 + shoulder_dy * 0.6, -26),
                (side * 28, -10, -30)
            ]
            avg_z = np.mean([self.rotate_point_3d(px, py, pz, eff_yaw, eff_pitch)[2] for px, py, pz in scap_pts])
            render_queue.append({
                "type": "polygon",
                "points": scap_pts,
                "z": avg_z,
                "fill": "#0e1e33" if avg_z > 0 else "#08101a",
                "outline": "#38bdf8" if avg_z > 0 else "#1e293b",
                "width": 2 if avg_z > 0 else 1
            })

        # ── E. Extremidades Superiores con Cinemática Coordinada (Hombro, Codo, Muñeca, Mano y Dedos) ─
        # Conexión directa con la regla ergonómica:
        # "en el hombro se debe mover ese hombro si es el codo, muñecas o manos tambien deben de moverse"

        # 1. Movilidad activa del hombro
        sh_move_r = fold_factor
        if is_artic and ("hombro_r" in sel_zone or sel_zone == "hombro_r"):
            sh_move_r = max(sh_move_r, artic_cycle)
        
        sh_move_l = 0.0
        if is_artic and ("hombro_l" in sel_zone):
            sh_move_l = artic_cycle

        # Hombro izquierdo
        sh_pos_l = (-sh_w + (sh_move_l * 14.0), -sh_drop + shoulder_dy + (sh_move_l * 6.0), sh_move_l * 14.0)

        # Hombro derecho: aducción medial (-X), descenso clavicular (+Y), flexión anterior (+Z)
        sh_delta_x = -sh_move_r * 14.0
        sh_delta_y = sh_move_r * 7.0
        sh_delta_z = sh_move_r * 16.0
        sh_pos_r = (sh_w + sh_delta_x, -sh_drop + shoulder_dy + sh_delta_y, sh_delta_z)

        # 2. Movilidad activa del codo
        codo_move_r = fold_factor
        if is_artic and ("codo_r" in sel_zone):
            codo_move_r = max(codo_move_r, artic_cycle)
        cur_ang_r = 108.0 - (codo_move_r * 28.0)
        rad_r = math.radians(cur_ang_r)

        codo_move_l = 0.0
        if is_artic and ("codo_l" in sel_zone):
            codo_move_l = artic_cycle
        cur_ang_l = self.metrics["avg_elbow_l"] - (codo_move_l * 25.0)
        rad_l = math.radians(cur_ang_l)

        elbow_pos_l = (sh_pos_l[0] - 22.0 + (codo_move_l * 14.0), 
                       sh_pos_l[1] + 85.0 - (codo_move_l * 10.0), 
                       12.0 + math.cos(rad_l) * 20.0 + (codo_move_l * 16.0))

        elbow_pos_r = (sh_pos_r[0] + 20.0 - (codo_move_r * 16.0), 
                       sh_pos_r[1] + 85.0 - (codo_move_r * 14.0), 
                       15.0 + math.cos(rad_r) * 20.0 + (codo_move_r * 22.0))

        # 3. Movilidad activa de la muñeca
        wrist_move_r = fold_factor
        if is_artic and ("muñeca_r" in sel_zone):
            wrist_move_r = max(wrist_move_r, artic_cycle)

        wrist_move_l = 0.0
        if is_artic and ("muñeca_l" in sel_zone):
            wrist_move_l = artic_cycle

        wrist_pos_l = (elbow_pos_l[0] + 38.0 - (wrist_move_l * 16.0), 
                       elbow_pos_l[1] + 75.0 - (wrist_move_l * 12.0), 
                       elbow_pos_l[2] + 45.0 + (wrist_move_l * 20.0))

        wrist_pos_r = (elbow_pos_r[0] - 38.0 - (wrist_move_r * 28.0), 
                       elbow_pos_r[1] + 75.0 - (wrist_move_r * 22.0), 
                       elbow_pos_r[2] + 45.0 + (wrist_move_r * 28.0))

        # 4. Movilidad activa de la mano (carpo y palma)
        hand_move_r = fold_factor
        if is_artic and ("mano_r" in sel_zone or "dedos_r" in sel_zone):
            hand_move_r = max(hand_move_r, artic_cycle)

        hand_move_l = 0.0
        if is_artic and ("mano_l" in sel_zone or "dedos_l" in sel_zone):
            hand_move_l = artic_cycle

        hand_pos_l = (wrist_pos_l[0] + 24.0 - (hand_move_l * 8.0), 
                      wrist_pos_l[1] + 28.0 - (hand_move_l * 6.0), 
                      wrist_pos_l[2] + 15.0 + (hand_move_l * 10.0))

        hand_pos_r = (wrist_pos_r[0] - 24.0 - (hand_move_r * 12.0), 
                      wrist_pos_r[1] + 28.0 - (hand_move_r * 10.0), 
                      wrist_pos_r[2] + 15.0 + (hand_move_r * 16.0))

        # 5. Brazos y Antebrazos (Líneas óseas principales)
        segments = [
            (sh_pos_l, elbow_pos_l, 4), (sh_pos_r, elbow_pos_r, 4),
            (elbow_pos_l, wrist_pos_l, 3), (elbow_pos_r, wrist_pos_r, 3),
            (wrist_pos_l, hand_pos_l, 2), (wrist_pos_r, hand_pos_r, 2)
        ]
        for p1, p2, w_seg in segments:
            avg_z = (self.rotate_point_3d(*p1, eff_yaw, eff_pitch)[2] + self.rotate_point_3d(*p2, eff_yaw, eff_pitch)[2]) / 2.0
            render_queue.append({
                "type": "segment", "p1": p1, "p2": p2, "z": avg_z,
                "color": "#38bdf8" if avg_z > 0 else "#1e3a5f", "width": w_seg if avg_z > 0 else 1
            })

        # 6. Cálculo Anatómico Realista de Manos y 5 Dedos Articulados
        fold_factor_r = fold_factor
        if is_artic and ("dedos_r" in sel_zone or "mano_r" in sel_zone):
            fold_factor_r = max(fold_factor_r, artic_cycle)

        fold_factor_l = (artic_cycle if (is_artic and ("dedos_l" in sel_zone or "mano_l" in sel_zone)) else 0.0)

        palm_l, fng_l = self._compute_hand_and_fingers(wrist_pos_l, hand_pos_l, is_right=False, fold_factor=fold_factor_l)
        palm_r, fng_r = self._compute_hand_and_fingers(wrist_pos_r, hand_pos_r, is_right=True, fold_factor=fold_factor_r)

        # Añadir palmas a la cola de renderizado
        for palm_pts, is_r in [(palm_l, False), (palm_r, True)]:
            avg_z_palm = np.mean([self.rotate_point_3d(px, py, pz, eff_yaw, eff_pitch)[2] for px, py, pz in palm_pts])
            render_queue.append({
                "type": "polygon",
                "points": palm_pts,
                "z": avg_z_palm,
                "fill": "#0f233d" if avg_z_palm > 0 else "#091424",
                "outline": "#38bdf8" if avg_z_palm > 0 else "#1e3a5f",
                "width": 1
            })

        # Añadir 5 dedos articulados para cada mano
        for fingers, is_r in [(fng_l, False), (fng_r, True)]:
            for f_name, f_pts in fingers.items():
                avg_z_fng = np.mean([self.rotate_point_3d(px, py, pz, eff_yaw, eff_pitch)[2] for px, py, pz in f_pts])
                is_active_pinch = (is_r and f_name in ["pulgar", "indice"])
                col = "#38bdf8" if avg_z_fng > 0 else "#1e3a5f"
                if is_active_pinch and fold_factor_r > 0.4:
                    col = "#f43f5e" if fold_factor_r > 0.75 else "#fbbf24"
                
                render_queue.append({
                    "type": "finger_line",
                    "points": f_pts,
                    "z": avg_z_fng,
                    "color": col,
                    "width": 2 if is_active_pinch else 1
                })

        # 7. Mesa de Trabajo y Hoja de Origami Holográfica en 3D
        paper_y = 125.0
        paper_pts = [
            (5.0, paper_y, 45.0),
            (75.0, paper_y, 65.0),
            (25.0, paper_y, 115.0),
            (-45.0, paper_y, 95.0)
        ]
        avg_z_paper = np.mean([self.rotate_point_3d(px, py, pz, eff_yaw, eff_pitch)[2] for px, py, pz in paper_pts])
        render_queue.append({
            "type": "polygon",
            "points": paper_pts,
            "z": avg_z_paper - 2,
            "fill": "#071221",
            "outline": "#1e3a8a",
            "width": 1
        })
        crease_pts = [
            (15.0, paper_y - 1, 55.0),
            (50.0, paper_y - 1, 90.0)
        ]
        render_queue.append({
            "type": "line_strip",
            "points": crease_pts,
            "z": avg_z_paper - 1,
            "color": "#38bdf8",
            "width": 2,
            "dash": (4, 3)
        })

        # ── F. Hotspots Articulares de Lesión en el Espacio 3D ─────────────
        # El hotspot de dedos_r se acopla EXACTAMENTE al punto de contacto de la pinza (pulgar e índice)
        t_tip_r = fng_r["pulgar"][-1]
        i_tip_r = fng_r["indice"][-1]
        dedos_pos_r = ((t_tip_r[0] + i_tip_r[0]) / 2.0, (t_tip_r[1] + i_tip_r[1]) / 2.0, (t_tip_r[2] + i_tip_r[2]) / 2.0)

        # Dedos izquierdos acoplados a las yemas estabilizadoras
        i_tip_l = fng_l["indice"][-1]
        m_tip_l = fng_l["medio"][-1]
        dedos_pos_l = ((i_tip_l[0] + m_tip_l[0]) / 2.0, (i_tip_l[1] + m_tip_l[1]) / 2.0, (i_tip_l[2] + m_tip_l[2]) / 2.0)

        time_mult = self._get_time_multiplier()
        self.projected_hotspots = {}

        hotspots_3d = {
            "cuello":       (0, -90 + neck_dy + neck_tilt, -5, 24),
            "hombro_l":     (sh_pos_l[0], sh_pos_l[1], sh_pos_l[2], 26),
            "hombro_r":     (sh_pos_r[0], sh_pos_r[1], sh_pos_r[2], 26),
            "codo_l":       (elbow_pos_l[0], elbow_pos_l[1], elbow_pos_l[2], 24),
            "codo_r":       (elbow_pos_r[0], elbow_pos_r[1], elbow_pos_r[2], 24),
            "muñeca_l":     (wrist_pos_l[0], wrist_pos_l[1], wrist_pos_l[2], 22),
            "muñeca_r":     (wrist_pos_r[0], wrist_pos_r[1], wrist_pos_r[2], 22),
            "mano_l":       (hand_pos_l[0], hand_pos_l[1], hand_pos_l[2], 20),
            "mano_r":       (hand_pos_r[0], hand_pos_r[1], hand_pos_r[2], 20),
            "dedos_l":      (dedos_pos_l[0], dedos_pos_l[1], dedos_pos_l[2], 19),
            "dedos_r":      (dedos_pos_r[0], dedos_pos_r[1], dedos_pos_r[2], 19),
            "espalda_alta": (0, -25, -34, 25)
        }

        for z_key, (hx, hy, hz, hr) in hotspots_3d.items():
            u, v, rz = self.project_3d(hx, hy, hz, cx, cy, yaw=eff_yaw, pitch=eff_pitch)
            base_imp = self.zone_impacts.get(z_key, 0.4)
            curr_imp = min(1.0, base_imp * time_mult)
            color = self._get_heat_color(curr_imp)
            is_active = (z_key == self.selected_zone.get())
            
            self.projected_hotspots[z_key] = (u, v, hr * self.zoom_level, rz)
            render_queue.append({
                "type": "hotspot",
                "u": u, "v": v, "r": hr * self.zoom_level, "z": rz,
                "color": color, "key": z_key, "active": is_active
            })

        # ── 3. ORDENAR POR PROFUNDIDAD Z Y RENDERIZAR EN CANVAS (Painter's Alg) ─
        render_queue.sort(key=lambda item: item["z"])

        for item in render_queue:
            t = item["type"]
            
            if t == "ring":
                proj_pts = []
                for pt in item["points"]:
                    u, v, _ = self.project_3d(*pt, cx, cy, yaw=eff_yaw, pitch=eff_pitch)
                    proj_pts.extend([u, v])
                if len(proj_pts) >= 4:
                    c.create_polygon(proj_pts, fill="", outline=item["color"], 
                                     width=item["width"], smooth=True)
                                     
            elif t == "polygon":
                proj_pts = []
                for pt in item["points"]:
                    u, v, _ = self.project_3d(*pt, cx, cy, yaw=eff_yaw, pitch=eff_pitch)
                    proj_pts.extend([u, v])
                if len(proj_pts) >= 6:
                    c.create_polygon(proj_pts, fill=item["fill"], outline=item["outline"], 
                                     width=item["width"], smooth=True)

            elif t == "line_strip":
                proj_pts = []
                for pt in item["points"]:
                    u, v, _ = self.project_3d(*pt, cx, cy, yaw=eff_yaw, pitch=eff_pitch)
                    proj_pts.extend([u, v])
                if len(proj_pts) >= 4:
                    dash = item.get("dash")
                    c.create_line(proj_pts, fill=item["color"], width=item["width"], dash=dash, smooth=True)

            elif t == "finger_line":
                proj_pts = []
                for pt in item["points"]:
                    u, v, _ = self.project_3d(*pt, cx, cy, yaw=eff_yaw, pitch=eff_pitch)
                    proj_pts.extend([u, v])
                if len(proj_pts) >= 4:
                    c.create_line(proj_pts, fill=item["color"], width=item["width"], capstyle="round", joinstyle="round", smooth=True)
                if len(proj_pts) >= 2:
                    u_tip, v_tip = proj_pts[-2], proj_pts[-1]
                    r_bead = 2.2 * self.zoom_level
                    c.create_oval(u_tip - r_bead, v_tip - r_bead, u_tip + r_bead, v_tip + r_bead, fill=item["color"], outline="")

            elif t == "segment":
                u1, v1, _ = self.project_3d(*item["p1"], cx, cy, yaw=eff_yaw, pitch=eff_pitch)
                u2, v2, _ = self.project_3d(*item["p2"], cx, cy, yaw=eff_yaw, pitch=eff_pitch)
                c.create_line(u1, v1, u2, v2, fill=item["color"], width=item["width"], capstyle="round")

            elif t == "hotspot":
                u, v, hr, rz = item["u"], item["v"], item["r"], item["z"]
                col = item["color"]
                
                # Ajustar brillo / tamaño por profundidad + pulso vascular
                depth_alpha = max(0.4, min(1.0, (rz + 200) / 400.0))
                eff_r = hr * depth_alpha * (1.0 + 0.18 * heart_pulse)
                
                # Anillo exterior punteado pulsante
                outer_mult = 1.5 + (0.35 * heart_pulse)
                c.create_oval(u - eff_r * outer_mult, v - eff_r * outer_mult, 
                              u + eff_r * outer_mult, v + eff_r * outer_mult,
                              outline=col, fill="", width=2 if (heart_pulse > 0.4 and rz > -20) else 1, 
                              dash=(3, 3))
                # Anillo medio sólido
                c.create_oval(u - eff_r * 1.0, v - eff_r * 1.0, u + eff_r * 1.0, v + eff_r * 1.0,
                              outline=col, fill="", width=2)
                # Núcleo brillante
                c.create_oval(u - eff_r * 0.45, v - eff_r * 0.45, u + eff_r * 0.45, v + eff_r * 0.45,
                              outline="", fill=col)

                # Resaltado de inspección activa (Idéntico a la imagen de referencia del usuario)
                if item["active"]:
                    c.create_oval(u - eff_r * 1.9, v - eff_r * 1.9, u + eff_r * 1.9, v + eff_r * 1.9,
                                  outline="#ffffff", width=2)
                    c.create_rectangle(u - 4, v - 11, u + 84, v + 9, fill="#070d19", outline="", width=0)
                    c.create_text(u + 40, v - 1, text="▶ INSPECCIÓN", fill="#ffffff", font=("Helvetica", 9, "bold"))
'''

content_before = content[:content.find(start_kin_marker)]
content_after = content[content.find(end_render_marker):]

content = content_before + new_kin_and_render + "\n" + content_after

# Also update the status text in Badges (Section 4)
old_status_block = '''            if is_work:
                status_txt = f"⚙️ TRABAJO EN VIVO · Plegado (Codo R: {cur_ang_r:.1f}° · Pinza: {pinch_pct}%)"
                status_col = "#c084fc"
            elif is_motion:
                status_txt = "🫁 RESPIRACIÓN BIOLÓGICA (16 rpm · Pulso: 72 bpm)"
                status_col = "#34d399"
            else:
                status_txt = "⏸ POSTURA ESTÁTICA EN REPOSO"
                status_col = "#94a3b8"'''

new_status_block = '''            pinch_pct = int(fold_factor_r * 100)
            if is_work:
                status_txt = f"⚙️ PLEGADO COORDINADO · Hombro + Codo {cur_ang_r:.1f}° + Muñeca + Dedos ({pinch_pct}%)"
                status_col = "#c084fc"
            elif is_artic:
                z_name = self.PATHOLOGIES_DB.get(sel_zone, {}).get("name", sel_zone)
                status_txt = f"🎯 ARTICULACIÓN ACTIVA · {z_name} ({int(artic_cycle * 100)}%)"
                status_col = "#fbbf24"
            elif is_motion:
                status_txt = "🫁 RESPIRACIÓN BIOLÓGICA (16 rpm · Pulso: 72 bpm)"
                status_col = "#34d399"
            else:
                status_txt = "⏸ POSTURA ESTÁTICA EN REPOSO"
                status_col = "#94a3b8"'''

assert old_status_block in content, "old_status_block not found!"
content = content.replace(old_status_block, new_status_block, 1)

with open(filepath, "w", encoding="utf-8") as f:
    f.write(content)

print("Applied fingers and kinematics update successfully!")

