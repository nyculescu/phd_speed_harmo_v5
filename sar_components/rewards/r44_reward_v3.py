# sar_components/rewards/r44_reward_v3.py
"""
5-term reward function v3 for ramps_v2 topology with per-lane control.

Changes from v2:
  - Adds r_lane_grad: penalises inter-lane speed gaps at seg_0_before.
  - Adds r_merge: rewards matching merge lane (L0) speed to ramp merge speed.
  - Action smoothness expanded from 2D to 4D normalization.
  - Reward weights: w_h=0.40, w_q=0.25, w_a=0.10, w_lg=0.15, w_m=0.10.

Five terms:

  r_harmo       Blended spatial + temporal corridor harmonization (from v2).

  r_q           Throughput penalty at downstream (seg_1_after).

  r_a           Action smoothness penalty (4D L2 norm of normalised action delta).

  r_lane_grad   Inter-lane speed gradient at seg_0_before.
                Penalises max(|L0-L1|, |L1-L2|) / 20 kph.
                Discourages dangerous inter-lane speed differentials that
                cause lane-change conflicts near the merge [MUTCD safety].

  r_merge       Merge speed matching.
                Penalises |L0_speed - ramp_merge_speed| / 30 kph.
                Rewards reducing the speed mismatch at the merge point —
                the primary cause of merge shockwaves (Ghiasi et al. 2019,
                Ko et al. 2020).

  total = w_h * r_harmo + w_q * r_q + w_a * r_a + w_lg * r_lane_grad + w_m * r_merge
"""
from __future__ import annotations

import logging
from typing import Any, Optional

import numpy as np

from core import RewardFunction, RewardSignal, TrafficMetrics
from sar_components.registry import register_reward

logger = logging.getLogger(__name__)

# Action bounds for smoothness normalization (must match r44_action_v2).
# [L0_range, L1_range, L2_range, ramp_range]
_ACTION_RANGE = np.array([60.0, 60.0, 60.0, 50.0], dtype=np.float32)

# Normalization ceilings.
_GRADIENT_NORM = 30.0       # Max adjacent segment speed gradient (kph)
_DS_DELTA_V_NORM = 15.0     # Downstream temporal speed change (kph)
_LANE_GRADIENT_NORM = 20.0  # Max inter-lane speed gap (kph)
_MERGE_DIFF_NORM = 30.0     # Max L0-ramp speed differential (kph)

# Speed floor below which harmonization is not actionable.
_SPEED_FLOOR_KPH = 50.0

# Throughput threshold.
_THROUGHPUT_THRESHOLD = 0.85


