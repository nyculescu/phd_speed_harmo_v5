#!/usr/bin/env python3
"""
Fixed-VSL sweep: constant speed limits × demand levels, run in parallel.

Tests whether a constant VSL alone can reduce upstream speed variance
compared to no-control.  This answers: "is the problem solvable at all?"

Grid:
  VSL levels: [no_control, 50, 70, 90, 110] kph
  Demands:    [5000, 6000, 6500, 7000, 7500] vph
  Total:      5 × 5 = 25 scenarios, run in parallel via multiprocessing.

Each CAV on upstream mainline (seg_0/1/2_before) receives
traci.vehicle.slowDown(veh_id, vsl_ms, 30.0) every simulation second.
Ramp CAVs receive min(vsl, 90 kph) on ramp_on_transition.

Usage:
    python3 tests/run_fixed_vsl_sweep.py
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

# ---------------------------------------------------------------------------
# SUMO / traci bootstrap (per-process; traci imported inside workers)
# ---------------------------------------------------------------------------
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

# ---------------------------------------------------------------------------
# Sweep grid
# ---------------------------------------------------------------------------
_VSL_LEVELS_KPH: List[Optional[float]] = [None, 50.0, 70.0, 90.0, 110.0]
# None = no control
_DEMAND_LEVELS: List[int] = [5000, 6000, 6500, 7000, 7500]

_MAINLINE_THROUGH_FRAC = 0.75
_RAMP_ON_FRAC = 0.15
_MAINLINE_TO_OFF_FRAC = 0.10

_MAINLINE_SEGS = [
    "seg_3_before", "seg_2_before", "seg_1_before", "seg_0_before",
    "seg_0_after", "seg_1_after",
]
_RAMP_SEGS = [
    "ramp_on_approach", "ramp_on_transition", "ramp_on_merge",
    "ramp_off_diverge", "ramp_off_transition", "ramp_off_departure",
]
_ALL_SEGS = _MAINLINE_SEGS + _RAMP_SEGS

_LANE_COUNTS: Dict[str, int] = {
    "seg_3_before": 3, "seg_2_before": 3, "seg_1_before": 3, "seg_0_before": 3,
    "seg_0_after": 4, "seg_1_after": 3,
    "ramp_on_approach": 1, "ramp_on_transition": 1, "ramp_on_merge": 1,
    "ramp_off_diverge": 1, "ramp_off_transition": 1, "ramp_off_departure": 1,
}

# Upstream segments where CAVs receive the VSL slowDown command.
_CONTROLLED_EDGES = {"seg_2_before", "seg_1_before", "seg_0_before"}
_RAMP_EDGES = {"ramp_on_transition"}

# Maximum ramp VSL (geometry limits ramp merge to ~25 kph anyway).
_MAX_RAMP_VSL_KPH = 90.0


# ---------------------------------------------------------------------------
# Route file generation (identical to baseline tests)
# ---------------------------------------------------------------------------

def _generate_route_file(
    output_path: Path, demand_vph: int, episode_s: int, cav_pct: float,
) -> None:
    routes = ET.Element("routes")
    ET.SubElement(routes, "vType",
                  id="HDV", carFollowModel="Krauss",
                  vClass="passenger", color="1,1,0",
                  length="4.50", minGap="2.50", accel="2.60",
                  decel="4.50", sigma="0.50", maxSpeed="36.11",
                  tau="1.40", speedFactor="1.00", speedDev="0.10")
    ET.SubElement(routes, "vType",
                  id="CAV", carFollowModel="Krauss",
                  vClass="passenger", color="0,1,0",
                  length="4.50", minGap="1.25", accel="2.86",
                  decel="4.73", sigma="0.00", maxSpeed="36.11",
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
    rng = np.random.default_rng(42)
    vehicles: List[Tuple[float, str]] = []

    def _emit(count: int, route_id: str, t_offset: float, t_span: float):
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

    for vid, (dep, rid) in enumerate(vehicles):
        is_cav = rng.random() * 100.0 < cav_pct
        ET.SubElement(routes, "vehicle",
                      id=f"veh_{vid}", type="CAV" if is_cav else "HDV",
                      route=rid, depart=f"{dep:.2f}",
                      departPos="last", departLane="best",
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


# ---------------------------------------------------------------------------
# E1 reader
# ---------------------------------------------------------------------------

def _read_e1_segment(traci_mod, seg: str, position: str, n_lanes: int):
    counts, speeds, occs = [], [], []
    for lane_idx in range(n_lanes):
        det_id = f"flow_loop_{seg}_{lane_idx}_{position}"
        try:
            cnt = float(traci_mod.inductionloop.getLastIntervalVehicleNumber(det_id))
            spd = float(traci_mod.inductionloop.getLastIntervalMeanSpeed(det_id))
            occ = float(traci_mod.inductionloop.getLastIntervalOccupancy(det_id))
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
# Single scenario worker (runs in a subprocess)
# ---------------------------------------------------------------------------

def _run_scenario(
    demand_vph: int,
    vsl_kph: Optional[float],
) -> List[Dict[str, Any]]:
    """Run one episode. Returns list of per-step records."""
    import traci

    label = f"vsl{int(vsl_kph) if vsl_kph else 'NC'}_{demand_vph}"

    tmpdir = Path(tempfile.mkdtemp(prefix=f"fvsl_{label}_"))
    rou_path = tmpdir / "flows.rou.xml"
    cfg_path = tmpdir / "sim.sumocfg"

    _generate_route_file(rou_path, demand_vph, _EPISODE_S, _CAV_PCT)
    _generate_sumocfg(cfg_path, rou_path)

    mainline_vsl_ms = (vsl_kph / 3.6) if vsl_kph is not None else None
    ramp_vsl_ms = (min(vsl_kph, _MAX_RAMP_VSL_KPH) / 3.6) if vsl_kph is not None else None

    cmd = ["sumo", "-c", str(cfg_path), "--start", "--no-step-log", "--no-warnings"]
    traci.start(cmd, label=label)
    conn = traci.getConnection(label)

    records: List[Dict[str, Any]] = []
    max_steps = _EPISODE_S // _AGG_TIME

    try:
        for step_idx in range(max_steps):
            # Advance one aggregation window, applying CAV control each second
            for _ in range(_AGG_TIME):
                if mainline_vsl_ms is not None:
                    for veh_id in conn.vehicle.getIDList():
                        vtype = conn.vehicle.getTypeID(veh_id)
                        if vtype != "CAV":
                            continue
                        edge = conn.vehicle.getRoadID(veh_id)
                        if edge in _CONTROLLED_EDGES:
                            conn.vehicle.slowDown(veh_id, mainline_vsl_ms, float(_AGG_TIME))
                        elif edge in _RAMP_EDGES:
                            conn.vehicle.slowDown(veh_id, ramp_vsl_ms, float(_AGG_TIME))
                conn.simulationStep()

            sim_time = (step_idx + 1) * _AGG_TIME
            n_veh = int(conn.vehicle.getIDCount())

            row: Dict[str, Any] = {
                "step": step_idx + 1,
                "sim_time_s": sim_time,
                "demand_vph": demand_vph,
                "vsl_kph": vsl_kph if vsl_kph is not None else "no_control",
                "n_vehicles_in_network": n_veh,
            }

            for seg in _ALL_SEGS:
                nl = _LANE_COUNTS.get(seg, 1)
                flow, speed, occ = _read_e1_segment(conn, seg, "exit", nl)
                row[f"{seg}_flow_vph"] = round(flow, 1)
                row[f"{seg}_speed_kph"] = round(speed, 1)
                row[f"{seg}_occ_pct"] = round(occ, 2)

            records.append(row)
    finally:
        try:
            conn.close()
        except Exception:
            pass
        shutil.rmtree(tmpdir, ignore_errors=True)

    return records


# ---------------------------------------------------------------------------
# Summary statistics from a record list
# ---------------------------------------------------------------------------

def _summarize(records: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Compute key metrics from per-step records."""
    # Skip warmup (first 5 steps = 150s)
    data = [r for r in records if r["sim_time_s"] > 150]
    if not data:
        return {}

    def _speeds(seg):
        return [r[f"{seg}_speed_kph"] for r in data if r[f"{seg}_speed_kph"] > 0]

    s2 = _speeds("seg_2_before")
    s1 = _speeds("seg_1_before")
    s0 = _speeds("seg_0_before")
    s0a = _speeds("seg_0_after")
    ds_flow = [r["seg_1_after_flow_vph"] for r in data if r["seg_1_after_flow_vph"] > 0]

    # Per-step upstream variance
    sigmas = []
    max_decel_proxy = []
    for i, r in enumerate(data):
        v2 = r["seg_2_before_speed_kph"]
        v1 = r["seg_1_before_speed_kph"]
        v0 = r["seg_0_before_speed_kph"]
        if v2 > 0 and v1 > 0 and v0 > 0:
            sigmas.append(float(np.std([v2, v1, v0])))
        if i > 0:
            prev = data[i - 1]
            for seg in ["seg_2_before", "seg_1_before", "seg_0_before"]:
                curr_s = r[f"{seg}_speed_kph"]
                prev_s = prev[f"{seg}_speed_kph"]
                if curr_s > 0 and prev_s > 0:
                    max_decel_proxy.append(abs(curr_s - prev_s))

    n_breakdown = sum(1 for r in data if r["seg_0_before_speed_kph"] < 45)

    return {
        "avg_sigma_upstream": round(np.mean(sigmas), 2) if sigmas else 0,
        "max_sigma_upstream": round(max(sigmas), 2) if sigmas else 0,
        "avg_s2b": round(np.mean(s2), 1) if s2 else 0,
        "avg_s1b": round(np.mean(s1), 1) if s1 else 0,
        "avg_s0b": round(np.mean(s0), 1) if s0 else 0,
        "min_s0b": round(min(s0), 1) if s0 else 0,
        "avg_s0a": round(np.mean(s0a), 1) if s0a else 0,
        "avg_ds_flow": round(np.mean(ds_flow), 0) if ds_flow else 0,
        "max_ds_flow": round(max(ds_flow), 0) if ds_flow else 0,
        "n_breakdown_steps": n_breakdown,
        "avg_upstream_speed": round(np.mean(
            [np.mean([r["seg_2_before_speed_kph"], r["seg_1_before_speed_kph"], r["seg_0_before_speed_kph"]])
             for r in data
             if r["seg_2_before_speed_kph"] > 0 and r["seg_1_before_speed_kph"] > 0 and r["seg_0_before_speed_kph"] > 0]
        ), 1) if s0 else 0,
        "max_decel_proxy": round(max(max_decel_proxy), 1) if max_decel_proxy else 0,
        "avg_decel_proxy": round(np.mean(max_decel_proxy), 1) if max_decel_proxy else 0,
        "max_veh": max(r["n_vehicles_in_network"] for r in data),
        "end_veh": data[-1]["n_vehicles_in_network"],
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    ts = datetime.now().strftime("%d-%m-%Y_%H-%M-%S")
    result_dir = _RESULTS_ROOT / f"fixed_vsl_sweep_{ts}"
    result_dir.mkdir(parents=True, exist_ok=True)

    # Build task list
    tasks = []
    for vsl in _VSL_LEVELS_KPH:
        for demand in _DEMAND_LEVELS:
            tasks.append((demand, vsl))

    n_tasks = len(tasks)
    n_workers = min(n_tasks, os.cpu_count() or 4)

    print(f"Fixed-VSL sweep: {n_tasks} scenarios on {n_workers} workers")
    print(f"  VSL levels: {_VSL_LEVELS_KPH}")
    print(f"  Demands:    {_DEMAND_LEVELS}")
    print(f"  Output:     {result_dir}")
    print()

    t0 = time.time()
    all_summaries: List[Dict[str, Any]] = []

    with ProcessPoolExecutor(max_workers=n_workers) as pool:
        futures = {}
        for demand, vsl in tasks:
            f = pool.submit(_run_scenario, demand, vsl)
            futures[f] = (demand, vsl)

        for f in as_completed(futures):
            demand, vsl = futures[f]
            vsl_label = f"{int(vsl)}kph" if vsl is not None else "no_control"

            try:
                records = f.result()
            except Exception as e:
                print(f"  FAILED: demand={demand}, vsl={vsl_label}: {e}")
                continue

            # Write per-scenario CSV
            csv_path = result_dir / f"{vsl_label}_{demand}vph.csv"
            if records:
                with csv_path.open("w", newline="", encoding="utf-8") as fh:
                    writer = csv.DictWriter(fh, fieldnames=records[0].keys())
                    writer.writeheader()
                    writer.writerows(records)

            # Summary
            summary = _summarize(records)
            summary["demand_vph"] = demand
            summary["vsl_kph"] = vsl_label
            all_summaries.append(summary)

            elapsed = time.time() - t0
            done = len(all_summaries)
            print(f"  [{done:>2}/{n_tasks}] {vsl_label:>12} @ {demand} vph  |  "
                  f"σ_up={summary.get('avg_sigma_upstream', '?'):>6}  "
                  f"avg_up={summary.get('avg_upstream_speed', '?'):>6}  "
                  f"ds_flow={summary.get('avg_ds_flow', '?'):>6}  "
                  f"BD_steps={summary.get('n_breakdown_steps', '?'):>3}  "
                  f"({elapsed:.0f}s)")

    # Write summary CSV
    if all_summaries:
        # Sort by VSL then demand for readability
        vsl_order = {"no_control": 0, "50kph": 1, "70kph": 2, "90kph": 3, "110kph": 4}
        all_summaries.sort(key=lambda s: (vsl_order.get(s["vsl_kph"], 99), s["demand_vph"]))

        summary_csv = result_dir / "summary.csv"
        with summary_csv.open("w", newline="", encoding="utf-8") as fh:
            writer = csv.DictWriter(fh, fieldnames=all_summaries[0].keys())
            writer.writeheader()
            writer.writerows(all_summaries)

    # Print summary table
    print(f"\n{'='*120}")
    print(f"SUMMARY TABLE")
    print(f"{'='*120}")
    print(f"{'VSL':>12} {'Demand':>7} | {'σ_up':>6} {'max_σ':>6} | {'s2b':>6} {'s1b':>6} {'s0b':>6} {'avg_up':>7} | {'s0a':>6} {'DS flow':>8} | {'BD':>3} {'MaxV':>5}")
    print(f"{'-'*120}")

    for s in all_summaries:
        print(f"{s['vsl_kph']:>12} {s['demand_vph']:>7} | "
              f"{s['avg_sigma_upstream']:>6} {s['max_sigma_upstream']:>6} | "
              f"{s['avg_s2b']:>6} {s['avg_s1b']:>6} {s['avg_s0b']:>6} {s['avg_upstream_speed']:>7} | "
              f"{s['avg_s0a']:>6} {s['avg_ds_flow']:>8} | "
              f"{s['n_breakdown_steps']:>3} {s['max_veh']:>5}")

    elapsed = time.time() - t0
    print(f"\nTotal time: {elapsed:.0f}s")
    print(f"Results: {result_dir}")


if __name__ == "__main__":
    main()
