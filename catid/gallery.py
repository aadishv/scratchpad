"""External gallery: detect + embed the shelter's official listing photos (Shelterluv), then
(a) score how well a listing photo retrieves the same cat among the café crops (cross-domain), and
(b) propose names for café crops from listed cats, respecting the intake date (no sightings before intake)."""
import sys, os, json, glob, numpy as np, torch, datetime as dt
from PIL import Image, ImageOps
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import models
try:
    from pillow_heif import register_heif_opener; register_heif_opener()
except ImportError: pass
MCT = '/home/user/data/mct'
def embed_listing(tags=('dinov2_b', 'dinov2_l')):
    from ultralytics import YOLO
    det = YOLO('/home/user/data/work/yolo11x-seg.pt'); meta = {m['name'].replace(' ', '_'): m for m in json.load(open(f'{MCT}/meta.json'))}
    crops, info = [], []
    for p in sorted(glob.glob(f'{MCT}/photos/*')):
        name = os.path.basename(p).rsplit('_', 1)[0]
        try: im = ImageOps.exif_transpose(Image.open(p)).convert('RGB')
        except Exception: print('skip unreadable', os.path.basename(p)); continue
        im.thumbnail((1600, 1600))
        r = det.predict(im, imgsz=1024, conf=0.25, classes=[15], verbose=False)[0]
        if not len(r.boxes): continue
        i = int(r.boxes.conf.argmax()); x1, y1, x2, y2 = r.boxes.xyxy[i].tolist(); pd = 0.08 * max(x2 - x1, y2 - y1)  # listing photos show one cat: keep the best box
        crops.append(im.crop((max(0, x1 - pd), max(0, y1 - pd), min(im.width, x2 + pd), min(im.height, y2 + pd))))
        info.append({'name': name, 'file': os.path.basename(p), 'n_boxes': len(r.boxes)})
    out = {}
    for t in tags:
        fn, S, mean, std = models.load(t); mean, std = torch.tensor(mean).view(3, 1, 1), torch.tensor(std).view(3, 1, 1); X = []
        for c in crops:
            c = c.copy(); c.thumbnail((S, S)); cv = Image.new('RGB', (S, S), (124, 116, 104)); cv.paste(c, ((S - c.width) // 2, (S - c.height) // 2))
            X.append((torch.from_numpy(np.asarray(cv).copy()).permute(2, 0, 1).float() / 255 - mean) / std)
        with torch.inference_mode(): E = torch.nn.functional.normalize(torch.cat([fn(torch.stack(X[i:i+8])) for i in range(0, len(X), 8)]).float(), dim=-1).numpy()
        np.save(f'{MCT}/work/{t}.npy', E)
    os.makedirs(f'{MCT}/work/crops', exist_ok=True)
    for k, c in enumerate(crops): c.thumbnail((400, 400)); c.save(f"{MCT}/work/crops/{k:03d}_{info[k]['name']}.jpg")
    json.dump(info, open(f'{MCT}/work/info.json', 'w'), indent=1)
    print(len(crops), 'listing crops')
if __name__ == '__main__':
    embed_listing()
