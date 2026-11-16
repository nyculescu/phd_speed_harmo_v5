# System context (v0.2)

*2026-10-13. Status: draft for author review; v0.2 (same day) applies V60, V61, V63 and the V64 road layout. It builds on the Notion draft "v5.B.1 system architecture" and resolves the blockers in `review_v0.md`. Decisions are cited as V#. Items marked **[PROPOSAL]** are mine and need the author; **[TBD-protocol]** values are fixed in the protocol before any data. The contracts themselves are in `interfaces.md`.*

## 1. Purpose
Research question:
> Can CAVs, commanded per vehicle and coordinated through V2V/V2X, cut the generalised cost (time and energy) of a congested freeway morning peak, without costing commuters noticeable time? The comparison is against human traffic, against the same CAVs on plain ACC, and against tuned published rule-based CAV controllers. A second question: is learning (shared-policy PPO) better than those rules in identifiable regimes?

The system has to:
- make every arm comparable: the same plant, the same inflow realisation and the same metric code;
- keep learning-specific machinery out of the plant and out of the metrics.

## 2. Scope and boundary
```
                 ┌──────────────────────── v5.B.1 system ─────────────────────────┐
 inflow family ─►│ PLANT (SUMO 1.27.1, libsumo, 0.2 s)                             │
 seeds, config   │   F3Z network · HDVs · CAVs · trucks                            │
                 │        │ CAV own sensors          ▲ CAV commands (±5 km/h / 2 s) │
                 │        ▼ + CAV probe reports      │                             │
                 │ V2X LAYER: zone units Z1..Z3 ──► ARM (one per run):             │
                 │   (CAV-probe summaries, V2V)        HDV-only · ACC-only ·       │
                 │                                     rule-based · PPO · VSL arms │
                 │ EXECUTION LAYER (slowDown 2 s, hold, release)  ◄────────────────┘
                 │ METRICS (from the simulator's ground truth, never from the arm) │
                 └─────────────────────────────────────────────────────────────────┘
```
**In scope:**
- a 3-zone freeway in SUMO;
- a near-future fleet (V42) with about 28 % CAVs;
- per-CAV speed commands as the **only** actuator of our system (V3, V15);
- V2V and V2X information (V27), with no loop detectors;
- metrics computed from simulator ground truth.

**Out of scope for now:**
- ramp meters (V15; they may return later);
- VSL as *our* actuator (it appears only as a comparator arm, V32);
- adaptive drivers (B3 placeholder);
- communication delay and loss (later robustness rows);
- weather and incidents.

**The honesty line.** Arms observe only what a deployed system could observe: CAV onboard sensors, plus V2V and V2X summaries built from CAV probes. Metrics and the *training* reward may use simulator ground truth for all vehicles, because they are evaluation and training instruments, not deployed inputs. HDV energy is a model **estimate**, by design (V23): in reality it could not be reported.

