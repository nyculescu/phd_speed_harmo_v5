"""Analysis of the no-control reference days (V167): Layer A safety, capacity per breakdown, conflict tail.

Conflict encounter = one follower-leader pair with TTC below the threshold u in consecutive whole seconds (a gap of
more than 1 s starts a new encounter); its severity is its lowest TTC. Peak over threshold on y = u - min TTC (the
excess of -TTC over -u), GPD with location 0 (V166 (c), Orsini et al. 2020). EVT crash estimate per encounter =
P(y >= u) = P(TTC reaches 0); 0 when the fitted tail ends before it (shape < 0, endpoint -scale/shape < u).
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
from scipy import stats

THRESHOLDS = (1.0, 1.5, 3.0)
TARGET = 0.288     # crashes per day: P(>= 1 crash per day) = 25 % (V167)


def encounters(z, u: float) -> np.ndarray:
    m = z["ttc"] < u
    t, f, l, ttc = z["t"][m], z["follower"][m], z["leader"][m], z["ttc"][m]
    order = np.lexsort((t, l, f))
    t, f, l, ttc = t[order], f[order], l[order], ttc[order]
    new = np.ones(len(t), bool)
    new[1:] = (f[1:] != f[:-1]) | (l[1:] != l[:-1]) | (t[1:] - t[:-1] > 1.0 + 1e-3)
    gid = np.cumsum(new) - 1
    out = np.full(gid[-1] + 1 if len(gid) else 0, np.inf)
    np.minimum.at(out, gid, ttc)
    return out


def tail(mins: np.ndarray, u: float, n_days: int) -> dict:
    y = u - mins
    if len(y) < 30:
        return {"n": int(len(y)), "fit": None}
    c, _, scale = stats.genpareto.fit(y, floc=0.0)
    end = -scale / c if c < 0 else np.inf
    p0 = float(stats.genpareto.sf(u, c, 0.0, scale))
    ks = stats.kstest(y, "genpareto", args=(c, 0.0, scale))
    return {"n": int(len(y)), "per_day": round(len(y) / n_days, 1), "shape": round(float(c), 4),
            "scale": round(float(scale), 4), "endpoint_ttc": round(float(u - end), 3) if np.isfinite(end) else None,
            "p_crash_per_encounter": p0, "evt_crashes_per_day": len(y) / n_days * p0,
            "ks_p": round(float(ks.pvalue), 4), "min_ttc_seen": round(float(mins.min()), 3)}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    d = Path(a.runs)
    days = sorted(d.glob("day_s*.json"))
    rows, mins = [], {u: [] for u in THRESHOLDS}
    for f in days:
        r = json.loads(f.read_text())
        z = np.load(d / f"conflicts_s{r['seed']}.npz")
        for u in THRESHOLDS:
            mins[u].append(encounters(z, u))
        rows.append({k: r[k] for k in ("seed", "generated", "arrived", "drained", "sumo_errors", "teleports",
                                       "collisions", "collision_pairs", "emergency_stops",
                                       "emergency_braking_warnings", "breakdowns", "vehicle_seconds",
                                       "closing_seconds", "ttc_seconds_below", "ttc_min", "delay_mean_by_class",
                                       "health", "wall_s")}
                    | {"encounters": {f"{u:g}": int(len(mins[u][-1])) for u in THRESHOLDS}})
    n = len(rows)
    bks = [b for r in rows for b in r["breakdowns"] if b["drop"] is not None and b["min"] >= 15]

    def med(xs):
        xs = [x for x in xs if x is not None]
        return round(float(np.median(xs)), 3) if xs else None

    summ = {
        "days": n, "seeds": [r["seed"] for r in rows],
        "layer_a": {"collisions": sum(r["collisions"] for r in rows), "teleports": sum(r["teleports"] for r in rows),
                    "emergency_stops": sum(r["emergency_stops"] for r in rows),
                    "emergency_braking_per_day": med([r["emergency_braking_warnings"] for r in rows]),
                    "all_drained": all(r["drained"] for r in rows), "sumo_errors": sum(r["sumo_errors"] for r in rows)},
        "capacity": {"breakdowns_per_day": med([len(r["breakdowns"]) for r in rows]), "n_used": len(bks),
                     "pre_median": med([b["pre"] for b in bks]), "qdf_median": med([b["qdf"] for b in bks]),
                     "drop_median": med([b["drop"] for b in bks]),
                     "drop_range": [round(min(b["drop"] for b in bks), 3), round(max(b["drop"] for b in bks), 3)]
                     if bks else None, "duration_min_median": med([b["min"] for b in bks])},
        "tail": {f"{u:g}": tail(np.concatenate(mins[u]), u, n) for u in THRESHOLDS},
        "target_crashes_per_day": TARGET,
    }
    Path(a.out).write_text(json.dumps({"summary": summ, "days": rows}, indent=1))
    print(json.dumps(summ, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
