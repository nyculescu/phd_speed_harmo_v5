# Exploration brief: where could learning-based control beat the tuned controllers?

For the "Project review with Fable 5.2" chat. Written 2026-11-10 by the Plan B session, after decision V501. This brief replaces §1 and §3 of `docs/handoff/2026-11-10_fable_project_review_handoff.md`. That note was written while S6 was still running, and its state is out of date. Its §5 rules still hold.

## 1. Goal

The author wants to know whether there is a credible way for per-CAV deep RL to show a measurable advantage over the best tuned non-learning controllers on this project's freeway problem. Four routes are open, alone or combined:
- **Improve the learner:** algorithm, inputs, actions, training or configuration.
- **Change the plant:** for example, give the controller more actuators.
- **Disturb the plant** so that fixed or tuned rules show weaknesses that an adaptive policy could avoid.
- **Hybrids:** DRL combined with a proven controller family.

Treat this as a search for the **conditions under which adaptation pays**, not as a hunt for any setting where DRL wins. This is the project's own principle: pre-register the regimes, the adaptation gain and the robustness rows, report all of them, and do not require universal superiority. A null result is an accepted outcome (V456). A direction that is likely to fail should be called that.

**Your deliverable is a design memo, not results.** Write it to `docs/research/exploration/drl_win_directions_v0.md`. It should hold:
1. **Evidence map.** For each reason DRL has not won so far (§3), the records that support it, cited by V-number or file:line. Add any reason you find that is missing from §3.
2. **Candidate directions,** at least ten, spread across the four routes. For each:
   - the mechanism by which DRL could gain;
   - why a tuned rule could not match it, and how the opponents get the same exposure as the learner (tuning on the same conditions the learner trains on);
   - the evidence in our records for and against;
   - related literature, marked [VERIFY] unless you read it in full;
   - what has to be built, including its effect on the plant's V&V record;
   - the cost, estimated as runs × measured rate (§4), with author time stated separately;
   - the risks: forking paths, a metric that is also in the reward, a straw-man opponent.
3. **A headroom screen for each of the top three.** Use a cheap test, run before any DRL training, that could KILL the direction. For example: can any controller, even an oracle with information a real controller would not have, beat the best tuned rule by a stated margin on the primary metric? For each screen, give the comparator set, the KILL threshold fixed before data, the run count and cost, and the seed range you would ask the author for (a proposal only).
4. **A recommendation** in the project's format: the recommended option with its pros and cons, the weaker alternatives and why each is weaker.

## 2. What is established (as of V501)

- **Plant (r2m3, `plant_c3`).**
  - SUMO 1.27.1; synthetic and uncalibrated.
  - Three main lanes and two on-ramps 1.2 km apart.
  - 50 % automated vehicles (ALKS) with ideal V2V.
  - Main level 5,300 veh/h, with slowdown conditions X1 and X2.
  - Documented in `docs/research/baseline_v3/BASELINE.md`, `baseline_v4`, and the outline `docs/thesis/outline_v1.md`.
- **The incumbent policy, v3w.**
  - Per-CAV PPO: one shared actor sees 16 normalised local inputs and, every 10 s, picks the car's time headway: 1.6, 1.2, 1.0 or 0.8 s. A centralised critic sees global state during training.
  - Training: 5 learners × 3 environments, 500 updates, demand cycling through 4,500-6,000 veh/h, with random slowdowns.
  - Its checkpoints were chosen on validation seeds. It has been frozen since 2026-11-06 (hashes in `docs/research/baseline_v4/SHA256SUMS`).
  - Recipe: `docs/research/protocols/round_1.md`. Reward form: `docs/research/baseline_v0/BASELINE.md` §Reward. Check the code for the current weights.

**Results, in order** (`docs/research/results/`, ledger `docs/decisions.md`):

