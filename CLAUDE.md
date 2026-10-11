# PhD v5 repo: working rules for Claude (VSL hybrid spin-off)

**Scope (author decision, 2026-10-01).** VSL / speed harmonisation is re-opened in THIS repo for a spin-off:
- a **validated, published controller stays in the loop**, and DRL adds value on top of it (parameter or strategy scheduling, activation switching, a residual, or MPC-model correction);
- **do not replace the controller with DRL.** v5 tried that (TQC) and stalled.

**Scope update (author decision, 2026-10-01, second message; supersedes the bullets above where they conflict).** Plan: `docs/plans/vsl_drl_run_roadmap_v0.md` (the "DRL lab", branch `claude/vsl-lab-core` plus one branch per track).
- **Direct DRL is allowed again**, hybrid or not.
- **Exploratory DRL may start before a headroom gate.** All of it is exploratory, and every run goes into `vsl_lab/runs/ledger.csv`, including failed and abandoned ones.
- **A thesis claim** still needs:
  - a frozen candidate;
  - pre-registered comparators and metric;
  - one confirmatory run on reserved seeds against **tuned** baselines (roadmap §0, §9).
- **No "lie with statistics":** no cherry-picked seeds, no weak baselines, no hidden variants, no proxy headline metrics.

**Claim update (author decisions, 2026-10-10; D5.1 in `docs/plans/day_pattern_decisions_v0.md`).** It supersedes the claim bullets above and the headroom gate below where they conflict.
- **The helper may be DRL or any other neural network** on top of a proven controller: a forecaster, a demand reconstructor, a model-error correction, or a scheduler. DRL alone is a reference arm only.
- **Pass bar (conditional bar, D5.8, 2026-10-11; replaces the D5.1 bar):**
  - the candidate is the **best learning-based controller on validation**, DRL alone or a hybrid;
  - it beats **no control by ≥ 10 %** (median paired difference, CI excluding 0, at the realistic demand level);
  - it beats the **best tuned proven controller** in **at least one pre-registered regime** (Bonferroni CI excluding 0);
  - it is **not significantly worse by > 5 %** in any pre-registered regime;
  - the full operating map is reported.
  - Why: R6+ showed a well-designed plain DRL meter beating every tuned meter controller and the hybrid on BN4, so the D5.1 bar (hybrid vs vanilla DRL) pointed the wrong way.
- **Fair vanilla DRL:**
  - a standard algorithm (PPO; SAC for continuous actions) acting directly on the same actuators, with the same observations;
  - the same training and tuning budget;
  - checkpoints chosen on validation only.
- **Tuned proven controllers are always reported** next to the hybrid, per regime. They form the operating map (where the hybrid wins, ties or loses), not the pass bar. Never hide them.
- **Design principle (author):** universal superiority is not required. Actively search for conditional advantages, adaptation benefits, robustness improvements and identifiable operating regimes.
  - Pre-register before data: the regimes; the adaptation gain (the share of the fixed-tuned → per-day-tuned gap that the helper closes); the robustness rows.
  - Report all of them, with multiplicity control.
- **Why:** on a real corridor the literature caps any helper at ≈ 2–3 % over the strongest published logic controller, and ≈ 9 % over MTFC+PI-ALINEA (Frejo & De Schutter 2021, Seville; D5.1).

In the v6 repo (`/run/media/catalin/Shared/Workspace/phd/phd_speed_harmo_v6`) VSL stays excluded:
- **do not modify v6;**
- read only `docs/handoff/lessons_learned.md`, `docs/feasibility/gate0_perimeter.md`, `docs/plans/phase7_novelty_check.md` and `feasibility/results/bench/parallel_sweet_spot_20261001.md`;
- never open the v6 CF06 paths listed in v6 `CLAUDE.md`.

**Thesis**
- title: "Adaptive driving algorithms for intelligent road traffic systems";
- about 11 months left (submission ≈ Sept 2027); target 2 papers;
- the thesis must show a learning-based controller (DRL alone or a proven controller helped by DRL or another neural network) beating no control by ≥ 10 % and the best tuned proven controller in identifiable regimes (conditional bar, D5.8, 2026-10-11);
- framing: the ARC-IT functional view, TM20 / TM21. Check PSpecs and flows against v6 `docs/arcitwebsite-20260715/`. No SOTIF.

## Repo state

