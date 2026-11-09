# Replication of three open implementations, protocol v0

**Status: DRAFT, not approved, nothing run (V484, 2026-11-08).** It takes effect only after the author approves §8, including the seed block and the budget. Evidence so far: [audit.py](../replication/audit.py) (read-only, facts checked at pinned commits).

Purpose: show that this project can run other groups' controllers, and find out how much of their reported effect survives a common protocol. It feeds thesis §"A replication programme" (`docs/thesis/chapters/ch02_literature.tex`). It changes no Plan B claim and uses no Plan B seed.

## 1. Targets

| Name | Repository | Commit to run | Licence | Handling |
|---|---|---|---|---|
| ACMPC | BelkhatirResearchLab/adaptive-compliance-mpc-rl-motorway-traffic | `6cca815` (HEAD); `a3f09e7^` for the final RL configuration | MIT | Keep the notice if code is copied |
| vsl2 | via-life/vsl2 | `4819675` | BSD 3-Clause | Keep the notice if code is copied |
| DWL-ST-VSL | kkusic/Multi_Agent_Based_Spatio_Temporal_Variable_Speed_Limit | `c040edc` | GPL-3.0 | Never copied into this repository; E5 reimplements from the paper |

## 2. Evidence ladder

| Level | Question | Simulation |
|---|---|---|
| E0 Inventory | What exists, at which commit, under which licence? | none |
| E1 Recomputation | Do stored results give the reported numbers? | none |
| E2 Execution | Does the pipeline run at its declared versions, and does a stored seed repeat? | pilot |
| E3 Claim reproduction | Does the reported effect appear with fresh seeds on the same plant? | yes |
| E4 Common protocol | Same controller and plant under fresh paired seeds, a closed metric, tuned opponents? | yes |
| E5 Transfer | Does the idea survive on r2m3? | yes, separate protocol |

A level is attempted only after the one below it passes or is recorded as impossible. E5 is out of scope here and needs its own protocol and the author's pick (V310).

## 3. Rules

- **Isolation.** Their code is untrusted. It runs only in disposable containers on rented machines (V483), one image per project. Nothing from their checkpoints or `.npy`/`.pkl` files is loaded on the laptop.
- **Their versions first.** E2 and E3 use the declared stack. A second E3 row at SUMO 1.27.1 reports version sensitivity.

| Project | Python | SUMO | Other pins |
|---|---|---|---|
| ACMPC | at least 3.11 (numpy 2.3.4; to confirm at build) | 1.24.0 | casadi 3.7.2, csnlp 1.6.8, sym_metanet as in `requirements.txt` |
| vsl2 | 3.10.10 | **not recorded**, E2 decision D-a below | ray 2.9.3, torch 2.0.1, numpy 1.23.5, gymnasium 0.28.1 |
| DWL-ST-VSL | 3.10.4 | 1.13.0 (README; the papers used an older one) | numpy 1.23.0, scipy 1.8.1 |

- **Minimal patches only.** Allowed: paths, headless SUMO, a seed argument, logging. Each patch is a recorded diff; none may touch control logic, rewards or metrics at E2 or E3.
- **Ledger.** Every run is logged, including failures and abandoned attempts.
- **Statistics (E3, E4).** Paired seeds, median of paired differences, 95 % percentile bootstrap, Bonferroni within a project. The same convention as the thesis.
- **Before each batch:** the resource check and the smoke check (outputs carry the inputs).

## 4. Pass criteria, fixed before any run

**E2.** Pass = the unpatched control logic completes a full run and writes the expected outputs. Same-seed agreement is reported separately: *repeated* if the headline metric is within 1 % of the stored value, *runs but not repeated* otherwise.

**E3.** Let D be the authors' reported effect and CI the 95 % interval of the fresh-seed median paired effect, on their own metric.

| Outcome | Condition | Thesis wording |
|---|---|---|
| Reproduced | D inside CI, and CI excludes 0 | "reproduced at n seeds" |
| Direction only | CI excludes 0, same sign, D outside CI | "the direction reproduced; the size did not" |
| Not reproduced | CI includes 0 | "no effect detected at n seeds" |
| Reversed | CI excludes 0, opposite sign | "the effect reversed" |

E3 needs a reported D. ACMPC's repository holds none, so ACMPC stays at E4 unless the authors supply one or a publication appears.

**E4.** Report-only, per project. Metrics: the authors' metric beside door-to-door delay with insertion queues, served throughput and time spent in a fixed window, plus collisions, teleports, and hard braking at step resolution. Opponents, all tuned on tuning seeds with the same budget: no control, best constant limit (grid), a tuned proportional speed law; ALINEA added for ACMPC. A learner that loses to its tuned opponents is reported as such. The wording never says "better" without naming the opponent.

