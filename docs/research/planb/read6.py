"""Plan B S6 reading (planb.md §8, V480): cell outcomes W, W-b, the metric-win variants, T and L; the study outcome; the mandatory
per-policy and T2 clauses; the label-swap nulls; the resilience reading R; the adaptation gain; the report-only map. Read once, by
this committed script, on the S6 rows.

Statistic: effect = sign x median(P - O) / median(O) x 100 over paired seeds, positive = v3w better; P is the per-seed mean over the
5 learners; percentile bootstrap, 20,000 resamples, one index matrix (rng 20261108) for every comparison. Side constraints use
paired means on the same matrix. Sentence-feeding readings use 1 - 0.05/m; harm, braking and side-constraint bounds use 95 %.

usage: read6.py ROWS.jsonl CONFIG.json OUT.json
  CONFIG: {"m": 2, "cells": [...], "learners": [...], "opponents": {cell: [...]}, "drain_cap": {cell: x}, "p333": "p333",
           "nc": "nc", "t3e": "3e", "e3c": {cell: name}, "e3d": {cell: name}, "null_swaps": 2000}"""
import json
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "conf3"))
import common as cc  # noqa: E402  confirmatory 3's raw(), for round 2's T2 clause only

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


def derive(r: dict) -> dict:
    """The values the reading uses, from one S6 row with the pack."""
    ev = sum(sum(r[f"m_peak_{c}"][b:]) for c, b in ROBUST_BIN.items())
    km = sum(r[f"m_dist_m_{c}"] for c in ROBUST_BIN) / 1000.0
    return {"all_delay": float(r["all_delay"]), "ttc_net": float(r["ttc_net"]), "passed": float(r["passed"]),
            "collisions": float(r["collisions"]), "alks_full_moving": float(r.get("alks_full_moving") or 0.0),
            "robust_rate": 1000.0 * ev / km if km > 0 else 0.0, "stuck_n": float(r["m_stuck_n"]), "pending_end": float(r["m_pending_end"]),
            "b3_step": float(r.get("b3_step") or 0.0)}


KEYS = ("all_delay", "ttc_net", "passed", "collisions", "alks_full_moving", "robust_rate", "stuck_n", "pending_end", "b3_step")


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
    f, _ = st.eff(P["passed"], O["passed"], 1)
    x, xb = st.eff(P["robust_rate"], O["robust_rate"], 1)     # excess: positive = v3w brakes more
    col, colb = st.mean_diff(P["collisions"], O["collisions"])
    fu, fub = st.mean_diff(P["alks_full_moving"], O["alks_full_moving"])
    return {"delay": (d, *ci(db, pct)), "delay95": (d, *ci(db, P95)), "cf": (c, *ci(cb, pct)), "cf95": (c, *ci(cb, P95)),
            "cf_per_run": float(np.median(O["ttc_net"] - P["ttc_net"])), "flow": f, "brake_excess": (x, *ci(xb, P95)),
            "coll_ub": float(np.percentile(colb, 95.0)), "coll_mean": col, "full_ub": float(np.percentile(fub, 95.0)), "full_mean": fu}


def metric_ok(c: dict) -> bool:
    return c["delay"][1] > 0 and c["cf"][1] > 0 and c["cf_per_run"] >= CF_PER_RUN


def gates(c: dict) -> dict:
    return {"flow": c["flow"] >= FLOW_PCT, "collisions": c["coll_ub"] <= TOL_COLL, "full_emergency": c["full_ub"] <= TOL_FULL}


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


