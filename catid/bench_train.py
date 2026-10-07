"""Learned projection head (leave-visits-out CV) on one or more embeddings."""
import sys, os, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bench as B, heuristics as H, train_proj as T
Sc = H.collar_sim(np.load(f'{B.WORK}/collar.npy')); out = []
for tag in sys.argv[1:]:
    E = H.center(np.load(f'{B.WORK}/emb/{tag}.npy'))
    for name, kw in (('resid r=16 e100', dict(resid=16, epochs=100, lr=1e-3)), ('resid r=32 e300', dict(resid=32, epochs=300, lr=1e-3)), ('resid r=16 e300 wd0.05', dict(resid=16, epochs=300, lr=1e-3, wd=0.05))):
        Z = T.oof_project(E, B.y_loose, B.sess, B.keep, **kw)
        B.score(Z @ Z.T, f'{tag} | supcon {name}', out, do_cluster=False)
        B.score(Z @ Z.T + 0.1 * Sc, f'{tag} | supcon {name} +collar', out, do_cluster=False)
    for dim in (30, 45):
        Z = T.oof_lda(E, B.y_loose, B.sess, B.keep, dim=dim)
        B.score(Z @ Z.T, f'{tag} | LDA shrink dim={dim}', out, do_cluster=False)
        Zc = np.hstack([E, 0.7 * Z]); Zc /= np.linalg.norm(Zc, axis=1, keepdims=True)
        B.score(Zc @ Zc.T + 0.1 * Sc, f'{tag} | concat(raw, LDA{dim}) +collar', out, do_cluster=False)
