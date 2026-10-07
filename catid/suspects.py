"""Label auditor: crops whose most similar same-visit crop carries a different label than theirs.
Within a visit the model is reliable (F1 ~0.86), so strong disagreements are often labeling mistakes.
Writes results/suspects.json (top pairs, deduplicated by label pair)."""
import sys, os, json, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bench as B, heuristics as H
tag = sys.argv[1] if len(sys.argv) > 1 else 'dinov2_b__crops'
Sc = H.collar_compat(np.load(f'{B.WORK}/collar.npy'), B.times, B.sess); Pc = H.coat_sim(np.load(f'{B.WORK}/coat.npy'))
Et = H.tracklet_pool(H.center(np.load(f'{B.WORK}/emb/{tag}.npy')), B.tid, alpha=0.5); S = Et @ Et.T + 0.2 * Sc + 0.3 * Pc
idx = np.nonzero(B.keep)[0]; rows = []
for i in idx:
    sv = idx[(B.sess[idx] == B.sess[i]) & (idx != i) & (np.array(B.files)[idx] != B.files[i])]
    same = sv[B.y_loose[sv] == B.y_loose[i]]; diff = sv[B.y_loose[sv] != B.y_loose[i]]
    if not len(diff): continue
    j = diff[S[i, diff].argmax()]
    rows.append((S[i, j] - (S[i, same].max() if len(same) else 0.3), int(i), int(j)))
rows.sort(reverse=True); seen = set(); out = []
# skip label pairs the user already judged in the review queue (pair_fb), per visit
import glob
fbdir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'labels/feedback/pair_fb')
for p in glob.glob(f'{fbdir}/*.json'):
    a, b = os.path.basename(p)[:-5].split('__'); ia = next(i for i, d in enumerate(B.dets) if d['id'] == a)
    ib = next(i for i, d in enumerate(B.dets) if d['id'] == b)
    seen.add(tuple(sorted((B.y_loose[ia], B.y_loose[ib])) + [int(B.sess[ia])]))
for mg, i, j in rows:
    if mg <= 0: break  # only pairs the model clearly prefers over the labeled match
    key = tuple(sorted((B.y_loose[i], B.y_loose[j])) + [int(B.sess[i])])
    if key in seen: continue
    seen.add(key); out.append({'a': B.dets[i]['id'], 'b': B.dets[j]['id'], 'la': B.raw[i], 'lb': B.raw[j], 'v': int(B.sess[i]), 'margin': round(float(mg), 3)})
    if len(out) == 30: break
json.dump(out, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'results/suspects.json'), 'w'), indent=0)
print(len(out), [(o['la'], o['lb'], o['margin']) for o in out[:8]])
