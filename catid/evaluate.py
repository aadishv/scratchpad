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

def set_retrieval(S, y, sess, agg='mean'):
    """Group-level cross-visit ID: each (visit, cat) group is a query set; gallery = all groups of OTHER visits.
    Set similarity = mean pairwise sim ('mean') or mean over query items of their best gallery match ('maxmean').
    Returns top-1 / top-3 accuracy over groups whose cat appears in another visit."""
    keys = sorted(set(zip(sess.tolist(), y.tolist())))
    idx = {k: np.nonzero((sess == k[0]) & (y == k[1]))[0] for k in keys}
    hits1 = hits3 = n = 0
    for q in keys:
        cands = [g for g in keys if g[0] != q[0]]
        if not any(g[1] == q[1] for g in cands): continue
        sims = []
        for g in cands:
            B = S[np.ix_(idx[q], idx[g])]
            sims.append(B.mean() if agg == 'mean' else B.max(1).mean())
        # collapse gallery groups to identities (best group per identity)
        best = {}
        for g, s in zip(cands, sims): best[g[1]] = max(best.get(g[1], -9), s)
        ranked = sorted(best, key=lambda c: -best[c])
        n += 1; hits1 += ranked[0] == q[1]; hits3 += q[1] in ranked[:3]
    return {'set_top1': hits1 / n, 'set_top3': hits3 / n, 'n_sets': n}

def pipeline_sim(S, y, sess, files, cluster_thr, taus=np.linspace(0.0, 1.2, 61), k=3, cannot_link=True, days=None, rec_w=0.0, rec_tau=21.0):
    """End-to-end replay of how the tool would be used. Visits in date order; for each visit:
      1. cluster its crops (average linkage, distance threshold, same-photo cannot-link),
      2. score each cluster against every cat confirmed on earlier visits: mean over the cluster's crops of
         the mean of their top-k similarities to that cat's crops,
      3. assign the best cat if score > tau, else 'new cat'; then the visit's TRUE labels join the roster
         (= the user confirmed/corrected the suggestions).
    A crop is correct if its cluster got its true cat, or 'new' when the cat was never seen before.
    Returns accuracy at the best tau plus the breakdown."""
    from sklearn.cluster import AgglomerativeClustering
    f = np.array(files); recs = []
    for v in np.unique(sess):
        idx = np.nonzero(sess == v)[0]
        if len(idx) == 1: cl = np.array([0])
        else:
            D = 1 - S[np.ix_(idx, idx)]
            if cannot_link: D[f[idx][:, None] == f[idx][None, :]] = 4.0
            np.fill_diagonal(D, 0)
            cl = AgglomerativeClustering(n_clusters=None, metric='precomputed', linkage='average', distance_threshold=cluster_thr).fit_predict(D)
        gal = sess < v; known = set(y[gal])
        for c in np.unique(cl):
            m = idx[cl == c]
            best, bs, allsc = None, -9, {}
            for g in known:
                G = S[np.ix_(m, np.nonzero(gal & (y == g))[0])]
                kk = min(k, G.shape[1]); s_ = np.sort(G, axis=1)[:, -kk:].mean()
                if rec_w and days is not None:  # recency prior: cats come and go (adopted cats stop appearing)
                    s_ += rec_w * np.exp(-(days[idx[0]] - days[gal & (y == g)].max()) / rec_tau)
                allsc[g] = s_
                if s_ > bs: best, bs = g, s_
            top3 = sorted(allsc, key=lambda g: -allsc[g])[:3]
            for i in m: recs.append((y[i], best, bs, y[i] not in known, y[i] in top3))
    out = None
    for t in taus:
        ok = [(p == yt and s >= t) if not new else (s < t) for yt, p, s, new, _ in recs]
        kn = [o for o, r in zip(ok, recs) if not r[3]]; nw = [o for o, r in zip(ok, recs) if r[3]]
        bal = (np.mean(kn) + np.mean(nw)) / 2  # balanced: ~45% of crops are a cat's first appearance
        if out is None or bal > out['sim_bal']:
            out = {'sim_bal': float(bal), 'sim_acc': float(np.mean(ok)), 'sim_tau': float(t), 'sim_known_acc': float(np.mean(kn)),
                   'sim_new_acc': float(np.mean(nw)) if nw else float('nan'), 'sim_n_known': len(kn), 'sim_n_new': len(nw)}
    out['sim_closed_known_acc'] = float(np.mean([p == yt for yt, p, s, new, _ in recs if not new]))
    out['sim_known_top3'] = float(np.mean([t3 for yt, p, s, new, t3 in recs if not new]))
    return out
