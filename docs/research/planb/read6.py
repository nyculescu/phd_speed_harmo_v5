"""Plan B S6 reading (planb.md §8, V480): cell outcomes W, W-b, the metric-win variants, T and L; the study outcome; the mandatory
per-policy and T2 clauses; the label-swap nulls; the resilience reading R; the adaptation gain; the report-only map. Read once, by
this committed script, on the S6 rows.

Statistic: effect = sign x median(P - O) / median(O) x 100 over paired seeds, positive = v3w better; P is the per-seed mean over the
5 learners; percentile bootstrap, 20,000 resamples, one index matrix (rng 20261108) for every comparison. Side constraints use
paired means on the same matrix. Sentence-feeding readings use 1 - 0.05/m; harm, braking and side-constraint bounds use 95 %.

Before any statistic, every arm of every cell (and every S row the resilience reading needs) must hold exactly the expected seeds
minus that condition's crash drops; a gap, a duplicate, a stray name or a seed outside the range stops the reading. read6 never
labels a cell "did not bind": S2 drops come from s2.json.

usage: read6.py ROWS.jsonl CONFIG.json OUT.json [--drops DROPS.json] [--seeds LO-HI]
  CONFIG: plan6.py's read6_config.json: {"m", "cells", "learners", "opponents": {cell: [...]}, "drain_cap", "seed_range": [lo, hi],
           "s_alias": {name: S twin}, "omitted", "p333", "nc", "t3e", "e3c", "e3d", "null_swaps"}
  DROPS: {condition: [seeds]} from run6.py, seeds that crashed on every attempt (planb.md §8.3); each is dropped from every arm there.
  --seeds: the S5 smoke range instead of the configured one; the output is then labelled SMOKE."""
import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

B, RNG = 20_000, 20261108
P95 = (2.5, 97.5)
TAU_BRAKE = 10.0     # % excess of robust braking per vehicle-km (V354)
TOL_COLL, TOL_FULL = 0.02, 0.10     # per run, one-sided 95 % upper bound of mean(P - O)
FLOW_PCT, CF_PER_RUN, LEARNERS_MIN = -0.5, 20.0, 4
HARM_DELAY, HARM_CF = -2.0, -10.0
NULL_FACTOR = 1.5
ROBUST_BIN = {"car": 2, "alks": 2, "truck": 1}


def level(m: int) -> tuple:
    return (2.5 / m, 100.0 - 2.5 / m)


REF_SPEED = 100.0 / 3.6


def location(r: dict) -> dict:
    """PR-28's location keys of one row: delay (veh-s - dist / 27.78), close-following and robust braking by road group and period;
    ramp-2 lane-end stops."""
    out = {f"delay|{g}|{p}": v - r["m_road_dist"].get(g, {}).get(p, 0.0) / REF_SPEED for g, x in r["m_road_vs"].items() for p, v in x.items()}
    out |= {f"cf|{g}|{p}": float(v) for g, x in r["m_road_ttc3"].items() for p, v in x.items()}
    out |= {f"brk|{g}|{p}": float(v) for g, x in r["m_robust_road"].items() for p, v in x.items()}
    out["end_stop2"] = float(r.get("end_stop2") or 0.0)
    return out


def derive(r: dict) -> dict:
    """The values the reading and the report map use, from one S6 row with the pack."""
    ev = sum(sum(r[f"m_peak_{c}"][b:]) for c, b in ROBUST_BIN.items())
    km = sum(r[f"m_dist_m_{c}"] for c in ROBUST_BIN) / 1000.0
    return {"all_delay": float(r["all_delay"]), "ttc_net": float(r["ttc_net"]), "passed": float(r["passed"]),
            "collisions": float(r["collisions"]), "alks_full_moving": float(r.get("alks_full_moving") or 0.0),
            "robust_rate": 1000.0 * ev / km if km > 0 else 0.0, "stuck_n": float(r["m_stuck_n"]), "pending_end": float(r["m_pending_end"]),
            "b3_step": float(r.get("b3_step") or 0.0), "b45_step": float(r.get("b45_step") or 0.0), "alks_past": float(sum(r["m_peak_alks"][4:8])),
            "ttt": float(r["N"]), "loc": location(r)}


KEYS = ("all_delay", "ttc_net", "passed", "collisions", "alks_full_moving", "robust_rate", "stuck_n", "pending_end", "b3_step", "b45_step",
        "alks_past", "ttt")
