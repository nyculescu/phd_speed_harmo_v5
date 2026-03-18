# No-Control Baseline Diagnostic — ramps_v1

**Date:** 2026-03-18
**Network:** ramps_v1 (3L mainline 4×1000m → 4L weaving 500m → 3L downstream 1000m)
**On-ramp:** 1000m (700 approach + 200 transition + 100 merge)
**Off-ramp:** 1000m (100 diverge + 200 transition + 700 departure)
**Episode:** 3600s | Aggregation: 30s | CAV penetration: 50%
**Ramp departure delay:** 100s (synchronized arrival at merge)
**Demand split:** 75% mainline through, 15% ramp-on, 10% mainline-to-offramp
**Demand sweep:** 2500, 3500, 4500, 5000, 5500, 6000, 6500, 7000 veh/h

---

## Findings

| Demand (vph) | seg_0_after avg speed | seg_0_before min speed | seg_1_before min speed | Max vehicles in network | Breakdown? |
|---|---|---|---|---|---|
| 2500 | 112.6 kph | 109.1 kph | 105.8 kph | 97 | No |
| 3500 | 111.2 kph | 106.4 kph | 107.6 kph | 136 | No |
| 4500 | 109.6 kph | 84.5 kph | 95.9 kph | 187 | No |
| 5000 | 107.8 kph | 96.9 kph | 102.0 kph | 209 | No |
| 5500 | 106.7 kph | 85.5 kph | 96.4 kph | 231 | No |
| 6000 | 102.1 kph | **62.1 kph** | 95.9 kph | 259 | Near-breakdown upstream |
| 6500 | **92.7 kph** | **61.6 kph** | **87.1 kph** | 299 | Weaving zone degraded |
| 7000 | 89.2 kph | **30.3 kph** | **35.1 kph** | **592** | **Full breakdown** |

## Key Observations

### 1. Breakdown onset: ~6000 vph

seg_0_before drops to 62 kph — the merge queue is forming and propagating upstream.
The weaving zone itself stays above 100 kph because it is 4 lanes wide — the bottleneck
is at the merge *entry* point (where 3 mainline lanes + 1 ramp lane compress into 4 weaving
lanes), not inside the weaving zone.

### 2. Full breakdown at 7000 vph

seg_0_before at 30 kph, seg_1_before at 35 kph — the queue has propagated 2 km upstream.
Max vehicles in network jumped to 592 (from 299 at 6500) — vehicles cannot exit fast enough.
This is the classic capacity drop phenomenon: once breakdown occurs, throughput drops below
the pre-breakdown maximum and the queue grows self-reinforcingly.

### 3. The congestion is recurrent and predictable

It forms at the merge point and propagates upstream in a consistent pattern across
demand levels. This is exactly the pattern where proactive VSL upstream can prevent
breakdown by metering inflow — the core mechanism described by Li et al. (2017),
Han et al. (2022), and the SPECIALIST algorithm (Hegyi et al., 2008).

### 4. Ramp merge speed is geometry-limited, not congestion-limited

ramp_on_merge speed is ~22–25 kph across all demand levels. This is the ramp curve
geometry (100m merge section at 90 kph speed limit) forcing vehicles to decelerate
for the tight merge angle, not a congestion signal. This speed is expected and correct
for a 100m curved merge section.

### 5. Training demand range should be 5000–7000 vph

- Below 5000 vph: no control needed (free-flow everywhere).
- 5000–6000 vph: transitional regime — the agent must learn proactive prevention.
- 6000–7000 vph: breakdown regime — the agent must learn to meter flow before it is too late.
- Above 7000 vph: over-saturated; no VSL can prevent gridlock (demand > capacity).

### 6. The weaving zone (seg_0_after) is the right observation point, not the right control point

The 4-lane weaving zone maintains high speeds even at 7000 vph (89 kph avg) because
the extra lane absorbs the merging flow. The *upstream* segments (seg_0_before, seg_1_before)
are where congestion manifests. The control action (VSL on upstream segments + ramp
transition speed) must target the *inflow* to the merge, while the *observation* of the
weaving zone provides the feedback signal about whether the merge is coping.

---

## Raw Data

Per-step CSVs for each demand level are stored alongside this file in:
`tests/results/persistent/nocontrol_ramps_v1_18-03-2026_14-08-30/`

Columns per CSV:
- `step`, `sim_time_s`, `demand_vph`, `n_vehicles_in_network`
- `{segment}_flow_vph`, `{segment}_speed_kph`, `{segment}_occ_pct` for all 12 segments
