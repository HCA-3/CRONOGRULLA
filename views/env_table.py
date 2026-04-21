import customtkinter as ctk
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import pandas as pd
import os

class EnvTableEditor(ctk.CTkFrame):
    def __init__(self, master, unit_label="Nivel"):
        super().__init__(master, fg_color="transparent")
        self.unit_label = unit_label
        
        # Tools
        toolbar = ctk.CTkFrame(self, fg_color="transparent")
        toolbar.pack(fill="x", pady=(0, 5))
        
        ctk.CTkButton(toolbar, text="➕ Agregar", width=80, command=self.add_row).pack(side="left", padx=2)
        ctk.CTkButton(toolbar, text="➖ Quitar", width=80, fg_color="#e74c3c", command=self.remove_row).pack(side="left", padx=2)
        ctk.CTkButton(toolbar, text="🗑️ Limpiar Todo", width=100, fg_color="#c0392b", command=self.clear_all).pack(side="left", padx=10)
        ctk.CTkButton(toolbar, text="✅ Seleccionar Todo", width=120, command=self.select_all).pack(side="left", padx=2)
        
        ctk.CTkButton(toolbar, text="📂 Importar Excel", width=120, fg_color="#f39c12", command=self.import_excel).pack(side="right", padx=2)
        ctk.CTkButton(toolbar, text="💾 Exportar Excel", width=120, fg_color="#3498db", command=self.export_excel).pack(side="right", padx=2)
        
        # Table
        self.tree = ttk.Treeview(self, columns=("ID", self.unit_label, "Operador", "Lugar"), show="headings", height=5)
        self.tree.heading("ID", text="Ref/Imagen")
        self.tree.heading(self.unit_label, text=self.unit_label)
        self.tree.heading("Operador", text="Operador")
        self.tree.heading("Lugar", text="Lugar")
        
        self.tree.column("ID", width=100, anchor="center")
        self.tree.column(self.unit_label, width=100, anchor="center")
        self.tree.column("Operador", width=120, anchor="center")
        self.tree.column("Lugar", width=150, anchor="center")
        
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview", background="#2d3436", foreground="white", fieldbackground="#2d3436", rowheight=25)
        style.configure("Treeview.Heading", background="#1e272e", foreground="white")
        style.map("Treeview", background=[('selected', '#3498db')])
        
        sb = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscroll=sb.set)
        
        self.tree.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")
        self.tree.bind("<Double-1>", self.on_double_click)
        
    def get_data(self):
        data = []
        for child in self.tree.get_children():
            v = self.tree.item(child, 'values')
            # Manejamos 4 columnas ahora
            data.append({
                "id": v[0] if len(v) > 0 else "",
                "val": v[1] if len(v) > 1 else "",
                "op": v[2] if len(v) > 2 else "",
                "loc": v[3] if len(v) > 3 else ""
            })
        return data
        
    def load_data(self, data):
        for child in self.tree.get_children(): self.tree.delete(child)
        for row in data:
            # Compatibilidad si no tiene id
            self.tree.insert("", "end", values=(
                row.get("id", "-"), 
                row.get("val", ""), 
                row.get("op", ""), 
                row.get("loc", "")
            ))
            
    def add_row(self):
        self.tree.insert("", "end", values=("-", "0", "N/A", "N/A"))
        
    def remove_row(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showinfo("Selección", "Por favor selecciona una o varias filas (Ctrl/Shift para múltiples) para eliminar.")
            return
        for item in selected:
            self.tree.delete(item)

    def select_all(self):
        self.tree.selection_set(self.tree.get_children())

    def clear_all(self):
        if messagebox.askyesno("Confirmar", "¿Estás seguro de eliminar TODOS los datos ambientales de esta tabla?"):
            for child in self.tree.get_children():
                self.tree.delete(child)
            
    def import_excel(self):
        path = filedialog.askopenfilename(filetypes=[("Excel/CSV Files", "*.xlsx *.xls *.csv")])
        if not path: return
        try:
            if path.endswith('.csv'):
                df = pd.read_csv(path, sep=None, engine='python').fillna("N/A")
            else:
                df = pd.read_excel(path).fillna("N/A")
                
            for _, row in df.iterrows():
                vals = row.tolist()
                # Rellenar si faltan columnas
                while len(vals) < 4: vals.insert(0, "-") 
                self.tree.insert("", "end", values=(vals[0], vals[1], vals[2], vals[3]))
        except Exception as e:
            messagebox.showerror("Error", f"Fallo al importar: {e}")
            
    def export_excel(self):
        path = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel", "*.xlsx")])
        if not path: return
        try:
            data = self.get_data()
            df = pd.DataFrame(data)
            df.columns = ["ID/Imagen", self.unit_label, "Operador", "Lugar"]
            df.to_excel(path, index=False)
            messagebox.showinfo("Éxito", "Exportado correctamente.")
        except Exception as e:
            messagebox.showerror("Error", f"Fallo al exportar: {e}")


    def on_double_click(self, event):
        item = self.tree.selection()[0]
        col = self.tree.identify_column(event.x)
        if not col: return
        col_idx = int(col.replace('#', '')) - 1
        
        x, y, width, height = self.tree.bbox(item, col)
        val = self.tree.item(item, 'values')[col_idx]
        
        entry = tk.Entry(self.tree)
        entry.place(x=x, y=y, width=width, height=height)
        entry.insert(0, val)
        entry.focus()
        
        def save_edit(e):
            if not self.tree.exists(item): return
            try:
                values = list(self.tree.item(item, 'values'))
                values[col_idx] = entry.get()
                self.tree.item(item, values=values)
            except: pass
            if entry.winfo_exists():
                entry.destroy()
            
        entry.bind("<Return>", save_edit)
        entry.bind("<FocusOut>", save_edit)
