#!/usr/bin/env python3
"""
Smoke test: pre-generate scenario pool → train SAC for ~2 minutes with 2 SUMO workers.

Validates the full pipeline:
  1. generate_demand_profile() creates piecewise Hermite profiles
  2. generate_scenario_pool() writes .rou.xml + .sumocfg to disk
  3. ScenarioManager serves scenarios to parallel workers
  4. TrafficEnv.reset() loads pre-generated scenarios (no on-the-fly generation)
  5. SAC trains for ~2000 steps across 2 SubprocVecEnv workers
"""
import logging
import shutil
import sys
import tempfile
import time
from pathlib import Path

import numpy as np

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("test_pool")

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def _generate_pool(pool_dir: str, n_scenarios: int = 10) -> None:
    """Pre-generate a small scenario pool."""
    from traffic_environment.scenario_pool import generate_scenario_pool

    logger.info("Generating %d scenarios into %s ...", n_scenarios, pool_dir)
    t0 = time.time()

    generate_scenario_pool(
        output_dir=pool_dir,
        n_scenarios=n_scenarios,
        duration_s=3600,
        bin_seconds=30,
        cav_pct=50.0,
        seed_offset=1000,
        n_workers=1,
        demand_kwargs={
            "noise_randomness": 0.5,
            "n_points_range": (5, 8),
            "peak_demand_range": (5500, 8000),
        },
    )

    dt = time.time() - t0
    n_files = len(list(Path(pool_dir).glob("*.sumocfg")))
    logger.info("Generated %d scenarios in %.1fs", n_files, dt)


def _make_env_fn(pool_dir: str, env_seed: int):
    """Create a thunk that returns a TrafficEnv connected to the scenario pool."""
    def _thunk():
        import yaml
        from sar_components.discovery import discover_components
        from core import (
            TrafficEnv,
            create_state_representation, create_action_strategy, create_reward_function,
        )
        from traffic_environment.scenario_pool import ScenarioManager

        discover_components()

        cfg_path = PROJECT_ROOT / "configurations" / "per_lane_stochastic.yaml"
        with open(cfg_path) as f:
            cfg = yaml.safe_load(f)

        sar_config = cfg["sar_config"]
        state_repr = create_state_representation(cfg["sar"]["state"], sar_config)
        action_strat = create_action_strategy(cfg["sar"]["action"], sar_config)
        reward_func = create_reward_function(cfg["sar"]["reward"], sar_config)

        env = TrafficEnv(
            sumo_cfg_path=None,
            state_repr=state_repr,
            action_strat=action_strat,
            reward_func=reward_func,
            episode_duration=cfg["sumo"]["episode_duration_s"],
            cav_percent=cfg["scenario"]["cav_percentage"] / 100.0,
            aggregation_time=cfg["sumo"]["aggregation_time"],
            anomaly_config=cfg["scenario"].get("anomalies"),
            env_seed=env_seed,
        )
        env.dry_run = False

        # Attach scenario manager (each worker gets unique seed for shuffle diversity)
        manager = ScenarioManager(pool_dir, worker_seed=env_seed)
        env.set_scenario_manager(manager)

        from stable_baselines3.common.monitor import Monitor
        return Monitor(env)

    return _thunk


def main():
    pool_dir = tempfile.mkdtemp(prefix="pool_test_")
    logger.info("Pool dir: %s", pool_dir)

    try:
        # Phase 1: Generate scenarios
        _generate_pool(pool_dir, n_scenarios=10)

        # Phase 2: Train SAC with 2 workers for ~2000 steps
        from stable_baselines3 import SAC
        from stable_baselines3.common.vec_env import SubprocVecEnv

        n_envs = 2
        env_fns = [_make_env_fn(pool_dir, env_seed=i) for i in range(n_envs)]

        logger.info("Creating SubprocVecEnv with %d workers...", n_envs)
        vec_env = SubprocVecEnv(env_fns, start_method="forkserver")

        logger.info("Creating SAC model...")
        model = SAC(
            "MlpPolicy",
            vec_env,
            learning_rate=3e-4,
            buffer_size=10_000,
            learning_starts=200,
            batch_size=64,
            tau=0.005,
            gamma=0.99,
            verbose=1,
            policy_kwargs=dict(net_arch=[64, 64]),  # small for test
        )

        target_steps = 2000
        logger.info("Training SAC for %d steps...", target_steps)
        t0 = time.time()
        model.learn(total_timesteps=target_steps)
        dt = time.time() - t0

        logger.info("Training complete: %d steps in %.1fs (%.1f fps)", target_steps, dt, target_steps / dt)

        # Verify: check reward is not NaN or constant
        from stable_baselines3.common.logger import Logger
        # Quick eval
        obs = vec_env.reset()
        total_reward = 0.0
        steps = 0
        for _ in range(10):
            action, _ = model.predict(obs, deterministic=True)
            obs, reward, done, info = vec_env.step(action)
            total_reward += reward.sum()
            steps += n_envs

        avg_r = total_reward / steps
        logger.info("Eval sanity: %d steps, avg reward/step = %.3f", steps, avg_r)
        assert not np.isnan(avg_r), "Reward is NaN!"
        assert avg_r != 0.0, "Reward is exactly 0 (likely broken)"

        vec_env.close()
        logger.info("SUCCESS — scenario pool training works end-to-end")

    except Exception:
        logger.exception("Test FAILED")
        raise
    finally:
        shutil.rmtree(pool_dir, ignore_errors=True)


if __name__ == "__main__":
    main()
