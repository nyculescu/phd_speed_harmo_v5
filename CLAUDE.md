# PhD v5.B.1 (branch `v5b1`): working rules for Claude

**Scope (author decisions, 2026-10-13).**
- **v5.B.1 is the PRIMARY PhD line.** The v6 traffic-signal work (`phd_v6`, branch `claude/tsc-foundation`) is secondary: v5.B.1 runs take CPU priority, and the open v6 S0 decisions wait.
- **Ground-up restart.** The author: "I want to build the project from the ground up again, step by step." Branch `v5b1` starts with empty history and becomes the main branch.
  - The earlier v5 / v5.B work stays on its own branches as the archive (see Repo state). Nothing from it is assumed here.
  - Old code (CORR2X network, meters, trainer, CPU guard, ledger) is ported only when a step needs it, and each port is recorded in the commit message with its source branch and commit.
  - The v5.B decisions B1–B15 (`docs/v5b/design_v0.md` on `claude/v5b-core`) are **draft inputs**, re-confirmed by the author one step at a time. Exception: the seed block below stays approved.
- **Topic (as drafted):** coordinated zone controllers on a multi-bottleneck freeway. Actuators: per-CAV speed commands, ramp meters, per-lane speed limits for HDVs. Conventional versus learning-based control. Heterogeneous and, later, adaptive human drivers. The network is **not chosen yet**; CORR2X is one candidate.
- **Architecture draft:** Notion page "v5.B.1 system architecture: from research concept to implementable software". Its §11 deliverables live under `docs/architecture/`, `docs/testing/` and `docs/research/`.

**Claim rules: update (V83, V85, 2026-10-16).** For the algorithm-first line #1 (self-calibrating safety margin), **V83 claim rule A replaced D5.8** and **DRL was dropped**. Rule A: A1 valid in every gated cell; A2 a win over every A1-valid opponent in at least one gated cell, never clearly worse by more than the harm margin; headroom and the full operating map always reported (protocol `docs/research/protocols/confirmatory_1.md`). Line #1 closed VALID-ONLY (V85): no paper. **The thesis-level claim bar is under review** with the academic supervisor (V85, option 2). Until that decision, the D5.8 text below is the historical bar for the SUMO/DRL lines only.

**Claim rules (author decisions 2026-10-10/11; D5.1, D5.8 in `docs/plans/day_pattern_decisions_v0.md` on `claude/day-pattern-core`).**
- **The helper may be DRL or any other neural network** on top of a proven controller: a forecaster, a demand reconstructor, a model-error correction, or a scheduler. DRL alone is also a candidate under D5.8.
- **Pass bar (conditional bar, D5.8, 2026-10-11):**
  - the candidate is the **best learning-based controller on validation**, DRL alone or a hybrid;
  - it beats **no control by ≥ 10 %** (median paired difference, CI excluding 0, at the realistic demand level);
  - it beats the **best tuned proven controller** in **at least one pre-registered regime** (Bonferroni CI excluding 0);
  - it is **not significantly worse by > 5 %** in any pre-registered regime;
  - the full operating map is reported.
- **Fair vanilla DRL:**
  - a standard algorithm (PPO; SAC for continuous actions) acting directly on the same actuators, with the same observations;
  - the same training and tuning budget;
  - checkpoints chosen on validation only.
- **Tuned proven controllers are always reported**, per regime. They form the operating map (where the candidate wins, ties or loses). Never hide them.
- **Design principle (author):** universal superiority is not required. Actively search for conditional advantages, adaptation benefits, robustness improvements and identifiable operating regimes.
  - Pre-register before data: the regimes; the adaptation gain (the share of the fixed-tuned → per-day-tuned gap that the helper closes); the robustness rows.
  - Report all of them, with multiplicity control.
- **No "lie with statistics":** no cherry-picked seeds, no weak baselines, no hidden variants, no proxy headline metrics. Every run goes into the ledger, including failed and abandoned ones.
- **Why:** on a real corridor the literature caps any helper at ≈ 2–3 % over the strongest published logic controller, and ≈ 9 % over MTFC+PI-ALINEA (Frejo & De Schutter 2021, Seville; D5.1) [VERIFY].

