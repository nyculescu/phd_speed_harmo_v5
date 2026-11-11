"""EXPLORATORY: time profile of delay on the merge edges, and p333's delay on seeds where merge 2 did not break down."""
import pickle
import numpy as np
T = pickle.load(open("comp.pkl", "rb"))
REF = 100.0 / 3.6
seeds = list(range(7480400, 7480640)); n = len(seeds)
IDX = np.random.default_rng(20261110).integers(0, n, (10_000, n))
LEARN = ["w0u250", "w1u500", "w2u250", "w3u500", "w4u500"]
def md(d):
    b = np.median(d[IDX], axis=1); lo, hi = np.percentile(b, (2.5, 97.5)); return "%+.0f [%+.0f, %+.0f]" % (np.median(d), lo, hi)
def ser(cell, arm, key): return np.array([T[(cell, arm)][s]["minute"][key] for s in seeds], float)
def sc(cell, arm, k): return np.array([float(T[(cell, arm)][s][k]) for s in seeds])
PART = {"edge 2": "m1_up", "3a": "m1_acc", "edge 3": "m2_up", "4a": "m2_acc"}
for cell in ("S", "TRUCK"):
    print("#####", cell)
    D = {}
    for arm in ("nc", "p333", "v3w"):
        arms = LEARN if arm == "v3w" else [arm]
        for nm, p in PART.items():
            d = np.mean([ser(cell, a, p + "_n") - ser(cell, a, p + "_vs") / REF for a in arms], axis=0)     # veh-s of delay per minute
            D[(arm, nm)] = d
        tot = sum(D[(arm, nm)] for nm in PART)
        print(f" {arm}: delay veh-s per 5-min block (median over seeds), window minutes 0-5 .. 20-25:")
        for nm in PART:
            print(f"    {nm}: " + " ".join("%.0f" % np.median(D[(arm, nm)][:, i:i + 5].sum(1)) for i in range(0, 25, 5)) + f" | total {np.median(D[(arm, nm)].sum(1)):.0f}")
        print("    four edges: " + " ".join("%.0f" % np.median(tot[:, i:i + 5].sum(1)) for i in range(0, 25, 5)))
    print(" paired p333 - v3w per block, four edges together:", " | ".join(md((sum(D[('p333', nm)] for nm in PART) - sum(D[('v3w', nm)] for nm in PART))[:, i:i + 5].sum(1)) for i in range(0, 25, 5)))
    print(" paired p333 - v3w per block, 4a:", " | ".join(md((D[('p333', '4a')] - D[('v3w', '4a')])[:, i:i + 5].sum(1)) for i in range(0, 25, 5)))
    # breakdown conditioning, p333
    for arm in ("p333", "nc"):
        v4 = ser(cell, arm, "m2_acc_vs") / np.maximum(ser(cell, arm, "m2_acc_n"), 1) * 3.6
        slow = (v4 < 60).sum(1)
        ad = sc(cell, arm, "all_delay"); pw = sc(cell, arm, "m_planned_window")
        per = ad / pw
        print(f" {arm}: minutes with 4a < 60 km/h: quartiles {np.percentile(slow, (0, 25, 50, 75, 100))}")
        for lo, hi in ((0, 0), (1, 5), (6, 12), (13, 25)):
            m = (slow >= lo) & (slow <= hi)
            if m.sum():
                print(f"    slow minutes {lo}-{hi}: {m.sum()} seeds; all_delay median {np.median(ad[m]):.0f} veh-s, per planned vehicle {np.median(per[m]):.1f} s; planned median {np.median(pw[m]):.0f}; passed - planned median {np.median(sc(cell, arm, 'passed')[m] - pw[m]):+.0f}")
        X = np.column_stack([np.ones(n), pw - pw.mean(), slow])
        b, *_ = np.linalg.lstsq(X, ad, rcond=None)
        r2 = 1 - ((ad - X @ b) ** 2).sum() / ((ad - ad.mean()) ** 2).sum()
        print(f"    least squares all_delay = {b[0]:.0f} + {b[1]:.0f} x (planned - mean) + {b[2]:.0f} x slow minutes; R2 {r2:.2f}; intercept / mean all_delay = {100*b[0]/ad.mean():.1f} %; mean {ad.mean():.0f}")
        print(f"    correlation planned vs slow minutes {np.corrcoef(pw, slow)[0,1]:.2f}; planned vs all_delay {np.corrcoef(pw, ad)[0,1]:.2f}")
