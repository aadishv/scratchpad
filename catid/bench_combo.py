"""Every available embedding with the standard recipe (center + burst pooling + collar), plus ensembles."""
import sys, os, glob, itertools, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bench as B, heuristics as H
Sc = H.collar_sim(np.load(f'{B.WORK}/collar.npy')); out = []
tags = [os.path.basename(p)[:-4] for p in sorted(glob.glob(f'{B.WORK}/emb/*.npy')) if not p.endswith('_tta.npy')]
only = sys.argv[1:]
def recipe(E): Et = H.tracklet_pool(H.center(E), B.tid, alpha=0.5); return Et @ Et.T + 0.1 * Sc
done = {}
for t in tags:
    if only and t not in only: continue
    S = recipe(np.load(f'{B.WORK}/emb/{t}.npy')); done[t] = S
    B.score(S, f'{t} | recipe', out)
# ensembles: average similarity of the recipe matrices (masked variants only, to keep the count sane)
m = [t for t in done if t.endswith('cropsm')]
for k in (2, 3):
    for combo in itertools.combinations(m, k):
        B.score(sum(done[t] for t in combo) / k, ' + '.join(c.split('__')[0] for c in combo) + ' | ensemble recipe', out)
