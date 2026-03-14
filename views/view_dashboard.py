import customtkinter as ctk

class DashboardView(ctk.CTkFrame):
    def __init__(self, master, app):
        super().__init__(master, fg_color="transparent")
        self.app = app
        self.grid_columnconfigure(0, weight=1)
        self.build_ui()

    def build_ui(self):
        header = ctk.CTkLabel(self, text="Panel de Control Principal", 
                              font=ctk.CTkFont(size=28, weight="bold"))
        header.pack(pady=(30, 20), anchor="w", padx=40)

        cards_frame = ctk.CTkFrame(self, fg_color="transparent")
        cards_frame.pack(fill="x", padx=40, pady=10)
        
        for i in range(3): cards_frame.grid_columnconfigure(i, weight=1)

        measurements = self.app.data.get("measurements", [])
        total_m = len(measurements)
        avg_time = sum(m.get("total_time", 0) for m in measurements) / total_m if total_m > 0 else 0
        total_ops = len(self.app.operator_data)

        self.create_info_card(cards_frame, "Ciclos Completados", f"{total_m} Registrados", "📊", 0, ("#3498db", "#2980b9"))
        self.create_info_card(cards_frame, "Tiempo Promedio", f"{avg_time:.2f} s", "⏱️", 1, ("#e67e22", "#d35400"))
        self.create_info_card(cards_frame, "Operarios Activos", f"{total_ops}", "👥", 2, ("#9b59b6", "#8e44ad"))

        banner = ctk.CTkFrame(self, corner_radius=10, fg_color=("#d1ecf1", "#1e3a5f"))
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
