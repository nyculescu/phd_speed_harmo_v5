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

  # Parallel SUMO workers (SubprocVecEnv)
  python train.py --algo tqc --seeds 0 --n-envs 8

The script creates a Gymnasium environment with stochastic demand +
anomaly injection, trains SAC or TQC (SB3/SB3-Contrib), and logs
to TensorBoard.  With --n-envs > 1, uses SubprocVecEnv for parallel
SUMO data collection (N× throughput).

Remote machine requirements:
  - SUMO >= 1.20 with traci
  - pip install -r requirements.txt
  - SUMO_HOME environment variable set
"""
from __future__ import annotations

import argparse
import os
import sys
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
_SEED_MOD = 2 ** 32


def _seed_u32(seed: int, offset: int = 0) -> int:
    """Fold any integer seed into NumPy RandomState's valid [0, 2**32-1] range."""
    return int((int(seed) + int(offset)) % _SEED_MOD)


def _load_config(box5: bool = False) -> dict:
    cfg_path = _PROJECT / "configurations" / "per_lane_stochastic.yaml"
    with open(cfg_path) as f:
        cfg = yaml.safe_load(f)
    if box5:
        cfg["sar_config"]["use_box5"] = True
    return cfg


def _make_env_fn(
    cfg: dict,
    seed: int,
    worker_idx: int = 0,
    scenario_pool_dir: str = "",
):
    """Return a callable that creates a TrafficEnv (for SubprocVecEnv).

    If ``scenario_pool_dir`` is set, the env loads pre-generated scenarios
    from disk via ScenarioManager (fast, reproducible, portable).
    Otherwise falls back to on-the-fly route generation (slower).
    """
    def _thunk():
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

        # Each worker gets a unique seed for demand diversity
        env_seed = _seed_u32(seed * 1000, worker_idx)

        from stable_baselines3.common.monitor import Monitor

        if scenario_pool_dir:
            # Pre-generated scenarios — fast, portable
            from traffic_environment.scenario_pool import ScenarioManager
            env = TrafficEnv(
                sumo_cfg_path=None,
                state_repr=state_repr,
                action_strat=action_strat,
                reward_func=reward_func,
                episode_duration=sumo_cfg["episode_duration_s"],
                cav_percent=scenario_cfg["cav_percentage"] / 100.0,
                aggregation_time=sumo_cfg["aggregation_time"],
                anomaly_config=scenario_cfg.get("anomalies"),
                env_seed=env_seed,
            )
            env.dry_run = False
            mgr = ScenarioManager(scenario_pool_dir, worker_seed=env_seed)
            env.set_scenario_manager(mgr)
        else:
            # On-the-fly generation (legacy fallback)
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

        return Monitor(env)

    return _thunk


