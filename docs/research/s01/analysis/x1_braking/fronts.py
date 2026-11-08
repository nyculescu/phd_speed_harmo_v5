"""(d) Speed fronts from the space-time fields: per 10-s bin and 50-m cell boundary j -> j+1, the kinematic deceleration a cell-mean
vehicle needs to go from V_j to V_j+1 within 50 m, a_req = (V_j^2 - V_j+1^2) / (2 * 50 m), and the vehicles crossing cell j in that bin
(flux = v_j / 50 m). fc<k> = vehicles crossing a boundary with a_req >= k m/s2 (an index: cell means blur the real fronts, so
real individual decelerations are larger). Split by zone (up: x < 4,987 m; m2: 4a, 4,987-5,282; e4: edge 4; down: edge 5) and by
period (before 300-600 s; win = slowdown on; after = 120 s after each window; rest). appr_kmh = flux-weighted V_j at fc15 crossings.
Writes fronts_rows.pkl ((name, q) -> seed -> metrics) and prints paired comparisons and seed-level associations with the -4.5 counts."""
import pickle
from collections import defaultdict
from pathlib import Path

import numpy as np
from scipy import stats as sst

OUT = Path(__file__).resolve().parent
ST = Path("/home/catalin/work/phd/v5b1_runs/measure_s01_remote/st")
rows = pickle.load(open(OUT / "test_rows.pkl", "rb"))
DX, DT, T0 = 50.0, 10.0, 300.0
WINS = {"X1": [(600, 720), (1200, 1320)], "X2": [(700, 880)]}
ZB = [("up", 0.0, 4987.32), ("m2", 4987.32, 5282.04), ("e4", 5282.04, 6278.04), ("down", 6278.04, 1e9)]


def period_mask(cell, nt):
    t = T0 + DT * (np.arange(nt) + 0.5)
    per = np.full(nt, "rest", dtype=object)
    per[t < 600] = "before"
    for a, b in WINS[cell]:
        per[(t >= a) & (t < b)] = "win"
        per[(t >= b) & (t < b + 120)] = "after"
    return per


def metrics(v, n, cell):
    with np.errstate(invalid="ignore", divide="ignore"):
        V = np.where(n > 0, v / np.maximum(n, 1e-9), np.nan)
    Vj, Vk = V[:, :-1], V[:, 1:]
    flux = v[:, :-1] / DX
    with np.errstate(invalid="ignore"):
        areq = np.where(np.isfinite(Vj) & np.isfinite(Vk) & (Vj > Vk), (Vj ** 2 - Vk ** 2) / (2 * DX), 0.0)
    xb = DX * (np.arange(Vj.shape[1]) + 1)     # boundary position
    per = period_mask(cell, V.shape[0])
    out = {}
    for k in (1.5, 2.5):
        hit = areq >= k
        out[f"fc{int(k * 10)}"] = float((flux * hit).sum())
        for zn, a, b in ZB:
            zm = (xb >= a) & (xb < b)
            out[f"fc{int(k * 10)}_{zn}"] = float((flux[:, zm] * hit[:, zm]).sum())
        for pn in ("before", "win", "after", "rest"):
            pm = per == pn
            out[f"fc{int(k * 10)}_p_{pn}"] = float((flux[pm] * hit[pm]).sum())
    hit = areq >= 1.5
    w = (flux * hit).sum()
    out["appr_kmh"] = float(3.6 * (flux * hit * np.nan_to_num(Vj)).sum() / w) if w else 0.0
    return out


R = defaultdict(dict)
for (name, seed), r in rows.items():
    f = np.load(ST / r["m_st_file"])
    R[(name, r["q"])][seed] = {"seed": seed, **metrics(f["v"].astype(float), f["n"].astype(float), name.split("|")[0])}
R = dict(R)
pickle.dump(R, open(OUT / "fronts_rows.pkl", "wb"))

