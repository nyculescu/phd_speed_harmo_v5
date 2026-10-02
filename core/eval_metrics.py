# core/eval_metrics.py
"""
Tier-A evaluation metrics: safety + system performance + macroscopic regime.

Captured during evaluation only (NOT during training — too expensive per step).
The collector is sampled at the env-step boundary (every aggregation_time
seconds, default 30 s), which under-counts very brief intra-window events
(e.g., a single hard-brake spike) but is sufficient for the cross-policy
*relative* comparison that the thesis defends.

Metrics produced:

  Safety (publication-required for VSL papers):
    hard_brake_count        — total veh-steps with accel < -4 m/s²
    min_ttc_s               — minimum observed TTC at the merge segments
    mean_ttc_s              — mean TTC across the episode at the merge
    n_ttc_critical          — # of observations with TTC < 1.0 s
    lc_count                — total lane-change events
    lc_per_veh_per_km       — normalised LC rate

  User experience / system performance:
    n_arrived               — vehicles that completed their route
    mean_travel_time_s      — mean origin→destination time
    p95_travel_time_s       — 95th-percentile travel time (worst-case UX)
    total_tts_veh_h         — Total Time Spent = Σ vehicles × Δt, in veh·h

  Macroscopic / fundamental:
    regime_free_flow_pct    — % of steps classified FREE_FLOW
    regime_metastable_pct   — % of steps classified METASTABLE
    regime_congested_pct    — % of steps classified CONGESTED
    density_seg_0_before    — mean density at the bottleneck (veh/km/lane)
    density_seg_0_after     — mean density at the merge zone

  Acceleration / jerk (per-SUMO-step — added 2026-05-21, traffic-smoothing study):
    accel_mean_abs_ms2 / accel_rms_ms2   — ride-harshness of the accel profile
    decel_mean_ms2 / decel_p95_ms2       — typical / tail braking magnitude
    decel_ct_{moderate,hard,severe}      — severity-binned braking-event counts
    decel_rate_{hard,severe}_per1k       — exposure-normalised braking-event rate
    jerk_{mean_abs,rms,p95}_ms3          — jerk (da/dt) distribution
    *_merge_* / *_upstream_*             — same metrics split by spatial zone
  Collected by sumo_step() (every ~1 s SUMO step), unlike every metric above
  which step() polls only at the 30 s env-step boundary. This finer sampling
  is why decel_ct_hard supersedes the (30 s-aliased) hard_brake_count.

TTC is computed only for vehicles on the merge approach (seg_0_before,
seg_0_after, ramp_on_merge), where it matters; computing TTC for every
vehicle in the network would 2× eval cost.
"""
from __future__ import annotations

from array import array
from typing import Any, Dict, List, Optional

import numpy as np

from .regime_detector import RegimeDetector, TrafficRegime

# ── Tunable thresholds ──────────────────────────────────────────────────────
HARD_BRAKE_THRESHOLD_MS2 = -4.0          # AASHTO/SSAM-aligned hard-brake floor
TTC_CRITICAL_S = 1.0                     # below this = critical near-miss
TTC_SEARCH_DISTANCE_M = 200.0            # how far ahead to look for a leader
TTC_MIN_GAP_M = 2.0                      # gap floor — SUMO reports ~0 m gap
                                         # immediately after vehicle insertion;
                                         # filter those out so they don't
                                         # poison min/mean TTC.
TTC_MIN_FOLLOWER_SPEED_MS = 1.0          # ignore stopped/just-departed vehicles
SAFETY_SEGMENTS = (
    "seg_0_before", "seg_0_after",
    "ramp_on_merge", "ramp_on_transition",
)

# ── Per-SUMO-step acceleration / jerk instrumentation ───────────────────────
# Added 2026-05-21 for the traffic-smoothing study (audit follow-up). Collected
# by EvalMetricsCollector.sumo_step(), called once per SUMO simulation step
# (~1 s) — far finer than the 30 s env-step poll used for hard_brake_count.
ACCEL_ARTIFACT_ABS_MS2 = 15.0   # |a| beyond this is an insertion/teleport artefact — discarded
JERK_ARTIFACT_ABS_MS3 = 30.0    # |jerk| beyond this is discarded as an artefact

