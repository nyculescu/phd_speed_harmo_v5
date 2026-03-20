#!/usr/bin/env python3
"""
Phase 3 Validation: confirm the v5.1 per-lane + stochastic demand problem
is NOT trivially solvable by a static policy.

Tests:
  1. Stochastic demand creates meaningful return variance across episodes
  2. Per-lane differential control produces different outcomes than uniform
  3. Anomaly episodes have measurably different returns
  4. Static M110 is no longer universally optimal

Runs N_SEEDS episodes for each strategy, each with a different stochastic
demand profile (and 15% anomaly rate).
"""
from __future__ import annotations

import csv
import os
import socket
import subprocess
import sys
import tempfile
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path

import numpy as np

# --- path setup ---
_PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_PROJECT))
os.chdir(_PROJECT)

_SUMO_HOME = os.environ.get("SUMO_HOME", "/usr/share/sumo")
sys.path.insert(0, os.path.join(_SUMO_HOME, "tools"))

from tests._sumo_helpers import (
    NET_FILE, DET_FILE, RESULTS_ROOT,
    generate_stochastic_route_file, generate_sumocfg,
)
from traffic_environment.stochastic_demand import generate_demand_profile
from traffic_environment.anomaly_injector import AnomalyInjector

# --- constants ---
N_SEEDS = 30          # episodes per strategy
N_WORKERS = 20
EPISODE_S = 3600
AGG_TIME = 30
CAV_PCT = 50.0
MAX_STEPS = EPISODE_S // AGG_TIME  # 120

# E1 detector reading helper
_DET_POS = "exit"

# Strategies to test: (name, per-lane L0/L1/L2, ramp, description)
STRATEGIES = [
    ("NC",           None,                        None, "No control"),
    ("M110_uniform", [110, 110, 110],             70,   "Uniform 110 kph (old optimal)"),
    ("M100_uniform", [100, 100, 100],             60,   "Uniform 100 kph"),
    ("M90_uniform",  [90, 90, 90],                60,   "Uniform 90 kph"),
    ("diff_funnel",  [110, 100, 90],              60,   "Funnel: slow L2, keep L0 fast"),
    ("diff_merge",   [85, 95, 110],               60,   "Merge-assist: slow L0, fast L2"),
    ("diff_equal",   [95, 95, 95],                65,   "Equal 95 kph (moderate)"),
    ("diff_extreme", [80, 100, 120],              50,   "Extreme differential"),
    ("diff_mild",    [105, 110, 115],             70,   "Mild differential"),
]


