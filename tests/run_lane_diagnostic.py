#!/usr/bin/env python3
"""
Lane-level diagnostic: confirms where the bottleneck actually forms.

Runs a few scenarios (NC + key VSL combos) at critical demands and
dumps per-lane, per-30s-window data for:
  - Every E1 loop: speed, flow, occupancy
  - seg_0_after lane 0 vs lanes 1-3 (ramp lane vs mainline lanes)
  - Off-ramp flow (how many ramp vehicles get forced off)
  - Per-vehicle route completion (via traci)

Output: one CSV per scenario with full time-series, plus a summary.
"""
from __future__ import annotations

import csv
import os
import socket
import subprocess
import sys
import tempfile
import time
from pathlib import Path

_SUMO_HOME = os.environ.get("SUMO_HOME", "/usr/share/sumo")
sys.path.insert(0, os.path.join(_SUMO_HOME, "tools"))

import traci  # noqa: E402

# --- paths ----------------------------------------------------------------
_HERE = Path(__file__).resolve().parent
_PROJ = _HERE.parent
_SUMO_DIR = _PROJ / "traffic_environment" / "sumo"
NET_FILE = _SUMO_DIR / "ramps_v1.net.xml"
DET_FILE = _SUMO_DIR / "detectors_ramps_v1.add.xml"
RESULTS_DIR = _HERE / "results" / "lane_diagnostic"

# --- E1 loops to query every step -----------------------------------------
# Focus on the merge zone: seg_0_after (4 lanes) and seg_1_after (3 lanes)
E1_LOOPS = []
for seg in ("seg_0_before", "seg_0_after", "seg_1_after"):
    n_lanes = 4 if seg == "seg_0_after" else 3
    for lane_idx in range(n_lanes):
        for pos_tag in ("entry", "mid", "exit"):
            E1_LOOPS.append(f"flow_loop_{seg}_{lane_idx}_{pos_tag}")

# Ramp loops
for seg in ("ramp_on_approach", "ramp_on_transition", "ramp_on_merge",
            "ramp_off_diverge", "ramp_off_transition", "ramp_off_departure"):
    for pos_tag in ("entry", "mid", "exit"):
        E1_LOOPS.append(f"flow_loop_{seg}_0_{pos_tag}")


def _find_free_port() -> int:
    with socket.socket() as s:
        s.bind(("", 0))
        return s.getsockname()[1]


def _generate_routes(path: Path, demand_vph: int, episode_s: int, seed: int = 42):
    """Minimal route generation matching _sumo_helpers."""
    import numpy as np
    import xml.etree.ElementTree as ET

    routes = ET.Element("routes")
    ET.SubElement(routes, "vType", id="HDV", carFollowModel="Krauss",
                  vClass="passenger", color="1,1,0", length="4.50",
                  minGap="2.50", accel="2.60", decel="4.50", sigma="0.50",
                  maxSpeed="36.11", tau="1.40", speedFactor="1.00", speedDev="0.10")
    ET.SubElement(routes, "vType", id="CAV", carFollowModel="Krauss",
                  vClass="passenger", color="0,1,0", length="4.50",
                  minGap="1.25", accel="2.86", decel="4.73", sigma="0.00",
                  maxSpeed="36.11", tau="1.00", speedFactor="1.00", speedDev="0.00")

    ET.SubElement(routes, "route", id="mainline_through",
                  edges="seg_3_before seg_2_before seg_1_before seg_0_before seg_0_after seg_1_after")
    ET.SubElement(routes, "route", id="ramp_on_through",
                  edges="ramp_on_approach ramp_on_transition ramp_on_merge seg_0_after seg_1_after")
    ET.SubElement(routes, "route", id="mainline_to_off",
                  edges="seg_3_before seg_2_before seg_1_before seg_0_before seg_0_after ramp_off_diverge ramp_off_transition ramp_off_departure")

    total_veh = int(demand_vph * episode_s / 3600)
    n_mainline = int(total_veh * 0.75)
    n_ramp = int(total_veh * 0.15)
    n_off = total_veh - n_mainline - n_ramp

    rng = np.random.default_rng(seed)
    vehicles = []
    ramp_delay = 100.0

    def _add(count, route_id, t_off, t_span):
        if count <= 0:
            return
        step = t_span / count
        for i in range(count):
            dep = t_off + (i + 0.5) * step
            if dep > episode_s:
                break
            vehicles.append((dep, route_id))

    _add(n_mainline, "mainline_through", 0.0, float(episode_s))
    _add(n_off, "mainline_to_off", 0.0, float(episode_s))
    _add(n_ramp, "ramp_on_through", ramp_delay, float(episode_s) - ramp_delay)
    vehicles.sort(key=lambda v: v[0])

    for vid, (depart, route_id) in enumerate(vehicles):
        is_cav = rng.random() * 100.0 < 50.0
        vtype = "CAV" if is_cav else "HDV"
        ET.SubElement(routes, "vehicle", id=f"veh_{vid}", type=vtype,
                      route=route_id, depart=f"{depart:.2f}",
                      departPos="last", departLane="best",
                      departSpeed="desired", insertionChecks="none")

    tree = ET.ElementTree(routes)
    ET.indent(tree, space="  ")
    tree.write(str(path), encoding="unicode", xml_declaration=True)


