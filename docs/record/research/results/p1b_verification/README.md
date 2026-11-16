# P1b verification evidence (for `../p1b_result.md`)

Single verifier, lean mode (V107, V111), 2026-10-20. Inputs: run files in `/home/catalin/work/phd/v5b1_runs/p1b/v108/runs/` and `result.json` there; frozen code `/home/catalin/work/phd/p1b_frozen_93ba655` (`93ba655`). Neither was changed. No script imports `v5b` except the spot re-runs, which call the frozen episode as a subprocess.

## Scripts (run with the v5b1 venv, `python -I`, `nice -n 19`, ≤ 4 processes)

- `load.py OUT.pkl`: reads the 330,302 tuning (7,400,300–339) and evaluation (7,400,600–699) run files into a slim pickle (kept outside the repo, `jobs/p1b_verify/recs.pkl`, 253 MB). key == filename for all.
- `rederive.py recs.pkl OUT.json page|own`: independent re-derivation of the protocol (adapted from `../p1_verification/rederive.py`): tuning of N, FX, FB, PI, AD, G_PI(q) (top 10 PI by pooled tuning median, R1), A(q) (120 actions; order G stay, G back, G_PI stay, G_PI back), ID, IP, the π-retuned arms; S1, S2, TP, S3, combined row, Table 1, clean day, false-alarm cost, f*(π); runner rows (R5); realism rows and the V109 spill indicator. Outputs: `out/mine_page.json` (page draws, seed 20261019), `out/mine_own.json` (independent seed).
- `compare.py mine.json`: 6,217 scalar values vs `result.json`. **0 mismatches** with page draws (`out/compare_page.log`); with the own seed 654 differ, all CI bounds or CI-derived values (x, y, break-even CI and censoring shares); no verdict, flag or binding arm changes (`out/compare_own.log`).
- `rerun.py KEY...`: 6 spot re-runs into `jobs/p1b_verify/scratch/` (never the run dir); all identical on hash, delay and the P1b reporting fields (`out/rerun.log`).
- `spill.py`: V109 spill shares per arm and cell (`out/spill.log`). Indicator: `max_queue_m ≥ avail_m − 50` OR `depart_delay_s > 5`; also both parts and the old 7 m flag.
- `runners.py`: runner rows: sign check of rel = median(r − t) / median(r), per-arm self-comparisons, commanded rate, discharge by phase, seeds tipping (`out/runners.log`).
- `p1_vs_p1b.py`: P1 → P1b rows from both `result.json` files; emergency stops (`emergency_stops`, the same SUMO counter in both studies) and `emergency_meter` (`out/p1_vs_p1b.log`).
- `safety.py`: approach speed at red ≥ 10 m/s shares; IP vs each L0 arm at the S1 level (`out/safety.log`).
- `ip_alt.py`: IP's tuning runner-up plans evaluated on the main runs (`out/ip_alt.log`).
- `note_numbers.py`, `selfcheck.py`, `check_note.py`: every number in the note against `result.json` / logs (`out/note_numbers.log`, `out/selfcheck.log`, `out/check_note.log`). The 16 numbers `check_note.py` does not find are roundings of logged values (115.17, 168.48, 192.76, 210.06, 45.28), seeds, years, the S1 level 0.99375, or hand arithmetic: cycle c(1000) = 28,800 / 1,000 = 28.8 s (amber 3 / 28.8, red 19.8 / 28.8); costs at 9.6 runs/s (`stage_wall`: 255,182 runs in 26,460 s): (1) 8 arms × 100 seeds + 2 runner shares × 700 ≈ 2,200 runs; (2) 120 actions × 2 types × 2 q × 40 seeds = 19,200 tuning + ≈ 2,800 evaluation runs; (3) 75,120 tuning + 63,182 non-replicate evaluation runs.

## Findings outside the note's main text

- V112 says "tool checks 6,150": `run.log` shows three tool-check stages (6,150 + 8,160 + 240 = 14,550). Files: 344,852 = 14,550 + 75,120 + 255,182.
- `summary.md` line 3 names the base page but prints the addendum's sha256 (cosmetic). Both hashes in `result.json` match the current files.
- `commanded_mean_vph` is a mean over the control window, so for back plans it mixes N and the plan (IP slow_q1600: 1,523 veh/h; the plan's own rate is 1,000).
