"""C1 readers (docs/local/research/protocols/c1_screen.md on v5b1, V521), each fixed before its data and run once by the remote script.

usage: read_c1.py ident ROWS OUT --cpu MODEL      §10 identity replays against S6
       read_c1.py checks ROWS OUT --st DIR         §6 (a) lane label and (b) PLANT OK
       read_c1.py gate ROWS OUT [--fallback]       §2 drain, stuck and bind
       read_c1.py pilot ROWS OUT --st DIR          §5 power: SEs, the n rule and the outcome table; never an effect
       read_c1.py screen OUT --rows R1 [R2] --st D1 [D2] --pilot PILOT.json --cell E30|E30s     §5 and §7

Statistic (C-D5): per learner, the median of paired % differences against the opponent (opponent's median in the denominator);
the deciding effect is the mean of the five, seeds resampled jointly (B = 20,000, rng 20261108). Positive = v3w better (less)."""
import argparse
import io
import json
import multiprocessing as mp
import re
import sys
from collections import defaultdict
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "planb"))
sys.path.insert(0, str(HERE.parent / "v505"))
import drain  # noqa: E402
import read6  # noqa: E402

V3W = ("w0u250", "w1u500", "w2u250", "w3u500", "w4u500")
S6_ROWS = Path("/home/catalin/work/phd/v5b1_runs/planb_s56_remote/s6/s6_rows.jsonl")
S6_CPU = "Xeon Platinum 8163"     # the S6 rental (V518, V519)
L975, L95 = (1.25, 98.75), (2.5, 97.5)
Z975, Z95 = 2.241402727604947, 1.959963984540054
DROP_VOID = 3     # common §4
# §4 road groups; delay adds the insertion queues
GROUP = {"4a": "merge2", "ramp2": "merge2", "pending_ramp2": "merge2", "3a": "merge1", "ramp1": "merge1", "pending_ramp": "merge1",
         "3": "between", "1": "event", "2": "event", "4": "down", "5": "down", "junction": "junction", "pending_main": "origin", "other": "other"}
AWAY = ("1", "2", "3", "4", "5")
# §5 rules
EDGE_K1 = 10.0
DELAY_MARGIN = -1.0
COST_PRESENT, COST_ABSENT = -3.0, -5.0
ELSE_TIES = 0.10
P0_BAR = 10.0
NULL_FACTOR = 1.5
NULL_SWAPS, NULL_B = 2000, 1000
NULL_BOUND_975 = 0.019     # §5's written bar ("at most 1.9 %"); the 95 % readings' bar is 3.75 %
# §5 power
PILOT_N, LADDER_N, INFLATE, Z80 = 60, (240, 480, 960, 1920), 1.15, 3.08
PLANNED = {"edge": 10.0, "delay": 1.0, "cost": 5.0}
TRUTHS = {     # §5: C's premise, the stored TRUCK mean-of-effects values, a null edge (vetoes at 0 under the premise)
    "premise": {"edge": 10.0, "cost": -5.0, "delay": 0.0, "else": 10.0, "ev45": 0.0, "jams": 0.0},
    "stored": {"edge": 12.68, "cost": -0.93, "delay": 0.14, "else": 30.54, "ev45": -4.10, "jams": -4.29},
    "null": {"edge": 0.0, "cost": 0.0, "delay": 0.0, "else": 0.0, "ev45": 0.0, "jams": 0.0}}
MEASURES = {"edge": ("3E-C_TRUCK", "ttc_net"), "cost": ("3E-C_TRUCK", "b45_step"), "delay": ("p333", "all_delay"),
            "else": ("3E-C_TRUCK", "ttc_away"), "ev45": ("3E-C_TRUCK", "events_ge45"), "jams": ("3E-C_TRUCK", "jams")}
# §2 drain
DRAIN_VEH, STUCK_SHARE, GATE_STUCK = 2.0, 0.01, 1
# §6
USE_COLL, USE_FULL = 0.05, 0.15
SENS_PCT, SENS_ALPHA = 10.0, 0.05
B_STUCK_MAX, B_COLL_UB, B_SAT_VEH, B_NULL = 1, 0.05, 2.0, 0.075
PREV_MIN = range(15, 20)     # the five minutes before V486's window (drain.WINDOW_MIN)


def gsum(d: dict, roads) -> float:
    """Sum of a road -> period -> value (or road -> value) map over roads; an absent road counts 0 (§4)."""
    out = 0.0
    for g in roads:
        x = d.get(g, 0.0)
        out += sum(x.values()) if isinstance(x, dict) else float(x)
    return out


def by_group(d: dict) -> dict:
    out = defaultdict(float)
    for road, x in d.items():
        out[GROUP.get(road, "other")] += sum(x.values()) if isinstance(x, dict) else float(x)
    return dict(out)


