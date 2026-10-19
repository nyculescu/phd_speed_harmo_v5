"""Screen D2 Rules 1, 4 and 5 on numbers (pure; no SUMO). docs/research/protocols/screen_D2_incidents.md

Convention (CLAUDE.md, Statistics; as in D1, v5b/d1/stats.py): paired seeds, the median of paired differences,
95 % percentile bootstrap, B = 2,000, seeds resampled jointly. Delays: lower is better. For a baseline b and a
treatment o: d_i = b_i - o_i (> 0: o better), rel = median(d) / median(b).
"""
from __future__ import annotations

import numpy as np

from v5b.d1.stats import B_BOOT, BOOT_SEED, T0_MIN_REL, T1_MAX_TELEPORT_SHARE, paired, t0_check, t1_check  # noqa: F401

HD_MIN = 0.10      # Rule 5
T4_MIN_REL = 0.10  # Rule 1 T4
FALLBACKS = ("FX", "FB", "IP")


def t1_cells(teleports_by_cell: dict) -> dict:
    """Rule 1 T1: in every cell, the share of runs with >= 1 teleport is < 5 %."""
    per = {c: t1_check(v) for c, v in teleports_by_cell.items()}
    return {"cells": per, "pass": bool(per) and all(p["pass"] for p in per.values())}


def t0_cells(best_by_cell: dict, nc_by_cell: dict, best_name: dict) -> dict:
    """Rule 1 T0: in EVERY incident cell, the best of the arms (lowest median delay) beats NC by >= 10 %
    (median paired difference relative to NC) with the CI of the median paired difference > 0."""
    per = {}
    for c in best_by_cell:
        r = t0_check(best_by_cell[c], nc_by_cell[c])
        r["best_arm"] = best_name[c]
        per[c] = r
    return {"cells": per, "pass": bool(per) and all(p["pass"] for p in per.values())}


def t4_cell(n_delays, best_delays, n_id: str, best_id: str) -> dict:
    """Rule 1 T4 in one incident cell: rel = median(N - g*) / median(N) over paired seeds, where N is the
    no-incident tuned controller and g* the hindsight-best fixed controller of G in this cell's incident runs.
    The cell shows that 'the incident changes what is best' if rel >= 10 % (the page states no CI for T4;
    the CI is reported)."""
    r = paired(n_delays, best_delays)
    r.update({"N": n_id, "best_fixed": best_id, "same_controller": n_id == best_id,
              "pass": bool(n_id != best_id and r["rel"] >= T4_MIN_REL)})
    return r


def t4_overall(cells: dict) -> dict:
    """T4 passes if at least one incident cell passes (Rule 5 needs only one cell; reading recorded in the
    build report). Per-cell results are always reported."""
    return {"cells": cells, "n_pass": int(sum(c["pass"] for c in cells.values())),
            "pass": any(c["pass"] for c in cells.values())}


def _hd(base, o) -> dict:
    r = paired(base, o)
    return {"HD": r["rel"], "HD_ci": r["rel_ci"], "med_diff_s": r["med_diff"], "diff_ci": r["diff_ci"],
            "med": r["med_base"], "pass": bool(r["rel"] >= HD_MIN and r["rel_ci"][0] > 0.0)}


def headroom_cell(o, fallbacks: dict) -> dict:
    """Rule 5 in one cell: HD_f = (f - OR) / f, as median(f - OR) / median(f) over paired seeds, for every
    fallback f in {FX, FB, IP}; the cell passes only if HD_f >= 10 % with its CI lower bound > 0 for EVERY f."""
    o = np.asarray(o, float)
    per = {a: _hd(x, o) for a, x in fallbacks.items()}
    binding = min(per, key=lambda a: (per[a]["HD_ci"][0], a))
    return {"n": int(o.size), "med_OR": float(np.median(o)), "per_fallback": per, "binding": binding,
            "pass": all(p["pass"] for p in per.values())}


def cell_with_invalid_check(o, fallbacks: dict, invalid) -> dict:
    """Rule 4 (as D1 A5): if a seed has an invalid run among the compared runs (OR's chosen run, FX, FB, IP),
    the cell is also computed without those seeds; it passes only if it passes both ways (no valid seed: fails)."""
    inv = np.asarray(invalid, bool)
    c = headroom_cell(o, fallbacks)
    c["n_invalid_seeds"] = int(inv.sum())
    c["pass_all_seeds"] = c["pass"]
    c["valid_only"] = None
    if not inv.any():
        c["pass_valid_only"] = c["pass"]
    elif inv.all():
        c["pass_valid_only"] = False
    else:
        keep = ~inv
        v = headroom_cell(np.asarray(o, float)[keep], {a: np.asarray(x, float)[keep] for a, x in fallbacks.items()})
        c["valid_only"] = v
        c["pass_valid_only"] = v["pass"]
    c["pass"] = bool(c["pass_all_seeds"] and c["pass_valid_only"])
    return c


def decide(cells: dict) -> str:
    """Rule 5: CONTINUE if at least one incident cell passes, else STOP."""
    return "CONTINUE" if any(c.get("pass") for c in cells.values()) else "STOP"
