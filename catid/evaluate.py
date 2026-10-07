"""Evaluation protocols on labeled crops (labels.json: det_id -> cat name; 'x' junk, '?' unknown are dropped).

retrieval  : leave-one-out kNN. To avoid the trivial "burst frame 2 matches burst frame 1" win, a query may NOT
             match anything from the same visit -> measures "recognize this cat on a different day".
             Reported: top-1 accuracy, mAP (queries whose cat appears in >=1 other visit).
openset    : chronological replay. Process visits in order; gallery = everything labeled in earlier visits.
             Each query predicts nearest gallery id if sim > tau else NEW. Metrics: known-cat accuracy,
             new-cat recall, overall accuracy at the best tau (and tau reported) -> "cats come and go".
clustering : given a predicted partition, B-cubed P/R/F1, ARI, #clusters vs #cats.
"""
import numpy as np
from sklearn.metrics import adjusted_rand_score

def retrieval(S, y, sess, mask_same=None):
    """S: NxN similarity. y: labels (str array). sess: visit id per item. Returns dict."""
    S = S.copy(); np.fill_diagonal(S, -np.inf)
    S[sess[:, None] == sess[None, :]] = -np.inf          # cross-visit only
    top1, aps, n = 0, [], 0
    for i in range(len(y)):
        valid = np.isfinite(S[i]); rel = (y == y[i]) & valid
        if rel.sum() == 0: continue
        n += 1; order = np.argsort(-S[i][valid]); r = rel[valid][order]
        top1 += r[0]; hits = np.cumsum(r); aps.append((hits[r] / (np.nonzero(r)[0] + 1)).mean())
    return {'top1': top1 / n, 'mAP': float(np.mean(aps)), 'n_queries': n}

def openset(S, y, sess, taus=np.linspace(0.0, 1.0, 101), agg='max'):
    """Chronological open-set identification. Score vs gallery identity = max sim over that id's items."""
    res = []
    order_s = np.unique(sess)
    preds = []  # (query idx, best id, best sim, is_new_truth)
    for s in order_s[1:]:
        gal = sess < s; q = np.nonzero(sess == s)[0]
        gids = np.unique(y[gal])
        for i in q:
            sims = np.array([S[i, gal & (y == g)].max() for g in gids])
            j = sims.argmax(); preds.append((gids[j], sims[j], y[i] not in set(gids), y[i]))
    best = None
    for t in taus:
        ok_known = [p[0] == p[3] and p[1] >= t for p in preds if not p[2]]
        ok_new = [p[1] < t for p in preds if p[2]]
        acc = (sum(ok_known) + sum(ok_new)) / len(preds)
        r = {'tau': float(t), 'acc': acc, 'known_acc': np.mean(ok_known), 'new_recall': np.mean(ok_new) if ok_new else np.nan}
        if best is None or acc > best['acc']: best = r
    closed = np.mean([p[0] == p[3] for p in preds if not p[2]])
    best['closed_set_known_acc'] = closed; best['n_known'] = sum(not p[2] for p in preds); best['n_new'] = sum(p[2] for p in preds)
    return best

def bcubed(pred, y):
    P, R = [], []
    for i in range(len(y)):
        same_c = pred == pred[i]; same_y = y == y[i]
        P.append((same_c & same_y).sum() / same_c.sum()); R.append((same_c & same_y).sum() / same_y.sum())
    p, r = np.mean(P), np.mean(R)
    return {'bP': p, 'bR': r, 'bF1': 2 * p * r / (p + r), 'ARI': adjusted_rand_score(y, pred),
            'n_clusters': len(np.unique(pred)), 'n_cats': len(np.unique(y))}
