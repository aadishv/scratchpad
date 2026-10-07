import sys, os, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bench as B, heuristics as H, train_proj as T
tags = sys.argv[1:]
C = np.load(f'{B.WORK}/collar.npy'); Sc = H.collar_sim(C)
out = []
for tag in tags:
    E = H.center(np.load(f'{B.WORK}/emb/{tag}.npy'))
    B.score(E @ E.T, f'{tag} | center', out, do_cluster=False)
    for kw in (dict(dim=128), dict(dim=128, hidden=512), dict(dim=64, epochs=600)):
        Z = T.oof_project(E, B.y_loose, B.sess, B.keep, **kw)
        B.score(Z @ Z.T, f'{tag} | supcon {kw}', out, do_cluster=False)
        B.score(Z @ Z.T + 0.1 * Sc, f'{tag} | supcon {kw} +collar', out, do_cluster=False)
