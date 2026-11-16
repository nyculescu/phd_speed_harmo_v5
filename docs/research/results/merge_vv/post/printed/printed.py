"""Post hoc assembly of merge_vv.md v1.1's printed items (V2, V3a, V3b) from the V&V screen rows.

Every number is recomputed here from s6_rows.jsonl with an own implementation of the C-D5 statistic (not importing read_vv.py),
then compared with the committed reader's v3.json. Nothing here decides anything.
usage: python -I printed.py"""
import json
from pathlib import Path

import numpy as np

RUN = Path("/home/catalin/work/phd/v5b1_runs/vv_remote")
OUT = Path("/home/catalin/work/phd/v5b1_runs/vv_post/printed")
V3W = ("w0u250", "w1u500", "w2u250", "w3u500", "w4u500")
RULES = ("lr400_16_1", "grid_lr400_13_1")
REFS = ("p333", "nc")
ARMS = V3W + RULES + REFS
OPPS = RULES + REFS
CELLS = ("L300", "L600")
SEEDS = list(range(7492000, 7492480))
B, RNG = 20_000, 20261108
PER = ("before", "taper", "hold", "after", "rest")
EDGE_KEYS = ("g_merge", "g_m1", "g_m2", "g_edge1", "g_rest", "ttc_no_e1") + tuple(f"p_{p}" for p in PER) + (
    "ttc_net", "all_delay", "N", "passed", "b45_step", "ttc2", "ttc15", "sev3", "vv_enc", "vv_ttc3_main")
M1, M2, E1 = ("3a", "ramp1"), ("4a", "ramp2"), ("1",)


def gsum(d: dict, roads) -> float:
    out = 0.0
    for g in roads:
        x = d.get(g, 0.0)
        out += sum(x.values()) if isinstance(x, dict) else float(x)
    return out


def take(r: dict, road_keys: set, absent: dict) -> dict:
    ttc = r.get("m_road_ttc3", {})
    road_keys |= set(ttc)
    m1, m2, e1 = gsum(ttc, M1), gsum(ttc, M2), gsum(ttc, E1)
    net = float(r["ttc_net"])
    d = {"ttc_net": net, "g_m1": m1, "g_m2": m2, "g_merge": m1 + m2, "g_edge1": e1, "g_rest": net - m1 - m2 - e1, "ttc_no_e1": net - e1,
         "roads_sum": gsum(ttc, ttc)}
    for p in PER:
        d[f"p_{p}"] = float(r.get(f"ttc3_p_{p}", 0.0))
        d[f"proad_{p}"] = sum(float(x.get(p, 0.0)) for x in ttc.values() if isinstance(x, dict))
    for k in ("all_delay", "N", "passed", "collisions", "b45_step", "ttc2", "ttc15", "sev3", "vv_enc", "vv_ttc3_main", "vv_m_time",
              "vv_m_whole", "vv_m_half", "ttc_half", "end_stop", "end_stop2", "teleports", "m_stuck_n", "vv_c15_cap", "vv_c15_n",
              "vv_x_out", "vv_x_acc_n", "arrived", "finished_pct"):
        # Counters are written only once they count something, so an absent key is 0 (as the reader reads it).
        d[k] = float(r.get(k) or 0.0)
        if k not in r:
            absent[(r["name"], k)] = absent.get((r["name"], k), 0) + 1
    d["has_m_time"] = "vv_m_time" in r
    sn, ss = r.get("vv_stand_n", {}), r.get("vv_stand_s", {})
    d["stand_n1"], d["stand_n2"] = float(sn.get("3a_0", 0)), float(sn.get("4a_0", 0))
    d["stand_s1"], d["stand_s2"] = float(ss.get("3a_0", 0)), float(ss.get("4a_0", 0))
    d["has_stand"] = "vv_stand_n" in r
    t0 = r.get("c1_t0") or {}
    d["demand"] = (t0.get("veh_n"), t0.get("alks_sha"))
    d["len"] = tuple(r.get("vv_lanes", {}).get(x) for x in ("3a_0", "4a_0"))
    return d


