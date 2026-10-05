"""Roadmap §9 C1 convergence check for a finished training run (S0 of the context-aware restart, 2026-10-04).

Inputs are the run dir's `val.csv` (validation every `val_every` updates, plus a "final" row) and `progress.csv`
(one row per update; `entropy` holds SB3's `train/entropy_loss`, i.e. minus the mean policy entropy).

Criteria (C1a-C1c on the validation RETURN, as roadmap §9 C1 says; the same three are also reported on the
selection metric as metric_C1a..c):
- C1a final vs best: (best - final) / |best| <= 2 %   (R6's finals were 6.7-10.7 % worse than their best checkpoint)
- C1b window level: mean of the validation points in the last `window` updates is within 2 % of the run's best
- C1c window slope: |OLS slope| over those points < 0.5 % of |best| per 100 updates (needs >= 3 distinct updates)
  The 'final' val row counts once: it is skipped in C1b/C1c when a periodic row exists at the same update.
- C1d explained variance: mean over the last `window` updates > 0.6
- C1e entropy stable: discrete actions: |mean entropy(last window) - mean(previous window)| / mean(previous) <= 10 %;
  continuous actions: absolute change <= 0.1 nats per action dimension (differential entropy has no fixed zero)
- C1f entropy floor (discrete actions only): mean entropy over the last window >= 0.25 * ln(n_actions)
- Missing entropy (e.g. sb3-contrib TRPO logs no entropy_loss) makes C1e (and C1f for discrete) FAIL, not n/a.

C1a-C1d follow the roadmap text. The 10 % stability tolerance, the 0.1-nat continuous tolerance and the 0.25 * ln(n)
floor are this lab's conventions (no literature source), fixed before any run used them (the continuous rule and
the review fixes #8-#11 on 2026-10-05, before any new training run). A criterion without data is "n/a" and does not
fail, except the entropy rule above; `converged` is True only if every applicable criterion passes.

python -m vsl_lab.train.convergence <run_dir> [--n-actions 4 | --action-dim 2]
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
ENT_ABS_TOL_PER_DIM = 0.10   # continuous actions: |delta entropy| in nats per action dimension (review fix #10)


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


def _scores(val_rows: list, n_upd: int, col: str, sign: float) -> list:
    """(update, score, is_final) per validation row; the 'final' row is placed at n_upd."""
    pts = []
    for r in val_rows:
        u = r["update"]
        v = _f(r.get(col))
        if v != v:
            continue
        pts.append((n_upd if str(u) == "final" else int(u), sign * v, str(u) == "final"))
    return pts


def _c1abc(pts: list, n_upd: int, window: int) -> dict:
    """C1a-C1c on one score series. The 'final' row is used for C1a only: when a periodic row exists at the same
    update (val_every divides updates) it is the same model on the same seeds, so counting it in the window would
    double-weight that point (review fix #8). C1c needs >= 3 distinct update positions."""
    trained = [p for p in pts if p[0] > 0 and not p[2]]
    best = max((p[1] for p in trained), default=math.nan)
    final = next((p[1] for p in pts if p[2]), math.nan)
    if final != final and trained:            # no final row: last periodic point stands in
        final = max(trained, key=lambda p: p[0])[1]
    best = max(best, final) if best == best and final == final else best

    def rel_gap(x):
        return (best - x) / abs(best) if best == best and x == x and best != 0 else math.nan

    win = sorted([p for p in trained if p[0] >= n_upd - window], key=lambda p: p[0])
    if final == final and not any(p[0] == n_upd for p in win):
        win.append((n_upd, final, True))       # final row counts once, only if no periodic row at n_upd
    out = {"best": best, "final": final, "n_window_points": len(win),
           "C1a": rel_gap(final), "C1b": rel_gap(_mean([p[1] for p in win]))}
    xs = [p[0] for p in win]
    if len(set(xs)) >= 3 and best == best and best != 0:
        out["C1c"] = abs(_slope(xs, [p[1] for p in win])) * 100.0 / abs(best)
    else:
        out["C1c"] = math.nan
    return out


def check(val_rows: list[dict], prog_rows: list[dict], sign: float, n_actions=None, window: int = 100,
          action_dim: int | None = None) -> dict:
    """val_rows: dicts with 'update' (int or 'final'), 'val_return' and 'val_metric_value'; prog_rows: 'update',
    'explained_var', 'entropy' (= entropy_loss). `sign` orients the selection metric (+1 maximise, -1 minimise).
    n_actions: Discrete n / MultiDiscrete list (discrete entropy rules); action_dim: Box dimension (continuous)."""
    n_upd = max((int(r["update"]) for r in prog_rows if str(r.get("update", "")).isdigit()), default=0)
    out: dict = {"updates_done": n_upd, "window": window}
    # roadmap §9 C1 is defined on the validation RETURN (review fix #11); the selection metric is reported too
    ret = _c1abc(_scores(val_rows, n_upd, "val_return", 1.0), n_upd, window)
    met = _c1abc(_scores(val_rows, n_upd, "val_metric_value", sign), n_upd, window)
    out["n_val_points"] = ret["n_window_points"]
    out["best_score"], out["final_score"] = ret["best"], ret["final"]
    out["C1a_final_vs_best"], out["C1b_window_vs_best"], out["C1c_slope_per100_rel"] = ret["C1a"], ret["C1b"], ret["C1c"]
    out["metric_C1a"], out["metric_C1b"], out["metric_C1c"] = met["C1a"], met["C1b"], met["C1c"]
    lo = n_upd - window
    ev = [_f(r.get("explained_var")) for r in prog_rows if str(r.get("update", "")).isdigit() and int(r["update"]) > lo]
    out["C1d_ev_window"] = _mean(ev)
    ent = {int(r["update"]): -_f(r.get("entropy")) for r in prog_rows if str(r.get("update", "")).isdigit()}
    e_last = _mean([v for u, v in ent.items() if u > lo])
    e_prev = _mean([v for u, v in ent.items() if lo - window < u <= lo])
    out["entropy_last"], out["entropy_prev"] = e_last, e_prev
    discrete = n_actions is not None
    out["entropy_kind"] = "discrete" if discrete else ("continuous" if action_dim else "unknown")
    if e_last == e_last and e_prev == e_prev:
        if discrete:
            out["C1e_entropy_change"] = abs(e_last - e_prev) / abs(e_prev) if e_prev != 0 else math.inf
            out["C1e_tol"] = ENT_STABLE_TOL                      # relative (entropy >= 0, bounded by ln n)
        else:
            # review fix #10: differential entropy has no fixed zero -> absolute change in nats, 0.1 per action
            # dimension (= a ~10 % change of each Gaussian std); lab convention, fixed 2026-10-05
            out["C1e_entropy_change"] = abs(e_last - e_prev)
            out["C1e_tol"] = ENT_ABS_TOL_PER_DIM * (action_dim or 1)
    else:
        out["C1e_entropy_change"], out["C1e_tol"] = math.nan, math.nan
    out["entropy_floor"] = entropy_floor(n_actions)
    out["C1f_entropy_last"] = e_last if out["entropy_floor"] == out["entropy_floor"] else math.nan

    def ok(x, test):
        return None if x != x else bool(test(x))

    passes = {
        "C1a": ok(out["C1a_final_vs_best"], lambda x: x <= TOL_FINAL),
        "C1b": ok(out["C1b_window_vs_best"], lambda x: x <= TOL_WINDOW),
        "C1c": ok(out["C1c_slope_per100_rel"], lambda x: x < TOL_SLOPE_PER100),
        "C1d": ok(out["C1d_ev_window"], lambda x: x > EV_MIN),
        "C1e": ok(out["C1e_entropy_change"], lambda x: x <= out["C1e_tol"]),
        "C1f": ok(out["C1f_entropy_last"], lambda x: x >= out["entropy_floor"]),
    }
    # review fix #9: missing entropy (e.g. TRPO logs no entropy_loss) must not pass silently
    if e_last != e_last:
        passes["C1e"] = False
        if discrete:
            passes["C1f"] = False
        out["entropy_note"] = "entropy not logged: C1e (and C1f for discrete actions) not evaluable -> FAIL"
    out["pass"] = passes
    out["converged"] = all(v is not False for v in passes.values()) and any(v is not None for v in passes.values())
    return out


def check_run_dir(run_dir: Path, n_actions=None, window: int = 100, action_dim: int | None = None) -> dict:
    run_dir = Path(run_dir)
    cfg = json.loads((run_dir / "config.json").read_text())
    sign = -1.0 if cfg.get("val_metric") in MIN_SIGNS else 1.0
    with open(run_dir / "val.csv") as f:
        val_rows = list(csv.DictReader(f))
    with open(run_dir / "progress.csv") as f:
        prog_rows = list(csv.DictReader(f))
    return check(val_rows, prog_rows, sign, n_actions=n_actions, window=window, action_dim=action_dim)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("run_dir", nargs="+")
    ap.add_argument("--n-actions", type=int, nargs="*", default=None)
    ap.add_argument("--window", type=int, default=100)
    ap.add_argument("--action-dim", type=int, default=None)
    a = ap.parse_args(argv)
    na = None if not a.n_actions else (a.n_actions[0] if len(a.n_actions) == 1 else a.n_actions)
    for d in a.run_dir:
        r = check_run_dir(Path(d), n_actions=na, window=a.window, action_dim=a.action_dim)
        print(json.dumps({"run_dir": d, "converged": r["converged"], "pass": r["pass"],
                          **{k: (round(v, 4) if isinstance(v, float) else v) for k, v in r.items()
                             if k.startswith("C1") or k.startswith("entropy")}}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
