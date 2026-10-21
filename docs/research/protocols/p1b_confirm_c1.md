# P1b confirmation C1: does the type plan beat always-on PI in block_q1600?

Status: **DRAFT (V114), awaiting the author's approval of the statement and the seeds.** It is run once, from a frozen worktree.

**Why.** P1b found, in a report-only row, that in cell block_q1600 the per-type plan IP beats tuned always-on PI by 18.0 % [8.9, 31.6] (`p1b_result.md`). A report-only row is not a claim. C1 tests it once, on fresh seeds, with the statement fixed here.

## Fixed before data

- **Plant, incident and meter:** exactly as P1b (`p1b_addendum.md`, V108, commit `93ba655`): BN4, q = 1600 veh/h, the block incident (onset and duration drawn per seed as in P1), the amber meter, runner share s = 0.
- **Arms:** frozen from P1b's tuning, with **no re-tuning**.
  - **IP:** N = `c1800` before onset; at onset, switch to `p20_20_16_e4` (stay).
  - **PI:** `p70_120_8_e4`, always on.
  - Reference rows (report only): N `c1800` throughout, and NC.
- **Seeds:** **7,400,700–799** (100 seeds), from the approved v5.B block's reserved confirmatory range (700–999). They are unused so far, and this needs the author's approval. No replicates; smoke runs only on 7,400,000–009.
- **Metric:** door-to-door delay including the meter queue, as in P1/P1b. Paired by seed.

## Statement C1 (the only claim)

Let rel = median(PI − IP) / median(PI) over the seeds, in the paired-median convention of P1.

- **CONFIRMED** iff rel ≥ 10 % **and** the lower bound of the two-sided 95 % percentile bootstrap CI of median(PI − IP) is > 0 (B = 20,000; bootstrap seed fixed in code before data).
- It must hold in **both views** (all seeds; and seeds with no invalid IP or PI run removed).
- **NOT CONFIRMED** otherwise.

It is a single test, so there is no multiplicity correction.

## Reported, descriptive (no claims)

- IP vs PI with detection delay d ∈ {30, 60, 120} s.
- IP vs PI with runner share s ∈ {10 %, 30 %}.
- Emergency stops, max queue, the recomputed spill share (V109 definition), and collisions.

## Integrity

- Code is committed before any C1 seed is run. A sentinel `P1B_C1_STARTED.json` makes it run once; resume only at the same commit.
- **Disclosure:** the cell and the arms were chosen *after* seeing P1b's evaluation data. That is exactly why C1 uses fresh seeds and a single pre-fixed statement.
- **If NOT CONFIRMED,** the paper reports the P1b row as descriptive only.

**Cost (estimate):** about (2 arms + 2 reference) × 100 seeds + the descriptive rows ≈ 1,000 runs, a few minutes at 32 workers.
