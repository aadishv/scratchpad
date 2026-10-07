"""Roster for pipeline.py from labeled crops of visits BEFORE a given visit (simulates 'what you have confirmed so far').
python build_roster.py EMB_TAG BEFORE_VISIT out.npz"""
import sys, os, json, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bench as B
tag, before, out = sys.argv[1], int(sys.argv[2]), sys.argv[3]
E = np.load(f'{B.WORK}/emb/{tag}.npy'); C = np.load(f'{B.WORK}/collar.npy')
m = B.keep & (B.sess < before)
np.savez(out, emb=E[m], label=B.y_loose[m], day=B.times[m] / 86400, collar_has=C[m].max(1) > 0.004, collar_dom=C[m].argmax(1),
         mean=E.mean(0), ids=np.array([B.dets[i]['id'] for i in np.nonzero(m)[0]]))
print(m.sum(), 'roster crops,', len(set(B.y_loose[m])), 'cats')
