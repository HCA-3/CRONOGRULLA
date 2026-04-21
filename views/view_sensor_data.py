import customtkinter as ctk
import tkinter as tk
from tkinter import ttk
import numpy as np

class SensorDataView(ctk.CTkFrame):
    def __init__(self, master, app):
        super().__init__(master, fg_color="transparent")
        self.app = app
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        self.build_ui()

    def build_ui(self):
        header_f = ctk.CTkFrame(self, fg_color="transparent")
        header_f.pack(fill="x", padx=40, pady=20)
        
        ctk.CTkLabel(header_f, text="📡 Datos del Sensor de Movimiento (Ergonomía)", 
                      font=ctk.CTkFont(size=26, weight="bold")).pack(side="left")
        
        ctk.CTkButton(header_f, text="🔄 Actualizar Análisis", fg_color="#3498db", 
                      command=self.update_analysis).pack(side="right", padx=5)

        # Contenedor de la tabla
        self.table_container = ctk.CTkFrame(self, corner_radius=15, fg_color=("#ffffff", "#1e293b"))
        self.table_container.pack(fill="both", expand=True, padx=40, pady=(0, 20))
        
        # Estilo de la tabla
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Ergo.Treeview", 
                        background="#1e293b", 
                        foreground="white", 
                        fieldbackground="#1e293b", 
                        rowheight=35)
        style.configure("Ergo.Treeview.Heading", 
                        background="#0f172a", 
                        foreground="white", 
                        font=('Arial', 11, 'bold'))
        
        cols = ("Operador", "Tarea", "Ángulo Codo D.", "Ángulo Codo I.", "Evaluación Postural")
        self.tree = ttk.Treeview(self.table_container, columns=cols, show="headings", style="Ergo.Treeview")
        
        for col in cols:
            self.tree.heading(col, text=col)
            self.tree.column(col, anchor="center", width=150)

        self.tree.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Panel Informativo
        info_panel = ctk.CTkFrame(self, corner_radius=10, fg_color=("#d1ecf1", "#1a242f"))
        info_panel.pack(fill="x", padx=40, pady=10)
        
        info_text = (
            "💡 Guía de Evaluación Postural:\n"
            "• Óptimo (90°-120°): Rango de movimiento natural y descansado.\n"
            "• Precaución (<70° o >140°): Posible fatiga muscular por ángulos extremos.\n"
            "• Riesgo: Mantener ángulos agudos por periodos prolongados sin descanso."
        )
        ctk.CTkLabel(info_panel, text=info_text, font=ctk.CTkFont(size=12), justify="left").pack(pady=10, padx=20)

        self.update_analysis()

    def update_analysis(self):
        # Limpiar tabla
        for item in self.tree.get_children():
            self.tree.delete(item)

        measurements = self.app.data.get("measurements", [])
        if not measurements:
            return

        for m in measurements:
            model = m.get("model", "N/A")
            for split in m.get("splits", []):
                ergo = split.get("ergo_summary", {})
                if not ergo: continue
                
                op = split.get("operator", "N/A")
                task = split.get("activity", "N/A")
                angle_r = ergo.get("avg_elbow_r", 0)
                angle_l = ergo.get("avg_elbow_l", 0)
                
                # Evaluación simplificada
                avg_angle = (angle_r + angle_l) / 2 if angle_r and angle_l else (angle_r or angle_l)
                if 80 <= avg_angle <= 130:
                    status = "✅ Óptimo"
                elif 60 <= avg_angle <= 150:
                    status = "⚠️ Precaución"
                else:
                    status = "🚨 Riesgo"

                self.tree.insert("", "end", values=(
                    op,
                    task[:30],
                    f"{int(angle_r)}°" if angle_r else "-",
                    f"{int(angle_l)}°" if angle_l else "-",
                    status
                ))
