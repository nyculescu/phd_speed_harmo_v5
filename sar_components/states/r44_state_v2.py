# sar_components/states/r44_state_v2.py
"""
Per-lane state representation v2 for ramps_v2 topology.

Changes from v1:
  - seg_0_before is now per-lane (L0/L1/L2 speed/flow/occ = 9 features)
    instead of aggregate (3 features).  The agent needs per-lane
    observability to make informed per-lane action decisions.
  - Previous action expanded from 2D to 4D (3 per-lane + ramp).
  - Anomaly active flag added as static feature.

Observation: 77-dim vector = 3-frame stack of 24 per-frame features + 5 static.

Per-frame features (24):
   0  seg_2_before speed   (normalized)
   1  seg_2_before flow    (normalized)
   2  seg_2_before occ     (normalized)
   3  seg_1_before speed   (normalized)
   4  seg_1_before flow    (normalized)
   5  seg_1_before occ     (normalized)
   6  seg_0_before L0 speed (normalized)
   7  seg_0_before L0 flow  (normalized)
   8  seg_0_before L0 occ   (normalized)
   9  seg_0_before L1 speed (normalized)
  10  seg_0_before L1 flow  (normalized)
  11  seg_0_before L1 occ   (normalized)
  12  seg_0_before L2 speed (normalized)
  13  seg_0_before L2 flow  (normalized)
  14  seg_0_before L2 occ   (normalized)
  15  seg_0_after speed    (normalized)
  16  seg_0_after flow     (normalized)
  17  seg_0_after occ      (normalized)
  18  ramp_on_approach flow (normalized)
  19  ramp_on_merge speed  (normalized)
  20  seg_1_after flow     (normalized)
  21  regime one-hot: FREE_FLOW
  22  regime one-hot: METASTABLE
  23  regime one-hot: CONGESTED

Static features (5):
  72  prev_action[0] L0 VSL   (normalized to [0,1])
  73  prev_action[1] L1 VSL   (normalized to [0,1])
  74  prev_action[2] L2 VSL   (normalized to [0,1])
  75  prev_action[3] ramp VSL (normalized to [0,1])
  76  anomaly_active flag     (0.0 or 1.0)
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

_FRAME_DIM = 24
_STACK_SIZE = 3
_STATIC_DIM = 5  # 4 prev_action + 1 anomaly flag
_OBS_DIM = _FRAME_DIM * _STACK_SIZE + _STATIC_DIM  # 77

# Action bounds for normalization (must match r44_action_v2).
_LANE_LOW, _LANE_HIGH = 60.0, 120.0
_RAMP_LOW, _RAMP_HIGH = 40.0, 90.0

# Speed normalization ceilings (m/s).
_MAX_MAINLINE_SPEED_MS = 130.0 / 3.6   # ~36.1 m/s
_MAX_RAMP_SPEED_MS = 90.0 / 3.6        # 25.0 m/s


@register_state("r44_state_v2")
class R44StateV2(StateRepresentation):
    """3-frame stacked observation with per-lane merge approach visibility."""

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

        # seg_2_before (furthest upstream, aggregate)
        frame[0] = m.seg_2_before_speed_ms / _MAX_MAINLINE_SPEED_MS
        frame[1] = m.seg_2_before_flow_vph / self._max_flow
        frame[2] = m.seg_2_before_occ_pct / 100.0

        # seg_1_before (pre-conditioning zone, aggregate)
        frame[3] = m.seg_1_before_speed_ms / _MAX_MAINLINE_SPEED_MS
        frame[4] = m.seg_1_before_flow_vph / self._max_flow
        frame[5] = m.seg_1_before_occ_pct / 100.0

        # seg_0_before PER-LANE (merge approach)
        frame[6] = m.seg_0_before_L0_speed_ms / _MAX_MAINLINE_SPEED_MS
        frame[7] = m.seg_0_before_L0_flow_vph / self._max_flow
        frame[8] = m.seg_0_before_L0_occ_pct / 100.0

        frame[9] = m.seg_0_before_L1_speed_ms / _MAX_MAINLINE_SPEED_MS
        frame[10] = m.seg_0_before_L1_flow_vph / self._max_flow
        frame[11] = m.seg_0_before_L1_occ_pct / 100.0

        frame[12] = m.seg_0_before_L2_speed_ms / _MAX_MAINLINE_SPEED_MS
        frame[13] = m.seg_0_before_L2_flow_vph / self._max_flow
        frame[14] = m.seg_0_before_L2_occ_pct / 100.0

        # seg_0_after (merge zone, aggregate)
        frame[15] = m.seg_0_after_speed_ms / _MAX_MAINLINE_SPEED_MS
        frame[16] = m.seg_0_after_flow_vph / self._max_flow
        frame[17] = m.seg_0_after_occ_pct / 100.0

        # ramp_on_approach (pending merge demand)
        frame[18] = m.ramp_on_approach_flow_vph / self._max_ramp_flow

        # ramp_on_merge (merge point speed)
        frame[19] = m.ramp_on_merge_speed_ms / _MAX_RAMP_SPEED_MS

        # seg_1_after (downstream throughput)
        frame[20] = m.seg_1_after_flow_vph / self._max_flow

        # Regime one-hot (based on seg_0_before aggregate — closest to bottleneck)
        speed_kph = m.seg_0_before_speed_ms * 3.6
        occ_pct = m.seg_0_before_occ_pct
        regime = self._regime.classify(speed_kph, occ_pct)
        frame[21] = 1.0 if regime == TrafficRegime.FREE_FLOW else 0.0
        frame[22] = 1.0 if regime == TrafficRegime.METASTABLE else 0.0
        frame[23] = 1.0 if regime == TrafficRegime.CONGESTED else 0.0

        self._buffer.append(frame)

        # Stack frames
        stacked = np.concatenate(list(self._buffer), dtype=np.float32)

        # Static features: prev_action (4D normalized) + anomaly flag
        static = np.zeros(_STATIC_DIM, dtype=np.float32)
        if m.prev_action is not None and len(m.prev_action) >= 4:
            static[0] = (float(m.prev_action[0]) - _LANE_LOW) / (_LANE_HIGH - _LANE_LOW)
            static[1] = (float(m.prev_action[1]) - _LANE_LOW) / (_LANE_HIGH - _LANE_LOW)
            static[2] = (float(m.prev_action[2]) - _LANE_LOW) / (_LANE_HIGH - _LANE_LOW)
            static[3] = (float(m.prev_action[3]) - _RAMP_LOW) / (_RAMP_HIGH - _RAMP_LOW)
        static[4] = 1.0 if m.anomaly_active else 0.0

        return np.concatenate([stacked, static], dtype=np.float32)

    def preprocess_state(self, raw_state: np.ndarray) -> np.ndarray:
        return np.clip(raw_state, 0.0, 1.0).astype(np.float32)
