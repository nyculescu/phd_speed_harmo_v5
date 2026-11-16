# Round 1 build review (baseline-v3..HEAD, branch v5b1)

Scope: b_env.py, c_train.py, plant_sweep.py, docs/research/round1/, tests/test_round1.py, read against protocol round_1.md rev. 2. No simulation, training or seed was used. `tests/test_round1.py`: 26 passed. Two read-only snippets were run (TensorBoard event files in a temporary directory only).

**One blocker found.** Without a fix, 2C is dropped after its 3.3 h slot without reaching the author.

## Blocker

**B1. Every 2C learner fails the log check because of `lagr/J`.**
- Where: `docs/research/round1/tbcheck1.py:43-45`, with `v5b/fleet/c_train.py:327` and `:401`.
- What happens: the trainer writes `lagr/J` only once λ starts moving (u ≥ 20). `log_faults` requires every tag in the file to have steps 0..499 exactly once. So each 2C learner gets "lagr/J: updates are not 0-499 once each", `wrong` lists all 5, and the script exits 1. `chain1.sh:136` then logs "lagr OUT OF THE ROUND" and goes on.
- Verified: `ct.tb_scalars` over 25 updates, with J from u = 20, gives `['lagr/J: updates are not 0-24 once each']`.
- Why the tests miss it: `_fake_log` (`tests/test_round1.py:101-103`) writes no `lagr/J`, and the smoke runs only 2 updates.
- Fix:
  - in `log_faults`, expect `range(ct.LAGR["freeze"], updates)` for `lagr/J` and `range(updates)` for every other tag;
  - build the fake 2C log with the trainer's own pattern (J only from u = 20), or call `ct.tb_scalars` for it.

## Major

**M1. Any failure of tbcheck drops the candidate instead of stopping the chain.**
- Where: `chain1.sh:132-138`, `tbcheck1.py:105`.
- What happens: tbcheck exits 1 on any of these:
  - log faults;
  - settings mismatches;
  - a Python exception, e.g. a missing `ppo/reward_per_decision` raising KeyError at `:97`.

  The chain reads every one of them as "OUT OF THE ROUND" and continues. The protocol makes only two outcomes "out": collapse in more than one learner, and λ at the cap in at least 3 learners. Any other failed check must stop the chain and go to the author.
- Example: B1 above, or M2 below, silently removes a candidate.
- Fix:
  - exit 1 only for collapse or cap;
  - exit 2 for log or settings faults, and wrap `__main__` so that an exception also exits 2;
  - in the chain, rc 1 means the candidate is out; any other non-zero rc means STOPPED.

**M2. A chain restart leaves stale event files, and the reader keeps them.**
- Where: `chain1.sh:113-119`, `c_train.py:384`, `checks1.py:107`.
- Verified: two writers in one directory (steps 0-6, then 0-4) read back as 12 values, `[(0,1.0)…(6,1.0),(0,2.0)…(4,2.0)]`. EventAccumulator does not purge across files.
- What happens: if the chain is restarted (reboot, unit stop) while slot K trains:
  - `train_K` has no `done`, so all 5 learners retrain;
  - their `tb/C{L}` directories still hold the old partial files;
  - tbcheck sees duplicate steps, and under M1 the candidate is dropped.

  The smoke has the same problem on any re-run of the chain: `checks/smoke_*/tb/C0` gets steps [0,1,0,1], the smoke FAILs and the chain stops. Only the in-chain crash restart (`:127`) moves the directory.
- Fix: before each `train` call, move `train_K/tb/C$L` aside (as `:127` does), and clear `smoke_{kind}`. Better still, `c_train.train` refuses to start on a non-empty `tb/C{L}`.

**M3 (unsure of size). The collapse rule may now be much looser than its calibration.**
- Where: `tbcheck1.py:67-73`.
- What changed: each update now covers 3 consecutive levels out of 7, so the per-update `ppo/reward_per_decision` has a period-7 level-mix component. An update at 4,500/4,750/5,000 and one at 5,500/5,750/6,000 should differ systematically, because the speed and vehicle-count terms depend on congestion. Baseline-v3 had one fixed level per environment, so its σ had no such component.
- Consequences:
  - σ over updates 101-500 now includes the cycle, so 0.4σ is probably wider than the ≈0.03 it was calibrated against;
  - the test on baseline-v3's logs cannot show this;
  - the windows are not whole cycles (100 = 14×7+2, 50 = 7×7+1), which adds a small bias to a and b.
- Risk: a drifting learner passes, and the check may be unable to fail (cf. V244).
- Fix, needing an author decision before stage 0: compute a, b and σ on the reward after subtracting the mean per (u mod 7), or on 7-update block means. At minimum, report σ both with and without the cycle for the first slot.

## Minor

**m1. Reading A is skipped when v3w is a finalist.**
- Where: `test1.py:155-156`.
- What happens: with finalists [v3w, res], `res` is never compared with the control arm.
- Fix: `if "v3w" in trained:` and loop over `k in fin if k != "v3w"`.

