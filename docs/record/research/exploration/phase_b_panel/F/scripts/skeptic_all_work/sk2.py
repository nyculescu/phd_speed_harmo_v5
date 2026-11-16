"""EXPLORATORY: operating characteristic of screen F's K1 and K2 at 480 verdict seeds, from the stored S6 TRUCK rows. No simulation.
A study = 480 seeds drawn with replacement from the 240 stored seeds; intervals 97.5 % two-sided (percentiles 1.25 / 98.75), B = 1000."""
import numpy as np
S = "/tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/89ba3663-8e1a-45c3-9415-9e2a743fb16b/scratchpad/phaseB"
Z = np.load(f"{S}/critic_F/s6_scalars.npz")
KEYS = list(Z["keys"]); N0 = len(Z["seeds"])
LEARN = ["w0u250", "w1u500", "w2u250", "w3u500", "w4u500"]
col = lambda arm, key: Z[f"TRUCK|{arm}"][:, KEYS.index(key)]
Lc = np.array([col(l, "ttc_net") for l in LEARN]); Ld = np.array([col(l, "all_delay") for l in LEARN])
Pc, Pd = Lc.mean(0), Ld.mean(0)
C1 = "3E-C_TRUCK"
D4 = ["3E-C_TRUCK", "p333", "os0_10_10", "3E-D_TRUCK"]
D9 = D4 + ["grid_os1_10_10", "os1_15_10", "lr1000_16_2", "grid_lr400_13_1", "lr400_13_2", "lr1000_10_1"]
Oc = col(C1, "ttc_net"); Od = {o: col(o, "all_delay") for o in D9}
N, B, ST = 480, 1000, 2000
r = np.random.default_rng(20261122)
med0 = np.median(Oc); base = np.median(-(Pc - Oc))
pe_l0 = np.mean([np.median(-(Lc[i] - Oc)) for i in range(5)])
EDGES = (0.0, 5.0, 8.0, 10.0, 11.0, 12.0, 13.0, 15.0)
res = {m: {e: [] for e in EDGES} for m in ("add", "mul", "learner")}
k2 = {k: [] for k in ("d4_lb", "d9_lb")}
for _ in range(ST):
    s = r.integers(0, N0, N); bi = r.integers(0, N, (B, N))
    m = np.median(Oc[s])
    for e in EDGES:
        # additive: v3w shifted so that the 240-seed pooled statistic equals e
        d = -((Pc[s] + (base - e / 100 * med0)) - Oc[s]) / m * 100
        bb = np.median(d[bi], axis=1)
        res["add"][e].append((np.median(d), np.percentile(bb, 1.25)))
        # multiplicative: v3w scaled so that the 240-seed pooled statistic equals e (found by bisection once, below)
        d = -(Pc[s] * SC[e] - Oc[s]) / m * 100 if 'SC' in globals() else d
        bb = np.median(d[bi], axis=1)
        res["mul"][e].append((np.median(d), np.percentile(bb, 1.25)))
        # learner truth: shift so that the MEAN OF THE 5 SINGLE-LEARNER effects equals e on the 240 seeds; the rule still reads the pooled arm
        d = -((Pc[s] + (pe_l0 - e / 100 * med0)) - Oc[s]) / m * 100
        bb = np.median(d[bi], axis=1)
        res["learner"][e].append((np.median(d), np.percentile(bb, 1.25)))
    lbs = []
    for o in D9:
        d = -(Pd[s] - Od[o][s]) / np.median(Od[o][s]) * 100
        lbs.append(np.percentile(np.median(d[bi], axis=1), 1.25))
    k2["d4_lb"].append(min(lbs[:4])); k2["d9_lb"].append(min(lbs))
print("multiplicative model skipped in pass 1" if 'SC' not in globals() else "")
print(f"## K1 (point < 10 or lower bound <= 0) against {C1}, n = {N}, {ST} studies, B = {B}")
print("true edge | P(KILL) additive shift | alt form (lb <= 0 or < 20 s) | P(KILL) when the stated edge is the mean of the single-learner effects")
for e in EDGES:
    a = np.array(res["add"][e]); l = np.array(res["learner"][e])
    kill = ((a[:, 0] < 10) | (a[:, 1] <= 0)).mean(); alt = (a[:, 1] <= 0).mean()
    kl = ((l[:, 0] < 10) | (l[:, 1] <= 0)).mean()
    print("%5.1f | %.3f | %.3f | %.3f" % (e, kill, alt, kl))
for k, names in (("d4_lb", D4), ("d9_lb", D9)):
    v = np.array(k2[k])
    print(f"K2 at the stored differences, n = {N}: P(lowest lower bound > -1) over {len(names)} rule arms = %.3f; > -2: %.3f" % ((v > -1).mean(), (v > -2).mean()))
