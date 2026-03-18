#!/usr/bin/env python3
"""
Fixed-VSL sweep v2: measures per-vehicle deceleration/acceleration.

Collects at every simulation second (not just every 30s window):
  - Per-vehicle acceleration via traci.vehicle.getAcceleration()
  - Aggregates: number of braking events, braking amplitude, accel events

Grid:
  VSL levels: [no_control, 50, 70, 90, 110] kph
  Demands:    [5000, 6000, 6500, 7000, 7500] vph
  Total:      25 scenarios, run in parallel.

Usage:
    python3 tests/run_fixed_vsl_sweep_v2.py
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

_VSL_LEVELS_KPH: List[Optional[float]] = [None, 50.0, 70.0, 90.0, 110.0]
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

_CONTROLLED_EDGES = {"seg_2_before", "seg_1_before", "seg_0_before"}
_RAMP_EDGES = {"ramp_on_transition"}

# Upstream edges where we measure accel/decel (the corridor we want to harmonize).
_UPSTREAM_EDGES = {"seg_3_before", "seg_2_before", "seg_1_before", "seg_0_before"}
# Merge + downstream (to see if we shift the problem or solve it).
_MERGE_DOWNSTREAM_EDGES = {"seg_0_after", "seg_1_after"}

_MAX_RAMP_VSL_KPH = 90.0

# Thresholds for counting braking/accel events.
_HARD_BRAKE_THRESHOLD = -2.0    # m/s² — hard braking
_BRAKE_THRESHOLD = -0.5         # m/s² — any noticeable braking
_ACCEL_THRESHOLD = 0.5          # m/s² — any noticeable acceleration


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
    rng = np.random.default_rng(42)
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

def _run_scenario(demand_vph: int, vsl_kph: Optional[float]) -> Dict[str, Any]:
    """Run one episode. Returns summary dict with accel/decel metrics."""
    import traci

    label = f"vsl{int(vsl_kph) if vsl_kph else 'NC'}_{demand_vph}"
    tmpdir = Path(tempfile.mkdtemp(prefix=f"fvsl2_{label}_"))
    rou_path = tmpdir / "flows.rou.xml"
    cfg_path = tmpdir / "sim.sumocfg"

    _generate_route_file(rou_path, demand_vph, _EPISODE_S, _CAV_PCT)
    _generate_sumocfg(cfg_path, rou_path)

    mainline_vsl_ms = (vsl_kph / 3.6) if vsl_kph is not None else None
    ramp_vsl_ms = (min(vsl_kph, _MAX_RAMP_VSL_KPH) / 3.6) if vsl_kph is not None else None

    cmd = ["sumo", "-c", str(cfg_path), "--start", "--no-step-log", "--no-warnings"]
    traci.start(cmd, label=label)
    conn = traci.getConnection(label)

    # -----------------------------------------------------------------------
    # Accumulators for vehicle-level metrics (collected every sim second)
    # -----------------------------------------------------------------------

    # Upstream corridor
    up_all_accels: List[float] = []           # every accel reading (m/s²)
    up_brake_count = 0                        # count of a < BRAKE_THRESHOLD
    up_hard_brake_count = 0                   # count of a < HARD_BRAKE_THRESHOLD
    up_accel_count = 0                        # count of a > ACCEL_THRESHOLD
    up_brake_amplitudes: List[float] = []     # |a| for braking events
    up_accel_amplitudes: List[float] = []     # |a| for accel events
    up_veh_seconds = 0                        # total vehicle-seconds in upstream

    # Merge + downstream
    md_all_accels: List[float] = []
    md_brake_count = 0
    md_hard_brake_count = 0
    md_veh_seconds = 0

    # E1 per-window records (for speed/flow/sigma)
    e1_records: List[Dict] = []
    max_steps = _EPISODE_S // _AGG_TIME

    # TTS accumulator
    tts_veh_seconds = 0

    try:
        for step_idx in range(max_steps):
            for sub_step in range(_AGG_TIME):
                # Apply VSL control
                if mainline_vsl_ms is not None:
                    for veh_id in conn.vehicle.getIDList():
                        if conn.vehicle.getTypeID(veh_id) != "CAV":
                            continue
                        edge = conn.vehicle.getRoadID(veh_id)
                        if edge in _CONTROLLED_EDGES:
                            conn.vehicle.slowDown(veh_id, mainline_vsl_ms, float(_AGG_TIME))
                        elif edge in _RAMP_EDGES:
                            conn.vehicle.slowDown(veh_id, ramp_vsl_ms, float(_AGG_TIME))

                conn.simulationStep()

                # Skip warmup (first 150s)
                sim_time = step_idx * _AGG_TIME + sub_step + 1
                if sim_time <= 150:
                    continue

                # Collect per-vehicle acceleration data
                for veh_id in conn.vehicle.getIDList():
                    edge = conn.vehicle.getRoadID(veh_id)
                    # Skip internal edges (junctions)
                    if edge.startswith(":"):
                        continue

                    try:
                        accel = float(conn.vehicle.getAcceleration(veh_id))
                    except Exception:
                        continue

                    # TTS: every vehicle in network contributes 1 vehicle-second
                    tts_veh_seconds += 1

                    if edge in _UPSTREAM_EDGES:
                        up_all_accels.append(accel)
                        up_veh_seconds += 1

                        if accel < _BRAKE_THRESHOLD:
                            up_brake_count += 1
                            up_brake_amplitudes.append(abs(accel))
                        if accel < _HARD_BRAKE_THRESHOLD:
                            up_hard_brake_count += 1
                        if accel > _ACCEL_THRESHOLD:
                            up_accel_count += 1
                            up_accel_amplitudes.append(accel)

                    elif edge in _MERGE_DOWNSTREAM_EDGES:
                        md_all_accels.append(accel)
                        md_veh_seconds += 1
                        if accel < _BRAKE_THRESHOLD:
                            md_brake_count += 1
                        if accel < _HARD_BRAKE_THRESHOLD:
                            md_hard_brake_count += 1

            # E1 readings at end of aggregation window
            sim_time_w = (step_idx + 1) * _AGG_TIME
            row = {"step": step_idx + 1, "sim_time_s": sim_time_w}
            for seg in _ALL_SEGS:
                nl = _LANE_COUNTS.get(seg, 1)
                flow, speed, occ = _read_e1_segment(conn, seg, "exit", nl)
                row[f"{seg}_flow_vph"] = round(flow, 1)
                row[f"{seg}_speed_kph"] = round(speed, 1)
                row[f"{seg}_occ_pct"] = round(occ, 2)
            row["n_vehicles"] = int(conn.vehicle.getIDCount())
            e1_records.append(row)

    finally:
        try:
            conn.close()
        except Exception:
            pass
        shutil.rmtree(tmpdir, ignore_errors=True)

    # -----------------------------------------------------------------------
    # Compute summary
    # -----------------------------------------------------------------------
    # E1-based metrics (skip warmup records)
    data = [r for r in e1_records if r["sim_time_s"] > 150]
    sigmas = []
    for r in data:
        v2 = r["seg_2_before_speed_kph"]
        v1 = r["seg_1_before_speed_kph"]
        v0 = r["seg_0_before_speed_kph"]
        if v2 > 0 and v1 > 0 and v0 > 0:
            sigmas.append(float(np.std([v2, v1, v0])))

    ds_flows = [r["seg_1_after_flow_vph"] for r in data if r["seg_1_after_flow_vph"] > 0]

    upstream_speeds = []
    for r in data:
        v2 = r["seg_2_before_speed_kph"]
        v1 = r["seg_1_before_speed_kph"]
        v0 = r["seg_0_before_speed_kph"]
        if v2 > 0 and v1 > 0 and v0 > 0:
            upstream_speeds.append(np.mean([v2, v1, v0]))

    n_breakdown = sum(1 for r in data if r["seg_0_before_speed_kph"] < 45)

    # Accel/decel rates (per 1000 vehicle-seconds to normalize)
    up_vs = max(up_veh_seconds, 1)

    summary = {
        "demand_vph": demand_vph,
        "vsl_kph": f"{int(vsl_kph)}kph" if vsl_kph is not None else "no_control",

        # Speed / flow
        "avg_sigma_upstream": round(np.mean(sigmas), 2) if sigmas else 0,
        "avg_upstream_speed_kph": round(np.mean(upstream_speeds), 1) if upstream_speeds else 0,
        "avg_ds_flow_vph": round(np.mean(ds_flows), 0) if ds_flows else 0,
        "n_breakdown_steps": n_breakdown,

        # TTS (vehicle-seconds, post-warmup)
        "tts_veh_seconds": tts_veh_seconds,
        "tts_veh_hours": round(tts_veh_seconds / 3600, 1),

        # Upstream decel/accel — absolute counts
        "up_veh_seconds": up_veh_seconds,
        "up_brake_events": up_brake_count,
        "up_hard_brake_events": up_hard_brake_count,
        "up_accel_events": up_accel_count,

        # Upstream decel/accel — rates per 1000 veh-seconds
        "up_brake_rate_per_1kvs": round(up_brake_count / up_vs * 1000, 1),
        "up_hard_brake_rate_per_1kvs": round(up_hard_brake_count / up_vs * 1000, 1),
        "up_accel_rate_per_1kvs": round(up_accel_count / up_vs * 1000, 1),

        # Upstream decel/accel — amplitudes
        "up_avg_brake_amplitude_ms2": round(np.mean(up_brake_amplitudes), 3) if up_brake_amplitudes else 0,
        "up_max_brake_amplitude_ms2": round(max(up_brake_amplitudes), 3) if up_brake_amplitudes else 0,
        "up_p95_brake_amplitude_ms2": round(np.percentile(up_brake_amplitudes, 95), 3) if up_brake_amplitudes else 0,
        "up_avg_accel_amplitude_ms2": round(np.mean(up_accel_amplitudes), 3) if up_accel_amplitudes else 0,

        # Upstream — overall jerk indicator (mean |accel| — lower is smoother)
        "up_mean_abs_accel_ms2": round(np.mean(np.abs(up_all_accels)), 4) if up_all_accels else 0,

        # Merge+downstream decel (to check if we shift the problem)
        "md_veh_seconds": md_veh_seconds,
        "md_brake_rate_per_1kvs": round(md_brake_count / max(md_veh_seconds, 1) * 1000, 1),
        "md_hard_brake_rate_per_1kvs": round(md_hard_brake_count / max(md_veh_seconds, 1) * 1000, 1),

        "max_veh_in_network": max(r["n_vehicles"] for r in e1_records) if e1_records else 0,
    }

    return summary


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    ts = datetime.now().strftime("%d-%m-%Y_%H-%M-%S")
    result_dir = _RESULTS_ROOT / f"fixed_vsl_sweep_v2_{ts}"
    result_dir.mkdir(parents=True, exist_ok=True)

    tasks = [(d, v) for v in _VSL_LEVELS_KPH for d in _DEMAND_LEVELS]
    n_tasks = len(tasks)
    n_workers = min(n_tasks, os.cpu_count() or 4)

    print(f"Fixed-VSL sweep v2 (with accel/decel metrics)")
    print(f"  {n_tasks} scenarios on {n_workers} workers")
    print(f"  VSL levels: {_VSL_LEVELS_KPH}")
    print(f"  Demands:    {_DEMAND_LEVELS}")
    print(f"  Brake threshold: {_BRAKE_THRESHOLD} m/s², hard: {_HARD_BRAKE_THRESHOLD} m/s²")
    print(f"  Output: {result_dir}\n")

    t0 = time.time()
    summaries: List[Dict[str, Any]] = []

    with ProcessPoolExecutor(max_workers=n_workers) as pool:
        futures = {pool.submit(_run_scenario, d, v): (d, v) for d, v in tasks}

        for f in as_completed(futures):
            d, v = futures[f]
            vl = f"{int(v)}kph" if v is not None else "no_control"
            try:
                s = f.result()
                summaries.append(s)
                done = len(summaries)
                print(f"  [{done:>2}/{n_tasks}] {vl:>12} @ {d} vph | "
                      f"σ={s['avg_sigma_upstream']:>5} "
                      f"spd={s['avg_upstream_speed_kph']:>5} "
                      f"flow={s['avg_ds_flow_vph']:>5} "
                      f"TTS={s['tts_veh_hours']:>6}vh | "
                      f"brake/1kvs={s['up_brake_rate_per_1kvs']:>5} "
                      f"hard/1kvs={s['up_hard_brake_rate_per_1kvs']:>5} "
                      f"avg|a|={s['up_mean_abs_accel_ms2']:>6} "
                      f"| {time.time()-t0:.0f}s")
            except Exception as e:
                print(f"  FAILED: {vl} @ {d}: {e}")

    # Sort and write
    vsl_order = {"no_control": 0, "50kph": 1, "70kph": 2, "90kph": 3, "110kph": 4}
    summaries.sort(key=lambda s: (vsl_order.get(s["vsl_kph"], 99), s["demand_vph"]))

    if summaries:
        csv_path = result_dir / "summary.csv"
        with csv_path.open("w", newline="", encoding="utf-8") as fh:
            writer = csv.DictWriter(fh, fieldnames=summaries[0].keys())
            writer.writeheader()
            writer.writerows(summaries)

    # Print results table
    print(f"\n{'='*160}")
    print("UPSTREAM CORRIDOR: deceleration-acceleration analysis")
    print(f"{'='*160}")
    print(f"{'VSL':>12} {'Dem':>5} | {'σ_up':>5} {'spd':>5} {'flow':>5} {'TTS':>6} | "
          f"{'brk/1k':>6} {'hard/1k':>7} {'acc/1k':>6} | "
          f"{'avg|brk|':>8} {'p95|brk|':>8} {'avg|acc|':>8} {'avg|a|':>6} | "
          f"{'MD brk/1k':>9} {'MD hrd/1k':>9} | {'BD':>3} {'MaxV':>5}")
    print("-" * 160)

    for s in summaries:
        print(f"{s['vsl_kph']:>12} {s['demand_vph']:>5} | "
              f"{s['avg_sigma_upstream']:>5} {s['avg_upstream_speed_kph']:>5} {s['avg_ds_flow_vph']:>5} {s['tts_veh_hours']:>6} | "
              f"{s['up_brake_rate_per_1kvs']:>6} {s['up_hard_brake_rate_per_1kvs']:>7} {s['up_accel_rate_per_1kvs']:>6} | "
              f"{s['up_avg_brake_amplitude_ms2']:>8} {s['up_p95_brake_amplitude_ms2']:>8} {s['up_avg_accel_amplitude_ms2']:>8} {s['up_mean_abs_accel_ms2']:>6} | "
              f"{s['md_brake_rate_per_1kvs']:>9} {s['md_hard_brake_rate_per_1kvs']:>9} | "
              f"{s['n_breakdown_steps']:>3} {s['max_veh_in_network']:>5}")

    print(f"\nTotal time: {time.time()-t0:.0f}s")
    print(f"Results: {result_dir}")


if __name__ == "__main__":
    main()
