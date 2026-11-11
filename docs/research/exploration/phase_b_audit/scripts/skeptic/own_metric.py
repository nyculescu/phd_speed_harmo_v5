"""EXPLORATORY skeptic checks on the metric audit. Read-only on stored extracts (audit2/*.pkl).
Statistic: median of paired differences, 95 % percentile bootstrap, 10,000 resamples, RNG 20261110; v3w = stacked single learners (seeds resampled together)."""
import pickle, sys
import numpy as np
A2 = "/tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/89ba3663-8e1a-45c3-9415-9e2a743fb16b/scratchpad/phaseB/audit2/"
sys.path.insert(0, A2)
from meas import boot, boot_stack, boot_mean, REF
S6 = pickle.load(open(A2 + "s6.pkl", "rb")); R2T = pickle.load(open(A2 + "r2t.pkl", "rb")); S01 = pickle.load(open(A2 + "s01.pkl", "rb"))
L = ["w0u250", "w1u500", "w2u250", "w3u500", "w4u500"]
f = lambda e, p=2: f"{e[0]:+.{p}f} [{e[1]:+.{p}f}, {e[2]:+.{p}f}]"
def arr(T, cell, arm, seeds, fn):
    return np.array([fn(T[(cell, arm)][s]) for s in seeds], float)
def unf(r):
    return r["m_planned_window"] * (1.0 - r["finished_pct"] / 100.0)
def late(r, k0):          # edges 2 to 4a plus ramp queues, minutes k0..24
    mm = r["minute"]; per = np.zeros(25)
    for k in ("m1_acc", "m1_up", "m2_acc", "m2_up"):
        per += np.array(mm[k + "_n"]) - np.array(mm[k + "_vs"]) / REF
    per += np.array(mm["ramp1_pending"]) + np.array(mm["ramp2_pending"])
    return per[k0:].sum()
def cmp(T, cell, opp, seeds, fn, ref_arm="p333", sign=1.0, p=2, pct=True):
    """sign=+1: X minus ref, % of ref median. v3w stacked."""
    r = arr(T, cell, ref_arm, seeds, fn); den = np.median(r) / 100.0 if pct else 1.0
    if opp == "v3w":
        D = np.array([sign * (arr(T, cell, l, seeds, fn) - r) / den for l in L]); return f(boot_stack(D), p)
    return f(boot(sign * (arr(T, cell, opp, seeds, fn) - r) / den), p)
print("### A. End-of-window backlog per arm (vehicles; medians), S6, 240 seeds")
for cell in ("S", "TRUCK"):
    seeds = list(range(7480400, 7480640))
    for a in ["nc", "p333", "os0_10_10", "3E-C_TRUCK", "3E-D_TRUCK"] + L:
        u = arr(S6, cell, a, seeds, unf); pe = arr(S6, cell, a, seeds, lambda r: r["m_pending_end"]); pa = arr(S6, cell, a, seeds, lambda r: r["passed"]); ar = arr(S6, cell, a, seeds, lambda r: r["arrived"])
        print(f"  {cell:5s} {a:11s} unfinished {np.median(u):7.1f} (mean {u.mean():7.1f}) | not inserted at end {np.median(pe):5.1f} (mean {pe.mean():5.1f}) | passed {np.median(pa):7.1f} | arrived {np.median(ar):7.1f} | all_delay median {np.median(arr(S6, cell, a, seeds, lambda r: r['all_delay'])):9.0f}")
    for o in ("v3w", "os0_10_10", "3E-C_TRUCK", "3E-D_TRUCK", "nc"):
        print(f"  {cell} {o:11s} minus p333: unfinished {cmp(S6, cell, o, seeds, unf, pct=False, p=1)} | not inserted {cmp(S6, cell, o, seeds, lambda r: r['m_pending_end'], pct=False, p=1)} | passed {cmp(S6, cell, o, seeds, lambda r: r['passed'], pct=False, p=1)} | arrived {cmp(S6, cell, o, seeds, lambda r: r['arrived'], pct=False, p=1)}")
print("\n### B. Reference speed sweep: delay(v) = N - dist_step / v. X minus p333, % of p333's median; positive = p333 better")
for cell in ("S", "TRUCK"):
    seeds = list(range(7480400, 7480640))
    for kmh in (80, 90, 100, 110, 120, 130):
        fn = lambda r, v=kmh / 3.6: r["N"] - r["dist_step"] / v
        print(f"  {cell:5s} {kmh:3d} km/h: p333 median {np.median(arr(S6, cell, 'p333', seeds, fn)):9.0f} | v3w {cmp(S6, cell, 'v3w', seeds, fn)} | os0 {cmp(S6, cell, 'os0_10_10', seeds, fn)} | 3E-C {cmp(S6, cell, '3E-C_TRUCK', seeds, fn)} | 3E-D {cmp(S6, cell, '3E-D_TRUCK', seeds, fn)}")
