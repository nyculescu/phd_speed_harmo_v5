"""EXPLORATORY: learner rule (close-following point > 0 and delay point > -1 %, 4 of 5, every rule arm) with planted delay deficits."""
import numpy as np
z = np.load("k4_scalars.npz", allow_pickle=True)
K = list(z["keys"]); ix = {k: K.index(k) for k in K}
LEARN = ["w0u250", "w1u500", "w2u250", "w3u500", "w4u500"]
OPP = ["3E-C_TRUCK", "p333", "os0_10_10", "3E-D_TRUCK"]
L = np.stack([z[f"TRUCK|{n}"] for n in LEARN]); O = {o: z[f"TRUCK|{o}"] for o in OPP}
n0 = L.shape[1]; rng = np.random.default_rng(20261113)
stuck = {f: int((z[f][:, ix["stuck_n"]] > 0).sum()) for f in z.files if f.startswith("TRUCK|")}
print("TRUCK arms with stuck rows:", {k: v for k, v in stuck.items() if v})
stuckS = {f: int((z[f][:, ix["stuck_n"]] > 0).sum()) for f in z.files if f.startswith("S|")}
print("S arms with stuck rows:", {k: v for k, v in stuckS.items() if v})
def fails(n, margin, worse):
    i = rng.integers(0, n0, n); ok = np.ones(5, bool)
    for o in OPP:
        Os = O[o][i]; mo = np.median(Os[:, ix["all_delay"]])
        for j in range(5):
            c = np.median(-(L[j, i, ix["ttc_net"]] - Os[:, ix["ttc_net"]]) / np.median(Os[:, ix["ttc_net"]]) * 100.0)
            d = np.median(-(L[j, i, ix["all_delay"]] + worse / 100.0 * mo - Os[:, ix["all_delay"]]) / mo * 100.0)
            ok[j] &= (c > 0) and (d > margin)
    return ok.sum() < 4
for worse in (0.0, 0.5, 1.0, 1.5, 2.0):
    print("every learner's delay made worse by", worse, "% of the rule's median: learner rule (margin -1 %) fails in", sum(fails(480, -1.0, worse) for _ in range(1500)) / 1500)
