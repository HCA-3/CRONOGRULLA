import customtkinter as ctk
from utils.excel_loader import ExcelDataLoader

class ObjectivesView(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color="transparent")
        self.controller = controller
        
        # Cargar datos desde el Excel
        self.data = ExcelDataLoader.get_group_data()
        
        self._build_ui()

    def _build_ui(self):
        # Título principal de la vista
        title_label = ctk.CTkLabel(
            self, 
            text="🎯 Objetivos y Metodología del Proyecto", 
            font=ctk.CTkFont(size=24, weight="bold", family="Helvetica"),
            text_color=("#1a252f", "#3498db")
        )
        title_label.pack(anchor="w", padx=30, pady=(25, 10))
        
        # Contenedor con scroll para ver toda la información de forma responsiva
        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=20, pady=10)
        
        # Tarjeta 1: Título e Integrantes del Grupo
        card_group = ctk.CTkFrame(scroll, fg_color=("#ffffff", "#1e293b"), corner_radius=12, border_width=1, border_color=("#e2e8f0", "#334155"))
        card_group.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(
            card_group, 
            text="📌 INFORMACIÓN GENERAL DEL PROYECTO (GRUPO 3)", 
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=("#2c3e50", "#60a5fa")
        ).pack(anchor="w", padx=20, pady=(15, 5))
        
        ctk.CTkLabel(
            card_group, 
            text="Tema de Investigación:", 
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=("#34495e", "#94a3b8")
        ).pack(anchor="w", padx=20, pady=(5, 0))
        
        ctk.CTkLabel(
            card_group, 
            text=self.data["titulo"], 
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=("#2c3e50", "#f8fafc"),
            wraplength=800,
            justify="left"
        ).pack(anchor="w", padx=20, pady=(0, 10))
        
        ctk.CTkLabel(
            card_group, 
            text="Participantes / Integrantes del Grupo:", 
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=("#34495e", "#94a3b8")
        ).pack(anchor="w", padx=20, pady=(5, 0))
        
        ctk.CTkLabel(
            card_group, 
            text=self.data["participantes"], 
            font=ctk.CTkFont(size=13),
            text_color=("#2c3e50", "#cbd5e1"),
            wraplength=800,
            justify="left"
        ).pack(anchor="w", padx=20, pady=(0, 15))

        # Tarjeta 2: Objetivos del Proyecto
        card_objectives = ctk.CTkFrame(scroll, fg_color=("#ffffff", "#1e293b"), corner_radius=12, border_width=1, border_color=("#e2e8f0", "#334155"))
        card_objectives.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(
            card_objectives, 
            text="🎯 OBJETIVOS DE INVESTIGACIÓN", 
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=("#2c3e50", "#34d399")
        ).pack(anchor="w", padx=20, pady=(15, 10))
        
        ctk.CTkLabel(
            card_objectives, 
            text=self.data["objetivos"], 
            font=ctk.CTkFont(size=13, family="Helvetica"),
            text_color=("#2c3e50", "#e2e8f0"),
            wraplength=800,
            justify="left"
        ).pack(anchor="w", padx=20, pady=(0, 15))

        # Tarjeta 3: Metodología Aplicada
        card_methodology = ctk.CTkFrame(scroll, fg_color=("#ffffff", "#1e293b"), corner_radius=12, border_width=1, border_color=("#e2e8f0", "#334155"))
        card_methodology.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(
            card_methodology, 
            text="🔬 METODOLOGÍA DEL PROYECTO", 
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=("#2c3e50", "#fb7185")
        ).pack(anchor="w", padx=20, pady=(15, 10))
        
        ctk.CTkLabel(
            card_methodology, 
            text=self.data["metodologia"], 
            font=ctk.CTkFont(size=13),
            text_color=("#2c3e50", "#e2e8f0"),
            wraplength=800,
            justify="left"
        ).pack(anchor="w", padx=20, pady=(0, 15))
        
        # Tarjeta de Impacto / Integración Premium en CronoGrulla
        card_impact = ctk.CTkFrame(scroll, fg_color=("#ebf5fb", "#0f172a"), corner_radius=12, border_width=1, border_color=("#aed6f1", "#1e293b"))
        card_impact.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(
            card_impact, 
            text="💡 INTEGRACIÓN DE LA TEMÁTICA EN CRONOGRULLA", 
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=("#21618c", "#38bdf8")
        ).pack(anchor="w", padx=20, pady=(15, 5))
        
        impact_text = (
            "Esta aplicación de CronoGrulla materializa directamente los objetivos de este proyecto a través de:\n\n"
            "• Monitoreo Inteligente de Micromovimientos: Clasificador SVM de Therbligs integrando inteligencia artificial.\n"
            "• Análisis Ergonómico Dinámico: Estimación de fatiga ergonómica combinando variables posturales (MediaPipe Holistic) y factores ambientales (Lux, Decibelios).\n"
            "• Optimización del Desempeño: Módulo avanzado para calcular Tiempos Estándar, Suplementos Ergonómicos e Índices de Productividad."
        )
        ctk.CTkLabel(
            card_impact, 
            text=impact_text, 
            font=ctk.CTkFont(size=12, slant="italic"),
            text_color=("#2e4053", "#94a3b8"),
            wraplength=800,
            justify="left"
        ).pack(anchor="w", padx=20, pady=(0, 15))
