#!/usr/bin/env python3
"""
Comprehensive feasibility sweep for the ramps_v2 topology.

Maps the full 2D action space (mainline VSL × ramp VSL) across all
operationally relevant demand levels.  This produces the dataset needed
to answer:
  1. At which demands does congestion form? (demand boundary)
  2. Which (mainline, ramp) combinations reduce avg|a| without
     destroying throughput? (Pareto front)
  3. Does independent ramp VSL add value over mainline-only control?
  4. What is the reward landscape shape for r44_reward_v2?

Grid (non-uniform — dense at the transitional edges):

  Demands (20 levels):
    Coarse (1000 vph step):  3000, 4000, 5000 vph          → 3 free-flow anchors
    Medium (500 vph step):   5500, 8000, 8500, 9000 vph    → 4 boundary/congested
    Fine (250 vph step):     5750, 6000, 6250, 6500, 6750,
                             7000, 7250, 7500, 7750 vph    → 9 transitional core
    Extreme:                 4500, 10000 vph                → 2 free-flow/saturation
    Total:                   18 demand levels

  Mainline VSL (9 levels):
    Coarse:   60, 70, 110, 120 kph                         → 4 extremes
    Fine:     80, 85, 90, 95, 100 kph                      → 5 around the sweet spot
    Total:    9 levels + NC

  Ramp VSL (6 levels):
    40, 50, 60, 70, 80, 90 kph                             → 6 levels

  no_control:    18 scenarios
  controlled:    18 × 9 × 6 = 972 scenarios
  Total:         990 scenarios

  With 140 workers: ~8 batches, estimated 30-60 min total.

Metrics collected per scenario (same as run_fixed_vsl_sweep_v2.py):
  - E1 speed/flow/occupancy per segment per 30s window
  - Per-vehicle acceleration via traci.vehicle.getAcceleration()
  - Braking events, hard braking, acceleration events
  - TTS, downstream flow, upstream speed variance
  - Max adjacent speed gradient (for r44_reward_v2 spatial term)

Usage:
    python3 tests/run_feasibility_sweep.py
    python3 tests/run_feasibility_sweep.py --workers 140
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
_NET_FILE = _SUMO_DIR / "ramps_v2.net.xml"
_DET_FILE = _SUMO_DIR / "detectors_ramps_v2.add.xml"
_RESULTS_ROOT = Path(__file__).resolve().parent / "results"

# Episode parameters
_EPISODE_S = 3600
_AGG_TIME = 30
_CAV_PCT = 50.0
_RAMP_DELAY_S = 100.0
_WARMUP_S = 150

# Sweep grid — non-uniform, dense at the transitional edges.
#
# Demand levels:
#   3000–5000: free-flow, coarse 1000 vph steps (nothing interesting)
#   5500–7750: transitional regime — congestion onset, 250 vph steps
#   8000–9000: established congestion, 500 vph steps
#   4500:      confirm free-flow extends past 4000
#   10000:     saturation anchor (what happens past capacity?)
_DEMAND_LEVELS: List[int] = sorted([
    3000, 4000, 4500, 5000,                            # free-flow
    5500, 5750, 6000, 6250, 6500, 6750, 7000, 7250,    # transitional (250 step)
    7500, 7750,                                         # late transitional
    8000, 8500, 9000,                                   # congested
    10000,                                              # saturation
])

# Mainline VSL: fine steps around the 85-95 kph sweet spot.
_MAINLINE_VSL_KPH: List[float] = [60.0, 70.0, 80.0, 85.0, 90.0, 95.0, 100.0, 110.0, 120.0]

# Ramp VSL: full range at 10 kph steps.
_RAMP_VSL_KPH: List[float] = [40.0, 50.0, 60.0, 70.0, 80.0, 90.0]

# Demand routing fractions
_MAINLINE_THROUGH_FRAC = 0.75
_RAMP_ON_FRAC = 0.25

# Segments
_MAINLINE_SEGS = [
    "seg_3_before", "seg_2_before", "seg_1_before", "seg_0_before",
    "seg_0_after", "seg_1_after",
]
_RAMP_SEGS = [
    "ramp_on_approach", "ramp_on_transition", "ramp_on_merge",
]
_ALL_SEGS = _MAINLINE_SEGS + _RAMP_SEGS

_LANE_COUNTS: Dict[str, int] = {
    "seg_3_before": 3, "seg_2_before": 3, "seg_1_before": 3, "seg_0_before": 3,
    "seg_0_after": 3, "seg_1_after": 3,
    "ramp_on_approach": 1, "ramp_on_transition": 1, "ramp_on_merge": 1,
}

_CONTROLLED_EDGES = {"seg_2_before", "seg_1_before", "seg_0_before"}
_RAMP_EDGES = {"ramp_on_transition"}
_UPSTREAM_EDGES = {"seg_3_before", "seg_2_before", "seg_1_before", "seg_0_before"}
_MERGE_DOWNSTREAM_EDGES = {"seg_0_after", "seg_1_after"}

# Thresholds
_HARD_BRAKE_THRESHOLD = -2.0
_BRAKE_THRESHOLD = -0.5
_ACCEL_THRESHOLD = 0.5


# ---------------------------------------------------------------------------
# Route / config generation (same as v2)
# ---------------------------------------------------------------------------

def _generate_route_file(
    output_path: Path, demand_vph: int, episode_s: int, cav_pct: float,
) -> None:
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

    total_veh = int(demand_vph * episode_s / 3600)
    n_mainline = int(total_veh * _MAINLINE_THROUGH_FRAC)
    n_ramp = total_veh - n_mainline
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
    """Read aggregated (cross-lane) E1 data for a segment."""
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


def _read_e1_per_lane(conn, seg: str, position: str, n_lanes: int):
    """Read per-lane E1 data. Returns dict of lane_idx -> (flow_vph, speed_kph, occ_pct)."""
    result = {}
    for lane_idx in range(n_lanes):
        det_id = f"flow_loop_{seg}_{lane_idx}_{position}"
        try:
            cnt = float(conn.inductionloop.getLastIntervalVehicleNumber(det_id))
            spd = float(conn.inductionloop.getLastIntervalMeanSpeed(det_id))
            occ = float(conn.inductionloop.getLastIntervalOccupancy(det_id))
            result[lane_idx] = (cnt * 3600.0 / _AGG_TIME, max(0.0, spd) * 3.6, occ)
        except Exception:
            result[lane_idx] = (0.0, 0.0, 0.0)
    return result


# Segments where we collect per-lane detail (merge zone + immediate upstream)
_LANE_DETAIL_SEGS = ["seg_0_before", "seg_0_after", "seg_1_after"]

# E3 detectors to query (travel time, vehicle count, halting count)
_E3_DETECTORS = [
    "e3_seg_0_before",       # immediate upstream of merge
    "e3_seg_0_after",        # merge zone (500m) — travel time = merge delay
    "e3_seg_1_after",        # downstream — clearance
    "e3_ramp_on_approach",   # ramp approach
    "e3_ramp_on_transition", # ramp speed control zone
    "e3_ramp_on_merge",      # ramp merge — halting = gap-wait
    "e3_corridor",           # full corridor travel time
]


# ---------------------------------------------------------------------------
# Single scenario worker
# ---------------------------------------------------------------------------

def _run_scenario(
    demand_vph: int,
    mainline_vsl_kph: Optional[float],
    ramp_vsl_kph: Optional[float],
) -> Dict[str, Any]:
    """Run one 1-hour episode.  Returns summary dict."""
    import traci

    ml_tag = f"M{int(mainline_vsl_kph)}" if mainline_vsl_kph is not None else "NC"
    rp_tag = f"R{int(ramp_vsl_kph)}" if ramp_vsl_kph is not None else "NC"
    label = f"{ml_tag}_{rp_tag}_{demand_vph}_{os.getpid()}"
    tmpdir = Path(tempfile.mkdtemp(prefix=f"fsweep_{label}_"))
    rou_path = tmpdir / "flows.rou.xml"
    cfg_path = tmpdir / "sim.sumocfg"

    _generate_route_file(rou_path, demand_vph, _EPISODE_S, _CAV_PCT)
    _generate_sumocfg(cfg_path, rou_path)

    mainline_vsl_ms = (mainline_vsl_kph / 3.6) if mainline_vsl_kph is not None else None
    ramp_vsl_ms = (ramp_vsl_kph / 3.6) if ramp_vsl_kph is not None else None

    # Let traci pick its own free port (same pattern as run_fixed_vsl_sweep_v2).
    # The label includes PID to guarantee uniqueness across workers.
    cmd = ["sumo", "-c", str(cfg_path), "--start", "--no-step-log", "--no-warnings"]
    traci.start(cmd, label=label)
    conn = traci.getConnection(label)

    # Accumulators
    up_all_accels: List[float] = []
    up_brake_count = 0
    up_hard_brake_count = 0
    up_accel_count = 0
    up_brake_amplitudes: List[float] = []
    up_accel_amplitudes: List[float] = []
    up_veh_seconds = 0

    md_all_accels: List[float] = []
    md_brake_count = 0
    md_hard_brake_count = 0
    md_veh_seconds = 0

    e1_records: List[Dict] = []
    max_steps = _EPISODE_S // _AGG_TIME
    tts_veh_seconds = 0

    try:
        for step_idx in range(max_steps):
            for sub_step in range(_AGG_TIME):
                # Apply VSL
                if mainline_vsl_ms is not None:
                    for veh_id in conn.vehicle.getIDList():
                        if conn.vehicle.getTypeID(veh_id) != "CAV":
                            continue
                        edge = conn.vehicle.getRoadID(veh_id)
                        if edge in _CONTROLLED_EDGES:
                            conn.vehicle.slowDown(veh_id, mainline_vsl_ms, float(_AGG_TIME))
                        elif edge in _RAMP_EDGES and ramp_vsl_ms is not None:
                            conn.vehicle.slowDown(veh_id, ramp_vsl_ms, float(_AGG_TIME))

                conn.simulationStep()

                sim_time = step_idx * _AGG_TIME + sub_step + 1
                if sim_time <= _WARMUP_S:
                    continue

                for veh_id in conn.vehicle.getIDList():
                    edge = conn.vehicle.getRoadID(veh_id)
                    if edge.startswith(":"):
                        continue
                    try:
                        accel = float(conn.vehicle.getAcceleration(veh_id))
                    except Exception:
                        continue

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

            # E1 readings — aggregated per segment
            row = {"step": step_idx + 1, "sim_time_s": (step_idx + 1) * _AGG_TIME}
            for seg in _ALL_SEGS:
                nl = _LANE_COUNTS.get(seg, 1)
                flow, speed, occ = _read_e1_segment(conn, seg, "exit", nl)
                row[f"{seg}_flow_vph"] = round(flow, 1)
                row[f"{seg}_speed_kph"] = round(speed, 1)
                row[f"{seg}_occ_pct"] = round(occ, 2)

            # Per-lane detail at merge zone segments
            for seg in _LANE_DETAIL_SEGS:
                nl = _LANE_COUNTS.get(seg, 3)
                lane_data = _read_e1_per_lane(conn, seg, "exit", nl)
                for li, (lf, ls, lo) in lane_data.items():
                    row[f"{seg}_L{li}_flow_vph"] = round(lf, 1)
                    row[f"{seg}_L{li}_speed_kph"] = round(ls, 1)
                    row[f"{seg}_L{li}_occ_pct"] = round(lo, 2)

            # E3 multi-entry-exit readings
            for e3_id in _E3_DETECTORS:
                try:
                    tt = float(conn.multientryexit.getLastIntervalMeanTravelTime(e3_id))
                    n_veh = int(conn.multientryexit.getLastIntervalVehicleSum(e3_id))
                    halt = int(conn.multientryexit.getLastIntervalMeanHaltsPerVehicle(e3_id) * max(n_veh, 1))
                    row[f"{e3_id}_travel_time_s"] = round(tt, 2) if tt >= 0 else 0
                    row[f"{e3_id}_veh_count"] = n_veh
                    row[f"{e3_id}_halts"] = halt
                except Exception:
                    row[f"{e3_id}_travel_time_s"] = 0
                    row[f"{e3_id}_veh_count"] = 0
                    row[f"{e3_id}_halts"] = 0

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
    data = [r for r in e1_records if r["sim_time_s"] > _WARMUP_S]

    # Per-window upstream metrics
    sigmas, max_gradients, upstream_speeds = [], [], []
    for r in data:
        v2 = r["seg_2_before_speed_kph"]
        v1 = r["seg_1_before_speed_kph"]
        v0 = r["seg_0_before_speed_kph"]
        if v2 > 0 and v1 > 0 and v0 > 0:
            sigmas.append(float(np.std([v2, v1, v0])))
            max_gradients.append(max(abs(v2 - v1), abs(v1 - v0)))
            upstream_speeds.append(float(np.mean([v2, v1, v0])))

    ds_flows = [r["seg_1_after_flow_vph"] for r in data if r["seg_1_after_flow_vph"] > 0]
    ds_speeds = [r["seg_0_after_speed_kph"] for r in data if r["seg_0_after_speed_kph"] > 0]

    # Temporal instability at downstream (consecutive window speed changes)
    ds_speed_series = [r["seg_0_after_speed_kph"] for r in data]
    ds_temporal_deltas = [
        abs(ds_speed_series[i] - ds_speed_series[i - 1])
        for i in range(1, len(ds_speed_series))
        if ds_speed_series[i] > 0 and ds_speed_series[i - 1] > 0
    ]

    n_breakdown = sum(1 for r in data if r["seg_0_before_speed_kph"] < 45)

    # Ramp metrics
    ramp_speeds = [r["ramp_on_transition_speed_kph"] for r in data
                   if r.get("ramp_on_transition_speed_kph", 0) > 0]
    ramp_merge_speeds = [r["ramp_on_merge_speed_kph"] for r in data
                         if r.get("ramp_on_merge_speed_kph", 0) > 0]

    up_vs = max(up_veh_seconds, 1)
    md_vs = max(md_veh_seconds, 1)

    summary: Dict[str, Any] = {
        "demand_vph": demand_vph,
        "mainline_vsl_kph": f"{int(mainline_vsl_kph)}" if mainline_vsl_kph is not None else "NC",
        "ramp_vsl_kph": f"{int(ramp_vsl_kph)}" if ramp_vsl_kph is not None else "NC",

        # Speed / flow / gradient
        "avg_sigma_upstream": round(np.mean(sigmas), 2) if sigmas else 0,
        "avg_max_gradient_kph": round(np.mean(max_gradients), 2) if max_gradients else 0,
        "max_max_gradient_kph": round(max(max_gradients), 1) if max_gradients else 0,
        "avg_upstream_speed_kph": round(np.mean(upstream_speeds), 1) if upstream_speeds else 0,
        "min_upstream_speed_kph": round(min(upstream_speeds), 1) if upstream_speeds else 0,
        "avg_ds_flow_vph": round(np.mean(ds_flows), 0) if ds_flows else 0,
        "avg_ds_speed_kph": round(np.mean(ds_speeds), 1) if ds_speeds else 0,
        "avg_ds_temporal_delta_kph": round(np.mean(ds_temporal_deltas), 2) if ds_temporal_deltas else 0,
        "max_ds_temporal_delta_kph": round(max(ds_temporal_deltas), 1) if ds_temporal_deltas else 0,
        "n_breakdown_steps": n_breakdown,

        # Ramp
        "avg_ramp_transition_speed_kph": round(np.mean(ramp_speeds), 1) if ramp_speeds else 0,
        "avg_ramp_merge_speed_kph": round(np.mean(ramp_merge_speeds), 1) if ramp_merge_speeds else 0,

        # TTS
        "tts_veh_seconds": tts_veh_seconds,
        "tts_veh_hours": round(tts_veh_seconds / 3600, 1),

        # Upstream accel/decel
        "up_veh_seconds": up_veh_seconds,
        "up_brake_rate_per_1kvs": round(up_brake_count / up_vs * 1000, 1),
        "up_hard_brake_rate_per_1kvs": round(up_hard_brake_count / up_vs * 1000, 1),
        "up_accel_rate_per_1kvs": round(up_accel_count / up_vs * 1000, 1),
        "up_avg_brake_amplitude_ms2": round(np.mean(up_brake_amplitudes), 3) if up_brake_amplitudes else 0,
        "up_p95_brake_amplitude_ms2": round(float(np.percentile(up_brake_amplitudes, 95)), 3) if up_brake_amplitudes else 0,
        "up_avg_accel_amplitude_ms2": round(np.mean(up_accel_amplitudes), 3) if up_accel_amplitudes else 0,
        "up_mean_abs_accel_ms2": round(float(np.mean(np.abs(up_all_accels))), 4) if up_all_accels else 0,

        # Merge+downstream
        "md_veh_seconds": md_veh_seconds,
        "md_brake_rate_per_1kvs": round(md_brake_count / md_vs * 1000, 1),
        "md_hard_brake_rate_per_1kvs": round(md_hard_brake_count / md_vs * 1000, 1),
        "md_mean_abs_accel_ms2": round(float(np.mean(np.abs(md_all_accels))), 4) if md_all_accels else 0,

        "max_veh_in_network": max(r["n_vehicles"] for r in e1_records) if e1_records else 0,
    }

    # E3 summary metrics — travel time, halts, vehicle throughput
    for e3_id in _E3_DETECTORS:
        tt_key = f"{e3_id}_travel_time_s"
        halt_key = f"{e3_id}_halts"
        veh_key = f"{e3_id}_veh_count"

        tts = [r[tt_key] for r in data if r.get(tt_key, 0) > 0]
        halts = [r[halt_key] for r in data if halt_key in r]
        vehs = [r[veh_key] for r in data if r.get(veh_key, 0) > 0]

        summary[f"{e3_id}_avg_tt_s"] = round(float(np.mean(tts)), 2) if tts else 0
        summary[f"{e3_id}_max_tt_s"] = round(float(max(tts)), 2) if tts else 0
        summary[f"{e3_id}_p95_tt_s"] = round(float(np.percentile(tts, 95)), 2) if tts else 0
        summary[f"{e3_id}_total_halts"] = int(sum(halts)) if halts else 0
        summary[f"{e3_id}_total_vehs"] = int(sum(vehs)) if vehs else 0

    # Per-lane metrics at merge zone (seg_0_after) and immediate upstream (seg_0_before)
    for seg in _LANE_DETAIL_SEGS:
        nl = _LANE_COUNTS.get(seg, 3)
        for li in range(nl):
            # Speed
            lane_speeds = [r[f"{seg}_L{li}_speed_kph"] for r in data
                           if r.get(f"{seg}_L{li}_speed_kph", 0) > 0]
            summary[f"{seg}_L{li}_avg_speed_kph"] = (
                round(float(np.mean(lane_speeds)), 1) if lane_speeds else 0)
            summary[f"{seg}_L{li}_min_speed_kph"] = (
                round(float(min(lane_speeds)), 1) if lane_speeds else 0)
            # Flow
            lane_flows = [r[f"{seg}_L{li}_flow_vph"] for r in data
                          if r.get(f"{seg}_L{li}_flow_vph", 0) > 0]
            summary[f"{seg}_L{li}_avg_flow_vph"] = (
                round(float(np.mean(lane_flows)), 0) if lane_flows else 0)
            # Occupancy
            lane_occs = [r[f"{seg}_L{li}_occ_pct"] for r in data
                         if f"{seg}_L{li}_occ_pct" in r]
            summary[f"{seg}_L{li}_avg_occ_pct"] = (
                round(float(np.mean(lane_occs)), 2) if lane_occs else 0)

        # Lane speed variance (how uneven is the flow across lanes at this segment)
        lane_avgs = [summary[f"{seg}_L{li}_avg_speed_kph"] for li in range(nl)]
        valid_avgs = [v for v in lane_avgs if v > 0]
        summary[f"{seg}_lane_speed_sigma_kph"] = (
            round(float(np.std(valid_avgs)), 2) if len(valid_avgs) > 1 else 0)

        # Speed differential between lane 0 (merge lane) and lanes 1-2
        l0_spd = summary.get(f"{seg}_L0_avg_speed_kph", 0)
        l12_spds = [summary.get(f"{seg}_L{li}_avg_speed_kph", 0)
                    for li in range(1, nl)]
        l12_avg = float(np.mean([s for s in l12_spds if s > 0])) if any(s > 0 for s in l12_spds) else 0
        summary[f"{seg}_L0_vs_L12_delta_kph"] = round(l0_spd - l12_avg, 1) if l0_spd > 0 and l12_avg > 0 else 0

    return summary


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    import argparse

    parser = argparse.ArgumentParser(description="Comprehensive feasibility sweep")
    parser.add_argument("--workers", type=int, default=140,
                        help="Max parallel SUMO processes (default: 140)")
    args = parser.parse_args()

    # Build task list
    tasks: List[Tuple[int, Optional[float], Optional[float]]] = []

    # No-control: one per demand
    for d in _DEMAND_LEVELS:
        tasks.append((d, None, None))

    # Controlled: all mainline × ramp combinations at each demand
    for d in _DEMAND_LEVELS:
        for ml in _MAINLINE_VSL_KPH:
            for rp in _RAMP_VSL_KPH:
                tasks.append((d, ml, rp))

    n_tasks = len(tasks)
    n_workers = min(n_tasks, args.workers)

    ts = datetime.now().strftime("%d-%m-%Y_%H-%M-%S")
    result_dir = _RESULTS_ROOT / f"feasibility_sweep_{ts}"
    result_dir.mkdir(parents=True, exist_ok=True)

    print(f"Feasibility sweep — comprehensive 2D action space mapping")
    print(f"  {n_tasks} scenarios on {n_workers} workers")
    print(f"  Demands:      {_DEMAND_LEVELS[0]}–{_DEMAND_LEVELS[-1]} vph "
          f"(step 500, {len(_DEMAND_LEVELS)} levels)")
    print(f"  Mainline VSL: NC + {_MAINLINE_VSL_KPH} kph ({1 + len(_MAINLINE_VSL_KPH)} levels)")
    print(f"  Ramp VSL:     NC + {_RAMP_VSL_KPH} kph ({1 + len(_RAMP_VSL_KPH)} levels)")
    print(f"  No-control:   {len(_DEMAND_LEVELS)} scenarios")
    print(f"  Controlled:   {len(_DEMAND_LEVELS)} × {len(_MAINLINE_VSL_KPH)} × "
          f"{len(_RAMP_VSL_KPH)} = "
          f"{len(_DEMAND_LEVELS) * len(_MAINLINE_VSL_KPH) * len(_RAMP_VSL_KPH)} scenarios")
    print(f"  Output: {result_dir}\n")

    t0 = time.time()
    summaries: List[Dict[str, Any]] = []
    failed = 0

    # Track in-flight workers so we can show how many are active.
    active_count = 0

    def _progress_bar(done: int, total: int, width: int = 40) -> str:
        frac = done / total if total else 0
        filled = int(width * frac)
        bar = "█" * filled + "░" * (width - filled)
        return f"|{bar}| {frac:5.1%}"

    print(f"  Submitting {n_tasks} tasks to {n_workers} workers...")
    sys.stdout.flush()

    with ProcessPoolExecutor(max_workers=n_workers) as pool:
        futures = {}
        for d, ml, rp in tasks:
            f = pool.submit(_run_scenario, d, ml, rp)
            futures[f] = (d, ml, rp)
        active_count = len(futures)

        print(f"  All {n_tasks} tasks submitted. Waiting for results...\n")
        sys.stdout.flush()

        for f in as_completed(futures):
            d, ml, rp = futures[f]
            active_count -= 1
            ml_s = f"M{int(ml)}" if ml is not None else "NC"
            rp_s = f"R{int(rp)}" if rp is not None else "NC"
            try:
                s = f.result()
                summaries.append(s)
                done = len(summaries) + failed
                elapsed = time.time() - t0
                rate = done / elapsed if elapsed > 0 else 0
                remaining = (n_tasks - done) / rate if rate > 0 else 0

                print(
                    f"  {_progress_bar(done, n_tasks)} "
                    f"[{done:>4}/{n_tasks}] "
                    f"{ml_s:>4}+{rp_s:>3}@{d:>5}vph "
                    f"avg|a|={s['up_mean_abs_accel_ms2']:>6} "
                    f"flow={s['avg_ds_flow_vph']:>5} "
                    f"TTS={s['tts_veh_hours']:>6}vh "
                    f"[{elapsed:>5.0f}s, ~{remaining/60:.0f}m left, "
                    f"{active_count} active]"
                )
                sys.stdout.flush()
            except Exception as e:
                failed += 1
                done = len(summaries) + failed
                elapsed = time.time() - t0
                print(
                    f"  {_progress_bar(done, n_tasks)} "
                    f"[{done:>4}/{n_tasks}] "
                    f"FAILED {ml_s}+{rp_s}@{d}vph: {e} "
                    f"[{elapsed:.0f}s, {active_count} active]"
                )
                sys.stdout.flush()

    # Sort: demand → mainline → ramp
    def _sort_key(s):
        ml = int(s["mainline_vsl_kph"]) if s["mainline_vsl_kph"] != "NC" else -1
        rp = int(s["ramp_vsl_kph"]) if s["ramp_vsl_kph"] != "NC" else -1
        return (s["demand_vph"], ml, rp)

    summaries.sort(key=_sort_key)

    # Write summary CSV
    if summaries:
        csv_path = result_dir / "summary.csv"
        with csv_path.open("w", newline="", encoding="utf-8") as fh:
            writer = csv.DictWriter(fh, fieldnames=summaries[0].keys())
            writer.writeheader()
            writer.writerows(summaries)
        print(f"\nSummary CSV: {csv_path}")

    # ----- Print condensed results -----
    elapsed_total = time.time() - t0

    # No-control baseline table
    nc = [s for s in summaries if s["mainline_vsl_kph"] == "NC"]
    if nc:
        print(f"\n{'='*120}")
        print("NO-CONTROL BASELINE")
        print(f"{'='*120}")
        print(f"{'Demand':>7} | {'σ_up':>5} {'grad':>5} {'spd':>5} {'min_spd':>7} "
              f"{'flow':>5} {'TTS_vh':>6} | "
              f"{'avg|a|':>6} {'brk/1k':>6} {'hard/1k':>7} | "
              f"{'DS_spd':>6} {'DS_Δv':>5} | {'BD':>3}")
        print("-" * 120)
        for s in nc:
            print(f"{s['demand_vph']:>7} | "
                  f"{s['avg_sigma_upstream']:>5} {s['avg_max_gradient_kph']:>5} "
                  f"{s['avg_upstream_speed_kph']:>5} {s['min_upstream_speed_kph']:>7} "
                  f"{s['avg_ds_flow_vph']:>5} {s['tts_veh_hours']:>6} | "
                  f"{s['up_mean_abs_accel_ms2']:>6} {s['up_brake_rate_per_1kvs']:>6} "
                  f"{s['up_hard_brake_rate_per_1kvs']:>7} | "
                  f"{s['avg_ds_speed_kph']:>6} {s['avg_ds_temporal_delta_kph']:>5} | "
                  f"{s['n_breakdown_steps']:>3}")

    # Best actions per demand (by avg|a| with throughput constraint)
    print(f"\n{'='*120}")
    print("BEST ACTIONS PER DEMAND (lowest avg|a| where ds_flow >= 80% of NC)")
    print(f"{'='*120}")
    print(f"{'Demand':>7} | {'Best ML':>7} {'Best RP':>7} | "
          f"{'avg|a|':>6} {'Δ vs NC':>7} | "
          f"{'flow':>5} {'TTS_vh':>6} {'Δ TTS':>6} | "
          f"{'grad':>5} {'DS_Δv':>5}")
    print("-" * 120)

    for d in _DEMAND_LEVELS:
        nc_row = next((s for s in nc if s["demand_vph"] == d), None)
        if nc_row is None:
            continue
        nc_flow = nc_row["avg_ds_flow_vph"]
        nc_accel = nc_row["up_mean_abs_accel_ms2"]
        nc_tts = nc_row["tts_veh_hours"]
        flow_floor = nc_flow * 0.80

        candidates = [
            s for s in summaries
            if s["demand_vph"] == d
            and s["mainline_vsl_kph"] != "NC"
            and s["avg_ds_flow_vph"] >= flow_floor
        ]

        if not candidates:
            print(f"{d:>7} | {'none':>7} {'':>7} | {'':>6} {'':>7} | "
                  f"{'':>5} {'':>6} {'':>6} | no candidate meets flow constraint")
            continue

        best = min(candidates, key=lambda s: s["up_mean_abs_accel_ms2"])
        delta_accel = best["up_mean_abs_accel_ms2"] - nc_accel
        delta_tts = best["tts_veh_hours"] - nc_tts

        print(f"{d:>7} | {best['mainline_vsl_kph']:>7} {best['ramp_vsl_kph']:>7} | "
              f"{best['up_mean_abs_accel_ms2']:>6} {delta_accel:>+7.3f} | "
              f"{best['avg_ds_flow_vph']:>5} {best['tts_veh_hours']:>6} {delta_tts:>+6.0f} | "
              f"{best['avg_max_gradient_kph']:>5} {best['avg_ds_temporal_delta_kph']:>5}")

    # Ramp independence check at two demand levels
    for check_demand in [6500, 7000]:
        for check_ml in ["90", "85"]:
            ramp_check = [
                s for s in summaries
                if s["demand_vph"] == check_demand
                and s["mainline_vsl_kph"] == check_ml
            ]
            if not ramp_check:
                continue
            print(f"\n{'='*120}")
            print(f"RAMP VSL INDEPENDENCE CHECK "
                  f"(mainline={check_ml} kph, demand={check_demand} vph)")
            print(f"{'='*120}")
            ramp_check.sort(key=lambda s: int(s["ramp_vsl_kph"]))
            print(f"{'Ramp':>6} | {'avg|a|':>6} {'grad':>5} {'flow':>5} {'TTS_vh':>6} | "
                  f"{'ramp_spd':>8} {'merge_spd':>9} | {'brk/1k':>6} {'DS_Δv':>5}")
            print("-" * 90)
            for s in ramp_check:
                print(f"{s['ramp_vsl_kph']:>6} | "
                      f"{s['up_mean_abs_accel_ms2']:>6} {s['avg_max_gradient_kph']:>5} "
                      f"{s['avg_ds_flow_vph']:>5} {s['tts_veh_hours']:>6} | "
                      f"{s['avg_ramp_transition_speed_kph']:>8} "
                      f"{s['avg_ramp_merge_speed_kph']:>9} | "
                      f"{s['up_brake_rate_per_1kvs']:>6} "
                      f"{s['avg_ds_temporal_delta_kph']:>5}")

    print(f"\nTotal: {len(summaries)} completed, {failed} failed, "
          f"{elapsed_total:.0f}s ({elapsed_total/60:.1f}m)")
    print(f"Results: {result_dir}")


if __name__ == "__main__":
    main()