| Stage | Outcome |
|---|---|
| Phase 1 (r1m3, undisturbed) | about 30 % less delay than no control, but +0.0 to +2.3 % against the fixed 0.8-s rule: a tie. The policies rediscovered 0.8 s everywhere. |
| Confirmatory 2 | 1 of 20 cells won, on close-following only (V359) |
| Confirmatory 3 | X2 won at the minimum, not replicated on fresh seeds (V395, V401) |
| Round 1 | v3w beats the tuned rule grid on close-following by 22-46 %. No delay win. In X1 it has more close-following than no control (V449, V452). |
| Round 2 | X1 won T2 against the rules that counted; the cell's own CMA-ES rule did not pass the delay filter, so it was not tested against. X2 closed (V466; `round_2_result.md`). |
| Plan B S6 (TRUCK: 10 trucks capped at 40 km/h; 23 opponents including per-cell CMA-ES rules, MPC-F and ASCH) | **T, study NULL.** Close-following is better against all 23 opponents (smallest margin +11.8 % [+5.0, +19.7]), but delay is not shown better against 9 of them, and only 3 of 5 learners are consistent (V496, V501). |

**Already tried, and not better than v3w:**
- Round 1's residual-on-rule (res), attributed delay (attr) and PPO-Lagrangian (lagr, which ended at its λ cap). The protocols are `docs/research/protocols/round_1.md` and `round_2.md`.
- Round 2's trained candidates 2B, 1B, 1D, ahead (look-ahead inputs) and rep (repeated slowdowns), and its evaluation-only candidates tail (tail-averaged) and sw (zone-switched hybrid).
- B-LOO, dropped before it ran because its estimator was biased on this plant (V445).
- Training on varying demand: the author has chased this before and judged it not worth it (V411).

**Exploratory hints, not evidence:**
- Demand sweep (V409): v3w had 10-49 % fewer close-following seconds than the rules at most levels. But the rules were tuned only at 5,300, which favours DRL away from that level.
- Demand profiles (V410), 10 seeds: under a step change DRL was best, under a slow sine better than the rules, under a fast sine no different, and under a peak worse on close-following.

**Earlier lines where adaptation did not pay:**
- a self-calibrating safety margin on real trajectories: valid, but no win (V85);
- mainline metering on a realistic capacity drop: KILL (V149);
- mobility results withdrawn as a plant artefact (V256).

## 3. Why DRL has not won so far: the working hypotheses for you to test against the records

1. **For delay, a fixed short headway is close to optimal.** Shorter gaps raise capacity, and the 0.8-s rule already captures most of that.
2. **The persistent edge is on close-following (TTC below 3 s), and that measure is also in the reward.** Optimising the metric you are judged on is not independent evidence of safety. Against no control the policies are not safer.
3. **The lever is narrow.** One headway level every 10 s, chosen from local state, with no memory and no look-ahead.
4. **Tuned and machine-searched rules absorb the remaining headroom.** Rules traced from the policies came close (V361, V368).
5. **Honest testing removes fragile wins.** Some wins depended on which rules passed a filter, or did not replicate on fresh seeds.

## 4. Numbers for cost estimates

| Item | Measured rate | Source |
|---|---|---|
| Plant run, idle laptop | about 21 s | V443 |
| Plant run, rented machine under full load | about 55 s | V443 |
| S6 with the full measurement pack | about 1,400-1,690 runs/h on 90 workers | V493 |
| One PPO training set (5 learners × 3 environments) | about 23.5 s per update on the laptop when nothing else runs; 500 updates | V391-V392 |
| Rentals | about $0.12-0.80/h; recent rentals $0.02-$9.9 each | V490-V499 |

**Budget caps:** the $40-per-7-days ceiling stays. V488's $20 cap applied to Plan B's rentals and now stands at about $17.50.

## 5. What you may do, and what needs the author first