MEASURES = (("delay", "all_delay", -1), ("cf", "ttc_net", -1), ("flow", "passed", 1), ("robust_braking", "robust_rate", -1),
            ("alks_past_limit", "alks_past", -1), ("b45_step", "b45_step", -1), ("b3_step", "b3_step", -1), ("ttt", "ttt", -1))


class Stat:
    """Paired statistics on one index matrix."""

    def __init__(self, n: int, b: int = B, seed: int = RNG):
        self.idx = np.random.default_rng(seed).integers(0, n, (b, n))

    def eff(self, P: np.ndarray, O: np.ndarray, sign: int = -1) -> tuple:
        d = sign * (P - O) / max(float(np.median(O)), 1e-9) * 100.0
        return float(np.median(d)), np.median(d[self.idx], axis=1)

    def mean_diff(self, P: np.ndarray, O: np.ndarray) -> tuple:
        d = P - O
        return float(np.mean(d)), np.mean(d[self.idx], axis=1)

    def med_diff(self, d: np.ndarray) -> tuple:
        return float(np.median(d)), np.median(d[self.idx], axis=1)


def ci(boot: np.ndarray, pct: tuple) -> tuple:
    lo, hi = np.percentile(boot, pct)
    return float(lo), float(hi)


def comparison(st: Stat, P: dict, O: dict, pct: tuple) -> dict:
    """One opponent: every quantity the cell rules read."""
    d, db = st.eff(P["all_delay"], O["all_delay"])
    c, cb = st.eff(P["ttc_net"], O["ttc_net"])
    f, fb = st.eff(P["passed"], O["passed"], 1)
    x, xb = st.eff(P["robust_rate"], O["robust_rate"], 1)     # excess: positive = v3w brakes more
    col, colb = st.mean_diff(P["collisions"], O["collisions"])
    fu, fub = st.mean_diff(P["alks_full_moving"], O["alks_full_moving"])
    return {"delay": (d, *ci(db, pct)), "delay95": (d, *ci(db, P95)), "cf": (c, *ci(cb, pct)), "cf95": (c, *ci(cb, P95)),
            "cf_per_run": float(np.median(O["ttc_net"] - P["ttc_net"])), "flow": (f, *ci(fb, pct)), "flow95": (f, *ci(fb, P95)),
            "brake_excess": (x, *ci(xb, P95)),
            "coll_ub": float(np.percentile(colb, 95.0)), "coll_mean": col, "full_ub": float(np.percentile(fub, 95.0)), "full_mean": fu}


def metric_ok(c: dict) -> bool:
    return c["delay"][1] > 0 and c["cf"][1] > 0 and c["cf_per_run"] >= CF_PER_RUN


def gates(c: dict) -> dict:
    return {"flow": c["flow"][0] >= FLOW_PCT, "collisions": c["coll_ub"] <= TOL_COLL, "full_emergency": c["full_ub"] <= TOL_FULL}


def harm(c: dict) -> list:
    out = []
    if c["delay95"][0] < HARM_DELAY and c["delay95"][2] < 0:
        out.append("delay")
    if c["cf95"][0] < HARM_CF and c["cf95"][2] < 0:
        out.append("close-following")
    return out


def drain_fail(rows: list, cap: float) -> bool:
    return any(r["stuck_n"] > 0 or r["pending_end"] > cap for r in rows)


def stack(T: dict, cell: str, name: str, seeds: list) -> dict:
    return {k: np.array([T[(cell, name)][s][k] for s in seeds]) for k in KEYS}


def arm(T: dict, cell: str, learners: list, seeds: list) -> dict:
    L = [stack(T, cell, n, seeds) for n in learners]
    return {k: np.mean([x[k] for x in L], axis=0) for k in KEYS}


def w_rule(st: Stat, P: dict, opp: dict, pct: tuple) -> dict:
    """The arm conditions of W (without the learner condition and drain), against every opponent."""
    comps = {o: comparison(st, P, O, pct) for o, O in opp.items()}
    metric = all(metric_ok(c) for c in comps.values())
    gate = {o: gates(c) for o, c in comps.items()}
    gate_ok = all(all(g.values()) for g in gate.values())
    brake_failed = [o for o, c in comps.items() if c["brake_excess"][1] > TAU_BRAKE]
    brake_point = [o for o, c in comps.items() if c["brake_excess"][0] > TAU_BRAKE]
    return {"comps": comps, "metric": metric, "gate": gate, "gate_ok": gate_ok, "brake_failed": brake_failed, "brake_point": brake_point}


