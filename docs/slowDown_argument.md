# Lagrangian Control via `slowDown()` — Why Lane Speed Limits Are Removed

## 1. The design decision

In the v5 iteration, the environment uses **pure Lagrangian control**: the RL agent's action is enforced exclusively through `traci.vehicle.slowDown()` on Connected Automated Vehicles (CAVs). The lane-level speed cap (`traci.lane.setMaxSpeed()`) has been removed from the control loop.

HDVs are not directly controlled. They slow down indirectly through car-following dynamics behind decelerating CAVs.

---

## 2. What `traci.vehicle.slowDown()` does

```python
traci.vehicle.slowDown(veh_id, target_speed_ms, duration_s)
```

This TraCI command instructs a specific vehicle to reduce its speed to `target_speed_ms` over `duration_s` seconds using a smooth deceleration profile. The vehicle's car-following model is temporarily overridden — the vehicle will decelerate regardless of what its leader is doing. Once the duration expires, the vehicle resumes normal car-following behaviour.

In the v5 control loop, this command is issued to every CAV at every SUMO simulation step (1 s), with `duration_s = aggregation_time` (30 s). This means the CAV is continuously held at the commanded speed for the entire control window.

---

## 3. Why `lane.setMaxSpeed()` is removed

### 3.1 The v4 → v5 paradigm shift

The v4 system posted speed limits on Variable Message Signs (VMS) and relied on HDV compliance — which was partial and unreliable. The v5 system abandons physical signs entirely: CAVs receive digital speed commands via V2I/V2V communication and comply perfectly; HDVs are never directly told to slow down.

This is the Lagrangian control paradigm introduced by Vinitsky et al. (2018) [R3]: *"we train the AVs with the goal of maximizing the outflow of the bottleneck [...] AVs can learn to effectively act like a ramp meter"* (p. 760). The control acts on mobile agents (vehicles) rather than fixed infrastructure (signs), hence "Lagrangian" — borrowed from fluid mechanics where Lagrangian coordinates track individual particles rather than fixed spatial points (Eulerian).

Applying `lane.setMaxSpeed()` simultaneously with `vehicle.slowDown()` conflates the two paradigms: it is both Lagrangian (CAV commands) and Eulerian (lane-level caps). This makes it impossible to isolate the Lagrangian contribution in experimental results.

### 3.2 HDVs comply through car-following, not signs

At 50% Market Penetration Rate (MPR), approximately every second vehicle is a CAV. When a CAV decelerates, the HDV behind it must decelerate too — the Krauss car-following model enforces collision avoidance regardless of lane speed limits. The HDV does not "choose" to comply; it is physically constrained by the slower vehicle ahead.

Ko et al. (2020) [R24] demonstrate this mechanism in a merge scenario: *"the speed harmonisation component [...] controls CAVs' speeds, and the following human-driven vehicles naturally adjust"* (Section 4.2). Vinitsky et al. (2018) [R3] show that at just 10% CAV penetration, the Lagrangian controller already improves bottleneck throughput by 25% — HDV compliance with signs is not required.

### 3.3 The edge case: HDVs ahead of all CAVs

At 50% MPR with random vehicle insertion, some HDVs may find themselves ahead of all CAVs on their lane within the controlled corridor. These vehicles receive no speed restriction from either mechanism.

**Probability estimate:** On a 1000 m segment at 50% MPR with average headway ~40 m (density ~25 veh/km/lane), there are ~25 vehicles per lane. The probability that all vehicles ahead of a given position are HDVs for k consecutive positions follows a geometric distribution: P(k HDVs in a row) = 0.5^k. For k = 5 (200 m of uncontrolled HDVs): P = 3.1%. For k = 10 (400 m): P = 0.1%. The expected length of an HDV-only platoon at the head of a lane is ~80 m (2 vehicles). This is a negligible fraction of the 3 km controlled corridor.

