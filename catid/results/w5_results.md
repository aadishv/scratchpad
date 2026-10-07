# w5: local feature re-ranking (DISK 1024 kpts + LightGlue, K=30)

16993 candidate pairs; features 449s for 827 crops; matching 275s for 993 pairs = 277 ms/pair (CPU, 4 threads, + F-matrix MAGSAC)
Note: the DISK+LightGlue run was resumed twice. The timed segment above is the last resumed chunk; the full 16,993-pair run averaged 238-249 ms/pair (about 70 min of matching plus 7.5 min of features at 543 ms/crop). Per-coat column = the variant with the best mean per-coat top-1.

RootSIFT variant: features 40s, matching 137s = 8.1 ms/pair

| variant | w | top1 | mAP | set top1 | set top3 | wv F1 | SIM | +recency |
|---|---|---|---|---|---|---|---|---|
| baseline | 0 | 0.463 | 0.383 | 0.488 | 0.732 | 0.849 | 0.586 | 0.592 |
| n_inl log1p/log1p(200) | 0.05 | 0.467 | 0.382 | 0.496 | 0.724 | 0.849 | 0.588 | 0.596 |
| n_inl log1p/log1p(200) | 0.1 | 0.458 | 0.382 | 0.496 | 0.715 | 0.849 | 0.590 | 0.599 |
| n_inl log1p/log1p(200) | 0.2 | 0.460 | 0.383 | 0.488 | 0.724 | 0.849 | 0.588 | 0.596 |
| n_inl log1p/log1p(200) | 0.4 | 0.480 | 0.377 | 0.488 | 0.715 | 0.849 | 0.590 | 0.594 |
| n_inl_fg log1p/log1p(200) | 0.05 | 0.467 | 0.383 | 0.496 | 0.724 | 0.849 | 0.586 | 0.592 |
| n_inl_fg log1p/log1p(200) | 0.1 | 0.460 | 0.382 | 0.480 | 0.724 | 0.849 | 0.590 | 0.597 |
| n_inl_fg log1p/log1p(200) | 0.2 | 0.458 | 0.378 | 0.472 | 0.724 | 0.849 | 0.599 | 0.599 |
| n_inl_fg log1p/log1p(200) | 0.4 | 0.460 | 0.371 | 0.472 | 0.699 | 0.849 | 0.588 | 0.594 |
| n_lg_fg log1p/log1p(200) | 0.05 | 0.465 | 0.383 | 0.496 | 0.724 | 0.849 | 0.588 | 0.596 |
| n_lg_fg log1p/log1p(200) | 0.1 | 0.463 | 0.382 | 0.480 | 0.724 | 0.849 | 0.590 | 0.596 |
| n_lg_fg log1p/log1p(200) | 0.2 | 0.463 | 0.378 | 0.472 | 0.699 | 0.849 | 0.590 | 0.599 |
| n_lg_fg log1p/log1p(200) | 0.4 | 0.463 | 0.370 | 0.463 | 0.707 | 0.849 | 0.590 | 0.588 |
| sift_inl log1p/log1p(200) | 0.05 | 0.465 | 0.382 | 0.472 | 0.724 | 0.849 | 0.590 | 0.596 |
| sift_inl log1p/log1p(200) | 0.1 | 0.454 | 0.377 | 0.472 | 0.732 | 0.849 | 0.588 | 0.599 |
| sift_inl log1p/log1p(200) | 0.2 | 0.438 | 0.368 | 0.447 | 0.740 | 0.849 | 0.592 | 0.607 |
| sift_inl log1p/log1p(200) | 0.4 | 0.401 | 0.350 | 0.423 | 0.699 | 0.849 | 0.592 | 0.596 |
| sift_inl_fg log1p/log1p(200) | 0.05 | 0.460 | 0.383 | 0.480 | 0.724 | 0.849 | 0.588 | 0.596 |
| sift_inl_fg log1p/log1p(200) | 0.1 | 0.465 | 0.382 | 0.488 | 0.715 | 0.849 | 0.592 | 0.594 |
| sift_inl_fg log1p/log1p(200) | 0.2 | 0.452 | 0.375 | 0.480 | 0.724 | 0.849 | 0.592 | 0.599 |
| sift_inl_fg log1p/log1p(200) | 0.4 | 0.434 | 0.365 | 0.480 | 0.732 | 0.849 | 0.586 | 0.594 |
| n_inl_fg sigmoid(mu=25,s=8) | 0.1 | 0.463 | 0.381 | 0.504 | 0.724 | 0.849 | 0.590 | 0.592 |
| n_inl_fg sigmoid(mu=25,s=8) | 0.2 | 0.469 | 0.376 | 0.504 | 0.732 | 0.849 | 0.594 | 0.592 |
| n_inl_fg sigmoid(mu=50,s=15) | 0.1 | 0.467 | 0.382 | 0.512 | 0.724 | 0.849 | 0.588 | 0.590 |
| n_inl_fg sigmoid(mu=50,s=15) | 0.2 | 0.467 | 0.379 | 0.504 | 0.724 | 0.849 | 0.590 | 0.588 |

Candidate-pair match counts (labelled pairs; median / 90th pct):

n_lg: same cat 30 / 116 (n=1413), diff cat 29 / 67 (n=6494)  
n_inl: same cat 15 / 81 (n=1413), diff cat 14 / 38 (n=6494)  
n_lg_fg: same cat 19 / 110 (n=1413), diff cat 18 / 58 (n=6494)  
n_inl_fg: same cat 11 / 80 (n=1413), diff cat 9 / 35 (n=6494)  
conf_sum: same cat 8 / 52 (n=1413), diff cat 8 / 21 (n=6494)  
sift_n: same cat 8 / 16 (n=1413), diff cat 8 / 15 (n=6494)  
sift_inl: same cat 7 / 9 (n=1413), diff cat 7 / 9 (n=6494)  
sift_n_fg: same cat 4 / 10 (n=1413), diff cat 4 / 9 (n=6494)  
sift_inl_fg: same cat 0 / 7 (n=1413), diff cat 0 / 6 (n=6494)  
AUC same-vs-diff among candidates: recipe sim 0.723, n_lg 0.531, n_inl 0.536, n_lg_fg 0.542, n_inl_fg 0.551, conf_sum 0.537, sift_n 0.518, sift_inl 0.523, sift_n_fg 0.543, sift_inl_fg 0.526


Per-coat cross-visit top-1 (query coat = CLIP zero-shot argmax; n queries):

| coat | n | baseline | n_inl log1p/log1p(200) w=0.4 |
|---|---|---|---|
| solid black | 85 | 0.376 | 0.376 |
| tuxedo | 40 | 0.250 | 0.300 |
| black and white bicolor | 4 | 0.750 | 0.750 |
| orange tabby | 92 | 0.533 | 0.565 |
| orange and white | 15 | 0.467 | 0.533 |
| brown tabby | 45 | 0.378 | 0.378 |
| tabby and white | 15 | 0.467 | 0.533 |
| calico | 38 | 0.763 | 0.711 |
| tortoiseshell | 15 | 0.200 | 0.133 |
| dilute | 18 | 0.444 | 0.556 |
| colorpoint | 35 | 0.686 | 0.743 |
| white | 23 | 0.609 | 0.565 |
| gray | 29 | 0.241 | 0.276 |
