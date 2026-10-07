"""dets_raw.json -> dets.json: cross-class NMS (YOLO sometimes calls a black cat a dog/bear too),
drop boxes too small to identify (min side < 64px on the 1024 thumb), embed RLE masks."""
import sys, json, numpy as np
from PIL import Image
sys.path.insert(0, __import__('os').path.dirname(__import__('os').path.abspath(__file__))); import rle
work = sys.argv[1]
raw = json.load(open(f'{work}/dets_raw.json'))
def iou(a, b):
    ix = max(0, min(a[2], b[2]) - max(a[0], b[0])); iy = max(0, min(a[3], b[3]) - max(a[1], b[1]))
    i = ix * iy; return i / ((a[2]-a[0])*(a[3]-a[1]) + (b[2]-b[0])*(b[3]-b[1]) - i)
by = {}
for d in raw: by.setdefault(d['file'], []).append(d)
out, dropped = [], {'small': 0, 'nms': 0, 'lowconf_noncat': 0}
for f, ds in by.items():
    ds = sorted(ds, key=lambda d: (d['cls'] != 15, -d['conf']))  # prefer 'cat' label, then confidence
    keep = []
    for d in ds:
        x1, y1, x2, y2 = d['box']
        if min(x2 - x1, y2 - y1) < 64: dropped['small'] += 1; continue
        if d['cls'] != 15 and d['conf'] < 0.3: dropped['lowconf_noncat'] += 1; continue
        if any(iou(d['box'], k['box']) > 0.6 for k in keep): dropped['nms'] += 1; continue
        keep.append(d)
    for d in keep:
        d['rle'] = rle.encode(np.asarray(Image.open(f"{work}/masks/{d['id']}.png")) > 127)
        out.append(d)
out.sort(key=lambda d: d['id'])
json.dump(out, open(f'{work}/dets.json', 'w'))
print(len(raw), '->', len(out), dropped)
