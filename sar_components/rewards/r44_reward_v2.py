# sar_components/rewards/r44_reward_v2.py
"""
Reward function v2 for ramps_v1 topology.

Changes from v1:
  - Splits the harmonization term into two sub-components:
      r_spatial   maximum adjacent inter-segment speed difference across the
                  3 upstream segments (captures shockwave front steepness)
      r_temporal  mean absolute speed change between consecutive E1 windows
                  measured at the DOWNSTREAM segment (seg_0_after), where the
                  agent has no direct control — captures traffic-induced
                  stop-and-go without penalising the agent's own VSL activation
  - r_harmo = blend * r_spatial + (1 - blend) * r_temporal
  - See docs/sac_tqc_argument.md §8 for the original justification and
    the "reward proxy gap" analysis that motivated this v2.

Spatial term (max adjacent gradient):
  Instead of std() over 3 points (a degenerate statistic dominated by the
  single largest outlier), we use max(|s2-s1|, |s1-s0|) — the steepest
  speed drop between adjacent segments.  This directly measures shockwave
  front steepness, which is what causes braking as vehicles traverse the
  corridor.  This is the same signal used by SPECIALIST (Hegyi et al., 2008)
  as its VSL activation trigger.

  Academic grounding:
  - Hegyi et al. (2008): SPECIALIST activates VSL when the speed difference
    across adjacent cells exceeds a threshold.
  - Li et al. (2017, IEEE T-ITS): The feedback controller monitors density
    at the bottleneck cross-section — a single-point gradient, not variance.

Temporal term (downstream speed stability):
  The temporal term measures speed stability at seg_0_after (the weaving
  zone), where the agent has NO direct control (CAVs are released downstream
  of the merge).  Speed changes at seg_0_after reflect genuine traffic
  dynamics — merge conflicts, shockwave propagation — not the agent's
  VSL commands.  This avoids the fundamental problem of penalising the
  agent for its own beneficial action (activating VSL necessarily changes
  upstream speeds, which would be erroneously penalised if measured there).

  Academic grounding:
  - Hua & Fan (2024, Physica A, §3.1): reward = -theta_t (cumulative
    emergency deceleration above 4.5 m/s²).  Their threshold filters out
    controlled decelerations; measuring downstream achieves the same
    separation between controlled and uncontrolled speed changes.
  - SPECIALIST (Hegyi et al., 2008): VSL activation triggers when speed
    change exceeds a threshold — the temporal derivative is the activation
    signal, measured downstream of the control zone.

Throughput term (penalty-only constraint):
  Throughput is framed as a constraint ("do not collapse flow"), not a
  bonus.  When downstream flow is above 85% of reference, no penalty.
  Below 85%, a linear penalty activates.  This is consistent with the
  thesis framing: "subject to maintaining throughput" (Li et al., 2017;
  MARVEL, Zhang et al., 2024).

Speed floor regime transition:
  Below 50 kph mean upstream speed, the corridor is in established
  congestion where harmonization is no longer actionable.  The reward
  transitions to a speed-recovery signal that incentivises the agent to
  raise speeds back above the floor.  This is documented as a deliberate
  regime transition, not a proxy.

Four terms:

  r_harmo   Blended spatial + temporal corridor harmonization.

  r_q       Throughput penalty at downstream (seg_1_after).  Zero when
            flow is above 85% of reference; linear penalty below.

  r_a       Action smoothness penalty (L2 norm of normalised action delta).

  total = w_h * r_harmo + w_q * r_q + w_a * r_a
"""
from __future__ import annotations

import logging
from typing import Any, Dict, Optional

import numpy as np

from core import RewardFunction, RewardSignal, TrafficMetrics
from sar_components.registry import register_reward

logger = logging.getLogger(__name__)

# Action bounds for smoothness normalization (must match r44_action_v1).
_ACTION_RANGE = np.array([120.0 - 60.0, 90.0 - 40.0], dtype=np.float32)

# Normalization ceiling for the maximum adjacent speed gradient (kph).
# From baseline: at 7000 vph no-control, seg_2=97 kph, seg_0=45 kph
# → adjacent diffs up to ~25 kph.  30 kph keeps penalty in [-1, 0].
_GRADIENT_NORM = 30.0

# Normalization ceiling for downstream temporal speed change (kph).
# seg_0_after: at 7000 vph breakdown onset, per-window swings of 15-25 kph.
# 15 kph maps "moderate instability" to penalty = -1.0.
_DS_DELTA_V_NORM = 15.0

# Speed floor below which harmonization is not actionable.
_SPEED_FLOOR_KPH = 50.0

# Default blend: 0.5 = equal weight spatial and temporal.
_DEFAULT_BLEND = 0.5