def pt(P: dict, O: dict, key: str, sign: int = -1) -> float:
    """confirmatory 3's raw() point: median of sign x (P - O) / median(O) x 100 over paired seeds."""
    return float(np.median(sign * (P[key] - O[key]) / max(float(np.median(O[key])), 1e-9) * 100.0))


def pmed(A: dict, B: dict, key: str) -> float:
    return float(np.median(A[key] - B[key]))


def t2_policy(st: Stat, P: dict, opp: dict, p333: dict, pct: tuple) -> bool:
    """Round 2's per-policy bar (round_2.md:199-202; decide1.tuned, decide3.fails, limits, anchored) against every opponent in opp, at
    pct; the close-following interval from the cell's index matrix (planb.md §8.1)."""
    for O in opp.values():
        c, cb = st.eff(P["ttc_net"], O["ttc_net"])
        ev = pt(P, O, "alks_full_moving") >= -5.0 or pmed(P, O, "alks_full_moving") <= 5.0
        if not (c >= 10.0 and ci(cb, pct)[0] > 0 and pmed(O, P, "ttc_net") >= 20.0 and pt(P, O, "all_delay") >= -2.0 and pt(P, O, "passed", 1) >= -0.5
                and pt(P, O, "b3_step") >= -5.0 and ev and P["collisions"].sum() <= O["collisions"].sum() + 1):
            return False
    return pt(P, p333, "all_delay") >= -5.0 and pt(P, p333, "passed", 1) >= -1.0


def counted(opp: dict, p333: dict) -> dict:
    """Round 2's counting filter (decide1.tuned): opponents whose delay is at most 2 % above p333's. Report-only in Plan B."""
    return {o: O for o, O in opp.items() if pt(O, p333, "all_delay") >= -2.0}


def swap_null(d: np.ndarray, pct_lo: float, swaps: int, rng_seed: int, b: int = B) -> float:
    """Share of sign-flipped copies of the paired differences d (each seed's pair swapped with probability 1/2) whose bootstrap lower
    bound is above 0: the false "better" rate of the statistic on these rows."""
    rng = np.random.default_rng(rng_seed)
    st = Stat(len(d), b, rng_seed + 1)
    hits = 0
    for _ in range(swaps):
        x = d * rng.choice((-1.0, 1.0), len(d))
        hits += np.percentile(np.median(x[st.idx], axis=1), pct_lo) > 0
    return hits / swaps


def cell_outcome(T: dict, cfg: dict, cell: str, seeds: list, st: Stat) -> dict:
    m, pct = cfg["m"], level(cfg["m"])
    learners, opp_names = cfg["learners"], cfg["opponents"][cell]
    P = arm(T, cell, learners, seeds)
    opp = {o: stack(T, cell, o, seeds) for o in opp_names}
    w = w_rule(st, P, opp, pct)
    harmed = {o: h for o, c in w["comps"].items() if (h := harm(c))}
    per_l = {n: stack(T, cell, n, seeds) for n in learners}
    l_signs = {n: all(st.eff(per_l[n]["all_delay"], O["all_delay"])[0] > 0 and st.eff(per_l[n]["ttc_net"], O["ttc_net"])[0] > 0 for O in opp.values())
               for n in learners}
    n_signs = sum(l_signs.values())
    drain = drain_fail([T[(cell, n)][s] for n in learners for s in seeds], cfg["drain_cap"][cell])
    if harmed:
        out = "L"
    elif w["metric"] and w["brake_failed"]:
        out = "metric win, braking constraint failed"
    elif w["metric"] and (not w["gate_ok"] or drain):
        out = "metric win, gate failure"
    elif w["metric"] and n_signs < LEARNERS_MIN:
        out = "arm win, learners inconsistent"
    elif w["metric"]:
        out = "W-b" if w["brake_point"] else "W"
    else:
        out = "T"
    res = {"cell": cell, "outcome": out, "harm": harmed, "learner_signs": l_signs, "n_learner_signs": n_signs, "drain_fail": drain,
           "brake_failed": w["brake_failed"], "brake_point_over": w["brake_point"], "gate": w["gate"], "pct": pct,
           "comparisons": w["comps"]}
    if out in ("W", "W-b"):
        k = 0
        for n in learners:
            wl = w_rule(st, per_l[n], opp, pct)
            k += wl["metric"] and wl["gate_ok"] and not wl["brake_failed"] and not drain_fail([T[(cell, n)][s] for s in seeds], cfg["drain_cap"][cell])
        res["k_policies"] = k
        p333 = stack(T, cell, cfg["p333"], seeds)
        res["t2_policies"] = sum(t2_policy(st, per_l[n], opp, p333, pct) for n in learners)
        res["t2_passes"] = res["t2_policies"] >= LEARNERS_MIN
        res["closest"] = {m: min(w["comps"], key=lambda o: w["comps"][o][m][1]) for m in ("delay", "cf", "flow")}
        d4 = {}     # claim review D4's "[x] % [CI]": per-learner points against the closest opponent, the lowest per-learner bound, the arm
        for meas, key in (("delay", "all_delay"), ("cf", "ttc_net")):
            O = opp[res["closest"][meas]][key]
            per = [st.eff(per_l[n][key], O) for n in learners]
            d4[meas] = {"learner_points": [p for p, _ in per], "lowest_learner_lower": min(ci(b, pct)[0] for _, b in per),
                        "arm": w["comps"][res["closest"][meas]][meas]}
        res["d4"] = d4
    return res


