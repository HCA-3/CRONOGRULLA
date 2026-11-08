import os
from PIL import Image

out_dir = os.path.join("assets", "mannequin")

male_files = [
    "male_front.png", "male_persp.png", "male_side.png",
    "male_persp_left.png", "male_side_left.png",
    "male_back.png", "male_back_persp.png"
]

target_h = 525

for fname in male_files:
    fpath = os.path.join(out_dir, fname)
    if os.path.exists(fpath):
        img = Image.open(fpath)
        w, h = img.size
        new_w = int(w * (target_h / float(h)))
        resized = img.resize((new_w, target_h), Image.LANCZOS)
        resized.save(fpath, "PNG")
        print(f"Reescalado con Lanczos: {fname} a {resized.size}")

print("Todos los maniquíes masculinos reescalados con alta fidelidad.")

