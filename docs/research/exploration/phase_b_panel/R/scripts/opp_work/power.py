"""EXPLORATORY planning null and power for screen R (draft_opponent). Stored X1 rows only, already read for verdicts."""
import sys, re
import numpy as np
sys.path.insert(0, "/srv/shared/Workspace/phd/phd_speed_harmo_v5b1/docs/research/exploration/phase_b_round1/scripts/x1x2")
from lib import RUNS, load, val

Q = 5300.0
R1 = ["w0u250", "w1u250", "w2u500", "w3u500", "w4u500"]
R2 = ["w0u250", "w1u500", "w2u250", "w3u500", "w4u500"]
DS = {"r1test": (RUNS + "round1_remote/out/test/test.jsonl", ["w0", "w1", "w2", "w3", "w4"]),
      "r2val": (RUNS + "round2/val/rows_6c49e7e.jsonl", R1),
      "r2test": (RUNS + "round2/test/rows_6c49e7e.jsonl", R2)}
T = {k: load(f) for k, (f, _) in DS.items()}
pol = re.compile(r"^[a-z]\d(u\d+)?$")
CELL = sys.argv[1] if len(sys.argv) > 1 else "X1"
KEY = "all_delay"

def rules_in(s):
    return {n.split("|")[1] for (n, q) in T[s] if n.startswith(CELL + "|") and q == Q}

common = set.intersection(*(rules_in(s) for s in DS))
opps = sorted(r for r in common if not pol.match(r) and r not in ("nc", "none", "no_control"))
print("cell", CELL, "rules in all three sets:", opps)

P, O, seeds = [], {r: [] for r in opps}, []
L = [[] for _ in range(5)]
for s, (_, names) in DS.items():
    ss = sorted(T[s][(f"{CELL}|p333", Q)])
    for sd in ss:
        lv = [val(T[s][(f"{CELL}|{n}", Q)][sd], KEY) for n in names]
        for i in range(5):
            L[i].append(lv[i])
        P.append(sum(lv) / 5.0)
        for r in opps:
            O[r].append(val(T[s][(f"{CELL}|{r}", Q)][sd], KEY))
        seeds.append(sd)
P = np.array(P); L = np.array(L); Om = np.array([O[r] for r in opps])
N = len(P)
print("pooled seeds", N)
pop = {r: float(np.median(Om[j] - P) / np.median(Om[j]) * 100) for j, r in enumerate(opps)}
print("population effects %:", {r: round(v, 2) for r, v in sorted(pop.items(), key=lambda x: x[1])})
close = min(pop, key=pop.get)
jc = opps.index(close)
print("closest stored rule:", close, round(pop[close], 2))
sd_pct = float(np.std((Om[jc] - P) / np.median(Om[jc]) * 100, ddof=1))
print("paired SD % against closest:", round(sd_pct, 2))

rng = np.random.default_rng(20261110)
EFF = [0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0]
STUD, B = 400, 2000
for n in (80, 120, 160, 200):
    out = {e: {"all": 0, "close": 0, "close_lb": 0, "all_l4": 0} for e in EFF}
    for _ in range(STUD):
        ix = rng.integers(0, N, n)
        p, o, l = P[ix], Om[:, ix], L[:, ix]
        ref = np.median(o, axis=1)
        d = (o - p) / ref[:, None] * 100
        bi = rng.integers(0, n, (B, n))
        bm = np.median(d[:, bi], axis=2)
        pt = np.median(d, axis=1)
        lb = np.percentile(bm, 1.25, axis=1)
        lpt = np.median((o[None, :, :] - l[:, None, :]), axis=2) / ref[None, :] * 100
        for e in EFF:
            c = (pop[close] - e) / 100.0 * np.median(Om[jc])
            sh = c / ref * 100
            ok = (pt - sh >= 3.0) & (lb - sh > 0.0)
            lpos = ((lpt - sh[None, :]) > 0).all(axis=1).sum()
            out[e]["all"] += ok.all()
            out[e]["close"] += ok[jc]
            out[e]["close_lb"] += (lb[jc] - sh[jc] > 0.0)
            out[e]["all_l4"] += ok.all() and lpos >= 4
    print(f"n={n}: true effect vs closest -> survive %: [every stored rule + 4of5 learners | every stored rule | closest only | closest, LB>0 only]")
    for e in EFF:
        r = out[e]
        print(f"  e={e:.0f} %: {100*r['all_l4']/STUD:.1f} | {100*r['all']/STUD:.1f} | {100*r['close']/STUD:.1f} | {100*r['close_lb']/STUD:.1f}")