# Deceleration severity bands (m/s²; braking is negative). For a sample a:
#   moderate : DECEL_HARD   < a <= DECEL_MODERATE
#   hard     : DECEL_SEVERE < a <= DECEL_HARD
#   severe   :               a <= DECEL_SEVERE
DECEL_MODERATE_MS2 = -2.5
DECEL_HARD_MS2 = -4.0           # matches HARD_BRAKE_THRESHOLD_MS2
DECEL_SEVERE_MS2 = -6.0

# Edge → spatial zone for the merge-vs-upstream split. Edges not listed
# (downstream release zone seg_*_after past the merge, internal ":" junction
# edges) are counted only in the network-wide "all" figures, never in a
# headline bucket. Adjust here if the topology's edge names change.
ACCEL_ZONE_BY_EDGE: Dict[str, str] = {
    "seg_3_before":       "upstream",
    "seg_2_before":       "upstream",
    "seg_1_before":       "upstream",
    "ramp_on_approach":   "upstream",
    "seg_0_before":       "merge",
    "seg_0_after":        "merge",
    "ramp_on_transition": "merge",
    "ramp_on_merge":      "merge",
}

# Per-segment lane counts (matches env_interact._SEGMENT_LANES)
_SEGMENT_LANES: Dict[str, int] = {
    "seg_0_before": 3, "seg_0_after": 4,
    "seg_1_before": 3, "seg_2_before": 3, "seg_3_before": 3,
    "seg_1_after": 3,
}


def _accel_zone_stats(samples) -> Dict[str, float]:
    """Acceleration / deceleration summary for one bucket of per-step samples.

    `samples` is a sequence of signed accelerations (m/s²); braking is negative.
    Returns zeros for an empty bucket so the CSV schema stays fixed.
    """
    if len(samples) == 0:
        return {
            "n": 0, "mean_abs": 0.0, "rms": 0.0,
            "decel_mean": 0.0, "decel_p95": 0.0,
            "ct_moderate": 0, "ct_hard": 0, "ct_severe": 0,
        }
    a = np.asarray(samples, dtype=np.float64)
    decel = -a[a < 0.0]                       # braking magnitudes, positive
    return {
        "n":           int(a.size),
        "mean_abs":    float(np.abs(a).mean()),
        "rms":         float(np.sqrt(np.mean(a * a))),
        "decel_mean":  float(decel.mean()) if decel.size else 0.0,
        "decel_p95":   float(np.percentile(decel, 95)) if decel.size else 0.0,
        "ct_moderate": int(np.sum((a <= DECEL_MODERATE_MS2) & (a > DECEL_HARD_MS2))),
        "ct_hard":     int(np.sum((a <= DECEL_HARD_MS2) & (a > DECEL_SEVERE_MS2))),
        "ct_severe":   int(np.sum(a <= DECEL_SEVERE_MS2)),
    }


def _jerk_zone_stats(samples) -> Dict[str, float]:
    """Jerk summary (mean |j|, RMS, p95 |j|) for one bucket of per-step samples."""
    if len(samples) == 0:
        return {"mean_abs": 0.0, "rms": 0.0, "p95": 0.0}
    j = np.asarray(samples, dtype=np.float64)
    aj = np.abs(j)
    return {
        "mean_abs": float(aj.mean()),
        "rms":      float(np.sqrt(np.mean(j * j))),
        "p95":      float(np.percentile(aj, 95)),
    }


