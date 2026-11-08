"""When a mainline vehicle departing at time t is on edge 3 and edge 4: a trajectory integrated through each run's space-time speed
field (10 s x 50 m, all lanes pooled; empty cells and times before the 300-s warm-up at the 100 km/h limit). A labelling aid for
cohort.py's departure bins, not a measurement: insertion delay and lane differences are ignored."""
import json
import sys
from pathlib import Path

import numpy as np

from common_dec import GROUPS, HERE

DATA = Path("/home/catalin/work/phd/v5b1_runs/measure_s01_remote/st")
WARM, DT, DX, FREE = 300.0, 10.0, 50.0, 100.0 / 3.6
EDGES = {"3": (3793.02, 4987.32), "4": (5282.04, 6278.04)}
SEEDS = list(range(7_440_840, 7_440_880))


def trajectory(V: np.ndarray, t0: float) -> dict:
    t, x, out = t0, 0.0, {}
    while x < 6778.0 and t < 2400.0:
        k, j = int((t - WARM) // DT), min(int(x // DX), V.shape[1] - 1)
        v = V[k, j] if 0 <= k < V.shape[0] and not np.isnan(V[k, j]) else FREE
        v = max(v, 0.5)
        for e, (a, b) in EDGES.items():
            if x < a <= x + v * 1.0:
                out[f"in{e}"] = t
            if x < b <= x + v * 1.0:
                out[f"out{e}"] = t
        x += v * 1.0
        t += 1.0
    return out


def main() -> int:
    res = {}
    for cell in ("X1", "X2"):
        for arm, names in (("v3w", GROUPS["v3w"]), ("os1_15_10", ["os1_15_10"])):
            per = {}
            for s in SEEDS:
                for n in names:
                    z = np.load(DATA / f"{cell}__{n}__5300__{s}.npz")
                    v, c = z["v"].astype(float), z["n"].astype(float)
                    V = np.where(c > 0, v / np.maximum(c, 1.0), np.nan)
                    for t0 in np.arange(30.0, 1800.0, 60.0):
                        tr = trajectory(V, t0)
                        for key, val in tr.items():
                            per.setdefault(f"{int(t0 - 30)}-{int(t0 + 30)}", {}).setdefault(key, []).append(val)
            res[f"{cell}|{arm}"] = {b: {k: float(np.median(x)) for k, x in d.items()} for b, d in per.items()}
    (HERE / "traj.json").write_text(json.dumps(res, indent=1))
    for key, d in res.items():
        print("==", key, "departure bin: median time on edge 3 [in-out], edge 4 [in-out]")
        for b, r in d.items():
            print(f"  {b:>10}  e3 {r.get('in3', float('nan')):6.0f}-{r.get('out3', float('nan')):6.0f}   e4 {r.get('in4', float('nan')):6.0f}-{r.get('out4', float('nan')):6.0f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