There are two identical mirrors of this repo:
- `/home/catalin/work/phd/phd_speed_harmo_v5`
- `/run/media/catalin/Shared/Workspace/phd/phd_speed_harmo_v5`

Work in ONE of them, confirmed with the author, and keep the other untouched.

**Canonical mirror** (author choice, 2026-10-01): `/run/media/catalin/Shared/Workspace/phd/phd_speed_harmo_v5`.

`main`: the previously uncommitted work (4 modified files and the May 2026 docs) was committed as `ebba794` with the author's approval. It is local only and has not been pushed.

**Branches:**
- `claude/vsl-hybrid-v1`: Step 1 screen;
- `claude/vsl-lab-core`: DRL lab infrastructure and roadmap;
- `claude/vsl-lab-t1-bottleneck`, `-t2-merge`, `-t3-ring`, `-t4-corridor`: one per track.
- **`claude/day-pattern-core`** (created 2026-10-05 from `claude/vsl-lab-core` at `2a79e5e`): **the day-pattern project.** It covers learning daily demand patterns for coordinated ramp metering and speed harmonisation over full days, on a real MnDOT corridor.
  - Author: "a big bump, like a new project". The repo stays v5, because v6 is assigned to traffic lights and intersections.
  - Front page: `docs/day_pattern/README.md`. All new day-pattern work goes on this branch; `claude/vsl-lab-core` is left as it was at the branch point.

**This mirror is on exFAT.** Its `.venv` has no `python` executable (symlinks are lost); use `venv314`.

## Method (binding)

- **Early KILL under the 2026-10-10 bar.** If no arm (a tuned proven controller, or an informed oracle) beats no control by ≥ 10 % at the realistic demand level, the hybrid claim on that plant is KILLed.
- **Headroom H (report-only since 2026-10-10, D5.1).** H is measured as a diagnostic of where the room is; it is no longer a claim prerequisite. Its definition is unchanged:
  - H = (best non-learning − I) / best non-learning ≥ **10 %**, with the paired CI lower bound > 0.
  - **I** = the same validated controller, with its parameters or strategy taken from a lookup table (hidden condition → parameters) tuned on the tuning seeds. Never use the best grid point per gate seed.
  - "Best non-learning" must include the tuned validated controller, a **non-learning adaptive** scheduler, and an **MPC with a model or forecast fitted on separate seeds**. Never give the MPC the true model.
- **Prior:** published hybrid gains over fixed-parameter controllers are about **1.5–6 %** (macroscopic models), and three v6 gates found 0–5 %. Expect a KILL; design so that the KILL comes early and cheap.
- **Tool checks first, with criteria committed BEFORE they run:**
  - **T0** the actuator binds (a limit change moves flow and density; check sensor reads: libsumo `getLastIntervalVehicleNumber`, not `getIntervalVehicleNumber`);
  - **T1** capacity drop exists without teleport artefacts, and control matters;
  - **T2** the mechanism: the best parameter differs across hidden conditions by enough cost (G ≥ 10 %; biased upwards, so a FAIL is a conservative KILL). Since 2026-10-10, G is report-only for claims: it shows the adaptation room, regime by regime;
  - **T3** determinism.
- **Protocol before data.** Calibrate only on a throw-away seed, and disclose it. Every new round uses **fresh seeds**. Seed ranges must be approved by the author before use.
  - **Approved on 2026-10-01:** the layout in roadmap §10, inside 7,100,000–7,399,999.
  - Per track *t*: 7,1t0,000–009 calibration; 010–099 plant checks; 100–299 tuning; 300–499 validation; 500–699 test; 700–999 reserved confirmatory.
  - DRL training: 7,2t0,000–7,2t9,999.
- **Statistics:** paired seeds, medians, 95 % percentile bootstrap CIs; one convention (the median of paired differences). A bug after results means: fix, re-run everything affected, log both outcomes.
- **Metrics:**
  - primary = door-to-door delay **including origin and insertion queues**, co-headlined with served throughput (see `docs/lessons_metric_gameability.md`);
  - yardsticks: the pass bar uses no control and a fair vanilla DRL (2026-10-10). A constant-cap baseline and the **tuned** validated controllers are always reported alongside. Never no-control alone in any table or text;
  - side constraints with stated tolerances.
