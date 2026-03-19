# core/env_metrics.py
"""
Traffic measurement container for a single E1 aggregation window.

Covers all 9 segments of the ramps_v2 topology:
  Mainline: seg_3_before, seg_2_before, seg_1_before, seg_0_before,
            seg_0_after, seg_1_after
  On-ramp:  ramp_on_approach, ramp_on_transition, ramp_on_merge
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

import numpy as np

from .constants import MAX_SPEED_KPH

_DEFAULT_SPEED_LIMIT_KPH: float = MAX_SPEED_KPH


@dataclass
class TrafficMetrics:
    """Per-step traffic measurements populated by TrafficEnv."""

    # ------------------------------------------------------------------
    # Per-segment measurements: speed (m/s), flow (veh/h), occupancy (%)
    # ------------------------------------------------------------------

    # Upstream mainline (furthest → closest to merge)
    seg_3_before_speed_ms: float = 0.0
    seg_3_before_flow_vph: float = 0.0
    seg_3_before_occ_pct: float = 0.0

    seg_2_before_speed_ms: float = 0.0
    seg_2_before_flow_vph: float = 0.0
    seg_2_before_occ_pct: float = 0.0

    seg_1_before_speed_ms: float = 0.0
    seg_1_before_flow_vph: float = 0.0
    seg_1_before_occ_pct: float = 0.0

    seg_0_before_speed_ms: float = 0.0
    seg_0_before_flow_vph: float = 0.0
    seg_0_before_occ_pct: float = 0.0

    # Merge zone (3 lanes)
    seg_0_after_speed_ms: float = 0.0
    seg_0_after_flow_vph: float = 0.0
    seg_0_after_occ_pct: float = 0.0

    # Downstream (3 lanes)
    seg_1_after_speed_ms: float = 0.0
    seg_1_after_flow_vph: float = 0.0
    seg_1_after_occ_pct: float = 0.0

    # On-ramp
    ramp_on_approach_speed_ms: float = 0.0
    ramp_on_approach_flow_vph: float = 0.0
    ramp_on_approach_occ_pct: float = 0.0

    ramp_on_transition_speed_ms: float = 0.0
    ramp_on_transition_flow_vph: float = 0.0
    ramp_on_transition_occ_pct: float = 0.0

    ramp_on_merge_speed_ms: float = 0.0
    ramp_on_merge_flow_vph: float = 0.0
    ramp_on_merge_occ_pct: float = 0.0

    # ------------------------------------------------------------------
    # Control state
    # ------------------------------------------------------------------

    # Current posted speed limits (kph):
    # [seg_0_before, seg_1_before, seg_2_before, ramp_on_transition]
    current_speed_limits: List[float] = field(
        default_factory=lambda: [_DEFAULT_SPEED_LIMIT_KPH] * 4
    )

    # Continuous action vectors (written by ActionStrategy, read by RewardFunction)
    action: Optional[np.ndarray] = None
    prev_action: Optional[np.ndarray] = None

    # ------------------------------------------------------------------
    # Global context
    # ------------------------------------------------------------------

    upstream_demand_vph: float = 0.0
    tts_increment_s: float = 0.0
    simulation_step: int = 0
