"""EXPLORATORY: joint PASS of screen F with the 1 % delay margin, on a finer grid of true edges; stored S6 rows resampled.
Same statistic and shifts as rigor_oc.py."""
import numpy as np
S = "/tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/89ba3663-8e1a-45c3-9415-9e2a743fb16b/scratchpad/phaseB"
Z = np.load(f"{S}/critic_F/s6_scalars.npz"); KEYS = list(Z["keys"]); N0 = len(Z["seeds"])
LEARN = ["w0u250", "w1u500", "w2u250", "w3u500", "w4u500"]
col = lambda arm, key: Z[f"TRUCK|{arm}"][:, KEYS.index(key)]
arm = lambda key: np.mean([col(l, key) for l in LEARN], axis=0)
C = ("3E-C_TRUCK", "3ex1"); DOPP = ["3E-C_TRUCK", "p333", "os0_10_10", "3E-D_TRUCK"]; B = 1000
Pc, Pd = arm("ttc_net"), arm("all_delay")
Oc = [col(o, "ttc_net") for o in C]; Od = [col(o, "all_delay") for o in DOPP]; Lc = np.array([col(l, "ttc_net") for l in LEARN])
base_c = np.array([np.median(-(Pc - o)) for o in Oc]); med_c0 = np.array([np.median(o) for o in Oc])
E = np.arange(0.0, 24.1, 1.0)
for n, studies in ((240, 2000), (480, 2000)):
    r = np.random.default_rng(20261116 + n)
    res = {k: [] for k in ("pt", "lb", "med", "lp", "dlb")}
    for _ in range(studies):
        s = r.integers(0, N0, n); bi = r.integers(0, n, (B, n))
        med = np.array([np.median(o[s]) for o in Oc])
        dc = np.array([-(Pc[s] - o[s]) / m * 100.0 for o, m in zip(Oc, med)])
        bc = np.median(dc[:, bi], axis=2)
        res["pt"].append(np.median(dc, axis=1)); res["lb"].append(np.percentile(bc, 1.25, axis=1)); res["med"].append(med)
        res["lp"].append(np.array([[np.median(-(Lc[k][s] - o[s])) / m * 100.0 for k in range(5)] for o, m in zip(Oc, med)]))
        dd = np.array([-(Pd[s] - o[s]) / np.median(o[s]) * 100.0 for o in Od])
        res["dlb"].append(np.percentile(np.median(dd[:, bi], axis=2), 1.25, axis=1))
    T = {k: np.array(v) for k, v in res.items()}
    ni1, ni2 = (T["dlb"] > -1.0).all(axis=1), (T["dlb"] > -2.0).all(axis=1)
    print(f"\nn = {n}, {studies} studies. Delay within 1 % of all four (as stored): {ni1.mean():.3f}; within 2 %: {ni2.mean():.3f}")
    print("true edge | stage 1 PASS (one opponent; cf rule, learners, delay 1 %) | both stages PASS (second opponent with 3ex1's noise at the same true edge) | cf rule alone, one opp")
    p1, p2 = [], []
    for e in E:
        adj = (base_c - e / 100.0 * med_c0)[None, :] / T["med"] * 100.0
        ok = ((T["pt"] - adj) >= 10.0) & ((T["lb"] - adj) > 0.0) & (((T["lp"] - adj[:, :, None]) > 0).sum(axis=2) >= 4)
        a1, a2 = (ok[:, 0] & ni1).mean(), (ok.all(axis=1) & ni1).mean()
        p1.append(a1); p2.append(a2)
        if e in (0, 5, 8, 10, 11, 12, 13, 15, 20):
            print("%5.1f | %.3f | %.3f | %.3f" % (e, a1, a2, ok[:, 0].mean()))
    w = np.exp(-0.5 * ((E - 11.8) / 3.3) ** 2); w /= w.sum()
    print("judgement aid: true edge against today's 3E-C drawn from N(11.8, 3.3) (the stored point and interval width; not a posterior): stage 1 PASS %.2f" % float((w * np.array(p1)).sum()))
    for mu in (6.0, 8.0, 10.0):
        w2 = np.exp(-0.5 * ((E - mu) / 3.3) ** 2); w2 /= w2.sum()
        print("   if the edge against the continued rule is N(%.0f, 3.3): PASS against it (one opponent curve) %.2f" % (mu, float((w2 * np.array(p1)).sum())))
