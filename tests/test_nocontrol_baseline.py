# tests/test_nocontrol_baseline.py
"""
No-control baseline diagnostic for the ramps_v1 network.

Purpose
-------
Answer: at what point in the episode does congestion form at the merge?
Is the failure mode recurrent/predictable or stochastic?

This test bypasses the SAR framework entirely and reads raw TraCI data
from every E1 detector at every 30 s window.  It writes a CSV with
per-window speed, flow, and occupancy for all segments + ramp edges,
plus the vehicle count in the network.

Network: ramps_v1
  3L mainline (4 × 1000m) → 4L weaving (500m) → 3L downstream (1000m)
  On-ramp: 1000m (700 approach + 200 transition + 100 merge)
  Off-ramp: 1000m (100 diverge + 200 transition + 700 departure)

Routes:
  mainline_through: seg_3..0_before → seg_0_after → seg_1_after  (75%)
  ramp_on_through:  ramp_on_* → seg_0_after → seg_1_after        (15%)
  mainline_to_off:  seg_3..0_before → seg_0_after → ramp_off_*   (10%)

Ramp departure delay: 100s (vehicles arrive at merge synchronized with
mainline vehicles that entered at t=0).

Run
---
    pytest tests/test_nocontrol_baseline.py -v -s
"""
from __future__ import annotations

import csv
import shutil
import tempfile
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np
import pytest

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_SUMO_DIR = Path(__file__).resolve().parents[1] / "traffic_environment" / "sumo"
_NET_FILE = _SUMO_DIR / "ramps_v1.net.xml"
_DET_FILE = _SUMO_DIR / "detectors_ramps_v1.add.xml"
_RESULTS_ROOT = Path(__file__).resolve().parent / "results"

_EPISODE_S = 3600          # 1-hour episode
_AGG_TIME = 30             # E1 aggregation window (seconds)
_CAV_PCT = 50.0            # % of vehicles that are CAVs
_RAMP_DELAY_S = 100.0      # ramp vehicle departure offset

_DEMAND_LEVELS = [2500, 3500, 4500, 5000, 5500, 6000, 6500, 7000]

# Demand split
_MAINLINE_THROUGH_FRAC = 0.75
_RAMP_ON_FRAC = 0.15
_MAINLINE_TO_OFF_FRAC = 0.10

# Segments to monitor
_MAINLINE_SEGS = [
    "seg_3_before", "seg_2_before", "seg_1_before", "seg_0_before",
    "seg_0_after", "seg_1_after",
]
_RAMP_SEGS = [
    "ramp_on_approach", "ramp_on_transition", "ramp_on_merge",
    "ramp_off_diverge", "ramp_off_transition", "ramp_off_departure",
]
_ALL_SEGS = _MAINLINE_SEGS + _RAMP_SEGS

# Lane counts per segment (ramps_v1)
_LANE_COUNTS: Dict[str, int] = {
    "seg_3_before": 3, "seg_2_before": 3, "seg_1_before": 3, "seg_0_before": 3,
    "seg_0_after": 4, "seg_1_after": 3,
    "ramp_on_approach": 1, "ramp_on_transition": 1, "ramp_on_merge": 1,
    "ramp_off_diverge": 1, "ramp_off_transition": 1, "ramp_off_departure": 1,
}

pytestmark = pytest.mark.sumo


# ---------------------------------------------------------------------------
# Route file generation
# ---------------------------------------------------------------------------

