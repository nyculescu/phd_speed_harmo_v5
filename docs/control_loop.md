# Control Loop — v5.1 Mixed Lagrangian-Eulerian Speed Harmonisation

## 1. Overview

The v5.1 control loop is a centralized, single-agent RL system that issues speed commands at 30 s intervals using two distinct control mechanisms:

1. **Lagrangian** (virtual VSL): `traci.vehicle.slowDown()` commands sent to Connected Automated Vehicles (CAVs) on seg_0_before (per-lane) and ramp_on_transition. CAVs comply at 100%.
2. **Eulerian** (physical VSL, Box(5) only): `traci.edge.setMaxSpeed()` applied to seg_1_before, simulating a posted overhead VSL sign with radar enforcement. HDVs comply at ~92%; CAVs comply at 100%.

This **mixed Lagrangian-Eulerian** architecture combines the precision of direct CAV control (Vinitsky et al. [R3]) with the universal reach of posted signs (MARVEL [R10]). The Box(4) variant uses pure Lagrangian control; the Box(5) variant adds the Eulerian dimension for experimental comparison.

---

## 2. Loop structure

```
┌──────────────────────────────────────────────────────────────────────┐
│                       One control step (30 s)                        │
│                                                                      │
│  ┌──────────┐    ┌───────────┐    ┌──────────┐    ┌──────────────┐   │
│  │ Collect  │───►│  Build    │───►│  TQC/SAC │───►│  Apply:      │   │
│  │ E1 + E3  │    │  state    │    │  policy  │    │  slowDown    │   │
│  │ per-lane │    │  (77-dim) │    │ (4D/5D)  │    │  per-lane    │   │
│  │ + anomaly│    │           │    │          │    │  + setMax    │   │
│  └──────────┘    └───────────┘    └──────────┘    │  (Box5 only) │   │
│       ▲                                           └──────┬───────┘   │
│       │            ┌──────────┐                          │           │
│       │            │ Compute  │◄─────────────────────────┘           │
│       │            │  reward  │                                      │
│       │            │  (5-term)│                                      │
│       │            └────┬─────┘                                      │
│       │                 │                                            │
│       └─────────────────┘  (next 30 s of SUMO simulation)            │
└──────────────────────────────────────────────────────────────────────┘
```

---

## 3. Step-by-step execution

Each call to `env.step(action)` executes the following sequence:

### Step 1: Action application

The TQC/SAC policy network outputs a 4D or 5D continuous action:

```python
# Box(4) — pure Lagrangian:
action = np.array([L0_kph, L1_kph, L2_kph, ramp_kph])  # e.g., [95.0, 88.0, 82.0, 65.0]

# Box(5) — mixed Lagrangian-Eulerian:
action = np.array([L0_kph, L1_kph, L2_kph, ramp_kph, seg1_kph])  # e.g., [95.0, 88.0, 82.0, 65.0, 100.0]
```

The action component converts this to a speed limits dictionary:

```python
speed_limits_ms = {
    "seg_0_before_L0": action[0] / 3.6,   # per-lane (CAV slowDown)
    "seg_0_before_L1": action[1] / 3.6,   # per-lane (CAV slowDown)
    "seg_0_before_L2": action[2] / 3.6,   # per-lane (CAV slowDown)
    "ramp_on_transition": action[3] / 3.6, # ramp CAV slowDown
    # Box(4): seg_1_before receives min(L0, L1, L2) as passive CAV-only limit
    # Box(5): seg_1_before receives action[4] as physical VSL (HDV + CAV)
}
```

The per-lane design on seg_0_before follows Wu et al. (2020) [R29] and Zhao et al. [R6], who use per-lane differential VSL with continuous-action actor-critic algorithms because discrete per-lane formulations produce combinatorially explosive action spaces (7³ = 343 for 3 lanes × 7 levels).

### Step 2: SUMO simulation advance (30 simulation seconds)

For each of the 30 SUMO steps (1 s each):

