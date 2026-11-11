"""M2 readings (docs/research/protocols/v505_m2_merge_check.md v2, V508): the planned power, the PR-24 trace, the identity replays,
the variant pick and the verdict. Statistics are read6's (v505_common.md §4): v3w's raw values averaged over the learners per seed,
the median of the paired % differences, one index matrix (B = 20,000, rng 20261108). Read once each, by this committed script.
Crash drops (common §4): every reader removes the union of the stage's dropped seeds from every arm, reports them, and reads VOID when
more than 3 seeds are dropped.

usage: read_m2.py power - OUT.json                        (S6 rows only; before any variant row)
       read_m2.py trace ROWS.jsonl OUT.json
       read_m2.py ident ROWS.jsonl OUT.json               (against the stored S6 rows, by row value)
       read_m2.py pick ROWS.jsonl OUT.json
       read_m2.py verdict ROWS.jsonl OUT.json --pick PICK.json [--fallback] [--x1 X1_ROWS.jsonl | --x1-dropped]"""
import argparse
import io
import json
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "planb"))
sys.path.insert(0, str(HERE))
import drain  # noqa: E402
import read6  # noqa: E402
import v5  # noqa: E402

S6_ROWS = Path("/home/catalin/work/phd/v5b1_runs/planb_s56_remote/s6/s6_rows.jsonl")
PICK_BAR, PARTIAL_BAR = 0.75, 0.50     # M2 §2
BIND_LB = 0.50     # V512: V-A binds in a cell when the 95 % lower bound of the median cut is at least 50 %
BRAKE_RATIO, BRAKE_LB = 1.05, 1.00
FULL_UB, COLL_EXCESS, DRAIN_VEH = 0.05, 0.05, 2.0
NOT_RESOLVABLE = 1.5     # Δv half-width over Δb half-width (M2 §4)
DROP_VOID = 3     # common §4
Z_LVL, Z80 = 2.2414, 0.8416     # 98.75 % one-sided and 80 % power quantiles of the normal
CONCLUSIONS = {     # M2 §3: cell, deciding opponent, measure key
    "C1": ("TRUCK", "os0_10_10", "all_delay"), "C2": ("TRUCK", "3E-C_TRUCK", "ttc_net"), "C3": ("S", "p333", "all_delay"),
    "C5": ("X1", "p333", "all_delay"), "C5b": ("X1", "p333", "ttc_net")}
RECORDED = {"C1": "neither", "C2": "better", "C3": "neither"}     # read6 v2.3 (read6_v23.json), M2 §3
NOT_TESTED = ("VARIANT DID NOT BIND", "NOT RESOLVABLE", read6.FAILED_NULL)     # M2 §5
LVL = read6.level(2)     # 97.5 % two-sided
TWIN = "~untraced"


def load(path: Path, keep=None) -> dict:
    """(condition, arm) -> seed -> raw row; stops on a duplicate. keep: a set of "cond|arm" names to load (None = all)."""
    T = defaultdict(dict)
    for line in open(path):
        r = json.loads(line)
        if keep is not None and r["name"] not in keep:
            continue
        cond, arm = r["name"].split("|", 1)
        if r["seed"] in T[(cond, arm)]:
            raise SystemExit(f"duplicate row {r['name']} {r['seed']}")
        T[(cond, arm)][r["seed"]] = r
    return dict(T)


def drops_of(rows: Path) -> list:
    """The union over conditions of the seeds run6 dropped in the stage whose rows these are (drops.json beside them)."""
    f = rows.parent / "drops.json"
    return sorted({s for v in json.loads(f.read_text()).values() for s in v}) if f.is_file() else []


def usable(stage_seeds: list, dropped: list) -> tuple:
    """Common §4: the stage's seeds minus every dropped seed; VOID when more than 3 are dropped."""
    return [s for s in stage_seeds if s not in set(dropped)], len(set(dropped) & set(stage_seeds)) > DROP_VOID


def complete(T: dict, names: list, seeds: list) -> list:
    """Missing (name, seed) pairs among those a reading needs."""
    return [f"{c}|{a} {s}" for c, a in names for s in seeds if s not in T.get((c, a), {})]