def load() -> tuple:
    T, road_keys, absent = {}, set(), {}
    with open(RUN / "vv_screen" / "s6_rows.jsonl") as f:
        for line in f:
            r = json.loads(line)
            c, a = r["name"].split("|", 1)
            key = (c, a, r["seed"])
            if key in T:
                raise SystemExit(f"duplicate {key}")
            T[key] = take(r, road_keys, absent)
    return T, road_keys, absent


def col(T, c, a, k) -> np.ndarray:
    return np.array([T[(c, a, s)][k] for s in SEEDS], dtype=float)


def pct_edge(T, c, opp, k, idx, sign=1.0) -> dict:
    """C-D5: per learner the median over seeds of -(P - O)/median(O) x 100; effect = mean of the five; joint seed resamples."""
    O = col(T, c, opp, k)
    m = max(float(np.median(O)), 1e-9)
    D = [sign * -(col(T, c, w, k) - O) / m * 100.0 for w in V3W]
    pt = float(np.mean([np.median(d) for d in D]))
    b = np.mean([np.median(d[idx], axis=1) for d in D], axis=0)
    lo, hi = np.percentile(b, (2.5, 97.5))
    return {"pt": pt, "lo95": float(lo), "hi95": float(hi), "se": float(np.std(b)), "_b": b,
            "opp_med": float(np.median(O)), "opp_zero_share": float(np.mean(O == 0)),
            "v3w_med": float(np.mean([np.median(col(T, c, w, k)) for w in V3W])),
            "learner_pts": [float(np.median(d)) for d in D]}


def single(T, c, a, ref, k, idx) -> dict:
    """Single arm against a reference (P0 form): median over seeds of -(a - ref)/median(ref) x 100."""
    R = col(T, c, ref, k)
    d = -(col(T, c, a, k) - R) / max(float(np.median(R)), 1e-9) * 100.0
    b = np.median(d[idx], axis=1)
    lo, hi = np.percentile(b, (2.5, 97.5))
    return {"pt": float(np.median(d)), "lo95": float(lo), "hi95": float(hi), "se": float(np.std(b)), "ref_med": float(np.median(R)),
            "arm_med": float(np.median(col(T, c, a, k)))}


def strip(x: dict) -> dict:
    return {k: v for k, v in x.items() if not k.startswith("_")}


