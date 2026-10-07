# catid — which shelter cat is this?

Experiments in identifying individual cats from a pile of phone photos taken at a cat café / shelter over
~6 months of visits, with embedding models + application-specific heuristics. No training labels to start
with; cats look alike (lots of black / tuxedo / orange), kittens grow up, and cats get adopted and new
ones arrive.

Photos are NOT in this repo (public). Only code, detections/masks (RLE silhouettes) and derived embeddings.

## Pipeline
1. `thumbs.py`      EXIF-rotate + 1024px thumbnails
2. `detect.py`      YOLO11-seg cat detection + instance masks  -> `dets_raw.json`
3. `filter_dets.py` cross-class NMS, size filter, RLE masks     -> `dets.json`
4. `crops.py`       crops from full-res originals: `crops/` (bbox+pad) and `cropsm/` (background greyed out)
5. `embed.py`       one embedding model over the crops (+ h-flip TTA)  -> `emb/<model>__<variant>[_tta].npy`
6. `collar.py`      hand-crafted collar-colour histogram
7. `heuristics.py`  whitening, burst/tracklet pooling, k-reciprocal re-ranking, collar similarity, ...
8. `evaluate.py`    cross-visit retrieval, chronological open-set ID ("cats come and go"), clustering

`worker.sh` lets a fresh cloud session rebuild the crops from the public zip and embed with a subset of models.
