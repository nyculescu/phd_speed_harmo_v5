# paper_1 v2 plan: C1 + C2 with exploit-first gates (V153, draft for author approval)

**Author decision (2026-10-21):**
- C1 + C2 are paper_1.
- "We must be sure we have a good chance of innovation."
- "Stay close to others' setups so that we can reproduce their results, and we come with the improvements."
- "Use smart gates that limit our exploration and focus on what we can exploit, to get results as soon as possible."

**Working title:** *Does the capacity drop decide the headroom of bottleneck control? A calibrated replication of mixed-autonomy RL against tuned feedback metering.*

- **C2 (replication + improvement).** Reproduce Vinitsky et al. 2023 (ACM TCPS, doi 10.1145/3582576; arXiv 2011.00120; open code github.com/eugenevinitsky/decentralized_bottlenecks) on its own setup:
  - the BN4 Bay-Bridge 4→2→1 bottleneck;
  - IDM humans with lane changes off;
  - multi-agent RL AVs at 5-40 % penetration;
  - an ALINEA traffic-light baseline.

  Then re-run the comparison on a calibrated plant, with tuned feedback opponents and fair statistics.
- **C1 (operating map).** The gain of tuned ALINEA / PI-ALINEA and RL as a function of the calibrated capacity-drop size Δ, on the same geometry, with paired confidence intervals.

## 1. Exploit first: assets that already exist

| Asset | Where | Use |
|---|---|---|
| BN4 geometry = Flow geometry | `v5b/d1/netgen_bn4.py`, `v5b/p1c/plant.py` (`bn4`) | Same network as the target paper |
| Flow IDM humans, lane changes off | `v5b/d1/plant.py` (Flow parameters) | The target paper's driver setting |
| Calibrated BN4-LC plant (Krauss, zipper 100 m, drop 5-8 %) | `v5b/p1c/` (V139, V147) | The "realistic" end of the map |
| **Measured Δ on BN4 for 54 configurations: 2.5 % to 54 %** | `docs/research/results/p1c_calibration_stage1.json` | The Δ levels for C1, with no new plant search |
| Tuned constant, ALINEA, PI-ALINEA on the release-tracking actuator (T0 PASS) | `v5b/p1c/meter.py`, `feedback_t1g.py` | Fair opponents |
| Gate tools (drop, QDF, artefacts, forced stops, determinism) | `v5b/p1c/calibrate.py`, `t1checks.py` | Plant checks at every Δ level |
| Unused seeds | V135 block: 7,430,040-049 (calibration), 100-149 (checks), 200-999 (tuning, validation, evaluation, confirmatory) | Fresh seeds, no new approval needed |

## 2. Exploration limits (from the ledger)

| Rule | Lesson | Source |
|---|---|---|
| E1 | **Reproduce before improving.** No new method or plant until the target paper's numbers are reproduced on its own setup (G1) | author, V153 |
| E2 | **Closed plant list.** Only (a) BN4-Flow (the target setup) and (b) BN4 at the Δ levels already measured in V139. No new geometry, merge type or driver model; any change needs an author V-entry | V59 realism rule; WZ cost V141-V145 |
| E3 | **Closed knob list.** The Δ levels come from existing V139 configurations. At most one extra knob (zipper visibility) if a gap in Δ must be filled; never more than 6 settings in total | V59 |
| E4 | **Time box and run budget per gate,** fixed below. A gate that runs over its box stops and reports | V80 screens |
| E5 | **Gates are pass/fail with numbers fixed before data,** on fresh seeds, from frozen code, run once | CLAUDE.md, V138 |
| E6 | **Fair opponents.** Tuned ALINEA / PI-ALINEA with grid adequacy (one-step extension), a pre-registered tuning rule, delay including origin queues, paired seeds | audit CTRL-F1/F2, V148 |
| E7 | **Known implementation traps are checked first:** actuator delivers the command (T0); drain with control on; breakdown detector outside the merge zone; run scripts via bash on exFAT; never commit inside a frozen copy | V140, V143, V142, memory |
| E8 | **DRL budget only after a GO** (CLAUDE.md): ≥ 500 PPO updates, 3-5 training seeds, checkpoint chosen on validation seeds | CLAUDE.md |

## 3. Gates (in order; each with criteria, time box and budget)

```
 G0 novelty ─► G1 reproduce target ─► G2 Δ ladder ─► G3 classical map ─► G4 RL map ─► G5 confirm ─► paper
  (author,      (≤ 1 day build,        (≤ 2 h,         (≤ 4 h compute)    (≤ 2 days      (fresh
   WoS, 1 h)     ≤ 6 h compute)          existing data                      compute)       seeds)
                                         + ≤ 200 runs)
```

