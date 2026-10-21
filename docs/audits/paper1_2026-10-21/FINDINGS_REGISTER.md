# Findings-resolution register: paper_1 audit (for author approval; D1-D3 decided in V131)

One row per merged finding group of the forensic audit (`REPORT_paper1_forensic_audit.md`, section 6.E numbering). Nothing here has been applied.

**Resolution types.**
- FIX: correct a false statement.
- REWORD: qualify a statement to what the evidence supports.
- DISCLOSE: add an omitted fact from existing evidence.
- REPORT: add an existing result to the paper.
- CITE: change or add a reference (you add it in Zotero).
- LIMIT: state as a limitation; an 8.4 experiment could remove it later.
- NOTES: fix a results note or a process, not the paper.
- NONE: no action (positive result, or a note about the audit itself).

**Exit rule (V130, proposed).** At the end, the claim-evidence matrix, rebuilt from the revised `paper.qmd`, has no CONTRADICTED and no UNVERIFIED claim.
- A claim leaves CONTRADICTED only in three ways: its text is changed to what the evidence supports, new evidence supports the original text, or the claim is removed.
- A claim leaves UNVERIFIED only through evidence (for example a source you have read) or by removal.
- Verdict definitions are never relaxed.
- Every claim the fixes add (new numbers, disclosures) enters the matrix and is verified too.

## Claims that block the exit rule now

| Claim | Now | Finding | How it leaves that state |
|---|---|---|---|
| C01 | UNVERIFIED | LIT-F12 | a source you have read (D5), or rephrase without an empirical claim |
| C06 | CONTRADICTED | LIT-F1 | cite Smaragdis et al. 2004 (abstract states AD-ALINEA); then VERIFIED at abstract level |
| C11 | CONTRADICTED | PROV-F1 | reword to per-study pre-registration + disclose the sequence; evidence: page hashes and git times |
| C53 | CONTRADICTED | PROV-F1 | as C11 |
| C18 | CONTRADICTED | G5-F1, S23-F2 | report p* and f* (data exist, A10 requires them), or delete the promise (D2) |
| C41 | CONTRADICTED | TEXT-F5 | fix the definition of N |
| C77 | CONTRADICTED | S23-F1 | 13.3 % -> 19.3 % |

## Decisions needed from you

- **D1**: DECIDED (V131): one Study-sequence paragraph + one sentence with P1's differing numbers. Question was: how to disclose the study sequence (D1/D2 -> P1 -> P1b -> C1) and how much of P1 to report
- **D2**: DECIDED (V131): p* and f* rows in Table II, clean-day and false-alarm cost one sentence each. Question was: which omitted pre-registered outputs enter the paper (p*, f*, clean-day and false-alarm cost, combined row, NC row)
- **D3**: DECIDED (V131): disclose the drain; give window TTT, paired served throughput and the share of gain after 940 s for S1b and C1, labelled as computed after the run. Question was: how to report the drain convention and the co-metrics (window TTT, served throughput)
- **D4**: Whether the post-hoc analyses (ID-rule sensitivity, C1 mechanism, floor, duration regime) go into the Discussion with numbers
- **D5**: Source for the opening sentence (C01), or a rewording
- **D6**: Keep or drop "Honest" in the title, and the other loaded words

Also open: the four severity overrides in report section 6.E (HEADLINE-F2, CTRL-F2, CTRL-F3, G2-F2 raised to major); confirm or change.

Counts by type (first word): DISCLOSE 29, REWORD 24, NONE 17, FIX 10, REPORT 8, CITE 6, NOTES 3, = 2, LIMIT 2.

## Register