- **DRL budget (only after a GO):** ≥ 500 PPO updates per run, 3–5 training seeds, a convergence check, final policy only, checkpoints chosen on validation seeds only.
- **Literature:** mark anything not read in full [VERIFY]. Never invent titles, authors or numbers. No "first/novel" claims.

## Toolchain (measured 2026-10-01; i9-13980HX 32 threads, 62 GB, RTX 4080)

- **Environment:** `/home/catalin/work/phd/phd_speed_harmo_v6_toolchain/venv314` (CPU torch; SUMO / libsumo 1.27.1, SB3 2.8.0), unless this repo's own env is confirmed working. Before runs: `unset SUMO_HOME; export OMP_NUM_THREADS=1`.
- **libsumo,** one simulation per process, unique file names that include every varying parameter and the PID.
  - v5 used socket TraCI. That is why ~140 workers paid off; with libsumo they do not.
- **Limits (author, 2026-10-05; replace the 2026-10-02/03 thermal guard and the 92 % concurrency rule):**
  - **≤ 100 worker processes.** Plain runs use **32 workers on all hardware threads** (the v6 sweet spot); E-core pinning is no longer used.
  - **Check machine resources before every simulation batch.**
  - **CPU rule:** if system CPU utilisation (`/proc/stat`) is **> 90 % for 2 consecutive minutes**, pause until it is back at or below 90 %:
    - new jobs launch only while utilisation is < 90 %;
    - after 2 minutes above 90 %, the newest running job is paused (SIGSTOP), and one more every 30 s while the condition holds;
    - after 30 s at ≤ 87 %, paused jobs are resumed one per 30 s. One at a time, because our own 32 workers are the load and pausing everything would thrash;
    - training pauses all of its env workers together.
  - **Thermal rule: removed (author, 2026-10-10: a proper cooling pad was bought).** The guard no longer pauses or blocks on temperature; the package temperature is still logged in each batch's `thermal.csv`. The old v6 hysteresis (95 ± 3 °C, 150 s holds, 99 °C emergency) can be turned back on with `"thermal": 1` in `/home/catalin/work/phd/vsl_lab_runs/ops/thermal.json` (re-read every poll), but only if the author asks.
  - **Code:** `vsl_lab/ops/guard.py` (unit-tested in `tests/test_guard.py`), used by `vsl_lab/ops/scheduler.py` and the `train_sb3.py` watchdog since 2026-10-05.
  - **Fans: the cooling pad (llano V12 Ultra) and the laptop fans (asusctl) are software-controlled by one controller** (author, 2026-10-10), `vsl_lab/ops/cooling.py` (tests `tests/test_cooling.py`), run as the systemd user unit `vsl-cooling`. It acts only under batch load (CPU ≥ 50 % over 60 s) and puts back what it changed 2 min after the load ends.
    - **Froonty's Focus** (Quick Settings; `~/.local/state/focus/mode.json`) picks the profile. Pad caps live in llano (`~/.config/llano/noise.json`): 1000 rpm by day, 600 rpm in quiet hours or Sleeping, none when Away. Laptop fans: firmware curves unless Away, then custom curves adjusted automatically (never weaker than firmware).
    - Do not drive the pad or the laptop curves from batch or training code; leave it to the controller. By hand, only through `llano.py`/`Pad` (never raw hidraw) and `asusctl`. Never run `loud`/`unlock` without the author. A manual change (Froonty, CLI) makes the controller hand that device over until the batch ends.
    - No power-profile, power-limit (`ppt_*`, `nv_temp_target`) or other system changes.
- **DRL training:** L learners × E SubprocVecEnv envs ≤ N_max, with `torch.set_num_threads(1)`. Torch's default threads made training 7–50× slower.
- **CUDA** (`venv314cu`) only for large GNN/LSTM policies.
- **Do not overlap heavy simulations with v6 runs.** The CPU is the bottleneck and runs at its thermal limit.
  - Before each batch, check that the v6 Claude sessions are idle or finished; if that cannot be determined, require CPU load < 15 %.

## Credits and git

- Background jobs only. Tail logs at most every 10 minutes. Never print raw run JSON. Do not re-read unchanged files.
- Commit summaries only (< 5 MB per file). Raw runs go under `/home/catalin/work/phd/` on ext4, not into the repo.
- Push via SSH: `git push git@github.com:nyculescu/phd_speed_harmo_v5.git <branch>`. Check `git branch --show-current` first; never push from a detached HEAD.

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
