# Control Loop — v5 Lagrangian Speed Harmonisation

## 1. Overview

The v5 control loop is a centralized, single-agent RL system that issues speed commands to Connected Automated Vehicles (CAVs) at 30 s intervals. The agent observes aggregate traffic state from E1 induction loop detectors and outputs a continuous 2D action — a mainline speed target and a ramp speed target. CAVs execute the command via `traci.vehicle.slowDown()`; Human-Driven Vehicles (HDVs) adapt indirectly through car-following dynamics.

This is a **Lagrangian control** architecture: the control acts on mobile agents (vehicles) rather than fixed infrastructure (signs). The term originates from fluid mechanics, where Lagrangian coordinates track individual particles (here, CAVs) as opposed to Eulerian coordinates that describe fixed spatial fields (here, lane speed limits) [R3].

---

## 2. Loop structure

```
┌─────────────────────────────────────────────────────────────────┐
│                    One control step (30 s)                      │
│                                                                 │
│  ┌──────────┐    ┌───────────┐    ┌──────────┐    ┌──────────┐  │
│  │ Collect  │───►│  Build    │───►│  TQC/SAC │───►│  Apply   │  │
│  │ E1 data  │    │  state    │    │  policy  │    │ slowDown │  │
│  │ (metrics)│    │  (38-dim) │    │ (2D act) │    │ to CAVs  │  │
│  └──────────┘    └───────────┘    └──────────┘    └──────────┘  │
│       ▲                                                │        │
│       │            ┌──────────┐                        │        │
│       │            │ Compute  │◄───────────────────────┘        │
│       │            │  reward  │                                 │
│       │            └────┬─────┘                                 │
│       │                 │                                       │
│       └─────────────────┘  (next 30 s of SUMO simulation)       │
└─────────────────────────────────────────────────────────────────┘
```

---

## 3. Step-by-step execution

Each call to `env.step(action)` executes the following sequence:

### Step 1: Action application

The TQC/SAC policy network outputs a 2D continuous action:

```python
action = np.array([mainline_kph, ramp_kph])  # e.g., [85.3, 62.7]
```

The action component (`r44_action_v0`) converts this to a speed limits dictionary:

```python
speed_limits_ms = {
    "seg_0_before": mainline_kph / 3.6,
    "seg_1_before": mainline_kph / 3.6,
    "seg_2_before": mainline_kph / 3.6,
    "ramp_on_transition": ramp_kph / 3.6,
}
```

The same mainline speed is applied uniformly to all three upstream segments — a single-zone controller. Per-segment differential control is a future extension. This uniform design follows Li et al. (2017) [R25], who use a single speed limit for the entire VSL-controlled section, and avoids the combinatorial action space explosion that Hua & Fan (2023) identified as a motivation for choosing continuous-action algorithms.

### Step 2: SUMO simulation advance (30 simulation seconds)

For each of the 30 SUMO steps (1 s each):

```python
traci.simulationStep()
for veh_id in traci.vehicle.getIDList():
    if is_cav(veh_id):
        edge = traci.vehicle.getRoadID(veh_id)
        limit = ramp_limit_ms if edge in RAMP_EDGES else mainline_limit_ms
        traci.vehicle.slowDown(veh_id, limit, 30.0)
```

**Why every simulation step?** The `slowDown()` command's duration parameter (30 s) means a single call would suffice per control window. However, new CAVs enter the network continuously — a vehicle that departs at simulation second 15 of a 30 s window would miss the command if it were issued only at the window start. Issuing at every step ensures all CAVs are captured immediately upon entry, consistent with Vinitsky et al. (2018) [R3] who update CAV max speed *"at each step for each segment"* (p. 761, Eq. 3–4).

**Zone assignment by edge:** Each CAV receives the speed command corresponding to the edge it currently occupies. CAVs on ramp edges (`ramp_on_approach`, `ramp_on_transition`, `ramp_on_merge`) receive the ramp speed; all others receive the mainline speed. This spatial conditioning is necessary because the ramp approach geometry requires lower speeds than the mainline (90 kph ramp design speed vs. 120 kph mainline).

**HDV response:** HDVs receive no direct command. They respond to decelerating CAVs ahead of them through the Krauss car-following model's collision avoidance logic. At 50% MPR, the expected gap between consecutive CAVs is ~2 vehicles (~80 m), so every HDV has a CAV within its car-following horizon. See `docs/slowDown_argument.md` for the full analysis and edge case probability estimates.

### Step 3: Metric collection

After the 30 s window, E1 induction loop detectors report aggregated measurements for all 12 network segments:

```python
for seg in ALL_SEGMENTS:   # 12 segments
    flow_vph, speed_ms, occ_pct = read_e1_detectors(seg, position="exit")
```

