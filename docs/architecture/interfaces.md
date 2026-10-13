# Interfaces (v0.1)

*2026-10-13. Status: draft for author review. Units are SI and euro (V20). **[PROPOSAL]** means a proposal that needs the author; **[TBD-protocol]** values are fixed in the protocol before any data. Each section says which review finding it resolves (`review_v0.md`).*

## 1. Vocabulary (resolves IF-C9)
| Term | Meaning (one meaning only) |
|---|---|
| **inflow** | vehicles arriving at the network boundary (V9). Never "demand" |
| **desired departure** | the time a vehicle wants to enter, from the inflow file. It is earlier than the actual insertion when there is an insertion queue |
| **cohort** | the vehicles scored in an episode (§5.1) |
| **zone** | a fixed mainline stretch (Z1–Z3) where CAVs accept commands, with one V2X zone unit |
| **decision boundary** | every 2 s of simulated time (10 steps of 0.2 s) |
| **snapshot** | the state at a decision boundary, read once and shared by every consumer |
| **command** | a CAV target-speed change of −5, 0 or +5 km/h |
| **target** | a CAV's commanded speed, in [v_min, 100] km/h |
| **arm** | one controller configuration under comparison (`system_context.md` §4) |
| **episode** | one simulation run: warm-up, scored inflow window, drain |
| **regime** | a pre-registered region of the scenario space (inflow level band, later CAV share, noise) |
| **invalid run** | more than 2 collisions or any teleport (V6). It counts as that arm's failure on that seed |

## 2. Time base and schedule (resolves BD-2, IF-C1, CX-F5)
- **SUMO step:** Δt = 0.2 s. **Decision period:** T_d = 2 s. There is no slower layer: no VSL or meter in our system. The I1/I2 arms update their posted limits every 60 s **[PROPOSAL]**.
- **Owner:** the `exp` episode loop. At each boundary it builds the snapshot, then calls v2x, then the arm, then exec, then the logger, in that order. Nothing commands SUMO between boundaries except `exec` hold logic.
- **Time-of-day:** never in any arm's observation **[PROPOSAL]**. The controller must learn when to act from what it measures (V8, V9), not from the clock.

## 3. Execution layer, `exec` (resolves IF-C5, IF-C7, BD-8; V26, V36)
| Rule | Specification |
|---|---|
| Entry | When a CAV enters a zone: target = its current speed, rounded to the nearest 5 km/h and clipped to [v_min, 100] |
| Command | target ← clip(target + 5·u, v_min, 100), with u ∈ {−1, 0, +1}. v_min = 30 km/h **[PROPOSAL]** |
| Apply | `vehicle.slowDown(id, target, 2.0)` at every boundary, so a ramp over 2 s is followed by the next ramp or hold. A ±5 km/h change over 2 s is about ±0.69 m/s² |
| Hold | Re-issuing `slowDown(target, 2.0)` with an unchanged target holds it. **T0 must verify** that SUMO does not release the vehicle to its desired speed between boundaries (the critic saw release after `slowDown` ends) |
| Safety | speedMode stays at the default (31): safe-gap car-following overrides any target. A command never forces a collision. There are no lane limits, so speedMode 95 (V5) is not needed |
| Exit | When a CAV leaves its zone: `setSpeed(id, -1)` releases it to its own ACC and desired speed |
| Rejection | A command that would exceed the bounds is clipped, not rejected; the clip is logged. Observations carry the current target, so a policy sees the clip |
| Fairness | Every commanding arm (R1–R4, L1, L2) goes through this same layer at the same 2-s rate |

## 4. Inflow family (V31) **[PROPOSAL; values TBD-protocol]**
- **Episode:** warm-up W = 15 min at base level, scored window T = 2.5 h, drain until all cohort vehicles arrive or a cap of 30 min after the window.
- **Mainline profile:** q(t) rises linearly from q₀ to q_peak at t_peak, then falls to q₁ (a morning triangle, rise faster than fall). The ramps R1 and R2 scale with their own peak levels; X1 and X2 take fixed shares of the mainline.
- **Noise:** Poisson arrivals, plus per-episode noise on peak level, peak time and widths. The magnitudes are labelled assumptions.
- **Sweep:** q_peak over a grid from under capacity to over capacity. Band = the levels where O or the best of R1–R4 reaches g = 10 % vs B0 (V45). The rule is fixed in the protocol before the sweep.
- **Common random numbers:** every arm on a seed sees the **same** inflow file and the same vehicle attributes (type, powertrain, speed factor, CAV flag). They are drawn once per seed, before the arm is known. Turning a vehicle into a CAV changes only its driver and control, never its powertrain (V42).