# Throughput threshold: flow above this fraction of ref_flow → no penalty.
_THROUGHPUT_THRESHOLD = 0.85


@register_reward("r44_reward_v2")
class R44RewardV2(RewardFunction):
    """4-component reward: spatial + temporal harmonization, throughput, smoothness."""

    def _setup(self) -> None:
        weights = self.config.get("reward_weights", {})
        self._w_h = float(weights.get("w_h", 0.55))
        self._w_q = float(weights.get("w_q", 0.30))
        self._w_a = float(weights.get("w_a", 0.15))
        self._ref_flow = float(self.config.get("ref_flow_vph", 6000.0))
        self._speed_floor = float(
            self.config.get("speed_floor_kph", _SPEED_FLOOR_KPH)
        )
        self._blend = float(
            self.config.get("harmo_spatial_blend", _DEFAULT_BLEND)
        )
        self._throughput_threshold = float(
            self.config.get("throughput_threshold", _THROUGHPUT_THRESHOLD)
        )

        # Previous-window downstream speed for temporal delta (reset in reset()).
        self._prev_ds_speed_kph: Optional[float] = None

    def reset(self) -> None:
        self._prev_ds_speed_kph = None

    def calculate(
        self,
        metrics: Any,
        safety_metrics: Optional[Any] = None,
    ) -> RewardSignal:
        m: TrafficMetrics = metrics

        # --- Current upstream speeds ---
        s2_kph = m.seg_2_before_speed_ms * 3.6
        s1_kph = m.seg_1_before_speed_ms * 3.6
        s0_kph = m.seg_0_before_speed_ms * 3.6

        speeds = np.array([s2_kph, s1_kph, s0_kph])
        mean_speed = float(np.mean(speeds))

        # --- Spatial component (max adjacent speed gradient) ---
        # max(|s2 - s1|, |s1 - s0|): steepest adjacent speed difference.
        adj_diff_21 = abs(s2_kph - s1_kph)
        adj_diff_10 = abs(s1_kph - s0_kph)
        max_gradient = max(adj_diff_21, adj_diff_10)

        if mean_speed >= self._speed_floor:
            r_spatial = -min(max_gradient / _GRADIENT_NORM, 1.0)
        else:
            # Established congestion: transition to speed-recovery signal.
            # At mean_speed=0 -> r=-1; at mean_speed=floor -> r=0.
            r_speed_recovery = -1.0 + (mean_speed / self._speed_floor)
            r_gradient_penalty = -min(max_gradient / _GRADIENT_NORM, 1.0)
            r_spatial = min(r_speed_recovery, r_gradient_penalty)

        # --- Temporal component (downstream speed stability) ---
        # Measured at seg_0_after (weaving zone), where the agent has NO
        # direct control.  Speed changes here reflect traffic dynamics
        # (merge conflicts, shockwave arrival), not the agent's VSL action.
        ds_speed_kph = m.seg_0_after_speed_ms * 3.6

        if self._prev_ds_speed_kph is not None:
            ds_delta_v = abs(ds_speed_kph - self._prev_ds_speed_kph)
            r_temporal = -min(ds_delta_v / _DS_DELTA_V_NORM, 1.0)
        else:
            # First step after reset — no previous window available.
            r_temporal = 0.0

        self._prev_ds_speed_kph = ds_speed_kph

        # --- Blended harmonization ---
        r_harmo = self._blend * r_spatial + (1.0 - self._blend) * r_temporal

        # --- Throughput penalty (constraint, not bonus) ---
        # Above threshold: no penalty (r_q = 0).
        # Below threshold: linear penalty proportional to the shortfall.
        if self._ref_flow > 0:
            flow_ratio = m.seg_1_after_flow_vph / self._ref_flow
            if flow_ratio >= self._throughput_threshold:
                r_q = 0.0
            else:
                # Linear penalty: at flow=0 -> r_q = -1.0
                # at flow=threshold*ref -> r_q = 0.0
                r_q = -(self._throughput_threshold - flow_ratio) / self._throughput_threshold
        else:
            r_q = 0.0

        # --- Action smoothness penalty ---
        r_a = 0.0
        if m.action is not None and m.prev_action is not None:
            delta = (
                np.asarray(m.action, dtype=np.float32)
                - np.asarray(m.prev_action, dtype=np.float32)
            )
            normalised_delta = delta / _ACTION_RANGE
            r_a = -float(np.clip(np.linalg.norm(normalised_delta), 0.0, 1.0))

        total = self._w_h * r_harmo + self._w_q * r_q + self._w_a * r_a

        return RewardSignal(
            total=total,
            components={
                "harmonization": r_harmo,
                "spatial": r_spatial,
                "temporal": r_temporal,
                "throughput": r_q,
                "smoothness": r_a,
            },
        )