def npz_equal(a: Path, b: Path) -> bool:
    """Two side files hold the same arrays (by value, not by file bytes)."""
    with np.load(io.BytesIO(a.read_bytes())) as x, np.load(io.BytesIO(b.read_bytes())) as y:
        return sorted(x.files) == sorted(y.files) and all(np.array_equal(x[k], y[k]) for k in x.files)


def read6_skip() -> set:
    return v5.run6.SKIP | {"commit", "name", "cfg", "ctrl_sha256", "files"}


def trace(T: dict, seeds: list, names: list | None = None) -> dict:
    """PR-24 (M2 §7): end_stop and end_stop2 recounted from the raw samples (a mismatch makes M2 VOID); the traced run equal to its
    untraced twin apart from the trace (a difference, or a missing traced run or twin, is a bug: stop). names: the planned traced arms;
    seeds: every planned seed, crash drops included, so a lost run stops M2 instead of passing unchecked."""
    out, count_ok, twin_ok = {}, True, bool(seeds)
    names = names if names is not None else [k for k in T if not k[1].endswith(TWIN)]
    for cond, arm in names:
        by_seed = T.get((cond, arm), {})
        for s in seeds:
            r, twin = by_seed.get(s), T.get((cond, arm + TWIN), {}).get(s)
            if r is None or twin is None:
                out[f"{cond}|{arm} {s}"] = {"missing": [x for x, y in (("traced", r), ("untraced", twin)) if y is None]}
                twin_ok = False
                continue
            count = {"3a_0": 0, "4a_0": 0}
            waits = defaultdict(int)
            for t, lane, length, cars in r["end_trace"]:
                for v, pos, sp in cars:
                    if sp < 1.0 and pos > length - 30.0:
                        count[lane] += 1
                        waits[(lane, v)] += 1
            diff = v5.same_row({k: x for k, x in r.items() if k != "end_trace"}, {**twin, "arm": twin["arm"].removesuffix(TWIN)}, read6_skip())
            res = {"end_stop": [count["3a_0"], r.get("end_stop", 0.0)], "end_stop2": [count["4a_0"], r.get("end_stop2", 0.0)],
                   "cars_waiting": {ln: sum(1 for (x, _) in waits if x == ln) for ln in count},
                   "wait_s_max": {ln: max([n for (x, _), n in waits.items() if x == ln], default=0) for ln in count}, "traced_differs": diff}
            res["count_ok"] = count["3a_0"] == res["end_stop"][1] and count["4a_0"] == res["end_stop2"][1]
            count_ok &= res["count_ok"]
            twin_ok &= not diff
            out[f"{cond}|{arm} {s}"] = res
    return {"runs": out, "count_ok": count_ok, "twin_equal": twin_ok, "action": "stop" if not twin_ok else "void" if not count_ok else "go"}


def ident(T: dict, S6: dict, names: list, seeds: list) -> dict:
    """M2 §6, by row value: a rule replay that differs from S6 (or is missing) stops M2; v3w rows alone differing switch the verdict to
    fresh seeds (the D4 fallback). Side files are not compared here (the S6 side folder is not shipped); the smoke compares a run's
    side files with its replay's."""
    rule_diff, learner_diff = {}, {}
    missing = complete(T, names, seeds)
    for c, a in names:
        for s in seeds:
            if s not in T.get((c, a), {}):
                continue
            d = v5.same_row(T[(c, a)][s], S6[(c, a)][s], read6_skip() | {"m_st_file"})
            if d:
                (learner_diff if a in v5.pb.V3W else rule_diff)[f"{c}|{a} {s}"] = d
    action = "stop" if rule_diff or missing or not seeds else "fresh_seeds" if learner_diff else "go"
    return {"rule_diff": rule_diff, "learner_diff": learner_diff, "missing": missing, "action": action}


def boot_ratio(st: read6.Stat, num: np.ndarray, den: np.ndarray, how: str) -> tuple:
    """Paired ratio num / den of medians or means, with its 95 % bootstrap interval on the index matrix."""
    f = np.median if how == "median" else np.mean
    pt = float(f(num) / max(f(den), 1e-9))
    b = f(num[st.idx], axis=1) / np.maximum(f(den[st.idx], axis=1), 1e-9)
    return (pt, *read6.ci(b, read6.P95))