The `exit` detector position (95% of segment length) is used because it captures vehicles just before they leave the segment — providing the best predictive signal for downstream conditions. This is standard practice in VSL studies using induction loop data; Li et al. (2017) [R25] place their measurement point *"immediately downstream of the VSL controlled area"* (p. 3208) for the same reason.

### Step 4: State construction

The state component (`r44_state_v0`) extracts 12 features from the current metrics and appends the frame to a 3-frame stack (90 s temporal context):

| Feature | Source | Normalisation |
|---|---|---|
| seg_0_before speed, flow, occ | E1 at closest upstream segment | speed / 36.1, flow / 8000, occ / 100 |
| seg_0_after speed, flow, occ | E1 at weaving zone | speed / 36.1, flow / 8000, occ / 100 |
| ramp_on_approach flow | E1 at ramp approach | flow / 2000 |
| ramp_on_merge speed | E1 at merge point | speed / 25.0 |
| seg_1_after flow | E1 at downstream | flow / 8000 |
| Regime one-hot (3 values) | RegimeDetector on seg_0_before | {0, 1} |

The 3-frame stack provides temporal context without requiring recurrent networks (LSTM). This follows the DQN frame-stacking approach introduced by Mnih et al. (2015) and applied to traffic control by multiple studies in the knowledge base. The 90 s lookback covers approximately one corridor transit time at reduced speed (~80 kph over 2 km = 90 s), giving the agent visibility of the traffic wave propagation dynamics.

Two static features (normalised previous action) are appended outside the stack, yielding a **38-dimensional observation** in [0, 1].

### Step 5: Reward computation

The reward function (`r44_reward_v0`) computes three terms following the MARVEL deployment structure [R10]:

```
r_t = w_v · r_v + w_q · r_q + w_a · r_a
```

| Term | Formula | Purpose | Weight |
|---|---|---|---|
| Speed variance | `r_v = -min(((v_weaving - v_target) / v_target)², 1)` | Penalise speed deviation from 80 kph at weaving zone | 0.50 |
| Throughput | `r_q = min(flow_downstream / flow_reference, 1)` | Reward maintained downstream flow | 0.35 |
| Smoothness | `r_a = -‖Δaction‖₂ / ‖action_range‖` | Penalise oscillating speed commands | 0.15 |

The speed variance term uses the weaving zone (`seg_0_after`) rather than upstream segments because the weaving zone is where merge conflicts manifest — it is the observation point closest to the bottleneck mechanism. The throughput term uses `seg_1_after` (downstream of the weaving zone) because this is where the benefit of successful harmonisation is measurable: maintained flow despite high demand. This 3-term structure mirrors the MARVEL deployment reward (Zhang et al., 2024) [R10], which was designed for real-world deployment compatibility.

---

## 4. Timing summary

| Event | Frequency | Triggered by |
|---|---|---|
| Agent decision (TQC/SAC forward pass) | Every 30 s | `env.step()` |
| CAV `slowDown()` command | Every 1 s (SUMO step) | `_advance_sumo()` |
| E1 detector aggregation | Every 30 s | SUMO internal (freq=30 in detector XML) |
| Episode termination | After 3600 s (120 steps) | `step_count >= max_steps` |

---

## 5. What the agent does NOT control

- **Individual vehicle trajectories:** The agent sets a zone-level speed, not per-vehicle acceleration profiles.
- **Lane-change decisions:** SUMO's LC2013 model handles lane changes autonomously.
- **HDV speed directly:** No `setMaxSpeed()` or `slowDown()` is applied to HDVs. See `docs/slowDown_argument.md`.
- **Ramp metering:** There is no physical gate or traffic signal on the ramp. The ramp VSL slows CAVs on the transition segment, which indirectly meters ramp flow.

---

## 6. References

- **[R3]** Vinitsky, E. et al. (2018). Lagrangian Control through Deep-RL: Applications to Bottleneck Decongestion. *IEEE ITSC 2018*, 759–765.
- **[R10]** Zhang, Y. et al. (2024). MARVEL: Bringing Multi-Agent Reinforcement-Learning Based Variable Speed Limit Controllers Closer to Deployment. *IEEE Access, 12*, 161995–162012.
- **[R25]** Li, Z. et al. (2017). Reinforcement Learning-Based Variable Speed Limit Control Strategy to Reduce Traffic Congestion at Freeway Recurrent Bottlenecks. *IEEE T-ITS, 18*(11), 3204–3217.
- Mnih, V. et al. (2015). Human-Level Control through Deep Reinforcement Learning. *Nature, 518*, 529–533.
