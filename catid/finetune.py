"""End-to-end fine-tuning of DINOv2 on the confirmed labels, evaluated leave-VISITS-out.

    python finetune.py WORK OUT_TAG [--arch dinov2_s] [--size 224] [--unfreeze 4] [--steps 300] [--folds 5] [--loss supcon|arcface]

For each fold, the held-out visits' crops are never seen in training; their embeddings come from the model
trained on the other visits. Output: WORK/emb/OUT_TAG.npy (N x D, dets.json order) = out-of-fold embeddings,
directly comparable with the frozen-model embeddings through bench.py / bench_combo.py.

Augmentations are identity-preserving for cats: random resized crop, h-flip, small rotation, brightness/contrast,
blur. No hue/saturation jitter (coat colour is identity). Batches are P cats x K crops, K drawn from as many
different visits as possible, so positives are mostly cross-visit (same-visit positives teach shortcuts).
"""
import os, sys, json, time, argparse, random
import numpy as np, torch, torch.nn as nn, torch.nn.functional as F
from PIL import Image, ImageFilter
import torchvision.transforms as T
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import models, common

ap = argparse.ArgumentParser()
ap.add_argument('work'); ap.add_argument('tag')
ap.add_argument('--arch', default='dinov2_s'); ap.add_argument('--size', type=int, default=224)
ap.add_argument('--unfreeze', type=int, default=4, help='number of last transformer blocks to train')
ap.add_argument('--steps', type=int, default=300); ap.add_argument('--lr', type=float, default=2e-5)
ap.add_argument('--P', type=int, default=8); ap.add_argument('--K', type=int, default=4)
ap.add_argument('--folds', type=int, default=5); ap.add_argument('--loss', default='supcon')
ap.add_argument('--threads', type=int, default=4); ap.add_argument('--labels', default=None)
ap.add_argument('--max-folds', type=int, default=99, help='run only the first N folds (quick tests)')
a = ap.parse_args()
torch.set_num_threads(a.threads); torch.manual_seed(0); random.seed(0); np.random.seed(0)

dets = json.load(open(f'{a.work}/dets.json'))
lab = json.load(open(a.labels or os.path.join(os.path.dirname(os.path.abspath(__file__)), 'labels/labels_v5.json')))
primary = np.load(f'{a.work}/primary.npy')
files = [d['file'] for d in dets]; sess = common.sessions(files)
raw = np.array([lab[d['id']] for d in dets]); y = np.array([l.rstrip('~') for l in raw])
usable = primary & ~np.isin(raw, ['?', 'x']) & ~np.char.endswith(raw.astype(str), '~')

_, S, mean, std = models.load(a.arch)  # for size/norm only
mean, std = list(mean), list(std)
aug = T.Compose([T.RandomResizedCrop(a.size, scale=(0.55, 1.0), ratio=(0.75, 1.33)), T.RandomHorizontalFlip(),
                 T.RandomApply([T.RandomRotation(12)], p=0.4), T.RandomApply([T.ColorJitter(0.25, 0.25, 0, 0)], p=0.6),
                 T.RandomApply([T.GaussianBlur(5, (0.1, 1.2))], p=0.2), T.ToTensor(), T.Normalize(mean, std)])
