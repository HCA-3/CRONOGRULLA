import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox, simpledialog
import time
import os
import cv2
from PIL import Image, ImageTk
import threading
import urllib.request
import numpy as np

class TimerView(ctk.CTkFrame):
    def __init__(self, master, app):
        super().__init__(master, fg_color="transparent")
        self.app = app
        self.grid_columnconfigure(0, weight=1)
        
        self.start_time = None
        self.last_split_time = 0
        self.current_cycle_splits = []
        self.running = False
        self.current_activity_index = 0
        self.waiting_for_operator = False
        self.camera_source = 0
        
        # Motion detection engine
        self.prev_gray_zone = None
        self.motion_threshold = 2000 # Sensibilidad
        
        self.cap = None
        self.camera_active = False
        self.media_path = "media_evidencia"
        if not os.path.exists(self.media_path): os.makedirs(self.media_path)
            
        self.build_ui()
        self.show_camera_setup_dialog()

    def show_camera_setup_dialog(self):
        src_win = ctk.CTkToplevel(self)
        src_win.title("Conectar Cámara")
        src_win.geometry("600x550")
        src_win.attributes("-topmost", True)
        
        ctk.CTkLabel(src_win, text="🎥 ¿QUÉ CÁMARA DESEAS USAR?", font=ctk.CTkFont(size=22, weight="bold")).pack(pady=20)
        
        def start_local():
            self.camera_source = 0
            src_win.destroy()
            threading.Thread(target=self.init_camera_stream, daemon=True).start()

        def start_usb():
            self.camera_source = 1
            src_win.destroy()
            threading.Thread(target=self.init_camera_stream, daemon=True).start()

        def start_ip():
            ip_win = ctk.CTkToplevel(src_win)
            ip_win.title("Usar Celular (WiFi)")
            ip_win.geometry("500x450")
            ip_win.attributes("-topmost", True)
            
            ctk.CTkLabel(ip_win, text="CONECTAR CELULAR (VÍA APP)", font=ctk.CTkFont(size=18, weight="bold")).pack(pady=10)
            
            inst = ("1. Instala la app gratuita 'IP Webcam' en tu celular Android.\n"
                    "2. Abre la app, baja al final y toca 'Start server'.\n"
                    "3. La app mostrará una dirección, por ejemplo:\n"
                    "   http://192.168.1.15:8080\n"
                    "4. Escríbela aquí abajo:")
            ctk.CTkLabel(ip_win, text=inst, justify="left", font=ctk.CTkFont(size=14)).pack(pady=10, padx=20)
            
            entry_url = ctk.CTkEntry(ip_win, width=300, font=ctk.CTkFont(size=16), placeholder_text="http://192.168.1.xxx:8080")
            entry_url.pack(pady=10)
            
            def connect():
                base_url = entry_url.get().strip()
                if not base_url.startswith("http"): base_url = "http://" + base_url
                if base_url.endswith("/"): base_url = base_url[:-1]
                
                try:
                    urllib.request.urlopen(f"{base_url}/shot.jpg", timeout=2)
                except Exception:
                    messagebox.showerror("Error", f"Fallo al conectar:\n{base_url}\nAsegúrate de estar en el mismo WiFi.", parent=ip_win)
                    return
                
                self.camera_source = f"{base_url}/video"
                ip_win.destroy()
                src_win.destroy()
                threading.Thread(target=self.init_camera_stream, daemon=True).start()
                
            ctk.CTkButton(ip_win, text="CONECTAR", font=ctk.CTkFont(weight="bold"), fg_color="#2ecc71", height=45, command=connect).pack(pady=20)

        ctk.CTkButton(src_win, text="💻 CÁMARA DEL PC (Integrada)", height=60, font=ctk.CTkFont(size=15, weight="bold"), fg_color="#34495e", command=start_local).pack(pady=10, fill="x", padx=40)
        ctk.CTkButton(src_win, text="🔌 CÁMARA EXTERNA (USB/DroidCam)", height=60, font=ctk.CTkFont(size=15, weight="bold"), fg_color="#2980b9", command=start_usb).pack(pady=10, fill="x", padx=40)
        ctk.CTkButton(src_win, text="📱 CÁMARA DEL CELULAR (IP Webcam)", height=60, font=ctk.CTkFont(size=15, weight="bold"), fg_color="#e67e22", command=start_ip).pack(pady=10, fill="x", padx=40)

    def init_camera_stream(self):
        try:
            self.after(0, lambda: self.gesture_status_lbl.configure(text="CONECTANDO CÁMARA...", text_color="#f1c40f"))
            if isinstance(self.camera_source, int):
                self.cap = cv2.VideoCapture(self.camera_source, cv2.CAP_DSHOW)
            else:
                self.cap = cv2.VideoCapture(self.camera_source)
                
            if self.cap.isOpened():
                self.camera_active = True
                self.after(200, self.update_loop)
            else:
                raise Exception("La cámara no responde.")
        except Exception as e:
            self.after(0, lambda: messagebox.showerror("Error", f"Fallo al conectar la cámara: {e}"))
            self.after(0, lambda: self.gesture_status_lbl.configure(text="ERROR DE VIDEO", text_color="#e74c3c"))

    def build_ui(self):
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=40, pady=(15, 0))
        cycle_num = len(self.app.data.get("measurements", [])) + 1
        ctk.CTkLabel(header, text=f"Estudio CronoVisión PRO - Ciclo #{cycle_num}", font=ctk.CTkFont(size=28, weight="bold")).pack(side="left")
        ctk.CTkButton(header, text="⚙ Cambiar Cámara", width=120, height=35, command=self.show_camera_setup_dialog).pack(side="right", padx=10)

        self.body = ctk.CTkFrame(self, fg_color="transparent")
        self.body.pack(fill="both", expand=True, padx=40, pady=10)
        self.body.grid_columnconfigure(0, weight=4)
        self.body.grid_columnconfigure(1, weight=5)

        # LEFT
        left_p = ctk.CTkFrame(self.body, fg_color="transparent")
        left_p.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        t_box = ctk.CTkFrame(left_p, corner_radius=20, fg_color=("#ffffff", "#1e293b"))
        t_box.pack(fill="x", pady=5, ipady=15)
        self.timer_label = ctk.CTkLabel(t_box, text="00:00.00", font=ctk.CTkFont(size=70, weight="bold", family="Courier New"), text_color="#3498db")
        self.timer_label.pack(pady=5)
        self.btn_start = ctk.CTkButton(t_box, text="▶ INICIAR ESTUDIO", font=ctk.CTkFont(size=16, weight="bold"), height=40, command=self.start_timer)
        self.btn_start.pack()

        # PANEL DE ENFOQUE (PASO ACTUAL)
        self.focus_panel = ctk.CTkFrame(left_p, corner_radius=20, fg_color=("#ffffff", "#1e293b"))
        self.focus_panel.pack(fill="both", expand=True, pady=5)
        
        self.lbl_step_num = ctk.CTkLabel(self.focus_panel, text="Paso 1 de X", font=ctk.CTkFont(size=14, weight="bold"), text_color="gray")
        self.lbl_step_num.pack(pady=(20, 5))
        
        self.lbl_step_title = ctk.CTkLabel(self.focus_panel, text="Esperando Inicio...", font=ctk.CTkFont(size=24, weight="bold"), wraplength=350)
        self.lbl_step_title.pack(pady=10, padx=20)
        
        self.lbl_step_desc = ctk.CTkLabel(self.focus_panel, text="Presiona el botón de arriba para comenzar el estudio de tiempos.", 
                                         font=ctk.CTkFont(size=15), wraplength=350, justify="left")
        self.lbl_step_desc.pack(pady=20, padx=30)
        
        self.lbl_operator_focus = ctk.CTkLabel(self.focus_panel, text="Operador: -", font=ctk.CTkFont(size=13, slant="italic"))
        self.lbl_operator_focus.pack(pady=5)
        
        # Botones de acción del paso
        actions_f = ctk.CTkFrame(self.focus_panel, fg_color="transparent")
        actions_f.pack(pady=20)
        
        self.btn_focus_incident = ctk.CTkButton(actions_f, text="⚠️ Reportar Error", fg_color="#e67e22", hover_color="#d35400",
                                               state="disabled", command=lambda: self.record_incident(self.current_activity_index))
        self.btn_focus_incident.pack(side="left", padx=10)
        
        self.btn_focus_ok = ctk.CTkButton(actions_f, text="SIGUIENTE PASO ✅", fg_color="#2ecc71", hover_color="#27ae60",
                                         font=ctk.CTkFont(weight="bold"), state="disabled", 
                                         command=lambda: self.record_split(self.current_activity_index))
        self.btn_focus_ok.pack(side="left", padx=10)

        # Mantenemos la lógica de inicialización técnica pero oculta si es necesario
        self.step_uis = []
        for i, task in enumerate(self.app.ACTIVITIES):
            self.step_uis.append({"op": self.app.line_config.get(str(i), "N/A"), "incidents": []})

        # RIGHT
        right_p = ctk.CTkFrame(self.body, fg_color="transparent")
        right_p.grid(row=0, column=1, sticky="nsew", padx=(10, 0))
        v_panel = ctk.CTkFrame(right_p, corner_radius=20, fg_color="#000000", border_width=2, border_color="#3498db")
        v_panel.pack(fill="both", expand=True, pady=5)
        
        self.video_display = ctk.CTkLabel(v_panel, text="Esperando cámara...", width=500, height=350)
        self.video_display.pack(padx=10, pady=10, fill="both", expand=True)
        self.gesture_status_lbl = ctk.CTkLabel(v_panel, text="NO VINCULADO", font=ctk.CTkFont(size=16, weight="bold"), text_color="#f1c40f")
        self.gesture_status_lbl.pack(pady=(0, 10))
        self.trans_box = ctk.CTkFrame(right_p, corner_radius=20, fg_color=("#ffffff", "#1e293b"))

    def detect_motion(self, frame):
        # Tomar la esquina superior derecha como zona de trigger
        h, w = frame.shape[:2]
        zone = frame[20:150, w-150:w-20]
        gray = cv2.cvtColor(zone, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (21, 21), 0)

        trigger = False
        if self.prev_gray_zone is not None:
            delta = cv2.absdiff(self.prev_gray_zone, gray)
            thresh = cv2.threshold(delta, 25, 255, cv2.THRESH_BINARY)[1]
            motion_level = cv2.countNonZero(thresh)
            if motion_level > self.motion_threshold:
                trigger = True

        self.prev_gray_zone = gray
        # Dibujar recuadro verde para la zona
        cv2.rectangle(frame, (w-150, 20), (w-20, 150), (0, 255, 0), 2)
        cv2.putText(frame, "PASA LA MANO AQUI", (w-200, 170), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        
        return frame, trigger

    def update_loop(self):
        if not self.camera_active or self.cap is None: return
        ret, frame = self.cap.read()
        if ret:
            # Espejo si es cámara interna
            if isinstance(self.camera_source, int): 
                frame = cv2.flip(frame, 1)
            
            # Detectar movimiento en la zona (Reemplaza Mediapipe para evitar crasheos)
            frame, moved = self.detect_motion(frame)
            if moved:
                cv2.putText(frame, "ACCION DETECTADA!", (20, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 0), 3)
                self.handle_trigger()

            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            self.gesture_status_lbl.configure(text="VIDEO ACTIVO - PASA LA MANO POR EL RECUADRO", text_color="#2ecc71")
            
            # Render
            img = Image.fromarray(rgb)
            w, h = self.video_display.winfo_width(), self.video_display.winfo_height()
            if w > 20 and h > 20: 
                try: img = img.resize((w, h), Image.Resampling.LANCZOS)
                except: img = img.resize((w, h))

            tk_img = ImageTk.PhotoImage(image=img)
            self.video_display.configure(image=tk_img, text="")
            self.video_display.image_ref = tk_img
        self.after(30, self.update_loop)

    def handle_trigger(self):
        t = time.time()
        if hasattr(self, 'lt') and (t - self.lt < 3.0): return
        self.lt = t
        if not self.running and not self.waiting_for_operator: self.start_timer()
        elif self.running and not self.waiting_for_operator: self.record_split(self.current_activity_index)
        elif self.waiting_for_operator: self.resume()

    def start_timer(self):
        self.running = True
        self.st = time.time()
        self.at = self.st
        self.btn_start.configure(state="disabled")
        self.update_c()
        self.hl(0)

    def update_c(self):
        if self.running and not self.waiting_for_operator:
            e = time.time() - self.st
            self.timer_label.configure(text=f"{int(e/60):02d}:{int(e%60):02d}.{int((e%1)*100):02d}")
            self.after(35, self.update_c)

    def hl(self, i):
        self.current_activity_index = i
        total = len(self.app.ACTIVITIES)
        
        # Actualizar UI de enfoque
        self.lbl_step_num.configure(text=f"PASO {i+1} DE {total}")
        self.lbl_step_title.configure(text=self.app.ACTIVITIES[i])
        
        # Obtener descripción (o manejar si no hay)
        desc = self.app.FULL_DESCRIPTIONS[i] if i < len(self.app.FULL_DESCRIPTIONS) else "Sin descripción adicional."
        self.lbl_step_desc.configure(text=desc)
        
        op = self.step_uis[i]["op"]
        self.lbl_operator_focus.configure(text=f"👷 Resp: {op}")
        
        # Activar botones
        self.btn_focus_ok.configure(state="normal")
        self.btn_focus_incident.configure(state="normal")
        
        # Feedback visual en panel
        self.focus_panel.configure(border_width=2, border_color="#3498db")

    def record_split(self, i):
        t = time.time()
        self.current_cycle_splits.append({
            "activity": self.app.ACTIVITIES[i],
            "operator": self.step_uis[i]["op"],
            "duration": round(t - self.at, 2),
            "evidence": self.snap(i),
            "incidents": self.step_uis[i]["incidents"].copy()
        })
        self.at = t
        if i + 1 < len(self.app.ACTIVITIES):
            if self.step_uis[i]["op"] != self.step_uis[i+1]["op"]:
                self.trans(self.step_uis[i+1]["op"], i+1)
            else:
                self.current_activity_index = i + 1
                self.hl(i+1)
        else: self.fin()

    def record_incident(self, i):
        desc = simpledialog.askstring("Incidente", "¿Cuál fue el error u observación?", parent=self)
        if desc:
            p = self.snap(i, is_error=True)
            self.step_uis[i]["incidents"].append({
                "description": desc,
                "timestamp": datetime.now().strftime("%H:%M:%S"),
                "photo": p
            })
            messagebox.showinfo("Incidente", "Error registrado con evidencia visual.")

    def snap(self, i, is_error=False):
        if not self.cap: return None
        ret, f = self.cap.read()
        if ret:
            prefix = "error" if is_error else "evid"
            p = os.path.join(self.media_path, f"{prefix}_{i+1}_{int(time.time())}.jpg")
            cv2.imwrite(p, f)
            return p
        return None

    def trans(self, op, idx):
        self.waiting_for_operator = True
        self.current_activity_index = idx
        self.trans_box.place(relx=0, rely=0, relwidth=1, relheight=1)
        for w in self.trans_box.winfo_children(): w.destroy()
        ctk.CTkLabel(self.trans_box, text="🔄 CAMBIO DE OPERARIO", font=ctk.CTkFont(size=24, weight="bold"), text_color="#f1c40f").pack(pady=40)
        ctk.CTkLabel(self.trans_box, text=f"Entra a línea: {op}\nPasa la mano por el recuadro para continuar", font=ctk.CTkFont(size=18)).pack(pady=20)

    def resume(self):
        self.waiting_for_operator = False
        self.trans_box.place_forget()
        self.at = time.time()
        self.hl(self.current_activity_index)
        self.update_c()

    def fin(self):
        self.running = False
        if self.cap: self.cap.release()
        total = round(time.time() - self.st, 2)
        meas = {"cycle_id": len(self.app.data.get("measurements", [])) + 1, "model": self.app.current_model_name, "total_time": total, "splits": self.current_cycle_splits}
        self.app.data.setdefault("measurements", []).append(meas)
        self.app.save_data()
        messagebox.showinfo("Exito", f"Estudio Guardado Correctamente.\nTiempo total: {total}s")
        self.app.show_dashboard()

    def reset_timer(self):
        if self.cap: self.cap.release()
        self.app.show_dashboard()

    def __del__(self):
        if hasattr(self, 'cap') and self.cap: self.cap.release()
