#!/usr/bin/env python3
"""
Ramp VSL isolation diagnostic: independently varies mainline and ramp VSL
to determine whether the ramp action dimension is learnable.

Grid:
  Mainline VSL: [None (=120 kph), 90 kph]
  Ramp VSL:     [40, 60, 90 kph]    (90 = no restriction)
  Demands:      [6500, 7000 vph]
  Total:        12 scenarios, run in parallel.

Key new metric: CAV-only speed tracking on ramp_on_transition, separate from
E1 (which averages CAVs and HDVs).

Uses the 3-zone slowDown logic from env_interact.py:
  - seg_0/1/2_before → mainline_vsl
  - ramp_on_approach + ramp_on_transition → ramp_vsl
  - everything else → no slowDown (free-flow)

Usage:
    python3 tests/run_ramp_vsl_isolation_sweep.py
"""
from __future__ import annotations

import csv
import os
import shutil
import sys
import tempfile
import time
import xml.etree.ElementTree as ET
from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

_SUMO_HOME = os.environ.get("SUMO_HOME", "/usr/share/sumo")
if os.path.join(_SUMO_HOME, "tools") not in sys.path:
    sys.path.insert(0, os.path.join(_SUMO_HOME, "tools"))

_SUMO_DIR = Path(__file__).resolve().parents[1] / "traffic_environment" / "sumo"
_NET_FILE = _SUMO_DIR / "ramps_v1.net.xml"
_DET_FILE = _SUMO_DIR / "detectors_ramps_v1.add.xml"
_RESULTS_ROOT = Path(__file__).resolve().parent / "results"

_EPISODE_S = 3600
_AGG_TIME = 30
_CAV_PCT = 50.0
_RAMP_DELAY_S = 100.0

# Independent parameter grid
_MAINLINE_VSL_LEVELS: List[Optional[float]] = [None, 90.0]
_RAMP_VSL_LEVELS: List[float] = [40.0, 60.0, 90.0]
_DEMAND_LEVELS: List[int] = [6500, 7000]

_MAINLINE_THROUGH_FRAC = 0.75
_RAMP_ON_FRAC = 0.15
_MAINLINE_TO_OFF_FRAC = 0.10

_ALL_SEGS = [
    "seg_3_before", "seg_2_before", "seg_1_before", "seg_0_before",
    "seg_0_after", "seg_1_after",
    "ramp_on_approach", "ramp_on_transition", "ramp_on_merge",
    "ramp_off_diverge", "ramp_off_transition", "ramp_off_departure",
]

_LANE_COUNTS: Dict[str, int] = {
    "seg_3_before": 3, "seg_2_before": 3, "seg_1_before": 3, "seg_0_before": 3,
    "seg_0_after": 4, "seg_1_after": 3,
    "ramp_on_approach": 1, "ramp_on_transition": 1, "ramp_on_merge": 1,
    "ramp_off_diverge": 1, "ramp_off_transition": 1, "ramp_off_departure": 1,
}

# 3-zone slowDown: matches env_interact.py Step 0 fix
_MAINLINE_CONTROLLED_EDGES = {"seg_0_before", "seg_1_before", "seg_2_before"}
_RAMP_CONTROLLED_EDGES = {"ramp_on_approach", "ramp_on_transition"}

# Measurement zones
_UPSTREAM_EDGES = {"seg_3_before", "seg_2_before", "seg_1_before", "seg_0_before"}
_RAMP_EDGES_ALL = {"ramp_on_approach", "ramp_on_transition", "ramp_on_merge"}
_MERGE_DS_EDGES = {"seg_0_after", "seg_1_after"}


