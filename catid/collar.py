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
        (h >= 180) & (h < 232) & (s > 0.6) & (v > 0.55),  # collar blue is bright; jeans/towels are darker
        (h >= 250) & (h < 300) & (s > 0.4) & (v > 0.3),
    ]

def collar_vector(hsv, m0, others, ring=10, outer=28, bg_max=0.25):
    """Colour fractions in the band just around the cat mask, excluding other cats' pixels.
    A colour that also covers more than bg_max of the wider outer band is background (towel, jeans,
    pants, a toy pile), not a collar, and is zeroed."""
    inner = ndimage.binary_dilation(m0, iterations=ring) & ~others
    band = ndimage.binary_dilation(m0, iterations=outer) & ~ndimage.binary_dilation(m0, iterations=ring) & ~others
    def frac(region):
        h, s, v = hsv[..., 0][region] * 360 / 255, hsv[..., 1][region] / 255, hsv[..., 2][region] / 255
        return np.array([r.sum() for r in rules(h, s, v)], np.float32)
    cin, cbg = frac(inner) / max(m0.sum(), 1), frac(band) / max(band.sum(), 1)
    fam = cbg.copy(); fam[0] = fam[1] = cbg[0] + cbg[1]  # pink and red are one family (red pants fire both)
    cin[fam > bg_max] = 0
    return cin

if __name__ == '__main__':
    work = sys.argv[1]
    dets = json.load(open(f'{work}/dets.json'))
    out = np.zeros((len(dets), len(NAMES)), np.float32)
    by = {}
    for i, d in enumerate(dets): by.setdefault(d['file'], []).append(i)
    for f, idx in by.items():
        hsv = np.asarray(Image.open(f'{work}/../img1024/{f}').convert('HSV')).astype(np.float32)
        ms = {i: rle.decode(dets[i]['rle']).astype(bool) for i in idx}
        for i in idx:
            others = np.zeros_like(ms[i])
            for j in idx:
                # other detections that are not this cat's duplicate fragments
                if j != i and (ms[i] & ms[j]).sum() / min(ms[i].sum(), ms[j].sum()) < 0.5: others |= ms[j]
            out[i] = collar_vector(hsv, ms[i], ndimage.binary_dilation(others, iterations=3))
    np.save(f'{work}/collar.npy', out)
    top = out.argmax(1); strength = out.max(1)
    print({n: int(((top == k) & (strength > 0.004)).sum()) for k, n in enumerate(NAMES)}, 'none:', int((strength <= 0.004).sum()))
