"""Plan B S2 (planb.md §7.3, V480): plant gates per cell, with no v3w row. Arms: no control, p333 and 3E-T in each cell and in S on
7,480,010-049, and the placebo (V341's brake, the null of G1) with no control and p333. Each gate is read on medians over the 40
seeds; effects are round 2's paired statistic against each arm's own S row, 95 % percentile bootstrap, 20,000 resamples.
G4(ii)(a,b) is the mean-excess drain test of V486 (drain.py), which replaced the registered median ratios after S2 was read; the registered
verdicts are kept beside it. A cell passes S2 if G1a and G1b pass, G2 passes and G4 passes; a broken null (the placebo passes G1a or G1b) stops the stage
(not a KILL: fix, log, re-run). If p333 and 3E-T both fail G2 in a cell, every other carried rule runs there before a KILL, and the
cell is "G2 pending" until they have. G4(iv): PR-24 counter traces of no control and p333 on the first 2 gate seeds, in each cell
and in S, recount equal to their rows and traced rows equal to the untraced ones. The drain cap for S6 is 1.5 x the largest
no-control end-of-run insertion backlog in the cell's rows.

usage: gates2.py run --out DIR --cells SURGE,TRUCK [--workers N]           the runs (pack on)
       gates2.py trace --out DIR --cells SURGE,TRUCK [--workers N]         G4(iv): 4 traced runs per condition, after run
       gates2.py fallback --out DIR --cells SURGE,TRUCK --fallback TRUCK   G2: the other 13 carried rules in the named cells
       gates2.py read --out DIR --cells SURGE,TRUCK [--result NAME]        the gate table, s2.json; exit 3 if the null is broken
  --result s2_v486.json: V486's re-read of the stored rows, once only, from a clean, detached tree; s2.json is written only at the rows' code."""
import argparse
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import pb  # noqa: E402
import drain  # noqa: E402

SEEDS = pb.seeds(7_480_010, 7_480_049)
TRACE_SEEDS = SEEDS[:2]
ARMS = ("nc", "p333", "3e")
FALLBACK = tuple(r for r in pb.CARRIED if r not in ("p333", "3e"))
P95, B, RNG = (2.5, 97.5), 20_000, 20261108
WINDOW_MIN = range(20, 25)     # minutes 20-24 after the warm-up: 1,500-1,800 s
DRAIN_FACTOR = 1.5


def jobs(cells: list, st_dir: str) -> dict:
    arms = pb.stored_arms()
    out = {}
    for cond in ["S"] + cells:
        for a in ARMS:
            out[f"{cond}|{a}"] = {**pb.with_cond(arms[a], cond), "measure": st_dir}
    for a in ("nc", "p333"):
        out[f"PLACEBO|{a}"] = {**pb.with_cond(arms[a], "S", pb.PLACEBO), "measure": st_dir}
    return out


def fallback_jobs(cells: list, st_dir: str) -> dict:
    arms = pb.stored_arms()
    return {f"{c}|{r}": {**pb.with_cond(arms[r], c), "measure": st_dir} for c in cells for r in FALLBACK}


def run(out: Path, cells: list, workers: int, runner=None) -> None:
    from v5b2.freeway import evaluate as plant_sweep  # noqa: F401  fail early without SUMO
    J = jobs(cells, str(out / "st"))
    pb.guard(out, {"cells": cells, "seeds": [SEEDS[0], SEEDS[-1]]}, J, strict=runner is None)
    pb.batch(J, SEEDS, out / "s2_runs.jsonl", out / "rd", workers, runner or full_runner)


def same_code(out: Path) -> dict:
    """A sub-step (fallback, trace) runs only at the code of the main S2 rows, so the verdict never mixes plants."""
    mf = out / "meta.json"
    if not mf.exists():
        raise SystemExit("run the S2 rows first")
    code = json.loads(mf.read_text())["code"]
    if code != pb.code_state():
        raise SystemExit(f"the S2 rows ran at {code['commit']} (clean={code['clean']}); this tree differs; re-run S2 from scratch")
    return code


def run_fallback(out: Path, cells: list, workers: int, runner=None) -> None:
    J = fallback_jobs(cells, str(out / "st"))
    if runner is None:
        same_code(out)
    pb.guard(out / "fallback", {"cells": cells, "seeds": [SEEDS[0], SEEDS[-1]]}, J, strict=runner is None)
    pb.batch(J, SEEDS, out / "fallback" / "s2_fallback_runs.jsonl", out / "rd", workers, runner or full_runner)


KEEP = ("q", "seed", "all_delay", "ttc_net", "passed", "collisions", "contact_steps", "b3_step", "brake3", "out_b3", "end_stop", "end_stop2",
        "m_cong_vs", "m_cong_run_s", "m_cong_vs_nc", "m_cong_run_s_nc", "m_stuck_n", "m_pending_end", "m_main_pending_min", "m_road_ttc3",
        "m_robust_road", "m_capped", "pert_log")


