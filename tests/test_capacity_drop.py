#!/usr/bin/env python3
"""
Test: Can the ramps_v2 topology produce capacity drop?

Capacity drop = discontinuous throughput reduction (5-18%) once queues
form at a merge bottleneck, with hysteresis preventing recovery until
demand drops well below the breakdown threshold.

This test sweeps mainline demand from 4000 to 9000 vph (ramp at 20%)
and measures the downstream discharge rate at seg_0_after. If capacity
drop exists, the flow-density plot will show two branches:
  - Free-flow branch: flow increases linearly with density
  - Congested branch: flow drops below the free-flow peak and stays low

We test 3 vehicle type configurations:
  1. Current defaults (sigma=0.5, tau=1.0)
  2. Calibrated for capacity drop (sigma=0.7, tau=1.1, heterogeneous types)
  3. Aggressive capacity drop (sigma=0.8, tau=1.2, low lcCooperative)

Literature reference values (Chung et al. 2007):
  - 3-lane merge: capacity ~6000-6600 vph, drop = 8-15%
  - Critical density: 30-55 veh/km/lane
  - Hysteresis gap: 5-15% between breakdown and recovery flows

Usage:
  python tests/test_capacity_drop.py
  python tests/test_capacity_drop.py --workers 20
"""
import argparse
import csv
import os
import socket
import subprocess
import sys
import tempfile
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

import numpy as np

_PROJECT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_PROJECT))
os.chdir(_PROJECT)

_SUMO_HOME = os.environ.get("SUMO_HOME", "/usr/share/sumo")
sys.path.insert(0, os.path.join(_SUMO_HOME, "tools"))

from tests._sumo_helpers import NET_FILE, DET_FILE, generate_sumocfg

# ── Vehicle type configurations ──────────────────────────────────────────────

VTYPES_DEFAULT = """
<vType id="car" carFollowModel="Krauss" length="5.0" minGap="2.5"
       maxSpeed="33.33" accel="2.6" decel="4.5" sigma="0.5" tau="1.0"
       speedFactor="1.0" laneChangeModel="LC2013"/>
"""

VTYPES_CALIBRATED = """
<vType id="car_normal" carFollowModel="Krauss" length="5.0" minGap="2.5"
       maxSpeed="33.33" accel="2.6" decel="4.5" sigma="0.7" tau="1.1"
       speedFactor="normc(1.0,0.10,0.85,1.15)"
       laneChangeModel="LC2013" lcStrategic="3.0" lcCooperative="0.8"
       lcSpeedGain="1.5" lcAssertive="1.5"/>
<vType id="car_aggressive" carFollowModel="Krauss" length="5.0" minGap="2.0"
       maxSpeed="36.11" accel="3.0" decel="5.0" sigma="0.8" tau="0.9"
       speedFactor="normc(1.05,0.08,0.90,1.20)"
       laneChangeModel="LC2013" lcStrategic="4.0" lcCooperative="0.5"
       lcSpeedGain="2.5" lcAssertive="3.0"/>
<vType id="car_timid" carFollowModel="Krauss" length="5.0" minGap="3.0"
       maxSpeed="30.56" accel="2.2" decel="4.0" sigma="0.6" tau="1.4"
       speedFactor="normc(0.95,0.05,0.85,1.05)"
       laneChangeModel="LC2013" lcStrategic="2.0" lcCooperative="1.0"
       lcSpeedGain="0.8" lcAssertive="1.0"/>
<vType id="truck" vClass="truck" carFollowModel="Krauss" length="12.0" minGap="3.0"
       maxSpeed="25.0" accel="1.3" decel="4.0" sigma="0.5" tau="1.5"
       speedFactor="normc(0.85,0.05,0.75,0.95)"
       laneChangeModel="LC2013" lcStrategic="2.0" lcCooperative="0.9"
       lcSpeedGain="0.5" lcKeepRight="2.0"/>
"""

