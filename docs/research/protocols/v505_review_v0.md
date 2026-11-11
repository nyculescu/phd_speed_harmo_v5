# Review of the V505 drafts v0, and how v1 handles each finding

Reviewers (2026-11-10): five lenses. Statistics, fairness and plant ran on Fable; build and rules ran on Opus. Each serious finding then went to its own skeptic. 56 findings: 7 blockers, 30 majors, 19 minors. Of the 37 blockers and majors, the skeptics confirmed 17, confirmed 20 in part, and refuted none. Raw texts are in the session scratchpad. Numbers quoted are the reviewers' recounts from the S6 rows.

| # | Finding (lens) | Verdict | v1 handling |
|---|---|---|---|
| 1 | M2's HOLDS bands for the interaction are out of reach at n = 240: CI half-width of I about 2 points for S delay and 9 for TRUCK close-following, against bands of ±1 and ±5 (stats, build, fairness, rules) | confirmed | Each conclusion is now re-read on the variant with its own recorded criterion (edge: lower bound > 0; tie: CI includes 0). I is report-only (M2 §4) |
| 2 | Identical rows on a third of S seeds (p333 = os0_10_10, lr1000_16_2) make CIs zero-width (stats, fairness) | partly | C4 is report-only. A zero-width CI is "not readable". Tie shares are printed (common §4) |
| 3 | A V-A set at departure is reset by `VTYPE_TUNE` (fleet.py:157, :179), and a whole-trip value changes every later lane change (build, plant) | confirmed | V-A is set at insertion after the type settings and reset to 1.4 off `4a_0`. Read-back is checked on 4a_0 and downstream (M2 §2, §7) |
| 4 | The pick has no hard-braking bound (plant) | partly | Step braking and an ALKS emergency-decel bound are added (M2 §2) |
| 5 | The pick needs pack-only fields, and its drain test is undefined in S (build) | confirmed | Pick runs use the pack; drain is variant minus base (M2 §2) |
| 6 | The variant is picked in S only, and may not bind in TRUCK or X1 (fairness, rules) | confirmed | Per-cell binding check on the verdict runs: VARIANT DID NOT BIND (M2 §4) |
| 7 | The 75 % bar ignores the load asymmetry (85 % against 70 %); the ratio was misquoted (plant) | partly | §1 states the load and the true ratio (26 times). A 50 % fallback with a "partial variant" label; the merge-1 reference at matched load is printed (M2 §1, §2) |
| 8 | Closed cells: the amendment wording is missing; V503 and X2 are not cited; the cell count is silent (fairness, rules) | partly | Amendment wording to approve; X2's exclusion stated; D7 on the count (M2 §0) |
| 9 | D4 reuses Plan B's "used once" seeds outside V505's block; "not re-read" is false; cross-machine identity for torch is unproven (build, rules) | confirmed | Cons listed; wording fixed; v3w identity replays first, with a fixed fallback to fresh seeds 7,488,760-999 (M2 §0, §6) |
| 10 | Conclusions missing: X1 close-following, TRUCK rule provenance (fairness) | partly | C5b added; C6 is report-only (M2 §3) |
| 11 | No consequence for UNCLEAR, VOID, mixed outcomes or a failed X1 replication; withdraw is not symmetric (rules) | partly | Consequence table split into edges and ties, with every outcome (M2 §5) |
| 12 | The V&V status wording overclaims ("located", "robust") (plant) | partly | Exact status text and the limit L-n; PR-28 stays open under V462 (M2 §5) |
| 13 | Both events are probably too weak for the gate (TRUCK passes only just; H1 failed G1a; 40 km/h on edge 2 forms no queue) (plant) | confirmed | One event, sized on throw-away seeds to a cost of at least 15 % of S, then a 40-seed gate (EV §2) |
| 14 | EV-B rides past merge 2 (lane-end confound), and its effect is cut off by the window end (plant, rules) | confirmed | EV-B dropped; the location rule now applies to KILL as well as GAIN (EV §0, common §6) |
| 15 | `_hw_level` takes the minimum: IP can only lengthen, and 0.8 s was missing (build) | confirmed | Override with L including 0.8; T0 rewritten on the commanded-level condition and the `tau_rise` timing (EV §3, §8) |
| 16 | ASCH's grid was miscounted, with no steady rule or switched rule named (build) | confirmed | Steady p333; switched rule from {3E-T, 3E-C_TRUCK, 3E-D_TRUCK}; 55 configurations (EV §3) |
| 17 | SW is not the untold twin of IP on the FX base (fairness) | partly | SW (a) is LocalRule on the FX base with IP's L grid (EV §3) |
| 18 | "Best U" undefined: picking it on evaluation rows is a forking path (stats, rules) | partly | bU frozen on the tuning seeds (EV §3) |
| 19 | The null was run only against N (stats, fairness) | confirmed | A null for each of N, FX and SW (EV §5) |
| 20 | 40 tuning seeds give a noisy pick that favours a false KILL; "upper limit" overclaims (stats, rules) | partly | 60 tuning seeds; IP picked on the paired difference against its base; a power rule extends to 100; "lower bound" wording; KILL narrowed (EV §1, §3, §5) |
| 21 | E3's reason was wrong (D2's 10 % was of total delay) (fairness) | partly | Reasons rewritten; the KILL sentence states the gain it does not exclude (EV §0, §5) |
| 22 | The T4-style line always passes (stats) | partly | Dropped |
| 23 | Missing: a deviations, bug, crash and budget section; a cap action; operating rules (rules, build) | confirmed | common §7-§8 |
| 24 | Served flow `passed` and TTT `N` were not named (rules) | confirmed | common §3 |
| 25 | Costs mixed two machine classes and left out rental overhead (build) | confirmed | Ranges per class, the preferred host, a cap action, stage order (common §2, §7) |
| 26 | The M2-to-EV link was inconsistent; the location share was not V482's (rules, fairness) | confirmed | One rule in common §6, quoted by both |
| 27 | Build hours underestimated (build) | minor | Re-estimated: M2 10-14 h, EV 12-16 h (common §7) |
| 28 | Dense text; undefined names; §0 lacked a Cons column (rules) | minor | Glossary in common §1; Pros and Cons columns in every §0 |