def _generate_route_file(output_path: Path, demand_vph: int, episode_s: int, cav_pct: float) -> None:
    routes = ET.Element("routes")
    ET.SubElement(routes, "vType", id="HDV", carFollowModel="Krauss",
                  vClass="passenger", color="1,1,0", length="4.50", minGap="2.50",
                  accel="2.60", decel="4.50", sigma="0.50", maxSpeed="36.11",
                  tau="1.40", speedFactor="1.00", speedDev="0.10")
    ET.SubElement(routes, "vType", id="CAV", carFollowModel="Krauss",
                  vClass="passenger", color="0,1,0", length="4.50", minGap="1.25",
                  accel="2.86", decel="4.73", sigma="0.00", maxSpeed="36.11",
                  tau="1.00", speedFactor="1.00", speedDev="0.00")
    ET.SubElement(routes, "route", id="mainline_through",
                  edges="seg_3_before seg_2_before seg_1_before seg_0_before seg_0_after seg_1_after")
    ET.SubElement(routes, "route", id="ramp_on_through",
                  edges="ramp_on_approach ramp_on_transition ramp_on_merge seg_0_after seg_1_after")
    ET.SubElement(routes, "route", id="mainline_to_off",
                  edges="seg_3_before seg_2_before seg_1_before seg_0_before seg_0_after ramp_off_diverge ramp_off_transition ramp_off_departure")

    total_veh = int(demand_vph * episode_s / 3600)
    n_mainline = int(total_veh * _MAINLINE_THROUGH_FRAC)
    n_ramp = int(total_veh * _RAMP_ON_FRAC)
    n_off = total_veh - n_mainline - n_ramp
    vehicles: List[Tuple[float, str]] = []

    def _emit(count, route_id, t_offset, t_span):
        if count <= 0:
            return
        step = t_span / count
        for i in range(count):
            dep = t_offset + (i + 0.5) * step
            if dep > episode_s:
                break
            vehicles.append((dep, route_id))

    _emit(n_mainline, "mainline_through", 0.0, float(episode_s))
    _emit(n_off, "mainline_to_off", 0.0, float(episode_s))
    _emit(n_ramp, "ramp_on_through", _RAMP_DELAY_S, float(episode_s) - _RAMP_DELAY_S)
    vehicles.sort(key=lambda v: v[0])

    rng = np.random.default_rng(42)
    for vid, (dep, rid) in enumerate(vehicles):
        is_cav = rng.random() * 100.0 < cav_pct
        ET.SubElement(routes, "vehicle", id=f"veh_{vid}", type="CAV" if is_cav else "HDV",
                      route=rid, depart=f"{dep:.2f}", departPos="last", departLane="best",
                      departSpeed="desired", insertionChecks="none")
    tree = ET.ElementTree(routes)
    ET.indent(tree, space="  ")
    tree.write(str(output_path), encoding="unicode", xml_declaration=True)


def _generate_sumocfg(cfg_path: Path, rou_path: Path) -> None:
    cfg_path.write_text(f"""<?xml version="1.0" encoding="UTF-8"?>
<configuration>
    <input>
        <net-file value="{_NET_FILE.resolve()}"/>
        <route-files value="{rou_path.resolve()}"/>
        <additional-files value="{_DET_FILE.resolve()}"/>
    </input>
    <time>
        <begin value="0"/>
        <end value="{_EPISODE_S}"/>
    </time>
</configuration>
""", encoding="utf-8")


def _read_e1_segment(conn, seg: str, position: str, n_lanes: int):
    counts, speeds, occs = [], [], []
    for lane_idx in range(n_lanes):
        det_id = f"flow_loop_{seg}_{lane_idx}_{position}"
        try:
            cnt = float(conn.inductionloop.getLastIntervalVehicleNumber(det_id))
            spd = float(conn.inductionloop.getLastIntervalMeanSpeed(det_id))
            occ = float(conn.inductionloop.getLastIntervalOccupancy(det_id))
            counts.append(cnt)
            speeds.append(max(0.0, spd))
            occs.append(occ)
        except Exception:
            pass
    flow_vph = sum(counts) * (3600.0 / _AGG_TIME)
    total_cnt = sum(counts)
    if total_cnt > 0.5:
        speed_ms = sum(c * s for c, s in zip(counts, speeds)) / total_cnt
    else:
        speed_ms = float(np.mean(speeds)) if speeds else 0.0
    return flow_vph, speed_ms * 3.6, float(np.mean(occs)) if occs else 0.0


# ---------------------------------------------------------------------------
# Single scenario worker
# ---------------------------------------------------------------------------