## 5. Metrics contract (resolves the blockers CX-F2 / EX-C2 and BD-3; V24, V25, V29, V37)
All metrics come from the simulator's ground-truth trace, the inflow manifest and the command log, inside `metrics/`. One implementation serves every arm.

### 5.1 Cohort and accounting
- **Cohort:** every vehicle whose desired departure lies in the scored window. All classes count: HDV cars, CAVs and trucks.
- **Door-to-door time** τ_v = arrival − desired departure. It includes the insertion queue, which never appears in a SUMO snapshot, so it is taken from the manifest.
- **Cut-off:** vehicles not arrived at the cap count up to the cap, and the run is flagged. Control stays active during the drain; there is no release at the end of the inflow.
- **Fixed denominator:** D = Σ over the cohort of the planned route length (km). Every "per vehicle-km" metric divides by D, so serving fewer kilometres cannot improve a ratio.

### 5.2 Delay
- **Reference time** r(route, class) = the median trip time on an almost empty network, with no control, the same fleet attributes and 100 km/h maximum. It is measured once per network version and stored with its hash.
- Delay d_v = τ_v − r(route_v, class_v). Network delay = Σ d_v (veh·h); also reported per vehicle.

### 5.3 Energy (V10, V34)
- Per vehicle and step, from SUMO HBEFA4 for cars: fuel in mg/s, electricity in Wh/s, × 0.2 s. Trucks use the road-load + Willans model, from the trace's speed and acceleration.
- **Conversion to kWh:** petrol 41.5 MJ/kg and 748 kg/m³ (E10); diesel 42.7 MJ/kg and 836 kg/m³ (B7) (JEC WTW v5; the Irish blend is [VERIFY]).
- **Electricity** is net of regeneration, at the battery. Grid energy = battery energy ÷ 0.90 charging efficiency (a labelled assumption) **[PROPOSAL]**.
- **Energy cost:** petrol €1.98/L, diesel €2.15/L, electricity €0.4042/kWh (V21).
- **Reported:** kWh per vehicle-km, the network total in kWh, € per scenario (V24), and CAV and HDV splits. HDV energy is labelled "estimated".

### 5.4 Generalised cost (headline, V29)
C = [Σ_v VoT_class · d_v + Σ_v € energy_v] / D, in € per vehicle-km.
- **VoT for cars:** €8.90 per person-hour (commuting, 2016 market prices) × 1.23 AM-peak occupancy. Uplifted to 2026 € with the TII real growth and the CSO price index. **[TBD: the computation is to be recorded step by step]**
- **VoT for trucks:** work VTT × 1.03 occupancy, uplifted the same way **[PROPOSAL]**.

### 5.5 Guards and constraints
- **Delay guard:** network delay must not exceed B0's by more than 2 % (V37). It is a one-sided paired test.
- **Hard braking (constraint, V25, V36):**
  - an event is a continuous stretch with CAV deceleration below −3 m/s²;
  - metric = events per CAV-km;
  - the constraint is "not worse than B1 by more than y %", with y **[TBD-protocol]**;
  - HDV braking is a placeholder only (V11).
- **Validity (V6):** collisions > 2 or teleports > 0 make the run invalid. It counts as that arm's failure on that seed.

### 5.6 Other reported metrics
- Stop-and-go cycles per vehicle-km on the mainline: a speed drop below 20 km/h followed by a rise above 50 km/h, per vehicle. Thresholds **[TBD-protocol]**.
- TTT over a fixed window (from the warm-up end to the cap).
- Served throughput.
- Per-zone travel time, to show congestion shifting.
- The CAV speed give-up: CAV mean speed vs B1.

## 6. V2X and V2V messages (resolves IF-C8, BD-9)
- **Zone unit Z_k**, every 2 s, from the probes CAVs report in that zone over the last 2 s:
  - per lane: CAV mean speed, CAV speed standard deviation, CAV count;
  - zone-wide: the same values.
  
  Empty lanes carry an explicit `n = 0` and fall back to a defined value (the last value, plus age).
- **V2V:** each CAV receives the speeds and gaps of up to k = 3 CAVs ahead within 300 m on its own and adjacent lanes **[PROPOSAL]**.
- **v0 delivery** is perfect and synchronous (zero delay, no loss), so the message carries no expiry or confidence fields (they cannot be exercised yet). Delay and loss are later robustness rows. Only then are age fields added.
- **Planned profiles (B4) are deferred** **[PROPOSAL]**. With per-CAV learned agents there is no zone-level plan to publish; coordination comes from shared summaries and, in L2, a centralised critic.

