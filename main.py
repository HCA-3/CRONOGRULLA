import tkinter as tk
import customtkinter as ctk
import json
import os
import subprocess
import sys
from PIL import Image

# Model Imports
from views.view_dashboard import DashboardView
from views.view_models import ModelsView
from views.view_operators import OperatorsView
from views.view_timer import TimerView
from views.view_tables import TablesView
from views.view_stats import StatsView
from views.view_media import MediaGalleryView
from views.view_trash import TrashView
from views.view_comparison import ComparisonView
from views.view_sensor_data import SensorDataView
from views.view_standard_time import StandardTimeView
from utils.pdf_report import PDFManager
from views.view_objectives import ObjectivesView


# Configuración de apariencia Premium..
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class CraneFlowApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("CronoGrulla | Ingeniería de Métodos")
        # Maximizar para ajustar a pantalla
        self.after(0, lambda: self.state('zoomed'))
        self.minsize(1100, 750)
        
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
        self.operator_allowances = self.data.get("operator_allowances", {})
        
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
            self.data = {"operators": [], "line_config": {}, "measurements": [], "operator_allowances": {}}

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
        self.data["operator_allowances"] = self.operator_allowances
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

        # Header: logo + título
        logo_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        logo_frame.grid(row=0, column=0, padx=12, pady=(20, 12), sticky="w")

        # Intentar cargar logo de la universidad si existe en assets/ o Imagenes/
        self.university_logo = None
        logo_candidates = ["assets/logo_ucatolica.png", "assets/ucatolica_logo.png", "Imagenes/logo_ucatolica.png"]
        for p in logo_candidates:
            if os.path.exists(p):
                try:
                    pil_img = Image.open(p)
                    self.university_logo = ctk.CTkImage(light_image=pil_img, size=(64, 64))
                    break
                except Exception:
                    self.university_logo = None

        if self.university_logo:
            img_label = ctk.CTkLabel(logo_frame, image=self.university_logo, text="")
            img_label.grid(row=0, column=0, padx=(8, 8))

        self.logo_label = ctk.CTkLabel(logo_frame, text="🏗️ CronoGrulla", font=ctk.CTkFont(size=20, weight="bold", family="Helvetica"))
        self.logo_label.grid(row=0, column=1, padx=6, pady=6, sticky="w")

        # Botones de navegación
        nav_buttons = [
            ("📊 Dashboard", self.show_dashboard),
            ("🎯 Objetivos y Metodología", self.show_objectives_panel),
            ("✨ Modelos Origami", self.show_models_panel),
            ("⏱️ Cronometrar", self.show_timer),
            ("📋 Datos y Tabla", self.show_tables),
            ("👥 Equipo y Tareas", self.show_operators_setup),
            ("📸 Evidencia Visual", self.show_media_gallery),
            ("📡 Datos del Sensor", self.show_sensor_data),
            ("📊 Comparativa Operarios", self.show_comparison),
            ("🗑️ Papelera", self.show_trash),
            ("📈 Estadísticas", self.show_stats),
            ("⏱️ Tiempo Estándar", self.show_standard_time)
        ]

        self.sidebar.grid_rowconfigure(1, weight=1)
        self.nav_scroll = ctk.CTkScrollableFrame(self.sidebar, fg_color="transparent", corner_radius=0)
        self.nav_scroll.grid(row=1, column=0, sticky="nsew", padx=0, pady=(0, 10))

        self.nav_btns = []
        for text, cmd in nav_buttons:
            btn = ctk.CTkButton(self.nav_scroll, text=text, anchor="w", fg_color="transparent", 
                                text_color=("white", "#c9d1d9"), font=ctk.CTkFont(size=14),
                                hover_color=("#34495e", "#2c3e50"), command=cmd)
            btn.pack(fill="x", padx=20, pady=5)
            self.nav_btns.append(btn)

        # Información del semillero / universidad (fija en la parte inferior)
        info_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        info_frame.grid(row=2, column=0, sticky="ew", padx=16, pady=(8, 8))
        ctk.CTkLabel(info_frame, text="Universidad Católica de Colombia", font=ctk.CTkFont(size=11, weight="bold"), anchor="w").pack(anchor="w")
        ctk.CTkLabel(info_frame, text="Semillero: Inspira", font=ctk.CTkFont(size=11), anchor="w").pack(anchor="w", pady=(2,0))
        ctk.CTkLabel(info_frame, text="Dirigido por: Prof. Karol Lizeth Roa Bohorquez", font=ctk.CTkFont(size=10), anchor="w").pack(anchor="w", pady=(2,4))

        # Contenedor inferior para botones de exportación (más pegados)
        self.pdf_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        self.pdf_frame.grid(row=3, column=0, sticky="ew", padx=20, pady=(10, 20))
        self.pdf_frame.grid_columnconfigure(0, weight=1)

        self.btn_pdf_instructions = ctk.CTkButton(self.pdf_frame, text="📘 Exportar Manual", 
                                     fg_color=("#3498db", "#2980b9"), hover_color=("#2980b9", "#3498db"),
                                     font=ctk.CTkFont(size=13, weight="bold"), command=self.pdf_manager.generate_instructions_pdf)
        self.btn_pdf_instructions.grid(row=0, column=0, pady=(0, 5), sticky="ew")

        self.btn_pdf = ctk.CTkButton(self.pdf_frame, text="📄 Exportar Informe PDF", 
                                     fg_color=("#27ae60", "#219653"), hover_color=("#2ecc71", "#27ae60"),
                                     font=ctk.CTkFont(size=13, weight="bold"), command=self.pdf_manager.generate_pdf)
        self.btn_pdf.grid(row=1, column=0, pady=0, sticky="ew")

        # --- BOTÓN IA ---
        self.btn_ia = ctk.CTkButton(
            self.pdf_frame,
            text="🧠 IA  — Ver Modelos",
            fg_color=("#6c3483", "#8e44ad"),
            hover_color=("#8e44ad", "#6c3483"),
            font=ctk.CTkFont(size=13, weight="bold"),
            command=self.show_ai_info
        )
        self.btn_ia.grid(row=2, column=0, pady=(8, 0), sticky="ew")

        # Contenedor Principal
        self.main_frame = ctk.CTkFrame(self, corner_radius=15, fg_color=("#ecf0f1", "#0f172a"))
        self.main_frame.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        
        # Toggle Sidebar Variables y Botón Flotante
        self.sidebar_expanded = True
        self.btn_toggle = ctk.CTkButton(self, text="☰ Ocultar Menú", width=140, height=32, 
                        fg_color="#e74c3c", hover_color="#c0392b", font=ctk.CTkFont(weight="bold"),
                        command=self.toggle_sidebar)
        # colocar el botón al lado derecho de la barra lateral para que no tape el título
        self.btn_toggle.place(x=240, y=10)

    def toggle_sidebar(self):
        if self.sidebar_expanded:
            self.sidebar.grid_remove() # Oculta la barra
            self.btn_toggle.configure(text="☰ Mostrar Menú", fg_color="#3498db", hover_color="#2980b9")
            # mover el botón al borde izquierdo cuando la barra está oculta
            self.btn_toggle.place(x=15, y=10)
            self.sidebar_expanded = False
        else:
            self.sidebar.grid() # Muestra la barra
            self.btn_toggle.configure(text="☰ Ocultar Menú", fg_color="#e74c3c", hover_color="#c0392b")
            # colocarlo junto a la barra para no tapar el título
            self.btn_toggle.place(x=240, y=10)
            self.sidebar_expanded = True

    def clear_main_frame(self):
        for widget in self.main_frame.winfo_children():
            widget.destroy()

    def show_dashboard(self):
        self.clear_main_frame()
        self.current_view = DashboardView(self.main_frame, self)
        self.current_view.pack(fill="both", expand=True)

    def show_objectives_panel(self):
        self.clear_main_frame()
        self.current_view = ObjectivesView(self.main_frame, self)
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

    def show_media_gallery(self):
        self.clear_main_frame()
        self.current_view = MediaGalleryView(self.main_frame, self)
        self.current_view.pack(fill="both", expand=True)

    def show_trash(self):
        self.clear_main_frame()
        self.current_view = TrashView(self.main_frame, self)
        self.current_view.pack(fill="both", expand=True)

    def show_comparison(self):
        self.clear_main_frame()
        self.current_view = ComparisonView(self.main_frame, self)
        self.current_view.pack(fill="both", expand=True)

    def show_sensor_data(self):
        self.clear_main_frame()
        self.current_view = SensorDataView(self.main_frame, self)
        self.current_view.pack(fill="both", expand=True)

    def show_standard_time(self):
        self.clear_main_frame()
        self.current_view = StandardTimeView(self.main_frame, self)
        self.current_view.pack(fill="both", expand=True)

    def show_ai_info(self):
        AIInfoDialog(self)

    def open_pdf_guide(self, model_name):
        self.current_view = ModelsView(self.main_frame, self)
        self.current_view.open_pdf_guide(model_name)