def _run_scenario(
    demand_vph: int,
    mainline_vsl_kph: Optional[float],
    ramp_vsl_kph: float,
) -> Dict[str, Any]:
    """Run one episode with independent mainline and ramp VSL."""
    import traci

    ml_label = f"ML{int(mainline_vsl_kph) if mainline_vsl_kph else 'NC'}"
    rp_label = f"RP{int(ramp_vsl_kph)}"
    label = f"iso_{ml_label}_{rp_label}_{demand_vph}"
    tmpdir = Path(tempfile.mkdtemp(prefix=f"riso_{label}_"))
    rou_path = tmpdir / "flows.rou.xml"
    cfg_path = tmpdir / "sim.sumocfg"

    _generate_route_file(rou_path, demand_vph, _EPISODE_S, _CAV_PCT)
    _generate_sumocfg(cfg_path, rou_path)

    mainline_vsl_ms = (mainline_vsl_kph / 3.6) if mainline_vsl_kph is not None else None
    ramp_vsl_ms = ramp_vsl_kph / 3.6

    cmd = ["sumo", "-c", str(cfg_path), "--start", "--no-step-log", "--no-warnings"]
    traci.start(cmd, label=label)
    conn = traci.getConnection(label)

    # Accumulators
    up_all_accels: List[float] = []
    up_veh_seconds = 0
    ramp_all_accels: List[float] = []
    ramp_veh_seconds = 0
    md_all_accels: List[float] = []
    md_veh_seconds = 0

    # CAV-only speed tracking on ramp_on_transition
    ramp_trans_cav_speeds: List[float] = []
    ramp_trans_hdv_speeds: List[float] = []

    # E1 records
    e1_records: List[Dict] = []
    max_steps = _EPISODE_S // _AGG_TIME

    try:
        for step_idx in range(max_steps):
            for sub_step in range(_AGG_TIME):
                # 3-zone slowDown (matches env_interact.py)
                for veh_id in conn.vehicle.getIDList():
                    vtype = conn.vehicle.getTypeID(veh_id)
                    if "cav" not in vtype.lower():
                        continue
                    edge = conn.vehicle.getRoadID(veh_id)
                    if edge in _MAINLINE_CONTROLLED_EDGES and mainline_vsl_ms is not None:
                        conn.vehicle.slowDown(veh_id, mainline_vsl_ms, float(_AGG_TIME))
                    elif edge in _RAMP_CONTROLLED_EDGES:
                        conn.vehicle.slowDown(veh_id, ramp_vsl_ms, float(_AGG_TIME))
                    # else: no slowDown — free-flow

                conn.simulationStep()

                sim_time = step_idx * _AGG_TIME + sub_step + 1
                if sim_time <= 150:
                    continue

                # Per-vehicle data collection
                for veh_id in conn.vehicle.getIDList():
                    edge = conn.vehicle.getRoadID(veh_id)
                    if edge.startswith(":"):
                        continue

                    try:
                        accel = float(conn.vehicle.getAcceleration(veh_id))
                    except Exception:
                        continue

                    if edge in _UPSTREAM_EDGES:
                        up_all_accels.append(accel)
                        up_veh_seconds += 1
                    elif edge in _RAMP_EDGES_ALL:
                        ramp_all_accels.append(accel)
                        ramp_veh_seconds += 1
                    elif edge in _MERGE_DS_EDGES:
                        md_all_accels.append(accel)
                        md_veh_seconds += 1

                    # CAV vs HDV speed tracking on ramp_on_transition
                    if edge == "ramp_on_transition":
                        try:
                            spd_ms = float(conn.vehicle.getSpeed(veh_id))
                            spd_kph = spd_ms * 3.6
                            vtype = conn.vehicle.getTypeID(veh_id)
                            if "cav" in vtype.lower():
                                ramp_trans_cav_speeds.append(spd_kph)
                            else:
                                ramp_trans_hdv_speeds.append(spd_kph)
                        except Exception:
                            pass

            # E1 at end of window
            row = {"step": step_idx + 1, "sim_time_s": (step_idx + 1) * _AGG_TIME}
            for seg in _ALL_SEGS:
                nl = _LANE_COUNTS.get(seg, 1)
                flow, speed, occ = _read_e1_segment(conn, seg, "exit", nl)
                row[f"{seg}_flow_vph"] = round(flow, 1)
                row[f"{seg}_speed_kph"] = round(speed, 1)
                row[f"{seg}_occ_pct"] = round(occ, 2)
            e1_records.append(row)

    finally:
        try:
            conn.close()
        except Exception:
            pass
        shutil.rmtree(tmpdir, ignore_errors=True)

    # Compute summary
    data = [r for r in e1_records if r["sim_time_s"] > 150]

    sigmas = []
    for r in data:
        v2, v1, v0 = r["seg_2_before_speed_kph"], r["seg_1_before_speed_kph"], r["seg_0_before_speed_kph"]
        if v2 > 0 and v1 > 0 and v0 > 0:
            sigmas.append(float(np.std([v2, v1, v0])))

    ds_flows = [r["seg_1_after_flow_vph"] for r in data if r["seg_1_after_flow_vph"] > 0]
    s0a_speeds = [r["seg_0_after_speed_kph"] for r in data if r["seg_0_after_speed_kph"] > 0]
    s0a_flows = [r["seg_0_after_flow_vph"] for r in data if r["seg_0_after_flow_vph"] > 0]
    merge_speeds = [r["ramp_on_merge_speed_kph"] for r in data if r["ramp_on_merge_speed_kph"] > 0]
    trans_speeds = [r["ramp_on_transition_speed_kph"] for r in data if r["ramp_on_transition_speed_kph"] > 0]

    summary = {
        "demand_vph": demand_vph,
        "mainline_vsl_kph": f"{int(mainline_vsl_kph)}" if mainline_vsl_kph else "NC",
        "ramp_vsl_kph": int(ramp_vsl_kph),

        # E1-based ramp metrics
        "ramp_trans_e1_avg_kph": round(np.mean(trans_speeds), 1) if trans_speeds else 0,
        "ramp_merge_e1_avg_kph": round(np.mean(merge_speeds), 1) if merge_speeds else 0,

        # CAV-only speed on ramp_on_transition (the critical metric)
        "ramp_trans_cav_avg_kph": round(np.mean(ramp_trans_cav_speeds), 1) if ramp_trans_cav_speeds else 0,
        "ramp_trans_hdv_avg_kph": round(np.mean(ramp_trans_hdv_speeds), 1) if ramp_trans_hdv_speeds else 0,
        "ramp_trans_cav_n": len(ramp_trans_cav_speeds),
        "ramp_trans_hdv_n": len(ramp_trans_hdv_speeds),

        # Merge / weaving zone outcome
        "seg0a_avg_speed_kph": round(np.mean(s0a_speeds), 1) if s0a_speeds else 0,
        "seg0a_avg_flow_vph": round(np.mean(s0a_flows), 0) if s0a_flows else 0,
        "ds_avg_flow_vph": round(np.mean(ds_flows), 0) if ds_flows else 0,

        # Upstream corridor
        "sigma_upstream_avg": round(np.mean(sigmas), 2) if sigmas else 0,

        # Acceleration metrics
        "up_avg_abs_accel": round(np.mean(np.abs(up_all_accels)), 4) if up_all_accels else 0,
        "ramp_avg_abs_accel": round(np.mean(np.abs(ramp_all_accels)), 4) if ramp_all_accels else 0,
        "md_avg_abs_accel": round(np.mean(np.abs(md_all_accels)), 4) if md_all_accels else 0,
    }

    return summary


