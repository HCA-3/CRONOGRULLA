import tkinter as tk
import customtkinter as ctk
import json
import os
import subprocess
import sys

# Model Imports
from views.view_dashboard import DashboardView
from views.view_models import ModelsView
from views.view_operators import OperatorsView
from views.view_timer import TimerView
from views.view_tables import TablesView
from views.view_stats import StatsView
from utils.pdf_report import PDFManager

# Configuración de apariencia Premium
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class CraneFlowApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("CronoGrulla | Ingeniería de Métodos")
        self.geometry("1200x850")
        self.minsize(1000, 700)
        
        # Archivo de datos
        self.data_file = "craneflow_data.json"
        self.pdf_folder = "guias_pdf"
        if not os.path.exists(self.pdf_folder):
            os.makedirs(self.pdf_folder)
            
        self.load_data()
        
        # Parámetros Base
        self.DEFAULT_ACTIVITIES = [
            "Paso 1: Diagonal y mitad",
            "Paso 2: Pliegues cruzados",
            "Paso 3: Juntar esquinas (Base)",
            "Paso 4: Marcar solapas",
            "Paso 5: Marcar punta superior",
            "Paso 6: Abrir solapa superior",
            "Paso 7: Repetir cara posterior",
            "Paso 8: Solapas al centro",
            "Paso 9: Repetir lado opuesto",
            "Paso 10: Marcar patas inf.",
            "Paso 11: Pliegue invertido",
            "Paso 12: Cabeza y alas"
        ]
        self.DEFAULT_DESCRIPTIONS = [
            "Coloca el papel cuadrado con el color hacia arriba, dobla la esquina superior hacia la inferior para marcar la diagonal, desdobla y luego dobla el papel por la mitad lateralmente.",
            "Da la vuelta al papel para que el lado blanco quede hacia arriba, dobla por la mitad en una dirección, marca el pliegue, desdobla y repite en la otra dirección.",
            "Usando los pliegues realizados, junta las 3 esquinas superiores hacia la esquina inferior y alisa el modelo.",
            "Dobla las solapas triangulares de los lados hacia el centro y luego desdóblalas para dejar la marca.",
            "Dobla la punta superior del modelo hacia abajo, marca con fuerza la plegadura y vuelve a desdoblar.",
            "Abre la solapa superior llevándola hacia arriba mientras presionas los laterales hacia el interior hasta que quede liso.",
            "Voltea el modelo y repite exactamente los pasos 4, 5 y 6 en la cara posterior.",
            "Dobla las solapas exteriores (las capas superiores) hacia la línea central.",
            "Repite el mismo doblez de las solapas en el lado opuesto del modelo.",
            "Dobla ambas 'patas' inferiores hacia arriba para marcar la posición, presiona bien y luego desdóblalas.",
            "Realiza un pliegue invertido hacia adentro (por el revés) para situar las 'patas' en la posición de la marca que hiciste antes.",
            "Realiza otro pliegue invertido en el extremo de una de las puntas para formar la cabeza y finalmente dobla las alas hacia abajo."
        ]

        self.models = self.data.get("models", {
            "Grulla Clásica": {
                "activities": self.DEFAULT_ACTIVITIES,
                "descriptions": self.DEFAULT_DESCRIPTIONS
            }
        })
        
        self.current_model_name = self.data.get("current_model", "Grulla Clásica")
        self.update_current_model_vars()
        
        self.operator_data = self.data.get("operators", [])
        self.line_config = self.data.get("line_config", {})
        
        self.pdf_manager = PDFManager(self)
        self.current_view = None
        
        self.setup_ui()
        
        # Lógica de inicio
        if not self.operator_data or not self.line_config:
            self.show_operators_setup()
        else:
            self.show_dashboard()

    def load_data(self):
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    self.data = json.load(f)
            except Exception:
                self.data = {"operators": [], "line_config": {}, "measurements": []}
        else:
            self.data = {"operators": [], "line_config": {}, "measurements": []}

    def update_current_model_vars(self):
        model_data = self.models.get(self.current_model_name)
        self.ACTIVITIES = model_data["activities"]
        self.FULL_DESCRIPTIONS = model_data["descriptions"]
        self.TARGET_TOTAL_CYCLES = len(self.ACTIVITIES)

    def change_model_from_menu(self, new_model):
        self.current_model_name = new_model
        self.update_current_model_vars()
        self.save_data()
        self.show_timer()

    def save_data(self):
        self.data["operators"] = self.operator_data
        self.data["line_config"] = self.line_config
        self.data["models"] = self.models
        self.data["current_model"] = self.current_model_name
        with open(self.data_file, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, indent=4, ensure_ascii=False)

    def setup_ui(self):
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Barra lateral moderna
        self.sidebar = ctk.CTkFrame(self, width=220, corner_radius=0, fg_color=("#2c3e50", "#1a242f"))
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_rowconfigure(7, weight=1)

        self.logo_label = ctk.CTkLabel(self.sidebar, text="🏗️ CronoGrulla", font=ctk.CTkFont(size=24, weight="bold", family="Helvetica"))
        self.logo_label.grid(row=0, column=0, padx=20, pady=(30, 20))

        # Botones de navegación
        nav_buttons = [
            ("📊 Dashboard", self.show_dashboard),
            ("✨ Modelos Origami", self.show_models_panel),
            ("⏱️ Cronometrar", self.show_timer),
            ("📋 Datos y Tabla", self.show_tables),
            ("👥 Equipo y Tareas", self.show_operators_setup),
            ("📈 Estadísticas", self.show_stats)
        ]

        self.nav_btns = []
        for i, (text, cmd) in enumerate(nav_buttons):
            btn = ctk.CTkButton(self.sidebar, text=text, anchor="w", fg_color="transparent", 
                                text_color=("white", "#c9d1d9"), font=ctk.CTkFont(size=15),
                                hover_color=("#34495e", "#2c3e50"), command=cmd)
            btn.grid(row=i+1, column=0, padx=20, pady=10, sticky="ew")
            self.nav_btns.append(btn)

        self.btn_pdf_instructions = ctk.CTkButton(self.sidebar, text="📘 Exportar Manual Instrucciones", 
                                     fg_color=("#3498db", "#2980b9"), hover_color=("#2980b9", "#3498db"),
                                     font=ctk.CTkFont(size=14, weight="bold"), command=self.pdf_manager.generate_instructions_pdf)
        self.btn_pdf_instructions.grid(row=8, column=0, padx=20, pady=(20, 0), sticky="ew")

        self.btn_pdf = ctk.CTkButton(self.sidebar, text="📄 Exportar Informe PDF", 
                                     fg_color=("#27ae60", "#219653"), hover_color=("#2ecc71", "#27ae60"),
                                     font=ctk.CTkFont(size=14, weight="bold"), command=self.pdf_manager.generate_pdf)
        self.btn_pdf.grid(row=9, column=0, padx=20, pady=20, sticky="ew")

        # Contenedor Principal
        self.main_frame = ctk.CTkFrame(self, corner_radius=15, fg_color=("#ecf0f1", "#0f172a"))
        self.main_frame.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)

    def clear_main_frame(self):
        for widget in self.main_frame.winfo_children():
            widget.destroy()

    def show_dashboard(self):
        self.clear_main_frame()
        self.current_view = DashboardView(self.main_frame, self)
        self.current_view.pack(fill="both", expand=True)

    def show_models_panel(self):
        self.clear_main_frame()
        self.current_view = ModelsView(self.main_frame, self)
        self.current_view.pack(fill="both", expand=True)

    def show_operators_setup(self):
        self.clear_main_frame()
        self.current_view = OperatorsView(self.main_frame, self)
        self.current_view.pack(fill="both", expand=True)

    def show_timer(self):
        self.clear_main_frame()
        self.current_view = TimerView(self.main_frame, self)
        self.current_view.pack(fill="both", expand=True)

    def show_tables(self):
        self.clear_main_frame()
        self.current_view = TablesView(self.main_frame, self)
        self.current_view.pack(fill="both", expand=True)

    def show_stats(self):
        self.clear_main_frame()
        self.current_view = StatsView(self.main_frame, self)
        self.current_view.pack(fill="both", expand=True)

    def open_pdf_guide(self, model_name):
        self.current_view = ModelsView(self.main_frame, self)
        self.current_view.open_pdf_guide(model_name)

if __name__ == "__main__":
    app = CraneFlowApp()
    app.mainloop()
