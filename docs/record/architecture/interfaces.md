# Interfaces (v0.2)

*2026-10-13. Status: draft for author review; v0.2 (same day) applies the protocol decisions approved by V65 (protocol `docs/research/protocol_p0p2_v1.md` v1, items A8, A9, A10, A12, A14, A19, A27–A30, A35) and the V64 layout. Units are SI and euro (V20). **[PROPOSAL]** means a proposal that needs the author; **[TBD-protocol]** values are fixed in the protocol before any data. Each section says which review finding it resolves (`review_v0.md`).*

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
| **invalid run** | more than 2 collisions or any teleport (V6), or any other FAIL row of the protocol's health layer (protocol §2.7, A19). It counts as that arm's failure on that seed |

## 2. Time base and schedule (resolves BD-2, IF-C1, CX-F5)
- **SUMO step:** Δt = 0.2 s. **Decision period:** T_d = 2 s. There is no slower layer: no VSL or meter in our system. The I1/I2 arms update their posted limits every 60 s. The limit is the zone's mean CAV-probe speed over the last 60 s, rounded **up** to the next 10 km/h and capped at 100 km/h (V55).
- **Owner:** the `exp` episode loop. At each boundary it builds the snapshot, then calls v2x, then the arm, then exec, then the logger, in that order. Nothing commands SUMO between boundaries: `exec` makes exactly one call per CAV per boundary, and the hold is a `setSpeed` call made at a boundary (§3; protocol T0a).
- **Time-of-day:** never in any arm's observation **[PROPOSAL]**. The controller must learn when to act from what it measures (V8, V9), not from the clock.

## 3. Execution layer, `exec` (resolves IF-C5, IF-C7, BD-8; V26, V36)
| Rule | Specification |
|---|---|
| Entry | At the first 2-s boundary after a CAV's front enters a zone: target = its current speed, rounded to the nearest 5 km/h and clipped to [v_min, 100]. The target is reached with `slowDown(id, target, 2.0)` from the current speed, never with a `setSpeed` step (a step from 97.4 to 95 km/h brakes at −3.333 m/s² for one 0.2-s step, a V36 hard brake made by `exec`). If the arm also commands u = ±1 at that boundary, the same single call ramps to the rounded target ± 5 km/h: at most 7.5 km/h over 2 s, ≤ 1.04 m/s² (protocol §2.5, A9) |
| Command | target ← clip(target + 5·u, v_min, 100), with u ∈ {−1, 0, +1}. v_min = 50 km/h (V47) |
| Apply | If the target changed at a boundary: `vehicle.slowDown(id, target, 2.0)`, a ramp over 2 s. A ±5 km/h change over 2 s is about ±0.69 m/s². Exactly one `exec` call per CAV per boundary, none between boundaries |
| Hold | If the target is unchanged and the previous ramp has ended: `vehicle.setSpeed(id, target)` holds it (V36; protocol A9). Re-issuing `slowDown` is not used (toy: re-issuing it every step never reached the target; protocol §2.5). T0a verifies the hold: \|v − target\| ≤ 0.01 km/h for ≥ 20 s and no release between boundaries; a once-only `slowDown` variant must FAIL that test (protocol §5) |
| Safety | speedMode stays at the default (31): safe-gap car-following overrides any target. A command never forces a collision. There are no lane limits, so speedMode 95 (V5) is not needed |
| Exit | At the first boundary after a CAV leaves its zone: `setSpeed(id, -1)` releases it to its own ACC and desired speed (V36; protocol A10 (a)). The ACC then accelerates at its own rate (2.6 m/s² in the toy); there is no release ramp and no command outside a zone |
| Rejection | A command that would exceed the bounds is clipped, not rejected; the clip is logged. Observations carry the current target, so a policy sees the clip |
| Fairness | Every commanding arm (R1–R4, L1, L2) goes through this same layer at the same 2-s rate |

## 4. Inflow family (V31) (fixed in protocol §2.4)
- **Episode:** warm-up W = 15 min at base level, scored window T = 2.5 h, drain until all cohort vehicles arrive or a cap of 30 min after the window.
- **Mainline profile:** q(t) rises linearly from q₀ to q_peak at t_peak, then falls to q₁ (a morning triangle, rise faster than fall). The on-ramps OR1 and OR2 (renamed from R1, R2 so that they cannot be confused with the arms; protocol A13) scale with their own peak levels; X1 and X2 take fixed shares of the mainline.
- **Noise:** Poisson arrivals, plus per-episode noise on peak level, peak time and widths. The magnitudes are labelled assumptions.
- **Sweep:** q_peak over a grid from under capacity to over capacity. Band = the levels where O or the best of R1–R4 reaches g = 10 % vs B0 (V45). The rule is fixed in the protocol before the sweep.
- **Fixed for P0–P2 by the protocol** (§2.4, A12, V65): q₀ = 0.5·q̂ in the warm-up and at window start, a linear rise to q̂ at 5,160 s from episode start, a linear fall to 0.7·q̂ at 9,900 s; inflow stops at the window end; λ scales all three streams; per-episode noise is off in P0–P2 and enters later as a pre-registered robustness row.
- **Common random numbers:** every arm on a seed sees the **same** inflow file and the same vehicle attributes (type, powertrain, speed factor, CAV flag). They are drawn once per seed, before the arm is known. Turning a vehicle into a CAV changes only its driver and control, never its powertrain (V42).

