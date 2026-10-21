# Appendix C: scripts and checks per agent to the paper_1 forensic audit

Main report: `REPORT_paper1_forensic_audit.md` (same folder). The text below is the agents' own output, reconciled as described in §0.2 of the main report. Paths of the form `/tmp/claude-1000/.../scratchpad/audit/<dir>/...` refer to the session scratch folder; the same files are now in `~/work/phd/v5b1_runs/audit_paper1_2026-10-21/<dir>/...` (caches over 10 MB excluded, see `EXCLUDED_CACHES.txt`).

### R1 PLANT (dir audit/PLANT/)

- /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/PLANT/scan_runs.py on p1b/v108/runs (344,852), p1b_c1/v114/runs (1,100), p1/v99/runs (296,527) -> compact JSONL, 0 parse errors; all commits 93ba655 / e7dd561 / 85f7d34
- /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/PLANT/analyze_plant.py -> analyze_plant.out: 0 collision/teleport/undrained runs; 0 red crossings without runners; incident windows identical per seed; spill per arm (FX 0.07/0.42 at q2000); clean-day and NC throughput
- /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/PLANT/delay_reference.py -> delay_reference.out: Table II rel values reproduced; hidden incident travel time 3-8 s/veh changes rel by at most 0.8 percentage points; realised vs commanded discharge
- /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/PLANT/drain_share.py -> drain_share.out: 22-56 % of TTT after control end
- /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/PLANT/demand_check.py -> demand_check.out: own Poisson regeneration, 0 count mismatches in 345,952 runs
- /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/PLANT/idm_capacity.py -> idm_capacity.out: IDM capacity 1,894-2,397 veh/h; crawl 276-393; slowdown 981-1,260
- grep -H 'performs emergency stop' over all SUMO logs (sequential xargs) -> p1b_all_emergency_stops.txt (44,816), p1_all_emergency_stops.txt (1,166,567), c1_all_emergency_stops.txt (154); parsed by /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/PLANT/estop_times.py -> estop_times.out: all red-light forced stops on edge 2, 44 % at the first red, median 26 m/s2
- /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/PLANT/estop_eval.py -> estop_eval.out: eval main s=0 metered 13.0 % with a stop, 5.3 % excluding t<60 s
- /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/PLANT/emerg_parse.py on a 862-log sample -> emergency braking mostly on edges 4/5 at 9 m/s2
- /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/PLANT/emerg_edges.py -> emerg_edges.out: merge emergency braking in 94.5 % of metered vs 61.2 % of NC eval runs
- /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/PLANT/runner_share.py -> runner_share.out: shares 0.101 / 0.301
- /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/PLANT/signal_clock_check.py, signal_clock_debug.py, signal_const_rate.py -> amber 3 s and red >= 2 s hold; rare 5/7-s greens from floating-point arithmetic after cycle changes; none for constant rates
- Read SUMO v1_27_1 source (/home/catalin/work/phd/phd_speed_harmo_v6_toolchain/sumo-src, third-party upstream code, read only): MSVehicle.cpp updateTimeLoss / ignoreRed / red emergency stop, MSLane.h getVehicleMaxSpeed, MSFrame.cpp defaults, MSLane.cpp collision gap
- git archive 93ba655 and e7dd561 into the scratch dir; git diff --stat 93ba655..HEAD -- v5b: only confirm_c1.py added; e7dd561..HEAD -- v5b: none

### R1 CTRL (dir audit/CTRL/)