def main():
    ts = datetime.now().strftime("%d-%m-%Y_%H-%M-%S")
    result_dir = _RESULTS_ROOT / f"ramp_vsl_isolation_{ts}"
    result_dir.mkdir(parents=True, exist_ok=True)

    tasks = [
        (d, ml, rp)
        for ml in _MAINLINE_VSL_LEVELS
        for rp in _RAMP_VSL_LEVELS
        for d in _DEMAND_LEVELS
    ]
    n_tasks = len(tasks)
    n_workers = min(n_tasks, os.cpu_count() or 4)

    print("Ramp VSL isolation diagnostic")
    print(f"  {n_tasks} scenarios on {n_workers} workers")
    print(f"  Mainline VSL: {_MAINLINE_VSL_LEVELS}")
    print(f"  Ramp VSL:     {_RAMP_VSL_LEVELS}")
    print(f"  Demands:      {_DEMAND_LEVELS}")
    print(f"  Output: {result_dir}\n")

    t0 = time.time()
    summaries: List[Dict[str, Any]] = []

    with ProcessPoolExecutor(max_workers=n_workers) as pool:
        futures = {pool.submit(_run_scenario, d, ml, rp): (d, ml, rp) for d, ml, rp in tasks}

        for f in as_completed(futures):
            d, ml, rp = futures[f]
            ml_s = f"ML{int(ml)}" if ml else "ML_NC"
            try:
                s = f.result()
                summaries.append(s)
                done = len(summaries)
                print(f"  [{done:>2}/{n_tasks}] {ml_s} RP{int(rp)} @ {d} | "
                      f"CAV_spd={s['ramp_trans_cav_avg_kph']:>5} "
                      f"HDV_spd={s['ramp_trans_hdv_avg_kph']:>5} "
                      f"merge={s['ramp_merge_e1_avg_kph']:>5} "
                      f"s0a={s['seg0a_avg_speed_kph']:>5} "
                      f"s0a_flow={s['seg0a_avg_flow_vph']:>5} "
                      f"ramp|a|={s['ramp_avg_abs_accel']:>6} "
                      f"| {time.time()-t0:.0f}s")
            except Exception as e:
                print(f"  FAILED: {ml_s} RP{int(rp)} @ {d}: {e}")

    # Sort: group by mainline VSL, then demand, then ramp VSL
    ml_order = {"NC": 0, "90": 1}
    summaries.sort(key=lambda s: (ml_order.get(s["mainline_vsl_kph"], 99),
                                   s["demand_vph"], s["ramp_vsl_kph"]))

    # Write CSV
    if summaries:
        csv_path = result_dir / "summary.csv"
        with csv_path.open("w", newline="", encoding="utf-8") as fh:
            writer = csv.DictWriter(fh, fieldnames=summaries[0].keys())
            writer.writeheader()
            writer.writerows(summaries)

    # Print comparison table
    print(f"\n{'='*140}")
    print("RAMP VSL ISOLATION: does ramp VSL change anything?")
    print(f"{'='*140}")
    print(f"{'ML_VSL':>6} {'Dem':>5} {'RP_VSL':>6} | "
          f"{'CAV_spd':>7} {'HDV_spd':>7} {'E1_trans':>8} {'E1_merge':>8} | "
          f"{'s0a_spd':>7} {'s0a_flow':>8} {'ds_flow':>7} | "
          f"{'σ_up':>5} {'up|a|':>6} {'ramp|a|':>7} {'md|a|':>6}")
    print("-" * 140)

    prev_ml = None
    prev_dem = None
    for s in summaries:
        ml = s["mainline_vsl_kph"]
        dem = s["demand_vph"]
        if ml != prev_ml or dem != prev_dem:
            if prev_ml is not None:
                print()
            prev_ml, prev_dem = ml, dem
        print(f"{ml:>6} {dem:>5} {s['ramp_vsl_kph']:>6} | "
              f"{s['ramp_trans_cav_avg_kph']:>7} {s['ramp_trans_hdv_avg_kph']:>7} "
              f"{s['ramp_trans_e1_avg_kph']:>8} {s['ramp_merge_e1_avg_kph']:>8} | "
              f"{s['seg0a_avg_speed_kph']:>7} {s['seg0a_avg_flow_vph']:>8} {s['ds_avg_flow_vph']:>7} | "
              f"{s['sigma_upstream_avg']:>5} {s['up_avg_abs_accel']:>6} "
              f"{s['ramp_avg_abs_accel']:>7} {s['md_avg_abs_accel']:>6}")

    print(f"\n--- Decision criteria ---")
    print("Compare ramp VSL 40 vs 90 within each (mainline_vsl, demand) group:")
    print("  - CAV speed diff ≥ 10 kph: CAVs comply with the ramp VSL")
    print("  - seg_0_after speed diff ≥ 2 kph: merge outcome affected")
    print("  - seg_0_after flow diff ≥ 100 vph: throughput affected")
    print("  - ramp avg|a| diff ≥ 0.05 m/s²: ramp smoothness affected")
    print(f"\nTotal time: {time.time()-t0:.0f}s")
    print(f"Results: {result_dir}")


if __name__ == "__main__":
    main()
