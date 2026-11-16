# Strengthening plan v0: proper results from a proper implementation (paper_1 line)

**Status:** draft (V132); S1-S3 decided in V133 (BN4 + lane changes; the strengthened study is paper_1's evidence; incident + day-mix evaluation). S4 open. Nothing has been built or run.
**Author goal (2026-10-21):** "I want the project to be strengthened so that we have proper results based on proper implementation and logic."
**Inputs:**
- the forensic audit `docs/audits/paper1_2026-10-21/`: the report and `FINDINGS_REGISTER.md`;
- `docs/research/capacity_drop_lit_v0.md`;
- the roadmap option A in `docs/roadmap/thesis_roadmap_v0.md`;
- decisions V95-V131.

## 1. Why the current results are not yet "proper"

The audit found the arithmetic, the data integrity and the pre-registered verdicts sound. The weaknesses sit in **design and implementation choices**, which shape what the numbers mean. Text fixes can only disclose these; they cannot remove them.

| Area | What the audit found (finding ids) | Why it matters |
|---|---|---|
| Plant | Lane changing off. The "lane blockage" is a 1 m/s crawl lane that about half the inflow must use (PLANT-F4, G2-F2). Capacity drop without control is about 40 % (PLANT-F1); field values are 2-11 %, HCM default 7 % (`capacity_drop_lit_v0.md` §1). q2000 is oversaturated even on clean days | The confirmed C1 gain runs through this artefact (PI holds all four lanes because the crawl lane fills its detector) |
| Signal physics | 3-s amber at 23 m/s. Vehicles that cannot stop are forced to an instantaneous stop (about 26 m/s²) in 12.8 % of runs (PLANT-F3, PLANT-F10) | "No red crossing" is a simulator artefact, not behaviour |
| Meter limits | Rate floor 200 veh/h = 135-s reds on all four lanes, a code default with no rationale. The cited work uses about 43 % of capacity (G3R-F1) | C1's gain tracks PI's time at the floor |
| End of horizon | Meter all-green and no demand after 940 s; the uncontrolled drain carries 55-106 % of the gains (DRAIN, COMETRIC) | slow_q2000 S1b depends on it; on window TTT no S1b cell reaches 10 % |
| Metric | timeLoss against the incident-reduced speed limit (PLANT-F7) | Hides 3-8 s/veh; small, but not "door-to-door delay" as defined |
| Sensors | One 0.5-s snapshot of the whole-edge count every 30 s (LIT-F5) | Not ALINEA's period-averaged measurement; it counts the crawl lane |
| Controllers | AD is an own sign rule, not AD-ALINEA (LIT-F1/F6). The PI optimum lies on grid edges and is Pareto-dominated (CTRL-F2) | The always-on opponents are weaker than "tuned PI-ALINEA" suggests |
| Tuning logic | The pooled-median rule picks type-blind plans that are dominated in both types (CTRL-F1). ID/IP run N before onset, not the best L0 law (CTRL-F3) | S1b magnitudes depend on the rule; S1a vs PI is partly built in |
| Selection noise | The CIs cover evaluation noise only; the tuned (IP, ID) pair returns in only 15-23 % of tuning-seed resamples (HEADLINE-F1) | Reported gains overstate their stability |
| Confirmation | C1 tested only PI, chosen after P1b; FB was stronger (HEADLINE-F2) | "Beyond strong always-on feedback" is not confirmed |
| Day mix | Always-on arms pay on clean days (PI +151.6 s/veh at q2000) but the main analysis is "given an incident" (S23-F2) | The deployment question is the expected cost over a mix of days |
| Detection | Delay, wrong type and false alarms appear only as break-evens; clearance is always perfect (G5-F1, G5-F5) | The type gain over FB is gone at p ≈ 0.2 in the C1 cell |
| Regimes | The gain reverses for incidents shorter than about 230 s, found post hoc (G2-F3) | A real "conditional advantage" that must be pre-registered to be claimed |
| CRN | Equal seeds share random draws only until insertion times diverge (REPRO-F3) | Pairing works but removes less noise than it could |

## 2. Acceptance criteria: what "proper" means here (to be fixed in the protocol before data)

```
 PLANT      realistic and artefact-free  → tool check T1 (criteria committed first)
 OPPONENTS  published laws, tuned to an interior optimum, Pareto-checked
 LOGIC      ID/IP differ from L0 only in the information they use
 METRIC     door-to-door delay under one end-of-horizon convention with control kept on;
            co-metrics paired; day mix reported
 STATISTICS powered; selection noise quantified; every L0 arm in the confirmation
 PROCESS    one protocol, fresh approved seeds, frozen code, run once, every round reported
```

Proposed T1 realism criteria (numbers to be confirmed by the author; field ranges from `capacity_drop_lit_v0.md`, several of them [VERIFY]):

| Criterion | Proposed tolerance |
|---|---|
| Capacity drop at the bottleneck, uncontrolled, clean day | inside 3-20 % (field 2-11 %, HCM 7 %, review range 3-18 %) |
| Queue discharge per lane | inside the field QDF range of the note (≈ 1,770-2,330 pcplph) |
| Teleports | 0 |
| Collisions, lanes **and junctions** checked | 0 |
| Forced (non-physical) stops at the meter | < 1 % of signal approaches |
| Incident: lane closure with lane changes; the capacity reduction and the queue reach stated targets | yes |
| Control matters: some arm beats no control by ≥ 10 % at the realistic demand (CLAUDE.md early-KILL rule) | yes, else **KILL** on this plant |

## 3. Work items, each mapped to the findings it removes at the source

### WP1 Plant v2

| Item | Change | Removes |
|---|---|---|
| P1 | Lane changing on (LC2013 or a calibrated variant). Incidents as a **real lane closure** (blocked lane, forced lane changes) and as a slowdown; the crawl substitute is dropped | PLANT-F4, G2-F1/F2/F4, REPRO-F7 |
| P2 | Geometry and calibration on throw-away seeds until T1 holds. Demand levels set relative to the *measured* capacity (one undersaturated, one near capacity on clean days); upstream storage sized to the demand | PLANT-F1, TEXT-F13, spill caveat |
| P3 | Signal physics: yellow time from the kinematic rule for the approach speed (for 23 m/s and 3 m/s², roughly 4.5-5 s [VERIFY standard]) and/or a reduced approach speed before the meter; junction collision check on; forced stops counted against a tolerance | PLANT-F3, F8, F10, F13, PROV-F5 |
| P4 | Meter limits from the literature (rate floor ≈ 40 % of capacity as in Papageorgiou et al. 2008; a maximum red); optional lane-group offsets as in that paper | G3R-F1, G3R-F2 |
| P5 | Control stays active during the drain (the project's own F3Z convention, `docs/architecture/interfaces.md`); fixed-window TTT with unfinished vehicles counted, as a co-metric | DRAIN, PLANT-F2, COMETRIC, FU1-F7 |
| P6 | Delay against the nominal free-flow trip time, not the incident-reduced limit | PLANT-F7, FU1-F6 |
| P7 | Common random numbers: fix per-vehicle attributes (speed factor, type, depart lane where valid) in the route file, so all arms share them | REPRO-F3; more power |
| P8 | Vehicle population stated and justified (the 10 % 'av' type removed, or motivated); car-following model and parameters stated | G4-F4, TEXT-F12 |
| P9 | Per-lane loop detectors at a stated location; occupancy or counts averaged over the control period (ALINEA standard) | LIT-F5, detector part of G2-F2 |

### WP2 Controllers v2

| Item | Change | Removes |
|---|---|---|
| C1 | Published forms with unit tests against the equations: ALINEA, PI-ALINEA (Wang et al. 2014), **AD-ALINEA** (Smaragdis, Papageorgiou & Kosmatopoulos 2004 estimator) | LIT-F1, LIT-F6, C45 |
| C2 | Grid-adequacy rule: an optimum on a grid edge triggers a pre-registered grid extension on tuning seeds; Pareto check across incident types | CTRL-F2, CTRL-F14 |
| C3 | Type-blind tuning rule (L0 and ID) that cannot pick a plan dominated in both types: for example expected cost under the stated type mix (mean of per-type medians), after a Pareto filter; sensitivity to the rule reported | CTRL-F1, FU2-1-F1/F2 |
| C4 | Common baseline: ID and IP run the strongest L0 law by default and switch at onset ("PI by default + type plan", roadmap option A) | CTRL-F3, CTRL-F4, the controller-family confound |
| C5 | Selection noise: more tuning seeds, plus a pre-registered tuning-seed resampling that reports how stable the chosen plans and gains are | HEADLINE-F1 |
| C6 | Imperfect detection inside the main design (delay, misclassification, false alarms, clearance delay), not only as break-evens | G5-F1, G5-F5, CTRL-F12, C18 |

### WP3 Analysis v2

| Item | Change | Removes |
|---|---|---|
| A1 | Day-mix evaluation: expected cost over incident and clean days at stated prevalences; clean-day cost always reported | S23-F2, C31, TEXT-F18 |
| A2 | Pre-registered operating map: regimes by incident duration and severity, and demand | G2-F3 (becomes a test, not a post-hoc find) |
| A3 | Confirmation against **every** L0 arm (intersection-union) with the rule fixed before data | HEADLINE-F2, TEXT-F9, C1-F3 |
| A4 | Power analysis from P1b variances for the seed counts; S2 criteria that are attainable | S23-F6, HEADLINE-F4 |
| A5 | Paired co-metrics (TTT, throughput), mean and median, both CI types reported | COMETRIC, HEADLINE-F3, HEADLINE-F8, FU1-F8 |

### WP4 Process

- **R1** One protocol before data, with a design review (ultracode on) and author approval. A **new seed block** is needed: only 7,400,800-999 (200 seeds) remain in the reserved range, too few for tuning + evaluation + confirmation; the block needs author approval.
- **R2** Tool checks T0-T4, with the §2 realism criteria committed before they run.
- **R3** Adversarial code review before the runs. The frozen worktree is kept until the paper is final (PROV-F8).
- **R4** Independent verification after the run: a smaller version of the forensic audit.
- **R5** Every round reported in the paper (D1/D2, P1, P1b, C1, the new study), following V131-D1.

### WP5 Paper

The paper is rewritten from the new study's results. The reporting-class rows of `FINDINGS_REGISTER.md` (FIX / REWORD / DISCLOSE / CITE) apply to the new text. The V130 exit rule then applies: no CONTRADICTED or UNVERIFIED claim.

## 4. Order of work and gates

```
 author decisions (S1-S4)
   │
   ▼
 WP1 plant v2 + tests ──► calibration on throw-away seeds ──► T1 realism gate ──✗──► stop: rethink plant (KILL on BN4-type plant)
   │                                                        ✔
   ▼
 WP2 controllers v2 + WP3 analysis v2 + tests
   │
   ▼
 protocol (pre-registration) ──► design review (ultracode) ──► author approval + seed block
   │
   ▼
 adversarial code review ──► frozen worktree ──► tool checks T0-T4 ──► tuning ──► evaluation ──► confirmation (fresh seeds)
   │
   ▼
 independent verification ──► interpretation (ultracode) ──► paper rewrite ──► exit check (V130)
```

**Sizes (machine-speed rule; rough, to be measured in T0).**
- P1b ran about 345,000 runs in about 10 h at 9.6 runs/s with 32 workers.
- With lane changing on, runs may be slower; T0 measures it.
- Calibration: a few thousand runs on throw-away seeds.
- One full study of P1b size: about 10-20 h of compute.
- Build: plant, controllers and analysis changes with tests, of the order of 1-3 days of build work, plus author review time.

These are estimates, not measurements.

**Risk that must be accepted up front.** The strengthened study can remove the current positive results: S1b may fail, and C1 may not survive a realistic closure with lane changes and a strong, Pareto-checked opponent. The protocol fixes the early-KILL rule and the claims before data, so either outcome is reportable.

## 5. Decisions for the author

| # | Decision | Options | Recommendation |
|---|---|---|---|
| S1 | Plant | (a) BN4 topology with lane changes, a real closure and calibration; (b) a work-zone lane drop modelled on the cited mainline-metering studies (e.g. 2→1 or 3→2); (c) F3Z | (a) first, because it keeps continuity with P1/P1b and the Flow citation; fall back to (b) if T1 fails |
| S2 | Scope and timing | (a) the strengthened study becomes paper_1's evidence (ITSC deadline 1 Mar 2027); (b) paper_1 stays on P1b with full disclosure, and the strengthened study goes to paper 2 | (a): about 4 months remain, and the study fits in weeks of build plus days of compute |
| S3 | Evaluation target | (a) "given an incident" only; (b) given an incident **and** the day-mix expected cost at stated prevalences | (b) |
| S4 | Realism targets and seed block | confirm the §2 tolerances; approve a new seed block (e.g. 7,420,000-7,429,999, outside the DRL block 7,410,000-7,419,999) | confirm in the protocol step |

**Status of V130/V131.**
- They still hold. The V131 reporting decisions (D1 study sequence, D2 pre-registered outputs) carry over to the rewritten paper.
- D3 (disclose the drain) applies to any P1b result that is still reported. The new study removes the uncontrolled drain by design.
