import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
import time
import os
from datetime import datetime

class TimerView(ctk.CTkFrame):
    def __init__(self, master, app):
        super().__init__(master, fg_color="transparent")
        self.app = app
        self.grid_columnconfigure(0, weight=1)
        
        self.start_time = None
        self.last_split_time = 0
        self.current_cycle_splits = []
        self.running = False
        self.current_activity_index = 0
        
        self.build_ui()

    def build_ui(self):
        if not self.app.line_config:
            messagebox.showwarning("Falta Configuración", "Por favor configura el equipo y la distribución de tareas primero.")
            self.app.show_operators_setup()
            return

        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=40, pady=(20, 0))
        
        cycle_num = len(self.app.data.get("measurements", [])) + 1
        ctk.CTkLabel(header, text=f"Estudio de Tiempos - Ciclo #{cycle_num}", font=ctk.CTkFont(size=26, weight="bold")).pack(side="left")

        self.content_container = ctk.CTkFrame(self, fg_color="transparent")
        self.content_container.pack(fill="both", expand=True, padx=40, pady=(10, 20))
        self.content_container.grid_columnconfigure(0, weight=1)
        self.content_container.grid_columnconfigure(1, weight=0)
        self.content_container.grid_rowconfigure(0, weight=1)

        self.timer_column = ctk.CTkFrame(self.content_container, fg_color="transparent")
        self.timer_column.grid(row=0, column=0, sticky="nsew", padx=(0, 10))

        model_selector_frame = ctk.CTkFrame(self.timer_column, fg_color="transparent")
        model_selector_frame.pack(fill="x", pady=(0, 10))
        ctk.CTkLabel(model_selector_frame, text="Seleccionar Modelo:", font=ctk.CTkFont(weight="bold")).pack(side="left", padx=10)
        
        self.timer_model_var = tk.StringVar(value=self.app.current_model_name)
        self.timer_model_menu = ctk.CTkOptionMenu(model_selector_frame, values=list(self.app.models.keys()), 
                                                variable=self.timer_model_var, command=self.app.change_model_from_menu)
        self.timer_model_menu.pack(side="left", padx=10)

        pdf_path = self.app.models.get(self.app.current_model_name, {}).get("pdf_guide")
        if pdf_path and os.path.exists(pdf_path):
            ctk.CTkButton(model_selector_frame, text="📄 Ver Guía Técnica PDF", 
                          fg_color="#3498db", hover_color="#2980b9", width=180,
                          command=lambda: self.app.open_pdf_guide(self.app.current_model_name)).pack(side="left", padx=20)

        self.qc_column = ctk.CTkFrame(self.content_container, corner_radius=15, fg_color=("#ffffff", "#1e293b"))

        timer_frame = ctk.CTkFrame(self.timer_column, corner_radius=20, fg_color=("#ffffff", "#1e293b"))
        timer_frame.pack(pady=10, fill="x", ipady=20)
        
        self.op_target_lbl = ctk.CTkLabel(timer_frame, text="Preparado para iniciar", font=ctk.CTkFont(size=20, slant="italic"), text_color="#f39c12")
        self.op_target_lbl.pack(pady=(10, 0))
        
        self.timer_label = ctk.CTkLabel(timer_frame, text="00:00.00", font=ctk.CTkFont(size=90, weight="bold", family="Courier New"), text_color="#3498db")
        self.timer_label.pack(pady=10)

        controls = ctk.CTkFrame(timer_frame, fg_color="transparent")
        controls.pack()

        self.btn_start = ctk.CTkButton(controls, text="▶ INICIAR CICLO", font=ctk.CTkFont(size=18, weight="bold"),
                                       height=50, width=250, fg_color="#27ae60", hover_color="#2ecc71",
                                       command=self.start_timer)
        self.btn_start.pack(side="left", padx=15)

        self.btn_cancel = ctk.CTkButton(controls, text="⏹ CANCELAR", font=ctk.CTkFont(size=16),
                                        height=50, width=150, fg_color="#e74c3c", hover_color="#c0392b",
                                        command=self.reset_timer, state="disabled")
        self.btn_cancel.pack(side="left", padx=15)

        self.act_frame = ctk.CTkScrollableFrame(self.timer_column)
        self.act_frame.pack(fill="both", expand=True, pady=(0, 10))
        
        self.act_widgets = []
        for i, act_name in enumerate(self.app.ACTIVITIES):
            f = ctk.CTkFrame(self.act_frame, fg_color=("#ecf0f1", "#0f172a"), corner_radius=10)
            f.pack(fill="x", pady=5, padx=10)
            f.grid_columnconfigure(1, weight=1)
            
            lbl_title = ctk.CTkLabel(f, text=str(i+1), font=ctk.CTkFont(weight="bold", size=18), width=30)
            lbl_title.grid(row=0, column=0, padx=10, pady=15)
            
            op = self.app.line_config.get(str(i), "")
            info_text = f"{act_name}\nResponable: {op}"
            lbl_info = ctk.CTkLabel(f, text=info_text, justify="left", font=ctk.CTkFont(size=14))
            lbl_info.grid(row=0, column=1, sticky="w", padx=10)
            
            btn_done = ctk.CTkButton(f, text="Finalizar Tarea", state="disabled", width=120, height=35,
                                     command=lambda idx=i: self.record_split(idx))
            btn_done.grid(row=0, column=2, padx=15)
            
            self.act_widgets.append({"frame": f, "title": lbl_title, "btn": btn_done, "op": op})

    def start_timer(self):
        if self.running: return
        self.running = True
        self.start_time = time.time()
        self.last_split_time = self.start_time
        self.current_cycle_splits = []
        self.current_activity_index = 0
        
        self.btn_start.configure(state="disabled", fg_color="gray")
        self.btn_cancel.configure(state="normal")
        
        self.update_clock()
        self.highlight_activity(0)

    def update_clock(self):
        if self.running:
            elapsed = time.time() - self.start_time
            mins, secs = divmod(elapsed, 60)
            cents = (elapsed % 1) * 100
            self.timer_label.configure(text=f"{int(mins):02d}:{int(secs):02d}.{int(cents):02d}")
            self.after(20, self.update_clock)

    def highlight_activity(self, index):
        for i, data in enumerate(self.act_widgets):
            if i == index:
                data["frame"].configure(border_width=2, border_color="#3498db")
                data["btn"].configure(state="normal", fg_color="#3498db")
                self.op_target_lbl.configure(text=f"Turno de: {data['op']} | Realizando tarea {i+1}")
                try:
                    self.act_frame._parent_canvas.yview_moveto(i / len(self.app.ACTIVITIES))
                except: pass
            else:
                data["frame"].configure(border_width=0)
                data["btn"].configure(state="disabled", fg_color="gray")

    def record_split(self, index):
        now = time.time()
        duration = now - self.last_split_time
        self.last_split_time = now
        
        self.act_widgets[index]["btn"].configure(state="disabled", fg_color="gray")

        self.qc_column.grid(row=0, column=1, sticky="nsew", padx=(10, 0))
        self.content_container.grid_columnconfigure(1, weight=1)
        
        for widget in self.qc_column.winfo_children():
            widget.destroy()

        ctk.CTkLabel(self.qc_column, text=f"Control Tarea {index+1}", font=ctk.CTkFont(size=20, weight="bold")).pack(pady=(20, 5))
        ctk.CTkLabel(self.qc_column, text="Problemas (Opcional):", text_color="gray").pack(pady=(0, 10))

        common_errors = [
             "Doblez incorrecto / asimétrico",
             "Falta de concentración",
             "Se saltó instrucción",
             "Demora externa",
             "Aplicó demasiada fuerza",
             "Equivocó el sentido del pliegue",
             "Dificultad de motricidad",
             "Duda o pausa excesiva",
             "Mala postura ergonómica",
             "Desorden en estación"
        ]

        scroll_errors = ctk.CTkScrollableFrame(self.qc_column)
        scroll_errors.pack(fill="both", expand=True, padx=20, pady=5)

        self.error_vars = []
        for error_text in common_errors:
            var = ctk.StringVar(value="")
            chk = ctk.CTkCheckBox(scroll_errors, text=error_text, variable=var, 
                                  onvalue=error_text, offvalue="")
            chk.pack(anchor="w", pady=5)
            self.error_vars.append(var)

        other_frame = ctk.CTkFrame(scroll_errors, fg_color="transparent")
        other_frame.pack(fill="x", pady=10)
        self.other_err_var = ctk.StringVar(value="")
        chk_other = ctk.CTkCheckBox(other_frame, text="Otro:", variable=self.other_err_var, 
                                    onvalue="Otro:", offvalue="")
        chk_other.pack(side="left", padx=(0, 5))
        self.other_entry = ctk.CTkEntry(other_frame, placeholder_text="Escribe detallado...")
        self.other_entry.pack(side="left", fill="x", expand=True)

        def save_and_continue(status):
            if status == "Normal":
                obs_text = "Normal"
            else:
                selected_errors = [var.get() for var in self.error_vars if var.get()]
                if self.other_err_var.get():
                    custom_err = self.other_entry.get().strip()
                    if custom_err:
                        selected_errors.append(f"Otro: {custom_err}")
                
                if not selected_errors:
                    obs_text = "Incidencia sin especificar"
                else:
                    obs_text = " | ".join(selected_errors)

            self.current_cycle_splits.append({
                "activity": self.app.ACTIVITIES[index],
                "operator": self.app.line_config.get(str(index), "N/A"),
                "duration": round(duration, 2),
                "observation": obs_text
            })
            
            self.qc_column.grid_forget()
            self.content_container.grid_columnconfigure(1, weight=0)
            
            if index < len(self.app.ACTIVITIES) - 1:
                self.current_activity_index += 1
                self.highlight_activity(self.current_activity_index)
                self.last_split_time = time.time()
            else:
                self.finish_cycle()

        button_frame = ctk.CTkFrame(self.qc_column, fg_color="transparent")
        button_frame.pack(fill="x", pady=10)

        ctk.CTkButton(button_frame, text="✅ Normal (Sin Errores)", fg_color="#27ae60", hover_color="#2ecc71", 
                      height=40, font=ctk.CTkFont(weight="bold"),
                      command=lambda: save_and_continue("Normal")).pack(fill="x", padx=20, pady=5)
        
        ctk.CTkButton(button_frame, text="⚠️ Guardar Errores", fg_color="#e67e22", hover_color="#d35400",
                      height=40, command=lambda: save_and_continue("Error")).pack(fill="x", padx=20, pady=5)

    def finish_cycle(self):
        self.running = False
        total = time.time() - self.start_time
        
        meas = {
            "cycle_id": len(self.app.data.get("measurements", [])) + 1,
            "model": self.app.current_model_name,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "total_time": round(total, 2),
            "splits": self.current_cycle_splits
        }
        self.app.data.setdefault("measurements", []).append(meas)
        self.app.save_data()
        
        messagebox.showinfo("Ciclo Finalizado", f"Toma de tiempos guardada.\nTiempo total del ciclo: {round(total, 2)}s")
        self.app.show_dashboard()

    def reset_timer(self):
        self.running = False
        self.timer_label.configure(text="00:00.00")
        self.op_target_lbl.configure(text="Preparado para iniciar")
        self.btn_start.configure(state="normal", fg_color="#27ae60")
        self.btn_cancel.configure(state="disabled")
        for data in self.act_widgets:
            data["frame"].configure(border_width=0)
            data["btn"].configure(state="disabled", fg_color="gray")
        
        if hasattr(self, 'qc_column') and self.qc_column.winfo_exists():
            self.qc_column.grid_forget()
            if hasattr(self, 'content_container') and self.content_container.winfo_exists():
                self.content_container.grid_columnconfigure(1, weight=0)