def keep_of(r: dict) -> dict:
    out = {k: r.get(k) for k in KEEP}
    out["m_minute"] = {k: r["m_minute"][k] for k in ("ramp1_pending", "ramp2_pending", "ramp1_queue", "ramp2_queue")}
    return out


def full_row(a: tuple) -> dict:
    from v5b2.freeway import evaluate as ps
    return keep_of(ps.run_one(a))


def trace(out: Path, cells: list, workers: int) -> dict:
    """G4(iv): traced re-runs of S2 rows (their own measure folder), recounted, and compared with the stored untraced rows."""
    import pr24
    same_code(out)
    stored = {(r["name"], r["seed"]): r for r in pb.cma2.load(out / "s2_runs.jsonl")}
    J = jobs(cells, str(out / "trace" / "st"))
    todo = [[n, J[n], pb.Q, s] for n in J if n.split("|")[1] in ("nc", "p333") and not n.startswith("PLACEBO") for s in TRACE_SEEDS]
    pb.guard(out / "trace", {"cells": cells, "seeds": TRACE_SEEDS}, {n: c for n, c, _, _ in todo}, strict=True)
    if any((n, s) not in stored for n, _, _, s in todo):
        raise SystemExit("run the S2 rows first")
    res = pr24.run(todo, workers, out / "trace")
    per = {f"{n} {s}": {"recount_differs": bad, "row_differs": pr24.row_differs(keep_of(row), {k: v for k, v in stored[(n, s)].items() if k != "name"})}
           for (n, s), (row, _, bad) in res.items()}
    conds = {n.split("|")[0] for n, *_ in todo}
    ok = {c: all(not v["recount_differs"] and not v["row_differs"] for k, v in per.items() if k.startswith(c + "|")) for c in conds}
    pb.cma2.write_json(out / "s2_trace.json", {"runs": per, "pass": ok})
    return ok


def full_runner(jobs_, workers):
    import multiprocessing as mp
    from concurrent.futures import ProcessPoolExecutor, as_completed
    failed = []
    with ProcessPoolExecutor(workers, mp_context=mp.get_context("spawn"), max_tasks_per_child=1) as ex:
        futs = {ex.submit(full_row, j): j for j in jobs_}
        for f in as_completed(futs):
            j = futs[f]
            try:
                yield (j[0], j[2], j[3]), f.result()
            except Exception as x:
                failed.append(j[0])
                print("FAILED", j[0], j[3], repr(x)[:300], flush=True)
    if failed:
        raise RuntimeError(f"{len(failed)} runs failed")


def eff(A: np.ndarray, Bv: np.ndarray, sign: int = 1) -> tuple:
    """sign x median(A - B) / median(B) x 100 with its 95 % percentile CI (here A is the cell, B its S row: positive = higher in the cell)."""
    d = sign * (A - Bv) / max(float(np.median(Bv)), 1e-9) * 100.0
    idx = np.random.default_rng(RNG).integers(0, len(d), (B, len(d)))
    lo, hi = np.percentile(np.median(d[idx], axis=1), P95)
    return float(np.median(d)), float(lo), float(hi)


def series(rows: list, key: str) -> np.ndarray:
    return np.array([float(r[key] or 0.0) for r in rows])


def backlog(r: dict) -> float:
    """Mean insertion backlog over 1,500-1,800 s, all routes (vehicles)."""
    m = r["m_minute"]
    return float(np.mean([(m["ramp1_pending"][i] + m["ramp2_pending"][i] + r["m_main_pending_min"][i]) / 60.0 for i in WINDOW_MIN]))


def ramp_queue(r: dict, k: str) -> float:
    return float(np.mean([r["m_minute"][k][i] / 60.0 for i in WINDOW_MIN]))


def g1(C: list, S: list, cong_key: str, run_key: str) -> dict:
    a = eff(series(C, "all_delay"), series(S, "all_delay"))
    b = eff(series(C, cong_key), series(S, cong_key))
    run_med = float(np.median(series(C, run_key)))
    return {"G1a": a, "G1a_pass": a[0] >= 10.0 and a[1] > 0, "G1b_cong": b, "G1b_run_s_median": run_med,
            "G1b_pass": b[0] >= 10.0 and b[1] > 0 and run_med >= 300.0}


