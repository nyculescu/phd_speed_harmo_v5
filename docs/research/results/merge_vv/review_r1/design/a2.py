import numpy as np, sys
D = sys.argv[1]
Z = np.load(D + "/cols.npz"); arms = list(Z["arms"]); ix = {a: i for i, a in enumerate(arms)}
V3W = ["E30|w0u250", "E30|w1u500", "E30|w2u250", "E30|w3u500", "E30|w4u500"]
def get(k, a): return Z[k][ix[a]]
def stat(P, R):
    # P: (5, n), R: (n,). mean over learners of median over seeds of -(P-R)/median(R)*100
    return np.mean(np.median(-(P - R) / np.median(R) * 100.0, axis=-1))
def boot(P, R, B=6000, n=None, seed=20261108, lev=(1.25, 98.75, 0.625, 99.375)):
    rng = np.random.default_rng(seed); N = R.shape[0]; n = n or N
    out = np.empty(B)
    for b in range(B):
        j = rng.integers(0, N, n)
        out[b] = stat(P[:, j], R[j])
    return stat(P, R), out.std(ddof=1), np.percentile(out, lev)
def show(lbl, P, R, **kw):
    pt, se, q = boot(P, R, **kw)
    print(f"{lbl:60s} pt {pt:+6.2f} SE {se:5.2f}  97.5% [{q[0]:+.2f}, {q[1]:+.2f}]  98.75% [{q[2]:+.2f}, {q[3]:+.2f}]", flush=True)
    return pt, se
for opp in ("E30|lr400_16_1", "E30|grid_lr400_13_1", "E30|p333", "E30|nc"):
    P = np.array([get("ttc_net", w) for w in V3W]); R = get("ttc_net", opp)
    print("==", opp, "median R", np.median(R), "| mean abs diff (events/run, median of paired, mean over learners):", round(float(np.mean(np.median(R - P, axis=1))), 1))
    show("ttc_net n=480", P, R)
    for n in (240, 160, 120, 80):
        show(f"ttc_net subsample-size n={n} (bootstrap draws of n from 480)", P, R, n=n, B=3000)
    for k in ("m1", "m2", "away", "ttc_half"):
        show(k + " n=480", np.array([get(k, w) for w in V3W]), get(k, opp), B=3000)
    # merge-scaling model: merge close-following multiplied by k in both arms, away and junction unchanged
    for kk in (0.65, 0.34, 0.2, 0.1, 0.02):
        f = lambda a: get("away", a) + get("jn", a) + kk * (get("m1", a) + get("m2", a))
        show(f"model: merges x{kk} both arms", np.array([f(w) for w in V3W]), f(opp), B=3000)
    for k1, k2 in ((1.0, 0.34), (1.0, 0.02)):
        f = lambda a: get("away", a) + get("jn", a) + k1 * get("m1", a) + k2 * get("m2", a)
        show(f"model: merge1 x{k1}, merge2 x{k2}", np.array([f(w) for w in V3W]), f(opp), B=3000)
