"""Aggregate checks of metric semantics on the round 1 rows; prints aggregates only."""
import json
from collections import Counter, defaultdict

import numpy as np

OUT = "/home/catalin/work/phd/v5b1_runs/round1_remote/out"
FILES = {"val": f"{OUT}/val/validation.jsonl", "test": f"{OUT}/test/test.jsonl", "band": f"{OUT}/test/band.jsonl"}
ROAD = ("r_3", "r_4a", "r_ramp2", "r_rest")
SPD = ("s_lo", "s_mid", "s_hi")
PER = ("p_before", "p_taper", "p_hold", "p_after", "p_rest")


def v(r, k):
    x = r.get(k)
    return 0.0 if x is None else float(x)


rows = {k: [json.loads(x) for x in open(f)] for k, f in FILES.items()}
for k, R in rows.items():
    c = Counter()
    for r in R:
        c["n"] += 1
        c["ttc3!=ttc_net"] += abs(v(r, "ttc3") - v(r, "ttc_net")) > 1e-9
        for m in ("ttc3", "sev3"):
            for grp, lab in ((ROAD, "road"), (SPD, "speed"), (PER, "period")):
                c[f"{m}_{lab}_sum_mismatch"] += abs(sum(v(r, f"{m}_{g}") for g in grp) - v(r, m)) > 1e-9
        c[f"steps={r['steps']}"] += 1
        c["sev3_gt_ttc3"] += v(r, "sev3") > v(r, "ttc3")
        c["brake_net==brake3+out_b3"] += abs(v(r, "brake_net") - v(r, "brake3") - v(r, "out_b3")) < 1e-9
    print(k, dict(c))

# Period windows: slowdown on/off times logged by the perturbation, per cell
T = rows["test"]
logs = defaultdict(Counter)
for r in T:
    cell = r["name"].split("|")[0]
    logs[cell][json.dumps(r.get("pert_log"))] += 1
for cell, c in logs.items():
    print("pert_log", cell, "distinct logs:", len(c), "most common:", c.most_common(1)[0][0][:200], c.most_common(1)[0][1])
for cell in ("X1", "X2"):
    e = Counter(json.dumps(r["cfg"]["ctrl"]["env"].get("perturb")) for r in T if r["name"].startswith(cell))
    print("perturb spec", cell, dict(e))

# Flow: passed per 1,500 s against demand
for cell in ("X1", "X2"):
    nc = [r for r in T if r["name"] == f"{cell}|nc"]
    p = np.median([v(r, "passed") for r in nc])
    print("flow", cell, "nc passed median", p, "-> veh/h", round(p / 1500 * 3600), "finished_pct median", round(float(np.median([v(r, "finished_pct") for r in nc])), 1))

# Band: what the random slowdowns drew
B = rows["band"]
seeds = sorted({r["seed"] for r in B})
draws = Counter()
for s in seeds:
    rg = np.random.default_rng(s + 910_000)
    if rg.random() >= 1.0 / 3.0:
        e = str(rg.choice(("3", "4", "5")))
        lim, dur, t0 = float(rg.uniform(25, 60)), float(rg.uniform(60, 180)), float(rg.uniform(400, 1200))
        draws[e] += 1
    else:
        draws["none"] += 1
print("band seeds", len(seeds), "draws", dict(draws))
logs_b = Counter()
nolog = defaultdict(set)
for r in B:
    nolog[r["seed"]].add(bool(r.get("pert_log")))
print("band seeds with a slowdown in pert_log:", sum(1 for s in nolog if True in nolog[s]), "without:", sum(1 for s in nolog if nolog[s] == {False}),
      "mixed:", sum(1 for s in nolog if len(nolog[s]) > 1))

# Band blind spot for w1 at 4,500 and the v3w arm median there
def med(A, k):
    return float(np.median([v(r, k) for r in A]))
w1 = [r for r in B if r["name"] == "B|w1" and r["q"] == 4500.0]
print("B|w1 4500 medians: ttc_net", med(w1, "ttc_net"), "ttc_half", med(w1, "ttc_half"), "brake_net", med(w1, "brake_net"), "b3_step", med(w1, "b3_step"))
by = defaultdict(dict)
for r in B:
    if r["q"] == 4500.0 and r["name"] in [f"B|w{i}" for i in range(5)]:
        by[r["seed"]][r["name"]] = r
arm = {k: [np.mean([v(x, k) for x in d.values()]) for d in by.values()] for k in ("ttc_net", "ttc_half")}
print("v3w arm 4500 medians: ttc_net", float(np.median(arm["ttc_net"])), "ttc_half", float(np.median(arm["ttc_half"])))
nc45 = [r for r in B if r["name"] == "B|nc" and r["q"] == 4500.0]
print("nc 4500 ttc_net median", med(nc45, "ttc_net"))

# Split differences (where the gain is), X1 vs p333 and X2 vs os1_15_10, with the v3w arm mean
def armT(cell):
    d = defaultdict(dict)
    for r in T:
        if r["name"] in [f"{cell}|w{i}" for i in range(5)]:
            d[r["seed"]][r["name"]] = r
    keys = {k for s in d for r in d[s].values() for k, x in r.items() if isinstance(x, (int, float)) and not isinstance(x, bool)}
    return [{k: np.mean([v(r, k) for r in d[s].values()]) for k in keys} for s in sorted(d)]
for cell, ref in (("X1", "p333"), ("X2", "os1_15_10")):
    A = armT(cell)
    O = [r for r in T if r["name"] == f"{cell}|{ref}"]
    Os = {r["seed"]: r for r in O}
    Ad = defaultdict(dict)
    for r in T:
        if r["name"] in [f"{cell}|w{i}" for i in range(5)]:
            Ad[r["seed"]][r["name"]] = r
    out = {}
    for g in ROAD + SPD + PER:
        k = f"ttc3_{g}"
        diffs = [v(Os[s], k) - np.mean([v(x, k) for x in Ad[s].values()]) for s in sorted(Ad)]
        out[g] = (round(med(O, k) - float(np.median([a[k] if k in a else 0.0 for a in A])), 1), round(float(np.median(diffs)), 1))
    print("split gain", cell, "vs", ref, "(diff of medians, median paired diff):", out)
    tot = [v(Os[s], "ttc_net") - np.mean([v(x, "ttc_net") for x in Ad[s].values()]) for s in sorted(Ad)]
    print("  total paired median", round(float(np.median(tot)), 1))

# Collisions per arm (sum), and alks_full events
for cell in ("X1", "X2"):
    for n in ("nc", "p333", "os1_15_10"):
        A = [r for r in T if r["name"] == f"{cell}|{n}"]
        print("coll", cell, n, sum(v(r, "collisions") for r in A), "alks_full_moving sum", sum(v(r, "alks_full_moving") for r in A), "alks_full_creep sum", sum(v(r, "alks_full_creep") for r in A))
    W = [r for r in T if r["name"] in [f"{cell}|w{i}" for i in range(5)]]
    print("coll", cell, "w0-4 total", sum(v(r, "collisions") for r in W), "runs", len(W))