```python
traci.simulationStep()
for veh_id in traci.vehicle.getIDList():
    edge = traci.vehicle.getRoadID(veh_id)
    if is_cav(veh_id):
        if edge == "seg_0_before":
            lane_idx = traci.vehicle.getLaneIndex(veh_id)
            limit = per_lane_limits[lane_idx]  # L0, L1, or L2
        elif edge in RAMP_EDGES:
            limit = ramp_limit_ms
        elif edge in MAINLINE_CONTROLLED:
            limit = upstream_limit_ms  # min(L0,L1,L2) or action[4]
        else:
            continue
        traci.vehicle.slowDown(veh_id, limit, 30.0)
    elif use_box5 and edge == "seg_1_before":
        # HDV on physical VSL segment — compliance is stochastic
        if not _is_non_compliant(veh_id):  # 92% comply
            pass  # Krauss follows edge max speed (set below)
        else:
            traci.vehicle.setMaxSpeed(veh_id, 33.33)  # ignore sign

# Box(5) only: set physical VSL on seg_1_before
if use_box5:
    traci.edge.setMaxSpeed("seg_1_before", seg1_limit_ms)
```

**Per-lane assignment on seg_0_before:** Each CAV receives the speed limit for its current lane via `traci.vehicle.getLaneIndex()`. If a CAV changes lanes mid-window, it receives the new lane's limit at the next simulation step — this is physically correct (the vehicle is now in a different control zone).

**Why every simulation step?** New CAVs enter the network continuously. Issuing `slowDown()` at every step ensures all CAVs are captured immediately upon entry, consistent with Vinitsky et al. [R3] who update CAV max speed *"at each step for each segment"* (p. 761, Eq. 3–4).

**HDV response on seg_0_before and seg_2_before:** HDVs receive no direct command. They respond to decelerating CAVs ahead of them through the Krauss car-following model. At 50% MPR, the expected gap between consecutive CAVs is ~2 vehicles (~80 m). See `docs/slowDown_argument.md`.

**HDV response on seg_1_before (Box(5) only):** HDVs respond to the physical VSL sign via `traci.edge.setMaxSpeed()`, which caps the lane speed in the Krauss model. 92% of HDVs comply (radar enforcement); 8% retain free-flow speed. This stochastic compliance creates return variance — the key differentiator for TQC vs SAC.

### Step 3: Metric collection

After the 30 s window, E1 induction loop detectors report aggregated measurements for all 12 network segments:

```python
for seg in ALL_SEGMENTS:   # 12 segments
    flow_vph, speed_ms, occ_pct = read_e1_detectors(seg, position="exit")
```

The `exit` detector position (95% of segment length) is used because it captures vehicles just before they leave the segment — providing the best predictive signal for downstream conditions. This is standard practice in VSL studies using induction loop data; Li et al. (2017) [R25] place their measurement point *"immediately downstream of the VSL controlled area"* (p. 3208) for the same reason.

### Step 4: State construction

The state component extracts 24 features per frame and appends to a 3-frame stack (90 s temporal context):

**Per-frame features (24):**

| Feature | Source | Dimensions |
|---|---|---|
| seg_2_before, seg_1_before speed/flow/occ (aggregate) | E1 exit | 6 |
| seg_0_before L0/L1/L2 speed/flow/occ (per-lane) | E1 per-lane exit | 9 |
| seg_0_after speed/flow/occ (aggregate) | E1 exit | 3 |
| ramp_on_approach flow, ramp_on_merge speed | E1 | 2 |
| seg_1_after flow | E1 exit | 1 |
| Regime one-hot (FREE_FLOW, METASTABLE, CONGESTED) | RegimeDetector | 3 |

**Static features (5):** previous action (normalised, 4 dims) + anomaly_active flag.

**Total: 3 × 24 + 5 = 77 dimensions** in [0, 1].

The per-lane observations at seg_0_before (9 features) are essential for per-lane control: the agent must observe per-lane speed/flow/occupancy to make informed differential decisions. This follows Wu et al. (2020) [R29] and Zhao et al. [R6], who include per-lane detector readings when per-lane actions are available.

### Step 5: Reward computation

The reward function computes five terms — the MARVEL 3-term core [R10] extended with two per-lane control terms:

