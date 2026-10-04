# Lead 1, T1-M2: incident-aware hybrid metering with varied severity and duration, pre-registration

*Committed 2026-10-03, before any run.*
- **Author decisions:** "both leads in parallel"; seed block **7,170,000–7,170,999** approved, with roles 000–099 scan, 100–299 tuning, 300–499 validation, 500–699 test, 700–999 reserved confirmatory.
- **Builds on** the R6 claim (`t1_meter_r6.md`).

**Why.** The R6 controller is still 5.8 % behind the oracle, and it chooses among 4 fixed settings tuned for 4 fixed event types. Real events vary in severity and duration. Fixed detector thresholds and fixed lookup settings should degrade there, while a policy with memory need not.

## Stage S: headroom scan (seeds 7,170,000–7,170,009)

**Plant:** BN4 at q = 1,600 (as in T1-M), 10 % uncontrolled AVs. Metric: door-to-door time.

**22 conditions** (per-seed start time from rng(seed + 991)):

| Kind | Variants |
|---|---|
| `none` | — |
| `slow` | v ∈ {3, 5, 8} m/s × duration ∈ {150, 300, 600} s |
| `block` | duration ∈ {60, 180, 360} s |
| `surge` | factor ∈ {1.15, 1.3, 1.5} × duration ∈ {150, 300, 600} s |

**Controllers (22):** `nc`, `meter:K:n` for K ∈ {5, 10, 20, 40} and n ∈ {4, 6, 8, 10, 12}, and `evsched:7:20:1.15` (the T1-M tuning, not re-tuned).
**Runs:** 4,840.

**Measures:**
- **G (all 22 conditions)** = (J of the pooled best fixed setting − mean of the per-condition best fixed J) / J pooled. Also reported per kind.
- **H_pre** = the same lookup against the best of {pooled fixed, `evsched`}. This is preliminary, because `evsched` is not re-tuned on this mix.

**Rule:**
- **G ≥ 10 % and H_pre ≥ 10 %:** go to stage H, pre-registered then. It will have a re-tuned `evsched`, an MPC-F refit on this mix (tuning seeds 7,170,100–7,170,299), and gate seeds.
- **Otherwise:** Lead 1 stops. G is biased upwards, so this is a conservative stop.

## Addendum A: stage H pre-registration (committed 2026-10-03, before any stage-H run)

### A.1 Correction to stage S (found after the scan, before stage H)

**The 360 s blockage is a plant artefact.** `block_d360` produced teleports (H-R3) in **209 of 220** scan runs, whatever the controller. SUMO teleports vehicles that wait behind the stopped vehicle for longer than the teleport time. This breaks the binding T1 criterion "no teleport artefacts", so the condition is **excluded from stage H onwards** (21 conditions).

Stage S recomputed on the same scan data; both outcomes logged:

| condition set | G | H_pre | pooled best |
|---|---|---|---|
| 22 (as pre-registered and reported) | 12.0 % | 12.0 % | `meter:5:10` |
| 21 (`block_d360` excluded) | 12.2 % | 12.2 % | `meter:5:10` |
| 21, FAIL runs dropped | 11.9 % | 11.9 % | `meter:5:10` |
| 18 (all blockages excluded) | 11.8 % | 11.8 % | `meter:5:10` |

**The stage-S decision does not change.** The family lookup changes in one entry: blockage → `meter:40:8` (it was `meter:5:10` with `block_d360` included).

**Smoke test, disclosed:** throw-away seed 7,170,099 (scan-role range) was used once for one `evsched2` run and one MPC-F2 data episode. It is not used in any analysis.

### A.2 Frozen inputs

- **`docs/lab/t1_meter2_lookup.json`,** sha256 `abd3b253…c440`, built from the scan seeds 7,170,000–009 only:
  - action set **A6** = {meter off, `meter:10:8`, `meter:40:8`, `meter:20:12`, `meter:5:10`, `meter:10:12`};
  - family lookup = {none: 10:8, slow: 40:8, block: 40:8, surge: 5:10};
  - pooled best fixed = `meter:5:10`;
  - per-condition oracle **I** (best of the full 21-setting grid);
  - per-condition oracle restricted to A6, **I_A6**.
