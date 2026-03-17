# core/env_metrics.py
"""
Traffic measurement container for a single E1 aggregation window.

Only fields consumed by v5 SAR components are included.
TrafficSafetyMetrics is not used in v5.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from .constants import MAX_SPEED_KPH

_DEFAULT_SPEED_LIMIT_KPH: float = MAX_SPEED_KPH


@dataclass
class TrafficMetrics:
    """Per-step traffic measurements populated by TrafficEnv."""

    # Speed (m/s) — flow-weighted mean from E1 tripwire lanes.
    avg_speed_upstream_s0: float = 0.0
    avg_speed_upstream_s1: float = 0.0
    avg_speed_upstream_s2: float = 0.0
    avg_speed_downstream_s0: float = 0.0

    # Flow (veh/h) — summed from per-lane induction-loop counts.
    flow_rate_vph_us0: float = 0.0
    flow_rate_vph_us1: float = 0.0
    flow_rate_vph_us2: float = 0.0
    flow_rate_vph_ds0: float = 0.0

    # Occupancy (%) — mean from E1 tripwire lanes.
    occupancy_pct_us0: float = 0.0
    occupancy_pct_us1: float = 0.0
    occupancy_pct_us2: float = 0.0
    occupancy_pct_ds0: float = 0.0

    # Current posted speed limits (kph) — [seg_0_before, seg_1_before, seg_2_before].
    current_speed_limits: List[float] = field(
        default_factory=lambda: [_DEFAULT_SPEED_LIMIT_KPH] * 3
    )

    # Control indices (written by ActionStrategy, read by RewardFunction).
    action_idx: Optional[int] = None
    prev_action_idx: Optional[int] = None

    # Global context features used by StateRepresentation.
    upstream_demand_vph: float = 0.0
    tts_increment_s: float = 0.0

    # Simulation bookkeeping.
    simulation_step: int = 0
