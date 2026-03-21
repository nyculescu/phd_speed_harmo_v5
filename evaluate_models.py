#!/usr/bin/env python3
"""
Ground-truth evaluation: NC, static baselines, and trained models
on IDENTICAL stochastic episodes with v4 reward.

Resolves the 5 critical unknowns:
  1. What is NC's actual reward in the stochastic training env?
  2. What does M110 uniform score?
  3. Are per-lane actions differentiated in the trained policy?
  4. Does the agent adapt actions across the episode?
  5. Is the reward signal strong enough for per-lane strategies?

Usage:
  python evaluate_models.py --experiment training_runs/experiment_20260320_201005
  python evaluate_models.py --experiment training_runs/experiment_20260320_201005 --episodes 50
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import sys
import time
from collections import defaultdict
from datetime import datetime
from pathlib import Path

import numpy as np
import yaml

_PROJECT = Path(__file__).resolve().parent
sys.path.insert(0, str(_PROJECT))
os.chdir(_PROJECT)

_SUMO_HOME = os.environ.get("SUMO_HOME", "/usr/share/sumo")
sys.path.insert(0, os.path.join(_SUMO_HOME, "tools"))


def _load_config(experiment_dir: Path) -> dict:
    """Load config from any arm's config.yaml."""
    for arm in ["sac_box4", "tqc_box4", "tqc_box5", "sac_box5"]:
        cfg_path = experiment_dir / arm / "config.yaml"
        if cfg_path.exists():
            with open(cfg_path) as f:
                return yaml.safe_load(f)
    # Fallback to project config
    with open(_PROJECT / "configurations" / "per_lane_stochastic.yaml") as f:
        return yaml.safe_load(f)


def _make_env(cfg: dict, env_seed: int):
    """Create a single TrafficEnv matching training conditions."""
    from sar_components.discovery import discover_components
    from core import (
        TrafficEnv,
        create_action_strategy,
        create_reward_function,
        create_state_representation,
    )

    discover_components()

    sar_config = cfg["sar_config"]
    sumo_cfg = cfg["sumo"]
    scenario_cfg = cfg["scenario"]

    state_repr = create_state_representation(cfg["sar"]["state"], sar_config)
    action_strat = create_action_strategy(cfg["sar"]["action"], sar_config)
    reward_func = create_reward_function(cfg["sar"]["reward"], sar_config)

    env = TrafficEnv(
        sumo_cfg_path=None,
        state_repr=state_repr,
        action_strat=action_strat,
        reward_func=reward_func,
        episode_duration=sumo_cfg["episode_duration_s"],
        cav_percent=scenario_cfg["cav_percentage"] / 100.0,
        aggregation_time=sumo_cfg["aggregation_time"],
        demand_config=scenario_cfg["stochastic_demand"],
        anomaly_config=scenario_cfg.get("anomalies"),
        env_seed=env_seed,
    )
    env.dry_run = False
    return env


def _find_models(experiment_dir: Path) -> dict:
    """Find all trained models (best_model and final_model) in the experiment."""
    models = {}
    for arm_dir in sorted(experiment_dir.iterdir()):
        if not arm_dir.is_dir():
            continue
        arm_name = arm_dir.name  # e.g., sac_box4, tqc_box4, tqc_box5
        for seed_dir in sorted(arm_dir.iterdir()):
            if not seed_dir.is_dir() or "seed" not in seed_dir.name:
                continue
            seed_num = seed_dir.name.split("seed")[-1]
            # Prefer best_model, fallback to final_model
            best = seed_dir / "best_model" / "best_model.zip"
            final = seed_dir / "final_model.zip"
            model_path = best if best.exists() else (final if final.exists() else None)
            if model_path:
                key = f"{arm_name}_seed{seed_num}"
                models[key] = str(model_path)
    return models


def _load_model(model_path: str, arm_name: str):
    """Load a trained SB3/SB3-Contrib model."""
    if "tqc" in arm_name:
        from sb3_contrib import TQC
        return TQC.load(model_path)
    else:
        from stable_baselines3 import SAC
        return SAC.load(model_path)


# Static baseline policies
def _nc_action(box5: bool = False) -> np.ndarray:
    """No control: all speeds at maximum."""
    if box5:
        return np.array([120.0, 120.0, 120.0, 90.0, 120.0], dtype=np.float32)
    return np.array([120.0, 120.0, 120.0, 90.0], dtype=np.float32)


def _m110_action(box5: bool = False) -> np.ndarray:
    """Uniform M110 on mainline, 75 on ramp."""
    if box5:
        return np.array([110.0, 110.0, 110.0, 75.0, 115.0], dtype=np.float32)
    return np.array([110.0, 110.0, 110.0, 75.0], dtype=np.float32)


