#!/usr/bin/env python3
"""
Extended no-control baseline: demands 7500–9000 vph.

Standalone script (no pytest required). Reuses the same logic as
test_nocontrol_baseline.py but runs directly.

Usage:
    python3 tests/run_extended_baseline.py
"""
from __future__ import annotations

import csv
import os
import shutil
import sys
import tempfile
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np

# Ensure traci is importable
_SUMO_HOME = os.environ.get("SUMO_HOME", "/usr/share/sumo")
sys.path.insert(0, os.path.join(_SUMO_HOME, "tools"))

_SUMO_DIR = Path(__file__).resolve().parents[1] / "traffic_environment" / "sumo"
_NET_FILE = _SUMO_DIR / "ramps_v1.net.xml"
_DET_FILE = _SUMO_DIR / "detectors_ramps_v1.add.xml"
_RESULTS_ROOT = Path(__file__).resolve().parent / "results"

_EPISODE_S = 3600
_AGG_TIME = 30
_CAV_PCT = 50.0
_RAMP_DELAY_S = 100.0

_DEMAND_LEVELS = [7500, 8000, 8500, 9000]

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


def _generate_route_file(output_path: Path, demand_vph: int, episode_s: int, cav_pct: float) -> None:
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
    vehicles = []

    def _make_vehicles(count, route_id, t_offset, t_span):
        if count <= 0:
            return
        step = t_span / count
        for i in range(count):
            depart = t_offset + (i + 0.5) * step
            if depart > episode_s:
                break
            vehicles.append((depart, route_id))

    _make_vehicles(n_mainline, "mainline_through", 0.0, float(episode_s))
    _make_vehicles(n_off, "mainline_to_off", 0.0, float(episode_s))
    _make_vehicles(n_ramp, "ramp_on_through", _RAMP_DELAY_S, float(episode_s) - _RAMP_DELAY_S)
    vehicles.sort(key=lambda v: v[0])

    for veh_id, (depart, route_id) in enumerate(vehicles):
        is_cav = rng.random() * 100.0 < cav_pct
        vtype = "CAV" if is_cav else "HDV"
        ET.SubElement(routes, "vehicle",
                      id=f"veh_{veh_id}", type=vtype,
                      route=route_id, depart=f"{depart:.2f}",
                      departPos="last", departLane="best",
                      departSpeed="desired", insertionChecks="none")

    tree = ET.ElementTree(routes)
    ET.indent(tree, space="  ")
    tree.write(str(output_path), encoding="unicode", xml_declaration=True)


def _generate_sumocfg(cfg_path: Path, rou_path: Path) -> None:
    content = f"""<?xml version="1.0" encoding="UTF-8"?>
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
"""
    cfg_path.write_text(content, encoding="utf-8")


def _read_e1_segment(seg: str, position: str, n_lanes: int) -> Tuple[float, float, float]:
    import traci
    counts, speeds, occs = [], [], []
    for lane_idx in range(n_lanes):
        det_id = f"flow_loop_{seg}_{lane_idx}_{position}"
        try:
            cnt = float(traci.inductionloop.getLastIntervalVehicleNumber(det_id))
            spd = float(traci.inductionloop.getLastIntervalMeanSpeed(det_id))
            occ = float(traci.inductionloop.getLastIntervalOccupancy(det_id))
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
    speed_kph = speed_ms * 3.6
    occ_pct = float(np.mean(occs)) if occs else 0.0
    return flow_vph, speed_kph, occ_pct


def run_episode(demand_vph: int) -> List[Dict]:
    import traci

    tmpdir = Path(tempfile.mkdtemp(prefix="nocontrol_ext_"))
    rou_path = tmpdir / "flows.rou.xml"
    cfg_path = tmpdir / "sim.sumocfg"

    _generate_route_file(rou_path, demand_vph, _EPISODE_S, _CAV_PCT)
    _generate_sumocfg(cfg_path, rou_path)

    cmd = ["sumo", "-c", str(cfg_path), "--start", "--no-step-log", "--no-warnings"]
    traci.start(cmd)

    records = []
    max_steps = _EPISODE_S // _AGG_TIME

    try:
        for step_idx in range(max_steps):
            for _ in range(_AGG_TIME):
                traci.simulationStep()

            sim_time = (step_idx + 1) * _AGG_TIME
            n_veh = int(traci.vehicle.getIDCount())

            row = {
                "step": step_idx + 1,
                "sim_time_s": sim_time,
                "demand_vph": demand_vph,
                "n_vehicles_in_network": n_veh,
            }

            for seg in _ALL_SEGS:
                n_lanes = _LANE_COUNTS.get(seg, 1)
                flow, speed, occ = _read_e1_segment(seg, "exit", n_lanes)
                row[f"{seg}_flow_vph"] = round(flow, 1)
                row[f"{seg}_speed_kph"] = round(speed, 1)
                row[f"{seg}_occ_pct"] = round(occ, 2)

            records.append(row)
    finally:
        try:
            traci.close(False)
        except Exception:
            pass
        shutil.rmtree(tmpdir, ignore_errors=True)

    return records


