# sar_components/actions/r44_action_v1.py
"""
Continuous 2D action v1 for ramps_v1 topology.

Changes from v0:
  - Mainline upper bound lowered from 130 to 120 kph.
    120 kph is effectively "no restriction" (network limit is 130 kph, so
    only CAVs above 120 are affected — a negligible fraction).
  - Lower bound kept at 60 kph: below this, control is counterproductive
    for recurrent congestion.  Non-recurrent scenarios (incidents, weather)
    will extend the range downward in v5.1.

Action space: Box([60, 40], [120, 90], shape=(2,), dtype=float32)
  action[0]: mainline VSL (kph) → seg_0/1/2_before
  action[1]: ramp VSL (kph)     → ramp_on_transition
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
_MAINLINE_SEGS = ("seg_0_before", "seg_1_before", "seg_2_before")


@register_action("r44_action_v1")
class R44ActionV1(ActionStrategy):
    """2D continuous action: [mainline_vsl_kph, ramp_vsl_kph]."""

    def _setup(self) -> None:
        self._mainline_low = float(self.config.get("mainline_low_kph", 60.0))
        self._mainline_high = float(self.config.get("mainline_high_kph", 120.0))
        self._ramp_low = float(self.config.get("ramp_low_kph", 40.0))
        self._ramp_high = float(self.config.get("ramp_high_kph", 90.0))

    def get_action_space(self) -> gym.spaces.Space:
        return gym.spaces.Box(
            low=np.array([self._mainline_low, self._ramp_low], dtype=np.float32),
            high=np.array([self._mainline_high, self._ramp_high], dtype=np.float32),
            dtype=np.float32,
        )

    def apply_action(
        self,
        action: Any,
        metrics: Any,
    ) -> Tuple[Dict[str, float], float, Optional[str]]:
        act = np.asarray(action, dtype=np.float32).flatten()
        mainline_kph = float(np.clip(act[0], self._mainline_low, self._mainline_high))
        ramp_kph = float(np.clip(act[1], self._ramp_low, self._ramp_high))

        mainline_ms = mainline_kph * _KPH_TO_MS
        ramp_ms = ramp_kph * _KPH_TO_MS

        speed_limits_ms: Dict[str, float] = {
            seg: mainline_ms for seg in _MAINLINE_SEGS
        }
        speed_limits_ms["ramp_on_transition"] = ramp_ms

        return speed_limits_ms, 0.0, None
