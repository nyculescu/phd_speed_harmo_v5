# sar_components/actions/m43_action_v0.py
"""
7-level absolute speed target action for merge_4_to_3_v0 (v5 SAR framework).

Design principles (see docs/speed_harmo_approach_v0.md):
- Actions are absolute posted speed levels (kph), not relative deltas.
  This eliminates the statefulness of v4's delta-based actions and removes
  the "anti-flicker" holdout logic that prevented the agent from correcting
  mistakes quickly.
- A single level is applied uniformly to all 3 upstream segments.
  Per-segment differential control is left for v5.1.
- 7 levels cover the operationally relevant range (70–100 kph) with
  5 kph granularity.  There are no invalid actions — every level is
  always applicable.
"""

from __future__ import annotations

import logging
from typing import Dict, Optional, Tuple

import gymnasium as gym

from core import ActionStrategy, TrafficMetrics
from sar_components.registry import register_action

logger = logging.getLogger(__name__)

# Absolute speed levels in kph (ascending).
SPEED_LEVELS_KPH: Tuple[float, ...] = (70.0, 75.0, 80.0, 85.0, 90.0, 95.0, 100.0)

# Index of the "release / free flow" action (100 kph).
_DEFAULT_ACTION_IDX: int = len(SPEED_LEVELS_KPH) - 1  # 6

# Segments that receive the posted limit.
_CONTROLLED_SEGMENTS = ("seg_2_before", "seg_1_before", "seg_0_before")

# m/s conversion factor.
_KPH_TO_MS: float = 1.0 / 3.6


@register_action("m43_action_v0")
class Merge43ActionV0(ActionStrategy):
    """
    Discrete action space with 7 absolute speed targets.

    Action 0 → 70 kph (most restrictive)
    Action 1 → 75 kph
    Action 2 → 80 kph
    Action 3 → 85 kph
    Action 4 → 90 kph
    Action 5 → 95 kph
    Action 6 → 100 kph (free flow / no restriction)

    The same target is applied to all three upstream segments simultaneously.
    CAVs receive `traci.vehicle.slowDown()` at each simulation step (handled
    in TrafficEnv._apply_vehicle_speed_controls when
    speed_limit_direct_control_CAV=True).  HDVs comply via the lane
    setMaxSpeed() Krauss car-following response.
    """

    def _setup(self) -> None:
        # Allow config override of speed levels (must be a list of kph values).
        raw_levels = self.config.get("speed_levels_kph")
        if raw_levels and isinstance(raw_levels, (list, tuple)) and len(raw_levels) > 0:
            self._levels_kph: Tuple[float, ...] = tuple(float(v) for v in sorted(raw_levels))
        else:
            self._levels_kph = SPEED_LEVELS_KPH

        self._n_actions = len(self._levels_kph)
        self._default_idx = self._n_actions - 1  # highest = free-flow
        self._prev_action_idx: int = self._default_idx

        logger.info(
            "Merge43ActionV0 initialised: %d actions, levels=%s kph",
            self._n_actions,
            self._levels_kph,
        )

    def reset(self) -> None:
        self._prev_action_idx = self._default_idx

    def get_action_space(self) -> gym.spaces.Space:
        return gym.spaces.Discrete(self._n_actions)

    def apply_action(
        self,
        action_id: int,
        metrics: TrafficMetrics,
    ) -> Tuple[Dict[str, float], float, Optional[str]]:
        """
        Convert action index to per-segment speed limit dict (m/s).

        Returns:
            speed_limits_ms: mapping of segment_name -> speed in m/s
            penalty: always 0.0 (no invalid actions)
            pattern_name: string label for logging
        """
        idx = int(action_id)
        if not (0 <= idx < self._n_actions):
            logger.warning("Merge43ActionV0: action_id %d out of range [0,%d), clipping.", idx, self._n_actions)
            idx = max(0, min(idx, self._n_actions - 1))

        level_kph = self._levels_kph[idx]
        level_ms = level_kph * _KPH_TO_MS

        speed_limits_ms: Dict[str, float] = {seg: level_ms for seg in _CONTROLLED_SEGMENTS}
        pattern_name = f"abs_{int(level_kph)}kph"

        self._prev_action_idx = idx
        return speed_limits_ms, 0.0, pattern_name

    # ------------------------------------------------------------------
    # Accessors used by the reward function.
    # ------------------------------------------------------------------

    @property
    def prev_action_idx(self) -> int:
        """Index of the last applied action (for smoothness penalty in reward)."""
        return self._prev_action_idx

    @property
    def n_actions(self) -> int:
        return self._n_actions

    @property
    def levels_kph(self) -> Tuple[float, ...]:
        return self._levels_kph
