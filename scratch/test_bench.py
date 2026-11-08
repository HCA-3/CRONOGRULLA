from PIL import Image
import time

img = Image.new("RGBA", (500, 600), (100, 100, 100, 255))
t0 = time.time()
for _ in range(30):
    img.resize((380, 500), Image.Resampling.BILINEAR)
print("BILINEAR 30 frames:", time.time() - t0)

t0 = time.time()
for _ in range(30):
    img.resize((380, 500), Image.Resampling.LANCZOS)
print("LANCZOS 30 frames:", time.time() - t0)

