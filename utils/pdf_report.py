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
        self.cell(0, 10, f'Página {self.page_no()} | Generado automatizadamente por CronoGrulla', 0, 0, 'C')

class PDFManager:
    def __init__(self, app):
        self.app = app

    def generate_pdf(self, selected_models=None):
        if selected_models is None:
            # Ventana de selección de modelos
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
                
            def on_confirm():
                selected = [n for n, v in self.export_vars.items() if v.get()]
                if not selected:
                    messagebox.showwarning("Atención", "Selecciona al menos un modelo para exportar.")
                    return
                self.sel_win.destroy()
                self.generate_pdf(selected)

            btn_f = ctk.CTkFrame(self.sel_win, fg_color="transparent")
            btn_f.pack(pady=30)
            
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

        default_filename = f"Reporte_CronoGrulla_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf"
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
            pdf.cell(0, 6, "Tamano del origami: 15x15 cm", 0, 1)
            
            pdf.set_font('Arial', 'B', 10)
            pdf.cell(0, 7, "Autores:", 0, 1)
            pdf.set_font('Arial', '', 10)
            pdf.cell(0, 5, " - David Santiago Castelblanco Artunduaga | Juan Diego Escobar Duarte | Laura Vanessa Cespedes Acosta", 0, 1)
            pdf.ln(3)

            pdf.cell(0, 6, f"Ciclos medidos: {len(measurements)}", 0, 1)
            avg = sum(m["total_time"] for m in measurements) / len(measurements)
            pdf.cell(0, 6, f"Tiempo de ciclo promedio: {avg:.2f} segundos", 0, 1)
            pdf.ln(5)

            # --- SECCION 2: Distribución Operativa ---
            pdf.set_font('Arial', 'B', 12)
            pdf.cell(0, 10, "2. Distribucion y Descripcion de Operaciones", 0, 1)
            
            configs = {}
            for idx, m in enumerate(measurements, 1):
                config = tuple(s.get("operator", "N/A") for s in m.get("splits", []))
                if len(config) < num_steps:
                    config = config + ("N/A",) * (num_steps - len(config))
                if config not in configs: configs[config] = []
                configs[config].append(idx)
                
            for config_idx, (config_tuple, cycles) in enumerate(configs.items(), 1):
                pdf.set_font('Arial', 'B', 10)
                pdf.set_text_color(52, 152, 219)
                pdf.cell(0, 8, f"Configuración #{config_idx} (Ciclos: {', '.join(map(str, cycles))})", 0, 1)
                pdf.set_text_color(0, 0, 0)
                
                pdf.set_fill_color(220, 230, 240)
                for i in range(num_steps):
                    op = config_tuple[i] if i < len(config_tuple) else "N/A"
                    pdf.set_font('Arial', 'B', 9)
                    pdf.cell(25, 7, f"Tarch {i+1}", 1, 0, 'C', True)
                    pdf.cell(35, 7, f"Op: {op}", 1, 0, 'C', True)
                    
                    clean_act = local_acts[i].encode('latin-1', 'replace').decode('latin-1')
                    pdf.multi_cell(0, 7, f" {clean_act}", 1, 'L', True)
                    pdf.set_x(10)
                    
                    pdf.set_font('Arial', '', 8)
                    clean_desc = local_descs[i].encode('latin-1', 'replace').decode('latin-1')
                    pdf.multi_cell(0, 5, f"{clean_desc}", 1, 'L')
                    pdf.set_x(10)
                pdf.ln(5)

            # --- SECCION 3: Matriz de Tiempos ---
            pdf.add_page()
            pdf.set_font('Arial', 'B', 12)
            pdf.cell(0, 10, "3. Matriz de Tiempos Registrados (Segundos)", 0, 1)
            
            pdf.set_font('Arial', 'B', 8)
            pdf.set_fill_color(52, 152, 219)
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
                
                pdf.set_font('Arial', 'B', 7)
                pdf.cell(w_tot, 7, f"{m['total_time']}", 1, 1, 'C', fill)
                pdf.set_font('Arial', '', 7)
                fill = not fill

            avg_ops = [sum_ops[i] / count_ops[i] if count_ops[i] > 0 else 0 for i in range(num_steps)]
            plt.figure(figsize=(10, 4))
            plt.bar([f"T{i+1}" for i in range(num_steps)], avg_ops, color='#3498db')
            plt.title(f'Cuellos de Botella: {m_name}')
            plt.ylabel('Segundos')
            plt.tight_layout()
            
            tmp_img = os.path.join(tempfile.gettempdir(), f"graph_{m_name}.png")
            plt.savefig(tmp_img)
            plt.close()
            pdf.ln(5)
            pdf.image(tmp_img, x=10, w=190)

            # --- SECCION 4: Eficiencia y Calidad ---
            pdf.add_page()
            pdf.set_font('Arial', 'B', 12)
            pdf.cell(0, 10, "4. Analisis Detallado de Rendimiento por Operador", 0, 1)
            
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
            
            op_names_clean = [op.encode('latin-1', 'replace').decode('latin-1') for op, d in sorted_ops]
            op_avgs = [d["avg"] for op, d in sorted_ops]
            plt.figure(figsize=(10, 4))
            plt.bar(op_names_clean, op_avgs, color='#2ecc71', edgecolor='black')
            plt.title(f'Rendimiento Promedio Individual: {m_name}')
            plt.ylabel('Segundos (Promedio por Tarea)')
            plt.grid(axis='y', linestyle='--', alpha=0.7)
            plt.tight_layout()
            
            tmp_op_img = os.path.join(tempfile.gettempdir(), f"op_graph_{m_name}.png")
            plt.savefig(tmp_op_img)
            plt.close()
            
            pdf.image(tmp_op_img, x=10, w=190)
            pdf.ln(2)

            pdf.set_font('Arial', 'B', 8)
            pdf.set_fill_color(44, 62, 80)
            pdf.set_text_color(255, 255, 255)
            
            pdf.cell(40, 8, "Operador", 1, 0, 'C', True)
            pdf.cell(20, 8, "Tareas Asig.", 1, 0, 'C', True)
            pdf.cell(30, 8, "Rango (Min - Max)", 1, 0, 'C', True)
            pdf.cell(25, 8, "Volatilidad", 1, 0, 'C', True)
            pdf.cell(35, 8, "Total Invertido", 1, 0, 'C', True)
            pdf.cell(40, 8, "Promedio/Tarea", 1, 1, 'C', True)
            
            pdf.set_text_color(0, 0, 0)
            fill = False
            pdf.set_fill_color(240, 248, 255)
            
            for op, stats in sorted_ops:
                clean_op = op.encode('latin-1', 'replace').decode('latin-1')
                pdf.set_font('Arial', 'B', 8)
                pdf.cell(40, 7, f" {clean_op[:20]}", 1, 0, 'L', fill)
                
                pdf.set_font('Arial', '', 8)
                assigned_str = ",".join(f"T{i+1}" for i in stats["assigned"])
                if len(assigned_str) > 12: assigned_str = assigned_str[:10] + "..."
                pdf.cell(20, 7, assigned_str, 1, 0, 'C', fill)
                
                pdf.cell(30, 7, f"{stats['min']}s - {stats['max']}s", 1, 0, 'C', fill)
                pdf.cell(25, 7, f"±{round(stats['std'], 2)}s", 1, 0, 'C', fill)
                pdf.cell(35, 7, f"{round(stats['time'], 2)}s", 1, 0, 'C', fill)
                
                pdf.set_font('Arial', 'B', 8)
                if op == sorted_ops[0][0] and len(sorted_ops)>1:
                    pdf.set_text_color(39, 174, 96)
                    pdf.cell(40, 7, f"{round(stats['avg'], 2)}s (Mas Rapido)", 1, 1, 'C', fill)
                    pdf.set_text_color(0, 0, 0)
                else:
                    pdf.cell(40, 7, f"{round(stats['avg'], 2)}s", 1, 1, 'C', fill)
                    
                fill = not fill
            
            pdf.ln(5)
            pdf.set_font('Arial', 'I', 8)
            pdf.set_text_color(80, 80, 80)
            explicacion_eficiencia = (
                "Análisis de Desempeño: La gráfica y la tabla presentan el perfil operativo de cada trabajador. "
                "'Rango (Min - Max)' muestra sus tiempos más veloces y más lentos. La 'Volatilidad' (Desviación "
                "Estándar) indica qué tan constante es un operador: un número bajo significa que trabaja a un "
                "ritmo estable, mientras que un número alto puede indicar falta de experiencia o fatiga. El 'Promedio' "
                "dictamina al operario más ágil en general."
            )
            pdf.multi_cell(0, 5, explicacion_eficiencia.encode('latin-1', 'replace').decode('latin-1'), 0, 'J')
            pdf.set_x(10)
            
            pdf.ln(10)
            pdf.set_font('Arial', 'B', 12)
            pdf.set_text_color(0, 0, 0)
            pdf.cell(0, 8, "5. Registro de Incidencias de Calidad", 0, 1)
            pdf.set_font('Arial', '', 9)
            
            if not incidences:
                pdf.cell(0, 6, "No se registraron fallas de calidad en este modelo.", 0, 1)
            else:
                defect_counts = {}
                pdf.set_text_color(192, 57, 43)
                for inc in incidences:
                    obs_text = inc.split(": ", 1)[1] if ": " in inc else inc
                    clean_inc = inc.encode('latin-1', 'replace').decode('latin-1')
                    pdf.multi_cell(0, 6, clean_inc)
                    pdf.set_x(10)
                    
                    errores = obs_text.split(" | ")
                    for err in errores:
                        short_err = err[:25] + ".." if len(err) > 25 else err
                        defect_counts[short_err] = defect_counts.get(short_err, 0) + 1

                pdf.set_text_color(0, 0, 0)
                
                errores_ord = sorted(defect_counts.items(), key=lambda x: x[1], reverse=False)
                if errores_ord:
                    keys = [x[0] for x in errores_ord]
                    vals = [x[1] for x in errores_ord]
                    
                    plt.figure(figsize=(10, 4))
                    plt.barh(keys, vals, color='#e74c3c', edgecolor='black')
                    plt.title(f'Frecuencia de Incidencias - {m_name}')
                    plt.xlabel('Cantidad')
                    plt.grid(axis='x', linestyle='--', alpha=0.7)
                    
                    from matplotlib.ticker import MaxNLocator
                    plt.gca().xaxis.set_major_locator(MaxNLocator(integer=True))
                    plt.tight_layout()
                    
                    grafica_errores_path = os.path.join(tempfile.gettempdir(), f"err_{m_name}.png")
                    plt.savefig(grafica_errores_path)
                    plt.close()
                    
                    pdf.ln(5)
                    pdf.image(grafica_errores_path, x=10, w=190)

                    pdf.ln(5)
                    pdf.set_font('Arial', 'B', 10)
                    pdf.cell(0, 8, "Analisis Porcentual de Incidencias:", 0, 1)
                    pdf.set_font('Arial', '', 9)
                    
                    total_errores = sum(vals)
                    for err_name, count in reversed(errores_ord):
                        pct = (count / total_errores) * 100
                        clean_err = err_name.encode('latin-1', 'replace').decode('latin-1')
                        pdf.cell(0, 6, f" - {clean_err}: {count} ocurrencia(s) ({pct:.1f}%)", 0, 1)

            pdf.ln(8)
            pdf.set_font('Arial', 'B', 12)
            pdf.set_text_color(0, 0, 0)
            pdf.cell(0, 8, "6. Conclusiones y Resumen de Eficiencia", 0, 1)
            pdf.set_font('Arial', '', 10)
            
            total_time_all_cycles = sum(m["total_time"] for m in measurements)
            mejor_ciclo = min(m["total_time"] for m in measurements) if measurements else 0
            ideal_time = mejor_ciclo * len(measurements)
            
            efficiency_pct = (ideal_time / total_time_all_cycles * 100) if total_time_all_cycles > 0 else 0
            
            promedio_ciclo_txt = f"El estudio del modelo '{m_name}' constó de {len(measurements)} ciclos operativos. El tiempo promedio general de fabricación es de {avg:.2f} segundos, mientras que el tiempo récord (mejor ciclo) fue de {mejor_ciclo:.2f} segundos."
            pdf.multi_cell(0, 6, promedio_ciclo_txt.encode('latin-1', 'replace').decode('latin-1'))
            pdf.ln(2)
            
            concl_txt = f"Comparando el ritmo general de la línea frente al mejor tiempo registrado, se estima que el equipo operó a un {efficiency_pct:.1f}% de su capacidad ideal. Para acortar la brecha y acercarse al nivel óptimo, se recomienda re-balancear los cuellos de botella identificados en la Gráfica 3 y entrenar al personal para mitigar las deficiencias especificadas en la Sección 5."
            pdf.multi_cell(0, 6, concl_txt.encode('latin-1', 'replace').decode('latin-1'))
            pdf.ln(5)
        
        try:
            pdf.output(out_path)
            messagebox.showinfo("Reporte Exportado", f"Informe consolidado guardado en:\n{out_path}")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo guardar el PDF: {e}")

    def generate_instructions_pdf(self):
        default_filename = f"Manual_Instrucciones_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf"
        out_path = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            initialfile=default_filename,
            title="Guardar Manual de Instrucciones Como...",
            filetypes=[("Archivos PDF", "*.pdf"), ("Todos los archivos", "*.*")]
        )
        
        if not out_path:
            return
        
        pdf = PremiumReportPDF()
        pdf.add_page()
        
        # TITLE
        pdf.set_font('Arial', 'B', 16)
        pdf.set_text_color(44, 62, 80)
        pdf.cell(0, 10, "MANUAL DE USUARIO E INSTRUCCIONES DEL SOFTWARE", 0, 1, 'C')
        pdf.ln(5)
        
        pdf.set_font('Arial', '', 11)
        pdf.set_text_color(80, 80, 80)
        pdf.cell(0, 6, "Software: CronoGrulla - Ingenieria de Metodos", 0, 1, 'C')
        pdf.cell(0, 6, "Autores (Ingenieros Industriales): David Santiago Castelblanco Artunduaga (5201057)", 0, 1, 'C')
        pdf.cell(0, 6, "Juan Diego Escobar Duarte (5200969) | Laura Vanessa Cespedes Acosta (5200901)", 0, 1, 'C')
        pdf.ln(8)
        
        # 1. EXPLICACION DEL PROGRAMA
        pdf.set_font('Arial', 'B', 14)
        pdf.set_text_color(52, 152, 219)
        pdf.cell(0, 8, "1. Descripcion del Software", 0, 1, 'L')
        pdf.set_font('Arial', '', 11)
        pdf.set_text_color(0, 0, 0)
        desc_software = (
            "CronoGrulla es un software de escritorio desarrollado para apoyar los estudios de tiempos y "
            "analisis de metodos, con un enfoque en el balanceo de lineas de produccion. El programa "
            "documenta, cronometra y evalua el rendimiento de operarios en procesos estandarizados.\n\n"
            "Modulos Principales de la Aplicacion:\n\n"
            " - Dashboard: Es el panel resumen de control. Muestra metricas generales como los ciclos "
            "completados de todos los modelos, el tiempo promedio general de produccion y la cantidad "
            "de operarios activos en la linea.\n\n"
            " - Modelos Origami: Es el administrador de ensambles. Aqui se pueden crear nuevas 'recetas' "
            "o listados de pasos para diferentes productos (por defecto incluye la Grulla Clasica). Permite editar "
            "instrucciones personalizadas y visualizar PDFs de referencia adjuntos.\n\n"
            " - Equipo y Tareas: Este modulo distribuye equitativamente (balancea) los pasos de manufactura "
            "segun la cantidad de trabajadores definidos para la celula de trabajo actuando como un configurador de turnos.\n\n"
            " - Cronometrar: Es el cronometro en tiempo real que dicta las pautas y asiste paso a paso en "
            "la produccion indicando que operario debe actuar en base al balanceo previo. Ademas, permite "
            "reportar defectos o incidencias de calidad justo despues de cada tarea.\n\n"
            " - Datos y Tabla: Muestra la bitacora de recoleccion en forma de matriz, listando los tiempos "
            "en segundos de todas las tareas a lo largo de los ciclos registrados para auditar posteriormente.\n\n"
            " - Estadisticas: Grafica visualmente las metricas derivadas de los tiempos guardados "
            "mostrando claramente cuales tareas se demoran mas (cuellos de botella por operacion)."
        ).encode('latin-1', 'replace').decode('latin-1')
        pdf.multi_cell(0, 6, desc_software, 0, 'J')
        # 3. INSTRUCCIONES DE INSTALACION
        pdf.set_font('Arial', 'B', 14)
        pdf.set_text_color(52, 152, 219)
        pdf.cell(0, 8, "2. Requerimientos e Instalacion", 0, 1, 'L')
        pdf.set_font('Arial', '', 11)
        pdf.set_text_color(0, 0, 0)
        
        inst_text = (
            "Para el correcto funcionamiento de CronoGrulla, se deben cumplir los siguientes requisitos tecnicos:\n\n"
            " Requisitos del Sistema:\n"
            " - Sistema Operativo: Windows 10/11, macOS o Linux.\n"
            " - Lenguaje: Python 3.10 o superior.\n"
            " - Librerias Necesarias: customtkinter, fpdf, matplotlib, numpy.\n\n"
            " Pasos para la ejecucion:\n"
            " 1. Descomprimir el paquete de software en una carpeta local.\n"
            " 2. Abrir una terminal o consola de comandos en dicha ubicacion.\n"
            " 3. Instalar las dependencias ejecutando: pip install -r requirements.txt\n"
            " 4. Iniciar la aplicacion con el comando: python main.py\n\n"
            "Nota: El software requiere permisos de escritura en su carpeta para guardar la base de datos "
            "(craneflow_data.json) y exportar los reportes generados."
        ).encode('latin-1', 'replace').decode('latin-1')
        
        pdf.multi_cell(0, 6, inst_text, 0, 'J')
        pdf.ln(8)

        # 4. MODELOS REGISTRADOS
        pdf.add_page()
        pdf.set_font('Arial', 'B', 14)
        pdf.set_text_color(52, 152, 219)
        pdf.cell(0, 8, "3. Instructivo de Manufactura (Modelos)", 0, 1, 'L')
        pdf.ln(4)
        
        pdf.set_text_color(0, 0, 0)
        
        for model_name, model_info in self.app.models.items():
            pdf.set_font('Arial', 'B', 12)
            pdf.set_fill_color(220, 230, 240)
            clean_name = model_name.encode('latin-1', 'replace').decode('latin-1')
            pdf.cell(0, 8, f" MODELO: {clean_name}", 0, 1, 'L', True)
            pdf.ln(2)
            
            acts = model_info.get("activities", [])
            descs = model_info.get("descriptions", [])
            
            for idx in range(len(acts)):
                pdf.set_font('Arial', 'B', 10)
                pdf.set_text_color(44, 62, 80)
                clean_act = acts[idx].encode('latin-1', 'replace').decode('latin-1')
                pdf.cell(0, 6, f"{idx+1}. {clean_act}", 0, 1, 'L')
                
                pdf.set_font('Arial', '', 10)
                pdf.set_text_color(0, 0, 0)
                clean_desc = descs[idx].encode('latin-1', 'replace').decode('latin-1')
                pdf.set_x(15)
                pdf.multi_cell(0, 5, clean_desc, 0, 'J')
                pdf.ln(2)
            pdf.ln(5)
            
        try:
            pdf.output(out_path)
            messagebox.showinfo("Manual Exportado", f"Manual guardado exitosamente en:\n{out_path}")
        except Exception as e:
            messagebox.showerror("Error de Exportacion", f"No se pudo guardar el PDF.\n\nDetalles: {e}")

    def generate_source_code_pdf(self):
        default_filename = f"Code_CronoGrulla_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf"
        out_path = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            initialfile=default_filename,
            title="Guardar Código Fuente Como...",
            filetypes=[("Archivos PDF", "*.pdf"), ("Todos los archivos", "*.*")]
        )
        
        if not out_path:
            return
            
        pdf = PremiumReportPDF()
        
        # Página de Título
        pdf.add_page()
        pdf.set_font('Arial', 'B', 22)
        pdf.set_text_color(44, 62, 80)
        pdf.ln(40)
        pdf.cell(0, 20, "ANEXO: CÓDIGO FUENTE COMPLETO", 0, 1, 'C')
        pdf.set_font('Arial', 'B', 16)
        pdf.cell(0, 10, "Software CronoGrulla", 0, 1, 'C')
        pdf.ln(10)
        pdf.set_font('Arial', '', 12)
        pdf.cell(0, 10, f"Fecha de generación: {datetime.now().strftime('%d/%m/%Y %H:%M')}", 0, 1, 'C')
        
        # Lista de archivos a incluir (en orden lógico)
        files_to_include = [
            "main.py",
            "utils/pdf_report.py",
            "views/view_dashboard.py",
            "views/view_info.py",
            "views/view_models.py",
            "views/view_operators.py",
            "views/view_stats.py",
            "views/view_tables.py",
            "views/view_timer.py"
        ]
        
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        for rel_path in files_to_include:
            full_path = os.path.join(base_dir, rel_path.replace("/", os.sep))
            if not os.path.exists(full_path):
                continue
                
            pdf.add_page()
            
            # Header del archivo
            pdf.set_fill_color(240, 240, 240)
            pdf.set_font('Arial', 'B', 12)
            pdf.set_text_color(52, 152, 219)
            pdf.cell(0, 10, f" ARCHIVO: {rel_path}", 0, 1, 'L', True)
            pdf.ln(5)
            
            # Contenido del código
            try:
                with open(full_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Reemplazar caracteres no compatibles con latin-1
                clean_content = content.encode('latin-1', 'replace').decode('latin-1')
                
                pdf.set_font('Courier', '', 8)
                pdf.set_text_color(0, 0, 0)
                # Usar multi_cell para el código
                pdf.multi_cell(0, 4, clean_content)
                
            except Exception as e:
                pdf.set_font('Arial', 'I', 10)
                pdf.set_text_color(192, 57, 43)
                pdf.cell(0, 10, f"Error al leer archivo: {e}", 0, 1)

        try:
            pdf.output(out_path)
            messagebox.showinfo("Código Exportado", f"El código fuente se ha exportado correctamente a:\n{out_path}")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo generar el PDF del código: {e}")

    def generate_summary_pdf(self):
        default_filename = f"Resumen_CronoGrulla_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf"
        out_path = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            initialfile=default_filename,
            title="Guardar Resumen del Software Como...",
            filetypes=[("Archivos PDF", "*.pdf"), ("Todos los archivos", "*.*")]
        )
        
        if not out_path:
            return
            
        pdf = PremiumReportPDF()
        pdf.add_page()
        
        # TÍTULO
        pdf.set_font('Arial', 'B', 18)
        pdf.set_text_color(44, 62, 80)
        pdf.cell(0, 15, "MEMORIA DESCRIPTIVA DEL SOFTWARE", 0, 1, 'C')
        pdf.set_font('Arial', 'B', 14)
        pdf.cell(0, 10, "Proyecto: CronoGrulla", 0, 1, 'C')
        pdf.ln(10)
        
        # AUTORES
        pdf.set_fill_color(240, 240, 240)
        pdf.set_font('Arial', 'B', 11)
        pdf.cell(0, 8, " Identificacion de Autores y Titulares", 0, 1, 'L', True)
        pdf.set_font('Arial', '', 10)
        pdf.set_text_color(0, 0, 0)
        pdf.ln(2)
        pdf.cell(0, 6, " - David Santiago Castelblanco Artunduaga (ID: 5201057)", 0, 1)
        pdf.cell(0, 6, " - Juan Diego Escobar Duarte (ID: 5200969)", 0, 1)
        pdf.cell(0, 6, " - Laura Vanessa Cespedes Acosta (ID: 5200901)", 0, 1)
        pdf.ln(8)
        
        # RESUMEN EJECUTIVO
        pdf.set_font('Arial', 'B', 11)
        pdf.set_text_color(52, 152, 219)
        pdf.cell(0, 8, "Resumen General del Sistema", 0, 1, 'L')
        pdf.set_font('Arial', '', 11)
        pdf.set_text_color(0, 0, 0)
        
        summary_text = (
            "CronoGrulla es una solucion de software avanzada disenada para la optimizacion de procesos en el ambito "
            "de la Ingenieria de Metodos. Su objetivo principal es facilitar el estudio de tiempos y movimientos, "
            "permitiendo a los analistas capturar datos con precision, balancear lineas de produccion de manera "
            "equitativa y generar reportes estadisticos detallados de forma automatizada.\n\n"
            "El sistema se estructura en diversos modulos integrados que cubren el ciclo completo de un estudio de metodos. "
            "El 'Dashboard' proporciona una vision ejecutiva del rendimiento global; el modulo de 'Modelos Origami' permite "
            "estandarizar las hojas de operaciones y metodologias de ensamble; el gestor de 'Equipo y Tareas' implementa "
            "algoritmos de balanceo de carga para distribuir el trabajo segun el numero de operarios disponibles; y el "
            "'Cronometro' guiado asiste en la recoleccion de tiempos en tiempo real, integrando controles de calidad e incidencias.\n\n"
            "Desde una perspectiva tecnica, CronoGrulla destaca por su capacidad de procesar matrices de tiempos complejas "
            "para identificar cuellos de botella mediante visualizaciones graficas de rendimiento individual y grupal. "
            "La herramienta no solo digitaliza la toma de tiempos tradicional, sino que añade una capa de inteligencia "
            "analitica que calcula indicadores de eficiencia, volatilidad operativa y cumplimiento de estandares de calidad.\n\n"
            "En resumen, CronoGrulla transforma la recoleccion de datos crudos en informacion estrategica para la toma de "
            "decisiones, reduciendo el margen de error humano y optimizando los recursos en entornos de manufactura y "
            "aprendizaje academico."
        ).encode('latin-1', 'replace').decode('latin-1')
        
        pdf.multi_cell(0, 6, summary_text, 0, 'J')
        
        # FIRMA O PIE
        pdf.ln(20)
        pdf.set_font('Arial', 'I', 9)
        pdf.set_text_color(100, 100, 100)
        pdf.cell(0, 5, f"Documento generado automaticamente por el sistema CronoGrulla el {datetime.now().strftime('%d/%m/%Y')}.", 0, 1, 'C')

        try:
            pdf.output(out_path)
            messagebox.showinfo("Resumen Exportado", f"La memoria descriptiva se ha exportado correctamente a:\n{out_path}")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo generar el PDF del resumen: {e}")
