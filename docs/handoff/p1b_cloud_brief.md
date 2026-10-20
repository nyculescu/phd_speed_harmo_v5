# P1b brief for a Claude Code cloud session (self-contained)

You are continuing a PhD project. This file and the repository are your **only** context. You cannot see the earlier conversation or the author's local memory. Read this first, then `docs/handoff/p1b_status.md`, which says what to do **now**.

## 1. Project in five lines

- **Thesis:** "Adaptive driving algorithms for intelligent road traffic systems". A solo, part-time author in the 6th year; submission ≈ Sept 2027.
- **Supervision:** the author and Claude set the scientific bar together (V95, `docs/decisions.md`). The **only hard constraint** is the title. The author decides; you are a critical co-supervisor.
- **Current paper:** "How much incident information does mainline metering need?", target **IEEE ITSC 2027, deadline 1 March 2027**.
- **P1 is done and verified:**
  - result note: `docs/research/results/p1_result.md`;
  - protocol: `docs/research/protocols/p1_incident_information.md`;
  - prior art: `docs/research/prior_art_P1_P2.md`, including the mainline section.
- **P1b** (approved in principle by the author: "go P1b") repeats P1 with these realism and fairness fixes.

## 2. What P1b changes (everything else as in P1)

1. **Amber phase (3–4 s) plus minimum green and red** at the mainline meter. Report the approach speed at red, and emergency stops per arm.
2. **Amber and red runners** as a sensitivity row. A vType distribution with a share s ∈ {0, 10, 30} % of drivers using SUMO's `jmDriveAfterYellowTime`, `jmDriveAfterRedTime` (1–2 s) and `jmDriveRedSpeed`.
   - The parameters exist in SUMO 1.27.1. **Verify their behaviour with a test** before relying on them.
   - Look up published meter-violation rates [VERIFY], and fix the shares **before any data**.
3. **PI-law plans in the L1/L2 action set:** incident plans may switch to PI-ALINEA settings. This removes the controller-family confound noted in P1 (V103).
4. **Report max meter queue against the available upstream length.** No queue cap unless the queue exceeds that length.
5. **Fresh seeds, proposed, needing the author's approval:**
   - tool checks 7,400,260–279;
   - tuning 7,400,300–339;
   - evaluation 7,400,600–699;
   - replicate seeds derived as in P1 (seed + k × 10,000,000);
   - smoke runs only on 7,400,000–009.

## 3. Binding rules (from `CLAUDE.md` and `docs/decisions.md`)

- **Protocol before data.** P1b is written as an **addendum** to the P1 protocol: `docs/research/protocols/p1b_addendum.md`, DRAFT. Nothing runs on protocol seeds before the author approves it in a new V entry.
- **Never run protocol seeds in the cloud.** Smoke runs on 7,400,000–009 only.
- **Bug rule:** a bug found after results means fix, re-run everything affected with the same seeds, and report both outcomes.
- **Honesty:**
  - no novelty or "first" claims;
  - mark unread sources [VERIFY];
  - report the full operating map and every rival;
  - never present report-only or descriptive numbers as claims;
  - this is **mainline** metering, not ramp metering.
- **Record every author decision** as the next V number in `docs/decisions.md`, committed in the same turn.
- **Git:**
  - work on branch **`p1b-cloud`**;
  - commit messages end with `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`;
  - push only `p1b-cloud`; never rewrite history.
- **Effort:** a protocol design review and a pre-run code review each use an adversarial review (reviewers that try to refute their own findings). The P1 reviews caught three outcome-changing problems: grid coarseness, selection-on-noise, and a meter-phase bug.

## 4. Division of labour (cloud ↔ laptop via GitHub)

| Step | Who | Output | Status after |
|---|---|---|---|
| A. Write the addendum, run the design review, list the author decisions | cloud | `p1b_addendum.md` DRAFT | `NEEDS_AUTHOR_APPROVAL` |
| B. Build P1b, tests, smoke, code review | cloud (after approval) | code + tests on `p1b-cloud` | `READY_FOR_LOCAL_RUN` (with exact commit and launch command) |
| C. Run on the laptop | local session | results summary + `result.json` committed to `p1b-cloud` | `RESULTS_READY` |
| D. Verify and write the result note | cloud | `docs/research/results/p1b_result.md` | `DONE` |

**Why the run is local:**
- the author's laptop has 32 threads (P1 took about 9 h at 32 workers);
- raw output is several GB and never enters the repo;
- the run uses the CPU guard and a frozen git worktree.

**Code requirement for step B:** every hard-coded local path (`/home/catalin/...`) in `v5b/` must become configurable, through an environment variable `V5B1_RUNS` for the run directory, defaulting to today's path. That lets cloud smoke runs work. In the cloud, install SUMO with `pip install eclipse-sumo libsumo` [VERIFY version 1.27.1 to match the laptop].

## 5. Local facts (laptop only; for the launch command)

- **Toolchain:** `/home/catalin/work/phd/phd_speed_harmo_v5b1_toolchain/venv`. Before runs: `unset SUMO_HOME; export OMP_NUM_THREADS=1`.
- **Launch:**
  - `systemd-run --user` from a **detached worktree at the run commit** (never commit there mid-run);
  - 32 workers, CPU guard 0.90;
  - the author controls the cooling pad manually.
