# Day-pattern track: plant options (v0, desk analysis, nothing run)

*2026-10-04 · inputs:*
- *`docs/review/day_pattern_research_v0.md` and its notes in `docs/review/day_pattern_notes/` (esp. `realistic_freeway_plants.md` Q1–Q5);*
- *`docs/lab/gate_ctx_r6/report_S1_20261004-1508.md`;*
- *the v6 `docs/feasibility/cvsig_step1_report.md` (read-only).*

*Scope: freeway, ramp and corridor control only. Traffic signals belong to v6.*

## What a plant must show (the existing realism gate, `t2_realism_protocol.md`, as applied in S1)

**Criteria:**
- **R-a:** capacity-drop ratio in [0.82, 0.97].
- **R-b:** wave speed in [−25, −10] km/h, or n/a.
- **R-c:** 0 teleports and 0 FAIL at the operating point; queue discharge in [1,600, 2,400] veh/h/lane; deterministic.
- **R-d:** congestion starts at the bottleneck.

**What the day-pattern idea needs in addition:**
- **D-1, full-day episodes:** 05:00–23:00 plus a drain, about 18 h of simulated time. Every plant is costed for this.
- **D-2, demand reconstruction:** demand must enter at an *uncongested* upstream boundary, so that the plant's counted profile at the bottleneck is clipped by the plant itself, not by the input data.
- **D-3, ramp queue storage:** ramp queues must be physical, so that a queue-limit side constraint means something.

**Where the plants so far stand:**
- Five v5 freeway plants failed the realism gate (MRG3, LD3, ZM3, and BN4 B0/B2/B3); their discharge was 900–1,528 veh/h/lane.
- The research notes found **no published SUMO configuration** that shows a discharge of ≥ 1,600 veh/h/lane and a 3–18 % drop together (notes Q1, all [VERIFY]-level).
- The v6 signalised plant passed with Krauss (1,854 veh/h/lane). **[Inference, notes]** This points to merge or lane-change artefacts rather than car-following as the v5 failure cause.

## Plant options

Cost: build = my estimate of engineering effort; full-day compute = estimated per episode and is **not measured**; risk = main threat to a thesis claim.

| # | Plant | Realism-gate expectation | Build cost | Full-day compute (est.) | Main risk |
|---|---|---|---|---|---|
| **P1** | **Two-capacity CTM** (Srivastava & Geroliminis-type memory rule, or a Kontorinaki et al. 2017 variant) of a metered on-ramp bottleneck or a short corridor; physical ramp queue; FD and drop fitted to a real site (MnDOT or PeMS) | R-a, R-c pass **by construction** (the drop and discharge are inputs); R-b **n/a** (a first-order model has no stop-and-go waves); R-d passes by construction | low: about 2–4 days of code, plus about 1 week to fit the FD and drop to field data | milliseconds to seconds | The drop is an assumption, and the controller benefit scales with it (Cao et al. 2021). Weak evidence on its own. VSL that acts through waves cannot be studied. |
| **P2** | **METANET**, calibrated to a real site (open calibration code: Chan et al. 2026 on PeMS [VERIFY]) | drop "to an extent" (Wang et al. 2023); some wave dynamics; discharge per calibration | medium: about 1–2 weeks, including calibration and identifiability checks | seconds | Identifiability of the parameters; drop magnitude only partly controlled; the same "model = plant" bias if the MPC comparator also uses METANET. That needs a structural mismatch (MPC on CTM, plant METANET, or the reverse). |
| **P3** | **Rebuilt SUMO on-ramp merge**: Krauss with σ > 0, or EIDM with error terms; ≥ 5 driver classes; assertive and impatient ramp drivers; a longer acceleration lane; a ban on mainline use of the auxiliary lane; an unregulated merge (maintainer advice and the 2026 recipe, both [VERIFY]) | **unknown, no precedent.** The cheapest discriminating test first: a single-lane jam-release discharge test with the candidate vTypes. If it reaches ≥ 1,600 veh/h/lane, the merge settings are the problem. | medium–high: about 1–3 weeks of gated iteration, each variant pre-registered | about 5–20 min per full-day run [estimate from BN4: 2,440 s with about 1,300 vehicles in about 5 s, scaled to about 50–80 k vehicles/day] | It may fail like the five plants before it. Stop-and-go waves are not reproduced even in calibrated SUMO I-24 scenarios (Hickert et al. 2026). |
| **P4** | **Open calibrated SUMO scenario, Alicante–Murcia** (9 days, 97 km, MIT licence [VERIFY]) | bottleneck drop and discharge undocumented; SUMO 1.27 compatibility unchecked | medium: run it, cut out a ramp-metered section, then run the realism gate | high (97 km); a cut-out section is cheaper | It may not contain a recurrent metered bottleneck, and the realism checks may fail. Its calibration targets counts and speeds, not the drop. |
| **P5** | **I-210 / I-24 SUMO scenarios** | I-24: waves not reproduced (Hickert et al. 2026); I-210: public availability unconfirmed | unknown (access first) | high | access; the same realism gaps as P3 |
| **P6** | **Hybrid: P1 or P2 for the gate and DRL training, plus P3 (or P4) for confirmation of the ranking** | P1/P2 as above; the claim needs P3 to pass realism | the sum of the parts | as the parts | Two plants double the gate work. A claim that holds only on P1 is a weak claim. |
| — | v6 signalised grid (passed realism) | — | — | — | **Out of scope** (signals belong to v6) |
| — | BN4 family | **FAIL** (S1 outcome C) | — | — | excluded |

**Data for calibration** (research notes Q4; status as of 2026-10-04, [VERIFY]):
- **MnDOT (Twin Cities):** 30-s data, public with no login, many metered ramps. This is the first choice.
- **PeMS:** a free account; its modernisation project ended in October 2025.
- **NDW and WebTRIS:** open, with sparser ramp data.
- **Caveat:** under active metering, ramp counts show the metered release, not demand. Ramp demand needs a queue-detector count plus the change in queue, or an upstream proxy.

## Recommendation (for the author to decide)

1. **First, the cheapest discriminating check (P3 pre-check):**
   - a pre-registered single-lane jam-release discharge test with 3–4 candidate freeway vTypes (Krauss σ, EIDM with error terms, Krauss as in v6);
   - about 1 hour of compute.
   - **If no vType reaches 1,600 veh/h/lane,** microscopic SUMO is out for this track. Go to P1/P2 and accept that the claim is conditional on the drop model.
2. **For the headroom gate itself, P1 (two-capacity CTM fitted to MnDOT) with the drop swept over {0, 5, 10, 15} %.**
   - Full days make SUMO costly, and the gate needs many day × seed × arm runs.
   - **GO requires H ≥ 10 % at the field-fitted drop. A GO that exists only at assumed drops above the field value is reported as conditional.**
3. **A GO on P1 is followed by confirmation on P3** (if P3 passed realism) before any DRL claim. This is the P6 structure.
