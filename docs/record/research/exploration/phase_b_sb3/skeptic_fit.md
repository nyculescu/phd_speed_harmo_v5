# Skeptic, project fit: sb3_table.md

Nothing built, trained or simulated; event files read with `tbread.py`. `sb3/`, `contrib/` = the installed 2.8.0 packages. CT, BE = `/home/catalin/work/phd/wt/planb_v23/v5b/fleet/c_train.py`, `b_env.py`. 1B/ = `/home/catalin/work/phd/v5b1_runs/round2/code_5c10e6f/v5b/fleet/`. `docs/` is under `/srv/shared/Workspace/phd/phd_speed_harmo_v5b1`; memo = `docs/research/exploration/drl_win_directions_v0.md`.

## Blockers

**B1. Screen R does not bound memory (RecurrentPPO cell 4, follow-up 1).**
- R compares frozen, memoryless v3w with memoryless searched rules (memo:305-311). A pass shows an edge without memory; a KILL says nothing about memory. The memo ties L2 to D1, not R (memo:145).
- R needs the author's override, and X2 is reported at its KILL (relayed, not checked).
- Change: cell 4 → "L2: untested; no screen bounds it". Follow-up 1 gets a rules-only precondition: a rule told the slowdown's phase (an informed oracle) against the best memoryless rule, e.g. 16 level pairs × 60 seeds × 2 cells = 1,920 runs ≈ 0.6-0.7 h, $0.19-0.25 at V475 (ESTIMATE). V347 and V491 lean to a KILL.

**B2. The plant record covers four values, and not yet those.**
- Intended use: "1.6, 1.2, 1.0 or 0.8 s" (`docs/testing/plant_vv_record_v0.md`:9). PR-10: "partial: no r2m3 T0 record" (:46). Any win against rules needs PR-10 (:87).
- The DDPG cell's "Outside 0.8-1.6 s the plant is unchecked" implies the inside is checked.
- Change: "any value other than the four is outside the record". Follow-up 2's "more levels if M passes" first needs an intended-use amendment and T0 (memo:263).

## Major

**M1. Car slots contradict the accepted trainer ADR,** which the table does not cite: `docs/architecture/adr/ADR-001-trainer.md`:10 (slots "re-creates the zone-slot design the author rejected (V3)"), :40 (SB3 with slots is the last of three fallbacks), :35 (no switch trigger on record), :42 ("trainers are never mixed within one comparison"). Change: delete "or car slots" (A2C row); cite the ADR.

**M2. Car slots also fail mechanically.**
- Stock collection stores one row per slot per step (`sb3/common/on_policy_algorithm.py`:218, :247). The buffer has no validity field (`sb3/common/buffers.py`:392-399). GAE uses one gamma per row (:426-435). Losses and advantage normalisation are means over all rows (`sb3/ppo/ppo.py`:219, :227, :244).
- With a 5-s step and 10-s own clocks (BE:942-945), half of a live slot's rows are not-due rows, plus empty-slot rows. Only the exit bootstrap carries over (`on_policy_algorithm.py`:236-245 against CT:259-262).
- The own loop is the only route that keeps V290's sample. INFERENCE: SB3 then adds only `train()` (`ppo.py`:184), which CT:309-347 already holds.

**M3. The off-policy "27 times" rests on an assumed ratio.** SB3 counts VecEnv steps (`sb3/common/off_policy_algorithm.py`:571) and defaults to one gradient step per such step (:92, :351), whatever the slot count. In an own loop `train(gradient_steps, batch_size)` has no default (`sb3/sac/sac.py`:202). The range is about 150,000 steps per learner (300 steps × 501 collects) to 47 million. Change, five rows: "updates per sample is a free choice with no record".

**M4. Follow-up 1's cost omits the opponents.**
- Missing: timer-rule tuning on the same cells (memo:141; by the 3E recipe 2 × 40,640 rows ≈ $9, memo:313); opponents on the fresh seeds, 8 arms × 80 × 2 = 1,280 runs; checkpoint validation, 2 arms × 5 learners × 2 checkpoints × 40 × 2 = 1,600 runs.
- Training is not runs × rate: 500 sequential updates took 4.1 h (v3w, laptop) and 11.4-11.7 h (1B, loaded rental) per set. V450 gives about $11 ÷ 8 sets ≤ $1.4 per set.
- Total about $12-13 (ESTIMATE), a third of the weekly $40 (memo:117).

**M5. Forking paths are named, not counted.** PPO recipes already read in X1 and X2: 10 trained (baseline-v3, v3w, res, attr, lagr, 2B, 1B, 1D, ahead, rep) and 2 untrained (`docs/research/results/round_1_result.md`:240-251; `docs/research/protocols/round_2.md`:26-32). The PPO record cell lists 6. Change: fix one memory form before data and state the count.

**M6. M8 gets worse, not "not addressed".** Within PPO one recipe change moved delay 3.4 %, not attributed (`round_1_result.md`:246-248); learner SD 0.3-4.1 % (:250-251). INFERENCE: 5 learners per arm resolve about ±0.4 to ±5 %, so a family effect below about 3.4 % cannot be attributed.

## Minor

- **MaskablePPO is not 1B.** It averages policy loss and entropy, and normalises advantages, over all rows (`contrib/ppo_mask/ppo_mask.py`:349, :357; `contrib/common/maskable/distributions.py`:72-82); 1B over open rows only (1B/`c_train.py`:293-299). At 0.44 masked those terms weigh 0.56 of 1B's (INFERENCE). Note (ii): "a new recipe".
- **1B record holds** (1B/`b_env.py`:691-692; `round_2.md`:27, :34-37; `round_2_result.md`:112; V465). Add: the upper bounds, +1.0 and +0.2 %, exclude a larger delay gain.
- **lagr record holds** (`docs/research/protocols/round_1.md`:50-66; CT:35, :63-66, :300-306; V429; V448). Add from `train_lagr/tb` (exploratory): λ median 10, J median 1.13-1.16, entropy 1.10-1.13 against v3w's 0.69-0.74. INFERENCE: at 10/11 delay weight the policy did not concentrate; that is credit assignment (M3), outside any family.
- "Nothing can run beside training (V392)" is a laptop finding; the rental held 40 learners and a search (V447, V450).
- v3w's event files carry the laptop's host name: resolves one "not verified" line.

## Confirmed

- No family touches M2 (BE:37, :774-779).
- 1,503 episodes per learner (CT:427, :431), 7,515 per set; `ppo/n` mean 94.2-94.6k, so 31.4k decisions per episode, 47 M per learner.
- No follow-up trains before a screen.
- "Nothing" for eight families matches `docs/decisions.md` (no match); archive branches not checked.