## 7. Arm and policy contracts (resolves BD-1, IF-C2, F3)
```python
class Arm:                                   # B1, R1–R4, I1–I2 and the PPO policies via an adapter
    def reset(self, scenario_meta) -> None: ...
    def act(self, obs: dict[str, np.ndarray]) -> dict[str, int]:   # cav_id -> u ∈ {-1, 0, +1}
        ...
```
- **One observation builder** (`v2x` + `exp`) produces each CAV's observation from a declared **observation spec**:
  - `local` (L1, R1): own state + leader + V2V;
  - `zone` (L2, R2, R3): `local` + own-zone and downstream-zone summaries.
- Arms never receive the raw snapshot.
- The spec's hash is written to the ledger. A contract test asserts that no field outside the spec reaches an arm.

**CAV observation (`zone` spec) [PROPOSAL]:**
- own: speed, acceleration, current target, lane (one-hot), position in zone (0–1), zone id (one-hot);
- leader (radar): present flag, gap, closing speed;
- V2V: up to 3 CAVs ahead (relative position, speed, mask);
- V2X: own zone + the next downstream zone, zone-wide mean speed and standard deviation + per-lane mean speeds.

All values are normalised to [−1, 1] with fixed constants (not running statistics) so that every arm and seed sees the same scaling.

- **I1/I2** act on posted limits, not on CAVs. They use a separate `InfraArm.act(zone_summaries) → limits` with the same snapshot rule.
- **The centralised critic (L2)** may read a privileged global state during **training only**. The deployed policy never does.

## 8. RL environment (V7, V17; ADR-001)
- `F3ZParallelEnv(pettingzoo.ParallelEnv)`. An agent is a CAV inside a zone; it appears on entry and leaves on exit (`terminations[id] = True` at exit).
- **Action:** `Discrete(3)` → u ∈ {−1, 0, +1}.
- **Reward [PROPOSAL]**, per agent per decision:

  r_i = −( VoT·Δd_i + €·ΔE_i ) − β · ΔC_net / N_zone − κ · 1[hard brake_i]

  - Δd_i = (1 − v_i / v_ref)·T_d is the incremental delay. Over a trip it integrates exactly to the trip's delay against v_ref.
  - ΔE_i is the vehicle's energy in the interval.
  - ΔC_net is the generalised cost of **all** vehicles in the corridor in the interval (ground truth; a training instrument only).
  - β and κ are tuned on validation within the budget.

  The same mix as the headline, so the policy optimises what is scored.
- **Budget, seeds and checkpoints:** as in `CLAUDE.md`. Training seeds 7,410,000–7,419,999; validation-only checkpoint selection; L1 and L2 get the same budget.

## 9. Fault rows (resolves IF-C10, IF-C6)
| Fault | Detection | Owner | Response | Recorded |
|---|---|---|---|---|
| Teleport | SUMO teleport count each step | `plant` | the run continues to the end, marked invalid (V6) | ledger, validity flag |
| Collision | SUMO collision list (each pair counted once) | `plant` | as above when > 2 | same |
| SUMO crash or exception | the worker exits non-zero | `ops` scheduler | the run is marked failed in the ledger; the same seed is re-run once; a second failure keeps it failed and is reported | ledger |
| NaN or negative-infinite energy | a check in `metrics` | `metrics` | the run is invalid; never patched | ledger |
| CAV leaves the zone mid-ramp | zone membership at the boundary | `exec` | release at the next boundary at the latest | command log |
| A command clipped at a bound | in `exec` | `exec` | clip and log | command log |
| An empty V2X lane or zone | n = 0 | `v2x` | defined fallback value + flag | trace |
| A worker hangs | wall-time limit per job | `ops` | kill, mark failed | ledger |

## 10. Records (resolves EX-C4, EX-C5, CX-F9)
- **Per run:** config hash, code commit + dirty flag (read at start **and** end), network spec hash, inflow file hash, observation-spec hash, trainer id (L arms), seed and role, validity, metric summary, and a determinism hash of the trajectory summary.
- **Ledger:** one row per run, including failed and invalid ones (ported `ops/ledger.py`).
- Raw traces go under `/home/catalin/work/phd/` on ext4, never into the repo.
