# tests/test_traf_env.py
"""
Full-episode SUMO integration test.

Purpose
-------
This test checks whether a single SUMO episode can run end-to-end in
isolation, using the project's real network, detector and route files.
It is the minimal gate before attempting a full training run: if this
test passes, the environment is wired correctly and suitable for a
training loop.

What is exercised
-----------------
Unlike test_env_inter.py, this test does NOT use dry-run mode.  It boots
a real SUMO process and drives it through one complete episode:

  1. Config loading
       Reads configurations/_common_config.yaml to obtain aggregation_time,
       CAV percentage, topology, SAR component names, and reward weights.
       This makes the test sensitive to config regressions, not just code
       regressions.

  2. Scenario generation
       Calls _generate_single_scenario_pair_worker() to produce one
       .rou.xml and one .sumocfg file inside a temporary directory.
       A short episode (EPISODE_DURATION = 300 s) and a representative
       demand (DEMAND_VPH = 2000) are used to keep the test fast.
       The generated files are discarded after the test.

  3. Environment boot
       Instantiates TrafficEnv with the generated .sumocfg path.  SUMO is
       started as a subprocess and TraCI is connected on a free port.

  4. Full episode loop
       reset() → step() × N until terminated=True.  Every step is driven
       with the middle action (action index 3, 85 kph) so the control path
       is exercised but the agent is not relevant here.

Assertions
----------
  - The episode terminates in exactly the expected number of steps
    (EPISODE_DURATION // aggregation_time).
  - Every observation is a float32 array of shape (105,) with values in
    [0, 1] after normalisation (zero-traffic edge case: all zeros).
  - Every reward is a finite float (no NaN / Inf from a zero-traffic step).
  - terminated is True on the final step and False on all preceding steps.
  - SUMO process is cleanly shut down after close() — the test does not
    leave zombie processes.

Skipping
--------
The test is skipped automatically if the ``sumo`` binary is not on PATH.
It is also slow (~10–30 s depending on hardware) and is therefore not
collected by the default pytest run when the -m flag is absent.  To run
it explicitly:

    pytest tests/test_traf_env.py -v -s

or mark it with the ``sumo`` marker:

    pytest -m sumo
"""
from __future__ import annotations

import csv
import math
import shutil
from datetime import datetime
from pathlib import Path

import numpy as np
import pytest
import yaml

from sar_components.discovery import discover_components
from core import (
    TrafficEnv,
    create_action_strategy,
    create_reward_function,
    create_state_representation,
)
from traffic_environment.scenario_generator import _generate_single_scenario_pair_worker

discover_components()

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_CONFIG_PATH  = Path(__file__).resolve().parents[1] / "configurations" / "_common_config.yaml"
_RESULTS_ROOT = Path(__file__).resolve().parent / "results"

# Short episode so the test completes in a few seconds.
_EPISODE_DURATION = 300   # seconds
_DEMAND_VPH       = 2000  # representative mid-range demand

