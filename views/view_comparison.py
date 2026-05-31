import customtkinter as ctk
import tkinter as tk
from tkinter import ttk
import numpy as np

class ComparisonView(ctk.CTkFrame):
    def __init__(self, master, app):
        super().__init__(master, fg_color="transparent")
        self.app = app
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        self.build_ui()

    def build_ui(self):
        header_f = ctk.CTkFrame(self, fg_color="transparent")
        header_f.pack(fill="x", padx=40, pady=20)
        
        ctk.CTkLabel(header_f, text="📊 Comparativa Automática de Operarios", 
                      font=ctk.CTkFont(size=26, weight="bold")).pack(side="left")
        
        ctk.CTkButton(header_f, text="🔄 Actualizar Datos", fg_color="#3498db", 
                  command=self.update_comparison).pack(side="right", padx=5)
        ctk.CTkButton(header_f, text="ℹ️ Fórmulas", fg_color=("#95a5a6", "#6b7b80"),
                  command=self.show_formulas).pack(side="right", padx=5)

        # Contenedor de la tabla
        self.table_container = ctk.CTkFrame(self, corner_radius=15, fg_color=("#ffffff", "#1e293b"))
        self.table_container.pack(fill="both", expand=True, padx=40, pady=(0, 20))
        
        # Estilo de la tabla
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Comparison.Treeview", 
                        background="#1e293b", 
                        foreground="white", 
                        fieldbackground="#1e293b", 
                        rowheight=35)
        style.configure("Comparison.Treeview.Heading", 
                        background="#0f172a", 
                        foreground="white", 
                        font=('Arial', 11, 'bold'))
        
        cols = ("Operador", "Ciclos", "T. Promedio", "T. Mínimo", "T. Máximo", "Eficiencia", "Estado")
        self.tree = ttk.Treeview(self.table_container, columns=cols, show="headings", style="Comparison.Treeview")
        
        for col in cols:
            self.tree.heading(col, text=col)
            self.tree.column(col, anchor="center", width=120)

        self.tree.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Resumen inferior
        self.summary_lbl = ctk.CTkLabel(self, text="", font=ctk.CTkFont(size=14, slant="italic"))
        self.summary_lbl.pack(pady=10)

        self.update_comparison()

    def show_formulas(self):
        """Muestra un modal explicando las fórmulas usadas para calcular los porcentajes."""
        dlg = ctk.CTkToplevel(self)
        dlg.title("ℹ️ Fórmulas — Comparativa Operarios")
        dlg.geometry("760x520")
        dlg.resizable(True, True)
        dlg.grab_set()

        header = ctk.CTkFrame(dlg, fg_color=("#1a0533", "#1a0533"))
        header.pack(fill="x")
        ctk.CTkLabel(header, text="Fórmulas y origen de datos", font=ctk.CTkFont(size=16, weight="bold"),
                     text_color="#ffffff").pack(side="left", padx=16, pady=12)

        scroll = ctk.CTkScrollableFrame(dlg, corner_radius=0)
        scroll.pack(fill="both", expand=True, padx=12, pady=12)

        text = (
            "Origen de datos:\n"
            "- Se usan las mediciones guardadas en 'measurements' → cada 'measurement' contiene 'splits'.\n"
            "- Para cada split se toma 'operator' y 'duration' (segundos).\n\n"
            "Cálculo mostrado en la tabla:\n"
            "- Ciclos: número de duraciones registradas para el operario.\n"
            "- T. Promedio: media aritmética de las duraciones → avg = mean(times).\n"
            "- T. Mínimo / Máximo: min(times) / max(times).\n\n"
            "Cálculo del porcentaje (Eficiencia):\n"
            "- Se identifica el mejor promedio (el más bajo): best_avg = min({avg_i}).\n"
            "- Para cada operario: efficiency = (best_avg / avg) * 100  (si avg>0).\n"
            "  Ejemplo: si best_avg=8s y avg=10s → efficiency = (8/10)*100 = 80%.\n\n"
            "Clasificación por estado:\n"
            "- efficiency >= 90 → '⭐ Excelente'\n"
            "- efficiency >= 75 → '✅ Óptimo'\n"
            "- else → '⚠️ Mejorable'\n\n"
            "Notas y alternativas recomendadas:\n"
            "- Asegúrate que 'duration' esté en segundos y sea mayor que 0, valores 0 distorsionan el cálculo.\n"
            "- Actualmente la referencia es el operario más rápido. Si prefieres otra referencia, se puede cambiar por:\n"
            "  • un tiempo estándar configurable (T_est): efficiency = (T_est / avg)*100\n"
            "  • la mediana de promedios: best_avg = median({avg_i})\n"
            "  • o el promedio global: best_avg = min(mean_all) según la métrica deseada.\n\n"
            "¿Quieres que cambie la referencia a mediana o a un tiempo estándar configurable?"
        )

        ctk.CTkLabel(scroll, text=text, justify="left", wraplength=700, font=ctk.CTkFont(size=12)).pack(padx=8, pady=8)

    def update_comparison(self):
        # Limpiar tabla
        for item in self.tree.get_children():
            self.tree.delete(item)

        measurements = self.app.data.get("measurements", [])
        if not measurements:
            self.summary_lbl.configure(text="No hay datos de ciclos registrados para comparar.")
            return

        # Procesar datos por operador
        op_stats = {}
        for m in measurements:
            for s in m.get("splits", []):
                op = s.get("operator", "Sin Asignar")
                if op not in op_stats:
                    op_stats[op] = []
                op_stats[op].append(s["duration"])

        if not op_stats:
            self.summary_lbl.configure(text="No se encontraron datos vinculados a operadores.")
            return

        all_avgs = []
        rows = []
        
        for op, times in op_stats.items():
            n = len(times)
            avg = np.mean(times)
            t_min = np.min(times)
            t_max = np.max(times)
            all_avgs.append(avg)
            rows.append({
                "op": op,
                "n": n,
                "avg": avg,
                "min": t_min,
                "max": t_max
            })

        # Calcular eficiencia relativa al mejor promedio
        best_avg = min(all_avgs) if all_avgs else 0
        
        for row in rows:
            efficiency = (best_avg / row["avg"] * 100) if row["avg"] > 0 else 0
            
            # Estado basado en eficiencia
            if efficiency >= 90: status = "⭐ Excelente"
            elif efficiency >= 75: status = "✅ Óptimo"
            else: status = "⚠️ Mejorable"

            self.tree.insert("", "end", values=(
                row["op"],
                row["n"],
                f"{row['avg']:.2f}s",
                f"{row['min']:.2f}s",
                f"{row['max']:.2f}s",
                f"{efficiency:.1f}%",
                status
            ))

        self.summary_lbl.configure(text=f"Comparativa basada en {len(measurements)} ciclos completos.")
