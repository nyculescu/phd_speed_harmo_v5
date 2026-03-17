# sar_components/rewards/m43_reward_v0.py
"""
3-term reward for merge_4_to_3_v0 (v5 SAR framework).

Design principles (see docs/speed_harmo_approach_v0.md):

    r = −w_v · σ²_norm  +  w_q · Δflow_norm  −  w_a · smoothness_norm

Term 1 — speed variance penalty (primary objective):
    Variance of the three upstream E1 space-mean speeds (m/s).
    Minimising this is equivalent to minimising shockwave intensity,
    which is the stated PhD objective (reducing braking/acceleration
    intensity as a fuel consumption proxy).

Term 2 — throughput delta reward (mobility constraint):
    Normalised deviation of the actual downstream flow from the
    no-control reference flow.  Positive when VSL improves throughput
    (rare but possible at high demand), negative when it reduces it.
    This provides a soft mobility constraint without a hard budget penalty.

Term 3 — action smoothness penalty:
    Penalises large step changes in the posted speed level to avoid
    oscillating VSL commands that confuse CAVs and HDVs.

Removed from v4: authority_gate, mobility_budget constraint,
w_tts, w_ttt, w_queue, w_shock, w_tail_ttt, w_tail_tts, w_low_speed.

Grounded in: MARVEL (Zhang et al., 2023) uses an equivalent 3-term
reward structure and achieved 32.7% speed variation reduction in
real-world I-24 deployment.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

import numpy as np

from core import MAX_SPEED_KPH, RewardFunction, RewardSignal, TrafficMetrics
from sar_components.registry import register_reward

logger = logging.getLogger(__name__)

_MAX_SPEED_MS: float = MAX_SPEED_KPH / 3.6          # ≈ 27.78 m/s
_MAX_VARIANCE_MS2: float = _MAX_SPEED_MS ** 2        # normalises σ² to [0,1]

# Number of speed levels in m43_action_v0 (7 levels → max index delta = 6).
_N_ACTION_LEVELS: int = 7
_MAX_ACTION_DELTA: float = float(_N_ACTION_LEVELS - 1)  # 6.0


@register_reward("m43_reward_v0")
class Merge43RewardV0(RewardFunction):
    """
    3-term reward: speed variance + throughput delta + action smoothness.

    Config keys (all under ``sar_config``):

    reward_weights_v9:
        w_v: 0.50    # weight for speed-variance penalty
        w_q: 0.35    # weight for throughput-delta reward
        w_a: 0.15    # weight for action-smoothness penalty

    ref_flow_vph: 2520.0   # no-control reference downstream flow (veh/h)
    max_flow_vph: 4000.0   # normaliser for flow values
    """

    def _setup(self) -> None:
        weights_cfg: Dict[str, Any] = self.config.get("reward_weights_v9", {})
        self._w_v: float = float(weights_cfg.get("w_v", 0.50))
        self._w_q: float = float(weights_cfg.get("w_q", 0.35))
        self._w_a: float = float(weights_cfg.get("w_a", 0.15))

        self._ref_flow_vph: float = float(self.config.get("ref_flow_vph", 2520.0))
        self._max_flow_vph: float = float(self.config.get("max_flow_vph", 4000.0))

        logger.info(
            "Merge43RewardV0 initialised: w_v=%.2f w_q=%.2f w_a=%.2f "
            "ref_flow=%.1f vph max_flow=%.1f vph",
            self._w_v, self._w_q, self._w_a,
            self._ref_flow_vph, self._max_flow_vph,
        )

    def calculate(
        self,
        metrics: TrafficMetrics,
        safety_metrics: Optional[Any] = None,
    ) -> RewardSignal:
        # ------------------------------------------------------------------
        # Term 1: upstream speed variance (lower = smoother traffic)
        # ------------------------------------------------------------------
        us0_spd = float(getattr(metrics, "avg_speed_upstream_s0", 0.0))  # m/s
        us1_spd = float(getattr(metrics, "avg_speed_upstream_s1", 0.0))
        us2_spd = float(getattr(metrics, "avg_speed_upstream_s2", 0.0))

        sigma2 = float(np.var([us0_spd, us1_spd, us2_spd]))
        sigma2_norm = float(np.clip(sigma2 / max(_MAX_VARIANCE_MS2, 1e-9), 0.0, 1.0))

        # ------------------------------------------------------------------
        # Term 2: downstream throughput delta vs no-control reference
        # ------------------------------------------------------------------
        ds0_flow = float(getattr(metrics, "flow_rate_vph_ds0", 0.0))
        if self._ref_flow_vph > 0.0:
            delta_flow = (ds0_flow - self._ref_flow_vph) / self._ref_flow_vph
        else:
            delta_flow = 0.0
        delta_flow_clipped = float(np.clip(delta_flow, -1.0, 1.0))

        # ------------------------------------------------------------------
        # Term 3: action smoothness penalty
        # ------------------------------------------------------------------
        action_idx      = int(metrics.action_idx)      if metrics.action_idx      is not None else (_N_ACTION_LEVELS - 1)
        prev_action_idx = int(metrics.prev_action_idx) if metrics.prev_action_idx is not None else action_idx

        action_delta = abs(action_idx - prev_action_idx)
        smoothness_norm = float(np.clip(action_delta / max(_MAX_ACTION_DELTA, 1.0), 0.0, 1.0))

        # ------------------------------------------------------------------
        # Combine
        # ------------------------------------------------------------------
        variance_term    = -self._w_v * sigma2_norm
        throughput_term  =  self._w_q * delta_flow_clipped
        smoothness_term  = -self._w_a * smoothness_norm

        total = float(np.clip(
            variance_term + throughput_term + smoothness_term,
            -1.5, 1.0,
        ))

        return RewardSignal(
            total=total,
            components={
                "variance":   float(variance_term),
                "throughput": float(throughput_term),
                "smoothness": float(smoothness_term),
                # Diagnostics (not weighted)
                "sigma2_norm":       sigma2_norm,
                "delta_flow_clipped": delta_flow_clipped,
                "smoothness_raw":     smoothness_norm,
            },
        )