def _diff_mild_action(box5: bool = False) -> np.ndarray:
    """Differential mild: L0=105, L1=110, L2=115, ramp=70."""
    if box5:
        return np.array([105.0, 110.0, 115.0, 70.0, 115.0], dtype=np.float32)
    return np.array([105.0, 110.0, 115.0, 70.0], dtype=np.float32)


def run_episode(env, policy_fn, episode_seed: int):
    """
    Run one episode with a given policy function.

    policy_fn: callable(obs) -> action (np.ndarray)

    Returns dict with per-step data and episode summary.
    """
    obs, info = env.reset()

    # Record anomaly info for this episode
    anomaly_type = "none"
    anomaly_start = 0
    if hasattr(env, "_anomaly_injector") and env._anomaly_injector and env._anomaly_injector.has_anomaly:
        anomaly_type = env._anomaly_injector.event.anomaly_type
        anomaly_start = env._anomaly_injector.event.start_time_s

    # Record demand info
    peak_demand = 0
    ramp_frac = 0
    if hasattr(env, "_demand_profile") and env._demand_profile is not None:
        peak_demand = env._demand_profile.peak_demand_vph
        ramp_frac = env._demand_profile.ramp_fraction

    steps = []
    total_reward = 0.0
    done = False
    step_idx = 0

    while not done:
        action = policy_fn(obs)
        obs, reward, terminated, truncated, info = env.step(action)
        done = terminated or truncated

        # Collect per-step data
        m = env._metrics
        step_data = {
            "step": step_idx,
            "sim_time_s": (step_idx + 1) * env._aggregation_time,
            "reward": float(reward),
            "action_L0": float(action[0]),
            "action_L1": float(action[1]),
            "action_L2": float(action[2]),
            "action_ramp": float(action[3]),
            "seg_0_before_speed_kph": float(m.seg_0_before_speed_ms * 3.6),
            "seg_0_before_L0_speed_kph": float(m.seg_0_before_L0_speed_ms * 3.6),
            "seg_0_before_L1_speed_kph": float(m.seg_0_before_L1_speed_ms * 3.6),
            "seg_0_before_L2_speed_kph": float(m.seg_0_before_L2_speed_ms * 3.6),
            "seg_0_after_speed_kph": float(m.seg_0_after_speed_ms * 3.6),
            "seg_1_after_flow_vph": float(m.seg_1_after_flow_vph),
            "seg_1_after_speed_kph": float(m.seg_1_after_speed_ms * 3.6),
            "ramp_merge_speed_kph": float(m.ramp_on_merge_speed_ms * 3.6),
            "anomaly_active": bool(m.anomaly_active),
        }

        # Add reward components if available
        rc = info.get("reward_components", {})
        for k, v in rc.items():
            step_data[f"rc_{k}"] = float(v)

        steps.append(step_data)
        total_reward += float(reward)
        step_idx += 1

    # Episode summary
    actions_L0 = [s["action_L0"] for s in steps]
    actions_L1 = [s["action_L1"] for s in steps]
    actions_L2 = [s["action_L2"] for s in steps]
    actions_ramp = [s["action_ramp"] for s in steps]

    summary = {
        "total_reward": total_reward,
        "n_steps": step_idx,
        "peak_demand_vph": peak_demand,
        "ramp_fraction": ramp_frac,
        "anomaly_type": anomaly_type,
        "anomaly_start_s": anomaly_start,
        # Action statistics
        "action_L0_mean": float(np.mean(actions_L0)),
        "action_L1_mean": float(np.mean(actions_L1)),
        "action_L2_mean": float(np.mean(actions_L2)),
        "action_ramp_mean": float(np.mean(actions_ramp)),
        "action_L0_std": float(np.std(actions_L0)),
        "action_L1_std": float(np.std(actions_L1)),
        "action_L2_std": float(np.std(actions_L2)),
        "action_ramp_std": float(np.std(actions_ramp)),
        "action_L0_L2_mean_diff": float(np.mean(actions_L0)) - float(np.mean(actions_L2)),
        # Traffic metrics
        "avg_ds_flow_vph": float(np.mean([s["seg_1_after_flow_vph"] for s in steps])),
        "avg_merge_speed_kph": float(np.mean([s["seg_0_after_speed_kph"] for s in steps])),
        "avg_L0_speed_kph": float(np.mean([s["seg_0_before_L0_speed_kph"] for s in steps])),
        "avg_L2_speed_kph": float(np.mean([s["seg_0_before_L2_speed_kph"] for s in steps])),
        "L0_L2_speed_delta": float(np.mean([s["seg_0_before_L0_speed_kph"] for s in steps])) -
                             float(np.mean([s["seg_0_before_L2_speed_kph"] for s in steps])),
    }

    # Reward component averages
    rc_keys = [k for k in steps[0] if k.startswith("rc_")]
    for k in rc_keys:
        vals = [s[k] for s in steps if k in s]
        summary[f"avg_{k}"] = float(np.mean(vals)) if vals else 0

    return summary, steps


