"""(d) Where and when, from the space-time speed fields (st/*.npz: v = speed sum in m/s over 1-Hz vehicle samples, n = vehicle-seconds,
10 s x 50 m cells from t = 300 s, x from the start of edge 1; edge 4 = 5,282-6,278 m, 4a = 4,987-5,282 m). Per run, per slowdown
window (cell X1: limit lowered 600-720 s and 1,200-1,320 s; X2: 700-880 s on edge 3, 3,793-4,987 m):
- fast_entries: vehicles entering the slowed edge from a 50-m approach cell whose mean speed is >= 60 km/h (flux = v / dx per bin);
- entries: all vehicles entering the slowed edge (same flux, no speed condition);
- appr_kmh: vehicle-weighted speed of the 250 m upstream of the slowed edge; in_kmh: of its first 100 m;
- queue_m: per bin, the length of the contiguous run of cells below 30 km/h that ends at the slowed edge's start, averaged over the window;
- macro_dec: vehicle-seconds in cells whose convective deceleration v * dv/dx (to the next cell downstream) is <= -1 m/s2, by zone.
Writes st_rows.pkl: (name, q) -> seed -> metrics, for every test run."""
import pickle
from collections import defaultdict
from pathlib import Path

import numpy as np

OUT = Path(__file__).resolve().parent
ST = Path("/home/catalin/work/phd/v5b1_runs/measure_s01_remote/st")
rows = pickle.load(open(OUT / "test_rows.pkl", "rb"))
DX, DT, T0 = 50.0, 10.0, 300.0
SPEC = {"X1": {"x0": 5282.04, "x1": 6278.04, "wins": [(600, 720), (1200, 1320)]}, "X2": {"x0": 3793.02, "x1": 4987.32, "wins": [(700, 880)]}}


def bins(t0, t1):
    return list(range(int((t0 - T0) // DT), int((t1 - T0) // DT)))


def metrics(v, n, cell):
    s = SPEC[cell]
    with np.errstate(invalid="ignore", divide="ignore"):
        V = np.where(n > 0, v / np.maximum(n, 1e-9), np.nan)     # m/s
    j0 = int(s["x0"] // DX)     # cell holding the slowed edge's start
    ja = j0 - 1     # approach cell, fully upstream
    out = {}
    tw = [k for a, b in s["wins"] for k in bins(a, b)]
    after = [k for a, b in s["wins"] for k in bins(b, b + 120)]
    for lab, ks in (("win", tw), ("after", after)):
        flux = v[ks, ja] / DX     # vehicles crossing the approach cell per bin
        fast = V[ks, ja] * 3.6 >= 60.0
        out[f"entries_{lab}"] = float(np.nansum(flux))
        out[f"fast_entries_{lab}"] = float(np.nansum(flux[fast]))
        up = slice(j0 - 5, j0)
        out[f"appr_kmh_{lab}"] = float(3.6 * v[ks, up].sum() / max(n[ks, up].sum(), 1e-9))
        inn = slice(j0 + 1, j0 + 3)
        out[f"in_kmh_{lab}"] = float(3.6 * v[ks, inn].sum() / max(n[ks, inn].sum(), 1e-9))
        q = []
        for k in ks:
            L, j = 0, j0
            while j >= 0 and np.isfinite(V[k, j]) and V[k, j] * 3.6 < 30.0:
                L += 1
                j -= 1
            q.append(L * DX)
        out[f"queue_m_{lab}"] = float(np.mean(q))
    # convective deceleration proxy over the whole run, by zone and period
    with np.errstate(invalid="ignore"):
        a = V[:, :-1] * (V[:, 1:] - V[:, :-1]) / DX
    hard = np.nan_to_num(a, nan=0.0) <= -1.0
    w = n[:, :-1]
    zones = {"up": slice(0, int(s["x0"] // DX) - 6), "appr": slice(int(s["x0"] // DX) - 6, int(s["x0"] // DX) + 1),
             "zone": slice(int(s["x0"] // DX) + 1, int(s["x1"] // DX)), "down": slice(int(s["x1"] // DX), a.shape[1])}
    per = np.zeros(V.shape[0], bool)
    per[tw] = True
    pa = np.zeros(V.shape[0], bool)
    pa[after] = True
    for zn, zs in zones.items():
        for pn, pm in (("win", per), ("after", pa), ("other", ~(per | pa))):
            out[f"macro_dec_{zn}_{pn}"] = float((w[pm, zs] * hard[pm, zs]).sum())
    return out


R = defaultdict(dict)
for (name, seed), r in rows.items():
    f = np.load(ST / r["m_st_file"])
    m = metrics(f["v"].astype(float), f["n"].astype(float), name.split("|")[0])
    R[(name, r["q"])][seed] = {"seed": seed, **m}
pickle.dump(dict(R), open(OUT / "st_rows.pkl", "wb"))
print("runs", sum(len(x) for x in R.values()))
