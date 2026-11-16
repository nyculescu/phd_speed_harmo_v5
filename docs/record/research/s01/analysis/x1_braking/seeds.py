"""(d) A few X1 seeds, v3w (mean of 5 learners) vs nc: the seeds with the smallest, median and largest paired excess of -4.5 events,
with the robust counts, front crossings and queue metrics; then a compact speed map (km/h // 10) of 4,300-5,700 m, 560-1,000 s for the
largest-excess seed (nc | v3w learner w0u250)."""
import pickle
from pathlib import Path

import numpy as np

from common_x import GROUPS, Q, arm_mean, load_T

OUT = Path(__file__).resolve().parent
T = load_T()
F = pickle.load(open(OUT / "fronts_rows.pkl", "rb"))
S = pickle.load(open(OUT / "st_rows.pkl", "rb"))
rows = pickle.load(open(OUT / "test_rows.pkl", "rb"))
cell = "X1"
A, B = arm_mean(T, [f"{cell}|{n}" for n in GROUPS["v3w"]], Q), T[(f"{cell}|nc", Q)]
AF, BF = arm_mean(F, [f"{cell}|{n}" for n in GROUPS["v3w"]], Q), F[(f"{cell}|nc", Q)]
AS, BS = arm_mean(S, [f"{cell}|{n}" for n in GROUPS["v3w"]], Q), S[(f"{cell}|nc", Q)]
ds = sorted(A, key=lambda s: A[s]["ev45_all"] - B[s]["ev45_all"])
pick = [ds[0], ds[len(ds) // 2], ds[-1]]
for s in pick:
    print(f"seed {s}: ev45 v3w {A[s]['ev45_all']:.0f} nc {B[s]['ev45_all']:.0f} | ev4 {A[s]['ev4_all']:.0f} vs {B[s]['ev4_all']:.0f} | ev5_alks {A[s]['ev5_alks']:.0f} vs {B[s]['ev5_alks']:.0f}"
          f" | fc15 {AF[s]['fc15']:.0f} vs {BF[s]['fc15']:.0f} (4a {AF[s]['fc15_m2']:.0f} vs {BF[s]['fc15_m2']:.0f}) | queue_m_win {AS[s]['queue_m_win']:.0f} vs {BS[s]['queue_m_win']:.0f}"
          f" | passed {A[s]['passed']:.0f} vs {B[s]['passed']:.0f}")
s = pick[-1]
ST = Path("/home/catalin/work/phd/v5b1_runs/measure_s01_remote/st")
j0, j1, k0, k1 = 86, 114, 26, 70
for nm in ("nc", "w0u250"):
    f = np.load(ST / rows[(f"{cell}|{nm}", s)]["m_st_file"])
    with np.errstate(invalid="ignore", divide="ignore"):
        V = np.where(f["n"] > 0, 3.6 * f["v"] / np.maximum(f["n"], 1e-9), np.nan)
    print(f"seed {s} {nm}: rows 10 s from {300 + 10 * k0} s, columns 50 m from {50 * j0} m; 4a starts at col {int(4987.3 // 50) - j0}, edge 4 at col {int(5282.0 // 50) - j0}")
    for k in range(k0, k1, 2):
        print(f"  {300 + 10 * k:5d} " + "".join("." if np.isnan(x) else str(min(int(x // 10), 9)) for x in V[k, j0:j1]))