def run_diagnostic(demand_vph: int, mainline_kph, ramp_kph,
                   episode_s: int = 3600, agg_s: int = 30) -> dict:
    """Run one scenario and return per-window, per-lane data."""
    label = f"D{demand_vph}_M{mainline_kph}_R{ramp_kph}"
    tmp = Path(tempfile.mkdtemp(prefix=f"diag_{label}_"))

    rou_path = tmp / "scenario.rou.xml"
    _generate_routes(rou_path, demand_vph, episode_s)

    cfg_path = tmp / "scenario.sumocfg"
    cfg_path.write_text(f"""<?xml version="1.0" encoding="UTF-8"?>
<configuration>
    <input>
        <net-file value="{NET_FILE.resolve()}"/>
        <route-files value="{rou_path.resolve()}"/>
        <additional-files value="{DET_FILE.resolve()}"/>
    </input>
    <time><begin value="0"/><end value="{episode_s}"/></time>
</configuration>
""")

    port = _find_free_port()
    sumo_cmd = [
        "sumo", "--configuration-file", str(cfg_path),
        "--step-length", "0.5",
        "--collision.action", "warn",
        "--time-to-teleport", "-1",
        "--no-warnings", "true",
    ]

    for attempt in range(5):
        try:
            proc = subprocess.Popen(
                sumo_cmd + ["--remote-port", str(port)],
                stdout=subprocess.DEVNULL, stderr=subprocess.PIPE,
            )
            time.sleep(1.0 + attempt * 0.5)
            traci.init(port=port, label=label)
            break
        except Exception:
            proc.kill()
            proc.wait()
            port = _find_free_port()
    else:
        raise RuntimeError(f"Failed to start SUMO for {label}")

    # Apply fixed VSL if requested
    mainline_ms = None if mainline_kph == "NC" else float(mainline_kph) / 3.6
    ramp_ms = None if ramp_kph == "NC" else float(ramp_kph) / 3.6

    if mainline_ms is not None:
        for seg in ("seg_2_before", "seg_1_before", "seg_0_before"):
            for li in range(3):
                traci.lane.setMaxSpeed(f"{seg}_{li}", mainline_ms)

    if ramp_ms is not None:
        traci.lane.setMaxSpeed("ramp_on_transition_0", ramp_ms)
        traci.lane.setMaxSpeed("ramp_on_approach_0", ramp_ms)

    conn = traci.getConnection(label)

    # Collect per-window data
    windows = []
    step_count = 0
    steps_per_window = int(agg_s / 0.5)

    # Vehicle tracking for route analysis
    arrived_routes = {"mainline_through": 0, "ramp_on_through": 0, "mainline_to_off": 0}
    ramp_vehs_entered = 0
    ramp_vehs_on_offramp = 0

    while conn.simulation.getMinExpectedNumber() > 0:
        conn.simulationStep()
        step_count += 1

        # Track departed ramp vehicles
        for vid in conn.simulation.getDepartedIDList():
            if conn.vehicle.getRouteID(vid) == "ramp_on_through":
                ramp_vehs_entered += 1

        # Track vehicles that ended up on off-ramp edges
        for vid in conn.simulation.getArrivedIDList():
            try:
                route_id = "unknown"
                # Can't query arrived vehicles; track via edge
            except Exception:
                pass

        if step_count % steps_per_window == 0:
            window_idx = step_count // steps_per_window
            sim_time = step_count * 0.5
            row = {"window": window_idx, "sim_time_s": sim_time}

            # E1 loop data
            for loop_id in E1_LOOPS:
                try:
                    spd = conn.inductionloop.getLastStepMeanSpeed(loop_id)
                    flow = conn.inductionloop.getLastStepVehicleNumber(loop_id)
                    occ = conn.inductionloop.getLastStepOccupancy(loop_id)
                    row[f"{loop_id}_speed_ms"] = round(spd, 2)
                    row[f"{loop_id}_flow"] = flow
                    row[f"{loop_id}_occ"] = round(occ, 3)
                except Exception:
                    row[f"{loop_id}_speed_ms"] = -1
                    row[f"{loop_id}_flow"] = -1
                    row[f"{loop_id}_occ"] = -1

            # Per-lane speeds at seg_0_after (the critical merge zone)
            for li in range(4):
                lane_id = f"seg_0_after_{li}"
                try:
                    vehs = conn.lane.getLastStepVehicleIDs(lane_id)
                    if vehs:
                        speeds = [conn.vehicle.getSpeed(v) for v in vehs]
                        row[f"s0a_L{li}_n_vehs"] = len(vehs)
                        row[f"s0a_L{li}_avg_spd_ms"] = round(sum(speeds) / len(speeds), 2)
                        row[f"s0a_L{li}_min_spd_ms"] = round(min(speeds), 2)
                    else:
                        row[f"s0a_L{li}_n_vehs"] = 0
                        row[f"s0a_L{li}_avg_spd_ms"] = -1
                        row[f"s0a_L{li}_min_spd_ms"] = -1
                except Exception:
                    row[f"s0a_L{li}_n_vehs"] = -1
                    row[f"s0a_L{li}_avg_spd_ms"] = -1
                    row[f"s0a_L{li}_min_spd_ms"] = -1

            # Off-ramp flow (vehicles on off-ramp edges right now)
            offramp_vehs = 0
            for eid in ("ramp_off_diverge", "ramp_off_transition", "ramp_off_departure"):
                try:
                    offramp_vehs += conn.edge.getLastStepVehicleNumber(eid)
                except Exception:
                    pass
            row["offramp_vehs"] = offramp_vehs

            # Total vehicles in network
            row["total_vehs"] = conn.vehicle.getIDCount()

            windows.append(row)

    conn.close()
    proc.wait()

    import shutil
    shutil.rmtree(tmp, ignore_errors=True)

    return {
        "label": label,
        "demand_vph": demand_vph,
        "mainline_kph": mainline_kph,
        "ramp_kph": ramp_kph,
        "windows": windows,
        "ramp_vehs_entered": ramp_vehs_entered,
    }


