import tkinter as tk
import customtkinter as ctk
from tkinter import messagebox, ttk
import json
import time
import os
from datetime import datetime
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np
from fpdf import FPDF
import tempfile
import shutil
import subprocess


# Configuración de apariencia Premium
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class PremiumReportPDF(FPDF):
    def header(self):
        self.set_fill_color(30, 41, 59) # Slate 800
        self.rect(0, 0, 210, 30, 'F')
        self.set_font('Arial', 'B', 20)
        self.set_text_color(255, 255, 255)
        self.cell(0, 15, 'CRONOGRULLA - INFORME METODOLÓGICO', 0, 1, 'C')
        self.set_font('Arial', 'I', 12)
        self.set_text_color(200, 200, 200)
        self.cell(0, 5, 'Ingeniería de Métodos - Balanceo de Línea (Grullas)', 0, 0, 'C')
        self.ln(20)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.set_text_color(128)
        self.cell(0, 10, f'Página {self.page_no()} | Generado automatizadamente por CronoGrulla', 0, 0, 'C')

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
        
        # Estado del Cronómetro
        self.start_time = None
        self.last_split_time = 0
        self.current_cycle_splits = []
        self.running = False
        self.current_activity_index = 0
        
        self.operator_data = self.data.get("operators", [])
        self.line_config = self.data.get("line_config", {})
        
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
        # Asegurarnos de que las mediciones se guarden bajo el modelo actual si queremos separarlas
        # Pero según entiendo, quieres mantener la estructura actual.
        # Si quieres separar tiempos por modelo, deberíamos estructurar data["measurements"] como un dict.
        with open(self.data_file, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, indent=4, ensure_ascii=False)

    def show_models_panel(self):
        self.clear_main_frame()
        self.main_frame.grid_columnconfigure(0, weight=1)
        
        header = ctk.CTkLabel(self.main_frame, text="Gestión de Modelos de Origami", 
                               font=ctk.CTkFont(size=28, weight="bold"))
        header.pack(pady=(30, 10), anchor="w", padx=40)

        # Panel para nuevo modelo
        new_model_frame = ctk.CTkFrame(self.main_frame, corner_radius=10)
        new_model_frame.pack(fill="x", padx=40, pady=10)
        
        ctk.CTkLabel(new_model_frame, text="Crear Nuevo Modelo:", font=ctk.CTkFont(weight="bold")).pack(side="left", padx=20, pady=20)
        
        self.new_model_name_entry = ctk.CTkEntry(new_model_frame, placeholder_text="Nombre del Modelo (ej: Grulla Pro)", width=300)
        self.new_model_name_entry.pack(side="left", padx=10)
        
        ctk.CTkButton(new_model_frame, text="Añadir Pasos", command=self.open_steps_editor).pack(side="left", padx=10)

        # Lista de modelos existentes
        list_label = ctk.CTkLabel(self.main_frame, text="Modelos Registrados:", font=ctk.CTkFont(size=18, weight="bold"))
        list_label.pack(pady=(20, 10), anchor="w", padx=40)

        self.models_list_frame = ctk.CTkScrollableFrame(self.main_frame, height=400)
        self.models_list_frame.pack(fill="both", expand=True, padx=40, pady=10)
        
        self.render_models_list()

    def render_models_list(self):
        for widget in self.models_list_frame.winfo_children():
            widget.destroy()
            
        for model_name in self.models.keys():
            row = ctk.CTkFrame(self.models_list_frame, fg_color=("#ffffff", "#1e293b"), corner_radius=8)
            row.pack(fill="x", pady=5, padx=5)
            
            ctk.CTkLabel(row, text=model_name, font=ctk.CTkFont(weight="bold")).pack(side="left", padx=20, pady=15)
            
            btn_frame = ctk.CTkFrame(row, fg_color="transparent")
            btn_frame.pack(side="right", padx=10)
            
            if model_name == self.current_model_name:
                badge = ctk.CTkLabel(btn_frame, text="ACTIVO", fg_color="#27ae60", text_color="white", corner_radius=10, padx=10)
                badge.pack(side="left", padx=5)
            else:
                ctk.CTkButton(btn_frame, text="Activar", width=80, command=lambda m=model_name: self.activate_model(m)).pack(side="left", padx=5)
            
            ctk.CTkButton(btn_frame, text="Eliminar", width=80, fg_color="#e74c3c", hover_color="#c0392b", 
                          command=lambda m=model_name: self.delete_model(m)).pack(side="left", padx=5)
            
            ctk.CTkButton(btn_frame, text="Editar Pasos", width=100, fg_color="#f39c12", hover_color="#e67e22",
                          command=lambda m=model_name: self.open_edit_steps_editor(m)).pack(side="left", padx=10)

            # Botones de PDF
            pdf_path = self.models[model_name].get("pdf_guide")
            if pdf_path and os.path.exists(pdf_path):
                ctk.CTkButton(btn_frame, text="📄 Ver PDF", width=80, fg_color="#34495e", 
                              command=lambda m=model_name: self.open_pdf_guide(m)).pack(side="left", padx=5)
            
            ctk.CTkButton(btn_frame, text="🔼 Subir PDF", width=80, fg_color="#95a5a6", 
                          command=lambda m=model_name: self.upload_pdf_guide(m)).pack(side="left", padx=5)

    def activate_model(self, model_name):
        self.current_model_name = model_name
        self.update_current_model_vars()
        self.save_data()
        self.render_models_list()
        messagebox.showinfo("Modelo Activo", f"Se ha activado el modelo: {model_name}")

    def delete_model(self, model_name):
        if model_name == "Grulla Clásica":
            messagebox.showwarning("Acción no permitida", "No puedes eliminar el modelo base.")
            return
        if messagebox.askyesno("Confirmar", f"¿Eliminar el modelo {model_name}?"):
            if self.current_model_name == model_name:
                self.activate_model("Grulla Clásica")
            del self.models[model_name]
            self.save_data()
            self.render_models_list()

    def open_steps_editor(self):
        name = self.new_model_name_entry.get().strip()
        if not name:
            messagebox.showwarning("Falta nombre", "Asigna un nombre al modelo primero.")
            return
        if name in self.models:
            messagebox.showwarning("Nombre duplicado", "Ya existe un modelo con ese nombre.")
            return
            
        self.steps_window = ctk.CTkToplevel(self)
        self.steps_window.title(f"Configurar pasos: {name}")
        self.steps_window.geometry("850x700")
        self.steps_window.grab_set()
        
        ctk.CTkLabel(self.steps_window, text=f"Definiendo pasos para: {name}", font=ctk.CTkFont(size=18, weight="bold")).pack(pady=10)
        ctk.CTkLabel(self.steps_window, text="Solo se guardarán los pasos que tengan nombre o descripción.", font=ctk.CTkFont(size=12, slant="italic")).pack(pady=5)
        
        self.scroll_steps = ctk.CTkScrollableFrame(self.steps_window)
        self.scroll_steps.pack(fill="both", expand=True, padx=20, pady=10)
        
        self.step_entries = []
        # Iniciar con 1 fila
        self.add_step_row()

        btn_frame = ctk.CTkFrame(self.steps_window, fg_color="transparent")
        btn_frame.pack(pady=10)

        ctk.CTkButton(btn_frame, text="+ Añadir un Paso", fg_color="#27ae60", hover_color="#2ecc71",
                      command=self.add_step_row).pack(side="left", padx=10)

        ctk.CTkButton(btn_frame, text="Guardar Modelo", font=ctk.CTkFont(weight="bold"),
                      command=lambda n=name: self.save_new_model(n)).pack(side="left", padx=10)

    def add_step_row(self, initial_name="", initial_desc=""):
        idx = len(self.step_entries)
        f = ctk.CTkFrame(self.scroll_steps, fg_color="transparent")
        f.pack(fill="x", pady=5)
        
        ctk.CTkLabel(f, text=f"Paso {idx+1}:", width=60).pack(side="left", padx=5)
        name_ent = ctk.CTkEntry(f, placeholder_text="Nombre del paso", width=200)
        if initial_name: name_ent.insert(0, initial_name)
        name_ent.pack(side="left", padx=5)
        
        desc_ent = ctk.CTkEntry(f, placeholder_text="Instrucción detallada", width=400)
        if initial_desc: desc_ent.insert(0, initial_desc)
        desc_ent.pack(side="left", padx=5)
        
        self.step_entries.append((name_ent, desc_ent))

    def save_new_model(self, name):
        acts = []
        descs = []
        for ne, de in self.step_entries:
            n = ne.get().strip()
            d = de.get().strip()
            # Solo guardamos si al menos uno tiene contenido
            if n or d:
                acts.append(n or f"Paso {len(acts)+1}")
                descs.append(d or "Sin descripción")
        
        if not acts:
            messagebox.showwarning("Sin pasos", "Debes agregar al menos un paso con información.")
            return
            
        self.models[name] = {
            "activities": acts,
            "descriptions": descs
        }
        self.save_data()
        self.steps_window.destroy()
        if hasattr(self, 'new_model_name_entry'):
            self.new_model_name_entry.delete(0, 'end')
        self.render_models_list()
        messagebox.showinfo("Guardado", f"Modelo {name} creado exitosamente con {len(acts)} pasos.")

    def open_edit_steps_editor(self, model_name):
        model_data = self.models.get(model_name)
        if not model_data: return
        
        self.steps_window = ctk.CTkToplevel(self)
        self.steps_window.title(f"Editar Pasos: {model_name}")
        self.steps_window.geometry("850x700")
        self.steps_window.grab_set()
        
        ctk.CTkLabel(self.steps_window, text=f"Editando pasos para: {model_name}", font=ctk.CTkFont(size=18, weight="bold")).pack(pady=10)
        
        self.scroll_steps = ctk.CTkScrollableFrame(self.steps_window)
        self.scroll_steps.pack(fill="both", expand=True, padx=20, pady=10)
        
        self.step_entries = []
        acts = model_data["activities"]
        descs = model_data["descriptions"]
        
        for i in range(len(acts)):
            self.add_step_row(acts[i], descs[i])

        btn_frame = ctk.CTkFrame(self.steps_window, fg_color="transparent")
        btn_frame.pack(pady=10)

        ctk.CTkButton(btn_frame, text="+ Añadir un Paso", fg_color="#27ae60", hover_color="#2ecc71",
                      command=self.add_step_row).pack(side="left", padx=10)

        ctk.CTkButton(btn_frame, text="Actualizar Modelo", font=ctk.CTkFont(weight="bold"),
                      command=lambda n=model_name: self.save_edited_model(n)).pack(side="left", padx=10)

    def save_edited_model(self, model_name):
        acts = []
        descs = []
        for ne, de in self.step_entries:
            n = ne.get().strip()
            d = de.get().strip()
            # Filtrar filas vacías
            if n or d:
                acts.append(n or f"Paso {len(acts)+1}")
                descs.append(d or "Sin descripción")

        if not acts:
            messagebox.showwarning("Sin pasos", "No puedes dejar el modelo sin pasos.")
            return

        self.models[model_name] = {
            "activities": acts,
            "descriptions": descs
        }
        if self.current_model_name == model_name:
            self.update_current_model_vars()
        self.save_data()
        self.steps_window.destroy()
        self.render_models_list()
        messagebox.showinfo("Actualizado", f"Modelo {model_name} actualizado con {len(acts)} pasos.")

    def save_new_model(self, name):
        acts = []
        descs = []
        for i, (ne, de) in enumerate(self.step_entries):
            step_name = ne.get().strip() or f"Paso {i+1}"
            step_desc = de.get().strip() or "Sin descripción"
            acts.append(step_name)
            descs.append(step_desc)
            
        self.models[name] = {
            "activities": acts,
            "descriptions": descs
        }
        self.save_data()
        self.steps_window.destroy()
        self.new_model_name_entry.delete(0, 'end')
        self.render_models_list()
        messagebox.showinfo("Guardado", f"Modelo {name} creado exitosamente.")

    def upload_pdf_guide(self, model_name):
        from tkinter import filedialog
        file_path = filedialog.askopenfilename(
            title="Seleccionar Guía PDF para " + model_name,
            filetypes=[("Archivos PDF", "*.pdf")]
        )
        if not file_path:
            return
        
        try:
            # Crear nombre seguro para el archivo
            safe_name = "".join([c if c.isalnum() else "_" for c in model_name]) + ".pdf"
            dest_path = os.path.join(self.pdf_folder, safe_name)
            
            shutil.copy2(file_path, dest_path)
            self.models[model_name]["pdf_guide"] = dest_path
            self.save_data()
            self.render_models_list()
            messagebox.showinfo("Éxito", f"Guía PDF cargada para {model_name}")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo copiar el archivo: {e}")

    def open_pdf_guide(self, model_name):
        pdf_path = self.models.get(model_name, {}).get("pdf_guide")
        if pdf_path and os.path.exists(pdf_path):
            try:
                if os.name == 'nt': # Windows
                    os.startfile(pdf_path)
                else: # macOS / Linux
                    opener = "open" if sys.platform == "darwin" else "xdg-open"
                    subprocess.call([opener, pdf_path])
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo abrir el PDF: {e}")
        else:
            messagebox.showwarning("Sin Archivo", "No hay una guía PDF cargada para este modelo.")

    def setup_ui(self):
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Barra lateral moderna
        self.sidebar = ctk.CTkFrame(self, width=220, corner_radius=0, fg_color=("#2c3e50", "#1a242f"))
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_rowconfigure(7, weight=1)

        self.logo_label = ctk.CTkLabel(self.sidebar, text="🏗️ CronoGrulla", font=ctk.CTkFont(size=24, weight="bold", family="Helvetica"))
        self.logo_label.grid(row=0, column=0, padx=20, pady=(30, 20))

        # Botones de navegación estilizados
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
                                     font=ctk.CTkFont(size=14, weight="bold"), command=self.generate_instructions_pdf)
        self.btn_pdf_instructions.grid(row=8, column=0, padx=20, pady=(20, 0), sticky="ew")

        self.btn_pdf = ctk.CTkButton(self.sidebar, text="📄 Exportar Informe PDF", 
                                     fg_color=("#27ae60", "#219653"), hover_color=("#2ecc71", "#27ae60"),
                                     font=ctk.CTkFont(size=14, weight="bold"), command=self.generate_pdf)
        self.btn_pdf.grid(row=9, column=0, padx=20, pady=20, sticky="ew")

        # Contenedor Principal
        self.main_frame = ctk.CTkFrame(self, corner_radius=15, fg_color=("#ecf0f1", "#0f172a"))
        self.main_frame.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)

    def clear_main_frame(self):
        for widget in self.main_frame.winfo_children():
            widget.destroy()

    def show_dashboard(self):
        self.clear_main_frame()
        self.main_frame.grid_columnconfigure(0, weight=1)
        
        # Header
        header = ctk.CTkLabel(self.main_frame, text="Panel de Control Principal", 
                              font=ctk.CTkFont(size=28, weight="bold"))
        header.pack(pady=(30, 20), anchor="w", padx=40)

        # Cards Frame
        cards_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        cards_frame.pack(fill="x", padx=40, pady=10)
        
        for i in range(3): cards_frame.grid_columnconfigure(i, weight=1)

        measurements = self.data.get("measurements", [])
        total_m = len(measurements)
        avg_time = sum(m.get("total_time", 0) for m in measurements) / total_m if total_m > 0 else 0
        total_ops = len(self.operator_data)

        self.create_info_card(cards_frame, "Ciclos Completados", f"{total_m} Registrados", "📊", 0, ("#3498db", "#2980b9"))
        self.create_info_card(cards_frame, "Tiempo Promedio", f"{avg_time:.2f} s", "⏱️", 1, ("#e67e22", "#d35400"))
        self.create_info_card(cards_frame, "Operarios Activos", f"{total_ops}", "👥", 2, ("#9b59b6", "#8e44ad"))

        # Banner informativo
        banner = ctk.CTkFrame(self.main_frame, corner_radius=10, fg_color=("#d1ecf1", "#1e3a5f"))
        banner.pack(fill="x", padx=40, pady=30)
        
        b_title = ctk.CTkLabel(banner, text="Resumen del Sistema de Balanceo", font=ctk.CTkFont(size=18, weight="bold"), text_color=("#0c5460", "#63b3ed"))
        b_title.pack(pady=(15, 5), padx=20, anchor="w")
        
        b_text = ("• Las tareas se han dividido automáticamente en base a la cantidad de operarios asignados.\n"
                  "• El cronómetro guiará paso a paso indicando el operador responsable de la tarea actual.\n"
                  "• Puedes registrar observaciones de calidad finalizado cada paso si ocurre un contratiempo.")
        ctk.CTkLabel(banner, text=b_text, font=ctk.CTkFont(size=14), justify="left", text_color=("#0c5460", "#e2e8f0")).pack(pady=(0, 15), padx=20, anchor="w")

    def create_info_card(self, parent, title, value, icon, col, colors):
        card = ctk.CTkFrame(parent, corner_radius=15, fg_color=colors[1])
        card.grid(row=0, column=col, padx=10, sticky="nsew", ipady=20)
        
        ctk.CTkLabel(card, text=icon, font=ctk.CTkFont(size=40)).pack(pady=(15, 5))
        ctk.CTkLabel(card, text=value, font=ctk.CTkFont(size=32, weight="bold"), text_color="white").pack()
        ctk.CTkLabel(card, text=title, font=ctk.CTkFont(size=14), text_color="#ecf0f1").pack(pady=(5, 10))

    def show_operators_setup(self):
        self.clear_main_frame()
        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_rowconfigure(1, weight=1)
        
        ctk.CTkLabel(self.main_frame, text="Configuración del Equipo de Trabajo", 
                     font=ctk.CTkFont(size=26, weight="bold")).pack(pady=(30, 10), padx=40, anchor="w")
        
        ctk.CTkLabel(self.main_frame, text="Define cuántas personas trabajarán en la línea y asigna sus nombres para dividir automáticamente las 12 tareas.",
                     font=ctk.CTkFont(size=14), text_color="gray").pack(padx=40, anchor="w", pady=(0, 20))

        setup_frame = ctk.CTkFrame(self.main_frame, fg_color=("#ffffff", "#1e293b"), corner_radius=10)
        setup_frame.pack(fill="both", expand=True, padx=40, pady=10)
        setup_frame.grid_columnconfigure((0, 1), weight=1)
        
        # Izquierda: Selección
        left_panel = ctk.CTkFrame(setup_frame, fg_color="transparent")
        left_panel.grid(row=0, column=0, padx=20, pady=20, sticky="n")
        
        ctk.CTkLabel(left_panel, text="1. Cantidad de Operarios:", font=ctk.CTkFont(size=16, weight="bold")).pack(anchor="w", pady=5)
        
        self.num_ops_var = tk.StringVar(value=str(len(self.operator_data)) if self.operator_data else "1")
        op_menu = ctk.CTkOptionMenu(left_panel, values=[str(i) for i in range(1, 13)], 
                                    variable=self.num_ops_var, command=self.generate_operator_entries,
                                    width=200, height=35)
        op_menu.pack(anchor="w", pady=(0, 20))

        ctk.CTkLabel(left_panel, text="2. Nombres de Operarios:", font=ctk.CTkFont(size=16, weight="bold")).pack(anchor="w", pady=5)
        self.entries_frame = ctk.CTkScrollableFrame(left_panel, width=300, height=250, fg_color="transparent")
        self.entries_frame.pack(anchor="w", fill="both", expand=True)
        
        self.op_entries = []
        self.generate_operator_entries(self.num_ops_var.get())

        ctk.CTkButton(left_panel, text="Generar / Actualizar Distribución", 
                      font=ctk.CTkFont(weight="bold"), fg_color="#3498db", hover_color="#2980b9",
                      command=self.update_distribution).pack(pady=20, fill="x")

        # Derecha: Visualización de Tareas
        right_panel = ctk.CTkFrame(setup_frame, fg_color=("#f8f9fa", "#0f172a"), corner_radius=10)
        right_panel.grid(row=0, column=1, padx=20, pady=20, sticky="nsew")
        right_panel.grid_rowconfigure(1, weight=1)
        right_panel.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(right_panel, text="Distribución de Tareas Asignada", font=ctk.CTkFont(size=18, weight="bold")).grid(row=0, column=0, pady=15)
        
        self.tasks_display = ctk.CTkScrollableFrame(right_panel, fg_color="transparent")
        self.tasks_display.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
        
        self.render_distribution_preview()

    def generate_operator_entries(self, num_str):
        for widget in self.entries_frame.winfo_children():
            widget.destroy()
        self.op_entries.clear()
        
        num = int(num_str)
        for i in range(num):
            val = self.operator_data[i] if i < len(self.operator_data) else f"Operador {i+1}"
            entry = ctk.CTkEntry(self.entries_frame, placeholder_text=f"Nombre Op. {i+1}", width=250)
            entry.insert(0, val)
            entry.pack(pady=5, anchor="w")
            self.op_entries.append(entry)

    def update_distribution(self):
        names = [e.get().strip() or f"Operador {i+1}" for i, e in enumerate(self.op_entries)]
        self.operator_data = names
        
        num_ops = len(names)
        base = 12 // num_ops
        rem = 12 % num_ops
        
        new_config = {}
        curr_task = 0
        for i in range(num_ops):
            tasks_to_assign = base + (1 if i < rem else 0)
            for _ in range(tasks_to_assign):
                new_config[str(curr_task)] = names[i]
                curr_task += 1
                
        self.line_config = new_config
        self.save_data()
        self.render_distribution_preview()
        messagebox.showinfo("Actualizado", "Equipo y distribución guardados correctamente. Las tareas se dividieron de forma equitativa.")

    def render_distribution_preview(self):
        for widget in self.tasks_display.winfo_children():
            widget.destroy()
            
        if not self.line_config:
            ctk.CTkLabel(self.tasks_display, text="Aún no hay distribución.\nConfigura el equipo a la izquierda.", text_color="gray").pack(pady=50)
            return

        for i, act_name in enumerate(self.ACTIVITIES):
            f = ctk.CTkFrame(self.tasks_display, fg_color=("#ffffff", "#1e293b"), corner_radius=8)
            f.pack(fill="x", pady=4, padx=5)
            op_assigned = self.line_config.get(str(i), "Sin asignar")
            
            ctk.CTkLabel(f, text=f"{act_name}", font=ctk.CTkFont(weight="bold")).pack(side="left", padx=10, pady=10)
            badge = ctk.CTkLabel(f, text=op_assigned, fg_color="#3498db", text_color="white", corner_radius=10, padx=10, pady=2)
            badge.pack(side="right", padx=10, pady=10)

    def show_timer(self):
        self.clear_main_frame()
        if not self.line_config:
            messagebox.showwarning("Falta Configuración", "Por favor configura el equipo y la distribución de tareas primero.")
            self.show_operators_setup()
            return

        header = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        header.pack(fill="x", padx=40, pady=(20, 0))
        
        cycle_num = len(self.data.get("measurements", [])) + 1
        ctk.CTkLabel(header, text=f"Estudio de Tiempos - Ciclo #{cycle_num}", font=ctk.CTkFont(size=26, weight="bold")).pack(side="left")

        # Configurar contenedor principal dividido en 2 columnas (Timer | Formulario QC)
        self.content_container = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.content_container.pack(fill="both", expand=True, padx=40, pady=(10, 20))
        self.content_container.grid_columnconfigure(0, weight=1)
        self.content_container.grid_columnconfigure(1, weight=0) # Oculto por defecto
        self.content_container.grid_rowconfigure(0, weight=1)

        self.timer_column = ctk.CTkFrame(self.content_container, fg_color="transparent")
        self.timer_column.grid(row=0, column=0, sticky="nsew", padx=(0, 10))

        # Selector de Modelo en Timer
        model_selector_frame = ctk.CTkFrame(self.timer_column, fg_color="transparent")
        model_selector_frame.pack(fill="x", pady=(0, 10))
        ctk.CTkLabel(model_selector_frame, text="Seleccionar Modelo:", font=ctk.CTkFont(weight="bold")).pack(side="left", padx=10)
        
        self.timer_model_var = tk.StringVar(value=self.current_model_name)
        self.timer_model_menu = ctk.CTkOptionMenu(model_selector_frame, values=list(self.models.keys()), 
                                                variable=self.timer_model_var, command=self.change_model_from_menu)
        self.timer_model_menu.pack(side="left", padx=10)

        # Botón para ver guía PDF en Timer
        pdf_path = self.models.get(self.current_model_name, {}).get("pdf_guide")
        if pdf_path and os.path.exists(pdf_path):
            ctk.CTkButton(model_selector_frame, text="📄 Ver Guía Técnica PDF", 
                          fg_color="#3498db", hover_color="#2980b9", width=180,
                          command=lambda: self.open_pdf_guide(self.current_model_name)).pack(side="left", padx=20)

        self.qc_column = ctk.CTkFrame(self.content_container, corner_radius=15, fg_color=("#ffffff", "#1e293b"))
        # self.qc_column no se ubica aún (permanece oculta)

        # Timer Display (en columna izquierda)
        timer_frame = ctk.CTkFrame(self.timer_column, corner_radius=20, fg_color=("#ffffff", "#1e293b"))
        timer_frame.pack(pady=10, fill="x", ipady=20)
        
        self.op_target_lbl = ctk.CTkLabel(timer_frame, text="Preparado para iniciar", font=ctk.CTkFont(size=20, slant="italic"), text_color="#f39c12")
        self.op_target_lbl.pack(pady=(10, 0))
        
        self.timer_label = ctk.CTkLabel(timer_frame, text="00:00.00", font=ctk.CTkFont(size=90, weight="bold", family="Courier New"), text_color="#3498db")
        self.timer_label.pack(pady=10)

        controls = ctk.CTkFrame(timer_frame, fg_color="transparent")
        controls.pack()

        self.btn_start = ctk.CTkButton(controls, text="▶ INICIAR CICLO", font=ctk.CTkFont(size=18, weight="bold"),
                                       height=50, width=250, fg_color="#27ae60", hover_color="#2ecc71",
                                       command=self.start_timer)
        self.btn_start.pack(side="left", padx=15)

        self.btn_cancel = ctk.CTkButton(controls, text="⏹ CANCELAR", font=ctk.CTkFont(size=16),
                                        height=50, width=150, fg_color="#e74c3c", hover_color="#c0392b",
                                        command=self.reset_timer, state="disabled")
        self.btn_cancel.pack(side="left", padx=15)

        # Activity List (en columna izquierda)
        self.act_frame = ctk.CTkScrollableFrame(self.timer_column)
        self.act_frame.pack(fill="both", expand=True, pady=(0, 10))
        
        self.act_widgets = []
        for i, act_name in enumerate(self.ACTIVITIES):
            f = ctk.CTkFrame(self.act_frame, fg_color=("#ecf0f1", "#0f172a"), corner_radius=10)
            f.pack(fill="x", pady=5, padx=10)
            f.grid_columnconfigure(1, weight=1)
            
            lbl_title = ctk.CTkLabel(f, text=str(i+1), font=ctk.CTkFont(weight="bold", size=18), width=30)
            lbl_title.grid(row=0, column=0, padx=10, pady=15)
            
            op = self.line_config.get(str(i), "")
            info_text = f"{act_name}\nResponable: {op}"
            lbl_info = ctk.CTkLabel(f, text=info_text, justify="left", font=ctk.CTkFont(size=14))
            lbl_info.grid(row=0, column=1, sticky="w", padx=10)
            
            btn_done = ctk.CTkButton(f, text="Finalizar Tarea", state="disabled", width=120, height=35,
                                     command=lambda idx=i: self.record_split(idx))
            btn_done.grid(row=0, column=2, padx=15)
            
            self.act_widgets.append({"frame": f, "title": lbl_title, "btn": btn_done, "op": op})

    def start_timer(self):
        if self.running: return
        self.running = True
        self.start_time = time.time()
        self.last_split_time = self.start_time
        self.current_cycle_splits = []
        self.current_activity_index = 0
        
        self.btn_start.configure(state="disabled", fg_color="gray")
        self.btn_cancel.configure(state="normal")
        
        self.update_clock()
        self.highlight_activity(0)

    def update_clock(self):
        if self.running:
            elapsed = time.time() - self.start_time
            mins, secs = divmod(elapsed, 60)
            cents = (elapsed % 1) * 100
            self.timer_label.configure(text=f"{int(mins):02d}:{int(secs):02d}.{int(cents):02d}")
            self.after(20, self.update_clock)

    def highlight_activity(self, index):
        for i, data in enumerate(self.act_widgets):
            if i == index:
                data["frame"].configure(border_width=2, border_color="#3498db")
                data["btn"].configure(state="normal", fg_color="#3498db")
                self.op_target_lbl.configure(text=f"Turno de: {data['op']} | Realizando tarea {i+1}")
                self.act_frame._parent_canvas.yview_moveto(i / len(self.ACTIVITIES)) # auto-scroll proporcional
            else:
                data["frame"].configure(border_width=0)
                data["btn"].configure(state="disabled", fg_color="gray")

    def record_split(self, index):
        now = time.time()
        duration = now - self.last_split_time
        self.last_split_time = now # Pause internal logic for popup measure
        
        # Desactivamos el botón actual para evitar múltiples clics
        self.act_widgets[index]["btn"].configure(state="disabled", fg_color="gray")

        # Mostrar Formulario QC en la columna lateral
        self.qc_column.grid(row=0, column=1, sticky="nsew", padx=(10, 0))
        self.content_container.grid_columnconfigure(1, weight=1)
        
        for widget in self.qc_column.winfo_children():
            widget.destroy()

        ctk.CTkLabel(self.qc_column, text=f"Control Tarea {index+1}", font=ctk.CTkFont(size=20, weight="bold")).pack(pady=(20, 5))
        ctk.CTkLabel(self.qc_column, text="Problemas (Opcional):", text_color="gray").pack(pady=(0, 10))

        # Lista de 10 Errores más comunes en operaciones manuales/plegado
        common_errors = [
             "Doblez incorrecto / asimétrico",
             "Falta de concentración",
             "Se saltó instrucción",
             "Demora externa",
             "Aplicó demasiada fuerza",
             "Equivocó el sentido del pliegue",
             "Dificultad de motricidad",
             "Duda o pausa excesiva",
             "Mala postura ergonómica",
             "Desorden en estación"
        ]

        # Contenedor con Scroll para los Checkboxes
        scroll_errors = ctk.CTkScrollableFrame(self.qc_column)
        scroll_errors.pack(fill="both", expand=True, padx=20, pady=5)

        # Variables para capturar la selección
        self.error_vars = []
        for error_text in common_errors:
            var = ctk.StringVar(value="")
            chk = ctk.CTkCheckBox(scroll_errors, text=error_text, variable=var, 
                                  onvalue=error_text, offvalue="")
            chk.pack(anchor="w", pady=5)
            self.error_vars.append(var)

        # Campo para otro error no listado
        other_frame = ctk.CTkFrame(scroll_errors, fg_color="transparent")
        other_frame.pack(fill="x", pady=10)
        self.other_err_var = ctk.StringVar(value="")
        chk_other = ctk.CTkCheckBox(other_frame, text="Otro:", variable=self.other_err_var, 
                                    onvalue="Otro:", offvalue="")
        chk_other.pack(side="left", padx=(0, 5))
        self.other_entry = ctk.CTkEntry(other_frame, placeholder_text="Escribe detallado...")
        self.other_entry.pack(side="left", fill="x", expand=True)

        def save_and_continue(status):
            if status == "Normal":
                obs_text = "Normal"
            else:
                # Recopilar todos los errores seleccionados
                selected_errors = [var.get() for var in self.error_vars if var.get()]
                
                # Agregar el custom si fue seleccionado
                if self.other_err_var.get():
                    custom_err = self.other_entry.get().strip()
                    if custom_err:
                        selected_errors.append(f"Otro: {custom_err}")
                
                if not selected_errors:
                    obs_text = "Incidencia sin especificar"
                else:
                    obs_text = " | ".join(selected_errors)

            self.current_cycle_splits.append({
                "activity": self.ACTIVITIES[index],
                "operator": self.line_config.get(str(index), "N/A"),
                "duration": round(duration, 2),
                "observation": obs_text
            })
            
            # Ocultamos la columna QC
            self.qc_column.grid_forget()
            self.content_container.grid_columnconfigure(1, weight=0)
            
            if index < len(self.ACTIVITIES) - 1:
                self.current_activity_index += 1
                self.highlight_activity(self.current_activity_index)
                self.last_split_time = time.time() # Resync
            else:
                self.finish_cycle()

        button_frame = ctk.CTkFrame(self.qc_column, fg_color="transparent")
        button_frame.pack(fill="x", pady=10)

        ctk.CTkButton(button_frame, text="✅ Normal (Sin Errores)", fg_color="#27ae60", hover_color="#2ecc71", 
                      height=40, font=ctk.CTkFont(weight="bold"),
                      command=lambda: save_and_continue("Normal")).pack(fill="x", padx=20, pady=5)
        
        ctk.CTkButton(button_frame, text="⚠️ Guardar Errores", fg_color="#e67e22", hover_color="#d35400",
                      height=40, command=lambda: save_and_continue("Error")).pack(fill="x", padx=20, pady=5)

    def finish_cycle(self):
        self.running = False
        total = time.time() - self.start_time
        
        meas = {
            "cycle_id": len(self.data.get("measurements", [])) + 1,
            "model": self.current_model_name,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "total_time": round(total, 2),
            "splits": self.current_cycle_splits
        }
        self.data.setdefault("measurements", []).append(meas)
        self.save_data()
        
        messagebox.showinfo("Ciclo Finalizado", f"Toma de tiempos guardada.\nTiempo total del ciclo: {round(total, 2)}s")
        self.show_dashboard()

    def reset_timer(self):
        self.running = False
        self.timer_label.configure(text="00:00.00")
        self.op_target_lbl.configure(text="Preparado para iniciar")
        self.btn_start.configure(state="normal", fg_color="#27ae60")
        self.btn_cancel.configure(state="disabled")
        for data in self.act_widgets:
            data["frame"].configure(border_width=0)
            data["btn"].configure(state="disabled", fg_color="gray")
        
        if hasattr(self, 'qc_column') and self.qc_column.winfo_exists():
            self.qc_column.grid_forget()
            if hasattr(self, 'content_container') and self.content_container.winfo_exists():
                self.content_container.grid_columnconfigure(1, weight=0)

    def show_tables(self):
        self.clear_main_frame()
        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_rowconfigure(1, weight=1)
        
        header_f = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        header_f.pack(fill="x", padx=40, pady=20)
        ctk.CTkLabel(header_f, text="Matriz de Tiempos Recolectados", font=ctk.CTkFont(size=26, weight="bold")).pack(side="left")
        
        ctk.CTkButton(header_f, text="Eliminar Último", fg_color="#e74c3c", command=self.delete_last_measurement).pack(side="right")

        # Segmented Button para elegir qué tabla ver
        self.table_selector_var = tk.StringVar(value=self.current_model_name)
        selector = ctk.CTkSegmentedButton(self.main_frame, values=list(self.models.keys()), 
                                         variable=self.table_selector_var, command=self.update_table_view)
        selector.pack(fill="x", padx=40, pady=(0, 10))

        self.table_container = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.table_container.pack(fill="both", expand=True, padx=40, pady=(0, 20))
        
        self.update_table_view(self.current_model_name)

    def update_table_view(self, model_name):
        for widget in self.table_container.winfo_children():
            widget.destroy()
            
        table_f = ctk.CTkFrame(self.table_container, corner_radius=10)
        table_f.pack(fill="both", expand=True)

        num_steps = len(self.models[model_name]["activities"])
        cols = ["Ciclo"] + [f"P{i+1}" for i in range(num_steps)] + ["TOTAL"]
        self.tree = ttk.Treeview(table_f, columns=cols, show="headings", style="Premium.Treeview")
        
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Premium.Treeview", background="#1e293b", foreground="white", fieldbackground="#1e293b", rowheight=30)
        style.configure("Premium.Treeview.Heading", background="#0f172a", foreground="white", font=('Arial', 10, 'bold'))

        for c in cols:
            self.tree.heading(c, text=c)
            w = 50 if "P" in c and len(c) < 4 else 80
            self.tree.column(c, width=w, anchor="center")

        sb = ttk.Scrollbar(table_f, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscroll=sb.set)
        self.tree.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")

        measurements = [m for m in self.data.get("measurements", []) if m.get("model") == model_name or (not m.get("model") and model_name == "Grulla Clásica")]
        display_count = max(10, len(measurements) + 2)
        
        for i in range(display_count):
            if i < len(measurements):
                m = measurements[i]
                row = [f"#{i+1}"]
                for s in m["splits"]: row.append(f"{s['duration']}")
                while len(row) < (num_steps + 1): row.append("-")
                row.append(f"{m['total_time']}")
                self.tree.insert("", "end", values=row)
            else:
                self.tree.insert("", "end", values=[f"#{i+1}"] + ["-"]*(num_steps + 1))

    def delete_last_measurement(self):
        measurements = self.data.get("measurements", [])
        if not measurements: return
        if messagebox.askyesno("Confirmar", "¿Eliminar el último ciclo registrado?"):
            measurements.pop()
            self.save_data()
            self.show_tables()

    def show_stats(self):
        self.clear_main_frame()
        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_rowconfigure(1, weight=1)
        
        ctk.CTkLabel(self.main_frame, text="Análisis de Rendimiento", font=ctk.CTkFont(size=26, weight="bold")).pack(pady=20, padx=40, anchor="w")

        # Segmented Button para elegir qué análisis ver
        self.stats_selector_var = tk.StringVar(value=self.current_model_name)
        selector = ctk.CTkSegmentedButton(self.main_frame, values=list(self.models.keys()), 
                                         variable=self.stats_selector_var, command=self.update_stats_view)
        selector.pack(fill="x", padx=40, pady=(0, 10))

        self.stats_container = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.stats_container.pack(fill="both", expand=True, padx=40, pady=(0, 20))
        
        self.update_stats_view(self.current_model_name)

    def update_stats_view(self, model_name):
        for widget in self.stats_container.winfo_children():
            widget.destroy()

        measurements = [m for m in self.data.get("measurements", []) if m.get("model") == model_name or (not m.get("model") and model_name == "Grulla Clásica")]
        if not measurements:
            ctk.CTkLabel(self.stats_container, text=f"No hay datos suficientes para '{model_name}'.", text_color="gray", font=ctk.CTkFont(size=14)).pack(pady=50)
            return

        chart_frame = ctk.CTkFrame(self.stats_container, fg_color="#ffffff", corner_radius=15)
        chart_frame.pack(fill="both", expand=True, pady=10)

        # Gráfico por modelo
        fig, ax = plt.subplots(figsize=(10, 5), dpi=100)
        
        # Calcular promedio por tarea del modelo seleccionado
        num_steps = len(self.models[model_name]["activities"])
        step_sums = [0.0] * num_steps
        step_counts = [0] * num_steps
        
        for m in measurements:
            for i, s in enumerate(m["splits"]):
                if i < num_steps:
                    step_sums[i] += s["duration"]
                    step_counts[i] += 1
        
        avgs = [step_sums[i]/step_counts[i] if step_counts[i] > 0 else 0 for i in range(num_steps)]
        
        bars = ax.bar(range(1, num_steps + 1), avgs, color='#3498db', alpha=0.8)
        ax.set_title(f"Tiempo Promedio por Tarea: {model_name}", fontsize=14, fontweight='bold', pad=20)
        ax.set_xlabel("Número de Tarea")
        ax.set_xticks(range(1, num_steps + 1))
        ax.set_xticklabels([f"T{i}" for i in range(1, num_steps + 1)])
        ax.set_ylabel("Segundos")
        
        ax.grid(axis='y', linestyle='--', alpha=0.7)
        for spine in ax.spines.values(): spine.set_visible(False)

        canvas = FigureCanvasTkAgg(fig, master=chart_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True, padx=20, pady=20)

    def generate_pdf(self, selected_models=None):
        if selected_models is None:
            # Ventana de selección de modelos
            self.sel_win = ctk.CTkToplevel(self)
            self.sel_win.title("Seleccionar Modelos para Reporte")
            self.sel_win.geometry("500x550")
            self.sel_win.grab_set()
            self.sel_win.attributes("-topmost", True)
            
            ctk.CTkLabel(self.sel_win, text="📊 Exportación de Reporte", font=ctk.CTkFont(size=22, weight="bold")).pack(pady=(20, 10))
            ctk.CTkLabel(self.sel_win, text="¿Qué modelos deseas incluir en el documento?", 
                         font=ctk.CTkFont(size=14), text_color="gray").pack(pady=(0, 20))
            
            scroll = ctk.CTkScrollableFrame(self.sel_win, height=250)
            scroll.pack(fill="both", expand=True, padx=40, pady=10)
            
            self.export_vars = {}
            for name in self.models.keys():
                # Marcar el actual por defecto
                var = tk.BooleanVar(value=(name == self.current_model_name))
                cb = ctk.CTkCheckBox(scroll, text=name, variable=var, font=ctk.CTkFont(size=13))
                cb.pack(pady=8, anchor="w", padx=10)
                self.export_vars[name] = var
                
            def on_confirm():
                selected = [n for n, v in self.export_vars.items() if v.get()]
                if not selected:
                    messagebox.showwarning("Atención", "Selecciona al menos un modelo para exportar.")
                    return
                self.sel_win.destroy()
                self.generate_pdf(selected) # Llamada con la lista seleccionada

            btn_f = ctk.CTkFrame(self.sel_win, fg_color="transparent")
            btn_f.pack(pady=30)
            
            ctk.CTkButton(btn_f, text="Generar Reporte", command=on_confirm, width=160, 
                          fg_color="#27ae60", hover_color="#2ecc71", font=ctk.CTkFont(weight="bold")).pack(side="left", padx=10)
            ctk.CTkButton(btn_f, text="Cancelar", command=self.sel_win.destroy, width=100, 
                          fg_color="transparent", text_color=("#2c3e50", "white"), border_width=1).pack(side="left", padx=10)
            return

        # --- Lógica de Generación para los modelos en 'selected_models' ---
        all_measurements = self.data.get("measurements", [])
        
        # Verificar si hay datos en alguno
        valid_models = []
        for m_name in selected_models:
            m_data = [m for m in all_measurements if m.get("model") == m_name or (not m.get("model") and m_name == "Grulla Clásica")]
            if m_data:
                valid_models.append((m_name, m_data))
        
        if not valid_models:
            messagebox.showwarning("Sin Datos", "Los modelos seleccionados no tienen ciclos registrados.")
            return

        # Pedir ruta de guardado
        from tkinter import filedialog
        default_filename = f"Reporte_CronoGrulla_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf"
        out_path = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            initialfile=default_filename,
            title="Guardar Informe PDF Como...",
            filetypes=[("Archivos PDF", "*.pdf"), ("Todos los archivos", "*.*")]
        )
        if not out_path: return
        
        pdf = PremiumReportPDF()
        
        for m_name, measurements in valid_models:
            model_info = self.models.get(m_name)
            local_acts = model_info["activities"]
            local_descs = model_info["descriptions"]
            num_steps = len(local_acts)

            pdf.add_page()
            
            # --- SECCION 1: Informacion del Modelo ---
            pdf.set_font('Arial', 'B', 14)
            pdf.set_text_color(44, 62, 80)
            pdf.cell(0, 10, f"MODELO: {m_name.upper()}", 0, 1)
            pdf.ln(2)
            
            pdf.set_font('Arial', 'B', 11)
            pdf.cell(0, 8, "1. Informacion del Estudio y Especificaciones", 0, 1)
            pdf.set_font('Arial', '', 10)
            pdf.cell(0, 6, f"Fecha de emision: {datetime.now().strftime('%d/%m/%Y %H:%M')}", 0, 1)
            pdf.cell(0, 6, "Tamano del origami: 15x15 cm", 0, 1)
            
            pdf.set_font('Arial', 'B', 10)
            pdf.cell(0, 7, "Autores:", 0, 1)
            pdf.set_font('Arial', '', 10)
            pdf.cell(0, 5, " - David Santiago Castelblanco Artunduaga | Juan Diego Escobar Duarte | Laura Vanessa Cespedes Acosta", 0, 1)
            pdf.ln(3)

            pdf.cell(0, 6, f"Ciclos medidos: {len(measurements)}", 0, 1)
            avg = sum(m["total_time"] for m in measurements) / len(measurements)
            pdf.cell(0, 6, f"Tiempo de ciclo promedio: {avg:.2f} segundos", 0, 1)
            pdf.ln(5)

            # --- SECCION 2: Distribución Operativa ---
            pdf.set_font('Arial', 'B', 12)
            pdf.cell(0, 10, "2. Distribucion y Descripcion de Operaciones", 0, 1)
            
            configs = {}
            for idx, m in enumerate(measurements, 1):
                config = tuple(s.get("operator", "N/A") for s in m.get("splits", []))
                if len(config) < num_steps:
                    config = config + ("N/A",) * (num_steps - len(config))
                if config not in configs: configs[config] = []
                configs[config].append(idx)
                
            for config_idx, (config_tuple, cycles) in enumerate(configs.items(), 1):
                pdf.set_font('Arial', 'B', 10)
                pdf.set_text_color(52, 152, 219)
                pdf.cell(0, 8, f"Configuración #{config_idx} (Ciclos: {', '.join(map(str, cycles))})", 0, 1)
                pdf.set_text_color(0, 0, 0)
                
                pdf.set_fill_color(220, 230, 240)
                for i in range(num_steps):
                    op = config_tuple[i] if i < len(config_tuple) else "N/A"
                    pdf.set_font('Arial', 'B', 9)
                    pdf.cell(25, 7, f"Tarch {i+1}", 1, 0, 'C', True)
                    pdf.cell(35, 7, f"Op: {op}", 1, 0, 'C', True)
                    
                    clean_act = local_acts[i].encode('latin-1', 'replace').decode('latin-1')
                    pdf.multi_cell(0, 7, f" {clean_act}", 1, 'L', True)
                    pdf.set_x(10)
                    
                    pdf.set_font('Arial', '', 8)
                    clean_desc = local_descs[i].encode('latin-1', 'replace').decode('latin-1')
                    pdf.multi_cell(0, 5, f"{clean_desc}", 1, 'L')
                    pdf.set_x(10)
                pdf.ln(5)

            # --- SECCION 3: Matriz de Tiempos ---
            pdf.add_page()
            pdf.set_font('Arial', 'B', 12)
            pdf.cell(0, 10, "3. Matriz de Tiempos Registrados (Segundos)", 0, 1)
            
            pdf.set_font('Arial', 'B', 8)
            pdf.set_fill_color(52, 152, 219)
            pdf.set_text_color(255, 255, 255)
            
            w_ciclo = 12
            w_tot = 18
            # Calcular ancho para tareas (distribuir espacio disponible 190 total - ciclo - total)
            w_op = (190 - w_ciclo - w_tot) / num_steps
            
            pdf.cell(w_ciclo, 9, "#", 1, 0, 'C', True)
            for i in range(num_steps): pdf.cell(w_op, 9, f"T{i+1}", 1, 0, 'C', True)
            pdf.cell(w_tot, 9, "TOTAL", 1, 1, 'C', True)
            
            pdf.set_text_color(0, 0, 0)
            pdf.set_font('Arial', '', 7)
            sum_ops = [0.0] * num_steps
            count_ops = [0] * num_steps
            fill = False

            for i, m in enumerate(measurements, 1):
                pdf.cell(w_ciclo, 7, f"{i}", 1, 0, 'C', fill)
                for j, s in enumerate(m["splits"]):
                    if j < num_steps:
                        pdf.cell(w_op, 7, f"{s['duration']}", 1, 0, 'C', fill)
                        sum_ops[j] += s["duration"]
                        count_ops[j] += 1
                
                # Rellenar faltantes
                if len(m["splits"]) < num_steps:
                    for _ in range(num_steps - len(m["splits"])): pdf.cell(w_op, 7, "-", 1, 0, 'C', fill)
                
                pdf.set_font('Arial', 'B', 7)
                pdf.cell(w_tot, 7, f"{m['total_time']}", 1, 1, 'C', fill)
                pdf.set_font('Arial', '', 7)
                fill = not fill

            # Gráfico de Cuellos de Botella
            avg_ops = [sum_ops[i] / count_ops[i] if count_ops[i] > 0 else 0 for i in range(num_steps)]
            plt.figure(figsize=(10, 4))
            plt.bar([f"T{i+1}" for i in range(num_steps)], avg_ops, color='#3498db')
            plt.title(f'Cuellos de Botella: {m_name}')
            plt.ylabel('Segundos')
            plt.tight_layout()
            
            tmp_img = os.path.join(tempfile.gettempdir(), f"graph_{m_name}.png")
            plt.savefig(tmp_img)
            plt.close()
            pdf.ln(5)
            pdf.image(tmp_img, x=10, w=190)

            # --- SECCION 4: Eficiencia y Calidad ---
            pdf.add_page()
            pdf.set_font('Arial', 'B', 12)
            pdf.cell(0, 10, "4. Analisis Detallado de Rendimiento por Operador", 0, 1)
            
            # Estadísticas agrupadas
            op_stats = {}
            incidences = []
            for i_m, m in enumerate(measurements, 1):
                for i_s, s in enumerate(m["splits"]):
                    op = s.get("operator", "N/A")
                    if op != "N/A":
                        if op not in op_stats: op_stats[op] = {"times": [], "tasks_idx": set()}
                        op_stats[op]["times"].append(s["duration"])
                        op_stats[op]["tasks_idx"].add(i_s)
                    
                    obs = s.get("observation", "Normal")
                    if obs != "Normal":
                        incidences.append(f"[Ciclo {i_m}-T{i_s+1}] {op}: {obs}")

            # Calcular metricas completas
            for op, data in op_stats.items():
                times = data["times"]
                data["time"] = sum(times)
                data["tasks"] = len(times)
                data["min"] = min(times)
                data["max"] = max(times)
                data["avg"] = data["time"] / data["tasks"]
                data["std"] = np.std(times) if len(times) > 1 else 0
                data["assigned"] = sorted(list(data["tasks_idx"]))

            # Ordenamos de más rápido a más lento (menor promedio por tarea)
            sorted_ops = sorted(op_stats.items(), key=lambda x: x[1]["avg"])
            
            # 1. Gráfico de Operadores
            op_names_clean = [op.encode('latin-1', 'replace').decode('latin-1') for op, d in sorted_ops]
            op_avgs = [d["avg"] for op, d in sorted_ops]
            plt.figure(figsize=(10, 4))
            plt.bar(op_names_clean, op_avgs, color='#2ecc71', edgecolor='black')
            plt.title(f'Rendimiento Promedio Individual: {m_name}')
            plt.ylabel('Segundos (Promedio por Tarea)')
            plt.grid(axis='y', linestyle='--', alpha=0.7)
            plt.tight_layout()
            
            tmp_op_img = os.path.join(tempfile.gettempdir(), f"op_graph_{m_name}.png")
            plt.savefig(tmp_op_img)
            plt.close()
            
            pdf.image(tmp_op_img, x=10, w=190)
            pdf.ln(2)

            # 2. Tabla Detallada
            pdf.set_font('Arial', 'B', 8)
            pdf.set_fill_color(44, 62, 80)
            pdf.set_text_color(255, 255, 255)
            
            pdf.cell(40, 8, "Operador", 1, 0, 'C', True)
            pdf.cell(20, 8, "Tareas Asig.", 1, 0, 'C', True)
            pdf.cell(30, 8, "Rango (Min - Max)", 1, 0, 'C', True)
            pdf.cell(25, 8, "Volatilidad", 1, 0, 'C', True)
            pdf.cell(35, 8, "Total Invertido", 1, 0, 'C', True)
            pdf.cell(40, 8, "Promedio/Tarea", 1, 1, 'C', True)
            
            pdf.set_text_color(0, 0, 0)
            fill = False
            pdf.set_fill_color(240, 248, 255)
            
            for op, stats in sorted_ops:
                clean_op = op.encode('latin-1', 'replace').decode('latin-1')
                pdf.set_font('Arial', 'B', 8)
                pdf.cell(40, 7, f" {clean_op[:20]}", 1, 0, 'L', fill)
                
                pdf.set_font('Arial', '', 8)
                assigned_str = ",".join(f"T{i+1}" for i in stats["assigned"])
                if len(assigned_str) > 12: assigned_str = assigned_str[:10] + "..."
                pdf.cell(20, 7, assigned_str, 1, 0, 'C', fill)
                
                pdf.cell(30, 7, f"{stats['min']}s - {stats['max']}s", 1, 0, 'C', fill)
                pdf.cell(25, 7, f"±{round(stats['std'], 2)}s", 1, 0, 'C', fill)
                pdf.cell(35, 7, f"{round(stats['time'], 2)}s", 1, 0, 'C', fill)
                
                # Resaltar el más eficiente en la columna final
                pdf.set_font('Arial', 'B', 8)
                if op == sorted_ops[0][0] and len(sorted_ops)>1:
                    pdf.set_text_color(39, 174, 96) # Verde
                    pdf.cell(40, 7, f"{round(stats['avg'], 2)}s (Mas Rapido)", 1, 1, 'C', fill)
                    pdf.set_text_color(0, 0, 0)
                else:
                    pdf.cell(40, 7, f"{round(stats['avg'], 2)}s", 1, 1, 'C', fill)
                    
                fill = not fill
            
            pdf.ln(5)
            pdf.set_font('Arial', 'I', 8)
            pdf.set_text_color(80, 80, 80)
            explicacion_eficiencia = (
                "Análisis de Desempeño: La gráfica y la tabla presentan el perfil operativo de cada trabajador. "
                "'Rango (Min - Max)' muestra sus tiempos más veloces y más lentos. La 'Volatilidad' (Desviación "
                "Estándar) indica qué tan constante es un operador: un número bajo significa que trabaja a un "
                "ritmo estable, mientras que un número alto puede indicar falta de experiencia o fatiga. El 'Promedio' "
                "dictamina al operario más ágil en general."
            )
            pdf.multi_cell(0, 5, explicacion_eficiencia.encode('latin-1', 'replace').decode('latin-1'), 0, 'J')
            pdf.set_x(10)
            
            # Incidencias y Análisis Gráfico Pareto
            pdf.ln(10)
            pdf.set_font('Arial', 'B', 12)
            pdf.set_text_color(0, 0, 0)
            pdf.cell(0, 8, "5. Registro de Incidencias de Calidad", 0, 1)
            pdf.set_font('Arial', '', 9)
            
            if not incidences:
                pdf.cell(0, 6, "No se registraron fallas de calidad en este modelo.", 0, 1)
            else:
                defect_counts = {}
                pdf.set_text_color(192, 57, 43)
                for inc in incidences:
                    # Extraer el texto de la observacion para el conteo (despues de los : )
                    obs_text = inc.split(": ", 1)[1] if ": " in inc else inc
                    clean_inc = inc.encode('latin-1', 'replace').decode('latin-1')
                    pdf.multi_cell(0, 6, clean_inc)
                    pdf.set_x(10)
                    
                    # Contabilidad para pareto
                    errores = obs_text.split(" | ")
                    for err in errores:
                        short_err = err[:25] + ".." if len(err) > 25 else err
                        defect_counts[short_err] = defect_counts.get(short_err, 0) + 1

                pdf.set_text_color(0, 0, 0)
                
                # Gráfico Pareto
                errores_ord = sorted(defect_counts.items(), key=lambda x: x[1], reverse=False)
                if errores_ord:
                    keys = [x[0] for x in errores_ord]
                    vals = [x[1] for x in errores_ord]
                    
                    plt.figure(figsize=(10, 4))
                    plt.barh(keys, vals, color='#e74c3c', edgecolor='black')
                    plt.title(f'Frecuencia de Incidencias - {m_name}')
                    plt.xlabel('Cantidad')
                    plt.grid(axis='x', linestyle='--', alpha=0.7)
                    
                    from matplotlib.ticker import MaxNLocator
                    plt.gca().xaxis.set_major_locator(MaxNLocator(integer=True))
                    plt.tight_layout()
                    
                    grafica_errores_path = os.path.join(tempfile.gettempdir(), f"err_{m_name}.png")
                    plt.savefig(grafica_errores_path)
                    plt.close()
                    
                    pdf.ln(5)
                    pdf.image(grafica_errores_path, x=10, w=190)

                    # Análisis de Pareto con Porcentajes
                    pdf.ln(5)
                    pdf.set_font('Arial', 'B', 10)
                    pdf.cell(0, 8, "Analisis Porcentual de Incidencias:", 0, 1)
                    pdf.set_font('Arial', '', 9)
                    
                    total_errores = sum(vals)
                    for err_name, count in reversed(errores_ord):
                        pct = (count / total_errores) * 100
                        clean_err = err_name.encode('latin-1', 'replace').decode('latin-1')
                        pdf.cell(0, 6, f" - {clean_err}: {count} ocurrencia(s) ({pct:.1f}%)", 0, 1)

            # --- SECCION 6: Conclusiones del Modelo ---
            pdf.ln(8)
            pdf.set_font('Arial', 'B', 12)
            pdf.set_text_color(0, 0, 0)
            pdf.cell(0, 8, "6. Conclusiones y Resumen de Eficiencia", 0, 1)
            pdf.set_font('Arial', '', 10)
            
            # Calcular eficiencia general del modelo
            total_time_all_cycles = sum(m["total_time"] for m in measurements)
            mejor_ciclo = min(m["total_time"] for m in measurements) if measurements else 0
            ideal_time = mejor_ciclo * len(measurements)
            
            efficiency_pct = (ideal_time / total_time_all_cycles * 100) if total_time_all_cycles > 0 else 0
            
            promedio_ciclo_txt = f"El estudio del modelo '{m_name}' constó de {len(measurements)} ciclos operativos. El tiempo promedio general de fabricación es de {avg:.2f} segundos, mientras que el tiempo récord (mejor ciclo) fue de {mejor_ciclo:.2f} segundos."
            pdf.multi_cell(0, 6, promedio_ciclo_txt.encode('latin-1', 'replace').decode('latin-1'))
            pdf.ln(2)
            
            concl_txt = f"Comparando el ritmo general de la línea frente al mejor tiempo registrado, se estima que el equipo operó a un {efficiency_pct:.1f}% de su capacidad ideal. Para acortar la brecha y acercarse al nivel óptimo, se recomienda re-balancear los cuellos de botella identificados en la Gráfica 3 y entrenar al personal para mitigar las deficiencias especificadas en la Sección 5."
            pdf.multi_cell(0, 6, concl_txt.encode('latin-1', 'replace').decode('latin-1'))
            pdf.ln(5)
        
        try:
            pdf.output(out_path)
            messagebox.showinfo("Reporte Exportado", f"Informe consolidado guardado en:\n{out_path}")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo guardar el PDF: {e}")

    def generate_instructions_pdf(self):
        from tkinter import filedialog
        default_filename = f"Manual_Instrucciones_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf"
        out_path = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            initialfile=default_filename,
            title="Guardar Manual de Instrucciones Como...",
            filetypes=[("Archivos PDF", "*.pdf"), ("Todos los archivos", "*.*")]
        )
        
        if not out_path:
            return
        
        pdf = PremiumReportPDF()
        pdf.add_page()
        
        pdf.set_font('Arial', 'B', 16)
        pdf.set_text_color(44, 62, 80)
        pdf.cell(0, 10, f"MANUAL: {self.current_model_name.upper()}", 0, 1, 'C')
        pdf.ln(5)
        
        pdf.set_font('Arial', '', 11)
        pdf.set_text_color(80, 80, 80)
        pdf.cell(0, 6, "Tamano del origami: 15x15 cm", 0, 1, 'C')
        pdf.cell(0, 6, "Autores (Ingenieros Industriales): David Santiago Castelblanco Artunduaga (5201057)", 0, 1, 'C')
        pdf.cell(0, 6, "Juan Diego Escobar Duarte (5200969) | Laura Vanessa Cespedes Acosta (5200901)", 0, 1, 'C')
        pdf.ln(8)
        
        pdf.set_font('Arial', 'I', 11)
        pdf.cell(0, 8, f"Procedimiento de {len(self.ACTIVITIES)} pasos para manufactura.", 0, 1, 'C')
        pdf.ln(8)
        
        for idx in range(len(self.ACTIVITIES)):
            pdf.set_font('Arial', 'B', 12)
            pdf.set_text_color(52, 152, 219)
            clean_act = self.ACTIVITIES[idx].encode('latin-1', 'replace').decode('latin-1')
            pdf.cell(0, 8, clean_act, 0, 1, 'L')
            
            pdf.set_font('Arial', '', 11)
            pdf.set_text_color(0, 0, 0)
            clean_desc = self.FULL_DESCRIPTIONS[idx].encode('latin-1', 'replace').decode('latin-1')
            pdf.multi_cell(0, 6, clean_desc, 0, 'J')
            pdf.ln(5)
            
        try:
            pdf.output(out_path)
            messagebox.showinfo("Manual Exportado", f"Manual guardado exitosamente en:\n{out_path}")
        except Exception as e:
            messagebox.showerror("Error de Exportacion", f"No se pudo guardar el PDF.\n\nDetalles: {e}")

if __name__ == "__main__":
    app = CraneFlowApp()
    app.mainloop()