Row 1 merged four findings: one confirmed (rules) and three partly confirmed (stats, fairness, build). Round-1 minors not listed above:
- fairness [8], MPC-F: v2 gives an exclusion reason that does not also apply to the 3E rules.
- rules [10](6), the per-type plan: v2 names IP as V506's per-type plan.
- plant [5], the dose check: dropped for simplicity (M2 §2).
- stats [8], raising evaluation n on a high spread: v2 makes it the second step of the power rule.
- rules [9], scope: answered by V507(3).
- The other minors are wording, and v2 takes them.

## Round 2 (v1 checked by three agents; 32 findings: 2 blockers, 21 majors, 9 minors), handled in v2

| # | Finding | v2 handling |
|---|---|---|
| R1 | v1's v3w statistic was not read6's, so M2 §3's base values were not the recorded ones. C3 is recorded as −1.57 [−2.70, −0.24] | read6's statistic exactly (common §4); M2 §3 filled from `read6_v23.json`; readings use Plan B's components (better / harm / neither) |
| R2 | M2's null swapped base and variant, which fails by construction for an edge and tests only the report-only I | read6's swap null on v3w and opponent labels, on the variant rows (M2 §4) |
| R3 | Tie SAME as "CI includes 0" is lenient; edges and ties move apart under noise | NOT RESOLVABLE when the variant's half-width is over 1.5 × the base's; the detectable shift is printed; power at 1-point and 5-point shifts stated (M2 §4) |
| R4 | The consequences put variant values beside recorded results, against the amendment; withdraw was dropped silently | labels only beside results, values only in the V&V record; D8 asks about withdraw (M2 §0, §5) |
| R5 | The binding check was weaker than the pick and skipped the deciding arms | every deciding arm plus no control, at the pick's bar, by the paired-ratio upper bound (M2 §4) |
| R6 | The braking bound had a 40 % false-fail rate; the emergency bound had no usable key | paired mean ratio with a CI; `alks_full_moving` in absolute terms; pick at n = 60; false-fail rate printed (M2 §2) |
| R7 | The V-A wording reset at insertion; read-back skipped 4a_1-3 | departure-time set in the step hook, reset after leaving 4a_0, 1-s lag disclosed, read-back on 4a_1-3 (M2 §2, §7) |
| R8 | D6 was decided silently; the Xeon cap analysis was wrong; host vs V488's offer rule | D6 and H1 restored as decisions (common §0); Xeon above the cap goes to the author; tuning and evaluation are one cap stage (common §7) |
| R9 | EV sized its event on p333 results, against V456(3) | sizing on no control only; p333 printed, not used; M2's pick disclosure added |
| R10 | The expected KILL was not stated; the IP build came before the gate | §1 states it and why; build split so the gate runs before part 2 (common §2) |
| R11 | Asymmetric pick statistics favoured IP; SW (a) lacked IP's hold | paired picks for every family with a shared base; SW (a) has the `after` hold (EV §3) |
| R12 | A "no switch" pick had no outcome | KILL BY PICK (EV §5) |
| R13 | The KILL location rule could not fire | G recomputed off merge 2; the repeat includes S runs; V-A must bind in the EV cell; outcomes when the repeat fails (common §6) |
| R14 | The power rule was not computable | the model is fixed; two extension steps, then "KILL, underpowered" (EV §5) |
| R15 | KILL consequence broader than the test; MPC-F reason; the per-type plan | narrowed to this event; reason fixed; IP named as the per-type plan (EV §1, §3, §6) |
| R16 | Counts (610; extension size; fallback missing from totals) | recounted in common §7 |
| R17 | Deviations weaker than planb §11; drop undefined | common §4, §8 |
| R18 | Undefined names; 3e and 3E-T | glossary extended (common §1) |
