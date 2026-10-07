"""Local-feature re-ranking (wildlife re-ID trick): DISK keypoints + LightGlue on the unmasked crops, only for
each primary crop's top-K cross-visit candidates under the recipe similarity; score = matches / RANSAC inliers.
  python3 catid/local_match.py match [K]   -> results/local_pairs.npz (pair cache, resumable)
  python3 catid/local_match.py fuse        -> S_recipe + w * f(n) variants through bench.score -> results/w5_results.md"""
import sys, os, time, json, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bench as B, heuristics as H
HERE = os.path.dirname(os.path.abspath(__file__))
CACHE = f'{HERE}/results/local_pairs.npz'; LOGMD = f'{HERE}/results/w5_results.md'
NFEAT = int(os.environ.get('NFEAT', 1024))

def recipe():
    E = np.load(f'{B.WORK}/emb/dinov2_b__cropsm.npy'); Sc = H.collar_sim(np.load(f'{B.WORK}/collar.npy'))
    Et = H.tracklet_pool(H.center(E), B.tid, alpha=0.5); return Et @ Et.T + 0.1 * Sc

def candidate_pairs(S, K):
    P = B.PRIMARY; S = S.copy(); S[B.sess[:, None] == B.sess[None, :]] = -np.inf; S[:, ~P] = -np.inf
    pairs = set()
    for i in np.nonzero(P)[0]:
        for j in np.argsort(-S[i])[:K]: pairs.add((min(i, j), max(i, j)))
    return np.array(sorted(pairs))

def features(ids):
    """DISK keypoints/descriptors per crop + per-keypoint foreground flag (crops vs cropsm: masked-out pixels differ)."""
    import torch, kornia.feature as KF
    from PIL import Image
    disk = KF.DISK.from_pretrained('depth').eval(); out = []
    for k, i in enumerate(ids):
        a = np.asarray(Image.open(f'{B.WORK}/crops/{i}.jpg').convert('RGB'), np.float32)
        m = np.asarray(Image.open(f'{B.WORK}/cropsm/{i}.jpg').convert('RGB'), np.float32)
        fg = np.abs(a - m).mean(2) < 12
        h, w = a.shape[:2]; H8, W8 = h // 16 * 16, w // 16 * 16  # DISK needs /16 sizes
        x = torch.from_numpy(a[:H8, :W8]).permute(2, 0, 1)[None] / 255
        with torch.inference_mode(): f = disk(x, NFEAT, pad_if_not_divisible=True)[0]
        kp = f.keypoints.numpy(); xi = kp[:, 0].astype(int).clip(0, W8 - 1); yi = kp[:, 1].astype(int).clip(0, H8 - 1)
        out.append(dict(kp=f.keypoints, desc=f.descriptors, fg=fg[yi, xi], hw=(H8, W8)))
        if k % 100 == 0: print('feat', k, len(ids), flush=True)
    return out

def match(K=30):
    import torch, kornia.feature as KF, cv2
    torch.set_num_threads(4)
    S = recipe(); pairs = candidate_pairs(S, K); print(len(pairs), 'pairs', flush=True)
    ids = [d['id'] for d in B.dets]; need = np.unique(pairs)
    t0 = time.time(); F = dict(zip(need, features([ids[i] for i in need]))); t_feat = time.time() - t0
    lg = KF.LightGlue('disk').eval()
    done = {}
    if os.path.exists(CACHE):
        z = np.load(CACHE); done = {(int(a), int(b)): r for (a, b), r in zip(z['pairs'], z['scores'])}
    def save(t_match, n_new):
        P = np.array(list(done)); Sc = np.array(list(done.values()))
        np.savez_compressed(CACHE, pairs=P, scores=Sc, cols=np.array(['n_lg', 'n_inl', 'n_lg_fg', 'n_inl_fg', 'conf_sum']),
                            K=K, nfeat=NFEAT, t_feat=t_feat, t_match=t_match, n_timed=n_new)
    t0 = time.time(); n_new = 0
    for k, (i, j) in enumerate(pairs):
        if (i, j) in done: continue
        a, b = F[i], F[j]
        with torch.inference_mode():
            o = lg({'image0': {'keypoints': a['kp'][None], 'descriptors': a['desc'][None], 'image_size': torch.tensor([a['hw'][::-1]])},
                    'image1': {'keypoints': b['kp'][None], 'descriptors': b['desc'][None], 'image_size': torch.tensor([b['hw'][::-1]])}})
        m = o['matches'][0].numpy(); c = o['scores'][0].numpy()
        fgm = a['fg'][m[:, 0]] & b['fg'][m[:, 1]] if len(m) else np.zeros(0, bool)
        inl = np.zeros(len(m), bool)
        if len(m) >= 8:
            p0 = a['kp'][m[:, 0]].numpy(); p1 = b['kp'][m[:, 1]].numpy()
            _, msk = cv2.findFundamentalMat(p0, p1, cv2.USAC_MAGSAC, 3.0, 0.999, 2000)
            if msk is not None: inl = msk.ravel().astype(bool)
        done[(int(i), int(j))] = np.array([len(m), inl.sum(), fgm.sum(), (inl & fgm).sum(), c.sum()], np.float32)
        n_new += 1
        if n_new % 1000 == 0:
            save(time.time() - t0, n_new); el = time.time() - t0
            print(f'{k}/{len(pairs)} {1000 * el / n_new:.0f} ms/pair', flush=True)
    t_match = time.time() - t0; save(t_match, n_new)
    print(f'features {t_feat:.0f}s ({1000 * t_feat / len(need):.0f} ms/img), matching {t_match:.0f}s ({1000 * t_match / max(n_new, 1):.0f} ms/pair)')

