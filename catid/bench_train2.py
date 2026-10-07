import sys, os, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bench as B, heuristics as H, train_proj as T
Sc = H.collar_sim(np.load(f'{B.WORK}/collar.npy')); out = []
for tag in sys.argv[1:]:
    E = H.center(np.load(f'{B.WORK}/emb/{tag}.npy'))
    for name, kw in (('linear128', dict(dim=128)), ('resid r=16 e100', dict(resid=16, epochs=100, lr=1e-3)), ('resid r=16 e300', dict(resid=16, epochs=300, lr=1e-3))):
        Z = T.oof_project(E, B.y_loose, B.sess, B.keep, cross=True, **kw)
        B.score(Z @ Z.T, f'{tag} | supcon-xvisit {name}', out, do_cluster=False)
        B.score(Z @ Z.T + 0.1 * Sc, f'{tag} | supcon-xvisit {name} +collar', out, do_cluster=False)
