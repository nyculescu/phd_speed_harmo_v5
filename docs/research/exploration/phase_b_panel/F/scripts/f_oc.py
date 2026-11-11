"""EXPLORATORY: operating characteristic of the draft KILL rules of screen F on the stored S6 TRUCK rows (already read for a verdict).
A study = 240 seeds resampled from the 240 stored ones; v3w's close-following or delay is shifted by a constant so that the 240-seed
statistic against the named opponent equals the stated true value. No traffic simulation."""
import sys
import numpy as np
Z = np.load("f_scalars.npz"); KEYS = list(Z["keys"]); n = len(Z["seeds"])
LEARN = ["w0u250", "w1u500", "w2u250", "w3u500", "w4u500"]
col = lambda arm, key: Z[f"TRUCK|{arm}"][:, KEYS.index(key)]
CF_OPP = ["3E-C_TRUCK", "os0_10_10", "lr400_16_1", "3ex2"]
DL_OPP = ["os0_10_10", "p333", "3E-D_TRUCK", "os1_15_10", "grid_os1_10_10", "lr1000_16_2", "3E-C_TRUCK"]
off = lambda arm: sum(col(arm, f"rt_{r}") for r in ("1", "2", "3a", "3", "5", "ramp1"))
L_cf = np.array([col(l, "ttc_net") for l in LEARN]); L_dl = np.array([col(l, "all_delay") for l in LEARN]); L_off = np.array([off(l) for l in LEARN])
O_cf = {o: col(o, "ttc_net") for o in CF_OPP}; O_dl = {o: col(o, "all_delay") for o in DL_OPP}; O_off = off("3E-C_TRUCK")
M, LEV, NI, FLOOR = 240, 97.5, 2.0, 20.0
A = (100 - LEV) / 2
def lb(d, den, r, B):
    b = np.median(d[r.integers(0, len(d), (B, len(d)))], axis=1) / den * 100
    return np.percentile(b, A)
def run(true_cf=None, true_dl=None, studies=1500, B=800, seed=20261113):
    cf, dl, of = L_cf.copy(), L_dl.copy(), L_off.copy()
    if true_cf is not None:     # shift every learner so that the pooled edge against 3E-C equals true_cf; the off-merge-2 count scales with it
        O = O_cf["3E-C_TRUCK"]
        base = np.median(-(cf.mean(0) - O)) / np.median(O) * 100
        cf = cf + (base - true_cf) / 100 * np.median(O)
        b2 = np.median(-(of.mean(0) - O_off)) / np.median(O_off) * 100
        of = of + (b2 - b2 * true_cf / base) / 100 * np.median(O_off)
    if true_dl is not None:     # shift so that the pooled delay effect against os0_10_10 equals true_dl (negative = v3w worse)
        O = O_dl["os0_10_10"]
        base = np.median(-(dl.mean(0) - O)) / np.median(O) * 100
        dl = dl + (base - true_dl) / 100 * np.median(O)
    r = np.random.default_rng(seed)
    k = dict(K1=0, K2=0, K3=0, any=0, G=0)
    for _ in range(studies):
        s = r.integers(0, n, M)
        P_cf, P_dl = cf[:, s].mean(0), dl[:, s].mean(0)
        k1 = any(lb(-(P_dl - O_dl[o][s]), np.median(O_dl[o][s]), r, B) <= -NI for o in DL_OPP)
        k2 = False
        for o in CF_OPP:
            d = -(P_cf - O_cf[o][s])
            if np.median(d) < FLOOR or lb(d, np.median(O_cf[o][s]), r, B) <= 0:
                k2 = True
                break
        good = 0
        for i in range(5):
            ok = all(np.median(-(cf[i, s] - O_cf[o][s])) > 0 for o in CF_OPP) and all(np.median(-(dl[i, s] - O_dl[o][s])) / np.median(O_dl[o][s]) * 100 > -NI for o in DL_OPP)
            good += ok
        k3 = good < 4
        g = lb(-(of[:, s].mean(0) - O_off[s]), np.median(O_off[s]), r, B) <= 0
        k["K1"] += k1; k["K2"] += k2; k["K3"] += k3; k["any"] += (k1 or k2 or k3); k["G"] += g
    return {a: b / studies for a, b in k.items()}
out = lambda t, d: print("%-34s P(K1 delay) %.3f | P(K2 edge) %.3f | P(K3 learners) %.3f | P(KILL) %.3f | P(guard fails) %.3f" % (t, d["K1"], d["K2"], d["K3"], d["any"], d["G"]), flush=True)
out("recorded effects, no shift", run())
for t in (0.0, 5.0, 8.0, 10.0, 12.0, 15.0, 20.0):
    out("true edge vs closest rule %4.1f %%" % t, run(true_cf=t))
for t in (0.0, -1.0, -1.5, -2.0, -3.0):
    out("true delay vs os0_10_10 %+4.1f %%" % t, run(true_dl=t))
