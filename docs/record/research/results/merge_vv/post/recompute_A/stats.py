"""Recomputer A: V2 and V3 readings of merge_vv.md from the screen rows, written from the plan text only."""
import json, sys
import numpy as np

LEARNERS = ["w0u250", "w1u500", "w2u250", "w3u500", "w4u500"]
RULES = ["lr400_16_1", "grid_lr400_13_1"]
OTHERS = ["p333", "nc"]
B, SEED = 20000, 20261108
SEEDS = np.arange(7492000, 7492480)

R = json.load(open("runs.json"))
tab = {}
for r in R:
    tab[(r["L"], r["arm"], r["seed"])] = r


def vec(L, arm, key):
    out = []
    for s in SEEDS:
        r = tab[(L, arm, int(s))]
        if key == "ttc_ex1":
            v = r["ttc_net"] - r["e1"]
        else:
            v = r[key]
        if v is None:
            # a counter that never fired leaves no key; only valid when the run had no close-following at all
            assert r["ttc_net"] == 0, (L, arm, s, key)
            v = 0.0
        out.append(float(v))
    return np.array(out)


def edges(L, rule, key):
    """Per-seed edges e[l, s] = (R_s - P_ls) / median(R) * 100, full-sample median of the rule."""
    Rv = vec(L, rule, key)
    med = np.median(Rv)
    P = np.stack([vec(L, l, key) for l in LEARNERS])
    if med == 0:
        return None, med
    return (Rv[None, :] - P) / med * 100.0, med


def stat(e):
    return float(np.mean(np.median(e, axis=1)))


rng = np.random.default_rng(SEED)
IDX = rng.integers(0, len(SEEDS), size=(B, len(SEEDS)))


def boot(e):
    """Statistic on every joint seed resample (same IDX for all comparisons)."""
    out = np.empty(B)
    step = 2000
    for i in range(0, B, step):
        sub = e[:, IDX[i:i + step]]          # learners x step x n
        out[i:i + step] = np.median(sub, axis=2).mean(axis=0)
    return out


def pct(x, lo, hi):
    a, b = np.percentile(x, [lo, hi])
    return [float(a), float(b)]


res = {"conventions": "e = (R - P)/median_full(R)*100; stat = mean over 5 learners of median over seeds; joint resamples B=20000, numpy default_rng(20261108).integers(0,480,(B,480)); percentiles numpy linear"}
store = {}


def reading(name, L, rule, key):
    e, med = edges(L, rule, key)
    if e is None:
        res[name] = {"point": None, "rule_median": med}
        return None
    bs = boot(e)
    store[name] = (e, bs)
    res[name] = {"point": stat(e), "rule_median": float(med),
                 "per_learner": [float(x) for x in np.median(e, axis=1)],
                 "ci95": pct(bs, 2.5, 97.5), "ci97_5": pct(bs, 1.25, 98.75), "ci98_75": pct(bs, 0.625, 99.375),
                 "se": float(bs.std(ddof=1))}
    return e, bs


for rule in RULES + OTHERS:
    # V2: 0.1-s and 1-Hz edges on the same 300-m runs, and their difference on joint resamples
    e01 = reading(f"V2_edge_0.1s|{rule}", "L300", rule, "vv_m_time")
    e1 = reading(f"V2_edge_1Hz|{rule}", "L300", rule, "ttc_net")
    if e01 and e1:
        d = e01[1] - e1[1]
        res[f"V2_diff|{rule}"] = {"point": stat(e01[0]) - stat(e1[0]), "ci95": pct(d, 2.5, 97.5)}
    # V3a replication and main-lane sensitivity, V3b at 600 m
    a = reading(f"V3a_ttc_net_300|{rule}", "L300", rule, "ttc_net")
    reading(f"V3a_main_300|{rule}", "L300", rule, "main")
    b = reading(f"V3b_ttc_net_600|{rule}", "L600", rule, "ttc_net")
    if a and b:
        c = b[1] - a[1]
        res[f"V3b_change|{rule}"] = {"point": stat(b[0]) - stat(a[0]), "ci95": pct(c, 2.5, 97.5)}
    # printed: edges without edge-1 samples, by road group, per merge
    for L in ("L300", "L600"):
        reading(f"ex_edge1_{L}|{rule}", L, rule, "ttc_ex1")
        for g in ("merge", "e1", "rest", "m1", "m2", "main"):
            if g == "main" and L == "L300":
                continue
            reading(f"group_{g}_{L}|{rule}", L, rule, g)

