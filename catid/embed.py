"""Stage 3: embed crops with one model. python embed.py MODEL work_dir [crops|cropsm] [--tta]
Letterbox to square (keeps aspect: a stretched cat changes body shape). With --tta also runs the
h-flipped crop and saves BOTH emb/<model>__<variant>.npy (plain) and ..._tta.npy (mean of both).
L2-normalized, row order = dets.json order."""
import sys, os, json, time
import numpy as np, torch
from PIL import Image
sys.path.insert(0, os.path.dirname(__file__)); import models
name, work, variant = sys.argv[1], sys.argv[2], sys.argv[3]
tta = '--tta' in sys.argv
torch.set_num_threads(int(os.environ.get('THREADS', 4)))
dets = json.load(open(f'{work}/dets.json'))
fn, S, mean, std = models.load(name)
mean, std = torch.tensor(mean).view(3, 1, 1), torch.tensor(std).view(3, 1, 1)

def prep(path):
    im = Image.open(path).convert('RGB'); im.thumbnail((S, S), Image.BICUBIC)
    canvas = Image.new('RGB', (S, S), (124, 116, 104)); canvas.paste(im, ((S - im.width) // 2, (S - im.height) // 2))
    return (torch.from_numpy(np.asarray(canvas).copy()).permute(2, 0, 1).float() / 255 - mean) / std

out, outt, t0, B = [], [], time.time(), 16
with torch.inference_mode():
    for i in range(0, len(dets), B):
        x = torch.stack([prep(f"{work}/{variant}/{d['id']}.jpg") for d in dets[i:i + B]])
        e = torch.nn.functional.normalize(fn(x).float(), dim=-1)
        out.append(e.numpy())
        if tta: outt.append(torch.nn.functional.normalize(e + torch.nn.functional.normalize(fn(x.flip(-1)).float(), dim=-1), dim=-1).numpy())
dt = time.time() - t0
os.makedirs(f'{work}/emb', exist_ok=True)
for E, suffix in ((out, ''), (outt, '_tta')):
    if not E: continue
    E = np.concatenate(E); tag = f"{name}__{variant}{suffix}"
    np.save(f'{work}/emb/{tag}.npy', E.astype(np.float32))
    # timing: plain pass is ~half the total when TTA ran
    sec = dt if (suffix or not tta) else dt / 2
    json.dump({'model': name, 'variant': variant, 'tta': bool(suffix), 'n': len(dets), 'sec': sec,
               'ms_per_crop': 1000 * sec / len(dets), 'dim': E.shape[1]}, open(f'{work}/emb/{tag}.json', 'w'))
    print(tag, E.shape, f'{sec:.0f}s', f'{1000*sec/len(dets):.0f}ms/crop', flush=True)
