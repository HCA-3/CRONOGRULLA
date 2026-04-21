import customtkinter as ctk
from views.view_timer import TimerView
from views.view_media import MediaGalleryView
from views.view_comparison import ComparisonView
from views.view_sensor_data import SensorDataView
import json
import os

class CronoGrullaApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("CronoGrulla V10 - Sistema de Tiempos y Métodos")
        self.geometry("1100x700")
        
        # Datos persistentes
        self.data_path = "craneflow_data.json"
        self.load_data()
        
        # Layout
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        self.sidebar = ctk.CTkFrame(self, width=220, corner_radius=0, fg_color=("#f1f5f9", "#0f172a"))
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        
        ctk.CTkLabel(self.sidebar, text="🤖 CRONOGRULLA", font=ctk.CTkFont(size=22, weight="bold")).pack(pady=30)
        
        self.btn_timer = ctk.CTkButton(self.sidebar, text="⏲ CRONÓMETRO", height=45, fg_color="transparent", text_color=("#334155", "#cbd5e1"), anchor="w", command=self.show_timer)
        self.btn_timer.pack(fill="x", padx=10, pady=5)
        
        self.btn_media.pack(fill="x", padx=10, pady=5)
        
        self.btn_sensor = ctk.CTkButton(self.sidebar, text="📡 SENSOR IA", height=45, fg_color="transparent", text_color=("#334155", "#cbd5e1"), anchor="w", command=self.show_sensor_data)
        self.btn_sensor.pack(fill="x", padx=10, pady=5)
        
        self.btn_comp = ctk.CTkButton(self.sidebar, text="📊 COMPARATIVA", height=45, fg_color="transparent", text_color=("#334155", "#cbd5e1"), anchor="w", command=self.show_comparison)
        self.btn_comp.pack(fill="x", padx=10, pady=5)
        
        self.container = ctk.CTkFrame(self, fg_color="transparent")
        self.container.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)
        self.container.grid_columnconfigure(0, weight=1)
        self.container.grid_rowconfigure(0, weight=1)
        
        self.views = {}
        self.show_timer()

    def load_data(self):
        if os.path.exists(self.data_path):
            with open(self.data_path, "r") as f: self.data = json.load(f)
        else:
            self.data = {"measurements": [], "operators": ["Laura", "Diego", "David"]}

    def show_timer(self):
        self.switch_view("timer", TimerView)

    def show_media(self):
        self.switch_view("media", MediaGalleryView)

    def show_comparison(self):
        self.switch_view("comparison", ComparisonView)

    def show_sensor_data(self):
        self.switch_view("sensor_data", SensorDataView)

    def switch_view(self, name, view_class):
        for v in self.views.values(): v.grid_forget()
        if name not in self.views:
            self.views[name] = view_class(self.container, self)
        self.views[name].grid(row=0, column=0, sticky="nsew")

if __name__ == "__main__":
    app = CronoGrullaApp()
    app.mainloop()
