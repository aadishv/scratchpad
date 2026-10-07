"""Every available embedding with the standard recipe (center + burst pooling + collar), plus ensembles."""
import sys, os, glob, itertools, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bench as B, heuristics as H
Sc = H.collar_compat(np.load(f'{B.WORK}/collar.npy'), B.times, B.sess); Pc = H.coat_sim(np.load(f'{B.WORK}/coat.npy')); out = []
tags = [os.path.basename(p)[:-4] for p in sorted(glob.glob(f'{B.WORK}/emb/*.npy')) if not p.endswith('_tta.npy')]
only = sys.argv[1:]
def recipe(E): Et = H.tracklet_pool(H.center(E), B.tid, alpha=0.5); return Et @ Et.T + 0.2 * Sc + 0.3 * Pc  # labels v3 recipe: collar code + coat gate
done = {}
for t in tags:
    if only and t not in only: continue
    S = recipe(np.load(f'{B.WORK}/emb/{t}.npy')); done[t] = S
    B.score(S, f'{t} | recipe', out)
# ensembles: average similarity of the recipe matrices (masked variants only, to keep the count sane)
m = [t for t in done if t.endswith('__crops') and t.split('__')[0] in ('dinov2_b', 'dinov2_s', 'mega_t224', 'clip_b16')]
for k in (2, 3):
    for combo in itertools.combinations(m, k):
        B.score(sum(done[t] for t in combo) / k, ' + '.join(c.split('__')[0] for c in combo) + ' | ensemble recipe', out)
