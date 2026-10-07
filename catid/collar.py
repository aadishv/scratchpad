"""Hand-crafted collar-colour descriptor. Café cats wear bright collars (pink, blue, lime, red, yellow...).
Inside the (undilated) YOLO cat mask, count strongly-saturated pixels per hue bin. Natural cat fur is never
saturated blue/pink/green, and orange fur sits at moderate saturation, so the histogram is ~0 except for
collars/tags (and toys/clothes that bleed into the mask, which is the main failure mode).
Output: collar.npy, N x 8 fractions [red, orange-ish, yellow, green, cyan, blue, purple, pink]."""
import sys, json, numpy as np
from PIL import Image, ImageOps
sys.path.insert(0, __import__('os').path.dirname(__import__('os').path.abspath(__file__))); import rle
work = sys.argv[1]
dets = json.load(open(f'{work}/dets.json'))
BINS = [(-15, 12, 'red'), (12, 40, 'orange'), (40, 70, 'yellow'), (70, 160, 'green'), (160, 200, 'cyan'),
        (200, 255, 'blue'), (255, 290, 'purple'), (290, 345, 'pink')]
out = np.zeros((len(dets), len(BINS)), np.float32)
cache = {}
for i, d in enumerate(dets):
    f = d['file']
    if f not in cache: cache = {f: np.asarray(Image.open(f'{work}/../img1024/{f}').convert('HSV')).astype(np.float32)}
    hsv = cache[f]; m = rle.decode(d['rle']).astype(bool)
    h = hsv[..., 0][m] * 360 / 255; s = hsv[..., 1][m] / 255; v = hsv[..., 2][m] / 255
    h = np.where(h > 345, h - 360, h)
    strong = (s > 0.55) & (v > 0.30)
    for b, (lo, hi, _) in enumerate(BINS):
        sel = strong & (h >= lo) & (h < hi)
        if BINS[b][2] in ('red', 'orange'): sel &= s > 0.75  # orange/ginger fur is saturated-ish: demand more
        out[i, b] = sel.sum() / max(m.sum(), 1)
np.save(f'{work}/collar.npy', out)
names = [b[2] for b in BINS]
top = out.argmax(1); strength = out.max(1)
print({n: int(((top == k) & (strength > 0.004)).sum()) for k, n in enumerate(names)}, 'none:', int((strength <= 0.004).sum()))
