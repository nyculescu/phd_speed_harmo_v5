# V505 studies: rules shared by M2 and EV

Status: **DRAFT v2, not approved.** It holds what both `v505_m2_merge_check.md` (M2) and `v505_ev_informed_rule.md` (EV) need: words, decisions, order, measures, statistics, seeds, cost, and what happens when something goes wrong. Review findings and their handling: `v505_review_v0.md`.

## 0. Decisions for both studies

| # | Decision | Recommendation | Pros | Cons | Weaker alternative |
|---|---|---|---|---|---|
| D6 | Where the code lives | new branch `v505/core` from `planb/core` `a8b7a50`, worktree `~/work/phd/wt/v505` | the plant, the pack and the runner exist only there; `git diff b0c9360 a8b7a50` touches no plant, controller or measurement code; branch-per-approach rule | a third long-lived branch beside `planb/core` and `v5b1` | build on `v5b1`: `planb_ctrl.py`, `measure.py` and the TRUCK and SURGE kinds are missing there |
| H1 | Which rented host | V488's offer rule (lowest price per effective CPU, at least 48 effective CPUs), with the EPYC 7xx3 class preferred among equal offers | the EPYC 7663 class measured about 3 times cheaper per run (V490); the whole plan fits the cap | S6 ran on a Xeon 8163, so M2's v3w identity replays may differ on another CPU; the fallback (M2 §6) then costs about +$0.7 | the Xeon 8163 class (as V498, for identity): about $8-10 for everything, above the cap. If only a non-EPYC offer exists, the author is asked again (V507(3)), never the rate check alone |

## 1. Words used

| Word | Meaning |
|---|---|
| ALKS | an automated car; 50 % of the fleet. Its time headway can be commanded at 1.6, 1.2, 1.0 or 0.8 s |
| v3w | the five frozen trained policies (learners w0-w4), never retrained here |
| Rules by name | p333: "0.8 s everywhere", the delay-best stored rule. os0_10_10: 1.6 s for a car that is slow and near a crowded accelerating lane, else 0.8 s. lr1000_16_2: 1.0 s when the roadside speed over the next 1,000 m is below 16 m/s, else 0.8 s. 3E-T (stored arm `3e`), 3E-C_TRUCK, 3E-D_TRUCK: zone rules found by machine search (CMA-ES), for close-following or delay. ASCH: switches the whole road between two rules on measured zone speeds. MPC-F: a model-predictive controller with a model fitted on separate seeds |
| carried and grid sets | the 14 stored rules Plan B carried (`pb.CARRIED`, minus `copy`) and the 5 grid re-picks of S3a |
| merge 2 | the second on-ramp. Ramp-2 cars enter on a 295-m accelerating lane (`4a_0`) that ends in a dead end |
| lane-end waiting | `end_stop2`: vehicle-seconds of cars below 1 m/s in the last 30 m of `4a_0`, counted once per second from 300 s (`end_stop` is the same at merge 1) |
| S, TRUCK, X1, S6 | the steady cell; 10 trucks capped at 40 km/h; two slowdowns on edge 4. All at 5,300 veh/h on r2m3 with `plant_c3`. S6 is Plan B's evaluation (240 seeds, run at `b0c9360`) |
| Δb, Δv | v3w's effect against an opponent on the base plant and on the variant |
| G1a, T0, T3 | the gate "delay in the cell at least 10 % above S"; the check that a command acts; determinism |
| the pack | the measurement add-on that writes road-by-road, minute-by-minute and braking data (`measure.py`) |
| PR-28, PR-24, PR-08 | plant verification items: gains not from an artefact; every counter traced; lane changing is our model, not validated |
| V-A | M2's variant plant: only the merge decision of ramp-2 cars on `4a_0` is made more assertive |

## 2. Order of stages (fixed)

