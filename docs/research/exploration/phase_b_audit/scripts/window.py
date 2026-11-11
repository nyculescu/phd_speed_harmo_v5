"""(D i) window sensitivity. EXPLORATORY.
U(T) = vehicle-seconds upstream of edge 4 (insertion queues included) accumulated from 300 s to T, arm X minus p333.
Inflow is the same per seed, so U(T) = - sum over minutes up to T of (cumulative passed_X - cumulative passed_p333) x 60 s."""
import pickle, numpy as np
from meas import *
f = lambda e, p=0: f"{e[0]:+.{p}f} [{e[1]:+.{p}f}, {e[2]:+.{p}f}]"
def U(T, cell, arm, seeds):
    fm = np.array([T[(cell, arm)][s]["flow_min"] for s in seeds], float)     # 26 bins: 301-359 s, then 60-s bins, then t = 1800
    return np.cumsum(fm, axis=1)
def prof(T, cell, opps, learners, seeds, ref="p333", sign=1.0):
    cp = U(T, cell, ref, seeds)
    ends = {600: 4, 900: 9, 1200: 14, 1500: 19, 1800: 24}
    for a in opps:
        cs = [U(T, cell, l, seeds) for l in learners] if a == "v3w" else [U(T, cell, a, seeds)]
        out = []
        for t_end, k in ends.items():
            D = np.array([sign * -((c - cp)[:, :k + 1].sum(axis=1)) * 60.0 for c in cs])
            e = boot_stack(D) if len(cs) > 1 else boot(D[0])
            m = boot_mean(D.mean(axis=0))
            out.append(f"{t_end} s: {f(e)} (mean {m[0]:+.0f} [{m[1]:+.0f}, {m[2]:+.0f}])")
        print(f"  {a:11s} " + " | ".join(out))
        # vehicles ahead at the window end
        D = np.array([sign * (c - cp)[:, -1] for c in cs])
        e = boot_stack(D, ) if len(cs) > 1 else boot(D[0])
        print(f"              cumulative passed at 1,800 s, {('X minus ' + ref) if sign > 0 else (ref + ' minus X')}: {f(e, 1)}")
S6 = pickle.load(open("s6.pkl", "rb"))
L = ["w0u250", "w1u500", "w2u250", "w3u500", "w4u500"]
for cell in ("S", "TRUCK"):
    print(f"\n## {cell}: X minus p333, veh-s upstream of edge 4 if the window ended at T (positive = p333 better); median [95 %], v3w = stacked single learners")
    prof(S6, cell, ["v3w", "os0_10_10", "3E-C_TRUCK", "nc"], L, list(range(7480400, 7480640)))
    # per 5-minute block: delay on edges 2, 3a, 3, 4a plus ramp insertion queues, v3w minus p333, % of p333's block median
    seeds = list(range(7480400, 7480640))
    def blocks(arm):
        out = []
        for s in seeds:
            mm = S6[(cell, arm)][s]["minute"]
            per = np.zeros(25)
            for k in ("m1_acc", "m1_up", "m2_acc", "m2_up"):
                per += np.array(mm[k + "_n"]) - np.array(mm[k + "_vs"]) / REF
            per += np.array(mm["ramp1_pending"]) + np.array(mm["ramp2_pending"])
            out.append(per.reshape(5, 5).sum(axis=1))
        return np.array(out)
    bp = blocks("p333"); bl = [blocks(l) for l in L]
    print(f"  5-min blocks, edges 2-4a + ramp queues, v3w minus p333, % of p333's block median (stacked median | mean of paired, pooled arm):")
    for b in range(5):
        ref = np.median(bp[:, b])
        D = np.array([(x[:, b] - bp[:, b]) / ref * 100 for x in bl])
        print(f"    block {b + 1} ({300 + 300 * b}-{600 + 300 * b} s): p333 median {ref:.0f} veh-s | {f(boot_stack(D), 2)} | {f(boot_mean(D.mean(axis=0)), 2)}")
    pp = np.array([np.array(S6[(cell, 'p333')][s]["flow_min"], float) for s in seeds])
    print("  passed per 5-min block, v3w minus p333 (vehicles; stacked median | mean): " + " | ".join(
        f"{f(boot_stack(np.array([np.array([S6[(cell, l)][s]['flow_min'] for s in seeds], float)[:, 5 * b:5 * b + 5].sum(axis=1) - pp[:, 5 * b:5 * b + 5].sum(axis=1) for l in L])), 1)} / {np.mean([np.array([S6[(cell, l)][s]['flow_min'] for s in seeds], float)[:, 5 * b:5 * b + 5].sum(axis=1) - pp[:, 5 * b:5 * b + 5].sum(axis=1) for l in L]):+.2f}" for b in range(5)))
R2T, R2V, R1 = (pickle.load(open(x, "rb")) for x in ("r2t.pkl", "r2v.pkl", "r1.pkl"))
for cell in ("X1", "X2"):
    print(f"\n## {cell} (round 2 test, 40 seeds): p333 or rule minus v3w, veh-s upstream of edge 4 if the window ended at T (positive = v3w better)")
    for opp in ("p333", "os0_10_10", "3ex1" if cell == "X1" else "3ex2"):
        cp = [U(R2T, cell, l, sorted(R2T[(cell, 'p333')])) for l in L]
        co = U(R2T, cell, opp, sorted(R2T[(cell, 'p333')]))
        out = []
        for t_end, k in {600: 4, 900: 9, 1200: 14, 1500: 19, 1800: 24}.items():
            D = np.array([((c - co)[:, :k + 1].sum(axis=1)) * 60.0 for c in cp])
            out.append(f"{t_end} s: {f(boot_stack(D))}")
        D = np.array([(c - co)[:, -1] for c in cp])
        print(f"  {opp:10s} " + " | ".join(out) + f" | v3w extra passed at 1,800 s: {f(boot_stack(D), 1)}")
# null of the pooled-arm statistic in X1 and X2, and collision totals
for nm, T, LL in (("r2t", R2T, L),):
    for cell in ("X1", "X2"):
        seeds = sorted(T[(cell, "p333")])
        A = {l: np.array([T[(cell, l)][s]["all_delay"] for s in seeds]) for l in LL}
        out = [boot((np.mean([A[m] for m in LL if m != l], axis=0) - A[l]) / np.median(A[l]) * 100) for l in LL]
        print(f"\n{cell} {nm}: NULL of the pooled-arm statistic (mean of the other 4 learners minus one learner, % of its median): " + " | ".join(f(e, 2) for e in out) + f" | mean {np.mean([e[0] for e in out]):+.2f}")
print("\n## totals over seeds: collisions, teleports, moving full-emergency events, stuck, dropped, pending at the end (sum)")
for nm, T in (("S6", S6), ("round 2 test", R2T)):
    for (cell, arm), d in sorted(T.items()):
        g = lambda k: sum((r.get(k) or 0) for r in d.values())
        print(f"  {nm} {cell:5s} {arm:11s} n={len(d)} collisions {g('collisions'):.0f} contact_steps {g('contact_steps'):.0f} teleports {g('teleports'):.0f} full_moving {g('alks_full_moving'):.0f} stuck {g('m_stuck_n'):.0f} dropped {g('m_dropped'):.0f} pending_end {g('m_pending_end'):.0f}")