def null_check(T: dict, cfg: dict, cell: str, seeds: list, res: dict) -> dict:
    """W's binding comparisons (the closest opponent on each measure) under the label-swap null, before any sentence."""
    P = arm(T, cell, cfg["learners"], seeds)
    pct, out = level(cfg["m"]), {}
    nominal = pct[0] / 100.0
    for meas, key in (("delay", "all_delay"), ("cf", "ttc_net")):
        o = res["closest"][meas]
        O = stack(T, cell, o, seeds)[key]
        d = -(P[key] - O) / max(float(np.median(O)), 1e-9) * 100.0
        rate = swap_null(d, pct[0], cfg.get("null_swaps", 2000), RNG + 7)
        out[meas] = {"opponent": o, "false_better": rate, "nominal": nominal, "ok": rate <= NULL_FACTOR * nominal}
    return out


def resilience(T: dict, cfg: dict, cell: str, seeds: list, st: Stat) -> dict:
    """R(o) = median(loss_o - loss_v3w), loss = delay in the cell minus delay in S on the same seed, each controller as tuned for the
    cell; an opponent deduplicated in S reads its twin's S rows (plan6's s_alias)."""
    pct = level(cfg["m"])
    sn = lambda o: cfg.get("s_alias", {}).get(o, o)
    lw = arm(T, cell, cfg["learners"], seeds)["all_delay"] - arm(T, "S", cfg["learners"], seeds)["all_delay"]
    nc_loss = float(np.median(stack(T, cell, cfg["nc"], seeds)["all_delay"] - stack(T, "S", cfg["nc"], seeds)["all_delay"]))
    out = {}
    for o in cfg["opponents"][cell]:
        lo = stack(T, cell, o, seeds)["all_delay"] - stack(T, "S", sn(o), seeds)["all_delay"]
        r, rb = st.med_diff(lo - lw)
        rate = swap_null(lo - lw, pct[0], cfg.get("null_swaps", 2000), RNG + 11)
        out[o] = {"R": (r, *ci(rb, pct)), "pct_of_nc_loss": 100.0 * r / nc_loss if nc_loss else None, "null_false_better": rate,
                  "null_ok": rate <= NULL_FACTOR * pct[0] / 100.0}
    ok_null = all(v["null_ok"] for v in out.values())
    return {"per_opponent": out, "nc_median_loss": nc_loss, "null_ok": ok_null,
            "passes": ok_null and all(v["R"][1] > 0 for v in out.values()),
            "reading": "passes" if ok_null and all(v["R"][1] > 0 for v in out.values()) else ("statistic failed its null" if not ok_null else "not shown")}


