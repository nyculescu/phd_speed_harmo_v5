# Baseline v5: Plan B, per-CAV DRL under a perturbation it was not trained on, 2026-11-10

Git tag `baseline-v5`. Decisions V478-V502. This baseline freezes the state after Plan B's evaluation (S6), its deciding reading (read6 v1) and the report supplement (read6 v2.3). It builds on baseline v3 (plant and method) and baseline v4 (the v3w policies). Any new direction, such as the DRL exploration briefed in `docs/handoff/2026-11-10_fable_drl_exploration_prompt.md`, compares with this baseline.

## What is frozen

- **Plant:** `plant_c3` on r2m3 (baseline v3), at 5,300 veh/h with 50 % automated vehicles (ALKS).
  - **TRUCK:** 10 trucks, chosen before the run, capped at 40 km/h.
  - **S:** the steady reference: the same demand with no event.
  - **SURGE** dropped at S2 (V487).
  - Every TRUCK row is labelled as outside the plant's stated intended use (V462(4)).
- **Protocol:** `docs/research/protocols/planb.md` v1, approved V480. The amendments are V486 (the drain test, a logged deviation) and V491 (the freeze).
- **Code** (branch `planb/core`):
  - S1, S3a and S4 ran at `96fde8d`.
  - S5 and S6 ran at `b0c9360`. Its diff from `96fde8d` is the picks file only.
  - The deciding reading, read6 v1, also ran at `b0c9360`.
  - The report supplement, read6 v2.3, ran at `09f49ad`. The branch head `a8b7a50` adds only tests, the spec and `read6_superset.py`.
  - The copy holds `git archive` tarballs of `b0c9360` and `a8b7a50`.
- **Policies (v3w),** frozen since 2026-11-06, with the same hashes as `baseline_v4/SHA256SUMS`:
  - w0 is `C0_u250`, w1 `C1_u500`, w2 `C2_u250`, w3 `C3_u500` and w4 `C4_u500`, each with its config and pilot file.
  - Recipe: `docs/research/protocols/round_1.md`. One shared PPO actor uses 16 normalised local inputs and picks a headway of 1.6, 1.2, 1.0 or 0.8 s every 10 s.
- **The 23 deciding opponents in TRUCK:**
  - 3E-C_TRUCK, labelled "not converged at 100 generations", and 3E-D_TRUCK, both CMA-ES rules tuned for this cell;
  - 3e (3E-T), 3ex1 and 3ex2;
  - MPC-F, an MPC with a model fitted on separate seeds;
  - copy, a rule distilled from the policies;
  - the grid re-picks: grid_a41000_10_2, grid_lr400_13_1, grid_os1_10_10, grid_r4a2 and grid_z31333;
  - the carried rules: a4400_10_1, lr1000_10_1, lr1000_16_2, lr400_13_2, lr400_16_1, os0_10_10, os1_10_0, os1_15_10, p333, r4a1 and z33133.

  ASCH picked the same controller as lr1000_16_2, which is also the steady pick, so it runs under that name. No control (`nc`) is reported in every table but is never an opponent.
- **Seeds:** the Plan B block 7,480,000-7,480,999, partitioned in planb.md §6. S6 used 7,480,400-7,480,639 (n = 240, every arm, no drops).

## Results

**Deciding (read6 v1, V495-V496): TRUCK = T, "no clear difference; neither W nor L; harm not excluded", so the study is NULL.**
- The W reading fails on two components:
  - against 9 of the 23 opponents, the delay lower bound at 97.5 % is at or below 0. The lowest is os0_10_10 at −0.58 % [−0.93, +0.20];
  - only 3 of the 5 learners are positive on both delay and close-following against every opponent.
- Every other W component passes:
  - close-following: the lower bound is above 0 against all 23 opponents. The smallest margin is 3E-C_TRUCK, +11.80 % [+4.97, +19.71];
  - flow, collisions and moving full-emergency events pass;
  - braking: the largest point excess is +2.00 %, against 3e.
- No L fires. k = 0 of 5 policies meet W alone.

**S2 (V484-V487):** KILL as registered. Under V486's drain test, TRUCK continues and SURGE drops. TRUCK fails G2-loss, so the best possible outcome was a level claim.

