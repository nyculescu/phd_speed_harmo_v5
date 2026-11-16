"""Post hoc, descriptive: why V3b reads WORSE at 600 m while V3a replicates at 300 m. Nothing here decides a reading.

usage: analyze.py runs.pkl cf_runs.pkl OUT.json
Post hoc intervals: percentile bootstrap over seeds (B = 2,000, rng 20261116), seeds resampled jointly."""
import itertools
import json
import math
import sys

import numpy as np
import pandas as pd

V3W = ("w0u250", "w1u500", "w2u250", "w3u500", "w4u500")
RULES = ("lr400_16_1", "grid_lr400_13_1")
ARMS = ("v3w",) + RULES + ("p333", "nc")
ROADS = ("3a", "ramp1", "4a", "ramp2", "1", "2", "3", "4", "5", "junction", "other")
PERIODS = ("before", "taper", "hold", "after", "rest")
B, RNG = 2000, 20261116


def tables(df: pd.DataFrame) -> dict:
    """cell -> arm (learners and the v3w mean) -> DataFrame indexed by seed, with group columns."""
    df = df.copy()
    tc = [f"t|{g}|{p}" for g in ROADS for p in PERIODS]
    df["m1"] = df[[f"t|{g}|{p}" for g in ("3a", "ramp1") for p in PERIODS]].sum(axis=1)
    df["m2"] = df[[f"t|{g}|{p}" for g in ("4a", "ramp2") for p in PERIODS]].sum(axis=1)
    df["merge"] = df["m1"] + df["m2"]
    for p in PERIODS:
        df[f"e1_{p}"] = df[f"t|1|{p}"]
    df["e1"] = df[[f"e1_{p}" for p in PERIODS]].sum(axis=1)
    df["e2"] = df[[f"t|2|{p}" for p in PERIODS]].sum(axis=1)
    df["rest"] = df["ttc_net"] - df["merge"] - df["e1"]
    df["no_e1"] = df["ttc_net"] - df["e1"]
    df["check_sum"] = df[tc].sum(axis=1) - df["ttc_net"]
    for g, p in (("1", "hold"), ("1", "before"), ("2", "hold"), ("2", "before"), ("3a", "before"), ("3a", "hold")):
        vs, dist = df[f"vs|{g}|{p}"], df[f"dist|{g}|{p}"]
        df[f"v_{g}_{p}"] = np.where(vs > 0, dist / vs.where(vs > 0, 1), np.nan) * 3.6
        df[f"vs_{g}_{p}"] = vs
    out = {}
    for c, g in df.groupby("cell"):
        out[c] = {a: x.set_index("seed").sort_index() for a, x in g.groupby("arm")}
        num = [k for k in out[c][V3W[0]].columns if out[c][V3W[0]][k].dtype.kind in "fi"]
        out[c]["v3w"] = sum(out[c][w][num] for w in V3W) / len(V3W)
    return out


def cd5(T: dict, rule: str, cols, idx=None) -> float | np.ndarray:
    """C-D5 on the sum of `cols` (c1_confirm.md §1): per learner the median over seeds of -(P - R)/median(R) x 100; mean of the five."""
    R = T[rule][list(cols)].sum(axis=1).to_numpy()
    m = max(float(np.median(R)), 1e-9)
    D = [-(T[w][list(cols)].sum(axis=1).to_numpy() - R) / m * 100.0 for w in V3W]
    if idx is None:
        return float(np.mean([np.median(d) for d in D]))
    return np.mean([np.median(d[idx], axis=1) for d in D], axis=0)


def cd5_mixed(Ta: dict, Tb: dict, rule: str, groups: dict, use_b: set, idx=None):
    """C-D5 on the total, taking each group's counts (learners and rule alike) from Tb if the group is in use_b, else from Ta."""
    def tot(arm):
        return sum((Tb if g in use_b else Ta)[arm][cols].sum(axis=1).to_numpy() for g, cols in groups.items())
    R = tot(rule)
    if idx is None:
        m = max(float(np.median(R)), 1e-9)
        return float(np.mean([np.median(-(tot(w) - R) / m * 100.0) for w in V3W]))
    m = np.maximum(np.median(R[idx], axis=1), 1e-9)     # the denominator is resampled with the seeds, as rf.moe does
    return np.mean([np.median(-(tot(w)[idx] - R[idx]), axis=1) / m * 100.0 for w in V3W], axis=0)


