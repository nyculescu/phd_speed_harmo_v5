# sar_components/actions/r44_action_v2.py
"""
Per-lane differential action v2 for ramps_v2 topology.

Supports three configurations:

  Box(4) — per-lane at merge only:
    action[0]: seg_0_before lane 0 VSL (kph) — merge lane, CAV slowDown
    action[1]: seg_0_before lane 1 VSL (kph) — middle lane, CAV slowDown
    action[2]: seg_0_before lane 2 VSL (kph) — fast lane, CAV slowDown
    action[3]: ramp_on_transition VSL (kph)  — ramp CAV slowDown

  Box(5) — Box(4) + physical sign on seg_1_before:
    action[0–3]: same as Box(4)
    action[4]: seg_1_before uniform VSL (kph) — physical sign + radar,
               HDV 92% compliance + CAV 100%

  Box(7) — per-lane at BOTH seg_1_before AND seg_0_before:
    action[0]: seg_1_before lane 0 VSL (kph) — upstream merge lane
    action[1]: seg_1_before lane 1 VSL (kph) — upstream middle
    action[2]: seg_1_before lane 2 VSL (kph) — upstream fast
    action[3]: seg_0_before lane 0 VSL (kph) — merge lane
    action[4]: seg_0_before lane 1 VSL (kph) — middle lane
    action[5]: seg_0_before lane 2 VSL (kph) — fast lane
    action[6]: ramp_on_transition VSL (kph)  — ramp

Constraints enforced at action application:
  - Adjacent lane gradient: |a[i] - a[i+1]| <= 10 kph (MUTCD safety)
    Applied independently per segment.
  - MUTCD step-down between seg_1_before and seg_0_before:
    For each lane k: seg_1_before[k] >= seg_0_before[k] - 16 kph
    (drivers approaching a lower limit must not encounter a >16 kph drop)

seg_2_before always receives min(seg_1_before lanes) as passive propagation.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, Optional, Tuple

import gymnasium as gym
import numpy as np

from core import ActionStrategy, TrafficMetrics
from sar_components.registry import register_action

logger = logging.getLogger(__name__)

_KPH_TO_MS = 1.0 / 3.6
_MAX_ADJACENT_DIFF_KPH = 10.0  # MUTCD inter-lane gradient constraint
_MUTCD_STEP_DOWN_KPH = 16.0   # ~10 mph max step-down between adjacent signs


def _enforce_lane_gradient(lanes: np.ndarray) -> np.ndarray:
    """Clip adjacent lane speeds to differ by at most _MAX_ADJACENT_DIFF_KPH.

    Iterates from L0 outward: L1 is clipped relative to L0, then L2
    relative to L1.  This preserves the agent's L0 intent (merge lane
    is the primary control) and adjusts L1/L2 to respect the constraint.
    """
    out = lanes.copy()
    for i in range(1, len(out)):
        diff = out[i] - out[i - 1]
        if abs(diff) > _MAX_ADJACENT_DIFF_KPH:
            out[i] = out[i - 1] + np.sign(diff) * _MAX_ADJACENT_DIFF_KPH
    return out


def _enforce_step_down(upstream: np.ndarray, downstream: np.ndarray) -> np.ndarray:
    """Ensure upstream[k] >= downstream[k] - MUTCD_STEP_DOWN for each lane.

    Raises upstream lanes if necessary so drivers don't encounter a
    speed drop > 16 kph between adjacent gantries.  Does NOT modify
    downstream — upstream is the one that adjusts.
    """
    out = upstream.copy()
    for k in range(min(len(out), len(downstream))):
        min_allowed = downstream[k] - _MUTCD_STEP_DOWN_KPH
        if out[k] < min_allowed:
            out[k] = min_allowed
    return out


@register_action("r44_action_v2")
class R44ActionV2(ActionStrategy):
    """Per-lane continuous action: Box(4), Box(5), or Box(7)."""

    def _setup(self) -> None:
        self._lane_low = float(self.config.get("lane_low_kph", 60.0))
        self._lane_high = float(self.config.get("lane_high_kph", 120.0))
        self._ramp_low = float(self.config.get("ramp_low_kph", 40.0))
        self._ramp_high = float(self.config.get("ramp_high_kph", 90.0))
        self._use_box5 = bool(self.config.get("use_box5", False))
        self._use_box7 = bool(self.config.get("use_box7", False))

        if self._use_box7 and self._use_box5:
            logger.warning("Both use_box5 and use_box7 are set; using Box(7).")
            self._use_box5 = False

    def get_action_space(self) -> gym.spaces.Space:
        if self._use_box7:
            # 7D: seg_1_before L0/L1/L2 + seg_0_before L0/L1/L2 + ramp
            low = np.array(
                [self._lane_low] * 6 + [self._ramp_low],
                dtype=np.float32,
            )
            high = np.array(
                [self._lane_high] * 6 + [self._ramp_high],
                dtype=np.float32,
            )
        elif self._use_box5:
            # 5D: seg_0_before L0/L1/L2 + ramp + seg_1_before uniform
            low = np.array(
                [self._lane_low] * 3 + [self._ramp_low, self._lane_low],
                dtype=np.float32,
            )
            high = np.array(
                [self._lane_high] * 3 + [self._ramp_high, self._lane_high],
                dtype=np.float32,
            )
        else:
            # 4D: seg_0_before L0/L1/L2 + ramp
            low = np.array(
                [self._lane_low] * 3 + [self._ramp_low], dtype=np.float32
            )
            high = np.array(
                [self._lane_high] * 3 + [self._ramp_high], dtype=np.float32
            )
        return gym.spaces.Box(low=low, high=high, dtype=np.float32)

    def apply_action(
        self,
        action: Any,
        metrics: Any,
    ) -> Tuple[Dict[str, float], float, Optional[str]]:
        act = np.asarray(action, dtype=np.float32).flatten()

        speed_limits_ms: Dict[str, float] = {}

        if self._use_box7:
            # ── Box(7): per-lane on BOTH segments + ramp ────────────
            # action[0:3] = seg_1_before L0/L1/L2
            # action[3:6] = seg_0_before L0/L1/L2
            # action[6]   = ramp
            raw_seg1 = np.clip(act[0:3], self._lane_low, self._lane_high)
            raw_seg0 = np.clip(act[3:6], self._lane_low, self._lane_high)
            ramp_kph = float(np.clip(act[6], self._ramp_low, self._ramp_high))

            # Enforce per-segment inter-lane gradient
            seg1_lanes = _enforce_lane_gradient(raw_seg1)
            seg0_lanes = _enforce_lane_gradient(raw_seg0)

            # Enforce MUTCD step-down: seg1[k] >= seg0[k] - 16 kph
            seg1_lanes = _enforce_step_down(seg1_lanes, seg0_lanes)

            # seg_1_before per-lane
            speed_limits_ms["seg_1_before_L0"] = float(seg1_lanes[0]) * _KPH_TO_MS
            speed_limits_ms["seg_1_before_L1"] = float(seg1_lanes[1]) * _KPH_TO_MS
            speed_limits_ms["seg_1_before_L2"] = float(seg1_lanes[2]) * _KPH_TO_MS

            # seg_0_before per-lane
            speed_limits_ms["seg_0_before_L0"] = float(seg0_lanes[0]) * _KPH_TO_MS
            speed_limits_ms["seg_0_before_L1"] = float(seg0_lanes[1]) * _KPH_TO_MS
            speed_limits_ms["seg_0_before_L2"] = float(seg0_lanes[2]) * _KPH_TO_MS

            # Ramp
            speed_limits_ms["ramp_on_transition"] = ramp_kph * _KPH_TO_MS

            # Upstream passive propagation: seg_2_before gets min of seg_1
            min_seg1_ms = float(seg1_lanes.min()) * _KPH_TO_MS
            speed_limits_ms["seg_2_before"] = min_seg1_ms

            pattern = (f"S1_{seg1_lanes[0]:.0f}_{seg1_lanes[1]:.0f}_{seg1_lanes[2]:.0f}_"
                       f"S0_{seg0_lanes[0]:.0f}_{seg0_lanes[1]:.0f}_{seg0_lanes[2]:.0f}_"
                       f"R{ramp_kph:.0f}")

        elif self._use_box5:
            # ── Box(5): per-lane seg_0 + uniform seg_1 + ramp ──────
            raw_lanes = np.clip(act[:3], self._lane_low, self._lane_high)
            lanes = _enforce_lane_gradient(raw_lanes)
            ramp_kph = float(np.clip(act[3], self._ramp_low, self._ramp_high))

            speed_limits_ms["seg_0_before_L0"] = float(lanes[0]) * _KPH_TO_MS
            speed_limits_ms["seg_0_before_L1"] = float(lanes[1]) * _KPH_TO_MS
            speed_limits_ms["seg_0_before_L2"] = float(lanes[2]) * _KPH_TO_MS
            speed_limits_ms["ramp_on_transition"] = ramp_kph * _KPH_TO_MS

            # Box(5) seg_1_before: independent uniform with MUTCD step-down
            seg1_kph = float(np.clip(act[4], self._lane_low, self._lane_high))
            max_lane_kph = float(lanes.max())
            seg1_kph = max(seg1_kph, max_lane_kph - _MUTCD_STEP_DOWN_KPH)
            speed_limits_ms["seg_1_before"] = seg1_kph * _KPH_TO_MS
            speed_limits_ms["seg_1_before_physical"] = seg1_kph * _KPH_TO_MS

            min_lane_ms = float(lanes.min()) * _KPH_TO_MS
            speed_limits_ms["seg_2_before"] = min_lane_ms

            pattern = f"L{lanes[0]:.0f}_{lanes[1]:.0f}_{lanes[2]:.0f}_R{ramp_kph:.0f}_S1_{seg1_kph:.0f}"

        else:
            # ── Box(4): per-lane seg_0 + ramp only ─────────────────
            raw_lanes = np.clip(act[:3], self._lane_low, self._lane_high)
            lanes = _enforce_lane_gradient(raw_lanes)
            ramp_kph = float(np.clip(act[3], self._ramp_low, self._ramp_high))

            speed_limits_ms["seg_0_before_L0"] = float(lanes[0]) * _KPH_TO_MS
            speed_limits_ms["seg_0_before_L1"] = float(lanes[1]) * _KPH_TO_MS
            speed_limits_ms["seg_0_before_L2"] = float(lanes[2]) * _KPH_TO_MS
            speed_limits_ms["ramp_on_transition"] = ramp_kph * _KPH_TO_MS

            # Passive upstream propagation
            min_lane_ms = float(lanes.min()) * _KPH_TO_MS
            speed_limits_ms["seg_1_before"] = min_lane_ms
            speed_limits_ms["seg_2_before"] = min_lane_ms

            pattern = f"L{lanes[0]:.0f}_{lanes[1]:.0f}_{lanes[2]:.0f}_R{ramp_kph:.0f}"

        return speed_limits_ms, 0.0, pattern
