# PhD v5 repo: working rules for Claude (VSL hybrid spin-off)

**Scope (author decision, 2026-10-01).** VSL / speed harmonisation is re-opened in THIS repo for a spin-off:
- a **validated, published controller stays in the loop**, and DRL adds value on top of it (parameter or strategy scheduling, activation switching, a residual, or MPC-model correction);
- **do not replace the controller with DRL.** v5 tried that (TQC) and stalled.

In the v6 repo (`/run/media/catalin/Shared/Workspace/phd/phd_speed_harmo_v6`) VSL stays excluded:
- **do not modify v6;**
- read only `docs/handoff/lessons_learned.md`, `docs/feasibility/gate0_perimeter.md`, `docs/plans/phase7_novelty_check.md` and `feasibility/results/bench/parallel_sweet_spot_20261001.md`;
- never open the v6 CF06 paths listed in v6 `CLAUDE.md`.

**Thesis**
- title: "Adaptive driving algorithms for intelligent road traffic systems";
- about 11 months left (submission ≈ Sept 2027); target 2 papers;
- the thesis must show DRL beating or measurably improving rule-based, reactive or predictive control;
- framing: the ARC-IT functional view, TM20 / TM21. Check PSpecs and flows against v6 `docs/arcitwebsite-20260715/`. No SOTIF.

## Repo state

There are two identical mirrors of this repo:
- `/home/catalin/work/phd/phd_speed_harmo_v5`
- `/run/media/catalin/Shared/Workspace/phd/phd_speed_harmo_v5`

Work in ONE of them, confirmed with the author, and keep the other untouched.

`main` has uncommitted work as of 2026-10-01:
- 4 modified files: `core/env_interact.py`, `core/eval_metrics.py`, `docs/experiment_catalog.md`, `evaluate_models.py`;
- 4 untracked docs, including `docs/lessons_metric_gameability.md`.

**Never discard it.** Ask before committing it. Branch for the spin-off: `claude/vsl-hybrid-v1`.

## Method (binding)

- **Headroom gate before any DRL.**
  - H = (best non-learning − I) / best non-learning ≥ **10 %**, with the paired CI lower bound > 0.
  - **I** = the same validated controller, with its parameters or strategy taken from a lookup table (hidden condition → parameters) tuned on the tuning seeds. Never use the best grid point per gate seed.
  - "Best non-learning" must include the tuned validated controller, a **non-learning adaptive** scheduler, and an **MPC with a model or forecast fitted on separate seeds**. Never give the MPC the true model.
- **Prior:** published hybrid gains over fixed-parameter controllers are about **1.5–6 %** (macroscopic models), and three v6 gates found 0–5 %. Expect a KILL; design so that the KILL comes early and cheap.
- **Tool checks first, with criteria committed BEFORE they run:**
  - **T0** the actuator binds (a limit change moves flow and density; check sensor reads: libsumo `getLastIntervalVehicleNumber`, not `getIntervalVehicleNumber`);
  - **T1** capacity drop exists without teleport artefacts, and control matters;
  - **T2** the mechanism: the best parameter differs across hidden conditions by enough cost (G ≥ 10 %; biased upwards, so a FAIL is a conservative KILL);
  - **T3** determinism.
- **Protocol before data.** Calibrate only on a throw-away seed, and disclose it. Every new round uses **fresh seeds**. Seed ranges must be approved by the author before use.
- **Statistics:** paired seeds, medians, 95 % percentile bootstrap CIs; one convention (the median of paired differences). A bug after results means: fix, re-run everything affected, log both outcomes.
- **Metrics:**
  - primary = door-to-door delay **including origin and insertion queues**, co-headlined with served throughput (see `docs/lessons_metric_gameability.md`);
  - yardsticks = a constant-cap baseline and the **tuned** validated controllers, never no-control alone;
  - side constraints with stated tolerances.
- **DRL budget (only after a GO):** ≥ 500 PPO updates per run, 3–5 training seeds, a convergence check, final policy only, checkpoints chosen on validation seeds only.
- **Literature:** mark anything not read in full [VERIFY]. Never invent titles, authors or numbers. No "first/novel" claims.

## Toolchain (measured 2026-10-01; i9-13980HX 32 threads, 62 GB, RTX 4080)

- **Environment:** `/home/catalin/work/phd/phd_speed_harmo_v6_toolchain/venv314` (CPU torch; SUMO / libsumo 1.27.1, SB3 2.8.0), unless this repo's own env is confirmed working. Before runs: `unset SUMO_HOME; export OMP_NUM_THREADS=1`.
- **libsumo,** one simulation per process, unique file names that include every varying parameter and the PID.
  - v5 used socket TraCI. That is why ~140 workers paid off; with libsumo they do not.
- **Plain runs: 32 workers.**
- **DRL training: 120 workers = 5 learners × 24 SubprocVecEnv,** with `torch.set_num_threads(1)`. Torch's default threads made training 7–50× slower.
- **CUDA** (`venv314cu`) only for large GNN/LSTM policies.
- **Do not overlap heavy simulations with v6 runs.** The CPU is the bottleneck and runs at its thermal limit.

## Credits and git

- Background jobs only. Tail logs at most every 10 minutes. Never print raw run JSON. Do not re-read unchanged files.
- Commit summaries only (< 5 MB per file). Raw runs go under `/home/catalin/work/phd/` on ext4, not into the repo.
- Push via SSH: `git push git@github.com:nyculescu/phd_speed_harmo_v5.git <branch>`. Check `git branch --show-current` first; never push from a detached HEAD.