from common_x import GROUPS, POLICIES, Q, arm_mean, diff_ci, effect95, load_T, med  # noqa: E402
T = load_T()
lines = ["cell\tP\tO\tmetric\tmedP\tmedO\teffect_pct\tlo\thi\tdiff\tdlo\tdhi"]
ms = ["fc15", "fc25", "fc15_up", "fc15_m2", "fc15_e4", "fc15_down", "fc15_p_before", "fc15_p_win", "fc15_p_after", "fc15_p_rest",
      "fc25_up", "fc25_m2", "fc25_e4", "fc25_p_before", "fc25_p_win", "fc25_p_after", "fc25_p_rest", "appr_kmh"]
ncomp = 0
for cell in ("X1", "X2"):
    for p, o in [(p, o) for p in POLICIES for o in ("nc", "3e")] + [("3e", "nc"), ("p333", "nc"), ("os1_15_10", "nc"), ("3ex1" if cell == "X1" else "3ex2", "nc")]:
        A = arm_mean(R, [f"{cell}|{x}" for x in GROUPS.get(p, [p])], Q)
        B = arm_mean(R, [f"{cell}|{x}" for x in GROUPS.get(o, [o])], Q)
        for m in ms:
            mo = med(B, m)
            e = effect95(A, B, m, sign=1 if m == "appr_kmh" else -1) if abs(mo) > 1e-9 else (float("nan"),) * 3
            d = diff_ci(A, B, m)
            ncomp += 1
            lines.append("\t".join([cell, p, o, m, f"{med(A, m):.5g}", f"{mo:.5g}", *[f"{x:.2f}" for x in e], *[f"{x:.5g}" for x in d]]))
(OUT / "fronts_stats.tsv").write_text("\n".join(lines) + "\n")
print("comparisons:", ncomp)
for ln in lines[1:]:
    f = ln.split("\t")
    if (f[1], f[2]) in (("v3w", "nc"), ("v3w", "3e"), ("3e", "nc"), ("p333", "nc")):
        print(f"{f[0]} {f[1]:4s} vs {f[2]:3s} {f[3]:14s} medP {float(f[4]):8.4g} medO {float(f[5]):8.4g} eff {f[6]:>7}% [{f[7]:>7},{f[8]:>7}] diff {float(f[9]):8.4g} [{float(f[10]):8.4g},{float(f[11]):8.4g}]")
# association: arm-level (median over seeds) across all arms of both cells, and seed-level v3w - nc
arms = ["nc", "3e", "p333", "os1_15_10", "os0_10_10", "os1_10_0", "copy", "a4400_10_1", "r4a1", "z33133", "lr1000_10_1", "lr1000_16_2", "lr400_13_2", "lr400_16_1", *POLICIES]
for cell in ("X1", "X2"):
    xs, ys, ys5 = [], [], []
    for a in arms + (["3ex1"] if cell == "X1" else ["3ex2"]):
        A = arm_mean(R, [f"{cell}|{x}" for x in GROUPS.get(a, [a])], Q)
        B = arm_mean(T, [f"{cell}|{x}" for x in GROUPS.get(a, [a])], Q)
        xs.append(med(A, "fc15"))
        ys.append(med(B, "ev45_all"))
        ys5.append(med(B, "ev4_all"))
    print(cell, f"across {len(xs)} arms: Spearman(median fc15, median ev45_all) = {sst.spearmanr(xs, ys)[0]:.2f}; with ev4_all = {sst.spearmanr(xs, ys5)[0]:.2f}")
    for p in ("v3w", "3e", "p333"):
        A = arm_mean(R, [f"{cell}|{x}" for x in GROUPS.get(p, [p])], Q)
        B = R and arm_mean(R, [f"{cell}|nc"], Q)
        At = arm_mean(T, [f"{cell}|{x}" for x in GROUPS.get(p, [p])], Q)
        Bt = arm_mean(T, [f"{cell}|nc"], Q)
        ds = sorted(set(A) & set(B))
        for fk in ("fc15", "fc25"):
            x = [A[s][fk] - B[s][fk] for s in ds]
            for k in ("ev45_all", "ev45_car", "ev45_alks", "ev4_all"):
                y = [At[s][k] - Bt[s][k] for s in ds]
                rho, pv = sst.spearmanr(x, y)
                print(f"  {cell} {p}-nc seed-level Spearman(d {fk}, d {k}) = {rho:.2f} (p {pv:.3f})")
