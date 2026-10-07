"""Hand-crafted collar-colour descriptor. Café cats wear bright collars (pink, blue, lime/yellow, red...).
YOLO masks stop AT the collar, so we look at the mask dilated by RING px. Per-colour pixel rules (HSV), tuned so
that skin/wood/orange fur (hue 0-40, low-mid sat) and blue jeans (hue ~210, sat < .55) do not fire.
Output collar.npy: N x 5 fractions (relative to cat mask area) [pink, red, yellowgreen, blue, purple]."""
import sys, os, json, numpy as np
from PIL import Image
from scipy import ndimage
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import rle
RING = int(os.environ.get('RING', 10))
NAMES = ['pink', 'red', 'yellowgreen', 'blue', 'purple']

def rules(h, s, v):
    return [
        (((h >= 300) & (h < 345) & (s > 0.25)) | ((h >= 345) & (s > 0.25) & (s < 0.7))) & (v > 0.45),
        ((h >= 345) | (h < 12)) & (s >= 0.7) & (v > 0.35),
        (h >= 45) & (h < 100) & (s > 0.45) & (v > 0.5),
        (h >= 180) & (h < 250) & (s > 0.6) & (v > 0.35),
        (h >= 250) & (h < 300) & (s > 0.4) & (v > 0.3),
    ]

if __name__ == '__main__':
    work = sys.argv[1]
    dets = json.load(open(f'{work}/dets.json'))
    out = np.zeros((len(dets), len(NAMES)), np.float32); cache = {}
    for i, d in enumerate(dets):
        f = d['file']
        if f not in cache: cache = {f: np.asarray(Image.open(f'{work}/../img1024/{f}').convert('HSV')).astype(np.float32)}
        hsv = cache[f]; m0 = rle.decode(d['rle']).astype(bool)
        m = ndimage.binary_dilation(m0, iterations=RING)
        h, s, v = hsv[..., 0][m] * 360 / 255, hsv[..., 1][m] / 255, hsv[..., 2][m] / 255
        for b, sel in enumerate(rules(h, s, v)): out[i, b] = sel.sum() / max(m0.sum(), 1)
    np.save(f'{work}/collar.npy', out)
    top = out.argmax(1); strength = out.max(1)
    print({n: int(((top == k) & (strength > 0.004)).sum()) for k, n in enumerate(NAMES)}, 'none:', int((strength <= 0.004).sum()))
