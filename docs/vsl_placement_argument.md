# VSL Placement Rationale — ramps_v1 Topology

## 1. The question

Should VSL enforcement points be placed 50–100 m before the merge point (and recursively before each upstream segment boundary), or should they cover entire 1000 m segments as currently implemented?

**Answer: entire-segment application is correct.** Short-range placement (50–100 m) is physically unrealistic, contradicts the VSL mechanism, and is unsupported by any published study. This document provides the full justification.

---

## 2. Current design

The ramps_v1 topology applies speed limits to four controlled edges via `traci.lane.setMaxSpeed()`:

| Controlled edge | Length | Distance from merge (J4) | Lane count |
|---|---|---|---|
| `seg_2_before` | 1000 m | 3000–4000 m upstream | 3 |
| `seg_1_before` | 1000 m | 2000–3000 m upstream | 3 |
| `seg_0_before` | 1000 m | 1000–2000 m upstream | 3 |
| `ramp_on_transition` | 200 m | 100–300 m from merge | 1 |

All lanes in each segment receive the same speed limit. The three mainline segments form a **3 km graduated deceleration corridor**; the ramp transition provides a separate control input for ramp-on vehicles.

---

## 3. Why 50–100 m placement fails

### 3.1 Insufficient deceleration distance

At 120 kph (33.3 m/s), comfortable deceleration to 80 kph requires:

```
Δv = (120 − 80) / 3.6 = 11.1 m/s
Comfortable deceleration a = 2.5 m/s² (Krauss model typical)
Time:     t = 11.1 / 2.5 = 4.4 s
Distance: d = v₀·t − ½·a·t² = 33.3 × 4.4 − 0.5 × 2.5 × 4.4² ≈ 122 m
```

A 50 m VSL zone forces deceleration at > 4 m/s² (emergency braking). A 100 m zone is marginal and still uncomfortable. **Speed harmonisation aims to eliminate abrupt braking — a 50 m VSL zone would create the shockwaves it is designed to prevent.**

### 3.2 No time for platoon spacing adjustment

The purpose of upstream VSL is not just to reduce individual vehicle speed, but to **reduce the flow rate arriving at the bottleneck** by allowing vehicles to increase headways at the lower speed. The flow-density relationship (fundamental diagram) requires sustained lower speed over a distance long enough for car-following dynamics to equilibrate — typically 300–500 m at highway speeds (Li et al. [R25], Hegyi et al. [R21]).

A 50 m zone is traversed in 1.5 s. Vehicle headways cannot adjust meaningfully in that time.

### 3.3 SUMO API constraint

`traci.lane.setMaxSpeed(lane_id, speed)` applies uniformly to the **entire lane**, not to a specific position. To enforce a speed limit at a specific location within a segment, the segment must be split into sub-edges at that position. This is possible (by generating shorter edges in the network file), but the physics argument above shows that sub-100 m control zones are counterproductive regardless of API capabilities.

---

## 4. Academic grounding for segment-level (500–1000 m+) VSL zones

### 4.1 Li et al. (2017) — [R25]

*"Reinforcement Learning-Based Variable Speed Limit Control Strategy to Reduce Traffic Congestion at Freeway Recurrent Bottlenecks"*, IEEE T-ITS 18(11).

- Study site: Interstate 880, Oakland, CA — 6-mile freeway section with merge bottleneck.
- VSL controlled area spans multiple detector stations (#1–#15), with a designated **acceleration section** downstream of the VSL zone that allows vehicles to recover speed before reaching the bottleneck (p. 3208).
- Loop detectors report 30 s aggregated data; VSL decisions based on density at the merge and upstream mainline.
- **The entire upstream section is controlled, not individual sign positions.**

### 4.2 Hegyi et al. (2008) — SPECIALIST [R21]

*"SPECIALIST: A Dynamic Speed Limit Control Algorithm Based on Shock Wave Theory"*, IEEE ITSC 2008.

- VSL placement is dynamic, tracking the shock wave: speed limits are applied across **Areas 2–4** spanning the full length of the detected jam wave plus safety margins (m_h and m_t in km).
- Typical detector spacing: 500–600 m.
- The algorithm explicitly adds upstream and downstream margins to ensure the speed-limited area fully covers the wave — the opposite of a minimal 50 m zone.

### 4.3 Han et al. (2022) — [R26]

*"A New Reinforcement Learning-Based Variable Speed Limit Control Approach to Improve Traffic Efficiency Against Freeway Jam Waves"*, TRC 144.

- The freeway is divided into four areas (p. 5, Fig. 4): Area I (upstream free-flow), **Area II (VSL-controlled)**, Area III (congestion), Area IV (downstream).
- Area II consists of "a number of consecutive cells," each cell = v_f × T_k (free-flow speed × control time step). At v_f = 120 kph and T_k = 30 s, one cell = 1000 m.
- **The VSL-controlled area is explicitly multi-cell (multi-km), not a single point.**

### 4.4 MARVEL (Zhang et al., 2024) — [R10]

*"Bringing Multi-Agent Reinforcement-Learning Based Variable Speed Limit Controllers Closer to Deployment"*, IEEE Access 12.

- Multiple VSL gantries evenly distributed along the freeway corridor (7 miles in training, 17 miles in deployment on I-24).
- Gantry spacing is designed to satisfy the MUTCD maximum step-down constraint (10 mph between adjacent signs).
- **Individual gantries are spaced at ~0.5–1.0 mile (800–1600 m), not 50–100 m.**

### 4.5 Hua & Fan (2023)

*"Dynamic Speed Harmonization for Mixed Traffic Flow on the Freeway Using Deep Reinforcement Learning"*, IET-ITS 17.

- Control section = full upstream mainline (2 km) before the weaving area.
- DDPG agent sets differential speed limits per lane for the entire control section.
- **No sub-segment placement; the entire upstream section is the control zone.**

---

## 5. Summary: why the current design is correct

| Criterion | 50–100 m placement | Current 1000 m segments |
|---|---|---|
| Deceleration physics | Forced emergency braking | Comfortable 4.4 s deceleration |
| Flow rate metering | No time for headway adjustment | Sustained speed → adjusted headways |
| Literature precedent | None | All 5 papers above |
| SUMO implementation | Requires sub-edge splits | Native `setMaxSpeed()` per lane |
| Shockwave prevention | Creates new shockwaves | Prevents shockwaves (the VSL purpose) |
| Action space impact | 6+ sub-zone dimensions | 1 mainline + 1 ramp = 2D (tractable for TQC/SAC) |

The 200 m `ramp_on_transition` is the shortest controlled edge and sits at the lower bound of what is physically meaningful — justified because ramp vehicles are already at lower speeds (90 kph ramp limit vs. 120 kph mainline), requiring less deceleration distance.

---

## 6. Open question: CAV slowDown() vs lane.setMaxSpeed()

The analysis above covers `traci.lane.setMaxSpeed()` which primarily affects HDVs (via Krauss car-following response to lane speed limits). A separate investigation is needed for `traci.vehicle.slowDown()` — the direct CAV control command — to determine:

1. Whether `_apply_segment_limits()` (HDV lane limits) is necessary at all when CAVs are the primary control lever and HDVs will be forced to slow down by car-following dynamics behind decelerating CAVs.
2. Whether `slowDown()` should be applied only to CAVs on specific edges or to all CAVs in the network.
3. The interaction between lane-level speed limits and vehicle-level slowDown commands when both are active.
