"""Stage 2: cut each detection out of the ORIGINAL full-res photo (EXIF-rotated).
Writes crops/<id>.jpg (bbox + 8% pad, longest side <=512) and cropsm/<id>.jpg (same, background
replaced by neutral gray using the dilated YOLO mask -> kills lap/couch/day-specific context)."""
import sys, os, json
import numpy as np
from concurrent.futures import ProcessPoolExecutor
from PIL import Image, ImageOps, ImageFilter
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import rle
raw, work = sys.argv[1], sys.argv[2]
dets = json.load(open(f'{work}/dets.json'))
os.makedirs(f'{work}/crops', exist_ok=True); os.makedirs(f'{work}/cropsm', exist_ok=True)
by_file = {}
for d in dets: by_file.setdefault(d['file'], []).append(d)
names = {f.replace('.MP.jpg', '.jpg'): f for f in os.listdir(raw)}

def work_file(f):
    im = ImageOps.exif_transpose(Image.open(os.path.join(raw, names[f]))).convert('RGB')
    s = im.width / by_file[f][0]['W']
    for d in by_file[f]:
        x1, y1, x2, y2 = [v * s for v in d['box']]; p = 0.08 * max(x2 - x1, y2 - y1)
        b = (int(max(0, x1 - p)), int(max(0, y1 - p)), int(min(im.width, x2 + p)), int(min(im.height, y2 + p)))
        c = im.crop(b)
        m = Image.fromarray(rle.decode(d['rle']) * 255) if 'rle' in d else Image.open(f"{work}/masks/{d['id']}.png")
        m = m.resize(im.size, Image.BILINEAR).crop(b)
        m = m.filter(ImageFilter.MaxFilter(9)).filter(ImageFilter.GaussianBlur(3))  # dilate + feather edges
        g = Image.new('RGB', c.size, (124, 116, 104))
        cm = Image.composite(c, g, m)
        for out, img in (('crops', c), ('cropsm', cm)):
            img = img.copy(); img.thumbnail((512, 512), Image.LANCZOS); img.save(f"{work}/{out}/{d['id']}.jpg", quality=93)
    return len(by_file[f])

with ProcessPoolExecutor(4) as ex: print(sum(ex.map(work_file, by_file)))
