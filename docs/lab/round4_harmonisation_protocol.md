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

---

## Addendum A (2026-10-02, after T-H, before any tuning or DRL run)

**T-H result** (`round4_th.md`):
- T-H0 PASSES.
- No classical controller harmonises for free:
  - at 3,900: `const:0.8` gives −63 % stops and +2.1 % delay;
  - at 4,500: MTFC (ρ̂ 32) gives −19 % stops and +9.5 % delay, while `const:0.8` gives −13 % stops and −7.6 % delay (both not significant).
- SPECIALIST is applicable: 3 and 10.5 isolated-jam minutes per run (median).
- SUMO's default CACC at 25 % worsens delay by 46–93 % vs humans, and the CAV arms show no authority. **The TM21 arms are parked** and reported as is.

### One scalar score: J = delay + w · stops, with w = 40 s per stop

- **Why one score:** it selects the tuned classical baseline. The co-primary measures are still reported separately.
- **Where w comes from:** the T-H frontier slopes (seconds of delay traded per stop avoided):
  - `const:0.8` at 3,900: about 33 s per stop;
  - MTFC ρ̂ 32 at 4,500: about 48 s per stop;
  - w = 40 is the rounded midpoint.
- **w is fixed now and is not tuned on DRL results.**

### R2-H: tuning the classical controllers

**Setup:**
- seeds 7,160,300–7,160,319 (20, from the approved block);
- cells 3,900 / 0 and 4,500 / 0;
- LD3, H5, 0.2 s, with tripinfo stops.

**Controllers** (20 in total; 800 runs):

| Family | Settings |
|---|---|
| no control | `nc` |
| constant posted VSL | `const:b`, b ∈ {0.75, 0.8, 0.85, 0.9, 0.95} |
| adaptive rule | `vslad:θ:b`, θ ∈ {50, 70, 90} km/h, b ∈ {0.7, 0.8, 0.9} |
| Carlson MTFC | `mtfc:ρ̂:38:9:0.0015`, ρ̂ ∈ {28, 32, 36, 40} |
| SPECIALIST | `spec`, P1 parameters, front equations derived from the stated rule (see the implementation notes when it is committed) |

The adaptive rule is the required non-learning adaptive scheduler: every 60 s, if the 1-min speed at the drop is < θ, it posts b on up1 and up0a (with the Carlson staircase upstream); it releases above θ + 10 km/h after at least 120 s on.

**Selection:**
- **tuned classical** = the controller with the lowest mean over the two cells of median J;
- **per-family best** = the same rule within each family;
- frozen in `docs/lab/round4_baselines_frozen.json`.

### DRL pilot P-H (exploratory)

**Environment:** MRG3Env in `direct` mode on LD3 / H5 / 0.2 s.
- **Actions:** b ∈ {0.2, …, 1.0}, with |Δb| ≤ 0.2 per 60-s decision, on the same actuator and staircase as `const:b`. So every constant controller lies inside the policy space.
- **Reward:** −(veh-s in system + 40 · new stops) / 30,000 per decision.
- **Observations:** S-HIST, 4 snapshots.

**Training:**
- main peak ~ U(3,600, 4,800), ramp 0; p_nc drawn from {0.1, 0.3, 0.5} (hidden);
- PPO, 16 envs × 120 steps, batch 1,920, 500 updates, γ 0.99, learning rate 3e-4 with decay, log-std n/a (discrete);
- training seed pool 7,220,000+ (approved T2 DRL range).

**Validation:**
- main peak ∈ {3,900, 4,500} × seeds 7,120,300–7,120,302 (T2 validation range);
- metric `score_h` = control-window veh-s + 40 · stops, lower is better;
- validation every 25 updates; the checkpoint is chosen on validation only.

**Screening** (on the validation specs, final policy; the best checkpoint is reported):
- **C-H1:** J(DRL) ≤ 0.95 × J(tuned classical), means over the specs;
- **C-H2:** DRL is no worse than the tuned classical by more than +2 % on delay **and** on stops;
- **C-H3:** 0 health FAIL.

**Passers** go to the F class (3 seeds × 1,000 updates) and to R5-H on the shared T2 test seeds 7,120,500–7,120,529 against the tuned classical and the per-family bests.

---

## Addendum B (2026-10-02, before any SPECIALIST tuning run): SPECIALIST implementation and variants

**Implementation:** `vsl_lab/controllers/specialist.py`, with 6 unit tests in `tests/test_specialist.py`. It follows Hegyi et al. 2008 (P1, ITSC, pp. 827–832) and 2009 (P2, ECC, pp. 1770–1774), read in full.

**Fronts.** The papers do not print the front equations (P1 p.830; P2 p.1773). They are derived from the stated rule w_ab = (q_a − q_b)/(ρ_a − ρ_b), and documented in the module docstring:
- the length of area 3 makes it vanish exactly where the jam is resolved ("exactly resolves", P1 p.828);
- the limits cover areas 2–4 (P1 p.830).

