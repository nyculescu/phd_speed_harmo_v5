"""Aggregates only: delay-win detail, split totals per row, v3w vs no control on sev3/b7."""
import sys
from pathlib import Path

REPO = Path("/srv/shared/Workspace/phd/phd_speed_harmo_v5b1")
sys.path.insert(0, str(REPO / "docs/research/round1"))
sys.path.insert(0, str(REPO / "docs/research/conf3"))
from common1 import LEARNERS, OPPONENTS, PRIMARY, Q, arm_mean, load, med, raw, val  # noqa: E402

OUT = Path("/home/catalin/work/phd/v5b1_runs/round1_remote/out")
T = load(OUT / "test/test.jsonl")
r = lambda x: tuple(round(v, 2) for v in x)

print("== delay of each v3w learner vs p333 and the delay opponent (CI 1.25-98.75)")
for c in PRIMARY:
    dop = OPPONENTS["cells"][c]["delay_opponent"]
    print(c, "delay opponent", dop, "median delay", round(med(T[(f"{c}|{dop}", Q)], "all_delay")), "p333", round(med(T[(f"{c}|p333", Q)], "all_delay")))
    for i in range(LEARNERS):
        P = T[(f"{c}|w{i}", Q)]
        print(c, i, "vs p333", r(raw(P, T[(f"{c}|p333", Q)], "all_delay")), "vs dop", r(raw(P, T[(f"{c}|{dop}", Q)], "all_delay")))
    W = arm_mean(T, [f"{c}|w{i}" for i in range(LEARNERS)])
    print(c, "arm vs p333 95 %", r(raw(W, T[(f"{c}|p333", Q)], "all_delay", pct=(2.5, 97.5))), "arm vs dop 95 %", r(raw(W, T[(f"{c}|{dop}", Q)], "all_delay", pct=(2.5, 97.5))))

print("== split totals per row: rows where road, speed or period sums differ from ttc3, and ttc3 != ttc_net")
bad = {"road": 0, "speed": 0, "period": 0, "ttc3_vs_net": 0}
n = 0
for (name, q), A in T.items():
    for s, row in A.items():
        n += 1
        t3 = val(row, "ttc3")
        bad["road"] += abs(sum(val(row, f"ttc3_r_{x}") for x in ("3", "4a", "ramp2", "rest")) - t3) > 1e-9
        bad["speed"] += abs(sum(val(row, f"ttc3_s_{x}") for x in ("lo", "mid", "hi")) - t3) > 1e-9
        bad["period"] += abs(sum(val(row, f"ttc3_p_{x}") for x in ("before", "taper", "hold", "after", "rest")) - t3) > 1e-9
        bad["ttc3_vs_net"] += abs(t3 - val(row, "ttc_net")) > 1e-9
print("rows", n, bad)

print("== X2 v3w vs os1_15_10: median paired split differences (arm minus rule)")
import numpy as np  # noqa: E402
for c, rule in (("X1", "p333"), ("X2", "os1_15_10")):
    W = arm_mean(T, [f"{c}|w{i}" for i in range(LEARNERS)])
    R = T[(f"{c}|{rule}", Q)]
    ks = [f"ttc3_{m}" for m in ("r_3", "r_4a", "r_ramp2", "r_rest", "s_lo", "s_mid", "s_hi", "p_before", "p_taper", "p_hold", "p_after", "p_rest")]
    print(c, rule, {k[5:]: round(float(np.median([val(W[s], k) - val(R[s], k) for s in sorted(set(W) & set(R))])), 1) for k in ks})