def arr(T: dict, cond: str, arm: str, seeds: list, key: str) -> np.ndarray:
    return np.array([float(T[(cond, arm)][s].get(key) or 0.0) for s in seeds])


def pick_one(T: dict, a: float, seeds: list, st: read6.Stat) -> dict:
    out = {}
    for arm in ("nc", "p333"):
        base, var = ("S", arm), (f"SV{a:g}", arm)
        es_b, es_v = arr(T, *base, seeds, "end_stop2"), arr(T, *var, seeds, "end_stop2")
        cut = 1.0 - float(np.median(es_v)) / max(float(np.median(es_b)), 1e-9)
        brake = {k: boot_ratio(st, arr(T, *var, seeds, k), arr(T, *base, seeds, k), "mean") for k in ("b45_step", "alks_b45_step")}
        brake_fail = [k for k, (p, lo, _) in brake.items() if p > BRAKE_RATIO and lo > BRAKE_LB]
        _, fb = st.mean_diff(arr(T, *var, seeds, "alks_full_moving"), arr(T, *base, seeds, "alks_full_moving"))
        full_ub = float(np.percentile(fb, 95.0))
        coll = float(arr(T, *var, seeds, "collisions").mean() - arr(T, *base, seeds, "collisions").mean())
        stuck = int(sum(T[var][s]["m_stuck_n"] > 0 for s in seeds))
        dv = [drain.series_from_row(T[var][s]) for s in seeds]
        db = [drain.series_from_row(T[base][s]) for s in seeds]
        excess = {k: float(np.mean([x[k] - y[k] for x, y in zip(dv, db)])) for k in drain.KEYS}
        safe = not brake_fail and full_ub <= FULL_UB and coll <= COLL_EXCESS and stuck == 0 and all(v <= DRAIN_VEH for v in excess.values())
        out[arm] = {"cut": cut, "end_stop2_median": [float(np.median(es_b)), float(np.median(es_v))], "brake_ratio": brake,
                    "brake_fail": brake_fail, "full_ub": full_ub, "coll_excess": coll, "stuck_rows": stuck, "drain_excess": excess, "safe": safe,
                    "end_stop_merge1_median": [float(np.median(arr(T, *base, seeds, "end_stop"))), float(np.median(arr(T, *var, seeds, "end_stop")))],
                    "va_skipped_mean": float(arr(T, *var, seeds, "va_skipped").mean()),
                    "r2_lc": {e: [float(np.median(arr(T, *base, seeds, k))), float(np.median(arr(T, *var, seeds, k)))]
                              for e, k in (("4a", "r2_lc_4a"), ("4", "r2_lc_4"), ("5", "r2_lc_5"), ("merges", "r2_merge"))}}
    return out


def pick(T: dict, seeds: list) -> dict:
    """M2 §2: the smallest a whose cut is at least 75 % for both arms within every bound; else the largest cut of at least 50 %
    within the bounds ("partial variant"); else VOID."""
    st = read6.Stat(len(seeds))
    lv = {f"{a:g}": pick_one(T, a, seeds, st) for a in v5.LADDER}
    min_cut = lambda r: min(r[x]["cut"] for x in ("nc", "p333"))
    safe = lambda r: all(r[x]["safe"] for x in ("nc", "p333"))
    full = [a for a in v5.LADDER if safe(lv[f"{a:g}"]) and min_cut(lv[f"{a:g}"]) >= PICK_BAR]
    if full:
        a, kind = full[0], "full"
    else:
        part = [a for a in v5.LADDER if safe(lv[f"{a:g}"]) and min_cut(lv[f"{a:g}"]) >= PARTIAL_BAR]
        a, kind = (max(part, key=lambda x: min_cut(lv[f"{x:g}"])), "partial") if part else (None, "VOID")
    cut = min_cut(lv[f"{a:g}"]) if a is not None else None
    return {"levels": lv, "a": a, "kind": kind, "cut": cut, "n": len(seeds)}


