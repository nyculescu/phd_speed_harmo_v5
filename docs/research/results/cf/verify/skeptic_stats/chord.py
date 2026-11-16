import sys, numpy as np
z = np.load(sys.argv[1]); A, arms, keys = z["A"], list(z["arms"]), list(z["keys"])
col = lambda a, k: A[arms.index(a), :, keys.index(k)]
V = ["w0u250", "w1u500", "w2u250", "w3u500", "w4u500"]; n = A.shape[1]; pct = (1.25, 98.75)
def chord(q, r, idx):
    P = [col(w, "all_delay") for w in V]; Qd, Rd = col(q, "all_delay"), col(r, "all_delay")
    mqb = np.mean([np.median((p - Qd)[idx], axis=1) for p in P], axis=0)
    mrb = np.mean([np.median((Rd - p)[idx], axis=1) for p in P], axis=0)
    s = mqb + mrb; wb = np.clip(np.where(s == 0, .5, mqb / np.where(s == 0, 1, s)), 0, 1)
    Qc, Rc = col(q, "ttc_net"), col(r, "ttc_net"); mdq, mdr = np.median(Qc), np.median(Rc)
    cb = ((1 - wb) * mdq + wb * mdr)[:, None]; Mb = (1 - wb)[:, None] * Qc[idx] + wb[:, None] * Rc[idx]
    b = np.mean([np.median(-(col(w, "ttc_net")[idx] - Mb) / cb * 100, axis=1) for w in V], axis=0)
    return np.percentile(b, pct), np.mean(wb == 1), np.mean(wb == 0)
for seed in (20261108, 424242, 777001):
    idx = np.random.default_rng(seed).integers(0, n, (20000, n))
    for q, r in (("lr400_16_1", "os1_10_0"), ("lr400_16_1", "nc")):
        ci, w1, w0 = chord(q, r, idx)
        print(seed, q, r, np.round(ci, 2), "share w=1", round(w1, 4), "w=0", round(w0, 4))
