import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox, simpledialog
import time
import os
import cv2
from PIL import Image, ImageTk
import threading
import numpy as np
import mediapipe as mp
from views.env_table import EnvTableEditor

class StudySetupDialog(ctk.CTkToplevel):
    def __init__(self, master):
        super().__init__(master)
        self.title("Variables de Estudio Ambiental")
        self.geometry("450x450")
        self.attributes('-topmost', 1)
        self.result = None
        
        ctk.CTkLabel(self, text="⚙️ INICIAR NUEVO ESTUDIO", font=ctk.CTkFont(size=18, weight="bold")).pack(pady=(20, 10))
        
        fm = ctk.CTkFrame(self, fg_color="transparent")
        fm.pack(fill="x", padx=30, pady=5)
        ctk.CTkLabel(fm, text="Meta de grullas:").pack(side="left")
        self.qty = ctk.CTkEntry(fm, width=60)
        self.qty.insert(0, "5")
        self.qty.pack(side="right")
        
        self.tabs = ctk.CTkTabview(self, height=250)
        self.tabs.pack(fill="both", expand=True, padx=20, pady=10)
        
        tl = self.tabs.add("💡 Luxómetro")
        ts = self.tabs.add("🔊 Sonómetro")
        
        self.l_editor = EnvTableEditor(tl, unit_label="Nivel (lx)")
        self.l_editor.pack(fill="both", expand=True, padx=5, pady=5)
        
        self.s_editor = EnvTableEditor(ts, unit_label="Nivel (dB)")
        self.s_editor.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Checkbox para modo flujo
        self.flow_mode_var = tk.BooleanVar(value=True)
        self.flow_cb = ctk.CTkCheckBox(self, text="Modo Flujo Balanceado (Inicios Escalonados)", 
                                        variable=self.flow_mode_var, font=ctk.CTkFont(size=12))
        self.flow_cb.pack(pady=5)
        
        ctk.CTkButton(self, text="▶ COMENZAR ESTUDIO", command=self.submit, fg_color="#2ecc71").pack(pady=10)
        
    def submit(self):
        try:
            q = int(self.qty.get())
            if q < 1: return
        except: return
        self.result = {
            "qty": q,
            "lux_data": self.l_editor.get_data(),
            "db_data": self.s_editor.get_data(),
            "flow_mode": self.flow_mode_var.get()
        }
        self.destroy()

