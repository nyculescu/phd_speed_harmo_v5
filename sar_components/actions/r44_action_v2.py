# sar_components/actions/r44_action_v2.py
"""
Per-lane differential action v2 for ramps_v2 topology.

Supports two configurations:
  Box(4) — pure Lagrangian:
    action[0]: seg_0_before lane 0 VSL (kph) — merge lane, CAV slowDown
    action[1]: seg_0_before lane 1 VSL (kph) — middle lane, CAV slowDown
    action[2]: seg_0_before lane 2 VSL (kph) — fast lane, CAV slowDown
    action[3]: ramp_on_transition VSL (kph)  — ramp CAV slowDown

  Box(5) — mixed Lagrangian-Eulerian:
    action[0–3]: same as Box(4)
    action[4]: seg_1_before uniform VSL (kph) — physical sign + radar,
               HDV 92% compliance + CAV 100%

Constraints enforced at action application:
  - Adjacent lane gradient: |a[i] - a[i+1]| <= 10 kph (MUTCD safety)
  - MUTCD step-down (Box(5)): a[4] >= max(a[0],a[1],a[2]) - 16 kph

seg_1_before and seg_2_before in Box(4) mode receive min(a[0],a[1],a[2])
as a passive uniform CAV-only limit.
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


@register_action("r44_action_v2")
class R44ActionV2(ActionStrategy):
    """Per-lane continuous action: Box(4) or Box(5)."""

    def _setup(self) -> None:
        self._lane_low = float(self.config.get("lane_low_kph", 60.0))
        self._lane_high = float(self.config.get("lane_high_kph", 120.0))
        self._ramp_low = float(self.config.get("ramp_low_kph", 40.0))
        self._ramp_high = float(self.config.get("ramp_high_kph", 90.0))
        self._use_box5 = bool(self.config.get("use_box5", False))

    def get_action_space(self) -> gym.spaces.Space:
        if self._use_box5:
            low = np.array(
                [self._lane_low] * 3 + [self._ramp_low, self._lane_low],
                dtype=np.float32,
            )
            high = np.array(
                [self._lane_high] * 3 + [self._ramp_high, self._lane_high],
                dtype=np.float32,
            )
        else:
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

        # Per-lane limits for seg_0_before
        raw_lanes = np.clip(act[:3], self._lane_low, self._lane_high)
        lanes = _enforce_lane_gradient(raw_lanes)

        # Ramp limit
        ramp_kph = float(np.clip(act[3], self._ramp_low, self._ramp_high))

        # Build speed limits dict (m/s)
        speed_limits_ms: Dict[str, float] = {
            "seg_0_before_L0": float(lanes[0]) * _KPH_TO_MS,
            "seg_0_before_L1": float(lanes[1]) * _KPH_TO_MS,
            "seg_0_before_L2": float(lanes[2]) * _KPH_TO_MS,
            "ramp_on_transition": ramp_kph * _KPH_TO_MS,
        }

        # Upstream propagation
        min_lane_ms = float(lanes.min()) * _KPH_TO_MS

        if self._use_box5 and len(act) >= 5:
            # Box(5): independent seg_1_before with MUTCD step-down
            seg1_kph = float(np.clip(act[4], self._lane_low, self._lane_high))
            max_lane_kph = float(lanes.max())
            seg1_kph = max(seg1_kph, max_lane_kph - _MUTCD_STEP_DOWN_KPH)
            speed_limits_ms["seg_1_before"] = seg1_kph * _KPH_TO_MS
            speed_limits_ms["seg_1_before_physical"] = seg1_kph * _KPH_TO_MS
        else:
            # Box(4): passive propagation
            speed_limits_ms["seg_1_before"] = min_lane_ms

        speed_limits_ms["seg_2_before"] = min_lane_ms

        pattern = f"L{lanes[0]:.0f}_{lanes[1]:.0f}_{lanes[2]:.0f}_R{ramp_kph:.0f}"
        return speed_limits_ms, 0.0, pattern
