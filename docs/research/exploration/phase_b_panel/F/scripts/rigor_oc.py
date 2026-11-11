"""EXPLORATORY: null and power of screen F's rules from the stored S6 rows (already read for a verdict). No simulation of traffic.
Statistic as planb.md:424: effect = -median(P - O) / median(O) * 100, P the per-seed mean of the 5 learners, percentile bootstrap,
denominator fixed inside the bootstrap. A study = n seeds drawn with replacement from the 240 stored seeds."""
import sys
import numpy as np

S = "/tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/89ba3663-8e1a-45c3-9415-9e2a743fb16b/scratchpad/phaseB"
Z = np.load(f"{S}/critic_F/s6_scalars.npz")
KEYS = list(Z["keys"])
N0 = len(Z["seeds"])
LEARN = ["w0u250", "w1u500", "w2u250", "w3u500", "w4u500"]
col = lambda cell, arm, key: Z[f"{cell}|{arm}"][:, KEYS.index(key)]
arm = lambda cell, key: np.mean([col(cell, l, key) for l in LEARN], axis=0)
STUDIES, B = int(sys.argv[1]) if len(sys.argv) > 1 else 3000, 1000
C1, C2 = "3E-C_TRUCK", sys.argv[2] if len(sys.argv) > 2 else "3ex1"
DOPP = ["3E-C_TRUCK", "p333", "os0_10_10", "3E-D_TRUCK"]

rng0 = np.random.default_rng(20261112)
IDX0 = rng0.integers(0, N0, (20000, N0))


def eff(P, O, lo=1.25, hi=98.75):
    d = -(P - O) / np.median(O) * 100.0
    b = np.median(d[IDX0], axis=1)
    return float(np.median(d)), float(np.percentile(b, lo)), float(np.percentile(b, hi)), float(d.std(ddof=1))


print("## Stored rows, 240 seeds, 97.5 % intervals, last value = SD of the paired difference in % of the opponent median")
for cell in ("TRUCK", "S"):
    for o in (C1, C2, "p333"):
        print(cell, "cf arm vs", o, "%+.2f [%+.2f, %+.2f] SD %.1f" % eff(arm(cell, "ttc_net"), col(cell, o, "ttc_net")))
    per = [eff(col(cell, l, "ttc_net"), col(cell, C1, "ttc_net"))[0] for l in LEARN]
    print(cell, "cf per learner vs", C1, " ".join("%+.2f" % p for p in per), "mean %+.2f" % np.mean(per))
    for o in DOPP:
        print(cell, "delay arm vs", o, "%+.2f [%+.2f, %+.2f] SD %.2f" % eff(arm(cell, "all_delay"), col(cell, o, "all_delay")))
dT = {o: arm("TRUCK", "ttc_net") - col("TRUCK", o, "ttc_net") for o in ("3E-C_TRUCK", "3e", "3ex1", "3ex2", "3E-D_TRUCK", "grid_os1_10_10")}
print("correlation of the per-seed cf difference (v3w - rule) with the one against 3E-C_TRUCK:",
      {o: round(float(np.corrcoef(dT["3E-C_TRUCK"], d)[0, 1]), 2) for o, d in dT.items()})
print("correlation of the rules' own cf per seed with 3E-C_TRUCK:",
      {o: round(float(np.corrcoef(col("TRUCK", "3E-C_TRUCK", "ttc_net"), col("TRUCK", o, "ttc_net"))[0, 1]), 2) for o in ("3e", "3ex1", "3ex2", "3E-D_TRUCK", "p333")})

# label-swap null of "lower bound > 0" on the stored rows (planb.md:484-486 form), v3w arm against 3E-C_TRUCK
P, O = arm("TRUCK", "ttc_net"), col("TRUCK", C1, "ttc_net")
r = np.random.default_rng(20261113)
hit = 0
SW = 2000
for _ in range(SW):
    f = r.random(N0) < 0.5
    p, o = np.where(f, O, P), np.where(f, P, O)
    d = -(p - o) / np.median(o) * 100.0
    b = np.median(d[r.integers(0, N0, (1000, N0))], axis=1)
    hit += np.percentile(b, 1.25) > 0
print("\nlabel-swap null, cf, TRUCK, v3w arm vs 3E-C_TRUCK, 240 seeds: false 'lower bound > 0' in %.2f %% of %d swaps (nominal 1.25 %%)" % (100 * hit / SW, SW))


def study_block(n, studies):
    """Per study: points and bootstrap bounds for cf (arm vs C1, C2), cf points per learner, delay (arm vs DOPP)."""
    r = np.random.default_rng(20261114 + n)
    Pc, Pd = arm("TRUCK", "ttc_net"), arm("TRUCK", "all_delay")
    Oc = {o: col("TRUCK", o, "ttc_net") for o in (C1, C2)}
    Od = {o: col("TRUCK", o, "all_delay") for o in DOPP}
    Lc = np.array([col("TRUCK", l, "ttc_net") for l in LEARN])
    out = {k: [] for k in ("cf_pt", "cf_lb", "cf_ub", "cf_med", "l_pt", "d_pt", "d_lb", "d_med")}
    for _ in range(studies):
        s = r.integers(0, N0, n)
        bi = r.integers(0, n, (B, n))
        med_c = np.array([np.median(Oc[o][s]) for o in (C1, C2)])
        dc = np.array([-(Pc[s] - Oc[o][s]) / m * 100.0 for o, m in zip((C1, C2), med_c)])
        bc = np.median(dc[:, bi], axis=2)
        out["cf_pt"].append(np.median(dc, axis=1)); out["cf_lb"].append(np.percentile(bc, 1.25, axis=1)); out["cf_ub"].append(np.percentile(bc, 98.75, axis=1))
        out["cf_med"].append(med_c)
        out["l_pt"].append(np.array([[np.median(-(Lc[k][s] - Oc[o][s])) / m * 100.0 for k in range(5)] for o, m in zip((C1, C2), med_c)]))
        med_d = np.array([np.median(Od[o][s]) for o in DOPP])
        dd = np.array([-(Pd[s] - Od[o][s]) / m * 100.0 for o, m in zip(DOPP, med_d)])
        bd = np.median(dd[:, bi], axis=2)
        out["d_pt"].append(np.median(dd, axis=1)); out["d_lb"].append(np.percentile(bd, 1.25, axis=1)); out["d_med"].append(med_d)
    return {k: np.array(v) for k, v in out.items()}


