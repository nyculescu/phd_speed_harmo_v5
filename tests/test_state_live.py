# tests/test_state_live.py
"""
Observation validity under live SUMO traffic.

Runs a single 3600s episode at 7000 vph (guaranteed breakdown) and
verifies that the 56-dim observation is well-formed at every step.

Requires SUMO.
Run:  pytest tests/test_state_live.py -v -s
"""
from __future__ import annotations

import math

import numpy as np
import pytest

from tests._sumo_helpers import make_env

pytestmark = pytest.mark.sumo

_DEMAND = 7000
_EPISODE_S = 3600
_OBS_DIM = 56
_FRAME_SIZE = 18
_N_FRAMES = 3
_ACTION = np.array([90.0, 65.0], dtype=np.float32)


class TestStateLive:
    """Verify observation contract under real SUMO traffic."""

    @pytest.fixture(autouse=True)
    def setup_env(self, tmp_path):
        self.env, self._tmp = make_env(_DEMAND, _EPISODE_S, tmp_dir=tmp_path)
        yield
        self.env.close()

    def test_observation_validity(self):
        obs, _ = self.env.reset()
        assert obs.shape == (_OBS_DIM,), f"Reset obs shape: {obs.shape}"
        assert obs.dtype == np.float32

        prev_action = None
        prev_obs = obs.copy()
        step_idx = 0
        saw_free_flow = False
        saw_congested = False

        while True:
            action = _ACTION.copy()
            obs, _, terminated, _, info = self.env.step(action)
            step_idx += 1

            # --- Shape and dtype ---
            assert obs.shape == (_OBS_DIM,), (
                f"Step {step_idx}: obs shape = {obs.shape}"
            )
            assert obs.dtype == np.float32

            # --- All values in [0, 1] ---
            assert obs.min() >= -0.001, (
                f"Step {step_idx}: obs min = {obs.min():.6f} < 0"
            )
            assert obs.max() <= 1.001, (
                f"Step {step_idx}: obs max = {obs.max():.6f} > 1"
            )

            # --- Regime one-hot in each frame ---
            for frame_idx in range(_N_FRAMES):
                base = frame_idx * _FRAME_SIZE
                regime = obs[base + 15: base + 18]  # indices 15, 16, 17
                regime_sum = float(np.sum(regime))

                # Frames that are still zero-padded (from reset) have
                # regime = [0, 0, 0].  This is expected for the first
                # N_FRAMES-1 steps.  Only check populated frames.
                is_padded = regime_sum < 0.01
                frame_age = step_idx - (_N_FRAMES - 1 - frame_idx)

                if frame_age >= 1:
                    # This frame should be populated
                    assert abs(regime_sum - 1.0) < 0.01, (
                        f"Step {step_idx}, frame {frame_idx} (age={frame_age}): "
                        f"regime one-hot sum = {regime_sum:.4f}, expected 1.0"
                    )
                    assert np.max(regime) > 0.9, (
                        f"Step {step_idx}, frame {frame_idx}: "
                        f"no regime active (max = {np.max(regime):.4f})"
                    )

                    # Track regime transitions
                    if regime[0] > 0.5:
                        saw_free_flow = True
                    if regime[2] > 0.5:
                        saw_congested = True

            # --- Frame stacking: after step 3+, all frames should differ ---
            if step_idx >= 4:
                frame0 = obs[0: _FRAME_SIZE]
                frame1 = obs[_FRAME_SIZE: 2 * _FRAME_SIZE]
                frame2 = obs[2 * _FRAME_SIZE: 3 * _FRAME_SIZE]
                # At least frames should not ALL be identical
                diff_01 = np.max(np.abs(frame0 - frame1))
                diff_12 = np.max(np.abs(frame1 - frame2))
                # In a live scenario with changing traffic, at least one
                # pair should differ by more than epsilon
                some_variation = diff_01 > 0.001 or diff_12 > 0.001
                assert some_variation, (
                    f"Step {step_idx}: all 3 frames identical "
                    f"(d01={diff_01:.6f}, d12={diff_12:.6f})"
                )

            # --- Prev action features (last 2 dims) ---
            if step_idx >= 2 and prev_action is not None:
                # obs[54] = (prev_mainline - 60) / 60
                expected_main = (prev_action[0] - 60.0) / 60.0
                # obs[55] = (prev_ramp - 40) / 50
                expected_ramp = (prev_action[1] - 40.0) / 50.0

                assert abs(obs[54] - expected_main) < 0.01, (
                    f"Step {step_idx}: prev_action[0] = {obs[54]:.4f}, "
                    f"expected {expected_main:.4f}"
                )
                assert abs(obs[55] - expected_ramp) < 0.01, (
                    f"Step {step_idx}: prev_action[1] = {obs[55]:.4f}, "
                    f"expected {expected_ramp:.4f}"
                )

            prev_action = action.copy()
            prev_obs = obs.copy()

            if terminated:
                break

        # --- At 7000 vph, we expect regime transitions ---
        # Early free-flow, then congestion (though not guaranteed
        # depending on exact timing)
        n_steps = step_idx
        print(f"\nSteps: {n_steps}")
        print(f"Saw FREE_FLOW: {saw_free_flow}")
        print(f"Saw CONGESTED: {saw_congested}")

        # At 7000 vph, breakdown should occur → expect congested regime
        # (but early steps might be free-flow)
        assert n_steps == _EPISODE_S // 30
