"""
Traffic regime detector for the 4→3 merge network.

Classifies each 150 s window into one of three regimes:

  FREE_FLOW   — traffic is uncongested; VSL has no useful effect.
  METASTABLE  — traffic is near the capacity boundary; VSL CAN help by
                smoothing the flow before breakdown occurs.
  CONGESTED   — breakdown has already happened; speeds are below the
                minimum VSL limit; VSL is non-binding and cannot help.

Design notes
------------
Classification uses TWO independent signals measured at seg_0_before
(the segment nearest to the merge, most sensitive to approaching breakdown):

  1. mean_speed_kph   — primary signal; directly reflects flow regime.
  2. mean_occupancy_pct — secondary signal; high occupancy at moderate speed
                          is the classic sign of metastable / near-breakdown flow.

Thresholds are calibrated for a 100 km/h free-flow network with a zipper
4→3 merge.  Typical capacity drop point for this geometry is ~75–80 km/h.
The minimum VSL posted by the current action space is ~50–60 km/h.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import List, Optional


class TrafficRegime(Enum):
    FREE_FLOW  = "free_flow"
    METASTABLE = "metastable"
    CONGESTED  = "congested"

    def vsl_useful(self) -> bool:
        """True only in the metastable regime where VSL can prevent breakdown."""
        return self is TrafficRegime.METASTABLE

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True)
class RegimeThresholds:
    """
    Speed and occupancy thresholds that bound the three regimes.

    All speeds in km/h; occupancy in percent (0–100, SUMO time-based).

    SUMO E1 occupancy values are typically low (2–20 %) even in congestion
    because they reflect the fraction of time a detector is covered, not
    space-mean density.  The thresholds here are calibrated accordingly.

    Regime boundaries (primary — speed):
      speed ≥ speed_free_flow_kph          → FREE_FLOW
      speed_congested_kph ≤ speed < speed_free_flow_kph → METASTABLE
      speed < speed_congested_kph          → CONGESTED

    Override to METASTABLE (secondary — occupancy):
      If occupancy > occ_metastable_threshold_pct, the window is upgraded
      from FREE_FLOW to METASTABLE even if speed is above the free-flow
      boundary.  This catches the brief high-density, still-fast phase just
      before breakdown.
    """
    # Speed boundaries (km/h).  Chosen so the metastable band maps to the
    # range where speed harmonisation literature shows VSL effectiveness.
    speed_free_flow_kph: float = 75.0    # above this → FREE_FLOW
    speed_congested_kph: float = 45.0    # below this → CONGESTED

    # Occupancy override: if occ exceeds this while speed is still "free-flow",
    # reclassify as METASTABLE (congestion is imminent).
    occ_metastable_threshold_pct: float = 8.0


# Default thresholds — calibrated for this network.
DEFAULT_THRESHOLDS = RegimeThresholds()


class RegimeDetector:
    """
    Classifies a single (speed, occupancy) measurement into a TrafficRegime.

    Parameters
    ----------
    thresholds: RegimeThresholds
        Speed/occupancy boundaries.  Defaults to DEFAULT_THRESHOLDS.
    segment: str
        Name of the segment these measurements come from (used in reports only).
    """

    def __init__(
        self,
        thresholds: RegimeThresholds = DEFAULT_THRESHOLDS,
        segment: str = "seg_0_before",
    ) -> None:
        self.thresholds = thresholds
        self.segment = segment

    def classify(
        self,
        mean_speed_kph: float,
        mean_occupancy_pct: float = 0.0,
    ) -> TrafficRegime:
        t = self.thresholds

        if mean_speed_kph < t.speed_congested_kph:
            return TrafficRegime.CONGESTED

        if mean_speed_kph >= t.speed_free_flow_kph:
            # Occupancy override: imminent breakdown despite still-fast speed.
            if mean_occupancy_pct > t.occ_metastable_threshold_pct:
                return TrafficRegime.METASTABLE
            return TrafficRegime.FREE_FLOW

        return TrafficRegime.METASTABLE


# ---------------------------------------------------------------------------
# Batch helpers
# ---------------------------------------------------------------------------

def classify_windows(
    speed_series: List[float],
    occupancy_series: Optional[List[float]] = None,
    thresholds: RegimeThresholds = DEFAULT_THRESHOLDS,
) -> List[TrafficRegime]:
    """
    Classify a series of per-window (speed, occupancy) pairs.

    Parameters
    ----------
    speed_series:     Mean upstream speed (km/h) per window.
    occupancy_series: Occupancy (%) per window.  None → treated as zeros.
    """
    detector = RegimeDetector(thresholds)
    occs = occupancy_series or [0.0] * len(speed_series)
    return [
        detector.classify(spd, occ)
        for spd, occ in zip(speed_series, occs)
    ]


def regime_fractions(regimes: List[TrafficRegime]) -> dict:
    """Return fraction of windows in each regime."""
    n = len(regimes)
    if n == 0:
        return {r.value: 0.0 for r in TrafficRegime}
    counts = {r: regimes.count(r) for r in TrafficRegime}
    return {r.value: counts[r] / n for r in TrafficRegime}
