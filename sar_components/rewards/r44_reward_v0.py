# sar_components/rewards/r44_reward_v0.py
"""
Reward function for ramps_v1 topology (r44 = ramp, 4 merging lanes, 4 post-merge).

Three terms following the MARVEL deployment structure [R10]:

  r_v  Speed variance penalty at the weaving zone (seg_0_after).
       Measures deviation from a target speed — penalises both congestion
       (speed too low) and over-restriction (speed too low from VSL).

  r_q  Throughput reward at the downstream section (seg_1_after).
       Positive reward for maintaining flow relative to a reference.

  r_a  Action smoothness penalty (L2 distance between consecutive actions).
       Discourages oscillating VSL commands.

  total = w_v * r_v + w_q * r_q + w_a * r_a
"""
from __future__ import annotations

import logging
from typing import Any, Dict, Optional

import numpy as np

from core import RewardFunction, RewardSignal, TrafficMetrics
from sar_components.registry import register_reward

logger = logging.getLogger(__name__)

# Action bounds for normalization of smoothness term.
_ACTION_RANGE = np.array([130.0 - 60.0, 90.0 - 40.0], dtype=np.float32)  # [70, 50]


@register_reward("r44_reward_v0")
class R44RewardV0(RewardFunction):
    """3-term reward: speed variance + throughput + smoothness."""

    def _setup(self) -> None:
        weights = self.config.get("reward_weights", {})
        self._w_v = float(weights.get("w_v", 0.50))
        self._w_q = float(weights.get("w_q", 0.35))
        self._w_a = float(weights.get("w_a", 0.15))
        self._ref_flow = float(self.config.get("ref_flow_vph", 5000.0))
        self._target_speed_kph = float(self.config.get("target_speed_kph", 80.0))

    def calculate(
        self,
        metrics: Any,
        safety_metrics: Optional[Any] = None,
    ) -> RewardSignal:
        m: TrafficMetrics = metrics

        # --- Speed variance penalty ---
        # Deviation of weaving zone speed from target, normalized to ~[-1, 0].
        weaving_speed_kph = m.seg_0_after_speed_ms * 3.6
        target = self._target_speed_kph
        # Squared deviation, normalised by target² so dimensionless.
        if target > 0:
            deviation = ((weaving_speed_kph - target) / target) ** 2
        else:
            deviation = 0.0
        r_v = -min(deviation, 1.0)  # clamp to [-1, 0]

        # --- Throughput reward ---
        # Fraction of downstream flow relative to reference. Positive [0, 1].
        if self._ref_flow > 0:
            r_q = min(m.seg_1_after_flow_vph / self._ref_flow, 1.0)
        else:
            r_q = 0.0

        # --- Action smoothness penalty ---
        # Normalised L2 distance between consecutive actions. In [-1, 0].
        r_a = 0.0
        if m.action is not None and m.prev_action is not None:
            delta = (np.asarray(m.action, dtype=np.float32)
                     - np.asarray(m.prev_action, dtype=np.float32))
            normalised_delta = delta / _ACTION_RANGE
            r_a = -float(np.clip(np.linalg.norm(normalised_delta), 0.0, 1.0))

        total = self._w_v * r_v + self._w_q * r_q + self._w_a * r_a

        return RewardSignal(
            total=total,
            components={
                "variance": r_v,
                "throughput": r_q,
                "smoothness": r_a,
            },
        )
