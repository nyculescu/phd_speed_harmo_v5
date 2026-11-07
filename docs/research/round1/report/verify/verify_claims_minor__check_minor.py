"""Aggregates for the minor-claim checks F11-F18 (stored rows only, no simulation)."""
import json
import sys
from pathlib import Path

REPO = Path("/srv/shared/Workspace/phd/phd_speed_harmo_v5b1")
sys.path.insert(0, str(REPO / "docs/research/round1"))
from common1 import LEARNERS, RULE, arm_mean, load, med, paired_median, raw  # noqa: E402

OUT = Path("/home/catalin/work/phd/v5b1_runs/round1_remote/out")
T = load(OUT / "test" / "test.jsonl")
P95 = (2.5, 97.5)

print("F13: X2 v3w arm minus os1_15_10, TTC split counters")
A = arm_mean(T, [f"X2|w{i}" for i in range(LEARNERS)])
R = T[("X2|os1_15_10", 5300.0)]
splits = ["r_3", "r_4a", "r_ramp2", "r_rest", "s_lo", "s_mid", "s_hi", "p_before", "p_taper", "p_hold", "p_after", "p_rest"]
for s in splits:
    k = "ttc3_" + s
    print(f"  {s}: med A {med(A, k):.1f} med R {med(R, k):.1f} diff-of-medians {med(A, k) - med(R, k):.1f} paired-median {paired_median(A, R, k):.1f}")
print("  total ttc3 paired", round(paired_median(A, R, "ttc3"), 1), "ttc_net paired", round(paired_median(A, R, "ttc_net"), 1))
for grp in (["r_3", "r_4a", "r_ramp2", "r_rest"], ["s_lo", "s_mid", "s_hi"], ["p_before", "p_taper", "p_hold", "p_after", "p_rest"]):
    dm = {s: med(A, "ttc3_" + s) - med(R, "ttc3_" + s) for s in grp}
    pm = {s: paired_median(A, R, "ttc3_" + s) for s in grp}
    tot_dm, tot_pm = sum(dm.values()), sum(pm.values())
    print("  shares diff-of-medians", {s: round(v / tot_dm * 100, 1) for s, v in dm.items()}, "| paired", {s: round(v / tot_pm * 100, 1) for s, v in pm.items()})
# mean-based shares (means add exactly)
import numpy as np  # noqa: E402
for grp in (["r_3", "r_4a", "r_ramp2", "r_rest"], ["s_lo", "s_mid", "s_hi"], ["p_before", "p_taper", "p_hold", "p_after", "p_rest"]):
    md = {s: float(np.mean([A[k].get("ttc3_" + s, 0.0) - float(R[k].get("ttc3_" + s, 0.0) or 0.0) for k in A])) for s in grp}
    tot = sum(md.values())
    print("  mean diffs", {s: round(v, 1) for s, v in md.items()}, "shares", {s: round(v / tot * 100, 1) for s, v in md.items()})

print("\nF12: T1 X2 TTC vs baseline-v3 at 98.75 %")
I = arm_mean(T, [f"X2|d{i}" for i in range(LEARNERS)])
print("  ", [round(x, 2) for x in raw(A, I, "ttc_net")])

print("\nF15: counting candidates, paired all_delay vs p333 (point), and TTC medians")
O = json.load(open(REPO / "docs/research/baseline_v3/opponents.json"))
for c in ("X1", "X2"):
    p = T[(f"{c}|p333", 5300.0)]
    for r in dict.fromkeys(["p333", *O["cells"][c]["forms"].values()]):
        X = T[(f"{c}|{r}", 5300.0)]
        print(f"  {c} {r}: delay vs p333 {raw(X, p, 'all_delay')[0]:.2f} counts {raw(X, p, 'all_delay')[0] >= -2.0} ttc med {med(X, 'ttc_net'):.1f}")

print("\nF11: X2 v3w arm vs nc (95 %)")
nc = T[("X2|nc", 5300.0)]
print("  ttc", [round(x, 1) for x in raw(A, nc, "ttc_net", pct=P95)], "delay", [round(x, 1) for x in raw(A, nc, "all_delay", pct=P95)])

print("\nF18: validation arms, TTC vs os1_15_10 (95 %)")
V = load(OUT / "val" / "validation.jsonl")
vj = json.load(open(OUT / "val" / "validation.json"))
print("  validation.json keys", list(vj.keys()))
names = sorted({k[0] for k in V})
print("  arm names sample", names[:12], "... n", len(names))
