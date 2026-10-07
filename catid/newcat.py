"""Open-set decision for the replay: is a visit's cluster a known cat (and which) or a new cat?
Per cluster features: best cat score, margin to 2nd, cluster size, days since best cat last seen,
best cat's #visits in roster, collar agreement with best cat. Classifier (logistic regression) is trained
leave-visits-out on replay records; assignment within a visit is one-to-one (Hungarian) so two clusters
of one visit cannot both claim the same known cat."""
import numpy as np
from sklearn.cluster import AgglomerativeClustering
from sklearn.linear_model import LogisticRegression
from scipy.optimize import linear_sum_assignment

def records(S, y, sess, files, times, collar_dom, collar_has, thr, k=3):
    f = np.array(files); recs = []
    for v in np.unique(sess):
        idx = np.nonzero(sess == v)[0]
        if len(idx) == 1: cl = np.array([0])
        else:
            D = np.clip(1 - S[np.ix_(idx, idx)], 0, None); np.fill_diagonal(D, 0)
            cl = AgglomerativeClustering(n_clusters=None, metric='precomputed', linkage='average', distance_threshold=thr).fit_predict(D)
        gal = sess < v; known = sorted(set(y[gal]))
        for c in np.unique(cl):
            m = idx[cl == c]; sc = {}
            for g in known:
                cols = np.nonzero(gal & (y == g))[0]; kk = min(k, len(cols))
                sc[g] = np.sort(S[np.ix_(m, cols)], axis=1)[:, -kk:].mean()
            r = sorted(sc, key=lambda g: -sc[g])
            if r:
                b = r[0]; cols = np.nonzero(gal & (y == b))[0]
                days = (times[m].min() - times[cols].max()) / 86400
                cd = collar_dom[m][collar_has[m]]; cdb = collar_dom[cols][collar_has[cols]]
                col = 0 if (len(cd) == 0 or len(cdb) == 0) else (1 if np.bincount(cd).argmax() == np.bincount(cdb).argmax() else -1)
                feat = [sc[b], sc[b] - (sc[r[1]] if len(r) > 1 else 0), np.log1p(len(m)), np.log1p(max(days, 0)), len(set(sess[cols])), col]
            else: feat = [0, 0, np.log1p(len(m)), 5, 0, 0]
            truth = [y[i] for i in m]
            recs.append({'v': int(v), 'members': m, 'scores': sc, 'feat': feat, 'truth': truth, 'known': known})
    return recs

def evaluate(recs, model='lr', tau=None, hungarian=True):
    """Leave-one-visit-out: train the new/known classifier on other visits' clusters, predict this visit."""
    X = np.array([r['feat'] for r in recs]); vis = np.array([r['v'] for r in recs])
    # cluster label for training: majority truth is a known cat AND best-scored cat is that cat -> 'accept'
    maj = [max(set(r['truth']), key=r['truth'].count) for r in recs]
    is_known = np.array([m in r['known'] for m, r in zip(maj, recs)])
    ok_kn = ok_new = n_kn = n_new = 0
    for v in np.unique(vis):
        te = vis == v; tr = ~te
        if model == 'lr':
            clf = LogisticRegression(C=1.0, max_iter=1000, class_weight='balanced').fit(X[tr], is_known[tr])
            p_known = clf.predict_proba(X[te])[:, 1]
            accept = p_known >= 0.5
        else: accept = X[te, 0] >= tau
        rs = [r for r, t in zip(recs, te) if t]
        # assignment: accepted clusters get a known cat; one-to-one within the visit (Hungarian on scores)
        assign = {}
        acc_idx = [i for i, a in enumerate(accept) if a and rs[i]['scores']]
        if acc_idx:
            cats = sorted(set(g for i in acc_idx for g in rs[i]['scores']))
            C = np.array([[-rs[i]['scores'].get(g, -9) for g in cats] for i in acc_idx])
            if hungarian and len(cats) >= len(acc_idx):
                ri, ci = linear_sum_assignment(C)
                for a_, b_ in zip(ri, ci): assign[acc_idx[a_]] = cats[b_]
            else:
                for a_, i in enumerate(acc_idx): assign[i] = cats[int(np.argmin(C[a_]))]
        for i, r in enumerate(rs):
            pred = assign.get(i, 'NEW')
            for t in r['truth']:
                if t in r['known']: n_kn += 1; ok_kn += pred == t
                else: n_new += 1; ok_new += pred == 'NEW'
    return {'known_acc': ok_kn / n_kn, 'new_acc': ok_new / n_new, 'bal': (ok_kn / n_kn + ok_new / n_new) / 2, 'n_known': n_kn, 'n_new': n_new}
