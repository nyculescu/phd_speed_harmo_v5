# S0/S1 interpretation: analysis files

Scripts and outputs under 1 MB from the S0/S1 interpretation (report: `docs/research/results/s01_result.md`). Each folder is one stage: an analysis (`integrity`, `x1_exposure`, `x1_braking`, `decisions`, `operating_map`, `map_all`), its independent re-computation (`verify_*`), the critic (`critic`), the revision's own checks (`revise`) and the checks of revisions 2 and 3 (`check_r1`, `check_r2`). `verified_material.json` and `map_all_verified.json` hold each analysis's findings with its verifier's verdicts; `critic_round1.json` holds the first critic's issues.

The scripts ran from a session scratchpad, so some hold `/tmp/claude-1000/.../scratchpad/s01/` paths. The full set, with the large intermediate files left out here (pickles and arrays, 158 MB), is in `/home/catalin/work/phd/v5b1_runs/s01_analysis/`; to re-run a script, point those paths there. Input data: `/home/catalin/work/phd/v5b1_runs/measure_s01_remote/`. No script runs a simulation.
