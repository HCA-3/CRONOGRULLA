import os
import sys
import tempfile
from fpdf import FPDF
from datetime import datetime
import matplotlib.pyplot as plt
import numpy as np
import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox, filedialog

class PremiumReportPDF(FPDF):
    def header(self):
        # Fondo decorativo para el encabezado
        self.set_fill_color(30, 41, 59) # Slate 800
        self.rect(0, 0, 210, 30, 'F')
        
        # Titulo Principal
        self.set_font('Arial', 'B', 20)
        self.set_text_color(255, 255, 255)
        self.cell(0, 15, 'CRONOGRULLA - INFORME METODOLÓGICO', 0, 1, 'C')
        
        # Subtitulo
        self.set_font('Arial', 'I', 12)
        self.set_text_color(200, 200, 200)
        self.cell(0, 5, 'Ingeniería de Métodos - Balanceo de Línea (Grullas)', 0, 0, 'C')
        self.ln(20)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.set_text_color(128)
        self.cell(0, 10, f'Página {self.page_no()} | Generado automatizadamente por CronoGrulla', 1, 0, 'C')

class PDFManager:
    def __init__(self, app):
        self.app = app

    def _refresh_comp_ui(self, current_m_count, create_cycle_grid):
        for widget in self.comp_ui_frame.winfo_children():
            widget.destroy()
            
        mode = self.comp_mode.get()
        if mode == "Selección Manual":
            self.base_vars = {}
            self.lote_vars = {}
            create_cycle_grid(self.comp_ui_frame, "Selección de Ciclos (Base/Unitario):", self.base_vars)
            create_cycle_grid(self.comp_ui_frame, "Selección de Ciclos (Lote/Balanceado):", self.lote_vars)
        elif mode == "Comparar Todo":
            half = current_m_count // 2
            ctk.CTkLabel(self.comp_ui_frame, text=f"Se compararán los primeros {half} ciclos contra los {current_m_count - half} restantes.", 
                         font=ctk.CTkFont(size=11, slant="italic"), text_color="gray").pack(pady=5)

    def generate_pdf(self, selected_models=None, custom_data=None, observations=None, recommendations=None):
        """
        Genera el informe PDF. Si selected_models es None, abre el diálogo de selección.
        """
        # --- PARTE 1: DIALOGO DE SELECCIÓN (Si no hay modelos seleccionados) ---
        if selected_models is None:
            self.sel_win = ctk.CTkToplevel(self.app)
            self.sel_win.title("Seleccionar Modelos para Reporte")
            self.sel_win.geometry("580x600")
            self.sel_win.grab_set()
            self.sel_win.attributes("-topmost", True)
            
            ctk.CTkLabel(self.sel_win, text="📊 Exportación de Reporte", 
                         font=ctk.CTkFont(size=22, weight="bold")).pack(pady=(15, 5))
            
            ctk.CTkLabel(self.sel_win, text="¿Qué modelos deseas incluir en el documento?", 
                         font=ctk.CTkFont(size=14), text_color="gray").pack(pady=(0, 5))
            
            # Variables de selección
            self.export_vars = {}
            self.base_vars = {}
            self.lote_vars = {}
            self.comp_mode = tk.StringVar(value="Ninguna")

            def on_confirm():
                selected = [n for n, v in self.export_vars.items() if v.get()]
                if not selected:
                    messagebox.showwarning("Atención", "Selecciona al menos un modelo para exportar.")
                    return
                
                c_data = None
                mode = self.comp_mode.get()
                all_m = self.app.data.get("measurements", [])
                curr_count = len([m for m in all_m if m.get("model") == self.app.current_model_name or (not m.get("model") and self.app.current_model_name == "Grulla Clásica")])

                if mode == "Comparar Todo":
                    half = curr_count // 2
                    c_data = {
                        "base": ",".join(map(str, range(1, half + 1))),
                        "lote": ",".join(map(str, range(half + 1, curr_count + 1)))
                    }
                elif mode == "Selección Manual":
                    base_list = [str(k) for k, v in self.base_vars.items() if v.get()]
                    lote_list = [str(k) for k, v in self.lote_vars.items() if v.get()]
                    if not base_list or not lote_list:
                        messagebox.showwarning("Atención", "Selecciona al menos un ciclo para Base y uno para Lote.")
                        return
                    c_data = {"base": ",".join(base_list), "lote": ",".join(lote_list)}

                obs = self.obs_text.get("1.0", "end-1c")
                rec = self.rec_text.get("1.0", "end-1c")
                self.sel_win.destroy()
                # Llamada recursiva con los datos seleccionados
                self.generate_pdf(selected, c_data, obs, rec)

            # Botones de acción (Anclados arriba para visibilidad)
            btn_f = ctk.CTkFrame(self.sel_win, fg_color="transparent")
            btn_f.pack(pady=10)
            
            ctk.CTkButton(btn_f, text="Generar Reporte", command=on_confirm, width=180, height=35,
                          fg_color="#27ae60", hover_color="#2ecc71", font=ctk.CTkFont(weight="bold")).pack(side="left", padx=10)
            
            ctk.CTkButton(btn_f, text="Cancelar", command=self.sel_win.destroy, width=100, height=35,
                          fg_color="transparent", text_color=("#2c3e50", "white"), border_width=1).pack(side="left", padx=10)

            # Contenedor con scroll para los modelos
            scroll = ctk.CTkScrollableFrame(self.sel_win, fg_color="transparent")
            scroll.pack(fill="both", expand=True, padx=30, pady=(0, 20))
            
            for name in self.app.models.keys():
                var = tk.BooleanVar(value=(name == self.app.current_model_name))
                cb = ctk.CTkCheckBox(scroll, text=name, variable=var, font=ctk.CTkFont(size=13))
                cb.pack(pady=6, anchor="w", padx=10)
                self.export_vars[name] = var
                
            # Sección de Comparación
            ctk.CTkLabel(scroll, text="🔍 Modo de Comparación de Rendimiento:", 
                         font=ctk.CTkFont(weight="bold")).pack(pady=(15, 5), anchor="w", padx=10)
            
            mode_selector = ctk.CTkSegmentedButton(scroll, values=["Ninguna", "Selección Manual", "Comparar Todo"], 
                                                  variable=self.comp_mode, command=lambda _: self.update_comp_ui())
            mode_selector.pack(fill="x", padx=10, pady=5)

            self.comp_ui_frame = ctk.CTkFrame(scroll, fg_color="transparent")
            self.comp_ui_frame.pack(fill="x", padx=10)

            # Calcular ciclos actuales (Usar todos los disponibles para mayor flexibilidad)
            all_m = self.app.data.get("measurements", [])
            current_m_count = len(all_m)

            def create_cycle_grid(parent, label_text, var_dict):
                ctk.CTkLabel(parent, text=label_text, font=ctk.CTkFont(size=11, weight="bold")).pack(anchor="w", pady=(5, 0))
                grid = ctk.CTkFrame(parent, fg_color="transparent")
                grid.pack(fill="x")
                for i in range(1, current_m_count + 1):
                    v = tk.BooleanVar(value=False)
                    cb = ctk.CTkCheckBox(grid, text=str(i), variable=v, width=45, font=ctk.CTkFont(size=10))
                    cb.grid(row=(i-1)//5, column=(i-1)%5, padx=2, pady=2)
                    var_dict[i] = v

            self.update_comp_ui = lambda: self._refresh_comp_ui(current_m_count, create_cycle_grid)
            self.update_comp_ui()

            # --- NUEVO: Campos para Observaciones y Recomendaciones ---
            ctk.CTkLabel(scroll, text="✍️ Observaciones del Autor:", 
                         font=ctk.CTkFont(weight="bold")).pack(pady=(15, 5), anchor="w", padx=10)
            self.obs_text = ctk.CTkTextbox(scroll, height=80)
            self.obs_text.insert("1.0", "Ingrese aquí sus observaciones del estudio...")
            self.obs_text.pack(fill="x", padx=10, pady=5)
            
            ctk.CTkLabel(scroll, text="💡 Recomendaciones de Ingeniería:", 
                         font=ctk.CTkFont(weight="bold")).pack(pady=(10, 5), anchor="w", padx=10)
            self.rec_text = ctk.CTkTextbox(scroll, height=80)
            self.rec_text.insert("1.0", "Ingrese aquí las recomendaciones para la mejora del proceso...")
            self.rec_text.pack(fill="x", padx=10, pady=5)

            return

        # --- PARTE 2: LOGICA DE GENERACION (Cuando selected_models NO es None) ---
        all_measurements = self.app.data.get("measurements", [])
        valid_models = []
        for m_name in selected_models:
            m_data = [m for m in all_measurements if m.get("model") == m_name or (not m.get("model") and m_name == "Grulla Clásica")]
            if m_data:
                valid_models.append((m_name, m_data))
        
        if not valid_models:
            messagebox.showwarning("Sin Datos", "Los modelos seleccionados no tienen ciclos registrados.")
            return

        try:
            default_filename = f"Reporte_Visual_CronoGrulla_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf"
            out_path = filedialog.asksaveasfilename(
                defaultextension=".pdf",
                initialfile=default_filename,
                title="Guardar Informe PDF Como...",
                filetypes=[("Archivos PDF", "*.pdf"), ("Todos los archivos", "*.*")]
            )
            if not out_path: return
            
            pdf = PremiumReportPDF()
            
            for m_name, measurements in valid_models:
                # Obtener info específica del modelo
                model_info = self.app.models.get(m_name, {})
                local_acts = model_info.get("activities", ["Tarea"])
                local_descs = model_info.get("descriptions", ["Sin descripción"])
                num_steps = len(local_acts)

                pdf.add_page()
                
                # --- SECCION 1: Informacion del Modelo ---
                pdf.set_font('Arial', 'B', 14)
                pdf.set_text_color(44, 62, 80)
                pdf.cell(0, 10, f"MODELO: {m_name.upper()}", 0, 1)
                pdf.ln(2)
                
                pdf.set_font('Arial', 'B', 11)
                pdf.cell(0, 8, "1. Informacion del Estudio y Especificaciones", 0, 1)
                pdf.set_font('Arial', '', 10)
                pdf.cell(0, 6, f"Fecha de emision: {datetime.now().strftime('%d/%m/%Y %H:%M')}", 0, 1)
                pdf.cell(0, 6, "Captura por Gestos Visuales: Activa (Deteccion de Palma)", 0, 1)
                
                pdf.set_font('Arial', 'B', 10)
                pdf.cell(0, 7, "Autores del Estudio:", 0, 1)
                pdf.set_font('Arial', '', 10)
                autores = " - David Santiago Castelblanco Artunduaga (5201057)\n - Juan Diego Escobar Duarte (5200969)\n - Laura Vanessa Cespedes Acosta (5200901)"
                pdf.multi_cell(0, 5, autores, 0, 'L')
                pdf.ln(3)

                pdf.cell(0, 6, f"Ciclos medidos: {len(measurements)}", 0, 1)
                avg = sum(m["total_time"] for m in measurements) / len(measurements)
                pdf.cell(0, 6, f"Tiempo de ciclo promedio: {avg:.2f} segundos", 0, 1)
                pdf.ln(5)

                # --- SECCION 2: Distribución Operativa (Balanceo) ---
                pdf.set_font('Arial', 'B', 14)
                pdf.set_text_color(44, 62, 80)
                pdf.cell(0, 10, "2. Distribucion y Descripcion de Operaciones", 0, 1)
                pdf.set_text_color(0, 0, 0)
                
                pdf.set_font('Arial', 'I', 10)
                dist_explication = (
                    "El balanceo de linea es una herramienta fundamental de la Ingenieria de Metodos que busca la optimizacion "
                    "de la capacidad productiva mediante la asignacion equitativa de cargas de trabajo. Esta seccion detalla "
                    "la division de tareas por puesto de trabajo (Workstation Balancing) con el fin de minimizar el tiempo "
                    "ocioso (Idle Time) y asegurar un flujo continuo sincronizado con el Takt Time del proceso."
                )
                pdf.multi_cell(0, 5, dist_explication.encode('latin-1', 'replace').decode('latin-1'), 0, 'J')
                pdf.ln(3)

                # Detectar configuraciones de balanceo únicas
                configs = {}
                for idx, m in enumerate(measurements, 1):
                    config = tuple(s.get("operator", "N/A") for s in m.get("splits", []))
                    if len(config) < num_steps:
                        config = config + ("N/A",) * (num_steps - len(config))
                    if config not in configs: configs[config] = []
                    configs[config].append(idx)
                    
                for config_idx, (config_tuple, cycles) in enumerate(configs.items(), 1):
                    pdf.set_font('Arial', 'B', 11)
                    pdf.set_text_color(52, 152, 219)
                    pdf.cell(0, 8, f"Configuracion de Balanceo #{config_idx} (Ciclos: {', '.join(map(str, cycles))})", 0, 1)
                    pdf.set_text_color(0, 0, 0)
                    
                    pdf.set_font('Arial', 'I', 9)
                    pdf.multi_cell(0, 5, "Descripcion del Metodo de Trabajo por Paso:", 0, 'L')
                    pdf.ln(1)

                    pdf.set_fill_color(235, 245, 255)
                    for i in range(num_steps):
                        op = config_tuple[i] if i < len(config_tuple) else "N/A"
                        pdf.set_font('Arial', 'B', 9)
                        pdf.cell(25, 8, f"Tarea {i+1}", 1, 0, 'C', True)
                        pdf.cell(40, 8, f"Operador: {op[:15]}", 1, 0, 'C', True)
                        
                        clean_act = local_acts[i].encode('latin-1', 'replace').decode('latin-1')
                        pdf.multi_cell(0, 8, f" {clean_act}", 1, 'L', True)
                        pdf.set_x(10)
                        
                        pdf.set_font('Arial', '', 8)
                        pdf.set_text_color(60, 60, 60)
                        clean_desc = local_descs[i].encode('latin-1', 'replace').decode('latin-1')
                        pdf.multi_cell(0, 5, f"Especificacion: {clean_desc}", 1, 'L')
                        pdf.set_text_color(0, 0, 0)
                        pdf.set_x(10)
                    pdf.ln(7)

                # --- SECCION 3: Evidencia Visual (Galería) ---
                pdf.add_page()
                pdf.set_font('Arial', 'B', 12)
                pdf.cell(0, 10, "3. Evidencia Visual del Proceso (Clasificado por Operador)", 0, 1)
                pdf.ln(5)
                
                op_evidences = {}
                # Agrupar evidencias por operador
                for m in reversed(measurements):
                    for split in m.get("splits", []):
                        op = split.get("operator", "Sin Asignar").encode('latin-1', 'replace').decode('latin-1')
                        imgs = []
                        if split.get("evidence"): imgs.append(split["evidence"])
                        if split.get("evidences"): imgs.extend(split["evidences"])
                        
                        if not imgs: continue
                        if op not in op_evidences: op_evidences[op] = []
                        
                        for p in imgs:
                            if os.path.exists(p) and len(op_evidences[op]) < 8:
                                clean_act = split.get('activity','').encode('latin-1', 'replace').decode('latin-1')
                                op_evidences[op].append((p, clean_act))

                for op, evid_list in op_evidences.items():
                    pdf.set_font('Arial', 'B', 11)
                    pdf.set_text_color(255, 255, 255)
                    pdf.set_fill_color(52, 152, 219)
                    pdf.cell(0, 7, f" Evidencia - Operador: {op}", 0, 1, 'L', True)
                    pdf.set_text_color(0, 0, 0)
                    pdf.ln(3)
                    
                    img_w, img_h, spacing, margin_x = 60, 45, 3, 10
                    col = 0
                    for img_path, act in evid_list:
                        if col == 3:
                            pdf.ln(spacing)
                            col = 0
                        
                        if pdf.get_y() > 230:
                            pdf.add_page()
                            pdf.set_font('Arial', 'B', 11)
                            pdf.set_fill_color(52, 152, 219)
                            pdf.set_text_color(255, 255, 255)
                            pdf.cell(0, 7, f" Evidencia (cont.) - Operador: {op}", 0, 1, 'L', True)
                            pdf.set_text_color(0, 0, 0)
                            pdf.ln(5)
                            col = 0

                        x = margin_x + (col * (img_w + spacing))
                        y = pdf.get_y()
                        pdf.set_xy(x, y)
                        pdf.set_font('Arial', 'B', 7)
                        pdf.cell(img_w, 5, f"{act[:35]}", 0, 1, 'C')
                        pdf.set_x(x)
                        pdf.image(img_path, x=x, y=pdf.get_y(), w=img_w, h=img_h)
                        col += 1
                        if col == 3: pdf.set_y(y + img_h + 10)
                    
                    if col != 0: pdf.ln(img_h + 10)
                    pdf.ln(5)
                
                if not op_evidences:
                    pdf.cell(0, 10, "No se encontraron evidencias fotograficas en los registros.", 0, 1)

                # --- SECCION 4: Matriz de Tiempos ---
                pdf.add_page()
                pdf.set_font('Arial', 'B', 14)
                pdf.set_text_color(44, 62, 80)
                pdf.cell(0, 10, "4. Matriz de Tiempos y Analisis de Cuellos de Botella", 0, 1)
                pdf.set_text_color(0, 0, 0)
                pdf.ln(5)

                pdf.set_font('Arial', 'B', 8)
                pdf.set_fill_color(44, 62, 80)
                pdf.set_text_color(255, 255, 255)
                
                w_ciclo, w_tot = 12, 18
                w_op = (190 - w_ciclo - w_tot) / num_steps
                
                pdf.cell(w_ciclo, 9, "#", 1, 0, 'C', True)
                for i in range(num_steps):
                    pdf.cell(w_op, 9, f"T{i+1}", 1, 0, 'C', True)
                pdf.cell(w_tot, 9, "TOTAL", 1, 1, 'C', True)
                
                pdf.set_text_color(0, 0, 0)
                pdf.set_font('Arial', '', 7)
                sum_ops, count_ops = [0.0] * num_steps, [0] * num_steps
                fill = False

                for i, m in enumerate(measurements, 1):
                    pdf.cell(w_ciclo, 7, f"{i}", 1, 0, 'C', fill)
                    for j, s in enumerate(m["splits"]):
                        if j < num_steps:
                            pdf.cell(w_op, 7, f"{s['duration']}", 1, 0, 'C', fill)
                            sum_ops[j] += s["duration"]
                            count_ops[j] += 1
                    
                    if len(m["splits"]) < num_steps:
                        for _ in range(num_steps - len(m["splits"])):
                            pdf.cell(w_op, 7, "-", 1, 0, 'C', fill)
                    
                    row_sum = sum(s.get("duration", 0) for s in m["splits"])
                    pdf.set_font('Arial', 'B', 7)
                    pdf.cell(w_tot, 7, f"{round(row_sum, 2)}", 1, 1, 'C', fill)
                    pdf.set_font('Arial', '', 7)
                    fill = not fill

                # Gráfico de Cuello de Botella
                avg_ops = [sum_ops[i] / count_ops[i] if count_ops[i] > 0 else 0 for i in range(num_steps)]
                plt.figure(figsize=(10, 4))
                plt.bar([f"T{i+1}" for i in range(num_steps)], avg_ops, color='#3498db', edgecolor='#2980b9')
                plt.title(f'Perfil de Carga por Tarea: {m_name}', fontsize=12, fontweight='bold')
                plt.ylabel('Tiempo Promedio (s)')
                plt.grid(axis='y', linestyle='--', alpha=0.7)
                plt.tight_layout()
                
                safe_m_name = "".join([c if c.isalnum() else "_" for c in m_name])
                tmp_img = os.path.join(tempfile.gettempdir(), f"graph_{safe_m_name}.png")
                plt.savefig(tmp_img, dpi=150)
                plt.close()
                pdf.ln(5)
                pdf.image(tmp_img, x=10, w=190)
                pdf.ln(5)

                # Análisis dinámico de cuellos de botella
                pdf.set_font('Arial', 'B', 10)
                pdf.cell(0, 8, "Analisis de Balanceo y Restricciones:", 0, 1)
                pdf.set_font('Arial', '', 9)
                max_t = max(avg_ops) if avg_ops else 0
                max_idx = avg_ops.index(max_t) if avg_ops else 0
                min_t = min([t for t in avg_ops if t > 0]) if any(t > 0 for t in avg_ops) else 0
                imbalance = (max_t - min_t) if max_t > 0 else 0
                
                analysis_4 = (
                    f"La grafica superior identifica la Tarea {max_idx+1} como la restriccion principal (Cuello de Botella) "
                    f"con un tiempo de {max_t:.2f}s. La variabilidad entre la tarea mas lenta y la mas rapida ({imbalance:.2f}s) "
                    "evidencia una oportunidad de re-balanceo. Segun la teoria de restricciones (TOC), cualquier mejora "
                    "fuera de este cuello de botella no incrementara la productividad global del sistema."
                )
                pdf.multi_cell(0, 5, analysis_4.encode('latin-1', 'replace').decode('latin-1'), 0, 'J')

                # --- SECCION 5: Rendimiento Individual por Operador ---
                pdf.add_page()
                pdf.set_font('Arial', 'B', 14)
                pdf.set_text_color(44, 62, 80)
                pdf.cell(0, 10, "5. Analisis de Rendimiento Individual por Operador", 0, 1)
                pdf.set_text_color(0, 0, 0)
                pdf.ln(3)

                op_stats = {}
                for m in measurements:
                    for i_s, s in enumerate(m["splits"]):
                        op = s.get("operator", "N/A")
                        if op != "N/A":
                            if op not in op_stats:
                                op_stats[op] = {"times": [], "tasks_idx": set()}
                            op_stats[op]["times"].append(s["duration"])
                            op_stats[op]["tasks_idx"].add(i_s)
                
                for op, data in op_stats.items():
                    times = data["times"]
                    data["avg"] = np.mean(times)
                    data["min"] = min(times)
                    data["max"] = max(times)
                    data["tasks"] = len(times)
                    data["std"] = np.std(times)
                    data["time"] = sum(times)

                sorted_ops = sorted(op_stats.items(), key=lambda x: x[1]["avg"])
                
                # Grafico de rendimiento por operador
                op_names = [op.encode('latin-1', 'replace').decode('latin-1') for op, d in sorted_ops]
                plt.figure(figsize=(10, 4))
                plt.bar(op_names, [d["avg"] for op, d in sorted_ops], color='#2ecc71', alpha=0.8)
                plt.title('Promedio de Tiempo por Operador (Ordenado por Eficiencia)', fontsize=12)
                plt.ylabel('Segundos (s)')
                plt.tight_layout()
                tmp_op_img = os.path.join(tempfile.gettempdir(), f"op_graph_{safe_m_name}.png")
                plt.savefig(tmp_op_img, dpi=120)
                plt.close()
                pdf.image(tmp_op_img, x=10, w=190)
                pdf.ln(5)

                # Tabla de Indicadores por Operador
                pdf.set_font('Arial', 'B', 9)
                pdf.set_fill_color(44, 62, 80)
                pdf.set_text_color(255, 255, 255)
                headers = ["Operador", "# Tareas", "Rango (s)", "Volatilidad (STD)", "Tiempo Total", "Promedio"]
                widths = [50, 20, 30, 25, 35, 30]
                for h, w in zip(headers, widths):
                    pdf.cell(w, 9, h, 1, 0, 'C', True)
                pdf.ln()
                
                pdf.set_text_color(0, 0, 0)
                pdf.set_font('Arial', '', 8)
                fill = False
                for op, stats in sorted_ops:
                    pdf.cell(widths[0], 8, f" {op[:25]}", 1, 0, 'L', fill)
                    pdf.cell(widths[1], 8, f"{stats['tasks']}", 1, 0, 'C', fill)
                    pdf.cell(widths[2], 8, f"{stats['min']:.1f} - {stats['max']:.1f}", 1, 0, 'C', fill)
                    pdf.cell(widths[3], 8, f"{stats['std']:.2f}", 1, 0, 'C', fill)
                    pdf.cell(widths[4], 8, f"{stats['time']:.2f} s", 1, 0, 'C', fill)
                    pdf.set_font('Arial', 'B', 8)
                    pdf.cell(widths[5], 8, f"{stats['avg']:.2f} s", 1, 1, 'C', fill)
                    pdf.set_font('Arial', '', 8)
                    fill = not fill
                pdf.ln(5)

                # Análisis de Desempeño Humano
                pdf.set_font('Arial', 'B', 10)
                pdf.cell(0, 8, "Interpretacion del Desempeño Operativo:", 0, 1)
                pdf.set_font('Arial', '', 9)
                best_op = sorted_ops[0][0] if sorted_ops else "N/A"
                consistency_note = "El equipo muestra una consistencia aceptable."
                if any(s[1]["std"] > 5 for s in sorted_ops):
                    consistency_note = "Se observa alta volatilidad en algunos operarios, sugiriendo la necesidad de re-entrenamiento en el metodo estandar."
                
                analysis_5 = (
                    f"El operario {best_op} lidera la eficiencia con un ritmo de {sorted_ops[0][1]['avg']:.2f}s por tarea. "
                    f"{consistency_note} La reduccion de la desviacion estandar (Mura) es clave para estabilizar el Lead Time "
                    "y asegurar el cumplimiento de las metas de produccion programadas."
                )
                pdf.multi_cell(0, 5, analysis_5.encode('latin-1', 'replace').decode('latin-1'), 0, 'J')
                pdf.ln(5)

            # --- SECCION 6: Conclusiones y Resumen Ejecutivo ---
            pdf.set_font('Arial', 'B', 14)
            pdf.set_text_color(44, 62, 80)
            pdf.cell(0, 10, "6. Conclusiones de Ingenieria y Resumen Ejecutivo", 0, 1)
            pdf.set_text_color(0, 0, 0)
            pdf.ln(3)
            
            pdf.set_font('Arial', '', 11)
            # Texto profesional solicitado por el usuario
            conclusion_profesional = (
                "Inicialmente medimos el proceso bajo un flujo secuencial, donde existian tiempos muertos por dependencia "
                "entre operarios, lo que generaba menor eficiencia. Posteriormente, implementamos balanceo de linea, "
                "eliminacion de desperdicios (Muda), y reduccion de variabilidad (Mura y Muri), logrando un flujo continuo. "
                "\n\nAunque los tiempos por ciclo pueden parecer mayores en la medicion bruta, esto se debe a que el sistema "
                "cambio de medicion: ya no se mide una unidad aislada, sino un sistema productivo en paralelo. Por esta razon, "
                "la comparacion correcta se realiza en terminos de productividad, evidenciando la mejora real en la capacidad de salida."
            )
            pdf.multi_cell(0, 6, conclusion_profesional.encode('latin-1', 'replace').decode('latin-1'), 0, 'J')
            pdf.ln(5)

            if observations and observations.strip() and observations != "Ingrese aquí sus observaciones del estudio...":
                pdf.set_font('Arial', 'B', 11)
                pdf.set_fill_color(245, 245, 245)
                pdf.cell(0, 8, " Observaciones Detalladas del Analista:", 0, 1, 'L', True)
                pdf.set_font('Arial', '', 10)
                pdf.multi_cell(0, 5, observations.encode('latin-1', 'replace').decode('latin-1'), 0, 'J')
                pdf.ln(4)
            
            if recommendations and recommendations.strip() and recommendations != "Ingrese aquí las recomendaciones para la mejora del proceso...":
                pdf.set_font('Arial', 'B', 11)
                pdf.set_fill_color(245, 245, 245)
                pdf.cell(0, 8, " Recomendaciones Estrategicas de Mejora:", 0, 1, 'L', True)
                pdf.set_font('Arial', '', 10)
                pdf.multi_cell(0, 5, recommendations.encode('latin-1', 'replace').decode('latin-1'), 0, 'J')
                pdf.ln(4)
            pdf.ln(5)

            # --- SECCION 7: Analisis de Condiciones Ambientales ---
            pdf.add_page()
            pdf.set_font('Arial', 'B', 14)
            pdf.set_text_color(44, 62, 80)
            pdf.cell(0, 10, "7. Analisis de Condiciones Ambientales", 0, 1)
            pdf.set_text_color(0, 0, 0)
            
            pdf.set_font('Arial', 'I', 10)
            env_intro = (
                "Las condiciones ambientales influyen directamente en la productividad y salud del trabajador. "
                "Segun la normativa colombiana (RETILAP) y estandares internacionales (OSHA), se deben garantizar "
                "niveles optimos de iluminacion y ruido para prevenir la fatiga y el estres laboral."
            )
            pdf.multi_cell(0, 5, env_intro.encode('latin-1', 'replace').decode('latin-1'), 0, 'J')
            pdf.ln(2)
            
            all_lx = []
            all_db = []
            for m in measurements:
                for l in m.get("lux_data", []):
                    try: 
                        val = float(l.get("val", 0))
                        if val > 0: all_lx.append(val)
                    except: pass
                for d in m.get("db_data", []):
                    try: 
                        val = float(d.get("val", 0))
                        if val > 0: all_db.append(val)
                    except: pass
            
            def render_env_block(title, data, unit, standard, limit, tech_note):
                pdf.set_font('Arial', 'B', 11)
                pdf.set_fill_color(240, 245, 250)
                pdf.cell(0, 8, f" {title}", 1, 1, 'L', True)
                
                if not data:
                    pdf.set_font('Arial', 'I', 10)
                    pdf.cell(0, 10, "      No se registraron datos suficientes para este analisis ambiental.", 0, 1)
                    return

                stats = {
                    "n": len(data),
                    "min": min(data),
                    "max": max(data),
                    "avg": np.mean(data),
                    "std": np.std(data)
                }
                    
                pdf.set_font('Arial', 'B', 9)
                pdf.set_fill_color(52, 152, 219)
                pdf.set_text_color(255, 255, 255)
                c_ws = [30, 32, 32, 32, 32, 30]
                headers = ["Muestras", "Minimo", "Maximo", "Promedio", "Desv. Est.", "Unidad"]
                for h, w in zip(headers, c_ws):
                    pdf.cell(w, 8, h, 1, 0, 'C', True)
                pdf.ln()
                
                pdf.set_text_color(0, 0, 0)
                pdf.set_font('Arial', '', 9)
                pdf.cell(c_ws[0], 8, str(stats["n"]), 1, 0, 'C')
                pdf.cell(c_ws[1], 8, f"{stats['min']:.1f}", 1, 0, 'C')
                pdf.cell(c_ws[2], 8, f"{stats['max']:.1f}", 1, 0, 'C')
                pdf.cell(c_ws[3], 8, f"{stats['avg']:.1f}", 1, 0, 'C')
                pdf.cell(c_ws[4], 8, f"{stats['std']:.2f}", 1, 0, 'C')
                pdf.cell(c_ws[5], 8, unit, 1, 1, 'C')
                
                pdf.set_font('Arial', 'B', 10)
                pdf.cell(50, 9, f"Referencia {standard}:", 0, 0)
                status = "OPTIMO" if (unit=="lx" and stats["avg"]>=500) or (unit=="dB" and stats["avg"]<80) else "ACEPTABLE"
                pdf.cell(0, 9, f"{status} (Observado: {stats['avg']:.1f} {unit} vs Meta: {limit})", 0, 1)
                
                pdf.set_font('Arial', 'I', 8)
                pdf.multi_cell(0, 5, f"Nota Tecnica: {tech_note}", 0, 'L')
                pdf.ln(5)

            render_env_block("7.1. Analisis de Iluminancia (Luxometria)", all_lx, "lx", "RETILAP", "300-500 lx", "Un nivel adecuado de iluminacion es fundamental para tareas de precision y reduccion de fatiga ocular.")
            render_env_block("7.2. Analisis de Ruido Laboral (Sonometria)", all_db, "dB", "OSHA", "< 85 dB", "El control de ruido previene la distraccion del operario y protege la salud auditiva a largo plazo.")

            # Análisis de cumplimiento ambiental
            pdf.set_font('Arial', 'B', 10)
            pdf.cell(0, 8, "Analisis de Higiene Industrial:", 0, 1)
            pdf.set_font('Arial', '', 9)
            env_analysis = (
                "Los datos recolectados indican si el ambiente de trabajo cumple con los limites permisibles. "
                "Un ambiente fuera de rango (ej. iluminacion < 300 lx) incrementa el tiempo de ciclo por dificultad "
                "visual y riesgo de errores de calidad (Muda de Defectos)."
            )
            pdf.multi_cell(0, 5, env_analysis.encode('latin-1', 'replace').decode('latin-1'), 0, 'J')
            pdf.ln(5)

            # --- SECCION 8: Comparativa de Rendimiento Unitario vs Lote ---
            if custom_data and (custom_data.get("base") and custom_data.get("lote")):
                pdf.add_page()
                pdf.set_font('Arial', 'B', 14)
                pdf.set_text_color(44, 62, 80)
                pdf.cell(0, 10, "8. Comparativa de Rendimiento Unitario vs Lote", 0, 1)
                pdf.set_text_color(0, 0, 0)
                
                pdf.set_font('Arial', '', 10)
                teoria_lote = (
                    "El analisis de rendimiento unitario vs lote evalua la eficiencia marginal de la produccion "
                    "balanceada. El flujo unitario (Single Piece Flow) es contrastado con el sistema de flujo "
                    "continuo por estaciones, permitiendo identificar la reduccion de tiempos de espera y el "
                    "incremento en la capacidad de salida (UPH) del sistema optimizado."
                )
                pdf.multi_cell(0, 5, teoria_lote.encode('latin-1', 'replace').decode('latin-1'), 0, 'J')
                pdf.ln(5)

                try:
                    base_ids = [int(x.strip()) for x in custom_data["base"].split(',')]
                    lote_ids = [int(x.strip()) for x in custom_data["lote"].split(',')]
                    
                    base_m = [m for idx, m in enumerate(measurements, 1) if idx in base_ids]
                    lote_m = [m for idx, m in enumerate(measurements, 1) if idx in lote_ids]
                    
                    if base_m and lote_m:
                        t_base = sum(m.get("total_time", 0) for m in base_m)
                        v_base = sum(m.get("volume", 1) for m in base_m)
                        t_lote = sum(m.get("total_time", 0) for m in lote_m)
                        v_lote = sum(m.get("volume", 1) for m in lote_m)
                        
                        avg_base = t_base / v_base if v_base else 0
                        avg_lote = t_lote / v_lote if v_lote else 0
                        
                        uph_base = 3600 / avg_base if avg_base > 0 else 0
                        uph_lote = 3600 / avg_lote if avg_lote > 0 else 0
                        mejora = ((uph_lote - uph_base) / uph_base * 100) if uph_base > 0 else 0
                        
                        pdf.set_font('Arial', 'B', 9)
                        pdf.set_fill_color(44, 62, 80)
                        pdf.set_text_color(255, 255, 255)
                        pdf.cell(60, 9, "Metrica", 1, 0, 'C', True)
                        pdf.cell(50, 9, "Sistema Unitario", 1, 0, 'C', True)
                        pdf.cell(50, 9, "Sistema Lote/Balanceado", 1, 0, 'C', True)
                        pdf.cell(30, 9, "Variacion", 1, 1, 'C', True)
                        
                        pdf.set_text_color(0, 0, 0)
                        pdf.set_font('Arial', '', 9)
                        pdf.cell(60, 8, " Tiempo Promedio por Unidad", 1, 0, 'L')
                        pdf.cell(50, 8, f"{avg_base:.2f} s", 1, 0, 'C')
                        pdf.cell(50, 8, f"{avg_lote:.2f} s", 1, 0, 'C')
                        pdf.cell(30, 8, f"{((avg_lote-avg_base)/avg_base*100):+.1f}%", 1, 1, 'C')
                        
                        pdf.cell(60, 8, " Capacidad de Salida (UPH)", 1, 0, 'L')
                        pdf.cell(50, 8, f"{uph_base:.1f} un/h", 1, 0, 'C')
                        pdf.cell(50, 8, f"{uph_lote:.1f} un/h", 1, 0, 'C')
                        pdf.set_font('Arial', 'B', 9)
                        pdf.cell(30, 8, f"{mejora:+.1f}%", 1, 1, 'C')
                        pdf.ln(5)
                        
                        pdf.set_fill_color(230, 240, 230)
                        pdf.set_font('Arial', 'B', 11)
                        pdf.cell(0, 10, " SINTESIS DE MEJORA (Interpretacion de Sistemas)", 1, 1, 'L', True)
                        pdf.set_font('Arial', 'I', 10)
                        # Texto explicativo sobre el error de comparación
                        sust = (
                            "IMPORTANTE: Los ciclos del sistema unitario (1-5) corresponden a una produccion secuencial donde "
                            "un operario realiza la grulla completa o depende estrictamente del anterior. Los ciclos del sistema "
                            "balanceado (6-10) representan un flujo continuo en paralelo. "
                            f"\n\nLa mejora del {mejora:.1f}% en la capacidad de salida (UPH) demuestra que, aunque el tiempo "
                            "de sistema parezca mayor, la productividad por unidad ha mejorado significativamente al eliminar "
                            "tiempos muertos y esperas (Muda de Espera)."
                        )
                        pdf.multi_cell(0, 5, sust.encode('latin-1', 'replace').decode('latin-1'), 1, 'J')
                except: pass

            # --- SECCION 9: Analisis de Consistencia y Eficiencia Benchmark ---
            pdf.add_page()
            pdf.set_font('Arial', 'B', 14)
            pdf.cell(0, 10, "9. Analisis de Consistencia y Eficiencia Benchmark", 0, 1)
            pdf.ln(2)
            
            best_avg = min(d["avg"] for d in op_stats.values()) if op_stats else 1
            pdf.set_font('Arial', 'B', 9)
            pdf.set_fill_color(30, 41, 59)
            pdf.set_text_color(255, 255, 255)
            h_bench = ["Operador", "Avg (s)", "Min (s)", "Max (s)", "Indice Eficiencia"]
            w_bench = [50, 35, 35, 35, 35]
            for h, w in zip(h_bench, w_bench):
                pdf.cell(w, 9, h, 1, 0, 'C', True)
            pdf.ln()
            
            pdf.set_text_color(0, 0, 0)
            pdf.set_font('Arial', '', 9)
            fill = False
            for op, s in sorted(op_stats.items(), key=lambda x: x[1]["avg"]):
                pdf.cell(w_bench[0], 8, f" {op[:25]}", 1, 0, 'L', fill)
                pdf.cell(w_bench[1], 8, f"{s['avg']:.2f}", 1, 0, 'C', fill)
                pdf.cell(w_bench[2], 8, f"{s['min']:.2f}", 1, 0, 'C', fill)
                pdf.cell(w_bench[3], 8, f"{s['max']:.2f}", 1, 0, 'C', fill)
                efficiency = (best_avg / s["avg"] * 100)
                pdf.set_font('Arial', 'B', 9)
                pdf.cell(w_bench[4], 8, f"{efficiency:.1f}%", 1, 1, 'C', fill)
                pdf.set_font('Arial', '', 9)
                fill = not fill
            pdf.ln(5)

            # Análisis de Eficiencia
            pdf.set_font('Arial', 'B', 10)
            pdf.cell(0, 8, "Analisis de Brecha de Eficiencia (Gap Analysis):", 0, 1)
            pdf.set_font('Arial', '', 9)
            efficiency_analysis = (
                "Este indice compara a cada operario contra el mejor desempeño registrado (Benchmark). "
                "Un indice inferior al 80% indica una brecha de habilidad que debe ser atendida mediante capacitacion "
                "o rediseño ergonomico del puesto para estandarizar el rendimiento de la linea."
            )
            pdf.multi_cell(0, 5, efficiency_analysis.encode('latin-1', 'replace').decode('latin-1'), 0, 'J')
            pdf.ln(5)

            # --- SECCION 10: Analisis Ergonomico y Postural ---
            pdf.add_page()
            pdf.set_font('Arial', 'B', 14)
            pdf.cell(0, 10, "10. Analisis Ergonomico y Postural", 0, 1)
            
            pdf.set_font('Arial', 'I', 10)
            ergo_explication = (
                "El analisis postural mediante vision artificial permite detectar angulos de flexion de las articulaciones "
                "en tiempo real. Un angulo de codo alejado de la posicion neutra (90-110 deg) o posturas forzadas incrementan "
                "el riesgo de trastornos musculoesqueleticos. Este estudio clasifica cada tarea segun el nivel de riesgo observado."
            )
            pdf.multi_cell(0, 5, ergo_explication.encode('latin-1', 'replace').decode('latin-1'), 0, 'J')
            pdf.ln(3)
            
            ergo_data = []
            for m in measurements:
                for s in m.get("splits", []):
                    ang = s.get("avg_angle", 0)
                    status = "Optimo" if ang < 45 else ("Precaucion" if ang < 90 else "Riesgo")
                    ergo_data.append((s.get("operator", "N/A"), s.get("activity", "N/A"), ang, status))
            
            pdf.set_font('Arial', 'B', 9)
            pdf.set_fill_color(22, 160, 133) # Esmeralda Ergonómico
            pdf.set_text_color(255, 255, 255)
            h_ergo = ["Operador", "Tarea Realizada", "Angulo Prom. Codo", "Nivel de Riesgo"]
            w_ergo = [45, 80, 35, 30]
            for h, w in zip(h_ergo, w_ergo):
                pdf.cell(w, 9, h, 1, 0, 'C', True)
            pdf.ln()
            
            pdf.set_text_color(0, 0, 0)
            pdf.set_font('Arial', '', 8)
            fill = False
            for r in ergo_data[:25]: # Limitar a 25 filas para no saturar
                pdf.cell(w_ergo[0], 7, f" {r[0][:20]}", 1, 0, 'L', fill)
                pdf.cell(w_ergo[1], 7, f" {r[1][:35]}", 1, 0, 'L', fill)
                pdf.cell(w_ergo[2], 7, f"{int(r[2])} deg", 1, 0, 'C', fill)
                pdf.cell(w_ergo[3], 7, r[3], 1, 1, 'C', fill)
                fill = not fill
            pdf.ln(5)

            # Análisis Ergonómico
            pdf.set_font('Arial', 'B', 10)
            pdf.cell(0, 8, "Analisis de Riesgo Biomecanico:", 0, 1)
            pdf.set_font('Arial', '', 9)
            risk_count = len([r for r in ergo_data if r[3] == "Riesgo"])
            risk_analysis = (
                f"Se han identificado {risk_count} tareas con nivel de 'Riesgo' postural. Angulos de flexion severos "
                "disminuyen la velocidad de operacion y aumentan el ausentismo a largo plazo. La optimizacion ergonómica "
                "es necesaria para mantener la productividad en el sistema de flujo continuo."
            )
            pdf.multi_cell(0, 5, risk_analysis.encode('latin-1', 'replace').decode('latin-1'), 0, 'J')
            pdf.ln(5)

            # --- SECCION 11: Determinacion del Tiempo Estandar (Maytag) ---
            pdf.add_page()
            pdf.set_font('Arial', 'B', 14)
            pdf.cell(0, 10, "11. Determinacion del Tiempo Estandar (Metodologia Maytag)", 0, 1)
            
            pdf.set_font('Arial', 'I', 10)
            maytag_explication = (
                "La metodologia Maytag se utiliza para estandarizar procesos industriales. Se aplica una Calificacion "
                "de la Actuacion (Rating) basada en la habilidad y esfuerzo del operario, y se añaden Suplementos "
                "por necesidades personales y fatiga (Allowances). El Tiempo Estandar resultante es la base para "
                "la planeacion de la produccion y costeo de mano de obra."
            )
            pdf.multi_cell(0, 5, maytag_explication.encode('latin-1', 'replace').decode('latin-1'), 0, 'J')
            pdf.ln(3)
            
            pdf.set_font('Arial', 'B', 8)
            pdf.set_fill_color(30, 41, 59)
            pdf.set_text_color(255, 255, 255)
            te_headers = ["Tarea", "N", "Avg (X)", "Rango (R)", "R/X %", "Cal. %", "T. Normal", "Sup. %", "T. Estandar"]
            te_ws = [45, 10, 20, 20, 15, 15, 25, 15, 25]
            for h, w in zip(te_headers, te_ws):
                pdf.cell(w, 9, h, 1, 0, 'C', True)
            pdf.ln()
            
            pdf.set_text_color(0, 0, 0)
            pdf.set_font('Arial', '', 8)
            total_ts_all = 0
            rating, allowance = 1.0, 0.12 # Rating 100%, Suplementos 12%
            fill = False
            
            for idx, act in enumerate(local_acts):
                t_list = [m["splits"][idx]["duration"] for m in measurements if idx < len(m.get("splits", []))]
                if not t_list: continue
                
                x_val = np.mean(t_list)
                r_val = max(t_list) - min(t_list)
                rx_val = (r_val / x_val * 100) if x_val > 0 else 0
                tn_val = x_val * rating
                ts_val = tn_val * (1 + allowance)
                total_ts_all += ts_val
                
                pdf.cell(te_ws[0], 8, f" {act[:22]}", 1, 0, 'L', fill)
                pdf.cell(te_ws[1], 8, str(len(t_list)), 1, 0, 'C', fill)
                pdf.cell(te_ws[2], 8, f"{x_val:.2f} s", 1, 0, 'C', fill)
                pdf.cell(te_ws[3], 8, f"{r_val:.2f} s", 1, 0, 'C', fill)
                pdf.cell(te_ws[4], 8, f"{rx_val:.1f}%", 1, 0, 'C', fill)
                pdf.cell(te_ws[5], 8, "100%", 1, 0, 'C', fill)
                pdf.cell(te_ws[6], 8, f"{tn_val:.2f} s", 1, 0, 'C', fill)
                pdf.cell(te_ws[7], 8, "12%", 1, 0, 'C', fill)
                pdf.set_font('Arial', 'B', 8)
                pdf.cell(te_ws[8], 8, f"{ts_val:.2f} s", 1, 1, 'C', fill)
                pdf.set_font('Arial', '', 8)
                fill = not fill

            pdf.ln(5)
            pdf.set_fill_color(230, 240, 230)
            pdf.set_font('Arial', 'B', 12)
            pdf.cell(140, 12, " TIEMPO ESTANDAR TOTAL DEL PROCESO (Minutos/Ciclo):", 1, 0, 'L', True)
            pdf.cell(50, 12, f" {(total_ts_all/60):.3f} min ", 1, 1, 'C', True)
            pdf.ln(5)

            # Análisis del Tiempo Estándar
            pdf.set_font('Arial', 'B', 10)
            pdf.cell(0, 8, "Interpretacion de la Estandarizacion (Maytag):", 0, 1)
            pdf.set_font('Arial', '', 9)
            standard_analysis = (
                f"El Tiempo Estandar calculado de {(total_ts_all/60):.3f} minutos es la base para la planeacion real. "
                "Cualquier desviacion significativa entre el tiempo observado y el estandar sugiere problemas de "
                "metodo o condiciones de fatiga no previstas (Muri)."
            )
            pdf.multi_cell(0, 5, standard_analysis.encode('latin-1', 'replace').decode('latin-1'), 0, 'J')
            pdf.ln(5)

            # --- SECCION 12: Analisis de Micro-movimientos (Therbligs) ---
            pdf.add_page()
            pdf.set_font('Arial', 'B', 14)
            pdf.cell(0, 10, "12. Analisis de Micro-movimientos (Therbligs)", 0, 1)
            
            pdf.set_font('Arial', 'I', 10)
            therblig_exp = (
                "Los Therbligs representan los movimientos elementales realizados por un operario. Mediante IA se han "
                "rastreado los micro-movimientos de 'Coger' (Grasp) y 'Soltar' (Release) durante cada paso. "
                "Un exceso de estos movimientos puede indicar ineficiencia en el diseño del puesto de trabajo."
            )
            pdf.multi_cell(0, 5, therblig_exp.encode('latin-1', 'replace').decode('latin-1'), 0, 'J')
            pdf.ln(3)

            pdf.set_font('Arial', 'B', 9)
            pdf.set_fill_color(52, 152, 219)
            pdf.set_text_color(255, 255, 255)
            pdf.cell(60, 9, "Tarea", 1, 0, 'C', True)
            pdf.cell(60, 9, "Operador", 1, 0, 'C', True)
            pdf.cell(70, 9, "Micro-movimiento Predominante", 1, 1, 'C', True)
            
            pdf.set_text_color(0, 0, 0)
            pdf.set_font('Arial', '', 8)
            fill = False
            for m in measurements:
                for s in m.get("splits", []):
                    therblig = s.get("therblig", "N/A")
                    if therblig != "N/A" and therblig != "ESPERANDO MANO...":
                        pdf.cell(60, 8, f" {s.get('activity', 'N/A')[:30]}", 1, 0, 'L', fill)
                        pdf.cell(60, 8, f" {s.get('operator', 'N/A')[:30]}", 1, 0, 'L', fill)
                        pdf.cell(70, 8, f" {therblig}", 1, 1, 'C', fill)
                        fill = not fill
            pdf.ln(10)

            # --- SECCION 13: Observaciones y Recomendaciones Finales ---
            if observations or recommendations:
                pdf.add_page()
                pdf.set_font('Arial', 'B', 14)
                pdf.set_text_color(44, 62, 80)
                pdf.cell(0, 10, "13. Observaciones y Recomendaciones del Autor", 0, 1)
                pdf.ln(5)
                
                if observations:
                    pdf.set_font('Arial', 'B', 11)
                    pdf.set_fill_color(240, 240, 240)
                    pdf.cell(0, 8, " Observaciones Tecnicas:", 0, 1, 'L', True)
                    pdf.set_font('Arial', '', 10)
                    pdf.set_text_color(0, 0, 0)
                    pdf.multi_cell(0, 6, observations.encode('latin-1', 'replace').decode('latin-1'), 0, 'J')
                    pdf.ln(5)
                
                if recommendations:
                    pdf.set_font('Arial', 'B', 11)
                    pdf.set_fill_color(230, 245, 230)
                    pdf.cell(0, 8, " Recomendaciones de Mejora (Ingenieria):", 0, 1, 'L', True)
                    pdf.set_font('Arial', 'I', 10)
                    pdf.set_text_color(0, 0, 0)
                    pdf.multi_cell(0, 6, recommendations.encode('latin-1', 'replace').decode('latin-1'), 0, 'J')
                    pdf.ln(5)

            pdf.output(out_path)
            messagebox.showinfo("Reporte Exportado", f"Informe visual guardado en:\n{out_path}")
        except Exception as e:
            messagebox.showerror("Error de Generación", f"Ocurrió un error al procesar el reporte: {str(e)}")

    def generate_instructions_pdf(self):
        default_filename = f"Guia_Detallada_CronoGrulla_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf"
        out_path = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            initialfile=default_filename,
            title="Guardar Guia Detallada Como...",
            filetypes=[("Archivos PDF", "*.pdf")]
        )
        if not out_path: return
        
        pdf = PremiumReportPDF()
        pdf.add_page()
        
        # TITULO Y VERSION
        pdf.set_font('Arial', 'B', 20)
        pdf.set_text_color(26, 54, 93)
        pdf.cell(0, 15, "GUIA COMPLETA DE USUARIO: CRONOGRULLA", 0, 1, 'C')
        pdf.set_font('Arial', '', 10)
        pdf.cell(0, 5, f"Version del Sistema: 2.5 (Edicion Industrial) | Fecha: {datetime.now().strftime('%d/%m/%Y')}", 0, 1, 'C')
        pdf.ln(10)

        def section_title(text):
            pdf.set_font('Arial', 'B', 14)
            pdf.set_text_color(44, 62, 80)
            pdf.set_fill_color(230, 240, 250)
            pdf.cell(0, 10, f"  {text}", 0, 1, 'L', True)
            pdf.ln(2)
            pdf.set_text_color(0, 0, 0)

        def item_desc(name, desc):
            pdf.set_font('Arial', 'B', 10)
            pdf.cell(45, 6, f" o {name}:", 0, 0)
            pdf.set_font('Arial', '', 10)
            pdf.multi_cell(0, 6, desc.encode('latin-1', 'replace').decode('latin-1'))
            pdf.ln(1)

        # 1. PESTAÑA: CONFIGURACION DEL ESTUDIO
        section_title("1. PESTAÑA: CONFIGURACION DEL ESTUDIO")
        item_desc("Datos de Proyecto", "Campos para definir el nombre del estudio, el modelo de origami y la meta de unidades.")
        item_desc("Selector de Camara", "Menu plegable para elegir la fuente de video (Webcam integrada o externa).")
        item_desc("Botones [+] y [-]", "Permiten agregar o eliminar pasos del proceso de fabricacion.")
        item_desc("Tabla de Tareas", "Asignacion de nombres de tareas y vinculacion con cada Operador responsable.")
        item_desc("Ambiente Inicial", "Ingreso manual de Luxometria y Sonometria base antes de la captura.")
        item_desc("[Ir a Estudio]", "Boton azul que valida la configuracion y desbloquea el monitoreo visual.")
        pdf.ln(5)

        # 2. PESTAÑA: ESTUDIO EN TIEMPO REAL
        section_title("2. PESTAÑA: ESTUDIO EN TIEMPO REAL (MONITOREO)")
        item_desc("[Iniciar Camara]", "Activa el reconocimiento de gestos. Se deben visualizar los Bounding Boxes sobre los operarios.")
        item_desc("[Iniciar Estudio]", "Boton VERDE que sincroniza reloj y sensores. Inicia formalmente la toma de tiempos.")
        item_desc("[Pausar]", "Detiene el tiempo ante interrupciones no planeadas (ej: llamadas, accidentes).")
        item_desc("[Finalizar]", "Boton ROJO que cierra la sesion de grabacion y congela los datos para auditoria.")
        pdf.ln(5)

        # 3. PESTAÑA: DATOS Y TABLA
        section_title("3. PESTAÑA: DATOS Y TABLA (AUDITORIA)")
        item_desc("Tabla de Tiempos", "Visualizacion en vivo de cada ciclo capturado. Permite detectar errores de toma.")
        item_desc("[Eliminar]", "Boton para borrar filas de tiempos erraticos (ej: gestos accidentales).")
        item_desc("[Exportar Excel]", "Genera un archivo .xlsx para calculos externos avanzados.")
        item_desc("[Importar OCR]", "Carga datos extraidos de monitoreos de video para sensores de Lux y dB.")
        item_desc("Editor Ambiental", "Ventana para limpiar datos de sensores mediante botones [Seleccionar Todo] y [Limpiar].")
        pdf.ln(5)

        pdf.add_page()
        # 4. PESTAÑA: EVIDENCIA VISUAL
        section_title("4. PESTAÑA: EVIDENCIA VISUAL (GALERIA)")
        item_desc("Miniaturas", "Muestra la fotografia tomada en el instante exacto del gesto de la palma.")
        item_desc("[Combinar Ciclos]", "Funcion avanzada para agrupar varios ciclos unitarios y compararlos como un 'Lote'.")
        pdf.ln(5)

        # 5. PESTAÑA: GENERAR REPORTE
        section_title("5. PESTAÑA: GENERAR REPORTE (FIN DEL PROCESO)")
        item_desc("[Seleccionar Logo]", "Carga un archivo de imagen para el encabezado del informe PDF.")
        item_desc("Campos de Texto", "Aqui se redactan las Observaciones del Autor y Recomendaciones de Ingenieria.")
        item_desc("[Generar PDF]", "Procesa todo el estudio y crea el informe tecnico final con graficos integrados.")
        item_desc("[Generar Manual]", "Crea este documento de guia para el usuario final.")

        pdf.ln(10)
        pdf.set_font('Arial', 'B', 10)
        pdf.set_fill_color(255, 230, 230)
        pdf.multi_cell(0, 8, "ADVERTENCIA: Para que el sistema detecte la palma, asegurese de no tener objetos que oculten sus manos durante el proceso.".encode('latin-1', 'replace').decode('latin-1'), 1, 'C', True)

        try:
            pdf.output(out_path)
            messagebox.showinfo("Documentacion Lista", f"Guia detallada generada en:\n{out_path}")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo guardar la guia: {e}")
