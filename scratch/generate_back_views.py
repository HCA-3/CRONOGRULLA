import os
import numpy as np
from PIL import Image, ImageFilter, ImageEnhance

out_dir = os.path.join("assets", "mannequin")

def create_back_view(front_path, out_path, is_female=False):
    img = Image.open(front_path).convert("RGBA")
    w, h = img.size
    data = np.array(img).copy()
    
    alpha = data[:, :, 3]
    body_mask = alpha > 30
    
    # 1. Suavizar sombras anteriores (pectoral/busto) y oscurecer levemente el tono base
    r = data[:, :, 0].astype(float)
    g = data[:, :, 1].astype(float)
    b = data[:, :, 2].astype(float)
    
    # Oscurecer un 10% el centro para simular la concavidad dorsal
    y_coords, x_coords = np.indices((h, w))
    cx = w / 2.0
    
    # Surco de la columna vertebral (línea vertical oscura central)
    spine_dist = np.abs(x_coords - cx)
    spine_mask = (spine_dist < 4) & (y_coords > h * 0.22) & (y_coords < h * 0.88) & body_mask
    r[spine_mask] *= 0.65
    g[spine_mask] *= 0.65
    b[spine_mask] *= 0.65

    # Relieve de las escápulas (omóplatos a ambos lados)
    scap_left = (np.abs(x_coords - (cx - w*0.20)) < w*0.12) & (y_coords > h * 0.26) & (y_coords < h * 0.46) & body_mask
    scap_right = (np.abs(x_coords - (cx + w*0.20)) < w*0.12) & (y_coords > h * 0.26) & (y_coords < h * 0.46) & body_mask
    
    r[scap_left | scap_right] = np.clip(r[scap_left | scap_right] * 1.15, 0, 255)
    g[scap_left | scap_right] = np.clip(g[scap_left | scap_right] * 1.15, 0, 255)
    b[scap_left | scap_right] = np.clip(b[scap_left | scap_right] * 1.15, 0, 255)

    # Nuca / Cabeza posterior (occipital liso)
    neck_head = (y_coords < h * 0.24) & body_mask
    r[neck_head] *= 0.92
    g[neck_head] *= 0.92
    b[neck_head] *= 0.92

    data[:, :, 0] = np.clip(r, 0, 255).astype(np.uint8)
    data[:, :, 1] = np.clip(g, 0, 255).astype(np.uint8)
    data[:, :, 2] = np.clip(b, 0, 255).astype(np.uint8)
    
    back_img = Image.fromarray(data, "RGBA")
    # Filtro de suavizado sutil para fusionar los relieves
    back_img = back_img.filter(ImageFilter.SMOOTH_MORE)
    # Restaurar la máscara alpha nítida original
    back_data = np.array(back_img)
    back_data[:, :, 3] = alpha
    
    final_back = Image.fromarray(back_data, "RGBA")
    final_back.save(out_path, "PNG")
    print(f"Generada vista posterior: {out_path} ({final_back.size})")

create_back_view(os.path.join(out_dir, "male_front.png"), os.path.join(out_dir, "male_back.png"), is_female=False)
create_back_view(os.path.join(out_dir, "female_front.png"), os.path.join(out_dir, "female_back.png"), is_female=True)
create_back_view(os.path.join(out_dir, "male_persp.png"), os.path.join(out_dir, "male_back_persp.png"), is_female=False)
create_back_view(os.path.join(out_dir, "female_persp.png"), os.path.join(out_dir, "female_back_persp.png"), is_female=True)