1. **Build part 1** on the D6 branch: M2's code, EV's drawn-timing event, both readers, tests.
2. **M2:** smoke and identity, trace, variant pick, then the S and TRUCK verdict. M2 is read.
3. **EV:** smoke, sizing and gate. If EV is VOID here, part 2 is not built.
4. **Build part 2:** the told rule (IP), detecting-rule wrappers (SW), the recovery measure.
5. **EV:** tuning and evaluation, a single stage for the cap check. EV is read after M2.
6. **M2 X1 verdict,** last. It is the first stage dropped at the cap.

## 3. Measures in every table

- Delay `all_delay`: door-to-door, including the insertion queues, in vehicle-seconds. It is co-headlined with served flow `passed`.
- Total travel time `N` (fixed window, unfinished vehicles counted to the window end).
- Close-following `ttc_net`; hard braking at step resolution `b45_step` and `alks_b45_step`; moving full-emergency events `alks_full_moving` (lane-end crawls `alks_full_creep` reported apart); collisions; `m_stuck_n`.
- No control is printed beside the controllers, never alone and never as a deciding opponent.

## 4. Statistics

- **Exactly read6's convention** (read6.py:14-15, `arm()`):
  - v3w's raw values are averaged over the five learners per seed;
  - the effect is the median of the paired % differences against the opponent;
  - one shared bootstrap index matrix: percentile, B = 20,000, rng 20261108.
  The mean of the five learners' own medians, which passes its no-effect null (memo §4.4), is printed beside it, as is each learner.
