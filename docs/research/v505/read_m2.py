"""M2 readings (docs/research/protocols/v505_m2_merge_check.md v2, V508): the PR-24 trace, the identity replays, the variant pick
and the verdict. Statistics are read6's (v505_common.md §4): v3w's raw values averaged over the learners per seed, the median of the
paired % differences, one index matrix (B = 20,000, rng 20261108). Read once each, by this committed script.

usage: read_m2.py trace ROWS.jsonl OUT.json
       read_m2.py ident ROWS.jsonl OUT.json            (against the stored S6 rows)
       read_m2.py pick ROWS.jsonl OUT.json
       read_m2.py verdict ROWS.jsonl OUT.json --a A [--x1 X1_ROWS.jsonl]"""
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
S6_ST = Path("/home/catalin/work/phd/v5b1_runs/planb_s56_remote/jobs/st")
PICK_BAR, PARTIAL_BAR = 0.75, 0.50     # M2 §2
BRAKE_RATIO, BRAKE_LB = 1.05, 1.00
FULL_UB, COLL_EXCESS, DRAIN_VEH = 0.05, 0.05, 2.0
NOT_RESOLVABLE = 1.5     # Δv half-width over Δb half-width (M2 §4)
Z_LVL, Z80 = 2.2414, 0.8416     # 98.75 % one-sided and 80 % power quantiles of the normal
CONCLUSIONS = {     # M2 §3: cell, deciding opponent, measure key
    "C1": ("TRUCK", "os0_10_10", "all_delay"), "C2": ("TRUCK", "3E-C_TRUCK", "ttc_net"), "C3": ("S", "p333", "all_delay"),
    "C5": ("X1", "p333", "all_delay"), "C5b": ("X1", "p333", "ttc_net")}
LVL = read6.level(2)     # 97.5 % two-sided


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


def trace(T: dict) -> dict:
    """PR-24: end_stop and end_stop2 recounted from the raw samples; the traced run equal to its untraced twin apart from the trace."""
    out, ok = {}, True
    for (cond, arm), by_seed in T.items():
        if arm.endswith("~untraced"):
            continue
        for s, r in by_seed.items():
            count = {"3a_0": 0, "4a_0": 0}
            waits = defaultdict(int)
            for t, lane, length, cars in r["end_trace"]:
                for v, pos, sp in cars:
                    if sp < 1.0 and pos > length - 30.0:
                        count[lane] += 1
                        waits[(lane, v)] += 1
            twin = T[(cond, arm + "~untraced")][s]
            diff = v5.same_row({k: x for k, x in r.items() if k != "end_trace"}, twin, read6_skip())
            res = {"end_stop": [count["3a_0"], r.get("end_stop", 0.0)], "end_stop2": [count["4a_0"], r.get("end_stop2", 0.0)],
                   "cars_waiting": {ln: sum(1 for (x, _) in waits if x == ln) for ln in ("3a_0", "4a_0")},
                   "wait_s_max": {ln: max([n for (x, _), n in waits.items() if x == ln], default=0) for ln in ("3a_0", "4a_0")},
                   "traced_differs": diff}
            res["pass"] = count["3a_0"] == res["end_stop"][1] and count["4a_0"] == res["end_stop2"][1] and not diff
            ok &= res["pass"]
            out[f"{cond}|{arm} {s}"] = res
    return {"runs": out, "pass": ok}


def read6_skip() -> set:
    return v5.run6.SKIP | {"commit", "name", "cfg", "ctrl_sha256", "files"}


def npz_equal(a: Path, b: Path) -> bool:
    with np.load(io.BytesIO(a.read_bytes())) as x, np.load(io.BytesIO(b.read_bytes())) as y:
        return sorted(x.files) == sorted(y.files) and all(np.array_equal(x[k], y[k]) for k in x.files)


def ident(T: dict, S6: dict, st_new: Path | None = None) -> dict:
    """M2 §6: every replay equal to its stored S6 row by value; side-file arrays equal where both exist. A rule that differs stops
    M2; v3w rows alone differing switches the verdict to fresh seeds (the D4 fallback)."""
    rule_diff, learner_diff, side = {}, {}, {}
    for (cond, arm), by_seed in T.items():
        for s, r in by_seed.items():
            old = S6[(cond, arm)][s]
            d = v5.same_row(r, old, read6_skip() | {"m_st_file"})
            if d:
                (learner_diff if arm in v5.pb.V3W else rule_diff)[f"{cond}|{arm} {s}"] = d
            if st_new is not None and r.get("m_st_file") and old.get("m_st_file"):
                side[f"{cond}|{arm} {s}"] = npz_equal(st_new / r["m_st_file"], S6_ST / old["m_st_file"])
    side_bad = sorted(k for k, v in side.items() if not v)
    action = "stop" if rule_diff else "fresh_seeds" if learner_diff or side_bad else "go"
    return {"rule_diff": rule_diff, "learner_diff": learner_diff, "side_files_differ": side_bad, "n": sum(len(v) for v in T.values()), "action": action}