At 75% and 100% MPR, the edge case effectively vanishes.

### 3.4 CAV release point and controlled zones

CAVs are only held at the VSL speed on **controlled edges**. Once a CAV leaves the controlled zone, it resumes normal car-following behaviour and accelerates back to free-flow speed. The controlled zones are:

```
Mainline controlled:  seg_2_before → seg_1_before → seg_0_before
                      (3 km upstream corridor)

Ramp controlled:      ramp_on_approach → ramp_on_transition
                      (900 m: approach 700 m + transition 200 m)

Release point:        ramp_on_merge (100 m) — geometry dominates (~25 kph)
                      seg_0_after (500 m weaving zone) — CAVs accelerate
                      seg_1_after (1 km downstream) — free-flow
```

**Why release at the start of seg_0_after:** The purpose of the VSL is to shape the inflow upstream of the bottleneck. Once a vehicle has passed the merge junction (J4), its speed no longer affects the merge conflict dynamics — it is downstream of the bottleneck. Holding CAVs at 90 kph in the 4-lane weaving zone would reduce downstream throughput without benefiting the merge. Releasing them immediately allows them to accelerate back to free-flow speed, preserving capacity.

**Why release ramp_on_merge:** The merge curve geometry forces all vehicles (CAVs and HDVs) to ~20–29 kph regardless of the approach speed (baseline data: ramp_on_merge avg speed = 25 kph at all demands from 5000 to 7500 vph). Applying `slowDown()` on the merge curve adds no control authority — the geometric constraint is binding.

**Implementation:** `_apply_cav_slowdown()` in `env_interact.py` uses a 3-zone design:
- CAVs on `_MAINLINE_CONTROLLED_EDGES` → `slowDown(mainline_limit_ms)`
- CAVs on `_RAMP_CONTROLLED_EDGES` → `slowDown(ramp_limit_ms)`
- CAVs on any other edge → no `slowDown()` issued (free-flow)

### 3.5 Cleaner experimental design

With pure Lagrangian control, the experimental comparison is:
- **No control** (baseline): all vehicles at free-flow speed
- **Lagrangian CAV control** (agent): CAVs receive `slowDown()`, HDVs follow

This isolates the contribution of Lagrangian control. Adding `setMaxSpeed()` would introduce a confound: is the improvement from CAV commands or from lane speed caps? The thesis cannot answer this question if both are active simultaneously.

---

## 4. Future iteration: advisory HDV speed limits (TODO)

In a future project iteration, `lane.setMaxSpeed()` may be re-introduced as a **secondary, advisory effect** for HDVs, simulating low-frequency advisory VMS signs:

- **Granularity:** 5 kph steps (rounded up to the nearest 5 kph from the agent's continuous action)
- **Update frequency:** every 5 minutes (10 control windows), not every 30 s — reflecting realistic VMS update rates and MUTCD sign-change interval guidelines [R10]
- **Purpose:** catch the rare HDVs ahead of all CAVs and provide advisory guidance
- **Implementation:** a separate method called every 10th `step()`, reading the current mainline action, rounding to 5 kph, and applying `lane.setMaxSpeed()` to controlled segments

This would be evaluated as an ablation study: pure Lagrangian vs. Lagrangian + advisory VMS.

---

## 5. References

- **[R3]** Vinitsky, E. et al. (2018). Lagrangian Control through Deep-RL: Applications to Bottleneck Decongestion. *IEEE ITSC 2018*, 759–765.
- **[R10]** Zhang, Y. et al. (2024). MARVEL: Bringing Multi-Agent Reinforcement-Learning Based Variable Speed Limit Controllers Closer to Deployment. *IEEE Access, 12*, 161995–162012.
- **[R24]** Ko, B. et al. (2020). Speed Harmonisation and Merge Control Using Connected Automated Vehicles on a Highway Lane Closure. *IET Intelligent Transport Systems, 14*(8), 947–957.
