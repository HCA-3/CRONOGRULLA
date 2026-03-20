import customtkinter as ctk

class InfoView(ctk.CTkFrame):
    def __init__(self, master, app):
        super().__init__(master, fg_color="transparent")
        self.app = app
        self.grid_columnconfigure(0, weight=1)
        self.build_ui()

    def build_ui(self):
        # Header
        header = ctk.CTkLabel(self, text="Información del Proyecto", 
                              font=ctk.CTkFont(size=28, weight="bold"))
        header.pack(pady=(30, 10), anchor="w", padx=40)

        sub_header = ctk.CTkLabel(self, text="CronoGrulla | Gestión de Ingeniería de Métodos", 
                                 font=ctk.CTkFont(size=16), text_color="gray")
        sub_header.pack(pady=(0, 30), anchor="w", padx=40)

        # Content Frame
        content_frame = ctk.CTkFrame(self, fg_color=("#ffffff", "#1e293b"), corner_radius=15)
        content_frame.pack(fill="both", expand=True, padx=40, pady=10)
        
        # Authors Section
        authors_title = ctk.CTkLabel(content_frame, text="Equipo de Desarrollo", 
                                    font=ctk.CTkFont(size=20, weight="bold"))
        authors_title.pack(pady=(30, 20), padx=30, anchor="w")

        authors = [
            ("Ing. David Santiago Castelblanco Artunduaga", "ID: 5201057"),
            ("Ing. Juan Diego Escobar Duarte", "ID: 5200969"),
            ("Ing. Laura Vanessa Cespedes Acosta", "ID: 5200901")
        ]

        for name, student_id in authors:
            author_box = ctk.CTkFrame(content_frame, fg_color="transparent")
            author_box.pack(fill="x", padx=30, pady=10)
            
            ctk.CTkLabel(author_box, text="👤", font=ctk.CTkFont(size=24)).pack(side="left", padx=(0, 15))
            
            text_container = ctk.CTkFrame(author_box, fg_color="transparent")
            text_container.pack(side="left", fill="both")
            
            ctk.CTkLabel(text_container, text=name, 
                        font=ctk.CTkFont(size=16, weight="bold")).pack(anchor="w")
            ctk.CTkLabel(text_container, text=student_id, 
                        font=ctk.CTkFont(size=14), text_color="gray").pack(anchor="w")

        # Project Details
        details_title = ctk.CTkLabel(content_frame, text="Detalles del Proyecto", 
                                    font=ctk.CTkFont(size=20, weight="bold"))
        details_title.pack(pady=(30, 10), padx=30, anchor="w")

        details_text = ("Este software ha sido diseñado como una herramienta integral para el estudio de tiempos "
                       "y movimientos, facilitando el balanceo de líneas en procesos de manufactura (ej. Grullas de Origami). "
                       "Permite la recoleccion de datos en tiempo real, análisis estadístico y generación de informes automáticos.")
        
        details_label = ctk.CTkLabel(content_frame, text=details_text, 
                                    font=ctk.CTkFont(size=14), justify="left", wraplength=700)
        details_label.pack(pady=(0, 30), padx=30, anchor="w")

        # Footer
        version_label = ctk.CTkLabel(self, text="Versión 1.0.0 | © 2026 Equipo CronoGrulla", 
                                    font=ctk.CTkFont(size=12), text_color="gray")
        version_label.pack(pady=20)