**Thesis**
- title: "Adaptive driving algorithms for intelligent road traffic systems";
- submission ≈ Sept 2027; target 2 papers;
- thesis-level claim bar: **under review** (V85). Historical bar (D5.8): a learning-based controller beating no control by ≥ 10 % and the best tuned proven controller in identifiable regimes;
- framing: the ARC-IT functional view, TM20 / TM21 [VERIFY codes against the ARC-IT site]. No SOTIF.

## Repo state

- **Repository:** `/srv/shared/Workspace/phd/phd_speed_harmo_v5` (exFAT; formerly mounted at `/run/media/catalin/Shared/...`). Remote `git@github.com:nyculescu/phd_speed_harmo_v5.git`.
- **`v5b1` worktree:** `/srv/shared/Workspace/phd/phd_speed_harmo_v5b1`. The main checkout may hold an archive branch that another session uses; do not switch its branch without the author.
- **Archive branches (read only, never rewrite):**
  - `claude/v5b-core`: v5.B design B1–B15, CORR2X v3, the M demand generator;
  - `claude/day-pattern-core`: day-pattern project, BN4 R6+ (D5.10 conditional-bar PASS, chapter-level), the METANET STOP (D5.5) and the testbed T0 KILL (D5.14), decision log D1–D6.0;
  - `claude/vsl-lab-core`, `claude/vsl-lab-t*`: DRL lab infrastructure and tracks;
  - `claude/vsl-hybrid-v1`: Step 1 screen;
  - `main` (`ebba794`): pre-spin-off work.
- **This filesystem is exFAT:** symlinks are lost, so in-repo virtual environments do not work. Use `venv314` (below).

## Method (binding)

- **Early KILL.** If no arm (a tuned proven controller, or an informed oracle) beats no control by ≥ 10 % at the realistic demand level, the claim on that plant is KILLed. Design so that the KILL comes early and cheap.
- **Headroom H (report-only since D5.1):** H = (best non-learning − I) / best non-learning, with the paired CI lower bound > 0.
  - **I** = the same validated controller with parameters or strategy taken from a lookup table (hidden condition → parameters) tuned on the tuning seeds. Never the best grid point per gate seed.
  - "Best non-learning" includes the tuned validated controller, a **non-learning adaptive** scheduler, and an **MPC with a model or forecast fitted on separate seeds** (never the true model). Under D5.8 the MPC arm is optional; dropping it must be disclosed.
- **Prior:** published hybrid gains over fixed-parameter controllers are about **1.5–6 %** (macroscopic models); three v6 gates found 0–5 %. Expect a KILL.
- **Tool checks first, with criteria committed BEFORE they run:**
  - **T0** the actuator binds (a command changes flow and density; read sensors with libsumo `getLastIntervalVehicleNumber`, not `getIntervalVehicleNumber`);
  - **T1** a capacity drop exists without teleport artefacts, and control matters;
  - **T2** the mechanism: the best parameter differs across hidden conditions by enough cost (G ≥ 10 %; report-only for claims);
  - **T3** determinism.
- **Protocol before data.** Calibrate only on throw-away seeds, and disclose it. Every new round uses **fresh seeds**. Seed ranges must be approved by the author before use.
  - **Approved v5.B seed block (2026-10-13):** 7,400,000–009 calibration; 010–099 plant and tool checks; 100–299 tuning; 300–499 validation; 500–699 test; 700–999 reserved confirmatory; DRL training 7,410,000–7,419,999.
  - Seeds 7,100,000–7,399,999 belong to the archived tracks; never reuse them here.
- **Statistics:** paired seeds, medians, 95 % percentile bootstrap CIs; one convention (the median of paired differences). A bug after results means: fix, re-run everything affected, log both outcomes.
- **Metrics:**
  - primary = door-to-door delay **including origin and insertion (ramp) queues**, co-headlined with served throughput (lesson: `docs/lessons_metric_gameability.md` on the archive branches);
  - TTT always reported alongside (fixed window; unfinished vehicles counted to the window end);
  - never no-control alone in any table or text; tuned controllers always alongside;
  - side constraints (safety) with stated tolerances.
- **DRL budget (only after a GO):** ≥ 500 PPO updates per run, 3–5 training seeds, a convergence check, final policy only, checkpoints chosen on validation seeds only.
- **Literature:** mark anything not read in full [VERIFY]. Never invent titles, authors or numbers. No "first/novel" claims.

