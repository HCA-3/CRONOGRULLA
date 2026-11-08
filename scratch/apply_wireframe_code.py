new_code = '''    def project_3d(self, x, y, z, cx, cy, fov=650, yaw=None, pitch=None):
        """Aplica perspectiva 3D calibrada a las dimensiones del maniquí holográfico."""
        rx, ry, rz = self.rotate_point_3d(x, y, z, yaw, pitch)
        scale = (fov / (fov + rz)) * self.zoom_level
        u = cx + rx * scale + self.pan_x
        v = cy + ry * scale + self.pan_y
        return u, v, rz

    # ── DIBUJO DEL MANIQUÍ ANATÓMICO 3D (HOLOGRÁFICO DE ANILLOS / ASTRA AI) ────
    def draw_mannequin_3d(self):
        c = self.canvas
        c.delete("all")
        
        w = c.winfo_width() or self.canvas_w
        h = c.winfo_height() or self.canvas_h
        cx = w / 2.0
        cy = (h / 2.0) - 10
        
        gender = self.selected_gender.get()
        is_female = (gender == "Femenino")
        op_name = self.selected_operator.get()

        # ── CÁLCULOS DE CINEMÁTICA HUMANA VIVA (RESPIRACIÓN, PULSO Y TRABAJO) ──
        now = time.time() - self.anim_start_time
        mode_val = self.human_motion_mode.get()
        is_motion = (mode_val != "⏸ Estático")
        is_work = ("Trabajo" in mode_val or "Plegado" in mode_val)

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

        # 2. Ciclo de Trabajo en Vivo (Simulación Cinemática de Plegado de Origami)
        if is_work:
            w_phase = now * 2.1 # Ciclo de ~3.0 seg por doblez
            fold_factor = (math.sin(w_phase - math.pi / 2.0) + 1.0) / 2.0 # 0.0 a 1.0
            neck_tilt = fold_factor * 4.0 # Inclinación atenta del cuello a la mesa
            cur_ang_r = 108.0 - (fold_factor * 26.0) # Flexión dinámica del codo derecho
            pinch_pct = int(fold_factor * 100) # Cierre de pinza digital
        else:
            fold_factor = 0.0
            neck_tilt = 0.0
            cur_ang_r = self.metrics["avg_elbow_r"]
            pinch_pct = 100

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

        # ── E. Extremidades Superiores con Cinemática de Brazos, Manos y Dedos ─
        sh_pos_l = (-sh_w, -sh_drop + shoulder_dy, 0)
        sh_pos_r = (sh_w, -sh_drop + shoulder_dy, 0)

        rad_r = math.radians(cur_ang_r)
        rad_l = math.radians(self.metrics["avg_elbow_l"])

        # Codo izquierdo
        elbow_pos_l = (sh_pos_l[0] - 22, sh_pos_l[1] + 85, 12 + math.cos(rad_l) * 20)
        # Codo derecho (con articulación de trabajo de plegado)
        elbow_pos_r = (sh_pos_r[0] + 22 - (fold_factor * 14.0), 
                       sh_pos_r[1] + 85 - (fold_factor * 16.0), 
                       12 + math.cos(rad_r) * 20 + (fold_factor * 18.0))

        # Muñecas
        wrist_pos_l = (elbow_pos_l[0] + 38, elbow_pos_l[1] + 75, elbow_pos_l[2] + 45)
        wrist_pos_r = (elbow_pos_r[0] - 38 - (fold_factor * 26.0), 
                       elbow_pos_r[1] + 75 - (fold_factor * 20.0), 
                       elbow_pos_r[2] + 45 + (fold_factor * 25.0))

        # Manos (Palmas / Región Tenar)
        hand_pos_l = (wrist_pos_l[0] + 24, wrist_pos_l[1] + 28, wrist_pos_l[2] + 15)
        hand_pos_r = (wrist_pos_r[0] - 24 - (fold_factor * 10.0), 
                      wrist_pos_r[1] + 28 - (fold_factor * 8.0), 
                      wrist_pos_r[2] + 15 + (fold_factor * 12.0))

        # Dedos (Pinza digital activa pulgar e índice)
        dedos_pos_l = (hand_pos_l[0] + 18, hand_pos_l[1] + 22, hand_pos_l[2] + 10)
        dedos_pos_r = (hand_pos_r[0] - 18 - (fold_factor * 8.0), 
                       hand_pos_r[1] + 22 - (fold_factor * 6.0), 
                       hand_pos_r[2] + 10 + (fold_factor * 10.0))

        # Segmentos de brazo, antebrazo, mano y dedos
        segments = [
            (sh_pos_l, elbow_pos_l, 4), (sh_pos_r, elbow_pos_r, 4),
            (elbow_pos_l, wrist_pos_l, 3), (elbow_pos_r, wrist_pos_r, 3),
            (wrist_pos_l, hand_pos_l, 2), (wrist_pos_r, hand_pos_r, 2),
            (hand_pos_l, dedos_pos_l, 2), (hand_pos_r, dedos_pos_r, 2)
        ]
        for p1, p2, w_seg in segments:
            avg_z = (self.rotate_point_3d(*p1, eff_yaw, eff_pitch)[2] + self.rotate_point_3d(*p2, eff_yaw, eff_pitch)[2]) / 2.0
            render_queue.append({
                "type": "segment", "p1": p1, "p2": p2, "z": avg_z,
                "color": "#38bdf8" if avg_z > 0 else "#1e3a5f", "width": w_seg if avg_z > 0 else 1
            })

        # ── F. Hotspots Articulares de Lesión en el Espacio 3D ─────────────
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

        # ── 4. Badges de Información 3D, Operario y Estado ────────────────
        yaw_deg = int(math.degrees(eff_yaw)) % 360
        pitch_deg = int(math.degrees(eff_pitch))
        
        view_label = "VISTA FRONTAL (0°)" if (yaw_deg < 22 or yaw_deg >= 338) else \
                     "PERSPECTIVA DERECHA (45°)" if (22 <= yaw_deg < 68) else \
                     "PERFIL DERECHO (90°)" if (68 <= yaw_deg < 112) else \
                     "PERSPECTIVA POSTERIOR D. (135°)" if (112 <= yaw_deg < 158) else \
                     "VISTA POSTERIOR / ESPALDA (180°)" if (158 <= yaw_deg < 202) else \
                     "PERSPECTIVA POSTERIOR I. (225°)" if (202 <= yaw_deg < 248) else \
                     "PERFIL IZQUIERDO (270°)" if (248 <= yaw_deg < 292) else \
                     "PERSPECTIVA IZQUIERDA (315°)"

        if w >= 220:
            c.create_text(20, 20, anchor="w", 
                          text=f"🔭 {view_label}  |  Giro: {yaw_deg}°",
                          fill="#38bdf8", font=("Helvetica", 10, "bold"))
            
            if is_work:
                status_txt = f"⚙️ TRABAJO EN VIVO · Plegado (Codo R: {cur_ang_r:.1f}° · Pinza: {pinch_pct}%)"
                status_col = "#c084fc"
            elif is_motion:
                status_txt = "🫁 RESPIRACIÓN BIOLÓGICA (16 rpm · Pulso: 72 bpm)"
                status_col = "#34d399"
            else:
                status_txt = "⏸ POSTURA ESTÁTICA EN REPOSO"
                status_col = "#94a3b8"
                
            c.create_text(20, 38, anchor="w",
                          text=status_txt, fill=status_col, font=("Helvetica", 9, "bold"))

            # Nombre de operario en la esquina inferior izquierda (idéntico a la imagen)
            c.create_text(25, h - 30, anchor="w",
                          text=f"Operario: {op_name}",
                          fill="#64748b", font=("Helvetica", 10, "bold"))
                          
            c.create_text(20, h - 12, anchor="w", 
                          text=f"{'Mujer ♀' if is_female else 'Hombre ♂'}  |  Zoom: {int(self.zoom_level*100)}%",
                          fill="#475569", font=("Helvetica", 8))'''

with open("views/view_lesiones_3d.py", "r", encoding="utf-8") as f:
    orig = f.read()

start_marker = "    def project_3d(self, x, y, z, cx, cy, img_scale=1.0, fov=650, yaw=None, pitch=None):"
end_marker = '            c.create_text(20, h - 20, anchor="w", \n                          text=f"{\'Mujer ♀\' if is_female else \'Hombre ♂\'}  |  Zoom: {int(self.zoom_level*100)}%",\n                          fill="#94a3b8", font=("Helvetica", 9))'

idx_start = orig.find(start_marker)
idx_end = orig.find(end_marker)

if idx_start == -1 or idx_end == -1:
    print("ERROR: Markers not found!")
    exit(1)

idx_end += len(end_marker)

updated = orig[:idx_start] + new_code + orig[idx_end:]

with open("views/view_lesiones_3d.py", "w", encoding="utf-8") as f:
    f.write(updated)

print("views/view_lesiones_3d.py successfully updated with 3D Holographic Wireframe Mannequin!")