def main():
    parser = argparse.ArgumentParser(
        description="Ground-truth evaluation of trained models vs baselines"
    )
    parser.add_argument(
        "--experiment", type=str, required=True,
        help="Path to experiment directory (e.g., training_runs/experiment_20260320_201005)",
    )
    parser.add_argument(
        "--episodes", type=int, default=30,
        help="Number of episodes per policy (default: 30)",
    )
    parser.add_argument(
        "--seed-offset", type=int, default=99000,
        help="Base seed for evaluation (must differ from training seeds)",
    )
    parser.add_argument(
        "--best-seed-only", action="store_true",
        help="Only evaluate the best seed per arm (from eval logs)",
    )
    args = parser.parse_args()

    experiment_dir = Path(args.experiment)
    cfg = _load_config(experiment_dir)
    n_episodes = args.episodes
    seed_offset = args.seed_offset

    # Output directory
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_dir = experiment_dir / f"evaluation_{timestamp}"
    out_dir.mkdir(parents=True, exist_ok=True)

    print(f"Ground-truth evaluation")
    print(f"  Experiment: {experiment_dir}")
    print(f"  Episodes per policy: {n_episodes}")
    print(f"  Seed offset: {seed_offset}")
    print(f"  Output: {out_dir}")
    print()

    # Find trained models
    models = _find_models(experiment_dir)
    print(f"  Found {len(models)} trained models:")
    for name, path in models.items():
        print(f"    {name}: {path}")
    print()

    # If best-seed-only, filter to best seed per arm
    if args.best_seed_only and models:
        best_per_arm = {}
        for arm in set(k.rsplit("_seed", 1)[0] for k in models):
            arm_models = {k: v for k, v in models.items() if k.startswith(arm)}
            # Load eval logs to find best seed
            best_reward = -float("inf")
            best_key = None
            for key in arm_models:
                prefix = arm.split("_")[0]
                seed_num = key.split("seed")[-1]
                eval_path = experiment_dir / arm / f"{prefix}_seed{seed_num}" / "eval_logs" / "evaluations.npz"
                if eval_path.exists():
                    data = np.load(eval_path)
                    final_mean = data["results"][-1].mean()
                    if final_mean > best_reward:
                        best_reward = final_mean
                        best_key = key
            if best_key:
                best_per_arm[best_key] = arm_models[best_key]
                print(f"  Best {arm}: {best_key} (eval={best_reward:.1f})")
        models = best_per_arm
        print()

    # Build policy list: baselines + trained models
    is_box5 = cfg["sar_config"].get("use_box5", False)
    policies = {
        "NC": lambda obs: _nc_action(is_box5),
        "M110_uniform": lambda obs: _m110_action(is_box5),
        "diff_mild": lambda obs: _diff_mild_action(is_box5),
    }

    # Add trained model policies
    loaded_models = {}
    for name, path in models.items():
        try:
            model = _load_model(path, name)
            loaded_models[name] = model
            policies[name] = lambda obs, m=model: m.predict(obs, deterministic=True)[0]
            print(f"  Loaded {name}")
        except Exception as e:
            print(f"  FAILED to load {name}: {e}")

    print()
    print(f"  Total policies to evaluate: {len(policies)}")
    print(f"  Policies: {list(policies.keys())}")
    print()

    # Create environment
    env = _make_env(cfg, env_seed=seed_offset)

    # Run evaluation
    all_summaries = []
    all_steps = {}
    t0 = time.time()

    for policy_idx, (policy_name, policy_fn) in enumerate(policies.items()):
        print(f">>> [{policy_idx+1}/{len(policies)}] {policy_name}")
        ep_rewards = []

        for ep in range(n_episodes):
            # Set env seed for this episode — same across all policies
            env._env_seed = seed_offset + ep
            env._episode_count = 0  # Force same episode seed derivation

            summary, steps = run_episode(env, policy_fn, seed_offset + ep)
            summary["policy"] = policy_name
            summary["episode"] = ep
            all_summaries.append(summary)
            ep_rewards.append(summary["total_reward"])

            # Save per-step data for first 3 episodes (for trajectory analysis)
            if ep < 3:
                key = f"{policy_name}_ep{ep}"
                all_steps[key] = steps

            if (ep + 1) % 10 == 0 or ep == n_episodes - 1:
                elapsed = time.time() - t0
                mean_r = np.mean(ep_rewards)
                std_r = np.std(ep_rewards) if len(ep_rewards) > 1 else 0
                print(f"    ep {ep+1}/{n_episodes}: mean_reward={mean_r:.1f} ± {std_r:.1f} [{elapsed:.0f}s]")

        print()

    env.close()

    # Write summary CSV
    summary_path = out_dir / "evaluation_summary.csv"
    if all_summaries:
        keys = all_summaries[0].keys()
        with open(summary_path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=keys)
            writer.writeheader()
            writer.writerows(all_summaries)
        print(f"Summary written to {summary_path}")

    # Write per-step trajectories (JSON for flexibility)
    traj_path = out_dir / "trajectories.json"
    with open(traj_path, "w") as f:
        json.dump(all_steps, f, indent=2, default=str)
    print(f"Trajectories written to {traj_path}")

    # Print comparison table
    print()
    print("=" * 120)
    print("GROUND-TRUTH COMPARISON")
    print("=" * 120)

    by_policy = defaultdict(list)
    for s in all_summaries:
        by_policy[s["policy"]].append(s)

    header = (f"{'Policy':>20} | {'Reward':>10} {'±':>5} | {'Flow':>6} | "
              f"{'L0act':>5} {'L1act':>5} {'L2act':>5} {'Ract':>5} | "
              f"{'L0spd':>5} {'L2spd':>5} {'L0-L2':>5} | "
              f"{'ActStd':>6} | {'Anom':>4}")
    print(header)
    print("-" * 120)

    nc_reward = None
    for policy_name in policies:
        eps = by_policy[policy_name]
        rewards = [e["total_reward"] for e in eps]
        mean_r = np.mean(rewards)
        std_r = np.std(rewards)
        if policy_name == "NC":
            nc_reward = mean_r

        avg_flow = np.mean([e["avg_ds_flow_vph"] for e in eps])
        avg_l0a = np.mean([e["action_L0_mean"] for e in eps])
        avg_l1a = np.mean([e["action_L1_mean"] for e in eps])
        avg_l2a = np.mean([e["action_L2_mean"] for e in eps])
        avg_ra = np.mean([e["action_ramp_mean"] for e in eps])
        avg_l0s = np.mean([e["avg_L0_speed_kph"] for e in eps])
        avg_l2s = np.mean([e["avg_L2_speed_kph"] for e in eps])
        avg_l0l2 = np.mean([e["L0_L2_speed_delta"] for e in eps])
        avg_act_std = np.mean([
            np.mean([e["action_L0_std"], e["action_L1_std"], e["action_L2_std"]])
            for e in eps
        ])
        n_anom = sum(1 for e in eps if e["anomaly_type"] != "none")

        marker = ""
        if nc_reward is not None and policy_name != "NC":
            delta = mean_r - nc_reward
            marker = f" ({delta:+.1f} vs NC)"

        print(f"{policy_name:>20} | {mean_r:>10.1f} {std_r:>5.1f} | {avg_flow:>6.0f} | "
              f"{avg_l0a:>5.1f} {avg_l1a:>5.1f} {avg_l2a:>5.1f} {avg_ra:>5.1f} | "
              f"{avg_l0s:>5.1f} {avg_l2s:>5.1f} {avg_l0l2:>+5.1f} | "
              f"{avg_act_std:>6.2f} | {n_anom:>4}{marker}")

    # Anomaly vs non-anomaly breakdown
    print()
    print("=" * 80)
    print("ANOMALY vs NON-ANOMALY BREAKDOWN")
    print("=" * 80)
    for policy_name in policies:
        eps = by_policy[policy_name]
        normal = [e["total_reward"] for e in eps if e["anomaly_type"] == "none"]
        anomaly = [e["total_reward"] for e in eps if e["anomaly_type"] != "none"]
        if normal and anomaly:
            print(f"  {policy_name:>20}: normal={np.mean(normal):.1f}±{np.std(normal):.1f}"
                  f"  anomaly={np.mean(anomaly):.1f}±{np.std(anomaly):.1f}"
                  f"  Δ={np.mean(anomaly)-np.mean(normal):.1f}")
        elif normal:
            print(f"  {policy_name:>20}: normal={np.mean(normal):.1f}±{np.std(normal):.1f}  (no anomalies)")

    # Per-reward-component breakdown
    print()
    print("=" * 80)
    print("REWARD COMPONENT BREAKDOWN (per-step averages)")
    print("=" * 80)
    rc_keys_available = [k for k in all_summaries[0] if k.startswith("avg_rc_")]
    if rc_keys_available:
        header = f"{'Policy':>20}"
        for k in rc_keys_available:
            short = k.replace("avg_rc_", "")[:12]
            header += f" | {short:>12}"
        print(header)
        for policy_name in policies:
            eps = by_policy[policy_name]
            line = f"{policy_name:>20}"
            for k in rc_keys_available:
                vals = [e[k] for e in eps if k in e]
                mean_v = np.mean(vals) if vals else 0
                line += f" | {mean_v:>12.4f}"
            print(line)

    print()
    print(f"Results saved to: {out_dir}")
    print("Done.")


if __name__ == "__main__":
    main()