VTYPES_AGGRESSIVE = """
<vType id="car_normal" carFollowModel="Krauss" length="5.0" minGap="2.5"
       maxSpeed="33.33" accel="2.6" decel="4.5" sigma="0.8" tau="1.2"
       speedFactor="normc(1.0,0.12,0.80,1.20)"
       laneChangeModel="LC2013" lcStrategic="3.0" lcCooperative="0.5"
       lcSpeedGain="2.0" lcAssertive="2.0"/>
<vType id="car_aggressive" carFollowModel="Krauss" length="5.0" minGap="2.0"
       maxSpeed="36.11" accel="3.0" decel="5.0" sigma="0.9" tau="0.8"
       speedFactor="normc(1.08,0.10,0.90,1.25)"
       laneChangeModel="LC2013" lcStrategic="4.0" lcCooperative="0.3"
       lcSpeedGain="3.0" lcAssertive="4.0"/>
<vType id="car_timid" carFollowModel="Krauss" length="5.0" minGap="3.5"
       maxSpeed="27.78" accel="2.0" decel="3.5" sigma="0.6" tau="1.6"
       speedFactor="normc(0.90,0.05,0.80,1.00)"
       laneChangeModel="LC2013" lcStrategic="1.5" lcCooperative="1.0"
       lcSpeedGain="0.5" lcAssertive="0.8"/>
<vType id="truck" vClass="truck" carFollowModel="Krauss" length="12.0" minGap="3.5"
       maxSpeed="22.22" accel="1.0" decel="3.5" sigma="0.5" tau="1.8"
       speedFactor="normc(0.80,0.05,0.70,0.90)"
       laneChangeModel="LC2013" lcStrategic="2.0" lcCooperative="0.8"
       lcSpeedGain="0.3" lcKeepRight="2.5"/>
"""

VTYPE_CONFIGS = {
    "default": VTYPES_DEFAULT,
    "calibrated": VTYPES_CALIBRATED,
    "aggressive": VTYPES_AGGRESSIVE,
}

# Vehicle type distribution for heterogeneous configs
VTYPE_DIST = {
    "default": [("car", 1.0)],
    "calibrated": [("car_normal", 0.60), ("car_aggressive", 0.15),
                   ("car_timid", 0.15), ("truck", 0.10)],
    "aggressive": [("car_normal", 0.55), ("car_aggressive", 0.15),
                   ("car_timid", 0.15), ("truck", 0.15)],
}


def _generate_route_file(path, demand_vph, duration_s, ramp_frac, vtype_config, seed):
    """Generate routes with specified vehicle types and demand."""
    rng = np.random.RandomState(seed)
    mainline_rate = demand_vph * (1 - ramp_frac) / 3600.0
    ramp_rate = demand_vph * ramp_frac / 3600.0
    dist = VTYPE_DIST[vtype_config]

    lines = ['<routes>']
    lines.append(VTYPE_CONFIGS[vtype_config])
    lines.append('  <route id="mainline" edges="seg_3_before seg_2_before seg_1_before seg_0_before seg_0_after seg_1_after"/>')
    lines.append('  <route id="ramp_route" edges="ramp_on_approach ramp_on_transition ramp_on_merge seg_0_after seg_1_after"/>')

    veh_id = 0
    for t in range(duration_s):
        # Mainline departures
        n_main = rng.poisson(mainline_rate)
        for _ in range(n_main):
            # Pick vehicle type
            r = rng.random()
            cum = 0
            vtype = dist[0][0]
            for vt, prob in dist:
                cum += prob
                if r < cum:
                    vtype = vt
                    break
            lines.append(f'  <vehicle id="m{veh_id}" type="{vtype}" route="mainline" '
                         f'depart="{t}" departLane="best" departSpeed="max"/>')
            veh_id += 1

        # Ramp departures
        n_ramp = rng.poisson(ramp_rate)
        for _ in range(n_ramp):
            r = rng.random()
            cum = 0
            vtype = dist[0][0]
            for vt, prob in dist:
                cum += prob
                if r < cum:
                    vtype = vt
                    break
            lines.append(f'  <vehicle id="r{veh_id}" type="{vtype}" route="ramp_route" '
                         f'depart="{t}" departLane="0" departSpeed="max"/>')
            veh_id += 1

    lines.append('</routes>')
    with open(path, 'w') as f:
        f.write('\n'.join(lines))
    return veh_id