print("\n### C. Completion charge: all_delay + h x unfinished vehicles at 1,800 s. X minus p333, % of p333's median; positive = p333 better")
for cell in ("S", "TRUCK"):
    seeds = list(range(7480400, 7480640))
    for h in (0, 60, 120, 300, 600, 900):
        fn = lambda r, h=h: r["all_delay"] + h * unf(r)
        print(f"  {cell:5s} h={h:4d} s: v3w {cmp(S6, cell, 'v3w', seeds, fn)} | os0 {cmp(S6, cell, 'os0_10_10', seeds, fn)} | 3E-C {cmp(S6, cell, '3E-C_TRUCK', seeds, fn)} | 3E-D {cmp(S6, cell, '3E-D_TRUCK', seeds, fn)}")
print("\n### D. Start-up excluded: edges 2 to 4a plus ramp queues, minutes k0 to 24. X minus p333, % of p333's median; positive = p333 better")
for cell in ("S", "TRUCK"):
    seeds = list(range(7480400, 7480640))
    for k0 in (0, 5, 10, 15, 20):
        fn = lambda r, k0=k0: late(r, k0)
        print(f"  {cell:5s} from minute {k0:2d}: p333 median {np.median(arr(S6, cell, 'p333', seeds, fn)):8.0f} veh-s | v3w {cmp(S6, cell, 'v3w', seeds, fn)} | os0 {cmp(S6, cell, 'os0_10_10', seeds, fn)} | 3E-C {cmp(S6, cell, '3E-C_TRUCK', seeds, fn)} | 3E-D {cmp(S6, cell, '3E-D_TRUCK', seeds, fn)}")
    # the same in absolute veh-s against the whole-network all_delay difference
    fnA = lambda r: r["all_delay"]
    print(f"  {cell} whole network all_delay, v3w minus p333, veh-s: {cmp(S6, cell, 'v3w', seeds, fnA, pct=False, p=0)}; edges 2-4a + ramp queues: all minutes {cmp(S6, cell, 'v3w', seeds, lambda r: late(r, 0), pct=False, p=0)}, first 5 {cmp(S6, cell, 'v3w', seeds, lambda r: late(r, 0) - late(r, 5), pct=False, p=0)}, last 5 {cmp(S6, cell, 'v3w', seeds, lambda r: late(r, 20), pct=False, p=0)}")
print("\n### E. Null of the pooled-arm statistic: mean of the other four learners minus one learner, % of that learner's median (all_delay)")
for cell in ("S", "TRUCK"):
    seeds = list(range(7480400, 7480640))
    A = {l: arr(S6, cell, l, seeds, lambda r: r["all_delay"]) for l in L}
    out = [boot((np.mean([A[m] for m in L if m != l], axis=0) - A[l]) / np.median(A[l]) * 100) for l in L]
    print(f"  {cell}: " + " | ".join(f(e) for e in out) + f" | mean of the five {np.mean([e[0] for e in out]):+.2f}")
    # second null: one learner minus another, all 20 ordered pairs -> should centre on 0 if learners are exchangeable
    pr = [boot((A[a] - A[b]) / np.median(A[b]) * 100)[0] for a in L for b in L if a != b]
    print(f"  {cell}: single learner minus single learner, 20 ordered pairs: medians min {min(pr):+.2f}, max {max(pr):+.2f}")
    # per-learner medians against p333
    P = arr(S6, cell, "p333", seeds, lambda r: r["all_delay"])
    print(f"  {cell}: each learner minus p333, % of p333 median: " + " | ".join(f(boot((A[l] - P) / np.median(P) * 100)) for l in L))
print("\n### F. X1, X2 (round 2 test rows, 40 seeds): p333 or rule minus v3w; positive = v3w better")
for cell, ex in (("X1", "3ex1"), ("X2", "3ex2")):
    seeds = sorted(R2T[(cell, "p333")])
    has_pl = R2T[(cell, "p333")][seeds[0]].get("m_planned_window") is not None
    print(f"  {cell}: n={len(seeds)}, planned count in rows: {has_pl}")
    for opp in ("p333", "os0_10_10", ex, "nc"):
        if (cell, opp) not in R2T:
            continue
        o = lambda fn: arr(R2T, cell, opp, seeds, fn)
        den = lambda fn: np.median(o(fn)) / 100.0
        st = lambda fn, pct=True: f(boot_stack(np.array([(o(fn) - arr(R2T, cell, l, seeds, fn)) / (den(fn) if pct else 1.0) for l in L])), 2 if pct else 1)
        line = f"  {cell} {opp:10s}"
        for kmh in (80, 100, 120):
            line += f" | ref {kmh}: {st(lambda r, v=kmh / 3.6: r['N'] - r['dist_step'] / v)}"
        line += f" | unfinished points of planned: {st(lambda r: 100.0 - r['finished_pct'], pct=False)} | passed: {st(lambda r: r['passed'], pct=False)}"
        print(line)
    # backlog medians per arm
    for a in ["nc", "p333", "os0_10_10", ex] + L:
        if (cell, a) in R2T:
            print(f"    {cell} {a:10s} unfinished % of planned, median {np.median(arr(R2T, cell, a, seeds, lambda r: 100.0 - r['finished_pct'])):5.2f} | passed {np.median(arr(R2T, cell, a, seeds, lambda r: r['passed'])):7.1f} | all_delay {np.median(arr(R2T, cell, a, seeds, lambda r: r['all_delay'])):9.0f}")