def split_sums(r: dict) -> list:
    """§10: the parts sum to the totals, absent keys as 0. Close-following and events exactly; braking and fuel within 1e-9
    relative; delay with insertion queues within 0.1 %."""
    bad = []
    rel = lambda a, b: abs(a - b) / max(abs(b), 1e-9)
    if "m_road_ttc3" in r and gsum(r["m_road_ttc3"], r["m_road_ttc3"]) != float(r["ttc_net"]):
        bad.append("ttc_net")
    if "m_road_ge45" in r and gsum(r["m_road_ge45"], r["m_road_ge45"]) != events_ge45(r):
        bad.append("events_ge45")
    b45 = sum(v for k, v in r.items() if k.startswith("b45_step_g_"))
    if rel(b45, float(r.get("b45_step") or 0.0)) > 1e-9 and abs(b45 - float(r.get("b45_step") or 0.0)) > 1e-9:
        bad.append("b45_step")
    fuel = sum(v for k, v in r.items() if k.startswith("fuel_g_"))
    if rel(fuel, float(r.get("fuel") or 0.0)) > 1e-9:
        bad.append("fuel")
    if "m_road_vs" in r:
        loc = read6.location(r)
        dl = sum(v for k, v in loc.items() if k.startswith("delay|"))
        if rel(dl, float(r["all_delay"])) > 1e-3:
            bad.append("delay")
    return bad


def events_ge45(r: dict) -> float:
    return float(sum(sum(r[f"m_peak_{c}"][3:]) for c in ("car", "alks", "truck")))     # read6.derive


VS_REL_STOP = 1e-2     # the side file is float32 (measure.py); stored rows drift up to 7.3e-4, so only a larger gap means another run


def jams_of(r: dict, st: Path | None) -> tuple:
    """Jam count of one run (read6's space-time reading, with its binding check), the jams by group of each cluster's head, and the
    binding's vs_rel (printed, as read6 v2.3 does)."""
    if st is None:
        return None, {}, None
    sp = read6.space_time(r, st)
    if sp.get("st_empty"):
        raise SystemExit(f"{r['name']} {r['seed']}: empty space-time file")
    b = sp["bind"]
    if not (b["run_s_equal"] and b["vs_rel"] < VS_REL_STOP):
        raise SystemExit(f"{r['name']} {r['seed']}: space-time file does not bind to its row ({b})")
    with np.load(io.BytesIO((st / r["m_st_file"]).read_bytes())) as z:
        w = read6.measure_module().waves(z["v"], z["n"], r["m_st_dt"], r["m_st_dx"])
    off = sorted((v, k) for k, v in r["m_offsets"].items() if k != "_end")
    heads = defaultdict(int)
    for c in w["jam_clusters"]:
        road = max((k for v, k in off if v <= c["head_m"]), default="1", key=lambda k: r["m_offsets"][k])
        heads[GROUP.get(road, "other")] += 1
    return float(sp["jams"]), dict(heads), float(b["vs_rel"])


def derive(r: dict, st: Path | None = None) -> dict:
    """The values C1 reads from one row."""
    ttc = r.get("m_road_ttc3", {})
    d = {"all_delay": float(r["all_delay"]), "ttc_net": float(r["ttc_net"]), "b45_step": float(r.get("b45_step") or 0.0),
         "events_ge45": events_ge45(r) if "m_peak_car" in r else None, "ttc_away": gsum(ttc, AWAY), "ttc_merge2": gsum(ttc, ("4a", "ramp2")),
         "ttc_merge1": gsum(ttc, ("3a", "ramp1")), "ttc_junction": gsum(ttc, ("junction",)),
         "b45_merge2": float(r.get("b45_step_g_4a", 0.0)) + float(r.get("b45_step_g_ramp2", 0.0)),
         "passed": float(r["passed"]), "N": float(r["N"]), "collisions": float(r["collisions"]), "stuck": float(r.get("m_stuck_n", 0)),
         "teleports": float(r.get("teleports", 0.0)), "end_stop": float(r.get("end_stop", 0.0)), "end_stop2": float(r.get("end_stop2", 0.0)),
         "alks_full_moving": float(r.get("alks_full_moving") or 0.0), "alks_b45_step": float(r.get("alks_b45_step") or 0.0),
         "fuel_km": float(r.get("fuel_km") or 0.0), "wall_s": r.get("wall_s"), "tau_on": [r.get("tau_on_match", 0.0), r.get("tau_on_n", 0.0)]}
    if "m_minute" in r:
        d |= {f"q_{k}": v for k, v in drain.series_from_row(r).items()}
        d["backlog_prev"] = drain.series_from_row(r, PREV_MIN)["backlog"]
    d["g_ttc"] = by_group(ttc)
    d["g_b45"] = by_group({k[len("b45_step_g_"):]: v for k, v in r.items() if k.startswith("b45_step_g_")})
    d["g_ge45"] = by_group(r.get("m_road_ge45", {}))
    d["g_fuel"] = by_group({k[len("fuel_g_"):]: v for k, v in r.items() if k.startswith("fuel_g_")})
    if "m_road_vs" in r:
        g = defaultdict(float)
        for k, v in read6.location(r).items():
            if k.startswith("delay|"):
                g[GROUP.get(k.split("|")[1], "other")] += v
        d["g_delay"] = dict(g)
    d["jams"], d["g_jams"], d["st_vs_rel"] = jams_of(r, st) if st is not None and r.get("m_st_file") else (None, {}, None)
    return d


def load(paths, sts=None, keep=None) -> dict:
    """(cell, arm) -> seed -> derived values, streaming the rows; a duplicate stops the reading."""
    sts = sts or [None] * len(paths)
    T = defaultdict(dict)
    for p, st in zip(paths, sts):
        for line in open(p):
            r = json.loads(line)
            if keep is not None and r["name"] not in keep:
                continue
            c, a = r["name"].split("|", 1)
            if r["seed"] in T[(c, a)]:
                raise SystemExit(f"duplicate row {r['name']} {r['seed']}")
            T[(c, a)][r["seed"]] = derive(r, Path(st) if st else None)
    return dict(T)


