#!/usr/bin/env python3
"""
Training script for v5.1 per-lane speed harmonisation.

Usage:
  # SAC Box(4) — 5 seeds
  python train.py --algo sac --seeds 0 1 2 3 4

  # TQC Box(4) — 5 seeds
  python train.py --algo tqc --seeds 0 1 2 3 4

  # TQC Box(5) — mixed Lagrangian-Eulerian
  python train.py --algo tqc --box5 --seeds 0 1 2 3 4

  # Single seed for debugging
  python train.py --algo sac --seeds 0 --timesteps 50000

The script creates a Gymnasium environment with stochastic demand +
anomaly injection, trains SAC or TQC (SB3/SB3-Contrib), and logs
to TensorBoard.

Remote machine requirements:
  - SUMO >= 1.20 with traci
  - pip install -r requirements.txt
  - SUMO_HOME environment variable set
"""
from __future__ import annotations

import argparse
import os
import sys
import tempfile
from datetime import datetime
from pathlib import Path

import numpy as np
import yaml

# --- path setup ---
_PROJECT = Path(__file__).resolve().parent
sys.path.insert(0, str(_PROJECT))
os.chdir(_PROJECT)

_SUMO_HOME = os.environ.get("SUMO_HOME", "/usr/share/sumo")
sys.path.insert(0, os.path.join(_SUMO_HOME, "tools"))


def _load_config(box5: bool = False) -> dict:
    cfg_path = _PROJECT / "configurations" / "per_lane_stochastic.yaml"
    with open(cfg_path) as f:
        cfg = yaml.safe_load(f)
    if box5:
        cfg["sar_config"]["use_box5"] = True
    return cfg


def _make_env(cfg: dict, seed: int):
    """Create a TrafficEnv with stochastic demand for training."""
    from tests._sumo_helpers import (
        generate_stochastic_route_file, generate_sumocfg,
    )
    from traffic_environment.stochastic_demand import generate_demand_profile
    from traffic_environment.anomaly_injector import AnomalyInjector
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

    # Generate stochastic scenario
    demand_cfg = scenario_cfg["stochastic_demand"]
    profile = generate_demand_profile(
        episode_duration_s=sumo_cfg["episode_duration_s"],
        peak_demand_range=tuple(demand_cfg["peak_demand_range"]),
        base_fraction_range=tuple(demand_cfg["base_fraction_range"]),
        ramp_fraction_range=tuple(demand_cfg["ramp_fraction_range"]),
        t_peak_frac_range=tuple(demand_cfg["t_peak_range"]),
        t_decay_frac_range=tuple(demand_cfg["t_decay_range"]),
        noise_std=demand_cfg["noise_std"],
        seed=seed,
    )

    tmp_dir = Path(tempfile.mkdtemp(prefix=f"train_s{seed}_"))
    rou_path = tmp_dir / "scenario.rou.xml"
    cfg_path = tmp_dir / "scenario.sumocfg"

    generate_stochastic_route_file(
        rou_path, profile,
        cav_pct=scenario_cfg["cav_percentage"],
        seed=seed + 10000,
    )
    generate_sumocfg(cfg_path, rou_path, sumo_cfg["episode_duration_s"])

    env = TrafficEnv(
        sumo_cfg_path=str(cfg_path),
        state_repr=state_repr,
        action_strat=action_strat,
        reward_func=reward_func,
        episode_duration=sumo_cfg["episode_duration_s"],
        cav_percent=scenario_cfg["cav_percentage"] / 100.0,
        aggregation_time=sumo_cfg["aggregation_time"],
    )

    return env, tmp_dir