# V2 decision
v2 = [res.get(f"V2_diff|{r}") for r in RULES]
res["V2_reading"] = "MET" if all(x and -3 <= x["ci95"][0] and x["ci95"][1] <= 3 for x in v2) else "LIMIT"
# V2 missed share per arm: (0.1-s time - 1-Hz count * 1 s) / 0.1-s time
ms = {}
for arm in LEARNERS + RULES + OTHERS:
    t01 = vec("L300", arm, "vv_m_time"); c1 = vec("L300", arm, "ttc_net")
    ms[arm] = {"pooled_sums": float((t01.sum() - c1.sum()) / t01.sum()),
               "median_of_runs": float(np.median([(a - b) / a for a, b in zip(t01, c1) if a > 0])),
               "runs_t01_zero": int((t01 == 0).sum())}
res["V2_missed_share"] = ms

# Readings without nulls (null columns are filled by nulls.py)
rep = [res[f"V3a_ttc_net_300|{r}"]["ci97_5"][0] > 0 for r in RULES]
res["V3a_replication_bounds_only"] = "REPLICATED" if all(rep) else "NOT REPLICATED"
mn = [res[f"V3a_main_300|{r}"]["ci97_5"][0] > 0 for r in RULES]
res["V3a_main_bounds_only"] = {r: ("shown" if m else "not shown") for r, m in zip(RULES, mn)}
holds = all(res[f"V3b_ttc_net_600|{r}"]["ci97_5"][0] > 0 for r in RULES)
worse = {r: res[f"V3b_ttc_net_600|{r}"]["ci98_75"][1] < 0 for r in RULES}
res["V3b_bounds_only"] = "HOLDS" if holds else ("WORSE" if any(worse.values()) else "NOT SHOWN")
res["V3b_worse_by_rule"] = worse

# Lane-end standing per arm and merge: cut = 1 - mean600 / mean300 (seeds resampled jointly); median version too
stand = {}
for arm in LEARNERS + RULES + OTHERS + ["v3w_pooled", "all9"]:
    for m, k, kn in (("m1", "end_stop", "stand_n1"), ("m2", "end_stop2", "stand_n2")):
        if arm == "v3w_pooled":
            a3 = np.mean([vec("L300", l, k) for l in LEARNERS], axis=0); a6 = np.mean([vec("L600", l, k) for l in LEARNERS], axis=0)
        elif arm == "all9":
            arms = LEARNERS + RULES + OTHERS
            a3 = np.mean([vec("L300", x, k) for x in arms], axis=0); a6 = np.mean([vec("L600", x, k) for x in arms], axis=0)
        else:
            a3 = vec("L300", arm, k); a6 = vec("L600", arm, k)
        cut = 1 - a6.mean() / a3.mean() if a3.mean() > 0 else None
        bs = 1 - a6[IDX].mean(axis=1) / a3[IDX].mean(axis=1)
        d = {"mean300": float(a3.mean()), "mean600": float(a6.mean()), "median300": float(np.median(a3)), "median600": float(np.median(a6)),
             "cut_mean": float(cut) if cut is not None else None, "cut_mean_ci95": pct(bs, 2.5, 97.5),
             "share_zero_600": float((a6 == 0).mean())}
        if arm not in ("v3w_pooled", "all9"):
            n3 = vec("L300", arm, kn); n6 = vec("L600", arm, kn)
            d["vehicles_mean300"] = float(n3.mean()); d["vehicles_mean600"] = float(n6.mean())
        d["removed_VV_D12_meanform"] = bool(d["cut_mean_ci95"][0] >= 0.8)
        stand[f"{arm}|{m}"] = d
res["standing"] = stand

json.dump(res, open("results_A.json", "w"), indent=1)
np.savez_compressed("edges_A.npz", **{k: v[0] for k, v in store.items()})
print("saved")
