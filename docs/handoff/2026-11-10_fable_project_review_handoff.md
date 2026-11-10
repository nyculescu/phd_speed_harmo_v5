> **Superseded in part (2026-11-10, after V501):** §1 and §3 describe the state while S6 was running. Current state and the exploration task: `docs/handoff/2026-11-10_fable_drl_exploration_prompt.md`. §5 still holds.

# Handoff: project review with Fable 5.2 (2026-11-10)

For the new chat. CLAUDE.md and the memory index load on their own; this note adds the live state and candidate review approaches. Read it before anything else.

**Mode: discussion only.** The author wants to discuss possible approaches first. Do not start any review: no agents or workflows, no reading of S6 rows or `read6.py`, no new folders, no ledger rows except for decisions the author actually makes. Section 4 is a starting point for that discussion, not a plan to carry out.

## 1. Who owns what

- **The Plan B session (Opus 5.5, the chat that wrote this) owns the running S6** on vast.ai instance 59973644 (`ssh -p 13379 root@174.88.252.223`, job `planb_s56`). It polls, fetches, verifies, destroys and runs `read6`.
- **This chat must not:**
  - SSH to that host or rent or destroy any machine;
  - stop the user units `planb-s56-watch` or `planb-s34-watch`;
  - commit on `planb/core` or edit `~/work/phd/wt/planb`, the frozen code (S5-S6 run at b0c9360, whose diff from 96fde8d must stay the picks file only).
- **Shared ledger:** `docs/decisions.md` on `v5b1`. The next free number was V494 at writing time. Read the tail before adding a row (two sessions once both wrote V484). One row per author decision, committed the same turn.
- No simulation on the laptop (V483).

## 2. The Fable facts are unverified

The author saw a Reddit summary claiming Fable-only usage resets (1-3, varying), a high token cost, and a much higher cost at Max effort. None of it is verified. The model list Claude Code gives its sessions names Fable 5.1 as the newest Fable, so check `/model` before assuming you run 5.2. Start at Medium or High effort, not Max.

## 3. Where Plan B stands (protocol `docs/research/protocols/planb.md`, approved V480)

- **Question:** v3w (frozen per-CAV PPO policies) against tuned non-learning controllers under pre-registered perturbations on plant r1m3 (code name m32).
- **S2** (`docs/research/results/planb_s2_result.md`, V484-V487):
  - **As registered: KILL.**
  - The G4(ii) drain gate had no null and was replaced after it had been read (V486, a logged §11 deviation). Every TRUCK sentence must carry the §10 G4(ii) disclosure.
  - Under V486, TRUCK passes and SURGE drops. TRUCK fails G2-loss, so the best possible outcome is a level claim.
- **S3a-S4** (rental 1, V490): done at 96fde8d. Every check passed.
- **Freeze** (V491):
  - cells = TRUCK only;
  - 3E-C TRUCK is labelled **"not converged at 100 generations"**, a departure every 3E-C sentence must name;
  - 3E-D met the plateau criterion;
  - **ASCH's pick is the same controller as the fixed rule lr1000_16_2**, which is also the steady pick (an alias in the config);
  - MPC-F passed its gate.
- **S6** (V492-V493):
  - 58 arms × 240 seeds (7,480,400-639) = 13,920 runs;
  - 23 deciding opponents;
  - m = 2 (97.5 %);
  - drain cap 39.0;
  - about 1,400 runs/h, DONE expected about 09:45 UTC on 2026-11-10.
  - Rows will land, after fetch and SHA-256 check, in `/home/catalin/work/phd/v5b1_runs/planb_s56_remote/`:
    - `s6/s6_rows.jsonl`;
    - `jobs/read6_config.json`;
    - `jobs/s6_jobs.json`;
    - `s5/`;
    - `s1/`.
  - **Do not read S6 rows before the Plan B session reports them fetched and verified.**
- **Code** (branch `planb/core`, worktree `~/work/phd/wt/planb`): `docs/research/planb/` (`pb.py`, `plan6.py`, `run6.py`, `read6.py`, `drain.py`, `gates2.py`, `pr24.py`) and `v5b/fleet/`.
- **Thesis state:**
  - `docs/handoff/2026-11-07_thesis_writing_handoff.md`;
  - `docs/thesis/outline_v1.md` (V459);
  - writing phase V456, where a null DRL result is accepted;
  - the claim bar is set by the author and Claude (memory "thesis claim definition", V95).

## 4. Candidate approaches, to discuss (nothing is approved)

Open questions for the discussion: what the review should cover (the S6 reading only, or the whole project: plant V&V, protocol, code, thesis claim); what Fable adds over the Opus session; the token budget; and when it would run.

**1. Blind S6 recount (recommended).** Two or three Fable agents receive:
- `planb.md` §1, §5, §8 and §10;
- `read6_config.json`;
- the row path.

They don't get `read6.py`, the Plan B session's reading, or any hint about the result. Each one writes its own scripts and produces:
- the per-cell operating map (every opponent × measure: paired median difference, 95 % percentile bootstrap CI);
- the verdict (PASS, W vetoed by an L, or NULL);
- the must-carry disclosures.

Structured output goes to `/home/catalin/work/phd/v5b1_runs/planb_s6_blind/<agent>/`. The comparison with `read6`'s output comes only after both are written. Precedent: the S2 recount matched all 583 values (`pr24.py`).

A mismatch means one of two things:
- a `read6` bug;
- protocol text that can be read two ways.

In both cases the rule from CLAUDE.md applies: fix, re-run everything affected, log both outcomes.

**2. Adversarial review of `read6.py` against §8**, if a mismatch appears, or as a second pass.

**3. Lower value:**
- thesis prose: cheaper on Opus;
- the literature [VERIFY] items: they need the papers read in full;
- any status or polling work: wasted on Fable.

## 5. Rules that bite here

- **Phase table:** interpreting gate or confirmatory results is Extra High with ultracode on. Ask the author to switch in one line.
- **Statistics:** paired seeds, medians, 95 % percentile bootstrap CIs, the median of paired differences. Never no control alone. Tuned controllers always shown. Primary metric is door-to-door delay including origin and ramp queues, co-headlined with throughput; TTT is always reported.
- **Reading pitfalls** (memory "conf3 reading pitfalls"):
  - period bins are absolute time;
  - medians are not tests;
  - use the paired statistic;
  - use the harm reference;
  - write the full sentence.
- **Replies:** short, with diagrams; recommendation + pros/cons + inferior alternatives; estimates as runs × rate; label every uncertain claim.
- **Commits:** a one-line message of at most 50 characters, no Claude mention, and only when asked (ledger rows are routine).