def drops_of(rows: Path) -> list:
    f = Path(rows).parent / "drops.json"
    return sorted({s for v in json.loads(f.read_text()).values() for s in v}) if f.is_file() else []


def col(T: dict, cell: str, arm: str, seeds: list, key: str) -> np.ndarray:
    return np.array([float(T[(cell, arm)][s][key]) for s in seeds])


def ci(b: np.ndarray, pct: tuple) -> tuple:
    lo, hi = np.percentile(b, pct)
    return float(lo), float(hi)


def diffs(P: np.ndarray, O: np.ndarray) -> np.ndarray:
    """Paired % differences, positive = P lower (better)."""
    return -(P - O) / max(float(np.median(O)), 1e-9) * 100.0


def moe(D: list, idx: np.ndarray) -> tuple:
    """Mean of the learners' medians: point and bootstrap draws on one index matrix."""
    return float(np.mean([np.median(d) for d in D])), np.mean([np.median(d[idx], axis=1) for d in D], axis=0)


def reading(D: list, idx: np.ndarray) -> dict:
    pt, b = moe(D, idx)
    lo, hi = ci(b, L975)
    lo95, hi95 = ci(b, L95)
    return {"pt": pt, "lo": lo, "hi": hi, "lo95": lo95, "hi95": hi95, "se": float(np.std(b))}


# §7, form A: one pure function for the screen, the pilot's simulation and the planted rows

def r_delay(x: dict) -> str:
    if x["pt"] is None:
        return "not resolvable"
    if x["lo"] > DELAY_MARGIN:
        return "KEPT"
    if x["pt"] <= DELAY_MARGIN and x["hi95"] < 0:
        return "WORSE"
    return "not resolvable"


def r_cost(x: dict) -> str:
    if x["hi"] < 0 and x["pt"] <= COST_PRESENT:
        return "present"
    if x["hi"] >= 0 and x["lo"] > COST_ABSENT:
        return "absent"
    return "undecided"


def r_else(x: dict, readable: bool = True) -> str:
    if not readable:
        return "not readable"
    if x["lo"] > 0:
        return "SHOWN"
    if x["hi95"] < 0:
        return "WORSE"
    return "NOT SHOWN"


def decide(x: dict) -> dict:
    """x: void (list of reasons), p0 (bool), p333_stuck (bool), else_readable (bool), and readings edge, delay, cost, else, ev45, jams,
    each {pt, lo, hi (97.5 %), lo95, hi95}. Returns the outcome and the readings it used, in §7's order."""
    if x.get("void"):
        return {"outcome": "VOID", "why": x["void"]}
    if not x["p0"]:
        return {"outcome": "P0 FAILS"}
    e = x["edge"]
    if not e["lo"] > 0:
        return {"outcome": "NOT RESOLVABLE (edge)" if e["hi"] >= EDGE_K1 else "K1 NO ROOM", "edge": e}
    if x.get("p333_stuck"):
        return {"outcome": "NOT RESOLVABLE (delay)", "why": "p333 failed the stuck part"}
    dl = r_delay(x["delay"])
    if dl == "WORSE":
        return {"outcome": "K2 DELAY", "delay": dl}
    if dl != "KEPT":
        return {"outcome": "NOT RESOLVABLE (delay)", "delay": dl}
    el = r_else(x["else"], x.get("else_readable", True))
    if el == "WORSE":
        return {"outcome": "K3 MERGES ONLY", "else": el}
    co = r_cost(x["cost"])
    if co == "present":
        return {"outcome": "ROOM WITH COST" if el == "SHOWN" else "ROOM WITH COST, merge-weighted", "else": el, "cost": co}
    if co == "absent":
        vetoes = [k for k in ("ev45", "jams") if x[k]["hi95"] < 0]
        return {"outcome": "COST ON ANOTHER MEASURE" if vetoes else "NO COST", "vetoes": vetoes, "else": el, "cost": co}
    return {"outcome": "COST UNDECIDED", "else": el, "cost": co}


OPENS = ("ROOM WITH COST", "ROOM WITH COST, merge-weighted")


def simulate(se: dict, truth: dict, corr: np.ndarray | None, draws: int = 20000, seed: int = 20261111) -> dict:
    """Outcome rates of decide() when each statistic is normal around the truth with the given SEs (and correlation); exploratory."""
    keys = list(MEASURES)
    rng = np.random.default_rng(seed)
    z = rng.standard_normal((draws, len(keys)))
    if corr is not None:
        z = z @ np.linalg.cholesky(corr + 1e-12 * np.eye(len(keys))).T
    out = defaultdict(int)
    for row in z:
        x = {"void": [], "p0": True}
        for j, k in enumerate(keys):
            pt = truth[k] + se[k] * row[j]
            x[k] = {"pt": pt, "lo": pt - Z975 * se[k], "hi": pt + Z975 * se[k], "lo95": pt - Z95 * se[k], "hi95": pt + Z95 * se[k]}
        out[decide(x)["outcome"]] += 1
    return {k: v / draws for k, v in sorted(out.items(), key=lambda kv: -kv[1])}


