#!/usr/bin/env python3
"""
Smoke test: verifies the full training pipeline works end-to-end
before committing to a multi-hour run on a remote machine.

Tests (in order of increasing scope):
  1. Imports       — SB3, SB3-Contrib, torch, gymnasium all importable
  2. Config        — per_lane_stochastic.yaml loads and SAR components resolve
  3. Env dry-run   — TrafficEnv with v2 SAR produces correct shapes
  4. Env live      — Single SUMO episode completes (120 steps)
  5. VecEnv        — SubprocVecEnv with 2 parallel SUMO workers
  6. SAC fit       — SAC.learn() for 240 steps (2 episodes) without crash
  7. TQC fit       — TQC.learn() for 240 steps (2 episodes) without crash
  8. Save/Load     — Model saves and reloads correctly
  9. Deterministic — Loaded model produces deterministic actions

Usage:
  python tests/test_smoke_training.py            # full smoke test
  python tests/test_smoke_training.py --fast     # skip SAC/TQC fit (env-only)
"""
from __future__ import annotations

import argparse
import os
import shutil
import sys
import tempfile
import time
import traceback
from pathlib import Path

# --- path setup ---
_PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_PROJECT))
os.chdir(_PROJECT)

_SUMO_HOME = os.environ.get("SUMO_HOME", "/usr/share/sumo")
sys.path.insert(0, os.path.join(_SUMO_HOME, "tools"))

SMOKE_EPISODE_S = 300   # 5 min episodes (shorter than training's 3600)
SMOKE_STEPS = 10        # 10 env steps = 300s at agg_time=30
SMOKE_TIMESTEPS = 20    # SAC/TQC learn steps (tiny — just checking no crash)
SMOKE_DEMAND_VPH = 6000


def _header(name: str):
    print(f"\n{'─'*60}")
    print(f"  {name}")
    print(f"{'─'*60}")


def _pass(msg: str = ""):
    print(f"  ✓ PASSED{': ' + msg if msg else ''}")


def _fail(msg: str):
    print(f"  ✗ FAILED: {msg}")
    traceback.print_exc()
    return False


def test_imports(fast: bool = False):
    _header("1. Imports")
    try:
        import numpy as np
        import gymnasium as gym
        print(f"  numpy={np.__version__}, gymnasium={gym.__version__}")

        if fast:
            print("  [fast mode] Skipping torch/SB3/SB3-Contrib import check")
            _pass("fast mode — core imports OK")
            return True

        import torch
        import stable_baselines3 as sb3
        import sb3_contrib
        print(f"  torch={torch.__version__}")
        print(f"  stable_baselines3={sb3.__version__}")
        print(f"  sb3_contrib={sb3_contrib.__version__}")
        print(f"  CUDA available: {torch.cuda.is_available()}")

        from stable_baselines3 import SAC
        from sb3_contrib import TQC
        from stable_baselines3.common.vec_env import SubprocVecEnv, DummyVecEnv

        _pass()
        return True
    except Exception as e:
        return _fail(str(e))


def test_config():
    _header("2. Config + SAR resolution")
    try:
        import yaml
        from sar_components.discovery import discover_components
        from core import (
            create_state_representation,
            create_action_strategy,
            create_reward_function,
        )

        discover_components()

        with open("configurations/per_lane_stochastic.yaml") as f:
            cfg = yaml.safe_load(f)

        sar_config = cfg["sar_config"]
        s = create_state_representation(cfg["sar"]["state"], sar_config)
        a = create_action_strategy(cfg["sar"]["action"], sar_config)
        r = create_reward_function(cfg["sar"]["reward"], sar_config)

        obs_space = s.get_observation_space()
        act_space = a.get_action_space()
        print(f"  State:  {cfg['sar']['state']} → obs_space={obs_space.shape}")
        print(f"  Action: {cfg['sar']['action']} → act_space={act_space.shape}")
        print(f"  Reward: {cfg['sar']['reward']}")

        assert obs_space.shape == (77,), f"Expected (77,), got {obs_space.shape}"
        assert act_space.shape == (4,), f"Expected (4,), got {act_space.shape}"

        _pass()
        return True
    except Exception as e:
        return _fail(str(e))


def test_env_dry_run():
    _header("3. Env dry-run (no SUMO)")
    try:
        import numpy as np
        from sar_components.discovery import discover_components
        from core import (
            TrafficEnv,
            create_state_representation,
            create_action_strategy,
            create_reward_function,
        )

        discover_components()
        sar_config = {"max_flow_vph": 8000, "max_ramp_flow_vph": 2000}
        s = create_state_representation("r44_state_v2", sar_config)
        a = create_action_strategy("r44_action_v2", sar_config)
        r = create_reward_function("r44_reward_v4", sar_config)

        env = TrafficEnv(None, s, a, r, SMOKE_EPISODE_S)
        obs, info = env.reset()
        assert obs.shape == (77,), f"obs shape {obs.shape}"

        action = np.array([95, 90, 85, 65], dtype=np.float32)
        obs2, rew, done, trunc, info2 = env.step(action)
        assert obs2.shape == (77,)
        assert isinstance(rew, float)
        print(f"  obs={obs.shape}, reward={rew:.3f}, done={done}")

        _pass()
        return True
    except Exception as e:
        return _fail(str(e))


