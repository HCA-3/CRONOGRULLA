import numpy as np
import matplotlib.pyplot as plt
import os

# Set random seed for consistent synthetic times
np.random.seed(24)

# List of 12 logical assembly tasks for 'Grulla 5-S'
tasks = [
    "T1. Plegar papel base",
    "T2. Definir pliegues cabeza",
    "T3. Doblar alas superior",
    "T4. Marcar cuerpo central",
    "T5. Ensamblar soporte",
    "T6. Plegar cola",
    "T7. Ajustar pico anterior",
    "T8. Perfilar contorno lateral",
    "T9. Unir pestañas base",
    "T10. Marcar patas inferior",
    "T11. Asegurar pliegue final",
    "T12. Inspección de calidad"
]

# Generate synthetic times (between 4 and 12 seconds) for 11 tasks
times = np.round(np.random.uniform(4.0, 12.0, len(tasks)), 2)

# Set Task 10 (index 9) to exactly 17.55 seconds (bottleneck)
times[9] = 17.55

# Visual styling for academic publication (IEEE style)
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['font.sans-serif'] = ['DejaVu Sans', 'Arial', 'Helvetica']
plt.rcParams['axes.edgecolor'] = '#333333'
plt.rcParams['axes.linewidth'] = 0.8
plt.rcParams['xtick.color'] = '#333333'
plt.rcParams['ytick.color'] = '#333333'

# We use a horizontal bar chart because the labels are relatively long
fig, ax = plt.subplots(figsize=(8.5, 5.5), dpi=300)

# Colors: steel blue for normal tasks, red for the bottleneck (Task 10)
colors = ['#4682B4' if i != 9 else '#D9534F' for i in range(len(tasks))]

# Draw the horizontal bars
bars = ax.barh(tasks, times, color=colors, edgecolor='none', height=0.65)

# Add data labels at the end of each bar
for bar in bars:
    width = bar.get_width()
    ax.text(width + 0.3, bar.get_y() + bar.get_height()/2, f'{width:.2f} s',
            va='center', ha='left', fontsize=9, color='#111111', fontweight='semibold')

# Set labels and title
ax.set_xlabel('Tiempo Promedio (s)', fontsize=10.5, color='#111111', labelpad=8)
ax.set_ylabel('Tareas de Ensamblaje', fontsize=10.5, color='#111111', labelpad=8)
ax.set_title('Grulla 5-S: Comparación de Tiempos Promedios por Tarea de Ensamblaje',
             fontsize=12, fontweight='bold', pad=15, color='#111111')

# Grid lines: subtle and vertical dotted lines (since it's a horizontal bar chart)
ax.grid(True, axis='x', linestyle=':', alpha=0.5, color='#cccccc', zorder=0)
ax.set_axisbelow(True)

# Adjust axes limits
ax.set_xlim(0, 21)
ax.invert_yaxis()  # Put T1 at the top

# Hide top and right spines
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.tick_params(labelsize=9.5)

# Highlight bottleneck callout with a legend / patch
import matplotlib.patches as mpatches
normal_patch = mpatches.Patch(color='#4682B4', label='Tareas Estándar')
bottleneck_patch = mpatches.Patch(color='#D9534F', label='Restricción del Sistema (Cuello de Botella)')
ax.legend(handles=[normal_patch, bottleneck_patch], loc='lower right', frameon=True, facecolor='#ffffff', edgecolor='#e2e2e2', fontsize=9)

plt.tight_layout()

# Save path on Desktop
desktop_path = r"C:\Users\dsant\Desktop\grafico_barras_grulla.png"
plt.savefig(desktop_path, dpi=300, bbox_inches='tight')
print(f"Bar chart successfully saved to {desktop_path}")
