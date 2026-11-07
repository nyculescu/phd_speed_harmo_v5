"""F1: learner spread of delay and TTC on the test, baseline-v3 (d) against v3w (w). Aggregates only."""
import sys
import numpy as np

sys.path.insert(0, "/srv/shared/Workspace/phd/phd_speed_harmo_v5b1/docs/research/conf3")
from common import load, raw, val  # noqa: E402

OUT = "/home/catalin/work/phd/v5b1_runs/round1_remote/out/test/test.jsonl"
T = load(OUT)
Q = 5300.0
P = (1.25, 98.75)


def arm(cell, pre):
    A = [T[(f"{cell}|{pre}{i}", Q)] for i in range(5)]
    seeds = sorted(set.intersection(*[set(a) for a in A]))
    keys = ("all_delay", "ttc_net", "passed")
    return {s: {k: float(np.mean([val(a[s], k) for a in A])) for k in keys} | {"seed": s} for s in seeds}


for cell in ("X1", "X2"):
    print(f"== {cell}")
    for key in ("all_delay", "ttc_net"):
        for pre in ("d", "w"):
            m = [float(np.median([val(r, key) for r in T[(f"{cell}|{pre}{i}", Q)].values()])) for i in range(5)]
            mu = np.mean(m)
            print(f"{key} {pre}: per-learner medians {[round(x) for x in m]} mean {mu:.0f} sd/mean {np.std(m, ddof=1) / mu * 100:.2f}%")
    W, D = arm(cell, "w"), arm(cell, "d")
    print("T1 delay w vs d", [round(x, 2) for x in raw(W, D, "all_delay", pct=P)])
    print("T1 ttc w vs d", [round(x, 2) for x in raw(W, D, "ttc_net", pct=P)])
    # each baseline-v3 learner alone against the v3w arm
    for i in range(5):
        Di = T[(f"{cell}|d{i}", Q)]
        print(f"d{i} alone vs w arm, delay (positive = d{i} less delay):", [round(x, 2) for x in raw(Di, W, "all_delay", pct=(2.5, 97.5))])
    # learner-level comparison: per-learner median delay, Welch t on 5 vs 5
    md = np.array([np.median([val(r, "all_delay") for r in T[(f"{cell}|d{i}", Q)].values()]) for i in range(5)])
    mw = np.array([np.median([val(r, "all_delay") for r in T[(f"{cell}|w{i}", Q)].values()]) for i in range(5)])
    diff = (md.mean() - mw.mean()) / md.mean() * 100
    se = np.sqrt(md.var(ddof=1) / 5 + mw.var(ddof=1) / 5) / md.mean() * 100
    print(f"learner-level: mean of medians diff {diff:.2f}% , SE {se:.2f}%, t {diff / se:.2f}")
    # simple permutation over learner labels (10 vs choose 5 = 252 splits)
    import itertools
    allm = np.concatenate([md, mw])
    obs = md.mean() - mw.mean()
    cnt = 0
    tot = 0
    for idx in itertools.combinations(range(10), 5):
        a = allm[list(idx)]
        b = np.delete(allm, list(idx))
        tot += 1
        if abs(a.mean() - b.mean()) >= abs(obs) - 1e-9:
            cnt += 1
    print(f"learner-label permutation, two-sided p = {cnt}/{tot} = {cnt / tot:.3f}")