def brake_null(S6: dict, n: int = 60, studies: int = 1000, seed: int = 505_201) -> dict:
    """M2 §2: the braking bound's false-fail rate at n seeds, per key and per level (any of 2 keys x 2 arms failing), on S6 S rows of
    two pairs of stored rules with labels swapped at random within seed (true ratio 1)."""
    rng = np.random.default_rng(seed)
    seeds = sorted(S6[("S", "p333")])
    pairs = (("p333", "3E-D_TRUCK"), ("lr1000_16_2", "os0_10_10"))
    vals = {(r, k): np.array([float(S6[("S", r)][s].get(k) or 0.0) for s in seeds]) for p in pairs for r in p for k in ("b45_step", "alks_b45_step")}
    per_key, level = defaultdict(int), 0
    for _ in range(studies):
        i = rng.choice(len(seeds), n, replace=False)
        st = read6.Stat(n, 2000, int(rng.integers(1 << 30)))
        any_fail = False
        for x, y in pairs:
            flip = rng.random(n) < 0.5
            for k in ("b45_step", "alks_b45_step"):
                a_, b_ = vals[(x, k)][i], vals[(y, k)][i]
                p, lo, _ = boot_ratio(st, np.where(flip, a_, b_), np.where(flip, b_, a_), "mean")
                fail = p > BRAKE_RATIO and lo > BRAKE_LB
                per_key[f"{x}|{k}"] += fail
                any_fail |= fail
        level += any_fail
    return {"per_key": {k: v / studies for k, v in per_key.items()}, "per_level": level / studies, "n": n}


def p_arm(T: dict, cond: str, seeds: list, key: str) -> np.ndarray:
    """v3w's per-seed mean over the learners (read6.arm)."""
    return np.mean([arr(T, cond, w, seeds, key) for w in v5.pb.V3W], axis=0)


def reading(st: read6.Stat, P: np.ndarray, O: np.ndarray) -> dict:
    """Plan B's components (common §4): better, harm or neither; with the CI half-width and the per-seed differences."""
    e, b = st.eff(P, O)
    lo, hi = read6.ci(b, LVL)
    lo95, hi95 = read6.ci(b, read6.P95)
    d = -(P - O) / max(float(np.median(O)), 1e-9) * 100.0
    return {"e": e, "ci": (lo, hi), "ci95": (lo95, hi95), "hw": (hi - lo) / 2.0, "d": d, "boot": b}


def component(r: dict, key: str) -> str:
    if r["ci"][0] == r["ci"][1]:
        return "not readable"     # common §4: a zero-width CI
    if r["ci"][0] > 0:
        return "better"
    harm = read6.HARM_DELAY if key == "all_delay" else read6.HARM_CF
    return "harm" if r["e"] < harm and r["ci95"][1] < 0 else "neither"


def bind(T: dict, cell: str, vcell: str, arms: list, seeds: list, st: read6.Stat) -> dict:
    """M2 §4 (V512): V-A binds in the cell when, for every arm of the comparison and for no control, the 95 % lower bound of
    the median end_stop2 cut is at least 50 % (the paired ratio of medians has its 95 % upper bound at most 0.5)."""
    out = {}
    for a in arms:
        get = (lambda c: p_arm(T, c, seeds, "end_stop2")) if a == "v3w" else (lambda c: arr(T, c, a, seeds, "end_stop2"))
        p, lo, hi = boot_ratio(st, get(vcell), get(cell), "median")
        out[a] = {"median_ratio": (p, lo, hi), "binds": hi <= 1.0 - BIND_LB}
    return out


