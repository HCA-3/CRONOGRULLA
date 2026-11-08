import math

# Probar la matemática de proyección 3D
def rotate_point(x, y, z, yaw, pitch):
    # Rotación en Yaw (alrededor del eje Y)
    cos_y = math.cos(yaw)
    sin_y = math.sin(yaw)
    x1 = x * cos_y - z * sin_y
    z1 = x * sin_y + z * cos_y
    
    # Rotación en Pitch (alrededor del eje X)
    cos_p = math.cos(pitch)
    sin_p = math.sin(pitch)
    y2 = y * cos_p - z1 * sin_p
    z2 = y * sin_p + z1 * cos_p
    
    return x1, y2, z2

def project_point(x, y, z, cx, cy, zoom, fov=600):
    scale = (fov / (fov + z)) * zoom
    u = cx + x * scale
    v = cy + y * scale
    return u, v, z

# Prueba con punto de columna
pt = (0, -10, -35) # Espalda alta
rx, ry, rz = rotate_point(pt[0], pt[1], pt[2], math.radians(0), 0)
u, v, z = project_point(rx, ry, rz, 250, 250, 1.0)
print(f"Vista Frontal (0 deg): Espalda z={rz:.1f} (debe ser negativo, fondo)")

rx, ry, rz = rotate_point(pt[0], pt[1], pt[2], math.radians(180), 0)
u, v, z = project_point(rx, ry, rz, 250, 250, 1.0)
print(f"Vista Espalda (180 deg): Espalda z={rz:.1f} (debe ser positivo, primer plano)")

assert rz > 0, "Al rotar 180°, la espalda debe estar al frente"
print("¡Matemática 3D de rotación 360° verificada con éxito!")

