#!/usr/bin/env python3
"""
v5.2 feasibility sweep — validates the trainable demand band with the
new fleet (reckless outliers 4%) and per-lane differential VSL actions.

Clear weather only. Weather effects are disabled pending further study.

Grid:
  14 demand levels × (NC + 14 uniform + 10 differential) = 350 scenarios

Key questions:
  1. Did reckless outliers shift the breakdown/capacity boundary?
  2. Does per-lane differential VSL outperform uniform VSL?
  3. Is the 5500-7250 vph training band still valid?
"""
import argparse
import csv
import logging
import os
import socket
import subprocess
import sys
import tempfile
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

import numpy as np

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger("sweep_v52")

_PROJECT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_PROJECT))
os.chdir(_PROJECT)

_SUMO_HOME = os.environ.get("SUMO_HOME", "/usr/share/sumo")
sys.path.insert(0, os.path.join(_SUMO_HOME, "tools"))

from tests._sumo_helpers import NET_FILE, DET_FILE

# ── Sweep grid ──────────────────────────────────────────────────────────────

DEMANDS = [3000, 4500, 5000, 5500, 5750, 6000, 6250, 6500, 6750, 7000, 7250, 7500, 8000, 9000]

UNIFORM_MAINLINE = [80, 90, 95, 100, 105, 110, 115]
RAMP_LEVELS = [60, 80]

# Per-lane differential: (L0_merge, L1_mid, L2_fast)
DIFF_CONFIGS = {
    "funnel_strong":  (80, 90, 100),
    "funnel_mid":     (90, 100, 110),
    "funnel_mild":    (100, 105, 110),
    "merge_only":     (105, 110, 110),
    "moderate_flat":  (95, 100, 105),
}

EPISODE_S = 3600
AGG_TIME = 30
SIM_STEP = 1.0
CAV_PCT = 50.0
RAMP_FRAC = 0.25
SEED = 42

# ── E1 helpers ──────────────────────────────────────────────────────────────

_UPSTREAM_SEGS = ["seg_2_before", "seg_1_before", "seg_0_before"]
_LANE_COUNTS = {"seg_0_before": 3, "seg_0_after": 4, "seg_1_after": 3}


def _read_e1(conn, seg, suffix, n_lanes):
    total_flow, total_speed_w, total_occ = 0.0, 0.0, 0.0
    total_cnt = 0.0
    for li in range(n_lanes):
        det = f"flow_loop_{seg}_{li}_{suffix}"
        cnt = float(conn.inductionloop.getLastIntervalVehicleNumber(det))
        spd = max(0.0, float(conn.inductionloop.getLastIntervalMeanSpeed(det)))
        occ = float(conn.inductionloop.getLastIntervalOccupancy(det))
        flow = cnt * (3600.0 / AGG_TIME)
        total_flow += flow
        total_speed_w += spd * cnt
        total_cnt += cnt
        total_occ += occ
    avg_speed = (total_speed_w / max(total_cnt, 1.0)) * 3.6
    return total_flow, avg_speed, total_occ / max(n_lanes, 1)


def _read_e1_lane(conn, seg, suffix, lane_idx):
    det = f"flow_loop_{seg}_{lane_idx}_{suffix}"
    cnt = float(conn.inductionloop.getLastIntervalVehicleNumber(det))
    spd = max(0.0, float(conn.inductionloop.getLastIntervalMeanSpeed(det))) * 3.6
    occ = float(conn.inductionloop.getLastIntervalOccupancy(det))
    flow = cnt * (3600.0 / AGG_TIME)
    return flow, spd, occ


# ── Single scenario runner ──────────────────────────────────────────────────