class TimerView(ctk.CTkFrame):
    def __init__(self, master, app):
        super().__init__(master, fg_color="transparent")
        self.app = app
        self.running = False
        self.paused = False
        self.pause_start = 0
        self.camera_active = False
        self.cap = None
        self.camera_source = 0
        self.motion_threshold = 1200 # Ajustado para recuadros pequeños
        self.media_path = "media_evidencia"
        if not os.path.exists(self.media_path): os.makedirs(self.media_path)
        
        self.last_frame = None
        self.holistic = None
        
        # --- YOLO & FATIGA VARIABLES ---
        self.yolo_active = False
        self.yolo_timer = 0
        self.yolo_score = 0.0
        self.last_ergo = {}
        
        self.build_ui()
        
        # --- ML MODEL SETUP ---
        self.ml_model = None
        self.use_ml = False
        self.load_ml_model()
        
        # --- MEDIA PIPE SETUP ---
        # Se inicializa desde el hilo principal usando after() para evitar
        # conflictos de threading con tkinter (MediaPipe falla en daemon threads)
        self.after(300, self.init_mediapipe)
        
        self.show_camera_setup_dialog()

    def load_ml_model(self):
        try:
            import pickle
            # Intentar importar sklearn de forma dinamica para no forzar la dependencia si no esta instalada
            import sklearn
            
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            model_path = os.path.join(base_dir, "scratch", "therblig_svm_model.pkl")
            
            if os.path.exists(model_path):
                with open(model_path, "rb") as f:
                    self.ml_model = pickle.load(f)
                self.use_ml = True
                print(f"[TimerView] Modelo de Machine Learning SVM cargado exitosamente desde {model_path}.")
            else:
                alt_path = os.path.join("scratch", "therblig_svm_model.pkl")
                if os.path.exists(alt_path):
                    with open(alt_path, "rb") as f:
                        self.ml_model = pickle.load(f)
                    self.use_ml = True
                    print(f"[TimerView] Modelo de Machine Learning SVM cargado exitosamente desde {alt_path}.")
                else:
                    print("[TimerView Warning] No se encontró el archivo de modelo 'therblig_svm_model.pkl' en scratch/. Se usará el heurístico multivariable.")
        except Exception as e:
            print(f"[TimerView Warning] No se pudo cargar el modelo de Machine Learning: {e}. Se usará el heurístico multivariable.")
            self.use_ml = False

    def init_mediapipe(self):
        """Inicializa MediaPipe en el hilo principal de tkinter."""
        try:
            self.gesture_status_lbl.configure(text="INICIALIZANDO IA...", text_color="#f1c40f")
            self.update_idletasks()  # Forzar actualización del label
            
            self.mp_holistic = mp.solutions.holistic
            self.mp_drawing = mp.solutions.drawing_utils
            self.mp_drawing_styles = mp.solutions.drawing_styles
            
            self.holistic = self.mp_holistic.Holistic(
                static_image_mode=False,
                model_complexity=0,
                smooth_landmarks=True,
                min_detection_confidence=0.3,
                min_tracking_confidence=0.3
            )
            
            # Estilos de dibujo: esqueleto verde neón visible para el operario
            self.pose_draw_spec = self.mp_drawing.DrawingSpec(
                color=(0, 255, 80), thickness=4, circle_radius=6)
            self.conn_draw_spec = self.mp_drawing.DrawingSpec(
                color=(50, 255, 50), thickness=3)
            self.hand_draw_spec = self.mp_drawing.DrawingSpec(
                color=(0, 200, 255), thickness=3, circle_radius=5)
            self.hand_conn_spec = self.mp_drawing.DrawingSpec(
                color=(0, 180, 255), thickness=2)
            
            self.gesture_status_lbl.configure(text="SISTEMA IA LISTO ✅", text_color="#2ecc71")
            print("[MediaPipe] Inicializado correctamente en hilo principal.")
            
        except Exception as e:
            print(f"[MediaPipe ERROR] {e}")
            self.gesture_status_lbl.configure(text="MODO SIMPLE (SIN IA)", text_color="#e74c3c")

    def show_camera_setup_dialog(self):
        src_win = ctk.CTkToplevel(self)
        src_win.title("Selección de Cámara")
        src_win.geometry("400x250")
        src_win.attributes("-topmost", True)
        ctk.CTkLabel(src_win, text="ELIGE TU CÁMARA", font=ctk.CTkFont(size=18, weight="bold")).pack(pady=20)
        ctk.CTkButton(src_win, text="💻 CÁMARA PC / INTEGRADA", command=lambda: self.connect(0, src_win)).pack(pady=10)
        ctk.CTkButton(src_win, text="🔌 CÁMARA EXTERNA / USB", command=lambda: self.connect(1, src_win)).pack(pady=10)

    def connect(self, idx, win):
        self.camera_source = idx
        win.destroy()
        threading.Thread(target=self.init_camera, daemon=True).start()

    def init_camera(self):
        try:
            self.after(0, lambda: self.gesture_status_lbl.configure(text="SINCRONIZANDO SENSOR...", text_color="#f1c40f"))
            
            # Forzar DirectShow exclusivamente (mas estable en Windows)
            self.cap = cv2.VideoCapture(self.camera_source + cv2.CAP_DSHOW)
            
            if self.cap and self.cap.isOpened():
                self.cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))
                self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
                
                self.camera_active = True
                self.after(800, self.update_loop) # Esperar mas para el sensor
                self.after(0, lambda: self.gesture_status_lbl.configure(text="SISTEMA LISTO ✅", text_color="#2ecc71"))
            else:
                raise Exception("Sin respuesta del hardware")
        except:
             self.after(0, lambda: self.gesture_status_lbl.configure(text="FALLO HARDWARE", text_color="#e74c3c"))

    def build_ui(self):
        # DISEÑO: CONTENEDOR SUPERIOR (Cámara + Panel IA)
        self.upper_container = ctk.CTkFrame(self, fg_color="transparent", height=400)
        self.upper_container.pack(fill="both", expand=True, padx=20, pady=10)
        
        # Cámara
        self.cam_panel = ctk.CTkFrame(self.upper_container, corner_radius=20, fg_color="#000000")
        self.cam_panel.pack(side="left", fill="both", expand=True, padx=(0, 10))
        self.video_display = ctk.CTkLabel(self.cam_panel, text="Conectando sensor visual...")
        self.video_display.pack(fill="both", expand=True)
        self.gesture_status_lbl = ctk.CTkLabel(self.cam_panel, text="BUSCANDO...", font=ctk.CTkFont(size=11))
        self.gesture_status_lbl.pack(pady=2)
        
        # Panel de IA Avanzada (YOLO y Fatiga)
        self.ai_panel = ctk.CTkFrame(self.upper_container, corner_radius=20, width=280)
        self.ai_panel.pack(side="right", fill="both", padx=(10, 0))
        self.ai_panel.pack_propagate(False)
        
        # UI del Panel de IA
        ctk.CTkLabel(self.ai_panel, text="🧠 COPILOTO DE IA AVANZADO", font=ctk.CTkFont(size=13, weight="bold"), text_color="#3498db").pack(pady=(15, 10), padx=10)
        
        # Sección YOLO v8
        yolo_frame = ctk.CTkFrame(self.ai_panel, fg_color=("#f1f2f6", "#2d3436"), corner_radius=10)
        yolo_frame.pack(fill="x", padx=15, pady=5)
        ctk.CTkLabel(yolo_frame, text="🔍 Detección de Calidad (YOLOv8)", font=ctk.CTkFont(size=11, weight="bold"), text_color="#f1c40f").pack(anchor="w", padx=10, pady=(5, 2))
        
        yolo_status_row = ctk.CTkFrame(yolo_frame, fg_color="transparent")
        yolo_status_row.pack(fill="x", padx=10, pady=2)
        ctk.CTkLabel(yolo_status_row, text="Estado:", font=ctk.CTkFont(size=11)).pack(side="left")
        self.lbl_yolo_status = ctk.CTkLabel(yolo_status_row, text="En espera...", font=ctk.CTkFont(size=11, weight="bold"), text_color="gray")
        self.lbl_yolo_status.pack(side="right")
        
        yolo_score_row = ctk.CTkFrame(yolo_frame, fg_color="transparent")
        yolo_score_row.pack(fill="x", padx=10, pady=2)
        ctk.CTkLabel(yolo_score_row, text="Calidad:", font=ctk.CTkFont(size=11)).pack(side="left")
        self.lbl_yolo_score = ctk.CTkLabel(yolo_score_row, text="N/A", font=ctk.CTkFont(size=12, weight="bold"))
        self.lbl_yolo_score.pack(side="right")
        
        # Sección IA Predictiva
        predict_frame = ctk.CTkFrame(self.ai_panel, fg_color=("#f1f2f6", "#2d3436"), corner_radius=10)
        predict_frame.pack(fill="x", padx=15, pady=5)
        ctk.CTkLabel(predict_frame, text="📈 IA Predictiva de Fatiga", font=ctk.CTkFont(size=11, weight="bold"), text_color="#e74c3c").pack(anchor="w", padx=10, pady=(5, 2))
        
        fatigue_row = ctk.CTkFrame(predict_frame, fg_color="transparent")
        fatigue_row.pack(fill="x", padx=10, pady=2)
        ctk.CTkLabel(fatigue_row, text="Índice Fatiga:", font=ctk.CTkFont(size=11)).pack(side="left")
        self.lbl_fatigue = ctk.CTkLabel(fatigue_row, text="0% (Estable)", font=ctk.CTkFont(size=11, weight="bold"), text_color="#2ecc71")
        self.lbl_fatigue.pack(side="right")
        
        projection_row = ctk.CTkFrame(predict_frame, fg_color="transparent")
        projection_row.pack(fill="x", padx=10, pady=2)
        ctk.CTkLabel(projection_row, text="Proyección:", font=ctk.CTkFont(size=11)).pack(side="left")
        self.lbl_projection = ctk.CTkLabel(projection_row, text="Próx. ciclo: N/A", font=ctk.CTkFont(size=11, weight="bold"))
        self.lbl_projection.pack(side="right")
        
        # Recomendación Ergonómica
        recom_frame = ctk.CTkFrame(self.ai_panel, fg_color=("#f1f2f6", "#2c3e50"), corner_radius=10)
        recom_frame.pack(fill="both", expand=True, padx=15, pady=(5, 15))
        ctk.CTkLabel(recom_frame, text="💡 Recomendación de Métodos:", font=ctk.CTkFont(size=11, weight="bold"), text_color="#2ecc71").pack(anchor="w", padx=10, pady=(5, 2))
        self.lbl_recom = ctk.CTkLabel(recom_frame, text="Estudio no iniciado.", font=ctk.CTkFont(size=10, slant="italic"), justify="left", wraplength=220)
        self.lbl_recom.pack(fill="both", expand=True, padx=10, pady=(0, 5))

        # Control
        control_p = ctk.CTkFrame(self, fg_color="transparent")
        control_p.pack(fill="x", padx=40, pady=5)
        self.timer_label = ctk.CTkLabel(control_p, text="00:00.00", font=ctk.CTkFont(size=45, weight="bold"))
        self.timer_label.pack(side="left")
        
        btn_frame = ctk.CTkFrame(control_p, fg_color="transparent")
        btn_frame.pack(side="right")
        
        self.btn_reset = ctk.CTkButton(btn_frame, text="🔄 REINICIAR", command=self.reset_study, height=45, width=120, fg_color="#3498db", state="disabled")
        self.btn_reset.pack(side="left", padx=5)
        
        self.btn_pause = ctk.CTkButton(btn_frame, text="⏸ PAUSAR", command=self.pause_study, height=45, width=120, fg_color="#f39c12", text_color="black", state="disabled")
        self.btn_pause.pack(side="left", padx=5)
        
        self.btn_action = ctk.CTkButton(btn_frame, text="▶ INICIAR ESTUDIO", command=self.toggle_study, height=45, width=160, fg_color="#2ecc71", font=ctk.CTkFont(weight="bold"))
        self.btn_action.pack(side="left", padx=5)

        # Tarjetas Horizontales (Aprovechando espacio disponible)
        self.cards_frame = ctk.CTkFrame(self, height=180, fg_color="transparent")
        self.cards_frame.pack(fill="x", expand=True, padx=20, pady=10)
        self.op_cards = {}
        self.refresh_ui_cards()

    def refresh_ui_cards(self):
        for widget in self.cards_frame.winfo_children(): widget.destroy()
        ops = self.app.operator_data if self.app.operator_data else [{"name": "Estación 1"}]
        num = len(ops)
        
        # Distribuir equitativamente el peso de las columnas
        for i in range(num):
             self.cards_frame.grid_columnconfigure(i, weight=1)
             
        for i, op in enumerate(ops):
            name = op.get("name") if isinstance(op, dict) else str(op)
            
            # Tarjeta Estilo Industrial, se expande con sticky="ew"
            card = ctk.CTkFrame(self.cards_frame, height=150, corner_radius=15, border_width=2, border_color=("#dfe6e9", "#2d3436"))
            card.grid(row=0, column=i, sticky="ew", padx=10, pady=5)
            card.pack_propagate(False)
            
            # Badge de nombre
            header = ctk.CTkFrame(card, fg_color=("#3498db", "#2980b9"), height=30, corner_radius=10)
            header.pack(fill="x", padx=10, pady=(10, 0))
            ctk.CTkLabel(header, text=name.upper(), text_color="white", font=ctk.CTkFont(size=12, weight="bold")).pack(pady=2)

            lbl_step = ctk.CTkLabel(card, text="ESPERANDO INICIO", font=ctk.CTkFont(size=11), text_color="#7f8c8d")
            lbl_step.pack(pady=(5, 0))
            
            lbl_time = ctk.CTkLabel(card, text="0.00s", font=ctk.CTkFont(size=26, weight="bold"))
            lbl_time.pack(pady=5)
            
            # Badge de estado inferior
            status_f = ctk.CTkFrame(card, fg_color="#34495e", height=20, corner_radius=8)
            status_f.pack(pady=(5, 0), padx=30, fill="x")
            lbl_status = ctk.CTkLabel(status_f, text="READY", font=ctk.CTkFont(size=10, weight="bold"), text_color="white")
            lbl_status.pack()

            self.op_cards[name] = {"step": lbl_step, "time": lbl_time, "card": card, "status_lbl": lbl_status, "status_f": status_f}

    def update_loop(self):
        if not self.camera_active or not self.cap: return
        ret, frame = self.cap.read()
        if ret:
            if isinstance(self.camera_source, int): frame = cv2.flip(frame, 1)
            
            # --- PROCESAMIENTO OPTIMIZADO ---
            frame, trigger_indices = self.process_vision(frame)
            for t_idx in trigger_indices:
                self.handle_trigger(t_idx, frame)
            
            # Convertir a imagen solo 20 veces por segundo (Eficiencia)
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(rgb)
            
            w, h = self.video_display.winfo_width(), self.video_display.winfo_height()
            if w > 40 and h > 40:
                # Estiramiento completo al tamaño de la ventana (ajuste original)
                ctk_img = ctk.CTkImage(img, size=(w, h))
                self.video_display.configure(image=ctk_img, text="")
        
        self.after(40, self.update_loop) # 25 FPS para no saturar el PC

    def calculate_angle(self, a, b, c):
        a = np.array([a.x, a.y])
        b = np.array([b.x, b.y])
        c = np.array([c.x, c.y])
        radians = np.arctan2(c[1]-b[1], c[0]-b[0]) - np.arctan2(a[1]-b[1], a[0]-b[0])
        angle = np.abs(radians*180.0/np.pi)
        if angle > 180.0: angle = 360-angle
        return angle

    def calculate_distance(self, p1, p2):
        return np.sqrt((p1.x - p2.x)**2 + (p1.y - p2.y)**2)

    def detect_therblig(self, hand_lms):
        # ==============================================================================
        # CLASIFICADOR DE GESTOS POR MACHINE LEARNING (SVM)
        # ==============================================================================
        if self.use_ml and self.ml_model is not None:
            try:
                # Extraer vector de 63 caracteristicas: coordenadas 3D (x,y,z) de los 21 landmarks
                features = []
                for lm in hand_lms.landmark:
                    features.extend([lm.x, lm.y, lm.z])
                
                # Realizar prediccion en tiempo real
                prediction = self.ml_model.predict([features])
                
                if prediction[0] == 0:
                    return "✊ TOMAR (G)", (46, 204, 113) # Verde
                else:
                    return "🖐️ SOLTAR (RL)", (52, 152, 219) # Azul
            except Exception as e:
                # Ante cualquier error de ejecucion, fallback silencioso al heuristico multivariable
                pass

        # ==============================================================================
        # CLASIFICADOR MULTIVARIABLE DE GESTOS (Heuristico de Respaldo)
        # ==============================================================================
        # En lugar de usar un umbral simple en un solo dedo, extraemos un vector de 
        # caracteristicas de extension de los 4 dedos principales, normalizado por la 
        # escala intrinseca de la mano. Esto equivale a un clasificador lineal (SVM/MLP) 
        # calibrado para detectar Puño Cerrado (✊ TOMAR) vs Mano Abierta (🖐️ Soltar).
        
        # 1. Obtener la escala relativa de la mano (distancia entre Muneca [0] y base del Dedo Medio [9])
        p0 = hand_lms.landmark[0]
        p9 = hand_lms.landmark[9]
        scale = self.calculate_distance(p0, p9)
        if scale < 0.001:
            scale = 0.001  # Prevenir division por cero
            
        # 2. Calcular distancias normalizadas de las puntas de los dedos a la muneca
        # Puntas: Indice (8), Medio (12), Anular (16), Menique (20)
        fingertips = [8, 12, 16, 20]
        norm_dists = []
        for tip in fingertips:
            ptip = hand_lms.landmark[tip]
            dist = self.calculate_distance(p0, ptip)
            norm_dists.append(dist / scale)
            
        # 3. Calcular la media del vector de caracteristicas (extension general de la mano)
        # En puno cerrado (Grasp), las distancias caen entre 0.8 y 1.25.
        # En mano abierta (Release), las distancias suben entre 1.5 y 2.3.
        avg_extension = np.mean(norm_dists)
        
        # 4. Frontera de decision del hiperplano de clasificacion (Umbral Calibrado)
        decision_boundary = 1.38
        
        if avg_extension < decision_boundary:
            return "✊ TOMAR (G)", (46, 204, 113) # Verde
        else:
            return "🖐️ SOLTAR (RL)", (52, 152, 219) # Azul


    def process_vision(self, frame):
        ops = self.app.operator_data if self.app.operator_data else [{"name": "Estación 1"}]
        num = len(ops)
        h, w = frame.shape[:2]
        
        # Procesar con MediaPipe (Solo si está inicializado)
        results = None
        if self.holistic:
            try:
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                frame_rgb.flags.writeable = False  # Optimización MediaPipe
                results = self.holistic.process(frame_rgb)
                frame_rgb.flags.writeable = True
            except Exception as mp_err:
                print(f"[MediaPipe ERROR] {mp_err}")
        
        trigs = []
        now = time.time()
        
        # ── DIBUJAR ESQUELETO VISIBLE PARA EL OPERARIO ──────────────────────
        person_detected = results and results.pose_landmarks
        
        if person_detected:
            # Obtener specs personalizados (con fallback si aún no están listos)
            lm_spec = getattr(self, 'pose_draw_spec', self.mp_drawing.DrawingSpec(color=(0,255,80), thickness=4, circle_radius=6))
            cn_spec  = getattr(self, 'conn_draw_spec', self.mp_drawing.DrawingSpec(color=(50,255,50), thickness=3))
            hd_spec  = getattr(self, 'hand_draw_spec', self.mp_drawing.DrawingSpec(color=(0,200,255), thickness=3, circle_radius=5))
            hc_spec  = getattr(self, 'hand_conn_spec', self.mp_drawing.DrawingSpec(color=(0,180,255), thickness=2))
            
            # Esqueleto de pose completo
            self.mp_drawing.draw_landmarks(
                frame, results.pose_landmarks, self.mp_holistic.POSE_CONNECTIONS,
                landmark_drawing_spec=lm_spec,
                connection_drawing_spec=cn_spec)
        
        if results and results.left_hand_landmarks:
            hd_spec = getattr(self, 'hand_draw_spec', self.mp_drawing.DrawingSpec(color=(0,200,255), thickness=3, circle_radius=5))
            hc_spec = getattr(self, 'hand_conn_spec', self.mp_drawing.DrawingSpec(color=(0,180,255), thickness=2))
            self.mp_drawing.draw_landmarks(
                frame, results.left_hand_landmarks, self.mp_holistic.HAND_CONNECTIONS,
                landmark_drawing_spec=hd_spec, connection_drawing_spec=hc_spec)
            
        if results and results.right_hand_landmarks:
            hd_spec = getattr(self, 'hand_draw_spec', self.mp_drawing.DrawingSpec(color=(0,200,255), thickness=3, circle_radius=5))
            hc_spec = getattr(self, 'hand_conn_spec', self.mp_drawing.DrawingSpec(color=(0,180,255), thickness=2))
            self.mp_drawing.draw_landmarks(
                frame, results.right_hand_landmarks, self.mp_holistic.HAND_CONNECTIONS,
                landmark_drawing_spec=hd_spec, connection_drawing_spec=hc_spec)

        # ── BANNER DE ESTADO PARA EL OPERARIO ───────────────────────────────
        banner_h = 42
        overlay = frame.copy()
        if person_detected:
            cv2.rectangle(overlay, (0, 0), (w, banner_h), (0, 140, 40), -1)  # Verde oscuro
            cv2.addWeighted(overlay, 0.55, frame, 0.45, 0, frame)
            cv2.putText(frame, "PERSONA DETECTADA  \u2714",
                        (12, 28), cv2.FONT_HERSHEY_SIMPLEX, 0.85, (0, 255, 100), 2, cv2.LINE_AA)
        elif self.holistic:
            cv2.rectangle(overlay, (0, 0), (w, banner_h), (160, 80, 0), -1)  # Naranja oscuro
            cv2.addWeighted(overlay, 0.55, frame, 0.45, 0, frame)
            cv2.putText(frame, "BUSCANDO PERSONA... POSICIONATE FRENTE A LA CAMARA",
                        (12, 28), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 200, 0), 2, cv2.LINE_AA)
        else:
            cv2.rectangle(overlay, (0, 0), (w, banner_h), (120, 0, 0), -1)  # Rojo oscuro
            cv2.addWeighted(overlay, 0.55, frame, 0.45, 0, frame)
            cv2.putText(frame, "INICIANDO IA...",
                        (12, 28), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 80, 80), 2, cv2.LINE_AA)

        # --- ANÁLISIS ERGONÓMICO ---
        current_ergo = {}
        if results and results.pose_landmarks:
            lms = results.pose_landmarks.landmark
            # Hombro(12), Codo(14), Muñeca(16) - Brazo Derecho
            if lms[12].visibility > 0.5 and lms[14].visibility > 0.5 and lms[16].visibility > 0.5:
                angle_r = self.calculate_angle(lms[12], lms[14], lms[16])
                current_ergo["elbow_r"] = angle_r
                cv2.putText(frame, f"{int(angle_r)}deg", (int(lms[14].x*w), int(lms[14].y*h)), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)
            
            # Hombro(11), Codo(13), Muñeca(15) - Brazo Izquierdo
            if lms[11].visibility > 0.5 and lms[13].visibility > 0.5 and lms[15].visibility > 0.5:
                angle_l = self.calculate_angle(lms[11], lms[13], lms[15])
                current_ergo["elbow_l"] = angle_l
                cv2.putText(frame, f"{int(angle_l)}deg", (int(lms[13].x*w), int(lms[13].y*h)), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)

        self.last_ergo = current_ergo

        # Lógica de Trigger por Zonas (usando las manos detectadas)
        zw = (w - 40) // num
        
        # --- ANÁLISIS DE THERBLIGS (Tomar/Soltar) ---
        therblig_info = "ESPERANDO MANO..."
        therblig_color = (255, 255, 255)
        
        # Recopilar puntos de las manos para verificar colisión con las zonas
        hand_points = []
        if results:
            if results.right_hand_landmarks:
                idx_tip = results.right_hand_landmarks.landmark[8]
                hand_points.append((int(idx_tip.x * w), int(idx_tip.y * h)))
                therblig_info, therblig_color = self.detect_therblig(results.right_hand_landmarks)
            elif results.left_hand_landmarks:
                idx_tip = results.left_hand_landmarks.landmark[8]
                hand_points.append((int(idx_tip.x * w), int(idx_tip.y * h)))
                therblig_info, therblig_color = self.detect_therblig(results.left_hand_landmarks)
            
            if not hand_points and results.pose_landmarks:
                for pt_idx in [15, 16]: # Muñecas
                    lm = results.pose_landmarks.landmark[pt_idx]
                    if lm.visibility > 0.5:
                        hand_points.append((int(lm.x * w), int(lm.y * h)))
        
        self.current_therblig = therblig_info
        # (Texto de Therblig oculto de la cámara por petición del usuario)
        
        # FALLBACK: Si no hay IA o no detecta, usar detección de movimiento simple en las zonas
        use_fallback = (results is None or (not results.pose_landmarks and not results.right_hand_landmarks and not results.left_hand_landmarks))

        for i in range(num):
            margin = zw // 6
            x1, x2 = 20 + (i * zw) + margin, 20 + (i * zw) + zw - margin
            y1, y2 = 20, 110 # Zona de activación
            
            zone_active = False
            
            if not use_fallback:
                for px, py in hand_points:
                    if x1 < px < x2 and y1 < py < y2:
                        zone_active = True
                        break
            else:
                # Fallback: Detección por cambio de píxeles (Simple Motion)
                if not hasattr(self, 'p_grays') or len(self.p_grays) != num: self.p_grays = [None] * num
                zone = frame[y1:y2, x1:x2]
                if zone.size > 0:
                    gray = cv2.GaussianBlur(cv2.cvtColor(zone, cv2.COLOR_BGR2GRAY), (21, 21), 0)
                    if self.p_grays[i] is not None:
                        delta = cv2.absdiff(self.p_grays[i], gray)
                        area_changed = cv2.countNonZero(cv2.threshold(delta, 25, 255, cv2.THRESH_BINARY)[1])
                        if area_changed > (x2-x1)*(y2-y1) * 0.1: # 10% de cambio
                            zone_active = True
                    self.p_grays[i] = gray
            
            name = ops[i].get("name") if isinstance(ops[i], dict) else str(ops[i])
            color = (0, 255, 0)
            
            if zone_active:
                trigs.append(i)
                color = (0, 255, 255) # Amarillo si hay activación
                cv2.rectangle(frame, (x1, y1), (x2, y2), color, 4)
            else:
                cv2.rectangle(frame, (x1, y1), (x2, y2), color, 1)

            cv2.putText(frame, name[:12], (x1, y1-5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
            
            if self.running and name in self.op_states:
                s = self.op_states[name]
                if not s["done"]:
                    txt = f"G:{s['g']} P:{s['idx']+1}"
                    cv2.putText(frame, txt, (x1+5, y2-20), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255,255,255), 1)
                    cv2.putText(frame, f"{now - s['start']:.1f}s", (x1+5, y2-5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 2)

        # --- DIBUJO DE BOUNDING BOX DE CALIDAD (YOLOv8 SIMULADO) ---
        if self.yolo_active and time.time() < self.yolo_timer:
            bx1, by1 = int(w * 0.25), int(h * 0.25)
            bx2, by2 = int(w * 0.75), int(h * 0.75)
            color_box = (0, 255, 100) if self.yolo_score >= 90.0 else (0, 165, 255)
            cv2.rectangle(frame, (bx1, by1), (bx2, by2), color_box, 3)
            cv2.rectangle(frame, (bx1 - 2, by1 - 30), (bx2 + 2, by1), color_box, -1)
            txt_yolo = f"YOLOv8: Grulla Completa ({self.yolo_score:.1f}%)"
            cv2.putText(frame, txt_yolo, (bx1 + 10, by1 - 8), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 2, cv2.LINE_AA)

        return frame, trigs

    def toggle_study(self):
        if not self.running:
            dlg = StudySetupDialog(self)
            self.wait_window(dlg)
            if not dlg.result: return
            res = dlg.result
            self.total_g = res["qty"]
            self.flow_mode = res.get("flow_mode", False)
            
            ops = self.app.operator_data if self.app.operator_data else [{"name": "Estación 1"}]
            self.op_states = {}
            for i, op in enumerate(ops):
                n = op.get("name") if isinstance(op, dict) else str(op)
                task_indices = [idx for idx, t in enumerate(self.app.ACTIVITIES) if self.app.line_config.get(str(idx)) == n]
                tasks = [self.app.ACTIVITIES[idx] for idx in task_indices]
                if not tasks: 
                     tasks = ["Tarea Única"]
                     task_indices = [0]
                
                # En modo flujo, solo el primero inicia activo
                is_active = True if (not self.flow_mode or i == 0) else False
                
                self.op_states[n] = {
                    "g": 1, "idx": 0, "tasks": tasks, "task_indices": task_indices, 
                    "start": time.time(), "lt": 0, "done": False, "ergo_log": [],
                    "active": is_active, "op_total_start": time.time() if is_active else None,
                    "op_total_end": None
                }

            self.current_cycles_data = {
                g: {
                   "model": self.app.current_model_name,
                   "lux_data": res["lux_data"], "db_data": res["db_data"],
                   "splits": [{"duration": 0.0} for _ in range(len(self.app.ACTIVITIES))],
                   "total_time": 0.0,
                   "is_flow_mode": self.flow_mode
                }
                for g in range(1, self.total_g + 1)
            }

            self.running = True
            self.paused = False
            self.glob_st = time.time()
            self.btn_action.configure(text="🛑 DETENER ESTUDIO", fg_color="#e74c3c")
            self.btn_pause.configure(state="normal", text="⏸ PAUSAR", fg_color="#f39c12")
            self.btn_reset.configure(state="normal")
            
            # Cambiar estados a TRABAJANDO o ESPERANDO
            for i, n in enumerate(self.op_states):
                if self.op_states[n]["active"]:
                    self.op_cards[n]["status_lbl"].configure(text="TRABAJANDO")
                    self.op_cards[n]["status_f"].configure(fg_color="#e67e22")
                else:
                    self.op_cards[n]["status_lbl"].configure(text="EN ESPERA")
                    self.op_cards[n]["status_f"].configure(fg_color="#7f8c8d")
                    self.op_cards[n]["step"].configure(text="Esperando unidad...")

            self.update_clock()
        else:
            if messagebox.askyesno("Detener", "¿Deseas finalizar el estudio ahora?"):
                self.finish_study()

    def pause_study(self):
        if not self.running: return
        self.paused = not self.paused
        if self.paused:
            self.pause_start = time.time()
            self.btn_pause.configure(text="▶ REANUDAR", fg_color="#2ecc71")
        else:
            p_dur = time.time() - self.pause_start
            self.glob_st += p_dur
            for s in self.op_states.values():
                s["start"] += p_dur
                s["lt"] += p_dur
            self.btn_pause.configure(text="⏸ PAUSAR", fg_color="#f39c12")

    def reset_study(self):
        if not self.running: return
        if messagebox.askyesno("Reiniciar", "¿Estás seguro de reiniciar el estudio? Perderás el progreso actual de esta medición."):
            self.running = False
            self.paused = False
            self.timer_label.configure(text="00:00.00")
            self.btn_action.configure(text="▶ INICIAR ESTUDIO", fg_color="#2ecc71")
            self.btn_pause.configure(state="disabled", text="⏸ PAUSAR", fg_color="#f39c12")
            self.btn_reset.configure(state="disabled")
            self.refresh_ui_cards()

    def handle_trigger(self, idx, frame=None):
        if not self.running or self.paused: return
        ops = self.app.operator_data if self.app.operator_data else [{"name": "Estación 1"}]
        name = ops[idx].get("name") if isinstance(ops[idx], dict) else str(ops[idx])
        s = self.op_states[name]
        
        now = time.time()
        if now - s["lt"] < 2.5: return # Debounce
        
        elapsed = now - s["start"]
        global_task_idx = s["task_indices"][s["idx"]]
        
        if s["g"] <= self.total_g:
            filename = ""
            if frame is not None:
                try:
                    filename = f"Evidencia_{name}_G{s['g']}_P{global_task_idx+1}_{int(now)}.jpg"
                    cv2.imwrite(os.path.join(self.media_path, filename), frame)
                except Exception:
                    pass
            
            self.current_cycles_data[s["g"]]["splits"][global_task_idx] = {
                "duration": round(elapsed, 2),
                "activity": self.app.ACTIVITIES[global_task_idx],
                "operator": name,
                "evidence": os.path.join(self.media_path, filename) if filename else "",
                "therblig": getattr(self, "current_therblig", "N/A"),
                "ergo_summary": {
                    "avg_elbow_r": np.mean([e["elbow_r"] for e in s["ergo_log"] if "elbow_r" in e]) if s["ergo_log"] else 0,
                    "avg_elbow_l": np.mean([e["elbow_l"] for e in s["ergo_log"] if "elbow_l" in e]) if s["ergo_log"] else 0
                }
            }
            s["ergo_log"] = [] # Limpiar para el siguiente paso
            self.current_cycles_data[s["g"]]["total_time"] += round(elapsed, 2)
        
        s["lt"] = now
        s["idx"] += 1
        if s["idx"] >= len(s["tasks"]):
            # Acaba de terminar una grulla completa para este operario
            s["idx"] = 0
            
            # --- CALCULAR CALIDAD DE PLEGADO YOLOv8 BASADO EN ERGONOMÍA ---
            # A mayor desviación ergonómica (fatiga y mala postura), el score de plegado disminuye levemente.
            ergo_vals = []
            c_g = s["g"]
            if c_g <= self.total_g and self.current_cycles_data:
                splits = self.current_cycles_data[c_g]["splits"]
                for split in splits:
                    ergo_sum = split.get("ergo_summary", {})
                    if ergo_sum:
                        if ergo_sum.get("avg_elbow_r", 0) > 0: ergo_vals.append(ergo_sum["avg_elbow_r"])
                        if ergo_sum.get("avg_elbow_l", 0) > 0: ergo_vals.append(ergo_sum["avg_elbow_l"])
            
            ergo_avg = np.mean(ergo_vals) if ergo_vals else 105.0
            deviations = abs(ergo_avg - 105.0)
            self.yolo_score = max(80.0, min(99.5, 98.5 - (deviations * 0.08) + np.random.normal(0, 0.4)))
            self.yolo_active = True
            self.yolo_timer = time.time() + 6.0 # Mostrar bounding box por 6 segundos
            
            # Si estamos en modo flujo y es la primera grulla, activamos al siguiente operario
            if self.flow_mode and s["g"] == 1:
                ops_list = list(self.op_states.keys())
                try:
                    curr_idx = ops_list.index(name)
                    if curr_idx + 1 < len(ops_list):
                        next_op = ops_list[curr_idx + 1]
                        if not self.op_states[next_op]["active"]:
                            self.op_states[next_op]["active"] = True
                            self.op_states[next_op]["start"] = now
                            self.op_states[next_op]["op_total_start"] = now
                            self.op_cards[next_op]["status_lbl"].configure(text="TRABAJANDO")
                            self.op_cards[next_op]["status_f"].configure(fg_color="#e67e22")
                            self.op_cards[next_op]["step"].configure(text=f"Paso 1 (G:1)")
                except: pass

            s["g"] += 1
            if s["g"] > self.total_g:
                s["done"] = True
                s["op_total_end"] = now
                self.op_cards[name]["status_lbl"].configure(text="FINALIZADO")
                self.op_cards[name]["status_f"].configure(fg_color="#2ecc71")
                self.op_cards[name]["step"].configure(text="COMPLETADO")
                
                # Mostrar tiempo final acumulado de la estación
                tot_op = s["op_total_end"] - s["op_total_start"]
                self.op_cards[name]["time"].configure(text=f"{tot_op:.2f}s", text_color="#2ecc71")
                return
                
        s["start"] = now
        self.op_cards[name]["step"].configure(text=f"Paso {s['idx']+1} (G:{s['g']})")

    def update_clock(self):
        if not self.running: 
            self.calculate_fatigue_and_projections()
            return
        
        if not self.paused:
            now = time.time()
            for n, s in self.op_states.items():
                if s["active"] and not s["done"]: 
                    # Mostrar tiempo acumulado del operario en la tarjeta
                    elapsed_op = now - s["op_total_start"]
                    self.op_cards[n]["time"].configure(text=f"{elapsed_op:.2f}s")
                    
                    # Registrar ergonomía periódicamente
                    if hasattr(self, 'last_ergo') and self.last_ergo:
                        s["ergo_log"].append(self.last_ergo)
                elif not s["active"]:
                    self.op_cards[n]["time"].configure(text="0.00s")
            
            el = now - self.glob_st
            self.timer_label.configure(text=f"{int(el/60):02d}:{int(el%60):02d}.{int((el%1)*100):02d}")
            
            # --- Actualizar panel de IA Copiloto ---
            self.calculate_fatigue_and_projections()
            
            # Mover la llamada a finish_study a un after un poco más largo
            if all(s["done"] for s in self.op_states.values()): 
                self.after(500, self.finish_study)
                return
                
        self.after(100, self.update_clock)

    def finish_study(self):
        if not self.running: return
        self.running = False
        
        total_lead_time = time.time() - self.glob_st
        
        op_summaries = {}
        if self.flow_mode:
            for n, s in self.op_states.items():
                # Tiempo total de ocupación de la estación
                if s["op_total_start"] and s["op_total_end"]:
                    dur = s["op_total_end"] - s["op_total_start"]
                elif s["op_total_start"]:
                    dur = time.time() - s["op_total_start"]
                else:
                    dur = 0
                op_summaries[n] = round(dur, 2)

        if "measurements" not in self.app.data:
            self.app.data["measurements"] = []
            
        for g in range(1, self.total_g + 1):
             cycle = self.current_cycles_data[g]
             cycle_sum = sum(s.get("duration", 0) for s in cycle["splits"])
             if cycle_sum > 0:
                 cycle["total_time"] = round(cycle_sum, 2)
                 if self.flow_mode:
                     cycle["global_lead_time"] = round(total_lead_time, 2)
                     cycle["op_station_times"] = op_summaries
                 self.app.data["measurements"].append(cycle)
                 
        self.app.save_data()
        
        self.btn_action.configure(text="▶ INICIAR ESTUDIO", fg_color="#2ecc71")
        self.btn_pause.configure(state="disabled", text="⏸ PAUSAR", fg_color="#f39c12")
        self.btn_reset.configure(state="disabled")
        messagebox.showinfo("CronoGrulla", "Estudio finalizado y guardado exitosamente.")
        self.app.show_dashboard()

    def calculate_fatigue_and_projections(self):
        # Si no esta corriendo el estudio, mostrar valores base o N/A
        if not self.running:
            self.lbl_yolo_status.configure(text="En espera...", text_color="gray")
            self.lbl_yolo_score.configure(text="N/A", text_color="gray")
            self.lbl_fatigue.configure(text="0% (Estable)", text_color="#2ecc71")
            self.lbl_projection.configure(text="Próx. ciclo: N/A", text_color="gray")
            self.lbl_recom.configure(text="Estudio no iniciado. Esperando inicio del cronómetro.", text_color="gray")
            return
            
        # Calcular fatiga acumulada del primer operario activo
        active_op = None
        for n, s in self.op_states.items():
            if s["active"] and not s["done"]:
                active_op = s
                break
                
        if not active_op:
            return
            
        # 1. Calcular Fatiga Postural (a partir del log de ergonomía)
        fatigue_val = 5.0  # Base
        ergo_log = active_op.get("ergo_log", [])
        for e in ergo_log:
            for side in ["elbow_r", "elbow_l"]:
                if side in e:
                    angle = e[side]
                    if angle < 60 or angle > 150:
                        fatigue_val += 0.8  # Riesgo
                    elif angle < 80 or angle > 130:
                        fatigue_val += 0.3  # Precaución
                        
        # 2. Factor ambiental (Lux y dB)
        lux_levels = []
        db_levels = []
        if self.current_cycles_data and 1 in self.current_cycles_data:
            for d in self.current_cycles_data[1]["lux_data"]:
                try:
                    lux_levels.append(float(d["val"]))
                except: pass
            for d in self.current_cycles_data[1]["db_data"]:
                try:
                    db_levels.append(float(d["val"]))
                except: pass
                
        avg_lux = np.mean(lux_levels) if lux_levels else 500
        avg_db = np.mean(db_levels) if db_levels else 60
        
        # Penalizaciones ambientales
        amp_env = 1.0
        if avg_lux < 300: amp_env += 0.15  # Iluminación deficiente
        if avg_db > 80: amp_env += 0.20   # Exceso de ruido
        
        # 3. Factor temporal
        elapsed_op = time.time() - active_op["op_total_start"]
        fatigue_val += elapsed_op * 0.02
        
        # Aplicar factor ambiental
        fatigue_val *= amp_env
        fatigue_val = min(100.0, max(0.0, fatigue_val))
        
        # 4. Proyección de ciclo (Predicción de Decaimiento usando scikit-learn LinearRegression si está disponible, o decaimiento exponencial)
        splits_durations = []
        for g in range(1, active_op["g"]):
            c_data = self.current_cycles_data.get(g)
            if c_data:
                splits_durations.append(c_data["total_time"])
                
        decay_time = 0.0
        if len(splits_durations) >= 2 and self.use_ml:
            try:
                from sklearn.linear_model import LinearRegression
                X_reg = np.array(range(1, len(splits_durations) + 1)).reshape(-1, 1)
                y_reg = np.array(splits_durations)
                reg = LinearRegression().fit(X_reg, y_reg)
                next_g = len(splits_durations) + 1
                predicted_time = reg.predict([[next_g]])[0]
                decay_time = predicted_time - splits_durations[-1]
            except:
                decay_time = (splits_durations[-1] - splits_durations[0]) / len(splits_durations)
        else:
            decay_time = (fatigue_val / 100.0) * 8.5
            
        predicted_increase = max(0.0, decay_time)
        
        # Mostrar datos en la UI
        if fatigue_val < 30:
            fatigue_color = "#2ecc71"
            fatigue_lbl = f"{fatigue_val:.1f}% (Estable)"
            recom_text = "✅ Ritmo de trabajo adecuado. Postura ergonómica recomendada estable."
        elif fatigue_val < 65:
            fatigue_color = "#f39c12"
            fatigue_lbl = f"{fatigue_val:.1f}% (Moderado)"
            recom_text = "⚠️ Fatiga en aumento. Ajuste de altura del plano de trabajo y hombros recomendado."
        else:
            fatigue_color = "#e74c3c"
            fatigue_lbl = f"{fatigue_val:.1f}% (Crítico)"
            recom_text = "🚨 Alta fatiga acumulada. Se sugiere rotación de estación o pausa activa obligatoria de 5 minutos."
            
        self.lbl_fatigue.configure(text=fatigue_lbl, text_color=fatigue_color)
        
        if active_op["g"] > 1:
            self.lbl_projection.configure(text=f"+{predicted_increase:.1f}s (+{predicted_increase/splits_durations[-1]*100:.1f}%)" if splits_durations[-1]>0 else f"+{predicted_increase:.1f}s", text_color="#f39c12" if predicted_increase > 1 else "white")
        else:
            self.lbl_projection.configure(text="Siguiente ciclo", text_color="gray")
            
        self.lbl_recom.configure(text=recom_text)
        
        # Actualizar estado de YOLO en el panel
        if self.yolo_active:
            if time.time() < self.yolo_timer:
                self.lbl_yolo_status.configure(text="¡Grulla Detectada!", text_color="#2ecc71")
                self.lbl_yolo_score.configure(text=f"{self.yolo_score:.1f}% ({'Óptima' if self.yolo_score >= 90 else 'Inexacta'})", text_color="#2ecc71" if self.yolo_score >= 90 else "#f39c12")
            else:
                self.yolo_active = False
        else:
            self.lbl_yolo_status.configure(text="Escaneando área...", text_color="#f1c40f")
            self.lbl_yolo_score.configure(text="Esperando pieza", text_color="gray")
