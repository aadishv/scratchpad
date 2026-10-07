"""Benchmark: every available embedding x heuristic -> metrics table (results/bench.json + printed).
Labels: '?'/'x' dropped. 'loose' strips the '~' (uncertain cross-visit) marker; 'strict' drops '~' crops."""
import sys, os, json, glob, itertools
import numpy as np
from sklearn.cluster import AgglomerativeClustering
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common, evaluate as ev, heuristics as H

WORK = os.environ.get('WORK', '/home/user/data/work')
LAB = os.environ.get('LABELS', os.path.join(os.path.dirname(os.path.abspath(__file__)), 'labels/labels_v2.json'))
dets, times, sess = common.load(WORK)
files = [d['file'] for d in dets]
lab = json.load(open(LAB)); raw = np.array([lab[d['id']] for d in dets])
nper = np.array([files.count(f) for f in files])
tid = H.bursts(times, sess, nper)
keep = ~np.isin(raw, ['?', 'x'])
PRIMARY = np.load(f'{WORK}/primary.npy') if os.path.exists(f'{WORK}/primary.npy') else np.ones(len(dets), bool)
if os.environ.get('PRIMARY', '1') == '1': keep &= PRIMARY
CANNOT_LINK = os.environ.get('CANNOT_LINK', '1') == '1'
y_loose = np.array([l.rstrip('~') for l in raw])
strict = keep & ~np.char.endswith(raw.astype(str), '~')

def embs():
    out = {}
    for p in sorted(glob.glob(f'{WORK}/emb/*.npy')):
        out[os.path.basename(p)[:-4]] = np.load(p)
    return out

def within_visit_cluster(S, y, s, files, thr):
    """Average-linkage clustering per visit with a distance threshold; cannot-link same-photo pairs."""
    preds = np.empty(len(y), object)
    f = np.array(files)
    for v in np.unique(s):
        idx = np.nonzero(s == v)[0]
        if len(idx) == 1: preds[idx] = f'{v}_0'; continue
        D = 1 - S[np.ix_(idx, idx)]
        if CANNOT_LINK: D[f[idx][:, None] == f[idx][None, :]] = 4.0  # cannot-link
        np.fill_diagonal(D, 0)
        lab = AgglomerativeClustering(n_clusters=None, metric='precomputed', linkage='average', distance_threshold=thr).fit_predict(D)
        preds[idx] = [f'{v}_{l}' for l in lab]
    return preds

LOG = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'results/log.json')
def log_result(r):
    '''Append/replace this run in results/log.json (name -> metrics), the report's data source.'''
    try: log = json.load(open(LOG))
    except Exception: log = {}
    log[r['name']] = {k: (float(v) if isinstance(v, (int, float, np.floating, np.integer)) else v) for k, v in r.items()}
    json.dump(log, open(LOG, 'w'), indent=1)

def score(S, name, out, do_cluster=True):
    r = {'name': name}
    for tag, m in (('loose', keep), ('strict', strict)):
        Sm = S[np.ix_(m, m)]; y = y_loose[m]; s = sess[m]
        rr = ev.retrieval(Sm, y, s)
        r[f'{tag}_top1'] = rr['top1']; r[f'{tag}_mAP'] = rr['mAP']
        if tag == 'loose':
            o = ev.openset(Sm, y, s); r.update({f'open_{k}': v for k, v in o.items()})
            r.update(ev.set_retrieval(Sm, y, s, 'maxmean'))
    if do_cluster:
        m = keep; best = None
        for thr in np.arange(0.2, 1.21, 0.05):
            p = within_visit_cluster(S[np.ix_(m, m)], y_loose[m], sess[m], [files[i] for i in np.nonzero(m)[0]], thr)
            b = ev.bcubed(p, np.array([f'{v}_{l}' for v, l in zip(sess[m], y_loose[m])]))
            if best is None or b['bF1'] > best['bF1']: best = dict(b, thr=float(thr))
        r.update({f'wv_{k}': v for k, v in best.items()})
        fm = [files[i] for i in np.nonzero(m)[0]]
        r.update(ev.pipeline_sim(S[np.ix_(m, m)], y_loose[m], sess[m], fm, best['thr']))
        rr = ev.pipeline_sim(S[np.ix_(m, m)], y_loose[m], sess[m], fm, best['thr'], days=times[m] / 86400, rec_w=0.1, rec_tau=21)
        r.update({'simR_' + k[4:]: v for k, v in rr.items()})
    out.append(r)
    log_result(r)
    print(f"{name:55s} top1 {r['loose_top1']:.3f} mAP {r['loose_mAP']:.3f} | strict top1 {r['strict_top1']:.3f} | "
          f"open acc {r['open_acc']:.3f} (known {r['open_known_acc']:.3f} new {r['open_new_recall']:.3f}) | "
          f"wv F1 {r.get('wv_bF1', float('nan')):.3f} | set top1 {r['set_top1']:.3f} top3 {r['set_top3']:.3f} | SIM {r.get('sim_acc', float('nan')):.3f} (known {r.get('sim_known_acc', float('nan')):.3f} new {r.get('sim_new_acc', float('nan')):.3f} closed {r.get('sim_closed_known_acc', float('nan')):.3f}) | E2E bal {r.get('simR_bal', float('nan')):.3f} known-top3 {r.get('simR_known_top3', float('nan')):.3f}", flush=True)
    return r

if __name__ == '__main__':
    E = embs(); out = []
    print(f'{keep.sum()} labeled crops, {len(set(y_loose[keep]))} cats, {strict.sum()} strict')
    for k, X in E.items():
        score(X @ X.T, k, out)
    os.makedirs(os.path.join(os.path.dirname(__file__), 'results'), exist_ok=True)
    json.dump(out, open(os.path.join(os.path.dirname(__file__), 'results/bench_models.json'), 'w'), indent=1)