def n_rule(se60: dict, n_pilot: int = PILOT_N) -> dict:
    """§5: SE_n = 1.15 x SE_60 x sqrt(60 / n) (60: the pilot's seeds after drops); the smallest n of the ladder at which the edge,
    delay and cost are powered."""
    proj = {n: {k: INFLATE * se60[k] * np.sqrt(n_pilot / n) for k in se60} for n in LADDER_N}
    ok = {n: all(PLANNED[k] / proj[n][k] >= Z80 for k in PLANNED) for n in LADDER_N}
    n = next((m for m in LADDER_N if ok[m]), None)
    return {"n": n, "projected_se": proj, "powered": ok}


# screen pieces

def seeds_of(T: dict, cell: str, arms, seeds: list) -> list:
    miss = [f"{cell}|{a} {s}" for a in arms for s in seeds if s not in T.get((cell, a), {})]
    if miss:
        raise SystemExit(f"rows missing: {miss[:10]}")
    return seeds


def learner_diffs(T: dict, cell: str, opp: str, key: str, seeds: list) -> list:
    O = col(T, cell, opp, seeds, key)
    return [diffs(col(T, cell, w, seeds, key), O) for w in V3W]


def else_readable(T: dict, cell: str, seeds: list) -> dict:
    O = col(T, cell, "3E-C_TRUCK", seeds, "ttc_away")
    ties = [float(np.mean(col(T, cell, w, seeds, "ttc_away") - O == 0)) for w in V3W]
    meds = [float(np.median(d)) for d in learner_diffs(T, cell, "3E-C_TRUCK", "ttc_away", seeds)]
    ok = float(np.median(O)) > 0 and all(m != 0 for m in meds) and max(ties) <= ELSE_TIES
    return {"readable": ok, "opp_median": float(np.median(O)), "tie_share": ties, "learner_medians_zero": [m == 0 for m in meds]}


def swap_rates(D: list, idx: np.ndarray, swaps: int = NULL_SWAPS, seed: int = 20261112) -> dict:
    """Sign-flip null, per learner and seed: the false rate of each reading the measure feeds."""
    rng = np.random.default_rng(seed)
    hit = defaultdict(int)
    for _ in range(swaps):
        F = [d * rng.choice((-1.0, 1.0), len(d)) for d in D]
        x = reading(F, idx)
        hit["lo>0"] += x["lo"] > 0
        hit["present"] += x["hi"] < 0 and x["pt"] <= COST_PRESENT
        hit["hi95<0"] += x["hi95"] < 0
        hit["delay_worse"] += x["pt"] <= DELAY_MARGIN and x["hi95"] < 0
        hit["hi95==0"] += x["hi95"] == 0
    return {k: v / swaps for k, v in hit.items()}


def drain_screen(T: dict, cell: str, seeds: list) -> dict:
    """§2 per-arm drain on the screen rows: queues in V486's form against p333 (v3w averaged per seed first), and stuck rows."""
    q = lambda a, k: col(T, cell, a, seeds, f"q_{k}")
    ref = {k: q("p333", k) for k in drain.KEYS}
    out = {}
    for a in ("v3w", "3E-C_TRUCK", "nc"):
        ex = {k: float(np.mean((np.mean([q(w, k) for w in V3W], axis=0) if a == "v3w" else q(a, k)) - ref[k])) for k in drain.KEYS}
        out[a] = {"queue_excess": ex, "queue_fail": any(v > DRAIN_VEH for v in ex.values())}
    for a in ("v3w", "3E-C_TRUCK", "p333", "nc"):
        names = V3W if a == "v3w" else (a,)
        n_st = {w: int(sum(col(T, cell, w, seeds, "stuck") > 0)) for w in names}
        share = sum(n_st.values()) / (len(seeds) * len(names))
        out.setdefault(a, {}).update({"stuck_rows": n_st, "stuck_share": share, "stuck_fail": share > STUCK_SHARE})
    return out


def p0(T: dict, cell: str, seeds: list, idx: np.ndarray) -> dict:
    """CLAUDE.md's early KILL on delay: 3E-C_TRUCK or p333 against no control, positive = less delay."""
    nc = col(T, cell, "nc", seeds, "all_delay")
    out = {}
    for a in ("3E-C_TRUCK", "p333"):
        d = diffs(col(T, cell, a, seeds, "all_delay"), nc)
        b = np.median(d[idx], axis=1)
        out[a] = {"pt": float(np.median(d)), "ci95": ci(b, L95)}
        out[a]["pass"] = out[a]["pt"] >= P0_BAR and out[a]["ci95"][0] > 0
    ttc = col(T, cell, "nc", seeds, "ttc_net")
    out["printed_cf"] = {a: float(np.median(diffs(col(T, cell, a, seeds, "ttc_net"), ttc))) for a in ("3E-C_TRUCK", "p333")}
    out["pass"] = out["3E-C_TRUCK"]["pass"] or out["p333"]["pass"]
    return out


