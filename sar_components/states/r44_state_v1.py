# sar_components/states/r44_state_v1.py
"""
State representation v1 for ramps_v1 topology.

Changes from v0:
  - Adds seg_1_before and seg_2_before speed/flow/occ to each frame.
    The agent needs full upstream corridor visibility to detect the speed
    gradient that precedes congestion (see docs/sac_tqc_argument.md §6).

Observation: 56-dim vector = 3-frame stack of 18 per-frame features + 2 static.

Per-frame features (18):
   0  seg_2_before speed   (normalized)
   1  seg_2_before flow    (normalized)
   2  seg_2_before occ     (normalized)
   3  seg_1_before speed   (normalized)
   4  seg_1_before flow    (normalized)
   5  seg_1_before occ     (normalized)
   6  seg_0_before speed   (normalized)
   7  seg_0_before flow    (normalized)
   8  seg_0_before occ     (normalized)
   9  seg_0_after speed    (normalized)
  10  seg_0_after flow     (normalized)
  11  seg_0_after occ      (normalized)
  12  ramp_on_approach flow (normalized)
  13  ramp_on_merge speed  (normalized)
  14  seg_1_after flow     (normalized)
  15  regime one-hot: FREE_FLOW
  16  regime one-hot: METASTABLE
  17  regime one-hot: CONGESTED

Static features (2):
  54  prev_action[0] mainline VSL (normalized to [0,1])
  55  prev_action[1] ramp VSL     (normalized to [0,1])
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

_FRAME_DIM = 18
_STACK_SIZE = 3
_ACTION_DIM = 2
_OBS_DIM = _FRAME_DIM * _STACK_SIZE + _ACTION_DIM  # 56

# Action bounds for normalization (must match r44_action_v1).
_MAINLINE_LOW, _MAINLINE_HIGH = 60.0, 120.0
_RAMP_LOW, _RAMP_HIGH = 40.0, 90.0

# Speed normalization ceilings (m/s).
_MAX_MAINLINE_SPEED_MS = 130.0 / 3.6   # ~36.1 m/s
_MAX_RAMP_SPEED_MS = 90.0 / 3.6        # 25.0 m/s


@register_state("r44_state_v1")
class R44StateV1(StateRepresentation):
    """3-frame stacked observation with full upstream corridor visibility."""

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
        frame = np.zeros(_FRAME_DIM, dtype=np.float32)

        # seg_2_before (furthest upstream)
        frame[0] = m.seg_2_before_speed_ms / _MAX_MAINLINE_SPEED_MS
        frame[1] = m.seg_2_before_flow_vph / self._max_flow
        frame[2] = m.seg_2_before_occ_pct / 100.0

        # seg_1_before
        frame[3] = m.seg_1_before_speed_ms / _MAX_MAINLINE_SPEED_MS
        frame[4] = m.seg_1_before_flow_vph / self._max_flow
        frame[5] = m.seg_1_before_occ_pct / 100.0

        # seg_0_before (closest upstream to merge)
        frame[6] = m.seg_0_before_speed_ms / _MAX_MAINLINE_SPEED_MS
        frame[7] = m.seg_0_before_flow_vph / self._max_flow
        frame[8] = m.seg_0_before_occ_pct / 100.0

        # seg_0_after (weaving zone)
        frame[9] = m.seg_0_after_speed_ms / _MAX_MAINLINE_SPEED_MS
        frame[10] = m.seg_0_after_flow_vph / self._max_flow
        frame[11] = m.seg_0_after_occ_pct / 100.0

        # ramp_on_approach (pending merge demand)
        frame[12] = m.ramp_on_approach_flow_vph / self._max_ramp_flow

        # ramp_on_merge (merge point speed)
        frame[13] = m.ramp_on_merge_speed_ms / _MAX_RAMP_SPEED_MS

        # seg_1_after (downstream throughput)
        frame[14] = m.seg_1_after_flow_vph / self._max_flow

        # Regime one-hot (based on seg_0_before — closest to bottleneck)
        speed_kph = m.seg_0_before_speed_ms * 3.6
        occ_pct = m.seg_0_before_occ_pct
        regime = self._regime.classify(speed_kph, occ_pct)
        frame[15] = 1.0 if regime == TrafficRegime.FREE_FLOW else 0.0
        frame[16] = 1.0 if regime == TrafficRegime.METASTABLE else 0.0
        frame[17] = 1.0 if regime == TrafficRegime.CONGESTED else 0.0

        self._buffer.append(frame)

        # Stack frames + static action features
        stacked = np.concatenate(list(self._buffer), dtype=np.float32)

        action_features = np.zeros(_ACTION_DIM, dtype=np.float32)
        if m.prev_action is not None and len(m.prev_action) >= 2:
            action_features[0] = (float(m.prev_action[0]) - _MAINLINE_LOW) / (_MAINLINE_HIGH - _MAINLINE_LOW)
            action_features[1] = (float(m.prev_action[1]) - _RAMP_LOW) / (_RAMP_HIGH - _RAMP_LOW)

        return np.concatenate([stacked, action_features], dtype=np.float32)

    def preprocess_state(self, raw_state: np.ndarray) -> np.ndarray:
        return np.clip(raw_state, 0.0, 1.0).astype(np.float32)
