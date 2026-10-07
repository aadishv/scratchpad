# w4: token pooling / mask-aware pooling / resolution (DINOv2-B reg4, one forward pass per crop, no TTA)
Metrics from `bench_combo.py` recipe. Baseline dinov2_b__cropsm: top1 0.463, set top3 0.732, +recency 0.592.
ms/crop is the shared forward pass on 3 CPU threads (all poolings of a run come from the same pass).

| tag | crops | top1 | set top3 | wv F1 | SIM | +recency | ms/crop |
|---|---|---|---|---|---|---|---|
| dinov2_b_sm_cls_336 | cropsm | 0.463 | 0.732 | 0.849 | 0.586 | 0.592 | 670 |
| dinov2_b_sm_mean_336 | cropsm | 0.284 | 0.537 | 0.759 | 0.522 | 0.528 | 670 |
| dinov2_b_sm_gem_336 | cropsm | 0.308 | 0.585 | 0.779 | 0.517 | 0.533 | 670 |
| dinov2_b_sm_cat_336 | cropsm | 0.430 | 0.724 | 0.851 | 0.562 | 0.599 | 670 |
