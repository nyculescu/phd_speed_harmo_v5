# v5.B design v0: coordinated zone control of CAV speeds on CORR2X

*2026-10-13 · branch `claude/v5b-core` (from `claude/day-pattern-core` at `8eb0343`) · status: design draft, no data*

v5.B is a secondary, new version of the v5 project (author, 2026-10-13). It runs alongside the v6 traffic-signal work
(`phd_v6`, `claude/tsc-foundation`). The v5 close-out (`docs/handoff/v5_closeout_2026-10-13.md`) stays valid for
everything v5 recorded before this point.

## 1. Research question
Can three **communicating** zone controllers, which command the speeds of about 50 % CAVs and run two ramp meters,
achieve the following, compared with uncoordinated and conventional control?
- improve network-wide flow;
- cut stop-and-go traffic sharply;
- do so without hurting safety or shifting congestion between zones;
- stay effective as human drivers become heterogeneous and, later, adaptive.

The second question is whether learning-based control (DRL) gives a measurable advantage over conventional control.

The method rules of `CLAUDE.md` apply unchanged:
- protocol before data;
- tool checks first;
- tuned comparators;
- approved seeds;
- the conditional bar for any claim.

## 2. Author decisions (2026-10-13)
| # | Decision |
|---|---|
| B1 | v5 continues as **v5.B**, a secondary, new version |
| B2 | **Actuators.** CAVs: per-vehicle *accelerate / hold / brake* commands in steps of X km/h, given to every CAV inside a controlled zone (the X m before each merge point). Ramp meters on R1 and R2. Posted speed limits are for **HDVs only**: one regulated speed per lane, at most ±10 km/h apart; HDVs see it rounded to 5 km/h. |
| B3 | Adaptive driver model: **placeholder** for now (interface only, §6) |
| B4 | Zones exchange **planned speed profiles** as well as state, so each controller can learn the effects of its own actions downstream and upstream |
| B5 | Headline: door-to-door delay **including on-ramp queues**, co-headlined with a stop-and-go index; safety (TTC, hard braking) is a constraint |
| B5a | **TTT** (total travel time, veh·h) is reported alongside average door-to-door delay: TTT measures the aggregate time consumed by all vehicles, delay measures how much longer journeys take than their reference (author, 2026-10-13) |

### My readings of B2 and B4, to be confirmed by the author
- **(a)** "At most ±10 km/h gap": any two lanes of the same cross-section differ by ≤ 10 km/h. The alternative reading, adjacent lanes only, allows up to 20 km/h across 3 lanes.
- **(b)** The 5-km/h rounding applies to what HDVs are shown (the displayed limit). Per-lane regulated speeds may be computed finer.
- **(c)** CAV commands change a CAV's own target speed by −X, 0 or +X km/h per decision. The car-following model keeps it safe: SUMO's speedMode stays safe, so a command never overrides collision avoidance.
- **(d)** Per-lane regulated speeds are set by the zone controllers too, as part of their action. CAVs are not bound by them.
- **(e)** Planned speed profile = each zone's intended per-lane regulated speeds and CAV speed targets over the next H_plan s, published every decision. Messages arrive with no delay or loss in v0; delay and loss are robustness rows later.

## 3. Plant: CORR2X (`vsl_lab/netgen/corr2.py` SPEC_AUX, built 2026-10-13)
```
x (km): 0 ─────── 3.0 ── 3.25 ────── 4.5 ───── 5.0 ── 5.25 ── 5.5 ──────── 6.75 ────── 8.75
        [3 lanes ]⋈merge1[ 3 lanes ]Z[ 2 lanes ][ 2 ]⋈merge2[ 2 lanes  ][ 2 lanes ]
                  ▲  4 lanes   │      3→2                  ▲ 3 lanes  │
            R1 + meter   aux ─►X1   zipper           R2 + meter   aux ─►X2
zones:  Z1 ◄── X1z m ──┤3.0      Z2 ◄── X2z m ──┤4.5   Z3 ◄─ X3z m ─┤5.25
```
- **Merge points:**
  - Z1: weaving section merge1, at 3.0 km;
  - Z2: 3→2 zipper, at 4.5 km;
  - Z3: weaving section merge2, at 5.25 km.