**Interpretations, all disclosed:**
- q2 = the mean flow of the jam detectors.
- Tail margin x̂_t = x_t − |m_t|. P1 p.831 prints m_t = −1.5 km, and its sign contradicts "on the safe side" on the same page.
- Missing detectors (v < 0) are dropped.
- With several jam clusters, the first solvable one from downstream is activated.
- "Fits the signs" means areas 3 and 4 lie within the VSL segments.

**Plant mapping:**
- detectors = the e1 loops at the edge ends (up3, up2, up1, up0a, up0b, down); `down` is rescaled from 2 to 3 lanes;
- VSL segments = the five approach edges (0–4 km);
- decisions every 60 s on 1-min data; the moving area is re-posted every 10 s.

**Feasibility on this plant.** With P1's tail margin (1.5 km), the required limit stretch (about 7.3 × the jam length) mostly extends beyond the 4 km of signs. In the throw-away smoke run at 4,500, faithful SPECIALIST activated once (1 solvable event in 37), and with a 0.25 km margin it activated 4 times in 33.

**Variants in R2-H** (no further tuning):
- `spec`: P1 parameters;
- `spec:0.25`: P1 with a 0.25 km tail margin. **This departs from P1**, disclosed, so that SPECIALIST can act within the 4 km of signs.

P1's q5 (6,100 veh/h for 3 lanes) exceeds the capacity downstream of the 3 → 2 drop. P1 p.831 says to lower q5 when there is a bottleneck downstream. **It is kept at P1's value**, so as not to tune; a disclosed limitation.

Both variants are reported. Their family best enters the screening references.

**R2-H result and a correction (2026-10-02 13:15, before any screening).**
- **Tuned classical** = `const:0.75` (90 km/h on up1 + up0a), with J score 287.3 against 380.5 for NC. At 4,500 it cuts delay by 25 % and stops by 55 % against NC (tuning seeds). See `round4_r2.md`.
- **Correction:** Addendum A said every constant controller lies inside the P-H policy space. **That is false for b = 0.75, 0.85 and 0.95.** The pilot's grid is {0.2, …, 1.0} in steps of 0.1, so it can only approximate 0.75 by alternating 0.7 and 0.8. The pilot was already training when this was noticed, so it is disclosed here and not changed. A follow-up pilot, if any, will use a grid that contains the tuned classical value.

## Addendum C (2026-10-02 13:25): P-H stopped, replaced by P-H2 before any screening data

**Why P-H was stopped:**
- After 10 of 500 updates it ran at about 260 s per update, which projects to more than 36 h.
- Two causes: CPU oversubscription during R2-H, and per-step (0.2 s) stop counting across all vehicles.
- Only its update-0 validation exists; no screening was run. It is logged as abandoned.

**P-H2 = P-H with exactly two changes, both made before any DRL screening result:**
1. **Action grid** `direct_fine`: b ∈ {0.5, 0.55, …, 1.0} (11 levels), with the same |Δb| ≤ 0.2 per 60-s decision and the same staircase and acceleration area. **The tuned classical `const:0.75` and every constant controller tuned in R2-H now lie inside the policy space.** The grid's lower bound (0.5) follows T-H and R2-H: b < 0.75 never improved J in any cell.
2. **Training-reward stop counting** samples every 1 s instead of every 0.2 s. Evaluation is unchanged: SUMO tripinfo `waitingCount`, via `r4_eval_rl --mode direct_fine`.

Everything else is as in Addendum A: reward weight, PPO configuration (minibatch 480), training and validation seeds, screening criteria and comparators. The comparators are the tuned classical `const:0.75` and the family bests `vslad:90:0.8`, `mtfc:36:38:9:0.0015`, `spec` and `nc`.

## Addendum D (2026-10-02 20:10): P-H3 hybrid residual pilot, using idle CPU while P-H2 trains

**Why.** P-H2 (16 envs) leaves about 70 % of the CPU idle, and the author asked to use it. P-H3 is the spin-off's original hybrid idea: a validated controller in the loop, with DRL on top.

**Design** (everything else as in P-H2):
- **Actions:** env mode `residual_c`, a continuous a ∈ [−1, 1]. b = clip(0.75 + 0.25·a, 0.5, 1.0), with |Δb| ≤ 0.2 per 60-s decision and the same staircase and acceleration area.
- **Starting point:** a = 0 reproduces the frozen tuned classical `const:0.75` exactly; the episode starts at b = 0.75. A Gaussian policy with log-std −1.0 starts near the tuned controller.
- **PPO:** 14 envs × 120 steps (rollout 1,680, minibatch 420), 500 updates, learning rate 3e-4 with decay, γ 0.99, GAE 0.95, net 128×128, learner seed 0.
- **Unchanged from P-H2:** reward weight (40 s per stop), training and validation seeds, `score_h` checkpointing, screening criteria and comparators.

**Screening:** the same `round4 screen`, run on P-H3's directory after it finishes, with policy evaluation in mode `residual_c`.

**Also, using the same idle CPU:** the **R5-H classical references** are pre-computed on the shared test seeds 7,120,500–7,120,529 (Addendum A) for `const:0.75`, `vslad:90:0.8`, `mtfc:36:38:9:0.0015`, `spec` and `nc`, at both cells. These are classical arms only. They are used only if a pilot passes screening.