def _make_smoke_env():
    """Create a live SUMO env for smoke testing (short episode)."""
    from tests._sumo_helpers import (
        generate_stochastic_route_file, generate_sumocfg,
    )
    from traffic_environment.stochastic_demand import generate_demand_profile
    from sar_components.discovery import discover_components
    from core import (
        TrafficEnv,
        create_state_representation,
        create_action_strategy,
        create_reward_function,
    )

    discover_components()
    sar_config = {"max_flow_vph": 8000, "max_ramp_flow_vph": 2000}

    s = create_state_representation("r44_state_v2", sar_config)
    a = create_action_strategy("r44_action_v2", sar_config)
    r = create_reward_function("r44_reward_v4", sar_config)

    profile = generate_demand_profile(
        episode_duration_s=SMOKE_EPISODE_S, seed=42,
    )
    tmp = Path(tempfile.mkdtemp(prefix="smoke_"))
    rou = tmp / "smoke.rou.xml"
    cfg = tmp / "smoke.sumocfg"
    generate_stochastic_route_file(rou, profile, cav_pct=50.0, seed=42)
    generate_sumocfg(cfg, rou, SMOKE_EPISODE_S)

    env = TrafficEnv(
        sumo_cfg_path=str(cfg),
        state_repr=s, action_strat=a, reward_func=r,
        episode_duration=SMOKE_EPISODE_S,
        cav_percent=0.5, aggregation_time=30,
    )
    return env, tmp


def test_env_live():
    _header("4. Env live SUMO (single episode)")
    env = None
    tmp = None
    try:
        import numpy as np

        env, tmp = _make_smoke_env()
        obs, _ = env.reset()
        total_r = 0.0
        t0 = time.time()

        for step in range(SMOKE_STEPS):
            action = np.array([100, 95, 90, 65], dtype=np.float32)
            obs, rew, done, trunc, info = env.step(action)
            total_r += rew

        elapsed = time.time() - t0
        print(f"  {SMOKE_STEPS} steps in {elapsed:.1f}s ({elapsed/SMOKE_STEPS:.2f}s/step)")
        print(f"  total_reward={total_r:.2f}, final obs range=[{obs.min():.3f}, {obs.max():.3f}]")

        assert obs.shape == (77,)
        assert not any(map(lambda x: x != x, obs)), "NaN in obs"

        _pass(f"{elapsed:.1f}s")
        return True
    except Exception as e:
        return _fail(str(e))
    finally:
        if env:
            env.close()
        if tmp:
            shutil.rmtree(tmp, ignore_errors=True)


def test_vecenv():
    _header("5. SubprocVecEnv (2 parallel SUMO workers)")
    vec_env = None
    try:
        import numpy as np
        from stable_baselines3.common.vec_env import SubprocVecEnv
        import yaml

        with open("configurations/per_lane_stochastic.yaml") as f:
            cfg = yaml.safe_load(f)
        # Override for smoke test
        cfg["sumo"]["episode_duration_s"] = SMOKE_EPISODE_S

        sys.path.insert(0, str(_PROJECT))
        from train import _make_env_fn

        env_fns = [_make_env_fn(cfg, seed=42, worker_idx=i) for i in range(2)]
        t0 = time.time()
        vec_env = SubprocVecEnv(env_fns)
        startup_s = time.time() - t0

        obs = vec_env.reset()
        assert obs.shape == (2, 77), f"Expected (2, 77), got {obs.shape}"

        action = np.array([[100, 95, 90, 65], [90, 85, 80, 60]], dtype=np.float32)
        obs2, rews, dones, infos = vec_env.step(action)
        assert obs2.shape == (2, 77)
        assert rews.shape == (2,)

        print(f"  Startup: {startup_s:.1f}s for 2 workers")
        print(f"  Step: obs={obs2.shape}, rewards={rews}")

        _pass(f"startup={startup_s:.1f}s")
        return True
    except Exception as e:
        return _fail(str(e))
    finally:
        if vec_env:
            vec_env.close()


def test_sac_fit():
    _header("6. SAC fit (tiny run)")
    vec_env = None
    try:
        import yaml
        import numpy as np
        from stable_baselines3 import SAC
        from stable_baselines3.common.vec_env import DummyVecEnv
        from train import _make_env_fn

        with open("configurations/per_lane_stochastic.yaml") as f:
            cfg = yaml.safe_load(f)
        cfg["sumo"]["episode_duration_s"] = SMOKE_EPISODE_S

        vec_env = DummyVecEnv([_make_env_fn(cfg, seed=42, worker_idx=0)])

        model = SAC(
            "MlpPolicy", vec_env,
            learning_rate=3e-4, buffer_size=1000,
            learning_starts=10, batch_size=32,
            policy_kwargs={"net_arch": [64, 64]},
            verbose=0,
        )

        t0 = time.time()
        model.learn(total_timesteps=SMOKE_TIMESTEPS)
        elapsed = time.time() - t0

        print(f"  SAC.learn({SMOKE_TIMESTEPS} steps) in {elapsed:.1f}s")

        _pass(f"{elapsed:.1f}s")
        return True
    except Exception as e:
        return _fail(str(e))
    finally:
        if vec_env:
            vec_env.close()


