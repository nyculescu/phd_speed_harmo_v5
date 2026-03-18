# tests/test_reward_e2e_verification.py
"""
End-to-end reward verification: hand-compute reward from raw E1 data
and compare against what the environment returns.

This is the strongest pre-training validation test.  It verifies the
full chain: SUMO E1 → _collect_metrics() → TrafficMetrics → reward_func
.calculate() → RewardSignal.  If this test passes, the reward the agent
receives during training is mathematically correct.

Methodology:
  1. Run a 600s episode at 6500 vph with constant 90/65 kph action.
  2. At each step, INDEPENDENTLY read the same E1 detectors that
     _collect_metrics() reads and compute the expected reward by hand.
  3. Assert the environment's reported reward matches the hand-computed
     value within a tight tolerance.

Requires SUMO.
Run:  pytest tests/test_reward_e2e_verification.py -v -s
"""
from __future__ import annotations

import math
import os
import socket
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np
import pytest

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT))

_SUMO_TOOLS = os.path.join(os.environ.get("SUMO_HOME", "/usr/share/sumo"), "tools")
if _SUMO_TOOLS not in sys.path:
    sys.path.insert(0, _SUMO_TOOLS)

from tests._sumo_helpers import make_env

pytestmark = pytest.mark.sumo

# ---- Constants matching the reward function and env ----
_GRADIENT_NORM = 30.0
_DS_DELTA_V_NORM = 15.0
_SPEED_FLOOR_KPH = 50.0
_BLEND = 0.5
_THROUGHPUT_THRESHOLD = 0.85
_REF_FLOW_VPH = 6000.0
_W_H = 0.55
_W_Q = 0.30
_W_A = 0.15
_ACTION_RANGE = np.array([60.0, 50.0], dtype=np.float32)  # [120-60, 90-40]

_DEMAND = 6500
_EPISODE_S = 600  # 20 steps — enough to verify, fast enough to iterate
_AGG_TIME = 30
_ACTION = np.array([90.0, 65.0], dtype=np.float32)

# Segments and lanes (must match env_interact.py exactly)
_SEGMENT_LANES = {
    "seg_3_before": 3, "seg_2_before": 3, "seg_1_before": 3, "seg_0_before": 3,
    "seg_0_after": 4, "seg_1_after": 3,
    "ramp_on_approach": 1, "ramp_on_transition": 1, "ramp_on_merge": 1,
    "ramp_off_diverge": 1, "ramp_off_transition": 1, "ramp_off_departure": 1,
}
_DET_POS = "exit"


def _det_ids(seg: str, n_lanes: int) -> List[str]:
    """Replicate env_interact._det_ids()."""
    return [f"flow_loop_{seg}_{i}_{_DET_POS}" for i in range(n_lanes)]


def _read_e1_raw(seg: str, n_lanes: int) -> Tuple[float, float, float]:
    """
    Read E1 detectors for one segment — replicating _collect_metrics._read()
    EXACTLY, including the weighted-mean speed logic and the max(0, spd) clip.

    Returns (flow_vph, speed_ms, occ_pct).
    """
    import traci

    counts, speeds, occs = [], [], []
    for det_id in _det_ids(seg, n_lanes):
        cnt = float(traci.inductionloop.getLastIntervalVehicleNumber(det_id))
        spd = float(traci.inductionloop.getLastIntervalMeanSpeed(det_id))
        occ = float(traci.inductionloop.getLastIntervalOccupancy(det_id))
        counts.append(cnt)
        speeds.append(max(0.0, spd))
        occs.append(occ)

    flow_vph = float(sum(counts)) * (3600.0 / _AGG_TIME)
    total_cnt = sum(counts)
    if total_cnt > 1e-6:
        speed_ms = float(sum(c * s for c, s in zip(counts, speeds)) / total_cnt)
    else:
        speed_ms = float(np.mean(speeds)) if speeds else 0.0
    occ_pct = float(np.mean(occs)) if occs else 0.0
    return flow_vph, speed_ms, occ_pct