- /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/CTRL/scripts/index_runs.py on p1b/v108 (344,852 runs), p1/v99 (296,527), p1b_c1/v114 (1,100) -> out/*_index.jsonl, 0 read errors
- code extracted with git archive 93ba655 and e7dd561 into the scratch dir code_*; git diff 93ba655 HEAD -- v5b/ shows only confirm_c1.py added
- scripts/retune.py -> out/retune.json: N, FX, FB, PI, AD, ID, IP and G_PI re-derived from tuning seeds only; all match result.json; |A| = 120 unique per q
- scripts/confound.py -> out/confound.json: N-before-onset cost per L0 law (eval); per-cell always-on best vs IP (tuning); ID == IP identical in block_q2000
- scripts/oracles.py -> out/oracles.json: OR_in, ORX_1/2/4, TP recomputed (match within bootstrap noise); replicate seed rule 0 violations; incident window mismatches 0; L0 beats OR_in on 5-16 seeds
- scripts/s3_tp_checks.py -> out/s3_tp.json: switch/back/d/c/fa ticks all correct; TP-picked run has fewer generated vehicles
- scripts/seed_audit.py -> out/seed_audit.json: seed blocks disjoint across P1/P1b/C1; one commit per study; C1 arms as frozen
- run-file mtime check (inline python): tcheck 10:38-11:03, tune 11:03-13:07:52, eval 13:07:56-20:28:55 vs sentinel 13:07:53
- scripts/pi_surface.py -> out/pi_surface.txt: PI q1600 surface decreasing toward the K_P=70/K_I=120 corner
- scripts/pi_objective.py -> out/pi_objective.txt: pooled mean / mean of type medians pick p70_70_10_e4 (better in both types)
- scripts/split_type_tuned.py -> out/split_type_tuned.json: per-type always-on beats IP in 8/8 fold-cells
- scripts/id_objective.py, scripts/pareto_id.py, scripts/id_alt_eval.py, scripts/s1_sensitivity.py -> S1b fragile to the ID pooling rule (pooled mean: FAIL); pooled-median reproduction matches Table II exactly
- scripts/pareto_all.py -> out/pareto_all.txt: PI@1600 dominated by 6, ID@1600 by 2, FB@2000 by 3
- scripts/pi_dominators.py, scripts/c1_comparator.py -> IP still 14-21 % ahead of non-dominated PI laws in block_q1600 (eval, descriptive)
- scripts/c1_check.py -> C1 16.2 % [7.3, 23.7], diff 41.4 [16.6, 65.7], 0 invalid
- pdftotext of papers/refs_papers/1-s2.0-S0968090X07000873-main.pdf -> §2.7.1 eq.(1) ALINEA with N; K_R sensitivity §3
- grep of paper.qmd / references.bib / decisions.md / prior_art_P1_P2.md for CRN, 13.3, P1, citations

### R1 S1 (dir audit/S1/)

- git -C /srv/shared/Workspace/phd/phd_speed_harmo_v5b1 diff --stat 93ba655 HEAD -- v5b/p1 v5b/p1b v5b/d1/stats.py -> only v5b/p1b/confirm_c1.py added; S1 code path in the working tree = run code
- git archive 93ba655 v5b tests -> /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/S1/code_93ba655 (read stats.py, analysis.py, family.py, episode.py, run.py)
- sha256 of p1b_addendum.md and p1_incident_information.md at 93ba655, at HEAD and in the working tree -> 2b3d3ccb…/fed27bf6…, equal to result.json page_sha256/base_page_sha256
- cmp docs/research/results/p1b_result.json ~/work/phd/v5b1_runs/p1b/v108/result.json -> IDENTICAL
- /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/S1/load_eval.py -> 3,200 S1 run files (8 arms x 100 seeds x 4 cells), 0 missing, 0 field mismatches, 0 incident-window mismatches, 0 invalid; writes eval_delays.json
- /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/S1/s1_recompute.py -> 44 S1-level rows; max abs deviation vs result.json = 0 for rel, diff, medians, rel_ci, diff_ci (same draws); own S1a FAIL (no common (a) cell; R(ID,FB) and R(ID,PI) never (a), R(ID,PI) fails (b) slow_q1600); own S1b PASS (a) cells slow_q2000, block_q1600; S1b unchanged under 3 alternative RNG seeds; output s1_recompute_out.json
- /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/S1/robustness.py -> over 20 RNG seeds: CI bounds move up to 1.6 points (block_q1600 IP vs ID lower 7.3-8.9); no sign change; leave-one-out rel slow_q2000 11.42-12.24 %; 8 greedy removals needed to fall below 10 %
- /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/S1/zero_diffs.py -> ID = PI controller at q2000 (7 hash-identical seeds per cell); ID = FB controller at q1600; IP = ID in block_q2000 (100/100 identical)
- /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/S1/tune_check.py -> N, FX, FB, PI, AD, G_PI, ID, IP re-derived from 60,480 raw tuning files; all agree with result.json; IP tuning margins 0.15 s/veh (block_q1600) and 4.05 s/veh (slow_q1600)
- /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/S1/clean_day.py -> clean-day medians from raw runs equal result.json: q1600 N 45.4, PI 81.1, FB 154.3; q2000 N 151.6, PI 301.1
- /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/S1/sign_consistency.py -> rel-CI and diff-CI lower bounds sign-consistent in 44/44 rows
- pdftotext -layout papers/paper_1/paper.pdf -> Table II caption and rows identical to paper.qmd:165-176
- grep of paper.qmd for clean/incident-free/prevalence -> clean-day cost promised at line 104, not reported anywhere

### R1 S23 (dir audit/S23/)

- git -C /srv/shared/Workspace/phd/phd_speed_harmo_v5b1 archive 93ba655 v5b docs/research/protocols tests | tar -x -C /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/S23/code_93ba655 ; git diff --stat 93ba655 HEAD -- v5b/p1b v5b/p1 -> only v5b/p1b/confirm_c1.py added; analysis.py and stats.py unchanged
- /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/S23/s23_load.py -> 269,084 run records (eval main + k1-k4 for 120 actions, tuning main, L0, d-grid, runners, clean days); 0 missing; key == filename; all code_commit 93ba655
- /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/S23/s23_recompute.py (seed 20261019) -> log s23_recompute_20261019.log: S2 x/y, ORX_R, plateau, TP, d* (value/bind/CI/shares), runner rows, IP vs L0 all match result.json exactly
- /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/S23/s23_recompute.py (seed 777) -> s23_recompute_777.log: CI ends move by up to 0.4 points (block_q1600 y 0.44 -> 0.56); no sign or flag changes
- /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/S23/s23_extra.py -> s23_extra.log: IP re-tuned matches in all 4 cells (slow_q1600 margin 4.1 s, block_q2000 2.9 s); c*, p* match result.json; clean-day medians and paired costs; OR_in over the top-5 tuning actions 2.5/10.3/7.5/8.6 %
- /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/S23/s23_dgrid_check.py -> s23_dgrid_check.log: slow_q1600 delayed runs switch at t_on+d and return at t_off (100/100); bimodal IP delays; seeds where IP beats PI 54 % -> 25 % from d=0 to d=30
- grep -rn '13\.3' docs/research/results papers/paper_1/paper.qmd docs/decisions.md -> 13.3 only as P1 slow_q2000 S2 upper bound (p1_result.json, p1_result.md:48, p1_summary.md:39)
- pdftotext papers/paper_1/paper.pdf | grep -> rendered PDF carries the same sentences (13.3, 'within 3 s', 'about 120 s', 'report separately')
- grep -n protocol p1_incident_information.md (S2 :105-110, break-even :76-81, clean day :102, S3 :112, A10 :116) and p1b_addendum.md:4,36 -> implementation matches the protocol; the paper omits the pre-registered outputs
- jq-like summaries of result.json eval.per_q (clean_day, false_alarm_cost, f_star) and eval.S3.*.combined_row -> data exist, absent from the paper

### R1 C1 (dir audit/C1/)

- /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/C1/c1_recompute.py -> C1 16.2 % [7.3, 23.7], diff 41.37 [16.61, 65.69], 0 invalid; all descriptive rows identical to result.json (log out/c1_recompute.log)
- /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/C1/c1_desc_sens.py -> descriptive diff CIs robust to bootstrap seed; at 99 % all IP-vs-PI rows stay > 0; the PI s=10 % degradation CI includes 0 (out/c1_desc_sens.log)
- /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/C1/c1_influence.py -> leave-one-out rel 15.5-17.0 %; 67/100 seeds favour IP; sign test p 4e-4 (out/c1_influence.log)
- /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/C1/c1_spill.py -> served IP 1140 vs PI 1074 veh/h; spill share 0.05 vs 0.32 (out/c1_spill.log)
- /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/C1/scan_runs.py (P1 v99 296,527 runs; P1b v108 344,852 runs) -> out/p1_runs.pkl, out/p1b_runs.pkl
- /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/C1/estops.py -> P1 43,370/50,061 = 86.6 %; P1b 7,396/57,782 = 12.8 %; population composition (out/estops.log)
- /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/C1/estops2.py -> matched 30 specs 67.6 % -> 14.7 %; const-rate 68-97 % -> 8-20 %; P1 meter-edge EB warnings 98.7 %; P1b red crossings at s=0: 0/339,450; collisions 0 (out/estops2.log)
- /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/C1/tune_check.py -> raw P1b tuning re-derives N c1800, PI p70_120_8_e4, IP block p20_20_16_e4 = C1 frozen arms (out/tune_check.log)
- /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/C1/tune_block_only.py -> always-on p20_20_16_e4 222.0 s, IP 224.7 s, pooled PI 293.4 s on block tuning seeds (out/tune_block_only.log)
- /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/C1/seed_overlap.py -> C1 seeds 7,400,700-799 disjoint from P1/P1b seeds; replicate RNG seeds never in 700-999 (out/seed_overlap.log)
- git diff --stat 93ba655 e7dd561 -- v5b/ -> only v5b/p1b/confirm_c1.py added; git diff e7dd561 HEAD -- v5b/ tests/ -> empty; git diff 85f7d34 93ba655 -- v5b/d1 v5b/d2 v5b/ops -> empty
- git log timestamps: protocol approved 7c6acc8 21:11:24, code e7dd561 21:16:00, sentinel/run 21:27:50, result 2202fb4 21:29:24 (2026-10-20)
- python full-JSON equality docs/research/results/p1b_c1_result.json vs ~/work/phd/v5b1_runs/p1b_c1/v114/result.json -> identical
- find ~/work/phd/v5b1_runs (excluding p1b_c1) for filenames with seeds 74007xx-74009xx -> none; integer-seed search of top-level JSONs -> none
- pdftotext paper.pdf -> rendered numbers match paper.qmd (16.2, 12.5-16.4, 24.4, 27.6, 87 %, 12.8 %)
- SUMO version in stats XML of one run each of P1, P1b, C1 -> libsumo 1.27.1 in all

### R1 PROV (dir audit/PROV/)

- /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/PROV/page_sha.sh -> recorded page_sha256 values match P1 page@0e8d49b, P1b addendum@75bcd2b, C1 page@7c6acc8 (and D1@a23613b, D2@72ba8f2); the working tree equals these, so there were no edits after the data
- /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/PROV/scan_runs.py (output scan_runs_out.json) -> P1b 344,852 = 14,550 + 75,120 + 255,182, all commit 93ba655, 0 invalid/teleport/collision/undrained; C1 1,100 clean, all e7dd561; P1 296,527 clean; D2 v92 had 20 teleport runs
- /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/PROV/seed_sets.py -> main seeds disjoint across D1, D2, P1, P1b and C1; the only overlaps are the bug re-runs and 6 verifier re-runs
- /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/PROV/pairing.py -> P1b 960 groups and C1 100 groups: identical incident window and demand across arms; sumo_seed = demand_seed = seed; replicates seed + k·1e7
- /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/PROV/c1_recompute.py -> C1 rel 16.2 %, diff 41.4 [16.6, 65.7], rel CI [7.3, 23.6]; CONFIRMED rule holds
- /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/PROV/c1_opponent.py -> P1b block_q1600: FB median 247.9 < PI 252.1; IP vs FB 15.9 % [20.1, 55.3 s], vs PI 18.0 %
- /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/PROV/p1_block1600.py -> P1 block_q1600 IP vs PI -0.7 % (diff -1.7 [-15.8, 21.2])
- /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/PROV/p1_vs_p1b.py -> same S1a/S1b verdicts; S2 and S3 differ (block_q2000 lower bound -1.8 vs 3.5; slow_q2000 d* 26 vs 120 s)
- /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/PROV/estop_share.py -> P1 86.6 % (43,370/50,061), P1b 12.8 % (7,396/57,782)
- /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/PROV/result_meta.py and p1b_arms.py -> code_commit/code_dirty=false/seeds/args per study; P1 resume=true; tuned arms (C1 frozen arms match P1b)
- git log --date per protocol/code/results commit; git show --stat e973f6e (docs only); git diff --stat 93ba655 e7dd561 (adds confirm_c1.py, a test and a tool only); git log -S for V99/V100/V108/V109/V114/V115 -> approvals precede their runs; no '-| V' row edits after 10-19 18:40
- journalctl --user (Oct 19-20) -> v100-queue failed 18:51:30; p1-run.service --resume 19:06:22; single p1b-run 10:38:06 and p1b-c1 21:27:49 starts
- sha256sum raw result.json vs docs/research/results/*_result.json -> identical for P1, P1b and C1
- grep for 74007xx across ~/work/phd/v5b1_runs outputs and tests -> C1 seeds appear only in p1b_c1/v114 and in job prompt texts; tests build keys only
- git show 93ba655:tests/test_p1b_sumo.py -> the pre-data runner check (B2/R4) exists on smoke seed 7,400,000

### R1 REPRO (dir audit/REPRO/)

- scratch/figs/fig_{plant,ladder,c1_robust,c1_delay}.py (copies with output paths moved to scratch/out, ROOT = repo, read-only) -> all ran; pdftotext identical; pdftoppm 200 dpi max pixel diff 0.0 vs repo PDFs (only 7 timestamp bytes differ)
- cmp docs/research/results/p1b_result.json vs ~/work/phd/v5b1_runs/p1b/v108/result.json, and the same for p1b_c1 -> byte-identical
- scratch/fig2_recompute.py scratch/out -> all 20 Fig. 2 medians plus strongest-L0 choices match the JSON exactly from 242,400 raw files (all 93ba655, keys == filenames)
- scratch/fig2_vs_paired.py scratch/out/fig2_recomputed.json -> marginal-median gaps differ from paired rel (sign flips in slow_q1600)
- scratch/fig3_recompute.py -> all 6 Fig. 3 points and 95 % CIs match exactly (same RNG recipe); independent RNG moves CI ends by <= 0.3 pt
- scratch/c1_arm_medians.py -> 11 C1 arm medians match JSON
- scratch/chain_integrity.py -> P1b eval files 255,182 (= eval.n_runs), all 93ba655, 0 key mismatches, all written inside 13:07:53-20:31; C1 1,100 files all e7dd561 inside 21:27:50-21:29:10
- find over all ~/work/phd/v5b1_runs subdirs for *s74007xx* -> 0 outside p1b_c1 (C1 seeds fresh); confirm_1 seeds do not overlap
- scratch/net_geometry.py on the cached bn4.net.xml -> 4/4/4/2/1 lanes, TLS 3 on 4 links at x=410, drops at 550 and 830 m
- netgen_bn4.build() with V5B1_RUNS=scratch/runs_root_fresh -> net body identical to the cache (header comment only differs)
- scratch/pdf_vs_qmd.py paper.qmd scratch/out/paper_pdf.txt -> every qmd-body number present in paper.pdf except citation years; PDF created 23:21:30, qmd mtime 23:21:29, commit 4de404a
- git diff --stat 93ba655 e7dd561 -- v5b tests -> only confirm_c1.py and test_p1b_c1.py added; e7dd561..HEAD -> no change in v5b/ tests/
- pytest (code_e7dd561, V5B1_RUNS=scratch/runs_root, -p no:cacheprovider) tests/test_p1b.py test_p1b_c1.py test_p1_stats.py test_p1_analysis.py test_p1_family.py test_p1_meters.py test_p1_runner.py -> 94 passed in 33.7 s
- systemd-run --user --wait --collect --pipe --unit=audit-repro-sumotests pytest tests/test_p1b_sumo.py -> 5 passed in 2.4 s
- scratch/cpu_check.sh -> CPU 3-5 % over 3-5 s, no v6/heavy jobs or sumo processes before the SUMO runs
- scratch/spot_run.sh N ARM SEED (systemd units audit-spot-1..4; IP/PI x seeds 7400700, 7400760; code e7dd561) + scratch/spot_compare.py -> all 4 runs identical to the stored C1 runs in every field except wall times (delay_s 173.455/329.973/288.818/437.620; hashes equal)
- scratch/crn_check.py, scratch/crn_check2.py -> seed 7400700: 0/403 vehicles differ (CRN holds); seed 7400760: divergence starts at the first insertion delay (475 s), 21/23 later on-time vehicles get different lanes
- All scratch paths are under /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/REPRO/

### R1 LIT (dir audit/LIT/)

- /home/catalin/work/phd/phd_speed_harmo_v5b1_toolchain/venv/bin/python -I /srv/shared/Workspace/phd/phd_speed_harmo_v5b1/tools/verify_bib_crossref.py papers/paper_1/references.bib -> 15 OK, 1 CHECK (Smaragdis2003 Crossref title quirk), 5 NO-DOI; output /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/LIT/crossref_tool_output.txt
- /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/LIT/scripts/fetch_meta.py references.bib dl_meta/ -> Crossref and OpenAlex records and abstracts for all DOIs; /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/LIT/fetch_meta_output.txt
- /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/LIT/scripts/compare_bib_full.py -> all DOI entries match Crossref; only the Lopez author order differs (bib = DLR's recommended order) plus a 'De Schutter' parsing artefact; /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/LIT/compare_bib_full_output.txt
- /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/LIT/scripts/fetch_s2.py -> Tympakianaki 2014 abstract (green-red signals, ALINEA-like PI-type regulator); Smaragdis 2004 and Carlson 2010 metadata; 3 queries hit HTTP 429; /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/LIT/fetch_s2_output.txt
- /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/LIT/scripts/crossref_candidates.py -> verified Knoop 2008 (10.3141/2071-03), Skabardonis 2003 (10.3141/1856-12), Smaragdis 2004 (10.1016/S0191-2615(03)00012-2), Carlson 2014 (10.1016/j.trc.2014.05.017); /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/LIT/crossref_candidates_output.txt
- pdftotext -layout papers/refs_papers/1-s2.0-S0968090X07000873-main.pdf -> /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/LIT/papageorgiou2008.txt; read §§1-5 in full (eq. 1 and truncation, eq. 3 cycle, green 4 s / red >= 2 s with no amber, all lanes signalised, attribution of the Smaragdis papers)
- Full texts downloaded into separate dl_* dirs and extracted: Cameron 2016 (author copy cs.ubc.ca) -> cameron2016.txt; van Hasselt 2010 (papers.nips.cc) -> vanhasselt2010.txt; Frejo 2021a/b AAM (idus.us.es) -> frejo2021a_raw.txt and frejo2021b_raw.txt; TOPS 2005 (files.topslab.wisc.edu) -> tops2005.txt; Vinitsky CoRL 2018 (PMLR) -> vinitsky2018.txt; all under /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/LIT/
- Abstracts and landing pages: IDEAS (Smaragdis 2004) -> dl_misc/ideas_smaragdis2004.html; TRID 365587 (ALINEA 1991 metadata), TRID 686972 (Smaragdis 2003); Chalmers 211200 (Dabiri abstract) -> dl_misc/chalmers_211200.html; EPFL Infoscience 154946 and 85041 (Carlson 2010/2011); FHWA 20008 page (Hale 2020); OpenAlex (Cameron pp. 712-719, van Hasselt vol 23 pp. 2613-2621, Vinitsky ITSC 2018 pp. 759-765); Crossref (Wang & Papageorgiou 2006 ITSC; Kosmatopoulos 2006); sumo.dlr.de Publications page (Lopez author order)
- git show {85f7d34,93ba655,e7dd561}:v5b/p1/meters.py and v5b/p1b/meters.py, plus 93ba655 d1/episode.py, d1/plant.py, d1/netgen_bn4.py, p1/family.py, p1b/episode.py -> /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/LIT/code/; md5: p1/meters.py identical at all three commits, p1b/meters.py identical at 93ba655 and e7dd561; git diff to HEAD empty for both
- pdftotext papers/paper_1/paper.pdf -> paper_pdf.txt: reference list renders with no unresolved keys
- Not used, because access was blocked (no bypass attempted): dias.library.tuc.gr and dblp.org (bot checks), rosap.ntl.bts.gov (Access Denied), publications.iowa.gov and sciencedirect.com (403), skoge.folk.ntnu.no (TLS error), arXiv API (429). As a result, the full texts of Wang 2014, Smaragdis 2003/2004, Carlson 2010/2011/2014, Sheu 2007, Wu 2014, Dabiri 2014 and Sun 2013 were not read

### R1 TEXT (dir audit/TEXT/)

- /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/TEXT/check_paper_numbers.py -> check_paper_numbers.out: all 24 Table II values match p1b_result.json; line 193's 13.3 % is P1's slow_q2000 x (P1b gives 19.3); C1 numbers match p1b_c1_result.json; the median-delay reduction is 17.3 % vs paired rel 16.2 %; extracted p*, the combined row, f*, the false-alarm cost, the prevalence line and grid edges (N at q2000 = f10_8; PI at q1600 on the K_P=70 and K_I=120 edges)
- /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/TEXT/clean_day_paired.py -> clean_day_paired.out: paired clean-day cost vs N from raw runs (B=20,000): q2000 PI +151.6 s [135.3, 163.3], FB +194.9, AD +200.4, FX +174.9; q1600 PI +12.0 [-0.5, 19.8], FB +85.3, AD +77.9, FX +119.0
- /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/TEXT/spill_q2000.py -> spill_q2000.out: V109 spill share at q2000: FX 0.07/0.42, NC 0.11/0.34, the other metered arms 0.85-1.00; no run has its tail within 7 m of the entry
- pdftotext paper.pdf -> /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/TEXT/paper_pdf.txt: the PDF matches the qmd (caption 'second arm', 13.3 %); 'Section IV' resolves; one [CITE] marker
- git log + sha256sum on the 3 protocol pages vs P1/P1B/P1B_C1 sentinels in ~/work/phd/v5b1_runs: each page was committed before its run and the hashes match; P1_EVAL_STARTED.json has resume=true
- git show 93ba655:v5b/d1/plant.py, v5b/p1b/episode.py, v5b/d2/incidents.py, v5b/p1b/meters.py -> Vinitsky 2018 origin, av_share 0.1 used, IDM parameters, step 0.5 s, crawl on lane 4_1 'more severe than a closure', [200, 2618] veh/h, 6/3/2 s signal: confirmed
- grep docs/decisions.md V95-V129 and docs/research/prior_art_P1_P2.md:34 -> the CRN claim rests on a source reading only; Klein 2024 is not cited
- read p1b_verification/out/p1_vs_p1b.log and spill.log (claims, cross-checked by my scripts) -> P1 block_q1600 IP vs PI -0.7 %, d* never ahead

### R1 HEADLINE (dir audit/HEADLINE/)

- Blind order kept: protocols and writer code were read first. All own numbers were computed before reading the paper text or the run record result.json. Docs results notes, JSON and verification folders were not read.
- load_runs.py: compact tables of all raw run JSONs (P1b v108: 344,852 files; C1 v114: 1,100), 0 unreadable. Path: /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/HEADLINE/load_runs.py
- tune.py: independent re-derivation of N/FX/FB/PI/G_PI/IP/ID from the tuning seeds 7,400,300-339, with near-tie margins: /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/HEADLINE/tune.py -> tune_out.json
- headline.py: (a)-(d) with rel CI, diff CI and scaled diff CI, own bootstrap seed, B = 20,000, both views: /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/HEADLINE/headline.py -> headline_out.json
- boot_sensitivity.py: CI bounds over 50 bootstrap seeds: /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/HEADLINE/boot_sensitivity.py
- repo_seed_replay.py: own code with the repo's fixed seeds 20261019 / 20261020 reproduces every reported bound exactly: /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/HEADLINE/repo_seed_replay.py
- pairing_check.py: per-seed pairing (demand/SUMO seed, onset, duration, generated), drained/valid, teleports, health codes; mean and arm-median versions of rel: /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/HEADLINE/pairing_check.py
- mtime_check.py: run-file timestamps vs sentinels; search for seeds 600-799 in other run dirs: /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/HEADLINE/mtime_check.py
- selection_sensitivity.py and selection_bootstrap.py: robustness of S1b to tuning-selection noise (runner-up arms; 1,000 tuning-seed resamples): /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/HEADLINE/selection_bootstrap.py -> selection_bootstrap_out.json
- s1a_all_l0.py and l0_medians.py: ID and IP vs every L0 arm, and arm medians per cell (strongest L0 in block_q1600 = FB): /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/HEADLINE/s1a_all_l0.py
- c1_desc.py: C1 detection-delay and runner rows: /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/HEADLINE/c1_desc.py
- eb_check.py: emergency fields in the headline rows (info for the safety auditor): /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/HEADLINE/eb_check.py
- git (read only): git archive 93ba655 / e7dd561 into code_93ba655/ and code_e7dd561/; diff 93ba655..e7dd561 -- v5b only adds confirm_c1.py; diff e7dd561..HEAD -- v5b is empty; commit times vs sentinel times; protocol-approval commits are ancestors of the run commits
- After my own numbers: compared arm identities, invalid_runs, code_dirty and the S1/C1 verdict fields in ~/work/phd/v5b1_runs/p1b/v108/result.json and p1b_c1/v114/result.json (all consistent), and read paper.qmd:143-197

### R1 FU1 (dir audit/FU1/)

- FU1/drain_audit.py ~/work/phd/v5b1_runs docs/research/results/p1b_result.json -> FU1/drain_audit.out: delay, window-TTT and full-TTT rels plus the drain split for every L0 arm, ID, IP and NC pair in 4 cells and the C1 rows; S1a/S1b verdicts per metric (D: S1a FAIL, S1b PASS; W: both FAIL; F: S1a FAIL, S1b PASS); C1 passes on all three metrics
- FU1/drain_dynamics.py (same args) -> FU1/drain_dynamics.out: pooled/per-arm quadratic drain fits (R2 ~0.98, implied mu ~800-1,000 veh/h); neutral-price rels slow_q2000 6.0 %, block_q1600 19.0 %, C1 14.9 %
- FU1/metric_ideal.py (same args) -> FU1/metric_ideal.out: ideal time clean 44.5 s vs incident 47.8-52.6 s; D' rels within 0.5 points of D; two-arm arm-effect shares 0.44 / 0.08 / 0.11 / 0.55 / -0.04 / 0.12
- FU1/served_check.py (same args) -> FU1/served_check.out: identity served*0.25 h + n_left constant per seed (max resid 0.00); paired served IP-ID +48 / +102 veh/h, C1 +52
- FU1/c1_diff.py ~/work/phd/v5b1_runs/p1b_c1/v114/runs -> FU1/c1_diff.out: C1 median diff 41.37 s/veh [16.61, 65.1-65.7]; window TTT 2.85 veh.h [1.6, 3.5]
- FU1/lcb_debug.py -> bootstrap-seed sensitivity of the S1-level LCB (16.7-21.4 s)
- re-ran critic/drain_decomp.py, critic/window_metric.py, critic/c1_vs_nocontrol.py -> FU1/rerun_*.out byte-identical to critic/*.out
- git diff --stat 93ba655 e7dd561 and e7dd561..worktree for v5b/p1b/episode.py, v5b/d1/sumo_runner.py, v5b/d1/episode.py, v5b/d1/plant.py, v5b/d2/incidents.py -> no differences
- grep of protocols (p1_incident_information.md:85, screen_D2_incidents.md:110, p1b_confirm_c1.md:15,21), docs/architecture (review_v0.md:392, interfaces.md:52) and paper.qmd (no TTT/throughput) -> as cited
- All FU1 scripts are in /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/FU1/ ; run with PYTHONDONTWRITEBYTECODE=1 /home/catalin/work/phd/phd_speed_harmo_v5b1_toolchain/venv/bin/python -I

### R2 G2 (dir audit/G2/)

- G2/net_read.py -> net_read.out: parsed the cached bn4.net.xml and det.add.xml (lanes, lengths, connections, internal lanes, TLS links)
- G2/g2_mechanism.py -> g2_mechanism.out: per-arm medians (delay, entered_e4_incident, time-weighted q and edge-4 count during the incident from meter_log, q in the 300 s after clearance, served, max_queue_m/halted, n_system_ctrl_end) for P1b eval in all 4 cells, C1, and P1b tuning (always-on p20_20_16_e4 vs PI vs IP); paired IP-PI, IP-ID, IP-NC with Spearman correlations
- G2/g2_spot_lanes.py -> g2_spot_lanes.out: per-lane-group (free path 4_0 vs crawl path 4_1) time loss and exit flows in the 4 REPRO C1 spot tripinfo files; spot hash equals raw hash in all 4
- G2/g2_actions_traj.py -> g2_actions_traj.out: ranking of all 120 P1b actions in eval block_q1600; median q and edge-4 count trajectories relative to onset and clearance for C1 IP, PI and N; incident_log read-back speeds in 12,500 block runs
- G2/g2_none_check.py -> g2_none_check.out: breakdown check (max edge-4 count >= 50, served) for incident-free and incident cells
- G2/g2_c1_recheck.py -> g2_c1_recheck.out: own bootstrap of C1 IP vs PI (16.2 % [7.3, 23.7])
- G2/g2_duration_split.py -> g2_duration_split.out: exploratory split of IP-PI, IP-ID and IP-NC by incident duration (P1b and C1)
- Code read at 93ba655 (extracted to G2/code_93ba655; identical to e7dd561 apart from confirm_c1.py): d1/plant.py, d1/netgen_bn4.py, d2/incidents.py, p1/family.py, p1b/family.py, p1b/meters.py, p1b/episode.py; papers/paper_1/figures/fig_plant.py; protocols screen_D2_incidents.md:91-96 and p1_incident_information.md:21-22
- Scratch dir for all G2 scripts and outputs: /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/G2/

### R2 G3 (dir audit/G3/)

- Read gaps.G3 in /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/round2_input.json and the round-1 C83/PLANT-F5/PLANT-F13 text in wf_result.json
- git show 93ba655 and e7dd561 of v5b/d1/sumo_runner.py (lines 100-110); git diff --stat 93ba655 e7dd561 over v5b/d1, d2, p1, p1b/episode.py, meters.py, runners.py: empty; git grep for collision/ignore-junction/extra_args at both commits
- Read the SUMO 1.27.1 source at /home/catalin/work/phd/phd_speed_harmo_v6_toolchain/sumo-src (tag v1_27_1, matches installed sumo --version): MSFrame.cpp option defaults, MSLane.cpp detectCollisions / mustCheckJunctionCollisions / executeMovements, MSCFModel.cpp:62, MSVehicle.cpp:4776-4787
- /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/G3/net_internal_map.py -> net_internal_map.out (cached net bn4_e578788201, sha1 c04dab298c12ae575cf53e7ce098e479c46a2105)
- /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/G3/scan_c1_emerg.py -> scan_c1_emerg.out (all 1,100 C1 runs)
- /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/G3/scan_p1b_emerg.py -> scan_p1b_emerg.out/.json (all 344,852 P1b runs)
- /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/G3/scan_red_cross.py -> scan_red_cross.out (C1, P1b, P1 runs)
- /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/G3/log_greps.sh -> p1b_log_emerg_lanes.out, collision_log_grep.out, c1_log_lanes.out (all stored SUMO logs)
- /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/G3/lane_by_cell.sh -> lane_by_cell.out
- Resource check with REPRO/cpu_check.sh: CPU 3 % over 5 s; no heavy user units; no sumo/simulation processes
- 4 SUMO runs via /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/G3/spot_run_cj.sh (systemd-run units audit-r2-1..4, SUMO_HOME unset, OMP_NUM_THREADS=1, PYTHONDONTWRITEBYTECODE=1, git-archive copy of e7dd561 with only sumo_runner.py:105 changed, copy of the cached net, outputs in G3/spot)
- /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/G3/compare_cj.py -> compare_cj.out (re-runs vs stored v114 JSON, stats XML, logs)
- Confirmed the patched module was the one imported (printed __file__ and the check-junctions line from the scratch copy)

### R2 G4 (dir audit/G4/)

- git -C repo diff --stat 93ba655 e7dd561 -- v5b/ (adds only confirm_c1.py); git diff --stat e7dd561 HEAD -- v5b/ (empty)
- git archive 93ba655 v5b -> /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/G4/code_93ba655 ; read plant.py, demand.py, sumo_runner.py, netgen_bn4.py, meter_signal.py, p1b/episode.py, runners.py, meters.py; grep for SUMO option overrides (none)
- Read the cached network /home/catalin/work/phd/v5b1_runs/_netcache/bn4_e578788201/bn4.net.xml (lane lengths 100/0.10/310 m, speed 23)
- Read SUMO 1.27.1 source (/home/catalin/work/phd/phd_speed_harmo_v6_toolchain/sumo-src, tag v1_27_1): MSVehicle.cpp 2780-2940, 3755-3800, 4512-4528, 4755-4790, 4965-4990, 7585-7621; MSFrame.cpp:513; SUMOVTypeParameter.cpp:979-1013; MSCFModel_IDM.cpp; MSCFModel.cpp:87-108, 199-207, 341
- /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/G4/kinematics.py -> kinematics.out (brake gaps, IDM free-road profile, zones, executed IDM braking)
- /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/G4/dilemma_pred.py -> dilemma_pred.out
- grep -r emergency over all 344,852 P1b and 1,100 C1 sumo_pid*.log -> /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/G4/p1b_emerg_lines.txt, c1_emerg_lines.txt (category tallies; all meter-edge brakings at decel 9.00)
- /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/G4/scan_small.py -> p1b_small.jsonl, c1_small.jsonl (small fields from every raw run JSON)
- /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/G4/by_type.py -> by_type_p1b.out, by_type_c1.out (own demand and runner rebuild, 0 mismatches against generated and n_runners)
- /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/G4/estop_speed.py -> estop_speed_p1b.out
- /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/G4/pair_check.py -> pair_check_p1b.out
- /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/G4/approach_cross.py -> approach_cross_p1b.out, approach_cross_c1.out
- /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/G4/clock_check.py -> clock_check.out
- grep of paper.qmd (IDM, AV, speed factor, depart, comfort, decel, emergency) and of protocols p1b_addendum.md, p1_incident_information.md, p1b_confirm_c1.md
- No SUMO run, no web access, no writes outside the G4 scratch dir

### R2 G5 (dir audit/G5/)

- Read the code at 93ba655 (extracted to /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/G5/code_93ba655): v5b/p1/meters.py:192-217, v5b/p1b/analysis.py:40-45, 76-89, 211-232, 521-580, v5b/p1/stats.py:48-66, 153-222, v5b/p1b/episode.py:50-56, 187-235
- Read the code at e7dd561: v5b/p1b/confirm_c1.py:55-110, 170-190
- Protocols: p1_incident_information.md §4, §6 (S3, A10), I5, I7; p1b_addendum.md:4; p1b_confirm_c1.md
- /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/G5/json_s3.py -> json_s3.out (stored S3 c*, combined and never-switch-back rows)
- /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/G5/g5_recompute.py -> g5_recompute_20261019.log/.json and g5_recompute_777.log/.json (own c*, combined row, one-imperfection rows, schedule check over 3,900 raw files; exact match with the JSON; 0 schedule mismatches)
- /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/G5/g5_schedules.py -> g5_schedules.log (P1b d rows return at t_off; C1 IP never returns; wrong-type plan in block_q1600)
- /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/G5/g5_slow1600_d.py -> g5_slow1600_d.log (slow_q1600 delayed IP vs N)
- /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/G5/g5_dstar_c1.py -> g5_dstar_c1.log, g5_dstar_c1_20261019.log (own d* for the slow cells; C1 delay rows equal to the JSON with seed 20261019)
- grep of paper.qmd and round-1 TEXT/paper_pdf.txt for clearance/misclassification/false alarm/combined

### R2 G8 (dir audit/G8/)

- G8/scripts/oa_locations.py -> OpenAlex OA locations for 14 DOIs; output G8/oa_locations_output.txt (all paths under /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/G8/)
- G8/scripts/s2_oa.py -> Semantic Scholar batch openAccessPdf (first try HTTP 429, retried); output G8/s2_oa_output.txt
- curl IFAC 2014 preprint 2383.pdf from skoge.folk.ntnu.no -> G8/dl_dabiri/, pdftotext -> G8/dabiri2014.txt; pdfinfo and page numbers 11338-11343 checked against the bib
- NYCU DSpace REST (pid/find 11536/10762 -> bundles): PDF truncated twice at 97 kB; used the repository TEXT bitstream -> G8/sheu2007.txt (page headers 359-367)
- curl author copy The_Optimizers_Curse.pdf and pds_correction.pdf (jimsmith.host.dartmouth.edu) -> G8/smith2006.txt, G8/smith2006_correction.txt
- WebFetch rosap.ntl.bts.gov dot_26290_DS1.pdf (curl got 403; WebFetch received the PDF, copied to G8/dl_rosap/) -> G8/edara2012_report.txt
- MOspace DSpace REST (handle 10355/43356) -> Zhu 2012 thesis PDF -> G8/zhu2012_thesis.txt
- G8/scripts/noncompliance_ranges.py G8/edara2012_report.txt G8/zhu2012_thesis.txt -> G8/noncompliance_ranges_output.txt
- G8/scripts/extract_quotes.sh G8 LIT -> G8/extract_quotes_output.txt (line-numbered quotes behind every verdict)
- EPFL Infoscience DSpace REST for records 154946/180988/154958: abstracts read, bundles hold only license.txt -> G8/dl_epfl/
- workzonesafety.org record 47333 (Tympakianaki abstract) -> G8/dl_tymp/wzs_47333.html, parsed with an inline python -I snippet
- Failed or blocked, not bypassed: dias.library.tuc.gr (Anubis), sndbx.library.tuc.gr 403, ScienceDirect 403 (Wu2014, Procedia), jtte.chd.edu.cn timeout, Elsevier API (metadata only without key), DOAJ web 403, CORE 403, publications.iowa.gov 403, InTrans (AWS WAF challenge); see G8/access_log.txt
- git -C repo show 93ba655:v5b/p1b/meters.py (lines 89-112: FB, PI and AD update laws)
- Re-read LIT full texts: LIT/papageorgiou2008.txt, LIT/frejo2021a_raw.txt, LIT/frejo2021b_raw.txt, LIT/tops2005.txt; dumped round-1 LIT result -> G8/lit_round1_dump.txt
- arXiv 2111.06610 downloaded to check for secondary descriptions of Wu/Sheu/Dabiri: no mentions (G8/arxiv_2111.06610.txt)

### R2 FU2 (dir audit/FU2-1/)

- /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/FU2-1/dump_wf.py and dump_findings.py: extracted full round-1/FU1 claim and finding texts (claims_full.txt, findings_full.txt)
- /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/FU2-1/s1_indep.py -> s1_indep.out: S1a/S1b on delay, window TTT, full TTT, both views; Table II rows and bold; arm medians; drain shares (raw v108 runs, own code)
- /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/FU2-1/id_rule_sens.py -> id_rule_sens.out: ID dominance on tuning seeds; S1a and S1b re-evaluated under pooled-median, pooled-mean, mean-of-type-medians, minimax ID rules
- /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/FU2-1/drain_nleft.py -> drain_nleft.out: leftover-count vs arm-specific share of post-control TTT difference
- /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/FU2-1/c1_indep.py -> c1_indep.out: C1 paired rel, difference of medians, mean rel, TTT co-metrics, invalid seeds (raw v114 runs)
- Code read at 93ba655 / e7dd561 (git archive to FU2-1/code_*): v5b/p1/stats.py:48-63, v5b/p1b/analysis.py:136-141,353-355, v5b/p1b/episode.py:239-251, v5b/p1b/confirm_c1.py:49-58,121-136
- Protocol read: p1_incident_information.md:28-46,80-104 (ID rule, co-metrics, S1 statements, fail texts)
- paper.qmd:95-200 and pdftotext of paper.pdf (Table II caption, S1/C1 sentences); grep for ID tuning rule in the paper (absent)

### R3 G3R (dir audit/G3R/)

- Read gaps CG2-2 and CG2-5 from round3_input.json; read v5b/p1b/meters.py@93ba655 in full and v5b/p1b/episode.py@93ba655:99-240 (meter_log logs q before the update; set_law before meter.step at the switch tick); v5b/p1/meters.py@93ba655:203-217 switch_schedule; v5b/d1/sumo_runner.py@93ba655:63,200-212 (H-R5)
- Traced the Q_MIN origin with git grep at 93ba655 (v5b/d1/episode.py:46, v5b/p1/meters.py, v5b/p1b/meters.py:31), git show 2a79e5e:vsl_lab/envs/bn4_env.py (q_min=200.0 at :42), and grep of the protocols, decisions.md and the results notes (no stated value or reason; p1b_addendum.md:68, decisions.md:127, p1_incident_information.md:187, port_map_v0.md:365)
- Read paper.qmd lines 58-203 (lines 110, 118, 145, 155-197); grep for update period, grid and P-kick wording (none)
- Read p1b_result.json tune.arms and eval.S3 (d* grid, M values); p1b_confirm_c1.md:21 C1 rule; p1_incident_information.md:76-77 (d* linear interpolation, pre-registered)
- /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/G3R/g3r_common.py (shared loader, floor intervals, tie-aware Spearman, rank partial correlation, rel bootstrap B = 20,000)
- /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/G3R/g3r_floor.py -> g3r_floor.out (floor use per arm in C1 and all 4 P1b cells; gain vs floor with partial correlation on duration and onset; duration terciles; H-R5 exclusion rel at 0.95 for C1 and 0.99375 for P1b)
- /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/G3R/g3r_floor_when.py -> g3r_floor_when.out (floor time before, during and after the incident; H-R5 counts incl. NC and N)
- /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/G3R/g3r_unclipped.py -> g3r_unclipped.out (exact re-computation of PI's unclipped command at floor updates; the assert matched every logged clipped q)
- /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/G3R/g3r_capacity.py -> g3r_capacity.out (served flows to set the floor against the plant's flow)
- pdftotext of the local cited source papers/refs_papers/1-s2.0-S0968090X07000873-main.pdf (Papageorgiou et al. 2008) into G3R/refpdf/ref.txt; read lines 353-382 and 520-556 (qmin, qmax, T = 30 s, lane offsets)
- /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/G3R/g3r_lag.py -> g3r_lag.out (lag L per switched plan and d; formula check; exact-shift-by-d check; per-seed outcome vs L incl. 5-replicate means; d = 30 cost; C1 d rows reproduce -0.7 / +0.2 / -1.5 %)
- /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/G3R/g3r_lag2.py -> g3r_lag2.out (n vs n_crit at the last pre-switch and first post-switch updates; time to the first rate cut)
- /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/G3R/g3r_pkick.py -> g3r_pkick.out (size of the P term suppressed by R3)
- /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/G3R/g3r_cut_vs_d.py -> g3r_cut_vs_d.out (first cut after onset by detection delay)
- /tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/36818454-1a99-4f3d-af16-d8a04fb03e18/scratchpad/audit/G3R/g3r_slow1600_d.py -> g3r_slow1600_d.out (per-seed tipping of the slow_q1600 constant plan under delay)
- Read critic2/c1_floor.py/.out and c1_hr5_sens.py/.out and G2/g2_mechanism.py/.out; checked wf_result.json and wf_result_r2.json for overlap (the 'within 3 s' interpolation is already S23-F3; N = f10_8 at q2000 was already flagged)

