import os
from PIL import Image

out_dir = os.path.join("assets", "mannequin")

keys = ["front", "persp", "side", "back_persp", "back", "back_persp_left", "side_left", "persp_left"]
genders = ["male", "female"]

for g in genders:
    for k in keys:
        fpath = os.path.join(out_dir, f"{g}_{k}.png")
        assert os.path.exists(fpath), f"Falta archivo: {fpath}"
        im = Image.open(fpath)
        assert im.mode == "RGBA", f"Debe ser RGBA: {fpath}"
        print(f"[OK] {g} {k}: {im.size}")

print("\n¡Todos los 16 archivos de textura de maniquí verificados al 100%!")

