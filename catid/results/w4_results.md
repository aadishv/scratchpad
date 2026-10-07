# w4: token pooling / mask-aware pooling / resolution (DINOv2-B reg4, one forward pass per crop, no TTA)
Metrics from `bench_combo.py` recipe. Baseline dinov2_b__cropsm: top1 0.463, set top3 0.732, +recency 0.592.
ms/crop is the shared forward pass on 3 CPU threads (all poolings of a run come from the same pass).

| tag | crops | top1 | set top3 | wv F1 | SIM | +recency | ms/crop |
|---|---|---|---|---|---|---|---|
| dinov2_b_sm_cls_336 | cropsm | 0.463 | 0.732 | 0.849 | 0.586 | 0.592 | 670 |
| dinov2_b_sm_mean_336 | cropsm | 0.284 | 0.537 | 0.759 | 0.522 | 0.528 | 670 |
| dinov2_b_sm_gem_336 | cropsm | 0.308 | 0.585 | 0.779 | 0.517 | 0.533 | 670 |
| dinov2_b_sm_cat_336 | cropsm | 0.430 | 0.724 | 0.851 | 0.562 | 0.599 | 670 |
| dinov2_b_sm_mmean_336 | cropsm, mask-weighted | 0.377 | 0.642 | 0.798 | 0.531 | 0.548 | 683 |
| dinov2_b_sm_mgem_336 | cropsm, mask-weighted | 0.383 | 0.667 | 0.821 | 0.548 | 0.555 | 683 |
| dinov2_b_sm_catm_336 | cropsm, cls+mask-mean | 0.421 | 0.740 | 0.843 | 0.581 | 0.594 | 683 |
| dinov2_b_raw_cls_336 | crops | 0.491 | 0.772 | 0.851 | 0.586 | 0.608 | 662 |
| dinov2_b_raw_mean_336 | crops | 0.273 | 0.455 | 0.793 | 0.537 | 0.539 | 662 |
| dinov2_b_raw_gem_336 | crops | 0.273 | 0.537 | 0.788 | 0.539 | 0.546 | 662 |
| dinov2_b_raw_cat_336 | crops | 0.430 | 0.724 | 0.853 | 0.603 | 0.621 | 662 |
| dinov2_b_raw_mmean_336 | crops, mask-weighted | 0.392 | 0.699 | 0.822 | 0.551 | 0.550 | 662 |
| dinov2_b_raw_mgem_336 | crops, mask-weighted | 0.410 | 0.707 | 0.825 | 0.542 | 0.583 | 662 |
| dinov2_b_raw_catm_336 | crops, cls+mask-mean | 0.489 | 0.748 | 0.848 | 0.586 | 0.612 | 662 |
| dinov2_b_raw_cls_224 | crops | 0.480 | 0.732 | 0.864 | 0.592 | 0.619 | 274 |
| dinov2_b_raw_cat_224 | crops | 0.432 | 0.715 | 0.858 | 0.575 | 0.603 | 274 |
| dinov2_b_raw_catm_224 | crops, cls+mask-mean | 0.471 | 0.724 | 0.854 | 0.579 | 0.603 | 274 |
| dinov2_b_raw_cls_448 | crops | 0.493 | 0.764 | 0.852 | 0.592 | 0.616 | 1283 |
| dinov2_b_raw_cat_448 | crops | 0.425 | 0.740 | 0.850 | 0.586 | 0.599 | 1283 |
| dinov2_b_raw_catm_448 | crops, cls+mask-mean | 0.478 | 0.756 | 0.852 | 0.616 | 0.621 | 1283 |
| dinov3_b_raw_cls_320 | crops | 0.515 | 0.732 | 0.841 | 0.616 | 0.623 | 482 |
| dinov3_b_raw_mean_320 | crops | 0.295 | 0.585 | 0.787 | 0.529 | 0.533 | 482 |
| dinov3_b_raw_cat_320 | crops | 0.454 | 0.699 | 0.844 | 0.605 | 0.616 | 482 |
| dinov3_b_raw_mmean_320 | crops, mask-weighted | 0.403 | 0.715 | 0.815 | 0.550 | 0.557 | 482 |
| dinov3_b_raw_catm_320 | crops, cls+mask-mean | 0.502 | 0.756 | 0.842 | 0.616 | 0.610 | 482 |

Conclusion: CLS stays the best single pooling; patch mean/GeM, with or without the mask, are far worse (-0.05 to -0.2 top1), and concatenating
them with CLS only shifts +recency by about ±0.02 (noise level). The robust gain is feeding unmasked crops (crops/) instead
of cropsm: DINOv2-B CLS goes from 0.463/0.732/0.592 to 0.491/0.772/0.608. 224 vs 336 vs 448 is within noise, so 224 (2.4x faster) is fine.
DINOv3-B CLS on crops/ at 320 gives the best top1 (0.515) and +recency (0.623).
