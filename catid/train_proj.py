"""Learn a small projection head on top of frozen embeddings from the hand labels (supervised contrastive),
evaluated with K-fold leave-VISITS-out cross-validation: the head never sees the test visits' crops.
This simulates 'the system learns from visits you already confirmed, then is used on a new visit'.
Output: out-of-fold projected embeddings for every crop (each crop embedded by the model trained without its visit)."""
import sys, os, numpy as np, torch, torch.nn as nn, torch.nn.functional as F
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def supcon(z, y, t=0.1):
    sim = z @ z.T / t; n = len(y)
    eye = torch.eye(n, dtype=torch.bool)
    pos = (y[:, None] == y[None, :]) & ~eye
    sim = sim.masked_fill(eye, -1e9)
    logp = sim - torch.logsumexp(sim, 1, keepdim=True)
    has = pos.sum(1) > 0
    return -(logp * pos).sum(1)[has].div(pos.sum(1)[has]).mean()

def train_head(X, y, dim=128, epochs=300, lr=3e-3, wd=1e-3, hidden=0, seed=0, residual=True):
    torch.manual_seed(seed)
    D = X.shape[1]
    head = nn.Sequential(nn.Linear(D, hidden), nn.GELU(), nn.Linear(hidden, dim)) if hidden else nn.Linear(D, dim, bias=False)
    opt = torch.optim.AdamW(head.parameters(), lr=lr, weight_decay=wd)
    Xt = torch.tensor(X); yt = torch.tensor(y)
    for ep in range(epochs):
        # class-balanced batch: up to 8 crops each from 24 cats
        cats = np.random.permutation(np.unique(y))[:24]
        idx = np.concatenate([np.random.permutation(np.nonzero(y == c)[0])[:8] for c in cats])
        xb = Xt[idx] + 0.02 * torch.randn(len(idx), D)  # feature noise = cheap augmentation
        z = F.normalize(head(xb), dim=-1)
        loss = supcon(z, yt[idx]); opt.zero_grad(); loss.backward(); opt.step()
    return head

def oof_project(X, y_str, sess, train_mask, folds=5, seed=0, **kw):
    """Returns out-of-fold projected embeddings (N x dim) for all crops. train_mask marks usable labeled crops."""
    vis = np.unique(sess); rng = np.random.RandomState(seed); rng.shuffle(vis)
    fold_of = {v: i % folds for i, v in enumerate(vis)}
    f = np.array([fold_of[s] for s in sess])
    _, y = np.unique(y_str, return_inverse=True)
    Z = None
    for k in range(folds):
        tr = train_mask & (f != k)
        head = train_head(X[tr], y[tr], seed=seed, **kw)
        with torch.no_grad(): z = F.normalize(head(torch.tensor(X[f == k])), dim=-1).numpy()
        if Z is None: Z = np.zeros((len(X), z.shape[1]), np.float32)
        Z[f == k] = z
    return Z