- **Plant and metric:** as in stage S. BN4 at q = 1,600; the metric is door-to-door time, with served vehicles co-reported.

### A.3 Rival 1: `evsched2` (tuned non-learning adaptive scheduler)

- The T1-M event scheduler (slow / block / surge detectors), mapping a detected state to the A6 family lookup above.
- **Tuning grid:** v_slow ∈ {5, 7, 9} m/s × t_block ∈ {10, 20, 40} s × f_surge ∈ {1.15, 1.25, 1.35} (27 configurations).
- **Tuning seeds:** 7,170,100–119 × 21 conditions (11,340 runs).
- **Selection:** the minimum over conditions of the mean of the per-condition median J. The result is frozen to `docs/lab/t1_meter2_evsched2.json`.

### A.4 Rival 2: MPC-F2 (MPC with a model fitted on separate seeds)

- Same method as MPC-F (`t1_meter_gscan_protocol.md`, Addenda D/D2), with these changes:
  - the **A6** action set (meter off allowed);
  - data from the 21-condition mix;
  - q = 1,600.
- **Data:** seeds 7,170,120–219 × 21 conditions × 2 episodes. Random 300 s holds give about 8,400 samples.
- **Fit:**
  - MLP 2 × 64 tanh;
  - 80/20 split by (condition, seed) group;
  - early stop.
- **Frozen model:** `docs/lab/t1_mpcf2_model.pt` with a fit report.
- **Never given:** the true model or the condition.

### A.5 Gate H2 (run once)

- **Seeds:** gate seeds **7,170,220–239** (20) × 21 conditions.
- **Arms:**

| arm | what it is |
|---|---|
| `nc` | no control |
| `pooled` | `meter:5:10` |
| `evsched2` | tuned (A.3) |
| `mpcf2` | fitted-model MPC (A.4) |
| `evsched_old` | T1-M tuning and lookup |
| `mpcf_old` | R6-frozen MPC-F |
| `I` | per-condition oracle |
| `IA6` | per-condition oracle restricted to A6 |
| `family` | family oracle with the true family; informative only |

- **Per-seed score:** J_s = the mean over the 21 conditions of door-to-door time.
- **B** = the arm with the lowest median J_s among {`nc`, `pooled`, `evsched2`, `mpcf2`, `evsched_old`, `mpcf_old`}.
- **H** = median_s(J_B − J_I) / median_s(J_B). The CI is a 95 % percentile bootstrap of the median paired difference (10,000 resamples).
- **Rule:**
  - **GO** to DRL if H ≥ 10 % **and** the CI lower bound is > 0;
  - otherwise Lead 1 stops (KILL), and that is logged.
  - H_A6 (oracle restricted to A6) and per-family H are reported as secondary, informative only, and do not change the rule.
- FAIL runs stay in the metric and are counted per arm.

### A.6 Prior expectation (written before any stage-H run)

**On the scan data,** the family oracle (true family, family lookup) is only **4.1 %** behind I. So most of the 12 % comes from telling slowdowns apart from the rest, not from severity or duration.

**What this predicts:**
- If `evsched2` or MPC-F2 detects the family reliably, H falls below 10 %, which is a KILL.
- In T1-M, detection lag left `evsched` about 9 % behind its lookup.
- A GO is therefore plausible but not likely. Expected H ≈ 4–13 %.

### A.7 If GO

- The DRL stage (RecurrentPPO hybrid over A6, with meter off allowed) will be pre-registered in Addendum B before training.
- **Seeds:** validation 7,170,300–499, test 500–699, reserved confirmatory 700–999.
- **Open item, needs the author's decision:** the training-seed pool. The T1-M learners already used 7,210,000–7,219,999 for training.
