#!/usr/bin/env bash
# Sibling-session worker: rebuild crops from the public Drive zip + dets.json, embed with the given models,
# write catid/results/emb/*.npy. Usage: bash catid/worker.sh "model1 model2 ..." [variants] (default "crops cropsm")
set -euo pipefail
MODELS="$1"; VARIANTS="${2:-crops cropsm}"
HERE="$(cd "$(dirname "$0")" && pwd)"; DATA=/home/user/data; W=$DATA/work
mkdir -p $DATA/raw $W
pip install --quiet torch torchvision --index-url https://download.pytorch.org/whl/cpu 2>&1 | grep -v WARNING || true
pip install --quiet open_clip_torch timm transformers safetensors scikit-learn pillow 2>&1 | grep -v WARNING || true
if [ ! -f $W/.crops_done ]; then
  curl -sSL --retry 5 -o $DATA/cats.zip "https://drive.usercontent.google.com/download?id=1_y8FkXamo9U4Ob3UfQmocydwHJ3u9axq&export=download&confirm=t"
  python3 -I -c "
import zipfile
z=zipfile.ZipFile('$DATA/cats.zip')
for i in z.infolist():
    if i.filename.lower().endswith('.jpg'): i.filename=i.filename.split('/')[-1]; z.extract(i,'$DATA/raw')"
  rm -f $DATA/cats.zip
  gunzip -c $HERE/results/dets.json.gz > $W/dets.json
  python3 $HERE/crops.py $DATA/raw $W && touch $W/.crops_done
fi
for m in $MODELS; do for v in $VARIANTS; do
  python3 $HERE/embed.py $m $W $v --tta 2>&1 | grep -v -i warn
done; done
mkdir -p $HERE/results/emb && cp $W/emb/* $HERE/results/emb/