class EvalMetricsCollector:
    """Accumulates Tier-A metrics across one episode via per-step TraCI polling."""

    def __init__(self, aggregation_time_s: float = 30.0) -> None:
        self.dt = float(aggregation_time_s)
        self._regime = RegimeDetector()

        # Per-vehicle state
        self._prev_lane: Dict[str, int] = {}
        self._depart_time: Dict[str, float] = {}

        # Episode counters
        self.hard_brake_count: int = 0
        self.lc_count: int = 0
        self.n_ttc_critical: int = 0
        self.tts_veh_seconds: float = 0.0  # sum of (n_vehs_present × dt)

        # Distributions across episode (for mean/p95)
        self._completed_travel_times_s: List[float] = []
        self._all_ttc_observations_s: List[float] = []  # only finite TTCs
        self._distance_traveled_per_veh: Dict[str, float] = {}  # for LC rate normalisation

        # Per-step regime counts
        self._regime_counts = {r: 0 for r in TrafficRegime}

        # Per-step density samples per segment (mean over episode at end)
        self._density_samples: Dict[str, List[float]] = {
            "seg_0_before": [], "seg_0_after": [],
        }

        # ── Per-SUMO-step acceleration / jerk samples, bucketed by zone ─────
        # Populated by sumo_step() (~1 s cadence); summarised in summary().
        # `array('d')` keeps ~1 M samples/episode at 8 B each instead of the
        # ~32 B/elem a Python list would cost. "other" = downstream + internal
        # edges; it feeds only the network-wide "all" figures.
        self._sumo_dt: Optional[float] = None        # SUMO step length (s), lazy-fetched
        self._prev_accel: Dict[str, float] = {}      # vid → accel at previous SUMO step
        self._accel_samples: Dict[str, array] = {
            "merge": array("d"), "upstream": array("d"), "other": array("d"),
        }
        self._jerk_samples: Dict[str, array] = {
            "merge": array("d"), "upstream": array("d"), "other": array("d"),
        }

    # ------------------------------------------------------------------
    # Per-step polling
    # ------------------------------------------------------------------
    def step(self, conn, sim_time_s: float, metrics: Any) -> None:
        """Call once per env.step() after env has advanced SUMO."""
        if conn is None:
            return

        try:
            veh_ids = conn.vehicle.getIDList()
        except Exception:
            return

        # ── TTS increment: vehicles currently in the network × Δt
        self.tts_veh_seconds += len(veh_ids) * self.dt

        # ── Per-vehicle scan
        for vid in veh_ids:
            try:
                lane_idx = conn.vehicle.getLaneIndex(vid)
                accel = conn.vehicle.getAcceleration(vid)
                road = conn.vehicle.getRoadID(vid)
                dist = conn.vehicle.getDistance(vid)
            except Exception:
                continue

            # Track depart time on first appearance
            if vid not in self._depart_time:
                self._depart_time[vid] = sim_time_s

            # Distance traveled (cumulative per veh) — used for LC rate normalisation
            self._distance_traveled_per_veh[vid] = max(
                self._distance_traveled_per_veh.get(vid, 0.0), dist
            )

            # Hard-brake event
            if accel < HARD_BRAKE_THRESHOLD_MS2:
                self.hard_brake_count += 1

            # Lane-change event
            if vid in self._prev_lane and self._prev_lane[vid] != lane_idx:
                self.lc_count += 1
            self._prev_lane[vid] = lane_idx

            # TTC — only at safety-critical segments (cheap subset).
            # Filter: gap >= 2 m and follower speed >= 1 m/s, so vehicle-
            # insertion artifacts and stopped traffic don't contaminate min/mean.
            if road in SAFETY_SEGMENTS:
                try:
                    leader_info = conn.vehicle.getLeader(vid, TTC_SEARCH_DISTANCE_M)
                except Exception:
                    leader_info = None
                if leader_info:
                    leader_id, gap = leader_info
                    if gap < TTC_MIN_GAP_M:
                        continue
                    try:
                        follower_speed = conn.vehicle.getSpeed(vid)
                        leader_speed = conn.vehicle.getSpeed(leader_id)
                    except Exception:
                        continue
                    if follower_speed < TTC_MIN_FOLLOWER_SPEED_MS:
                        continue
                    rel_speed = follower_speed - leader_speed
                    if rel_speed > 0.1:  # follower closing on leader
                        ttc = gap / rel_speed
                        self._all_ttc_observations_s.append(ttc)
                        if ttc < TTC_CRITICAL_S:
                            self.n_ttc_critical += 1

        # ── Process arrivals (completed routes → travel times)
        try:
            arrived = conn.simulation.getArrivedIDList()
        except Exception:
            arrived = []
        for vid in arrived:
            depart = self._depart_time.pop(vid, None)
            if depart is not None:
                self._completed_travel_times_s.append(sim_time_s - depart)
            self._prev_lane.pop(vid, None)
            self._distance_traveled_per_veh.pop(vid, None)

        # ── Regime time-share (classify at seg_0_before, the bottleneck)
        speed_kph = float(metrics.seg_0_before_speed_ms) * 3.6
        occ_pct = float(metrics.seg_0_before_occ_pct)
        regime = self._regime.classify(speed_kph, occ_pct)
        self._regime_counts[regime] += 1

        # ── Density per critical segment (k = flow / speed / lanes)
        # Use kph / vph to get veh/km/lane.
        for seg in ("seg_0_before", "seg_0_after"):
            flow_vph = float(getattr(metrics, f"{seg}_flow_vph", 0.0))
            speed_ms = float(getattr(metrics, f"{seg}_speed_ms", 0.0))
            speed_kph = max(speed_ms * 3.6, 1.0)  # guard divide-by-zero
            n_lanes = _SEGMENT_LANES.get(seg, 3)
            density = flow_vph / speed_kph / n_lanes  # veh/km/lane
            self._density_samples[seg].append(density)

    # ------------------------------------------------------------------
    # Per-SUMO-step polling (acceleration / jerk) — finer than step()
    # ------------------------------------------------------------------
    def sumo_step(self, conn, sim_time_s: float = 0.0) -> None:
        """Poll per-vehicle acceleration and jerk for the traffic-smoothing study.

        Call once per SUMO *simulation* step (~1 s), NOT per env step. Wired via
        ``TrafficEnv._eval_collector`` so the hook runs during evaluation only
        and adds zero overhead to training. SUMO's own ``getAcceleration()`` is
        used for accel; jerk is the first difference of accel over the SUMO step
        length. Samples are bucketed merge / upstream / other by current edge.
        """
        if conn is None:
            return
        if self._sumo_dt is None:
            try:
                self._sumo_dt = float(conn.simulation.getDeltaT())
            except Exception:
                self._sumo_dt = 1.0
        dt = self._sumo_dt or 1.0

        try:
            veh_ids = conn.vehicle.getIDList()
        except Exception:
            return

        seen = set()
        for vid in veh_ids:
            try:
                accel = float(conn.vehicle.getAcceleration(vid))
                road = conn.vehicle.getRoadID(vid)
            except Exception:
                continue
            seen.add(vid)
            prev = self._prev_accel.get(vid)
            self._prev_accel[vid] = accel

            # Discard insertion / teleport artefacts (and NaNs).
            if accel != accel or abs(accel) > ACCEL_ARTIFACT_ABS_MS2:
                continue
            zone = ACCEL_ZONE_BY_EDGE.get(road, "other")
            self._accel_samples[zone].append(accel)

            # Jerk needs a finite, non-artefact previous accel for this vehicle.
            if prev is not None and prev == prev and abs(prev) <= ACCEL_ARTIFACT_ABS_MS2:
                jerk = (accel - prev) / dt
                if abs(jerk) <= JERK_ARTIFACT_ABS_MS3:
                    self._jerk_samples[zone].append(jerk)

        # Forget vehicles that have left the network (bounds _prev_accel).
        if len(self._prev_accel) > len(seen):
            for vid in [v for v in self._prev_accel if v not in seen]:
                self._prev_accel.pop(vid, None)

    # ------------------------------------------------------------------
    # Episode end summary
    # ------------------------------------------------------------------
    def summary(self) -> Dict[str, float]:
        """Return one dict per-episode, ready to merge into the eval CSV."""
        # Travel-time stats over vehicles that completed their route
        if self._completed_travel_times_s:
            tt = np.asarray(self._completed_travel_times_s, dtype=np.float64)
            mean_tt = float(tt.mean())
            p95_tt = float(np.percentile(tt, 95))
        else:
            mean_tt = 0.0
            p95_tt = 0.0

        # TTC stats — minimum + mean across all observations
        if self._all_ttc_observations_s:
            ttc = np.asarray(self._all_ttc_observations_s, dtype=np.float64)
            min_ttc = float(ttc.min())
            mean_ttc = float(ttc.mean())
        else:
            min_ttc = float("inf")  # no closing pairs = no near-miss observed
            mean_ttc = float("inf")

        # LC normalisation — total VKT across all vehicles in the episode
        total_vkt_km = sum(self._distance_traveled_per_veh.values()) / 1000.0
        if total_vkt_km > 0 and len(self._depart_time) > 0:
            # LC per vehicle per km is the canonical aggressive-LC indicator
            lc_per_veh_per_km = self.lc_count / total_vkt_km
        else:
            lc_per_veh_per_km = 0.0

        # Regime time-share
        total_regime = sum(self._regime_counts.values()) or 1
        regime_share = {
            f"regime_{r.value}_pct": (self._regime_counts[r] / total_regime) * 100
            for r in TrafficRegime
        }

        # Density (mean over episode per segment)
        density_means = {
            f"density_{seg}_veh_per_km_lane": (
                float(np.mean(samples)) if samples else 0.0
            )
            for seg, samples in self._density_samples.items()
        }

        # ── Per-SUMO-step acceleration / jerk study ────────────────────────
        acc = {z: _accel_zone_stats(s) for z, s in self._accel_samples.items()}
        jrk = {z: _jerk_zone_stats(s) for z, s in self._jerk_samples.items()}
        acc["all"] = _accel_zone_stats(
            self._accel_samples["merge"] + self._accel_samples["upstream"]
            + self._accel_samples["other"]
        )
        jrk["all"] = _jerk_zone_stats(
            self._jerk_samples["merge"] + self._jerk_samples["upstream"]
            + self._jerk_samples["other"]
        )

        def _rate_per1k(count: int, n: int) -> float:
            """Braking-event count normalised per 1000 vehicle-steps (exposure)."""
            return (count / n * 1000.0) if n > 0 else 0.0

        accel_summary = {
            # Network-wide
            "accel_n_samples":         acc["all"]["n"],
            "accel_mean_abs_ms2":      acc["all"]["mean_abs"],
            "accel_rms_ms2":           acc["all"]["rms"],
            "decel_mean_ms2":          acc["all"]["decel_mean"],
            "decel_p95_ms2":           acc["all"]["decel_p95"],
            "decel_ct_moderate":       acc["all"]["ct_moderate"],
            "decel_ct_hard":           acc["all"]["ct_hard"],
            "decel_ct_severe":         acc["all"]["ct_severe"],
            "decel_rate_hard_per1k":   _rate_per1k(acc["all"]["ct_hard"], acc["all"]["n"]),
            "decel_rate_severe_per1k": _rate_per1k(acc["all"]["ct_severe"], acc["all"]["n"]),
            "jerk_mean_abs_ms3":       jrk["all"]["mean_abs"],
            "jerk_rms_ms3":            jrk["all"]["rms"],
            "jerk_p95_ms3":            jrk["all"]["p95"],
            # Merge zone
            "accel_n_merge":                   acc["merge"]["n"],
            "accel_mean_abs_merge_ms2":        acc["merge"]["mean_abs"],
            "decel_p95_merge_ms2":             acc["merge"]["decel_p95"],
            "decel_rate_hard_merge_per1k":     _rate_per1k(acc["merge"]["ct_hard"], acc["merge"]["n"]),
            "decel_rate_severe_merge_per1k":   _rate_per1k(acc["merge"]["ct_severe"], acc["merge"]["n"]),
            "jerk_p95_merge_ms3":              jrk["merge"]["p95"],
            # Upstream zone
            "accel_n_upstream":                acc["upstream"]["n"],
            "accel_mean_abs_upstream_ms2":     acc["upstream"]["mean_abs"],
            "decel_p95_upstream_ms2":          acc["upstream"]["decel_p95"],
            "decel_rate_hard_upstream_per1k":  _rate_per1k(acc["upstream"]["ct_hard"], acc["upstream"]["n"]),
            "decel_rate_severe_upstream_per1k": _rate_per1k(acc["upstream"]["ct_severe"], acc["upstream"]["n"]),
            "jerk_p95_upstream_ms3":           jrk["upstream"]["p95"],
        }

        return {
            # Safety
            "hard_brake_count": int(self.hard_brake_count),
            "min_ttc_s": min_ttc,
            "mean_ttc_s": mean_ttc,
            "n_ttc_critical": int(self.n_ttc_critical),
            "lc_count": int(self.lc_count),
            "lc_per_veh_per_km": float(lc_per_veh_per_km),
            # System performance
            "n_arrived": len(self._completed_travel_times_s),
            "mean_travel_time_s": mean_tt,
            "p95_travel_time_s": p95_tt,
            "total_tts_veh_h": self.tts_veh_seconds / 3600.0,
            # Macroscopic
            **regime_share,
            **density_means,
            # Acceleration / jerk (per-SUMO-step — traffic-smoothing study)
            **accel_summary,
        }