def _generate_route_file(
    output_path: Path,
    demand_vph: int,
    episode_s: int,
    cav_pct: float,
) -> None:
    """Write a .rou.xml with 3 routes and 100s ramp delay."""
    routes = ET.Element("routes")

    # Vehicle types — one HDV, one CAV (Krauss)
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

    # 3 routes
    ET.SubElement(routes, "route", id="mainline_through",
                  edges="seg_3_before seg_2_before seg_1_before seg_0_before seg_0_after seg_1_after")
    ET.SubElement(routes, "route", id="ramp_on_through",
                  edges="ramp_on_approach ramp_on_transition ramp_on_merge seg_0_after seg_1_after")
    ET.SubElement(routes, "route", id="mainline_to_off",
                  edges="seg_3_before seg_2_before seg_1_before seg_0_before seg_0_after ramp_off_diverge ramp_off_transition ramp_off_departure")

    # Vehicle counts per route
    total_veh = int(demand_vph * episode_s / 3600)
    n_mainline = int(total_veh * _MAINLINE_THROUGH_FRAC)
    n_ramp = int(total_veh * _RAMP_ON_FRAC)
    n_off = total_veh - n_mainline - n_ramp

    rng = np.random.default_rng(42)
    vehicles = []  # list of (depart_time, route_id)

    def _make_vehicles(count: int, route_id: str, t_offset: float, t_span: float):
        if count <= 0:
            return
        step = t_span / count
        for i in range(count):
            depart = t_offset + (i + 0.5) * step
            if depart > episode_s:
                break
            vehicles.append((depart, route_id))

    # Mainline vehicles depart from t=0 over the full episode
    _make_vehicles(n_mainline, "mainline_through", 0.0, float(episode_s))
    # Off-ramp destined vehicles also from t=0 (they enter on mainline)
    _make_vehicles(n_off, "mainline_to_off", 0.0, float(episode_s))
    # Ramp-on vehicles depart from t=100s (synchronized arrival at merge)
    ramp_span = float(episode_s) - _RAMP_DELAY_S
    _make_vehicles(n_ramp, "ramp_on_through", _RAMP_DELAY_S, ramp_span)

    # Sort by departure time
    vehicles.sort(key=lambda v: v[0])

    # Emit vehicle elements
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


# ---------------------------------------------------------------------------
# E1 reader
# ---------------------------------------------------------------------------

def _read_e1_segment(seg: str, position: str, n_lanes: int) -> Tuple[float, float, float]:
    """Return (flow_vph, speed_kph, occ_pct) for a segment/position."""
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


# ---------------------------------------------------------------------------
# Test
# ---------------------------------------------------------------------------

