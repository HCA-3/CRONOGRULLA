import os
import numpy as np
from PIL import Image

out_dir = os.path.join("assets", "mannequin")

def make_transparent(img_path, out_path, bg_thresh=245):
    img = Image.open(img_path).convert("RGBA")
    data = np.array(img)
    
    # Canales R, G, B
    r, g, b, a = data[:, :, 0], data[:, :, 1], data[:, :, 2], data[:, :, 3]
    
    # Los fondos son blancos o casi blancos (> bg_thresh)
    # Suavizar el borde para que no queden halos blancos
    dist_white = np.sqrt((255.0 - r)**2 + (255.0 - g)**2 + (255.0 - b)**2)
    
    # Si la distancia a blanco es menor a 25, es fondo blanco puro (alpha = 0)
    # Si está entre 25 y 60, rampa suave de alpha (anti-aliasing)
    alpha = np.clip((dist_white - 15.0) / 35.0 * 255.0, 0, 255).astype(np.uint8)
    
    data[:, :, 3] = alpha
    
    out_img = Image.fromarray(data, "RGBA")
    out_img.save(out_path, "PNG")
    print(f"Guardado transparente: {out_path} ({out_img.size})")

# Procesar hombre
make_transparent(os.path.join(out_dir, "male_front_raw.png"), os.path.join(out_dir, "male_front.png"))
make_transparent(os.path.join(out_dir, "male_persp_raw.png"), os.path.join(out_dir, "male_persp.png"))
make_transparent(os.path.join(out_dir, "male_side_raw.png"), os.path.join(out_dir, "male_side.png"))

# Generar espejos para hombre
im_persp = Image.open(os.path.join(out_dir, "male_persp.png"))
im_persp.transpose(Image.FLIP_LEFT_RIGHT).save(os.path.join(out_dir, "male_persp_left.png"))

im_side = Image.open(os.path.join(out_dir, "male_side.png"))
im_side.transpose(Image.FLIP_LEFT_RIGHT).save(os.path.join(out_dir, "male_side_left.png"))

# Procesar mujer
make_transparent(os.path.join(out_dir, "female_front_raw.png"), os.path.join(out_dir, "female_front.png"))
make_transparent(os.path.join(out_dir, "female_persp_raw.png"), os.path.join(out_dir, "female_persp.png"))
make_transparent(os.path.join(out_dir, "female_side_raw.png"), os.path.join(out_dir, "female_side.png"))

# Generar espejos para mujer
im_f_persp = Image.open(os.path.join(out_dir, "female_persp.png"))
im_f_persp.transpose(Image.FLIP_LEFT_RIGHT).save(os.path.join(out_dir, "female_persp_left.png"))

im_f_side = Image.open(os.path.join(out_dir, "female_side.png"))
im_f_side.transpose(Image.FLIP_LEFT_RIGHT).save(os.path.join(out_dir, "female_side_left.png"))

print("Todas las texturas de maniquí procesadas exitosamente!")

