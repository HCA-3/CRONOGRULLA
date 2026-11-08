import numpy as np
import matplotlib.pyplot as plt
from scipy import stats
import os

# Set random seed for reproducibility of random vector generation
np.random.seed(42)

# Parameters
n_points = 50
m_target = 0.72
r2_target = 0.77
r_target = np.sqrt(r2_target)

# 1. Generate realistic X data: Postural Deviation (degrees) between 5 and 45
x = np.random.uniform(5, 45, n_points)
x_mean = np.mean(x)
x_std = np.std(x, ddof=1)

# Standardize X
x_scaled = (x - x_mean) / x_std

# 2. Generate a random vector Z
z = np.random.normal(0, 1, n_points)

# Remove the projection of x_scaled from Z to make it orthogonal
projection = np.dot(z, x_scaled) / np.dot(x_scaled, x_scaled) * x_scaled
w = z - projection

# Center and scale the orthogonal vector W
w = w - np.mean(w)
w_scaled = w / np.std(w, ddof=1)

# 3. Combine to get standard Y with correlation exactly r_target
y_scaled = r_target * x_scaled + np.sqrt(1 - r2_target) * w_scaled

# 4. Scale Y to achieve the target slope
# Since slope = r * (std_y / std_x) => std_y = (slope * std_x) / r
y_std_target = (m_target * x_std) / r_target
# Shift mean of Y to a realistic value, e.g., 20 seconds
y_mean_target = 20.0

y = y_scaled * y_std_target + y_mean_target

# Verify metrics using scipy linregress
slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)
r_squared = r_value ** 2

print(f"Verified slope (m): {slope:.4f}")
print(f"Verified R-squared: {r_squared:.4f}")

# 5. Visual styling for academic publication (IEEE style)
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['font.sans-serif'] = ['DejaVu Sans', 'Arial', 'Helvetica']
plt.rcParams['axes.edgecolor'] = '#333333'
plt.rcParams['axes.linewidth'] = 0.8
plt.rcParams['xtick.color'] = '#333333'
plt.rcParams['ytick.color'] = '#333333'

fig, ax = plt.subplots(figsize=(6, 4.5), dpi=300)

# Scatter plot: Navy blue points with slight transparency and white border
ax.scatter(x, y, color='#1f4e79', edgecolor='w', s=55, alpha=0.9, label='Mediciones del Sistema', zorder=3)

# Regression line: Dotted crimson red
x_line = np.linspace(min(x) - 2, max(x) + 2, 100)
y_line = slope * x_line + intercept
ax.plot(x_line, y_line, color='#d9534f', linestyle='--', linewidth=1.8, label='Línea de Regresión', zorder=4)

# Grid: subtle and dotted
ax.grid(True, linestyle=':', alpha=0.6, color='#cccccc', zorder=1)

# Labels
ax.set_xlabel('Desviación Postural (°)', fontsize=10, fontweight='normal', color='#111111')
ax.set_ylabel('Tiempo de Ejecución (s)', fontsize=10, fontweight='normal', color='#111111')
ax.set_title('Análisis de Regresión: Tiempo de Ejecución vs. Desviación Postural', fontsize=11, fontweight='bold', pad=12, color='#111111')

# Add textbox in the bottom right corner showing R^2 and slope
text_box_content = f"$R^2 = {r_squared:.2f}$\n$m = {slope:.2f}$"
props = dict(boxstyle='round,pad=0.5', facecolor='#fcfcfc', edgecolor='#cccccc', alpha=0.9)
ax.text(0.72, 0.15, text_box_content, transform=ax.transAxes, fontsize=10,
        verticalalignment='bottom', bbox=props)

# Layout improvements
ax.set_xlim(min(x) - 3, max(x) + 3)
ax.set_ylim(min(y) - 2, max(y) + 2)
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.tick_params(labelsize=9)
ax.legend(loc='upper left', frameon=True, facecolor='#ffffff', edgecolor='#e2e2e2', fontsize=9)

plt.tight_layout()

# Save path
desktop_path = r"C:\Users\dsant\Desktop\grafica_regresion.png"
plt.savefig(desktop_path, dpi=300, bbox_inches='tight')
print(f"Graph saved successfully to {desktop_path}")
