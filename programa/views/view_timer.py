import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox, simpledialog, filedialog
import pandas as pd
import cv2
from PIL import Image, ImageTk
import threading
import json
import os
import numpy as np

class EnvDataDialog(ctk.CTkToplevel):
    def __init__(self, master, mode="lux", callback=None, stations=None):
        super().__init__(master)
        self.title("Ingreso Técnico Avanzado")
        self.geometry("650x700")
        self.attributes("-topmost", True)
        self.grab_set()
        self.callback = callback
        self.mode = mode
        self.stations = stations or []
        self.worker_data = [] 
        self.build_ui()

    def build_ui(self):
        title = "💡 LUXOMETRÍA" if self.mode == "lux" else "🔊 SONOMETRÍA"
        ctk.CTkLabel(self, text=title, font=ctk.CTkFont(size=22, weight="bold")).pack(pady=20)
        self.scroll = ctk.CTkScrollableFrame(self)
        self.scroll.pack(padx=20, pady=10, fill="both", expand=True)
        
        if self.mode == "lux": self.setup_lux_ui()
        else: self.setup_sound_ui()
            
        btn_f = ctk.CTkFrame(self, fg_color="transparent"); btn_f.pack(pady=20)
        ctk.CTkButton(btn_f, text="GUARDAR", fg_color="#2ecc71", command=self.save_and_close).pack(side="left", padx=5)
        ctk.CTkButton(btn_f, text="GLOBAL EXCEL", fg_color="#3498db", command=self.import_data).pack(side="left", padx=5)
        ctk.CTkButton(btn_f, text="SALTAR", fg_color="#95a5a6", command=self.skip_and_close).pack(side="left", padx=5)

    def import_for_worker(self, info):
        file_path = filedialog.askopenfilename(filetypes=[("Excel/CSV", "*.xlsx *.csv")])
        if not file_path: return
        try:
            df = pd.read_csv(file_path) if file_path.endswith('.csv') else pd.read_excel(file_path)
            sub_df = df[df["Operario"].astype(str) == info["name"]] if "Operario" in df.columns else df
            if len(sub_df) == 0: return messagebox.showwarning("Aviso", "No hay datos para este operario.")
            info["count_e"].delete(0, 'end'); info["count_e"].insert(0, str(len(sub_df)))
            if self.mode == "lux": self.refresh_lux_rows(info)
            else: self.refresh_sound_rows_grouped(info)
            for i in range(len(sub_df)):
                row = sub_df.iloc[i]
                if self.mode == "lux":
                    v = row["LUX"] if "LUX" in sub_df.columns else row.iloc[0]
                    info["entries"][i].insert(0, str(v))
                else:
                    loc = row["Lugar"] if "Lugar" in sub_df.columns else "Punto"
                    db = row["dB"] if "dB" in sub_df.columns else row.iloc[0]
                    info["entries"][i][0].insert(0, str(loc)); info["entries"][i][1].insert(0, str(db))
            messagebox.showinfo("Éxito", f"Datos cargados para {info['name']}")
        except Exception as e: messagebox.showerror("Error", str(e))

    def export_for_worker(self, info):
        file_path = filedialog.asksaveasfilename(defaultextension=".xlsx")
        if not file_path: return
        data = []
        for e in info["entries"]:
            if self.mode == "lux": data.append({"Operario": info["name"], "LUX": e.get()})
            else: data.append({"Operario": info["name"], "Lugar": e[0].get(), "dB": e[1].get()})
        try: pd.DataFrame(data).to_excel(file_path, index=False); messagebox.showinfo("Éxito", "Exportado.")
        except Exception as e: messagebox.showerror("Error", str(e))

    def setup_lux_ui(self):
        for s in self.stations:
            card = ctk.CTkFrame(self.scroll, fg_color=("#f1f5f9", "#1e293b"), corner_radius=10); card.pack(fill="x", pady=10, padx=10)
            top = ctk.CTkFrame(card, fg_color="transparent"); top.pack(fill="x", padx=10, pady=5)
            ctk.CTkLabel(top, text=f"👤 {s['op_name']}", font=ctk.CTkFont(weight="bold")).pack(side="left")
            ce = ctk.CTkEntry(top, width=50); ce.insert(0, "1"); ce.pack(side="left", padx=10)
            rf = ctk.CTkFrame(card, fg_color="transparent"); rf.pack(fill="x", padx=20, pady=5)
            w_info = {"name": s['op_name'], "rows_f": rf, "entries": [], "count_e": ce}
            ops_f = ctk.CTkFrame(top, fg_color="transparent"); ops_f.pack(side="right")
            ctk.CTkButton(ops_f, text="📥", width=30, height=24, command=lambda info=w_info: self.import_for_worker(info)).pack(side="left", padx=2)
            ctk.CTkButton(ops_f, text="📤", width=30, height=24, command=lambda info=w_info: self.export_for_worker(info)).pack(side="left", padx=2)
            ctk.CTkButton(ops_f, text="⚙️", width=30, height=24, command=lambda info=w_info: self.refresh_lux_rows(info)).pack(side="left", padx=2)
            self.worker_data.append(w_info); self.refresh_lux_rows(w_info)

    def refresh_lux_rows(self, info):
        for w in info["rows_f"].winfo_children(): w.destroy()
        info["entries"] = []
        try: n = int(info["count_e"].get())
        except: n = 1
        for i in range(n):
            row, col = divmod(i, 4)
            e = ctk.CTkEntry(info["rows_f"], placeholder_text=f"M{i+1}", width=90)
            e.grid(row=row, column=col, padx=5, pady=5); info["entries"].append(e)

    def setup_sound_ui(self):
        for s in self.stations:
            card = ctk.CTkFrame(self.scroll, fg_color=("#fef2f2", "#450a0a"), corner_radius=10); card.pack(fill="x", pady=10, padx=10)
            top = ctk.CTkFrame(card, fg_color="transparent"); top.pack(fill="x", padx=10, pady=5)
            ctk.CTkLabel(top, text=f"👤 {s['op_name']}", font=ctk.CTkFont(weight="bold")).pack(side="left")
            ce = ctk.CTkEntry(top, width=50); ce.insert(0, "1"); ce.pack(side="left", padx=10)
            rf = ctk.CTkFrame(card, fg_color="transparent"); rf.pack(fill="x", padx=20, pady=5)
            w_info = {"name": s['op_name'], "rows_f": rf, "entries": [], "count_e": ce}
            ops_f = ctk.CTkFrame(top, fg_color="transparent"); ops_f.pack(side="right")
            ctk.CTkButton(ops_f, text="📥", width=30, height=24, command=lambda info=w_info: self.import_for_worker(info)).pack(side="left", padx=2)
            ctk.CTkButton(ops_f, text="📤", width=30, height=24, command=lambda info=w_info: self.export_for_worker(info)).pack(side="left", padx=2)
            ctk.CTkButton(ops_f, text="⚙️", width=30, height=24, command=lambda info=w_info: self.refresh_sound_rows_grouped(info)).pack(side="left", padx=2)
            self.worker_data.append(w_info); self.refresh_sound_rows_grouped(w_info)

    def refresh_sound_rows_grouped(self, info):
        for w in info["rows_f"].winfo_children(): w.destroy()
        info["entries"] = []
        try: n = int(info["count_e"].get())
        except: n = 1
        for i in range(n):
            row, col = divmod(i, 2); f = ctk.CTkFrame(info["rows_f"], fg_color="transparent"); f.grid(row=row, column=col, padx=4, pady=2)
            le = ctk.CTkEntry(f, placeholder_text="Lugar", width=130); le.pack(side="left", padx=2)
            de = ctk.CTkEntry(f, placeholder_text="dB", width=60); de.pack(side="left", padx=2)
            info["entries"].append((le, de))

    def save_and_close(self):
        res = []
        for w in self.worker_data:
            if self.mode == "lux":
                vals = [float(e.get() or 0) for e in w["entries"]]
                res.append({"puesto": w["name"], "lux": vals})
            else:
                meds = [{"lugar": le.get() or "Punto", "db": float(de.get() or 0)} for le, de in w["entries"]]
                res.append({"operario": w["name"], "medidas": meds})
        self.destroy()
        if self.callback:
            self.callback(res)

    def skip_and_close(self): 
        self.destroy()
        if self.callback:
            self.callback([])
    def import_data(self): messagebox.showinfo("Info", "Use los botones 📥 de cada operario.")