def adaptation_gain(T: dict, cfg: dict, cell: str, seeds: list, st: Stat) -> dict:
    """AG = e(v3w vs 3E-T) / e(tuned vs 3E-T): 3E-C on close-following, 3E-D on delay; read only if the denominator's 95 % lower bound
    is at least half its point estimate."""
    P = arm(T, cell, cfg["learners"], seeds)
    t3 = stack(T, cell, cfg["t3e"], seeds)
    out = {}
    for meas, key, tuned in (("cf", "ttc_net", cfg["e3c"].get(cell)), ("delay", "all_delay", cfg["e3d"].get(cell))):
        if not tuned:
            continue
        num, nb = st.eff(P[key], t3[key])
        den, db = st.eff(stack(T, cell, tuned, seeds)[key], t3[key])
        lo95 = ci(db, P95)[0]
        read = den > 0 and lo95 >= 0.5 * den
        out[meas] = {"num": (num, *ci(nb, P95)), "den": (den, *ci(db, P95)), "read": read,
                     "AG": (num / den, *ci(nb / np.where(np.abs(db) > 1e-12, db, np.nan), P95)) if read else None}
    return out


def no_control(T: dict, cfg: dict, cell: str, seeds: list, st: Stat) -> dict:
    P = arm(T, cell, cfg["learners"], seeds)
    nc = stack(T, cell, cfg["nc"], seeds)
    d, db = st.eff(P["all_delay"], nc["all_delay"])
    c, cb = st.eff(P["ttc_net"], nc["ttc_net"])
    c95 = (c, *ci(cb, P95))
    return {"delay": (d, *ci(db, level(cfg["m"]))), "cf95": c95, "cf_shown_higher": c95[0] < HARM_CF and c95[2] < 0}


PR28_ROADS = ("4a", "4", "ramp2", "pending_ramp2", "junction")


def pr28(T: dict, cfg: dict, cell: str, seeds: list, o: str) -> dict:
    """§1's PR-28 location rule (V482): the median paired road-delay difference (o minus v3w's arm) over 4a, 4, ramp 2, its insertion
    queue and junction lanes, divided by the same over every road group; read only if the denominator's point is above 0."""
    def road(n, s, only):
        return sum(v for k, v in T[(cell, n)][s]["loc"].items() if k.startswith("delay|") and (only is None or k.split("|")[1] in only))
    out = {}
    for tag, only in (("num", PR28_ROADS), ("den", None)):
        P = np.array([np.mean([road(n, s, only) for n in cfg["learners"]]) for s in seeds])
        O = np.array([road(o, s, only) for s in seeds])
        out[tag] = float(np.median(O - P))
    read = out["den"] > 0
    share = out["num"] / out["den"] if read else None
    return {"opponent": o, **out, "read": read, "share": share, "adds_pr28": bool(read and share > 0.5)}


def tile(meas: str, e: tuple) -> str:
    """V462(1)'s descriptive tile on the arm at 95 %: W, L or T (delay: 5 % / 2 %; close-following: 10 % / 10 %)."""
    win, lose = (5.0, -2.0) if meas == "delay" else (10.0, -10.0)
    return "W" if e[0] >= win and e[1] > 0 else "L" if e[0] < lose and e[2] < 0 else "T"


def markers(P: dict, O: dict) -> list:
    """T2's side limits a tile breaches (flow, braking at 3 m/s², moving full-emergency events, collisions)."""
    ev = pt(P, O, "alks_full_moving") >= -5.0 or pmed(P, O, "alks_full_moving") <= 5.0
    return [k for k, ok in (("flow", pt(P, O, "passed", 1) >= -0.5), ("brake", pt(P, O, "b3_step") >= -5.0), ("events", ev),
                            ("coll", P["collisions"].sum() <= O["collisions"].sum() + 1)) if not ok]


def report_map(T: dict, cfg: dict, cond: str, seeds: list, st: Stat, opp_names: list) -> dict:
    """planb.md §8.7's operating map in one condition: v3w's arm against every opponent on every measure (positive = v3w better),
    95 % and 1 - 0.05/m intervals, the V462(1) tile with its markers and the count of single policies whose own tile is W, and each
    learner's points. Report-only."""
    pct = level(cfg["m"])
    P = arm(T, cond, cfg["learners"], seeds)
    per_l = {n: stack(T, cond, n, seeds) for n in cfg["learners"]}
    out = {}
    for o in opp_names:
        O = stack(T, cond, o, seeds)
        row = {}
        for meas, key, sign in MEASURES:
            e, b = st.eff(P[key], O[key], sign)
            row[meas] = {"effect": e, "ci95": ci(b, P95), "ci_m": ci(b, pct)}
        for meas in ("delay", "cf"):
            row[meas]["tile"] = tile(meas, (row[meas]["effect"], *row[meas]["ci95"]))
            key = "all_delay" if meas == "delay" else "ttc_net"
            row[meas]["policies_w"] = sum(tile(meas, (lambda e, b: (e, *ci(b, P95)))(*st.eff(per_l[n][key], O[key]))) == "W" for n in cfg["learners"])
        row["markers"] = markers(P, O)
        row["per_learner"] = {n: {m: pt(per_l[n], O, k) for m, k in (("delay", "all_delay"), ("cf", "ttc_net"))} for n in cfg["learners"]}
        out[o] = row
    return out