def _train_single_seed(
    algo: str, seed: int, cfg: dict, timesteps: int, n_envs: int, log_dir: Path,
    scenario_pool_dir: str = "",
):
    """Train one seed of SAC or TQC with optional SubprocVecEnv."""
    import torch
    from stable_baselines3.common.callbacks import (
        EvalCallback, CallbackList, CheckpointCallback,
    )
    from stable_baselines3.common.vec_env import DummyVecEnv, SubprocVecEnv

    from stable_baselines3.common.callbacks import BaseCallback

    try:
        from stable_baselines3.common.callbacks import ProgressBarCallback
        has_tqdm = True
    except ImportError:
        has_tqdm = False

    class LogProgressCallback(BaseCallback):
        """Line-based progress for log files (no carriage returns)."""

        def __init__(self, total_timesteps: int, log_every: int = 10000, verbose=0):
            super().__init__(verbose)
            self._total = total_timesteps
            self._log_every = log_every
            self._t0 = None

        def _on_training_start(self):
            import time as _time
            self._t0 = _time.time()

        def _on_step(self) -> bool:
            import time as _time
            step = self.num_timesteps
            if step % self._log_every == 0 or step == self._total:
                elapsed = _time.time() - self._t0 if self._t0 else 0
                pct = step / self._total * 100
                eps = step / 120  # approx episodes
                rate = step / elapsed if elapsed > 0 else 0
                eta_s = (self._total - step) / rate if rate > 0 else 0
                eta_m = eta_s / 60

                bar_len = 30
                filled = int(bar_len * step / self._total)
                bar = "█" * filled + "░" * (bar_len - filled)
                print(f"  |{bar}| {pct:5.1f}% [{step:>8,}/{self._total:,}] "
                      f"~{eps:,.0f} eps  {rate:,.0f} stp/s  "
                      f"ETA {eta_m:.0f}m  [{elapsed/60:.0f}m elapsed]",
                      flush=True)
            return True

    # Set seeds
    np.random.seed(seed)
    torch.manual_seed(seed)

    print(f"\n{'='*60}")
    print(f"Training {algo.upper()} seed={seed} for {timesteps:,} steps")
    print(f"  Parallel SUMO workers: {n_envs}")
    print(f"{'='*60}")

    # Create vectorized training env
    pool = scenario_pool_dir
    if n_envs > 1:
        env_fns = [
            _make_env_fn(cfg, seed, worker_idx=i, scenario_pool_dir=pool)
            for i in range(n_envs)
        ]
        train_env = SubprocVecEnv(env_fns)
    else:
        train_env = DummyVecEnv([
            _make_env_fn(cfg, seed, worker_idx=0, scenario_pool_dir=pool)
        ])

    # Eval env — always single, separate seed space for independence.
    eval_env = DummyVecEnv([
        _make_env_fn(cfg, seed + 5000, worker_idx=0, scenario_pool_dir=pool)
    ])

    # Model directory
    model_dir = log_dir / f"{algo}_seed{seed}"
    model_dir.mkdir(parents=True, exist_ok=True)
    tb_dir = model_dir / "tensorboard"

    # Eval callback — eval_freq is in steps *per env*, so divide by n_envs.
    # With n_envs=16 and eval_freq=50000: eval every 50000/16 ≈ 3125 steps
    # per env, which is ~26 episodes per env → eval every ~26 episodes.
    raw_eval_freq = cfg["training"]["eval_freq"]
    eval_freq_per_env = max(raw_eval_freq // n_envs, 1)
    n_eval_episodes = max(cfg["training"]["n_eval_episodes"], 10)

    eval_callback = EvalCallback(
        eval_env,
        best_model_save_path=str(model_dir / "best_model"),
        log_path=str(model_dir / "eval_logs"),
        eval_freq=eval_freq_per_env,
        n_eval_episodes=n_eval_episodes,
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

    # Checkpoint callback — saves every 50k steps so progress is never lost
    checkpoint_callback = CheckpointCallback(
        save_freq=max(50_000 // n_envs, 1),
        save_path=str(model_dir / "checkpoints"),
        name_prefix=f"{algo}_s{seed}",
        save_replay_buffer=False,  # Too large; model weights are enough
        save_vecnormalize=False,
    )

    # Build callback list
    callbacks = [eval_callback, checkpoint_callback]
    if sys.stdout.isatty() and has_tqdm:
        # Interactive terminal → tqdm progress bar
        callbacks.append(ProgressBarCallback())
    else:
        # Background / log file → line-based progress
        callbacks.append(LogProgressCallback(timesteps, log_every=5000))
    callback = CallbackList(callbacks)

    # Train
    try:
        model.learn(
            total_timesteps=timesteps,
            callback=callback,
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
        "--n-envs", type=int, default=1,
        help="Number of parallel SUMO workers (SubprocVecEnv). "
             "Each worker runs its own SUMO instance with a unique "
             "stochastic demand profile. Recommended: 4-16.",
    )
    parser.add_argument(
        "--log-dir", type=str, default=None,
        help="Output directory (default: training_runs/<timestamp>)",
    )
    parser.add_argument(
        "--scenario-pool", type=str, default="",
        help="Path to pre-generated scenario pool directory. "
             "If set, loads .sumocfg files from this directory instead of "
             "generating routes on-the-fly. Use generate_scenarios.py to create.",
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

    n_envs = args.n_envs

    print(f"v5.1 Training — {args.algo.upper()} {box_label}")
    print(f"  Seeds: {args.seeds}")
    print(f"  Timesteps per seed: {timesteps:,}")
    print(f"  Parallel SUMO workers: {n_envs}")
    print(f"  Output: {log_dir}")
    print(f"  Stochastic demand: peak [{cfg['scenario']['stochastic_demand']['peak_demand_range']}] vph")
    print(f"  Anomaly prob: {cfg['scenario']['anomalies']['probability']}")

    pool_dir = args.scenario_pool
    if pool_dir:
        print(f"  Scenario pool: {pool_dir}")
    else:
        print(f"  Scenario pool: (on-the-fly generation)")

    for seed in args.seeds:
        _train_single_seed(
            args.algo, seed, cfg, timesteps, n_envs, log_dir,
            scenario_pool_dir=pool_dir,
        )

    print(f"\n{'='*60}")
    print(f"All seeds complete. Results in {log_dir}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
