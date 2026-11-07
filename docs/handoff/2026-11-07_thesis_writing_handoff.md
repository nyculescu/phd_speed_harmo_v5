# Handoff: thesis and article writing (2026-11-07)

From session 3c (round 2) to the new thesis chat. The writing line starts here. Decisions V456 and V457 in `docs/decisions.md` are binding.

## 1. Who owns what

| Session | Owns |
|---|---|
| new thesis chat | thesis outline v1, the claim, the plant V&V record, article 1, the LaTeX set-up |
| 3c | round 2: the chain, the remote poller `r2-remote-finish`, the round-2 readings and report |
| c3 | rented hardware only |

Don't touch the running units: r2-chain, r2-guard, r2-pad, r2-health, r2-remote-finish, and the r2-pace timers. The laptop's CPU belongs to round 2 until it ends, likely on 2026-11-08 (night cap 40 % from 23:00 to 09:00). Writing work needs no compute.

## 2. Fixed facts

- Title: "Adaptive driving algorithms for intelligent road traffic systems". Submission is about September 2027; target 2 papers.
- The claim bar is set by the author and Claude (V95, and V402: "We are on our own here"). D5.8 is history.
- Principle: conditional advantages, not universal superiority. Pre-register the regimes and report the full operating map.
- No "first/novel" claims. Mark literature not read in full [VERIFY]. Never invent titles, authors or numbers. ARC-IT framing codes [VERIFY]; no SOTIF.

## 3. Decisions that start this line

- **V456:** start writing the thesis and one article now. The clean plant gets a systems-engineering V&V record. A null DRL result is accepted. Disturbing the plant so that DRL shows value is the next step, and each disturbance is fixed before any control result (V245 caveat). The standard to claim is "verified and validated for its intended use", never "100 % proven".
- **V457:**
  - article 1 = the plant, the method and the operating map (DRL against tuned rules: win, tie or lose); publishable whatever round 2 shows;
  - parallel track after round 2 = non-learning opponents (an MPC with a model fitted on separate seeds, a non-learning adaptive scheduler); the plant stays unchanged;
  - medium = LaTeX in the repo, `docs/thesis` and `docs/paper1` on v5b1, tables generated from stored results.

## 4. Open blockers (ask the author)

1. No LaTeX on the machine: no pdflatex, latexmk or biber. Claude proposed Tectonic (a single binary in `~`, no sudo), or TinyTeX; a full TeX Live needs the author's `sudo apt`. Install nothing before the author picks.
2. The university's thesis template, if one exists.
3. The effort switch: CLAUDE.md's phase table puts a thesis claim at Extra High with ultracode on for the review. Ask in one line before starting.

## 5. Where the science stands

- **Closed or withdrawn** (archive branches `claude/*`, read only):
  - line #1, the safety margin: VALID-ONLY, no paper (V85);
  - metering claim KILLed on the realistic plant (V149);
  - old mobility results withdrawn as claims (V256).
  - `docs/roadmap/thesis_roadmap_v0.md` (V129) predates all three: rewrite it, don't extend it.
- **Current line:** per-CAV DRL speed commands on synthetic freeway plants (V245: synthetic preferred over a calibrated field site).
  - r1m3 (code name m32): 1 ramp lane, 3 main lanes. Plant P0 is V314 plus V328 (`docs/research/baseline_v1/plant_p0.json`).
  - r2m3 is used from phase 3 on.
- **Results so far:**
  - phase 1: DRL ties the rules on r1m3 P0;
  - confirmatory 2 (V359): DRL wins 1 of 20 cells, on safety (r2m3 X1 at 5,300);
  - confirmatory 3: X2 won, X1 closed (V396); X2 not replicated on 20 fresh seeds (V401);
  - V405: Claude's overstatement withdrawn; each baseline is beaten on one measure only;
  - demand sweep (V409, exploratory): edge over no control in a band of about 4,500-5,400 veh/h.
- **Baselines:** tags baseline-v0 to baseline-v4. baseline-v3 is plant_c3 with code `d2b2ecc`; baseline-v4 is v3w's policies (round 1).
- **Round 1** (`docs/research/results/round_1_result.md`, V451-V452): the control arm v3w advanced (baseline-v3's recipe retrained over 4,500-6,000 veh/h); the method candidates did not.
- **Round 2** (protocol `docs/research/protocols/round_2.md` rev 2, V453-V455): 5 trained candidates plus tail and sw against v3w, with re-tuned 3E rules (3E-X, searched on a rented machine). Validation, test and band follow; 3c writes the report.
- **Visual reports:** `docs/reports/`, for example `2026-11-05_19-22/`.

## 6. Plant V&V record (V456): starting material

Structure: requirements → verification method (test, analysis, inspection, demonstration) → evidence → traceability matrix → stated limits.

**Evidence that exists:**
- 501 unit tests; `docs/testing/test_strategy.md`;
- checks T0 (the actuator binds), T1 (capacity drop without teleport artefacts), T3 (determinism);
- smoke checks, traced = untraced (V386);
- baselines v0-v4;
- sources: `docs/research/capacity_drop_lit_v0.md`, `driver_params_hdv_cav_v0.md`, `irish_parameters_v0.md`, `crash_model_evidence_v0.md`;
- architecture: `docs/architecture/`.

**Known gaps to turn into requirements:**
- V367: P0 hides full 9 m/s² ALKS braking from 1-Hz metrics. Braking must be measured at step resolution; a b7 step metric exists in round 2.
- V283: check what a count measures (short gaps were stopped queues).
- V387: inputs were not normalised until revision 4.
- Validation is against published ranges, not a field site (V245). Claude proposed one empirical sanity comparison with MnDOT detector data (Mayfly, no account): a comparison, not a calibration.

## 7. Article 1 and the method chapter: material

- Protocols: `docs/research/protocols/` (confirmatory 1-3, 3b, round 1, round 2, reviews).
- Statistics: paired seeds, median of paired differences, percentile bootstrap, Bonferroni; seed blocks pre-approved.
- Lessons: `docs/lessons_metric_gameability.md` on the archive branches; memories on metric traps.

## 8. Suggested first steps

1. Ask for the effort switch; resolve the LaTeX choice and the template.
2. Thesis outline v1 and the claim statement, replacing roadmap v0.
3. Draft the plant requirements list, mapped to existing evidence and gaps.
4. Article 1 skeleton: sections and the figure and table list, each tied to a stored result.

Record every author decision as the next V# in `docs/decisions.md` and commit it the same turn. 3c also appends V entries, so check the last number before writing.