def printed(T: dict, cell: str, seeds: list, idx: np.ndarray) -> dict:
    """Never gating: the pooled arm, each learner, the 4-against-1 effects, the parts by group, side measures."""
    out = {}
    for k, (opp, key) in MEASURES.items():
        D = learner_diffs(T, cell, opp, key, seeds)
        O = col(T, cell, opp, seeds, key)
        pooled = diffs(np.mean([col(T, cell, w, seeds, key) for w in V3W], axis=0), O)
        out[k] = {"pooled": (float(np.median(pooled)), *ci(np.median(pooled[idx], axis=1), L975)),
                  "learners": {w: float(np.median(d)) for w, d in zip(V3W, D)}}
        out[k]["learner_range"] = [min(out[k]["learners"].values()), max(out[k]["learners"].values())]
        four = {}
        for i, w in enumerate(V3W):
            rest = np.mean([col(T, cell, v, seeds, key) for v in V3W if v != w], axis=0)
            d = diffs(rest, col(T, cell, w, seeds, key))
            four[w] = (float(np.median(d)), *ci(np.median(d[idx], axis=1), L95))
        out[k]["four_against_one"] = four
    groups = {}
    for gk in ("g_ttc", "g_b45", "g_ge45", "g_delay", "g_fuel", "g_jams"):
        groups[gk] = {a: {g: float(np.mean([T[(cell, a)][s].get(gk, {}).get(g, 0.0) for s in seeds]))
                          for g in sorted({g for s in seeds for g in T[(cell, a)][s].get(gk, {})})} for a in V3W + ("3E-C_TRUCK", "p333", "nc")}
    out["groups_mean"] = groups
    side = {}
    for a in V3W + ("3E-C_TRUCK", "p333", "nc"):
        side[a] = {k: float(np.mean(col(T, cell, a, seeds, k))) for k in ("collisions", "stuck", "teleports", "end_stop", "end_stop2", "passed", "N",
                                                                           "alks_full_moving", "alks_b45_step", "fuel_km")}
    out["side_means"] = side
    return out


def screen(T: dict, seeds: list, cell: str, dropped: list, pilot: dict | None = None, swaps: int = NULL_SWAPS, b: int = read6.B,
           cpus: list | None = None) -> dict:
    arms = V3W + ("3E-C_TRUCK", "p333", "nc")
    void = []
    if cpus is not None and len(set(cpus)) > 1:
        void.append(f"CPU-model change between pilot and screen ({sorted(set(cpus))}, §7)")
    if len(set(dropped)) > DROP_VOID:
        void.append(f"{len(set(dropped))} seeds dropped (common §4)")
    seeds = seeds_of(T, cell, arms, [s for s in seeds if s not in set(dropped)])
    n = len(seeds)
    idx = np.random.default_rng(read6.RNG).integers(0, n, (b, n))
    nidx = np.random.default_rng(read6.RNG + 1).integers(0, n, (NULL_B, n))
    dr = drain_screen(T, cell, seeds)
    for a in ("v3w", "3E-C_TRUCK"):
        if dr[a]["queue_fail"] or dr[a]["stuck_fail"]:
            void.append(f"per-arm drain: {a}")
    Ds = {k: learner_diffs(T, cell, opp, key, seeds) for k, (opp, key) in MEASURES.items()}
    R = {k: reading(D, idx) for k, D in Ds.items()}
    with ProcessPoolExecutor(len(Ds), mp_context=mp.get_context("fork")) as ex:     # one process per measure; each null is independent
        futs = {k: ex.submit(swap_rates, D, nidx, swaps) for k, D in Ds.items()}
        nulls = {k: f.result() for k, f in futs.items()}
    bound975, bound95 = NULL_BOUND_975, NULL_FACTOR * L95[0] / 100.0
    null_fail = [f"{k}:{r}" for k, r, bd in (("edge", "lo>0", bound975), ("cost", "present", bound975), ("else", "lo>0", bound975),
                                             ("delay", "delay_worse", bound95), ("else", "hi95<0", bound95)) if nulls[k][r] > bd]
    if null_fail:
        void.append("swap null: " + ", ".join(null_fail))
    veto_over = [k for k in ("ev45", "jams") if nulls[k]["hi95<0"] > bound95]
    er = else_readable(T, cell, seeds)
    pz = p0(T, cell, seeds, idx)
    x = {"void": void, "p0": pz["pass"], "p333_stuck": dr["p333"]["stuck_fail"], "else_readable": er["readable"], **R}
    out = {"cell": cell, "n": n, "dropped": dropped, "decision": decide(x), "readings": R, "nulls": nulls, "veto_null_over_bound": veto_over,
           "jams_hi95_zero": {"bootstrap_draws": float(np.mean(moe(Ds["jams"], idx)[1] == 0)), "reading": R["jams"]["hi95"] == 0,
                              "swap_replicates": nulls["jams"]["hi95==0"]},
           "else_parts": {k: reading(learner_diffs(T, cell, "3E-C_TRUCK", k, seeds), idx) for k in ("ttc_merge2", "ttc_merge1", "ttc_junction")},
           "side_file_binding": vs_rel_summary(T, cell, seeds),
           "else_readability": er, "p0": pz, "drain": dr, "printed": printed(T, cell, seeds, idx)}
    if pilot is not None and pilot.get("n"):
        proj = pilot["n_rule"]["projected_se"][str(pilot["n"])] if str(pilot["n"]) in pilot["n_rule"]["projected_se"] else pilot["n_rule"]["projected_se"][pilot["n"]]
        out["se_realised_vs_projected"] = {k: [R[k]["se"], proj.get(k)] for k in MEASURES}
    return out


