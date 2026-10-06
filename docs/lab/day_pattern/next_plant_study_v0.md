# Next plant after the METANET v3 route stop: design study (v0, 2026-10-06)

**Status:** a study for the author's decision, not a protocol. Nothing here is binding until a protocol is committed. It was produced by a multi-agent design study: 4 independent analyses (METANET numerics, geometry and observation, SUMO route, integrity), a judge and a completeness critic. Their full outputs are in the session scratchpad (`design_study.json`) and the workflow journal `wf_53592a04-e30`. The claims marked **[checked]** were re-derived by the main session; everything else rests on the agents' analyses and is unverified.

Context: the METANET v3 plant stopped at the gated step-halving check (D4.1; `metanet_calibration.md`). No validation day was simulated.

## 1. What we learned about v3 (why it failed)

1. **The 5-s time step was numerically unstable for this model.** v3's build checks covered the speed-based CFL condition and τ ≥ 2T. They did not cover the anticipation term, which acts like diffusion with coefficient up to ν.
   - **[checked]** The diffusion number ν·T/L_min² is 1.01 at T = 5 s with ν at its upper bound, and 0.61 at the fitted ν. Both exceed the usual 0.5 limit for explicit diffusion. At T = 2.5 s it is 0.50 / 0.31; at T = 1.25 s, 0.25 / 0.15; at T = 1.0 s, 0.20 / 0.12 (L_min = 352 m).
   - A frozen-coefficient stability scan by the numerics analysis finds spurious explicit-Euler growth at 5 s and 2.5 s, and none at T ≤ 1.25 s for cells ≥ 319 m. The step-halving check caught a real defect.
2. **v3's "B1 agreement 22/22" was an artefact of the speed–density curve, not a queue.**
   - **[checked]** All 8 restarts put G2's speed at capacity at 46.5–48.1 km/h, with a2 between 1.00 and 1.06. The event threshold at S of Highwood Ave, converted to model scale, is 67.4 km/h (40 mph × c_s 1.047). So the model reads "< 40 mph" there in uncongested flow near capacity.
   - The geometry analysis reports that in 142 of 147 model P_1 episode bins (on 8 calibration days), no cell from 20 to 31 is above critical density.
3. **B2 is a knife edge on the deterministic plant.** Model B2 occurs on 2 of the 9 real-B2 calibration days at 5 s and on 3 at 2.5 s. **[checked]** In the capacity grid at c1 = 1, model B2 is active on 22/22 days at c2 = 0.90 and 2/22 at c2 = 1.00.
4. **Event stations sit inside bottleneck cells. [checked]** Pioneer Tr reads B1's last cell; Old Shakopee Rd reads B2's last cell (c2-scaled). Relocation branch (b) therefore fires almost everywhere at low c2.
5. **Relocation at c = 1 comes from the E15 merge cell (cell 33) on 6/22 days**, not from station placement. **[checked]** It depends on the unresolved lane geometry at E15–X15 (v3 A1(ii), step (b) substitute G4).

## 2. Options and the study's verdict

