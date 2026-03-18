# sar_components/rewards/r44_reward_v1.py
"""
Reward function v1 for ramps_v1 topology.

Changes from v0:
  - r_v (speed variance at merge zone) replaced by r_harmo (inter-segment
    speed variance across the upstream corridor with a speed floor).
  - Targets deceleration-acceleration reduction, not merge-zone speed.
  - See docs/sac_tqc_argument.md §8 for the empirical justification.

Three terms:

  r_harmo   Upstream corridor speed harmonization.
            Penalises std(speed_s2b, speed_s1b, speed_s0b) when mean speed
            is above a floor.  Below the floor, penalises low speed directly
            to prevent the trivial solution (uniform gridlock at 30 kph).

  r_q       Throughput reward at downstream (seg_1_after).

  r_a       Action smoothness penalty (L2 norm of normalised action delta).

  total = w_h * r_harmo + w_q * r_q + w_a * r_a
"""
from __future__ import annotations

import logging
from typing import Any, Dict, Optional

import numpy as np

from core import RewardFunction, RewardSignal, TrafficMetrics
from sar_components.registry import register_reward

logger = logging.getLogger(__name__)

# Action bounds for smoothness normalization (must match r44_action_v1).
_ACTION_RANGE = np.array([120.0 - 60.0, 90.0 - 40.0], dtype=np.float32)  # [60, 50]

# Normalization ceiling for sigma (kph).  From baseline data: max useful
# sigma ≈ 34 kph at 7000 vph no-control.  30 kph keeps penalty in [-1, 0].
_SIGMA_NORM = 30.0

# Speed floor below which variance reduction is not meaningful.
_SPEED_FLOOR_KPH = 50.0


@register_reward("r44_reward_v1")
class R44RewardV1(RewardFunction):
    """3-term reward: corridor harmonization + throughput + smoothness."""

    def _setup(self) -> None:
        weights = self.config.get("reward_weights", {})
        self._w_h = float(weights.get("w_h", 0.55))
        self._w_q = float(weights.get("w_q", 0.30))
        self._w_a = float(weights.get("w_a", 0.15))
        self._ref_flow = float(self.config.get("ref_flow_vph", 6000.0))
        self._speed_floor = float(self.config.get("speed_floor_kph", _SPEED_FLOOR_KPH))

    def calculate(
        self,
        metrics: Any,
        safety_metrics: Optional[Any] = None,
    ) -> RewardSignal:
        m: TrafficMetrics = metrics

        # --- Upstream corridor harmonization ---
        s2_kph = m.seg_2_before_speed_ms * 3.6
        s1_kph = m.seg_1_before_speed_ms * 3.6
        s0_kph = m.seg_0_before_speed_ms * 3.6

        speeds = np.array([s2_kph, s1_kph, s0_kph])
        mean_speed = float(np.mean(speeds))
        sigma = float(np.std(speeds))

        if mean_speed >= self._speed_floor:
            # Penalise inter-segment variance, normalized to [-1, 0].
            r_harmo = -min(sigma / _SIGMA_NORM, 1.0)
        else:
            # Below floor: penalise low speed.  At mean_speed=0 → r=-1;
            # at mean_speed=floor → r=0.  Smooth linear ramp.
            r_harmo = -1.0 + (mean_speed / self._speed_floor)
            # Also still penalise variance if any, but floor penalty dominates.
            r_harmo = min(r_harmo, -min(sigma / _SIGMA_NORM, 1.0))

        # --- Throughput reward ---
        if self._ref_flow > 0:
            r_q = min(m.seg_1_after_flow_vph / self._ref_flow, 1.0)
        else:
            r_q = 0.0

        # --- Action smoothness penalty ---
        r_a = 0.0
        if m.action is not None and m.prev_action is not None:
            delta = (np.asarray(m.action, dtype=np.float32)
                     - np.asarray(m.prev_action, dtype=np.float32))
            normalised_delta = delta / _ACTION_RANGE
            r_a = -float(np.clip(np.linalg.norm(normalised_delta), 0.0, 1.0))

        total = self._w_h * r_harmo + self._w_q * r_q + self._w_a * r_a

        return RewardSignal(
            total=total,
            components={
                "harmonization": r_harmo,
                "throughput": r_q,
                "smoothness": r_a,
            },
        )
