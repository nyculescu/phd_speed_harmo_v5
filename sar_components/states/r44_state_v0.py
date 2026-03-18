# sar_components/states/r44_state_v0.py
"""
State representation for ramps_v1 topology (r44 = ramp, 4 merging lanes, 4 post-merge).

Observation: 38-dim vector = 3-frame stack of 12 per-frame features + 2 static features.

Per-frame features (12):
  0  seg_0_before speed (normalized)
  1  seg_0_before flow  (normalized)
  2  seg_0_before occ   (normalized)
  3  seg_0_after speed  (normalized)
  4  seg_0_after flow   (normalized)
  5  seg_0_after occ    (normalized)
  6  ramp_on_approach flow (normalized)
  7  ramp_on_merge speed   (normalized)
  8  seg_1_after flow      (normalized)
  9  regime one-hot: FREE_FLOW
  10 regime one-hot: METASTABLE
  11 regime one-hot: CONGESTED

Static features (2):
  36 prev_action[0] mainline VSL (normalized to [0,1])
  37 prev_action[1] ramp VSL     (normalized to [0,1])
"""
from __future__ import annotations

import logging
from collections import deque
from typing import Any, Dict, Optional

import gymnasium as gym
import numpy as np

from core import StateRepresentation, TrafficMetrics
from core.regime_detector import RegimeDetector, TrafficRegime
from sar_components.registry import register_state

logger = logging.getLogger(__name__)

_FRAME_DIM = 12
_STACK_SIZE = 3
_ACTION_DIM = 2
_OBS_DIM = _FRAME_DIM * _STACK_SIZE + _ACTION_DIM  # 38

# Action bounds for normalization
_MAINLINE_LOW, _MAINLINE_HIGH = 60.0, 130.0
_RAMP_LOW, _RAMP_HIGH = 40.0, 90.0

# Speed normalization ceilings (m/s)
_MAX_MAINLINE_SPEED_MS = 130.0 / 3.6  # ~36.1 m/s
_MAX_RAMP_SPEED_MS = 90.0 / 3.6       # 25.0 m/s


@register_state("r44_state_v0")
class R44StateV0(StateRepresentation):
    """3-frame stacked observation for the ramps_v1 topology."""

    def _setup(self) -> None:
        self._max_flow = float(self.config.get("max_flow_vph", 8000.0))
        self._max_ramp_flow = float(self.config.get("max_ramp_flow_vph", 2000.0))
        self._regime = RegimeDetector()
        self._buffer: deque = deque(maxlen=_STACK_SIZE)

    def reset(self, **kwargs: Any) -> None:
        self._buffer.clear()
        for _ in range(_STACK_SIZE):
            self._buffer.append(np.zeros(_FRAME_DIM, dtype=np.float32))

    def get_observation_space(self) -> gym.spaces.Space:
        return gym.spaces.Box(
            low=0.0, high=1.0, shape=(_OBS_DIM,), dtype=np.float32
        )

    def build_state(
        self,
        metrics: Any,
        safety_metrics: Optional[Any] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> np.ndarray:
        m: TrafficMetrics = metrics

        # Per-frame features
        frame = np.zeros(_FRAME_DIM, dtype=np.float32)

        # seg_0_before (closest upstream to merge)
        frame[0] = m.seg_0_before_speed_ms / _MAX_MAINLINE_SPEED_MS
        frame[1] = m.seg_0_before_flow_vph / self._max_flow
        frame[2] = m.seg_0_before_occ_pct / 100.0

        # seg_0_after (weaving zone)
        frame[3] = m.seg_0_after_speed_ms / _MAX_MAINLINE_SPEED_MS
        frame[4] = m.seg_0_after_flow_vph / self._max_flow
        frame[5] = m.seg_0_after_occ_pct / 100.0

        # ramp_on_approach (pending merge demand)
        frame[6] = m.ramp_on_approach_flow_vph / self._max_ramp_flow

        # ramp_on_merge (merge point speed)
        frame[7] = m.ramp_on_merge_speed_ms / _MAX_RAMP_SPEED_MS

        # seg_1_after (downstream throughput)
        frame[8] = m.seg_1_after_flow_vph / self._max_flow

        # Regime one-hot (based on seg_0_before)
        speed_kph = m.seg_0_before_speed_ms * 3.6
        occ_pct = m.seg_0_before_occ_pct
        regime = self._regime.classify(speed_kph, occ_pct)
        frame[9] = 1.0 if regime == TrafficRegime.FREE_FLOW else 0.0
        frame[10] = 1.0 if regime == TrafficRegime.METASTABLE else 0.0
        frame[11] = 1.0 if regime == TrafficRegime.CONGESTED else 0.0

        # Append to stack
        self._buffer.append(frame)

        # Concatenate stack + static action features
        stacked = np.concatenate(list(self._buffer), dtype=np.float32)

        # Normalized previous action
        action_features = np.zeros(_ACTION_DIM, dtype=np.float32)
        if m.prev_action is not None and len(m.prev_action) >= 2:
            action_features[0] = (float(m.prev_action[0]) - _MAINLINE_LOW) / (_MAINLINE_HIGH - _MAINLINE_LOW)
            action_features[1] = (float(m.prev_action[1]) - _RAMP_LOW) / (_RAMP_HIGH - _RAMP_LOW)

        return np.concatenate([stacked, action_features], dtype=np.float32)

    def preprocess_state(self, raw_state: np.ndarray) -> np.ndarray:
        return np.clip(raw_state, 0.0, 1.0).astype(np.float32)
