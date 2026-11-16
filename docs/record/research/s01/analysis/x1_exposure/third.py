"""x1_exposure, third pass: road-group sums (edges 3+4a against ramp 2 + rest) per cell and the X1-X2 contrast; an
nc-calibrated counterfactual (TTC that nc's own seed-to-seed relation predicts at the arm's jam or band exposure);
per-learner exposure-normalised rates; the shared-nc null for the nc-jam-level correlation; small-gap counters."""
import json

import numpy as np

import lib

T = lib.load()
for A in T.values():
    for r in A.values():
        g = lambda k: lib.val(r, k)
        r["ttc_34a"] = g("ttc3_r_3") + g("ttc3_r_4a")
        r["ttc_other"] = g("ttc3_r_ramp2") + g("ttc3_r_rest")
        r["jam_share"] = g("st_jam") / g("st_vs")
        r["rate_mov18"] = (g("ttc3_s_mid") + g("ttc3_s_hi")) / (g("e_mid") + g("e_hi"))
        r["rate_km"] = g("ttc_net") / g("dist") * 1000.0
NC = {"n": 0}


def rnd(t, k=1):
    return [round(float(x), k) for x in t]


def counterfactual(nc: dict, A: dict, xs: list, intercept: bool) -> dict:
    """OLS of ttc3 on xs over nc's seeds; the arm's observed minus predicted ttc3 per seed (mean), bootstrap refits the model."""
    seeds = sorted(nc)
    X = lambda R, ss: np.column_stack(([np.ones(len(ss))] if intercept else []) + [[R[s][k] for s in ss] for k in xs])
    y_n, y_p = np.array([nc[s]["ttc3"] for s in seeds]), np.array([A[s]["ttc3"] for s in seeds])
    Xn, Xp = X(nc, seeds), X(A, seeds)
    beta = np.linalg.lstsq(Xn, y_n, rcond=None)[0]
    resid = y_p - Xp @ beta
    pred_nc = Xn @ beta
    r2 = 1 - ((y_n - pred_nc) ** 2).sum() / ((y_n - y_n.mean()) ** 2).sum()
    idx = lib.boot_idx(len(seeds))
    bs = []
    for i in idx[:5000]:
        b = np.linalg.lstsq(Xn[i], y_n[i], rcond=None)[0]
        bs.append((y_p[i] - Xp[i] @ b).mean())
    rng_x = {k: [round(min(nc[s][k] for s in seeds), 4), round(max(nc[s][k] for s in seeds), 4), round(min(A[s][k] for s in seeds), 4), round(max(A[s][k] for s in seeds), 4)] for k in xs}
    NC["n"] += 1
    return {"xs": xs, "intercept": intercept, "beta": rnd(beta, 5), "r2_nc": round(float(r2), 3), "obs_minus_pred_mean": [round(float(resid.mean()), 1), round(float(np.percentile(bs, 2.5)), 1), round(float(np.percentile(bs, 97.5)), 1)],
            "obs_minus_nc_mean": round(float((y_p - y_n).mean()), 1), "pred_minus_nc_mean": round(float((Xp @ beta - y_n).mean()), 1), "range_nc_min_max_arm_min_max": rng_x}


OUT = {}
POL = ("v3w", "tail", "sw", "baseline-v3")
for cell in ("X1", "X2"):
    nc = T[(f"{cell}|nc", lib.Q)]
    seeds = sorted(nc)
    C = {}
    for name, nm in lib.arms(cell).items():
        if name == "nc":
            continue
        A = lib.arm_mean(T, [f"{cell}|{n}" for n in nm])
        R = {"ttc_34a_diff_mean": rnd(lib.ci(lib.paired(A, nc, "ttc_34a"), np.mean)), "ttc_other_diff_mean": rnd(lib.ci(lib.paired(A, nc, "ttc_other"), np.mean)),
             "nc_med_34a_other": [float(np.median([nc[s]["ttc_34a"] for s in seeds])), float(np.median([nc[s]["ttc_other"] for s in seeds]))]}
        NC["n"] += 2
        R["cf_jam"] = counterfactual(nc, A, ["jam_share"], True)
        R["cf_bands"] = counterfactual(nc, A, ["e_lo", "e_mid", "e_hi"], False)
        R["cf_bands_icpt"] = counterfactual(nc, A, ["e_lo", "e_mid", "e_hi"], True)
        R["small_gaps_paired_median"] = {k: [float(np.median([lib.val(nc[s], k) for s in seeds])), float(np.median([lib.val(A[s], k) for s in seeds])),
                                             float(np.median(lib.paired(A, nc, k)))] for k in ("gap25", "stop_gap")}
        if name in POL:
            R["per_learner"] = {n: {"rate_mov18": [round(x, 2) for x in lib.raw(T[(f"{cell}|{n}", lib.Q)], nc, "rate_mov18")],
                                    "rate_km": [round(x, 2) for x in lib.raw(T[(f"{cell}|{n}", lib.Q)], nc, "rate_km")]} for n in nm}
            NC["n"] += 10
            # shared-nc null for the correlation of the TTC difference with nc's own jam level
            tp, tn = np.array([A[s]["ttc3"] for s in seeds]), np.array([nc[s]["ttc3"] for s in seeds])
            jn = np.array([nc[s]["jam_share"] for s in seeds])
            rho = lib.spearman(tp - tn, jn)
            rng = np.random.default_rng(lib.RNG + 3)
            null = []
            for _ in range(10000):
                pi = rng.permutation(len(seeds))
                null.append(lib.spearman(tp - tn[pi], jn[pi]))
            null = np.array(null)
            R["rho_dttc_ncjam"] = {"rho": round(rho, 3), "shuffled_nc_null_2.5_50_97.5": rnd(np.percentile(null, [2.5, 50, 97.5]), 3)}
            NC["n"] += 1
        C[name] = R
    OUT[cell] = C
# X1 minus X2 for the policies (same seed numbers in both cells; paired by seed)
OUT["X1_minus_X2"] = {}
for name in POL:
    nm = lib.LEARNERS[name]
    d = {}
    for k in ("ttc3", "ttc_34a", "ttc_other"):
        x1 = lib.paired(lib.arm_mean(T, [f"X1|{n}" for n in nm]), T[("X1|nc", lib.Q)], k)
        x2 = lib.paired(lib.arm_mean(T, [f"X2|{n}" for n in nm]), T[("X2|nc", lib.Q)], k)
        d[k] = rnd(lib.ci(x1 - x2, np.mean))
        NC["n"] += 1
    OUT["X1_minus_X2"][name] = d
OUT["comparisons_with_ci"] = NC["n"]
json.dump(OUT, open(lib.HERE / "third.json", "w"), indent=1)
for cell in ("X1", "X2"):
    print("==", cell)
    for a, R in OUT[cell].items():
        print(f"-- {a}: 3+4a {R['ttc_34a_diff_mean']} other {R['ttc_other_diff_mean']} nc med {R['nc_med_34a_other']}")
        for k in ("cf_jam", "cf_bands", "cf_bands_icpt"):
            c = R[k]
            print(f"   {k}: r2_nc {c['r2_nc']} beta {c['beta']} obs-pred {c['obs_minus_pred_mean']} obs-nc {c['obs_minus_nc_mean']} pred-nc {c['pred_minus_nc_mean']} ranges {c['range_nc_min_max_arm_min_max']}")
        print("   gaps", R["small_gaps_paired_median"])
        if "per_learner" in R:
            print("   learners", R["per_learner"])
            print("   rho dttc ncjam", R["rho_dttc_ncjam"])
print("X1-X2", OUT["X1_minus_X2"])
print("tests", NC["n"])
