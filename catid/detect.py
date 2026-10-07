"""Stage 1: detect + segment cats with YOLO11-seg. Writes dets.json and per-detection mask PNGs.

Each detection: {id, file, box[x1,y1,x2,y2] in 1024-thumb px, conf, mask (path), area_frac}.
Low conf threshold on purpose: close-ups / black cats score low, we filter later.
"""
import sys, os, json, time
import numpy as np
from PIL import Image
from ultralytics import YOLO

src, out = sys.argv[1], sys.argv[2]
weights = sys.argv[3] if len(sys.argv) > 3 else 'yolo11x-seg.pt'
os.makedirs(f'{out}/masks', exist_ok=True)
model = YOLO(weights)
CAT, DOG = 15, 16  # dogs: black cats are sometimes called dogs/bears; keep and relabel
files = sorted(os.listdir(src))
dets, t0 = [], time.time()
for i, f in enumerate(files):
    r = model.predict(os.path.join(src, f), imgsz=1024, conf=0.15, classes=[CAT, DOG, 21, 17], retina_masks=True, verbose=False)[0]
    H, W = r.orig_shape
    for j in range(len(r.boxes)):
        did = f"{f[:-4]}_{j}"
        m = r.masks.data[j].cpu().numpy() > 0.5
        Image.fromarray((m * 255).astype(np.uint8)).save(f'{out}/masks/{did}.png', optimize=True)
        dets.append(dict(id=did, file=f, box=[round(v, 1) for v in r.boxes.xyxy[j].tolist()],
                         conf=round(float(r.boxes.conf[j]), 3), cls=int(r.boxes.cls[j]),
                         area_frac=round(float(m.mean()), 4), W=W, H=H))
    if i % 50 == 0: print(i, len(dets), f'{time.time()-t0:.0f}s', flush=True)
json.dump(dets, open(f'{out}/dets_raw.json', 'w'))
print('total', len(dets), f'{time.time()-t0:.0f}s')
