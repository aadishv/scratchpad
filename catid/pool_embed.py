"""Token-pooling study: ONE forward pass per crop of a timm DINO ViT, several poolings of the output tokens.
python pool_embed.py MODEL work_dir VARIANT SIZE [--poolings cls,mean,...] [--tag-prefix P]
MODEL is a timm name or a models.REGISTRY key (dinov2_b / dinov3_b). Crops are letterboxed exactly as in
embed.py. Poolings (all L2-normalized, rows in dets.json order):
  cls       CLS token                 mean   mean of patch tokens      gem   GeM(p=3) of patch tokens (clamped >0)
  cat       concat(L2 cls, L2 mean)   mmean  mask-weighted patch mean  mgem  mask-weighted GeM
  catm      concat(L2 cls, L2 mmean)
Mask weights: the dets.json RLE silhouette (1024px-thumbnail coords) cut to the same bbox+8% pad as crops.py,
resized to the crop, letterboxed like the image, then area-averaged onto the patch grid (soft weights).
Saves {work}/emb/<prefix>_<pool>_<size>.npy (+ .json with ms/crop)."""
import sys, os, json, time, argparse
import numpy as np, torch, timm
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import rle

TIMM = {'dinov2_b': 'vit_base_patch14_reg4_dinov2.lvd142m', 'dinov3_b': 'vit_base_patch16_dinov3.lvd1689m'}
IMNET = ((0.485, 0.456, 0.406), (0.229, 0.224, 0.225))
GREY = (124, 116, 104)

ap = argparse.ArgumentParser()
ap.add_argument('model'); ap.add_argument('work'); ap.add_argument('variant'); ap.add_argument('size', type=int)
ap.add_argument('--poolings', default='cls,mean,gem,cat,mmean,mgem,catm')
ap.add_argument('--tag-prefix', default=None)
a = ap.parse_args()
pools = a.poolings.split(',')
prefix = a.tag_prefix or a.model
torch.set_num_threads(int(os.environ.get('THREADS', 3)))
S = a.size
dets = json.load(open(f'{a.work}/dets.json'))
net = timm.create_model(TIMM.get(a.model, a.model), pretrained=True, num_classes=0, img_size=S).eval()
P = net.patch_embed.patch_size[0]; G = S // P; NP = net.num_prefix_tokens
mean, std = torch.tensor(IMNET[0]).view(3, 1, 1), torch.tensor(IMNET[1]).view(3, 1, 1)

def letterbox(im, fill):
    im = im.copy(); im.thumbnail((S, S), Image.BICUBIC if im.mode == 'RGB' else Image.BILINEAR)
    c = Image.new(im.mode, (S, S), fill); c.paste(im, ((S - im.width) // 2, (S - im.height) // 2)); return c

def prep(d):
    im = Image.open(f"{a.work}/{a.variant}/{d['id']}.jpg").convert('RGB')
    x = (torch.from_numpy(np.asarray(letterbox(im, GREY)).copy()).permute(2, 0, 1).float() / 255 - mean) / std
    # mask in thumbnail coords -> same crop box as crops.py -> crop's pixel size -> same letterbox
    x1, y1, x2, y2 = d['box']; p = 0.08 * max(x2 - x1, y2 - y1)
    b = (max(0, x1 - p), max(0, y1 - p), min(d['W'], x2 + p), min(d['H'], y2 + p))
    m = Image.fromarray(rle.decode(d['rle']).astype(np.float32)).crop(b).resize(im.size, Image.BILINEAR)
    m = np.asarray(letterbox(m, 0.0), np.float32)[:G * P, :G * P]
    w = torch.from_numpy(m.reshape(G, P, G, P).mean((1, 3)).ravel().clip(0, 1).copy())
    if w.sum() < 1: w = torch.ones_like(w)  # degenerate mask: fall back to plain mean
    return x, w

def l2(v): return torch.nn.functional.normalize(v.float(), dim=-1)
def gem(t, w, p=3.0):
    return ((t.clamp(min=1e-6).pow(p) * w[..., None]).sum(1) / w.sum(1, keepdim=True)).pow(1 / p)

out = {k: [] for k in pools}; t0 = time.time(); B = 16
with torch.inference_mode():
    for i in range(0, len(dets), B):
        xs, ws = zip(*[prep(d) for d in dets[i:i + B]])
        x, w = torch.stack(xs), torch.stack(ws)
        tok = net.forward_features(x); cls, pt = tok[:, 0], tok[:, NP:]
        assert pt.shape[1] == G * G, pt.shape
        one = torch.ones_like(w)
        f = {'cls': lambda: cls, 'mean': lambda: pt.mean(1), 'gem': lambda: gem(pt, one),
             'mmean': lambda: (pt * w[..., None]).sum(1) / w.sum(1, keepdim=True), 'mgem': lambda: gem(pt, w)}
        f['cat'] = lambda: torch.cat([l2(f['cls']()), l2(f['mean']())], 1)
        f['catm'] = lambda: torch.cat([l2(f['cls']()), l2(f['mmean']())], 1)
        for k in pools: out[k].append(l2(f[k]()).numpy())
dt = time.time() - t0
os.makedirs(f'{a.work}/emb', exist_ok=True)
for k in pools:
    E = np.concatenate(out[k]).astype(np.float32); tag = f'{prefix}_{k}_{S}'
    np.save(f'{a.work}/emb/{tag}.npy', E)
    json.dump({'model': a.model, 'variant': a.variant, 'pool': k, 'size': S, 'n': len(dets),
               'ms_per_crop': 1000 * dt / len(dets), 'dim': E.shape[1]}, open(f'{a.work}/emb/{tag}.json', 'w'))
    print(tag, E.shape, f'{1000 * dt / len(dets):.0f}ms/crop (shared pass)', flush=True)
