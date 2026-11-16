# proj_facts: our trainer, its sizes, what was tried, what an SB3 port needs

CT = `/home/catalin/work/phd/wt/planb_v23/v5b/fleet/c_train.py` (its `gae`, `collect`, `update` equal round 1's snapshot `93ec97e`); BE = `b_env.py` beside it; 1B/ = `/home/catalin/work/phd/v5b1_runs/round2/code_5c10e6f/v5b/fleet/`; r1, r2 = `docs/research/results/round_{1,2}_result.md`; p1, p2 = `docs/research/protocols/round_{1,2}.md`; memo = `drl_win_directions_v0.md`; TB = event files under `/home/catalin/work/phd/v5b1_runs/round1_remote/out/train_*/tb` and `round2_remote/train_1b/tb`, read with `tbread.py` (scratchpad, standard library only). Nothing was trained, built or simulated; no SB3 capability is stated.

## 1. How the trainer forms a batch

- **Sample** = one due vehicle's decision: local 16, global 10, action, log-prob, value, and the mean reward over the env steps until its next decision (CT:240-244, :251-257, :220-224). Due = own clock reaches `hold` (BE:942-945). v3w: hold 10 s, step 5 s (`baseline_v5/policies_v3w/C0_config.json`).
- **Trajectory** = one vehicle in one env, first sight to exit. On exit it is "cut off, not ended": the bootstrap is the value at its own last decision (CT:3-4, :259-262).
- **Episode end:** every env truncates at 300 + 1,500 s, after 300 env steps (BE:102, :152; CT:25); live vehicles bootstrap from the critic on the final observation (CT:263-277).
- **GAE per vehicle** over its own decisions (CT:175-182, :279-287). The discount is per decision: v3w gamma 0.933, lambda 0.967 (config; default 0.8/0.9, CT:29).
- **Update** = one episode per env, 3 envs, flattened (CT:227-228).
- **Critic:** a separate MLP on [local 16, global 10]; the env's global vector is repeated per due vehicle (CT:73, :94-95, :204; BE:946-949). Return scale fixed at update 0 (CT:432-433); advantages normalised per minibatch (CT:302); input statistics frozen during a collect and its update, saved with the weights (CT:75-86; V388).
- **Gate-closed decisions** are ordinary rows in the policy, value and entropy terms (CT:321-336; V413). In v3w they are not no-ops: the level is set, the hold starts, and the level acts once the gate opens (BE:692-715, :774-779; p2:34-36).

## 2. Sizes

| Quantity | Value | Source |
|---|---|---|
| Decisions per update | median 92.8k-93.9k, range 71k-127k | TB `ppo/n`, v3w C0-C4 |
| Decisions per episode | about 31k; 326k ALKS-seconds, about 217 ALKS present at once | TB, C0, C3 |
| Epochs, minibatch | 10 × 4,096; about 22 minibatches per epoch, remainder skipped; about 110k gradient steps per learner | CT:30, :321-323 |
| Gate-closed share | "about half" (V413); gate open 51-52 % of ALKS-seconds (V385); 1B masked 0.44 in training, 42.5 % at smoke | TB `ppo/mask_frac`; r2:88 |
| Seconds per update | 23-24 (confirmatory 3, laptop, V391-V392); v3w 29.6-29.8 median, 4.13 h per set (laptop, 5 learners in parallel); 1B, lagr 80-83, 11.1-11.7 h (rented, 40 learners at once, V447) | TB `ppo/wall_s` |
| Per learner | 1,503 episodes (500 × 3 plus 3 pilot, CT:426-429); about 47 M decisions | arithmetic |
| Per training set | 7,515 episodes; about 236 M decisions | arithmetic |

- **Simulator share of wall time: not logged.** INFERENCE from v3w C0: update 0, with the pilot collect, took 47.6 s and later updates about 28 s, so a collect is at most about 20 of 28 s. That fits 21 s per plant run (V443).
- INFERENCE: a training set costs about 9 evaluations of 800 runs. Transitions are cheap (31k per run); independent episodes are scarce (1,503 per learner).

## 3. What was tried on the learner side

Round 2: validation against the v3w arm, X1 / X2 delay, positive = better (r2:109-117).

| Variant | Change | End |
|---|---|---|
| v3w | PPO as in §1, 7 levels 4,500-6,000 | Test against baseline-v3: delay +3.5 [+1.2, +5.3], +3.4 [+1.0, +4.8]; "not from a change of method" (r1:9, :105-106). "No delay wins over the rules" (V449) |
| 1B | Env: a gate-closed decision is dropped, the level holds (1B/b_env.py:691-693). Trainer: those rows leave the policy and entropy terms; the critic keeps them (1B/c_train.py:293-301) | −0.8 [−4.2, +1.0] / −1.2 [−3.0, +0.2]. Hold and mask confounded (p2:34-37); laptop rows against remote v3w rows (V465) |
| 2B | learning-rate and entropy decay | −1.6 [−2.9, +1.0] / +0.1 [−2.5, +1.2] |
| 1D | 0.1-s braking charge | +1.0 [−1.8, +2.9] / +0.1 [−1.0, +1.7] |
| ahead | two look-ahead inputs | −0.7 [−3.2, +0.3] / −0.8 [−1.6, +0.6]; X2 close-following +7.3 [+2.4, +11.2] |
| rep | repeated slowdown in training | −0.4 [−1.6, +1.0] / +0.2 [−1.7, +1.7] |
| lagr | Reward = safety only; cost = own and bin lost time plus network delay rate (BE:847-848, :859-861). Second critic (CT:74). Advantage (A_r − λ·A_c) / (1 + λ) (CT:300-306). λ ← clip(λ + 1.0 × (J − 0.97), 0, 10) after 20 frozen updates (CT:35, :63-66, :441-443) | Never evaluated: λ at the cap in 5 of 5 (V448). Target about 6 % below the rules' mean delay, not 3 % (V429). TB, 5 learners: λ at 10 by update 61-67; J minimum 1.05-1.10 per learner; final entropy 1.08-1.11 against v3w's 0.67-0.70 (C0, C4). INFERENCE: near-uniform policies; the run says little about constrained PPO |
| res | ±1 level on os1_15_10 (BE:680-688) | X1 delay −1.6 [−3.5, +1.5]; did not qualify (V449); range confounded (r1:274) |
| attr | attributed delay (BE:845) | "delay worse by 13.5 % [11.4, 14.5]" (V449); weight untuned (p1:48) |
| tail, sw | no training (CT:137-172) | validation advances did not hold at the test (r2:175-178, through `results_round12.md`) |

## 4. What a port to SB3 would need (all INFERENCE)

**(a) Adapter.**
- Car slots as "environments": K per SUMO process, K above the peak ALKS count (mean 217; peak not logged).
- A slot resets on entry. An exit must be a truncation that bootstraps from the car's own last value (CT:259-262); no observation exists after it.
- Empty slots produce padding rows that must stay out of the loss.
- All slots of a process share one SUMO step; none steps or resets alone.
- Clocks: about half of the cars are due per 5-s step. A synchronous step needs one global 10-s decision step (a new car waits up to 5 s at 1.6 s; departs from V290) or pseudo-rows for cars not due, the no-effect samples V290 removed.

**(b) Critic.** Actor on 16, critic on 26 (CT:72-73): one observation carrying both, an actor that ignores the global 10. Off-policy: Q(local, global, own action), without the other cars' actions.

**(c) Off-policy transition.**
- (s, a, mean 10-s reward, s' at the car's next decision). `done` is never true: exits and the horizon are truncations. A car's last transition has no s' (roughly 1 in 30, with the brief's thousand cars per run): drop it, or store s' = s as CT:259-262 does.
- Gate-closed rows: valid under v3w's actuator (delayed effect). Under 1B's hold they are needed as next states and useless for the actor; dropping them needs variable-length transitions.
- Non-stationarity: the shared term is 33-45 % of the reward's magnitude (V385) and depends on about 200 other cars' current policy. A replay keeps rewards from older policies; a PPO batch has every car under one policy.
- Scale: a replay of 1 M transitions (illustrative size) holds about 32 episodes, 11 of our updates. One gradient step per transition is 47 M steps per learner against about 110k now: learner compute, not SUMO, would bound the run.

**(d) Ours whatever the library:** plant, gate, hold, reward (BE:554, :842-848), saved input statistics, pilot, the TensorBoard tags `tbcheck1` requires (V440), 5 learners on common seeds, greedy deployment through `{"pt": FILE}` (CT:119-134), evaluation, checkpoints chosen on validation seeds. A continuous headway needs a new action path: `_apply` moves one of 4 level indices per hold (BE:703-711, :779); input 10 and the `lv` counters are level-indexed (BE:789-790, :932).

## 5. Fair vanilla baseline

`CLAUDE.md`:22-25: "**Fair vanilla DRL:** a standard algorithm (PPO; SAC for continuous actions) acting directly on the same actuators, with the same observations; the same training and tuning budget; checkpoints chosen on validation only."

Status: `CLAUDE.md`:12: "**The thesis-level claim bar is under review** ... Until that decision, the D5.8 text below is the historical bar for the SUMO/DRL lines only." V95 (`decisions.md`:114), later: "D5.8 is history; V85's "under review" is resolved by this entry"; "**The claim bar is set by the author and Claude**, pre-registered per study." INFERENCE: the lines are historical guidance, not binding.

## 6. What a change of algorithm could address

| Weakness | Algorithm change? (INFERENCE) |
|---|---|
| M2: one-sided, gated lever (BE:37, :774-779) | No: action set and plant. A continuous family implies a new action design, which PPO could use too; above 1.6 s is screen M's question |
| H1: a 100-generation delay search from p333 ended at p333, +0.01 % [−0.45, +0.25] (memo:19; TRUCK cell, 20-parameter rule family) | No where p333 is the lever's delay optimum: an optimiser does not move it. Open in X1 and X2 (v3w +5.5, +6.1 % against p333, descriptive, memo:44): screen R's question |
| M3, reward (BE:554, :842; V413) | No: the reward is ours |
| M3, unmasked rows | Yes in principle; 1B did it in our trainer: no gain shown, confounded |
| M3, delay as a constraint | Tried as lagr; not a clean negative |
| L2: no memory (CT:41-42) | Yes, with a recurrent actor; never tried. Memo:143-145: "likely to fail alone" |
| M8: learner SD 0.3-4.1 % (r1:250-251); checkpoint ranks reverse (V429) | No; it bounds the comparison: each family is one more recipe trained once; at 40 seeds a 1-2 % delay effect is not detectable (paired SD 7-11 %, V435) |

**Not checked:** the instantaneous ALKS peak; `test_table.csv`.
