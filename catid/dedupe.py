"""Mark duplicate / fragment detections of the same cat within a photo.
Greedy by (cat class, confidence); a detection whose mask overlaps an already-kept one by > IOS_T of the
smaller mask is a duplicate. Writes primary.npy (bool per det, dets.json order) and dup_of.json."""
import sys, os, json, collections, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import rle
work = sys.argv[1]; IOS_T = float(sys.argv[2]) if len(sys.argv) > 2 else 0.5
dets = json.load(open(f'{work}/dets.json'))
by = collections.defaultdict(list)
for i, d in enumerate(dets): by[d['file']].append(i)
primary = np.ones(len(dets), bool); dup_of = {}
for f, idx in by.items():
    if len(idx) < 2: continue
    ms = {i: rle.decode(dets[i]['rle']).astype(bool) for i in idx}
    kept = []
    for i in sorted(idx, key=lambda i: (dets[i]['cls'] != 15, -dets[i]['conf'])):
        for k in kept:
            if (ms[i] & ms[k]).sum() / min(ms[i].sum(), ms[k].sum()) > IOS_T:
                primary[i] = False; dup_of[dets[i]['id']] = dets[k]['id']; break
        else: kept.append(i)
np.save(f'{work}/primary.npy', primary); json.dump(dup_of, open(f'{work}/dup_of.json', 'w'))
print(f'{primary.sum()} primary of {len(dets)}; {len(dup_of)} duplicates')