**Report-only (read6 v2.3, V497-V501), no reading:**
- **Round 2's T2 with its counting filter:** 6 opponents counted, 5 of 5 policies meet the bar. v1's universe counts 14, also 5 of 5.
- **No control:** v3w has 28.94 % less delay [+28.07, +30.10].
- **Adaptation gain:** close-following 1.56 [1.19, 2.09]; delay 1.05 [0.90, 1.33].
- **Resilience R and close-following resilience:** computed and labelled report-only.
- **The full map** against every opponent and no control: v1's measures, §5's report-only measures, and 12 jam keys from the space-time side files, each with and without the capped trucks. Against p333, jam share is +10.65 % [+0.02, +17.61] at 95 %; its 98.75 % interval includes 0.

**Verification:**
- v1: two blind recounts matched all 1,886 map values, plus three reviews.
- v2.x: blind recounts C to F matched every new number within 1.4e-14, plus five review rounds with skeptics.
- No finding changed a number or a deciding field.

## Disclosures every sentence must carry

- **TRUCK passes S2 only under V486's drain test,** a logged deviation (planb.md §10, G4(ii)).
- **3E-C_TRUCK is "not converged at 100 generations".**
- **ASCH is the same controller as lr1000_16_2 and the steady pick.**
- **V494's outage:** 251 S6 runs were resumed on the same host and code after the host rebooted.
- **The 14 rebuilt side files:** 14 side files were rebuilt on another platform (V498-V500). Their rows are equal on every key's value, and a control rerun of 4 runs reproduced their side files byte for byte. Only 3E-C_TRUCK's jam entries depend on them.
- **Near-twin opponent pairs:** p333 and lr1000_10_1, and grid_a41000_10_2 and grid_r4a2, have equal per-seed delay on 190-220 of 240 seeds.
- **The plant:** outside its stated intended use; synthetic and uncalibrated.

## Known limits

- **One cell, one level.** Plan B speaks of TRUCK at 5,300 only. Every condition explored adds to the count of cells tested (planb.md:145).
- **The edge is on a metric in the reward.** Close-following (TTC below 3 s, read once a second) is also in the reward. Lateral and merge conflicts are not measured.
- **No independent fuel test.** Fuel is measured by the pack but was never in the reward or in a pre-registered reading.
- **Not every opponent converged.** 3E-C did not converge, so it is a lower bound on its family. MPC-F's held-out MSE is in S4c's record, not in read6.
- **Row key order is not deterministic,** although the values are: plant_sweep.py:218 loops over a hash-seeded set. Compare rows value by value (V499).

## Where everything is

**In git, beside this file:**
- `readings/`: the deciding v1 output, the v2.3 supplement and the input hash lists of both;
- `inputs/`: read6's config, the S6 jobs, meta and drops files, S3a's repick.json, the frozen picks and the hashes of the 14 rebuilt side files;
- `policies/`: v3w's 5 chosen checkpoints, with their config and pilot files.

**Not in git** (over the 5 MB per-file limit): the S6 rows (177 MB; 64 MB gzipped) and the 13,920 side files (2.9 GB).

**Read-only full copy, with `SHA256SUMS`:** `/home/catalin/work/phd/v5b1_runs/baseline_v5/`.
- `runs/` holds every Plan B run folder:
  - S2 (`planb_remote`);
  - S1, S3a and S4 (`planb_s34_remote`);
  - S5, S6 and the side files (`planb_s56_remote`, including `jobs/st_rebuilt`);
  - the readings v1 to v2.3, with v2.0 to v2.2 marked superseded;
  - the rebuild;
  - every blind recount and review folder.
- `policies_v3w/` and `code/` hold the policies and the code tarballs.
- The files are hard links to the run folders, so they take no extra disk. Making the copy read-only also made those run files read-only.
- `planb_s34_backup` and `planb_s56_backup` are left out: they are partial in-run backups, superseded by the verified fetches.

**Reports:**
- `docs/research/results/planb_s2_result.md`;
- the read6 v2 spec with amendments 1-5a, `docs/research/planb/read6_v2_spec.md` on `planb/core`;
- the ledger, V478-V502.
