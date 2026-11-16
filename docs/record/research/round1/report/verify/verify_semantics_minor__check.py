"""Aggregates only: checks for claims S4-S12 on the round-1 rows."""
import json
from collections import defaultdict, Counter
import numpy as np

OUT = "/home/catalin/work/phd/v5b1_runs/round1_remote/out"
files = {"val": f"{OUT}/val/validation.jsonl", "test": f"{OUT}/test/test.jsonl", "band": f"{OUT}/test/band.jsonl"}
rows = {k: [json.loads(l) for l in open(p)] for k, p in files.items()}

# S4: ttc3 vs ttc_net and split sums
ROADS, SPEEDS, PERS = ("r_3", "r_4a", "r_ramp2", "r_rest"), ("s_lo", "s_mid", "s_hi"), ("p_before", "p_taper", "p_hold", "p_after", "p_rest")
n = neq = 0
bad = Counter()
for k, R in rows.items():
    for r in R:
        n += 1
        neq += r.get("ttc3", 0) != r.get("ttc_net", 0)
        for m in ("ttc3", "sev3"):
            for lab, grp in (("road", ROADS), ("speed", SPEEDS), ("period", PERS)):
                if abs(sum(r.get(f"{m}_{g}", 0) for g in grp) - r.get(m, 0)) > 1e-9:
                    bad[(m, lab)] += 1
print("S4 rows", n, "ttc3!=ttc_net", neq, "split mismatches", dict(bad))

# arms in test
by = defaultdict(list)
for r in rows["test"]:
    by[r["name"]].append(r)
print("test arms", len(by), "rows per arm", Counter(len(v) for v in by.values()))


def arm_mean(cell, pre, key):
    per = defaultdict(list)
    for i in range(5):
        for r in by[f"{cell}|{pre}{i}"]:
            per[r["seed"]].append(r.get(key, 0.0))
    return {s: np.mean(v) for s, v in per.items() if len(v) == 5}


for cell in ("X1", "X2"):
    keys = [f"ttc3_{g}" for g in ROADS]
    meds = [np.median(list(arm_mean(cell, "w", k).values())) for k in keys]
    print("S4", cell, "v3w road medians", [round(x, 1) for x in meds], "sum", round(sum(meds), 1), "ttc3 median", round(np.median(list(arm_mean(cell, "w", "ttc3").values())), 1))

# S5: pert_log on/off times by cell
for cell in ("X1", "X2"):
    logs = Counter()
    for name, R in by.items():
        if name.startswith(cell + "|"):
            for r in R:
                logs[json.dumps(r.get("pert_log"))] += 1
    print("S5", cell, "distinct pert_log", len(logs), [(k[:80], v) for k, v in logs.most_common(3)])
    for name, R in by.items():
        if name.startswith(cell + "|"):
            print("S5", cell, "steps", Counter(r["steps"] for r in R).most_common(2)); break

# S7: band slowdown draw
draw = Counter()
for s in range(7_440_540, 7_440_560):
    r = np.random.default_rng(s + 910_000)
    if r.random() >= 1 / 3:
        e = str(r.choice(("3", "4", "5")))
        draw[e] += 1
    else:
        draw["none"] += 1
print("S7 draw", dict(draw))
bp = defaultdict(set)
for r in rows["band"]:
    bp[r["seed"]].add(json.dumps(r.get("pert_log")))
print("S7 band seeds", len(bp), "seeds with one distinct log across arms/levels", sum(len(v) == 1 for v in bp.values()), "seeds with events", sum(any(json.loads(x) for x in v) for v in bp.values()))
bcfg = Counter(json.dumps(r["cfg"].get("ctrl", {}).get("env", {}).get("perturb")) for r in rows["band"])
print("S7 band perturb cfg", bcfg.most_common(3))

# S8: w1 at 4500
bb = defaultdict(list)
for r in rows["band"]:
    bb[(r["name"], r["q"])].append(r)
w1 = bb[("B|w1", 4500.0)]
print("S8 B|w1 4500 n", len(w1), "ttc_net med", np.median([r["ttc_net"] for r in w1]), "ttc_half med", np.median([r["ttc_half"] for r in w1]))
per = defaultdict(lambda: [[], []])
for i in range(5):
    for r in bb[(f"B|w{i}", 4500.0)]:
        per[r["seed"]][0].append(r["ttc_net"]); per[r["seed"]][1].append(r["ttc_half"])
tn = np.median([np.mean(a) for a, b in per.values()]); th = np.median([np.mean(b) for a, b in per.values()])
print("S8 v3w arm 4500 ttc_net med", tn, "ttc_half med", th, "ratio", round(tn / th, 3))
for i in range(5):
    R = bb[(f"B|w{i}", 4500.0)]
    print("S8 w%d 4500 ttc_net/half" % i, np.median([r["ttc_net"] for r in R]), np.median([r["ttc_half"] for r in R]))

# S9: moving full-emergency totals
for cell in ("X1", "X2"):
    tot = {}
    for lab, names in (("v3w", [f"{cell}|w{i}" for i in range(5)]), ("baseline-v3", [f"{cell}|d{i}" for i in range(5)]), ("p333", [f"{cell}|p333"]), ("os1_15_10", [f"{cell}|os1_15_10"]), ("nc", [f"{cell}|nc"])):
        R = [r for nm in names for r in by[nm]]
        tot[lab] = (len(R), sum(r.get("alks_full_moving", 0) for r in R), sum(r.get("alks_full_creep", 0) for r in R), np.median([r.get("alks_full_moving", 0) for r in R]))
    print("S9", cell, tot)
    allr = Counter()
    for nm, R in by.items():
        if nm.startswith(cell + "|"):
            allr[nm.split("|")[1]] = sum(r.get("alks_full_moving", 0) for r in R)
    print("S9", cell, "all arms moving totals", dict(allr))
