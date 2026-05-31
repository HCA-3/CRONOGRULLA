import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
import numpy as np

class StandardTimeView(ctk.CTkFrame):
    def __init__(self, master, app):
        super().__init__(master, fg_color="transparent")
        self.app = app
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        
        # Valores por defecto para cálculos
        self.default_rating = 100 # %
        self.default_allowance = 12 # % (Fatiga, personales, etc)
        
        self.build_ui()

    def build_ui(self):
        # Título y Header
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=40, pady=20)
        
        ctk.CTkLabel(header, text="📊 Determinación de Tiempo Estándar", 
                     font=ctk.CTkFont(size=26, weight="bold")).pack(side="left")
        
        # Selector de Modelo
        self.model_var = tk.StringVar(value=self.app.current_model_name)
        selector = ctk.CTkOptionMenu(header, values=list(self.app.models.keys()), 
                                    variable=self.model_var, command=self.refresh_data)
        selector.pack(side="right", padx=10)

        # Panel de Parámetros Globales
        params_p = ctk.CTkFrame(self, corner_radius=15)
        params_p.pack(fill="x", padx=40, pady=(0, 10))
        
        ctk.CTkLabel(params_p, text="⚙️ Parámetros de Estudio (Globales):", font=ctk.CTkFont(weight="bold")).grid(row=0, column=0, padx=20, pady=10)
        
        ctk.CTkLabel(params_p, text="Calificación (%):").grid(row=0, column=1, padx=5)
        self.rating_ent = ctk.CTkEntry(params_p, width=60)
        self.rating_ent.insert(0, str(self.default_rating))
        self.rating_ent.grid(row=0, column=2, padx=5)
        
        ctk.CTkLabel(params_p, text="Suplementos (%):").grid(row=0, column=3, padx=5)
        self.allow_ent = ctk.CTkEntry(params_p, width=60)
        self.allow_ent.insert(0, str(self.default_allowance))
        self.allow_ent.grid(row=0, column=4, padx=5)
        
        ctk.CTkButton(params_p, text="🔄 Recalcular Todo", command=self.refresh_data, 
                      fg_color="#3498db", width=120).grid(row=0, column=5, padx=20)

        self.operator_allowance_vars = {}
        self.last_operator_list = []
        self.allowances_frame = ctk.CTkFrame(self, corner_radius=15)
        self.allowances_frame.pack(fill="x", padx=40, pady=(0, 10))
        ctk.CTkLabel(self.allowances_frame, text="🧑‍🏭 Suplementos individuales por operario:",
                     font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=20, pady=(10, 5))
        self.allow_inputs = ctk.CTkFrame(self.allowances_frame, fg_color="transparent")
        self.allow_inputs.pack(fill="x", padx=20, pady=(0, 10))
        ctk.CTkButton(self.allowances_frame, text="Guardar Suplementos", command=self.save_operator_allowances,
                      fg_color="#27ae60", width=180).pack(anchor="e", padx=20, pady=(0, 10))
        
        self.render_operator_allowance_inputs()

        # Contenedor de la Tabla
        self.table_container = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.table_container.pack(fill="both", expand=True, padx=40, pady=(0, 20))
        
        self.refresh_data()

    def render_operator_allowance_inputs(self):
        for widget in self.allow_inputs.winfo_children():
            widget.destroy()
        self.operator_allowance_vars.clear()

        operators = self.app.operator_data or []
        if not operators:
            ctk.CTkLabel(self.allow_inputs, text="No hay operarios configurados. Ve a Equipo y Tareas para agregarlos.",
                         text_color="gray").pack(anchor="w", pady=10)
            return

        for op_name in operators:
            row = ctk.CTkFrame(self.allow_inputs, fg_color="transparent")
            row.pack(fill="x", pady=4)
            ctk.CTkLabel(row, text=op_name, width=220, anchor="w").pack(side="left", padx=(0, 10))
            var = tk.StringVar(value=str(self.app.operator_allowances.get(op_name, self.default_allowance)))
            entry = ctk.CTkEntry(row, width=80, textvariable=var)
            entry.pack(side="left")
            ctk.CTkLabel(row, text="%").pack(side="left", padx=(5, 0))
            self.operator_allowance_vars[op_name] = var

    def get_operator_allowances(self):
        allowances = {}
        for op_name, var in self.operator_allowance_vars.items():
            try:
                allowances[op_name] = float(var.get())
            except ValueError:
                allowances[op_name] = self.default_allowance
        return allowances

    def save_operator_allowances(self):
        self.app.operator_allowances = self.get_operator_allowances()
        self.app.save_data()
        messagebox.showinfo("Guardado", "Suplementos individuales guardados correctamente.")
        self.refresh_data()

    def refresh_data(self, *args):
        if self.app.operator_data != self.last_operator_list:
            self.render_operator_allowance_inputs()
            self.last_operator_list = list(self.app.operator_data)

        for widget in self.table_container.winfo_children():
            widget.destroy()
            
        model_name = self.model_var.get()
        activities = self.app.models[model_name]["activities"]
        measurements = [m for m in self.app.data.get("measurements", []) if m.get("model") == model_name]
        
        if not measurements:
            ctk.CTkLabel(self.table_container, text="Sin datos de medición para este modelo.", 
                         text_color="gray").pack(pady=50)
            return

        # Cabecera de Tabla Premium
        headers = ["Tarea", "Oper.", "N", "Avg (X)", "Rango (R)", "R/X (%)", "Calif.", "T. Normal", "Suplem.", "T. Estándar"]
        h_frame = ctk.CTkFrame(self.table_container, fg_color="#34495e", height=40)
        h_frame.pack(fill="x", pady=2)
        
        widths = [180, 120, 40, 80, 80, 80, 60, 80, 70, 100]
        for i, h in enumerate(headers):
            lbl = ctk.CTkLabel(h_frame, text=h, width=widths[i], font=ctk.CTkFont(size=11, weight="bold"), text_color="white")
            lbl.pack(side="left", padx=2)

        try:
            global_rating = float(self.rating_ent.get()) / 100
            global_allow = float(self.allow_ent.get()) / 100
        except:
            global_rating, global_allow = 1.0, 0.12

        operator_allowances = self.get_operator_allowances() if self.operator_allowance_vars else self.app.operator_allowances or {}
        total_ts_sum = 0
        
        # Procesar cada actividad
        for idx, act in enumerate(activities):
            times = []
            for m in measurements:
                if idx < len(m["splits"]):
                    times.append(m["splits"][idx]["duration"])
            
            if not times: continue
            
            n = len(times)
            avg = np.mean(times)
            rango = max(times) - min(times)
            rx = (rango / avg * 100) if avg > 0 else 0
            
            tn = avg * global_rating
            op_name = self.app.line_config.get(str(idx), "N/A")
            individual_allow_pct = operator_allowances.get(op_name, global_allow * 100)
            ts = tn * (1 + individual_allow_pct / 100)
            total_ts_sum += ts
            
            # Fila de datos
            row = ctk.CTkFrame(self.table_container, fg_color=("#f1f2f6", "#2d3436") if idx%2==0 else "transparent")
            row.pack(fill="x", pady=1)
            
            # Aplicar regla Maytag (Warning si insuficiente)
            warning_color = "white"
            if (avg <= 120 and n < 10) or (avg > 120 and n < 5): # 120s = 2min
                warning_color = "#e67e22" # Naranja para advertencia Maytag

            ctk.CTkLabel(row, text=act[:25], width=widths[0], anchor="w").pack(side="left", padx=5)
            ctk.CTkLabel(row, text=op_name, width=widths[1], anchor="w").pack(side="left")
            ctk.CTkLabel(row, text=str(n), width=widths[2], text_color=warning_color).pack(side="left")
            ctk.CTkLabel(row, text=f"{avg:.2f}s", width=widths[3]).pack(side="left")
            ctk.CTkLabel(row, text=f"{rango:.2f}s", width=widths[4]).pack(side="left")
            ctk.CTkLabel(row, text=f"{rx:.1f}%", width=widths[5]).pack(side="left")
            ctk.CTkLabel(row, text=f"{global_rating*100:.0f}%", width=widths[6]).pack(side="left")
            ctk.CTkLabel(row, text=f"{tn:.2f}s", width=widths[7], font=ctk.CTkFont(weight="bold")).pack(side="left")
            ctk.CTkLabel(row, text=f"{individual_allow_pct:.0f}%", width=widths[8]).pack(side="left")
            ctk.CTkLabel(row, text=f"{ts:.2f}s", width=widths[9], font=ctk.CTkFont(weight="bold"), text_color="#2ecc71").pack(side="left")

        # Resumen Final
        footer = ctk.CTkFrame(self.table_container, fg_color="#2c3e50", height=50, corner_radius=10)
        footer.pack(fill="x", pady=20, padx=50)
        
        ctk.CTkLabel(footer, text="TIEMPO ESTÁNDAR TOTAL DEL PROCESO (Σ TS):", 
                     font=ctk.CTkFont(size=14, weight="bold"), text_color="white").pack(side="left", padx=20)
        
        ctk.CTkLabel(footer, text=f"{total_ts_sum:.2f} segundos", 
                     font=ctk.CTkFont(size=18, weight="bold"), text_color="#2ecc71").pack(side="right", padx=20)
        
        # Nota técnica
        note = ctk.CTkLabel(self.table_container, text="* Nota: El Factor R/X y el tamaño de muestra (N) se calculan bajo criterios de la metodología Maytag.",
                           font=ctk.CTkFont(size=10, slant="italic"), text_color="gray")
        note.pack(pady=10)
