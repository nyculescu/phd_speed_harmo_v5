# sar_components/states/m43_state_v0.py
"""
Stacked 5-frame E1 state for merge_4_to_3_v0 (v5 SAR framework).

Design principles (see docs/speed_harmo_approach_v0.md):
- Observe every 30s (aggregation_time=30) instead of 150s → 5x finer resolution.
- Stack the last 5 frames to give the agent a 150s temporal context while
  preserving the ability to detect speed trends within that window.
- No temporal deltas or moving averages computed by the state — the stacking
  provides the agent with raw trajectory data to derive its own features.
- Regime is explicitly included as a one-hot so the agent can learn a
  conditional policy without an external regime gate.
"""

from __future__ import annotations

import logging
from collections import deque
from typing import Any, Dict, Optional

import gymnasium as gym
import numpy as np

from core import MAX_SPEED_KPH, StateRepresentation, TrafficMetrics
from sar_components.registry import register_state

from core.regime_detector import DEFAULT_THRESHOLDS, RegimeDetector

logger = logging.getLogger(__name__)

# Topology gate: only register for supported networks.
SUPPORTED_NETWORK_TOPOLOGIES = frozenset({"merge_4_to_3", "merge_4_to_3_v0"})

# Per-frame feature count (21 features × 5 frames = 105 total).
_FRAME_DIM = 21
_N_FRAMES = 5
_OBS_DIM = _N_FRAMES * _FRAME_DIM

# Speed normaliser: max speed in m/s.
_MAX_SPEED_MS = MAX_SPEED_KPH / 3.6  # ≈ 27.78 m/s


