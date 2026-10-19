# P1 protocol: how much incident information does ramp metering need?

Status: **DRAFT (V98), awaiting design review and author approval.** No evaluation seed is run before approval. Claim bar: set by the author and Claude (V95), fixed here before data.

**Paper question.** During non-recurring incidents at a freeway bottleneck, how much of the attainable delay reduction from ramp metering needs incident information, and how much?
- **L0, none:** strong always-on control.
- **L1, incident type** (and its start and end): a stored plan per type, with switch-back.
- **L2, full per-incident information** (type, onset, duration): a hindsight bound, bracketed honestly.

Also: how robust is the L1 gain to real detection imperfections?

**Prior art** (`docs/research/prior_art_P1_P2.md`): incident-responsive metering exists (Sheu & Chang 2007; Dabiri & Kulcsár 2014; Wu et al. 2014; Gao & Xu 2026; FHWA plans). This paper claims no new mechanism. It contributes:
- the information decomposition;
- honest headroom bounds (selection on noise; Cameron et al. 2016, van Hasselt 2010);
- the imperfection map.

The term "event-triggered" is not used.

## 1. Plants

- **Plant A:** BN4 single merge, as ported for D1/D2 (`v5b/d1`, `v5b/d2`, commit `72ba8f2`), q ∈ {1600, 2000} veh/h.
- **Incidents:** as in screen D2, including Addendum A2.
  - **slow:** bottleneck speed limit 5 m/s;
  - **block:** lane 4_1 crawls at 1.0 m/s, because lane changing is off (disclosed);
  - **onset:** uniform in the first third of the 900-s control period;
  - **duration:** uniform 120–480 s.
- **Plant B (second geometry, optional):** a plant from the archive with a different merge geometry, e.g. MRG3 (`claude/vsl-lab-core` @ `2a79e5e`, `vsl_lab/netgen/mrg3.py`).
  - It enters **only** if it passes the same tool checks (§3).
  - Otherwise it is dropped and disclosed. Plant A alone answers the paper.

## 2. Arms by information level

| Level | Arm | Definition |
|---|---|---|
| L0 | **N** | Best of family G on no-incident tuning runs (as D2) |
| L0 | **FX** | Best constant rate, tuned on the incident mix |
| L0 | **FB** | Best feedback meter (K_F, n_crit grid of D2), tuned on the incident mix |
| L0 | **AD** | Feedback meter with an online-estimated set point (AD-ALINEA style: critical count re-estimated from measured flow and count). Its parameters are tuned on the incident mix |
| L1 | **IP** | At onset, the per-type best action of G × {stay, back}, tuned on tuning seeds (as D2 + A12) |
| L2 | **OR_in** | Per seed, the best action on the same run: an **upper bound**, inflated by selection on noise |
| L2 | **ORX_R** | Per seed, the action chosen on the mean of R independent replicate runs (R ∈ {1, 2, 4, 8}), scored on the main run. R = 1 is a **lower bound** (double estimator); a rising R shows convergence |
| ref | **NC** | No meter; reference only |

- **"Best L0"** is the L0 arm with the lowest median delay on the **tuning** seeds, per cell. It is fixed before evaluation.
- **Family G:** as in D2. The constant-rate grid is 600, 800, 1000–2600 step 100; feedback is K_F ∈ {10, 20, 40, 70} × n_crit ∈ {6, 8, 10, 12}. Actions are G × {stay, back}.
- **Grid edges:** if a tuned choice lies at a grid edge, the run HALTs before evaluation (extend the grid; disclosed).

## 3. Tool checks (on the tool-check seeds, before tuning)

| Check | What it requires | If it fails |
|---|---|---|
| T0 | The best arm beats NC by ≥ 10 % in every incident cell (median paired difference, CI > 0) | STOP |
| T1 | Teleports occur in < 5 % of runs per cell | fix with a test, then repeat |
| T3 | The same seed twice gives identical results | fix, then repeat |
| T4 | The incident changes the best fixed controller by ≥ 10 % in every incident cell (as D2-A5) | STOP |
| **TV** (VSL, V98) | Posted VSL on all gantries during the incident, b ∈ {0.8, 0.6, 0.4}, from onset to clearance. Tested alone (vs NC) and on top of IP (vs IP) | **VSL enters** if either beats its reference by ≥ 10 % (median paired, CI > 0) in at least 1 incident cell: VSL arms join L1 (IP+VSL) and L2. Otherwise one negative row |
| **TP** (placebo) | The same controller (IP) run under K = 8 SUMO seeds per scenario. The in-sample "oracle" over these K copies measures **pure-noise inflation** | report only; sets the noise floor |

## 4. Imperfection map (L1 robustness; report-only rows with CIs)

All imperfections apply to IP. Each is varied one at a time; all others are perfect.

- **Detection delay:** {0, 30, 60, 120} s.
- **Clearance detection delay:** {0, 60, 180} s, plus "never switch back".
- **Misclassification:** the incident type is swapped with probability p ∈ {0, 0.2, 0.5}.
- **False alarms:** in no-incident runs, a plan switch is triggered at a random time for a typical duration (240 s), with a probability per run ∈ {0, 0.25, 0.5}.

For each, report IP − best L0 and the **break-even level** (where IP stops beating the best L0).

## 5. Metrics and statistics

- **Primary:** door-to-door delay including the ramp queue. Served throughput is co-headlined; TTT is reported alongside.
- **Statistics:** paired seeds; median of paired differences; 95 % percentile bootstrap, B = 2,000.
- **Bonferroni** over the claim cells: incident type × demand × plant (4, or 8 with plant B).
- **Invalid runs:** results must hold with seeds that have invalid runs removed.

## 6. Pre-registered statements (what the paper may say)

- **S1, type information pays:** IP beats the best L0 by ≥ 10 % (Bonferroni CI lower bound > 0) in ≥ 1 cell, and is never worse than the best L0 by > 5 % in any cell. Otherwise: **"type information does not pay beyond strong always-on control"** (also reported as a finding).
- **S2, the value of per-incident information:** report the bracket [ORX_1, OR_in] relative to IP, plus ORX_R for R = 2, 4, 8 and the placebo floor (TP).
  - "Per-incident information adds at most x %" may be said only if OR_in − TP floor < x with a CI.
  - Otherwise only the bracket is stated.
- **S3, robustness:** the break-even detection delay, misclassification rate and false-alarm rate, with CIs.
- **No novelty claims.** Every other number is descriptive.

## 7. Seeds (from the approved v5.B block; need the author's approval)

| Use | Seeds |
|---|---|
| Tool checks | 7,400,700–719 |
| Tuning | 7,400,200–239 |
| Evaluation | 7,400,500–599 (100 seeds) |
| Replicates (derived SUMO RNG seeds) | evaluation seed + k × 10,000,000, k = 1–8 |
| Placebo | uses the replicates |
| Smoke and build runs only | 7,400,000–009 |

## 8. Operation and integrity

- **Machine:** 32 workers, CPU guard at 90 % (V93), its own systemd unit. The pad and fans are handled per the author's current instruction.
- **Code and tests** are committed before any tool-check seed is run. A global run-once sentinel guards the evaluation. Resume only at the same commit.
- **Disclosures:**
  - screens D1 and D2 and their numbers were seen;
  - the D2 tuning and evaluation seeds are not reused;
  - the block substitute;
  - no amber at the meter;
  - VSL's archived failure on BN4.
- **Estimated cost:**
  - author 0.5 h;
  - build about 1–2 days (AD arm, replicates R ≤ 8, imperfection layer, VSL check, placebo, plant B check);
  - compute about 2–4 h at 32 workers (estimate).