def pilot(T: dict, seeds: list, cell: str, b: int = read6.B) -> dict:
    """§5: SEs of the six statistics at 60 seeds, their bootstrap correlation, R-else's opponent median and tie share, the n rule, and the
    outcome rates at each candidate n under the three truths. No effect is computed into the output."""
    arms = V3W + ("3E-C_TRUCK", "p333", "nc")
    seeds = seeds_of(T, cell, arms, seeds)
    n = len(seeds)
    idx = np.random.default_rng(read6.RNG).integers(0, n, (b, n))
    draws, se60 = {}, {}
    for k, (opp, key) in MEASURES.items():
        _, bd = moe(learner_diffs(T, cell, opp, key, seeds), idx)
        draws[k], se60[k] = bd, float(np.std(bd))
    corr = np.corrcoef(np.array([draws[k] for k in MEASURES]))
    rule = n_rule({k: se60[k] for k in PLANNED}, n)
    er = else_readable(T, cell, seeds)
    table = {}
    for m in LADDER_N:
        table[m] = {}
        for lab, f in (("inflated (SE_n of §5)", INFLATE), ("uninflated (as §1)", 1.0)):
            se = {k: f * se60[k] * np.sqrt(n / m) for k in MEASURES}
            table[m][lab] = {t: simulate(se, TRUTHS[t], corr) for t in TRUTHS}
            sc = se["cost"]
            table[m][lab]["cost_rates"] = {"P(present | -5)": float(np.mean([r_cost(_x(-5.0, sc, z)) == "present" for z in _z()])),
                                           "P(absent | 0)": float(np.mean([r_cost(_x(0.0, sc, z)) == "absent" for z in _z()]))}
    return {"n_pilot": n, "se60": se60, "corr": corr.tolist(), "n_rule": rule, "n": rule["n"], "outcome_table": table,
            "else_opp_median": er["opp_median"], "else_tie_share": er["tie_share"], "side_file_binding": vs_rel_summary(T, cell, seeds)}


def vs_rel_summary(T: dict, cell: str, seeds: list) -> dict:
    """read6 v2.3's report of the side files' binding drift: rows above 1e-6 and the largest."""
    v = [x for (c, _), by in T.items() if c == cell for s, d in by.items() if s in set(seeds) and (x := d.get("st_vs_rel")) is not None]
    return {"rows": len(v), "above_1e-6": int(sum(x > 1e-6 for x in v)), "max": max(v, default=None)}


def _z(k: int = 20000) -> np.ndarray:
    return np.random.default_rng(20261113).standard_normal(k)


def _x(t: float, se: float, z: float) -> dict:
    pt = t + se * z
    return {"pt": pt, "lo": pt - Z975 * se, "hi": pt + Z975 * se, "lo95": pt - Z95 * se, "hi95": pt + Z95 * se}


# §2 gate and §6 checks

def gate(T: dict, seeds: list, ev: str) -> dict:
    out = {}
    for a in ("nc", "p333"):
        ex = {k: float(np.mean(col(T, ev, a, seeds, f"q_{k}") - col(T, "S", a, seeds, f"q_{k}"))) for k in drain.KEYS}
        st = {c: int(sum(col(T, c, a, seeds, "stuck") > 0)) for c in ("S", ev)}
        out[a] = {"drain_excess": ex, "drain_pass": all(v <= DRAIN_VEH for v in ex.values()), "stuck_runs": st,
                  "stuck_pass": all(v <= GATE_STUCK for v in st.values())}
    st_ = read6.Stat(len(seeds))
    pt, bd = st_.med_diff(col(T, ev, "nc", seeds, "all_delay") - col(T, "S", "nc", seeds, "all_delay"))
    out["bind"] = {"nc_delay_cost": (pt, *ci(bd, L95))}
    out["bind"]["pass"] = out["bind"]["nc_delay_cost"][1] > 0
    drained = all(out[a]["drain_pass"] and out[a]["stuck_pass"] for a in ("nc", "p333"))
    out["outcome"] = "PASS" if drained and out["bind"]["pass"] else "BIND FAILS" if not out["bind"]["pass"] else "DRAIN FAILS"
    return out


def flip_null(d: np.ndarray, test, swaps: int = 2000, seed: int = 20261114) -> float:
    rng = np.random.default_rng(seed)
    return float(np.mean([test(d * rng.choice((-1.0, 1.0), d.shape)) for _ in range(swaps)]))


