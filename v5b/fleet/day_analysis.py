"""Analysis of the no-control reference days (V167): Layer A safety, capacity per breakdown, conflict tail.

Conflict encounter = one follower-leader pair with TTC below the threshold u in consecutive whole seconds (a gap of
more than 1 s starts a new encounter); its severity is its lowest TTC. Peak over threshold on y = u - min TTC (the
excess of -TTC over -u), GPD with location 0 (V166 (c), Orsini et al. 2020). EVT crash estimate per encounter =
P(y >= u) = P(TTC reaches 0); 0 when the fitted tail ends before it (shape < 0, endpoint -scale/shape < u).
"""
from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path

import numpy as np
from scipy import stats

from v5b.fleet import day, fleet as fl
from v5b.fleet.smoke import CFG

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


_EB = re.compile(r"Vehicle '([^']+)' performs emergency braking on lane '([^']+)' with decel=([\d.]+), wished=([\d.]+),"
                 r" severity=([\d.]+), time=([\d.]+)")


def diagnostics(d: Path, rows: list) -> dict:
    """Who brakes at the emergency limit, and where; the collision events with the colliders' drawn parameters."""
    by_cls, by_place, hour, rate_n = Counter(), Counter(), Counter(), Counter()
    tau_eb, tau_all, asl_eb, asl_all, coll = [], [], [], [], []
    for r in rows:
        log = d / f"sumo_s{r['seed']}.log"
        if not log.exists():
            continue
        spec = fl.FleetDemand(r["seed"], day.profile(r["adt"]), CFG).by_id
        rate_n.update(v.cls for v in spec.values())
        tau_all += [v.tau for v in spec.values() if v.cls == "hdv_car"]
        asl_all += [v.asl for v in spec.values() if v.cls == "hdv_car"]
        for m in _EB.finditer(log.read_text(errors="replace")):
            v = spec[m.group(1)]
            lane = m.group(2)
            by_cls[v.cls] += 1
            by_place[("junction " if lane.startswith(":") else "edge ") + lane.split("_")[0].lstrip(":")] += 1
            hour[int(float(m.group(6).rstrip(".")) // 3600)] += 1
            if v.cls == "hdv_car":
                tau_eb.append(v.tau)
                asl_eb.append(v.asl)
        for c in r.get("collision_events", []):
            a, b = spec[c["collider"]], spec[c["victim"]]
            coll.append(c | {"collider_cls": a.cls, "victim_cls": b.cls, "collider_tau": a.tau,
                             "collider_asl": a.asl, "collider_sigma": a.sigma, "victim_tau": b.tau})
    n_eb = sum(by_cls.values())
    qs = (0.0, 0.25, 0.5, 0.75, 1.0)
    return {
        "emergency_braking": n_eb,
        "per_1000_vehicles_by_class": {c: round(1000 * by_cls[c] / rate_n[c], 1) for c in fl.CLASSES if rate_n[c]},
        "by_place": dict(by_place.most_common()), "by_hour": dict(sorted(hour.items())),
        "hdv_car_tau_quartiles_braking_vs_all": [list(np.round(np.quantile(tau_eb, qs), 2)) if tau_eb else None,
                                                 list(np.round(np.quantile(tau_all, qs), 2)) if tau_all else None],
        "hdv_car_asl_mean_braking_vs_all": [round(float(np.mean(asl_eb)), 3) if asl_eb else None,
                                            round(float(np.mean(asl_all)), 3) if asl_all else None],
        "collisions": coll,
    }


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
        rows.append({k: r.get(k) for k in (
            "seed", "adt", "collision_events", "generated", "arrived", "drained", "sumo_errors", "teleports",
            "collisions", "collision_pairs", "emergency_stops", "emergency_braking_warnings", "breakdowns",
            "vehicle_seconds", "closing_seconds", "ttc_seconds_below", "ttc_min", "delay_mean_by_class", "health",
            "wall_s")}
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
        "diagnostics": diagnostics(d, rows),
    }
    Path(a.out).write_text(json.dumps({"summary": summ, "days": rows}, indent=1))
    print(json.dumps(summ, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
