"""Online (causal) protocol: for visit v, only crops from visits <= v exist. A similarity builder gets that
subset and returns its similarity matrix; queries are labeled crops of v whose cat was seen before;
candidates = cats labeled in visits < v; score per cat = mean of top-3 sims. Reports top-1 / top-3."""
import numpy as np
def run(build, y, sess, keep, k=3):
    t1 = t3 = n = 0
    for v in np.unique(sess)[1:]:
        sub = np.nonzero(sess <= v)[0]
        S = build(sub)
        loc = {g: i for i, g in enumerate(sub)}
        gal = [i for i in sub if sess[i] < v and keep[i]]
        cats = sorted(set(y[gal]))
        for q in sub:
            if sess[q] != v or not keep[q] or y[q] not in cats: continue
            sc = {}
            for c in cats:
                cols = [loc[i] for i in gal if y[i] == c]
                sc[c] = np.sort(S[loc[q], cols])[-k:].mean()
            r = sorted(sc, key=lambda c: -sc[c]); n += 1; t1 += r[0] == y[q]; t3 += y[q] in r[:3]
    return t1 / n, t3 / n, n
