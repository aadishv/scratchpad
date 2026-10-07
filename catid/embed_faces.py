"""Embed face crops (WORK/faces/<id>.jpg) with a model; rows without a face crop get zeros. -> emb/<model>__faces.npy"""
import sys, os, json, numpy as np, torch
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import models
name, work = sys.argv[1], sys.argv[2]
torch.set_num_threads(4)
dets = json.load(open(f'{work}/dets.json')); fn, S, mean, std = models.load(name)
mean, std = torch.tensor(mean).view(3, 1, 1), torch.tensor(std).view(3, 1, 1)
idx = [i for i, d in enumerate(dets) if os.path.exists(f"{work}/faces/{d['id']}.jpg")]
def prep(p):
    im = Image.open(p).convert('RGB'); im.thumbnail((S, S)); c = Image.new('RGB', (S, S), (124, 116, 104)); c.paste(im, ((S - im.width) // 2, (S - im.height) // 2))
    return (torch.from_numpy(np.asarray(c).copy()).permute(2, 0, 1).float() / 255 - mean) / std
E = None
with torch.inference_mode():
    for k in range(0, len(idx), 16):
        x = torch.stack([prep(f"{work}/faces/{dets[i]['id']}.jpg") for i in idx[k:k + 16]])
        e = torch.nn.functional.normalize(fn(x).float(), dim=-1).numpy()
        if E is None: E = np.zeros((len(dets), e.shape[1]), np.float32)
        E[idx[k:k + 16]] = e
np.save(f'{work}/emb/{name}__faces.npy', E); print(name, len(idx), 'faces')
