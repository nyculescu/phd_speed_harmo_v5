"""Aggregates only: CI level, per-learner spread, copy rule, excluded opponents, severe and no-control checks."""
import json
import sys
from pathlib import Path

import numpy as np

REPO = Path("/srv/shared/Workspace/phd/phd_speed_harmo_v5b1")
sys.path.insert(0, str(REPO / "docs/research/round1"))
sys.path.insert(0, str(REPO / "docs/research/conf3"))
sys.path.insert(0, str(REPO))
from common1 import LEARNERS, OPPONENTS, PRIMARY, Q, arm_mean, collisions, load, med, paired_median, raw  # noqa: E402
import decide1 as dc  # noqa: E402

OUT = Path("/home/catalin/work/phd/v5b1_runs/round1_remote/out")
T = load(OUT / "test/test.jsonl")
V = load(OUT / "val/validation.jsonl")
TB = load(OUT / "test/band.jsonl")
P975 = (1.25, 98.75)
P9875 = (0.625, 99.375)
P95 = (2.5, 97.5)
r = lambda x: tuple(round(v, 2) for v in x)

w = [f"w{i}" for i in range(LEARNERS)]
d = [f"d{i}" for i in range(LEARNERS)]
print("== T1 at percentiles (1.25,98.75) and true 98.75 % (0.625,99.375)")
for c in PRIMARY:
    for p in (P975, P9875):
        b = dc.better(T, c, w, d, p)
        print(c, p, "delay", r(b["delay_vs_incumbent"]), "ttc", r(b["ttc_vs_incumbent"]), "better", b["better"])
print("== T2 at true 98.75 %")
for c in PRIMARY:
    for p in (P975, P9875):
        t = dc.tuned(T, c, OPPONENTS, w, p)
        ti = dc.tuned(T, c, OPPONENTS, d, p)
        print(c, p, "v3w tuned", t["tuned"], t["blocked"], "| inc tuned", ti["tuned"], ti["blocked"])

print("== per-learner median delay and TTC (test), v3w and baseline-v3")
for c in PRIMARY:
    for pre in ("w", "d"):
        dl = [med(T[(f"{c}|{pre}{i}", Q)], "all_delay") for i in range(LEARNERS)]
        tt = [med(T[(f"{c}|{pre}{i}", Q)], "ttc_net") for i in range(LEARNERS)]
        print(c, pre, "delay", [round(x) for x in dl], "sd/mean %", round(np.std(dl, ddof=1) / np.mean(dl) * 100, 2),
              "ttc", [round(x) for x in tt], "sd/mean %", round(np.std(tt, ddof=1) / np.mean(tt) * 100, 2))
    I = arm_mean(T, [f"{c}|{x}" for x in d])
    print(c, "each v3w learner vs baseline-v3 arm, delay", [r(raw(T[(f"{c}|w{i}", Q)], I, "all_delay", pct=P95))[0] for i in range(LEARNERS)])
    W = arm_mean(T, [f"{c}|{x}" for x in w])
    print(c, "each baseline-v3 learner vs v3w arm, delay", [r(raw(T[(f"{c}|d{i}", Q)], W, "all_delay", pct=P95))[0] for i in range(LEARNERS)])

print("== opponents: paired delay vs p333 (point), TTC median; counting")
for c in PRIMARY:
    p333 = T[(f"{c}|p333", Q)]
    forms = OPPONENTS["cells"][c]["forms"]
    for n in OPPONENTS["ctrl"]:
        e = raw(T[(f"{c}|{n}", Q)], p333, "all_delay")[0]
        print(c, n, "form" if n in forms.values() else "-", "delay vs p333", round(e, 2), "ttc", med(T[(f"{c}|{n}", Q)], "ttc_net"))

print("== copy rule: each v3w learner against copy (TTC effect, CI 1.25-98.75, fails)")
for c in PRIMARY:
    cp = T[(f"{c}|copy", Q)]
    for i in range(LEARNERS):
        P = T[(f"{c}|w{i}", Q)]
        print(c, i, r(raw(P, cp, "ttc_net")), "delay", round(raw(P, cp, "all_delay")[0], 2), dc.fails(P, cp, 10.0, P975))

print("== severe check: per learner paired median sev3 vs counting rules; vs nc")
for c in PRIMARY:
    t = dc.tuned(T, c, OPPONENTS, w, P975)
    for i in range(LEARNERS):
        P = T[(f"{c}|w{i}", Q)]
        print(c, i, {o: paired_median(P, T[(f"{c}|{o}", Q)], "sev3") for o in t["counts"]}, "vs nc", paired_median(P, T[(f"{c}|nc", Q)], "sev3"))

print("== v3w learners vs no control (TTC, sev3, b3_step, delay), CI 1.25-98.75")
for c in PRIMARY:
    nc = T[(f"{c}|nc", Q)]
    for i in range(LEARNERS):
        P = T[(f"{c}|w{i}", Q)]
        print(c, i, "ttc", r(raw(P, nc, "ttc_net")), "sev3", r(raw(P, nc, "sev3")), "b3", r(raw(P, nc, "b3_step")), "delay", r(raw(P, nc, "all_delay")))
    W = arm_mean(T, [f"{c}|{x}" for x in w])
    for p in (P95, P975):
        print(c, "arm", p, "ttc", r(raw(W, nc, "ttc_net", pct=p)), "sev3", r(raw(W, nc, "sev3", pct=p)), "b3", r(raw(W, nc, "b3_step", pct=p)),
              "b7", r(raw(W, nc, "b7_step", pct=p)), "delay", r(raw(W, nc, "all_delay", pct=p)))
    print(c, "nc extra delay vs arm", round(raw(nc, W, "all_delay", 1)[0], 2), "per learner median", sorted(round(raw(nc, T[(f"{c}|w{i}", Q)], "all_delay", 1)[0], 1) for i in range(LEARNERS)))

print("== collisions per arm (sum over 40 seeds)")
for c in PRIMARY:
    print(c, {n: collisions(T[(f"{c}|{n}", Q)]) for n in [*w, *d, "nc", *OPPONENTS["ctrl"]] if collisions(T[(f"{c}|{n}", Q)])})

print("== validation: baseline-v3 arm vs os1_15_10 TTC (95 %), and res / v3w")
inc = {i: 500 for i in range(LEARNERS)}
for c in PRIMARY:
    I = dc.arm(V, c, "d", inc)
    print(c, "baseline-v3 ttc vs os1_15_10", r(raw(I, V[(f"{c}|os1_15_10", Q)], "ttc_net", pct=P95)), "delay vs os1", r(raw(I, V[(f"{c}|os1_15_10", Q)], "all_delay", pct=P95)))

print("== band: each learner vs nc at each level (95 %), ttc and delay")
for q in (4500.0, 5000.0, 5250.0, 5500.0, 6000.0):
    nc = TB[("B|nc", q)]
    for pre in ("w", "d"):
        out = []
        for i in range(LEARNERS):
            t = raw(TB[(f"B|{pre}{i}", q)], nc, "ttc_net", pct=P95)
            dd = raw(TB[(f"B|{pre}{i}", q)], nc, "all_delay", pct=P95)
            out.append((round(t[0], 1), round(t[2], 1), round(dd[0], 1)))
        print(q, pre, out, "nc per-run ttc", med(nc, "ttc_net"))
    W = arm_mean(TB, [f"B|w{i}" for i in range(LEARNERS)], q)
    print(q, "v3w arm per-run lower (nc - arm)", paired_median(nc, W, "ttc_net"))
