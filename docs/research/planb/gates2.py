"""Plan B S2 (planb.md §7.3, V480): plant gates per cell, with no v3w row. Arms: no control, p333 and 3E-T in each cell and in S on
7,480,010-049, and the placebo (V341's brake, the null of G1) with no control and p333. Each gate is read on medians over the 40
seeds; effects are round 2's paired statistic against each arm's own S row, 95 % percentile bootstrap, 20,000 resamples.
A cell passes S2 if G1a and G1b pass, G2 passes and G4 passes; a broken null (the placebo passes G1a or G1b) stops the stage.
The drain cap for S6 is 1.5 x the largest no-control end-of-run insertion backlog in the cell's rows.

usage: gates2.py run --out DIR --cells SURGE,TRUCK [--workers N]     the runs (pack on)
       gates2.py read --out DIR --cells SURGE,TRUCK                  the gate table, s2.json"""
import argparse
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import pb  # noqa: E402

SEEDS = pb.seeds(7_480_010, 7_480_049)
ARMS = ("nc", "p333", "3e")
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


def run(out: Path, cells: list, workers: int, runner=None) -> None:
    from v5b.fleet import plant_sweep  # noqa: F401  fail early without SUMO
    rr = runner or full_runner
    pb.batch(jobs(cells, str(out / "st")), SEEDS, out / "s2_runs.jsonl", out / "rd", workers, rr)


def full_row(a: tuple) -> dict:
    from v5b.fleet import plant_sweep as ps
    r = ps.run_one(a)
    keep = ("q", "seed", "all_delay", "ttc_net", "passed", "collisions", "contact_steps", "b3_step", "brake3", "out_b3", "end_stop", "end_stop2",
            "m_cong_vs", "m_cong_run_s", "m_cong_vs_nc", "m_cong_run_s_nc", "m_stuck_n", "m_pending_end", "m_main_pending_min", "m_road_ttc3",
            "m_robust_road", "m_capped", "pert_log")
    out = {k: r.get(k) for k in keep}
    out["m_minute"] = {k: r["m_minute"][k] for k in ("ramp1_pending", "ramp2_pending", "ramp1_queue", "ramp2_queue")}
    return out


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


def read(T: dict, cells: list) -> dict:
    """T: name -> rows in seed order."""
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
            g4[a] = {"pr09_ratio": float(one_hz / step) if step else None, "pr09_pass": bool(step) and abs(one_hz / step - 1.0) <= 0.05,
                     "backlog": (float(bl_c), float(bl_s)), "backlog_pass": bl_c <= (bl_s if c == "SURGE" else 1.1 * bl_s),
                     "ramp_queue": rq, "ramp_queue_pass": all(x <= 1.1 * y for x, y in rq.values()),
                     "stuck_rows": int(sum(r["m_stuck_n"] > 0 for r in C)), "stuck_pass": all(r["m_stuck_n"] == 0 for r in C)}
        pc, ps_ = T[f"{c}|p333"], T["S|p333"]
        g4["collisions_pass"] = (np.median(series(pc, "collisions")) <= np.median(series(ps_, "collisions")) + 1
                                 and np.median(series(pc, "contact_steps")) <= np.median(series(ps_, "contact_steps")) + 1)
        g4_pass = bool(g4["collisions_pass"]) and all(g4[a][k] for a in ("nc", "p333") for k in ("pr09_pass", "backlog_pass", "ramp_queue_pass", "stuck_pass"))
        g1_pass = all(G1[a]["G1a_pass"] and G1[a]["G1b_pass"] for a in ("nc", "p333"))
        location = {a: {"end_stop": float(np.median(series(T[f"{c}|{a}"], "end_stop"))), "end_stop2": float(np.median(series(T[f"{c}|{a}"], "end_stop2"))),
                        "ttc3_by_road_period": med_nested([r["m_road_ttc3"] for r in T[f"{c}|{a}"]])} for a in ("nc", "p333")}
        res["cells"][c] = {"G1": G1, "G1_pass": g1_pass, "G2": g2, "G2_pass": g2_pass, "G2_loss": {"best": best, "effect": g2l,
                           "report_only_pass": g2l[0] >= 10.0 and g2l[1] > 0}, "G4": g4, "G4_pass": g4_pass, "location": location,
                           "passes": g1_pass and g2_pass and g4_pass and not res["null_broken"],
                           "drain_cap": DRAIN_FACTOR * max(r["m_pending_end"] for r in T[f"{c}|nc"]),
                           "g2_failed_action": None if g2_pass else "run every carried rule in the cell before a KILL (planb.md §7.3)"}
    res["kill"] = not any(v["passes"] for v in res["cells"].values())
    return res


def med_nested(ds: list) -> dict:
    keys = {(g, p) for d in ds for g, x in d.items() for p in x}
    return {f"{g}|{p}": float(np.median([d.get(g, {}).get(p, 0) for d in ds])) for g, p in sorted(keys)}


def main(argv: list) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("step", choices=("run", "read"))
    ap.add_argument("--out", required=True)
    ap.add_argument("--cells", required=True)
    ap.add_argument("--workers", type=int, default=4)
    a = ap.parse_args(argv)
    cells = a.cells.split(",")
    if not set(cells) <= set(pb.CELLS):
        ap.error(f"cells: {pb.CELLS}")
    out = Path(a.out)
    if a.step == "run":
        run(out, cells, a.workers)
        return 0
    rows = pb.cma2.load(out / "s2_runs.jsonl")
    T = {}
    for r in sorted(rows, key=lambda r: r["seed"]):
        T.setdefault(r["name"], []).append(r)
    need = set(jobs(cells, ""))
    if set(T) != need or any(len(v) != len(SEEDS) for v in T.values()):
        raise SystemExit("S2 rows incomplete")
    res = read(T, cells)
    pb.cma2.write_json(out / "s2.json", res)
    print("null broken" if res["null_broken"] else "null holds", "| KILL" if res["kill"] else "",
          {c: ("passes" if v["passes"] else "drops") for c, v in res["cells"].items()})
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
