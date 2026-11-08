"""Paired v3w against p333 on the measurement pack's panel metrics (measure2.METRICS without the decision metrics), per setting.
Arm value per seed = mean over the 5 learners of the per-run metric, as report() does. Paired median difference v3w - p333 in the
metric's units, 95 % percentile bootstrap (20,000, default_rng(20261104)); the relative effect only where p333's median is > 0.
usage: python -B panels_ci.py OUTDIR"""
import json
import sys
from pathlib import Path

import numpy as np

D = Path("/home/catalin/work/phd/v5b1_runs/measure_s01_remote")
OUT = Path(sys.argv[1])
W = ["w0u250", "w1u500", "w2u250", "w3u500", "w4u500"]
CL = ("car", "alks", "truck")
# copied from docs/research/round2/measure2.py METRICS (decision metrics left out); +1 = higher is better
M = [("car speed, median", 1, lambda m: m["v_q_car"][2]), ("ALKS speed, median", 1, lambda m: m["v_q_alks"][2]),
     ("car |accel| RMS", -1, lambda m: m["a_rms_car"]), ("car decel, 5th pct", 1, lambda m: m["a_q_car"][0]),
     ("braking events, all classes", -1, None), ("events peaking at -4.5 or harder", -1, None),
     ("cascade share (cars)", -1, lambda m: m["cascade_share_car"]), ("petrol fuel, cars + ALKS", -1, lambda m: m["fuel_petrol_g_km"]),
     ("merge 1 slow minutes", -1, lambda m: m["m1"]["slow_minutes"]), ("merge 2 slow minutes", -1, lambda m: m["m2"]["slow_minutes"]),
     ("ramp 1 queue, mean", -1, lambda m: m["ramp1_queue_mean"] + m["ramp1_pending_mean"]),
     ("ramp 2 queue, mean", -1, lambda m: m["ramp2_queue_mean"] + m["ramp2_pending_mean"]),
     ("jam share (< 30 km/h)", -1, lambda m: m["waves"]["jam_share"]), ("jam clusters", -1, lambda m: m["waves"]["jams"]),
     ("speed oscillation", -1, lambda m: m["waves"]["osc_kmh"]), ("congested length, max", -1, lambda m: m["waves"]["congested_km_max"])]
SET = [("3500", "s1", "B", 3500), ("4500", "band", "B", 4500), ("5000", "band", "B", 5000), ("5250", "band", "B", 5250), ("X1@5300", "test", "X1", 5300),
       ("X2@5300", "test", "X2", 5300), ("5500", "band", "B", 5500), ("6000", "band", "B", 6000), ("7000", "s1", "B", 7000)]
S = {k: json.load(open(D / f"summary_rows_{k}.json")) for k in ("s1", "band", "test")}
classes = None


def fval(title, f, m):
    global classes
    if classes is None:
        classes = [c for c in CL if f"events_{c}" in m]
    if title == "braking events, all classes":
        return sum(m[f"events_{c}"] for c in classes)
    if title == "events peaking at -4.5 or harder":
        return sum(m[f"events_ge45_{c}"] for c in classes)
    return f(m)


def ci(d):
    b = np.median(d[np.random.default_rng(20261104).integers(0, len(d), (20000, len(d)))], axis=1)
    return [float(np.median(d)), float(np.percentile(b, 2.5)), float(np.percentile(b, 97.5))]


out, n = {}, 0
for lab, ph, cell, q in SET:
    X = S[ph]
    P = [X[f"{cell}|{w}|{q}"] for w in W]
    O = X[f"{cell}|p333|{q}"]
    seeds = sorted(set(O).intersection(*[set(p) for p in P]))
    out[lab] = {"seeds": len(seeds)}
    for title, hi, f in M:
        pv = np.array([np.mean([fval(title, f, p[s]) for p in P]) for s in seeds])
        ov = np.array([fval(title, f, O[s]) for s in seeds])
        a = ci(pv - ov)
        better = hi * a[1] > 0 if hi > 0 else a[2] < 0
        worse = a[2] < 0 if hi > 0 else a[1] > 0
        mo = float(np.median(ov))
        rel = [hi * x / mo * 100 for x in a] if mo > 0 else None
        if rel is not None and hi < 0:
            rel = [rel[0], rel[2], rel[1]]
        out[lab][title] = {"v3w_med": float(np.median(pv)), "p333_med": mo, "diff_v3w_minus_p333": a, "rel_pct_pos_v3w_better": rel,
                           "v3w_better_ci": bool(better), "p333_better_ci": bool(worse)}
        n += 1
summ = {lab: {"v3w_better_ci": [t for t, _, _ in M if out[lab][t]["v3w_better_ci"]], "p333_better_ci": [t for t, _, _ in M if out[lab][t]["p333_better_ci"]]}
        for lab in out}
print("comparisons:", n)
for lab, s in summ.items():
    print(lab, "v3w better (CI):", len(s["v3w_better_ci"]), s["v3w_better_ci"])
    print(lab, "p333 better (CI):", len(s["p333_better_ci"]), s["p333_better_ci"])
for lab in ("3500", "4500", "5000"):
    for t in ("car speed, median", "ALKS speed, median", "jam clusters", "merge 1 slow minutes", "congested length, max"):
        r = out[lab][t]
        print(lab, t, "v3w", round(r["v3w_med"], 3), "p333", round(r["p333_med"], 3), "diff", [round(x, 3) for x in r["diff_v3w_minus_p333"]])
json.dump({"n_comparisons": n, "summary": summ, "detail": out}, open(OUT / "panels_ci.json", "w"), indent=1)