def _run_episode(strategy_name, lanes, ramp_kph, seed):
    """Run one episode with stochastic demand + anomaly injection."""
    import traci

    tmp = Path(tempfile.mkdtemp(prefix=f"p3_{strategy_name}_{seed}_"))
    try:
        # Generate stochastic demand
        profile = generate_demand_profile(episode_duration_s=EPISODE_S, seed=seed)

        # Generate route file from profile
        rou = tmp / "ep.rou.xml"
        cfg = tmp / "ep.sumocfg"
        generate_stochastic_route_file(rou, profile, cav_pct=CAV_PCT, seed=seed + 10000)
        generate_sumocfg(cfg, rou, EPISODE_S)

        # Anomaly injector (same seed for reproducibility)
        anomaly = AnomalyInjector(
            episode_duration_s=EPISODE_S,
            anomaly_prob=0.15,
            seed=seed + 20000,
        )

        # Start SUMO
        with socket.socket() as s:
            s.bind(("", 0))
            port = s.getsockname()[1]

        label = f"p3_{strategy_name}_{seed}"
        proc = subprocess.Popen(
            ["sumo", "--configuration-file", str(cfg),
             "--step-length", "1.0", "--collision.action", "warn",
             "--time-to-teleport", "-1", "--no-warnings", "true",
             "--remote-port", str(port)],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
        time.sleep(1.0)

        for attempt in range(5):
            try:
                traci.init(port=port, label=label)
                break
            except Exception:
                time.sleep(1.0)
        else:
            proc.kill()
            return None

        conn = traci.getConnection(label)

        # Metrics accumulators
        total_reward_proxy = 0.0
        per_step_sigma = []
        per_step_flow = []
        per_step_l0_speed = []
        per_step_l2_speed = []
        tts_total = 0.0
        brake_count = 0
        veh_seconds = 0

        _KPH_TO_MS = 1.0 / 3.6
        duration = float(AGG_TIME)

        for step_idx in range(MAX_STEPS):
            # Advance SUMO for AGG_TIME seconds
            for sim_step in range(AGG_TIME):
                conn.simulationStep()
                sim_t = step_idx * AGG_TIME + sim_step

                # Anomaly injection
                anomaly.step(float(sim_t), conn)

                # Apply CAV slowDown (if not NC)
                if lanes is not None:
                    for veh_id in conn.vehicle.getIDList():
                        try:
                            vtype = conn.vehicle.getTypeID(veh_id)
                        except Exception:
                            continue
                        if "cav" not in vtype.lower():
                            continue
                        try:
                            edge = conn.vehicle.getRoadID(veh_id)
                        except Exception:
                            continue

                        if edge == "seg_0_before":
                            try:
                                li = conn.vehicle.getLaneIndex(veh_id)
                                limit = lanes[li] * _KPH_TO_MS if li < 3 else lanes[0] * _KPH_TO_MS
                            except Exception:
                                limit = lanes[0] * _KPH_TO_MS
                        elif edge in ("seg_1_before", "seg_2_before"):
                            limit = min(lanes) * _KPH_TO_MS
                        elif edge in ("ramp_on_approach", "ramp_on_transition"):
                            limit = (ramp_kph or 90) * _KPH_TO_MS
                        else:
                            continue
                        try:
                            conn.vehicle.slowDown(veh_id, limit, duration)
                        except Exception:
                            pass

                # Track braking
                for veh_id in conn.vehicle.getIDList():
                    try:
                        edge = conn.vehicle.getRoadID(veh_id)
                        if edge in ("seg_0_before", "seg_1_before", "seg_2_before"):
                            accel = conn.vehicle.getAcceleration(veh_id)
                            veh_seconds += 1
                            if accel < -2.0:
                                brake_count += 1
                    except Exception:
                        pass

            # Collect E1 metrics
            speeds_upstream = []
            for seg in ("seg_2_before", "seg_1_before", "seg_0_before"):
                total_cnt, weighted_spd = 0.0, 0.0
                for li in range(3):
                    det = f"flow_loop_{seg}_{li}_{_DET_POS}"
                    try:
                        cnt = float(conn.inductionloop.getLastIntervalVehicleNumber(det))
                        spd = max(0.0, float(conn.inductionloop.getLastIntervalMeanSpeed(det)))
                        total_cnt += cnt
                        weighted_spd += cnt * spd
                    except Exception:
                        pass
                avg_spd = (weighted_spd / total_cnt * 3.6) if total_cnt > 0 else 0
                speeds_upstream.append(avg_spd)

            sigma = float(np.std(speeds_upstream)) if len(speeds_upstream) == 3 else 0
            per_step_sigma.append(sigma)

            # Downstream flow
            ds_flow = 0.0
            for li in range(3):
                det = f"flow_loop_seg_1_after_{li}_{_DET_POS}"
                try:
                    cnt = float(conn.inductionloop.getLastIntervalVehicleNumber(det))
                    ds_flow += cnt * (3600.0 / AGG_TIME)
                except Exception:
                    pass
            per_step_flow.append(ds_flow)

            # Per-lane speeds at seg_0_before
            for li, arr in [(0, per_step_l0_speed), (2, per_step_l2_speed)]:
                det = f"flow_loop_seg_0_before_{li}_{_DET_POS}"
                try:
                    spd = max(0.0, float(conn.inductionloop.getLastIntervalMeanSpeed(det))) * 3.6
                except Exception:
                    spd = 0
                arr.append(spd)

            # TTS
            try:
                n_veh = float(conn.vehicle.getIDCount())
            except Exception:
                n_veh = 0
            tts_total += n_veh * AGG_TIME

            # Simple reward proxy: -sigma - 0.001 * max(0, 6000 - ds_flow)
            r = -sigma - 0.001 * max(0, 6000 - ds_flow)
            total_reward_proxy += r

        conn.close()
        proc.wait(timeout=10)

        return {
            "strategy": strategy_name,
            "seed": seed,
            "peak_demand_vph": profile.peak_demand_vph,
            "ramp_fraction": profile.ramp_fraction,
            "anomaly": anomaly.event.anomaly_type if anomaly.has_anomaly else "none",
            "anomaly_start": anomaly.event.start_time_s if anomaly.has_anomaly else 0,
            "reward_proxy": total_reward_proxy,
            "avg_sigma": float(np.mean(per_step_sigma)),
            "std_sigma": float(np.std(per_step_sigma)),
            "avg_ds_flow": float(np.mean(per_step_flow)),
            "tts_hours": tts_total / 3600.0,
            "brake_rate_per_1kvs": brake_count / max(veh_seconds, 1) * 1000,
            "avg_l0_speed": float(np.mean(per_step_l0_speed)) if per_step_l0_speed else 0,
            "avg_l2_speed": float(np.mean(per_step_l2_speed)) if per_step_l2_speed else 0,
            "l0_l2_delta": float(np.mean(per_step_l0_speed)) - float(np.mean(per_step_l2_speed)) if per_step_l0_speed else 0,
        }

    except Exception as e:
        return {"strategy": strategy_name, "seed": seed, "error": str(e)}
    finally:
        try:
            import shutil
            shutil.rmtree(tmp, ignore_errors=True)
        except Exception:
            pass


def main():
    timestamp = datetime.now().strftime("%d-%m-%Y_%H-%M-%S")
    out_dir = RESULTS_ROOT / f"phase3_validation_{timestamp}"
    out_dir.mkdir(parents=True, exist_ok=True)

    # Build task list
    tasks = []
    for strat_name, lanes, ramp, desc in STRATEGIES:
        for seed in range(N_SEEDS):
            tasks.append((strat_name, lanes, ramp, seed))

    total = len(tasks)
    print(f"Phase 3 Validation — {len(STRATEGIES)} strategies × {N_SEEDS} seeds = {total} episodes")
    print(f"  Workers: {N_WORKERS}")
    print(f"  Output: {out_dir}")
    print()

    results = []
    done = 0

    with ProcessPoolExecutor(max_workers=N_WORKERS) as pool:
        futures = {
            pool.submit(_run_episode, sn, ln, rp, sd): (sn, sd)
            for sn, ln, rp, sd in tasks
        }

        for future in as_completed(futures):
            done += 1
            sn, sd = futures[future]
            try:
                r = future.result()
                if r and "error" not in r:
                    results.append(r)
                    pct = done / total * 100
                    bar = "█" * int(pct / 2.5) + "░" * (40 - int(pct / 2.5))
                    print(f"  |{bar}| {pct:5.1f}% [{done:>4}/{total}] "
                          f"{r['strategy']:>15s} seed={r['seed']:>2} "
                          f"σ={r['avg_sigma']:>5.2f} flow={r['avg_ds_flow']:>6.0f} "
                          f"r={r['reward_proxy']:>+7.1f} "
                          f"anom={r['anomaly']:>5s}")
                else:
                    err = r.get("error", "unknown") if r else "None returned"
                    print(f"  FAILED {sn} seed={sd}: {err}")
            except Exception as e:
                print(f"  EXCEPTION {sn} seed={sd}: {e}")

    # Write CSV
    if results:
        csv_path = out_dir / "validation_results.csv"
        fields = list(results[0].keys())
        with open(csv_path, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=fields)
            w.writeheader()
            w.writerows(sorted(results, key=lambda r: (r["strategy"], r["seed"])))
        print(f"\n  Results written to {csv_path}")

    # Print summary
    print("\n" + "=" * 100)
    print("SUMMARY")
    print("=" * 100)
    print(f"{'Strategy':>15s} | {'avg_σ':>6s} {'std_σ':>6s} | {'avg_flow':>8s} | "
          f"{'avg_reward':>10s} {'std_reward':>10s} | {'brk_rate':>8s} | "
          f"{'L0_spd':>6s} {'L2_spd':>6s} {'L0-L2':>5s} | {'n_anom':>5s}")
    print("-" * 100)

    for strat_name, _, _, desc in STRATEGIES:
        strat_results = [r for r in results if r["strategy"] == strat_name and "error" not in r]
        if not strat_results:
            print(f"{strat_name:>15s} | (no results)")
            continue

        sigmas = [r["avg_sigma"] for r in strat_results]
        flows = [r["avg_ds_flow"] for r in strat_results]
        rewards = [r["reward_proxy"] for r in strat_results]
        brakes = [r["brake_rate_per_1kvs"] for r in strat_results]
        l0s = [r["avg_l0_speed"] for r in strat_results]
        l2s = [r["avg_l2_speed"] for r in strat_results]
        deltas = [r["l0_l2_delta"] for r in strat_results]
        n_anom = sum(1 for r in strat_results if r["anomaly"] != "none")

        print(f"{strat_name:>15s} | {np.mean(sigmas):>6.2f} {np.std(sigmas):>6.2f} | "
              f"{np.mean(flows):>8.0f} | {np.mean(rewards):>+10.1f} {np.std(rewards):>10.1f} | "
              f"{np.mean(brakes):>8.1f} | {np.mean(l0s):>6.1f} {np.mean(l2s):>6.1f} "
              f"{np.mean(deltas):>+5.1f} | {n_anom:>5}")

    # Anomaly vs no-anomaly comparison
    print("\n" + "=" * 100)
    print("ANOMALY vs NO-ANOMALY RETURN COMPARISON")
    print("=" * 100)
    for strat_name, _, _, _ in STRATEGIES:
        sr = [r for r in results if r["strategy"] == strat_name and "error" not in r]
        anom = [r["reward_proxy"] for r in sr if r["anomaly"] != "none"]
        norm = [r["reward_proxy"] for r in sr if r["anomaly"] == "none"]
        if anom and norm:
            print(f"  {strat_name:>15s}: normal={np.mean(norm):>+7.1f}±{np.std(norm):.1f}  "
                  f"anomaly={np.mean(anom):>+7.1f}±{np.std(anom):.1f}  "
                  f"Δ={np.mean(anom)-np.mean(norm):>+6.1f}")


if __name__ == "__main__":
    main()
