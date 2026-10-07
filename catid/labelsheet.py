"""Render numbered crop grids for manual labeling / cluster review.
python labelsheet.py work out_prefix cols tile ids_file  (ids_file: one det id per line, '#title' lines start a new sheet)"""
import sys
from PIL import Image, ImageDraw
work, prefix, cols, tile, idf = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4]), sys.argv[5]
groups, cur = [], None
for line in open(idf):
    line = line.strip()
    if not line: continue
    if line.startswith('#'): cur = (line[1:], []); groups.append(cur)
    else:
        if cur is None: cur = ('', []); groups.append(cur)
        cur[1].append(line)
for gi, (title, ids) in enumerate(groups):
    for part in range(0, len(ids), cols * cols):
        chunk = ids[part:part + cols * cols]; rows = (len(chunk) + cols - 1) // cols
        S = Image.new('RGB', (cols * tile, rows * tile + 18), 'white'); d = ImageDraw.Draw(S)
        d.text((4, 3), f"{title}  ({part // (cols*cols)})", fill='black')
        for i, did in enumerate(chunk):
            im = Image.open(f'{work}/crops/{did}.jpg'); im.thumbnail((tile - 4, tile - 4))
            x, y = (i % cols) * tile, (i // cols) * tile + 18
            S.paste(im, (x + 2, y + 2)); lab = f"{part + i}"
            d.rectangle([x + 2, y + 2, x + 8 + 7 * len(lab), y + 15], fill='black'); d.text((x + 4, y + 3), lab, fill='yellow')
        S.save(f'{prefix}_{gi:02d}_{part // (cols*cols)}.jpg', quality=85)
