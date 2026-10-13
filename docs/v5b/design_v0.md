# v5.B design v0: coordinated zone control of CAV speeds on CORR2X

*2026-10-13 · branch `claude/v5b-core` (from `claude/day-pattern-core` at `8eb0343`) · status: design draft, no data*

v5.B is a new version of the v5 project (author, 2026-10-13) and, by a later author decision the same day (B15), the **primary** PhD line; v6 is secondary. It runs alongside the v6 traffic-signal work
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
| B2 | **Actuators.** CAVs: per-vehicle *accelerate / hold / brake* commands in steps of 5 km/h (§10), given to every CAV inside a controlled zone (the X m before each merge point). Ramp meters on R1 and R2. Posted speed limits are for **HDVs only**: one regulated speed per lane, at most ±10 km/h apart; HDVs see it rounded to 5 km/h. |
| B3 | Adaptive driver model: **placeholder** for now (interface only, §6) |
| B4 | Zones exchange **planned speed profiles** as well as state, so each controller can learn the effects of its own actions downstream and upstream |
| B5 | Headline: door-to-door delay **including on-ramp queues**, co-headlined with a stop-and-go index; safety (TTC, hard braking) is a constraint |
| B5a | **TTT** (total travel time, veh·h) is reported alongside average door-to-door delay: TTT measures the aggregate time consumed by all vehicles, delay measures how much longer journeys take than their reference (author, 2026-10-13) |
| B6 | ~~superseded by B12 (the M)~~ **Demand:** a synthetic M fitted to the real MnDOT weekday shape (US-169 SB, station S460 at T.H.62, median of 156 Tue-Thu weekdays 2023). **Every day differs:** noise on peak timing, height and width plus stochastic arrivals. The noise level is a parameter, raised later to stress the system. |
| B7 | ~~Day window 06:00-19:00 (one full M): superseded by B12 (06:00-10:00)~~. The pause rule stays (its "full congestion" part is open, Q5). In free-flow or fully congested stretches there is nothing to optimise. **Controllers must detect this and pause learning, inference and activity**: one gate rule shared by every arm. |
| B8 | **Zones of 1000 m each:** Z1 2.0-3.0 km, Z2 3.5-4.5 km, Z3 4.75-5.75 km. merge2 / R2 / X2 moved to 5.75 km (CORR2X v3). |
| B9 | **Intervals:** CAV commands every 2 s (±5 km/h); HDV lane limits and ramp meters every 60 s; plan horizon 120 s. |
| B10 | **Seed block approved:** 7,400,000-009 throw-away calibration; 010-099 plant and tool checks; 100-299 tuning; 300-499 validation; 500-699 test; 700-999 reserved confirmatory; 7,410,000-7,419,999 DRL training. |
| B11 | **DRL trains on the peak windows only** (free flow needs no optimisation) |
| B12 | **Demand revised (supersedes the M in B6 and the window in B7):** one direction carries one commuter peak. The day is a single **morning triangle-ish peak**: the morning part of the fitted MnDOT shape, a fast rise to about 07:50 and a slower fall, with the same per-day noise. **Window 06:00-10:00.** Training and evaluation share this window; the B7 pause rule stays. |
| B13 | **Higher on-ramp demand:** peaks R1 1,200 veh/h, R2 1,000 veh/h, mainline about 4,000 veh/h. Ramp storage is about 50 vehicles per ramp, so metering faces a real trade-off. |
| B14 | **Safety counted at speed:** TTC < 1.5 s and hard braking above about 10 m/s. Raw SUMO "emergency braking" warnings are mostly zipper-queue creeping. A 2026-10-13 replay of the M day: all 730 vehicles braked in the last 125 m before the zipper, at about 0 m/s afterwards, 2.5 m gap. |
| B15 | **Priority:** v5.B is the PRIMARY PhD line and v6 (traffic signals) is secondary. v5.B work and runs come first, including CPU. |

