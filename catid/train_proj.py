"""Learn a small projection head on frozen embeddings from the hand labels (supervised contrastive loss),
evaluated with K-fold leave-VISITS-out cross-validation: a head never sees its test visits' crops.
Simulates 'learn from the visits you already confirmed, then run on a new visit'. Returns out-of-fold
projected embeddings for every crop."""
import numpy as np, torch, torch.nn as nn, torch.nn.functional as F
torch.set_num_threads(2)

def supcon(z, y, t=0.1, sv=None):
    sim = z @ z.T / t; eye = torch.eye(len(y), dtype=torch.bool)
    pos = (y[:, None] == y[None, :]) & ~eye
    if sv is not None:  # cross-visit positives only; same-visit same-cat pairs are neither pos nor neg
        same_v = sv[:, None] == sv[None, :]
        sim = sim.masked_fill(pos & same_v, -1e9); pos = pos & ~same_v
    logp = sim.masked_fill(eye, -1e9); logp = logp - torch.logsumexp(logp, 1, keepdim=True)
    has = pos.sum(1) > 0
    return -(logp * pos).sum(1)[has].div(pos.sum(1)[has]).mean()

class Resid(nn.Module):
    '''x + low-rank update, starts as identity: can only nudge the generic embedding.'''
    def __init__(s, D, r):
        super().__init__(); s.a = nn.Linear(D, r, bias=False); s.b = nn.Linear(r, D, bias=False); nn.init.zeros_(s.b.weight)
    def forward(s, x): return x + s.b(s.a(x))

def train_head(X, y, dim=128, epochs=300, lr=3e-3, wd=1e-3, hidden=0, seed=0, resid=0, sv=None):
    torch.manual_seed(seed); rng = np.random.RandomState(seed); D = X.shape[1]
    if resid: head = Resid(D, resid)
    else: head = nn.Sequential(nn.Linear(D, hidden), nn.GELU(), nn.Linear(hidden, dim)) if hidden else nn.Linear(D, dim, bias=False)
    opt = torch.optim.AdamW(head.parameters(), lr=lr, weight_decay=wd)
    Xt, yt = torch.tensor(X), torch.tensor(y)
    for _ in range(epochs):
        cats = rng.permutation(np.unique(y))[:24]  # class-balanced batch: <=8 crops x 24 cats
        idx = np.concatenate([rng.permutation(np.nonzero(y == c)[0])[:8] for c in cats])
        z = F.normalize(head(Xt[idx] + 0.02 * torch.randn(len(idx), D)), dim=-1)
        loss = supcon(z, yt[idx], sv=None if sv is None else torch.tensor(sv[idx])); opt.zero_grad(); loss.backward(); opt.step()
    return head

def oof_project(X, y_str, sess, train_mask, folds=5, seed=0, cross=False, **kw):
    vis = np.unique(sess); rng = np.random.RandomState(seed); rng.shuffle(vis)
    fold_of = {v: i % folds for i, v in enumerate(vis)}; f = np.array([fold_of[s] for s in sess])
    _, y = np.unique(y_str, return_inverse=True); Z = None
    for k in range(folds):
        tr = train_mask & (f != k)
        head = train_head(X[tr], y[tr], seed=seed, sv=sess[tr] if cross else None, **kw)
        with torch.no_grad(): z = F.normalize(head(torch.tensor(X[f == k])), dim=-1).numpy()
        if Z is None: Z = np.zeros((len(X), z.shape[1]), np.float32)
        Z[f == k] = z
    return Z

def oof_lda(X, y_str, sess, train_mask, folds=5, seed=0, dim=40, shrink='auto'):
    from sklearn.discriminant_analysis import LinearDiscriminantAnalysis as LDA
    vis = np.unique(sess); rng = np.random.RandomState(seed); rng.shuffle(vis)
    fold_of = {v: i % folds for i, v in enumerate(vis)}; f = np.array([fold_of[s] for s in sess])
    Z = None
    for k in range(folds):
        tr = train_mask & (f != k)
        lda = LDA(solver='eigen', shrinkage=shrink, n_components=min(dim, len(np.unique(y_str[tr])) - 1)).fit(X[tr], y_str[tr])
        z = lda.transform(X[f == k]); z /= np.linalg.norm(z, axis=1, keepdims=True)
        if Z is None: Z = np.zeros((len(X), z.shape[1]), np.float32)
        Z[f == k] = z
    return Z