@pytest.mark.skipif(shutil.which("sumo") is None, reason="sumo not on PATH")
class TestNoControlBaseline:

    def _run_episode(self, demand_vph: int) -> List[Dict]:
        """Run one no-control episode and return per-step records."""
        import traci

        tmpdir = Path(tempfile.mkdtemp(prefix="nocontrol_"))
        rou_path = tmpdir / "flows.rou.xml"
        cfg_path = tmpdir / "sim.sumocfg"

        _generate_route_file(rou_path, demand_vph, _EPISODE_S, _CAV_PCT)
        _generate_sumocfg(cfg_path, rou_path)

        cmd = [
            "sumo",
            "-c", str(cfg_path),
            "--start",
            "--no-step-log",
            "--no-warnings",
        ]
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

    def test_demand_sweep(self):
        """Sweep demand levels and write per-step CSV for each."""
        ts = datetime.now().strftime("%d-%m-%Y_%H-%M-%S")
        result_dir = _RESULTS_ROOT / f"nocontrol_ramps_v1_{ts}"
        result_dir.mkdir(parents=True, exist_ok=True)

        all_records = []

        for demand_vph in _DEMAND_LEVELS:
            print(f"\n{'='*60}")
            print(f"  No-control baseline @ {demand_vph} veh/h")
            print(f"  Routes: 75% mainline, 15% ramp-on, 10% to off-ramp")
            print(f"  Ramp delay: {_RAMP_DELAY_S}s")
            print(f"{'='*60}")

            records = self._run_episode(demand_vph)
            all_records.extend(records)

            # Per-demand CSV
            csv_path = result_dir / f"nocontrol_{demand_vph}vph.csv"
            if records:
                with csv_path.open("w", newline="", encoding="utf-8") as fh:
                    writer = csv.DictWriter(fh, fieldnames=records[0].keys())
                    writer.writeheader()
                    writer.writerows(records)

            if records:
                # Merge zone analysis
                s0a_speeds = [r["seg_0_after_speed_kph"] for r in records]
                s0a_occs = [r["seg_0_after_occ_pct"] for r in records]
                min_speed = min(s0a_speeds)
                max_occ = max(s0a_occs)
                avg_speed = sum(s0a_speeds) / len(s0a_speeds)

                breakdown_step = None
                for r in records:
                    if r["seg_0_after_speed_kph"] < 60.0 and r["sim_time_s"] > 150:
                        breakdown_step = r["step"]
                        break

                print(f"\n  seg_0_after (weaving zone, 500m, 4 lanes):")
                print(f"    Avg speed: {avg_speed:.1f} kph | Min: {min_speed:.1f} kph")
                print(f"    Max occupancy: {max_occ:.1f}%")
                if breakdown_step:
                    print(f"    >>> BREAKDOWN at step {breakdown_step} "
                          f"(t={breakdown_step * _AGG_TIME}s) <<<")
                else:
                    print(f"    No breakdown (speed stayed >= 60 kph)")

                # Upstream propagation
                for seg in ["seg_0_before", "seg_1_before"]:
                    speeds = [r[f"{seg}_speed_kph"] for r in records
                              if r[f"{seg}_speed_kph"] > 0]
                    if speeds:
                        print(f"  {seg}: avg={sum(speeds)/len(speeds):.1f} kph, "
                              f"min={min(speeds):.1f} kph")

                # Ramp merge
                ramp_speeds = [r["ramp_on_merge_speed_kph"] for r in records
                               if r["ramp_on_merge_speed_kph"] > 0]
                if ramp_speeds:
                    print(f"  ramp_on_merge: avg={sum(ramp_speeds)/len(ramp_speeds):.1f} kph, "
                          f"min={min(ramp_speeds):.1f} kph")

                # Downstream throughput
                ds_flows = [r["seg_1_after_flow_vph"] for r in records
                            if r["seg_1_after_flow_vph"] > 0]
                if ds_flows:
                    print(f"  seg_1_after throughput: avg={sum(ds_flows)/len(ds_flows):.0f} vph, "
                          f"max={max(ds_flows):.0f} vph")

                # Vehicles in network (queue buildup indicator)
                max_veh = max(r["n_vehicles_in_network"] for r in records)
                print(f"  Max vehicles in network: {max_veh}")

        # Combined CSV
        if all_records:
            combined_path = result_dir / "nocontrol_all_demands.csv"
            with combined_path.open("w", newline="", encoding="utf-8") as fh:
                writer = csv.DictWriter(fh, fieldnames=all_records[0].keys())
                writer.writeheader()
                writer.writerows(all_records)

        # Summary
        summary_path = result_dir / "summary.txt"
        with summary_path.open("w", encoding="utf-8") as fh:
            fh.write("No-control baseline diagnostic — ramps_v1\n")
            fh.write("=" * 50 + "\n")
            fh.write(f"Network: ramps_v1 (3L×4km + 4L weaving 500m + 3L×1km)\n")
            fh.write(f"On-ramp: 1000m | Off-ramp: 1000m\n")
            fh.write(f"Episode: {_EPISODE_S}s | Aggregation: {_AGG_TIME}s\n")
            fh.write(f"CAV penetration: {_CAV_PCT}%\n")
            fh.write(f"Ramp departure delay: {_RAMP_DELAY_S}s\n")
            fh.write(f"Demand split: {_MAINLINE_THROUGH_FRAC*100:.0f}% mainline, "
                     f"{_RAMP_ON_FRAC*100:.0f}% ramp-on, "
                     f"{_MAINLINE_TO_OFF_FRAC*100:.0f}% to off-ramp\n")
            fh.write(f"Demand levels: {_DEMAND_LEVELS} veh/h\n\n")
            fh.write(f"Results: {result_dir}\n")

        print(f"\n\nResults written to: {result_dir}")