### My readings of B2 and B4, to be confirmed by the author
- **(a)** "At most ±10 km/h gap": any two lanes of the same cross-section differ by ≤ 10 km/h. The alternative reading, adjacent lanes only, allows up to 20 km/h across 3 lanes.
- **(b)** The 5-km/h rounding applies to what HDVs are shown (the displayed limit). Per-lane regulated speeds may be computed finer.
- **(c)** CAV commands change a CAV's own target speed by −X, 0 or +X km/h per decision. The car-following model keeps it safe: SUMO's speedMode stays safe, so a command never overrides collision avoidance.
- **(d)** Per-lane regulated speeds are set by the zone controllers too, as part of their action. CAVs are not bound by them.
- **(e)** Planned speed profile = each zone's intended per-lane regulated speeds and CAV speed targets over the next H_plan s, published every decision. Messages arrive with no delay or loss in v0; delay and loss are robustness rows later.

## 3. Plant: CORR2X v3 (`vsl_lab/netgen/corr2.py` SPEC_AUX)
```
x (km): 0 ──── 2.0 ════ 3.0 ─ 3.25 ── 3.5 ════ 4.5 ── 4.75 ════ 5.75 ─ 6.0 ──────── 7.25 ────── 9.25
        [ 3 lanes  ]⋈merge1[ 3 lanes      ]Z[ 2 lanes          ]⋈merge2[ 2 lanes ][ 2 lanes ]
             [  Z1   ]  4 lanes    [  Z2   ] 3→2     [  Z3   ]   3 lanes
                      ▲  │aux→X1            zipper            ▲  │aux→X2
                     R1 + meter                              R2 + meter
```
- **Merge points and zones (B8, 1000 m each, non-overlapping):**
  - Z1 is 2.0-3.0 km, before the weaving section merge1 at 3.0 km;
  - Z2 is 3.5-4.5 km, before the 3→2 zipper at 4.5 km;
  - Z3 is 4.75-5.75 km, before the weaving section merge2 at 5.75 km.
  
  merge2 / R2 / X2 were moved from 5.25 km to 5.75 km so that Z3 starts 250 m after the zipper.
- **No-control baseline:** the GUI runs show stop-and-go waves at all three points. This still has to be **measured** against the realism checks (§8 P0). v5's realism gate never achieved a capacity drop without simulation artefacts, so this is the first risk.
- **Demand (B12, B13):** one morning peak, 06:00-10:00, peaks of about 4,000 veh/h on the mainline (upstream of merge1), 1,200 on R1 and 1,000 on R2.
  - Desk estimate at the peak: about 4,800 veh/h reach the 2-lane zipper (≈ 4,000 + 1,200 − 400 to X1), against a capacity of roughly 3,800-4,000. So it is over capacity only around the peak. To be checked on paper before any run.
  - Exit shares: X1 10 % and X2 10 % of the mainline, X2 10 % of R1; trucks 10 %.

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

## 10. Parameters
**Decided (author, 2026-10-13):**
- CAV command step 5 km/h.
- Zones 1000 m each (B8).
- Intervals Δt: CAV commands 2 s; HDV lane limits and ramp meters 60 s.
- Plan horizon H_plan 120 s (B9).
- Demand: one morning peak 06:00-10:00 with per-day noise; peaks: mainline about 4,000, R1 1,200, R2 1,000 veh/h (B12, B13).
- DRL trains on the peak (B11). Seed block 7,400,000 (B10). Safety counted at speed (B14). v5.B primary (B15).

**Open (author), as numbered in the v5.B session's report of 2026-10-13:**
- Q1: readings (a)-(e) in §2.
- Q2: confirm exit shares (X1 / X2 10 % each) and trucks 10 %.
- Q3: is the ≥ 10 % bar on delay only, with stop-and-go as co-headline (recommended)?
- Q4: do controllers output lane/segment targets, with a shared per-CAV ±5 / 0 rule (recommended)?
- Q5: pause in free flow only (recommended), or also in full congestion?
- Q6: is no control = CAVs on plain ACC, no limits, no meters?
- Q7: MPC arm: build it, or drop it with disclosure (optional under D5.8)?
- Q9: regime candidates: demand level, CAV share (50 / 25 / 10 %), driver mix, noise?
- Implementation: reshape `plants/m_day.py` from the M to the B12 morning peak.
