"""Alternative delay definitions per run, from stored fields only. EXPLORATORY."""
import numpy as np
REF = 100.0 / 3.6
PEND = ("pending_main", "pending_ramp", "pending_ramp2")
LOW = {"all_delay", "delay_s", "innet", "pend_total", "pend_main", "pend_ramps", "TTT", "per_passed", "per_arrived", "merge_roads", "main_roads", "ramp_all",
       "caralks", "truck25", "own_mean", "own_p95", "own_ramp", "own_ramp2", "own_total", "h1", "h2", "unfinished", "pending_end", "endstop", "minus_endstop",
       "r1", "r2", "r3a", "r3", "r4a", "r4", "r5", "junction", "class_ref", "collisions", "stuck", "dropped", "teleports", "full_moving", "m2only", "m1only", "in_net_end", "first5_m", "last5_m", "unfinished_pp", "endstop2", "pend_ramps_min"}
def g(r, k, d=np.nan):
    v = r.get(k)
    return d if v is None else float(v)
def measures(r):
    o = {}
    o["all_delay"], o["delay_s"], o["TTT"] = g(r, "all_delay"), g(r, "delay_s"), g(r, "N")
    o["innet"] = g(r, "vs") - g(r, "dist") / REF
    o["pend_total"] = g(r, "N") - g(r, "vs")
    o["passed"], o["arrived"] = g(r, "passed"), g(r, "arrived")
    o["per_passed"] = o["all_delay"] / o["passed"]
    o["per_arrived"] = o["all_delay"] / o["arrived"]
    o["dist_km"] = g(r, "dist_step") / 1000.0
    o["own_mean"], o["own_p95"], o["own_ramp"], o["own_ramp2"] = g(r, "delay"), g(r, "delay_p95"), g(r, "delay_ramp"), g(r, "delay_ramp2")
    o["finished_pct"] = g(r, "finished_pct")
    o["unfinished_pp"] = 100.0 - o["finished_pct"]
    o["endstop"] = g(r, "end_stop", 0.0) + g(r, "end_stop2", 0.0)
    o["endstop2"] = g(r, "end_stop2", 0.0)
    o["minus_endstop"] = o["all_delay"] - o["endstop"]
    o["collisions"], o["teleports"] = g(r, "collisions", 0.0), g(r, "teleports", 0.0)
    o["full_moving"] = g(r, "alks_full_moving", 0.0)
    fm = r.get("flow_min")
    if fm:
        o["passed_h1"], o["passed_h2"] = float(sum(fm[:12])), float(sum(fm[12:]))
        o["passed_last5"] = float(sum(fm[-6:]))
    if r.get("m_n_car") is not None:
        o["caralks"] = 0.1 * (g(r, "m_n_car") + g(r, "m_n_alks")) - (g(r, "m_dist_m_car") + g(r, "m_dist_m_alks")) / REF
        o["truck25"] = 0.1 * g(r, "m_n_truck") - g(r, "m_dist_m_truck") / 25.0
        o["truck_km"] = g(r, "m_dist_m_truck") / 1000.0
        o["truck_offset"] = g(r, "m_dist_m_truck") * (1.0 / 25.0 - 1.0 / REF)     # veh-s a truck at 90 km/h accrues against 100 km/h
        o["class_ref"] = o["caralks"] + o["truck25"] + o["pend_total"]
    if r.get("m_planned_window") is not None:
        pl = g(r, "m_planned_window"); done = o["finished_pct"] / 100.0 * pl
        o["planned"], o["unfinished"], o["pending_end"] = pl, pl - done, g(r, "m_pending_end")
        o["in_net_end"] = o["unfinished"] - o["pending_end"]
        o["own_total"] = o["own_mean"] * done
        o["stuck"], o["dropped"] = g(r, "m_stuck_n", 0.0), g(r, "m_dropped", 0.0)
    if r.get("road_vs"):
        vs = {k: sum(x.values()) for k, x in r["road_vs"].items()}; ds = {k: sum(x.values()) for k, x in r["road_dist"].items()}
        dl = lambda ks: sum(vs.get(k, 0.0) - ds.get(k, 0.0) / REF for k in ks)
        o["pend_main"], o["pend_ramps"] = vs.get("pending_main", 0.0), vs.get("pending_ramp", 0.0) + vs.get("pending_ramp2", 0.0)
        o["merge_roads"], o["main_roads"] = dl(("3a", "4a")), dl(("1", "2", "3", "4", "5"))
        o["ramp_all"] = dl(("ramp1", "ramp2")) + o["pend_ramps"]
        for k in ("1", "2", "3a", "3", "4a", "4", "5", "junction"):
            o["r" + k if k != "junction" else k] = dl((k,))
    mm = r.get("minute")
    if mm:
        n = len(mm["m1_acc_n"])
        per = np.zeros(n)
        for k in ("m1_acc", "m1_up", "m2_acc", "m2_up"):
            per += np.array(mm[k + "_n"]) - np.array(mm[k + "_vs"]) / REF
        per += np.array(mm["ramp1_pending"]) + np.array(mm["ramp2_pending"])
        o["h1"], o["h2"] = float(per[:12].sum()), float(per[12:].sum())
        o["m2only"] = float((np.array(mm["m2_acc_n"]) - np.array(mm["m2_acc_vs"]) / REF).sum())
        o["m1only"] = float((np.array(mm["m1_acc_n"]) - np.array(mm["m1_acc_vs"]) / REF).sum())
        o["pend_ramps_min"] = float(np.sum(mm["ramp1_pending"]) + np.sum(mm["ramp2_pending"]))
        o["last5_m"] = float(per[-5:].sum()); o["first5_m"] = float(per[:5].sum())
    return o
IDX = {}
def boot(d, lo=2.5, hi=97.5):
    n = len(d)
    if n not in IDX:
        IDX[n] = np.random.default_rng(20261110).integers(0, n, (10_000, n))
    b = np.median(d[IDX[n]], axis=1)
    return float(np.median(d)), float(np.percentile(b, lo)), float(np.percentile(b, hi))
def table(T, cell, arms, learners, seeds):
    """arm -> measure -> array over seeds; 'v3w' = per-seed mean of the learners."""
    M = {}
    for a in list(arms) + list(learners):
        rows = [measures(T[(cell, a)][s]) for s in seeds]
        keys = set.intersection(*(set(x) for x in rows))
        M[a] = {k: np.array([x[k] for x in rows]) for k in keys}
    keys = set.intersection(*(set(M[l]) for l in learners))
    M["v3w"] = {k: np.mean([M[l][k] for l in learners], axis=0) for k in keys}
    return M

def boot_stack(D, lo=2.5, hi=97.5):
    """D: learners x seeds paired differences; statistic = median over all learner-seed differences; seeds resampled together."""
    n = D.shape[1]
    if n not in IDX:
        IDX[n] = np.random.default_rng(20261110).integers(0, n, (10_000, n))
    b = np.median(D[:, IDX[n]].transpose(1, 0, 2).reshape(10_000, -1), axis=1)
    return float(np.median(D)), float(np.percentile(b, lo)), float(np.percentile(b, hi))
def boot_mean(d, lo=2.5, hi=97.5):
    n = len(d)
    if n not in IDX:
        IDX[n] = np.random.default_rng(20261110).integers(0, n, (10_000, n))
    b = np.mean(d[IDX[n]], axis=1)
    return float(np.mean(d)), float(np.percentile(b, lo)), float(np.percentile(b, hi))
