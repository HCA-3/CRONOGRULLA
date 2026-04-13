import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox, simpledialog
import time
import os
import cv2
from PIL import Image, ImageTk
import threading
import numpy as np

class TimerView(ctk.CTkFrame):
    def __init__(self, master, app):
        super().__init__(master, fg_color="transparent")
        self.app = app
        self.running = False
        self.camera_active = False
        self.cap = None
        self.camera_source = 0
        self.motion_threshold = 1200 # Ajustado para recuadros pequeños
        self.media_path = "media_evidencia"
        if not os.path.exists(self.media_path): os.makedirs(self.media_path)
        
        self.last_frame = None
        self.build_ui()
        self.show_camera_setup_dialog()

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
        
        self.btn_action = ctk.CTkButton(control_p, text="▶ INICIAR ESTUDIO", command=self.toggle_study, height=45, fg_color="#2ecc71", font=ctk.CTkFont(weight="bold"))
        self.btn_action.pack(side="right")

        # Tarjetas Horizontales
        self.cards_scroll = ctk.CTkScrollableFrame(self, orientation="horizontal", height=180, fg_color="transparent")
        self.cards_scroll.pack(fill="x", padx=20, pady=10)
        self.op_cards = {}
        self.refresh_ui_cards()

    def refresh_ui_cards(self):
        for widget in self.cards_scroll.winfo_children(): widget.destroy()
        ops = self.app.operator_data if self.app.operator_data else [{"name": "Estación 1"}]
        for op in ops:
            name = op.get("name") if isinstance(op, dict) else str(op)
            # Tarjeta Estilo Industrial
            card = ctk.CTkFrame(self.cards_scroll, width=220, height=150, corner_radius=15, border_width=2, border_color=("#dfe6e9", "#2d3436"))
            card.pack(side="left", padx=10, pady=5)
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
            frame, trigger_idx = self.process_vision(frame)
            if trigger_idx is not None: self.handle_trigger(trigger_idx, frame)
            
            # Convertir a imagen solo 20 veces por segundo (Eficiencia)
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(rgb)
            w, h = self.video_display.winfo_width(), self.video_display.winfo_height()
            if w > 40 and h > 40:
                ctk_img = ctk.CTkImage(img, size=(w, h))
                self.video_display.configure(image=ctk_img, text="")
        
        self.after(40, self.update_loop) # 25 FPS para no saturar el PC

    def process_vision(self, frame):
        ops = self.app.operator_data if self.app.operator_data else [{"name": "Estación 1"}]
        num = len(ops)
        h, w = frame.shape[:2]
        if not hasattr(self, 'p_grays') or len(self.p_grays) != num: self.p_grays = [None] * num
        
        zw = (w - 40) // num
        trig = None
        now = time.time()
        
        for i in range(num):
            # Recuadros más pequeños y centrados en su zona
            margin = zw // 4
            x1, x2 = 20 + (i * zw) + margin, 20 + (i * zw) + zw - margin
            y1, y2 = 20, 70  # Altura reducida de 100px a 50px
            
            zone = frame[y1:y2, x1:x2]
            if zone.size == 0: continue
            gray = cv2.GaussianBlur(cv2.cvtColor(zone, cv2.COLOR_BGR2GRAY), (21, 21), 0)

            if self.p_grays[i] is not None:
                delta = cv2.absdiff(self.p_grays[i], gray)
                if cv2.countNonZero(cv2.threshold(delta, 25, 255, cv2.THRESH_BINARY)[1]) > self.motion_threshold:
                    trig = i
                    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 255), 4)

            self.p_grays[i] = gray
            name = ops[i].get("name") if isinstance(ops[i], dict) else str(ops[i])
            color = (0, 255, 0) if trig != i else (0, 255, 255)
            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
            cv2.putText(frame, name[:12], (x1, y1-5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
            
            if self.running and name in self.op_states:
                s = self.op_states[name]
                if not s["done"]:
                    txt = f"G:{s['g']} P:{s['idx']+1}"
                    cv2.putText(frame, txt, (x1+5, y2-20), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255,255,255), 1)
                    cv2.putText(frame, f"{now - s['start']:.1f}s", (x1+5, y2-5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 2)

        return frame, trig

    def toggle_study(self):
        if not self.running:
            qty = simpledialog.askinteger("Meta", "Número de grullas:", minvalue=1, initialvalue=5)
            if not qty: return
            self.total_g = qty
            
            ops = self.app.operator_data if self.app.operator_data else [{"name": "Estación 1"}]
            self.op_states = {}
            for op in ops:
                n = op.get("name") if isinstance(op, dict) else str(op)
                task_indices = [i for i, t in enumerate(self.app.ACTIVITIES) if self.app.line_config.get(str(i)) == n]
                tasks = [self.app.ACTIVITIES[i] for i in task_indices]
                if not tasks: 
                     tasks = ["Tarea Unica"]
                     task_indices = [0]
                self.op_states[n] = {"g": 1, "idx": 0, "tasks": tasks, "task_indices": task_indices, "start": time.time(), "lt": 0, "done": False}

            self.current_cycles_data = {
                g: {"model": self.app.current_model_name, "splits": [{"duration": 0.0} for _ in range(len(self.app.ACTIVITIES))], "total_time": 0.0}
                for g in range(1, self.total_g + 1)
            }

            self.running = True
            self.glob_st = time.time()
            self.btn_action.configure(text="🛑 DETENER ESTUDIO", fg_color="#e74c3c")
            
            # Cambiar estados a TRABAJANDO
            for n in self.op_states:
                self.op_cards[n]["status_lbl"].configure(text="TRABAJANDO")
                self.op_cards[n]["status_f"].configure(fg_color="#e67e22")

            self.update_clock()
        else:
            if messagebox.askyesno("Detener", "¿Deseas finalizar el estudio ahora?"):
                self.finish_study()

    def handle_trigger(self, idx, frame=None):
        if not self.running: return
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
                "evidence": os.path.join(self.media_path, filename) if filename else ""
            }
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
        now = time.time()
        for n, s in self.op_states.items():
            if not s["done"]: self.op_cards[n]["time"].configure(text=f"{now - s['start']:.2f}s")
        el = now - self.glob_st
        self.timer_label.configure(text=f"{int(el/60):02d}:{int(el%60):02d}.{int((el%1)*100):02d}")
        
        # Mover la llamada de finish_study a un after un poco más largo para evitar recursividad
        if all(s["done"] for s in self.op_states.values()): 
            self.after(500, self.finish_study)
        else: 
            self.after(100, self.update_clock)

    def finish_study(self):
        if not self.running: return
        self.running = False
        
        if "measurements" not in self.app.data:
            self.app.data["measurements"] = []
            
        for g in range(1, self.total_g + 1):
             cycle = self.current_cycles_data[g]
             if cycle["total_time"] > 0:
                 cycle["total_time"] = round(cycle["total_time"], 2)
                 self.app.data["measurements"].append(cycle)
                 
        self.app.save_data()
        
        self.btn_action.configure(text="▶ INICIAR ESTUDIO", fg_color="#2ecc71")
        messagebox.showinfo("CronoGrulla", "Estudio finalizado y guardado exitosamente.")
        self.app.show_dashboard()