def ratio_ci(st: read6.Stat, num: np.ndarray, den: np.ndarray) -> tuple:
    """Paired ratio of means, num / den, with its 95 % bootstrap interval on the index matrix."""
    pt = float(num.mean() / max(den.mean(), 1e-9))
    b = num[st.idx].mean(axis=1) / np.maximum(den[st.idx].mean(axis=1), 1e-9)
    return (pt, *read6.ci(b, read6.P95))


def arr(T: dict, cond: str, arm: str, seeds: list, key: str) -> np.ndarray:
    return np.array([float(T[(cond, arm)][s].get(key) or 0.0) for s in seeds])


def pick_one(T: dict, a: float, seeds: list, st: read6.Stat) -> dict:
    out = {}
    for arm in ("nc", "p333"):
        base, var = ("S", arm), (f"SV{a:g}", arm)
        es_b, es_v = arr(T, *base, seeds, "end_stop2"), arr(T, *var, seeds, "end_stop2")
        cut = 1.0 - float(np.median(es_v)) / max(float(np.median(es_b)), 1e-9)
        brake = {k: ratio_ci(st, arr(T, *var, seeds, k), arr(T, *base, seeds, k)) for k in ("b45_step", "alks_b45_step")}
        brake_fail = [k for k, (p, lo, _) in brake.items() if p > BRAKE_RATIO and lo > BRAKE_LB]
        fd, fb = st.mean_diff(arr(T, *var, seeds, "alks_full_moving"), arr(T, *base, seeds, "alks_full_moving"))
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
                    "r2_lc": {e: [float(np.median(arr(T, *base, seeds, f"r2_lc_{e}"))), float(np.median(arr(T, *var, seeds, f"r2_lc_{e}")))]
                              for e in ("4a", "4", "5")}}
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
    bar = PICK_BAR if kind == "full" else min_cut(lv[f"{a:g}"]) if a is not None else None
    return {"levels": lv, "a": a, "kind": kind, "bar": bar, "seeds": [seeds[0], seeds[-1]], "n": len(seeds)}


def brake_null(S6: dict, n: int = 60, studies: int = 2000, seed: int = 505_201) -> dict:
    """M2 §2: the braking bound's false-fail rate at n seeds, on S6 S rows of two stored rules with their labels swapped at random
    within seed (true ratio 1)."""
    rng = np.random.default_rng(seed)
    seeds = sorted(S6[("S", "p333")])
    out = {}
    for k in ("b45_step", "alks_b45_step"):
        x = np.array([float(S6[("S", "p333")][s].get(k) or 0.0) for s in seeds])
        y = np.array([float(S6[("S", "3E-D_TRUCK")][s].get(k) or 0.0) for s in seeds])
        fails = 0
        for _ in range(studies):
            i = rng.choice(len(seeds), n, replace=False)
            flip = rng.random(n) < 0.5
            a, b = np.where(flip, x[i], y[i]), np.where(flip, y[i], x[i])
            st = read6.Stat(n, 2000, int(rng.integers(1 << 30)))
            p, lo, _ = ratio_ci(st, a, b)
            fails += p > BRAKE_RATIO and lo > BRAKE_LB
        out[k] = fails / studies
    return out


def p_arm(T: dict, cond: str, seeds: list, key: str) -> np.ndarray:
    """v3w's per-seed mean over the learners (read6.arm)."""
    return np.mean([arr(T, cond, w, seeds, key) for w in v5.pb.V3W], axis=0)


def reading(st: read6.Stat, P: np.ndarray, O: np.ndarray) -> dict:
    """Plan B's components (common §4): better, harm or neither; with the CI half-width and the per-seed differences."""
    e, b = st.eff(P, O)
    lo, hi = read6.ci(b, LVL)
    lo95, hi95 = read6.ci(b, read6.P95)
    d = -(P - O) / max(float(np.median(O)), 1e-9) * 100.0
    return {"e": e, "ci": (lo, hi), "ci95": (lo95, hi95), "hw": (hi - lo) / 2.0, "d": d}


def component(r: dict, key: str) -> str:
    if r["ci"][0] > 0:
        return "better"
    harm = read6.HARM_DELAY if key == "all_delay" else read6.HARM_CF
    return "harm" if r["e"] < harm and r["ci95"][1] < 0 else "neither"


def bind(T: dict, cell: str, vcell: str, arms: list, seeds: list, bar: float, st: read6.Stat) -> dict:
    """M2 §4: V-A must cut end_stop2 by at least the pick's bar for every arm of the comparison and for no control, judged by the
    paired-ratio 95 % upper bound."""
    out = {}
    for a in arms:
        get = (lambda c: p_arm(T, c, seeds, "end_stop2")) if a == "v3w" else (lambda c: arr(T, c, a, seeds, "end_stop2"))
        p, lo, hi = ratio_ci(st, get(vcell), get(cell))
        out[a] = {"ratio": (p, lo, hi), "binds": hi <= 1.0 - bar}
    return out


