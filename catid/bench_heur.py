"""Heuristic ablations on one embedding: python bench_heur.py EMB_TAG"""
import sys, os, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bench as B, heuristics as H
tag = sys.argv[1]
E = np.load(f'{B.WORK}/emb/{tag}.npy'); C = np.load(f'{B.WORK}/collar.npy')
out = []
S0 = E @ E.T
B.score(S0, f'{tag} | raw', out)
Ec = H.center(E); B.score(Ec @ Ec.T, f'{tag} | center', out)
for k in (64, 128, 256):
    Ew = H.whiten(E, k=k); B.score(Ew @ Ew.T, f'{tag} | whiten k={k}', out)
Ew = H.whiten(E, k=128)
for a in (0.5, 1.0):
    Et = H.tracklet_pool(Ec, B.tid, alpha=a); B.score(Et @ Et.T, f'{tag} | center+tracklet a={a}', out)
Sc = H.collar_sim(C)
for beta in (0.05, 0.1, 0.2):
    B.score(Ec @ Ec.T + beta * Sc, f'{tag} | center+collar b={beta}', out)
B.score(H.k_reciprocal(Ec @ Ec.T), f'{tag} | center+kreciprocal', out)