def main():
    ts = datetime.now().strftime("%d-%m-%Y_%H-%M-%S")
    result_dir = _RESULTS_ROOT / f"nocontrol_extended_{ts}"
    result_dir.mkdir(parents=True, exist_ok=True)

    all_records = []

    for demand_vph in _DEMAND_LEVELS:
        print(f"\n{'='*60}")
        print(f"  No-control baseline @ {demand_vph} veh/h")
        print(f"{'='*60}")

        records = run_episode(demand_vph)
        all_records.extend(records)

        # Per-demand CSV
        csv_path = result_dir / f"nocontrol_{demand_vph}vph.csv"
        if records:
            with csv_path.open("w", newline="", encoding="utf-8") as fh:
                writer = csv.DictWriter(fh, fieldnames=records[0].keys())
                writer.writeheader()
                writer.writerows(records)

        if records:
            s0a_speeds = [r["seg_0_after_speed_kph"] for r in records]
            s0a_occs = [r["seg_0_after_occ_pct"] for r in records]
            s0b_speeds = [r["seg_0_before_speed_kph"] for r in records if r["seg_0_before_speed_kph"] > 0]
            ramp_speeds = [r["ramp_on_merge_speed_kph"] for r in records if r["ramp_on_merge_speed_kph"] > 0]
            ds_flows = [r["seg_1_after_flow_vph"] for r in records if r["seg_1_after_flow_vph"] > 0]
            n_vehs = [r["n_vehicles_in_network"] for r in records]

            avg_s0a = sum(s0a_speeds) / len(s0a_speeds)
            min_s0a = min(s for s in s0a_speeds if s > 0) if any(s > 0 for s in s0a_speeds) else 0
            max_occ = max(s0a_occs)

            # Breakdown detection at merge zone
            breakdown_merge = None
            for r in records:
                if r["seg_0_after_speed_kph"] < 60.0 and r["sim_time_s"] > 150:
                    breakdown_merge = f"step {r['step']} (t={r['sim_time_s']}s)"
                    break

            # Breakdown detection at upstream
            breakdown_upstream = None
            for r in records:
                if r["seg_0_before_speed_kph"] < 45.0 and r["sim_time_s"] > 150:
                    breakdown_upstream = f"step {r['step']} (t={r['sim_time_s']}s)"
                    break

            # Spillback detection (queue reaches seg_2_before)
            spillback = None
            for r in records:
                if r["seg_2_before_speed_kph"] < 60.0 and r["sim_time_s"] > 200:
                    spillback = f"step {r['step']} (t={r['sim_time_s']}s)"
                    break

            print(f"\n  seg_0_after (merge zone):")
            print(f"    Avg speed: {avg_s0a:.1f} kph | Min (excl warmup): {min_s0a:.1f} kph")
            print(f"    Max occupancy: {max_occ:.1f}%")
            print(f"    Merge breakdown: {breakdown_merge or 'None'}")

            print(f"  seg_0_before (upstream):")
            if s0b_speeds:
                print(f"    Avg: {sum(s0b_speeds)/len(s0b_speeds):.1f} kph | Min: {min(s0b_speeds):.1f} kph")
            print(f"    Upstream breakdown (<45 kph): {breakdown_upstream or 'None'}")
            print(f"    Spillback to seg_2 (<60 kph): {spillback or 'None'}")

            if ramp_speeds:
                print(f"  ramp_on_merge: avg={sum(ramp_speeds)/len(ramp_speeds):.1f} kph, min={min(ramp_speeds):.1f} kph")
            if ds_flows:
                print(f"  seg_1_after throughput: avg={sum(ds_flows)/len(ds_flows):.0f} vph, max={max(ds_flows):.0f} vph")
            print(f"  Max vehicles in network: {max(n_vehs)}")
            print(f"  Final vehicles in network: {n_vehs[-1]}")

    # Combined CSV
    if all_records:
        combined_path = result_dir / "nocontrol_all_demands.csv"
        with combined_path.open("w", newline="", encoding="utf-8") as fh:
            writer = csv.DictWriter(fh, fieldnames=all_records[0].keys())
            writer.writeheader()
            writer.writerows(all_records)

    print(f"\n\nResults written to: {result_dir}")


if __name__ == "__main__":
    main()