**m2. Band Bonferroni (unsure of intent).**
- Where: `test1.py:151-154`.
- What happens: m counts only the tested candidates. The incumbent's band is read at the same corrected level but is not counted in m.
- Fix: if the incumbent's "shown" counts as a reading, add 1 to m. If not, label it report-only.

**m3. Stage 0a uses neither the protocol's checkpoint rule nor its score (report-only).**
- Where: `stage0.py:50`, `:43-48`.
- What happens:
  - `choose(T, "d", i, CHECKPOINTS)` picks among all 10 checkpoints, while the protocol's rule picks between u250 and u500;
  - the rank correlation uses a different score (delay effect if TTC ≥ 10, else −100), not the checkpoint-selection score;
  - ties at −100 get arbitrary `argsort` ranks, and an all-tied vector gives NaN.
- Fix: `choose(..., (250, 500))`; rank on `choose`'s score tuple with average ranks for ties.

**m4. The TensorBoard tag names differ from the approved text.**
- Where: `c_train.py` `tb_scalars`.
- What happens: the protocol says `ep/q<level>/<counter>`; the code writes `ep/e<slot>/<counter>` plus `ep/e<slot>/q`. The change is needed, because per-level tags could not hold one value per update with 7 levels in 3 slots. Still, it departs from the approved protocol.
- Fix: record it as a decision before stage 0.

**m5. The 1A disclosure understates double charging.**
- Where: `b_env.py:811-814` and `:826-829`; protocol line 247.
- What happens: a vehicle on 3a_0 or 4a_0 whose leader is a ramp ALKS is charged to two different ALKS: the leader (follower term) and the nearest mainline ALKS (merge term). This follows the protocol text, but the disclosure names only ALKS-ALKS pairs.
- Fix: extend the disclosure.

**m6. 2C's J is measured on sampled actions; stage 0b on greedy ones (unsure of size).**
- Where: `c_train.py:399-402`, `stage0.py:66-68`.
- What happens: training J comes from sampled actions, while d_ref and the 0b stop come from greedy runs. Exploration raises training delay, so J is biased upward: λ may climb, and the cap stop may fire, from exploration noise. This follows the protocol as written, and should be disclosed.

**m7. If one learner fails twice, the others keep running.**
- Where: `chain1.sh:124`.
- What happens: `exit 3` leaves the other 4 learners running. A `systemd-run` service kills its cgroup when the main process exits; a `--scope` unit does not (unsure how the chain is launched).
- Fix: `trap 'kill $WD $(jobs -p) 2>/dev/null' EXIT`.

**m8. Wording: n_ref.**
- What happens: the 2C network rate uses `_ref()[2]`, which is stage 0c's no-control N, not env.json's. That is consistent with 0c replacing env.json's references, but the 2C text still says "from env.json".

## Checked and matching the protocol

**1A** (`b_env.py:836-840`):
- −0.5·lost(own);
- −0.5 × (lost time of followers within 200 m behind an ALKS + accelerating-lane vehicles assigned to their nearest mainline ALKS on the same edge within 50 m);
- −10 × safety;
- no near or flow term; shared term and collision charge kept;
- per-second sums divided by the 5-s decision.

**2C reward:** safety, collision and move charges only; `_efficiency` returns 0.

**2C cost:** per second, lost(own) + lost(bin mean) + (N − Σv/27.78)/n_ref, averaged over the decision. Its keys match the reward's.

**Training-mode delay:** training and `plant_sweep` compute it from the same `ep` counters, with the same episode length.

**c_train, 2C:**
- cost GAE with the same γ and λ;
- bootstrap on exit and at truncation, matching the reward's;
- separate per-minibatch normalisation, then (A_r − λA_c)/(1+λ);
- VF·(v + v_c);
- `scale_c` fixed at u = 0.

**Dual variable:**
- λ = 1 for updates 1-21 (it first changes after update 21 and is first used at update 22, matching "after every later update");
- the window is the last 20 updates (60 episodes);
- `lagr/lambda` logs the λ actually used.

**3B:**
- bias (0, ln 18, 0), so p(offset 0) = 0.9;
- offsets change only for due vehicles; base + offset is applied to every ALKS every 5 s, clipped to 0-3;
- `act_env` travels in the checkpoint, and `Greedy` loads 17 inputs and the cost critic.

**Seeds and levels per slot:** the largest seed is 7,471,782 (≤ 7,471,799) and the largest episode index is 502 (< 520). The expected level is levels[(e+1+u) mod 7], which matches `reset`.

**Validation:** the checkpoint rule, the advance rule (same cell), harm, the floor at u500, at most 2 finalists, and ranking.

**Test:**
- T1;
- T2 at 1 − 0.05/m, with counting opponents found per cell and the p333 anchor;
- the band rule (10 %, 20 per run, CI above 0 at all three band levels).

**Chain:** the 2C skip on `stop_2c`, `trained.json`, and the two ROUND KILL exits. `ps.matrix` resumes completed rows on a restart.