def main():
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    # Key scenarios: NC and best/worst VSL combos at critical demands
    scenarios = [
        # NC baseline at key demands
        (5500, "NC", "NC"),
        (6000, "NC", "NC"),
        (6500, "NC", "NC"),
        (6750, "NC", "NC"),
        (7000, "NC", "NC"),
        (7500, "NC", "NC"),
        # Best sigma combos from the sweep
        (6750, 70, 70),
        (7000, 60, 60),
        # Moderate VSL
        (6750, 95, 60),
        (7000, 90, 50),
    ]

    n = len(scenarios)
    for i, (demand, m_kph, r_kph) in enumerate(scenarios):
        label = f"D{demand}_M{m_kph}_R{r_kph}"
        print(f"[{i+1}/{n}] Running {label}...", end=" ", flush=True)
        t0 = time.time()

        result = run_diagnostic(demand, m_kph, r_kph)
        windows = result["windows"]

        # Write per-window CSV
        csv_path = RESULTS_DIR / f"{label}.csv"
        if windows:
            with open(csv_path, "w", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=windows[0].keys())
                writer.writeheader()
                writer.writerows(windows)

        elapsed = time.time() - t0
        n_win = len(windows)

        # Quick summary: seg_0_after lane 0 vs lanes 1-3 average speed
        l0_speeds = [w["s0a_L0_avg_spd_ms"] for w in windows if w["s0a_L0_avg_spd_ms"] > 0]
        l123_speeds = []
        for w in windows:
            for li in (1, 2, 3):
                v = w.get(f"s0a_L{li}_avg_spd_ms", -1)
                if v > 0:
                    l123_speeds.append(v)

        l0_avg = sum(l0_speeds) / len(l0_speeds) * 3.6 if l0_speeds else 0
        l123_avg = sum(l123_speeds) / len(l123_speeds) * 3.6 if l123_speeds else 0

        # Off-ramp usage
        offramp_peak = max((w["offramp_vehs"] for w in windows), default=0)

        print(f"done in {elapsed:.0f}s | {n_win} windows | "
              f"L0_avg={l0_avg:.1f}kph L1-3_avg={l123_avg:.1f}kph "
              f"offramp_peak={offramp_peak} "
              f"ramp_entered={result['ramp_vehs_entered']}")

    print(f"\nResults in {RESULTS_DIR}/")


if __name__ == "__main__":
    main()
