import customtkinter as ctk
import tkinter as tk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

class StatsView(ctk.CTkFrame):
    def __init__(self, master, app):
        super().__init__(master, fg_color="transparent")
        self.app = app
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        self.build_ui()

    def build_ui(self):
        ctk.CTkLabel(self, text="Análisis de Rendimiento", font=ctk.CTkFont(size=26, weight="bold")).pack(pady=20, padx=40, anchor="w")

        self.stats_selector_var = tk.StringVar(value=self.app.current_model_name)
        selector = ctk.CTkSegmentedButton(self, values=list(self.app.models.keys()), 
                                         variable=self.stats_selector_var, command=self.update_stats_view)
        selector.pack(fill="x", padx=40, pady=(0, 10))

        self.stats_container = ctk.CTkFrame(self, fg_color="transparent")
        self.stats_container.pack(fill="both", expand=True, padx=40, pady=(0, 20))
        
        self.update_stats_view(self.app.current_model_name)

    def update_stats_view(self, model_name):
        for widget in self.stats_container.winfo_children():
            widget.destroy()

        measurements = [m for m in self.app.data.get("measurements", []) if m.get("model") == model_name or (not m.get("model") and model_name == "Grulla Clásica")]
        if not measurements:
            ctk.CTkLabel(self.stats_container, text=f"No hay datos suficientes para '{model_name}'.", text_color="gray", font=ctk.CTkFont(size=14)).pack(pady=50)
            return

        chart_frame = ctk.CTkFrame(self.stats_container, fg_color="#ffffff", corner_radius=15)
        chart_frame.pack(fill="both", expand=True, pady=10)

        fig, ax = plt.subplots(figsize=(10, 5), dpi=100)
        
        num_steps = len(self.app.models[model_name]["activities"])
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