def _run_scenario(task):
    """Run one scenario and return summary metrics."""
    import traci

    demand = task["demand"]
    label = task["label"]
    mainline_kph = task["mainline_kph"]
    ramp_kph = task["ramp_kph"]
    diff_name = task.get("diff_name", "")

    from traffic_environment.vehicle_fleet import generate_fleet_xml, pick_vehicle_type

    tmp_dir = Path(tempfile.mkdtemp(prefix=f"fsv52_{label[:20]}_"))
    rou_path = tmp_dir / "scenario.rou.xml"
    cfg_path = tmp_dir / "scenario.sumocfg"

    fleet_xml = generate_fleet_xml(seed=SEED, weather="clear")
    rng = np.random.RandomState(SEED + demand)

    total_veh = int(demand * EPISODE_S / 3600)
    n_mainline = int(total_veh * (1 - RAMP_FRAC))
    n_ramp = total_veh - n_mainline

    vehicles = []
    veh_id = 0

    def _add(count, route, t0, span):
        nonlocal veh_id
        if count <= 0:
            return
        step = span / count
        for i in range(count):
            dep = t0 + (i + 0.5) * step
            if dep > EPISODE_S:
                break
            is_cav = rng.random() * 100.0 < CAV_PCT
            vtype = pick_vehicle_type(rng, is_cav=is_cav)
            vehicles.append((dep, route, veh_id, vtype))
            veh_id += 1

    _add(n_mainline, "mainline_through", 0, EPISODE_S)
    _add(n_ramp, "ramp_on_through", 100, EPISODE_S - 100)
    vehicles.sort(key=lambda v: v[0])

    lines = ['<?xml version="1.0" encoding="UTF-8"?>', "<routes>", fleet_xml]
    lines.append('  <route id="mainline_through" edges="seg_3_before seg_2_before seg_1_before seg_0_before seg_0_after seg_1_after"/>')
    lines.append('  <route id="ramp_on_through" edges="ramp_on_approach ramp_on_transition ramp_on_merge seg_0_after seg_1_after"/>')
    for dep, route, vid, vtype in vehicles:
        lines.append(f'  <vehicle id="veh_{vid}" type="{vtype}" route="{route}" depart="{dep:.2f}" departPos="last" departLane="best" departSpeed="desired" insertionChecks="none"/>')
    lines.append("</routes>")
    rou_path.write_text("\n".join(lines))

    from tests._sumo_helpers import generate_sumocfg
    generate_sumocfg(cfg_path, rou_path, EPISODE_S)

    # Start SUMO
    with socket.socket() as s:
        s.bind(("", 0))
        port = s.getsockname()[1]

    proc = subprocess.Popen(
        ["sumo", "--configuration-file", str(cfg_path),
         "--step-length", str(SIM_STEP),
         "--step-method.ballistic",
         "--collision.action", "warn",
         "--time-to-teleport", "-1",
         "--no-warnings", "true",
         "--remote-port", str(port)],
        stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)

    for attempt in range(5):
        try:
            time.sleep(1.0 + attempt * 0.5)
            traci.init(port=port, numRetries=10, label=label)
            break
        except Exception:
            if attempt == 4:
                proc.kill()
                import shutil
                shutil.rmtree(tmp_dir, ignore_errors=True)
                return {"label": label, "demand": demand, "error": "SUMO_START_FAILED",
                        "diff_name": diff_name, "mainline_kph": str(mainline_kph),
                        "ramp_kph": str(ramp_kph), "avg_sigma": 0, "avg_ds_flow": 0,
                        "avg_ds_speed": 0, "brake_per_1kvs": 0, "hard_brake_per_1kvs": 0,
                        "L0_avg_speed": 0, "L1_avg_speed": 0, "L2_avg_speed": 0, "L0_L2_delta": 0}

    conn = traci.getConnection(label)

    # Apply VSL (static for entire episode)
    is_nc = mainline_kph is None

    if not is_nc:
        if isinstance(mainline_kph, tuple):
            for li, spd_kph in enumerate(mainline_kph):
                conn.lane.setMaxSpeed(f"seg_0_before_{li}", spd_kph / 3.6)
        else:
            conn.edge.setMaxSpeed("seg_0_before", mainline_kph / 3.6)

        if ramp_kph is not None:
            conn.edge.setMaxSpeed("ramp_on_transition", ramp_kph / 3.6)

    # Run simulation
    n_steps = EPISODE_S // AGG_TIME
    sigma_vals = []
    ds_flows = []
    ds_speeds = []
    lane_speeds = {f"L{i}": [] for i in range(3)}
    # Accel lane (seg_0_after L0) metrics
    accel_lane_speeds = []
    accel_lane_flows = []
    brake_count = 0
    hard_brake_count = 0
    total_veh_seconds = 0
    # Insertion backlog tracking
    total_loaded = 0
    total_departed = 0
    max_backlog = 0
    backlog_samples = []
    collision_count = 0

    for step in range(n_steps):
        for _ in range(AGG_TIME):
            conn.simulationStep()

            # Track insertion backlog
            total_loaded += int(conn.simulation.getLoadedNumber())
            total_departed += int(conn.simulation.getDepartedNumber())
            backlog = total_loaded - total_departed
            max_backlog = max(max_backlog, backlog)

            # Track collisions
            collision_count += int(conn.simulation.getCollidingVehiclesNumber())

            for vid in conn.vehicle.getIDList():
                edge = conn.vehicle.getRoadID(vid)
                if edge in _UPSTREAM_SEGS:
                    accel = conn.vehicle.getAcceleration(vid)
                    total_veh_seconds += 1
                    if accel < -2.5:
                        brake_count += 1
                    if accel < -4.0:
                        hard_brake_count += 1

        # Current backlog at this aggregation step
        backlog_samples.append(total_loaded - total_departed)

        # E1 readings
        speeds = []
        for seg in _UPSTREAM_SEGS:
            nl = _LANE_COUNTS.get(seg, 3)
            _, spd, _ = _read_e1(conn, seg, "exit", nl)
            speeds.append(spd)
        sigma_vals.append(float(np.std(speeds)))

        ds_flow, ds_speed, _ = _read_e1(conn, "seg_1_after", "exit", 3)
        ds_flows.append(ds_flow)
        ds_speeds.append(ds_speed)

        # Per-lane upstream (seg_0_before)
        for li in range(3):
            _, lspd, _ = _read_e1_lane(conn, "seg_0_before", "exit", li)
            lane_speeds[f"L{li}"].append(lspd)

        # Acceleration lane (seg_0_after L0) — the merge zone
        al_flow, al_spd, _ = _read_e1_lane(conn, "seg_0_after", "exit", 0)
        accel_lane_speeds.append(al_spd)
        accel_lane_flows.append(al_flow)

    conn.close()
    proc.wait()

    import shutil
    shutil.rmtree(tmp_dir, ignore_errors=True)

    kvs = max(total_veh_seconds / 1000.0, 0.001)
    l0_avg = float(np.mean(lane_speeds["L0"])) if lane_speeds["L0"] else 0
    l1_avg = float(np.mean(lane_speeds["L1"])) if lane_speeds["L1"] else 0
    l2_avg = float(np.mean(lane_speeds["L2"])) if lane_speeds["L2"] else 0
    al_spd_avg = float(np.mean(accel_lane_speeds)) if accel_lane_speeds else 0
    al_flow_avg = float(np.mean(accel_lane_flows)) if accel_lane_flows else 0
    avg_backlog = float(np.mean(backlog_samples)) if backlog_samples else 0
    end_backlog = backlog_samples[-1] if backlog_samples else 0

    return {
        "label": label,
        "demand": demand,
        "mainline_kph": str(mainline_kph) if mainline_kph else "NC",
        "ramp_kph": str(ramp_kph) if ramp_kph else "NC",
        "diff_name": diff_name,
        "avg_sigma": round(float(np.mean(sigma_vals)), 3),
        "avg_ds_flow": round(float(np.mean(ds_flows)), 1),
        "avg_ds_speed": round(float(np.mean(ds_speeds)), 1),
        "brake_per_1kvs": round(brake_count / kvs, 1),
        "hard_brake_per_1kvs": round(hard_brake_count / kvs, 1),
        "L0_avg_speed": round(l0_avg, 1),
        "L1_avg_speed": round(l1_avg, 1),
        "L2_avg_speed": round(l2_avg, 1),
        "L0_L2_delta": round(l0_avg - l2_avg, 1),
        # Insertion backlog
        "max_backlog": max_backlog,
        "avg_backlog": round(avg_backlog, 1),
        "end_backlog": end_backlog,
        # Acceleration lane (seg_0_after L0)
        "accel_lane_avg_speed": round(al_spd_avg, 1),
        "accel_lane_avg_flow": round(al_flow_avg, 1),
        # Collisions
        "collisions": collision_count,
        "error": "",
    }


