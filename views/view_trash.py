import customtkinter as ctk
import json
import os
from tkinter import messagebox

class TrashView(ctk.CTkFrame):
    def __init__(self, master, app):
        super().__init__(master, fg_color="transparent")
        self.app = app
        self.build_ui()

    def build_ui(self):
        # Header
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=20)
        
        ctk.CTkLabel(header, text="🗑️ PAPELERA DE RECICLAJE", 
                     font=ctk.CTkFont(size=24, weight="bold")).pack(side="left")
        
        ctk.CTkButton(header, text="Vaciar Papelera", fg_color="#e74c3c", 
                      hover_color="#c0392b", command=self.empty_trash).pack(side="right", padx=10)

        # Contenedor de elementos
        self.scroll = ctk.CTkScrollableFrame(self, fg_color=("#ffffff", "#1e293b"), corner_radius=15)
        self.scroll.pack(fill="both", expand=True, padx=20, pady=10)
        
        self.refresh_trash()

    def refresh_trash(self):
        for widget in self.scroll.winfo_children():
            widget.destroy()
        
        trash_data = self.app.data.get("trash", [])
        
        if not trash_data:
            ctk.CTkLabel(self.scroll, text="La papelera está vacía.", 
                         font=ctk.CTkFont(slant="italic")).pack(pady=40)
            return

        for i, item in enumerate(reversed(trash_data)):
            card = ctk.CTkFrame(self.scroll, fg_color=("#f8f9fa", "#2d3748"), corner_radius=10)
            card.pack(fill="x", pady=5, padx=5)
            
            info_txt = f"Estudio #{item.get('id')} - {item.get('timestamp')} | {len(item.get('results', []))} ciclos"
            ctk.CTkLabel(card, text=info_txt, font=ctk.CTkFont(weight="bold")).pack(side="left", padx=15, pady=10)
            
            # Botones
            btn_f = ctk.CTkFrame(card, fg_color="transparent")
            btn_f.pack(side="right", padx=10)
            
            ctk.CTkButton(btn_f, text="Restaurar", width=100, fg_color="#27ae60", 
                          command=lambda x=item: self.restore_item(x)).pack(side="left", padx=5)
            
            ctk.CTkButton(btn_f, text="Borrar Def.", width=80, fg_color="transparent", 
                          text_color="#e74c3c", border_width=1, border_color="#e74c3c",
                          command=lambda idx=len(trash_data)-1-i: self.permanent_delete(idx)).pack(side="left", padx=5)

    def restore_item(self, item):
        if "trash" not in self.app.data: self.app.data["trash"] = []
        if "measurements" not in self.app.data: self.app.data["measurements"] = []
        
        # Mover de vuelta a measurements
        self.app.data["measurements"].append(item)
        self.app.data["trash"].remove(item)
        
        self.app.save_data()
        self.refresh_trash()
        messagebox.showinfo("Éxito", "Estudio restaurado correctamente.")

    def permanent_delete(self, idx):
        if messagebox.askyesno("Confirmar", "¿Eliminar permanentemente este registro?"):
            self.app.data["trash"].pop(idx)
            self.app.save_data()
            self.refresh_trash()

    def empty_trash(self):
        if messagebox.askyesno("Confirmar", "¿Vaciar toda la papelera? Esta acción no se puede deshacer."):
            self.app.data["trash"] = []
            self.app.save_data()
            self.refresh_trash()