def read(T: dict, cells: list, trace: dict | None = None) -> dict:
    """T: name -> rows in seed order; trace: condition -> whether its G4(iv) traces passed."""
    trace = trace or {}
    res = {"placebo": {}, "cells": {}}
    for a in ("nc", "p333"):
        g = g1(T[f"PLACEBO|{a}"], T[f"S|{a}"], "m_cong_vs", "m_cong_run_s")
        res["placebo"][a] = g
    res["null_broken"] = any(g["G1a_pass"] or g["G1b_pass"] for g in res["placebo"].values())
    for c in cells:
        ck, rk = ("m_cong_vs_nc", "m_cong_run_s_nc") if c == "TRUCK" else ("m_cong_vs", "m_cong_run_s")
        G1 = {a: g1(T[f"{c}|{a}"], T[f"S|{a}"], ck, rk) for a in ("nc", "p333")}     # S has no capped truck: its _nc field is the full one
        nc = series(T[f"{c}|nc"], "all_delay")
        g2 = {a: eff(series(T[f"{c}|{a}"], "all_delay"), nc, -1) for a in ("p333", "3e")}
        g2_pass = any(e[0] >= 10.0 and e[1] > 0 for e in g2.values())
        g2_fallback, g2_pending = None, False
        if not g2_pass:     # planb.md §7.3: every carried rule runs before a KILL
            if all(f"{c}|{r}" in T for r in FALLBACK):
                g2_fallback = {r: eff(series(T[f"{c}|{r}"], "all_delay"), nc, -1) for r in FALLBACK}
                g2_pass = any(e[0] >= 10.0 and e[1] > 0 for e in g2_fallback.values())
            else:
                g2_pending = True
        loss = lambda a: series(T[f"{c}|{a}"], "all_delay") - series(T[f"S|{a}"], "all_delay")
        best = min(("p333", "3e"), key=lambda a: float(np.median(series(T[f"{c}|{a}"], "all_delay"))))
        g2l = eff(loss(best), loss("nc"), -1)
        g4 = {}
        for a in ("nc", "p333"):
            C, S = T[f"{c}|{a}"], T[f"S|{a}"]
            one_hz = np.median(series(C, "brake3") + series(C, "out_b3"))
            step = np.median(series(C, "b3_step"))
            bl_c, bl_s = np.median([backlog(r) for r in C]), np.median([backlog(r) for r in S])
            rq = {k: (float(np.median([ramp_queue(r, k) for r in C])), float(np.median([ramp_queue(r, k) for r in S]))) for k in ("ramp1_queue", "ramp2_queue")}
            g4[a] = {"pr09_ratio": float(one_hz / step) if step else None, "pr09_pass": bool(step) and bool(abs(one_hz / step - 1.0) <= 0.05),
                     "backlog": (float(bl_c), float(bl_s)), "backlog_pass": bool(bl_c <= (bl_s if c == "SURGE" else 1.1 * bl_s)),
                     "ramp_queue": rq, "ramp_queue_pass": all(x <= 1.1 * y for x, y in rq.values()),
                     "stuck_rows": int(sum(r["m_stuck_n"] > 0 for r in C)), "stuck_rows_S": int(sum(r["m_stuck_n"] > 0 for r in S)),
                     "stuck_pass": all(r["m_stuck_n"] == 0 for r in C)}
        pc, ps_ = T[f"{c}|p333"], T["S|p333"]
        g4["collisions_pass"] = bool(np.median(series(pc, "collisions")) <= np.median(series(ps_, "collisions")) + 1
                                     and np.median(series(pc, "contact_steps")) <= np.median(series(ps_, "contact_steps")) + 1)
        g4["pr24_pass"] = bool(trace.get(c)) and bool(trace.get("S"))
        g4["drain"] = drain.read_drain({a: T[f"{c}|{a}"] for a in drain.ARMS}, {a: T[f"S|{a}"] for a in drain.ARMS}, surge=c == "SURGE", seed=RNG)
        other = bool(g4["collisions_pass"]) and g4["pr24_pass"] and all(g4[a][k] for a in ("nc", "p333") for k in ("pr09_pass", "stuck_pass"))
        g4_pass = other and g4["drain"]["verdict"]["pass"]
        g4_registered = other and all(g4[a][k] for a in ("nc", "p333") for k in ("backlog_pass", "ramp_queue_pass"))
        g1_pass = all(G1[a]["G1a_pass"] and G1[a]["G1b_pass"] for a in ("nc", "p333"))
        location = {a: {"end_stop": float(np.median(series(T[f"{c}|{a}"], "end_stop"))), "end_stop2": float(np.median(series(T[f"{c}|{a}"], "end_stop2"))),
                        "ttc3_by_road_period": med_nested([r["m_road_ttc3"] for r in T[f"{c}|{a}"]])} for a in ("nc", "p333")}
        decided = g1_pass and g2_pass and g4_pass
        if res["null_broken"]:
            passes, status = None, "stopped: the placebo passed G1, the gate is broken (fix, log, re-run)"
        elif g2_pending and g1_pass and g4_pass:
            passes, status = None, "G2 pending: run the other carried rules in this cell (gates2.py fallback)"
        else:
            passes, status = decided, "passes" if decided else "drops"
        registered = None if res["null_broken"] or (g2_pending and g1_pass and g4_registered) else (g1_pass and g2_pass and g4_registered)
        res["cells"][c] = {"G1": G1, "G1_pass": g1_pass, "G2": g2, "G2_fallback": g2_fallback, "G2_pass": g2_pass, "G2_loss": {"best": best, "effect": g2l,
                           "report_only_pass": g2l[0] >= 10.0 and g2l[1] > 0}, "G4": g4, "G4_pass": g4_pass, "G4_pass_registered": g4_registered,
                           "passes_registered": registered, "location": location,
                           "passes": passes, "status": status, "drain_cap": DRAIN_FACTOR * max(r["m_pending_end"] for r in T[f"{c}|nc"])}
    ps_ = [v["passes"] for v in res["cells"].values()]
    res["kill"] = None if res["null_broken"] or (None in ps_ and True not in ps_) else not any(ps_)
    return res


