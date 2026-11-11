"""EXPLORATORY: nulls of screen F's side conditions (planb.md:438, decision 9) and of the learner rule, stored S6 TRUCK rows resampled."""
import numpy as np
z = np.load("k4_scalars.npz", allow_pickle=True)
K = list(z["keys"])
ix = {k: K.index(k) for k in K}
LEARN = ["w0u250", "w1u500", "w2u250", "w3u500", "w4u500"]
OPP = ["3E-C_TRUCK", "p333", "os0_10_10", "3E-D_TRUCK"]
L = np.stack([z[f"TRUCK|{n}"] for n in LEARN])      # 5 x 240 x keys
O = {o: z[f"TRUCK|{o}"] for o in OPP}
P = L.mean(axis=0)
n0 = P.shape[0]
rng = np.random.default_rng(20261112)
print("stored, 240 seeds")
for k in ("collisions", "alks_full_moving"):
    print(" ", k, "v3w total", L[:, :, ix[k]].sum(), "of", 5 * n0, "runs;", {o: (float(O[o][:, ix[k]].sum()), round(float((P[:, ix[k]] - O[o][:, ix[k]]).mean()), 4)) for o in OPP})
pe = L[:, :, ix["pending_end"]].ravel()
print("  drain: v3w rows", pe.size, "stuck>0:", int((L[:, :, ix["stuck_n"]] > 0).sum()), "pending_end max", pe.max(), "p99", np.percentile(pe, 99), "p99.9", np.percentile(pe, 99.9), "rows above 20:", int((pe > 20).sum()), "above 30:", int((pe > 30).sum()))
allrules = [f for f in z.files if f.startswith("TRUCK|") and f.split("|")[1] not in LEARN + ["nc"]]
pr = np.concatenate([z[f][:, ix["pending_end"]] for f in allrules])
print("  drain: rule rows", pr.size, "max", pr.max(), "above 39:", int((pr > 39).sum()), "stuck>0:", int(sum((z[f][:, ix["stuck_n"]] > 0).sum() for f in allrules)))
nc = z["TRUCK|nc"][:, ix["pending_end"]]
print("  no control pending_end max", nc.max())

def study(n, B, plant):
    """One resampled study of n seeds; plant = dict of planted changes. Returns fail flags."""
    i = rng.integers(0, n0, n)
    Ls = L[:, i, :].copy()
    q = plant.get("coll", 0.0)
    if q:
        Ls[:, :, ix["collisions"]] += rng.random((5, n)) < q
    q = plant.get("full", 0.0)
    if q:
        Ls[:, :, ix["alks_full_moving"]] += rng.poisson(q, (5, n))
    Ps = Ls.mean(axis=0)
    Ps[:, ix["passed"]] *= 1.0 - plant.get("flow", 0.0) / 100.0
    Ps[:, ix["robust_rate"]] *= 1.0 + plant.get("brake", 0.0) / 100.0
    bi = rng.integers(0, n, (B, n))
    out = {"coll": False, "full": False, "flow": False, "brake": False}
    for o in OPP:
        Os = O[o][i]
        d = Ps[:, ix["collisions"]] - Os[:, ix["collisions"]]
        out["coll"] |= np.percentile(d[bi].mean(axis=1), 95.0) > 0.02
        d = Ps[:, ix["alks_full_moving"]] - Os[:, ix["alks_full_moving"]]
        out["full"] |= np.percentile(d[bi].mean(axis=1), 95.0) > 0.10
        f = (Ps[:, ix["passed"]] - Os[:, ix["passed"]]) / np.median(Os[:, ix["passed"]]) * 100.0
        out["flow"] |= np.median(f) < -0.5
        x = (Ps[:, ix["robust_rate"]] - Os[:, ix["robust_rate"]]) / np.median(Os[:, ix["robust_rate"]]) * 100.0
        out["brake"] |= np.percentile(np.median(x[bi], axis=1), 2.5) > 10.0
    return out

N, B, S = 480, 400, 600
for name, grid, key in (("collisions, planted extra per learner run", (0.0, 0.01, 0.02, 0.03, 0.05), "coll"),
                        ("moving full-emergency, planted extra per learner run", (0.0, 0.05, 0.10, 0.15, 0.20, 0.25), "full"),
                        ("flow, v3w scaled down by %", (0.0, 0.3, 0.6, 0.8, 1.0), "flow"),
                        ("robust braking, v3w scaled up by %", (0.0, 5.0, 10.0, 12.0, 15.0), "brake")):
    res = []
    for g in grid:
        fails = sum(study(N, B, {key: g})[key] for _ in range(S))
        res.append((g, round(fails / S, 3)))
    print(name, "n =", N, "P(condition fails against any of 4 rules):", res)

def learners(n, margin, cf_shift=0.0):
    i = rng.integers(0, n0, n)
    ok = np.ones(5, bool)
    for o in OPP:
        Os = O[o][i]
        for j in range(5):
            c = np.median(-(L[j, i, ix["ttc_net"]] - Os[:, ix["ttc_net"]]) / np.median(Os[:, ix["ttc_net"]]) * 100.0)
            d = np.median(-(L[j, i, ix["all_delay"]] - Os[:, ix["all_delay"]]) / np.median(Os[:, ix["all_delay"]]) * 100.0)
            ok[j] &= (c > 0) and (d > margin)
    return ok.sum() < 4
for margin in (0.0, -1.0, -2.0):
    f = sum(learners(N, margin) for _ in range(2000)) / 2000
    print(f"learner rule with a delay point above {margin} %: fails in {f:.3f} of studies at the stored values, n = {N}")
