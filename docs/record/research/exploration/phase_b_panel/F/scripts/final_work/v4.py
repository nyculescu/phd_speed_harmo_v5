"""EXPLORATORY: nulls of the two statistic forms on rules-only pseudo-arms, the per-policy form of K2, and the location share.
Stored S6 TRUCK rows (240 seeds, already read for a verdict). No simulation."""
import itertools
import numpy as np
Z = np.load("f_scalars.npz")
KEYS = [str(k) for k in Z["keys"]]; N0 = len(Z["seeds"])
LEARN = ["w0u250", "w1u500", "w2u250", "w3u500", "w4u500"]
col = lambda arm, key: Z[f"TRUCK|{arm}"][:, KEYS.index(key)]
TIED = ["os0_10_10", "p333", "grid_os1_10_10", "os1_15_10", "3E-D_TRUCK", "lr1000_16_2", "grid_lr400_13_1", "lr400_13_2"]     # lr1000_10_1 left out: p333's near-twin (V496)
ARMS = ["3E-C_TRUCK", "os0_10_10", "p333", "lr1000_10_1", "grid_os1_10_10", "os1_15_10", "3E-D_TRUCK", "lr1000_16_2", "grid_lr400_13_1", "lr400_13_2"]
N, B = 480, 1000
r = np.random.default_rng(20261132)
# 1. location share of v3w's counted seconds on roads 4a, 4 and ramp 2
tot = np.mean([col(l, "m_ttc3_all") for l in LEARN], axis=0)
loc = np.mean([col(l, "rt_4a") + col(l, "rt_4") + col(l, "rt_ramp2") for l in LEARN], axis=0)
print("1. share of v3w's counted seconds on roads 4a, 4 and ramp 2: ratio of means %.3f, median of per-seed ratios %.3f" % (loc.mean() / tot.mean(), np.median(loc / tot)))
# 2. rules-only placebo: 5 rules as pseudo-learners against a sixth, every pseudo-learner shifted to tie the sixth
combos = [(o, g) for o in TIED for g in itertools.combinations([x for x in TIED if x != o], 5)]
pick = [combos[i] for i in r.choice(len(combos), 24, replace=False)]
ST = 250
for key in ("all_delay", "ttc_net"):
    off, res = [], {k: [] for k in ("P_lb", "L_lb", "P_ub", "L_ub")}
    for o, g in combos:
        O = col(o, key); L = np.array([col(x, key) for x in g]); den = np.median(O)
        off.append(-np.median(L.mean(0) - O) / den * 100 - np.mean([-np.median(L[i] - O) / den * 100 for i in range(5)]))
    off = np.array(off)
    for o, g in pick:
        O = col(o, key); L = np.array([col(x, key) for x in g])
        L = L - np.median(L - O[None], axis=1)[:, None]     # each pseudo-learner now ties the sixth rule exactly on the stored seeds
        S = np.vstack([L.mean(0)[None], L])
        for _ in range(ST):
            s = r.integers(0, N0, N); bi = r.integers(0, N, (B, N))
            d = -(S[:, s] - O[s][None]) / np.median(O[s]) * 100.0
            bs = np.median(d[:, bi], axis=2); lm = bs[1:].mean(0)
            res["P_lb"].append(np.percentile(bs[0], 1.25)); res["P_ub"].append(np.percentile(bs[0], 98.75))
            res["L_lb"].append(np.percentile(lm, 1.25)); res["L_ub"].append(np.percentile(lm, 98.75))
    R = {k: np.array(v) for k, v in res.items()}
    print(f"2. {key}: {len(combos)} pseudo-arms; offset pooled minus mean of singles: median %+.2f, 5th-95th %+.2f to %+.2f, share below 0 %.2f" % (np.median(off), np.percentile(off, 5), np.percentile(off, 95), (off < 0).mean()))
    print(f"   null at n = {N}, {len(pick)} pseudo-arms x {ST} studies, every single tied: pooled form shown worse (upper bound < 0) %.3f, shown better (lower bound > 0) %.3f, lower bound <= -1 %.3f"
          % ((R["P_ub"] < 0).mean(), (R["P_lb"] > 0).mean(), (R["P_lb"] <= -1).mean()))
    print("   single-mean form shown worse %.3f, shown better %.3f, lower bound <= -1 %.3f (nominal 0.0125 per side)" % ((R["L_ub"] < 0).mean(), (R["L_lb"] > 0).mean(), (R["L_lb"] <= -1).mean()))
# 3. K2 in the per-policy form of round_2.md:209: at least 4 of 5 learners with a 97.5 % lower bound above -M against every rule arm
ST3 = 400
Ld = np.array([col(l, "all_delay") for l in LEARN])
lbs = np.zeros((ST3, len(ARMS), 5)); base = np.zeros((len(ARMS), 5)); med0 = np.zeros(len(ARMS)); meds = np.zeros((ST3, len(ARMS)))
for j, o in enumerate(ARMS):
    base[j] = np.median(-(Ld - col(o, "all_delay")[None]), axis=1); med0[j] = np.median(col(o, "all_delay"))
for k in range(ST3):
    s = r.integers(0, N0, N); bi = r.integers(0, N, (B, N))
    for j, o in enumerate(ARMS):
        O = col(o, "all_delay"); m = np.median(O[s]); meds[k, j] = m
        d = -(Ld[:, s] - O[s][None]) / m * 100.0
        lbs[k, j] = np.percentile(np.median(d[:, bi], axis=2), 1.25, axis=1)
print(f"3. per-policy K2, n = {N}, {ST3} studies, 10 rule arms: P(at least 4 of 5 learners above -M against every arm)")
for lab, sh in (("stored differences", lambda j: 0.0), ("every learner ties every arm", lambda j: base[j]), ("every learner 1 % worse", lambda j: base[j] + 0.01 * med0[j]), ("every learner 2 % worse", lambda j: base[j] + 0.02 * med0[j])):
    out = []
    for M in (1.0, 2.0):
        ok = np.ones((ST3, 5), bool)
        for j in range(len(ARMS)):
            shift = np.asarray(sh(j)) / meds[:, j][:, None] * 100.0 if not np.isscalar(sh(j)) else 0.0
            ok &= (lbs[:, j] - shift) > -M
        out.append((ok.sum(1) >= 4).mean())
    print("   %-30s M = 1: %.3f | M = 2: %.3f" % (lab, out[0], out[1]))
