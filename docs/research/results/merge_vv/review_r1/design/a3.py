import numpy as np, sys
from math import erf, sqrt
D = sys.argv[1]
Z = np.load(D + "/cols.npz"); arms = list(Z["arms"]); ix = {a: i for i, a in enumerate(arms)}
V3W = ["E30|w0u250", "E30|w1u500", "E30|w2u250", "E30|w3u500", "E30|w4u500"]
def get(k, a): return Z[k][ix[a]]
Phi = lambda x: 0.5 * (1 + erf(x / sqrt(2)))
def boot(P, R, B=8000, n=None, seed=20261108):
    """protocol form: denominator = full-sample median of the opponent, fixed over resamples (read_c1.diffs, moe)"""
    d = -(P - R) / max(np.median(R), 1e-9) * 100.0
    rng = np.random.default_rng(seed); N = R.shape[0]; n = n or N
    idx = rng.integers(0, N, (B, n))
    b = np.mean([np.median(x[idx], axis=1) for x in d], axis=0)
    return float(np.mean(np.median(d, axis=1))), b
def show(lbl, P, R, **kw):
    pt, b = boot(P, R, **kw); se = b.std()
    q = np.percentile(b, (1.25, 98.75, 0.625, 99.375))
    print(f"{lbl:52s} pt {pt:+6.2f} SE {se:5.2f} 97.5% [{q[0]:+6.2f},{q[1]:+6.2f}] 98.75% [{q[2]:+6.2f},{q[3]:+6.2f}] P(lb>0) boot-shift 97.5%: {np.mean(b - (pt - q[0]) * 0 > 0 if False else (2 * pt - b) * 0 + b - (pt - q[0]) > 0):.2f}", flush=True)
    return pt, se
for opp in ("E30|lr400_16_1", "E30|grid_lr400_13_1"):
    P = np.array([get("ttc_net", w) for w in V3W]); R = get("ttc_net", opp)
    print("==", opp)
    for n in (480, 320, 240, 160, 120):
        pt, se = show(f"ttc_net n={n}", P, R, n=n)
        for true in (pt, 5.0):
            print(f"      normal approx power P(lower>0 | true {true:+.1f}): z=2.24 (97.5%) {Phi(true / se - 2.2414):.3f}; z=2.50 (98.75%) {Phi(true / se - 2.4977):.3f}")
    for k in ("m1", "m2", "away", "ttc_half"):
        show(k + " n=480", np.array([get(k, w) for w in V3W]), get(k, opp))
    mm = lambda a: get("m1", a) + get("m2", a)
    show("merges (m1+m2) n=480", np.array([mm(w) for w in V3W]), mm(opp))
    nl = lambda a: get("ttc_net", a) - get("ttc3_lc", a)
    show("not within LC window n=480", np.array([nl(w) for w in V3W]), nl(opp))
    show("within LC window n=480", np.array([get("ttc3_lc", w) for w in V3W]), get("ttc3_lc", opp))
    # 1 Hz at phase 0 against phase 0.5: paired difference of the two edges
    d1 = -(P - R) / np.median(R) * 100; H = np.array([get("ttc_half", w) for w in V3W]); RH = get("ttc_half", opp); d2 = -(H - RH) / np.median(RH) * 100
    rng = np.random.default_rng(1); idx = rng.integers(0, 480, (8000, 480))
    bd = np.mean([np.median(x[idx], axis=1) for x in d2], axis=0) - np.mean([np.median(x[idx], axis=1) for x in d1], axis=0)
    print(f"edge(ttc_half) - edge(ttc_net), same runs: pt {np.mean(np.median(d2, axis=1)) - np.mean(np.median(d1, axis=1)):+.2f} SE {bd.std():.2f} 95% [{np.percentile(bd, 2.5):+.2f},{np.percentile(bd, 97.5):+.2f}]")
    r = [np.corrcoef(get("ttc_net", a), get("ttc_half", a))[0, 1] for a in V3W + [opp]]
    print("corr(ttc_net, ttc_half) per arm:", np.round(r, 4), "| ratio of sums half/net:", [round(float(get('ttc_half', a).sum() / get('ttc_net', a).sum()), 4) for a in V3W + [opp]])
    for kk in (0.65, 0.34, 0.2, 0.1, 0.02):
        f = lambda a: get("away", a) + get("jn", a) + kk * (get("m1", a) + get("m2", a))
        pt, se = show(f"model: merges x{kk} both arms", np.array([f(w) for w in V3W]), f(opp))
        print(f"      median opp count {np.median(f(opp)):.0f}; normal power P(lb>0): z2.24 {Phi(pt / se - 2.2414):.2f} z2.50 {Phi(pt / se - 2.4977):.2f}; P(ub<0): z2.50 {Phi(-pt / se - 2.4977):.2f}")
# stop gate inputs
print("== lane-end stopped vehicle-seconds at 300 m in E30 (end_stop + end_stop2), per arm: median, mean, p10, p90")
for a in V3W + ["E30|lr400_16_1", "E30|grid_lr400_13_1", "E30|p333", "E30|nc"]:
    s = get("end_stop", a) + get("end_stop2", a)
    print(a.ljust(22), np.median(s), round(s.mean(), 1), np.percentile(s, [10, 90]), "| merge1 median", np.median(get("end_stop", a)), "merge2 median", np.median(get("end_stop2", a)), "| 20 % of median:", round(0.2 * np.median(s), 1))
