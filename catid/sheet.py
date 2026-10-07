"""Contact sheet: python sheet.py out.jpg cols tile img1 img2 ... (labels = index/name)"""
import sys
from PIL import Image, ImageDraw
out, cols, tile = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]); fs = sys.argv[4:]
rows = (len(fs) + cols - 1) // cols
S = Image.new('RGB', (cols * tile, rows * tile), 'white'); d = ImageDraw.Draw(S)
for i, f in enumerate(fs):
    im = Image.open(f); im.thumbnail((tile, tile)); x, y = (i % cols) * tile, (i // cols) * tile
    S.paste(im, (x, y)); lab = f.split('/')[-1].replace('PXL_2026','').replace('.jpg','')
    d.rectangle([x, y, x + 120, y + 12], fill='black'); d.text((x + 2, y), f"{i} {lab}", fill='yellow')
S.save(out, quality=85)
