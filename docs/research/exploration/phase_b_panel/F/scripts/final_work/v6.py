"""EXPLORATORY: nulls of K4's side conditions (planb.md:438; decision 9) against the 10 rule arms of the final text; stored S6 TRUCK rows
(240 seeds, read for a verdict) resampled to 480. Same planted changes as synth_work/k4_null.py. No simulation."""
import numpy as np
z = np.load("synth_work/k4_scalars.npz", allow_pickle=True)
K = [str(k) for k in z["keys"]]; ix = {k: K.index(k) for k in K}
LEARN = ["w0u250", "w1u500", "w2u250", "w3u500", "w4u500"]
OPP = ["3E-C_TRUCK", "os0_10_10", "p333", "lr1000_10_1", "grid_os1_10_10", "os1_15_10", "3E-D_TRUCK", "lr1000_16_2", "grid_lr400_13_1", "lr400_13_2"]
L = np.stack([z[f"TRUCK|{n}"] for n in LEARN]); O = {o: z[f"TRUCK|{o}"] for o in OPP}; n0 = L.shape[1]
rng = np.random.default_rng(20261134)
print("stored: v3w collisions %d and moving full-emergency events %d in %d runs; per rule arm (collisions, full-emergency) in 240 runs: %s" % (
    L[:, :, ix["collisions"]].sum(), L[:, :, ix["alks_full_moving"]].sum(), 5 * n0, {o: (int(O[o][:, ix["collisions"]].sum()), int(O[o][:, ix["alks_full_moving"]].sum())) for o in OPP}))
def study(n, B, plant):
    i = rng.integers(0, n0, n); Ls = L[:, i, :].copy()
    if plant.get("coll"):
        Ls[:, :, ix["collisions"]] += rng.random((5, n)) < plant["coll"]
    if plant.get("full"):
        Ls[:, :, ix["alks_full_moving"]] += rng.poisson(plant["full"], (5, n))
    Ps = Ls.mean(axis=0)
    Ps[:, ix["passed"]] *= 1.0 - plant.get("flow", 0.0) / 100.0
    Ps[:, ix["robust_rate"]] *= 1.0 + plant.get("brake", 0.0) / 100.0
    bi = rng.integers(0, n, (B, n)); out = {"coll": False, "full": False, "flow": False, "brake": False}
    for o in OPP:
        Os = O[o][i]
        out["coll"] |= np.percentile((Ps[:, ix["collisions"]] - Os[:, ix["collisions"]])[bi].mean(axis=1), 95.0) > 0.02
        out["full"] |= np.percentile((Ps[:, ix["alks_full_moving"]] - Os[:, ix["alks_full_moving"]])[bi].mean(axis=1), 95.0) > 0.10
        out["flow"] |= np.median((Ps[:, ix["passed"]] - Os[:, ix["passed"]]) / np.median(Os[:, ix["passed"]]) * 100.0) < -0.5
        x = (Ps[:, ix["robust_rate"]] - Os[:, ix["robust_rate"]]) / np.median(Os[:, ix["robust_rate"]]) * 100.0
        out["brake"] |= np.percentile(np.median(x[bi], axis=1), 2.5) > 10.0
    return out
N, B, S = 480, 400, 500
base = [study(N, B, {}) for _ in range(S)]
print("n = %d, %d studies, 10 rule arms. At the stored values K4 fires: collisions %.3f, full-emergency %.3f, flow %.3f, braking %.3f, any %.3f" % (
    N, S, *[np.mean([b[k] for b in base]) for k in ("coll", "full", "flow", "brake")], np.mean([any(b.values()) for b in base])))
for name, grid, key in (("planted collisions per learner run", (0.01, 0.02, 0.03), "coll"), ("planted moving full-emergency events per learner run", (0.05, 0.10, 0.15), "full"),
                        ("flow scaled down by %", (0.3, 0.6, 0.8), "flow"), ("robust braking scaled up by %", (5.0, 10.0, 12.0), "brake")):
    print(name, [(g, round(float(np.mean([study(N, B, {key: g})[key] for _ in range(S)])), 3)) for g in grid])
