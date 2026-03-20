# traffic_environment/anomaly_injector.py
"""
Anomaly injection for v5.1 stochastic training episodes.

15% of episodes contain a single anomaly during the peak demand phase.
Three anomaly types simulate real-world disruptions:
  - ramp_spike:      2x ramp flow burst (60–120 s)
  - speed_reduction: rubbernecking / debris on seg_1_before (90–180 s)
  - lane_closure:    partial obstruction of seg_0_before L2 (120–240 s)

The anomaly_active flag is observable in the agent's state (realistic:
traffic management centres have incident detection systems).
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import List, Optional

import numpy as np

logger = logging.getLogger(__name__)

ANOMALY_TYPES = ("ramp_spike", "speed_reduction", "lane_closure")


@dataclass
class AnomalyEvent:
    """Describes a single anomaly within an episode."""

    anomaly_type: str = ""
    start_time_s: float = 0.0
    duration_s: float = 0.0
    active: bool = False
    _activated: bool = field(default=False, repr=False)
    _deactivated: bool = field(default=False, repr=False)


class AnomalyInjector:
    """Manages anomaly lifecycle for a single episode.

    Parameters
    ----------
    episode_duration_s:
        Total episode length in simulation seconds.
    anomaly_prob:
        Probability that this episode contains an anomaly (default 0.15).
    warmup_s:
        Minimum simulation time before anomaly can start.
    peak_start_frac, peak_end_frac:
        Anomaly can only start during this fraction of the episode (peak phase).
    seed:
        Random seed for reproducibility.
    """

    def __init__(
        self,
        episode_duration_s: int = 3600,
        anomaly_prob: float = 0.15,
        warmup_s: float = 160.0,
        peak_start_frac: float = 0.30,
        peak_end_frac: float = 0.70,
        seed: Optional[int] = None,
    ) -> None:
        self._rng = np.random.default_rng(seed)
        self._T = float(episode_duration_s)

        self.event = AnomalyEvent()
        self._injected_vehs: List[str] = []

        has_anomaly = self._rng.random() < anomaly_prob
        if not has_anomaly:
            return

        # Sample anomaly parameters
        atype = self._rng.choice(ANOMALY_TYPES)
        earliest = max(warmup_s + 60.0, peak_start_frac * self._T)
        latest = peak_end_frac * self._T

        if latest <= earliest:
            return

        start = self._rng.uniform(earliest, latest)

        dur_ranges = {
            "ramp_spike": (60.0, 120.0),
            "speed_reduction": (90.0, 180.0),
            "lane_closure": (120.0, 240.0),
        }
        dur_lo, dur_hi = dur_ranges[atype]
        duration = self._rng.uniform(dur_lo, dur_hi)

        # Clamp end to episode
        duration = min(duration, self._T - start - 30.0)
        if duration < 30.0:
            return

        self.event = AnomalyEvent(
            anomaly_type=atype,
            start_time_s=start,
            duration_s=duration,
        )
        logger.info(
            "AnomalyInjector: %s at t=%.0f for %.0fs",
            atype, start, duration,
        )

    @property
    def has_anomaly(self) -> bool:
        return self.event.anomaly_type != ""

    @property
    def is_active(self) -> bool:
        return self.event.active

    def step(self, sim_time_s: float, traci_conn) -> bool:
        """Call at each SUMO simulation step. Returns True if anomaly is active."""
        if not self.has_anomaly:
            return False

        e = self.event
        end_time = e.start_time_s + e.duration_s

        # Activate
        if sim_time_s >= e.start_time_s and sim_time_s < end_time:
            if not e._activated:
                self._activate(traci_conn)
                e._activated = True
                e.active = True
            # For ramp_spike: inject extra vehicles each second
            if e.anomaly_type == "ramp_spike":
                self._inject_ramp_burst(sim_time_s, traci_conn)
            return True

        # Deactivate
        if sim_time_s >= end_time and e._activated and not e._deactivated:
            self._deactivate(traci_conn)
            e._deactivated = True
            e.active = False

        return False

    def _activate(self, conn) -> None:
        """Apply the anomaly effect at onset."""
        atype = self.event.anomaly_type

        if atype == "speed_reduction":
            # Slow ALL vehicles on seg_1_before to 40 kph (rubbernecking)
            try:
                conn.edge.setMaxSpeed("seg_1_before", 40.0 / 3.6)
            except Exception:
                pass
            logger.info("Anomaly ACTIVATED: speed_reduction on seg_1_before → 40 kph")

        elif atype == "lane_closure":
            # Partial obstruction: set seg_0_before lane 2 to 10 kph
            try:
                conn.lane.setMaxSpeed("seg_0_before_2", 10.0 / 3.6)
            except Exception:
                pass
            logger.info("Anomaly ACTIVATED: lane_closure on seg_0_before_2 → 10 kph")

        elif atype == "ramp_spike":
            logger.info("Anomaly ACTIVATED: ramp_spike (2x ramp vehicles)")

    def _deactivate(self, conn) -> None:
        """Remove the anomaly effect."""
        atype = self.event.anomaly_type

        if atype == "speed_reduction":
            try:
                conn.edge.setMaxSpeed("seg_1_before", 120.0 / 3.6)
            except Exception:
                pass
            logger.info("Anomaly DEACTIVATED: speed_reduction")

        elif atype == "lane_closure":
            try:
                conn.lane.setMaxSpeed("seg_0_before_2", 120.0 / 3.6)
            except Exception:
                pass
            logger.info("Anomaly DEACTIVATED: lane_closure")

        elif atype == "ramp_spike":
            logger.info("Anomaly DEACTIVATED: ramp_spike")

    def _inject_ramp_burst(self, sim_time_s: float, conn) -> None:
        """Inject extra ramp vehicles during ramp_spike anomaly.

        Doubles the ramp flow by adding one extra vehicle per second
        (on top of the normal route-file departures).
        """
        veh_id = f"anomaly_ramp_{int(sim_time_s)}"
        try:
            conn.vehicle.add(
                vehID=veh_id,
                routeID="ramp_route",
                typeID="HDV",
                depart="now",
                departLane="0",
                departSpeed="max",
            )
            self._injected_vehs.append(veh_id)
        except Exception:
            pass  # Route may not exist yet or vehicle limit reached
