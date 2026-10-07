"""Unsupervised transductive tricks on the full crop set (no labels used):
  alpha_qe      : alpha query expansion, each crop -> weighted mean of itself + top-k neighbours
  diffusion     : Iscen et al. 2017 style, (I - a W)^-1 on a symmetric mutual-kNN affinity graph
  visit_consolidate : cluster each visit (same as the within-visit grouping) and pool each crop with its
                  predicted group mean; a visit's photos of a cat become one multi-view descriptor."""
import numpy as np
from sklearn.cluster import AgglomerativeClustering

def l2n(X): return X / np.linalg.norm(X, axis=1, keepdims=True).clip(1e-8)

def alpha_qe(E, k=5, alpha=3.0, S=None):
    S = E @ E.T if S is None else S
    idx = np.argsort(-S, axis=1)[:, :k + 1]
    W = np.take_along_axis(S, idx, 1).clip(0) ** alpha
    return l2n((W[..., None] * E[idx]).sum(1))

def diffusion(S, k=15, a=0.9, gamma=3):
    N = len(S); A = np.zeros_like(S)
    nn = np.argsort(-S, axis=1)[:, 1:k + 1]
    for i in range(N): A[i, nn[i]] = S[i, nn[i]].clip(0) ** gamma
    A = np.minimum(A, A.T)  # mutual neighbours
    d = A.sum(1); d[d == 0] = 1; Dm = 1 / np.sqrt(d)
    W = Dm[:, None] * A * Dm[None, :]
    F = np.linalg.inv(np.eye(N) - a * W)
    F = (F + F.T) / 2
    Fn = F / np.sqrt(np.outer(np.diag(F), np.diag(F)))
    return Fn

def visit_consolidate(E, S, sess, files, thr=0.55, beta=1.0, linkage='average'):
    """Cluster each visit's crops on S (distance 1-S, same-photo cannot-link off), then
    E_i <- normalize(E_i + beta * mean(E of its predicted group))."""
    out = E.copy(); f = np.array(files); groups = np.zeros(len(E), int) - 1; g0 = 0
    for v in np.unique(sess):
        idx = np.nonzero(sess == v)[0]
        if len(idx) == 1: groups[idx] = g0; g0 += 1; continue
        D = np.clip(1 - S[np.ix_(idx, idx)], 0, None); np.fill_diagonal(D, 0)
        lab = AgglomerativeClustering(n_clusters=None, metric='precomputed', linkage=linkage, distance_threshold=thr).fit_predict(D)
        groups[idx] = lab + g0; g0 += lab.max() + 1
    for g in np.unique(groups):
        idx = np.nonzero(groups == g)[0]
        if len(idx) > 1: out[idx] = E[idx] + beta * E[idx].mean(0)
    return l2n(out), groups