```
r_t = 0.40·r_harmo + 0.25·r_throughput + 0.10·r_smooth + 0.15·r_lane_grad + 0.10·r_merge
```

| Term | Formula | Purpose | Weight |
|---|---|---|---|
| Harmonisation | `−min(σ_upstream / σ_max, 1)` | Upstream spatial + temporal speed variance | 0.40 |
| Throughput | `−max(0, 1 − flow_ds / flow_ref)` | Penalise flow collapse at seg_1_after | 0.25 |
| Smoothness | `−‖Δaction‖₂ / ‖action_range‖` | Penalise oscillating 4D commands | 0.10 |
| Lane gradient | `−min(max(\|L0−L1\|, \|L1−L2\|) / 20, 1)` | Penalise inter-lane speed gaps at seg_0_before | 0.15 |
| Merge match | `−min(\|L0_speed − ramp_merge_speed\| / 30, 1)` | Reward matching merge lane to ramp speed | 0.10 |

The two new terms address the per-lane control problem: r_lane_grad discourages dangerous inter-lane speed differentials (MUTCD safety); r_merge rewards reducing the speed mismatch at J4 — the primary cause of merge shockwaves [R5], [R24]. The 3-term core structure mirrors MARVEL [R10].

---

## 4. Timing summary

| Event | Frequency | Triggered by |
|---|---|---|
| Agent decision (TQC/SAC forward pass) | Every 30 s | `env.step()` |
| CAV `slowDown()` command (per-lane on seg_0_before) | Every 1 s (SUMO step) | `_advance_sumo()` |
| Physical VSL update on seg_1_before (Box(5) only) | Every 30 s | `env.step()` |
| Anomaly injection check | Every 1 s | `AnomalyInjector.step()` |
| E1/E3 detector aggregation | Every 30 s | SUMO internal (freq=30 in detector XML) |
| Episode termination | After 3600 s (120 steps) | `step_count >= max_steps` |

---

## 5. What the agent does NOT control

- **Individual vehicle trajectories:** The agent sets zone-level and lane-level speeds, not per-vehicle acceleration profiles.
- **Lane-change decisions:** SUMO's LC2013 model handles lane changes autonomously. Per-lane speed differentials may influence lane-change incentives, but the agent does not command lane changes.
- **HDV speed on seg_0_before:** No `setMaxSpeed()` or `slowDown()` is applied to HDVs on the per-lane virtual VSL segment. HDVs follow CAVs via car-following. See `docs/slowDown_argument.md`.
- **HDV speed on seg_1_before (Box(4)):** In Box(4), seg_1_before is CAV-only (passive limit). In Box(5), HDVs respond to the physical sign with 92% compliance.
- **Ramp metering:** There is no physical gate or traffic signal on the ramp. The ramp VSL slows CAVs on the transition segment, which indirectly meters ramp flow.
- **Anomaly resolution:** The agent observes the `anomaly_active` flag but cannot remove the anomaly — it must adapt its speed policy to mitigate the disruption.

---

## 6. References

- **[R3]** Vinitsky, E. et al. (2018). Lagrangian Control through Deep-RL: Applications to Bottleneck Decongestion. *IEEE ITSC 2018*, 759–765.
- **[R5]** Ghiasi, A. et al. (2019). A Mixed Traffic Speed Harmonization Model with Connected Autonomous Vehicles. *TRC, 104*, 210–233.
- **[R6]** Zhao, D. et al. (2021). A Lane-Level VSL Approach Based on TD3 in a CAV Environment. *AAP, 160*.
- **[R10]** Zhang, Y. et al. (2024). MARVEL: Bringing Multi-Agent Reinforcement-Learning Based Variable Speed Limit Controllers Closer to Deployment. *IEEE Access, 12*, 161995–162012.
- **[R24]** Ko, B. et al. (2020). Speed Harmonisation and Merge Control Using CAVs on a Highway Lane Closure. *IET ITS, 14*(8), 947–957.
- **[R29]** Wu, Y. et al. (2020). Differential Variable Speed Limits Control for Freeway Recurrent Bottlenecks via Deep Actor-Critic Algorithm. *TRC, 117*.
