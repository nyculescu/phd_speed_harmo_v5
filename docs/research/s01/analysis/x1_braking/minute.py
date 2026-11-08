"""(d) m_minute holds, per minute after the warm-up (minute m = 300 + 60 m to 360 + 60 m s): merge outflows and inflows, speed sums and
vehicle-seconds on each acceleration section (m1 = 3a, m2 = 4a) and on the road before it (m1_up = edge 2, m2_up = edge 3), ramp queue
and insertion-pending vehicle-seconds. No braking. Here: seed-median of the 4a and edge-3 mean speed per minute (km/h), nc vs v3w (mean
of the learners' speeds) vs 3E-T, and the paired median difference v3w - nc with its 95 % bootstrap CI."""
import pickle
from pathlib import Path

import numpy as np

OUT = Path(__file__).resolve().parent
rows = pickle.load(open(OUT / "test_rows.pkl", "rb"))
V3W = ["w0u250", "w1u500", "w2u250", "w3u500", "w4u500"]
for cell in ("X1", "X2"):
    seeds = sorted({s for (n, s) in rows if n == f"{cell}|nc"})

    def sp(name, s, part):
        mm = rows[(f"{cell}|{name}", s)]["m_minute"]
        n = np.asarray(mm[f"m2_{part}_n"], float)
        return np.where(n > 0, 3.6 * np.asarray(mm[f"m2_{part}_vs"], float) / np.maximum(n, 1), np.nan)
    for part, lab in (("acc", "4a"), ("up", "edge 3")):
        nc = np.array([sp("nc", s, part) for s in seeds])
        w = np.array([np.nanmean([sp(a, s, part) for a in V3W], axis=0) for s in seeds])
        e3 = np.array([sp("3e", s, part) for s in seeds])
        d = w - nc
        rng = np.random.default_rng(20261104)
        idx = rng.integers(0, len(seeds), (20000, len(seeds)))
        print(f"{cell} {lab} speed per minute (km/h): min, t(s), nc, v3w, 3E-T, v3w-nc [95% CI]")
        for m in range(nc.shape[1]):
            b = np.nanmedian(d[idx, m], axis=1)
            print(f"  {m:2d} {300 + 60 * m:5d}-{360 + 60 * m:<5d} {np.nanmedian(nc[:, m]):6.1f} {np.nanmedian(w[:, m]):6.1f} {np.nanmedian(e3[:, m]):6.1f}  "
                  f"{np.nanmedian(d[:, m]):6.1f} [{np.nanpercentile(b, 2.5):6.1f}, {np.nanpercentile(b, 97.5):6.1f}]")
