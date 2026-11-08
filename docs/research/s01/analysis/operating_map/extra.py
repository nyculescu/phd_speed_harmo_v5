"""1 No-effect null of round 2's CI statistic: how often a 95 % percentile-bootstrap CI of the paired median excludes 0 when the
paired differences are sign-flipped (median 0 by symmetry), using each comparison's own magnitudes (v3w against p333, 3E-T,
os1_15_10, nc; six main metrics; nine settings). 2 Which arm has the best median in each ASCII report panel (where a
"p333 wins" reading could come from). usage: python -B extra.py OUTDIR"""
import json
import re
import sys
from pathlib import Path

sys.dont_write_bytecode = True
WT = Path("/home/catalin/work/phd/wt/r2-metrics")
sys.path[:0] = [str(WT / "docs/research/conf3"), str(WT / "docs/research/round1")]
import numpy as np  # noqa: E402
from common import val, load  # noqa: E402
from common1 import arm_mean  # noqa: E402

D = Path("/home/catalin/work/phd/v5b1_runs/measure_s01_remote")
OUT = Path(sys.argv[1])
W = ["w0u250", "w1u500", "w2u250", "w3u500", "w4u500"]
TB, TT, TS1 = load(D / "rows_band.jsonl"), load(D / "rows_test.jsonl"), load(D / "rows_s1.jsonl")
SET = [("3500", TS1, "B", 3500.0), ("4500", TB, "B", 4500.0), ("5000", TB, "B", 5000.0), ("5250", TB, "B", 5250.0), ("X1@5300", TT, "X1", 5300.0),
       ("X2@5300", TT, "X2", 5300.0), ("5500", TB, "B", 5500.0), ("6000", TB, "B", 6000.0), ("7000", TS1, "B", 7000.0)]
KEYS = ("all_delay", "ttc_net", "passed", "b3_step", "b45_step", "finished_pct")
R, B = 300, 4000
rng = np.random.default_rng(7)
rates, rows = {20: [], 40: []}, []
for lab, T, cell, q in SET:
    P = arm_mean(T, [f"{cell}|{n}" for n in W], q)
    for o in ("p333", "3e", "os1_15_10", "nc"):
        O = T[(f"{cell}|{o}", q)]
        ds = sorted(set(P) & set(O))
        for k in KEYS:
            a = np.abs(np.array([val(P[s], k) - val(O[s], k) for s in ds]))
            n = len(a)
            if not a.any():
                continue
            exc = 0
            for _ in range(R):
                d = a * rng.choice((-1.0, 1.0), n)
                m = np.median(d[rng.integers(0, n, (B, n))], axis=1)
                lo, hi = np.percentile(m, (2.5, 97.5))
                exc += lo > 0 or hi < 0
            rates[n].append(exc / R)
            rows.append([lab, o, k, n, exc / R])
null = {f"n={n}": {"comparisons": len(v), "mean_false_exclusion": round(float(np.mean(v)), 4), "min": round(float(np.min(v)), 4),
                   "max": round(float(np.max(v)), 4)} for n, v in rates.items() if v}
null["replicates_per_comparison"], null["bootstrap_resamples"] = R, B
print("1 null:", json.dumps(null))

# 2 best median per ASCII panel
BETTER_HIGH = ("car speed, median", "ALKS speed, median", "car decel, 5th pct")
SKIP = ("decisions applied", "excess level changes", "reversals per change", "ALKS at the longest level", "policy confidence")
win = {}
for f in ("report_rows_s1.txt", "report_rows_band.txt", "report_rows_test.txt"):
    for block in (D / f).read_text().split("\n\n"):
        lines = block.strip().splitlines()
        m = re.match(r"(\S+) at ([\d,]+) veh/h: (.+), axis", lines[0])
        cell, q, metric = m.group(1), m.group(2), m.group(3)
        if metric.startswith(SKIP):
            continue
        meds = {}
        for ln in lines[1:]:
            mm = re.match(r"  (.+?)\s{2,}.*med (\S+)\s+IQR", ln)
            meds[mm.group(1).strip()] = float(mm.group(2))
        hi = metric.startswith(BETTER_HIGH)
        best = (max if hi else min)(meds.values())
        winners = [a for a, v in meds.items() if v == best]
        key = f"{cell}@{q}"
        w = win.setdefault(key, {"panels": 0, "p333_best_or_tied": 0, "v3w_best_or_tied": 0, "nc_best_or_tied": 0, "p333_better_than_v3w": 0,
                                 "v3w_better_than_p333": 0, "equal": 0, "p333_best_panels": []})
        w["panels"] += 1
        w["p333_best_or_tied"] += "p333" in winners
        w["v3w_best_or_tied"] += "v3w" in winners
        w["nc_best_or_tied"] += "no control" in winners
        if "p333" in winners:
            w["p333_best_panels"].append(metric)
        pv, vv = meds.get("p333"), meds.get("v3w")
        if pv is not None and vv is not None:
            if pv == vv:
                w["equal"] += 1
            elif (pv > vv) == hi:
                w["p333_better_than_v3w"] += 1
            else:
                w["v3w_better_than_p333"] += 1
print("2 panels:")
for k, v in win.items():
    print(" ", k, {x: y for x, y in v.items()})
json.dump({"null": null, "null_rows": rows, "panels": win}, open(OUT / "extra.json", "w"), indent=1)