def letterbox(path, size):
    im = Image.open(path).convert('RGB'); im.thumbnail((size, size), Image.BICUBIC)
    c = Image.new('RGB', (size, size), (124, 116, 104)); c.paste(im, ((size - im.width) // 2, (size - im.height) // 2)); return c
plain = T.Compose([T.ToTensor(), T.Normalize(mean, std)])
cache = {}
def img(i):
    if i not in cache: cache[i] = Image.open(f"{a.work}/crops/{dets[i]['id']}.jpg").convert('RGB')
    return cache[i]

def build():
    import timm
    name = {'dinov2_s': 'vit_small_patch14_reg4_dinov2.lvd142m', 'dinov2_b': 'vit_base_patch14_reg4_dinov2.lvd142m'}[a.arch]
    m = timm.create_model(name, pretrained=True, num_classes=0, img_size=a.size)
    for p in m.parameters(): p.requires_grad = False
    for blk in m.blocks[-a.unfreeze:]:
        for p in blk.parameters(): p.requires_grad = True
    for p in m.norm.parameters(): p.requires_grad = True
    return m

def supcon(z, yb, t=0.07):
    sim = z @ z.T / t; eye = torch.eye(len(yb), dtype=torch.bool); pos = (yb[:, None] == yb[None, :]) & ~eye
    logp = sim.masked_fill(eye, -1e9); logp = logp - torch.logsumexp(logp, 1, keepdim=True)
    has = pos.sum(1) > 0
    return -(logp * pos).sum(1)[has].div(pos.sum(1)[has]).mean()

class ArcFace(nn.Module):
    def __init__(s, d, n, m=0.3, sc=30.0):
        super().__init__(); s.W = nn.Parameter(torch.randn(n, d) * 0.01); s.m, s.s = m, sc
    def forward(s, z, yb):
        cos = z @ F.normalize(s.W, dim=-1).T; th = torch.acos(cos.clamp(-1 + 1e-6, 1 - 1e-6))
        logits = torch.where(F.one_hot(yb, cos.shape[1]).bool(), torch.cos(th + s.m), cos) * s.s
        return F.cross_entropy(logits, yb)

def sample_batch(idx_by_cat, cats):
    """P cats x K crops; crops spread over as many visits as possible."""
    chosen = random.sample(cats, min(a.P, len(cats))); idx, yb = [], []
    for c in chosen:
        pool = idx_by_cat[c]; by_v = {}
        for i in pool: by_v.setdefault(sess[i], []).append(i)
        vs = list(by_v); random.shuffle(vs); pick = []
        while len(pick) < a.K:
            for v in vs:
                if len(pick) < a.K: pick.append(random.choice(by_v[v]))
        idx += pick; yb += [c] * a.K
    return idx, yb

def embed_all(m, which):
    m.eval(); out = []
    with torch.inference_mode():
        for k in range(0, len(which), 32):
            x = torch.stack([plain(letterbox(f"{a.work}/crops/{dets[i]['id']}.jpg", a.size)) for i in which[k:k + 32]])
            out.append(F.normalize(m(x), dim=-1).numpy())
    return np.concatenate(out)

vis = np.unique(sess); rng = np.random.RandomState(0); rng.shuffle(vis)
fold_of = {v: k % a.folds for k, v in enumerate(vis)}; fold = np.array([fold_of[s] for s in sess])
Z = None; t0 = time.time(); log = []
for k in range(min(a.folds, a.max_folds)):
    tr = usable & (fold != k)
    cats = sorted(set(y[tr])); cid = {c: n for n, c in enumerate(cats)}
    idx_by_cat = {c: list(np.nonzero(tr & (y == c))[0]) for c in cats}
    # cats seen in >= 2 visits drive cross-visit positives; single-visit cats still act as negatives
    m = build(); head = ArcFace(m.num_features, len(cats)) if a.loss == 'arcface' else None
    params = [p for p in m.parameters() if p.requires_grad] + (list(head.parameters()) if head else [])
    opt = torch.optim.AdamW(params, lr=a.lr, weight_decay=0.05)
    sched = torch.optim.lr_scheduler.OneCycleLR(opt, max_lr=a.lr, total_steps=a.steps, pct_start=0.1)
    m.train()
    for step in range(a.steps):
        idx, yb = sample_batch(idx_by_cat, cats)
        x = torch.stack([aug(img(i)) for i in idx]); yt = torch.tensor([cid[c] for c in yb])
        z = F.normalize(m(x), dim=-1)
        loss = head(z, yt) if head else supcon(z, yt)
        opt.zero_grad(); loss.backward(); opt.step(); sched.step()
        if step % 50 == 0: print(f'fold {k} step {step} loss {loss.item():.3f} {time.time() - t0:.0f}s', flush=True)
    test = np.nonzero(fold == k)[0]
    zt = embed_all(m, list(test))
    if Z is None: Z = np.zeros((len(dets), zt.shape[1]), np.float32)
    Z[test] = zt; log.append({'fold': k, 'train_crops': int(tr.sum()), 'cats': len(cats), 'sec': time.time() - t0})
os.makedirs(f'{a.work}/emb', exist_ok=True)
np.save(f'{a.work}/emb/{a.tag}.npy', Z)
json.dump({'args': vars(a), 'folds': log, 'sec': time.time() - t0}, open(f'{a.work}/emb/{a.tag}.json', 'w'), indent=1)
print('saved', a.tag, Z.shape, f'{time.time() - t0:.0f}s')
