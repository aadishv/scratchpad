"""Decode once: EXIF-rotate and downscale every photo to 1024px JPEGs (fast reloads later)."""
import sys, os
from concurrent.futures import ProcessPoolExecutor
from PIL import Image, ImageOps
src, dst = sys.argv[1], sys.argv[2]
os.makedirs(dst, exist_ok=True)
def work(f):
    im = Image.open(os.path.join(src, f)); im.draft('RGB', (1024, 1024))
    im = ImageOps.exif_transpose(im).convert('RGB'); im.thumbnail((1024, 1024))
    im.save(os.path.join(dst, f.replace('.MP.jpg', '.jpg')), quality=92)
fs = sorted(f for f in os.listdir(src) if f.lower().endswith('.jpg'))
with ProcessPoolExecutor(4) as ex: list(ex.map(work, fs, chunksize=8))
print(len(fs))
