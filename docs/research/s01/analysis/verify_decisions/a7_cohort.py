"""D9 proxy: departure time of main.<i> rebuilt from rng(seed) (fleet.FleetDemand: exponential gaps 3600/q over [0, 1800),
rounded up to 0.1 s); v3w and os1_15_10 share3 X1 minus X2 per 60-s departure bin; the climb confound check (p333 same bins)."""
import math, numpy as np
from base import *
ST = "/home/catalin/work/phd/v5b1_runs/measure_s01_remote/st/"
rows, T = load()
def deps(seed, q=5300.0):
    rng = np.random.default_rng(seed); t = 0.0; out = []
    while True:
        t += rng.exponential(3600.0 / q)
        if t >= 1800.0: break
        out.append(round(math.ceil(t / 0.1 - 1e-9) * 0.1, 3))
    return np.array(out)
DEP = {s: deps(s) for s in T[("X1", "nc", 5300.0)]}
gaps = []
for s, r in T[("X1", "p333", 5300.0)].items():
    ids = np.load(ST + r["m_st_file"])["dec_ids"]; mi = max(int(x.split(".")[1]) for x in ids)
    gaps.append(len(DEP[s]) - 1 - mi)
print("departures per seed med", np.median([len(d) for d in DEP.values()]), "; last departure index minus highest ALKS index: min", min(gaps), "max", max(gaps))
BINS = [(360, 420), (540, 600), (1080, 1140), (1380, 1440), (0, 240)]
def share_bin(r, s, b):
    z = np.load(ST + r["m_st_file"]); idx = np.array([int(x.split(".")[1]) for x in z["dec_ids"]]); t = DEP[s][idx]
    m = (t >= b[0]) & (t < b[1]); L = z["dec_level_s"][m, :4].sum(0)
    return L[3] / L.sum() if L.sum() else np.nan
for gname, names in [("v3w", ARMS["v3w"]), ("os1_15_10", ["os1_15_10"]), ("p333", ["p333"])]:
    out = []
    for b in BINS:
        A = arm_series(T, "X1", names, 5300.0, lambda r, b=b: share_bin(r, r["seed"], b))
        B = arm_series(T, "X2", names, 5300.0, lambda r, b=b: share_bin(r, r["seed"], b))
        d, _ = paired_diff(A, B); out.append(f"{b[0]}-{b[1]}: {fmt(d)}")
    print(gname, "; ".join(out))
