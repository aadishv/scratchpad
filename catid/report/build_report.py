"""Build the review artifact: sprite atlases of all crops + data.json + index.html (template).
python build_report.py WORK OUT_DIR"""
import sys, os, json, collections, datetime as dt
import numpy as np
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
import common
work, out = sys.argv[1], sys.argv[2]
os.makedirs(out, exist_ok=True)
CELL, PER = 128, 16  # 16x16 cells per atlas

dets, times, sess = common.load(work)
lab = json.load(open(os.path.join(ROOT, 'labels/labels_v5.json')))
primary = np.load(f'{work}/primary.npy')
collar = np.load(f'{work}/collar.npy')
from collar import NAMES as CNAMES

# --- sprite atlases (crop letterboxed into a square cell) ---
n_atlas = (len(dets) + PER * PER - 1) // (PER * PER)
for a in range(n_atlas):
    A = Image.new('RGB', (PER * CELL, PER * CELL), (38, 40, 46))
    for j in range(PER * PER):
        i = a * PER * PER + j
        if i >= len(dets): break
        im = Image.open(f"{work}/crops/{dets[i]['id']}.jpg"); im.thumbnail((CELL, CELL), Image.LANCZOS)
        A.paste(im, ((j % PER) * CELL + (CELL - im.width) // 2, (j // PER) * CELL + (CELL - im.height) // 2))
    A.save(f'{out}/atlas{a}.jpg', quality=80, optimize=True)

visits = []
for v in np.unique(sess):
    fs = [d['file'] for d, s in zip(dets, sess) if s == v]
    t0 = common.local(min(fs, key=common.ts))
    visits.append({'v': int(v), 'date': t0.strftime('%b %-d'), 'iso': t0.strftime('%Y-%m-%d'), 'dow': t0.strftime('%a'),
                   'n': len(fs), 'photos': len(set(fs))})
crops = []
for i, d in enumerate(dets):
    c = collar[i]
    crops.append({'i': i, 'id': d['id'], 'v': int(sess[i]), 'lab': lab[d['id']], 'p': bool(primary[i]),
                  't': common.local(d['file']).strftime('%H:%M:%S'), 'conf': d['conf'],
                  'col': CNAMES[int(c.argmax())] if c.max() > 0.004 else ''})
log = json.load(open(os.path.join(ROOT, 'results/log.json')))
extra = {}
for f in ('detector_bench.json', 'notes.json', 'suspects.json', 'by_coat.json', 'pipeline_v27.json'):
    p = os.path.join(ROOT, 'results', f)
    if os.path.exists(p): extra[f[:-5]] = json.load(open(p))
emb_meta = {}
for p in sorted(os.listdir(f'{work}/emb')):
    if p.endswith('.json'): emb_meta[p[:-5]] = json.load(open(f'{work}/emb/{p}'))
named = sorted(set(json.load(open(os.path.join(ROOT, 'labels/feedback/cat_names.json'))).values()) | {'Onyx', 'Shovel', 'Jade', 'Rocky'})
data = {'names': {}, 'named': named, 'updated': dt.datetime.now(dt.timezone(dt.timedelta(hours=-7))).strftime('%b %-d, %-I:%M %p PT'),
        'visits': visits, 'crops': crops, 'cell': CELL, 'per': PER, 'n_atlas': n_atlas,
        'results': log, 'emb': emb_meta, **extra}
tpl = open(os.path.join(HERE, 'template.html')).read()
open(f'{out}/index.html', 'w').write(tpl.replace('/*__DATA__*/null', json.dumps(data, separators=(',', ':'))))
print('atlases', n_atlas, 'html', os.path.getsize(f'{out}/index.html') // 1024, 'KB')
