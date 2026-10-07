"""Similarity post-processing tricks. All take/return NxN similarity matrices or NxD embeddings."""
import numpy as np

def l2n(X): return X / np.linalg.norm(X, axis=1, keepdims=True).clip(1e-8)

def whiten(E, k=None, shrink=0.1):
    """Unsupervised: center on the dataset mean and PCA-whiten (ZCA-ish with eigenvalue shrinkage).
    Removes the dominant 'generic cat on a lap' directions that make every crop look similar."""
    X = E - E.mean(0); U, s, Vt = np.linalg.svd(X, full_matrices=False)
    k = k or len(s); lam = s[:k] ** 2 / len(X)
    return l2n(X @ Vt[:k].T / np.sqrt(lam + shrink * lam.mean()))

def center(E): return l2n(E - E.mean(0))

def bursts(times, sess, nper, gap=25.0):
    """Burst/tracklet id: consecutive photos in the same visit < gap seconds apart, where the photo
    has a single detected cat (multi-cat frames are ambiguous -> own singleton tracklet)."""
    order = np.argsort(times, kind='stable'); tid, out, prev = -1, np.zeros(len(times), int), None
    for i in order:
        if nper[i] != 1 or prev is None or sess[i] != sess[prev] or times[i] - times[prev] > gap: tid += 1
        out[i] = tid
        prev = i if nper[i] == 1 else None
    return out

def tracklet_pool(E, tid, alpha=1.0, S=None, min_sim=0.0):
    """Replace each embedding with itself + alpha * mean of its burst-mates (gated by similarity to stay
    safe when the camera switched cats within the burst window)."""
    out = E.copy()
    for t in np.unique(tid):
        idx = np.nonzero(tid == t)[0]
        if len(idx) < 2: continue
        for i in idx:
            mates = idx if S is None else idx[S[i, idx] >= min_sim]
            out[i] = E[i] + alpha * E[mates].mean(0)
    return l2n(out)

def k_reciprocal(S, k1=20, k2=6, lam=0.3):
    """Zhong et al. 2017 re-ranking (Jaccard over k-reciprocal neighbour sets), compact numpy version."""
    N = len(S); D = 2 - 2 * S; rank = np.argsort(D, axis=1)
    V = np.zeros((N, N), np.float32)
    for i in range(N):
        fk = rank[i, :k1 + 1]; recip = fk[np.any(rank[fk, :k1 + 1] == i, axis=1)]
        exp = recip
        for j in recip:
            fj = rank[j, :int(round(k1 / 2)) + 1]; rj = fj[np.any(rank[fj, :int(round(k1 / 2)) + 1] == j, axis=1)]
            if len(np.intersect1d(rj, recip)) > 2 / 3 * len(rj): exp = np.append(exp, rj)
        exp = np.unique(exp); w = np.exp(-D[i, exp]); V[i, exp] = w / w.sum()
    if k2 > 1: V = np.stack([V[rank[i, :k2]].mean(0) for i in range(N)])
    inv = [np.nonzero(V[:, j])[0] for j in range(N)]
    J = np.zeros((N, N), np.float32)
    for i in range(N):
        tmin = np.zeros(N, np.float32); nz = np.nonzero(V[i])[0]
        for j in nz: tmin[inv[j]] += np.minimum(V[i, j], V[inv[j], j])
        J[i] = 1 - tmin / (2 - tmin)
    Dfin = (1 - lam) * J + lam * D / 4
    return 1 - Dfin  # back to a similarity-like score

def collar_sim(C, floor=0.004):
    """Similarity from collar-colour histograms: +1 same dominant colour, -1 different colours, 0 if either
    has no visible collar (unknown != different)."""
    has = C.max(1) > floor; dom = C.argmax(1)
    M = np.where(dom[:, None] == dom[None, :], 1.0, -1.0)
    M[~has, :] = 0; M[:, ~has] = 0
    return M

def same_photo_mask(files):
    f = np.array(files); return f[:, None] == f[None, :]

def coat_sim(P):
    """Bhattacharyya overlap of zero-shot coat-pattern distributions, in [0, 1]."""
    R = np.sqrt(P); return R @ R.T

# Café collar code (from the user): blue = male, pink = female, yellow = adopted.
# A cat can go blue->yellow or pink->yellow over time, never any other direction.
COLLAR_SEX = {'pink': 'F', 'blue': 'M'}
def collar_compat(C, times, sess, floor=0.004, names=('pink', 'red', 'yellowgreen', 'blue', 'purple'),
                  same=1.0, impossible=-3.0, adopt=0.3, other_diff=-1.0):
    """Pairwise collar compatibility using the collar code. 0 where either collar is not visible.
    same colour: +same; pink vs blue: impossible; yellow-after-pink/blue (later visit): +adopt (allowed);
    yellow-before-pink/blue or a different colour within one visit: impossible; any other mismatch: other_diff."""
    has = C.max(1) > floor; col = np.array([names[k] for k in C.argmax(1)])
    N = len(C); M = np.zeros((N, N), np.float32)
    for i in np.nonzero(has)[0]:
        for j in np.nonzero(has)[0]:
            a, b = col[i], col[j]
            if a == b: M[i, j] = same
            elif sess[i] == sess[j]: M[i, j] = impossible   # collars don't change within a visit
            elif {a, b} == {'pink', 'blue'}: M[i, j] = impossible
            elif 'yellowgreen' in (a, b) and ({a, b} & {'pink', 'blue'}):
                y, o = (i, j) if a == 'yellowgreen' else (j, i)   # adoption: pink/blue -> yellow, never back
                M[i, j] = adopt if times[y] > times[o] else impossible
            else: M[i, j] = other_diff
    return M