## 5. Metrics contract (resolves the blockers CX-F2 / EX-C2 and BD-3; V24, V25, V29, V37)
All metrics come from the simulator's ground-truth trace, the inflow manifest and the command log, inside `metrics/`. One implementation serves every arm.

### 5.1 Cohort and accounting
- **Cohort:** every vehicle whose desired departure lies in the scored window [900, 9,900) s (protocol §3.1). All classes count: HDV cars, CAVs and trucks.
- **Door-to-door time** τ_v = arrival − desired departure. It includes the insertion queue, which never appears in a SUMO snapshot, so it is taken from the manifest.
- **Cut-off:** vehicles not arrived at the cap (t = 11,700 s, V49) count up to the cap, and the run is flagged. Inflow stops at the window end (9,900 s), so the drain adds no new arrivals (protocol §2.4). Control stays active during the drain; there is no release at the end of the inflow.
- **Fixed denominator:** D = Σ over the cohort of the planned route length (km). Every "per vehicle-km" metric divides by D, so serving fewer kilometres cannot improve a ratio.

### 5.2 Delay
- **Reference time** r(route, cat), cat ∈ {car, truck} (protocol A8 (a), V65): the median trip time (insertion to arrival) per route and vehicle category in **B0** (no control, the same fleet attributes, 100 km/h maximum) at λ = 0.05, pooled over the calibration seeds 7,400,002–009. A cell needs ≥ 20 vehicles; a sparser cell uses the category's median free-flow pace × the route length, and such cells are recorded. It is measured once per network version and stored with the network hash and its own hash.
- **The same r table serves every arm.** It is indexed by vehicle category, never by driver class, so a vehicle has the same reference in B0, B1 and every commanding arm (a driver-class index would bias C across arms).
- Delay d_v = τ_v − r(route_v, cat_v). Network delay Dl = Σ d_v (veh·h); also reported per vehicle. R_tot = Σ_v r_v, the cohort's total reference time, is used by the delay-guard floor (§5.5).

### 5.3 Energy (V10, V34)
- Over each vehicle's whole trip, per step, from SUMO HBEFA4 for cars: fuel in mg/s, electricity in Wh/s, × 0.2 s. Trucks use the road-load + Willans model, from the trace's speed and acceleration.
- **Conversion to kWh:** petrol 41.5 MJ/kg and 748 kg/m³ (E10); diesel 42.7 MJ/kg and 836 kg/m³ (B7) (JEC WTW v5; the Irish blend is [VERIFY]).
- **Electricity** is net of regeneration, at the battery, and priced as is. There is no charging-loss factor for now (V53); it may be added later.
- **Energy cost:** petrol €1.98/L, diesel €2.15/L, electricity €0.4042/kWh (V21).
- **Reported:** kWh per vehicle-km, the network total in kWh, € per scenario (V24), and CAV and HDV splits. HDV energy is labelled "estimated".
- Vehicles in the origin queue use no energy in SUMO; an idle-energy imputation row is reported (protocol §6.12, A23).

### 5.4 Generalised cost (headline, V29)
C = [Σ_v VoT_class · d_v + Σ_v € energy_v] / D, in € per vehicle-km.
- **VoT for cars:** €8.90 per person-hour (commuting, 2016 market prices) × 1.23 AM-peak occupancy. Uplifted to 2026 € with the TII real growth and the CSO price index. **[TBD: computed step by step in protocol Addendum B, frozen before seed 7,400,000 (A18)]**
- **VoT for trucks:** work VTT × 1.03 occupancy, uplifted the same way (V54).

