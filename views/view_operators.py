import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox

class OperatorsView(ctk.CTkFrame):
    def __init__(self, master, app):
        super().__init__(master, fg_color="transparent")
        self.app = app
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        self.op_entries = []
        self.build_ui()

    def build_ui(self):
        ctk.CTkLabel(self, text="Configuración del Equipo de Trabajo", 
                     font=ctk.CTkFont(size=26, weight="bold")).pack(pady=(30, 10), padx=40, anchor="w")
        
        ctk.CTkLabel(self, text="Define cuántas personas trabajarán en la línea y asigna sus nombres para dividir automáticamente las 12 tareas.",
                     font=ctk.CTkFont(size=14), text_color="gray").pack(padx=40, anchor="w", pady=(0, 20))

        setup_frame = ctk.CTkFrame(self, fg_color=("#ffffff", "#1e293b"), corner_radius=10)
        setup_frame.pack(fill="both", expand=True, padx=40, pady=10)
        setup_frame.grid_columnconfigure((0, 1), weight=1)
        
        left_panel = ctk.CTkFrame(setup_frame, fg_color="transparent")
        left_panel.grid(row=0, column=0, padx=20, pady=20, sticky="n")
        
        ctk.CTkLabel(left_panel, text="1. Cantidad de Operarios:", font=ctk.CTkFont(size=16, weight="bold")).pack(anchor="w", pady=5)
        
        self.num_ops_var = tk.StringVar(value=str(len(self.app.operator_data)) if self.app.operator_data else "1")
        op_menu = ctk.CTkOptionMenu(left_panel, values=[str(i) for i in range(1, 13)], 
                                    variable=self.num_ops_var, command=self.generate_operator_entries,
                                    width=200, height=35)
        op_menu.pack(anchor="w", pady=(0, 20))

        ctk.CTkLabel(left_panel, text="2. Nombres de Operarios:", font=ctk.CTkFont(size=16, weight="bold")).pack(anchor="w", pady=5)
        self.entries_frame = ctk.CTkScrollableFrame(left_panel, width=300, height=250, fg_color="transparent")
        self.entries_frame.pack(anchor="w", fill="both", expand=True)
        
        self.generate_operator_entries(self.num_ops_var.get())

        ctk.CTkButton(left_panel, text="Generar / Actualizar Distribución", 
                      font=ctk.CTkFont(weight="bold"), fg_color="#3498db", hover_color="#2980b9",
                      command=self.update_distribution).pack(pady=20, fill="x")

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
            val = self.app.operator_data[i] if i < len(self.app.operator_data) else f"Operador {i+1}"
            entry = ctk.CTkEntry(self.entries_frame, placeholder_text=f"Nombre Op. {i+1}", width=250)
            entry.insert(0, val)
            entry.pack(pady=5, anchor="w")
            self.op_entries.append(entry)

    def update_distribution(self):
        names = [e.get().strip() or f"Operador {i+1}" for i, e in enumerate(self.op_entries)]
        self.app.operator_data = names
        
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
                
        self.app.line_config = new_config
        self.app.save_data()
        self.render_distribution_preview()
        messagebox.showinfo("Actualizado", "Equipo y distribución guardados correctamente. Las tareas se dividieron de forma equitativa.")

    def render_distribution_preview(self):
        for widget in self.tasks_display.winfo_children():
            widget.destroy()
            
        if not self.app.line_config:
            ctk.CTkLabel(self.tasks_display, text="Aún no hay distribución.\nConfigura el equipo a la izquierda.", text_color="gray").pack(pady=50)
            return

        for i, act_name in enumerate(self.app.ACTIVITIES):
            f = ctk.CTkFrame(self.tasks_display, fg_color=("#ffffff", "#1e293b"), corner_radius=8)
            f.pack(fill="x", pady=4, padx=5)
            op_assigned = self.app.line_config.get(str(i), "Sin asignar")
            
            ctk.CTkLabel(f, text=f"{act_name}", font=ctk.CTkFont(weight="bold")).pack(side="left", padx=10, pady=10)
            badge = ctk.CTkLabel(f, text=op_assigned, fg_color="#3498db", text_color="white", corner_radius=10, padx=10, pady=2)
            badge.pack(side="right", padx=10, pady=10)
