import customtkinter as ctk
import tkinter as tk
from tkinter import ttk, messagebox

class TablesView(ctk.CTkFrame):
    def __init__(self, master, app):
        super().__init__(master, fg_color="transparent")
        self.app = app
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        self.build_ui()

    def build_ui(self):
        header_f = ctk.CTkFrame(self, fg_color="transparent")
        header_f.pack(fill="x", padx=40, pady=20)
        ctk.CTkLabel(header_f, text="Matriz de Tiempos Recolectados", font=ctk.CTkFont(size=26, weight="bold")).pack(side="left")
        
        ctk.CTkButton(header_f, text="Eliminar Último", fg_color="#e74c3c", command=self.delete_last_measurement).pack(side="right")

        self.table_selector_var = tk.StringVar(value=self.app.current_model_name)
        selector = ctk.CTkSegmentedButton(self, values=list(self.app.models.keys()), 
                                         variable=self.table_selector_var, command=self.update_table_view)
        selector.pack(fill="x", padx=40, pady=(0, 10))

        self.table_container = ctk.CTkFrame(self, fg_color="transparent")
        self.table_container.pack(fill="both", expand=True, padx=40, pady=(0, 20))
        
        self.update_table_view(self.app.current_model_name)

    def update_table_view(self, model_name):
        for widget in self.table_container.winfo_children():
            widget.destroy()
            
        table_f = ctk.CTkFrame(self.table_container, corner_radius=10)
        table_f.pack(fill="both", expand=True)

        num_steps = len(self.app.models[model_name]["activities"])
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

        measurements = [m for m in self.app.data.get("measurements", []) if m.get("model") == model_name or (not m.get("model") and model_name == "Grulla Clásica")]
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
        measurements = self.app.data.get("measurements", [])
        if not measurements: return
        if messagebox.askyesno("Confirmar", "¿Eliminar el último ciclo registrado?"):
            measurements.pop()
            self.app.save_data()
            self.update_table_view(self.table_selector_var.get())