### 5.5 Guards and constraints
- **Delay guard (V37):** Δ_D = median_s(Dl_A − Dl_B0) / max(median_s(Dl_B0), 0.05 · median_s(R_tot)) ≤ +0.02. The floor keeps the guard continuous where B0's delay is near or below 0 (ASSUMPTION). Burden of proof: the paired point estimate must lie within the margin; the Bonferroni interval is reported (protocol §6.8(e), A27 (c)).
- **Hard braking (constraint, V25, V36):**
  - an event is a continuous stretch with CAV deceleration below −3 m/s², at any speed (protocol A28 (α′)); the split at onset speed ≥ 10 m/s is reported;
  - metric = events per CAV-km, where CAV-km = the planned km of the cohort CAVs (fixed);
  - the constraint is the pooled rate ratio arm / B1, continuity-corrected: R̃ = ((k_A + 0.5) / E_A) / ((k_B1 + 0.5) / E_B1), with k the pooled event counts and E the pooled CAV-km over the seeds of the comparison, must be ≤ 1 + y with **y = 10 %** (protocol §6.8(f), §8.5, A14, V65);
  - a second guard (f′) against the same vehicles in B0 applies only if the protocol's P0-G3 ratio R₃ (B1 vs B0 at −3 m/s²) exceeds 1 + y (protocol §6.8);
  - HDV braking is not a constraint (V11): HDV hard-brake (< −3 m/s²) and severe rates per HDV-km are reported for every arm, with a FLAG when A/B1 > 1 + y (protocol A29 (a)).
- **Validity (V6, protocol A19):** collisions > 2, teleports > 0, or any other protocol §2.7 FAIL row make the run invalid. It counts as that arm's failure on that seed. An operations failure (a hung worker) is re-run once on the same seed and not scored.

### 5.6 Other reported metrics
- Stop-and-go cycles per vehicle-km on the mainline: a speed drop below 20 km/h followed by a rise above 50 km/h, per vehicle. Thresholds fixed by the protocol as labelled assumptions (A24, A35).
- TTT = ∫ over [900, 11,700) s of the number of vehicles that have reached their desired departure and not yet arrived, in the network **or in the origin queue** (veh·h); unfinished vehicles count to the cap (protocol §3.1).
- Served throughput: cohort vehicles arrived by the cap, and vehicles per hour at the exits over the window; reported with a CI wherever C is.
- Origin-queue vehicle-hours and the censored count, per arm (protocol §3.1, §6.8(g)).
- Per-zone travel time, to show congestion shifting.
- The CAV speed give-up: CAV mean speed vs B1.
- The share of CAV boundaries with the target at 50 or at 100 km/h (V47).

The definitions of §5.1–§5.6 are those of protocol §3.1, which close V18 (A35, V65).

## 6. V2X and V2V messages (resolves IF-C8, BD-9)
- **Zone unit Z_k**, every 2 s, from the probes CAVs report in that zone over the last 2 s:
  - per lane: CAV mean speed, CAV speed standard deviation, CAV count;
  - zone-wide: the same values.
  
  Empty lanes carry an explicit `n = 0` and fall back to a defined value (the last value, plus age).
- **Downstream unit Z3+ (protocol A30 (b), V65; V68 layout):** a probe-summary unit on [15,000, 16,000) m (V68; was [6,000, 7,000) under V64), just downstream of the 3 → 2 lane drop at Z3's downstream end (BN-LD, the expected first bottleneck). Same fields and fallback as a zone unit; no commands there. It serves as Z3's "next downstream zone" (Z1's is Z2, Z2's is Z3), with the same information for every zone-spec arm (R2, R3, L2).
- **V2V (V50):** a CAV hears every CAV within 300 m. This is the DSRC range in NHTSA's V2V fact sheet; standard broadcasts are 1–10 Hz. The observation keeps the 5 nearest CAVs ahead individually, plus the count and mean speed of all CAVs heard within 300 m ahead.
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
- V2V: the 5 nearest CAVs ahead within 300 m (relative position, speed, mask), plus the count and mean speed of all CAVs within 300 m ahead;
- V2X: own zone + the next downstream zone (for Z3: the downstream unit Z3+, §6), zone-wide mean speed and standard deviation + per-lane mean speeds.

The `local` and `zone` specs, including the normalisation constants and the Z3+ field, are frozen in protocol Addendum C before seed 7,400,060 (protocol §6.3, A30).

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
| A worker hangs | its CPU time grows by < 1 s over 10 min of wall time while the CPU guard has not paused it (protocol §2.7, A19) | `ops` | kill and re-run once on the same seed (an operations failure, not scored); a second hang is a FAIL of that arm, reported | ledger |
| Plant collapse | process CPU time above the per-arm-family cap (protocol §2.6 C8) | `ops` | kill; a FAIL of that arm on that seed, never excluded | ledger |

## 10. Records (resolves EX-C4, EX-C5, CX-F9)
- **Per run:** config hash, code commit + dirty flag (read at start **and** end), network spec hash, inflow file hash, observation-spec hash, trainer id (L arms), seed and role, validity, metric summary, and the determinism hash of the per-step trace (protocol T3).
- **Ledger:** one row per run, including failed and invalid ones (ported `ops/ledger.py`).
- Raw traces go under `/home/catalin/work/phd/` on ext4, never into the repo.