- **Zone lengths:** zones must not overlap a neighbour's bottleneck. Z3 has only 750 m between the zipper and merge2, so X3z ≤ 750 m; X1z and X2z can be up to about 1.25 km. To decide: one common X, or one per zone.
- **No-control baseline:** your GUI screenshots show stop-and-go waves at all three points. This still has to be **measured** against the realism checks (§8 P0). v5's realism gate never achieved a capacity drop without simulation artefacts, so this is the first risk.
- Demand: default 4,500 / 600 / 900 veh/h overloads the 2-lane section (smoke run: 932 s mean time in system). The demand levels (regimes) are set in the protocol.

## 4. Control architecture
```
   ┌──────────────── message bus (every decision, Δt_d) ────────────────┐
   │ m_i = {state summary of zone i, planned profile of zone i (H_plan)} │
 ┌─▼──┐                         ┌─▼──┐                         ┌─▼──┐
 │ Z1 │ obs: own detectors,     │ Z2 │                         │ Z3 │
 │    │ CAV probes, m_2, m_3    │    │                         │    │
 └─┬──┘                         └─┬──┘                         └─┬──┘
   │ actions: per-CAV ±X/0 · per-lane regulated speed (HDV display, 5-km/h rounding) · meter rate (Z1→R1, Z3→R2)
 ┌─▼──────────────────────────────▼──────────────────────────────▼─┐
 │ actuation layer: CAV commands (bounded accel/jerk, safe mode),   │
 │ per-lane VSL with the ±10 km/h and 5-km/h rules, Meter (existing)│
 └──────────────────────────────────────────────────────────────────┘
```
- **One controller interface** for every arm:
  - `ZoneController.act(obs_i, msgs) -> (cav_cmds, lane_speeds, meter_rate, plan_i)`;
  - the bus and the actuation layer are shared;
  - so rule-based, MPC and DRL arms differ only in their policy.
