# VSL Placement Rationale — ramps_v2 Topology

**Updated:** 2026-03-20 — revised for v5.1 mixed Lagrangian-Eulerian design with per-lane control.

## 1. The question

Which segments should carry VSL control, what type of VSL (physical sign vs. virtual CAV command), and why are some segments deliberately left uncontrolled?

**Answer:** The v5.1 design uses a **two-zone control architecture** — physical Eulerian VSL on seg_1_before (pre-conditioning) and virtual Lagrangian per-lane VSL on seg_0_before (merge approach). Upstream segments (seg_2_before, seg_3_before) are uncontrolled free-flow reference zones. Downstream segments are observation-only. This document provides the full justification.

---

## 2. Current design

The ramps_v2 topology uses two distinct control mechanisms on two segments:

| Controlled edge | Length | Dist. to merge | Type | Mechanism | Applies to |
|---|---|---|---|---|---|
| `seg_1_before` | 1000 m | 1000–1500 m | **Physical VSL** (posted sign + radar) | `traci.edge.setMaxSpeed()` | HDV (92%) + CAV (100%) |
| `seg_0_before` | 1000 m | 0–1000 m | **Virtual VSL** (per-lane Lagrangian) | `traci.vehicle.slowDown()` per lane | CAV only (50% of traffic) |
| `ramp_on_transition` | 200 m | 100 m | **Virtual VSL** (Lagrangian) | `traci.vehicle.slowDown()` | CAV only |

| Uncontrolled edge | Length | Purpose |
|---|---|---|
| `seg_3_before`, `seg_2_before` | 1000 m each | Free-flow reference; incoming demand measurement |
| `seg_0_after` | 500 m | Merge zone observation (E1/E3 sensors) |
| `seg_1_after` | 1000 m | Downstream throughput measurement |

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

## 5. Summary: why the current two-zone design is correct

| Criterion | seg_2_before (uncontrolled) | seg_1_before (physical VSL) | seg_0_before (virtual per-lane) |
|---|---|---|---|
| Distance to merge | 2000–2500 m (72–90 s transit) | 1000–1500 m (36–54 s transit) | 0–1000 m (0–36 s transit) |
| Credit assignment | 2.4–3.0 control steps delay | 1.2–1.8 steps — within γ=0.99 horizon | Immediate — direct merge effect |
| Control type | None (free-flow reference) | Uniform physical sign (MUTCD-compliant) | Per-lane CAV commands (digital) |
| HDV reach | N/A | 92% compliance via radar enforcement | Indirect via car-following behind CAVs |
| Literature | Han et al. [R26] Area I (uncontrolled) | Li et al. [R25], MARVEL [R10] (posted VSL) | Wu et al. [R29], Zhao et al. [R6] (per-lane) |
| Action space impact | 0 dimensions | 1 dimension (Box(5) only) | 3 dimensions (per-lane) |

The 200 m `ramp_on_transition` is the shortest controlled edge and sits at the lower bound of what is physically meaningful — justified because ramp vehicles are already at lower speeds (90 kph ramp design speed vs. 120 kph mainline), requiring less deceleration distance.

---

## 6. Resolved: CAV slowDown() and lane.setMaxSpeed() coexistence

The v5.0 open question about `slowDown()` vs. `setMaxSpeed()` is resolved in v5.1 by using **both mechanisms on different segments**:

- **seg_0_before**: Pure Lagrangian (`slowDown()` on CAVs only). HDVs follow via car-following. No `setMaxSpeed()` — preserves clean experimental isolation of Lagrangian contribution.
- **seg_1_before (Box(5))**: Mixed Lagrangian-Eulerian. `setMaxSpeed()` provides the physical sign for HDVs; `slowDown()` provides instant CAV compliance. The two mechanisms reinforce each other — CAVs decelerate immediately, HDVs follow the sign with 92% compliance.

This resolves the interaction concern raised in v5.0: the two mechanisms act on **different segments**, so there is no conflict between lane-level caps and vehicle-level commands on the same edge.