@register_reward("r44_reward_v3")
class R44RewardV3(RewardFunction):
    """5-component reward: harmonization, throughput, smoothness, lane gradient, merge match."""

    def _setup(self) -> None:
        weights = self.config.get("reward_weights", {})
        self._w_h = float(weights.get("w_h", 0.40))
        self._w_q = float(weights.get("w_q", 0.25))
        self._w_a = float(weights.get("w_a", 0.10))
        self._w_lg = float(weights.get("w_lg", 0.15))
        self._w_m = float(weights.get("w_m", 0.10))

        self._ref_flow = float(self.config.get("ref_flow_vph", 6000.0))
        self._speed_floor = float(
            self.config.get("speed_floor_kph", _SPEED_FLOOR_KPH)
        )
        self._blend = float(
            self.config.get("harmo_spatial_blend", 0.5)
        )
        self._throughput_threshold = float(
            self.config.get("throughput_threshold", _THROUGHPUT_THRESHOLD)
        )

        self._prev_ds_speed_kph: Optional[float] = None

    def reset(self) -> None:
        self._prev_ds_speed_kph = None

    def calculate(
        self,
        metrics: Any,
        safety_metrics: Optional[Any] = None,
    ) -> RewardSignal:
        m: TrafficMetrics = metrics

        # --- Upstream speeds (aggregate, for spatial gradient) ---
        s2_kph = m.seg_2_before_speed_ms * 3.6
        s1_kph = m.seg_1_before_speed_ms * 3.6
        s0_kph = m.seg_0_before_speed_ms * 3.6
        mean_speed = (s2_kph + s1_kph + s0_kph) / 3.0

        # --- Per-lane speeds at seg_0_before ---
        l0_kph = m.seg_0_before_L0_speed_ms * 3.6
        l1_kph = m.seg_0_before_L1_speed_ms * 3.6
        l2_kph = m.seg_0_before_L2_speed_ms * 3.6

        # === TERM 1: Harmonization (spatial + temporal, from v2) ===

        # Spatial: max adjacent segment gradient
        adj_diff_21 = abs(s2_kph - s1_kph)
        adj_diff_10 = abs(s1_kph - s0_kph)
        max_gradient = max(adj_diff_21, adj_diff_10)

        if mean_speed >= self._speed_floor:
            r_spatial = -min(max_gradient / _GRADIENT_NORM, 1.0)
        else:
            r_speed_recovery = -1.0 + (mean_speed / self._speed_floor)
            r_gradient_penalty = -min(max_gradient / _GRADIENT_NORM, 1.0)
            r_spatial = min(r_speed_recovery, r_gradient_penalty)

        # Temporal: downstream speed stability at seg_0_after
        ds_speed_kph = m.seg_0_after_speed_ms * 3.6

        if self._prev_ds_speed_kph is not None:
            ds_delta_v = abs(ds_speed_kph - self._prev_ds_speed_kph)
            r_temporal = -min(ds_delta_v / _DS_DELTA_V_NORM, 1.0)
        else:
            r_temporal = 0.0

        self._prev_ds_speed_kph = ds_speed_kph

        r_harmo = self._blend * r_spatial + (1.0 - self._blend) * r_temporal

        # === TERM 2: Throughput penalty ===
        if self._ref_flow > 0:
            flow_ratio = m.seg_1_after_flow_vph / self._ref_flow
            if flow_ratio >= self._throughput_threshold:
                r_q = 0.0
            else:
                r_q = -(self._throughput_threshold - flow_ratio) / self._throughput_threshold
        else:
            r_q = 0.0

        # === TERM 3: Action smoothness (4D) ===
        r_a = 0.0
        if m.action is not None and m.prev_action is not None:
            act = np.asarray(m.action, dtype=np.float32)[:4]
            prev = np.asarray(m.prev_action, dtype=np.float32)[:4]
            if len(act) == 4 and len(prev) == 4:
                delta = act - prev
                normalised_delta = delta / _ACTION_RANGE
                r_a = -float(np.clip(np.linalg.norm(normalised_delta), 0.0, 1.0))

        # === TERM 4: Inter-lane speed gradient at seg_0_before ===
        lane_diff_01 = abs(l0_kph - l1_kph)
        lane_diff_12 = abs(l1_kph - l2_kph)
        max_lane_diff = max(lane_diff_01, lane_diff_12)
        r_lane_grad = -min(max_lane_diff / _LANE_GRADIENT_NORM, 1.0)

        # === TERM 5: Merge speed matching (L0 vs ramp) ===
        ramp_merge_kph = m.ramp_on_merge_speed_ms * 3.6
        merge_diff = abs(l0_kph - ramp_merge_kph)
        r_merge = -min(merge_diff / _MERGE_DIFF_NORM, 1.0)

        # === Total ===
        total = (
            self._w_h * r_harmo
            + self._w_q * r_q
            + self._w_a * r_a
            + self._w_lg * r_lane_grad
            + self._w_m * r_merge
        )

        return RewardSignal(
            total=total,
            components={
                "harmonization": r_harmo,
                "spatial": r_spatial,
                "temporal": r_temporal,
                "throughput": r_q,
                "smoothness": r_a,
                "lane_gradient": r_lane_grad,
                "merge_match": r_merge,
            },
        )