def check_a(T: dict, seeds: list, flips: int = 2000) -> dict:
    """§6 (a): usable lengths (point form, on the seeds where neither run is stuck), then the Bonferroni label over the tests read, with
    its sign-flip null (one sign per seed and length-arm pair, shared by both keys of that pair)."""
    out = {"usable": {}, "tests": {}, "stuck_dropped": {}}
    ok_s = {}
    for L in ("SL450", "SL600"):
        for a in ("nc", "p333"):
            ok_s[(L, a)] = [s for s in seeds if T[("S", a)][s]["stuck"] == 0 and T[(L, a)][s]["stuck"] == 0]
            out["stuck_dropped"][f"{L}|{a}"] = len(seeds) - len(ok_s[(L, a)])
    usable = []
    for L in ("SL450", "SL600"):
        u = {a: {k: float(np.mean(col(T, L, a, ok_s[(L, a)], k) - col(T, "S", a, ok_s[(L, a)], k))) for k in ("collisions", "alks_full_moving")}
             for a in ("nc", "p333")}
        ok = all(u[a]["collisions"] <= USE_COLL and u[a]["alks_full_moving"] <= USE_FULL for a in u)
        out["usable"][L] = {"excess": u, "usable": ok}
        if ok:
            usable.append(L)
    if not usable:
        out["label"] = "(a) not readable"
        return out
    tests = []     # (L, arm, key, paired % change, positive = more at the longer length)
    for L in usable:
        for a in ("nc", "p333"):
            ss = ok_s[(L, a)]
            for key in ("ttc_merge2", "b45_merge2"):
                base, var = col(T, "S", a, ss, key), col(T, L, a, ss, key)
                if float(np.median(base)) == 0:
                    out["tests"][f"{L}|{a}|{key}"] = "not readable (median 0 at 295 m)"
                    continue
                tests.append((L, a, key, -diffs(var, base)))
    k = len(tests)
    pct = (100 * SENS_ALPHA / (2 * max(k, 1)), 100 - 100 * SENS_ALPHA / (2 * max(k, 1)))

    def sensitive(d, idx):
        lo, hi = ci(np.median(d[idx], axis=1), pct)
        return abs(float(np.median(d))) >= SENS_PCT and (lo > 0 or hi < 0), lo, hi
    hit = False
    for L, a, key, d in tests:
        sens, lo, hi = sensitive(d, read6.Stat(len(d)).idx)
        hit |= sens
        ss = ok_s[(L, a)]
        out["tests"][f"{L}|{a}|{key}"] = {"pt": float(np.median(d)), "ci": (lo, hi), "sensitive": sens,
                                          "printed": {"all_delay": float(np.median(-diffs(col(T, L, a, ss, "all_delay"), col(T, "S", a, ss, "all_delay")))),
                                                      "end_stop2": [float(np.median(col(T, "S", a, ss, "end_stop2"))), float(np.median(col(T, L, a, ss, "end_stop2")))]}}
    if tests:
        rng = np.random.default_rng(20261116)
        idxs = {len(d): read6.Stat(len(d)).idx for *_, d in tests}     # the tests' own index, so the null matches the label as read
        hits = 0
        for _ in range(flips):
            sign = {(L, a): rng.choice((-1.0, 1.0), len(ok_s[(L, a)])) for L in usable for a in ("nc", "p333")}
            hits += any(sensitive(d * sign[(L, a)], idxs[len(d)])[0] for L, a, _, d in tests)
        out["label_null_rate"] = hits / flips
    out["n_tests"], out["bonferroni_pct"] = k, pct
    out["label"] = "SENSITIVE" if hit else "sensitivity not shown at n = 60"
    return out


def check_b(T: dict, seeds: list) -> dict:
    """§6 (b): PLANT OK at 30 % and 70 % against the 50 % rows on the same seeds."""
    out = {}
    for sh in ("SH30", "SH70"):
        r = {"coll_ub": {}, "saturation": {}}
        for a in ("nc", "p333"):
            d = col(T, sh, a, seeds, "collisions") - col(T, "S", a, seeds, "collisions")
            st_ = read6.Stat(len(seeds))
            r["coll_ub"][a] = float(np.percentile(np.mean(d[st_.idx], axis=1), 95.0))
            g = lambda c: col(T, c, a, seeds, "q_backlog") - col(T, c, a, seeds, "backlog_prev")
            sat = g(sh) - g("S")
            r["saturation"][a] = {"mean_excess": float(np.mean(sat)),
                                  "null_rate": flip_null(sat - np.mean(sat), lambda x: float(np.mean(x)) > B_SAT_VEH)}
        bad = sum(int(T[(sh, a)][s]["stuck"] > 0 or T[(sh, a)][s]["teleports"] > 0) for a in ("nc", "p333") for s in seeds)
        r["stuck_or_teleport_runs"] = bad
        d = diffs(col(T, sh, "p333", seeds, "all_delay"), col(T, sh, "nc", seeds, "all_delay"))
        st_ = read6.Stat(len(seeds))
        lo, hi = ci(np.median(d[st_.idx], axis=1), L95)
        r["command"] = {"pt": float(np.median(d)), "ci95": (lo, hi), "acts": lo > 0 or hi < 0}
        st2 = read6.Stat(len(seeds), 1000, 20261117)
        r["command_null"] = flip_null(d, lambda x: not (ci(np.median(x[st2.idx], axis=1), L95)[0] <= 0 <= ci(np.median(x[st2.idx], axis=1), L95)[1]), 1000)
        r["tau_on"] = float(np.mean([T[(sh, "p333")][s]["tau_on"][0] / max(T[(sh, "p333")][s]["tau_on"][1], 1.0) for s in seeds]))
        keys = ("all_delay", "passed", "N", "ttc_net", "b45_step", "end_stop", "end_stop2", "q_ramp1_queue", "q_ramp2_queue", "q_backlog")
        r["printed"] = {a: {k: [float(np.median(col(T, "S", a, seeds, k))), float(np.median(col(T, sh, a, seeds, k)))] for k in keys}
                        | {"jams": [float(np.median([T[(c, a)][s]["jams"] for s in seeds])) if T[(c, a)][seeds[0]]["jams"] is not None else None for c in ("S", sh)]}
                        for a in ("nc", "p333")}     # [50 %, this share]
        r["void"] = r["command_null"] > B_NULL
        r["plant_ok"] = (not r["void"] and all(v <= B_COLL_UB for v in r["coll_ub"].values()) and bad <= B_STUCK_MAX and r["command"]["acts"]
                         and all(v["mean_excess"] <= B_SAT_VEH for v in r["saturation"].values()))
        out[sh] = r
    out["amend"] = all(out[s]["plant_ok"] for s in ("SH30", "SH70"))
    out["void"] = any(out[s]["void"] for s in ("SH30", "SH70"))
    return out


# §10 identity

