"""Tiny run-length codec for binary masks (row-major), so detections+masks ship as one small JSON."""
import numpy as np
def encode(m):
    f = np.concatenate([[0], m.ravel().astype(np.uint8), [0]]); r = np.nonzero(f[1:] != f[:-1])[0]
    return {'shape': list(m.shape), 'runs': (r[1::2] - r[::2]).tolist(), 'starts': r[::2].tolist()}
def decode(e):
    m = np.zeros(e['shape'][0] * e['shape'][1], np.uint8)
    for s, n in zip(e['starts'], e['runs']): m[s:s + n] = 1
    return m.reshape(e['shape'])