def conclusion(T: dict, name: str, a: float, seeds: list, fallback: bool = False, swaps: int = 2000) -> dict:
    cell, opp, key = CONCLUSIONS[name]
    vcell = f"{cell}V{a:g}"
    st = read6.Stat(len(seeds))
    base = reading(st, p_arm(T, cell, seeds, key), arr(T, cell, opp, seeds, key))
    var = reading(st, p_arm(T, vcell, seeds, key), arr(T, vcell, opp, seeds, key))
    cb, cv = component(base, key), component(var, key)
    bd = bind(T, cell, vcell, ["v3w", opp, "nc"], seeds, st)
    null = read6.swap_null(var["d"], LVL[0], swaps, 505_301)
    ib = var["boot"] - base["boot"]     # I = Δv - Δb, the difference of the two medians on the shared index matrix
    out = {"cell": cell, "opponent": opp, "measure": key, "base": {k: base[k] for k in ("e", "ci", "ci95", "hw")}, "base_reading": cb,
           "variant": {k: var[k] for k in ("e", "ci", "ci95", "hw")}, "variant_reading": cv, "bind": bd, "null_rate": null,
           "interaction": (var["e"] - base["e"], *read6.ci(ib, LVL)), "n": len(seeds)}
    recorded = RECORDED.get(name)
    if cell == "X1" and cb != "better":
        out["reading"] = "NOT REPLICATED"
    elif fallback and recorded is not None and cb != recorded:     # V512: fresh base differs from the record
        out["reading"] = "NOT REPLICATED"
    elif not all(x["binds"] for x in bd.values()):
        out["reading"] = "VARIANT DID NOT BIND"
    elif null > read6.NULL_FACTOR * LVL[0] / 100.0:
        out["reading"] = read6.FAILED_NULL
    elif "not readable" in (cb, cv) or var["hw"] > NOT_RESOLVABLE * base["hw"]:
        out["reading"] = "NOT RESOLVABLE"
    else:
        out["reading"] = "SAME" if cv == cb else "CHANGED"
    if out["reading"] == "SAME" and cb == "neither":
        out["detectable_shift_80"] = var["hw"] * (1.0 + Z80 / Z_LVL)
    return out


def pr28_status(res: dict, a: float, kind: str, cut: float, x1: str) -> str:
    """M2 §5: PR-28's line, fixed before data. x1: 'read', 'pending' (part 2 not run yet) or 'dropped' (at the cap)."""
    deciding = [res[c]["reading"] for c in ("C1", "C2", "C3")]
    if x1 == "pending":
        return "provisional, X1 pending" if all(r == "SAME" for r in deciding) else "gap"
    x1r = ["not tested" if x1 == "dropped" else "not tested" if res[c]["reading"] in NOT_TESTED else res[c]["reading"] for c in ("C5", "C5b")]
    if all(r == "SAME" for r in deciding) and all(r in ("SAME", "not tested") for r in x1r):
        read = [c for c in ("C1", "C2", "C3", "C5", "C5b") if c in res and res[c]["reading"] == "SAME"]
        lbl = f"V-A, a = {a:g}" + ("" if kind == "full" else f", partial variant (cut {cut:.0%})")
        return (f"partial: located by road and period (not lane); not shown to depend on the merge gap-acceptance scale on 4a_0 ({lbl}) "
                f"for {', '.join(read)}; SUMO's stop-at-lane-end mechanism and the commanded-headway dependence (PR-08) untested")
    return "gap"


def verdict(T: dict, p: dict, seeds: list, x1_seeds: list | None, x1: str, fallback: bool) -> dict:
    res = {c: conclusion(T, c, p["a"], seeds, fallback) for c in ("C1", "C2", "C3")}
    if x1_seeds:
        res |= {c: conclusion(T, c, p["a"], x1_seeds) for c in ("C5", "C5b")}
    return {"a": p["a"], "kind": p["kind"], "cut": p["cut"], "conclusions": res, "pr28": pr28_status(res, p["a"], p["kind"], p["cut"], x1)}


def power(S6: dict, rho: float = 0.2, studies: int = 200, seed: int = 505_401) -> dict:
    """M2 §4's planned power, from the S6 rows before any variant row: for C1-C3, a variant made of the base's per-seed effects mixed
    with resampled ones at correlation rho, (a) with no change, (b) shifted by 2 points (delay) or 10 points (close-following). Reports
    how often the reading changes. Planning only; never used to change a rule."""
    rng = np.random.default_rng(seed)
    seeds = v5.seeds("m2_verdict")
    out = {}
    for c in ("C1", "C2", "C3"):
        cell, opp, key = CONCLUSIONS[c]
        P, O = p_arm(S6, cell, seeds, key), arr(S6, cell, opp, seeds, key)
        st = read6.Stat(len(seeds), 2000, seed)
        base = component(reading(st, P, O), key)
        shift = 2.0 if key == "all_delay" else 10.0
        rates = {}
        for label, s in (("no_change", 0.0), (f"v3w_better_by_{shift:g}", shift), (f"v3w_worse_by_{shift:g}", -shift)):
            changed = 0
            for _ in range(studies):
                j = rng.integers(0, len(seeds), len(seeds))
                mix = rho * (P - O) + np.sqrt(1 - rho ** 2) * (P - O)[j] + (1 - np.sqrt(1 - rho ** 2) - rho) * np.mean(P - O)
                Pv = O + mix - s / 100.0 * np.median(O)     # lower P = v3w better
                changed += component(reading(st, Pv, O), key) != base
            rates[label] = changed / studies
        out[c] = {"base_reading": base, "p_reading_changes": rates}
    return {"rho": rho, "studies": studies, "conclusions": out}


