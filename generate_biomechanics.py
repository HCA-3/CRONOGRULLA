import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches

# Coordinates of the joints
H = np.array([2.0, 7.0])     # Shoulder (Hombro)
C = np.array([2.0, 2.5])     # Elbow (Codo)
M = np.array([5.5, 3.2])     # Wrist (Muñeca)

# Plot configuration
fig, ax = plt.subplots(figsize=(6.5, 6.5), dpi=300)
ax.set_facecolor('white')
fig.patch.set_facecolor('white')

# 1. Draw stylized background body outline (shoulder, torso, arm)
# We draw the arm contour using filled polygons/paths with a very soft grey
arm_color = '#f0f2f5'
outline_color = '#d0d4dc'

# Outer contour approximation of a flexed arm
arm_outline_x = [
    1.2, 1.6, 2.2, 2.6, 2.4, 2.2, 2.1, 2.0, 2.0, 2.3, 3.5, 5.0, 5.8, 6.2, 5.9, 5.5, 4.5, 3.0, 1.8, 1.2
]
arm_outline_y = [
    7.5, 7.8, 7.8, 7.2, 5.0, 3.5, 2.2, 1.9, 1.7, 1.8, 2.2, 2.6, 2.9, 3.2, 3.6, 3.5, 3.0, 2.6, 2.6, 5.0
]

# Plot stylized shadow/contour of the arm
ax.fill(arm_outline_x, arm_outline_y, color=arm_color, zorder=1)
ax.plot(arm_outline_x, arm_outline_y, color=outline_color, linewidth=1.5, zorder=2)

# 2. Draw Vector Arrows (Shoulder to Elbow, Elbow to Wrist)
# v_HC (Shoulder -> Elbow)
arrow_hc = patches.FancyArrowPatch(
    posA=H, posB=C,
    arrowstyle='-|>',
    mutation_scale=15,
    linewidth=2.0,
    color='#2c3e50',
    zorder=5
)
ax.add_patch(arrow_hc)

# v_CM (Elbow -> Wrist)
arrow_cm = patches.FancyArrowPatch(
    posA=C, posB=M,
    arrowstyle='-|>',
    mutation_scale=15,
    linewidth=2.0,
    color='#2c3e50',
    zorder=5
)
ax.add_patch(arrow_cm)

# 3. Draw Landmarks (MediaPipe-style joints)
joint_color = '#27ae60'  # Elegant green for MediaPipe landmarks
ax.scatter([H[0], C[0], M[0]], [H[1], C[1], M[1]], color=joint_color, s=100, zorder=6, edgecolors='white', linewidths=1.5)

# Label landmarks
ax.text(H[0]-0.3, H[1]+0.3, 'Hombro\n(Shoulder)', fontsize=9, fontweight='semibold', color='#34495e', ha='right', va='bottom')
ax.text(C[0]-0.4, C[1]-0.4, 'Codo\n(Elbow)', fontsize=9, fontweight='semibold', color='#34495e', ha='right', va='top')
ax.text(M[0]+0.3, M[1]+0.3, 'Muñeca\n(Wrist)', fontsize=9, fontweight='semibold', color='#34495e', ha='left', va='bottom')

# 4. Draw angle arc at the elbow
# Angle theta calculation
v_ch = H - C
v_cm = M - C
angle_ch = np.arctan2(v_ch[1], v_ch[0])
angle_cm = np.arctan2(v_cm[1], v_cm[0])

# Draw internal angle arc
arc_radius = 0.8
angle_start = np.degrees(angle_cm)
angle_end = np.degrees(angle_ch)
# Arc patch
arc = patches.Arc(
    xy=C,
    width=arc_radius * 2,
    height=arc_radius * 2,
    angle=0,
    theta1=angle_start,
    theta2=angle_end,
    color='#e74c3c',
    linewidth=2.0,
    zorder=4
)
ax.add_patch(arc)

# 5. Label vectors and angle
# Label v_HC
ax.text(H[0]+0.35, (H[1]+C[1])/2, r'$\mathbf{\vec{v}_{HC}}$', fontsize=12, color='#2c3e50', fontweight='bold', va='center')
# Label v_CM
ax.text((C[0]+M[0])/2 - 0.1, (C[1]+M[1])/2 + 0.35, r'$\mathbf{\vec{v}_{CM}}$', fontsize=12, color='#2c3e50', fontweight='bold', ha='center')
# Label theta (inside the angle)
# Calculate theta bisector vector for placing label
bisector_angle = (angle_ch + angle_cm) / 2
label_pos = C + (arc_radius + 0.4) * np.array([np.cos(bisector_angle), np.sin(bisector_angle)])
ax.text(label_pos[0], label_pos[1], r'$\theta$', fontsize=14, color='#e74c3c', fontweight='bold', ha='center', va='center')

# Final plot formatting
ax.set_xlim(0.5, 7.0)
ax.set_ylim(0.5, 8.5)
ax.set_aspect('equal')

# Hide axes completely for clean vector illustration style
ax.axis('off')

# Title
plt.title('Modelo Biomecánico del Brazo: Vectores y Ángulo Articular', fontsize=11, fontweight='bold', color='#2c3e50', pad=15)

plt.tight_layout()

# Save path
desktop_path = r"C:\Users\dsant\Desktop\ilustracion_biomecanica.png"
plt.savefig(desktop_path, dpi=300, bbox_inches='tight', facecolor='white')
print(f"Biomechanics illustration saved successfully to {desktop_path}")
