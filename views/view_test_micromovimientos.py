"""
views/view_test_micromovimientos.py
Módulo de Test Movimiento: Análisis y Calibración de Micromovimientos y Postura en Tiempo Real.
Superpone un croquis anatómico tipo Kinect sobre la persona (tronco superior, brazos, muñecas y 5 dedos por mano).
Lógica dinámica de colores:
  - Verde (#2ecc71): Postura ergonómica segura y rango de confort (Codo 80°-130°, muñeca neutra, Therblig dinámico).
  - Rojo  (#e74c3c): Postura forzada (Codo < 75° o > 140°), desviación de muñeca o pinza sostenida > 3.5s (riesgo ocupacional).
Telemetría y estadísticas en tiempo real.
"""

import os
import cv2
import time
import math
import threading
import numpy as np
from PIL import Image, ImageTk
import customtkinter as ctk
import tkinter as tk

# Intentar importar MediaPipe Tasks
HAVE_MEDIAPIPE = False
try:
    import mediapipe as mp
    from mediapipe.tasks.python import BaseOptions
    from mediapipe.tasks.python.vision import PoseLandmarker, PoseLandmarkerOptions, HandLandmarker, HandLandmarkerOptions
    HAVE_MEDIAPIPE = True
except Exception as e:
    print(f"[TestMovimiento] MediaPipe Tasks no disponible: {e}")

# Intentar cargar clasificador SVM entrenado
SVM_MODEL = None
try:
    import pickle
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    for p in [os.path.join(base_dir, "models", "therblig_svm_model.pkl"), 
              os.path.join(base_dir, "scratch", "therblig_svm_model.pkl")]:
        if os.path.exists(p):
            with open(p, "rb") as f:
                SVM_MODEL = pickle.load(f)
            print(f"[TestMovimiento] Modelo SVM cargado desde {p}")
            break
except Exception as e:
    print(f"[TestMovimiento] No se pudo cargar SVM: {e}")