def main() -> None:
    T, road_keys, absent = load()
    n = len(SEEDS)
    idx = np.random.default_rng(RNG).integers(0, n, (B, n))
    R = {"n_rows": len(T), "road_keys": sorted(road_keys), "absent_keys": {f"{n} {k}": v for (n, k), v in sorted(absent.items())}}
    miss = [f"{c} {a} {s}" for c in CELLS for a in ARMS for s in SEEDS if (c, a, s) not in T]
    R["missing"] = miss[:10]

    # Row-level checks (post hoc unless the plan names them)
    chk = {}
    rows = list(T.items())
    chk["roads_sum_ne_ttc_net"] = sum(1 for _, d in rows if d["roads_sum"] != d["ttc_net"])
    chk["period_ne_road_periods"] = sum(1 for _, d in rows for p in PER if d[f"p_{p}"] != d[f"proad_{p}"])
    chk["periods_sum_ne_ttc_net"] = sum(1 for _, d in rows if sum(d[f"p_{p}"] for p in PER) != d["ttc_net"])
    chk["L300_rows_without_meter"] = sum(1 for (c, a, s), d in rows if c == "L300" and not d["has_m_time"])
    chk["L600_rows_with_meter"] = sum(1 for (c, a, s), d in rows if c == "L600" and d["has_m_time"])
    chk["meter_whole_ne_ttc_net"] = sum(1 for (c, a, s), d in rows if c == "L300" and d["vv_m_whole"] != d["ttc_net"])
    chk["meter_half_ne_ttc_half"] = sum(1 for (c, a, s), d in rows if c == "L300" and d["vv_m_half"] != d["ttc_half"])
    chk["stand_s_ne_end_stop"] = sum(1 for _, d in rows if d["stand_s1"] != d["end_stop"] or d["stand_s2"] != d["end_stop2"])
    chk["rows_without_stand_log"] = sum(1 for _, d in rows if not d["has_stand"])
    chk["demand_unpaired"] = sum(1 for a in ARMS for s in SEEDS if None in T[("L300", a, s)]["demand"]
                                 or T[("L300", a, s)]["demand"] != T[("L600", a, s)]["demand"])
    chk["lane_len"] = {c: sorted({tuple(round(x, 2) for x in T[(c, a, s)]["len"]) for a in ARMS for s in SEEDS}) for c in CELLS}
    chk["teleports_sum"] = {c: {a: float(np.nansum(col(T, c, a, "teleports"))) for a in ARMS} for c in CELLS}
    chk["stuck_sum"] = {c: {a: float(np.nansum(col(T, c, a, "m_stuck_n"))) for a in ARMS} for c in CELLS}
    chk["c15_600"] = {a: {"cap": float(np.nansum(col(T, "L600", a, "vv_c15_cap"))), "n": float(np.nansum(col(T, "L600", a, "vv_c15_n"))),
                          "x_out": float(np.nansum(col(T, "L600", a, "vv_x_out"))), "x_acc_n": float(np.nansum(col(T, "L600", a, "vv_x_acc_n")))}
                      for a in ARMS}
    chk["c15_300"] = {a: {"cap": float(np.nansum(col(T, "L300", a, "vv_c15_cap"))), "n": float(np.nansum(col(T, "L300", a, "vv_c15_n")))}
                      for a in V3W}
    R["checks"] = chk

    # Printed edges: all four opponents, both lengths
    E = {}
    for c in CELLS:
        E[c] = {}
        for o in OPPS:
            E[c][o] = {}
            for k in EDGE_KEYS:
                if c == "L600" and k == "vv_m_time":
                    continue
                E[c][o][k] = pct_edge(T, c, o, k, idx, sign=-1.0 if k == "passed" else 1.0)
        E[c]["v2"] = {}
        if c == "L300":
            for o in RULES:
                a, b = pct_edge(T, c, o, "vv_m_time", idx), E[c][o]["ttc_net"]
                dlt = a["_b"] - b["_b"]
                E[c]["v2"][o] = {"edge_01s": strip(a), "edge_1hz": strip(b), "diff": {"pt": a["pt"] - b["pt"],
                                 "lo95": float(np.percentile(dlt, 2.5)), "hi95": float(np.percentile(dlt, 97.5))}}
    R["edges"] = {c: {o: {k: strip(v) for k, v in E[c][o].items()} for o in OPPS} for c in CELLS}
    R["v2"] = E["L300"]["v2"]

    # V2 missed share per arm (median over seeds), plus a pooled ratio (post hoc)
    ms = {}
    for a in ARMS:
        t01, t1 = col(T, "L300", a, "vv_m_time"), col(T, "L300", a, "ttc_net")
        r_ = (t01 - t1) / np.maximum(t01, 1e-9)
        ms[a] = {"median": float(np.median(r_)), "pooled": float((t01.sum() - t1.sum()) / t01.sum()),
                 "sum_01s": float(t01.sum()), "sum_1hz": float(t1.sum()), "q10": float(np.percentile(r_, 10)), "q90": float(np.percentile(r_, 90))}
    R["missed_share"] = ms

    # Collisions, standing, delay medians per arm
    arm_tab = {}
    for c in CELLS:
        arm_tab[c] = {}
        for a in ARMS:
            x = {k: col(T, c, a, k) for k in ("collisions", "end_stop", "end_stop2", "stand_n1", "stand_n2", "all_delay", "N", "passed", "ttc_net",
                                               "vv_enc", "b45_step", "arrived")}
            arm_tab[c][a] = {"collisions_sum": float(x["collisions"].sum()), "collision_runs": int((x["collisions"] > 0).sum()),
                             "end_stop_med": float(np.median(x["end_stop"])), "end_stop_mean": float(x["end_stop"].mean()),
                             "end_stop2_med": float(np.median(x["end_stop2"])), "end_stop2_mean": float(x["end_stop2"].mean()),
                             "stand_n1_med": float(np.median(x["stand_n1"])), "stand_n1_mean": float(x["stand_n1"].mean()),
                             "stand_n2_med": float(np.median(x["stand_n2"])), "stand_n2_mean": float(x["stand_n2"].mean()),
                             "stand_n1_zero": float(np.mean(x["stand_n1"] == 0)), "stand_n2_zero": float(np.mean(x["stand_n2"] == 0)),
                             "delay_med": float(np.median(x["all_delay"])), "N_med": float(np.median(x["N"])),
                             "passed_med": float(np.median(x["passed"])), "ttc_med": float(np.median(x["ttc_net"])),
                             "enc_med": float(np.median(x["vv_enc"])), "b45_med": float(np.median(x["b45_step"]))}
    R["arms"] = arm_tab

    # VV-D12 cut (record sentence input), v3w = per-seed mean of the learners
    def series(c, a, k):
        return np.mean([col(T, c, w, k) for w in V3W], axis=0) if a == "v3w" else col(T, c, a, k)
    cut = {}
    for m, k in (("merge1", "end_stop"), ("merge2", "end_stop2")):
        cut[m] = {}
        for a in ("v3w",) + OPPS:
            x3, x6 = series("L300", a, k), series("L600", a, k)
            b = 1.0 - np.median(x6[idx], axis=1) / np.maximum(np.median(x3[idx], axis=1), 1e-9)
            cut[m][a] = {"cut": 1.0 - float(np.median(x6)) / max(float(np.median(x3)), 1e-9), "lo95": float(np.percentile(b, 2.5)),
                         "med300": float(np.median(x3)), "med600": float(np.median(x6))}
    R["cut"] = cut

    # Deficit by group at 600 m (samples per run)
    R["deficit_600"] = {r: {g: float(np.median(series("L600", "v3w", g) - col(T, "L600", r, g))) for g in ("g_merge", "g_edge1", "g_rest")}
                        for r in RULES}

    # P0 on delay, both lengths: rules and p333 against no control; learners post hoc
    p0 = {}
    for c in CELLS:
        p0[c] = {a: single(T, c, a, "nc", "all_delay", idx) for a in RULES + ("p333",) + V3W}
        p0[c]["any_rule"] = any(p0[c][a]["pt"] >= 10.0 and p0[c][a]["lo95"] > 0 for a in RULES + ("p333",))
    R["p0"] = p0

    # Comparison with the committed reader's output
    v3 = json.loads((RUN / "vv_screen" / "v3.json").read_text())
    cmp_rows, worst = [], 0.0

    def gap(a, b):
        return float("inf") if (a != a or b != b) else abs(a - b)
    for c, pk in (("L300", "printed_300"), ("L600", "printed_600")):
        P = v3[pk]
        for o in OPPS:
            for k, v in P[o].items():
                if k == "jams":
                    continue
                mine = R["edges"][c][o][k]
                for f in ("pt", "lo95", "hi95", "se"):
                    dlt = gap(mine[f], v[f])
                    worst = max(worst, dlt)
                    cmp_rows.append([c, o, k, f, v[f], mine[f], dlt])
        for a, v in P["collisions"].items():
            dlt = gap(arm_tab[c][a]["collisions_sum"], v)
            worst = max(worst, dlt)
            cmp_rows.append([c, a, "collisions", "sum", v, arm_tab[c][a]["collisions_sum"], dlt])
        for a, v in P["rule_beats_nc_by_10"]["by_rule"].items():
            for f in ("pt", "lo95"):
                dlt = gap(p0[c][a][f], v[f])
                worst = max(worst, dlt)
                cmp_rows.append([c, a, "p0_delay", f, v[f], p0[c][a][f], dlt])
    for c in CELLS:
        for a in ARMS:
            for m, key in (("3a_0", "stand_n1_med"), ("4a_0", "stand_n2_med")):
                v = v3["standing_vehicles"][c][a][m]
                dlt = gap(arm_tab[c][a][key], v)
                worst = max(worst, dlt)
                cmp_rows.append([c, a, f"standing_vehicles {m}", "median", v, arm_tab[c][a][key], dlt])
    for a, v in v3["v2"]["missed_share"].items():
        dlt = gap(ms[a]["median"], v)
        worst = max(worst, dlt)
        cmp_rows.append(["L300", a, "missed_share", "median", v, ms[a]["median"], dlt])
    for a in V3W:
        mine = chk["c15_600"][a]["cap"] / max(chk["c15_600"][a]["n"], 1.0)
        dlt = gap(mine, v3["c15_cap_share_600"][a])
        worst = max(worst, dlt)
        cmp_rows.append(["L600", a, "c15_cap_share", "ratio", v3["c15_cap_share_600"][a], mine, dlt])
    for m in ("merge1", "merge2"):
        for a in ("v3w",) + OPPS:
            for f in ("cut", "lo95", "med300", "med600"):
                dlt = gap(cut[m][a][f], v3["v3b"]["cut"][m][a][f])
                worst = max(worst, dlt)
                cmp_rows.append(["L300/L600", a, f"cut {m}", f, v3["v3b"]["cut"][m][a][f], cut[m][a][f], dlt])
    for r in RULES:
        for g in ("g_merge", "g_edge1", "g_rest"):
            dlt = gap(R["deficit_600"][r][g], v3["v3b"]["deficit_600"][r]["by_group"][g])
            worst = max(worst, dlt)
            cmp_rows.append(["L600", r, f"deficit {g}", "median", v3["v3b"]["deficit_600"][r]["by_group"][g], R["deficit_600"][r][g], dlt])
        for f in ("pt", "lo95", "hi95"):
            for blk, mine in (("edge_01s", R["v2"][r]["edge_01s"]), ("edge_1hz", R["v2"][r]["edge_1hz"]), ("diff", R["v2"][r]["diff"])):
                dlt = gap(mine[f], v3["v2"][r][blk][f])
                worst = max(worst, dlt)
                cmp_rows.append(["L300", r, f"v2 {blk}", f, v3["v2"][r][blk][f], mine[f], dlt])
    R["compare"] = {"n_numbers": len(cmp_rows), "max_abs_diff": worst, "over_1e-6": [x for x in cmp_rows if x[-1] > 1e-6]}
    (OUT / "compare_v3.tsv").write_text("cell\tarm_or_opp\tkey\tfield\tv3json\trecomputed\tabs_diff\n"
                                         + "\n".join("\t".join(str(y) for y in x) for x in cmp_rows) + "\n")
    R["jams_v3json"] = {c: {o: v3[pk][o].get("jams") for o in OPPS} for c, pk in (("L300", "printed_300"), ("L600", "printed_600"))}
    (OUT / "recomputed.json").write_text(json.dumps(R, indent=1, default=float))
    print("rows", len(T), "missing", len(miss), "compared", len(cmp_rows), "max diff", worst, "over 1e-6", len(R["compare"]["over_1e-6"]))
    print("road keys", sorted(road_keys))
    print("checks", {k: v for k, v in chk.items() if k not in ("teleports_sum", "stuck_sum", "c15_600", "c15_300", "lane_len")})


if __name__ == "__main__":
    main()