## 3. Plant
| Element | Content | Source |
|---|---|---|
| Network F3Z (V2, V64, V68) | Evolved from CORR2X v3, re-arranged by V64 and spaced by V68:<br>• 3 lanes 0–3.0 km (no zone, V71);<br>• merge 1 at 3.0–3.25 km (on-ramp OR1 joins on an auxiliary lane, which leaves as off-ramp X1);<br>• 3 lanes 3.25–9.0 km (Z1 8.0–9.0);<br>• merge 2 at 9.0–9.25 km (OR2 joins on an auxiliary lane, which leaves as X2);<br>• 3 lanes 9.25–15.0 km (Z2 11.0–12.0, Z3 14.0–15.0);<br>• **3→2 lane drop at 15.0 km** (the expected first bottleneck, at Z3's downstream end);<br>• 2 lanes 15.0–18.25 km.<br>Zones Z1 8.0–9.0, Z2 11.0–12.0, Z3 14.0–15.0 km, on the drop's approach (V71, protocol Addendum Z1; open to change under V56). Network maximum 100 km/h (V30) | port `netgen/corr2.py` SPEC_AUX, trimmed and re-arranged (`port_map_v0.md`, V64); edge table and desk estimate in protocol §2.1 |
| Step | 0.2 s. ACC/CACC give emergency-braking artefacts at 0.5 s | archive STATUS #14 |
| HDV cars | EIDM (archive driver H5). Desired speed = 100 km/h × a speed factor drawn from V43: 55 % at 100, 44.7 % at 100–120, 0.3 % at 120–150 km/h | port the `plants/mrg3.py` vType layer |
| Heavy vehicles | 7.5 % of vehicles (V40), 40 t articulated, vType maxSpeed 25 m/s (90 km/h); EIDM truck parameters | archive `_IDM_TRK` |
| CAVs | About 28 % of cars: 50 % of the electrified + hybrid cars (V42). Base car-following: ACC selected from the pre-registered ladder A0–A3 (V36, V60; protocol §2.6 C4): SUMO ACC variants A0–A2, or A3, an IDM-based ACC without driver noise (Kesting et al. 2008 [VERIFY]); `speedDev=0` | port `cav_vtype_xml`; selection in protocol calibration C4 |
| Powertrains | 2025 new-sales mix (V42):<br>• petrol and diesel: `HBEFA4/PC_*_Euro-6d`;<br>• BEV: `HBEFA4/PC_BEV`;<br>• HEV+PHEV: `HBEFA4/PC_PHEV_petrol_Euro-6d_(P)` / `_(El)`, one mode per trip, 50 % electric (V35, V38, V46);<br>• trucks: road-load + Willans, in our own code (V34) | `truck_energy_check_v0.md` |
| Inflow | A synthetic morning-peak family with Poisson arrivals and off-ramp shares at X1/X2. The level is swept, then the band is fixed (V31, V45) | `interfaces.md` §4 |

## 4. Arms (what is compared)
| Id | Arm | Role |
|---|---|---|
| B0 | **All-HDV fleet**: no CAVs; the same vehicles driven by humans | D5.8 baseline: the candidate must reach ≥ 10 % vs B0 (V44) |
| B1 | **The same CAVs on plain ACC, no commands** | The candidate must also beat B1 **by at least 5 %** in generalised cost (V61), so the gain comes from control and not from automation (V44) |
| R1 | PI with saturation (Stern et al. 2018), re-parametrised for 100 km/h, tuned | rule comparator (V19) |
| R2 | An explicit MicroAccel-family controller (Hayat et al.; CIRCLES I-24), local mode + V2X planner mode, tuned | rule comparator |
| R3 | CAV speed harmonisation upstream of each merge (FHWA / Ghiasi family), adapted from loop detectors to V2X probes (disclosed) | rule comparator |
| R4 | A constant CAV speed cap, one tuned parameter | trivial comparator |
| L1 | **Vanilla PPO:** independent agents, one shared policy, onboard + V2V observations only, no zone messages | fair vanilla DRL (`CLAUDE.md`) |
| L2 | **Candidate PPO:** shared policy + V2X zone summaries, optional centralised critic | candidate |
| I1 | VSL, M50 eMOS-like, low compliance | research reference (V32, V39) |
| I2 | VSL + average-speed cameras, high compliance | research reference |
| O | **Informed oracle:** the best rule (R1–R4) with parameters looked up per inflow level, tuned on tuning seeds | band rule (V45) and headroom diagnostic |

- R1–R4 use the **same** execution layer (2-s commands) as L1/L2. Their native-rate versions are a sensitivity row only.
- The best of R1–R4 on validation is "the best tuned proven controller" in D5.8.
- I1, I2 and every row outside the pass bar are always reported.
- MPC is dropped, and the drop is disclosed (allowed under D5.8).
- The non-learning adaptive scheduler is dropped from P2 and the drop is disclosed; the headroom figure is relabelled "G, i.e. H without the adaptive scheduler" (V63).

## 5. Modules (package `v5b`)
| Module | Owns | Must not |
|---|---|---|
| `plant/` | the F3Z network build, vTypes, inflow generation, the SUMO lifecycle, health checks, the per-step ground-truth trace | know about arms or rewards |
| `v2x/` | zone units (CAV-probe summaries per zone and lane), V2V neighbour lists, the message schema | read HDV state |
| `exec/` | CAV command execution (V26/V36): bounds, the `slowDown` ramp, hold, release on zone exit | decide anything |
| `arms/` | B1, R1–R4 and I1–I2 policies behind one `Arm` contract | touch SUMO directly |
| `rl/` | the PettingZoo `ParallelEnv` (CAV agents), shared-parameter PPO, the `Policy` contract (ADR-001) | contain plant or metric logic |
| `metrics/` | delay, energy (HBEFA4 read-out + truck model), generalised cost, braking, stop-and-go, TTT, throughput, validity | read anything an arm produced except the command log |
| `ops/` | CPU guard, scheduler, ledger, run directories (ported, trimmed) | — |
| `exp/` | configs, seeds, the episode loop and its multirate schedule, sweeps, tuning, statistics | — |

**Dependency direction:** `exp → {arms, rl} → {v2x, exec} → plant`, and `metrics → plant trace`. There are no cycles. Only `plant` imports libsumo.

## 6. One episode
```
exp: build scenario (seed, inflow level, fleet) ─► plant.reset ─► loop every 0.2 s:
   plant.step  → ground-truth trace row (all vehicles)                  [metrics input]
   every 2 s (decision boundary, one consistent snapshot):
      v2x.update(CAV probes of the last 2 s) → zone summaries
      arm.act(observations of CAVs in zones)  → target per CAV
      exec.apply(targets)                     → slowDown / hold / release
      log commands
 end: drain until all cohort vehicles arrive or the cap → metrics.finalise → validity → ledger
```
- Every arm computes from the same snapshot, before any command is applied.
- One module owns time: the episode loop in `exp`.

## 7. Build order (resolves review BD-4 / CX-F1)
1. **Contracts:** this file and `interfaces.md`, approved by the author.
2. **Protocol P0/P1:** plant realism and the T0–T3 tool checks, with criteria fixed before data. Extra High effort, ultracode on for its review.
3. Port and trim the plant, `ops` and metrics (`port_map_v0.md`), with tests.
4. Run T0–T3 on the check seeds 7,400,010–099.
5. **Inflow band sweep** with B0, B1, R1–R4 and O (V31, V45). This is also the early KILL: if no level reaches g = 10 %, there is no claim on this plant.
6. Build the RL environment and run the trainer ladder (ADR-001 §4).
7. Train and validate L1/L2 inside the band, choosing checkpoints on validation only.
8. Confirmatory run on the reserved seeds 7,400,700–999.

## 8. What would invalidate this design (falsifiers)
- **No realistic breakdown:** F3Z shows no artefact-free capacity drop at 100 km/h with this fleet, so P0 fails (after at most 2 variants and 6 setting changes, V59). On paper the first bottleneck is the lane drop at the end of Z3 (V64); if the measured one lies elsewhere, the zones may not sit where the jam forms (zone moves: V56, protocol A34).
- **No room:** no inflow level where a non-learning arm or the oracle reaches g = 10 % vs B0 (early KILL).
- **Commands are not carried out:** the `slowDown`/hold execution does not do what V26 assumes, so T0 fails.