- **Comparison readings** (Plan B's components, planb.md:437-440):
  - **better:** lower bound above 0 at 97.5 %;
  - **harm:** delay more than 2 % worse by point with the 95 % upper bound below 0, or close-following more than 10 % worse by point with the 95 % upper bound below 0;
  - **neither:** otherwise.
- **Ties:** for every deciding comparison, the share of seeds where the two arms give identical rows is printed. A zero-width CI is "not readable" in M2. EV's own rule (EV §5) applies there.
- **Crashes and drops:** a crashed run is re-run on the same seed and commit, up to 3 attempts. A seed that fails every attempt is dropped from every arm of the comparison, and the drop is reported. More than 3 dropped seeds in one stage voids that stage.

## 5. Seeds (proposed; V505 block 7,488,000-999 plus D4 of M2)

| Seeds | Use |
|---|---|
| 7,488,000-009 | M2 smoke, determinism, traced against untraced |
| 7,488,010-019 | M2 trace of `end_stop2` and `end_stop` (PR-24) |
| 7,488,020-079 | M2 variant pick (n = 60) |
| 7,488,080-099 | M2 reserved: repeats after a code fix |
| 7,480,400-639 | M2 S and TRUCK verdict, variant only (D4 of M2) |
| 7,488,200-219 | EV smoke and T0 |
| 7,488,220-239 | EV sizing (throw-away, disclosed) |
| 7,488,240-279 | EV gate (n = 40) |
| 7,488,280-339 | EV tuning (n = 60) |
| 7,488,340-459 | EV evaluation (n = 120), used once, plus at most one pre-planned repeat on V-A (§6) |
| 7,488,460-499 | EV reserved: repeats after a code fix |
| 7,488,500-539 | EV tuning extension to n = 100, only if EV §5's power rule fires |
| 7,488,540-579 | EV evaluation extension to n = 160, only if EV §5's power rule fires |
| 7,488,600-759 | M2 X1 verdict, both plants (n = 160) |
| 7,488,760-999 | M2 fallback only: fresh S and TRUCK verdict seeds on both plants (n = 240) |
| others | reserved; any use needs its own V# |

## 6. How M2 and EV connect (one rule, quoted in both)

- **GAIN:** if the location share is above 50 %, the GAIN is "lane-end-bound". The share follows V482's definition (planb.md:143): the median paired road-delay difference over 4a, 4, ramp 2, the ramp-2 insertion queue and the junction lanes, divided by the same over all roads, read only when the denominator is above 0. If the share is not readable, the GAIN stands with "location not read".
- **KILL:** G(bU) is recomputed with those merge-2 road groups removed. If its upper bound is then at least 10 %, the KILL is "lane-end-bound".
- **Repeat:** a lane-end-bound outcome repeats its deciding comparison on V-A, on the same evaluation seeds. That is the cell and S for NC, N, FX and SW, plus IP in the cell: 1,080 runs. V-A must bind in that cell, by M2's binding check. The outcome stands only if it holds there with the same rule. Otherwise:
  - a GAIN reads NOT SHOWN;
  - a KILL reads "unresolved" and closes nothing.
- **If M2 is VOID or V-A does not bind in the EV cell:** a lane-end-bound GAIN reads NOT SHOWN, and a lane-end-bound KILL reads "unresolved".

## 7. Cost, machine and the spend cap

| Stage | Runs with the pack | Runs without |
|---|---|---|
| M2 smoke, identity, trace | about 250 | |
| M2 variant pick (5 levels × 2 arms × 60) | 600 | |
| M2 S and TRUCK verdict | 5,280 | |
| EV smoke, sizing, gate | 610 | |
| EV tuning (FX, then IP and SW) | | about 9,700-12,000 |
| EV evaluation | 1,080 | |
| M2 X1 verdict | 2,880 | |
| Only if triggered: EV repeat on V-A 1,080; tuning extension about 6,500-8,000 (no pack); evaluation extension 360; M2 fresh-seed fallback 5,280 | | |

- **Rates, whole rental, outages excluded:**
  - EPYC 7663 class: about $0.11 per 1,000 without the pack (V490), and about $0.14 with it (inferred: × 1.24, V468).
  - Xeon 8163 class: about $0.47 per 1,000 with the pack (V494 without its billed outage hour), and about $0.29 without it (inferred).
- **Totals, X1 included:** about $2.7 on an EPYC 7663 class host, and about $4.4 if every trigger fires. On a Xeon 8163 class host, about $8, which is above the cap (H1).
- **Cap action, fixed now:** a rate check in the first 30 minutes projects the total. If spend plus the projected cost of the next stage would pass the cap, the stage in progress finishes, no new stage starts, and this is logged. Finished stages are read; unstarted ones are not run. EV tuning and evaluation are one stage, so tuning never starts unless evaluation is affordable. With the §2 order, X1 is dropped first.
- **Build** (my estimate after two reviews): part 1 about 12-16 h, part 2 about 10-14 h, including tests.
  - Files: `fleet.py` or the `run_one` step hook (V-A), `plant_sweep.py` (pass-through), `perturb.py` (drawn timing, the told plan), `b_env.py` (the override), new conditions, `pb.py` and the runner (seed blocks as job fields), `measure.py` (recovery time, ramp-2 lane-change counts), and `toolchain/remote` DATA_EXTRA.
  - New pieces: the PR-24 tracer, the identity comparer, LocalRule on a chosen base rule, the freeze step between FX and IP/SW, two readers with planted-row tests, and the two power simulations.

## 8. Deviations, bugs and operation

- **No change to any criterion of M2 or EV after the first data row of the study** (M2 smoke). An unavoidable change needs a V# before the affected stage, and every sentence then names it.
- **Bug rule (CLAUDE.md):** fix it test-first, re-run everything affected on the same seeds, and log both outcomes. After results exist, a corrected reading counts only if a test written before the fix fails on the old code. Every bug search is logged with its trigger.
- **Disclosed omissions:** an opponent that cannot be built is a disclosed omission, never a silent one.
- **Platform:** one machine class per stage (V436, V465). A mid-stage platform change voids the stage or is disclosed in every sentence.
- **Ledger:** every run goes into the ledger, including failed and abandoned ones.
- **Operation:**
  - runs only on rented machines (V483), from a frozen detached worktree at the run commit;
  - S1-style identity rows are repeated on each new machine (V488);
  - fetch, verify by sorted SHA-256 lists, then destroy;
  - at most 100 workers;
  - rows are compared by value, never by line text (V499).