PROV = {"commit", "name", "cfg", "ctrl_sha256", "files", "m_st_file", "wall_s"}
DIAG_PREFIX = ("m_dec_", "lv_sum_", "lv_n_")
DIAG = {"tau_on_n", "tau_on_match", "tau_mismatch"}


def key_class(k: str) -> str:
    if k in PROV:
        return "provenance"
    if k in DIAG or k.startswith(DIAG_PREFIX):
        return "diagnostic"
    return "traffic"


def rel_diff(a, b) -> float:
    if isinstance(a, dict) and isinstance(b, dict):
        return max((rel_diff(a.get(k), b.get(k)) for k in set(a) | set(b)), default=0.0)
    try:
        return float(np.max(np.abs(np.asarray(a, float) - np.asarray(b, float)) / np.maximum(np.abs(np.asarray(b, float)), 1e-12)))
    except (TypeError, ValueError):
        return float("inf")


def ident(rows: list, S6: dict, cpu: str) -> dict:
    """Traffic keys (every key of the stored S6 row outside provenance and diagnostics) equal by value; diagnostics printed with their
    largest relative difference; a rule mismatch, or a learner mismatch on S6's CPU model, falls under the bug rule (stop); a learner
    mismatch on another CPU model is logged and disclosed."""
    rule_diff, learner_diff, diag, missing = {}, {}, {}, []
    for r in rows:
        ref = S6.get((r["name"], r["seed"]))
        if ref is None:
            missing.append(f"{r['name']} {r['seed']}")
            continue
        bad = sorted(k for k in ref if key_class(k) == "traffic" and json.dumps(r.get(k), sort_keys=True) != json.dumps(ref[k], sort_keys=True))
        dg = {k: rel_diff(r.get(k), ref[k]) for k in ref if key_class(k) == "diagnostic" and r.get(k) != ref[k]}
        if dg:
            diag[f"{r['name']} {r['seed']}"] = dg
        if bad:
            (learner_diff if r["name"].split("|", 1)[1] in V3W else rule_diff)[f"{r['name']} {r['seed']}"] = bad
    norm = lambda t: " ".join(re.sub(r"\((r|tm)\)|@.*", " ", t.lower()).replace(" cpu", " ").split())
    same_cpu = norm(S6_CPU) in norm(cpu)     # lscpu: "Intel(R) Xeon(R) Platinum 8163 CPU @ 2.50GHz"
    action = "stop" if rule_diff or missing or (learner_diff and same_cpu) else "go"
    return {"rule_diff": rule_diff, "learner_diff": learner_diff, "learner_diff_disclosed": bool(learner_diff and not same_cpu),
            "diagnostics": diag, "missing": missing, "cpu": cpu, "s6_cpu": S6_CPU, "action": action}


def main(argv: list) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("step", choices=("ident", "checks", "gate", "pilot", "screen"))
    ap.add_argument("rows", nargs="?")
    ap.add_argument("out")
    ap.add_argument("--rows", dest="rows_list", nargs="+")
    ap.add_argument("--st", nargs="+")
    ap.add_argument("--cpu", default="")
    ap.add_argument("--fallback", action="store_true")
    ap.add_argument("--pilot")
    ap.add_argument("--cell", default="E30")
    ap.add_argument("--seeds", help="LO-HI, the stage's planned seeds")
    x = ap.parse_args(argv)
    lohi = [int(v) for v in x.seeds.split("-")] if x.seeds else None
    plan_seeds = list(range(lohi[0], lohi[1] + 1)) if lohi else None
    if x.step == "ident":
        rows = [json.loads(line) for line in open(x.rows)]
        names = {r["name"] for r in rows}
        S6 = {(r["name"], r["seed"]): r for r in map(json.loads, open(S6_ROWS)) if r["name"] in names}
        res = ident(rows, S6, x.cpu)
    elif x.step == "screen":
        T = load(x.rows_list, x.st)
        dropped = sorted({s for p in x.rows_list for s in drops_of(Path(p))})
        cpus = [json.loads((Path(p).parent / "meta.json").read_text())["inputs"].get("cpu") for p in x.rows_list]
        res = screen(T, plan_seeds, x.cell, dropped, json.loads(Path(x.pilot).read_text()) if x.pilot else None, cpus=cpus)
    else:
        T = load([x.rows], x.st)
        dropped = drops_of(Path(x.rows))
        sd = [s for s in plan_seeds if s not in set(dropped)]
        if len(set(dropped)) > DROP_VOID:
            res = {"outcome": "VOID", "reason": f"{len(set(dropped))} seeds dropped (common §4)"}
        elif x.step == "checks":
            res = {"a": check_a(T, sd), "b": check_b(T, sd)}
        elif x.step == "gate":
            res = gate(T, sd, "E30s" if x.fallback else "E30")
        else:
            res = pilot(T, sd, x.cell)
        res["dropped"] = dropped
    Path(x.out).parent.mkdir(parents=True, exist_ok=True)
    Path(x.out).write_text(json.dumps(res, indent=1, default=lambda o: sorted(o) if isinstance(o, set) else str(o)))
    summary = {k: res.get(k) for k in ("outcome", "action", "n", "label", "amend") if k in res}
    if x.step == "screen":
        summary = {"outcome": res["decision"]["outcome"]}
    if x.step == "checks" and "a" in res:
        summary = {"a": res["a"].get("label"), "b_amend": res["b"]["amend"], "b_void": res["b"]["void"]}
    print(x.step, json.dumps(summary))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