## Toolchain (measured 2026-10-01 and 2026-10-13; i9-13980HX 32 threads, 62 GB, RTX 4080)

- **Environment (own, separate from v6 since 2026-10-13, V14):** `/home/catalin/work/phd/phd_speed_harmo_v5b1_toolchain/venv` (ext4). Python 3.14.4, CPU torch 2.11, SUMO / libsumo 1.27.1, SB3 2.8.0, Gymnasium 1.2.3, PettingZoo 1.27.0, pytest 9.1.1; exact pins in `toolchain/requirements_lock.txt`. Never install into v6's `venv314`. Before runs: `unset SUMO_HOME; export OMP_NUM_THREADS=1`.
- **libsumo,** one simulation per process, unique file names that include every varying parameter and the PID.
- **Limits (author, 2026-10-05):**
  - **≤ 100 worker processes.** Plain runs use **32 workers on all hardware threads**.
  - **Check machine resources before every simulation batch.**
  - **CPU rule:** if system CPU utilisation (`/proc/stat`) is **> 90 % for 2 consecutive minutes**, pause until it is back at or below 90 %:
    - new jobs launch only while utilisation is < 90 %;
    - after 2 minutes above 90 %, the newest running job is paused (SIGSTOP), and one more every 30 s while the condition holds;
    - after 30 s at ≤ 87 %, paused jobs are resumed one per 30 s;
    - training pauses all of its env workers together.
  - The guard implementation lives on the archive branches (`vsl_lab/ops/guard.py`, `tests/test_guard.py`); port it before the first batch on `v5b1`.
  - **Thermal rule removed** (author, 2026-10-10). The package temperature is still logged per batch.
  - **Fans:** the cooling pad and laptop fans are driven by the systemd user unit `vsl-cooling` (code `vsl_lab/ops/cooling.py` on the archive branches). It is not running since the 2026-10-12 shutdown; restart only on the author's request (`/home/catalin/work/phd/tsc_lab_runs/s0_logs/restart_vsl_cooling.sh`). Never drive the pad or the laptop fan curves from batch or training code; never run `loud`/`unlock` without the author. No power-profile, power-limit or other system changes.
- **DRL training:** L learners × E SubprocVecEnv envs ≤ N_max, with `torch.set_num_threads(1)`.
- **CUDA** (`venv314cu`) only for large GNN/LSTM policies.
- **Long runs** go in their own systemd user unit (`systemd-run --user --unit ...`), outside the editor's cgroup.
- **Do not overlap heavy simulations with v6 runs.** Before each batch, check that the v6 sessions are idle; if that cannot be determined, require CPU load < 15 %.

## v6 boundary

- v6 lives at `/srv/shared/Workspace/phd/phd_speed_harmo_v6`. Do not modify v6 from this repo's sessions.
- Read only its handoff notes (`docs/handoff/`) unless the author asks for more; never open the v6 CF06 paths listed in v6 `CLAUDE.md`.

## Credits and git

- Background jobs only. Tail logs at most every 10 minutes. Never print raw run JSON. Do not re-read unchanged files.
- Commit summaries only (< 5 MB per file). Raw runs go under `/home/catalin/work/phd/` on ext4, not into the repo.
- Push via SSH: `git push git@github.com:nyculescu/phd_speed_harmo_v5.git <branch>`, only when the author asks. Check `git branch --show-current` first; never push from a detached HEAD.

## Effort and ultracode per phase (author, 2026-10-05)

Claude cannot change these settings itself. **Before each phase it asks the author to switch, in one line**, e.g. "Next: X. Suggest Extra High, ultracode off. Switch?". It also suggests switching back down after a checkpoint.

| Phase | Effort | Ultracode |
|---|---|---|
| Routine: data pulls, batch runs, monitoring, small fixes, status replies | High | off |
| Implementing the plant, opponents and training code | High | off |
| Writing a protocol (criteria fixed before data) | Extra High | **on** for its design review, then off |
| METANET calibration; the MPC opponent; any subtle numerics | Extra High | off |
| Checkpoint: plant and all opponents done, before the gate runs | High | **on** (adversarial code review) |
| Checkpoint: DRL training code done, before long runs | High | **on** (review) |
| Interpreting gate or confirmatory results; any thesis claim | Extra High | **on** (verify before reporting) |
| Stuck on a hard bug after two attempts | Max | off |
