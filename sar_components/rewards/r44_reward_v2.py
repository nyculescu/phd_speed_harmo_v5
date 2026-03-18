# sar_components/rewards/r44_reward_v2.py
"""
Reward function v2 for ramps_v1 topology.

Changes from v1:
  - Splits the harmonization term into two sub-components:
      r_spatial   inter-segment speed variance (v1's σ across 3 segments)
      r_temporal  mean absolute speed change between consecutive E1 windows
                  across the 3 upstream segments (captures stop-and-go)
  - r_harmo = blend * r_spatial + (1 - blend) * r_temporal
  - See docs/sac_tqc_argument.md §8 for the original justification and
    the "reward proxy gap" analysis that motivated this v2.

Rationale for the temporal term:
  v1's inter-segment σ correlates with avg|a| up to ~7000 vph, but breaks
  at 7500+ vph where all segments congest uniformly (low σ) while stop-and-go
  dynamics within each segment keep avg|a| high.  The temporal term captures
  this: if a segment's E1 speed drops 20 kph between consecutive 30 s windows,
  vehicles in that segment underwent significant deceleration — regardless of
  whether other segments show the same speed.

  The mean absolute speed change across consecutive windows is a macroscopic
  proxy for the microscopic mean absolute acceleration avg|a|.  The proxy
  relationship:
    Δv_segment / Δt ≈ mean acceleration over that window
  where Δt = 30 s (aggregation time).  This is the same quantity used by
  emission models (MOVES, HBEFA) at macroscopic granularity.

  Academic grounding:
  - Hua & Fan (2024, Physica A, §3.1): reward = -θ_t (cumulative emergency
    deceleration).  Our temporal term approximates this at macroscopic level.
  - SPECIALIST (Hegyi et al., 2008): VSL activation triggers when speed change
    exceeds a threshold — the temporal derivative is the activation signal.

Four terms:

  r_harmo   Blended spatial + temporal corridor harmonization.

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
_ACTION_RANGE = np.array([120.0 - 60.0, 90.0 - 40.0], dtype=np.float32)

# Normalization ceiling for spatial sigma (kph).
_SIGMA_NORM = 30.0

# Normalization ceiling for temporal speed change (kph).
# From baseline data: at 7000 vph no-control, per-window speed drops of
# 20–30 kph are common during breakdown onset.  15 kph maps "moderate
# stop-and-go" to penalty ≈ -1.0.
_DELTA_V_NORM = 15.0

# Speed floor below which variance reduction is not meaningful.
_SPEED_FLOOR_KPH = 50.0

# Default blend: 0.5 = equal weight spatial and temporal.
_DEFAULT_BLEND = 0.5


@register_reward("r44_reward_v2")
class R44RewardV2(RewardFunction):
    """4-component reward: spatial + temporal harmonization, throughput, smoothness."""

    def _setup(self) -> None:
        weights = self.config.get("reward_weights", {})
        self._w_h = float(weights.get("w_h", 0.55))
        self._w_q = float(weights.get("w_q", 0.30))
        self._w_a = float(weights.get("w_a", 0.15))
        self._ref_flow = float(self.config.get("ref_flow_vph", 6000.0))
        self._speed_floor = float(
            self.config.get("speed_floor_kph", _SPEED_FLOOR_KPH)
        )
        self._blend = float(
            self.config.get("harmo_spatial_blend", _DEFAULT_BLEND)
        )

        # Previous-window speeds for temporal delta (reset in reset()).
        self._prev_speeds_kph: Optional[np.ndarray] = None

    def reset(self) -> None:
        self._prev_speeds_kph = None

    def calculate(
        self,
        metrics: Any,
        safety_metrics: Optional[Any] = None,
    ) -> RewardSignal:
        m: TrafficMetrics = metrics

        # --- Current upstream speeds ---
        s2_kph = m.seg_2_before_speed_ms * 3.6
        s1_kph = m.seg_1_before_speed_ms * 3.6
        s0_kph = m.seg_0_before_speed_ms * 3.6

        speeds = np.array([s2_kph, s1_kph, s0_kph])
        mean_speed = float(np.mean(speeds))
        sigma = float(np.std(speeds))

        # --- Spatial component (inter-segment variance) ---
        if mean_speed >= self._speed_floor:
            r_spatial = -min(sigma / _SIGMA_NORM, 1.0)
        else:
            r_spatial = -1.0 + (mean_speed / self._speed_floor)
            r_spatial = min(r_spatial, -min(sigma / _SIGMA_NORM, 1.0))

        # --- Temporal component (inter-window speed change) ---
        if self._prev_speeds_kph is not None:
            # Mean absolute speed change across the 3 upstream segments
            # between this window and the previous one.
            delta_v = np.abs(speeds - self._prev_speeds_kph)
            mean_delta_v = float(np.mean(delta_v))
            r_temporal = -min(mean_delta_v / _DELTA_V_NORM, 1.0)
        else:
            # First step after reset — no previous window available.
            r_temporal = 0.0

        self._prev_speeds_kph = speeds.copy()

        # --- Blended harmonization ---
        r_harmo = self._blend * r_spatial + (1.0 - self._blend) * r_temporal

        # --- Throughput reward ---
        if self._ref_flow > 0:
            r_q = min(m.seg_1_after_flow_vph / self._ref_flow, 1.0)
        else:
            r_q = 0.0

        # --- Action smoothness penalty ---
        r_a = 0.0
        if m.action is not None and m.prev_action is not None:
            delta = (
                np.asarray(m.action, dtype=np.float32)
                - np.asarray(m.prev_action, dtype=np.float32)
            )
            normalised_delta = delta / _ACTION_RANGE
            r_a = -float(np.clip(np.linalg.norm(normalised_delta), 0.0, 1.0))

        total = self._w_h * r_harmo + self._w_q * r_q + self._w_a * r_a

        return RewardSignal(
            total=total,
            components={
                "harmonization": r_harmo,
                "spatial": r_spatial,
                "temporal": r_temporal,
                "throughput": r_q,
                "smoothness": r_a,
            },
        )
