"""EXPLORATORY: stage 0 in both statistic forms, steady traffic (S) and TRUCK, from the stored S6 rows (240 seeds, read for a verdict)."""
import numpy as np
Z = np.load("f_scalars.npz")
KEYS = [str(k) for k in Z["keys"]]; N0 = len(Z["seeds"])
LEARN = ["w0u250", "w1u500", "w2u250", "w3u500", "w4u500"]
r = np.random.default_rng(20261133)
IDX = r.integers(0, N0, (10000, N0))
for cell in ("S", "TRUCK"):
    col = lambda arm, key: Z[f"{cell}|{arm}"][:, KEYS.index(key)]
    rules = sorted(f.split("|")[1] for f in Z.files if f.startswith(cell + "|") and f.split("|")[1] not in LEARN + ["nc"])
    out = []
    for o in rules:
        row = [o]
        for key in ("ttc_net", "all_delay"):
            L = np.array([col(l, key) for l in LEARN]); O = col(o, key); S = np.vstack([L.mean(0)[None], L])
            d = -(S - O[None]) / np.median(O) * 100.0
            pts = np.median(d, axis=1)
            bs = np.median(d[:, IDX], axis=2); lm = bs[1:].mean(0)
            row += [pts[0], np.percentile(bs[0], 1.25), np.percentile(bs[0], 98.75), pts[1:].mean(), np.percentile(lm, 1.25), np.percentile(lm, 98.75), pts[1:].min(), pts[1:].max()]
        out.append(row)
    k1P = [x[0] for x in out if x[1] < 10 or x[2] <= 0]; k1L = [x[0] for x in out if x[4] < 10 or x[5] <= 0]
    k2P = [x[0] for x in out if x[10] <= -1]; k2L = [x[0] for x in out if x[13] <= -1]
    print(f"{cell}: K1 fires, pooled form, against {len(k1P)} {k1P}; single-mean form, against {len(k1L)} {k1L}")
    print(f"{cell}: K2 (margin 1 %) fires, pooled form, against {len(k2P)}; single-mean form, against {len(k2L)} {k2L}")
    for x in sorted(out, key=lambda x: x[4])[:5]:
        print("   cf  %-16s pooled %+.2f [%+.2f, %+.2f] | single mean %+.2f [%+.2f, %+.2f] | learners %+.1f..%+.1f" % tuple(x[:9]))
    for x in sorted(out, key=lambda x: x[13])[:6]:
        print("   del %-16s pooled %+.2f [%+.2f, %+.2f] | single mean %+.2f [%+.2f, %+.2f] | learners %+.2f..%+.2f" % ((x[0],) + tuple(x[9:17])))