| # | Group | Severity | Finding | Resolution | Proposed action | Claims touched | Decision |
|---|---|---|---|---|---|---|---|
| 1 | PROV-F1 | critical | 'Pre-registered before any data' is false: D2->P1->P1b->C1 sequence and post-hoc choices undisclosed | **REWORD + DISCLOSE** | Lines 69, 145: "each study's statements, seed ranges and code were fixed and hashed before that study's data". Add a short "Study sequence" paragraph: D1/D2 screens -> P1 -> P1b (redesigned after P1: amber, PI-law plans, rate clip, runner rows) -> C1 (cell and comparator chosen from P1b results). | C11, C13, C46, C47, C53, C60, C71, C75, C85 | D1 |
| 2 | COMETRIC | major | Pre-registered co-metrics (served throughput, TTT) missing; on fixed-window TTT S1b has no passing cell | **REPORT + DISCLOSE** | Report the pre-registered co-metrics for the S1b and C1 comparisons: paired served throughput and fixed-window TTT (S1b IP vs ID 7.4 / 1.7 / 9.9 / 0.0 %, no cell >= 10 %; C1 11.7 %), labelled as computed after the run from stored per-run fields. | - | D3 |
| 3 | CTRL-F1 | major | S1b magnitudes depend on a fragile/dominated ID plan chosen by the pooled-median rule | **DISCLOSE** | State the pre-registered pooled-median tuning rule for ID and L0, and that the S1b magnitudes are conditional on it; optionally one sentence on the tuning-seed resampling (post hoc): PASS in about 74 % of resamples, median gains 4.4 / 12.5 %. | C27, C46, C47, C64, C66, C69 | D4 |
| 4 | CTRL-F2 | major | C1 reference PI is Pareto-dominated and on grid edges; tuned arms on grid edges undisclosed | **DISCLOSE (+ 8.4 option)** | State that the q1600 PI optimum lies on two grid edges (K_P = 70, K_I = 120) and is Pareto-dominated; optionally add that IP also beats the dominating PI laws by 14-21 % on P1b seeds (post hoc). 8.4 option: extended PI grid + C1-style test. | C08, C12, C26, C44 | D4 |
| 5 | CTRL-F3 | major | ID equals the always-on law with N before onset (and IP=ID in block_q2000); comparisons measure only pre-onset effect | **DISCLOSE** | State that ID's tuned plan is FB's law (q1600) and PI's law (q2000) started at onset, so ID vs that arm measures the cost of running N before onset; IP = ID in block_q2000 by construction (0.0 is an identity). | C27, C28, C29, C46, C64, C65 | - |
| 6 | CTRL-F4 | major | IP gain comes from type-specific parameters, not timing; controller-family confound undisclosed | **DISCLOSE** | Discussion: the type gain comes from type-specific parameters (set point), not from the switching time; an always-on law tuned per type would do as well but needs the type in advance, so it is not an L0 arm. | C12, C26, C28, C44, C71, C73 | D4 |
| 7 | DRAIN | major | End-of-horizon convention (all-green, demand-free drain after 940 s) carries most of every headline gain | **DISCLOSE + LIMIT** | Plant section: demand stops at 940 s, the meter goes all-green and the network drains without control; this phase is in the delay metric. Results: share of the gain after 940 s (S1b 83 / 67 %, C1 55 %); the slow_q2000 S1b pass depends on it. 8.4 option: control kept active during the drain. | C12, C24, C34, C57, C66, C69, C71, C85 | D3 |
| 8 | G2-F2 | major | C1/crawl gains come from L0/ID laws over-holding all four lanes (the crawl lane inflates the edge-4 count; no lane changes); untested with lane changi | **DISCLOSE + LIMIT (+ 8.4 option)** | Discussion: C1 mechanism (crawl lane fills the edge-4 count; PI holds all four lanes; about half the inflow must use the crawl lane; no lane changes). Limitation: a blockage with lane changes was not tested. 8.4 options: lane-change blockage; lane-group detector. | C36, C37, C71 | D4 |
| 9 | G2-F3 | major | Exploratory: the type-plan gain over PI/ID reverses for incidents shorter than about 230 s and grows with duration (replicated on P1b and C1 seeds) | **REPORT (exploratory) or LIMIT** | The crawl-cell gain over PI reverses for incidents shorter than about 230 s (replicated on P1b and C1 seeds). Report as exploratory with numbers, or mention as a limitation; a confirmatory claim needs a pre-registered test (8.4). | C71 | D4 |
| 10 | G3R-F1 | major | The 200 veh/h floor (135-s reds on all four lanes) has no stated reason, is far below the paper's own cited source, binds in every C1 PI run and alone | **DISCLOSE + LIMIT (+ 8.4 option)** | State the 200 veh/h floor and its 135-s reds on all four lanes, that it binds in every C1 PI run, and that the cited work uses floors near 43 % of capacity. Before using its numbers: one adversarial check (it is the only single-agent major). 8.4 option: higher floor. | C35, C66, C71, C72, C85 | D4 |
| 11 | G5-F1 | major | Pre-registered S3 rows omitted: p*, f* (paper outputs under A10) and the combined row; under d=60, c=60, p=0.2 IP has no CI above zero vs the stronges | **REPORT** | Report p* and f* (A10 paper outputs), with CIs and binding arm (C1 cell: p* = 0.21 [0.12, 0.33] vs FB); optionally the combined row (no CI above 0 vs the strongest L0 in any cell). | C14, C18, C73, C79, C80 | D2 |
| 12 | HEADLINE-F2 | major | C1 tests IP only against PI; FB was the strongest always-on arm in that cell | **DISCLOSE** | C1 section: the comparator PI was chosen after P1b; FB had the lower median in that cell on P1b seeds (IP vs FB 15.9 %, not re-tested on fresh seeds). | C60, C68, C70, C75 | D1 |
| 13 | LIT-F1 | major | AD-ALINEA cited to wrong Smaragdis paper/year; AD arm weak | **CITE** | Cite Smaragdis, Papageorgiou & Kosmatopoulos 2004 (TR-B 38(3):251-270, doi 10.1016/S0191-2615(03)00012-2) for AD-ALINEA at lines 65, 81, 118; say AD uses its own sign-rule set-point update. You add it in Zotero. | C06, C17, C45 | - |
| 14 | LIT-F3 | major | Plant geometry and FB baseline from Flow / Vinitsky et al. 2018 not cited | **CITE** | Credit the Flow / Vinitsky et al. bottleneck (ITSC 2018, pp. 759-765, doi 10.1109/itsc.2018.8569615) for the geometry and the FB meter defaults. Metadata verified; you should read its Sec. III-E to confirm before citing. | C04, C09, C16 | - |
| 15 | PLANT-F1 | major | q2000 oversaturated without incident; uncontrolled plant loses ~40 % capacity | **DISCLOSE** | Plant section: at q2000 demand exceeds the metered capacity even without an incident (about 1,450-1,610 veh/h); without control the plant serves about 960-1,010 veh/h. | C22, C33, C84 | - |
| 16 | PLANT-F2 | major | Meter off and demand stops after 900 s; large delay share in uncontrolled drain | **= DRAIN** | Same root cause as DRAIN; resolved by the same text. | C24, C34 | D3 |
| 17 | PLANT-F3 | major | No-red-crossing enforced by physically impossible SUMO emergency stops | **DISCLOSE + REWORD** | Say that SUMO forbids non-runners to pass red and forces a non-physical stop at the line when they cannot brake (12.8 % of runs); "no red crossing" is by construction, not a safety result. | C20, C61, C62, C83 | - |
| 18 | PLANT-F4 | major | Crawl lane forces half the inflow through 1 m/s lane with no lane change; not disclosed | **= G2-F2** | Plant section: the crawl is on lane 4_1 of the 2-lane edge, fed by lanes 3_2 and 3_3; with lane changing off about half the vehicles must use it. | C22, C25, C36, C37 | - |
| 19 | PROV-F2 | major | Earlier P1 round omitted despite addendum promise; its results differ | **DISCLOSE / REPORT** | Report P1 as the earlier round, as the P1b addendum promised. At minimum: what changed and the key differing numbers (C1 cell IP vs PI -0.7 % in P1; d* slow_q2000 26 s vs 120 s; block_q2000 S2 lower bound -1.8 vs 3.5 %); say the C1 effect appeared after PI-law plans were added to A. | C11, C13, C53, C54, C60, C85 | D1 |
| 20 | REPRO-F3 | major | CRN claim overstated and unsupported by reported experiment or citation | **REWORD** | Line 141 CRN sentence: describe the spot-run evidence (equal seeds give identical vehicle streams until insertion times diverge) or delete it; pairing stays valid. | C13, C52 | - |
| 21 | S1-F1 | major | Table II caption inverts the sign convention | **FIX** | Table II caption: "positive favours the first-named arm". | C12, C56, C69 | - |
| 22 | S23-F1 | major | Stale P1 value 13.3 % in S2 upper-bound range (should be 19.3-47.9 %) | **FIX** | Line 193: 13.3 % -> 19.3 %. | C13, C49, C68, C77 | - |
| 23 | S23-F2 | major | Pre-registered outputs missing: clean-day cost, prevalence, p*, f*, c*, false-alarm cost, combined row | **REPORT** | Report the clean-day cost per arm (e.g. always-on PI +12.0 / +151.6 s/veh vs N) and the false-alarm cost (39.5 / 120.4 s/veh), as line 104 and the protocol promise; with G5-F1 this keeps line 85. | C08, C14, C18, C30, C31, C59, C64 | D2 |
| 24 | TEXT-F12 | major | Plant details needed for reproduction missing from the paper | **DISCLOSE** | Plant details: IDM parameters, 10 % AV vType, 0.5-s step, random depart lane, Poisson demand, drain cap, 50/50 type mix in tuning, simulated lane lengths. | C09, C12, C32, C33, C34, C37, C61, C62, C85 | - |
| 25 | TEXT-F13 | major | Spill share uses an undisclosed post-run proxy and excludes FX | **REWORD** | Line 197 spill sentence: define the indicator (tail within 50 m of the entry or mean depart delay > 5 s), say it was recomputed after the run, give FX's values; the queue tail never passed 368.7 of 410 m. | C53, C84, C85 | - |
| 26 | TEXT-F5 | major | N described as constant rate but is a feedback law at q2000 | **FIX** | Line 118: N = "the best of 20 constant rates and 30 FB laws on incident-free days" (a constant rate at q1600, a feedback law at q2000). | C12, C64 | - |
| 27 | TEXT-F9 | major | C1 reporting gaps (rule, CI, post-hoc, PI only, metric name) | **REWORD + DISCLOSE** | C1 paragraph: state the rule (point rel >= 10 % and diff-CI lower bound > 0, both views), the post-hoc choice of cell and comparator, the statistic name, and "no run was invalid". | C12, C13 | D1 |
| 28 | C1-F3 | minor | Decision rule tests >=10 % on point estimate only; CIs include gains below 10 % | **REWORD** | Do not suggest that a gain of at least 10 % was confirmed: the rule tests the point estimate; rel CI [7.3, 23.7]. | C64, C66, C71, C73, C75 | - |
| 29 | C1-F7 | minor | Emergency-stop population and braking warnings not stated | **DISCLOSE** | If the emergency-stop share stays: say which runs it covers (all k = 0, s = 0 runs, 83 % oracle actions) or give it per deployed arm. | C82 | D1 |
| 30 | C1-F8 | minor | C1 descriptive rows not labelled descriptive | **REWORD** | Label the C1 detection-delay and runner rows "descriptive". | C73, C74 | - |
| 31 | CTRL-F12 | minor | Wrong-type p* is a per-seed exact mixture, not simulated misclassification | **DISCLOSE** | When p* is reported: it is an exact per-seed mixture of the two plans, not simulated misclassification. | C47 | D2 |
| 32 | CTRL-F6 | minor | TP placebo is not a like-for-like measure of OR_in noise inflation | **REWORD** | Lines 141, 193: TP = best of the main run and 4 replicates with demand redrawn; an illustration of noise, not a matched null for OR_in. | C49, C51, C78 | - |
| 33 | CTRL-F9 | minor | Fig. 2 strongest always-on arm chosen per cell on evaluation seeds | **REWORD** | Fig. 2 caption: the strongest L0 bar is chosen per cell on evaluation seeds (conservative). | C48 | - |
| 34 | G2-F5 | minor | The gain over no control comes from avoiding a post-clearance zipper breakdown; the paper does not explain this | **DISCLOSE (optional)** | Discussion: IP's gain over no control comes from avoiding a post-clearance zipper breakdown. | C71 | D4 |
| 35 | G3R-F2 | minor | Long-wait warnings (H-R5, a vehicle waiting > 120 s) appear only in arms that reach the floor and are not reported; the results survive excluding them | **NONE (optional DISCLOSE)** | Long-wait warnings (H-R5) appear only in arms at the floor; C1 holds without those seeds (13.5 % [3.3, 20.5], post hoc). Mention only if the floor is discussed. | C71, C72 | D4 |
| 36 | G3R-F3 | minor | Actuation lag of switched law plans: real and pre-registered, with no measurable bias; the critic's proposed mechanism is not supported; the 30-s upda | **DISCLOSE** | State the 30-s update grid on the edge-4 count and that law plans act at the next update after a switch (lag 1-29 s, no bias found). | C14, C47, C73, C79, C80, C81, C86 | - |
| 37 | G3R-F4 | minor | C1's tolerance of detection delay comes from a slow-acting plan, not from robust use of type information | **DISCLOSE (optional)** | Discussion: C1's tolerance of detection delay comes from a slow-acting plan, not from robust use of type information. | C73, C79, C80, C86 | D4 |
| 38 | G4-F5 | minor | Cycle formula written with the demand q; the code uses the commanded rate | **FIX** | Line 110: write the cycle with the commanded rate r, not the demand q. | C22, C35 | - |
| 39 | G5-F4 | minor | c* '> 180' in three cells is vacuous: the stay plans cannot be affected by a clearance delay | **FIX (+ NOTES)** | If c* is reported: "n/a (stay plan)" where IP never returns; same fix in p1b_result.md. | C79 | D2 |
| 40 | G5-F5 | minor | 'Detection delay' means onset delay only; Table I overstates which information the tuned plans use | **REWORD** | "Detection delay" = onset delay, clearance perfect; adjust Table I (only 1 of 4 IP plans and no ID plan use clearance). | C14, C73, C80 | - |
| 41 | G8-F6 | minor | 'Feedback laws ... apply directly' sits beside a source that reports calibration and auto-tuning were needed | **REWORD** | Line 81 "apply directly" -> the law structure transfers; parameters need tuning (Tympakianaki 2014). | C15, C44 | - |
| 42 | HEADLINE-F3 | minor | Printed S1 intervals are rel CIs, not the decision-rule diff CIs | **REWORD** | Say the printed intervals are CIs of rel; the decisions use the CI of the median difference. | - | - |
| 43 | HEADLINE-F4 | minor | Bootstrap Monte Carlo error of 0.99375 bounds exceeds printed precision | **DISCLOSE** | Footnote: CI ends at the 0.99375 level move by up to about 1.6 points with the bootstrap seed; the fixed seed is used. | C56, C66, C67 | - |
| 44 | HEADLINE-F5 | minor | 'Same result excluding invalid runs' is vacuous: zero invalid runs | **REWORD** | Line 187: "no run was invalid" instead of "the same result when seeds with invalid runs are excluded". | C70, C72, C75 | - |
| 45 | HEADLINE-F6 | minor | 'Reduced median delay by 16.2 %' is not the change in the median | **REWORD** | Line 187: "the median paired reduction was 16.2 % of PI's median delay" (the medians differ by 17.3 %). | C71 | - |
| 46 | LIT-F10 | minor | Bias results concern expectations; paper reports medians | **REWORD** | Lines 89, 141: the bias results concern expectations; ORX is low in expectation (mean version used). | C10, C21 | - |
| 47 | LIT-F11 | minor | Cited mainline metering engages only in near-stopped traffic | **LIMIT** | Discussion: cited mainline meters engage in near-stopped traffic (Ghiasi 2018); here the meter cycles from the start of control at 23 m/s. | C03, C15 | - |
| 48 | LIT-F12 | minor | C01 opening sentence uncited | **CITE or REWORD** | Line 63 (C01): a source you have read (candidates Knoop et al. 2008, Skabardonis et al. 2003; or your WoS search #2), or rephrase. | C01 | D5 |
| 49 | LIT-F13 | minor | C07 wording mismatches cited methods | **REWORD** | Line 65: Sheu detects incidents itself, Dabiri schedules gains on estimated incident parameters; drop "usually compared with ...". | C07, C17 | - |
| 50 | LIT-F2 | minor | Carlson2010 is optimal control, not the same feedback laws | **CITE / REWORD** | Line 65: replace Carlson2010 by Carlson et al. 2014 (TR-C 46:209-221, metadata verified) or reword; you add it in Zotero. | C05 | - |
| 51 | LIT-F4 | minor | Amber presented beside sources using green-red signals | **REWORD** | Line 81: the amber phase is this study's design; the cited works use green-red signals. | C15 | - |
| 52 | LIT-F5 | minor | Feedback laws use 0.5-s count snapshot, undisclosed | **DISCLOSE** | State the 0.5-s count snapshot per 30-s update (not a period average). | C04, C16 | - |
| 53 | LIT-F6 | minor | AD arm is the paper's own sign rule, not stated | **DISCLOSE** | State the AD update rule in one line. | C06, C17 | - |
| 54 | LIT-F7 | minor | Runner shares not compared with field numbers | **REWORD** | Line 149: give the verified field range (TOPS 2005: 0.9-9 % red violations, SOV lanes) so s = 10 / 30 % read as stress values. | C19, C63 | - |
| 55 | LIT-F9 | minor | TOPS2005 wrong author and missing report details | **CITE** | Fix the TOPS2005 author in Zotero (UW-Madison ITS Program, for WisDOT, 13 Jan 2005). | C19, C63 | - |
| 56 | PLANT-F10 | minor | Amber threshold and dilemma zone not stated; 3-s amber short for 23 m/s | **DISCLOSE** | State the amber stop threshold (3 m/s2) and the dilemma zone of a 3-s amber at 23 m/s. | C61 | - |
| 57 | PLANT-F5 | minor | Emergency braking at downstream merges in 94.5 % of metered runs unreported | **NONE** | Downgraded by verification (hard braking is on the incident lanes, not the merges); no paper action unless braking is discussed. | C83 | - |
| 58 | PLANT-F7 | minor | Delay reference speed is the incident-reduced lane limit | **DISCLOSE** | One clause: timeLoss is measured against the incident-reduced speed limit (effect <= 0.8 points). | C24 | - |
| 59 | PLANT-F8 | minor | Emergency-stop share dominated by meter start-up transient | **DISCLOSE** | If the emergency-stop share stays: 44 % of forced stops occur at the first red after warm-up (start-up transient). | C61, C83 | D1 |
| 60 | PLANT-F9 | minor | Runners cross later reds whenever they cannot brake | **REWORD** | Line 149: runners also cross any red when they cannot brake. | C62 | - |
| 61 | PROV-F4 | minor | 'Run once from frozen code' does not hold for P1 or D1/D2 | **DISCLOSE** | Study-sequence paragraph: P1 was aborted and resumed at the tool-check stage (same commit); D1/D2 were re-run after the V100 bug. | C54 | D1 |
| 62 | PROV-F5 | minor | Amber 87 % -> 12.8 % emergency-stop reduction compares two different studies | **REWORD** | Line 197: the 87 % -> 12.8 % comparison spans two studies; use the matched comparisons (30 matched specs 67.6 -> 14.7 %; smoke 538 -> 13 stops) or drop the causal wording. | C14, C54, C82 | D1 |
| 63 | PROV-F6 | minor | Seed use departs from approved block labels; not disclosed in paper | **DISCLOSE** | One clause: seed ranges used vs approved labels (tool checks 260-279, tuning 300-339), all disjoint. | C53, C55 | - |
| 64 | REPRO-F2 | minor | Fig. 2 marginal medians disagree with paired statistics | **REWORD** | Fig. 2 caption: bars are marginal medians; the bounds in Table II are paired CI ends. | C68 | - |
| 65 | REPRO-F5 | minor | Fig. 1 text labels overlap | **FIX** | Fig. 1: move the overlapping labels (fig_plant.py:25, 34). | C25 | - |
| 66 | REPRO-F7 | minor | 'Incident of random type may occur' does not match cell design | **FIX** | Line 93: "an incident of a given type" (type fixed per cell). | C25 | - |
| 67 | S1-F6 | minor | S1 family and interval construction not described | **DISCLOSE** | Bonferroni family m = 8 (2 statements x 4 cells), intersection-union across L0 arms, both views, fail closed. | C56, C57, C58 | - |
| 68 | S1-F8 | minor | Table II shows S1a only against PI; FB also blocks S1a | **REPORT / REWORD** | Table II: add ID vs FB, or note that FB also blocks S1a. | C64, C69 | - |
| 69 | S23-F3 | minor | 'Lead vanished within 3 s' is an interpolation artefact | **REWORD** | Line 197: "between 0 and 30 s (interpolated 2.6 s)" instead of "within 3 s". | C80 | - |
| 70 | S23-F4 | minor | 'Stayed ahead to ~120 s' omits wide CI and zero margin | **REWORD** | Line 197: d* = 120 s with 95 % CI [20.1, 168.5]; the lead at d = 0 was not significant. | C79 | - |
| 71 | S23-F6 | minor | Plateau criterion unattainable at n=100 and tests ORX only | **DISCLOSE** | The plateau criterion needed a CI width <= 2 points, unattainable at n = 100. | C76 | - |
| 72 | TEXT-F15 | minor | Loaded or overstated wording | **REWORD** | Soften "honest", "strong", "full set", "upper limit", "never better", "the lead held". | C12, C13, C85 | D6 |
| 73 | TEXT-F17 | minor | Small internal inconsistencies | **FIX** | Small inconsistencies: lane drop 4 -> 2 -> 1 everywhere; TP wording; incident location. | C13 | - |
| 74 | TEXT-F18 | minor | Other protocol-required outputs absent (NC row, operating map, tool checks) | **REPORT** | NC row (in C1's cell N is worse than NC), the tool checks T0-T4 and the operating map, as space allows. | C12 | D2 |
| 75 | TEXT-F6 | minor | What ID knows is defined inconsistently | **FIX** | One definition of ID's information (onset; clearance only through "back" actions) in lines 100, 118 and Table I. | C08, C12 | - |
| 76 | C1-F9 | info | C1 throughput co-headline not reported | **REPORT** | C1 served throughput 1,140 vs 1,074 veh/h (with COMETRIC). | C71 | D3 |
| 77 | CTRL-F13 | info | No data leakage found | **NONE** | Positive: no data leakage found. | C47, C50 | - |
| 78 | CTRL-F14 | info | Unequal tuning freedom across arms | **NONE (optional DISCLOSE)** | Tuning freedom differs by arm; selection is out of sample, so no inflation. | C26, C42 | - |
| 79 | FU2-1-F5 | info | Round-1 VERIFIED verdicts on C66, C69, C71 contradict the tracers' own failure points | **NONE** | About the audit itself (round-1 verdict inconsistencies, already reconciled). | C64, C66, C69, C71 | - |
| 80 | G2-F7 | info | The protocols give node-to-node lengths, not the simulated lane lengths | **NONE** | Protocol node-to-node lengths vs simulated lane lengths; the paper gives lane lengths under TEXT-F12. | C37 | - |
| 81 | G5-F6 | info | slow_q1600 c* is non-monotone and interpolated; a 60-s late return beats the exact return | **NONE** | Only relevant if c* is reported (non-monotone in slow_q1600). | C80 | D2 |
| 82 | G8-F7 | info | Several cited works remain abstract-only after all legal routes failed | **NOTES** | You obtain full texts via the library (Tympakianaki 2014, Wang 2014, Wu 2014, Spiliopoulou 2010, Carlson 2010/2011) to raise those citations from abstract to full-text basis. | C02, C05, C06, C07, C16, C44 | - |
| 83 | HEADLINE-F8 | info | slow_q1600 median and mean disagree in sign | **NONE (optional REPORT)** | slow_q1600 median +4.5 % vs mean -13.5 %: supports the fragility remark. | - | - |
| 84 | HEADLINE-F9 | info | Headline numbers verified from raw data | **NONE** | Positive: headline numbers verified from raw data. | - | - |
| 85 | LIT-F14 | info | PI degradation with runners unexplained vs literature | **NONE (optional DISCLOSE)** | PI degraded with runners although the literature reports robustness to red-light violations. | C19, C63 | - |
| 86 | LIT-F15 | info | Bib metadata state | **NONE** | Bib metadata state (all DOI entries match Crossref). | C02, C03, C04, C05, C10, C16, C19, C21 | - |
| 87 | LIT-F16 | info | FB and PI laws match ALINEA/PI-ALINEA structure | **NONE** | Positive: FB and PI match the ALINEA / PI-ALINEA structure. | C04, C16 | - |
| 88 | LIT-F8 | info | PI-ALINEA first proposed in Wang & Papageorgiou 2006 | **CITE (optional)** | Also cite Wang & Papageorgiou 2006 (ITSC, doi 10.1109/itsc.2006.1706778) for PI-ALINEA priority. | C04, C16 | - |
| 89 | PLANT-F13 | info | Collision check excludes junctions | **DISCLOSE** | With PLANT-F3: collisions were checked on lanes, not inside junctions (4 re-runs with junction checks: 0). | C40, C72, C83 | - |
| 90 | PLANT-F14 | info | Floating-point artefact in signal clock | **NONE** | Floating-point signal-clock artefact; code note for future studies. | C35 | - |
| 91 | PLANT-F15 | info | Protocol edge lengths differ from built network | **NONE** | Protocol lengths vs network; no paper claim. | C37 | - |
| 92 | PROV-F8 | info | Frozen worktrees deleted; frozen launch inferred | **NOTES** | Process: keep frozen worktrees until the paper is final, or record their removal. | C54, C70 | - |
| 93 | PROV-F9 | info | Hashed P1 page lists D1-D5 as open choices | **NONE** | Process: the page hash does not pin decisions D1-D5 (recorded in V100 and run args). | C53 | - |
| 94 | REPRO-F10 | info | Reproducibility positives; build artefacts not versioned | **NONE** | Positive: figures and data chain reproducible. | C68, C75 | - |
| 95 | S1-F10 | info | summary.md labels page path with addendum hash | **NOTES** | p1b_summary.md labels the base page with the addendum hash; fix the label. | - | - |
| 96 | S1-F11 | info | 'Never beat PI' is a median statement | **REWORD** | Line 197 "never beat" is a median statement. | C67 | - |
| 97 | S1-F9 | info | Integrity checks passed; tiny selection margins for two IP plans | **NONE** | Positive: integrity checks passed (tiny selection margins covered by CTRL-F1). | C66, C67 | - |
| 98 | S23-F7 | info | S2 bracket mixes estimands and confidence levels without disclosure | **DISCLOSE** | S2 bracket: lower end = mean-version ORX_4, upper end = median-version OR_in, level 0.9875. | C59, C86 | - |
| 99 | S23-F8 | info | Table II d* row lacks CIs and binding arms | **REPORT** | Table II d* row: add CIs and binding arms. | C86 | - |
| 100 | S23-F9 | info | TP wording 'best of five replicate runs' is inaccurate | **FIX** | TP = main run + 4 replicates (with CTRL-F6). | C78 | - |
| 101 | TEXT-F19 | info | Draft state: limitations not written | **LIMIT** | Discussion/Limitations and Conclusion still to be written; they collect every LIMIT item above. | C85 | - |
