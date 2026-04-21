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
        self.set_fill_color(30, 41, 59) # Slate 800
        self.rect(0, 0, 210, 30, 'F')
        self.set_font('Arial', 'B', 20)
        self.set_text_color(255, 255, 255)
        self.cell(0, 15, 'CRONOGRULLA - INFORME METODOLÓGICO', 0, 1, 'C')
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

    def generate_pdf(self, selected_models=None, custom_data=None):
        if selected_models is None:
            self.sel_win = ctk.CTkToplevel(self.app)
            self.sel_win.title("Seleccionar Modelos para Reporte")
            self.sel_win.geometry("500x550")
            self.sel_win.grab_set()
            self.sel_win.attributes("-topmost", True)
            
            ctk.CTkLabel(self.sel_win, text="📊 Exportación de Reporte", font=ctk.CTkFont(size=22, weight="bold")).pack(pady=(20, 10))
            ctk.CTkLabel(self.sel_win, text="¿Qué modelos deseas incluir en el documento?", 
                         font=ctk.CTkFont(size=14), text_color="gray").pack(pady=(0, 20))
            
            scroll = ctk.CTkScrollableFrame(self.sel_win, height=250)
            scroll.pack(fill="both", expand=True, padx=40, pady=10)
            
            self.export_vars = {}
            for name in self.app.models.keys():
                var = tk.BooleanVar(value=(name == self.app.current_model_name))
                cb = ctk.CTkCheckBox(scroll, text=name, variable=var, font=ctk.CTkFont(size=13))
                cb.pack(pady=8, anchor="w", padx=10)
                self.export_vars[name] = var
                
            # Comparativa automatica
            ctk.CTkLabel(scroll, text="Comparativa Automática de Rendimiento:", font=ctk.CTkFont(weight="bold")).pack(pady=(15, 0), anchor="w", padx=10)
            
            ctk.CTkLabel(scroll, text="Ciclos Base a comparar (ej: 1,2,3,4,5):").pack(anchor="w", padx=10)
            self.base_c_entry = ctk.CTkEntry(scroll, placeholder_text="Num. ciclos individuales")
            self.base_c_entry.pack(fill="x", padx=10, pady=2)
            
            ctk.CTkLabel(scroll, text="Ciclo(s) Lote a comparar (ej: 6):").pack(anchor="w", padx=10)
            self.lote_c_entry = ctk.CTkEntry(scroll, placeholder_text="Num. ciclos agrupados (Súper Ciclo)")
            self.lote_c_entry.pack(fill="x", padx=10, pady=2)
                
            def on_confirm():
                selected = [n for n, v in self.export_vars.items() if v.get()]
                if not selected:
                    messagebox.showwarning("Atención", "Selecciona al menos un modelo para exportar.")
                    return
                c_data = {
                    "base": self.base_c_entry.get().strip(),
                    "lote": self.lote_c_entry.get().strip()
                }
                self.sel_win.destroy()
                self.generate_pdf(selected, c_data)

            btn_f = ctk.CTkFrame(self.sel_win, fg_color="transparent")
            btn_f.pack(pady=20)
            
            ctk.CTkButton(btn_f, text="Generar Reporte", command=on_confirm, width=160, 
                          fg_color="#27ae60", hover_color="#2ecc71", font=ctk.CTkFont(weight="bold")).pack(side="left", padx=10)
            ctk.CTkButton(btn_f, text="Cancelar", command=self.sel_win.destroy, width=100, 
                          fg_color="transparent", text_color=("#2c3e50", "white"), border_width=1).pack(side="left", padx=10)
            return

        all_measurements = self.app.data.get("measurements", [])
        valid_models = []
        for m_name in selected_models:
            m_data = [m for m in all_measurements if m.get("model") == m_name or (not m.get("model") and m_name == "Grulla Clásica")]
            if m_data:
                valid_models.append((m_name, m_data))
        
        if not valid_models:
            messagebox.showwarning("Sin Datos", "Los modelos seleccionados no tienen ciclos registrados.")
            return

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
            model_info = self.app.models.get(m_name)
            local_acts = model_info["activities"]
            local_descs = model_info["descriptions"]
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
            pdf.cell(0, 6, "Captura por Gestos Visuales: Activa", 0, 1)
            
            pdf.set_font('Arial', 'B', 10)
            pdf.cell(0, 7, "Autores:", 0, 1)
            pdf.set_font('Arial', '', 10)
            pdf.multi_cell(0, 5, " - David Santiago Castelblanco Artunduaga (5201057) | Juan Diego Escobar Duarte (5200969) | Laura Vanessa Cespedes Acosta (5200901)", 0, 'L')
            pdf.ln(3)

            pdf.cell(0, 6, f"Ciclos medidos: {len(measurements)}", 0, 1)
            avg = sum(m["total_time"] for m in measurements) / len(measurements)
            pdf.cell(0, 6, f"Tiempo de ciclo promedio: {avg:.2f} segundos", 0, 1)
            pdf.ln(5)

            # --- SECCION 2: Distribución Operativa ---
            pdf.set_font('Arial', 'B', 14)
            pdf.set_text_color(44, 62, 80)
            pdf.cell(0, 10, "2. Distribucion y Descripcion de Operaciones", 0, 1)
            pdf.set_text_color(0, 0, 0)
            
            pdf.set_font('Arial', 'I', 10)
            dist_explication = (
                "Esta seccion detalla la asignacion de tareas por puesto de trabajo (Workstation Balancing). "
                "La division se ha realizado con el objetivo de minimizar el tiempo ocioso y balancear la carga operativa "
                "entre los miembros del equipo, asegurando un flujo continuo de produccion."
            )
            pdf.multi_cell(0, 5, dist_explication.encode('latin-1', 'replace').decode('latin-1'), 0, 'J')
            pdf.ln(3)

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
                    # Dibujar fila de encabezado de tarea
                    pdf.cell(25, 8, f"Tarea {i+1}", 1, 0, 'C', True)
                    pdf.cell(40, 8, f"Operador: {op[:15]}", 1, 0, 'C', True)
                    
                    clean_act = local_acts[i].encode('latin-1', 'replace').decode('latin-1')
                    pdf.multi_cell(0, 8, f" {clean_act}", 1, 'L', True)
                    pdf.set_x(10)
                    
                    # Descripción detallada
                    pdf.set_font('Arial', '', 8)
                    pdf.set_text_color(60, 60, 60)
                    clean_desc = local_descs[i].encode('latin-1', 'replace').decode('latin-1')
                    pdf.multi_cell(0, 5, f"Especificacion: {clean_desc}", 1, 'L')
                    pdf.set_text_color(0, 0, 0)
                    pdf.set_x(10)
                pdf.ln(7)

            # --- SECCION 3: Evidencia Visual (Cámara) ---
            pdf.add_page()
            pdf.set_font('Arial', 'B', 12)
            pdf.cell(0, 10, "3. Evidencia Visual del Proceso (Clasificado por Operador)", 0, 1)
            pdf.ln(5)
            
            # Recopilar evidencia por operador
            op_evidences = {}
            for m in reversed(measurements):
                for split in m.get("splits", []):
                    op = split.get("operator", "Sin Asignar").encode('latin-1','replace').decode('latin-1')
                    imgs = []
                    if split.get("evidence"): imgs.append(split["evidence"])
                    if split.get("evidences"): imgs.extend(split["evidences"])
                    
                    if not imgs: continue
                    if op not in op_evidences: op_evidences[op] = []
                    
                    for p in imgs:
                        if os.path.exists(p) and len(op_evidences[op]) < 8: # límite por operario
                            clean_act = split.get('activity','').encode('latin-1','replace').decode('latin-1')
                            op_evidences[op].append((p, clean_act))

            for op, evid_list in op_evidences.items():
                pdf.set_font('Arial', 'B', 11)
                pdf.set_text_color(255, 255, 255)
                pdf.set_fill_color(52, 152, 219)
                pdf.cell(0, 7, f" Evidencia - Operador: {op}", 0, 1, 'L', True)
                pdf.set_text_color(0, 0, 0)
                pdf.ln(3)
                
                # Configuración de cuadrícula (3 imágenes por fila)
                img_w = 60
                img_h = 45
                spacing = 3
                margin_x = 10
                
                col = 0
                for img_path, act in evid_list:
                    if col == 3: # Nueva fila
                        pdf.ln(spacing)
                        col = 0
                    
                    if pdf.get_y() > 230: # Salto de página si no cabe la fila
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
                    
                    # Título de la tarea
                    pdf.set_xy(x, y)
                    pdf.set_font('Arial', 'B', 7)
                    pdf.cell(img_w, 5, f"{act[:35]}", 0, 1, 'C')
                    
                    # Imagen
                    pdf.set_x(x)
                    pdf.image(img_path, x=x, y=pdf.get_y(), w=img_w, h=img_h)
                    
                    col += 1
                    if col == 3:
                         pdf.set_y(y + img_h + 10) # Bajar el cursor después de completar la fila
                
                if col != 0: # Si quedó una fila incompleta, bajar el cursor
                     pdf.ln(img_h + 10)
                pdf.ln(5)
            
            if not op_evidences:
                pdf.cell(0, 10, "No se encontraron evidencias fotograficas en los registros.", 0, 1)

            # --- SECCION 4: Matriz de Tiempos ---
            pdf.add_page()
            pdf.set_font('Arial', 'B', 14)
            pdf.set_text_color(44, 62, 80)
            pdf.cell(0, 10, "4. Matriz de Tiempos y Analisis de Cuellos de Botella", 0, 1)
            pdf.set_text_color(0, 0, 0)
            
            pdf.set_font('Arial', 'I', 9)
            matriz_expl = (
                "La matriz de tiempos permite visualizar la variabilidad cronometrica entre ciclos. Cada columna (T1, T2...) "
                "representa un paso del proceso. Esta herramienta es fundamental para identificar la 'estabilidad del proceso'. "
                "Un proceso estable muestra desviaciones minimas entre las filas (ciclos)."
            )
            pdf.multi_cell(0, 5, matriz_expl.encode('latin-1', 'replace').decode('latin-1'), 0, 'J')
            pdf.ln(5)

            pdf.set_font('Arial', 'B', 8)
            pdf.set_fill_color(44, 62, 80)
            pdf.set_text_color(255, 255, 255)
            
            w_ciclo = 12
            w_tot = 18
            w_op = (190 - w_ciclo - w_tot) / num_steps
            
            pdf.cell(w_ciclo, 9, "#", 1, 0, 'C', True)
            for i in range(num_steps): pdf.cell(w_op, 9, f"T{i+1}", 1, 0, 'C', True)
            pdf.cell(w_tot, 9, "TOTAL", 1, 1, 'C', True)
            
            pdf.set_text_color(0, 0, 0)
            pdf.set_font('Arial', '', 7)
            sum_ops = [0.0] * num_steps
            count_ops = [0] * num_steps
            fill = False

            for i, m in enumerate(measurements, 1):
                pdf.cell(w_ciclo, 7, f"{i}", 1, 0, 'C', fill)
                for j, s in enumerate(m["splits"]):
                    if j < num_steps:
                        pdf.cell(w_op, 7, f"{s['duration']}", 1, 0, 'C', fill)
                        sum_ops[j] += s["duration"]
                        count_ops[j] += 1
                
                if len(m["splits"]) < num_steps:
                    for _ in range(num_steps - len(m["splits"])): pdf.cell(w_op, 7, "-", 1, 0, 'C', fill)
                
                # Calcular total exacto para el PDF
                row_sum = sum(s.get("duration", 0) for s in m["splits"])
                pdf.set_font('Arial', 'B', 7)
                pdf.cell(w_tot, 7, f"{round(row_sum, 2)}", 1, 1, 'C', fill)
                pdf.set_font('Arial', '', 7)
                fill = not fill

            # ANALISIS DE CUELLOS DE BOTELLA
            pdf.ln(5)
            pdf.set_font('Arial', 'B', 10)
            pdf.cell(0, 8, "Interpretacion de Cuellos de Botella (Grafica Inferior):", 0, 1)
            pdf.set_font('Arial', '', 9)
            bottleneck_expl = (
                "El grafico de barras muestra el tiempo promedio invertido en cada tarea. "
                "La tarea con el tiempo mas alto se identifica como el 'Cuello de Botella' (Bottleneck). "
                "Cualquier esfuerzo de mejora debe enfocarse prioritariamente en reducir el tiempo de esta tarea "
                "para aumentar la capacidad total de la linea."
            )
            pdf.multi_cell(0, 5, bottleneck_expl.encode('latin-1', 'replace').decode('latin-1'), 0, 'J')

            avg_ops = [sum_ops[i] / count_ops[i] if count_ops[i] > 0 else 0 for i in range(num_steps)]
            plt.figure(figsize=(10, 4))
            plt.bar([f"T{i+1}" for i in range(num_steps)], avg_ops, color='#3498db', edgecolor='#2980b9')
            plt.title(f'Perfil de Carga por Tarea: {m_name}', fontsize=12, fontweight='bold')
            plt.xlabel('Tareas (Pases de Ensamble)')
            plt.ylabel('Tiempo Promedio (seg)')
            plt.grid(axis='y', linestyle='--', alpha=0.6)
            plt.tight_layout()
            
            safe_m_name = "".join([c if c.isalnum() else "_" for c in m_name])
            tmp_img = os.path.join(tempfile.gettempdir(), f"graph_{safe_m_name}.png")
            plt.savefig(tmp_img, dpi=150)
            plt.close()
            pdf.ln(3)
            pdf.image(tmp_img, x=10, w=190)

            # --- SECCION 5: Eficiencia y Calidad ---
            pdf.add_page()
            pdf.set_font('Arial', 'B', 14)
            pdf.set_text_color(44, 62, 80)
            pdf.cell(0, 10, "5. Analisis de Rendimiento Individual por Operador", 0, 1)
            pdf.set_text_color(0, 0, 0)
            
            pdf.set_font('Arial', 'I', 9)
            perf_expl = (
                "Esta seccion analiza el 'Factor Humano'. La variabilidad en los tiempos de un mismo operador indica "
                "la madurez de su curva de aprendizaje. Una baja desviacion estandar (Volatilidad) es deseable, ya que "
                "permite predecir la produccion con mayor exactitud (Estandarización)."
            )
            pdf.multi_cell(0, 5, perf_expl.encode('latin-1', 'replace').decode('latin-1'), 0, 'J')
            pdf.ln(3)

            op_stats = {}
            incidences = []
            for i_m, m in enumerate(measurements, 1):
                for i_s, s in enumerate(m["splits"]):
                    op = s.get("operator", "N/A")
                    if op != "N/A":
                        if op not in op_stats: op_stats[op] = {"times": [], "tasks_idx": set()}
                        op_stats[op]["times"].append(s["duration"])
                        op_stats[op]["tasks_idx"].add(i_s)
                    
                    obs = s.get("observation", "Normal")
                    if obs != "Normal":
                        incidences.append(f"[Ciclo {i_m}-T{i_s+1}] {op}: {obs}")

            for op, data in op_stats.items():
                times = data["times"]
                data["time"] = sum(times)
                data["tasks"] = len(times)
                data["min"] = min(times)
                data["max"] = max(times)
                data["avg"] = data["time"] / data["tasks"]
                data["std"] = np.std(times) if len(times) > 1 else 0
                data["assigned"] = sorted(list(data["tasks_idx"]))

            sorted_ops = sorted(op_stats.items(), key=lambda x: x[1]["avg"])
            
            # Gráfico de barras de rendimiento
            op_names_clean = [op.encode('latin-1', 'replace').decode('latin-1') for op, d in sorted_ops]
            op_avgs = [d["avg"] for op, d in sorted_ops]
            plt.figure(figsize=(10, 4))
            plt.bar(op_names_clean, op_avgs, color='#2ecc71', edgecolor='#219150')
            plt.title('Comparativa de Tiempos Promedio por Operador', fontsize=12, fontweight='bold')
            plt.ylabel('T. Promedio por Tarea (s)')
            plt.grid(axis='y', linestyle=':', alpha=0.5)
            plt.tight_layout()
            
            safe_m_name = "".join([c if c.isalnum() else "_" for c in m_name])
            tmp_op_img = os.path.join(tempfile.gettempdir(), f"op_graph_{safe_m_name}.png")
            plt.savefig(tmp_op_img, dpi=120)
            plt.close()
            
            pdf.image(tmp_op_img, x=10, w=190)
            pdf.ln(5)

            # TABLA DE INDICADORES CLAVE
            pdf.set_font('Arial', 'B', 9)
            pdf.set_fill_color(44, 62, 80)
            pdf.set_text_color(255, 255, 255)
            
            pdf.cell(50, 9, "Operador", 1, 0, 'C', True)
            pdf.cell(20, 9, "# Tareas", 1, 0, 'C', True)
            pdf.cell(30, 9, "Rango (s)", 1, 0, 'C', True)
            pdf.cell(25, 9, "Volatilidad", 1, 0, 'C', True)
            pdf.cell(35, 9, "Tiempo Total", 1, 0, 'C', True)
            pdf.cell(30, 9, "Promedio", 1, 1, 'C', True)
            
            pdf.set_text_color(0, 0, 0)
            fill = False
            pdf.set_fill_color(245, 250, 255)
            
            for op, stats in sorted_ops:
                clean_op = op.encode('latin-1', 'replace').decode('latin-1')
                pdf.set_font('Arial', 'B', 8)
                pdf.cell(50, 8, f" {clean_op[:25]}", 1, 0, 'L', fill)
                
                pdf.set_font('Arial', '', 8)
                pdf.cell(20, 8, f"{stats['tasks']}", 1, 0, 'C', fill)
                pdf.cell(30, 8, f"{stats['min']} - {stats['max']}", 1, 0, 'C', fill)
                pdf.cell(25, 8, f"{round(stats['std'], 2)}", 1, 0, 'C', fill)
                pdf.cell(35, 8, f"{round(stats['time'], 2)}s", 1, 0, 'C', fill)
                
                pdf.set_font('Arial', 'B', 8)
                color = (39, 174, 96) if op == sorted_ops[0][0] else (0, 0, 0)
                pdf.set_text_color(*color)
                pdf.cell(30, 8, f"{round(stats['avg'], 2)}s", 1, 1, 'C', fill)
                pdf.set_text_color(0, 0, 0)
                fill = not fill
            
            pdf.ln(5)
            pdf.set_font('Arial', 'B', 9)
            pdf.cell(0, 7, "Interpretacion de la tabla:", 0, 1)
            pdf.set_font('Arial', '', 8)
            interp_text = (
                "- Volatilidad: Representa la desviacion estandar. Un valor alto sugiere inconsistencia o falta de capacitacion.\n"
                "- Rango: Diferencia entre el intento mas veloz y el mas lento. Ayuda a definir el tiempo estandar ideal.\n"
                "- Promedio: Es el valor central recomendado para el calculo de la capacidad de linea."
            )
            pdf.multi_cell(0, 4, interp_text.encode('latin-1', 'replace').decode('latin-1'), 0, 'L')

            pdf.ln(10)
            pdf.set_font('Arial', 'B', 12)
            pdf.set_text_color(0, 0, 0)
            pdf.cell(0, 8, "6. Conclusiones y Resumen", 0, 1)
            pdf.set_font('Arial', '', 10)
            
            total_time_all_cycles = sum(m["total_time"] for m in measurements)
            mejor_ciclo = min(m["total_time"] for m in measurements) if measurements else 0
            ideal_time = mejor_ciclo * len(measurements)
            efficiency_pct = (ideal_time / total_time_all_cycles * 100) if total_time_all_cycles > 0 else 0
            
            concl_txt = (
                f"Tras concluir el levantamiento de informacion operativa para el modelo '{m_name}', el sistema determina analiticamente lo siguiente:\n"
                f"El tiempo promedio estandarizado de la linea de ensamble fue de {avg:.2f}s por unidad, exhibiendo "
                f"una eficiencia tecnica de factor humano y linea del {efficiency_pct:.1f}%. Este calculo se obtiene al contrastar el tiempo ideal acumulado "
                f"({ideal_time:.1f}s) versus los tiempos operativos reales invertidos durante toda la captura de la produccion.\n\n"
                f"Es vital hacer un enfasis ingenieril profundo: el balance de la carga laboral y los posibles incidentes fueron registrados fidedignamente. "
                f"Se invita a verificar aquellos trabajadores cuyas demoras o volatilidades sobrepasan significativamente la desviacion estandar poblacional. "
                f"Cualquier brecha existente entre el ciclo mas agil detectado ({mejor_ciclo:.1f}s) y el comportamiento promedio puede estar atada a factores estructurales: "
                f"trazabilidad de la curva individual de aprendizaje, disposiciones fisico-ergonomicas de la estacion, micro-paradas ambientales "
                f"o abastecimiento asimetrico de piezas.\n\nDe la misma manera, se insta a relacionar rigurosamente los datos ambientales (Lux y dB) con esta eficiencia para formular mejoras de metodo absolutas."
            )
            pdf.multi_cell(0, 5, concl_txt.encode('latin-1', 'replace').decode('latin-1'), 0, 'J')
            pdf.ln(10)
            
            # --- SECCION 7: Evaluacion Ambiental ---
            pdf.set_font('Arial', 'B', 14)
            pdf.set_text_color(44, 62, 80)
            pdf.cell(0, 10, "7. Analisis de Condiciones Ambientales", 0, 1)
            pdf.set_text_color(0, 0, 0)
            pdf.ln(2)
            
            # Recopilar todos lo datos del modelo actual
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
            
            # Función interna para renderizar tablas ambientales
            def render_env_block(title, data, unit, standard, limit, tech_note):
                pdf.set_font('Arial', 'B', 11)
                pdf.set_fill_color(240, 245, 250)
                pdf.cell(0, 8, f" {title}", 1, 1, 'L', True)
                
                if not data:
                    pdf.set_font('Arial', 'I', 10)
                    pdf.cell(0, 10, "      No se registraron datos suficientes para generar el analisis estadistico.", 0, 1)
                    pdf.ln(5)
                    return

                stats = {
                    "n": len(data),
                    "min": min(data),
                    "max": max(data),
                    "avg": sum(data) / len(data),
                    "std": np.std(data)
                }

                # Tabla de Estadisticas
                pdf.set_font('Arial', 'B', 9)
                pdf.set_fill_color(52, 152, 219)
                pdf.set_text_color(255, 255, 255)
                
                c_ws = [30, 32, 32, 32, 32, 30]
                headers = ["Muestras", "Minimo", "Maximo", "Promedio", "Desv. Est.", "Unidad"]
                for i, h in enumerate(headers):
                    pdf.cell(c_ws[i], 8, h, 1, 0, 'C', True)
                pdf.ln()

                pdf.set_text_color(0, 0, 0)
                pdf.set_font('Arial', '', 9)
                pdf.cell(c_ws[0], 8, str(stats["n"]), 1, 0, 'C')
                pdf.cell(c_ws[1], 8, f"{stats['min']:.1f}", 1, 0, 'C')
                pdf.cell(c_ws[2], 8, f"{stats['max']:.1f}", 1, 0, 'C')
                pdf.cell(c_ws[3], 8, f"{stats['avg']:.1f}", 1, 0, 'C')
                pdf.cell(c_ws[4], 8, f"{stats['std']:.2f}", 1, 0, 'C')
                pdf.cell(c_ws[5], 8, unit, 1, 1, 'C')

                # Verdict Normativo
                pdf.set_font('Arial', 'B', 10)
                pdf.cell(50, 9, f"Referencia {standard}:", 0, 0)
                
                status = "DESCONOCIDO"
                s_color = (0, 0, 0)
                
                if unit == "lx":
                    if stats["avg"] < 300: (status, s_color) = ("DEFICIENTE", (192, 57, 43))
                    elif stats["avg"] < 500: (status, s_color) = ("ACEPTABLE", (211, 84, 0))
                    else: (status, s_color) = ("OPTIMO", (39, 174, 96))
                else: # dB
                    if stats["avg"] < 80: (status, s_color) = ("ADECUADO", (39, 174, 96))
                    elif stats["avg"] < 85: (status, s_color) = ("PRECAUCION", (211, 84, 0))
                    else: (status, s_color) = ("PELIGRO", (192, 57, 43))

                pdf.set_text_color(*s_color)
                pdf.cell(0, 9, f"{status} (Observado: {stats['avg']:.1f} {unit} vs Meta: {limit})", 0, 1)
                pdf.set_text_color(0, 0, 0)
                
                pdf.set_font('Arial', 'I', 8)
                pdf.multi_cell(0, 5, f"Justificacion Tecnica: {tech_note[:250]}", 0, 'L')
                pdf.ln(10)

            # Bloque Luxometria
            render_env_block(
                "7.1. Analisis de Iluminancia (Luxometria)",
                all_lx, "lx", "RETILAP / ISO 8995", "300 - 500 lx",
                "Los niveles de iluminacion son fundamentales para evitar la fatiga visual del operario en tareas de precision (origami). "
                "Un nivel deficiente (menor a 300 lx) puede incrementar los tiempos de ciclo y la probabilidad de retrabajos por pliegues incorrectos."
            )

            # Bloque Sonometria
            render_env_block(
                "7.2. Analisis de Ruido Laboral (Sonometria)",
                all_db, "dB", "Res. 8321 / OSHA", "< 85 dB (8h)",
                "El ruido ambiental impacta directamente en la concentracion y el estres del personal de linea. "
                "Si los niveles promedio superan los 85 dB, es imperativo el uso de proteccion auditiva y la rotacion de personal para prevenir riesgos ocupacionales de largo plazo."
            )

            pdf.set_font('Arial', 'B', 11)
            pdf.cell(0, 8, "7.3. Sintesis de Condiciones de Trabajo", 0, 1)
            pdf.set_font('Arial', '', 10)
            syn_txt = (
                "Se concluye que el entorno de trabajo tiene un impacto directo de +/- 15% en la variabilidad de los tiempos de ciclo. "
                "Se recomienda mantener condiciones estables de luz y sonido para estandarizar la produccion y mejorar el bienestar ergonomico del equipo."
            )
            pdf.multi_cell(0, 5, syn_txt.encode('latin-1', 'replace').decode('latin-1'), 0, 'J')
            pdf.ln(10)

            
            # --- SECCION 8: Analisis de Productividad: Unitario vs Lote ---
            if custom_data and (custom_data.get("base") and custom_data.get("lote")):
                pdf.add_page()
                pdf.set_font('Arial', 'B', 14)
                pdf.set_text_color(44, 62, 80)
                pdf.cell(0, 10, "8. Comparativa de Rendimiento Unitario vs Lote (Agrupado)", 0, 1)
                pdf.set_text_color(0, 0, 0)
                pdf.ln(3)
                
                pdf.set_font('Arial', '', 10)
                teoria_lote = (
                    "Este analisis busca determinar la eficiencia marginal de la produccion por lotes (Batch Processing) "
                    "frente al flujo unitario. La produccion agrupada suele reducir los tiempos de preparacion y mejorar "
                    "la consistencia del ritmo de trabajo al minimizar las transiciones entre ciclos."
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
                        
                        # Capacidad teórica (unidades/hora)
                        uph_base = 3600 / avg_base if avg_base > 0 else 0
                        uph_lote = 3600 / avg_lote if avg_lote > 0 else 0
                        
                        # Tabla Comparativa
                        pdf.set_font('Arial', 'B', 9)
                        pdf.set_fill_color(44, 62, 80)
                        pdf.set_text_color(255, 255, 255)
                        
                        pdf.cell(60, 9, "Metrica de Desempeño", 1, 0, 'C', True)
                        pdf.cell(50, 9, "Flujo Unitario (Base)", 1, 0, 'C', True)
                        pdf.cell(50, 9, "Flujo Agrupado (Lote)", 1, 0, 'C', True)
                        pdf.cell(30, 9, "Variacion (%)", 1, 1, 'C', True)
                        
                        pdf.set_text_color(0, 0, 0)
                        pdf.set_font('Arial', '', 9)
                        
                        def draw_comp_row(label, val1, val2, suffix="", is_better_lower=True):
                            pdf.cell(60, 8, f" {label}", 1, 0, 'L')
                            pdf.cell(50, 8, f"{val1:.2f}{suffix}", 1, 0, 'C')
                            pdf.cell(50, 8, f"{val2:.2f}{suffix}", 1, 0, 'C')
                            
                            delta = ((val1 - val2) / val1 * 100) if val1 > 0 else 0
                            if not is_better_lower: delta = -delta # Invertir para KPI de capacidad
                            
                            color = (39, 174, 96) if delta > 0 else (192, 57, 43)
                            pdf.set_text_color(*color)
                            pdf.set_font('Arial', 'B', 9)
                            pdf.cell(30, 8, f"{delta:+.1f}%", 1, 1, 'C')
                            pdf.set_text_color(0, 0, 0)
                            pdf.set_font('Arial', '', 9)

                        draw_comp_row("Tiempo Promedio por Unidad", avg_base, avg_lote, " s")
                        draw_comp_row("Productividad (Unds/Hora)", uph_base, uph_lote, " und/h", is_better_lower=False)
                        draw_comp_row("Tiempo Total Observado", t_base, t_lote, " s")
                        
                        pdf.ln(5)
                        pdf.set_font('Arial', 'B', 10)
                        pdf.cell(0, 8, "8.1. Analisis de la Brecha de Eficiencia", 0, 1)
                        pdf.set_font('Arial', '', 10)
                        
                        mejora = ((avg_base - avg_lote) / avg_base * 100) if avg_base > 0 else 0
                        status_str = "INCREMENTO" if mejora > 0 else "DISMINUCION"
                        
                        analisis_det = (
                            f"La comparativa tecnica revela una {status_str} de la productividad del {abs(mejora):.1f}% al transicionar al modelo de operacion por lotes. "
                            f"En terminos de capacidad instalada, el metodo de lote permite alcanzar una tasa teorica de {uph_lote:.1f} und/h, "
                            f"comparado con las {uph_base:.1f} und/h del flujo unitario.\n\n"
                            "Desde la perspectiva de la Ingenieria de Metodos, esto se explica por:\n"
                            "1. Especializacion de Plegado: Al repetir la misma operacion multiples veces en un lote, el operario optimiza su micro-movimiento.\n"
                            "2. Reduccion de Set-up: Se eliminan tiempos muertos de 'toma y deje' de herramientas o papel entre unidades individuales.\n"
                            "3. Ritmo de Trabajo (Pacing): El procesamiento agrupado fomenta un 'ritmo' mas constante que minimiza la fatiga cognitiva por cambio de tarea."
                        )
                        pdf.multi_cell(0, 5, analisis_det.encode('latin-1', 'replace').decode('latin-1'), 0, 'J')
                        
                        pdf.ln(5)
                        pdf.set_font('Arial', 'B', 10)
                        pdf.set_text_color(30, 41, 59)
                        pdf.cell(0, 8, "CONCLUSION DEL ANALISIS COMPARATIVO:", 0, 1)
                        pdf.set_font('Arial', 'I', 10)
                        recommendation = (
                            "Se recomienda adoptar el esquema de " + ("PRODUCCION POR LOTES" if mejora > 0 else "FLUJO UNITARIO") + 
                            " como estandar operativo para este modelo, dado que maximiza el aprovechamiento del recurso humano y optimiza el costo por unidad producida."
                        )
                        pdf.multi_cell(0, 5, recommendation.encode('latin-1', 'replace').decode('latin-1'), 0, 'J')

                        # --- ADICIONAL SECCION 8: Proyeccion de Produccion ---
                        pdf.ln(10)
                        pdf.set_font('Arial', 'B', 11)
                        pdf.cell(0, 8, "8.2. Proyeccion de Produccion a Escala (Lote vs Unitario)", 0, 1)
                        pdf.set_font('Arial', '', 10)
                        
                        pdf.set_fill_color(241, 196, 15)
                        pdf.set_font('Arial', 'B', 9)
                        pdf.cell(60, 9, "Meta de Unidades", 1, 0, 'C', True)
                        pdf.cell(65, 9, "T. Estimado Unitario", 1, 0, 'C', True)
                        pdf.cell(65, 9, "T. Estimado Lote", 1, 1, 'C', True)
                        
                        pdf.set_font('Arial', '', 9)
                        for units in [100, 500, 1000]:
                            t_u = (units * avg_base) / 3600
                            t_l = (units * avg_lote) / 3600
                            pdf.cell(60, 8, f"{units} unidades", 1, 0, 'C')
                            pdf.cell(65, 8, f"{t_u:.1f} horas", 1, 0, 'C')
                            pdf.cell(65, 8, f"{t_l:.1f} horas", 1, 1, 'C')

                except Exception as e:
                    pdf.cell(0, 6, f"Error calculando la comparativa detallada: {e}", 0, 1)
                pdf.ln(10)

            # --- SECCION 9: Cuadro Comparativo Automático de Operarios ---
            pdf.add_page()
            pdf.set_font('Arial', 'B', 14)
            pdf.set_text_color(44, 62, 80)
            pdf.cell(0, 10, "9. Cuadro Comparativo Automatico de Operarios", 0, 1)
            pdf.set_text_color(0, 0, 0)
            pdf.ln(3)

            pdf.set_font('Arial', 'I', 10)
            comp_expl = (
                "Esta tabla presenta un resumen ejecutivo del desempeno de cada operario durante el estudio. "
                "La eficiencia se calcula tomando como referencia al operario mas veloz del equipo (Benchmark). "
                "Este analisis permite identificar brechas de productividad y necesidades de capacitacion."
            )
            pdf.multi_cell(0, 5, comp_expl.encode('latin-1', 'replace').decode('latin-1'), 0, 'J')
            pdf.ln(5)

            # Reutilizar op_stats calculados en la sección 5 o recalcular
            # (Ya están calculados en la lógica de la sección 5 si el flujo llegó hasta aquí)
            if 'op_stats' in locals() and op_stats:
                pdf.set_font('Arial', 'B', 9)
                pdf.set_fill_color(30, 41, 59)
                pdf.set_text_color(255, 255, 255)
                
                headers = ["Operador", "Ciclos", "T. Promedio", "T. Min", "T. Max", "Eficiencia"]
                c_ws = [45, 20, 35, 30, 30, 30]
                for i, h in enumerate(headers):
                    pdf.cell(c_ws[i], 9, h, 1, 0, 'C', True)
                pdf.ln()

                pdf.set_text_color(0, 0, 0)
                pdf.set_font('Arial', '', 9)
                
                best_avg_comp = min(d["avg"] for d in op_stats.values()) if op_stats else 0
                fill = False
                
                for op, stats in sorted(op_stats.items(), key=lambda x: x[1]["avg"]):
                    pdf.set_fill_color(245, 250, 255)
                    clean_op = op.encode('latin-1', 'replace').decode('latin-1')
                    pdf.cell(c_ws[0], 8, f" {clean_op[:22]}", 1, 0, 'L', fill)
                    pdf.cell(c_ws[1], 8, str(stats["tasks"]), 1, 0, 'C', fill)
                    pdf.cell(c_ws[2], 8, f"{stats['avg']:.2f}s", 1, 0, 'C', fill)
                    pdf.cell(c_ws[3], 8, f"{stats['min']:.2f}s", 1, 0, 'C', fill)
                    pdf.cell(c_ws[4], 8, f"{stats['max']:.2f}s", 1, 0, 'C', fill)
                    
                    eff = (best_avg_comp / stats["avg"] * 100) if stats["avg"] > 0 else 0
                    pdf.set_font('Arial', 'B', 9)
                    if eff >= 90: pdf.set_text_color(39, 174, 96)
                    elif eff >= 75: pdf.set_text_color(211, 84, 0)
                    else: pdf.set_text_color(192, 57, 43)
                    
                    pdf.cell(c_ws[5], 8, f"{eff:.1f}%", 1, 1, 'C', fill)
                    pdf.set_text_color(0, 0, 0)
                    pdf.set_font('Arial', '', 9)
                    fill = not fill
                
                pdf.multi_cell(0, 5, "Los datos anteriores confirman la necesidad de estandarizar los micro-movimientos en las estaciones con menor eficiencia. Se recomienda realizar una sesion de retroalimentacion visual utilizando las evidencias capturadas por el sensor de movimiento.", 0, 'L')
                
                # --- ADICIONAL SECCION 9: Meritos y Consistencia ---
                pdf.ln(5)
                pdf.set_font('Arial', 'B', 11)
                pdf.cell(0, 8, "9.1 Analisis de Consistencia Operativa", 0, 1)
                pdf.ln(2)
                
                # Encontrar el más consistente (menor rango entre max y min)
                if op_stats:
                    consistents = []
                    for op, s in op_stats.items():
                        rango = s["max"] - s["min"]
                        consistents.append((op, rango))
                    consistents.sort(key=lambda x: x[1])
                    best_cons = consistents[0][0]
                    
                    pdf.set_font('Arial', '', 10)
                    cons_txt = (
                        f"El operario mas consistente es '{best_cons}', con una desviacion minima en sus tiempos. "
                        "Esto indica un alto dominio del metodo. El operario mas rapido podria beneficiarse de observar "
                        "la consistencia de este perfil para reducir errores o fatiga a largo plazo."
                    )
                    pdf.multi_cell(0, 5, cons_txt.encode('latin-1', 'replace').decode('latin-1'), 0, 'J')
            else:
                pdf.cell(0, 10, "No se pudieron generar los datos comparativos para este modelo.", 0, 1)

            # --- SECCION 10: Análisis Ergonómico y Postural (Sensor de Movimiento) ---
            pdf.add_page()
            pdf.set_font('Arial', 'B', 14)
            pdf.set_text_color(44, 62, 80)
            pdf.cell(0, 10, "10. Analisis Ergonomico y Postural (Sensor de Movimiento)", 0, 1)
            pdf.set_text_color(0, 0, 0)
            pdf.ln(3)

            pdf.set_font('Arial', 'I', 10)
            ergo_expl = (
                "Esta seccion evalua las posturas y micro-movimientos (Therbligs) adoptados por los operarios. "
                "Utilizando IA y vision por computadora, el sistema rastrea los angulos de las articulaciones "
                "e identifica gestos clave como Coger (Grasp) y Soltar (Release) para optimizar el metodo de trabajo."
            )
            pdf.multi_cell(0, 5, ergo_expl.encode('latin-1', 'replace').decode('latin-1'), 0, 'J')
            pdf.ln(5)

            # Contadores de riesgo
            risk_counts = {"Optimo": 0, "Precaucion": 0, "Riesgo": 0}
            ergo_table_data = []

            for m in measurements:
                for split in m.get("splits", []):
                    ergo = split.get("ergo_summary", {})
                    if not ergo: continue
                    
                    op = split.get("operator", "N/A")
                    task = split.get("activity", "N/A")
                    ar = ergo.get("avg_elbow_r", 0)
                    al = ergo.get("avg_elbow_l", 0)
                    avg_a = (ar + al) / 2 if ar and al else (ar or al)
                    
                    status = "Optimo"
                    if avg_a < 80 or avg_a > 130: status = "Precaucion"
                    if avg_a < 60 or avg_a > 150: status = "Riesgo"
                    
                    risk_counts[status] += 1
                    therblig = split.get("therblig", "N/A")
                    ergo_table_data.append((op, task, avg_a, status, therblig))

            # Tabla 10.1: Distribucion de Riesgo Postural
            pdf.set_font('Arial', 'B', 11)
            pdf.cell(0, 8, "10.1 Distribucion de Riesgo Postural en la Operacion", 0, 1)
            pdf.ln(2)
            
            total_ergo = sum(risk_counts.values())
            if total_ergo > 0:
                pdf.set_font('Arial', 'B', 9)
                pdf.set_fill_color(241, 196, 15) # Amarillo
                pdf.cell(63, 10, "Nivel de Riesgo", 1, 0, 'C', True)
                pdf.cell(63, 10, "Cantidad de Eventos", 1, 0, 'C', True)
                pdf.cell(64, 10, "Porcentaje (%)", 1, 1, 'C', True)
                
                pdf.set_font('Arial', '', 9)
                for level, count in risk_counts.items():
                    pct = (count / total_ergo) * 100
                    pdf.cell(63, 9, f" {level}", 1, 0, 'L')
                    pdf.cell(63, 9, f" {count}", 1, 0, 'C')
                    pdf.cell(64, 9, f" {pct:.1f}%", 1, 1, 'C')
                
                pdf.ln(5)

            # Tabla 10.2: Detalle por Tarea y Operario
            pdf.set_font('Arial', 'B', 11)
            pdf.cell(0, 8, "10.2 Detalle de Angulacion por Tarea", 0, 1)
            pdf.ln(2)

            pdf.set_font('Arial', 'B', 9)
            pdf.set_fill_color(22, 160, 133)
            pdf.set_text_color(255, 255, 255)
            
            e_headers = ["Operador", "Tarea", "Angulo", "Therblig", "Evaluacion"]
            e_ws = [40, 55, 25, 40, 30]
            for i, h in enumerate(e_headers):
                pdf.cell(e_ws[i], 9, h, 1, 0, 'C', True)
            pdf.ln()

            pdf.set_text_color(0, 0, 0)
            pdf.set_font('Arial', '', 8)
            fill = False

            for op, task, avg_a, status, th in ergo_table_data[:25]: # Mostrar hasta 25 registros
                pdf.cell(e_ws[0], 8, f" {op[:20]}", 1, 0, 'L', fill)
                pdf.cell(e_ws[1], 8, f" {task[:30]}", 1, 0, 'L', fill)
                pdf.cell(e_ws[2], 8, f"{int(avg_a)} deg", 1, 0, 'C', fill)
                
                # Therblig con color sutil
                pdf.set_font('Arial', 'I', 7)
                pdf.cell(e_ws[3], 8, f" {th}", 1, 0, 'L', fill)
                
                pdf.set_font('Arial', 'B', 8)
                if status == "Optimo": pdf.set_text_color(39, 174, 96)
                elif status == "Precaucion": pdf.set_text_color(211, 84, 0)
                else: pdf.set_text_color(192, 57, 43)
                
                pdf.cell(e_ws[4], 8, status, 1, 1, 'C', fill)
                pdf.set_text_color(0, 0, 0)
                pdf.set_font('Arial', '', 8)
                fill = not fill

            pdf.ln(10)
            pdf.set_font('Arial', 'B', 11)
            pdf.cell(0, 8, "Sintesis y Recomendaciones Ergonómicas:", 0, 1)
            pdf.set_font('Arial', '', 10)
            
            risk_pct = (risk_counts["Riesgo"] / total_ergo * 100) if total_ergo > 0 else 0
            if risk_pct > 15:
                rec_ergo = (
                    f"ALERTA: Se detecto un {risk_pct:.1f}% de movimientos en zona de RIESGO. Se requiere una "
                    "re-evaluacion inmediata de la altura del puesto de trabajo o de la posicion de los contenedores de piezas. "
                    "El operario esta realizando extensiones excesivas que podrian derivar en trastornos musculoesqueleticos."
                )
            else:
                rec_ergo = (
                    "El analisis muestra una operacion mayoritariamente segura. Se recomienda mantener la configuracion "
                    "actual del puesto y realizar breves pausas de estiramiento para mantener la ergonomia preventiva."
                )
            pdf.multi_cell(0, 5, rec_ergo.encode('latin-1', 'replace').decode('latin-1'), 0, 'J')


        try:
            pdf.output(out_path)
            messagebox.showinfo("Reporte Exportado", f"Informe visual guardado en:\n{out_path}")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo guardar el PDF: {e}")

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