def _compute_expected_reward(
    s2_speed_ms: float,
    s1_speed_ms: float,
    s0_speed_ms: float,
    ds_speed_ms: float,
    ds1_flow_vph: float,
    action: np.ndarray,
    prev_action,
    prev_ds_speed_kph,
) -> Tuple[float, Dict[str, float], float]:
    """
    Hand-compute the reward from raw E1 readings.

    Returns (total_reward, components_dict, new_prev_ds_speed_kph).
    """
    s2_kph = s2_speed_ms * 3.6
    s1_kph = s1_speed_ms * 3.6
    s0_kph = s0_speed_ms * 3.6
    ds_kph = ds_speed_ms * 3.6

    mean_speed = (s2_kph + s1_kph + s0_kph) / 3.0

    # --- Spatial ---
    adj_21 = abs(s2_kph - s1_kph)
    adj_10 = abs(s1_kph - s0_kph)
    max_gradient = max(adj_21, adj_10)

    if mean_speed >= _SPEED_FLOOR_KPH:
        r_spatial = -min(max_gradient / _GRADIENT_NORM, 1.0)
    else:
        r_recovery = -1.0 + (mean_speed / _SPEED_FLOOR_KPH)
        r_grad = -min(max_gradient / _GRADIENT_NORM, 1.0)
        r_spatial = min(r_recovery, r_grad)

    # --- Temporal ---
    if prev_ds_speed_kph is not None:
        delta_v = abs(ds_kph - prev_ds_speed_kph)
        r_temporal = -min(delta_v / _DS_DELTA_V_NORM, 1.0)
    else:
        r_temporal = 0.0

    # --- Harmonization blend ---
    r_harmo = _BLEND * r_spatial + (1.0 - _BLEND) * r_temporal

    # --- Throughput ---
    if _REF_FLOW_VPH > 0:
        flow_ratio = ds1_flow_vph / _REF_FLOW_VPH
        if flow_ratio >= _THROUGHPUT_THRESHOLD:
            r_q = 0.0
        else:
            r_q = -(_THROUGHPUT_THRESHOLD - flow_ratio) / _THROUGHPUT_THRESHOLD
    else:
        r_q = 0.0

    # --- Smoothness ---
    r_a = 0.0
    if prev_action is not None:
        delta = (action - np.asarray(prev_action, dtype=np.float32)) / _ACTION_RANGE
        r_a = -float(np.clip(np.linalg.norm(delta), 0.0, 1.0))

    total = _W_H * r_harmo + _W_Q * r_q + _W_A * r_a

    return total, {
        "harmonization": r_harmo,
        "spatial": r_spatial,
        "temporal": r_temporal,
        "throughput": r_q,
        "smoothness": r_a,
    }, ds_kph


