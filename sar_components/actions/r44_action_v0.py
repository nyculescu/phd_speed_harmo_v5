# sar_components/actions/r44_action_v0.py
"""
Continuous 2D action for ramps_v1 topology (r44 = ramp, 4 merging lanes, 4 post-merge).

Action space: Box([60, 40], [130, 90], shape=(2,), dtype=float32)
  action[0]: mainline VSL (kph) → applied uniformly to seg_0/1/2_before
  action[1]: ramp transition VSL (kph) → applied to ramp_on_transition

All actions are valid (no penalty). TQC/SAC clip to Box bounds internally.
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

# Controlled mainline segments (all get the same limit).
_MAINLINE_SEGS = ("seg_0_before", "seg_1_before", "seg_2_before")


@register_action("r44_action_v0")
class R44ActionV0(ActionStrategy):
    """2D continuous action: [mainline_vsl_kph, ramp_vsl_kph]."""

    def _setup(self) -> None:
        self._mainline_low = float(self.config.get("mainline_low_kph", 60.0))
        self._mainline_high = float(self.config.get("mainline_high_kph", 130.0))
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
