"""Collar colour vs. hand labels: per cat, distribution of detected dominant collar colour."""
import json, sys, os, collections, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); from collar import NAMES
work, labf, floor = sys.argv[1], sys.argv[2], float(sys.argv[3]) if len(sys.argv) > 3 else 0.004
dets = json.load(open(f'{work}/dets.json')); lab = json.load(open(labf)); C = np.load(f'{work}/collar.npy')
for cat, expect in [('TuxPink','pink'),('Rocky','blue'),('OrangeYellow','yellowgreen'),('TabbyLime','yellowgreen'),('Jade','pink'),
                    ('TuxYellow','yellowgreen'),('Siamese','blue'),('Bean','pink'),('OrangePink','pink'),('Tortie','pink'),('TuxBlue_v11','blue'),('FluffyCalico','-'),('BlackLH','-')]:
    idx = [i for i, d in enumerate(dets) if lab[d['id']].rstrip('~') == cat]
    dom = [NAMES[C[i].argmax()] if C[i].max() > floor else '-' for i in idx]
    print(f'{cat:13s} expect {expect:12s}', collections.Counter(dom).most_common(4))
