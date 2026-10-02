"""BN4 job: no-control run at a constant inflow (plant check T1 / T3, smoke and thermal burn).

Run as:  python -m vsl_lab.jobs.bn4_nc --inflow 1500 --seed 7110010 --tag t1sweep
Writes <run_dir>/summary.json and prints the run_dir on the last stdout line.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

import libsumo as ls

from vsl_lab.config import RUNS_ROOT
from vsl_lab.plants import bn4
from vsl_lab.sim.runner import SumoSim, outflow_vph


def run(inflow: float, seed: int, t_demand: float, t_max: float, av_share: float, lane_changing: bool,
        tag: str, out_root: Path, window: tuple, av_cap: float | None = None, av_cap_t: float | None = None) -> dict:
    run_id = (f"bn4_nc_q{int(inflow)}_s{seed}_td{int(t_demand)}_av{av_share:g}_lc{int(lane_changing)}"
              f"{'' if av_cap is None else f'_cap{av_cap:g}at{int(av_cap_t)}'}_pid{os.getpid()}")
    run_dir = out_root / tag / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    f = bn4.files()
    dem = bn4.demand(seed, [(0.0, t_demand, inflow)], av_share=av_share, lane_changing=lane_changing)
    rou = run_dir / f"routes_q{int(inflow)}_s{seed}_pid{os.getpid()}.rou.xml"
    dem.write(rou)
    sim = SumoSim(f["net"], rou, run_dir, dem, additional=[f["add"]], step_length=bn4.STEP_LENGTH,
                  checkpoint_s=300.0, seed=seed)
    av_ids = {vid for _, vid, _, vt in dem.vehicles if vt == "av"}
    sim.start()
    bn4.set_all_green()
    sim.asserts.append(bn4.assert_all_green)
    # H-R8: exit loop vs arrivals, compared at loop period boundaries
    period = 20.0
    loop_total, loop_mismatch = 0, 0
    capped = False
    next_p = period
    while sim.t < t_demand - 1e-9:
        sim.run_until(min(next_p, t_demand))
        if sim.t >= next_p - 1e-9:
            loop_total += bn4.exit_loop_count()
            next_p += period
        if av_cap is not None and not capped and sim.t >= av_cap_t - 1e-9:
            capped = True
        if capped:  # T0 step test: cap every AV currently on edges 2-4
            for e in ("2", "3", "4"):
                for vid in ls.edge.getLastStepVehicleIDs(e):
                    if vid in av_ids:
                        ls.vehicle.setMaxSpeed(vid, av_cap)
    drained = sim.drain(t_max)
    # final loop reading only if a full period just closed
    out = sim.close(drained=drained)
    arrived_at_last_boundary = sum(v for k, v in out["arrivals_bins"].items()
                                   if (int(k) + 1) * out["bin_s"] <= next_p - period + 1e-9)
    diff = loop_total - arrived_at_last_boundary
    if abs(diff) > 3:
        out["health"]["by_code"].setdefault("H-R8", {"level": "WARN", "n": 0})
        out["health"]["by_code"]["H-R8"]["n"] += 1
        if out["health"]["status"] == "PASS":
            out["health"]["status"] = "WARN"
    out.update({
        "job": "bn4_nc", "run_id": run_id, "inflow_vph": inflow, "seed": seed, "t_demand": t_demand,
        "av_share": av_share, "lane_changing": lane_changing, "av_cap": av_cap, "av_cap_t": av_cap_t,
        "loop_vs_arrivals_diff": diff,
        "outflow_window": list(window),
        "outflow_vph": round(outflow_vph(out, *window), 1),
        "realised_inflow_vph": round(out["generated"] * 3600.0 / t_demand, 1),
    })
    (run_dir / "summary.json").write_text(json.dumps(out, indent=1))
    try:
        rou.unlink()  # routes are reproducible from (seed, profile); keep raw dirs small
    except OSError:
        pass
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--inflow", type=float, required=True)
    ap.add_argument("--seed", type=int, required=True)
    ap.add_argument("--t-demand", type=float, default=1500.0)
    ap.add_argument("--t-max", type=float, default=7200.0)
    ap.add_argument("--av-share", type=float, default=0.1)
    ap.add_argument("--lane-changing", action="store_true")
    ap.add_argument("--window", type=float, nargs=2, default=(1000.0, 1500.0))
    ap.add_argument("--av-cap", type=float, default=None)
    ap.add_argument("--av-cap-t", type=float, default=None)
    ap.add_argument("--tag", default="smoke")
    ap.add_argument("--out-root", default=str(RUNS_ROOT / "t1"))
    a = ap.parse_args(argv)
    out = run(a.inflow, a.seed, a.t_demand, a.t_max, a.av_share, a.lane_changing, a.tag, Path(a.out_root),
              tuple(a.window), a.av_cap, a.av_cap_t)
    print(json.dumps({k: out[k] for k in ("run_id", "outflow_vph", "realised_inflow_vph", "hash", "wall_s",
                                            "sim_per_wall")} | {"health": out["health"]["status"]}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