class TimerView(ctk.CTkFrame):
    def __init__(self, master, app):
        super().__init__(master, fg_color="transparent")
        self.app = app
        self.running = False
        self.camera_source = 0
        self.build_ui()

    def build_ui(self):
        top = ctk.CTkFrame(self, fg_color="transparent")
        top.pack(fill="x", pady=10)
        self.cam_lbl = ctk.CTkLabel(top, text="Cámara", fg_color="black", width=800, height=450, corner_radius=15)
        self.cam_lbl.pack(pady=10)
        
        ctrl = ctk.CTkFrame(self, fg_color=("#ffffff", "#1e293b"), corner_radius=15)
        ctrl.pack(fill="x", padx=20, pady=10)
        self.btn_start = ctk.CTkButton(ctrl, text="▶ INICIAR ESTUDIO", command=self.start_study, fg_color="#10b981", height=45, font=ctk.CTkFont(size=15, weight="bold"))
        self.btn_start.pack(side="left", expand=True, padx=20, pady=15)
        self.btn_stop = ctk.CTkButton(ctrl, text="🛑 DETENER", command=self.stop_study, fg_color="#ef4444", height=45)
        self.btn_stop.pack(side="left", expand=True, padx=20, pady=15)

        self.stations_f = ctk.CTkFrame(self, fg_color="transparent")
        self.stations_f.pack(fill="x", padx=20, pady=10)
        self.stations = []
        op_names = self.app.data.get("operators", ["Laura", "Diego", "David"])
        colors = [("#dcfce7", "#064e3b"), ("#dbeafe", "#1e3a8a"), ("#fef3c7", "#78350f")]
        for i in range(3):
            s_f = ctk.CTkFrame(self.stations_f, fg_color=colors[i][0], corner_radius=12)
            s_f.pack(side="left", expand=True, fill="both", padx=5)
            ctk.CTkLabel(s_f, text=f"👤 {op_names[i]}", font=ctk.CTkFont(size=14, weight="bold")).pack(pady=5)
            timer_lbl = ctk.CTkLabel(s_f, text="0.00s", font=ctk.CTkFont(size=24, family="Courier"))
            timer_lbl.pack(pady=5)
            palm_f = ctk.CTkFrame(s_f, width=60, height=40, fg_color="gray")
            palm_f.pack(pady=5)
            self.stations.append({"op_name": op_names[i], "lbl": timer_lbl, "palm": palm_f, "time": 0.0, "active": False})

    def start_study(self):
        goal = simpledialog.askinteger("Config", "¿Meta de grullas?", initialvalue=5)
        if not goal: return
        self.production_goal = goal
        def on_lux(data):
            self.lux_data = data
            EnvDataDialog(self.master, mode="sound", callback=on_sound, stations=self.stations)
        def on_sound(data):
            self.sound_data = data
            self.running = True
            threading.Thread(target=self.camera_loop, daemon=True).start()
        EnvDataDialog(self.master, mode="lux", callback=on_lux, stations=self.stations)

    def stop_study(self):
        self.running = False
        if hasattr(self, 'cap'):
            self.cap.release()
        messagebox.showinfo("Fin", "Estudio finalizado.")

    def camera_loop(self):
        self.cap = cv2.VideoCapture(self.camera_source)
        while self.running:
            ret, frame = self.cap.read()
            if not ret: break
            cv2.rectangle(frame, (50, 200), (150, 300), (0, 255, 255), 2)
            cv2.rectangle(frame, (270, 200), (370, 300), (0, 255, 255), 2)
            cv2.rectangle(frame, (490, 200), (590, 300), (0, 255, 255), 2)
            img = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
            img_tk = ImageTk.PhotoImage(img)
            self.cam_lbl.configure(image=img_tk, text=""); self.cam_lbl.image = img_tk
        self.cap.release()
