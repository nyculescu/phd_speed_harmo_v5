# Round 4: harmonisation (stop-and-go damping) on the lane-drop plant, pre-registration

*Committed 2026-10-02, before any Round 4 run. Branch `claude/vsl-lab-core`.*

**Author decisions (2026-10-02):**
- pivot Track 2 to harmonisation (`t2_realism_ld3.md`: SUMO shows realistic waves but no artefact-free capacity drop);
- primary metric = **door-to-door delay and stops per vehicle, co-primary**;
- throughput and emergency braking are side constraints.

## Framing

ARC-IT TM21 "Speed Harmonization" (sp68) aims at "reducing unnecessary stops and starts, and maintaining consistent speeds". TM20 "Variable Speed Limits" (sp138) is the posted-limit counterpart.

ARC-IT is used as a source of ideas and citations, not as a specification (author, 2026-10-02).

## Plant

**LD3** (3 → 2 lane drop, `--geom lanedrop`) with **H5** drivers (EIDM, every EIDM parameter at its SUMO default) and a 0.2 s step.
- **Gate verdict for H5:** FAIL, on R-a only. Waves −16.4 km/h, origin at the bottleneck 100 %, no teleports, no collisions, deterministic.
- **The capacity-drop requirement is dropped for this round.** This is a disclosed deviation that follows from the author's pivot.

**Operating cells:** 3,900 / 0 and 4,500 / 0.
- 3,900 is the lowest LD3 calibration cell with a breakdown share ≥ 0.9 and 0 teleports / 0 FAIL.
- 4,500 is a heavier-congestion cell. In the throw-away smoke run it gave 3.7 stops per vehicle.

**Seeds:** 7,160,200–7,160,229 (30 seeds), from the "Track 2 plant development" block approved on 2026-10-02.

## Measures

**Co-primary:**
- **delay:** mean door-to-door time per vehicle, including the origin queue;
- **stops:** stops per vehicle, i.e. SUMO tripinfo `waitingCount`, the number of times a vehicle's speed falls to ≤ 0.1 m/s.

**Side constraints:**
- exit throughput over the control window;
- emergency-braking events per 1,000 veh-km (CAV / human split).

**Reported:**
- share of vehicles that stop at least once;
- stopped time per vehicle;
- time loss.

**Statistics:** the median of paired differences, with 95 % percentile bootstrap CIs.

## Runs (T-H stage)

30 seeds × 2 cells × 11 controllers = 660 runs:

| Group | Controllers | Reference |
|---|---|---|
| Humans only | `nc` | (itself) |
| Posted VSL (TM20, arm A) | `const:b`, b ∈ {0.5, 0.6, 0.7, 0.8} (application area up1 + up0a, Carlson safety staircase upstream) | NC-human |
| Posted VSL (TM20, arm A) | `mtfc:ρ̂:38:9:0.0015`, ρ̂ ∈ {20, 25, 32} (Carlson MTFC; drop-zone density) | NC-human |
| 25 % CACC CAVs | `nc`, i.e. NC-p (arm C machinery, no command) | — |
| 25 % CACC CAVs | arm C `cavconst:0.6` | NC-p |
| 25 % CACC CAVs | arm P `cavpi` (every CAV runs PI-with-saturation onboard, Stern et al. 2018) | NC-p |

**On X = 1 s for arm C:** this is **provisional**. Round 3's T-X never ran, because no plant passed before this pivot. It is disclosed here.

## Criteria (fixed now)

| Check | Rule |
|---|---|
| **T-H0: posted VSL has authority over stops** | `const:0.6` vs NC-human: median paired relative change in stops per vehicle ≤ −10 %, with the CI excluding 0, in at least one cell. **If it FAILS: harmonisation by posted VSL is KILLED on LD3**, and nothing else is run for arm A. |
| **Harmonises for free** (per controller, per cell) | stops ≤ −10 % (CI excluding 0) **and** median delay change ≤ +2 % against its own NC (NC-human for arm A, NC-p for CAV arms) |
| **Frontier** (reported) | every controller's (Δdelay %, Δstops %) with CIs: the classical trade-off frontier that DRL must beat |
| **SPECIALIST applicability** | **Why:** SPECIALIST (Hegyi et al. 2008) assumes isolated moving jams with free flow downstream and upstream (P1 p.830); its front equations are not printed (P1 p.830; P2 p.1773). **Test:** count, in the NC-human runs, minutes in which a detector shows a jam (1-min q ≤ 1,500 veh/h/lane and v ≤ 50 km/h, P1 thresholds) while the nearest detectors downstream and upstream both show v > 50 km/h. **If the median count per run is 0,** SPECIALIST is reported as **not applicable** to this plant (by its own assumptions) and excluded. Otherwise it is implemented from the stated shock-wave rule, before any DRL comparison, in an addendum |
| **CAV-model note** (reported) | NC-p vs NC-human delay. In the throw-away smoke run, SUMO's default CACC at 25 % raised delay by 78 %. ACC string instability is a known issue on SUMO's ACC page; how much of this is a model artefact is not tested here |

## After T-H (pre-registered now, details in an addendum before any DRL run)

**If T-H0 PASSES:**
- a DRL pilot on posted VSL (arm A): PPO, decisions every 30 s, actions b ∈ {0.5, …, 1.0} per VSL segment;
- reward = −(Δ vehicles in system · Δt) − w · (new stops). The weight w is fixed in the addendum before the pilot, from the T-H frontier, not tuned on DRL results;
- screening: the final policy must lie **outside** the classical frontier, i.e. strictly better on one co-primary measure and not worse than +2 % on the other, against the best classical controller on that axis, on validation seeds.
- the TM21 arms follow only if a CAV arm shows authority in T-H.

**Honest prior:**
- constant VSL already cuts stops but costs delay (smoke run);
- SPECIALIST resolved only about 6 % of 407 real waves in its field evaluation (P2 p.1775);
- a Pareto improvement by DRL is plausible but far from certain.
