# P1 verification evidence (for `../p1_result.md`)

Independent checks of the P1 run (V102), done on 2026-10-20 before the result note was written. Inputs: the run files in `/home/catalin/work/phd/v5b1_runs/p1/v99/runs/` and `result.json` there, and the frozen code `/home/catalin/work/phd/p1_frozen_85f7d34` (`85f7d34`). The run directory and the frozen tree were not changed. The only simulations are the 26 spot re-runs below.

## What was re-derived

- `load.py` reads the 281,981 run files of the tuning (7,400,200–239) and evaluation (7,400,500–599) seeds into `recs.pkl`. `rederive.py` does **not** import `v5b`. It re-tunes every arm (N, FX, FB, PI, AD, ID, IP and the π-retuned arms) and recomputes S1, S2, TP, S3, the combined row, the Table 1 and clean-day medians, the false-alarm cost and f*(π). Outputs: `out/mine_page.json` (the page's bootstrap draws, seed 20261019) and `out/mine_own.json` (an independent seed).
- `compare.py` compares **3,364 scalar values** with `result.json`. They are: the arm choices per q (main and π-retuned); per cell, every S1 statistic (ID vs each L0 arm, IP vs ID, IP vs each L0 arm: ref, treat, diff, rel and both CI bounds); S2 (OR_in and ORX_1/2/4, median and mean versions, plateau, x, y, ŷ, plateau flag); TP; S3 (d*, c*, p*: value, flag, binding arm, CI, censoring shares, per-arm value and M curve); the combined row; Table 1 medians; clean-day medians; the false-alarm cost; f*(π); the S1 pass flags and cells. Result: 0 mismatches with the page draws (`out/compare_page.log`). With the independent seed, 385 values differ, all of them CI bounds or CI-derived values (x, y, censoring shares); no verdict, flag or binding arm changes (`out/compare_own.log`).
- `a1.py`–`a5.py` (rivals and fairness) read `runs.pkl`, an index of all 296,527 run files. They check signal, commit, validity, teleports, the switch schedule (226,413 switch runs) and "N before onset" (224,801 runs). They also re-tune the arms, recompute S1, test the controller-family question (`a3`, `a4`) and the ID choice (`a5`). Their printed outputs were not saved; the numbers are quoted in the note.
- `prev/` (clean day and prevalence): `prev_check.py` builds `delays.json`; `analyse.py`, `analyse2.py` and `clean.py` give `prev/out/*.log` and `prev/out/prev_out.json`.

## Numbers in the note

- `note_numbers.py`: every `result.json` number the note uses (`out/note_numbers.log`).
- `make_tables.py`: Tables 1 and 2 of the note (`out/make_tables.log`). Pre-registered numbers are copied from `result.json`; descriptive rows are recomputed with the frozen `v5b.p1.stats.paired` (seed 20261019, B = 20,000).
- `ip_checks.py` (IP vs each L0 arm at 95 %, IP with detection delay vs ID, the runner-up ID, OR_in picks with n_crit = 16), `clean_paired.py`, `orin_es.py`, `safety.py` (all 50,061 non-replicate evaluation runs), `safety3.py` (emergency stops per arm): outputs in `out/`.
- `chk.py`, `chk2.py`, `check_note.py`, `dcheck.py`, `idtie.py`, `tune_id.py`, `ad.py`, `safety2.py`: the checker's spot checks; outputs not saved.

## Spot re-runs (26)

`rerun.py` (16 specs) and `spot.py` (10 specs) re-ran stored run specs with the frozen code (`python -m v5b.p1.episode`, 8 workers) into a scratch folder. `rerun_compare.py` → `out/rerun_compare.log`: 26 of 26 identical in hash, delay, served throughput, TTT, max queue, meter log, switch times and the valid flag.

## How to re-run

Paths are hard-coded as they were run (a session scratchpad under `/tmp/claude-1000/...`); edit them first. Scripts that import the frozen code must run as `python -I -B` with the toolchain venv, so no bytecode is written into the frozen tree. Not copied (too large): `runs.pkl` (365 MB), `recs.pkl` (134 MB), `prev/delays.json` (4.7 MB) and the SUMO outputs of the re-runs.