class TestRewardE2EVerification:

    @pytest.fixture(autouse=True)
    def setup_env(self, tmp_path):
        self.env, self._tmp = make_env(_DEMAND, _EPISODE_S, tmp_dir=tmp_path)
        yield
        self.env.close()

    def test_reward_matches_hand_computation(self):
        """
        At each step, independently read E1 detectors and hand-compute
        the expected reward.  Assert it matches the env's output.
        """
        import traci

        obs, _ = self.env.reset()

        prev_action = None
        prev_ds_speed_kph = None
        step_idx = 0
        max_error = 0.0
        mismatches = []

        while True:
            action = _ACTION.copy()
            obs, env_reward, terminated, _, info = self.env.step(action)
            step_idx += 1

            env_comps = info["reward_components"]

            # --- Read raw E1 data independently ---
            _, s2_speed_ms, _ = _read_e1_raw("seg_2_before", 3)
            _, s1_speed_ms, _ = _read_e1_raw("seg_1_before", 3)
            _, s0_speed_ms, _ = _read_e1_raw("seg_0_before", 3)
            _, ds_speed_ms, _ = _read_e1_raw("seg_0_after", 4)
            ds1_flow_vph, _, _ = _read_e1_raw("seg_1_after", 3)

            # --- Hand-compute expected reward ---
            expected_total, expected_comps, new_ds_kph = _compute_expected_reward(
                s2_speed_ms, s1_speed_ms, s0_speed_ms,
                ds_speed_ms, ds1_flow_vph,
                action, prev_action, prev_ds_speed_kph,
            )

            # --- Compare each component ---
            for key in ("spatial", "temporal", "throughput",
                        "smoothness", "harmonization"):
                env_val = env_comps[key]
                exp_val = expected_comps[key]
                err = abs(env_val - exp_val)
                if err > 0.001:
                    mismatches.append(
                        f"Step {step_idx}, {key}: env={env_val:.6f}, "
                        f"expected={exp_val:.6f}, err={err:.6f}"
                    )

            # --- Compare total ---
            total_err = abs(env_reward - expected_total)
            max_error = max(max_error, total_err)
            if total_err > 0.001:
                mismatches.append(
                    f"Step {step_idx}, TOTAL: env={env_reward:.6f}, "
                    f"expected={expected_total:.6f}, err={total_err:.6f}"
                )

            prev_action = action.copy()
            prev_ds_speed_kph = new_ds_kph

            if terminated:
                break

        # --- Report ---
        print(f"\n  Steps verified: {step_idx}")
        print(f"  Max total error: {max_error:.8f}")
        print(f"  Component mismatches (>0.001): {len(mismatches)}")
        if mismatches:
            for m in mismatches[:20]:
                print(f"    {m}")

        assert len(mismatches) == 0, (
            f"{len(mismatches)} reward mismatches between env and hand "
            f"computation.  First: {mismatches[0]}"
        )

    def test_temporal_tracks_downstream_not_upstream(self):
        """
        Verify that the temporal term responds to downstream speed changes
        and NOT to upstream speed changes caused by the agent's VSL action.

        Run 2 steps: step 1 with 120 kph (no restriction), step 2 with
        70 kph (heavy restriction).  The upstream speeds will change
        dramatically between steps, but the temporal term should only
        reflect the downstream (seg_0_after) speed change.
        """
        import traci

        obs, _ = self.env.reset()

        # Step 1: no restriction
        action_1 = np.array([120.0, 90.0], dtype=np.float32)
        obs, _, _, _, info_1 = self.env.step(action_1)
        # First step: temporal = 0 (no previous window)
        assert abs(info_1["reward_components"]["temporal"]) < 0.001, (
            f"Step 1 temporal should be 0, got "
            f"{info_1['reward_components']['temporal']:.6f}"
        )

        # Read downstream speed after step 1
        _, ds_speed_ms_1, _ = _read_e1_raw("seg_0_after", 4)
        ds_kph_1 = ds_speed_ms_1 * 3.6

        # Step 2: heavy restriction (upstream speeds will drop)
        action_2 = np.array([70.0, 40.0], dtype=np.float32)
        obs, _, _, _, info_2 = self.env.step(action_2)

        # Read downstream speed after step 2
        _, ds_speed_ms_2, _ = _read_e1_raw("seg_0_after", 4)
        ds_kph_2 = ds_speed_ms_2 * 3.6

        # Hand-compute expected temporal
        ds_delta = abs(ds_kph_2 - ds_kph_1)
        expected_temporal = -min(ds_delta / _DS_DELTA_V_NORM, 1.0)

        actual_temporal = info_2["reward_components"]["temporal"]
        err = abs(actual_temporal - expected_temporal)

        print(f"\n  DS speed step 1: {ds_kph_1:.1f} kph")
        print(f"  DS speed step 2: {ds_kph_2:.1f} kph")
        print(f"  DS delta: {ds_delta:.1f} kph")
        print(f"  Expected temporal: {expected_temporal:.6f}")
        print(f"  Actual temporal:   {actual_temporal:.6f}")
        print(f"  Error: {err:.8f}")

        # Also read upstream to show it changed but wasn't used
        _, s0_ms_1, _ = _read_e1_raw("seg_0_before", 3)
        print(f"  Upstream seg_0_before speed: {s0_ms_1 * 3.6:.1f} kph "
              f"(changed due to VSL, but NOT used in temporal)")

        assert err < 0.001, (
            f"Temporal component mismatch: env={actual_temporal:.6f}, "
            f"expected={expected_temporal:.6f}, err={err:.6f}"
        )