def location_table(T: dict, cfg: dict, cell: str, seeds: list, names: list) -> dict:
    """PR-28: medians over seeds of each location key, for v3w's arm (per-seed mean over the learners), every opponent and no control."""
    keys = sorted({k for n in cfg["learners"] + names for s in seeds for k in T[(cell, n)][s]["loc"]})
    get = lambda n, s, k: T[(cell, n)][s]["loc"].get(k, 0.0)
    out = {"v3w": {k: float(np.median([np.mean([get(n, s, k) for n in cfg["learners"]]) for s in seeds])) for k in keys}}
    for n in names:
        out[n] = {k: float(np.median([get(n, s, k) for s in seeds])) for k in keys}
    return out


def overfit(T: dict, cfg: dict, cell: str, seeds: list, st: Stat) -> dict:
    """Each opponent against p333 in the cell on the S6 seeds, at 95 % (half of §8.7's overfitting check; the tuning-seed half comes
    from the stage records)."""
    pp = stack(T, cell, cfg["p333"], seeds)
    out = {}
    for o in cfg["opponents"][cell]:
        if o == cfg["p333"]:
            continue
        O = stack(T, cell, o, seeds)
        out[o] = {m: (lambda e, b: (e, *ci(b, P95)))(*st.eff(O[k], pp[k])) for m, k in (("delay", "all_delay"), ("cf", "ttc_net"))}
    return out


def expected(cfg: dict) -> dict:
    """condition -> the arm names whose rows the reading needs."""
    out = {}
    for c in cfg["cells"]:
        extra = [cfg["t3e"], *(x for x in (cfg["e3c"].get(c), cfg["e3d"].get(c)) if x)]
        out[c] = set(cfg["learners"]) | set(cfg["opponents"][c]) | {cfg["nc"], *extra}
    sn = lambda o: cfg.get("s_alias", {}).get(o, o)
    out["S"] = set(cfg["learners"]) | {cfg["nc"]} | {sn(o) for c in cfg["cells"] for o in cfg["opponents"][c]}
    return out


def complete(T: dict, cfg: dict, seeds: list, drops: dict) -> dict:
    """condition -> the seeds read there (the range minus its drops); stops on a missing arm or seed, or a seed outside the range."""
    use = {}
    for cond, names in expected(cfg).items():
        want = sorted(set(seeds) - set(drops.get(cond, [])))
        bad = {}
        for n in sorted(names):
            have = set(T.get((cond, n), {}))
            if missing := sorted(set(want) - have):
                bad[n] = {"missing": missing[:10], "n_missing": len(missing)}
            if stray := sorted(have - set(seeds)):
                bad[n] = {**bad.get(n, {}), "outside_range": stray[:10]}
        if bad:
            raise SystemExit(f"{cond}: rows incomplete {bad}")
        use[cond] = want
    return use


def load_rows(path, cfg: dict, seeds: list) -> dict:
    """(condition, arm) -> seed -> derived values; a row's name is 'condition|arm'. Stops on a duplicate, a stray name or seed."""
    want, ok = expected(cfg), set(seeds)
    T = defaultdict(dict)
    for line in open(path):
        r = json.loads(line)
        cond, name = r["name"].split("|", 1)
        if r.get("cell", cond) != cond or r.get("arm", name) != name:
            raise SystemExit(f"row {r['name']} says cell {r.get('cell')}, arm {r.get('arm')}")
        if name not in want.get(cond, ()):
            raise SystemExit(f"row {r['name']} is not in the reading's arms")
        if r["seed"] not in ok:
            raise SystemExit(f"row {r['name']} on seed {r['seed']}, outside {seeds[0]}-{seeds[-1]}")
        if r["seed"] in T[(cond, name)]:
            raise SystemExit(f"duplicate row {r['name']} {r['seed']}")
        T[(cond, name)][r["seed"]] = derive(r)
    return dict(T)