## 5. Plan per project (order: cheapest evidence first)

### vsl2

1. E2: replay the stored 10 % checkpoint on seeds 101-103, with and without control, in a container. No training needed.
2. E3: same checkpoint, 40 fresh paired seeds, D = 5.46 % mean travel time.
3. E3b: retrain at 10 % with 5 training seeds (5 × 1,000 episodes), to test whether the near-zero worker output (mean 0.0026 m/s) is typical of training or of this checkpoint.
4. E4: add a metric over the whole road (load edge to downstream edge, with insertion delay), and the opponents of §4.

### DWL-ST-VSL

1. E2: one short training run (patches: paths, headless), then a full 14,000 + 100 run, one training seed.
2. E3: 5 training seeds; each policy evaluated with learning off on 40 fresh SUMO seeds. D from the papers (must be read first). Report the mean over seeds and, separately, the paper's selection rule if it uses one.
3. E4: resample demand between seeds; add the opponents of §4. The proportional comparator of the journal paper is absent from the code, so it is reimplemented from the text and labelled so.

### ACMPC

1. Blocker: `micronet/` is in no commit. Route A: the author asks the maintainers for it (recommended). Route B: rebuild from `network.py` and `scenario.json`, labelled a re-creation, so E2 and E3 become weak evidence.
2. E2: one coordinated run at constant α = 0.01; one RL run at `a3f09e7^` with the final configuration.
3. Seed check: two runs, identical settings; if the stored SUMO seed is really constant, the only variation is solver timing. Report it. Then add a seed argument (a permitted patch).
4. E4: 40 fresh paired seeds; adaptive α against best constant α, on scenarios s1, s2 and s4, and the opponents of §4.

## 6. Budget

Run counts are exact from the code; **rates are not measured**. A pilot of 10 runs per project (cap $2 in total) measures seconds per run first; no longer batch is launched before it.

| Item | Simulated runs |
|---|---|
| vsl2 E2 | 9 |
| vsl2 E3 | 80 |
| vsl2 E3b training | 5,000 episodes of 5,700 steps |
| DWL one training | 14,101 |
| DWL E3, 5 seeds | 70,505 training, plus 5 × 40 evaluation and 40 no-VSL |
| ACMPC E4 | 3 scenarios × 40 seeds × arms (about 5), each 90,000 steps with 37 solves, plus tuning |

Illustration only, not an estimate: if a DWL run took 60 s on one effective CPU, five trainings would be about 1,175 CPU-hours, or about $6 at the last rented rate (V475: $0.312/h for about 61 effective CPUs). The cost is unlikely to be the constraint; author time is. Per-project caps are fixed in §8.

Author time, separately: reading 3 Kušić papers (needed for E3), writing to two sets of maintainers, approving §8.

## 7. Seeds

Proposed: **7,500,000-7,500,999, not approved.** A scan of `docs/decisions.md` and the protocols finds no use of this block; a full scan of every ref is repeated at approval, as for Plan B. Partition: 000-099 pilots and smoke; 100-299 tuning; 300-699 evaluation (40 per cell, used once); 700-999 reserved. Original seeds (101-103, 28815, 42) are used only for repeat checks at E2.

## 8. Decisions needed before this runs

| # | Decision | Recommendation | Pros | Cons | Weaker alternatives |
|---|---|---|---|---|---|
| D1 | Scope | E0-E4 for all three; order vsl2, DWL, ACMPC | Cheapest evidence first; vsl2 already has a checkpoint | Longest for DWL | E0-E2 only: proves it runs, says nothing about the effects |
| D2 | Timing | After Plan B's S6 is read | Keeps attention on the thesis claim | Replication results arrive later | In parallel: splits author attention |
| D3 | Contact maintainers | Yes, for ACMPC's network and DWL's scenario II, after E1 | Fair to them; unblocks ACMPC | Depends on replies | Rebuild without asking: weak evidence |
| D4 | Seeds | Approve §7 | Fresh block | None seen | Reuse any earlier block: forbidden |
| D-a | vsl2's SUMO version | Start from SUMO 1.19, my estimate of the era of the pinned Ray 2.9.3 (to confirm); report the version used | Reversible; recorded | Replay may fail the 1 % check | Try every release: cost without an inference |
| D5 | Budget caps | $2 pilot; then $30 total, per-project split after the pilot | A hard stop | Rates unknown until the pilot | No cap |

## 9. What this protocol cannot show

E4 on their plants says nothing about r2m3. A pass at E3 reproduces an effect on that plant, with that code; it does not validate the plant. A failure at E3 may come from software version drift, which is why E2's same-seed check and the SUMO 1.27.1 row are reported beside it.
