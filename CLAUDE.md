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

**Canonical mirror** (author choice, 2026-10-01): `/run/media/catalin/Shared/Workspace/phd/phd_speed_harmo_v5`.

`main`: the previously uncommitted work (4 modified files and the May 2026 docs) was committed as `ebba794` with the author's approval. It is local only and has not been pushed.

**Branches:**
- `claude/vsl-hybrid-v1`: Step 1 screen;
- `claude/vsl-lab-core`: DRL lab infrastructure and roadmap;
- `claude/vsl-lab-t1-bottleneck`, `-t2-merge`, `-t3-ring`, `-t4-corridor`: one per track.

**This mirror is on exFAT.** Its `.venv` has no `python` executable (symlinks are lost); use `venv314`.

## Method (binding)

- **Headroom gate before any DRL *claim* involving a hybrid.** Since the 2026-10-01 scope update, exploratory DRL may run before it.
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
  - **Approved on 2026-10-01:** the layout in roadmap §10, inside 7,100,000–7,399,999.
  - Per track *t*: 7,1t0,000–009 calibration; 010–099 plant checks; 100–299 tuning; 300–499 validation; 500–699 test; 700–999 reserved confirmatory.
  - DRL training: 7,2t0,000–7,2t9,999.
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
- **Limits (author, 2026-10-01; replace the earlier 32 / 120 defaults):**
  - **≤ 100 worker processes and CPU package (`coretemp` "Package id 0") < 90 °C.**
  - Temperature is controlled **by worker throttling only.** No power-profile, fan or other system changes.
  - The thermal guard pauses jobs at ≥ 88 °C and resumes them below 82 °C.
  - The v6 benchmark hit 96–100 °C at 32+ saturated workers, so expect N_max ≈ 16–24, measured by the calibration in roadmap R0.4.
- **DRL training:** L learners × E SubprocVecEnv envs ≤ N_max, with `torch.set_num_threads(1)`. Torch's default threads made training 7–50× slower.
- **CUDA** (`venv314cu`) only for large GNN/LSTM policies.
- **Do not overlap heavy simulations with v6 runs.** The CPU is the bottleneck and runs at its thermal limit.
  - Before each batch, check that the v6 Claude sessions are idle or finished; if that cannot be determined, require CPU load < 15 %.

## Credits and git

- Background jobs only. Tail logs at most every 10 minutes. Never print raw run JSON. Do not re-read unchanged files.
- Commit summaries only (< 5 MB per file). Raw runs go under `/home/catalin/work/phd/` on ext4, not into the repo.
- Push via SSH: `git push git@github.com:nyculescu/phd_speed_harmo_v5.git <branch>`. Check `git branch --show-current` first; never push from a detached HEAD.
