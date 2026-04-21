import customtkinter as ctk
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import os
from views.env_table import EnvTableEditor

class MediaGalleryView(ctk.CTkFrame):
    def __init__(self, master, app):
        super().__init__(master, fg_color="transparent")
        self.app = app
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=3)
        self.grid_rowconfigure(0, weight=1)
        
        self.build_ui()

    def build_ui(self):
        # Sidebar for study selector
        self.list_frame = ctk.CTkFrame(self, width=250, corner_radius=15)
        self.list_frame.grid(row=0, column=0, sticky="nsew", padx=(40, 10), pady=20)
        
        ctk.CTkLabel(self.list_frame, text="📦 Seleccionar Ciclo", font=ctk.CTkFont(size=18, weight="bold")).pack(pady=15)
        
        ctk.CTkButton(self.list_frame, text="🧩 Juntar Ciclos (Merge)", fg_color="#8e44ad", hover_color="#9b59b6", command=self.merge_cycles_ui).pack(fill="x", padx=10, pady=(0, 10))
        
        self.scroll_list = ctk.CTkScrollableFrame(self.list_frame)
        self.scroll_list.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Details area
        self.details_frame = ctk.CTkFrame(self, corner_radius=15)
        self.details_frame.grid(row=0, column=1, sticky="nsew", padx=(10, 40), pady=20)
        
        self.update_measurement_list()

    def merge_cycles_ui(self):
        from tkinter import messagebox
        measurements = self.app.data.get("measurements", [])
        if not measurements: return

        # Pre-calcular indices relativos
        model_counts = {}
        for m in measurements:
            mod = m.get('model', 'N/A')
            model_counts[mod] = model_counts.get(mod, 0) + 1
            m['_rel_id'] = model_counts[mod]

        win = ctk.CTkToplevel(self.app)
        win.title("Juntar Ciclos en Lote")
        win.geometry("400x500")
        win.grab_set()
        win.attributes("-topmost", True)

        ctk.CTkLabel(win, text="🧩 Selecciona los ciclos a agrupar", font=ctk.CTkFont(size=18, weight="bold")).pack(pady=15)
        
        scroll = ctk.CTkScrollableFrame(win)
        scroll.pack(fill="both", expand=True, padx=20, pady=10)

        vars_dict = {}
        for i, m in enumerate(measurements):
            var = tk.BooleanVar(value=False)
            chk = ctk.CTkCheckBox(scroll, text=f"{m.get('model', 'N/A')} - Ciclo #{m.get('_rel_id', '?')}", variable=var)
            chk.pack(anchor="w", pady=5)
            vars_dict[i] = var

        def on_confirm():
            selected_indices = [idx for idx, v in vars_dict.items() if v.get()]
            if len(selected_indices) < 2:
                messagebox.showwarning("Atención", "Selecciona al menos 2 ciclos para unirlos.")
                return
            
            targets = [measurements[i] for i in selected_indices]
            base_mod = targets[0].get('model', 'N/A')
            
            # Filtrar targets solo por ese modelo
            targets = [m for m in targets if m.get('model', 'N/A') == base_mod]
            if len(targets) < 2:
                messagebox.showwarning("Atención", "Los ciclos a agrupar deben pertenecer al mismo Modelo.")
                return
                
            self.execute_merge(targets, measurements)
            win.destroy()

        ctk.CTkButton(win, text="Fusionar Seleccionados", command=on_confirm, fg_color="#2ecc71", hover_color="#27ae60").pack(pady=20)

    def execute_merge(self, targets, measurements):
        base_mod = targets[0].get('model', 'N/A')
        if len(targets) < 2: return
        
        # Crear el super-ciclo
        super_c = {
            "model": base_mod,
            "volume": sum(m.get("volume", 1) for m in targets),
            "total_time": round(sum(m.get("total_time", 0.0) for m in targets), 2),
            "lux_data": [],
            "db_data": [],
            "splits": []
        }
        
        # Combinar ambientes
        for m in targets:
            super_c["lux_data"].extend(m.get("lux_data", []))
            super_c["db_data"].extend(m.get("db_data", []))
            
        # Combinar splits
        num_steps = len(targets[0].get("splits", []))
        for i in range(num_steps):
            t_dur = 0.0
            t_evidences = []
            t_incidents = []
            t_act = targets[0]["splits"][i].get("activity", f"Tarea {i+1}")
            t_op = targets[0]["splits"][i].get("operator", "N/A")
            for m in targets:
                if i < len(m["splits"]):
                    sp = m["splits"][i]
                    t_dur += sp.get("duration", 0.0)
                    if sp.get("evidence"): t_evidences.append(sp["evidence"])
                    if sp.get("evidences"): t_evidences.extend(sp["evidences"])
                    if sp.get("incidents"): t_incidents.extend(sp["incidents"])
            
            super_c["splits"].append({
                "activity": t_act,
                "operator": t_op,
                "duration": round(t_dur, 2),
                "evidences": list(set(t_evidences)),
                "incidents": list(set(t_incidents))
            })
            
        # Reemplazar en data
        new_ms = []
        added_super = False
        for m in measurements:
            if m in targets:
                if not added_super:
                    new_ms.append(super_c)
                    added_super = True
            else:
                new_ms.append(m)
                
        self.app.data["measurements"] = new_ms
        self.app.save_data()
        self.update_measurement_list()
        
    def update_measurement_list(self):
        for widget in self.scroll_list.winfo_children():
            widget.destroy()
            
        measurements = self.app.data.get("measurements", [])
        if not measurements:
            ctk.CTkLabel(self.scroll_list, text="No hay mediciones").pack(pady=20)
            return
            
        # Pre-calcular el número relativo de ciclo para cada modelo
        model_counts = {}
        for m in measurements:
            mod = m.get('model', 'N/A')
            model_counts[mod] = model_counts.get(mod, 0) + 1
            m['_rel_id'] = model_counts[mod]

        for i, m in enumerate(reversed(measurements)):
            model_name = m.get('model', 'N/A')
            rel_id = m.get('_rel_id', "?")
            
            btn = ctk.CTkButton(self.scroll_list, 
                                text=f"{model_name}\nCiclo #{rel_id}", 
                                fg_color=("#34495e", "#2c3e50"),
                                hover_color="#3498db",
                                command=lambda val=m: self.show_details(val))
            btn.pack(fill="x", pady=5)
            if i == 0: self.after(100, lambda: self.show_details(m))

    def show_details(self, measurement):
        for widget in self.details_frame.winfo_children():
            widget.destroy()
            
        header = ctk.CTkFrame(self.details_frame, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=20)
        
        title_text = f"📸 {measurement.get('model')} - Ciclo #{measurement.get('_rel_id', '?')}"
        ctk.CTkLabel(header, text=title_text, 
                     font=ctk.CTkFont(size=22, weight="bold")).pack(side="left")
        
        ctk.CTkLabel(header, text=f"⏱️ Tiempo Total: {measurement.get('total_time')}s", 
                     font=ctk.CTkFont(size=14, weight="bold")).pack(side="right", padx=(10, 0))
                     
        v_frame = ctk.CTkFrame(header, fg_color="transparent")
        v_frame.pack(side="right", padx=10)
        ctk.CTkLabel(v_frame, text="📦 Volumen (Unidades):").pack(side="left")
        self.vol_entry = ctk.CTkEntry(v_frame, width=50)
        self.vol_entry.insert(0, str(measurement.get("volume", 1)))
        self.vol_entry.pack(side="left", padx=5)

        # Editables de Ambiente
        env_tabs = ctk.CTkTabview(self.details_frame, height=200)
        env_tabs.pack(fill="x", padx=20, pady=(0, 15))
        
        tab_l = env_tabs.add("💡 Luxómetro")
        tab_s = env_tabs.add("🔊 Sonómetro")
        
        self.lv_editor = EnvTableEditor(tab_l, unit_label="Nivel (lx)")
        self.lv_editor.pack(fill="both", expand=True)
        self.lv_editor.load_data(measurement.get("lux_data", []))
        
        self.sv_editor = EnvTableEditor(tab_s, unit_label="Nivel (dB)")
        self.sv_editor.pack(fill="both", expand=True)
        self.sv_editor.load_data(measurement.get("db_data", []))
        
        # The button should be outside the Tabview
        btn_save = ctk.CTkButton(self.details_frame, text="💾 GUARDAR CAMBIOS AMBIENTALES", height=28, fg_color="#27ae60",
                                 command=lambda: self.save_env(measurement, btn_save))
        btn_save.pack(pady=(0, 15))

        # Scrollable area for steps
        scroll_details = ctk.CTkScrollableFrame(self.details_frame)
        scroll_details.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        
        for i, split in enumerate(measurement.get("splits", [])):
            step_f = ctk.CTkFrame(scroll_details, corner_radius=10, border_width=1, border_color="#34495e")
            step_f.pack(fill="x", pady=10, padx=5)
            
            # Left side: Step info
            info_f = ctk.CTkFrame(step_f, fg_color="transparent")
            info_f.pack(side="left", fill="both", expand=True, padx=15, pady=15)
            
            act = split.get('activity', 'Tarea sin nombre')
            op = split.get('operator', 'No asignado')
            ctk.CTkLabel(info_f, text=f"Paso {i+1}: {act}", font=ctk.CTkFont(weight="bold")).pack(anchor="w")
            ctk.CTkLabel(info_f, text=f"Operador: {op} | Tiempo: {split.get('duration', 0.0)}s").pack(anchor="w")
            
            # Incidents
            if split.get("incidents"):
                ctk.CTkLabel(info_f, text="⚠️ INCIDENTES:", font=ctk.CTkFont(size=11, weight="bold"), text_color="#e67e22").pack(anchor="w", pady=(10, 0))
                for inc in split["incidents"]:
                    inc_f = ctk.CTkFrame(info_f, fg_color=("#f39c12", "#4b2c20"), corner_radius=5)
                    inc_f.pack(fill="x", pady=2)
                    ctk.CTkLabel(inc_f, text=f"[{inc['timestamp']}] {inc['description']}", font=ctk.CTkFont(size=11)).pack(padx=5)
                    if inc.get("photo"):
                        self.load_thumbnail(inc_f, inc["photo"])
            
            # Right side: Main photo
            photo_f = ctk.CTkFrame(step_f, fg_color="transparent", width=150)
            photo_f.pack(side="right", padx=15, pady=15)
            
            has_photo = False
            if split.get("evidence"):
                self.load_thumbnail(photo_f, split["evidence"], size=(90, 70))
                has_photo = True
            if split.get("evidences"):
                # Mostrar en cuadricula
                grid_f = ctk.CTkFrame(photo_f, fg_color="transparent")
                grid_f.pack()
                for img_idx, path in enumerate(split["evidences"]):
                    self.load_thumbnail(grid_f, path, size=(50, 40), in_grid=True, r=img_idx//3, c=img_idx%3)
                has_photo = True
                
            if not has_photo:
                ctk.CTkLabel(photo_f, text="Sin Foto", font=ctk.CTkFont(size=10)).pack()

    def save_env(self, measurement, btn):
        try: measurement['volume'] = int(self.vol_entry.get())
        except: measurement['volume'] = 1
        measurement['lux_data'] = self.lv_editor.get_data()
        measurement['db_data'] = self.sv_editor.get_data()
        self.app.save_data()
        
        # Feedback visual
        btn.configure(text="✅ GUARDADO", fg_color="#2ecc71")
        self.after(2000, lambda: btn.configure(text="💾 GUARDAR CAMBIOS AMBIENTALES", fg_color="#27ae60"))

    def load_thumbnail(self, master, path, size=(80, 60), in_grid=False, r=0, c=0):
        if not os.path.exists(path): return
        try:
            img = Image.open(path)
            ctk_img = ctk.CTkImage(light_image=img, size=size)
            lbl = ctk.CTkLabel(master, image=ctk_img, text="")
            lbl.image_ref = ctk_img
            if in_grid: lbl.grid(row=r, column=c, padx=2, pady=2)
            else: lbl.pack(pady=5)
            
            lbl.bind("<Button-1>", lambda e, p=path: self.open_full_image(p))
        except: pass

    def open_full_image(self, path):
        top = ctk.CTkToplevel(self)
        top.title("Evidencia Visual")
        top.attributes("-topmost", True)
        
        img = Image.open(path)
        w, h = img.size
        scale = min(1200 / w, 800 / h)
        new_size = (int(w * scale), int(h * scale))
        
        ctk_img = ctk.CTkImage(light_image=img, size=new_size)
        lbl = ctk.CTkLabel(top, image=ctk_img, text="")
        lbl.image_ref = ctk_img
        lbl.pack(padx=20, pady=20)
