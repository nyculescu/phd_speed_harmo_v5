"""Roadmap §9 C1 convergence check for a finished training run (S0 of the context-aware restart, 2026-10-04).

Inputs are the run dir's `val.csv` (validation every `val_every` updates, plus a "final" row) and `progress.csv`
(one row per update; `entropy` holds SB3's `train/entropy_loss`, i.e. minus the mean policy entropy).

Criteria (all computed on scores oriented so that higher is better, s = sign * metric):
- C1a final vs best: (best - final) / |best| <= 2 %   (R6's finals were 6.7-10.7 % worse than their best checkpoint)
- C1b window level: mean of the validation points in the last `window` updates is within 2 % of the run's best
- C1c window slope: |OLS slope| over those points < 0.5 % of |best| per 100 updates (needs >= 3 points)
- C1d explained variance: mean over the last `window` updates > 0.6
- C1e entropy stable: |mean entropy(last window) - mean entropy(previous window)| / mean(previous) <= 10 %
- C1f entropy floor (discrete actions only): mean entropy over the last window >= 0.25 * ln(n_actions)
  (R6's learners collapsed to 0.16-0.22 nats with 4 actions; ln 4 = 1.39)

C1a-C1d follow the roadmap text; the 10 % stability tolerance and the 0.25 * ln(n) floor are this lab's conventions
(no literature source), fixed here before any run uses them. A criterion without data is "n/a" and does not fail;
`converged` is True only if every applicable criterion passes.

python -m vsl_lab.train.convergence <run_dir> [--n-actions 4]
"""
from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path

MIN_SIGNS = ("tts_ctrl_vehh", "mean_time_in_system_s", "score_h", "tts_system_ctrl_vehh")
TOL_FINAL = 0.02
TOL_WINDOW = 0.02
TOL_SLOPE_PER100 = 0.005
EV_MIN = 0.6
ENT_STABLE_TOL = 0.10
ENT_FLOOR_FRAC = 0.25


def _f(x) -> float:
    try:
        v = float(x)
    except (TypeError, ValueError):
        return math.nan
    return v


def _mean(xs: list[float]) -> float:
    xs = [x for x in xs if x == x]
    return sum(xs) / len(xs) if xs else math.nan


def _slope(xs: list[float], ys: list[float]) -> float:
    n = len(xs)
    mx, my = sum(xs) / n, sum(ys) / n
    sxx = sum((x - mx) ** 2 for x in xs)
    return sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / sxx if sxx > 0 else math.nan


def entropy_floor(n_actions) -> float:
    """Floor in nats for a Discrete(n) action (int) or MultiDiscrete (list of n); NaN if not discrete."""
    if n_actions is None:
        return math.nan
    ns = n_actions if isinstance(n_actions, (list, tuple)) else [n_actions]
    return ENT_FLOOR_FRAC * sum(math.log(n) for n in ns if n > 1)


def check(val_rows: list[dict], prog_rows: list[dict], sign: float, n_actions=None, window: int = 100) -> dict:
    """val_rows: dicts with 'update' (int or 'final') and 'val_metric_value'; prog_rows: 'update', 'explained_var',
    'entropy' (= entropy_loss). Returns per-criterion values, pass flags (True/False/None) and `converged`."""
    pts = []
    n_upd = max((int(r["update"]) for r in prog_rows if str(r.get("update", "")).isdigit()), default=0)
    for r in val_rows:
        u = r["update"]
        v = _f(r.get("val_metric_value"))
        if v != v:
            continue
        pts.append((n_upd if str(u) == "final" else int(u), sign * v, str(u) == "final"))
    out: dict = {"updates_done": n_upd, "window": window, "n_val_points": len(pts)}
    trained = [p for p in pts if p[0] > 0]
    best = max((p[1] for p in trained), default=math.nan)
    final = next((p[1] for p in pts if p[2]), math.nan)
    out["best_score"], out["final_score"] = best, final

    def rel_gap(x):
        return (best - x) / abs(best) if best == best and x == x and best != 0 else math.nan

    out["C1a_final_vs_best"] = rel_gap(final)
    lo = n_upd - window
    win = sorted([p for p in trained if p[0] >= lo], key=lambda p: p[0])
    out["C1b_window_vs_best"] = rel_gap(_mean([p[1] for p in win]))
    if len(win) >= 3 and best == best and best != 0:
        out["C1c_slope_per100_rel"] = abs(_slope([p[0] for p in win], [p[1] for p in win])) * 100.0 / abs(best)
    else:
        out["C1c_slope_per100_rel"] = math.nan
    ev = [_f(r.get("explained_var")) for r in prog_rows if str(r.get("update", "")).isdigit() and int(r["update"]) > lo]
    out["C1d_ev_window"] = _mean(ev)
    ent = {int(r["update"]): -_f(r.get("entropy")) for r in prog_rows if str(r.get("update", "")).isdigit()}
    e_last = _mean([v for u, v in ent.items() if u > lo])
    e_prev = _mean([v for u, v in ent.items() if lo - window < u <= lo])
    out["entropy_last"], out["entropy_prev"] = e_last, e_prev
    out["C1e_entropy_change_rel"] = abs(e_last - e_prev) / abs(e_prev) if e_prev == e_prev and e_prev != 0 and e_last == e_last else math.nan
    out["entropy_floor"] = entropy_floor(n_actions)
    out["C1f_entropy_last"] = e_last if out["entropy_floor"] == out["entropy_floor"] else math.nan

    def ok(x, test):
        return None if x != x else bool(test(x))

    passes = {
        "C1a": ok(out["C1a_final_vs_best"], lambda x: x <= TOL_FINAL),
        "C1b": ok(out["C1b_window_vs_best"], lambda x: x <= TOL_WINDOW),
        "C1c": ok(out["C1c_slope_per100_rel"], lambda x: x < TOL_SLOPE_PER100),
        "C1d": ok(out["C1d_ev_window"], lambda x: x > EV_MIN),
        "C1e": ok(out["C1e_entropy_change_rel"], lambda x: x <= ENT_STABLE_TOL),
        "C1f": ok(out["C1f_entropy_last"], lambda x: x >= out["entropy_floor"]),
    }
    out["pass"] = passes
    out["converged"] = all(v is not False for v in passes.values()) and any(v is not None for v in passes.values())
    return out


def check_run_dir(run_dir: Path, n_actions=None, window: int = 100) -> dict:
    run_dir = Path(run_dir)
    cfg = json.loads((run_dir / "config.json").read_text())
    sign = -1.0 if cfg.get("val_metric") in MIN_SIGNS else 1.0
    with open(run_dir / "val.csv") as f:
        val_rows = list(csv.DictReader(f))
    with open(run_dir / "progress.csv") as f:
        prog_rows = list(csv.DictReader(f))
    return check(val_rows, prog_rows, sign, n_actions=n_actions, window=window)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("run_dir", nargs="+")
    ap.add_argument("--n-actions", type=int, nargs="*", default=None)
    ap.add_argument("--window", type=int, default=100)
    a = ap.parse_args(argv)
    na = None if not a.n_actions else (a.n_actions[0] if len(a.n_actions) == 1 else a.n_actions)
    for d in a.run_dir:
        r = check_run_dir(Path(d), n_actions=na, window=a.window)
        print(json.dumps({"run_dir": d, "converged": r["converged"], "pass": r["pass"],
                          **{k: (round(v, 4) if isinstance(v, float) else v) for k, v in r.items()
                             if k.startswith("C1") or k.startswith("entropy")}}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
