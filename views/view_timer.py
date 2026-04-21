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
        
        ctk.CTkButton(self, text="▶ COMENZAR ESTUDIO", command=self.submit, fg_color="#2ecc71").pack(pady=10)
        
    def submit(self):
        try:
            q = int(self.qty.get())
            if q < 1: return
        except: return
        self.result = {
            "qty": q,
            "lux_data": self.l_editor.get_data(),
            "db_data": self.s_editor.get_data()
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
        
        self.build_ui()
        
        # --- MEDIA PIPE SETUP (Robust Initialization) ---
        threading.Thread(target=self.init_mediapipe, daemon=True).start()
        
        self.show_camera_setup_dialog()

    def init_mediapipe(self):
        try:
            self.after(0, lambda: self.gesture_status_lbl.configure(text="INICIALIZANDO IA...", text_color="#f1c40f"))
            self.mp_holistic = mp.solutions.holistic
            self.holistic = self.mp_holistic.Holistic(
                static_image_mode=False,
                model_complexity=1,
                smooth_landmarks=True,
                min_detection_confidence=0.5,
                min_tracking_confidence=0.5
            )
            self.mp_drawing = mp.solutions.drawing_utils
            self.mp_drawing_styles = mp.solutions.drawing_styles
            self.after(0, lambda: self.gesture_status_lbl.configure(text="SISTEMA IA LISTO ✅", text_color="#2ecc71"))
        except Exception as e:
            print(f"Error MediaPipe: {e}")
            self.after(0, lambda: self.gesture_status_lbl.configure(text="MODO SIMPLE (SIN IA)", text_color="#e74c3c"))

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
        # DISEÑO: CÁMARA ARRIBA, TARJETAS ABAJO
        # Cámara
        self.cam_panel = ctk.CTkFrame(self, corner_radius=20, fg_color="#000000", height=400)
        self.cam_panel.pack(fill="both", expand=True, padx=20, pady=10)
        self.video_display = ctk.CTkLabel(self.cam_panel, text="Conectando sensor visual...")
        self.video_display.pack(fill="both", expand=True)
        self.gesture_status_lbl = ctk.CTkLabel(self.cam_panel, text="BUSCANDO...", font=ctk.CTkFont(size=11))
        self.gesture_status_lbl.pack(pady=2)

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
        # Distancia entre punta de pulgar (4) e índice (8)
        d = self.calculate_distance(hand_lms.landmark[4], hand_lms.landmark[8])
        if d < 0.06:
            return "✊ COGER (G)", (46, 204, 113) # Verde
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
                results = self.holistic.process(frame_rgb)
            except:
                pass
        
        trigs = []
        now = time.time()
        
        # Dibujar landmarks de MediaPipe
        if results and results.pose_landmarks:
            self.mp_drawing.draw_landmarks(
                frame, results.pose_landmarks, self.mp_holistic.POSE_CONNECTIONS,
                landmark_drawing_spec=self.mp_drawing_styles.get_default_pose_landmarks_style())
        
        if results and results.left_hand_landmarks:
            self.mp_drawing.draw_landmarks(
                frame, results.left_hand_landmarks, self.mp_holistic.HAND_CONNECTIONS)
            
        if results and results.right_hand_landmarks:
            self.mp_drawing.draw_landmarks(
                frame, results.right_hand_landmarks, self.mp_holistic.HAND_CONNECTIONS)

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
        
        # --- ANÁLISIS DE THERBLIGS (Coger/Soltar) ---
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
        # Dibujar info de Therblig en pantalla
        cv2.putText(frame, f"THERBLIG: {therblig_info}", (20, h - 20), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, therblig_color, 2)
        
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

        return frame, trigs

    def toggle_study(self):
        if not self.running:
            dlg = StudySetupDialog(self)
            self.wait_window(dlg)
            if not dlg.result: return
            res = dlg.result
            self.total_g = res["qty"]
            
            ops = self.app.operator_data if self.app.operator_data else [{"name": "Estación 1"}]
            self.op_states = {}
            for op in ops:
                n = op.get("name") if isinstance(op, dict) else str(op)
                task_indices = [i for i, t in enumerate(self.app.ACTIVITIES) if self.app.line_config.get(str(i)) == n]
                tasks = [self.app.ACTIVITIES[i] for i in task_indices]
                if not tasks: 
                     tasks = ["Tarea Unica"]
                     task_indices = [0]
                self.op_states[n] = {"g": 1, "idx": 0, "tasks": tasks, "task_indices": task_indices, "start": time.time(), "lt": 0, "done": False, "ergo_log": []}

            self.current_cycles_data = {
                g: {
                   "model": self.app.current_model_name,
                   "lux_data": res["lux_data"], "db_data": res["db_data"],
                   "splits": [{"duration": 0.0} for _ in range(len(self.app.ACTIVITIES))],
                   "total_time": 0.0
                }
                for g in range(1, self.total_g + 1)
            }

            self.running = True
            self.paused = False
            self.glob_st = time.time()
            self.btn_action.configure(text="🛑 DETENER ESTUDIO", fg_color="#e74c3c")
            self.btn_pause.configure(state="normal", text="⏸ PAUSAR", fg_color="#f39c12")
            self.btn_reset.configure(state="normal")
            
            # Cambiar estados a TRABAJANDO
            for n in self.op_states:
                self.op_cards[n]["status_lbl"].configure(text="TRABAJANDO")
                self.op_cards[n]["status_f"].configure(fg_color="#e67e22")

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
            s["idx"] = 0
            s["g"] += 1
            if s["g"] > self.total_g:
                s["done"] = True
                self.op_cards[name]["status_lbl"].configure(text="FINALIZADO")
                self.op_cards[name]["status_f"].configure(fg_color="#2ecc71")
                self.op_cards[name]["step"].configure(text="COMPLETADO")
                return
        s["start"] = now
        self.op_cards[name]["step"].configure(text=f"Paso {s['idx']+1} (G:{s['g']})")

    def update_clock(self):
        if not self.running: return
        
        if not self.paused:
            now = time.time()
            for n, s in self.op_states.items():
                if not s["done"]: 
                    self.op_cards[n]["time"].configure(text=f"{now - s['start']:.2f}s")
                    # Registrar ergonomía periódicamente
                    if hasattr(self, 'last_ergo') and self.last_ergo:
                        s["ergo_log"].append(self.last_ergo)
            
            el = now - self.glob_st
            self.timer_label.configure(text=f"{int(el/60):02d}:{int(el%60):02d}.{int((el%1)*100):02d}")
            
            # Mover la llamada a finish_study a un after un poco más largo
            if all(s["done"] for s in self.op_states.values()): 
                self.after(500, self.finish_study)
                return
                
        self.after(100, self.update_clock)

    def finish_study(self):
        if not self.running: return
        self.running = False
        
        if "measurements" not in self.app.data:
            self.app.data["measurements"] = []
            
        for g in range(1, self.total_g + 1):
             cycle = self.current_cycles_data[g]
             # Recalcular total como suma exacta de splits para consistencia total en reportes
             cycle_sum = sum(s.get("duration", 0) for s in cycle["splits"])
             if cycle_sum > 0:
                 cycle["total_time"] = round(cycle_sum, 2)
                 self.app.data["measurements"].append(cycle)
                 
        self.app.save_data()
        
        self.btn_action.configure(text="▶ INICIAR ESTUDIO", fg_color="#2ecc71")
        self.btn_pause.configure(state="disabled", text="⏸ PAUSAR", fg_color="#f39c12")
        self.btn_reset.configure(state="disabled")
        messagebox.showinfo("CronoGrulla", "Estudio finalizado y guardado exitosamente.")
        self.app.show_dashboard()
