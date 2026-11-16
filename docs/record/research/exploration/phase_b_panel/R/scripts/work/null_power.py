# EXPLORATORY: operating characteristics of screen R's stage-1 KILL rule in X1, from the 120 stored seeds (r1, r2v, r2t).
# Rows were already read for verdicts. Read-only. Single process.
import json, numpy as np
from collections import defaultdict
RUNS = "/home/catalin/work/phd/v5b1_runs/"
R1 = ["w0u250","w1u250","w2u500","w3u500","w4u500"]; R2 = ["w0u250","w1u500","w2u250","w3u500","w4u500"]
DS = {"r1test": (RUNS+"round1_remote/out/test/test.jsonl", ["w0","w1","w2","w3","w4"]),
      "r2val": (RUNS+"round2/val/rows_6c49e7e.jsonl", R1),
      "r2test": (RUNS+"round2/test/rows_6c49e7e.jsonl", R2)}
Q = 5300.0; C = "X1"; RULES = ["p333", "lr1000_10_1", "os0_10_10"]
D = {}  # name -> {seed: all_delay}; learners keyed L0..L4
for s, (f, names) in DS.items():
    want = {f"{C}|{r}": r for r in RULES} | {f"{C}|{n}": f"L{i}" for i, n in enumerate(names)}
    with open(f) as h:
        for line in h:
            if '"X1|' not in line: continue
            r = json.loads(line)
            if r["q"] == Q and r["name"] in want:
                D.setdefault(want[r["name"]], {})[r["seed"]] = float(r["all_delay"])
seeds = sorted(set.intersection(*(set(v) for v in D.values())))
N = len(seeds)
L = np.array([[D[f"L{i}"][s] for s in seeds] for i in range(5)])          # learners x seeds
O = np.array([[D[r][s] for s in seeds] for r in RULES])                   # rules x seeds
ref = np.median(O, axis=1)                                                # fixed denominators (pooled medians)
arm = L.mean(axis=0)
print("seeds", N, "rule medians", dict(zip(RULES, ref.round(0))))
print("stored arm effect %:", {r: round(float(np.median((O[k]-arm)/ref[k]*100)), 2) for k, r in enumerate(RULES)})
print("stored per-learner effect % vs p333:", [round(float(np.median((O[0]-L[i])/ref[0]*100)), 2) for i in range(5)])
rng = np.random.default_rng(20261110)
def study(n, shift_pct, B=1000, pct=1.25, thr=3.0, need=4):
    """One resampled study. shift_pct: target true arm edge against p333 (stored median moved to it); None = stored."""
    idx = rng.integers(0, N, n)
    add = 0.0 if shift_pct is None else (np.median((O[0]-arm)/ref[0]*100) - shift_pct) / 100 * ref[0]   # veh-s added to every learner
    a = arm[idx] + add; l = L[:, idx] + add; o = O[:, idx]
    bi = rng.integers(0, n, (B, n))
    kill_edge = False; hw = []
    pts = []
    for k in range(len(RULES)):
        d = (o[k] - a) / np.median(o[k]) * 100
        p = np.median(d); bs = np.median(d[bi], axis=1); lo, hi = np.percentile(bs, [pct, 100 - pct])
        pts.append(p); hw.append((p - lo, hi - p))
        if p < thr or lo <= 0: kill_edge = True
    pos = [all(np.median(o[k] - l[i]) > 0 for k in range(len(RULES))) for i in range(5)]
    kill_learn = sum(pos) < need
    return kill_edge, kill_learn, pts, hw
def run(n, shift, R=1500):
    ke = kl = ka = 0; hws = []
    for _ in range(R):
        e, l, pts, hw = study(n, shift)
        ke += e; kl += l; ka += (e or l); hws.append(hw[0])
    hws = np.array(hws)
    return ke / R, kl / R, ka / R, hws[:, 0].mean(), hws[:, 1].mean()
print("n | true arm edge vs p333 | P(KILL by edge rule) | P(KILL by learner rule) | P(KILL any) | mean CI half-widths vs p333 (lower, upper)")
for n in (60, 80, 120):
    for sh in (0.0, 1.0, 2.0, 3.0, None, 5.0, 6.0):
        r = run(n, sh)
        print(f"{n} | {'stored (+4.2)' if sh is None else sh} | {r[0]:.3f} | {r[1]:.3f} | {r[2]:.3f} | {r[3]:.2f}, {r[4]:.2f}", flush=True)