# ── Main ────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="v5.2 feasibility sweep")
    parser.add_argument("--workers", type=int, default=20)
    args = parser.parse_args()

    tasks = []
    task_id = 0

    for d in DEMANDS:
        # NC
        tasks.append({
            "demand": d, "label": f"NC_{d}_t{task_id}",
            "mainline_kph": None, "ramp_kph": None, "diff_name": "NC",
        })
        task_id += 1

        # Uniform mainline × ramp
        for m in UNIFORM_MAINLINE:
            for r in RAMP_LEVELS:
                tasks.append({
                    "demand": d, "label": f"M{m}_R{r}_{d}_t{task_id}",
                    "mainline_kph": float(m), "ramp_kph": float(r),
                    "diff_name": f"uniform_M{m}",
                })
                task_id += 1

        # Differential per-lane × ramp
        for dname, (l0, l1, l2) in DIFF_CONFIGS.items():
            for r in RAMP_LEVELS:
                tasks.append({
                    "demand": d, "label": f"{dname}_R{r}_{d}_t{task_id}",
                    "mainline_kph": (float(l0), float(l1), float(l2)),
                    "ramp_kph": float(r), "diff_name": dname,
                })
                task_id += 1

    timestamp = time.strftime("%d-%m-%Y_%H-%M-%S")
    out_dir = _PROJECT / "tests" / "results" / f"feasibility_v52_{timestamp}"
    out_dir.mkdir(parents=True, exist_ok=True)

    print(f"v5.2 Feasibility sweep — new fleet + per-lane differential VSL")
    print(f"  {len(tasks)} scenarios on {args.workers} workers")
    print(f"  Demands: {DEMANDS[0]}-{DEMANDS[-1]} vph ({len(DEMANDS)} levels)")
    print(f"  Uniform: {len(UNIFORM_MAINLINE)} levels × {len(RAMP_LEVELS)} ramp")
    print(f"  Diff:    {len(DIFF_CONFIGS)} configs × {len(RAMP_LEVELS)} ramp")
    print(f"  Fleet:   96% normal HDV + 4% reckless + 50% CAV")
    print(f"  Output:  {out_dir}")
    print()

    results = []
    t0 = time.time()

    with ProcessPoolExecutor(max_workers=args.workers) as pool:
        futures = {pool.submit(_run_scenario, t): t for t in tasks}
        done = 0
        for future in as_completed(futures):
            done += 1
            try:
                r = future.result()
                results.append(r)
                err = r.get("error", "")
                if err:
                    status = f"FAILED: {err}"
                else:
                    status = f"σ={r['avg_sigma']:>5.2f} flow={r['avg_ds_flow']:>5.0f} brk={r['brake_per_1kvs']:>4.0f} bklog={r['max_backlog']:>4} col={r['collisions']:>2}"
                elapsed = int(time.time() - t0)
                pct = done / len(tasks) * 100
                remaining = len(tasks) - done
                eta = int(elapsed / max(done, 1) * remaining / 60)
                bar_len = 40
                filled = int(bar_len * done / len(tasks))
                bar = "█" * filled + "░" * (bar_len - filled)
                print(f"  |{bar}| {pct:5.1f}% [{done:>4}/{len(tasks)}] "
                      f"{r.get('diff_name',''):>15}@{r['demand']:>5}vph {status} "
                      f"[{elapsed}s, ~{eta}m left]")
            except Exception as e:
                print(f"  ERROR: {e}")
                done += 1

    # Write CSV
    csv_path = out_dir / "summary.csv"
    if results:
        keys = ["demand", "diff_name", "mainline_kph", "ramp_kph",
                "avg_sigma", "avg_ds_flow", "avg_ds_speed",
                "brake_per_1kvs", "hard_brake_per_1kvs",
                "L0_avg_speed", "L1_avg_speed", "L2_avg_speed", "L0_L2_delta",
                "max_backlog", "avg_backlog", "end_backlog",
                "accel_lane_avg_speed", "accel_lane_avg_flow",
                "collisions", "error"]
        with open(csv_path, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=keys, extrasaction="ignore")
            w.writeheader()
            for r in sorted(results, key=lambda x: (x["demand"], x["diff_name"], str(x["mainline_kph"]))):
                w.writerow(r)

    elapsed = int(time.time() - t0)
    print(f"\nDone: {len(results)} scenarios in {elapsed}s → {csv_path}")


if __name__ == "__main__":
    main()