def _run_scenario(demand_vph, vtype_config, ramp_frac, duration_s, seed):
    """Run one SUMO scenario and return flow/speed/density measurements."""
    import traci

    tmp = Path(tempfile.mkdtemp(prefix=f"captest_{vtype_config}_{demand_vph}_"))
    rou = tmp / "test.rou.xml"
    cfg = tmp / "test.sumocfg"

    _generate_route_file(rou, demand_vph, duration_s, ramp_frac, vtype_config, seed)
    generate_sumocfg(cfg, rou, duration_s)

    # Find free port
    with socket.socket() as s:
        s.bind(('', 0))
        port = s.getsockname()[1]

    proc = subprocess.Popen(
        ['sumo', '--configuration-file', str(cfg),
         '--step-length', '0.5',
         '--collision.action', 'warn',
         '--collision.check-junctions', 'true',
         '--time-to-teleport', '300',
         '--no-warnings', 'true',
         '--remote-port', str(port)],
        stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)

    for attempt in range(5):
        try:
            time.sleep(1.0 + attempt)
            label = f"cap_{vtype_config}_{demand_vph}_{seed}"
            traci.init(port=port, numRetries=10, label=label)
            break
        except Exception:
            if attempt == 4:
                proc.kill()
                import shutil
                shutil.rmtree(tmp, ignore_errors=True)
                return None

    conn = traci.getConnection(label)

    # Measurement: collect 60s aggregated flow/speed at downstream (seg_0_after)
    agg_interval = 60  # seconds
    step_length = 0.5
    steps_per_agg = int(agg_interval / step_length)

    records = []
    step = 0
    window_flows = {f"seg_0_after_{i}": 0 for i in range(3)}
    window_speeds = {f"seg_0_after_{i}": [] for i in range(3)}
    window_densities = []

    try:
        while conn.simulation.getMinExpectedNumber() > 0:
            conn.simulationStep()
            step += 1
            sim_time = step * step_length

            # Count vehicles passing downstream detectors
            for lane_idx in range(3):
                det_id = f"flow_loop_seg_0_after_{lane_idx}_exit"
                try:
                    cnt = conn.inductionloop.getLastStepVehicleNumber(det_id)
                    spd = conn.inductionloop.getLastStepMeanSpeed(det_id)
                    window_flows[f"seg_0_after_{lane_idx}"] += cnt
                    if spd > 0:
                        window_speeds[f"seg_0_after_{lane_idx}"].append(spd)
                except Exception:
                    pass

            # Collect density on seg_0_after
            try:
                n_vehs = conn.edge.getLastStepVehicleNumber("seg_0_after")
                edge_len_km = 0.5  # 500m
                density = n_vehs / (edge_len_km * 3)  # veh/km/lane
                window_densities.append(density)
            except Exception:
                pass

            # Aggregate every interval
            if step % steps_per_agg == 0 and sim_time >= 120:  # skip warmup
                total_flow = sum(window_flows.values()) * (3600 / agg_interval)
                lane_speeds = []
                for lane_idx in range(3):
                    spds = window_speeds[f"seg_0_after_{lane_idx}"]
                    lane_speeds.append(np.mean(spds) * 3.6 if spds else 0)
                avg_speed = np.mean(lane_speeds) if lane_speeds else 0
                avg_density = np.mean(window_densities) if window_densities else 0

                records.append({
                    "sim_time_s": sim_time,
                    "demand_vph": demand_vph,
                    "vtype_config": vtype_config,
                    "ds_flow_vph": total_flow,
                    "ds_speed_kph": avg_speed,
                    "ds_density_vkl": avg_density,
                    "n_vehs": conn.vehicle.getIDCount(),
                })

                # Reset window
                for k in window_flows:
                    window_flows[k] = 0
                for k in window_speeds:
                    window_speeds[k] = []
                window_densities = []

    finally:
        conn.close()
        proc.wait()

    import shutil
    shutil.rmtree(tmp, ignore_errors=True)

    if not records:
        return None

    # Summary
    # Use last 2/3 of episode for steady-state measurement
    n_warmup = len(records) // 3
    steady = records[n_warmup:]

    flows = [r["ds_flow_vph"] for r in steady]
    speeds = [r["ds_speed_kph"] for r in steady]
    densities = [r["ds_density_vkl"] for r in steady]

    peak_flow = max(flows) if flows else 0
    avg_flow = np.mean(flows) if flows else 0
    min_speed = min(speeds) if speeds else 0
    avg_speed = np.mean(speeds) if speeds else 0
    avg_density = np.mean(densities) if densities else 0

    # Detect breakdown: sustained speed < 80 kph for >= 3 consecutive windows
    breakdown = False
    consec_slow = 0
    for r in steady:
        if r["ds_speed_kph"] < 80:
            consec_slow += 1
            if consec_slow >= 3:
                breakdown = True
        else:
            consec_slow = 0

    return {
        "demand_vph": demand_vph,
        "vtype_config": vtype_config,
        "ramp_frac": ramp_frac,
        "avg_flow_vph": round(avg_flow, 1),
        "peak_flow_vph": round(peak_flow, 1),
        "avg_speed_kph": round(avg_speed, 1),
        "min_speed_kph": round(min_speed, 1),
        "avg_density_vkl": round(avg_density, 1),
        "breakdown": breakdown,
        "n_records": len(records),
    }


