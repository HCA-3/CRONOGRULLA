import sys
import os
from PIL import Image

p_male = r'C:/Users/dsant/.gemini/antigravity/brain/4903879f-82ad-4c93-ab27-8a9d5d3b00b0/.user_uploaded/media_1794095775371_e3d349c1.jpg'
p_female = r'C:/Users/dsant/.gemini/antigravity/brain/4903879f-82ad-4c93-ab27-8a9d5d3b00b0/.user_uploaded/media_1794095797494_c87a4fe5.jpg'

im_m = Image.open(p_male)
im_f = Image.open(p_female)

# Guardar carpeta assets/mannequin si no existe
out_dir = os.path.join("assets", "mannequin")
os.makedirs(out_dir, exist_ok=True)

# 1. Analizar imagen masculina (465x430)
# Tres figuras:
# Fig 1 (3/4): x de 15 a 150
# Fig 2 (Frontal): x de 160 a 300
# Fig 3 (Perfil): x de 315 a 455
# Y cintura hacia arriba: y de 0 a 240 (altura total 430, cintura está aprox al 50-55% de la altura)
mw, mh = im_m.size
m_front = im_m.crop((160, 5, 305, int(mh * 0.56)))
m_persp = im_m.crop((15, 5, 155, int(mh * 0.56)))
m_side = im_m.crop((315, 5, 455, int(mh * 0.56)))

m_front.save(os.path.join(out_dir, "male_front_raw.png"))
m_persp.save(os.path.join(out_dir, "male_persp_raw.png"))
m_side.save(os.path.join(out_dir, "male_side_raw.png"))
print(f"Hombre recortado: front {m_front.size}, persp {m_persp.size}, side {m_side.size}")

# 2. Analizar imagen femenina (1000x1000)
# Tres figuras:
# Fig 1 (3/4): x de 90 a 380
# Fig 2 (Frontal): x de 390 a 690
# Fig 3 (Perfil): x de 700 a 890
# Y cintura hacia arriba: y de 10 a 540 (cintura/pelvis superior está aprox en y=540)
fw, fh = im_f.size
f_persp = im_f.crop((95, 15, 380, int(fh * 0.54)))
f_front = im_f.crop((390, 15, 685, int(fh * 0.54)))
f_side = im_f.crop((700, 15, 885, int(fh * 0.54)))

f_front.save(os.path.join(out_dir, "female_front_raw.png"))
f_persp.save(os.path.join(out_dir, "female_persp_raw.png"))
f_side.save(os.path.join(out_dir, "female_side_raw.png"))
print(f"Mujer recortada: front {f_front.size}, persp {f_persp.size}, side {f_side.size}")