- **Arms** (comparators, final list in the protocol):
  - **NC:** no control.
  - **Local conventional:**
    - ALINEA on each ramp;
    - a per-zone speed-limit rule (MTFC-style, one instance per zone);
    - a CAV rule (staircase / PI towards the zone's target).
    - Each zone runs alone, with no messages.
  - **Coordinated conventional:** the same rules plus the bus, e.g. an upstream cascade where Z_i lowers its targets when Z_{i+1} reports a queue.
  - **MPC:** METANET-based. The stepper needs a speed-limit input and a CORR2X model first, so this arm is optional.
  - **DRL:**
    - **Fair vanilla:** single-agent and centralised, same actuators and observations.
    - **Coordinated multi-agent:** one agent per zone, trained centrally and run decentrally, with the bus messages as observations.
- **Learning to read cause and effect (B4):**
  - each agent's observation includes its neighbours' planned profiles;
  - each agent's reward includes a share of network TTS, so effects that spill into other zones are paid for;
  - this is the mechanism against shifting congestion.

## 5. Vehicles
- **CAVs:** share p_cav = 0.5 by default; lower shares are a later sweep.
  - Model: a CAV vType (port `plants/mrg3.py:51-94` into CORR2 demand).
  - Control only through the command layer.
- **HDVs:** heterogeneous mix, ported from the BN4 "B3" population (`plants/bn4.py:58-110`):
  - EIDM timid / normal / assertive, compliant / non-compliant, ±15 % parameter jitter;
  - plus a small reckless share (legacy `traffic_environment/vehicle_fleet.py`; fix its docstring/code mismatch first);
  - trucks 10 %.
- **Compliance with the displayed per-lane limit:** speedFactor groups (existing mechanism).

## 6. Adaptive drivers: placeholder (B3)
Interface only, no behaviour in v0. It is built so that it can be added without touching the controllers:
```python
class DriverPopulation:
    def assign(self, vid, rng) -> str: ...          # strategy label per new HDV (v0: always "static")
    def on_step(self, t, sim) -> None: ...          # in-run tactics (v0: no-op)
    def on_episode_end(self, outcomes) -> None: ... # strategy shares update (v0: no-op)
    def state(self) -> dict: ...                    # persisted across episodes, logged
```
The candidate model for later is a small set of strategies, with shares updated by imitation dynamics across episodes, starting from a small non-compliant seed. A separate design is written when the author opens B3.

## 7. Metrics (B5)
- **Headline: average door-to-door delay**, including on-ramp and insertion queues. It answers: *how much longer is a journey than its reference?*
  - Per vehicle: door-to-door time minus the free-flow (reference) time of its own route.
  - Averaged over the cohort; `jobs/corr_run.py` computes the d2d times.
- **Reported alongside: total travel time (TTT)** (author, 2026-10-13). It answers: *how much time does all traffic consume in aggregate?*
  - Definition: the sum over all vehicles of time spent in the system, including origin and insertion queues, over a fixed window [t0, t1], in veh·h.
  - Vehicles still queued or unfinished at t1 count up to t1, so an arm cannot lower TTT by serving fewer vehicles.
  - TTT is reported with served throughput next to it, because it scales with how many vehicles the window covers.
  - The two can disagree: TTT weighs where most vehicle-hours go, while average delay weighs each journey equally. Both are reported per arm and per regime.
- **Co-headline: stop-and-go index.** Pre-registered candidates:
  - share of vehicle-time inside stop-and-go oscillations;
  - stops per vehicle-km;
  - speed standard deviation over space and time.
  
  The protocol picks one and reports the others.
- **Reported alongside:**
  - throughput;
  - **per-zone TTS against NC**, to show congestion shifting;
  - ramp queues and spillback.
- **Safety constraints:**
  - TTC < 1.5 s events from SUMO's SSM device (port `core/eval_metrics.py`);
  - hard braking (< −4 m/s²), emergency braking, collisions = 0.
  - Tolerances are fixed in the protocol.
- **Missing today, to build:** stop-and-go index, SSM/TTC on CORR2X, per-zone TTS balance.

## 8. Phases (each gated, criteria written before data)
| Phase | Content | Gate |
|---|---|---|
| P0 plant | CORR2X + CAV/HDV mix; realism checks (capacity drop without artefacts, wave speed, discharge) | breaks down realistically at the chosen demand |
| P1 tool checks | T0: CAV commands and lane speeds move flow/density; T1: three interacting zones (control at one zone changes another); T2: per-regime best differs; T3: determinism | as in the CLAUDE.md method |
| P2 conventional | local and coordinated arms, tuned on tuning seeds | — |
| P3 room | informed references (oracle schedules) vs best tuned arm | report-only headroom |
| P4 DRL | fair vanilla DRL, coordinated multi-agent DRL | conditional bar, pre-registered regimes |
| P5 (later) | adaptive drivers (B3), lower CAV shares | robustness rows |

## 9. Integration into the code (new or changed modules)
| Module | Status |
|---|---|
| `netgen/corr2.py` SPEC_AUX | exists (CORR2X); add the zone definitions |
| `plants/corr2.py` | extend: `cav_share` in demand, per-lane speed-limit setter with the B2 rules, B3 HDV mix |
| `controllers/zone.py` (new) | `ZoneController` interface, `MessageBus`, rule-based local and coordinated arms |
| `actuators/cav_cmd.py` (new) | per-CAV ±X / 0 commands with accel/jerk bounds (from `cav_staircase` / `pi_saturation`) |
| `drivers/population.py` (new) | B3 placeholder (§6) |
| `envs/corr2x_env.py` (new) | gymnasium (centralised) + PettingZoo parallel API (one agent per zone) |
| `train/` | extend `train_sb3` for the CORR2X env; add a multi-agent trainer (choice of library in the protocol) |
| `eval/` | stop-and-go index, SSM/TTC, per-zone TTS |

## 10. Open parameters (author)
- ~~X km/h, the CAV command step~~ **5 km/h** (author, 2026-10-13).
- Zone lengths: one per zone (author); Z3 = 1000 m before merge2 (author), which reaches past the 3→2 zipper unless merge2 moves downstream (pending decision).
- Δt_d, the decision interval; H_plan, the plan horizon.
- Readings (a)–(e) above.
- Demand regimes; CAV-share sweep.
- Seed block for v5.B, to be approved before any protocol run.
