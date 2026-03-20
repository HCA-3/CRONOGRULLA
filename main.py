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
from views.view_info import InfoView
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

        self.logo_label = ctk.CTkLabel(self.sidebar, text="🏗️ CronoGrulla", font=ctk.CTkFont(size=24, weight="bold", family="Helvetica"))
        self.logo_label.pack(pady=(30, 20), padx=20)

        # Frame con desplazamiento para botones para evitar encimamiento
        self.scroll_sidebar = ctk.CTkScrollableFrame(self.sidebar, fg_color="transparent", corner_radius=0)
        self.scroll_sidebar.pack(fill="both", expand=True, padx=5)

        # --- SECCIÓN: MÓDULOS DE TRABAJO ---
        ctk.CTkLabel(self.scroll_sidebar, text="🔹 MÓDULOS DE TRABAJO", 
                    font=ctk.CTkFont(size=11, weight="bold"), text_color="#3498db").pack(pady=(10, 5), padx=20, anchor="w")

        nav_buttons = [
            ("📊 Dashboard", self.show_dashboard),
            ("✨ Modelos Origami", self.show_models_panel),
            ("⏱️ Cronometrar", self.show_timer),
            ("📋 Datos y Tabla", self.show_tables),
            ("👥 Equipo y Tareas", self.show_operators_setup),
            ("📈 Estadísticas", self.show_stats),
            ("ℹ️ Info. Proyecto", self.show_info)
        ]

        self.nav_btns = []
        for text, cmd in nav_buttons:
            btn = ctk.CTkButton(self.scroll_sidebar, text=text, anchor="w", fg_color="transparent", 
                                text_color=("white", "#c9d1d9"), font=ctk.CTkFont(size=14),
                                hover_color=("#34495e", "#2c3e50"), command=cmd)
            btn.pack(padx=10, pady=3, fill="x")
            self.nav_btns.append(btn)

        # --- SECCIÓN: EXPORTACIÓN Y REPORTES ---
        ctk.CTkLabel(self.scroll_sidebar, text="📄 REPORTES Y ENTREGABLES", 
                    font=ctk.CTkFont(size=11, weight="bold"), text_color="#27ae60").pack(pady=(20, 5), padx=20, anchor="w")

        self.btn_source = ctk.CTkButton(self.scroll_sidebar, text="💾 Exportar Código Fuente", 
                                       fg_color="transparent", text_color=("white", "#c9d1d9"),
                                       font=ctk.CTkFont(size=14), anchor="w",
                                       hover_color=("#34495e", "#2c3e50"),
                                       command=self.pdf_manager.generate_source_code_pdf)
        self.btn_source.pack(padx=10, pady=3, fill="x")

        self.btn_summary = ctk.CTkButton(self.scroll_sidebar, text="📜 Exportar Resumen Software", 
                                       fg_color="transparent", text_color=("white", "#c9d1d9"),
                                       font=ctk.CTkFont(size=14), anchor="w",
                                       hover_color=("#34495e", "#2c3e50"),
                                       command=self.pdf_manager.generate_summary_pdf)
        self.btn_summary.pack(padx=10, pady=3, fill="x")

        self.btn_manual = ctk.CTkButton(self.scroll_sidebar, text="📘 Exportar Manual Usuario", 
                                       fg_color=("#3498db", "#2980b9"), hover_color=("#2980b9", "#3498db"),
                                       font=ctk.CTkFont(size=14, weight="bold"), 
                                       command=self.pdf_manager.generate_instructions_pdf)
        self.btn_manual.pack(padx=10, pady=(15, 5), fill="x")

        self.btn_report = ctk.CTkButton(self.scroll_sidebar, text="📄 Exportar Informe PDF", 
                                       fg_color=("#27ae60", "#219653"), hover_color=("#2ecc71", "#27ae60"),
                                       font=ctk.CTkFont(size=14, weight="bold"), 
                                       command=self.pdf_manager.generate_pdf)
        self.btn_report.pack(padx=10, pady=(5, 20), fill="x")

        # --- INFORMACIÓN DE GUARDADO ---
        self.footer_sidebar = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        self.footer_sidebar.pack(side="bottom", fill="x", pady=15)
        
        info_label = ctk.CTkLabel(self.footer_sidebar, 
                                 text="📂 Los archivos se guardan en la\nruta seleccionada por el usuario.",
                                 font=ctk.CTkFont(size=11, slant="italic"), text_color="gray")
        info_label.pack()

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

    def show_info(self):
        self.clear_main_frame()
        self.current_view = InfoView(self.main_frame, self)
        self.current_view.pack(fill="both", expand=True)

    def open_pdf_guide(self, model_name):
        self.current_view = ModelsView(self.main_frame, self)
        self.current_view.open_pdf_guide(model_name)

if __name__ == "__main__":
    app = CraneFlowApp()
    app.mainloop()
