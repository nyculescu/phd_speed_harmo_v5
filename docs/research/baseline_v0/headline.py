"""V307: paired comparisons on the instrumented rows, higher is better everywhere. usage: headline.py rows.jsonl out_dir [prefix]"""
import csv
import gzip
import json
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

T = Path(sys.argv[2])
PRE = sys.argv[3] if len(sys.argv) > 3 else ""
R = defaultdict(dict)
for line in open(sys.argv[1]):
    r = json.loads(line)
    R[(r["name"], r["q"])][r["seed"]] = {"flow": r["passed"], "speed": r["mean_v"], "vehicles": r["N"], "ttc_merge": r["E30"], "ttc_net": r["E30"] + r["out_E30"], "brake_merge": r["brake3"], "brake_net": r["brake3"] + r["out_b3"], "collisions": r["collisions"]}
for r in csv.DictReader(gzip.open(T / f"{PRE}detail_delay_per_run.csv.gz", "rt")):
    q, s = float(r["q"]), int(r["seed"])
    x = R[(r["name"], q)][s]
    for g, tag in (("all", "all"), ("main", "main"), ("ramp", "ramp")):
        if r["group"] == g:
            x[f"delay_{tag}"], x[f"delay_p95_{tag}"], x[f"time_in_system_{tag}"], x[f"finished_{tag}"], x[f"wait_{tag}"] = float(r["delay_finished_s"]), float(r["delay_p95_s"]), float(r["time_in_system_s"]), float(r["finished_pct"]), float(r["insertion_wait_s"])
R = {k: {s: x for s, x in v.items() if "delay_all" in x} for k, v in R.items()}
R = {k: v for k, v in R.items() if v}
SIGN = {"flow": 1, "speed": 1, "finished_all": 1, "finished_main": 1, "finished_ramp": 1}
METRICS = sorted({k for v in R.values() for s in v.values() for k in s} - {"collisions"})
abs_rows, pair_rows = [], []
for (n, q), A in sorted(R.items(), key=lambda x: (x[0][1], x[0][0])):
    abs_rows.append({"name": n, "q": q, "n": len(A), "collisions_sum": sum(a["collisions"] for a in A.values()), **{m: round(float(np.median([a[m] for a in A.values()])), 2) for m in METRICS}})
    for c in ("a000", "p303", "a333"):
        if n == c:
            continue
        B = R[(c, q)]
        ds = sorted(set(A) & set(B))
        for m in METRICS:
            base = np.median([B[k][m] for k in ds])
            d = np.array([SIGN.get(m, -1) * (A[k][m] - B[k][m]) / base * 100 for k in ds])
            rng = np.random.default_rng(20261103)
            lo, hi = np.percentile(np.median(d[rng.integers(0, len(d), (20000, len(d)))], axis=1), [2.5, 97.5])
            pair_rows.append({"name": n, "q": q, "against": c, "metric": m, "median_pct": round(float(np.median(d)), 2), "lo": round(float(lo), 2), "hi": round(float(hi), 2)})
for f, rows in ((f"{PRE}headline_absolute.csv", abs_rows), (f"{PRE}headline_paired.csv", pair_rows)):
    with open(T / f, "w", newline="") as o:
        w = csv.DictWriter(o, list(rows[0]))
        w.writeheader()
        w.writerows(rows)