def t2_policy(T: dict, cell: str, name: str, opp: list, p333: str, seeds: list, pct: tuple) -> bool:
    """Round 2's per-policy bar (round_2.md:199-202) against every opponent, no counting filter, at pct."""
    P = {s: T[(cell, name)][s] for s in seeds}
    A = lambda o: {s: T[(cell, o)][s] for s in seeds}
    for o in opp:
        O = A(o)
        e = cc.raw(P, O, "ttc_net", pct=pct)
        ev = cc.raw(P, O, "alks_full_moving")[0] >= -5.0 or cc.paired_median(P, O, "alks_full_moving") <= 5.0
        if not (e[0] >= 10.0 and e[1] > 0 and cc.paired_median(O, P, "ttc_net") >= 20.0 and cc.raw(P, O, "all_delay")[0] >= -2.0
                and cc.raw(P, O, "passed", 1)[0] >= -0.5 and cc.raw(P, O, "b3_step")[0] >= -5.0 and ev and cc.collisions(P) <= cc.collisions(O) + 1):
            return False
    pp = A(p333)
    return cc.raw(P, pp, "all_delay")[0] >= -5.0 and cc.raw(P, pp, "passed", 1)[0] >= -1.0


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
        res["t2_policies"] = sum(t2_policy(T, cell, n, opp_names, cfg["p333"], seeds, pct) for n in learners)
        res["t2_passes"] = res["t2_policies"] >= LEARNERS_MIN
        res["closest"] = {"delay": min(w["comps"], key=lambda o: w["comps"][o]["delay"][1]), "cf": min(w["comps"], key=lambda o: w["comps"][o]["cf"][1])}
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
    """R(o) = median(loss_o - loss_v3w), loss = delay in the cell minus delay in S on the same seed, each controller as tuned for the cell."""
    pct = level(cfg["m"])
    lw = arm(T, cell, cfg["learners"], seeds)["all_delay"] - arm(T, "S", cfg["learners"], seeds)["all_delay"]
    nc_loss = float(np.median(stack(T, cell, cfg["nc"], seeds)["all_delay"] - stack(T, "S", cfg["nc"], seeds)["all_delay"]))
    out = {}
    for o in cfg["opponents"][cell]:
        lo = stack(T, cell, o, seeds)["all_delay"] - stack(T, "S", o, seeds)["all_delay"]
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


def load_rows(path) -> dict:
    T = defaultdict(dict)
    for line in open(path):
        r = json.loads(line)
        T[(r["cell"], r["name"])][r["seed"]] = derive(r)
    return T


def read(T: dict, cfg: dict) -> dict:
    cells = {}
    for cell in cfg["cells"]:
        names = cfg["learners"] + cfg["opponents"][cell] + [cfg["nc"]]
        seeds = sorted(set.intersection(*(set(T[(cell, n)]) for n in names)))
        if not seeds:
            cells[cell] = {"cell": cell, "outcome": "did not bind"}
            continue
        st = Stat(len(seeds))
        res = cell_outcome(T, cfg, cell, seeds, st)
        res["n_seeds"] = len(seeds)
        res["no_control"] = no_control(T, cfg, cell, seeds, st)
        res["adaptation_gain"] = adaptation_gain(T, cfg, cell, seeds, st)
        if res["outcome"] in ("W", "W-b"):
            res["null"] = null_check(T, cfg, cell, seeds, res)
            if not all(v["ok"] for v in res["null"].values()):
                res["outcome_before_null"], res["outcome"] = res["outcome"], "statistic failed its null"
            else:
                res["resilience"] = resilience(T, cfg, cell, seeds, st)
        cells[cell] = res
    outs = [c["outcome"] for c in cells.values()]
    passed = any(o in ("W", "W-b") for o in outs) and "L" not in outs
    vetoed = [c for c, r in cells.items() if r["outcome"] in ("W", "W-b") and "L" in outs]
    return {"study": "PASS" if passed else "NULL", "vetoed_cells": vetoed, "cells": cells, "m": cfg["m"]}


def main(argv: list) -> int:
    if len(argv) != 3:
        print(__doc__)
        return 2
    rows, cfg, out = argv
    res = read(load_rows(rows), json.loads(Path(cfg).read_text()))
    Path(out).write_text(json.dumps(res, indent=1, default=float))
    print("study", res["study"], {c: r["outcome"] for c, r in res["cells"].items()})
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