def med_nested(ds: list) -> dict:
    keys = {(g, p) for d in ds for g, x in d.items() for p in x}
    return {f"{g}|{p}": float(np.median([d.get(g, {}).get(p, 0) for d in ds])) for g, p in sorted(keys)}


def main(argv: list) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("step", choices=("run", "trace", "fallback", "read"))
    ap.add_argument("--out", required=True)
    ap.add_argument("--cells", required=True)
    ap.add_argument("--fallback", default="")
    ap.add_argument("--result", default="s2.json", choices=("s2.json", "s2_v486.json"))
    ap.add_argument("--workers", type=int, default=4)
    a = ap.parse_args(argv)
    cells = a.cells.split(",")
    if sorted(cells) != sorted(pb.CELLS):     # every approved cell is gated, so none can leave S6 unread (review F9)
        ap.error(f"--cells must list every approved cell: {pb.CELLS}")
    out = Path(a.out).resolve()
    if a.step in ("run", "trace", "fallback"):
        pb.reserve(a.workers)
    if a.step == "run":
        run(out, cells, a.workers)
        return 0
    if a.step == "trace":
        print("G4(iv) traces:", trace(out, cells, a.workers))
        return 0
    if a.step == "fallback":
        fb = [c for c in a.fallback.split(",") if c]
        if not fb or not set(fb) <= set(cells):
            ap.error("--fallback names the cells where p333 and 3E-T failed G2")
        run_fallback(out, fb, a.workers)
        return 0
    rows = pb.cma2.load(out / "s2_runs.jsonl") + pb.cma2.load(out / "fallback" / "s2_fallback_runs.jsonl")
    T = {}
    for r in sorted(rows, key=lambda r: r["seed"]):
        T.setdefault(r["name"], []).append(r)
    fb_cells = sorted({n.split("|")[0] for n in T if n.split("|")[1] in FALLBACK})
    need = set(jobs(cells, "")) | set(fallback_jobs(fb_cells, ""))
    if set(T) != need or any([r["seed"] for r in v] != SEEDS for v in T.values()):
        raise SystemExit("S2 rows incomplete, duplicated or off the gate seeds")
    tf = out / "s2_trace.json"
    if not tf.exists():
        raise SystemExit("run the G4(iv) trace step first")
    metas = [out / "meta.json", out / "trace" / "meta.json"] + ([out / "fallback" / "meta.json"] if fb_cells else [])
    codes = [json.loads(m.read_text())["code"] if m.exists() else None for m in metas]
    if None in codes or any(c != codes[0] for c in codes):
        raise SystemExit(f"S2's rows, traces and fallback rows must come from one code: {[c and c['commit'] for c in codes]}")
    target = out / a.result
    here = pb.code_state()
    if a.result == "s2.json" and here != codes[0]:     # the registered name is written only at the rows' own code
        raise SystemExit(f"s2.json is written only at the code of the rows ({codes[0]['commit']}); this tree is {here['commit']}")
    if a.result != "s2.json" and (target.exists() or not (here["clean"] and here["detached"])):     # V486's re-read happens once
        raise SystemExit(f"{target} exists, or this tree is not clean and detached: the re-read happens once")
    res = read(T, cells, json.loads(tf.read_text())["pass"])
    res["code"] = codes[0]
    if a.result != "s2.json":
        res["read_code"] = here
    pb.cma2.write_json(target, json.loads(json.dumps(res, default=lambda x: x.item())))
    print("null broken: stage stopped" if res["null_broken"] else "null holds", "| KILL" if res["kill"] else "",
          {c: v["status"] for c, v in res["cells"].items()})
    return 3 if res["null_broken"] else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
