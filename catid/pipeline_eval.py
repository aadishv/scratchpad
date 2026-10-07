"""Score a pipeline.py run against the hand labels: match its crops to labeled detections by box IoU
(both in normalized image coordinates), then check each crop's group call (top-1 / top-3 / NEW)."""
import sys, os, json, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bench as B
run, roster = sys.argv[1], np.load(sys.argv[2], allow_pickle=True)
res = json.load(open(f'{run}/result.json')); known = set(roster['label'])
from PIL import Image
def nb(box, W, H): return np.array(box) / np.array([W, H, W, H])
lab_by_file = {}
for i, d in enumerate(B.dets):
    lab_by_file.setdefault(d['file'], []).append((nb(d['box'], d['W'], d['H']), B.raw[i]))
def iou(a, b):
    ix = max(0, min(a[2], b[2]) - max(a[0], b[0])); iy = max(0, min(a[3], b[3]) - max(a[1], b[1])); i = ix * iy
    return i / ((a[2] - a[0]) * (a[3] - a[1]) + (b[2] - b[0]) * (b[3] - b[1]) - i)
call = {}; top3 = {}
for g in res['groups']:
    for c in g['crops']: call[c] = g['call']; top3[c] = [s['cat'] for s in g['suggest']]
rows = []
for k, m in enumerate(res['crops_meta']):
    f = m['file'].replace('.MP.jpg', '.jpg'); W, H = Image.open(os.path.join(sys.argv[3] if len(sys.argv) > 3 else '/home/user/data/raw', m['file'])).size if False else (None, None)
    cands = lab_by_file.get(f, [])
    if not cands: rows.append(('unmatched', None)); continue
    # pipeline boxes are in the 1/4-scale decoded image; normalize with its size (stored implicitly: use max coords heuristic)
    rows.append((k, cands))
# need decoded sizes: recompute from file headers (EXIF-rotated)
from PIL import ImageOps
out = {'known_top1': [], 'known_top3': [], 'new_ok': [], 'unlabeled': 0, 'unmatched': 0}
for k, m in enumerate(res['crops_meta']):
    f = m['file'].replace('.MP.jpg', '.jpg'); cands = lab_by_file.get(f, [])
    im = Image.open(f'/home/user/data/raw/{m["file"]}'); im.draft('RGB', (im.width // 4, im.height // 4)); im = ImageOps.exif_transpose(im)
    b = nb(m['box'], im.width, im.height)
    best = max(cands, key=lambda c: iou(b, c[0]), default=None)
    if best is None or iou(b, best[0]) < 0.3: out['unmatched'] += 1; continue
    y = best[1].rstrip('~')
    if y in ('?', 'x'): out['unlabeled'] += 1; continue
    if y in known: out['known_top1'].append(call[k] == y); out['known_top3'].append(y in top3[k])
    else: out['new_ok'].append(call[k] == 'NEW')
summ = {k: (round(float(np.mean(v)), 3), len(v)) if isinstance(v, list) else v for k, v in out.items()}
print(json.dumps(summ))