def test_tqc_fit():
    _header("7. TQC fit (tiny run)")
    vec_env = None
    try:
        import yaml
        import numpy as np
        from sb3_contrib import TQC
        from stable_baselines3.common.vec_env import DummyVecEnv
        from train import _make_env_fn

        with open("configurations/per_lane_stochastic.yaml") as f:
            cfg = yaml.safe_load(f)
        cfg["sumo"]["episode_duration_s"] = SMOKE_EPISODE_S

        vec_env = DummyVecEnv([_make_env_fn(cfg, seed=42, worker_idx=0)])

        model = TQC(
            "MlpPolicy", vec_env,
            learning_rate=3e-4, buffer_size=1000,
            learning_starts=10, batch_size=32,
            top_quantiles_to_drop_per_net=2,
            policy_kwargs={
                "net_arch": [64, 64],
                "n_quantiles": 25,
                "n_critics": 3,
            },
            verbose=0,
        )

        t0 = time.time()
        model.learn(total_timesteps=SMOKE_TIMESTEPS)
        elapsed = time.time() - t0

        print(f"  TQC.learn({SMOKE_TIMESTEPS} steps) in {elapsed:.1f}s")

        _pass(f"{elapsed:.1f}s")
        return True
    except Exception as e:
        return _fail(str(e))
    finally:
        if vec_env:
            vec_env.close()


def test_save_load():
    _header("8. Save / Load model")
    vec_env = None
    try:
        import yaml
        import numpy as np
        from stable_baselines3 import SAC
        from stable_baselines3.common.vec_env import DummyVecEnv
        from train import _make_env_fn

        with open("configurations/per_lane_stochastic.yaml") as f:
            cfg = yaml.safe_load(f)
        cfg["sumo"]["episode_duration_s"] = SMOKE_EPISODE_S

        vec_env = DummyVecEnv([_make_env_fn(cfg, seed=99, worker_idx=0)])

        model = SAC(
            "MlpPolicy", vec_env,
            learning_rate=3e-4, buffer_size=1000,
            learning_starts=5, batch_size=32,
            policy_kwargs={"net_arch": [64, 64]},
            verbose=0,
        )
        model.learn(total_timesteps=10)

        tmp = Path(tempfile.mkdtemp(prefix="smoke_save_"))
        save_path = tmp / "test_model"
        model.save(str(save_path))
        print(f"  Saved to {save_path}")

        loaded = SAC.load(str(save_path), env=vec_env)
        obs = vec_env.reset()
        action_orig, _ = model.predict(obs, deterministic=True)
        action_loaded, _ = loaded.predict(obs, deterministic=True)

        match = np.allclose(action_orig, action_loaded, atol=1e-5)
        print(f"  Original action:  {action_orig.flatten()}")
        print(f"  Loaded action:    {action_loaded.flatten()}")
        print(f"  Match: {match}")

        shutil.rmtree(tmp, ignore_errors=True)

        assert match, "Loaded model produces different actions"
        _pass()
        return True
    except Exception as e:
        return _fail(str(e))
    finally:
        if vec_env:
            vec_env.close()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--fast", action="store_true",
                        help="Skip SAC/TQC fit tests (env-only)")
    args = parser.parse_args()

    tests = [
        ("Imports", lambda: test_imports(fast=args.fast)),
        ("Config", test_config),
        ("Env dry-run", test_env_dry_run),
        ("Env live", test_env_live),
    ]
    if not args.fast:
        tests += [
            ("SubprocVecEnv", test_vecenv),
            ("SAC fit", test_sac_fit),
            ("TQC fit", test_tqc_fit),
            ("Save/Load", test_save_load),
        ]

    results = {}
    t_total = time.time()

    for name, fn in tests:
        try:
            results[name] = fn()
        except Exception:
            results[name] = False
            traceback.print_exc()

    elapsed = time.time() - t_total

    print(f"\n{'='*60}")
    print(f"  SMOKE TEST RESULTS ({elapsed:.0f}s)")
    print(f"{'='*60}")
    all_pass = True
    for name, passed in results.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"  {status}  {name}")
        if not passed:
            all_pass = False

    if all_pass:
        print(f"\n  All {len(results)} tests passed. Safe to launch full training.")
    else:
        failed = [n for n, p in results.items() if not p]
        print(f"\n  {len(failed)} test(s) FAILED: {', '.join(failed)}")
        print("  Fix before launching full training.")

    return 0 if all_pass else 1


if __name__ == "__main__":
    sys.exit(main())
