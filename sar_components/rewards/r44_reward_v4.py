# sar_components/rewards/r44_reward_v4.py
"""
5-term reward function v4 — redesigned for learnable gradients.

Changes from v3 (and why):
  v3 had a total signal of ~3 reward points between NC and optimal over
  a full episode. Three of five terms PUNISHED the agent for acting.
  The throughput term had a dead zone above flow_ratio=0.85.
  Normalization ceilings were too high, compressing meaningful
  differences into tiny reward deltas.

  v4 fixes:
    1. Quadratic penalties instead of linear-clipped: small deviations
       produce near-zero penalty, large deviations are amplified.
       This gives the agent a clear gradient to follow.
    2. Continuous throughput term (no dead zone): every bit of flow
       matters, with a smooth log-based bonus above reference.
    3. Lower normalization ceilings calibrated from feasibility data.
    4. Harmonization term focuses on what VSL actually controls:
       upstream speed VARIANCE across segments (σ²), not max gradient.
    5. Merge term rewards REDUCING the L0-ramp differential from the
       NC baseline (~15 kph gap), not penalising any remaining gap.
    6. Scale factor of 10× so episode returns are in [-600, 0] range,
       matching SAC/TQC default hyperparameters.

Five terms:

  r_harmo       Upstream speed variance across seg_2/seg_1/seg_0 +
                per-lane variance at seg_0_before.
                Quadratic: -(σ / σ_ref)².

  r_temporal    Downstream speed stability at seg_0_after.
                Quadratic: -(Δv / Δv_ref)².

  r_throughput  Continuous throughput term (no dead zone).
                Linear: (flow / ref_flow) - 1.0, clipped to [-1, +0.1].

  r_lane_eq     Per-lane speed equalisation at seg_0_before.
                Quadratic: -((max_lane_diff) / lane_ref)².

  r_smooth      Action smoothness (4D L2 norm).
                Quadratic: -(||Δa||/a_ref)².

  total = scale * (w_h * r_harmo + w_t * r_temporal + w_q * r_throughput
                   + w_l * r_lane_eq + w_s * r_smooth)
"""
from __future__ import annotations

import logging
from typing import Any, Optional

import numpy as np

from core import RewardFunction, RewardSignal, TrafficMetrics
from sar_components.registry import register_reward

logger = logging.getLogger(__name__)

# Normalization references — calibrated from feasibility sweep data.
# These are the NC baseline values at 6500 vph (the target operating point).
_SIGMA_REF_KPH = 5.0         # σ across 3 upstream segments at NC ≈ 3 kph; 5 = soft ceiling
_DS_DELTA_REF_KPH = 8.0      # Downstream step-to-step speed change; NC ≈ 4 kph
_LANE_REF_KPH = 15.0         # Max inter-lane gap; NC L0-L2 ≈ 12 kph
_ACTION_RANGE = np.array([60.0, 60.0, 60.0, 50.0], dtype=np.float32)
_ACTION_NORM = 0.5            # Normalised action delta above which penalty saturates

# Scale factor: raw reward per step ∈ [-1, ~0.1].
# × 5 → episode return ∈ [-600, ~+60] over 120 steps.
_SCALE = 5.0