def fuse():
    S0 = recipe(); z = np.load(CACHE); P, Sc, cols = z['pairs'], z['scores'], list(z['cols'])
    coat = np.load(f'{B.WORK}/coat.npy').argmax(1)
    names = json.load(open(f'{B.WORK}/coat_names.json')) if os.path.exists(f'{B.WORK}/coat_names.json') else None
    def bonus(col, f):
        M = np.zeros_like(S0); v = f(Sc[:, cols.index(col)]); M[P[:, 0], P[:, 1]] = v; M[P[:, 1], P[:, 0]] = v; return M
    log = lambda n, c=200: np.log1p(n) / np.log1p(c)
    sig = lambda mu, s: (lambda n: 1 / (1 + np.exp(-(n - mu) / s)))
    variants = [('baseline', None, None, 0)]
    for col in ('n_inl', 'n_inl_fg', 'n_lg_fg'):
        for w in (0.05, 0.1, 0.2, 0.4): variants.append((f'{col} log1p/log1p(200)', col, log, w))
    for w in (0.1, 0.2): variants.append(('n_inl_fg sigmoid(mu=25,s=8)', 'n_inl_fg', sig(25, 8), w))
    for w in (0.1, 0.2): variants.append(('n_inl_fg sigmoid(mu=50,s=15)', 'n_inl_fg', sig(50, 15), w))
    out, lines = [], []
    tf, tm, nt = float(z['t_feat']), float(z['t_match']), int(z['n_timed'])
    lines.append(f'# w5: local feature re-ranking (DISK {int(z["nfeat"])} kpts + LightGlue, K={int(z["K"])})\n')
    lines.append(f'{len(P)} candidate pairs; features {tf:.0f}s for {len(np.unique(P))} crops; matching {tm:.0f}s for {nt} pairs '
                 f'= {1000 * tm / max(nt, 1):.0f} ms/pair (CPU, 4 threads, + F-matrix MAGSAC)\n')
    lines.append('| variant | w | top1 | mAP | set top1 | set top3 | wv F1 | SIM | +recency |\n|---|---|---|---|---|---|---|---|---|')
    pc = {}
    for name, col, f, w in variants:
        S = S0 if col is None else S0 + w * bonus(col, f)
        r = B.score(S, f'w5 {name} w={w}', out)
        lines.append(f"| {name} | {w} | {r['loose_top1']:.3f} | {r['loose_mAP']:.3f} | {r['set_top1']:.3f} | {r['set_top3']:.3f} | "
                     f"{r['wv_bF1']:.3f} | {r['sim_acc']:.3f} | {r['simR_acc']:.3f} |")
        # per-coat cross-visit top-1 (query coat = CLIP zero-shot argmax)
        m = B.keep; Sm = S[np.ix_(m, m)].copy(); y = B.y_loose[m]; s = B.sess[m]; cm = coat[m]
        Sm[s[:, None] == s[None, :]] = -np.inf
        ok = np.array([(y[s != s[q]] == y[q]).any() for q in range(len(y))])
        hit = y[Sm.argmax(1)] == y
        pc[f'{name} w={w}'] = {int(c): (hit[ok & (cm == c)].mean(), int((ok & (cm == c)).sum())) for c in np.unique(cm[ok])}
    # pair diagnostics: inlier distribution for same-cat vs different-cat candidate pairs
    yl = B.y_loose; lab = B.keep[P[:, 0]] & B.keep[P[:, 1]]; same = yl[P[:, 0]] == yl[P[:, 1]]
    lines.append('\nCandidate-pair match counts (labelled pairs; median / 90th pct):\n')
    for col in cols:
        v = Sc[:, cols.index(col)]
        lines.append(f'{col}: same cat {np.median(v[lab & same]):.0f} / {np.percentile(v[lab & same], 90):.0f} (n={int((lab & same).sum())}), '
                     f'diff cat {np.median(v[lab & ~same]):.0f} / {np.percentile(v[lab & ~same], 90):.0f} (n={int((lab & ~same).sum())})  ')
    try:
        from sklearn.metrics import roc_auc_score
        lines.append('AUC same-vs-diff among candidates: recipe sim ' + f'{roc_auc_score(same[lab], S0[P[lab, 0], P[lab, 1]]):.3f}, ' +
                     ', '.join(f'{c} {roc_auc_score(same[lab], Sc[lab, cols.index(c)]):.3f}' for c in cols) + '\n')
    except Exception as e: print(e)
    lines.append('\nPer-coat cross-visit top-1 (query coat = CLIP zero-shot argmax; n queries):\n')
    keys = sorted({c for d in pc.values() for c in d}); best = max(pc, key=lambda k: np.mean([pc[k][c][0] for c in pc[k]]) if k != 'baseline w=0' else -1)
    lines.append(f'| coat | n | baseline | {best} |\n|---|---|---|---|')
    for c in keys:
        b0 = pc['baseline w=0'].get(c, (np.nan, 0)); b1 = pc[best].get(c, (np.nan, 0))
        lines.append(f'| {names[c] if names else c} | {b0[1]} | {b0[0]:.3f} | {b1[0]:.3f} |')
    open(LOGMD, 'w').write('\n'.join(lines) + '\n'); print('\n'.join(lines))

if __name__ == '__main__':
    if sys.argv[1] == 'match': match(int(sys.argv[2]) if len(sys.argv) > 2 else 30)
    else: fuse()