| Criterion (1–5, higher is better; the judge's scores) | METANET v4 | SUMO as gate plant |
|---|---|---|
| Time to a usable gate plant | 4 | 2 |
| Probability of passing an honest plant gate | 2.5 | 2 |
| Speed for DRL training | 5 | 1 |
| Integrity risk (higher = safer) | 2.5 | 3 |
| Merge / capacity-drop fidelity | 3 | 2.5 |
| Reuse of existing work | 4.5 | 2.5 |

**Judge:** METANET v4 as the gate plant, with P6b unchanged (SUMO stays the confirmation plant). It is framed as a new plant attempt after a pre-registered stop, not a rescue of v3.
- Estimate: about 3–5 weeks to a v4 plant verdict.
- The §4 compute at T = 1.0 s is extrapolated at about 13–18 h.
- SUMO as the gate plant is estimated at about 8–11 weeks to a validated full-day plant, at about 5–26 min per simulated full day.
- All of these figures are estimates, not measurements.

**Critic (it changes the recommendation):**
- **(a) A third option was not scored.** A two-capacity cell-transmission (CTM) plant was the plants document's own gate recommendation, and the gate draft needs a CTM anyway (the `mpc_f` opponent and the fallback cross-check).
- **(b) The main KILL risk comes later and is plant-independent.** The field drop is about 1.6 % (D3.1), and the v6 tuned ALINEA was about equal to no control. The headroom gate may KILL on any faithful plant. A **KILL-only screen of the size of the prize** on a fast, deliberately optimistic plant, run before the v4 compute, would bring that KILL forward. It must be pre-registered and needs author approval.
- **(c) SUMO's merge pre-check (S0) is on the critical path of every claim**, because P6b needs a SUMO confirmation. It should be pre-registered now and run when the machine is free.
- **(d) The proposed T rule must be a finite, pre-registered ladder** (e.g. T ∈ {1.25, 1.0, 0.75, 0.625, 0.5} s). A free T would be a degree of freedom.
- **(e) No seed room is left for v4 in 7,190,000–7,190,999** without eroding the gate's tuning, validation and test roles. A new block needs author approval.
- **(f) Some v4 changes mechanically ease v3 failure paths.** Head-only capacity scaling and moving stations out of scaled cells remove relocation branch (b) as a failure path and change how F̂ estimability works. They must be disclosed as such, or replaced by the minimal change (exclude only the station cells from scaling).

## 3. Draft METANET v4 change list (only if the author chooses v4)

1. **Numerics (§2.5).**
   - T comes from a pre-registered ladder by a data-free rule: ν_max·T/L_min² ≤ 0.25. That gives T = 1.0 s if L_min ≥ 317 m.
   - Step-halving runs at T/2, with the strict criterion unchanged.
   - New build checks against the bound maxima: the diffusion number, a wave Courant number, T ≤ τ_min/10, and merge-term stiffness < 1. A unit test runs a frozen-coefficient stability scan.
   - τ stays at 10–60 s, restated as a prior bound.
   - Each day's event decision margins are reported, ungated.
2. **Cells and stations (§1.4–1.5).**
   - Cell boundaries are fixed by lane changes and ramp gores, not by stations.
   - No event or fit station may read a capacity-scaled cell (a build check).
   - The bottleneck cell sets are re-specified by a data-free rule. Either head-only or the minimal exclusion of station cells; the critic prefers the minimal one. Its effect on relocation and F̂ is disclosed.
3. **Speed–density admissibility (§4.1).** Each group's speed at capacity must stay above its event threshold, otherwise J = 10. This is a fit-informed narrowing and is disclosed. The critic expects B1 may then FAIL honestly.
4. **E15–X15 lane check** from documents or imagery only (no traffic data), before the v4 commit. It reopens A1(ii).
5. **Seeds, paths and records.**
   - A new author-approved seed block and cold starts only (no warm start from v3).
   - New raw directory and `metanet_v4_*` records.
   - A sha256 manifest and git tag of the v3 evidence.
6. **Unchanged.**
   - The objective, the event rule and c_s, every gate threshold and minimum, the F̂ rules and the substitute.
   - The day split: the 22 calibration and 97 validation days. This is the single METANET look at these validation days.
   - 2024 stays unopened.

## 4. Integrity conditions (any route)

- Protocol, generated cell table and unit tests are committed before any v4 run. No validation-day model run before the v4 freeze.
- Exactly one configuration is committed. Any discrete choice has its candidates and selection rule pre-registered, and results read "selected from N".
- **Disclosure:** v4 was designed after seeing v3 calibration-day model output, including post-stop diagnostics. The v3 record's sentence that post-stop results "may not inform any … plant or protocol choice" needs an author ruling, e.g. a dated addendum that lifts it for v4 with this disclosure.
- Every downstream result states the number of plant attempts. If SUMO is used, it is labelled as designed after the METANET v3 results.
- The post-stop runs of 2026-10-06 are ledgered as report-only design input (done: rows `metanet-poststop`).

## 5. Open risks

- B2 occurrence may stay unreproducible on the deterministic plant.
- B1 may FAIL once the speed–density artefact is excluded.
- A near-tie day can still flip at step-halving: 20230517 has a count margin of 0 even at converged steps.
- The E15–X15 check may be inconclusive, which caps v4 at KILL-only.
- F̂ is likely "not estimable" at B2 under rule (iii).
- Compute at T ≤ 1 s is extrapolated, not measured.
- Even a passing plant faces a likely headroom KILL. Published hybrid gains are about 1.5–6 % [VERIFY], and the field drop here is about 1.6 %.

## 6. Not checked by anyone in this study

- No v4 variant was simulated, deliberately: such runs would themselves become design input.
- T = 1.0 s and 0.5 s were not simulated; only 2 of the 22 calibration days were probed at T ≤ 1.25 s.
- The SUMO cost figures are extrapolated from other networks.
- The E15–X15 lane count was not looked up.
- The literature conventions cited by the analyses (ramp-at-node placement, the HCM influence area, active-bottleneck definitions) are [VERIFY].