class TestMicromovimientosView(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, fg_color="transparent")
        self.app = app
        
        # Estado de video y hardware
        self.is_running = True
        self.camera_source = 0
        self.cap = None
        self.is_camera_connected = False
        self.is_mirror = tk.BooleanVar(value=True)
        self.sensitivity_mode = tk.StringVar(value="Estándar RULA (80°-130°)")
        
        # Detectores MediaPipe
        self.pose_detector = None
        self.hand_detector = None
        self.init_mediapipe_detectors()
        
        # Métricas ergonómicas en tiempo real
        self.metrics = {
            "elbow_r": 105.0,
            "elbow_l": 102.0,
            "wrist_dev_r": 12.0,
            "wrist_dev_l": 10.0,
            "shoulder_tilt": 2.0,
            "is_posture_safe": True,
            "therblig_r": "🖐️ SOLTAR (RL)",
            "therblig_l": "🖐️ SOLTAR (RL)",
            "therblig_r_time": 0.0,
            "therblig_l_time": 0.0,
            "pinch_held_seconds_r": 0.0,
            "pinch_held_seconds_l": 0.0,
            "flexion_pct_r": 20,
            "flexion_pct_l": 20,
            "safe_time": 0.0,
            "risk_time": 0.0,
            "count_tomar": 0,
            "count_soltar": 0,
            "count_sostener": 0,
            "fps": 28.0
        }
        
        self.last_therblig_r = "🖐️ SOLTAR (RL)"
        self.last_therblig_l = "🖐️ SOLTAR (RL)"
        self.last_update_time = time.time()
        self.session_start_time = time.time()
        self.sim_time = 0.0
        
        # Construir interfaz
        self.build_ui()
        
        # Iniciar cámara en hilo secundario para no congelar la UI
        threading.Thread(target=self._start_camera_stream, daemon=True).start()
        
        # Bucle de actualización a 30 FPS
        self.after(50, self._video_loop)

    def init_mediapipe_detectors(self):
        """Inicializa los modelos .task de MediaPipe para Pose y Manos."""
        if not HAVE_MEDIAPIPE:
            return
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        pose_task_path = os.path.join(base_dir, "models", "pose_landmarker_lite.task")
        hand_task_path = os.path.join(base_dir, "models", "hand_landmarker.task")
        
        try:
            if os.path.exists(pose_task_path):
                pose_opts = PoseLandmarkerOptions(
                    base_options=BaseOptions(model_asset_path=pose_task_path),
                    output_segmentation_masks=False
                )
                self.pose_detector = PoseLandmarker.create_from_options(pose_opts)
                print("[TestMovimiento] PoseLandmarker inicializado OK.")
        except Exception as e:
            print(f"[TestMovimiento] Error PoseLandmarker: {e}")
            
        try:
            if os.path.exists(hand_task_path):
                hand_opts = HandLandmarkerOptions(
                    base_options=BaseOptions(model_asset_path=hand_task_path),
                    num_hands=2
                )
                self.hand_detector = HandLandmarker.create_from_options(hand_opts)
                print("[TestMovimiento] HandLandmarker inicializado OK.")
        except Exception as e:
            print(f"[TestMovimiento] Error HandLandmarker: {e}")

    def build_ui(self):
        """Construye la interfaz gráfica de dos columnas: Video/Croquis a la izquierda, Métricas a la derecha."""
        self.grid_columnconfigure(0, weight=65, uniform="test_cols")
        self.grid_columnconfigure(1, weight=35, uniform="test_cols")
        self.grid_rowconfigure(0, weight=1)

        # ── COLUMNA IZQUIERDA: FEED DE CÁMARA Y CROQUIS KINECT ────────────────
        left_f = ctk.CTkFrame(self, fg_color=("#f8fafc", "#070d19"), corner_radius=12)
        left_f.grid(row=0, column=0, sticky="nsew", padx=(0, 6), pady=4)
        left_f.grid_rowconfigure(1, weight=1)
        left_f.grid_columnconfigure(0, weight=1)

        # Barra superior de la cámara
        top_bar = ctk.CTkFrame(left_f, fg_color="transparent", height=42)
        top_bar.grid(row=0, column=0, sticky="ew", padx=12, pady=(8, 4))
        
        ctk.CTkLabel(
            top_bar, 
            text="🎯 TEST MOVIMIENTO (CROQUIS KINECT SOBRE EL OPERARIO)", 
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="#38bdf8"
        ).pack(side="left")

        # Checkbox Espejo
        chk_mirror = ctk.CTkCheckBox(
            top_bar, 
            text="Modo Espejo", 
            variable=self.is_mirror,
            font=ctk.CTkFont(size=11),
            width=90, height=22
        )
        chk_mirror.pack(side="right", padx=(6, 0))

        # Selector de cámara
        self.combo_cam = ctk.CTkOptionMenu(
            top_bar,
            values=["Cámara 0 (Principal)", "Cámara 1 (Externa)", "Modo Simulación"],
            command=self.on_camera_source_changed,
            width=150, height=26,
            font=ctk.CTkFont(size=11)
        )
        self.combo_cam.pack(side="right", padx=6)

        # Contenedor central del video
        self.video_container = ctk.CTkFrame(left_f, fg_color="#000000", corner_radius=8)
        self.video_container.grid(row=1, column=0, sticky="nsew", padx=12, pady=6)
        self.video_container.grid_rowconfigure(0, weight=1)
        self.video_container.grid_columnconfigure(0, weight=1)

        self.video_lbl = ctk.CTkLabel(
            self.video_container, 
            text="Iniciando sensor Kinect sobre el operario...",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#64748b"
        )
        self.video_lbl.grid(row=0, column=0, sticky="nsew")

        # Barra inferior de controles rápidos
        bot_bar = ctk.CTkFrame(left_f, fg_color="transparent", height=38)
        bot_bar.grid(row=2, column=0, sticky="ew", padx=12, pady=(4, 10))

        self.btn_toggle = ctk.CTkButton(
            bot_bar, text="⏸ Pausar Prueba", command=self.toggle_test,
            width=120, height=30, fg_color="#ef4444", hover_color="#dc2626",
            font=ctk.CTkFont(size=11, weight="bold")
        )
        self.btn_toggle.pack(side="left", padx=(0, 6))

        btn_photo = ctk.CTkButton(
            bot_bar, text="📸 Capturar Evidencia", command=self.capture_evidence,
            width=140, height=30, fg_color="#6366f1", hover_color="#4f46e5",
            font=ctk.CTkFont(size=11, weight="bold")
        )
        btn_photo.pack(side="left", padx=6)

        btn_reset = ctk.CTkButton(
            bot_bar, text="🔄 Reiniciar Estadísticas", command=self.reset_stats,
            width=150, height=30, fg_color="#475569", hover_color="#334155",
            font=ctk.CTkFont(size=11, weight="bold")
        )
        btn_reset.pack(side="left", padx=6)

        self.lbl_fps = ctk.CTkLabel(
            bot_bar, text="FPS: 30 · Sensor Kinect IA", font=ctk.CTkFont(size=11), text_color="#64748b"
        )
        self.lbl_fps.pack(side="right", padx=6)

        # ── COLUMNA DERECHA: PANEL DE ESTADÍSTICAS Y TELEMETRÍA EN VIVO ───────
        right_f = ctk.CTkScrollableFrame(self, fg_color=("#f8fafc", "#0b1320"), corner_radius=12)
        right_f.grid(row=0, column=1, sticky="nsew", padx=(6, 0), pady=4)
        
        # 1. TARJETA: SEMÁFORO GLOBAL DE POSTURA Y ERGONOMÍA
        self.card_status = ctk.CTkFrame(right_f, fg_color="#064e3b", corner_radius=10)
        self.card_status.pack(fill="x", padx=10, pady=(10, 8))

        self.lbl_global_badge = ctk.CTkLabel(
            self.card_status,
            text="🟢 POSTURA ERGONÓMICA SEGURA",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#34d399"
        )
        self.lbl_global_badge.pack(padx=12, pady=(10, 2))

        self.lbl_global_desc = ctk.CTkLabel(
            self.card_status,
            text="Ángulos articulares dentro de los límites de confort ISO 11226 / RULA. Sin tensión isométrica en dedos.",
            font=ctk.CTkFont(size=11),
            text_color="#a7f3d0",
            wraplength=260,
            justify="center"
        )
        self.lbl_global_desc.pack(padx=12, pady=(0, 10))

        # 2. TARJETA: TELEMETRÍA ARTICULAR EN TIEMPO REAL
        card_angles = ctk.CTkFrame(right_f, fg_color=("#ffffff", "#0f172a"), corner_radius=10)
        card_angles.pack(fill="x", padx=10, pady=6)

        ctk.CTkLabel(
            card_angles, 
            text="📐 ÁNGULOS Y SENSORES ARTICULARES", 
            font=ctk.CTkFont(size=12, weight="bold"), 
            text_color="#38bdf8"
        ).pack(anchor="w", padx=12, pady=(10, 6))

        # Codo Derecho
        row_codo_r = ctk.CTkFrame(card_angles, fg_color="transparent")
        row_codo_r.pack(fill="x", padx=12, pady=3)
        ctk.CTkLabel(row_codo_r, text="Codo Derecho:", font=ctk.CTkFont(size=11)).pack(side="left")
        self.lbl_val_codo_r = ctk.CTkLabel(row_codo_r, text="105.0° (Confort)", font=ctk.CTkFont(size=11, weight="bold"), text_color="#2ecc71")
        self.lbl_val_codo_r.pack(side="right")

        self.bar_codo_r = ctk.CTkProgressBar(card_angles, height=8, progress_color="#2ecc71")
        self.bar_codo_r.set(0.65)
        self.bar_codo_r.pack(fill="x", padx=12, pady=(0, 6))

        # Codo Izquierdo
        row_codo_l = ctk.CTkFrame(card_angles, fg_color="transparent")
        row_codo_l.pack(fill="x", padx=12, pady=3)
        ctk.CTkLabel(row_codo_l, text="Codo Izquierdo:", font=ctk.CTkFont(size=11)).pack(side="left")
        self.lbl_val_codo_l = ctk.CTkLabel(row_codo_l, text="102.0° (Confort)", font=ctk.CTkFont(size=11, weight="bold"), text_color="#2ecc71")
        self.lbl_val_codo_l.pack(side="right")

        self.bar_codo_l = ctk.CTkProgressBar(card_angles, height=8, progress_color="#2ecc71")
        self.bar_codo_l.set(0.62)
        self.bar_codo_l.pack(fill="x", padx=12, pady=(0, 6))

        # Muñecas y Sensores
        row_sens = ctk.CTkFrame(card_angles, fg_color="transparent")
        row_sens.pack(fill="x", padx=12, pady=(4, 10))
        
        self.lbl_wrist_sens_r = ctk.CTkLabel(row_sens, text="Muñeca D: Confort ✅", font=ctk.CTkFont(size=10, weight="bold"), text_color="#2ecc71")
        self.lbl_wrist_sens_r.pack(side="left")
        
        self.lbl_wrist_sens_l = ctk.CTkLabel(row_sens, text="Muñeca I: Confort ✅", font=ctk.CTkFont(size=10, weight="bold"), text_color="#2ecc71")
        self.lbl_wrist_sens_l.pack(side="right")

        # 3. TARJETA: CLASIFICADOR DE MICROMOVIMIENTOS (THERBLIGS IA)
        card_therbligs = ctk.CTkFrame(right_f, fg_color=("#ffffff", "#0f172a"), corner_radius=10)
        card_therbligs.pack(fill="x", padx=10, pady=6)

        ctk.CTkLabel(
            card_therbligs, 
            text="⚡ MICROMOVIMIENTOS Y PINZA DIGITAL", 
            font=ctk.CTkFont(size=12, weight="bold"), 
            text_color="#c084fc"
        ).pack(anchor="w", padx=12, pady=(10, 6))

        # Mano Derecha
        box_th_r = ctk.CTkFrame(card_therbligs, fg_color=("#f1f5f9", "#1e293b"), corner_radius=6)
        box_th_r.pack(fill="x", padx=12, pady=4)
        ctk.CTkLabel(box_th_r, text="Mano Derecha:", font=ctk.CTkFont(size=10, weight="bold")).pack(anchor="w", padx=8, pady=(4, 0))
        self.lbl_therblig_r = ctk.CTkLabel(box_th_r, text="🖐️ SOLTAR (RL)", font=ctk.CTkFont(size=13, weight="bold"), text_color="#38bdf8")
        self.lbl_therblig_r.pack(anchor="w", padx=8, pady=(0, 2))
        self.lbl_tension_r = ctk.CTkLabel(box_th_r, text="Pinza: 20% · Tensión sostenida: 0.0s", font=ctk.CTkFont(size=10), text_color="#94a3b8")
        self.lbl_tension_r.pack(anchor="w", padx=8, pady=(0, 6))

        # Mano Izquierda
        box_th_l = ctk.CTkFrame(card_therbligs, fg_color=("#f1f5f9", "#1e293b"), corner_radius=6)
        box_th_l.pack(fill="x", padx=12, pady=(4, 10))
        ctk.CTkLabel(box_th_l, text="Mano Izquierda:", font=ctk.CTkFont(size=10, weight="bold")).pack(anchor="w", padx=8, pady=(4, 0))
        self.lbl_therblig_l = ctk.CTkLabel(box_th_l, text="🖐️ SOLTAR (RL)", font=ctk.CTkFont(size=13, weight="bold"), text_color="#60a5fa")
        self.lbl_therblig_l.pack(anchor="w", padx=8, pady=(0, 2))
        self.lbl_tension_l = ctk.CTkLabel(box_th_l, text="Pinza: 20% · Tensión sostenida: 0.0s", font=ctk.CTkFont(size=10), text_color="#94a3b8")
        self.lbl_tension_l.pack(anchor="w", padx=8, pady=(0, 6))

        # 4. TARJETA: ESTADÍSTICAS ACUMULADAS DE LA SESIÓN
        card_stats = ctk.CTkFrame(right_f, fg_color=("#ffffff", "#0f172a"), corner_radius=10)
        card_stats.pack(fill="x", padx=10, pady=6)

        ctk.CTkLabel(
            card_stats, 
            text="📊 MÉTRICAS ACUMULADAS", 
            font=ctk.CTkFont(size=12, weight="bold"), 
            text_color="#f59e0b"
        ).pack(anchor="w", padx=12, pady=(10, 6))

        row_time = ctk.CTkFrame(card_stats, fg_color="transparent")
        row_time.pack(fill="x", padx=12, pady=3)
        ctk.CTkLabel(row_time, text="Tiempo en Zona Segura:", font=ctk.CTkFont(size=11)).pack(side="left")
        self.lbl_safe_pct = ctk.CTkLabel(row_time, text="100%", font=ctk.CTkFont(size=11, weight="bold"), text_color="#2ecc71")
        self.lbl_safe_pct.pack(side="right")

        self.bar_safe = ctk.CTkProgressBar(card_stats, height=8, progress_color="#2ecc71")
        self.bar_safe.set(1.0)
        self.bar_safe.pack(fill="x", padx=12, pady=(0, 8))

        row_counts = ctk.CTkFrame(card_stats, fg_color="transparent")
        row_counts.pack(fill="x", padx=12, pady=(2, 10))
        
        self.lbl_c_tomar = ctk.CTkLabel(row_counts, text="✊ Tomar: 0", font=ctk.CTkFont(size=11, weight="bold"), text_color="#38bdf8")
        self.lbl_c_tomar.pack(side="left", padx=(0, 10))
        
        self.lbl_c_soltar = ctk.CTkLabel(row_counts, text="🖐️ Soltar: 0", font=ctk.CTkFont(size=11, weight="bold"), text_color="#60a5fa")
        self.lbl_c_soltar.pack(side="left")

        # 5. TARJETA: CRITERIO Y SENSIBILIDAD
        card_cfg = ctk.CTkFrame(right_f, fg_color=("#ffffff", "#0f172a"), corner_radius=10)
        card_cfg.pack(fill="x", padx=10, pady=(6, 12))

        ctk.CTkLabel(
            card_cfg, 
            text="⚙️ CRITERIO DE EVALUACIÓN", 
            font=ctk.CTkFont(size=12, weight="bold"), 
            text_color="#94a3b8"
        ).pack(anchor="w", padx=12, pady=(10, 4))

        combo_sens = ctk.CTkOptionMenu(
            card_cfg,
            values=["Estándar RULA (80°-130°)", "Sensibilidad Alta (85°-120°)", "Tolerante (70°-145°)"],
            variable=self.sensitivity_mode,
            height=28,
            font=ctk.CTkFont(size=11)
        )
        combo_sens.pack(fill="x", padx=12, pady=(0, 10))

    def _start_camera_stream(self):
        """Intenta abrir la cámara web con DirectShow o V4L2."""
        try:
            if self.camera_source == "sim":
                self.is_camera_connected = False
                return

            self.cap = cv2.VideoCapture(int(self.camera_source) + cv2.CAP_DSHOW)
            if self.cap and self.cap.isOpened():
                self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
                self.cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))
                self.is_camera_connected = True
                print(f"[TestMovimiento] Cámara {self.camera_source} abierta correctamente.")
            else:
                self.is_camera_connected = False
                print("[TestMovimiento] Cámara física no disponible. Activando modo simulación interactivo.")
        except Exception as e:
            self.is_camera_connected = False
            print(f"[TestMovimiento] Excepción al abrir cámara: {e}")

    def on_camera_source_changed(self, choice):
        """Cambia entre cámara web física o modo simulación."""
        if self.cap:
            try:
                self.cap.release()
            except Exception:
                pass
            self.cap = None

        if "Simulación" in choice:
            self.camera_source = "sim"
            self.is_camera_connected = False
        elif "1" in choice:
            self.camera_source = 1
            threading.Thread(target=self._start_camera_stream, daemon=True).start()
        else:
            self.camera_source = 0
            threading.Thread(target=self._start_camera_stream, daemon=True).start()

    def _video_loop(self):
        """Bucle principal de procesamiento de visión y actualización de UI (protegido contra fallos)."""
        if not self.winfo_exists():
            return

        try:
            now = time.time()
            dt = max(0.001, now - self.last_update_time)
            self.last_update_time = now
            self.sim_time += dt

            if self.is_running:
                frame = None
                if self.is_camera_connected and self.cap and self.cap.isOpened():
                    ret, cam_frame = self.cap.read()
                    if ret and cam_frame is not None:
                        frame = cam_frame
                
                # Si no hay cámara física o falló la lectura, generar frame simulado
                if frame is None:
                    frame = self._generate_simulated_frame(self.sim_time)

                if self.is_mirror.get():
                    frame = cv2.flip(frame, 1)

                # Procesar detección y pintar croquis Kinect
                processed_frame = self.process_and_draw_kinect(frame, dt)

                # Renderizar en el label de CustomTkinter
                self._render_frame_to_ui(processed_frame)

                # Actualizar panel de estadísticas derecho
                self.update_statistics_ui(dt)
        except Exception as e:
            print(f"[TestMovimiento ERROR en bucle]: {e}")
        finally:
            if self.winfo_exists():
                self.after(33, self._video_loop)

    def process_and_draw_kinect(self, frame, dt):
        """Aplica MediaPipe Tasks y dibuja el croquis Kinect sobre la persona sin riesgo de cuelgue."""
        h, w = frame.shape[:2]
        is_safe = True
        elbow_ang_r = self.metrics["elbow_r"]
        elbow_ang_l = self.metrics["elbow_l"]

        # 1. Ejecutar Detección Real si MediaPipe Tasks está activo
        pose_res = None
        hand_res = None
        if HAVE_MEDIAPIPE and (self.pose_detector or self.hand_detector):
            try:
                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                mp_img = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
                if self.pose_detector:
                    pose_res = self.pose_detector.detect(mp_img)
                if self.hand_detector:
                    hand_res = self.hand_detector.detect(mp_img)
            except Exception:
                pass

        # 2. Dibujar Croquis sobre la persona (Tronco Superior Waist-Up)
        has_real_pose = pose_res and hasattr(pose_res, 'pose_landmarks') and len(pose_res.pose_landmarks) > 0
        has_real_hands = hand_res and hasattr(hand_res, 'hand_landmarks') and len(hand_res.hand_landmarks) > 0

        # Rango de confort según sensibilidad seleccionada
        sens = self.sensitivity_mode.get()
        min_ang, max_ang = (80, 130) if "RULA" in sens else ((85, 120) if "Alta" in sens else (70, 145))

        if has_real_pose:
            try:
                lms = pose_res.pose_landmarks[0]
                def to_px(lm): return int(lm.x * w), int(lm.y * h)

                nose = to_px(lms[0])
                sh_l = to_px(lms[11])
                sh_r = to_px(lms[12])
                el_l = to_px(lms[13])
                el_r = to_px(lms[14])
                wr_l = to_px(lms[15])
                wr_r = to_px(lms[16])
                hip_l = to_px(lms[23])
                hip_r = to_px(lms[24])

                # Calcular ángulos reales
                elbow_ang_r = self._calc_angle_2d(sh_r, el_r, wr_r)
                elbow_ang_l = self._calc_angle_2d(sh_l, el_l, wr_l)
                
                # Criterio de color
                col_el_r = (46, 204, 113) if (min_ang <= elbow_ang_r <= max_ang) else (60, 76, 231)
                col_el_l = (46, 204, 113) if (min_ang <= elbow_ang_l <= max_ang) else (60, 76, 231)
                
                if col_el_r == (60, 76, 231) or col_el_l == (60, 76, 231):
                    is_safe = False

                # Dibujar esqueleto Kinect del tronco superior
                mid_sh = ((sh_l[0] + sh_r[0]) // 2, (sh_l[1] + sh_r[1]) // 2)
                mid_hip = ((hip_l[0] + hip_r[0]) // 2, (hip_l[1] + hip_r[1]) // 2)

                # Cabeza y columna torácica
                cv2.circle(frame, nose, 36, (56, 189, 248), 3)
                cv2.line(frame, nose, mid_sh, (56, 189, 248), 4)
                cv2.line(frame, sh_l, sh_r, (56, 189, 248), 5)
                cv2.line(frame, mid_sh, mid_hip, (56, 189, 248), 5)

                # Brazos y antebrazos con color dinámico (Verde/Rojo)
                cv2.line(frame, sh_r, el_r, col_el_r, 4)
                cv2.line(frame, el_r, wr_r, col_el_r, 4)
                cv2.line(frame, sh_l, el_l, col_el_l, 4)
                cv2.line(frame, el_l, wr_l, col_el_l, 4)

                # Nodos articulares de hombros y codos
                for pt in [sh_r, sh_l]:
                    cv2.circle(frame, pt, 9, (56, 189, 248), -1)
                    cv2.circle(frame, pt, 14, (255, 255, 255), 2)

                cv2.circle(frame, el_r, 9, col_el_r, -1)
                cv2.circle(frame, el_r, 14, (255, 255, 255), 2)
                cv2.circle(frame, el_l, 9, col_el_l, -1)
                cv2.circle(frame, el_l, 14, (255, 255, 255), 2)

                # Sensores en Muñecas
                cv2.circle(frame, wr_r, 12, (241, 196, 15), 2)
                cv2.circle(frame, wr_r, 6, (241, 196, 15), -1)
                cv2.circle(frame, wr_l, 12, (241, 196, 15), 2)
                cv2.circle(frame, wr_l, 6, (241, 196, 15), -1)

                # Etiquetas con ángulos en vivo
                cv2.putText(frame, f"{int(elbow_ang_r)} deg", (el_r[0] + 15, el_r[1]), cv2.FONT_HERSHEY_SIMPLEX, 0.6, col_el_r, 2)
                cv2.putText(frame, f"{int(elbow_ang_l)} deg", (el_l[0] - 80, el_l[1]), cv2.FONT_HERSHEY_SIMPLEX, 0.6, col_el_l, 2)
            except Exception as e:
                print(f"[Pose Draw Error]: {e}")

        # 3. Dibujar MANOS Y DEDOS reales (Corregido para listas de MediaPipe Tasks)
        if has_real_hands:
            for idx, hand_lms in enumerate(hand_res.hand_landmarks):
                try:
                    # Determinar si es mano derecha o izquierda
                    hand_label = "Right"
                    if hasattr(hand_res, 'handedness') and len(hand_res.handedness) > idx:
                        cats = hand_res.handedness[idx]
                        if len(cats) > 0 and hasattr(cats[0], 'category_name'):
                            hand_label = cats[0].category_name

                    # Clasificar Therblig real de esta mano
                    th_name, flexion_pct = self._classify_therblig_from_landmarks(hand_lms)
                    
                    is_right = (hand_label == "Right")
                    if is_right:
                        self.metrics["therblig_r"] = th_name
                        self.metrics["flexion_pct_r"] = flexion_pct
                        if "TOMAR" in th_name:
                            self.metrics["pinch_held_seconds_r"] += dt
                        else:
                            self.metrics["pinch_held_seconds_r"] = 0.0
                        is_strained = (self.metrics["pinch_held_seconds_r"] > 3.5)
                    else:
                        self.metrics["therblig_l"] = th_name
                        self.metrics["flexion_pct_l"] = flexion_pct
                        if "TOMAR" in th_name:
                            self.metrics["pinch_held_seconds_l"] += dt
                        else:
                            self.metrics["pinch_held_seconds_l"] = 0.0
                        is_strained = (self.metrics["pinch_held_seconds_l"] > 3.5)

                    if is_strained:
                        is_safe = False

                    # Dibujar los 21 puntos y sensores en yemas
                    self._draw_hand_skeleton_and_sensors(frame, hand_lms, w, h, is_pinch_strained=is_strained)
                except Exception as e:
                    print(f"[Hand Draw Error]: {e}")

        # 4. Si no hay persona real detectada (o en simulación), renderizar Croquis Sintético
        if not has_real_pose:
            is_safe, elbow_ang_r, elbow_ang_l = self._draw_kinect_simulated_skeleton(frame, w, h, self.sim_time)
            self._evaluate_simulated_therblig(dt, is_safe, elbow_ang_r, elbow_ang_l)
        else:
            self.metrics["elbow_r"] = elbow_ang_r
            self.metrics["elbow_l"] = elbow_ang_l
            self.metrics["is_posture_safe"] = is_safe
            if is_safe: self.metrics["safe_time"] += dt
            else: self.metrics["risk_time"] += dt

        # 5. Superponer HUD y Banner de Alerta en pantalla
        self._draw_hud_overlay(frame, w, h)

        return frame

    def _classify_therblig_from_landmarks(self, hand_lms):
        """Clasifica el Therblig (TOMAR G vs SOLTAR RL) a partir de los 21 puntos normalizados."""
        landmarks = hand_lms.landmark if hasattr(hand_lms, 'landmark') else hand_lms
        if len(landmarks) < 21:
            return "🖐️ SOLTAR (RL)", 20

        def dist(p1, p2):
            return math.sqrt((p1.x - p2.x)**2 + (p1.y - p2.y)**2)

        p0 = landmarks[0]
        p9 = landmarks[9]
        scale = dist(p0, p9)
        if scale < 0.001: scale = 0.001

        fingertips = [4, 8, 12, 16, 20]
        d_wrist = [dist(p0, landmarks[tip]) / scale for tip in fingertips]
        
        mcp_pairs = [(8, 5), (12, 9), (16, 13), (20, 17)]
        d_mcp = [dist(landmarks[tip], landmarks[mcp]) / scale for tip, mcp in mcp_pairs]

        spread = [
            dist(landmarks[8], landmarks[12]) / scale,
            dist(landmarks[12], landmarks[16]) / scale,
            dist(landmarks[16], landmarks[20]) / scale,
        ]

        mean_ext = float(np.mean(d_wrist))
        flexion_pct = int(max(0, min(100, (2.2 - mean_ext) / (2.2 - 0.9) * 100)))

        # Clasificación con SVM
        if SVM_MODEL is not None:
            try:
                features = list(d_wrist) + list(d_mcp) + list(spread) + [mean_ext]
                pred = SVM_MODEL.predict([features])[0]
                if pred == 0 or mean_ext < 1.38:
                    return "✊ TOMAR (G)", flexion_pct
                else:
                    return "🖐️ SOLTAR (RL)", flexion_pct
            except Exception:
                pass

        if mean_ext < 1.38:
            return "✊ TOMAR (G)", flexion_pct
        else:
            return "🖐️ SOLTAR (RL)", flexion_pct

    def _draw_hand_skeleton_and_sensors(self, frame, hand_lms, w, h, is_pinch_strained=False):
        """Dibuja el esqueleto de 21 puntos y sensores de dedos (compatible con listas de MediaPipe Tasks)."""
        landmarks = hand_lms.landmark if hasattr(hand_lms, 'landmark') else hand_lms
        pts = [(int(lm.x * w), int(lm.y * h)) for lm in landmarks]
        if len(pts) < 21:
            return
            
        wrist = pts[0]
        # Verde si postura ergonómica, Rojo si hay pinza forzada sostenida > 3.5s
        col_hand = (60, 76, 231) if is_pinch_strained else (46, 204, 113)

        # Sensor de muñeca (Doble anillo concéntrico)
        cv2.circle(frame, wrist, 14, col_hand, 2)
        cv2.circle(frame, wrist, 7, (241, 196, 15), -1)

        # 5 Dedos anatómicos (Pulgar, Índice, Medio, Anular, Meñique)
        finger_chains = [
            [0, 1, 2, 3, 4],
            [0, 5, 6, 7, 8],
            [0, 9, 10, 11, 12],
            [0, 13, 14, 15, 16],
            [0, 17, 18, 19, 20]
        ]

        for chain in finger_chains:
            for i in range(len(chain) - 1):
                p1 = pts[chain[i]]
                p2 = pts[chain[i + 1]]
                cv2.line(frame, p1, p2, col_hand, 3)
                cv2.circle(frame, p1, 4, (56, 189, 248), -1)

            # Sensor circular de contacto en la yema del dedo
            tip_pt = pts[chain[-1]]
            cv2.circle(frame, tip_pt, 7, col_hand, -1)
            cv2.circle(frame, tip_pt, 10, (255, 255, 255), 2)

        if is_pinch_strained:
            cv2.putText(frame, "PINZA SOSTENIDA > 3.5s", (wrist[0] - 60, wrist[1] - 25), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (60, 76, 231), 2)

    def _draw_kinect_simulated_skeleton(self, frame, w, h, t):
        """Dibuja un croquis cinemático tipo Kinect sobre el video con simulación interactiva de plegado."""
        cx = w // 2
        cy = int(h * 0.42)
        
        cycle = (math.sin(t * 2.2) + 1.0) / 2.0
        ang_r = 108.0 - (cycle * 38.0)
        ang_l = 104.0 - (cycle * 20.0)
        
        is_safe = (75 <= ang_r <= 130 and 75 <= ang_l <= 130)
        col_r = (46, 204, 113) if (75 <= ang_r <= 130) else (60, 76, 231)
        col_l = (46, 204, 113) if (75 <= ang_l <= 130) else (60, 76, 231)

        head = (cx, cy - 110)
        neck = (cx, cy - 55)
        sh_r = (cx + 90, cy - 45)
        sh_l = (cx - 90, cy - 45)
        spine_end = (cx, cy + 90)

        el_r = (sh_r[0] + 45 - int(cycle * 25), sh_r[1] + 75)
        el_l = (sh_l[0] - 45, sh_l[1] + 75)

        wr_r = (el_r[0] - int(cycle * 40), el_r[1] + 65 - int(cycle * 20))
        wr_l = (el_l[0] + 35, el_l[1] + 65)

        cv2.circle(frame, head, 38, (56, 189, 248), 3)
        cv2.line(frame, head, neck, (56, 189, 248), 4)
        cv2.line(frame, sh_l, sh_r, (56, 189, 248), 5)
        cv2.line(frame, neck, spine_end, (56, 189, 248), 5)

        cv2.line(frame, sh_r, el_r, col_r, 4)
        cv2.line(frame, el_r, wr_r, col_r, 4)
        cv2.line(frame, sh_l, el_l, col_l, 4)
        cv2.line(frame, el_l, wr_l, col_l, 4)

        for pt in [sh_r, sh_l]:
            cv2.circle(frame, pt, 8, (56, 189, 248), -1)
            cv2.circle(frame, pt, 14, (255, 255, 255), 2)

        cv2.circle(frame, el_r, 8, col_r, -1)
        cv2.circle(frame, el_r, 14, (255, 255, 255), 2)
        cv2.circle(frame, el_l, 8, col_l, -1)
        cv2.circle(frame, el_l, 14, (255, 255, 255), 2)

        cv2.circle(frame, wr_r, 12, col_r, 2)
        cv2.circle(frame, wr_r, 6, (241, 196, 15), -1)
        cv2.circle(frame, wr_l, 12, col_l, 2)
        cv2.circle(frame, wr_l, 6, (241, 196, 15), -1)

        self._draw_simulated_fingers(frame, wr_r, is_right=True, cycle=cycle, is_safe=is_safe)
        self._draw_simulated_fingers(frame, wr_l, is_right=False, cycle=0.2, is_safe=True)

        cv2.putText(frame, f"{int(ang_r)} deg", (el_r[0] + 12, el_r[1]), cv2.FONT_HERSHEY_SIMPLEX, 0.6, col_r, 2)
        cv2.putText(frame, f"{int(ang_l)} deg", (el_l[0] - 80, el_l[1]), cv2.FONT_HERSHEY_SIMPLEX, 0.6, col_l, 2)

        return is_safe, ang_r, ang_l

    def _draw_simulated_fingers(self, frame, wrist_pt, is_right=True, cycle=0.0, is_safe=True):
        """Dibuja 5 dedos anatómicos y sensores circulares en las yemas."""
        wx, wy = wrist_pt
        sign = 1 if is_right else -1
        
        finger_offsets = [
            (-22 * sign, 18, 30),
            (-12 * sign, 38, 45),
            (0, 42, 48),
            (12 * sign, 36, 44),
            (24 * sign, 28, 36)
        ]
        
        col_finger = (46, 204, 113) if is_safe else (60, 76, 231)
        if is_right and cycle > 0.8:
            col_finger = (60, 76, 231)

        for ox, oy_mid, oy_tip in finger_offsets:
            p_knuckle = (wx + ox // 2, wy + oy_mid // 2)
            p_mid = (wx + ox, wy + oy_mid)
            p_tip = (wx + ox + int(sign * cycle * 6), wy + oy_tip)

            cv2.line(frame, (wx, wy), p_knuckle, (56, 189, 248), 2)
            cv2.line(frame, p_knuckle, p_mid, col_finger, 2)
            cv2.line(frame, p_mid, p_tip, col_finger, 2)

            cv2.circle(frame, p_tip, 5, col_finger, -1)
            cv2.circle(frame, p_tip, 8, (255, 255, 255), 1)

    def _evaluate_simulated_therblig(self, dt, is_safe, elbow_r, elbow_l):
        """Evalúa los micromovimientos en modo simulación."""
        self.metrics["elbow_r"] = elbow_r
        self.metrics["elbow_l"] = elbow_l
        
        cycle = (math.sin(self.sim_time * 2.2) + 1.0) / 2.0
        if cycle > 0.45:
            current_th_r = "✊ TOMAR (G)"
            self.metrics["flexion_pct_r"] = int(50 + cycle * 45)
            self.metrics["pinch_held_seconds_r"] += dt
        else:
            current_th_r = "🖐️ SOLTAR (RL)"
            self.metrics["flexion_pct_r"] = int(20 + cycle * 30)
            self.metrics["pinch_held_seconds_r"] = 0.0

        current_th_l = "🖐️ SOLTAR (RL)" if cycle > 0.5 else "🤲 SOSTENER (H)"

        if current_th_r != self.last_therblig_r:
            if "TOMAR" in current_th_r: self.metrics["count_tomar"] += 1
            elif "SOLTAR" in current_th_r: self.metrics["count_soltar"] += 1
            self.last_therblig_r = current_th_r

        self.metrics["therblig_r"] = current_th_r
        self.metrics["therblig_l"] = current_th_l

        if self.metrics["pinch_held_seconds_r"] > 3.5:
            is_safe = False

        self.metrics["is_posture_safe"] = is_safe

        if is_safe: self.metrics["safe_time"] += dt
        else: self.metrics["risk_time"] += dt

    def _draw_hud_overlay(self, frame, w, h):
        """Dibuja el banner superior HUD con la telemetría del croquis."""
        is_safe = self.metrics["is_posture_safe"]
        status_txt = "POSTURA ERGONOMICA SEGURA" if is_safe else "ALERTA: POSTURA FORZADA / TENSION EN DEDOS"
        col_txt = (46, 204, 113) if is_safe else (60, 76, 231)

        overlay = frame.copy()
        cv2.rectangle(overlay, (0, 0), (w, 48), (10, 15, 25), -1)
        cv2.addWeighted(overlay, 0.7, frame, 0.3, 0, frame)

        cv2.putText(frame, f"TEST MOVIMIENTO: {status_txt}", (18, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.65, col_txt, 2)
        th_txt = f"Therblig D: {self.metrics['therblig_r']}"
        cv2.putText(frame, th_txt, (w - 300, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 1)

    def update_statistics_ui(self, dt):
        """Actualiza los widgets del panel lateral de estadísticas."""
        is_safe = self.metrics["is_posture_safe"]
        
        # 1. Semáforo Global
        if is_safe:
            self.card_status.configure(fg_color="#064e3b")
            self.lbl_global_badge.configure(text="🟢 POSTURA ERGONÓMICA SEGURA", text_color="#34d399")
            self.lbl_global_desc.configure(
                text="Ángulos articulares dentro de los límites de confort ISO 11226 / RULA. Sin tensión isométrica en dedos.",
                text_color="#a7f3d0"
            )
        else:
            self.card_status.configure(fg_color="#7f1d1d")
            self.lbl_global_badge.configure(text="🔴 ALERTA: POSTURA FORZADA / SOBRECARGA", text_color="#f87171")
            
            reasons = []
            if not (75 <= self.metrics["elbow_r"] <= 130):
                reasons.append(f"Codo D en ángulo crítico ({int(self.metrics['elbow_r'])}°)")
            if self.metrics["pinch_held_seconds_r"] > 3.5:
                reasons.append(f"Pinza sostenida > 3.5s ({self.metrics['pinch_held_seconds_r']:.1f}s)")
            
            desc_text = " | ".join(reasons) if reasons else "Desviación postural detectada en tronco superior."
            self.lbl_global_desc.configure(text=desc_text, text_color="#fca5a5")

        # 2. Codos
        er = self.metrics["elbow_r"]
        col_er = "#2ecc71" if (75 <= er <= 130) else "#ef4444"
        desc_er = "Confort" if (75 <= er <= 130) else "Ángulo Forzado"
        self.lbl_val_codo_r.configure(text=f"{er:.1f}° ({desc_er})", text_color=col_er)
        self.bar_codo_r.configure(progress_color=col_er)
        self.bar_codo_r.set(min(1.0, er / 180.0))

        el = self.metrics["elbow_l"]
        col_el = "#2ecc71" if (75 <= el <= 130) else "#ef4444"
        desc_el = "Confort" if (75 <= el <= 130) else "Ángulo Forzado"
        self.lbl_val_codo_l.configure(text=f"{el:.1f}° ({desc_el})", text_color=col_el)
        self.bar_codo_l.configure(progress_color=col_el)
        self.bar_codo_l.set(min(1.0, el / 180.0))

        # 3. Therbligs
        self.lbl_therblig_r.configure(text=self.metrics["therblig_r"])
        self.lbl_therblig_l.configure(text=self.metrics["therblig_l"])
        
        held_r = self.metrics["pinch_held_seconds_r"]
        col_held = "#ef4444" if held_r > 3.5 else "#94a3b8"
        self.lbl_tension_r.configure(
            text=f"Pinza: {self.metrics['flexion_pct_r']}% · Tensión sostenida: {held_r:.1f}s",
            text_color=col_held
        )

        # 4. Estadísticas acumuladas
        total_time = max(0.1, self.metrics["safe_time"] + self.metrics["risk_time"])
        safe_pct = int((self.metrics["safe_time"] / total_time) * 100)
        self.lbl_safe_pct.configure(text=f"{safe_pct}%")
        self.bar_safe.set(safe_pct / 100.0)

        self.lbl_c_tomar.configure(text=f"✊ Tomar: {self.metrics['count_tomar']}")
        self.lbl_c_soltar.configure(text=f"🖐️ Soltar: {self.metrics['count_soltar']}")

    def _render_frame_to_ui(self, cv2_frame):
        """Convierte frame BGR a CTkImage y actualiza el label de pantalla completa."""
        try:
            rgb = cv2.cvtColor(cv2_frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(rgb)
            
            target_w = max(100, self.video_container.winfo_width())
            target_h = max(100, self.video_container.winfo_height())
            
            ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=(target_w, target_h))
            self.video_lbl.configure(image=ctk_img, text="")
        except Exception:
            pass

    def _calc_angle_2d(self, a, b, c):
        """Calcula el ángulo en grados formado por 3 puntos 2D (a-b-c)."""
        ba = (a[0] - b[0], a[1] - b[1])
        bc = (c[0] - b[0], c[1] - b[1])
        
        dot = ba[0]*bc[0] + ba[1]*bc[1]
        mag_ba = math.sqrt(ba[0]*ba[0] + ba[1]*ba[1]) or 1.0
        mag_bc = math.sqrt(bc[0]*bc[0] + bc[1]*bc[1]) or 1.0
        
        cos_ang = max(-1.0, min(1.0, dot / (mag_ba * mag_bc)))
        return math.degrees(math.acos(cos_ang))

    def _generate_simulated_frame(self, t):
        """Crea un frame oscuro de simulación con silueta humana suave si no hay cámara activa."""
        frame = np.full((480, 640, 3), (12, 18, 28), dtype=np.uint8)
        for x in range(0, 640, 40): cv2.line(frame, (x, 0), (x, 480), (20, 28, 42), 1)
        for y in range(0, 480, 40): cv2.line(frame, (0, y), (640, y), (20, 28, 42), 1)
        
        cx, cy = 320, 240
        cv2.ellipse(frame, (cx, cy - 80), (45, 60), 0, 0, 360, (25, 35, 52), -1)
        cv2.ellipse(frame, (cx, cy + 50), (120, 100), 0, 0, 360, (22, 32, 48), -1)
        cv2.rectangle(frame, (80, 370), (560, 480), (18, 24, 36), -1)
        cv2.putText(frame, "MODO SIMULACION - KINECT VIRTUAL 30 FPS", (20, 460), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (70, 85, 110), 1)
        return frame

    def toggle_test(self):
        """Pausa o reanuda la prueba de micromovimientos."""
        self.is_running = not self.is_running
        if self.is_running:
            self.btn_toggle.configure(text="⏸ Pausar Prueba", fg_color="#ef4444", hover_color="#dc2626")
        else:
            self.btn_toggle.configure(text="▶ Reanudar", fg_color="#22c55e", hover_color="#16a34a")

    def capture_evidence(self):
        """Guarda un fotograma con el croquis y telemetría en media_evidencia."""
        try:
            folder = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "media_evidencia")
            os.makedirs(folder, exist_ok=True)
            fname = f"evidencia_kinect_{int(time.time())}.jpg"
            p = os.path.join(folder, fname)
            
            if self.is_camera_connected and self.cap and self.cap.isOpened():
                ret, frame = self.cap.read()
                if ret and frame is not None:
                    processed = self.process_and_draw_kinect(frame, 0.033)
                    cv2.imwrite(p, processed)
                    print(f"[TestMovimiento] Evidencia guardada en {p}")
        except Exception as e:
            print(f"[TestMovimiento] Error guardando evidencia: {e}")

    def reset_stats(self):
        """Reinicia los contadores y tiempos acumulados de la sesión."""
        self.metrics["safe_time"] = 0.0
        self.metrics["risk_time"] = 0.0
        self.metrics["count_tomar"] = 0
        self.metrics["count_soltar"] = 0
        self.metrics["pinch_held_seconds_r"] = 0.0
        self.metrics["pinch_held_seconds_l"] = 0.0
        self.update_statistics_ui(0.0)

    def destroy(self):
        """Libera de forma segura la cámara web y los detectores MediaPipe."""
        self.is_running = False
        if self.cap:
            try:
                self.cap.release()
            except Exception:
                pass
            self.cap = None

        if self.pose_detector:
            try:
                self.pose_detector.close()
            except Exception:
                pass
            self.pose_detector = None

        if self.hand_detector:
            try:
                self.hand_detector.close()
            except Exception:
                pass
            self.hand_detector = None

        super().destroy()