# ─────────────────────────────────────────────────────────────────────────────
# VENTANA MODAL: Explicación del Motor de IA
# ─────────────────────────────────────────────────────────────────────────────
class AIInfoDialog(ctk.CTkToplevel):
    """Ventana modal que detalla todos los modelos de IA usados en CronoGrulla."""

    def __init__(self, master):
        super().__init__(master)
        self.title("🧠 Motor de Inteligencia Artificial — CronoGrulla")
        self.geometry("820x680")
        self.resizable(True, True)
        self.attributes("-topmost", True)
        self.grab_set()  # Modal bloqueante
        self._build()

    def _build(self):
        # ── Encabezado ──────────────────────────────────────────────────────
        header = ctk.CTkFrame(self, fg_color=("#1a0533", "#1a0533"), corner_radius=0, height=80)
        header.pack(fill="x")
        header.pack_propagate(False)
        ctk.CTkLabel(
            header,
            text="🧠  Motor de Inteligencia Artificial",
            font=ctk.CTkFont(size=22, weight="bold"),
            text_color="#d7beff"
        ).pack(side="left", padx=30, pady=20)
        ctk.CTkLabel(
            header,
            text="CronoGrulla · Ingeniería de Métodos",
            font=ctk.CTkFont(size=12),
            text_color="#9b59b6"
        ).pack(side="right", padx=30)

        # ── Área de scroll ───────────────────────────────────────────────────
        scroll = ctk.CTkScrollableFrame(self, fg_color=("#0f0020", "#0f0020"), corner_radius=0)
        scroll.pack(fill="both", expand=True, padx=0, pady=0)

        def section(parent, icon, title, color):
            """Crea un bloque de sección con título coloreado."""
            f = ctk.CTkFrame(parent, fg_color=("#1c0040", "#1c0040"), corner_radius=12)
            f.pack(fill="x", padx=20, pady=8)
            hdr = ctk.CTkFrame(f, fg_color="transparent")
            hdr.pack(fill="x", padx=15, pady=(12, 4))
            ctk.CTkLabel(hdr, text=f"{icon}  {title}",
                         font=ctk.CTkFont(size=15, weight="bold"),
                         text_color=color).pack(side="left")
            return f

        def body(parent, text):
            ctk.CTkLabel(
                parent, text=text,
                font=ctk.CTkFont(size=12),
                text_color="#ccc",
                justify="left",
                wraplength=700
            ).pack(anchor="w", padx=15, pady=(0, 12))

        def badge(parent, label, value, badge_color="#6c3483"):
            row = ctk.CTkFrame(parent, fg_color="transparent")
            row.pack(anchor="w", padx=15, pady=2)
            ctk.CTkLabel(row, text=label,
                         font=ctk.CTkFont(size=12),
                         text_color="#aaa", width=170, anchor="w").pack(side="left")
            ctk.CTkLabel(row, text=value,
                         font=ctk.CTkFont(size=12, weight="bold"),
                         text_color="white",
                         fg_color=badge_color,
                         corner_radius=6,
                         padx=8, pady=2).pack(side="left")

        # ── 1. MediaPipe Holistic ─────────────────────────────────────────────
        s1 = section(scroll, "🦴", "1. Estimación de Pose — MediaPipe Holistic", "#5dade2")
        body(s1,
             "MediaPipe Holistic es un pipeline de visión por computador de Google que detecta en tiempo real "
             "33 puntos de referencia del cuerpo (pose), 21 por cada mano y 468 faciales. "
             "En CronoGrulla se usa para:\n"
             "  • Calcular los ángulos del codo derecho e izquierdo (Hombro→Codo→Muñeca) a 30 FPS.\n"
             "  • Detectar si el operario está frente a la cámara (visibilidad > 0.5).\n"
             "  • Alimentar de datos crudos al clasificador de Therbligs y al motor de fatiga.")
        badge(s1, "Tipo de modelo:",  "Red Neuronal CNN (BlazePose)",  "#1a5276")
        badge(s1, "Framework:",        "MediaPipe 0.10 + OpenCV",        "#1a5276")
        badge(s1, "Inferencia:",       "Tiempo real · ~30 ms/frame",     "#1a5276")
        badge(s1, "Uso en el panel:",  "Ángulos Codo D. / Codo I.",      "#1a5276")
        ctk.CTkFrame(s1, height=8, fg_color="transparent").pack()

        # ── 2. Clasificador SVM de Therbligs ──────────────────────────────────
        s2 = section(scroll, "✊", "2. Clasificador de Therbligs — SVM (scikit-learn)", "#2ecc71")
        body(s2,
             "Un modelo de Máquina de Soporte Vectorial (SVM) entrenado con vectores de 63 elementos "
             "(coordenadas X, Y, Z de los 21 landmarks de la mano detectados por MediaPipe) clasifica "
             "en tiempo real el microelemento de trabajo (Therblig) que está realizando el operario:\n"
             "  ✊  TOMAR (Grasp) — Dedos doblados, puntas compactas hacia la muñeca.\n"
             "  🖐️  SOLTAR (Release) — Dedos extendidos radialmente, separados de la muñeca.\n\n"
             "Si el modelo .pkl no está disponible, el sistema aplica automáticamente un "
             "clasificador heurístico multivariable (umbral calibrado en extensión promedio de dedos ≥ 1.38).")
        badge(s2, "Tipo de modelo:",  "SVM — kernel RBF (SVC)",           "#1e8449")
        badge(s2, "Vector entrada:",  "63 features (21 lm × x,y,z)",      "#1e8449")
        badge(s2, "Archivo modelo:",  "scratch/therblig_svm_model.pkl",    "#1e8449")
        badge(s2, "Fallback:",        "Heurístico de extensión de dedos",  "#1e8449")
        ctk.CTkFrame(s2, height=8, fg_color="transparent").pack()

        # ── 3. Detección de Calidad — YOLO Simulado ───────────────────────────
        s3 = section(scroll, "🔍", "3. Verificación de Calidad de Plegado — YOLOv8 (Simulado)", "#f1c40f")
        body(s3,
             "Al finalizar cada ciclo de plegado de una grulla, se activa una detección de calidad "
             "geométrica simulada basada en YOLOv8 Object Detection.\n"
             "La calidad se calcula como:\n"
             "  Calidad (%) = 98.5 − (|ángulo_promedio − 105°| × 0.08) + ruido_gaussiano\n"
             "  • Grulla ÓPTIMA (≥ 90 %): Ángulos posturales dentro del rango ergonómico 90°–120°.\n"
             "  • Grulla INEXACTA (< 90 %): Desviaciones posturales acumuladas indican movimientos imprecisos.\n\n"
             "El bounding box verde/naranja se superpone sobre el video durante 6 segundos al completar la pieza, "
             "replicando la visualización de un detector YOLOv8 real sobre la zona de trabajo.")
        badge(s3, "Tipo de modelo:",  "YOLOv8 Object Detection (sim.)",   "#7d6608")
        badge(s3, "Entrada:",         "Registro ergonómico del ciclo",     "#7d6608")
        badge(s3, "Salida visual:",   "Bounding Box en cámara (6 seg)",   "#7d6608")
        badge(s3, "Score range:",     "80 % – 99.5 %",                    "#7d6608")
        ctk.CTkFrame(s3, height=8, fg_color="transparent").pack()

        # ── 4. IA Predictiva de Fatiga ─────────────────────────────────────────
        s4 = section(scroll, "📈", "4. IA Predictiva de Fatiga — Regresión Lineal (scikit-learn)", "#e74c3c")
        body(s4,
             "Un motor de IA predictiva estima continuamente el índice de fatiga del operario y proyecta "
             "cuándo decaerá su productividad ANTES de que ocurra, con tres componentes:\n"
             "  1. Fatiga Postural: Cada ángulo fuera del rango óptimo (80°–130°) suma penalidades al índice.\n"
             "  2. Factor Ambiental: Iluminación < 300 lx (+15%) y ruido > 80 dB (+20%) amplifican la fatiga.\n"
             "  3. Factor Temporal: La fatiga crece linealmente con el tiempo de trabajo acumulado.\n\n"
             "Con ≥ 2 ciclos históricos disponibles, un modelo LinearRegression (scikit-learn) ajusta "
             "los tiempos anteriores para predecir la duración y variación del próximo ciclo. "
             "Sin históricos, se usa un decaimiento estimado proporcional al índice de fatiga.")
        badge(s4, "Tipo de modelo:",  "LinearRegression (sklearn)",       "#922b21")
        badge(s4, "Variables entrada:","Ángulos codo, Lux, dB, tiempo",   "#922b21")
        badge(s4, "Rangos fatiga:",    "< 30% Estable · 30-65% Mod · > 65% Crítico", "#922b21")
        badge(s4, "Actualización:",    "Cada 100 ms (update_clock)",       "#922b21")
        ctk.CTkFrame(s4, height=8, fg_color="transparent").pack()

        # ── Tabla de flujo de datos ───────────────────────────────────────────
        s5 = section(scroll, "🔄", "Flujo de Datos entre Módulos de IA", "#9b59b6")
        flow_text = (
            "  Cámara (OpenCV)\n"
            "       ↓\n"
            "  MediaPipe Holistic  →  33 landmarks pose + 21 landmarks mano\n"
            "       ↓                        ↓\n"
            "  Ángulos de codo          Clasificador SVM / Heurístico\n"
            "  (ergo_log)               (Therblig: TOMAR / SOLTAR)\n"
            "       ↓\n"
            "  Motor de Fatiga  →  Índice (%) + Proyección ciclo siguiente\n"
            "       ↓\n"
            "  Al completar ciclo → Score YOLOv8 + Bounding Box en video"
        )
        ctk.CTkLabel(s5, text=flow_text,
                     font=ctk.CTkFont(family="Courier", size=11),
                     text_color="#bb8fce",
                     justify="left").pack(anchor="w", padx=18, pady=(4, 14))

        # ── Botón cerrar ──────────────────────────────────────────────────────
        ctk.CTkButton(
            self,
            text="✅  Entendido — Cerrar",
            fg_color=("#6c3483", "#8e44ad"),
            hover_color=("#8e44ad", "#6c3483"),
            font=ctk.CTkFont(size=14, weight="bold"),
            height=42,
            command=self.destroy
        ).pack(fill="x", padx=30, pady=16)


if __name__ == "__main__":
    app = CraneFlowApp()
    app.mainloop()