def shapley(f, players: list) -> dict:
    """Exact Shapley split of f(all) - f(none) over players."""
    n = len(players)
    val = {s: f(set(s)) for k in range(n + 1) for s in itertools.combinations(players, k)}
    key = lambda s: tuple(p for p in players if p in s)
    out = {}
    for p in players:
        tot = 0.0
        for k in range(n):
            for s in itertools.combinations([q for q in players if q != p], k):
                w = math.factorial(k) * math.factorial(n - k - 1) / math.factorial(n)
                tot = tot + w * (val[key(set(s) | {p})] - val[key(set(s))])
        out[p] = tot
    return out


def ci(b) -> list:
    return [round(float(x), 2) for x in np.percentile(b, (2.5, 97.5))]


def r2(x):
    return None if x is None or (isinstance(x, float) and not np.isfinite(x)) else round(float(x), 2)


def stats(x: pd.Series) -> dict:
    return {"mean": r2(x.mean()), "median": r2(x.median())}


def main(runs: str, cf: str, out: str) -> None:
    df = pd.read_pickle(runs)
    res = {"note": "post hoc, descriptive; no reading is decided here"}
    # checks
    T = tables(df)
    chk = {"sum_mismatch_rows": int((df[[f"t|{g}|{p}" for g in ROADS for p in PERIODS]].sum(axis=1) != df["ttc_net"]).sum())}
    chk["unknown_roads"] = sorted(set(df["unknown_roads"]) - {""})
    chk["lanes_other_distinct"] = int(df["lanes_other"].nunique())
    chk["len_1_0"] = sorted(df["len_1_0"].unique().tolist())
    chk["len_2_0"] = sorted(df["len_2_0"].unique().tolist())
    chk["len_acc_by_cell"] = {c: sorted(set(g["len_3a_0"]) | set(g["len_4a_0"])) for c, g in df.groupby("cell")}
    offs = {c: [json.loads(x) for x in g["offsets"].unique()] for c, g in df.groupby("cell")}
    chk["offsets"] = {c: v for c, v in offs.items()}
    chk["stand_eq_end_stop"] = bool(((df["stand_s_3a_0"] == df["end_stop"]) & (df["stand_s_4a_0"] == df["end_stop2"])).all())
    chk["period_keys_eq"] = bool(all((df[[f"t|{g}|{p}" for g in ROADS]].sum(axis=1) == df[f"p_{p}"]).all() for p in PERIODS))
    p3 = df[df.cell == "L300"].set_index(["arm", "seed"])["veh_n"]
    p6 = df[df.cell == "L600"].set_index(["arm", "seed"])["veh_n"]
    chk["demand_paired"] = bool((p3.sort_index() == p6.sort_index()).all())
    res["checks"] = chk
    seeds = T["L300"]["v3w"].index
    rng = np.random.default_rng(RNG)
    idx = rng.integers(0, len(seeds), (B, len(seeds)))

    # Q1: per arm, group counts per run
    q1 = {}
    cols = ["ttc_net", "m1", "m2", "merge"] + [f"e1_{p}" for p in PERIODS] + ["e1", "e2", "rest"]
    for c in ("L300", "L600"):
        q1[c] = {a: {k: stats(T[c][a][k]) for k in cols} for a in ARMS + V3W}
    res["q1"] = q1

    # Q2 (and the 600-m twin): decompositions of the edge against each rule
    G4 = {"m1": ["m1"], "m2": ["m2"], "e1": ["e1"], "rest": ["rest"]}
    q2 = {}
    for c in ("L300", "L600"):
        q2[c] = {}
        for r in RULES:
            t = T[c]
            Rt = t[r]["ttc_net"]
            d = {"cd5_total": r2(cd5(t, r, ["ttc_net"])), "cd5_no_e1": r2(cd5(t, r, ["no_e1"])),
                 "median_rule_total": r2(Rt.median()), "median_v3w_total": r2(t["v3w"]["ttc_net"].median()),
                 "mean_rule_total": r2(Rt.mean()), "mean_v3w_total": r2(t["v3w"]["ttc_net"].mean())}
            # exact additive split of the mean-based edge: mean(R_g - V_g)/mean(R_total)
            mb = {g: r2((t[r][g] - t["v3w"][g]).mean() / Rt.mean() * 100) for g in ["m1", "m2", "e1", "rest"] + [f"e1_{p}" for p in PERIODS]}
            mb["total"] = r2((Rt - t["v3w"]["ttc_net"]).mean() / Rt.mean() * 100)
            d["mean_based_pct"] = mb
            # samples per run, rule minus v3w (positive = v3w fewer): mean, pooled median, mean of learner medians
            d["diff_samples"] = {g: {"mean": r2((t[r][g] - t["v3w"][g]).mean()), "pooled_median": r2((t[r][g] - t["v3w"][g]).median()),
                                     "learner_median_mean": r2(np.mean([(t[r][g] - t[w][g]).median() for w in V3W]))}
                                 for g in ["ttc_net", "merge", "m1", "m2", "e1", "e1_hold", "rest", "no_e1"]}
            # exact Shapley split of the C-D5 point: groups switched from the rule's counts to each learner's
            def f(S, t=t, r=r):
                R = t[r]["ttc_net"].to_numpy()
                m = max(float(np.median(R)), 1e-9)
                vals = []
                for w in V3W:
                    P = sum((t[w] if g in S else t[r])[g].to_numpy() for g in G4)
                    vals.append(np.median(-(P - R) / m * 100.0))
                return float(np.mean(vals))
            d["shapley_cd5"] = {k: r2(v) for k, v in shapley(f, list(G4)).items()}
            q2[c][r] = d
    res["q2"] = q2

    # Q3: merge-area counts 300 -> 600, lane-end standing
    q3 = {}
    for a in ARMS:
        x3, x6 = T["L300"][a], T["L600"][a]
        q3[a] = {}
        for g in ("m1", "m2", "merge", "e1", "rest", "ttc_net"):
            q3[a][g] = {"mean300": r2(x3[g].mean()), "mean600": r2(x6[g].mean()), "kept_mean": r2(x6[g].mean() / max(x3[g].mean(), 1e-9)),
                        "med300": r2(x3[g].median()), "med600": r2(x6[g].median()), "kept_median": r2(x6[g].median() / max(x3[g].median(), 1e-9))}
        for k in ("stand_s_3a_0", "stand_s_4a_0", "stand_n_3a_0", "stand_n_4a_0"):
            q3[a][k] = {"mean300": r2(x3[k].mean()), "mean600": r2(x6[k].mean()), "med300": r2(x3[k].median()), "med600": r2(x6[k].median()),
                        "cut_median": r2(1 - x6[k].median() / max(x3[k].median(), 1e-9)), "cut_mean": r2(1 - x6[k].mean() / max(x3[k].mean(), 1e-9))}
    res["q3"] = q3

    # Q4: edge 1 between 300 and 600 m; the slowdown queue on edge 1 and 2
    q4 = {}
    qcols = ([f"e1_{p}" for p in PERIODS] + ["e1", "e2"] + [f"e1cong_{p}" for p in PERIODS] + [f"e1reach_max_{p}" for p in PERIODS] +
             [f"e1reach_mean_{p}" for p in ("before", "hold", "after")] + [f"e1v_{p}" for p in PERIODS] + ["e2v_before"] +
             [f"v_{g}_{p}" for g, p in (("1", "hold"), ("1", "before"), ("2", "hold"), ("2", "before"), ("3a", "before"), ("3a", "hold"))] +
             ["vs_1_hold", "vs_2_hold", "vs_1_before", "passed", "all_delay"])
    for a in ARMS:
        x3, x6 = T["L300"][a], T["L600"][a]
        q4[a] = {}
        for k in qcols:
            dd = (x6[k] - x3[k]).to_numpy()
            ok = np.isfinite(dd)
            q4[a][k] = {"mean300": r2(x3[k].mean()), "mean600": r2(x6[k].mean()), "med300": r2(x3[k].median()), "med600": r2(x6[k].median()),
                        "paired_mean_diff": r2(np.nanmean(dd)), "paired_median_diff": r2(np.nanmedian(dd)),
                        "ci95_mean_diff": ci(np.nanmean(np.where(ok, dd, np.nan)[idx], axis=1)) if ok.all() else None}
    # does edge-1 hold count follow the queue on edge 1? Spearman over seeds, per arm and length
    corr = {}
    for c in ("L300", "L600"):
        corr[c] = {a: {k: r2(T[c][a]["e1_hold"].rank().corr(T[c][a][k].rank())) for k in ("e1reach_max_hold", "e1cong_hold", "dur", "m1", "end_stop")}
                   for a in ARMS}
    q4["spearman_e1_hold"] = corr
    res["q4"] = q4

    # Q5: reconcile deficit_600 with no_edge1_600, against both rules
    q5 = {}
    t = T["L600"]
    for r in RULES:
        d = {}
        for g in ("merge", "m1", "m2", "e1", "rest", "no_e1", "ttc_net"):
            per = {w: r2((t[w][g] - t[r][g]).median()) for w in V3W}
            d[g] = {"reader_style_pooled_median_v3w_minus_rule": r2((t["v3w"][g] - t[r][g]).median()),
                    "mean_v3w_minus_rule": r2((t["v3w"][g] - t[r][g]).mean()),
                    "per_learner_median_P_minus_R": per, "mean_of_learner_medians": r2(np.mean(list(per.values()))),
                    "rule_median": r2(t[r][g].median()), "rule_mean": r2(t[r][g].mean()),
                    "cd5_pct": r2(cd5(t, r, [g])),
                    "share_seeds_v3w_more": r2(((t["v3w"][g] - t[r][g]) > 0).mean()),
                    "share_seeds_zero_diff_learners": r2(np.mean([((t[w][g] - t[r][g]) == 0).mean() for w in V3W]))}
        d["sum_of_group_pooled_medians"] = r2(sum(d[g]["reader_style_pooled_median_v3w_minus_rule"] for g in ("merge", "e1", "rest")))
        q5[r] = d
    res["q5"] = q5

    # Q6: the change 300 -> 600 split over groups (exact Shapley of the C-D5 point and per-resample)
    q6 = {}
    G3 = {"merge": ["m1", "m2"], "e1": ["e1"], "rest": ["rest"]}
    G4b = {"m1": ["m1"], "m2": ["m2"], "e1": ["e1"], "rest": ["rest"]}
    for r in RULES:
        d = {}
        for name, G in (("3 groups", G3), ("4 groups", G4b)):
            f = lambda S, G=G: cd5_mixed(T["L300"], T["L600"], r, G, S)
            sv = shapley(f, list(G))
            fb = lambda S, G=G: cd5_mixed(T["L300"], T["L600"], r, G, S, idx)
            svb = shapley(fb, list(G))
            d[name] = {"e300": r2(f(set())), "e600": r2(f(set(G))), "change": r2(f(set(G)) - f(set())),
                       "shapley": {k: {"pt": r2(v), "ci95": ci(svb[k])} for k, v in sv.items()},
                       "one_at_a_time_from_300": {k: r2(f({k}) - f(set())) for k in G},
                       "all_but_one_from_600": {k: r2(f(set(G)) - f(set(G) - {k})) for k in G}}
        # the denominator's part: 600-m numerators over the 300-m median of the rule
        R3, R6 = T["L300"][r]["ttc_net"], T["L600"][r]["ttc_net"]
        num6 = np.mean([np.median(-(T["L600"][w]["ttc_net"] - R6)) for w in V3W])
        num3 = np.mean([np.median(-(T["L300"][w]["ttc_net"] - R3)) for w in V3W])
        d["numerator_samples"] = {"300": r2(num3), "600": r2(num6)}
        d["denominator_rule_median"] = {"300": r2(R3.median()), "600": r2(R6.median())}
        d["e600_on_300_denominator"] = r2(num6 / R3.median() * 100)
        q6[r] = d
    res["q6"] = q6

    # consistency: v3w and the rules at 300 m, stored E30 confirmation rows (other seeds) against L300 here
    cfd = pd.read_pickle(cf)
    TC = tables(cfd)["E30"]
    cons = {}
    for a in ARMS:
        cons[a] = {k: {"cf_E30": stats(TC[a][k]), "vv_L300": stats(T["L300"][a][k])}
                   for k in ("ttc_net", "m1", "m2", "e1", "e1_hold", "rest", "end_stop", "end_stop2", "all_delay")}
    for r in RULES:
        cons[f"edge_{r}"] = {"cf_E30_cd5": r2(cd5(TC, r, ["ttc_net"])), "vv_L300_cd5": r2(cd5(T["L300"], r, ["ttc_net"])),
                             "cf_E30_cd5_no_e1": r2(cd5(TC, r, ["no_e1"])), "vv_L300_cd5_no_e1": r2(cd5(T["L300"], r, ["no_e1"])),
                             "cf_mean_based": {g: r2((TC[r][g] - TC["v3w"][g]).mean() / TC[r]["ttc_net"].mean() * 100) for g in ("m1", "m2", "e1", "rest", "ttc_net")},
                             "vv_mean_based": {g: r2((T["L300"][r][g] - T["L300"]["v3w"][g]).mean() / T["L300"][r]["ttc_net"].mean() * 100) for g in ("m1", "m2", "e1", "rest", "ttc_net")}}
    cons["cf_checks"] = {"n_seeds": int(TC["v3w"].shape[0]), "sum_mismatch": int((cfd[[f"t|{g}|{p}" for g in ROADS for p in PERIODS]].sum(axis=1) != cfd["ttc_net"]).sum()),
                         "unknown_roads": sorted(set(cfd["unknown_roads"]) - {""})}
    res["consistency"] = cons
    with open(out, "w") as fh:
        json.dump(res, fh, indent=1)
    print("written", out)


if __name__ == "__main__":
    main(*sys.argv[1:4])
