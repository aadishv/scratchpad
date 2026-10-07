"""Fast end-to-end cat ID for a new batch of photos (one visit).

    python pipeline.py PHOTOS_DIR --roster roster.npz --out out_dir [--det yolo11n-seg.pt --imgsz 640 --emb dinov2_b]

Stages (all CPU):
  decode   JPEG draft-mode decode at 1/4 scale (+ EXIF rotation)       -- avoids full 12MP decode
  detect   YOLO-seg (cat class), conf 0.25
  dedupe   drop detections whose mask overlaps a kept one by >50% (YOLO splits/duplicates cats)
  embed    DINOv2 on the letterboxed bbox crop, batched
  collar   colour of the ring just outside the cat mask (pink / red / yellow-green / blue / purple)
  group    average-linkage clustering of this visit's crops (distance threshold)
  match    each group vs roster cats: mean top-k similarity + recency prior -> top-3 suggestions or NEW
Writes out_dir/result.json (per photo: cats with suggestions) and out_dir/index.html (contact sheet by group).
"""
import os, sys, json, time, argparse, datetime as dt
import numpy as np, torch
from PIL import Image, ImageOps
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import models, common
from collar import rules as collar_rules, NAMES as CNAMES
from scipy import ndimage

def load_photo(path, scale=4):
    im = Image.open(path); im.draft('RGB', (im.width // scale, im.height // scale))
    return ImageOps.exif_transpose(im).convert('RGB')

class Timer:
    def __init__(s): s.t = {}
    def __call__(s, k):
        s.k, s.t0 = k, time.perf_counter(); return s
    def __enter__(s): return s
    def __exit__(s, *a): s.t[s.k] = s.t.get(s.k, 0) + time.perf_counter() - s.t0

def collar_vec(im_np_hsv, mask, ring=6):
    m = ndimage.binary_dilation(mask, iterations=ring)
    h, sat, v = im_np_hsv[..., 0][m] * 360 / 255, im_np_hsv[..., 1][m] / 255, im_np_hsv[..., 2][m] / 255
    return np.array([r.sum() / max(mask.sum(), 1) for r in collar_rules(h, sat, v)], np.float32)

def write_html(a, out, files):
    '''Contact sheet: one row per group with its call and top-3 suggestions, crops as inline thumbnails.'''
    import base64, io, html
    def thumb(m):
        im = load_photo(os.path.join(a.photos, m['file'])).crop(tuple(m['box'])); im.thumbnail((140, 140))
        b = io.BytesIO(); im.save(b, 'JPEG', quality=80); return base64.b64encode(b.getvalue()).decode()
    rows = []
    for g in sorted(out['groups'], key=lambda g: -len(g['crops'])):
        sug = ' · '.join(f"{html.escape(s['cat'])} {s['score']:.2f}" for s in g['suggest'])
        imgs = ''.join(f'<img src="data:image/jpeg;base64,{thumb(out["crops_meta"][c])}" title="{html.escape(out["crops_meta"][c]["file"])}">' for c in g['crops'])
        call = 'New cat?' if g['call'] == 'NEW' else html.escape(g['call'])
        rows.append(f'<section><h2>{call} <small>{len(g["crops"])} crops · suggestions: {sug}</small></h2><div>{imgs}</div></section>')
    open(f'{a.out}/index.html', 'w').write('<!doctype html><meta charset=utf-8><title>Cat groups</title><style>body{font:14px system-ui;margin:16px;background:#f4f5f7;color:#1d2230}'
        'section{background:#fff;border:1px solid #dde0e7;border-radius:10px;padding:12px;margin:0 0 12px}h2{font-size:17px;margin:0 0 8px}small{color:#5d6475;font-weight:400}'
        'img{height:110px;margin:0 4px 4px 0;border-radius:6px}</style>'
        f'<h1>{len(files)} photos, {out["crops"]} cats detected, {len(out["groups"])} groups</h1>' + ''.join(rows))

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('photos'); ap.add_argument('--roster'); ap.add_argument('--out', default='pipeline_out')
    ap.add_argument('--det', default='yolo11n-seg.pt'); ap.add_argument('--imgsz', type=int, default=640)
    ap.add_argument('--emb', default='dinov2_b'); ap.add_argument('--threads', type=int, default=4)
    ap.add_argument('--cluster-thr', type=float, default=0.7); ap.add_argument('--new-thr', type=float, default=0.55)
    ap.add_argument('--files', nargs='*', help='subset of file names to process')
    a = ap.parse_args()
    torch.set_num_threads(a.threads)
    from ultralytics import YOLO
    T = Timer(); os.makedirs(a.out, exist_ok=True)
    files = sorted(f for f in (a.files or os.listdir(a.photos)) if f.lower().endswith('.jpg'))
    with T('load models'):
        det = YOLO(a.det); fn, S, mean, std = models.load(a.emb)
        mean, std = torch.tensor(mean).view(3, 1, 1), torch.tensor(std).view(3, 1, 1)
    crops, meta = [], []
    for f in files:
        with T('decode'): im = load_photo(os.path.join(a.photos, f))
        with T('detect'):
            r = det.predict(im, imgsz=a.imgsz, conf=0.25, classes=[15], retina_masks=True, verbose=False)[0]
        if not len(r.boxes): continue
        with T('dedupe+collar'):
            ms = (r.masks.data.cpu().numpy() > 0.5); order = np.argsort(-r.boxes.conf.numpy()); kept = []
            for i in order:
                if any((ms[i] & ms[k]).sum() / min(ms[i].sum(), ms[k].sum()) > 0.5 for k in kept): continue
                kept.append(i)
            hsv = np.asarray(im.convert('HSV')).astype(np.float32)
        for i in kept:
            x1, y1, x2, y2 = r.boxes.xyxy[i].tolist(); p = 0.08 * max(x2 - x1, y2 - y1)
            box = (int(max(0, x1 - p)), int(max(0, y1 - p)), int(min(im.width, x2 + p)), int(min(im.height, y2 + p)))
            with T('dedupe+collar'): cv = collar_vec(hsv, ms[i])
            with T('crop'):
                c = im.crop(box); c.thumbnail((S, S), Image.BICUBIC)
                canvas = Image.new('RGB', (S, S), (124, 116, 104)); canvas.paste(c, ((S - c.width) // 2, (S - c.height) // 2))
                crops.append((torch.from_numpy(np.asarray(canvas).copy()).permute(2, 0, 1).float() / 255 - mean) / std)
            meta.append({'file': f, 'box': box, 'conf': round(float(r.boxes.conf[i]), 3), 'collar': CNAMES[int(cv.argmax())] if cv.max() > 0.004 else '', 'cv': cv})
    with T('embed'), torch.inference_mode():
        E = torch.cat([torch.nn.functional.normalize(fn(torch.stack(crops[i:i + 16])).float(), dim=-1) for i in range(0, len(crops), 16)]).numpy() if crops else np.zeros((0, 768))
    with T('group+match'):
        R = np.load(a.roster, allow_pickle=True) if a.roster else None
        mu = R['mean'] if R is not None else E.mean(0)
        Ec = E - mu; Ec /= np.linalg.norm(Ec, axis=1, keepdims=True)
        C = np.stack([m['cv'] for m in meta]) if meta else np.zeros((0, 5))
        has = C.max(1) > 0.004; dom = C.argmax(1)
        def csim(Ca_has, Ca_dom, Cb_has, Cb_dom):
            M = np.where(Ca_dom[:, None] == Cb_dom[None, :], 1.0, -1.0); M[~Ca_has] = 0; M[:, ~Cb_has] = 0; return M
        # burst pooling: consecutive single-cat photos < 25 s apart share their embedding mean
        ts = np.array([common.ts(m['file']).timestamp() for m in meta]); nper = np.array([sum(x['file'] == m['file'] for x in meta) for m in meta])
        import heuristics as H
        Ec = H.tracklet_pool(Ec, H.bursts(ts, np.zeros(len(meta), int), nper), alpha=0.5)
        Sv = Ec @ Ec.T + 0.1 * csim(has, dom, has, dom)
        from sklearn.cluster import AgglomerativeClustering
        if len(meta) > 1:
            D = np.clip(1 - Sv, 0, None); np.fill_diagonal(D, 0)
            grp = AgglomerativeClustering(n_clusters=None, metric='precomputed', linkage='average', distance_threshold=a.cluster_thr).fit_predict(D)
        else: grp = np.zeros(len(meta), int)
        groups = []
        for g in np.unique(grp):
            idx = np.nonzero(grp == g)[0]; sug = []
            if R is not None:
                Rc = R['emb'] - mu; Rc /= np.linalg.norm(Rc, axis=1, keepdims=True)
                Sr = Ec[idx] @ Rc.T + 0.1 * csim(has[idx], dom[idx], R['collar_has'], R['collar_dom'])
                now = ts[idx].min() / 86400
                for name in np.unique(R['label']):
                    cols = np.nonzero(R['label'] == name)[0]; k = min(3, len(cols))
                    sc = np.sort(Sr[:, cols], axis=1)[:, -k:].mean() + 0.1 * np.exp(-(now - R['day'][cols].max()) / 21)
                    sug.append((float(sc), str(name)))
                sug.sort(reverse=True)
            top = sug[:3]
            groups.append({'group': int(g), 'crops': idx.tolist(), 'suggest': [{'cat': n, 'score': round(s, 3)} for s, n in top],
                           'call': top[0][1] if top and top[0][0] >= a.new_thr else 'NEW'})
    n_ph = len(files)
    timing = {k: round(v, 2) for k, v in T.t.items()}
    per_photo = {k: round(1000 * v / max(n_ph, 1), 1) for k, v in T.t.items() if k != 'load models'}
    out = {'photos': n_ph, 'crops': len(meta), 'timing_s': timing, 'ms_per_photo': per_photo,
           'ms_per_photo_total': round(sum(per_photo.values()), 1), 'groups': groups,
           'crops_meta': [{k: v for k, v in m.items() if k != 'cv'} for m in meta]}
    json.dump(out, open(f'{a.out}/result.json', 'w'), indent=1)
    with T('html'): write_html(a, out, files)
    np.save(f'{a.out}/emb.npy', E)
    print(json.dumps({k: out[k] for k in ('photos', 'crops', 'timing_s', 'ms_per_photo', 'ms_per_photo_total')}))
    print(len(groups), 'groups;', sum(g['call'] == 'NEW' for g in groups), 'called NEW')

if __name__ == '__main__':
    main()
