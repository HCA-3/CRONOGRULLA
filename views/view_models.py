import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox, filedialog
import os
import shutil
import sys
import subprocess

class ModelsView(ctk.CTkFrame):
    def __init__(self, master, app):
        super().__init__(master, fg_color="transparent")
        self.app = app
        self.grid_columnconfigure(0, weight=1)
        self.build_ui()

    def build_ui(self):
        header = ctk.CTkLabel(self, text="Gestión de Modelos de Origami", 
                               font=ctk.CTkFont(size=28, weight="bold"))
        header.pack(pady=(30, 10), anchor="w", padx=40)

        new_model_frame = ctk.CTkFrame(self, corner_radius=10)
        new_model_frame.pack(fill="x", padx=40, pady=10)
        
        ctk.CTkLabel(new_model_frame, text="Crear Nuevo Modelo:", font=ctk.CTkFont(weight="bold")).pack(side="left", padx=20, pady=20)
        
        self.new_model_name_entry = ctk.CTkEntry(new_model_frame, placeholder_text="Nombre del Modelo (ej: Grulla Pro)", width=300)
        self.new_model_name_entry.pack(side="left", padx=10)
        
        ctk.CTkButton(new_model_frame, text="Añadir Pasos", command=self.open_steps_editor).pack(side="left", padx=10)

        list_label = ctk.CTkLabel(self, text="Modelos Registrados:", font=ctk.CTkFont(size=18, weight="bold"))
        list_label.pack(pady=(20, 10), anchor="w", padx=40)

        self.models_list_frame = ctk.CTkScrollableFrame(self, height=400)
        self.models_list_frame.pack(fill="both", expand=True, padx=40, pady=10)
        
        self.render_models_list()

    def render_models_list(self):
        for widget in self.models_list_frame.winfo_children():
            widget.destroy()
            
        for model_name in self.app.models.keys():
            row = ctk.CTkFrame(self.models_list_frame, fg_color=("#ffffff", "#1e293b"), corner_radius=8)
            row.pack(fill="x", pady=5, padx=5)
            
            ctk.CTkLabel(row, text=model_name, font=ctk.CTkFont(weight="bold")).pack(side="left", padx=20, pady=15)
            
            btn_frame = ctk.CTkFrame(row, fg_color="transparent")
            btn_frame.pack(side="right", padx=10)
            
            if model_name == self.app.current_model_name:
                badge = ctk.CTkLabel(btn_frame, text="ACTIVO", fg_color="#27ae60", text_color="white", corner_radius=10, padx=10)
                badge.pack(side="left", padx=5)
            else:
                ctk.CTkButton(btn_frame, text="Activar", width=80, command=lambda m=model_name: self.activate_model(m)).pack(side="left", padx=5)
            
            ctk.CTkButton(btn_frame, text="Eliminar", width=80, fg_color="#e74c3c", hover_color="#c0392b", 
                          command=lambda m=model_name: self.delete_model(m)).pack(side="left", padx=5)
            
            ctk.CTkButton(btn_frame, text="Editar Pasos", width=100, fg_color="#f39c12", hover_color="#e67e22",
                          command=lambda m=model_name: self.open_edit_steps_editor(m)).pack(side="left", padx=10)

            pdf_path = self.app.models[model_name].get("pdf_guide")
            if pdf_path and os.path.exists(pdf_path):
                ctk.CTkButton(btn_frame, text="📄 Ver PDF", width=80, fg_color="#34495e", 
                              command=lambda m=model_name: self.open_pdf_guide(m)).pack(side="left", padx=5)
            
            ctk.CTkButton(btn_frame, text="🔼 Subir PDF", width=80, fg_color="#95a5a6", 
                          command=lambda m=model_name: self.upload_pdf_guide(m)).pack(side="left", padx=5)

    def activate_model(self, model_name):
        self.app.current_model_name = model_name
        self.app.update_current_model_vars()
        self.app.save_data()
        self.render_models_list()
        messagebox.showinfo("Modelo Activo", f"Se ha activado el modelo: {model_name}")

    def delete_model(self, model_name):
        if model_name == "Grulla Clásica":
            messagebox.showwarning("Acción no permitida", "No puedes eliminar el modelo base.")
            return
        if messagebox.askyesno("Confirmar", f"¿Eliminar el modelo {model_name}?"):
            if self.app.current_model_name == model_name:
                self.activate_model("Grulla Clásica")
            del self.app.models[model_name]
            self.app.save_data()
            self.render_models_list()

    def open_steps_editor(self):
        name = self.new_model_name_entry.get().strip()
        if not name:
            messagebox.showwarning("Falta nombre", "Asigna un nombre al modelo primero.")
            return
        if name in self.app.models:
            messagebox.showwarning("Nombre duplicado", "Ya existe un modelo con ese nombre.")
            return
            
        self.steps_window = ctk.CTkToplevel(self.app)
        self.steps_window.title(f"Configurar pasos: {name}")
        self.steps_window.geometry("850x700")
        self.steps_window.grab_set()
        
        ctk.CTkLabel(self.steps_window, text=f"Definiendo pasos para: {name}", font=ctk.CTkFont(size=18, weight="bold")).pack(pady=10)
        ctk.CTkLabel(self.steps_window, text="Solo se guardarán los pasos que tengan nombre o descripción.", font=ctk.CTkFont(size=12, slant="italic")).pack(pady=5)
        
        self.scroll_steps = ctk.CTkScrollableFrame(self.steps_window)
        self.scroll_steps.pack(fill="both", expand=True, padx=20, pady=10)
        
        self.step_entries = []
        self.add_step_row()

        btn_frame = ctk.CTkFrame(self.steps_window, fg_color="transparent")
        btn_frame.pack(pady=10)

        ctk.CTkButton(btn_frame, text="+ Añadir un Paso", fg_color="#27ae60", hover_color="#2ecc71",
                      command=self.add_step_row).pack(side="left", padx=10)

        ctk.CTkButton(btn_frame, text="Guardar Modelo", font=ctk.CTkFont(weight="bold"),
                      command=lambda n=name: self.save_new_model(n)).pack(side="left", padx=10)

    def add_step_row(self, initial_name="", initial_desc=""):
        idx = len(self.step_entries)
        f = ctk.CTkFrame(self.scroll_steps, fg_color="transparent")
        f.pack(fill="x", pady=5)
        
        ctk.CTkLabel(f, text=f"Paso {idx+1}:", width=60).pack(side="left", padx=5)
        name_ent = ctk.CTkEntry(f, placeholder_text="Nombre del paso", width=200)
        if initial_name: name_ent.insert(0, initial_name)
        name_ent.pack(side="left", padx=5)
        
        desc_ent = ctk.CTkEntry(f, placeholder_text="Instrucción detallada", width=400)
        if initial_desc: desc_ent.insert(0, initial_desc)
        desc_ent.pack(side="left", padx=5)
        
        self.step_entries.append((name_ent, desc_ent))

    def save_new_model(self, name):
        acts = []
        descs = []
        for i, (ne, de) in enumerate(self.step_entries):
            n = ne.get().strip()
            d = de.get().strip()
            if n or d:
                acts.append(n or f"Paso {len(acts)+1}")
                descs.append(d or "Sin descripción")
        
        if not acts:
            messagebox.showwarning("Sin pasos", "Debes agregar al menos un paso con información.")
            return
            
        self.app.models[name] = {
            "activities": acts,
            "descriptions": descs
        }
        self.app.save_data()
        self.steps_window.destroy()
        if hasattr(self, 'new_model_name_entry'):
            self.new_model_name_entry.delete(0, 'end')
        self.render_models_list()
        messagebox.showinfo("Guardado", f"Modelo {name} creado exitosamente con {len(acts)} pasos.")

    def open_edit_steps_editor(self, model_name):
        model_data = self.app.models.get(model_name)
        if not model_data: return
        
        self.steps_window = ctk.CTkToplevel(self.app)
        self.steps_window.title(f"Editar Pasos: {model_name}")
        self.steps_window.geometry("850x700")
        self.steps_window.grab_set()
        
        ctk.CTkLabel(self.steps_window, text=f"Editando pasos para: {model_name}", font=ctk.CTkFont(size=18, weight="bold")).pack(pady=10)
        
        self.scroll_steps = ctk.CTkScrollableFrame(self.steps_window)
        self.scroll_steps.pack(fill="both", expand=True, padx=20, pady=10)
        
        self.step_entries = []
        acts = model_data["activities"]
        descs = model_data["descriptions"]
        
        for i in range(len(acts)):
            self.add_step_row(acts[i], descs[i])

        btn_frame = ctk.CTkFrame(self.steps_window, fg_color="transparent")
        btn_frame.pack(pady=10)

        ctk.CTkButton(btn_frame, text="+ Añadir un Paso", fg_color="#27ae60", hover_color="#2ecc71",
                      command=self.add_step_row).pack(side="left", padx=10)

        ctk.CTkButton(btn_frame, text="Actualizar Modelo", font=ctk.CTkFont(weight="bold"),
                      command=lambda n=model_name: self.save_edited_model(n)).pack(side="left", padx=10)

    def save_edited_model(self, model_name):
        acts = []
        descs = []
        for ne, de in self.step_entries:
            n = ne.get().strip()
            d = de.get().strip()
            if n or d:
                acts.append(n or f"Paso {len(acts)+1}")
                descs.append(d or "Sin descripción")

        if not acts:
            messagebox.showwarning("Sin pasos", "No puedes dejar el modelo sin pasos.")
            return

        self.app.models[model_name] = {
            "activities": acts,
            "descriptions": descs
        }
        if self.app.current_model_name == model_name:
            self.app.update_current_model_vars()
        self.app.save_data()
        self.steps_window.destroy()
        self.render_models_list()
        messagebox.showinfo("Actualizado", f"Modelo {model_name} actualizado con {len(acts)} pasos.")

    def upload_pdf_guide(self, model_name):
        file_path = filedialog.askopenfilename(
            title="Seleccionar Guía PDF para " + model_name,
            filetypes=[("Archivos PDF", "*.pdf")]
        )
        if not file_path:
            return
        
        try:
            safe_name = "".join([c if c.isalnum() else "_" for c in model_name]) + ".pdf"
            dest_path = os.path.join(self.app.pdf_folder, safe_name)
            
            shutil.copy2(file_path, dest_path)
            self.app.models[model_name]["pdf_guide"] = dest_path
            self.app.save_data()
            self.render_models_list()
            messagebox.showinfo("Éxito", f"Guía PDF cargada para {model_name}")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo copiar el archivo: {e}")

    def open_pdf_guide(self, model_name):
        pdf_path = self.app.models.get(model_name, {}).get("pdf_guide")
        if pdf_path and os.path.exists(pdf_path):
            try:
                if os.name == 'nt':
                    os.startfile(pdf_path)
                else: 
                    opener = "open" if sys.platform == "darwin" else "xdg-open"
                    subprocess.call([opener, pdf_path])
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo abrir el PDF: {e}")
        else:
            messagebox.showwarning("Sin Archivo", "No hay una guía PDF cargada para este modelo.")
