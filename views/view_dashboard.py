import customtkinter as ctk
import numpy as np

class DashboardView(ctk.CTkFrame):
    def toggle_theme(self):
        """Toggle between dark and light appearance modes."""
        current = ctk.get_appearance_mode()
        new_mode = "Light" if current == "Dark" else "Dark"
        ctk.set_appearance_mode(new_mode)
    def __init__(self, master, app):
        super().__init__(master, fg_color="transparent")
        self.app = app
        self.grid_columnconfigure(0, weight=1)
        self.build_ui()

    def build_ui(self):
        header = ctk.CTkLabel(self, text="Panel de Control Principal", 
                              font=ctk.CTkFont(size=28, weight="bold"))
        header.pack(pady=(30, 15), anchor="w", padx=40)
        # Theme toggle switch
        theme_switch = ctk.CTkSwitch(self, text="Tema Oscuro", command=self.toggle_theme)
        # Set initial state based on current mode
        if ctk.get_appearance_mode() == "Dark":
            theme_switch.select()
        else:
            theme_switch.deselect()
        theme_switch.pack(pady=(30, 15), anchor="e", padx=40)

        cards_frame = ctk.CTkFrame(self, fg_color="transparent")
        cards_frame.pack(fill="x", padx=40, pady=5)
        
        for i in range(3): cards_frame.grid_columnconfigure(i, weight=1)

        measurements = self.app.data.get("measurements", [])
        total_m = len(measurements)
        avg_time = sum(m.get("total_time", 0) for m in measurements) / total_m if total_m > 0 else 0
        total_ops = len(self.app.operator_data)

        self.create_info_card(cards_frame, "Ciclos Completados", f"{total_m} Registrados", "📊", 0, ("#3498db", "#2980b9"))
        self.create_info_card(cards_frame, "Tiempo Promedio", f"{avg_time:.2f} s", "⏱️", 1, ("#e67e22", "#d35400"))
        self.create_info_card(cards_frame, "Operarios Activos", f"{total_ops}", "👥", 2, ("#9b59b6", "#8e44ad"))

        banner = ctk.CTkFrame(self, corner_radius=10, fg_color=("#d1ecf1", "#1e3a5f"))
        banner.pack(fill="x", padx=40, pady=(20, 10))
        
        b_title = ctk.CTkLabel(banner, text="Resumen del Sistema de Balanceo", font=ctk.CTkFont(size=16, weight="bold"), text_color=("#0c5460", "#63b3ed"))
        b_title.pack(pady=(10, 2), padx=20, anchor="w")
        
        b_text = ("• Las tareas se han dividido automáticamente en base a la cantidad de operarios asignados.\n"
                  "• El cronómetro guiará paso a paso indicando el operador responsable de la tarea actual.\n"
                  "• Puedes registrar observaciones de calidad finalizado cada paso si ocurre un contratiempo.")
        ctk.CTkLabel(banner, text=b_text, font=ctk.CTkFont(size=12), justify="left", text_color=("#0c5460", "#e2e8f0")).pack(pady=(0, 10), padx=20, anchor="w")

        # ---- NUEVO: PANEL DE WIDGETS ERGONÓMICOS ----
        widgets_frame = ctk.CTkFrame(self, fg_color="transparent")
        widgets_frame.pack(fill="both", expand=True, padx=40, pady=(10, 20))
        widgets_frame.grid_columnconfigure(0, weight=1)
        widgets_frame.grid_columnconfigure(1, weight=1)
        
        # Panel Izquierdo: Semáforo Ergonómico
        ergo_card = ctk.CTkFrame(widgets_frame, corner_radius=15, fg_color=("#ffffff", "#1b2430"))
        ergo_card.grid(row=0, column=0, padx=(0, 10), sticky="nsew", ipady=10)
        
        ctk.CTkLabel(ergo_card, text="🚦 Semáforo Ergonómico (Higiene)", 
                     font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(10, 5), padx=20, anchor="w")
        
        # Calcular estado ergonómico
        all_lux = []
        for m in measurements:
            for l in m.get("lux_data", []):
                try: all_lux.append(float(l.get("val", 0)))
                except: pass
        avg_lux = np.mean(all_lux) if all_lux else 350.0
        
        all_angles = []
        for m in measurements:
            for s in m.get("splits", []):
                ang = s.get("avg_angle", 0)
                if ang > 0: all_angles.append(ang)
        max_angle = max(all_angles) if all_angles else 0.0
        
        # Reglas simples del semáforo
        if max_angle >= 70:
            ergo_status = "🔴 Riesgo Alto"
            ergo_color = "#e74c3c"
            ergo_desc = "Mala postura frecuente detectada (Ángulo > 70°).\nSe sugiere ajustar altura del puesto de trabajo."
        elif total_m > 8:
            ergo_status = "🟡 Riesgo Medio"
            ergo_color = "#f1c40f"
            ergo_desc = "Repetitividad elevada (Ciclos > 8).\nSe recomiendan pausas activas programadas."
        elif avg_lux >= 450:
            ergo_status = "🟢 Bajo Riesgo"
            ergo_color = "#2ecc71"
            ergo_desc = "Condiciones óptimas detectadas.\nIluminación excelente y posturas neutrales."
        else:
            ergo_status = "🟢 Bajo Riesgo"
            ergo_color = "#2ecc71"
            ergo_desc = "Nivel ergonómico aceptable.\nPosturas confortables observadas en el ciclo."

        status_lbl = ctk.CTkLabel(ergo_card, text=ergo_status, font=ctk.CTkFont(size=22, weight="bold"), text_color=ergo_color)
        status_lbl.pack(pady=5)
        
        desc_lbl = ctk.CTkLabel(ergo_card, text=ergo_desc, font=ctk.CTkFont(size=12), justify="center")
        desc_lbl.pack(pady=(5, 10), padx=20)
        
        # Panel Derecho: Top Tareas más Fatigantes
        fatigue_card = ctk.CTkFrame(widgets_frame, corner_radius=15, fg_color=("#ffffff", "#1b2430"))
        fatigue_card.grid(row=0, column=1, padx=(10, 0), sticky="nsew", ipady=10)
        
        ctk.CTkLabel(fatigue_card, text="🔥 Top Tareas más Fatigantes", 
                     font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(10, 5), padx=20, anchor="w")
        
        # Calcular top tareas fatigantes
        task_fatigue = {}
        for m in measurements:
            for s in m.get("splits", []):
                act = s.get("activity", "Tarea")
                dur = s.get("duration", 0)
                ang = s.get("avg_angle", 0)
                if dur > 0:
                    if act not in task_fatigue:
                        task_fatigue[act] = []
                    fatigue_index = dur * (1.0 + (ang / 90.0))
                    task_fatigue[act].append(fatigue_index)
                    
        fatigue_ranked = []
        for act, indices in task_fatigue.items():
            fatigue_ranked.append((act, np.mean(indices)))
            
        fatigue_ranked.sort(key=lambda x: x[1], reverse=True)
        top_fatigantes = [item[0] for item in fatigue_ranked[:3]]
        
        if not top_fatigantes:
            top_fatigantes = ["Repetir cara posterior", "Marcar patas inf.", "Solapas al centro"]
            
        for rank, task in enumerate(top_fatigantes, 1):
            t_row = ctk.CTkFrame(fatigue_card, fg_color="transparent")
            t_row.pack(fill="x", padx=20, pady=3)
            
            num_lbl = ctk.CTkLabel(t_row, text=f"#{rank}", font=ctk.CTkFont(size=13, weight="bold"), text_color="#e74c3c", width=25)
            num_lbl.pack(side="left")
            
            name_lbl = ctk.CTkLabel(t_row, text=task[:40], font=ctk.CTkFont(size=12))
            name_lbl.pack(side="left", padx=5)

    def create_info_card(self, parent, title, value, icon, col, colors):
        card = ctk.CTkFrame(parent, corner_radius=15, fg_color=colors[1])
        card.grid(row=0, column=col, padx=10, sticky="nsew", ipady=20)
        
        ctk.CTkLabel(card, text=icon, font=ctk.CTkFont(size=40)).pack(pady=(15, 5))
        ctk.CTkLabel(card, text=value, font=ctk.CTkFont(size=32, weight="bold"), text_color="white").pack()
        ctk.CTkLabel(card, text=title, font=ctk.CTkFont(size=14), text_color="#ecf0f1").pack(pady=(5, 10))