def main(argv: list) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("step", choices=("power", "trace", "ident", "pick", "verdict"))
    ap.add_argument("rows")
    ap.add_argument("out")
    ap.add_argument("--pick")
    ap.add_argument("--x1")
    ap.add_argument("--x1-dropped", action="store_true")
    ap.add_argument("--fallback", action="store_true")
    x = ap.parse_args(argv)
    if x.step == "power":
        keep = {f"{c}|{n}" for c in ("S", "TRUCK") for n in v5.M2_RULES + v5.pb.V3W}
        res = power(load(S6_ROWS, keep))
        v5.pb.cma2.write_json(Path(x.out), res)
        print("power", json.dumps(res["conclusions"]))
        return 0
    rows = Path(x.rows)
    T = load(rows)
    dropped = drops_of(rows)
    stage = {"trace": "m2_trace", "ident": "m2_ident", "pick": "m2_pick", "verdict": "m2_fallback" if x.fallback else "m2_verdict"}[x.step]
    lo, hi = v5.STAGES[stage]
    if x.step == "trace":
        hi = lo + v5.TRACE_SEEDS - 1
    seeds, void = usable(list(range(lo, hi + 1)), dropped)
    full = list(range(lo, hi + 1))
    if x.step in ("trace", "ident"):     # check stages: every planned run must be there, drops included (a lost run stops M2)
        planned = [tuple(n.split("|", 1)) for n in v5.plan(stage, rows.parent)["arms"]]
        if x.step == "trace":
            res = trace(T, full, [k for k in planned if not k[1].endswith(TWIN)])
        else:
            res = ident(T, load(S6_ROWS, {f"{c}|{n}" for c, n in planned}), planned, full)
    elif void:
        res = {"outcome": "VOID", "reason": f"more than {DROP_VOID} seeds dropped", "dropped": dropped}
    elif x.step == "pick":
        need = [("S", r) for r in ("nc", "p333")] + [(f"SV{a:g}", r) for a in v5.LADDER for r in ("nc", "p333")]
        if miss := complete(T, need, seeds):
            raise SystemExit(f"pick rows incomplete: {miss[:10]}")
        res = pick(T, seeds)
        res["brake_null"] = brake_null(load(S6_ROWS, {"S|p333", "S|3E-D_TRUCK", "S|lr1000_16_2", "S|os0_10_10"}))
    else:
        p = json.loads(Path(x.pick).read_text())
        if p["a"] is None:
            raise SystemExit("M2 is VOID at the pick: no verdict")
        if not x.fallback:     # D4: the stored S6 rows are the base plant
            T |= load(S6_ROWS, {f"{c}|{n}" for c in ("S", "TRUCK") for n in v5.M2_RULES + v5.pb.V3W})
        x1_seeds, x1 = None, "dropped" if x.x1_dropped else "pending"
        if x.x1:
            T |= load(Path(x.x1))
            x1_seeds, x1_void = usable(v5.seeds("m2_x1"), drops_of(Path(x.x1)))
            x1 = "dropped" if x1_void else "read"
        res = verdict(T, p, seeds, x1_seeds, x1, x.fallback)
        res["base_rows"] = "fresh seeds, both plants" if x.fallback else "stored S6 rows (D4)"
    res["dropped"] = dropped
    v5.pb.cma2.write_json(Path(x.out), res)
    print(x.step, json.dumps({k: v for k, v in res.items() if k in ("outcome", "action", "a", "kind", "pr28", "count_ok", "twin_equal")}))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