def main():
    parser = argparse.ArgumentParser(description="Test capacity drop at ramps_v2 merge")
    parser.add_argument("--workers", type=int, default=20)
    parser.add_argument("--duration", type=int, default=1800, help="Episode duration (s)")
    parser.add_argument("--ramp-frac", type=float, default=0.20)
    args = parser.parse_args()

    demands = list(range(4000, 9500, 500))
    configs = ["default", "calibrated", "aggressive"]
    duration = args.duration
    ramp_frac = args.ramp_frac

    tasks = []
    for cfg in configs:
        for d in demands:
            tasks.append((d, cfg, ramp_frac, duration, 42))

    n_total = len(tasks)
    print(f"Capacity drop test — {n_total} scenarios on {args.workers} workers")
    print(f"  Demands: {demands[0]}-{demands[-1]} vph ({len(demands)} levels)")
    print(f"  Configs: {configs}")
    print(f"  Duration: {duration}s, ramp fraction: {ramp_frac}")
    print(flush=True)

    results = []
    completed = 0
    t0 = time.time()

    with ProcessPoolExecutor(max_workers=args.workers) as pool:
        futures = {pool.submit(_run_scenario, *t): t for t in tasks}
        for future in as_completed(futures):
            completed += 1
            task = futures[future]
            try:
                r = future.result()
                if r:
                    results.append(r)
                    bkdn = "BREAKDOWN" if r["breakdown"] else ""
                    elapsed = time.time() - t0
                    print(f"  [{completed:>3}/{n_total}] {r['vtype_config']:>12} {r['demand_vph']:>5}vph: "
                          f"flow={r['avg_flow_vph']:>6.0f} speed={r['avg_speed_kph']:>5.1f} "
                          f"density={r['avg_density_vkl']:>5.1f} {bkdn} [{elapsed:.0f}s]",
                          flush=True)
            except Exception as e:
                print(f"  [{completed:>3}/{n_total}] FAILED {task[:2]}: {e}", flush=True)

    # Save results
    out_dir = _PROJECT / "tests" / "results" / f"capacity_drop_test_{time.strftime('%d-%m-%Y_%H-%M-%S')}"
    out_dir.mkdir(parents=True, exist_ok=True)
    csv_path = out_dir / "capacity_drop_results.csv"

    if results:
        with open(csv_path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=results[0].keys())
            writer.writeheader()
            writer.writerows(sorted(results, key=lambda x: (x["vtype_config"], x["demand_vph"])))

    # Print summary table
    print()
    print("=" * 100)
    print("CAPACITY DROP ANALYSIS")
    print("=" * 100)

    for cfg in configs:
        cfg_results = sorted([r for r in results if r["vtype_config"] == cfg],
                             key=lambda x: x["demand_vph"])
        if not cfg_results:
            continue

        print(f"\n--- {cfg} ---")
        print(f"{'Demand':>7} | {'Avg Flow':>8} {'Peak Flow':>9} | {'Avg Spd':>7} {'Min Spd':>7} | "
              f"{'Density':>7} | {'Breakdown':>9}")
        print("-" * 80)

        peak_throughput = 0
        for r in cfg_results:
            bkdn = "YES" if r["breakdown"] else ""
            peak_throughput = max(peak_throughput, r["avg_flow_vph"])
            print(f"{r['demand_vph']:>7} | {r['avg_flow_vph']:>8.0f} {r['peak_flow_vph']:>9.0f} | "
                  f"{r['avg_speed_kph']:>7.1f} {r['min_speed_kph']:>7.1f} | "
                  f"{r['avg_density_vkl']:>7.1f} | {bkdn:>9}")

        # Find breakdown point and capacity drop
        breakdown_demand = None
        pre_breakdown_flow = None
        post_breakdown_flow = None
        for i, r in enumerate(cfg_results):
            if r["breakdown"] and breakdown_demand is None:
                breakdown_demand = r["demand_vph"]
                post_breakdown_flow = r["avg_flow_vph"]
                if i > 0:
                    pre_breakdown_flow = cfg_results[i - 1]["avg_flow_vph"]

        if breakdown_demand and pre_breakdown_flow:
            drop_pct = (pre_breakdown_flow - post_breakdown_flow) / pre_breakdown_flow * 100
            print(f"\n  Breakdown at: {breakdown_demand} vph demand")
            print(f"  Pre-breakdown flow: {pre_breakdown_flow:.0f} vph")
            print(f"  Post-breakdown flow: {post_breakdown_flow:.0f} vph")
            print(f"  Capacity drop: {drop_pct:.1f}%")
            print(f"  Peak throughput: {peak_throughput:.0f} vph")
        else:
            print(f"\n  No breakdown detected up to {demands[-1]} vph")
            print(f"  Peak throughput: {peak_throughput:.0f} vph")

    print(f"\nResults saved to: {csv_path}")


if __name__ == "__main__":
    main()