**G0 Novelty** (author with WoS / Scopus; Claude's web sweep found nothing, V152).
- **Search:**
  - "capacity drop" AND (magnitude OR size OR sensitivity) AND (metering OR "speed limit" OR ALINEA OR reinforcement), 2015-2026;
  - works citing doi 10.1145/3582576.
- **PASS:** no paper reports (i) control gain as a function of capacity-drop size for tuned feedback and RL, or (ii) a calibrated replication of the BN4 MARL result.
- **FAIL:** C1 or C2 already exists. Re-scope to the difference before any run.

**G1 Reproduce the target on its own setup** (C2, part 1).
- **Route A:** run the authors' code as published (their Flow fork, the RLlib/SUMO versions it pins), at most 1 day of build.
- **Route B,** if A cannot be built in time: port the environment exactly, using the same geometry, inflow, IDM parameters, lane changes off, AV fractions, observation, action and reward, into our SUMO 1.27 stack, and train with PPO (SB3).
- **PASS:** both hold, on fresh seeds:
  - uncontrolled outflow and ALINEA outflow match the paper's reported values within ±5 %;
  - RL at 5 % and 40 % penetration reaches the paper's reported outflow within ±10 %, with the paper's ordering kept: RL at 40 % ≈ ALINEA, RL > uncontrolled.
- **FAIL:** the target is not reproducible in our hands. This is reported as a finding, with the cause isolated (code, versions, settings), and C2 shrinks to that report.
- **Budget:** ≤ 6 h of training compute.

**G2 Δ ladder** (C1 plant levels; mostly existing data).
- Choose 4-5 BN4 configurations from V139 that span Δ from about 3 % to about 20 %, plus the Flow-IDM reference (about 50 %). Each must pass T1b (QDF in range) and T1c (no artefacts).
- Verify the Δ of each on fresh check seeds (7,430,100-119; 20 ramp runs per level; ≤ 120 runs).
- **PASS:** at least 4 levels with distinct median Δ (non-overlapping 95 % CIs) inside [2, 20] %, each with QDF in range and 0 artefacts.
- **If a gap remains:** one extra knob, zipper visibility, on calibration seeds 040-049, at most 6 settings (E3).

**G3 Classical operating map** (C1, part 1).
- **Arms:** no control, tuned constant, tuned ALINEA, tuned PI-ALINEA (the T1g grids with the adequacy rule).
- **Conditions:** each Δ level, near-capacity demand and one incident type (slowdown).
- **Seeds:** tune on 200-219, evaluate on 600-639 (40 paired seeds).
- **Report** per Δ: rel gain vs no control with 95 % paired CIs; window TTT; throughput. The pre-registered prediction is that headroom grows with Δ.
- **This is a mapping result, not a pass/fail claim.** The gate passes when the map is complete and every run is valid.

**G4 RL map** (C1, part 2, and C2, part 2).
- The G1 RL setup retrained at three Δ levels (low, middle, Flow-reference), at penetrations 10 % and 40 %, with 3 training seeds each (E8). Checkpoints are chosen on validation seeds 400-419; evaluation on 600-639, paired with G3.
- Lane changes are on in the calibrated levels, as on the realistic plant.
- **Report:** RL vs no control, and RL vs tuned ALINEA, per Δ.
- **Pre-registered statements** (fixed before G4 data):
  - (S1) at the calibrated Δ, the RL vs tuned-ALINEA difference has a CI that includes 0 or favours ALINEA;
  - (S2) the RL gain over no control shrinks with Δ.

**G5 Confirmation** on reserved seeds 800-899, for the two headline cells only: the calibrated-Δ RL vs ALINEA, and the Flow-reference RL vs ALINEA.

## 4. What counts as the innovation (if G0 passes)

1. The first **calibrated replication** of a widely cited mixed-autonomy RL bottleneck result, against **tuned** feedback metering.
2. The **operating map of headroom against capacity-drop size**, for learned and classical bottleneck control: a reusable answer to "how much can control gain here?" before anyone trains RL.
3. A **realism gate** (Δ, QDF, artefacts, actuator) others can apply, packaged with the code (the C6 benchmark seed).

## 5. Decisions needed

1. Approve the gates, criteria, time boxes and the closed plant and knob lists (E1-E8).
2. Run G0 (Web of Science / Scopus), or tell Claude to rely on the open-web check.
3. G1 route: try A (the authors' code) first, with B as the fallback (recommended).