def conclusion(T: dict, name: str, a: float, bar: float, seeds: list, swaps: int = 2000) -> dict:
    cell, opp, key = CONCLUSIONS[name]
    vcell = f"{cell}V{a:g}"
    st = read6.Stat(len(seeds))
    bd = bind(T, cell, vcell, ["v3w", opp, "nc"], seeds, bar, st)
    base = reading(st, p_arm(T, cell, seeds, key), arr(T, cell, opp, seeds, key))
    var = reading(st, p_arm(T, vcell, seeds, key), arr(T, vcell, opp, seeds, key))
    cb, cv = component(base, key), component(var, key)
    null = read6.swap_null(var["d"], LVL[0], swaps, 505_301)
    I = var["d"] - base["d"]
    ie, ib = st.med_diff(I)
    out = {"cell": cell, "opponent": opp, "measure": key, "base": {k: base[k] for k in ("e", "ci", "ci95", "hw")}, "base_reading": cb,
           "variant": {k: var[k] for k in ("e", "ci", "ci95", "hw")}, "variant_reading": cv, "bind": bd,
           "null_rate": null, "interaction": (ie, *read6.ci(ib, LVL))}
    if not all(x["binds"] for x in bd.values()):
        out["reading"] = "VARIANT DID NOT BIND"
    elif cell == "X1" and cb != "better":
        out["reading"] = "NOT REPLICATED"
    elif null > read6.NULL_FACTOR * LVL[0] / 100.0:
        out["reading"] = read6.FAILED_NULL
    elif var["hw"] > NOT_RESOLVABLE * base["hw"]:
        out["reading"] = "NOT RESOLVABLE"
    else:
        out["reading"] = "SAME" if cv == cb else "CHANGED"
    if out["reading"] == "SAME" and cb == "neither":
        out["detectable_shift_80"] = var["hw"] * (1.0 + Z80 / Z_LVL)
    return out


def pr28_status(res: dict, a: float, kind: str, bar: float) -> str:
    """M2 §5: PR-28's line, fixed before data."""
    deciding = [res[c]["reading"] for c in ("C1", "C2", "C3")]
    x1 = [res[c]["reading"] if c in res else "not tested" for c in ("C5", "C5b")]
    if all(r == "SAME" for r in deciding) and all(r in ("SAME", "not tested") for r in x1):
        read = [c for c in ("C1", "C2", "C3", "C5", "C5b") if c in res and res[c]["reading"] == "SAME"]
        lbl = f"V-A, a = {a:g}" + ("" if kind == "full" else f", partial variant (cut {bar:.0%})")
        return (f"partial: located by road and period (not lane); not shown to depend on the merge gap-acceptance scale on 4a_0 ({lbl}) "
                f"for {', '.join(read)}; SUMO's stop-at-lane-end mechanism and the commanded-headway dependence (PR-08) untested")
    return "gap"


def verdict(T: dict, a: float, kind: str, bar: float, seeds: list, x1_seeds: list | None) -> dict:
    res = {c: conclusion(T, c, a, bar, seeds) for c in ("C1", "C2", "C3")}
    if x1_seeds:
        res |= {c: conclusion(T, c, a, bar, x1_seeds) for c in ("C5", "C5b")}
    return {"a": a, "kind": kind, "bar": bar, "conclusions": res, "pr28": pr28_status(res, a, kind, bar)}


def main(argv: list) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("step", choices=("trace", "ident", "pick", "verdict"))
    ap.add_argument("rows")
    ap.add_argument("out")
    ap.add_argument("--pick")
    ap.add_argument("--x1")
    ap.add_argument("--st")
    x = ap.parse_args(argv)
    T = load(Path(x.rows))
    if x.step == "trace":
        res = trace(T)
    elif x.step == "ident":
        res = ident(T, load(S6_ROWS), Path(x.st) if x.st else None)
    elif x.step == "pick":
        res = pick(T, v5.seeds("m2_pick"))
        res["brake_null"] = brake_null(load(S6_ROWS))
    else:
        p = json.loads(Path(x.pick).read_text())
        if p["a"] is None:
            raise SystemExit("M2 is VOID at the pick: no verdict")
        T |= {k: v for k, v in load(S6_ROWS).items() if k[0] in ("S", "TRUCK")}     # D4: the stored S6 rows are the base plant
        x1 = None
        if x.x1:
            T |= load(Path(x.x1))
            x1 = v5.seeds("m2_x1")
        res = verdict(T, p["a"], p["kind"], p["bar"], v5.seeds("m2_verdict"), x1)
    v5.pb.cma2.write_json(Path(x.out), res)
    print(x.step, json.dumps({k: v for k, v in res.items() if k in ("pass", "action", "a", "kind", "pr28")}))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