@register_reward("r44_reward_v4")
class R44RewardV4(RewardFunction):
    """5-component reward with quadratic penalties and no dead zones."""

    def _setup(self) -> None:
        weights = self.config.get("reward_weights", {})
        self._w_h = float(weights.get("w_h", 0.35))
        self._w_t = float(weights.get("w_t", 0.20))
        self._w_q = float(weights.get("w_q", 0.25))
        self._w_l = float(weights.get("w_l", 0.15))
        self._w_s = float(weights.get("w_s", 0.05))

        self._ref_flow = float(self.config.get("ref_flow_vph", 6000.0))
        self._scale = float(self.config.get("reward_scale", _SCALE))

        self._prev_ds_speed_kph: Optional[float] = None

    def reset(self) -> None:
        self._prev_ds_speed_kph = None

    def calculate(
        self,
        metrics: Any,
        safety_metrics: Optional[Any] = None,
    ) -> RewardSignal:
        m: TrafficMetrics = metrics

        # --- Upstream segment speeds ---
        s2_kph = m.seg_2_before_speed_ms * 3.6
        s1_kph = m.seg_1_before_speed_ms * 3.6
        s0_kph = m.seg_0_before_speed_ms * 3.6
        upstream_speeds = np.array([s2_kph, s1_kph, s0_kph])

        # --- Per-lane speeds at seg_0_before ---
        l0_kph = m.seg_0_before_L0_speed_ms * 3.6
        l1_kph = m.seg_0_before_L1_speed_ms * 3.6
        l2_kph = m.seg_0_before_L2_speed_ms * 3.6

        # === TERM 1: Harmonization — upstream speed variance ===
        # Combines inter-segment variance with per-lane variance.
        # Low σ = smooth flow = good.
        segment_sigma = float(np.std(upstream_speeds))
        lane_sigma = float(np.std([l0_kph, l1_kph, l2_kph]))
        combined_sigma = (segment_sigma + lane_sigma) / 2.0

        r_harmo = -min((combined_sigma / _SIGMA_REF_KPH) ** 2, 1.0)

        # === TERM 2: Temporal — downstream speed stability ===
        ds_speed_kph = m.seg_0_after_speed_ms * 3.6

        if self._prev_ds_speed_kph is not None:
            ds_delta_v = abs(ds_speed_kph - self._prev_ds_speed_kph)
            r_temporal = -min((ds_delta_v / _DS_DELTA_REF_KPH) ** 2, 1.0)
        else:
            r_temporal = 0.0

        self._prev_ds_speed_kph = ds_speed_kph

        # === TERM 3: Throughput — continuous, no dead zone ===
        if self._ref_flow > 0:
            flow_ratio = m.seg_1_after_flow_vph / self._ref_flow
            # Linear: positive reward for flow above ref, penalty below.
            # Clipped to [-1, +0.1] to prevent throughput from dominating.
            r_throughput = float(np.clip(flow_ratio - 1.0, -1.0, 0.1))
        else:
            r_throughput = 0.0

        # === TERM 4: Lane equalisation — per-lane speed gap ===
        max_lane_diff = max(abs(l0_kph - l1_kph), abs(l1_kph - l2_kph))
        r_lane_eq = -min((max_lane_diff / _LANE_REF_KPH) ** 2, 1.0)

        # === TERM 5: Action smoothness ===
        r_smooth = 0.0
        if m.action is not None and m.prev_action is not None:
            act = np.asarray(m.action, dtype=np.float32)[:4]
            prev = np.asarray(m.prev_action, dtype=np.float32)[:4]
            if len(act) == 4 and len(prev) == 4:
                delta = act - prev
                normalised_delta = delta / _ACTION_RANGE
                norm = float(np.linalg.norm(normalised_delta))
                r_smooth = -min((norm / _ACTION_NORM) ** 2, 1.0)

        # === Total with scale ===
        raw = (
            self._w_h * r_harmo
            + self._w_t * r_temporal
            + self._w_q * r_throughput
            + self._w_l * r_lane_eq
            + self._w_s * r_smooth
        )
        total = self._scale * raw

        return RewardSignal(
            total=total,
            components={
                "harmonization": r_harmo,
                "segment_sigma": segment_sigma,
                "lane_sigma": lane_sigma,
                "temporal": r_temporal,
                "throughput": r_throughput,
                "flow_ratio": m.seg_1_after_flow_vph / self._ref_flow if self._ref_flow > 0 else 0,
                "lane_equalisation": r_lane_eq,
                "max_lane_diff_kph": max_lane_diff,
                "smoothness": r_smooth,
                "raw_unscaled": raw,
            },
        )