def _train_single_seed(algo: str, seed: int, cfg: dict, timesteps: int, log_dir: Path):
    """Train one seed of SAC or TQC."""
    import torch
    from stable_baselines3.common.callbacks import EvalCallback

    # Set seeds
    np.random.seed(seed)
    torch.manual_seed(seed)

    print(f"\n{'='*60}")
    print(f"Training {algo.upper()} seed={seed} for {timesteps:,} steps")
    print(f"{'='*60}")

    # Create training env
    train_env, train_tmp = _make_env(cfg, seed)

    # Create eval env (different seed)
    eval_env, eval_tmp = _make_env(cfg, seed + 5000)

    # Model directory
    model_dir = log_dir / f"{algo}_seed{seed}"
    model_dir.mkdir(parents=True, exist_ok=True)
    tb_dir = model_dir / "tensorboard"

    # Eval callback
    eval_callback = EvalCallback(
        eval_env,
        best_model_save_path=str(model_dir / "best_model"),
        log_path=str(model_dir / "eval_logs"),
        eval_freq=cfg["training"]["eval_freq"],
        n_eval_episodes=cfg["training"]["n_eval_episodes"],
        deterministic=True,
        render=False,
    )

    # Create model
    algo_cfg = cfg["training"][algo]
    policy_kwargs = algo_cfg.get("policy_kwargs", {})

    if algo == "sac":
        from stable_baselines3 import SAC

        model = SAC(
            policy=algo_cfg["policy"],
            env=train_env,
            learning_rate=algo_cfg["learning_rate"],
            buffer_size=algo_cfg["buffer_size"],
            learning_starts=algo_cfg["learning_starts"],
            batch_size=algo_cfg["batch_size"],
            tau=algo_cfg["tau"],
            gamma=algo_cfg["gamma"],
            ent_coef=algo_cfg["ent_coef"],
            target_entropy=algo_cfg["target_entropy"],
            policy_kwargs=policy_kwargs,
            tensorboard_log=str(tb_dir),
            seed=seed,
            verbose=1,
        )
    elif algo == "tqc":
        from sb3_contrib import TQC

        model = TQC(
            policy=algo_cfg["policy"],
            env=train_env,
            learning_rate=algo_cfg["learning_rate"],
            buffer_size=algo_cfg["buffer_size"],
            learning_starts=algo_cfg["learning_starts"],
            batch_size=algo_cfg["batch_size"],
            tau=algo_cfg["tau"],
            gamma=algo_cfg["gamma"],
            ent_coef=algo_cfg["ent_coef"],
            target_entropy=algo_cfg["target_entropy"],
            top_quantiles_to_drop_per_net=algo_cfg["top_quantiles_to_drop_per_net"],
            policy_kwargs={
                **policy_kwargs,
                "n_quantiles": algo_cfg["n_quantiles"],
                "n_critics": algo_cfg["n_critics"],
            },
            tensorboard_log=str(tb_dir),
            seed=seed,
            verbose=1,
        )
    else:
        raise ValueError(f"Unknown algorithm: {algo}")

    # Train
    try:
        model.learn(
            total_timesteps=timesteps,
            callback=eval_callback,
            log_interval=10,
            tb_log_name=f"{algo}_s{seed}",
        )

        # Save final model
        final_path = model_dir / "final_model"
        model.save(str(final_path))
        print(f"\nModel saved to {final_path}")

    finally:
        train_env.close()
        eval_env.close()
        # Clean up temp dirs
        import shutil
        shutil.rmtree(train_tmp, ignore_errors=True)
        shutil.rmtree(eval_tmp, ignore_errors=True)

    return str(model_dir)


def main():
    parser = argparse.ArgumentParser(
        description="Train SAC or TQC for v5.1 per-lane speed harmonisation"
    )
    parser.add_argument(
        "--algo", choices=["sac", "tqc"], required=True,
        help="Algorithm to train",
    )
    parser.add_argument(
        "--seeds", type=int, nargs="+", default=[0],
        help="Random seeds to train (default: [0])",
    )
    parser.add_argument(
        "--timesteps", type=int, default=None,
        help="Total timesteps per seed (default: from config)",
    )
    parser.add_argument(
        "--box5", action="store_true",
        help="Use Box(5) mixed Lagrangian-Eulerian (adds physical VSL on seg_1_before)",
    )
    parser.add_argument(
        "--log-dir", type=str, default=None,
        help="Output directory (default: training_runs/<timestamp>)",
    )
    args = parser.parse_args()

    cfg = _load_config(box5=args.box5)
    timesteps = args.timesteps or cfg["training"]["total_timesteps"]

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    box_label = "box5" if args.box5 else "box4"
    log_dir = Path(args.log_dir) if args.log_dir else (
        _PROJECT / "training_runs" / f"{args.algo}_{box_label}_{timestamp}"
    )
    log_dir.mkdir(parents=True, exist_ok=True)

    # Save config snapshot
    with open(log_dir / "config.yaml", "w") as f:
        yaml.dump(cfg, f, default_flow_style=False)

    print(f"v5.1 Training — {args.algo.upper()} {box_label}")
    print(f"  Seeds: {args.seeds}")
    print(f"  Timesteps per seed: {timesteps:,}")
    print(f"  Output: {log_dir}")
    print(f"  Stochastic demand: peak [{cfg['scenario']['stochastic_demand']['peak_demand_range']}] vph")
    print(f"  Anomaly prob: {cfg['scenario']['anomalies']['probability']}")

    for seed in args.seeds:
        _train_single_seed(args.algo, seed, cfg, timesteps, log_dir)

    print(f"\n{'='*60}")
    print(f"All seeds complete. Results in {log_dir}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