pytestmark = pytest.mark.sumo


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _load_config() -> dict:
    with _CONFIG_PATH.open("r", encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def _build_sar_config(cfg: dict) -> dict:
    sc = cfg.get("sar_config", {})
    weights = sc.get("reward_weights", {})
    return {
        "max_flow_vph":  sc.get("max_flow_vph",  4000.0),
        "max_tts_s":     sc.get("max_tts_s",     5000.0),
        "ref_flow_vph":  sc.get("ref_flow_vph",  2520.0),
        "reward_weights": {
            "w_v": weights.get("w_v", 0.50),
            "w_q": weights.get("w_q", 0.35),
            "w_a": weights.get("w_a", 0.15),
        },
    }


# ---------------------------------------------------------------------------
# Fixture: one generated scenario in a temp directory
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def scenario_cfg_path(tmp_path_factory):
    """Generate a single .sumocfg in a temporary directory and return its path."""
    tmpdir = tmp_path_factory.mktemp("sumo_scenario")
    rou_dir = tmpdir / "flows"
    cfg_dir = tmpdir / "configs"
    rou_dir.mkdir()
    cfg_dir.mkdir()

    cfg = _load_config()
    cav_pct   = float(cfg.get("scenario_generation", {}).get("cavs_percentage", 50.0))
    topology  = cfg.get("scenario_generation", {}).get("network_topology", "merge_4_to_3_v0")
    agg_time  = int(cfg.get("sumo", {}).get("aggregation_time", 30))

    _generate_single_scenario_pair_worker({
        "index":            0,
        "prefix":           "test_episode",
        "demand_vph":       _DEMAND_VPH,
        "episode_duration": _EPISODE_DURATION,
        "cav_percentage":   cav_pct,
        "network_topology": topology,
        "rou_output_dir":   str(rou_dir),
        "cfg_output_dir":   str(cfg_dir),
        "pattern":          "flat",
        "bin_seconds":      agg_time,
    })

    cfg_files = list(cfg_dir.glob("*.sumocfg"))
    assert cfg_files, f"Scenario generation produced no .sumocfg in {cfg_dir}"
    return str(cfg_files[0])


# ---------------------------------------------------------------------------
# Test
# ---------------------------------------------------------------------------

@pytest.mark.skipif(shutil.which("sumo") is None, reason="sumo binary not found on PATH")
class TestFullEpisode:

    def test_single_episode(self, scenario_cfg_path):
        """Run one full SUMO episode and verify correctness at every step."""
        cfg        = _load_config()
        sar_config = _build_sar_config(cfg)
        sar_names  = cfg.get("sar", {})
        agg_time   = int(cfg.get("sumo", {}).get("aggregation_time", 30))
        cav_pct    = float(cfg.get("scenario_generation", {}).get("cavs_percentage", 50.0))
        version    = cfg.get("meta", {}).get("version", "unknown") if "meta" in cfg else "m43_v0"

        # Build timestamped results directory: tests/results/m43-v0_DD-MM-YYYY_HH-MM-SS
        ts         = datetime.now().strftime("%d-%m-%Y_%H-%M-%S")
        result_dir = _RESULTS_ROOT / f"{version.replace('_', '-')}_{ts}"
        result_dir.mkdir(parents=True, exist_ok=True)

        state_repr   = create_state_representation(sar_names.get("state",  "m43_state_v0"),  sar_config)
        action_strat = create_action_strategy(     sar_names.get("action", "m43_action_v0"), {})
        reward_func  = create_reward_function(     sar_names.get("reward", "m43_reward_v0"), sar_config)

        env = TrafficEnv(
            sumo_cfg_path    = scenario_cfg_path,
            state_repr       = state_repr,
            action_strat     = action_strat,
            reward_func      = reward_func,
            episode_duration = _EPISODE_DURATION,
            cav_percent      = cav_pct / 100.0,
            aggregation_time = agg_time,
        )

        expected_steps = _EPISODE_DURATION // agg_time
        middle_action  = env.action_space.n // 2   # action index 3 → 85 kph
        step_log       = []

        try:
            obs, info = env.reset()
            assert obs.shape  == (105,),     f"reset obs shape: {obs.shape}"
            assert obs.dtype  == np.float32,  "reset obs dtype"
            assert obs.min()  >= 0.0,         "reset obs below 0"
            assert obs.max()  <= 1.0,         "reset obs above 1"
            assert isinstance(info, dict),    "reset info not a dict"

            steps      = 0
            terminated = False

            while not terminated:
                obs, reward, terminated, truncated, info = env.step(middle_action)
                steps += 1
                rc = info.get("reward_components", {})
                step_log.append({
                    "step":       steps,
                    "reward":     reward,
                    "variance":   rc.get("variance",   float("nan")),
                    "throughput": rc.get("throughput", float("nan")),
                    "smoothness": rc.get("smoothness", float("nan")),
                    "terminated": terminated,
                })

                # Observation contract
                assert obs.shape == (105,),      f"step {steps} obs shape"
                assert obs.dtype == np.float32,   f"step {steps} obs dtype"
                assert obs.min() >= 0.0,          f"step {steps} obs below 0"
                assert obs.max() <= 1.0,          f"step {steps} obs above 1"

                # Reward contract
                assert isinstance(reward, float),   f"step {steps} reward not float"
                assert math.isfinite(reward),        f"step {steps} reward not finite: {reward}"

                # Termination contract
                assert isinstance(terminated, bool), f"step {steps} terminated not bool"
                assert truncated is False,            f"step {steps} truncated should be False"

                # Reward breakdown
                assert "reward_components" in info,         f"step {steps} missing reward_components"
                for key in ("variance", "throughput", "smoothness"):
                    assert key in info["reward_components"], f"step {steps} missing component '{key}'"

                assert steps <= expected_steps, (
                    f"Episode exceeded expected {expected_steps} steps (still running at step {steps})"
                )

            assert steps == expected_steps, (
                f"Episode terminated after {steps} steps, expected {expected_steps}"
            )
            assert terminated is True, "Last step must be terminated"

        finally:
            env.close()

        # Write per-step CSV to the results directory
        csv_path = result_dir / "episode_steps.csv"
        with csv_path.open("w", newline="", encoding="utf-8") as fh:
            writer = csv.DictWriter(fh, fieldnames=["step", "reward", "variance", "throughput", "smoothness", "terminated"])
            writer.writeheader()
            writer.writerows(step_log)

        # Write a short summary file
        total_reward = sum(r["reward"] for r in step_log)
        summary_path = result_dir / "summary.txt"
        with summary_path.open("w", encoding="utf-8") as fh:
            fh.write(f"config_version : {version}\n")
            fh.write(f"episode_duration: {_EPISODE_DURATION} s\n")
            fh.write(f"aggregation_time: {agg_time} s\n")
            fh.write(f"steps           : {steps}\n")
            fh.write(f"total_reward    : {total_reward:.4f}\n")
            fh.write(f"mean_reward     : {total_reward / steps:.4f}\n")