**Free to do, with no approval needed:**
- Read anything in this repo, the archive branches and the run folders under `/home/catalin/work/phd/v5b1_runs/`, including the ledger, protocols, results and code.
- Search the web and the literature.
- Write the memo and scratch analysis scripts.
- Run small read-only analyses of stored rows on the laptop (no simulation), at `nice 19` and single-threaded.
- Use subagents for independent sweeps of the records or the literature, and give each a full brief. Each subagent costs tokens, so use one only when the reading is large or the work is parallel. One adversarial critic of your top three is worthwhile before you finish.

**Ask the author first, naming the exact action:**
- **Any simulation or training.** It runs on a rented machine only (V483), so it also needs a rental.
- **Any rental or spend.**
- **Any seed range,** because seeds need approval before use.
- **Any commit or push.** Write the memo file, but commit only when asked.
- **Any ledger row.** Rows record decisions the author has made, never proposals.

When the author approves, take exactly that action.

**Do not touch:**
- the worktrees `~/work/phd/wt/planb` and `~/work/phd/wt/planb_v23`, which are the record of the S6 reading;
- the v6 repository;
- archive branches, which you may read but not write.

**Honesty rules,** because the thesis's credibility rests on them:
- A win found while exploring is exploratory. It counts only after a protocol fixed before data, confirmed on fresh seeds.
- A disturbance is fixed before any control result on it is seen (V456).
- Opponents get the same exposure to a disturbance as the learner.
- Every new condition explored adds to the count of cells tested (planb.md:145), so list the cells each direction would add.
- No "first" or "novel".
- Never invent a source, a number or a quote. Mark anything you have not read in full as [VERIFY].

## 6. How to work and report

- Before you start, say in a line what you are about to do. Brief updates while you work help the author follow along. Close with a short recap that stands on its own: what you found, what you did, and what comes next.
- **Work in two phases.**
  - **Phase A,** at High effort with ultracode off: the evidence map, the candidate directions and a first ranking.
  - **Phase B,** the stress test of the top three and their headroom screens. This is protocol design, so the project's phase table asks for Extra High effort with ultracode on for its review. When Phase A is done, ask the author in one line to switch, then continue.

### Finishing work
Please avoid stopping while you still owe work the user asked for. Be persistent and do not stop unless needed.

While status notes are welcome, as is clarifying with the user on open decisions, carry on with work that does not depend on the user's answer without unnecessary stops.

If you notice yourself inviting the user to redirect you or offering to wait, instead proceed on the next part of the task. You may meet ordinary obstacles like errors, timeouts, locked files, empty results or failing tools. Diagnose them first, and when they are not real blockers, work through them with the access you have (wait and retry, fix the request, use another tool or source) rather than stopping unnecessarily.

If someone clearly decided something is a hard blocker, such as a file marked not to be touched, access that was intentionally withheld, or a safety guardrail, leave it alone, say plainly what you found, and look for another safe way to finish the task. Stopping before the task is complete is very rarely merited, as in when the task can't move forward without user input, or where the blocker is deliberate and should not be worked past. This does not override the need for confirmation on risky or destructive actions.

### Communicating clearly
Write for an intelligent but low-context reader. The person reading has not seen your tool calls, your reasoning or the files you opened, and may be switching in from other work. Messages should generally be self-contained: the reader should understand what you mean without having to dig for other context. Put the key points in the first few sentences. Practice progressive disclosure in your sentence order, and do not use undefined references and ideas in line 1 that won't make sense until the reader reaches line 12.

Use plain words, and write in clear, understandable full sentences. Do not use a term or abbreviation that you made up during the work. Say what the thing is in a way any reader would understand. Write mostly in the style of ASD-STE100 Simplified Technical English: short sentences, one idea per sentence, active voice, and consistently using the same word for the same thing. Use a paragraph of flowing prose where ideas connect, and keep bullets for lists of separate items. Leave out unnecessary details unless the reader asks and practice concision, but do ensure that your messages have the key context. Aim to make your user-facing text as human-readable and clear as possible.
