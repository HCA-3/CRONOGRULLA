import customtkinter as ctk
import tkinter as tk
from PIL import Image, ImageTk
import os

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
        
        self.scroll_list = ctk.CTkScrollableFrame(self.list_frame)
        self.scroll_list.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Details area
        self.details_frame = ctk.CTkFrame(self, corner_radius=15)
        self.details_frame.grid(row=0, column=1, sticky="nsew", padx=(10, 40), pady=20)
        
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
                     font=ctk.CTkFont(size=14)).pack(side="right")

        # Scrollable area for steps
        scroll_details = ctk.CTkScrollableFrame(self.details_frame)
        scroll_details.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        
        for i, split in enumerate(measurement.get("splits", [])):
            step_f = ctk.CTkFrame(scroll_details, corner_radius=10, border_width=1, border_color="#34495e")
            step_f.pack(fill="x", pady=10, padx=5)
            
            # Left side: Step info
            info_f = ctk.CTkFrame(step_f, fg_color="transparent")
            info_f.pack(side="left", fill="both", expand=True, padx=15, pady=15)
            
            ctk.CTkLabel(info_f, text=f"Paso {i+1}: {split['activity']}", font=ctk.CTkFont(weight="bold")).pack(anchor="w")
            ctk.CTkLabel(info_f, text=f"Operador: {split['operator']} | Tiempo: {split['duration']}s").pack(anchor="w")
            
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
            
            if split.get("evidence"):
                self.load_thumbnail(photo_f, split["evidence"], size=(120, 90))
            else:
                ctk.CTkLabel(photo_f, text="Sin Foto", font=ctk.CTkFont(size=10)).pack()

    def load_thumbnail(self, master, path, size=(80, 60)):
        if not os.path.exists(path): return
        try:
            img = Image.open(path)
            img = img.resize(size, Image.Resampling.LANCZOS)
            tk_img = ImageTk.PhotoImage(img)
            lbl = ctk.CTkLabel(master, image=tk_img, text="")
            lbl.image_ref = tk_img
            lbl.pack(pady=5)
            
            # Click to view full
            lbl.bind("<Button-1>", lambda e, p=path: self.open_full_image(p))
        except: pass

    def open_full_image(self, path):
        top = ctk.CTkToplevel(self)
        top.title("Evidencia Visual")
        top.attributes("-topmost", True)
        
        img = Image.open(path)
        # Scale to fit screen roughly
        w, h = img.size
        scale = min(1200 / w, 800 / h)
        img = img.resize((int(w * scale), int(h * scale)), Image.Resampling.LANCZOS)
        
        tk_img = ImageTk.PhotoImage(img)
        lbl = ctk.CTkLabel(top, image=tk_img, text="")
        lbl.image_ref = tk_img
        lbl.pack(padx=20, pady=20)