Pc, Pd = arm("TRUCK", "ttc_net"), arm("TRUCK", "all_delay")
base_c = np.array([np.median(-(Pc - col("TRUCK", o, "ttc_net"))) for o in (C1, C2)])     # seconds per run, positive = v3w fewer
med_c0 = np.array([np.median(col("TRUCK", o, "ttc_net")) for o in (C1, C2)])
base_d = np.array([np.median(-(Pd - col("TRUCK", o, "all_delay"))) for o in DOPP])
med_d0 = np.array([np.median(col("TRUCK", o, "all_delay")) for o in DOPP])
EDGES = (0.0, 5.0, 8.0, 10.0, 12.0, 15.0, 20.0)
for n in (80, 240, 360, 480):
    st = max(1000, STUDIES if n <= 240 else STUDIES * 2 // 3)
    T = study_block(n, st)
    print(f"\n## n = {n} verdict seeds, {st} studies, B = {B}, 97.5 % intervals; second opponent stand-in = {C2}")
    print("true cf edge % | KILL-A one opp | KILL-A two opps | part: point<10 | part: lb<=0 | KILL-B (lb<=0 or <20 s/run) one opp | learner cond fails (one opp) | SD of point | mean upper bound minus point")
    for e in EDGES:
        sh = (base_c - e / 100.0 * med_c0)     # seconds added to v3w so that the 240-seed statistic equals e against each opponent
        adj = sh[None, :] / T["cf_med"] * 100.0
        pt, lb, ub = T["cf_pt"] - adj, T["cf_lb"] - adj, T["cf_ub"] - adj
        a = (pt < 10.0) | (lb <= 0.0)
        bq = (lb <= 0.0) | (pt / 100.0 * T["cf_med"] < 20.0)
        lp = T["l_pt"] - adj[:, :, None]
        lfail = (lp > 0).sum(axis=2) < 4
        print("%5.1f | %.3f | %.3f | %.3f | %.3f | %.3f | %.3f | %.2f | %.2f" % (e, a[:, 0].mean(), a.any(axis=1).mean(), (pt[:, 0] < 10).mean(), (lb[:, 0] <= 0).mean(),
              bq[:, 0].mean(), lfail[:, 0].mean(), pt[:, 0].std(), (ub[:, 0] - pt[:, 0]).mean()))
    print("delay non-inferiority, P(lower bound > -margin) at 97.5 %; opponents " + ", ".join(DOPP))
    print("true v3w delay effect % (same against each; 'stored' = unshifted) | margin 1: each opp, all | margin 2: each opp, all | SD of point per opp")
    for t in ("stored", 0.0, -0.5, -1.0, -2.0):
        if t == "stored":
            adj = np.zeros_like(T["d_pt"])
        else:
            adj = (base_d - t / 100.0 * med_d0)[None, :] / T["d_med"] * 100.0
        lb = T["d_lb"] - adj
        row = []
        for mg in (1.0, 2.0):
            ok = lb > -mg
            row.append(" ".join("%.3f" % v for v in ok.mean(axis=0)) + " all %.3f" % ok.all(axis=1).mean())
        print(str(t).rjust(6), "|", row[0], "|", row[1], "|", " ".join("%.2f" % v for v in (T["d_pt"] - adj).std(axis=0)))
    print("joint PASS (cf rule A against both opponents, learner condition against both, delay within 2 % of all four as stored):")
    okd = (T["d_lb"] > -2.0).all(axis=1)
    for e in EDGES:
        sh = (base_c - e / 100.0 * med_c0)
        adj = sh[None, :] / T["cf_med"] * 100.0
        pt, lb = T["cf_pt"] - adj, T["cf_lb"] - adj
        a = ((pt >= 10.0) & (lb > 0.0)).all(axis=1)
        lok = (((T["l_pt"] - adj[:, :, None]) > 0).sum(axis=2) >= 4).all(axis=1)
        a1 = ((pt >= 10.0) & (lb > 0.0))[:, 0] & (((T["l_pt"] - adj[:, :, None]) > 0).sum(axis=2) >= 4)[:, 0] & okd
        print("  true edge %4.1f: PASS %.3f (stage 1 alone, one opponent: %.3f)" % (e, (a & lok & okd).mean(), a1.mean()))

# steady traffic: interval width of the cf effect against 3E-C_TRUCK when the stored S rows are resampled to n seeds
print("\n## S (steady): half-width of the 97.5 % interval of the cf effect against 3E-C_TRUCK, stored rows resampled to n")
r = np.random.default_rng(20261115)
P, O = arm("S", "ttc_net"), col("S", C1, "ttc_net")
for n in (240, 480, 960):
    w = []
    for _ in range(400):
        s = r.integers(0, N0, n)
        d = -(P[s] - O[s]) / np.median(O[s]) * 100.0
        b = np.median(d[r.integers(0, n, (B, n))], axis=1)
        w.append((np.percentile(b, 98.75) - np.percentile(b, 1.25)) / 2)
    print(n, "median half-width %.1f points" % np.median(w))