def read(T: dict, cfg: dict, drops: dict | None = None, seeds: list | None = None) -> dict:
    drops = drops or {}
    seeds = seeds or list(range(cfg["seed_range"][0], cfg["seed_range"][1] + 1))
    use = complete(T, cfg, seeds, drops)
    cells = {}
    for cell in cfg["cells"]:
        sd = use[cell]
        st = Stat(len(sd))
        res = cell_outcome(T, cfg, cell, sd, st)
        res["n_seeds"], res["dropped_seeds"] = len(sd), sorted(drops.get(cell, []))
        res["no_control"] = no_control(T, cfg, cell, sd, st)
        res["adaptation_gain"] = adaptation_gain(T, cfg, cell, sd, st)
        res["map"] = report_map(T, cfg, cell, sd, st, cfg["opponents"][cell])
        res["location"] = location_table(T, cfg, cell, sd, cfg["opponents"][cell] + [cfg["nc"]])
        res["pr28"] = pr28(T, cfg, cell, sd, res["closest"]["delay"]) if "closest" in res else None
        res["overfit_vs_p333"] = overfit(T, cfg, cell, sd, st)
        opp = {o: stack(T, cell, o, sd) for o in cfg["opponents"][cell]}
        p333 = stack(T, cell, cfg["p333"], sd)
        filt = counted(opp, p333)
        res["t2_counting_filter"] = {"counted": sorted(filt), "policies": sum(t2_policy(st, stack(T, cell, n, sd), filt, p333, level(cfg["m"])) for n in cfg["learners"])}
        if res["outcome"] in ("W", "W-b"):
            res["null"] = null_check(T, cfg, cell, sd, res)
            if not all(v["ok"] for v in res["null"].values()):
                res["outcome_before_null"], res["outcome"] = res["outcome"], "statistic failed its null"
            else:
                rs = sorted(set(sd) & set(use["S"]))
                res["resilience"] = resilience(T, cfg, cell, rs, st if rs == sd else Stat(len(rs)))
                res["resilience"]["n_seeds"] = len(rs)
        cells[cell] = res
    s_names = sorted(expected(cfg)["S"] - set(cfg["learners"]) - {cfg["nc"]})
    s_st = Stat(len(use["S"]))
    outs = [c["outcome"] for c in cells.values()]
    passed = any(o in ("W", "W-b") for o in outs) and "L" not in outs
    vetoed = [c for c, r in cells.items() if r["outcome"] in ("W", "W-b") and "L" in outs]
    return {"study": "PASS" if passed else "NULL", "vetoed_cells": vetoed, "cells": cells, "m": cfg["m"], "omitted": cfg.get("omitted", {}),
            "S": {"n_seeds": len(use["S"]), "dropped_seeds": sorted(drops.get("S", [])), "map": report_map(T, cfg, "S", use["S"], s_st, s_names)}}


def main(argv: list) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("rows")
    ap.add_argument("config")
    ap.add_argument("out")
    ap.add_argument("--drops")
    ap.add_argument("--seeds")
    a = ap.parse_args(argv)
    cfg = json.loads(Path(a.config).read_text())
    if a.seeds:
        lo, hi = map(int, a.seeds.split("-"))
        seeds = list(range(lo, hi + 1))
    else:
        seeds = list(range(cfg["seed_range"][0], cfg["seed_range"][1] + 1))
    drops = json.loads(Path(a.drops).read_text()) if a.drops else {}
    res = read(load_rows(a.rows, cfg, seeds), cfg, drops, seeds)
    res["smoke"] = bool(a.seeds)
    Path(a.out).write_text(json.dumps(res, indent=1, default=float))
    if a.seeds:     # S5: the reader runs end to end; no performance field is printed
        print("SMOKE: read6 ran on", len(seeds), "seeds;", {c: r["n_seeds"] for c, r in res["cells"].items()})
        return 0
    print("study", res["study"], {c: (r["outcome"], r["n_seeds"], r["dropped_seeds"]) for c, r in res["cells"].items()})
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
