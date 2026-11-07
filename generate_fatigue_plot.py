import numpy as np
import matplotlib.pyplot as plt
from scipy import stats
import os

# Set random seed for reproducibility
np.random.seed(30)

# Generate synthetic data for 30 work cycles
cycles = np.arange(1, 31)
# Base linear growth: fatigue starts at 0.25 and rises by 0.018 per cycle
base_fatigue = 0.25 + 0.018 * cycles
# Add realistic gaussian noise to represent daily/momentary fluctuations
noise = np.random.normal(0, 0.045, len(cycles))
fatigue_index = np.clip(base_fatigue + noise, 0.0, 1.0)

# Calculate linear regression trend
slope, intercept, r_value, p_value, std_err = stats.linregress(cycles, fatigue_index)
trend_line = slope * cycles + intercept

# Define Critical Fatigue Threshold (e.g., at 0.75)
threshold = 0.75

# Visual styling for academic publication (IEEE style)
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['font.sans-serif'] = ['DejaVu Sans', 'Arial', 'Helvetica']
plt.rcParams['axes.edgecolor'] = '#333333'
plt.rcParams['axes.linewidth'] = 0.8
plt.rcParams['xtick.color'] = '#333333'
plt.rcParams['ytick.color'] = '#333333'

fig, ax = plt.subplots(figsize=(7, 4.8), dpi=300)

# Plot actual noisy measurements (individual cycle data)
ax.plot(cycles, fatigue_index, color='#7fb2e5', linestyle='-', linewidth=1.2, alpha=0.7, zorder=2)
ax.scatter(cycles, fatigue_index, color='#1f4e79', edgecolor='w', s=30, label='Índice de Fatiga Medido', zorder=3)

# Plot the regression trend line (highlighted)
ax.plot(cycles, trend_line, color='#1f4e79', linestyle='-', linewidth=2.2, label='Tendencia (Regresión Lineal)', zorder=4)

# Plot the threshold line
ax.axhline(y=threshold, color='#d9534f', linestyle='--', linewidth=1.5, label='Umbral Crítico de Fatiga', zorder=1)

# Annotate threshold line
ax.text(1, threshold + 0.02, 'Umbral Crítico de Fatiga ($F = 0.75$)', fontsize=9, color='#d9534f', fontweight='semibold')

# Set labels and title
ax.set_xlabel('Ciclos de Trabajo', fontsize=10, color='#111111')
ax.set_ylabel('Índice de Fatiga (F)', fontsize=10, color='#111111')
ax.set_title('Evolución Temporal del Índice de Fatiga (F) por Ciclo', fontsize=11, fontweight='bold', pad=12, color='#111111')

# Set limits
ax.set_xlim(0, 31)
ax.set_ylim(0.1, 1.0)
ax.set_xticks(np.arange(0, 31, 5))

# Subtle grid only on Y-axis
ax.grid(True, axis='y', linestyle=':', alpha=0.5, color='#cccccc', zorder=0)

# Hide top and right spines
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.tick_params(labelsize=9)

# Legend positioning
ax.legend(loc='lower right', frameon=True, facecolor='#ffffff', edgecolor='#e2e2e2', fontsize=9)

plt.tight_layout()

# Save path on Desktop
desktop_path = r"C:\Users\dsant\Desktop\evolucion_fatiga.png"
plt.savefig(desktop_path, dpi=300, bbox_inches='tight')
print(f"Fatigue evolution graph saved successfully to {desktop_path}")
