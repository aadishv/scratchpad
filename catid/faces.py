"""Cat head/face crops: OWLv2 open-vocabulary detection ("a photo of a cat's face" / "a cat's head") on each
primary body crop, then re-cut the face from the full-resolution original (+20% pad) and embed it.
python faces.py WORK RAW  -> WORK/faces.json (box in crop coords + score), WORK/faces/<id>.jpg, emb/<model>__faces.npy"""
import os, sys, json, time, numpy as np, torch
from PIL import Image, ImageOps
from transformers import Owlv2Processor, Owlv2ForObjectDetection
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
work, raw = sys.argv[1], sys.argv[2]
torch.set_num_threads(int(os.environ.get('THREADS', 4)))
dets = json.load(open(f'{work}/dets.json')); primary = np.load(f'{work}/primary.npy')
out_path = f'{work}/faces.json'
res = json.load(open(out_path)) if os.path.exists(out_path) else {}
name = 'google/owlv2-base-patch16-ensemble'
proc = Owlv2Processor.from_pretrained(name); model = Owlv2ForObjectDetection.from_pretrained(name).eval()
t0 = time.time(); todo = [d for d, p in zip(dets, primary) if p and d['id'] not in res]
for n, d in enumerate(todo):
    im = Image.open(f"{work}/crops/{d['id']}.jpg").convert('RGB')
    inp = proc(text=[["a photo of a cat's face", "a cat's head"]], images=im, return_tensors='pt')
    with torch.no_grad(): o = model(**inp)
    sc = o.logits[0].max(-1).values.sigmoid(); k = sc.argmax().item(); cx, cy, w, h = o.pred_boxes[0][k].tolist(); W = max(im.size)
    res[d['id']] = {'score': round(sc[k].item(), 3), 'box': [max(0, (cx - w / 2) * W), max(0, (cy - h / 2) * W), min(im.width, (cx + w / 2) * W), min(im.height, (cy + h / 2) * W)], 'crop_size': list(im.size)}
    if n % 50 == 0:
        json.dump(res, open(out_path, 'w')); print(n, len(todo), f'{time.time() - t0:.0f}s', flush=True)
json.dump(res, open(out_path, 'w'))
# re-cut faces from the full-resolution originals
os.makedirs(f'{work}/faces', exist_ok=True)
names = {f.replace('.MP.jpg', '.jpg'): f for f in os.listdir(raw)}
by_file = {}
for d in dets:
    if d['id'] in res: by_file.setdefault(d['file'], []).append(d)
for f, ds in by_file.items():
    big = ImageOps.exif_transpose(Image.open(os.path.join(raw, names[f]))).convert('RGB'); s = big.width / ds[0]['W']
    for d in ds:
        x1, y1, x2, y2 = [v * s for v in d['box']]; p = 0.08 * max(x2 - x1, y2 - y1)
        bx = (max(0, x1 - p), max(0, y1 - p)); bw = min(big.width, x2 + p) - bx[0]
        r = res[d['id']]; k = bw / r['crop_size'][0]
        fx1, fy1, fx2, fy2 = [v * k for v in r['box']]; fp = 0.2 * max(fx2 - fx1, fy2 - fy1)
        face = big.crop((int(bx[0] + fx1 - fp), int(bx[1] + fy1 - fp), int(bx[0] + fx2 + fp), int(bx[1] + fy2 + fp)))
        face.thumbnail((448, 448)); face.save(f"{work}/faces/{d['id']}.jpg", quality=92)
print('faces done', len(res), f'{time.time() - t0:.0f}s')