@register_state("m43_state_v0")
class Merge43StateV0(StateRepresentation):
    """
    5-frame stacked 21-dim E1 observation for the merge_4_to_3 network.

    Each frame encodes the instantaneous traffic state at the end of a 30s
    E1 aggregation window:

        [0]   us2 mean speed (m/s, normalised)
        [1]   us1 mean speed (m/s, normalised)
        [2]   us0 mean speed (m/s, normalised)
        [3]   ds0 mean speed (m/s, normalised)
        [4]   us2 flow (veh/h, normalised)
        [5]   us1 flow (veh/h, normalised)
        [6]   us0 flow (veh/h, normalised)
        [7]   ds0 flow (veh/h, normalised)
        [8]   us2 occupancy (%, normalised)
        [9]   us1 occupancy (%, normalised)
        [10]  us0 occupancy (%, normalised)
        [11]  ds0 occupancy (%, normalised)
        [12]  speed gradient = (us0_speed - ds0_speed) / MAX_SPEED_MS  (clipped [-1,1])
        [13]  flow gradient  = (us0_flow  - ds0_flow)  / max_flow_vph  (clipped [-1,1])
        [14]  regime FREE_FLOW  (0 or 1)
        [15]  regime METASTABLE (0 or 1)
        [16]  regime CONGESTED  (0 or 1)
        [17]  current posted speed limit for seg_0_before (kph, normalised)
        [18]  demand (veh/h, normalised)
        [19]  TTS increment (s, normalised)
        [20]  time in episode (0→1)

    The full observation is the concatenation of the last 5 frames (oldest first),
    giving shape (105,).
    """

    def _setup(self) -> None:
        self._max_flow_vph: float = float(self.config.get("max_flow_vph", 4000.0))
        self._max_tts_s: float = float(self.config.get("max_tts_s", 5000.0))
        self._episode_duration: float = float(self.config.get("episode_duration", 7950.0))

        self._regime_detector = RegimeDetector(DEFAULT_THRESHOLDS)

        self._frame_buffer: deque = deque(maxlen=_N_FRAMES)
        self._zero_frame = np.zeros(_FRAME_DIM, dtype=np.float32)
        self._reset_buffer()

        logger.info(
            "Merge43StateV0 initialised: %d frames × %d features = %d-dim obs",
            _N_FRAMES,
            _FRAME_DIM,
            _OBS_DIM,
        )

    def _reset_buffer(self) -> None:
        self._frame_buffer.clear()
        for _ in range(_N_FRAMES):
            self._frame_buffer.append(self._zero_frame.copy())

    def reset(self, **kwargs: Any) -> None:
        """Clear the frame buffer at the start of each new episode."""
        self._reset_buffer()

    def get_observation_space(self) -> gym.spaces.Space:
        return gym.spaces.Box(
            low=0.0,
            high=1.0,
            shape=(_OBS_DIM,),
            dtype=np.float32,
        )

    # ------------------------------------------------------------------
    # StateRepresentation protocol
    # ------------------------------------------------------------------

    def build_state(
        self,
        metrics: TrafficMetrics,
        safety_metrics: Optional[Any] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> np.ndarray:
        frame = self._build_frame(metrics, context or {})
        self._frame_buffer.append(frame)
        return np.concatenate(list(self._frame_buffer), axis=0)

    def preprocess_state(self, raw_state: np.ndarray) -> np.ndarray:
        # Normalisation is already applied inside build_state; just clip for safety.
        return np.clip(raw_state, 0.0, 1.0).astype(np.float32)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _build_frame(
        self,
        metrics: TrafficMetrics,
        context: Dict[str, Any],
    ) -> np.ndarray:
        # --- Raw values from TrafficMetrics ---
        us0_spd = float(getattr(metrics, "avg_speed_upstream_s0", 0.0))   # m/s
        us1_spd = float(getattr(metrics, "avg_speed_upstream_s1", 0.0))   # m/s
        us2_spd = float(getattr(metrics, "avg_speed_upstream_s2", 0.0))   # m/s
        ds0_spd = float(getattr(metrics, "avg_speed_downstream_s0", 0.0)) # m/s

        us0_flow = float(getattr(metrics, "flow_rate_vph_us0", 0.0))   # veh/h
        us1_flow = float(getattr(metrics, "flow_rate_vph_us1", 0.0))
        us2_flow = float(getattr(metrics, "flow_rate_vph_us2", 0.0))
        ds0_flow = float(getattr(metrics, "flow_rate_vph_ds0", 0.0))

        us0_occ = float(getattr(metrics, "occupancy_pct_us0", 0.0))   # %
        us1_occ = float(getattr(metrics, "occupancy_pct_us1", 0.0))
        us2_occ = float(getattr(metrics, "occupancy_pct_us2", 0.0))
        ds0_occ = float(getattr(metrics, "occupancy_pct_ds0", 0.0))

        # current_speed_limits is in kph
        limits_kph = getattr(metrics, "current_speed_limits", [MAX_SPEED_KPH] * 3)
        seg0_limit_kph = float(limits_kph[0]) if limits_kph else MAX_SPEED_KPH

        demand_vph = float(getattr(metrics, "upstream_demand_vph", 0.0))
        tts_inc_s  = float(getattr(metrics, "tts_increment_s", 0.0))

        # Time in episode from context (passed by TrafficEnv as sim_time)
        sim_time = float(context.get("sim_time", 0.0))
        time_ratio = np.clip(sim_time / max(self._episode_duration, 1.0), 0.0, 1.0)

        # --- Regime one-hot (based on us0 speed kph + occupancy) ---
        us0_spd_kph = us0_spd * 3.6
        regime = self._regime_detector.classify(us0_spd_kph, us0_occ)
        regime_ff  = 1.0 if regime.value == "free_flow"  else 0.0
        regime_ms  = 1.0 if regime.value == "metastable" else 0.0
        regime_cng = 1.0 if regime.value == "congested"  else 0.0

        # --- Normalised gradients ---
        speed_grad = np.clip((us0_spd - ds0_spd) / max(_MAX_SPEED_MS, 1e-6), -1.0, 1.0)
        flow_grad  = np.clip((us0_flow - ds0_flow) / max(self._max_flow_vph, 1.0), -1.0, 1.0)
        # Shift gradients from [-1,1] to [0,1] for the Box(0,1) space.
        speed_grad_norm = (speed_grad + 1.0) * 0.5
        flow_grad_norm  = (flow_grad  + 1.0) * 0.5

        frame = np.array([
            # [0-3] speeds
            np.clip(us2_spd / _MAX_SPEED_MS, 0.0, 1.0),
            np.clip(us1_spd / _MAX_SPEED_MS, 0.0, 1.0),
            np.clip(us0_spd / _MAX_SPEED_MS, 0.0, 1.0),
            np.clip(ds0_spd / _MAX_SPEED_MS, 0.0, 1.0),
            # [4-7] flows
            np.clip(us2_flow / self._max_flow_vph, 0.0, 1.0),
            np.clip(us1_flow / self._max_flow_vph, 0.0, 1.0),
            np.clip(us0_flow / self._max_flow_vph, 0.0, 1.0),
            np.clip(ds0_flow / self._max_flow_vph, 0.0, 1.0),
            # [8-11] occupancies
            np.clip(us2_occ / 100.0, 0.0, 1.0),
            np.clip(us1_occ / 100.0, 0.0, 1.0),
            np.clip(us0_occ / 100.0, 0.0, 1.0),
            np.clip(ds0_occ / 100.0, 0.0, 1.0),
            # [12] speed gradient (shifted to [0,1])
            float(speed_grad_norm),
            # [13] flow gradient (shifted to [0,1])
            float(flow_grad_norm),
            # [14-16] regime one-hot
            regime_ff,
            regime_ms,
            regime_cng,
            # [17] current posted speed limit seg_0_before (kph, normalised)
            np.clip(seg0_limit_kph / MAX_SPEED_KPH, 0.0, 1.0),
            # [18] demand
            np.clip(demand_vph / self._max_flow_vph, 0.0, 1.0),
            # [19] TTS increment
            np.clip(tts_inc_s / max(self._max_tts_s, 1.0), 0.0, 1.0),
            # [20] time in episode
            float(time_ratio),
        ], dtype=np.float32)

        assert frame.shape == (_FRAME_DIM,), f"Frame shape mismatch: {frame.shape}"
        return frame
