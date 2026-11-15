# C1 confirmation: on fresh seeds in E30, does frozen v3w follow too closely less often than every non-learning rule at its delay?

Status: **v1.1, approved (V527).** One pre-registered study (V524, V526) that replaces the separate frontier check. On fresh seeds in E30 it asks whether frozen v3w has less close-following than every stored non-learning rule not shown slower than it, and than every straight mix of a faster rule with a slower rule at v3w's delay. Braking is a co-star; delay is stated as a trade against p333. Cell, code, statistic, measures, checks, crashes, bugs and operation follow `c1_screen.md` (V521) unless stated here. E30 was chosen after C1's rows were seen: the study is post hoc for its cell, and its effects come from fresh seeds. Review rounds 0 (frontier draft), 1 (this study's v0) and the final check of v1 are in `c1_confirm_review.md`.

## 0. Decisions for the author

| # | Decision | Recommendation | Pros | Cons | Weaker alternatives |
|---|---|---|---|---|---|
| CF-D1 | Cell | **E30** as C1 (`c1_screen.md` C-D1); the run commit's `v5b/` equals 98cac5c's | C1's edge showed there; gate passed (V523) | post hoc for the cell; v3w trained under random slowdowns on edges 3-5 (E30 is on edge 2, with another duration) | another event: no edge on record; a new gate |
| CF-D2 | Arms | v3w's five frozen learners; the 23 stored S6 rules; no control; **uniform rules p111 and p222** (an ALKS following an ALKS under V2V at 1.2 s or 1.0 s; p333 is 0.8 s) | every rule on record plus the "longer headways" probe; 1.6 s is no control's headway, so p000 is dropped | no rule is tuned on E30 | stored rules only: leaves out the simplest way to buy close-following with delay |
| CF-D3 | Competitors | a rule competes unless v3w is shown faster than it by more than 1 % (the 97.5 % lower bound of D(r) above +1 %; V521's tie margin); **p333 always competes** | rules that trade delay for close-following are read by chords instead (CF-D5) | a rule 1-2 % slower may compete (CF-D4 handles a match there) | every rule a competitor: a slow rule could "beat" v3w only by trading delay |
| CF-D4 | Worthwhile edge | **5 %**: a competitor or chord shown within 5 % of v3w (97.5 % upper bound of the edge below +5 %) is MATCHED | an edge under 5 % is not a thesis-worthy win | a real 2-5 % edge stops the line | 0 %: ties read UNRESOLVED |
| CF-D5 | Chords | for **every pair** of non-learning arms that may lie on either side of v3w's delay (§1), the straight mix of the two at v3w's delay (§1), read as a competitor | tests the rules' trade-off line at v3w's delay, through any fast rule | a tuned rule between two rules could lie below the line (disclosed); many tests, all needed for PASS | p333's chords only: misses a lower line through another fast rule (in S, grid_os1_10_10 with MPC-F lay below every p333 chord) |
| CF-D6 | Co-star and delay | `b45_step` against every competitor: BRAKING SHOWN if every lower bound is above 0 and every braking null passes (a claim line, not gating); `b45_step` against 3E-C_TRUCK read and stated in every case (V524(2)). Delay against p333 read by C-D6 (KEPT / WORSE / not resolvable) and stated in the sentence, with the exchange rate; not gating (**departs from C1's K2**, as V524(2) allows: delay is a trade) | the trade is said plainly | a PASS can carry a shown delay loss against p333 | gate on delay as C1: C1 already parked on it |
| CF-D7 | Sample size | **n = 480** fresh seeds, fixed. At most one extension of **480** seeds (size fixed now), only after UNRESOLVED and under its own V# (which names and approves its seeds), on the screen's CPU model (else VOID): read once on all 960 seeds with 98.75 % intervals, classes, pairs, weights and nulls recomputed, null bar 0.94 % with 20,000 swaps and 4,000 resamples per swap | C1 measured E30's spreads; no pilot; the extension has more power than a second look alone | the other rules' spreads are unmeasured (their SEs are printed) | 240: a true tie mostly reads UNRESOLVED; an extension read alone: the same power as the first look |
| CF-D8 | Seeds | screen 7,489,160-7,489,639; smoke 7,489,640; identity replays 7,480,400-402 (S6 seeds, never read) | fresh; inside V521's approved block, its reserved range | each use needs this V#; 359 reserved seeds remain afterwards | a new block: a new approval |
| CF-D9 | Machine and cap | one rental, one CPU model; **cap $4** | as C1 | none | none |

## 1. Readings (fixed before data)

**Statistic:** as C1 (C-D5). For arm r and measure m, per learner l, the median over seeds of the paired % differences −(P_l − R)/median(R) × 100; the effect is the mean of the five; seeds resampled jointly (B = 20,000, rng 20261108); 97.5 % percentile intervals unless stated. Positive = v3w better (less).

**Per rule r:**
- D(r): delay edge (`all_delay`). r is a **competitor** if the lower bound of D(r) is at most +1 %, or if r is p333; otherwise a **trade point**.
- E(r): close-following edge (`ttc_net`).

**Chords.** The pairs come from all 26 non-learning arms (the 23 stored rules, p111, p222 and no control). For every pair (q, r) with the lower bound of D(q) below 0 (q may be faster than v3w) and the upper bound of D(r) above 0 (r may be slower), so that a chord cannot drop out by noise:
- m_q = the mean over learners of the median over seeds of (P_l − q) on delay, = −D(q) × a_q / 100; m_r = the same of (r − P_l), = D(r) × b_r / 100; a_q and b_r are the full-sample median delays. Weight on r: w = m_q / (m_q + m_r) (0.5 if m_q + m_r = 0), recomputed on each resample and clamped to [0, 1]; a clamped w gives the end of the segment nearest v3w's delay, so a same-side pair reads as its nearer rule.
- Chord edge, per learner and seed: −(P_l − M)/c_M × 100, with the per-seed mix M = (1 − w) × q + w × r on close-following and c_M = (1 − w) × median(q) + w × median(r) (full-sample medians), so at w = 0 or 1 the chord equals that rule's E; median over seeds, mean over learners; 97.5 % interval from the same resamples.
- If no rule has a lower bound of D below 0, no chord is read.

**Reading of a competitor or a chord, in this order:**
1. **MATCHED** if the upper bound of its edge is below +5 % (CF-D4). For a competitor whose D point is above +1 %, this reads **MATCHED AT A DELAY COST** instead.
2. **BEATEN** if the lower bound of its edge is above 0.
3. otherwise **UNRESOLVED**.

**Null (V244):** for every competitor and chord, C1's swap null (2,000 swaps; one sign per learner and seed, on the per-seed edge; for a chord on the per-seed chord value with w fixed at its full-sample value). Its rate is the mean of the false rates of a lower bound above 0 and of an upper bound below 0 (the null is symmetric). A rate above 1.9 % is re-estimated once with 20,000 swaps (its own rng) and that value decides. A failed null makes that test UNRESOLVED, whatever it read (a departure from C1's VOID, §6). The same null on every braking edge of BRAKING SHOWN; a failed one reads "braking not shown". Expected number of nulls: up to a few hundred (competitors, chords, braking), all printed.

**Outcome, in this order:**

| Reading | Rule | Consequence |
|---|---|---|
| VOID | a §3 check fails | nothing; a re-run needs its own V# |
| P0 FAILS | no rule beats no control by at least 10 % on delay with its 95 % lower bound above 0 (CLAUDE.md early KILL; C1 §5; stored E30 +29.1 %) | the line closes |
| **KILL** | any competitor or chord MATCHED | v3w lies on the rules' trade-off line in E30: the confirmation line closes (V524 (2)); C1's screen stays an exploratory result. Sentence names the matching rule or pair with its intervals (and 3E-C_TRUCK's label, §6, when it is named) |
| **PASS** | every competitor and every chord BEATEN (p333 always competes) | **CONFIRMED** (§4 sentence) |
| UNRESOLVED | otherwise, including any MATCHED AT A DELAY COST | parked; the author decides on CF-D7's one extension or stops |

**Error rates, stated:**
- PASS needs every test to pass, so no correction is needed. Against a competitor with no true edge it can still pass falsely by a wrong trade-point class (at most 1.25 %) or a false BEATEN (at most 1.25 %): at most about 2.5 %; with CF-D7's extension, at most about 3.75 %.
- PASS shows each edge above 0, not above 5 %; the PASS sentence gives the smallest lower bound.
- KILL is a union over competitors and chords. A test whose true edge is exactly 5 % reads MATCHED about 1.25 % of the time, so with k such tests a false stop is at most k × 1.25 %. A false stop loses an opportunity and makes no claim. The numbers of competitors and chords are printed.
- A rule truly 1-2.5 % slower than v3w competes with probability falling from about 0.99 at +1 % to about 0.03 at +2.5 % (n = 480, C1's spreads). A match there reads MATCHED AT A DELAY COST when its D point is above +1 %; a rule truly 1.2 % (1.5 %) slower still reads plain MATCHED, and KILLs, about 0.29 (0.09) of the time (estimate).

**Printed, never deciding:**
- per arm: median close-following, delay, `b45_step`, `events_ge45`, served flow, TTT; the arms sorted by delay;
- per rule: E, D, close-following away from both merges, `b45_step` and `events_ge45` edges, each with its interval and SE, and its drain label; per chord: the pair, w with its interval, the edge;
- C-D6's delay reading against p333 and the exchange rate (% close-following per % delay against p333) of v3w and of every slower rule;
- the pooled arm and each learner; the 4-against-1 learner effects; P0's close-following version.

## 2. Expectations (exploratory, stated before data)

- **Stored rows, this statistic** (review rounds 0 and 1): every rule within 1 % of v3w's delay trails it on close-following, in S by at least +14.2 % [+2.5, +39.7] (MPC-F +23.3 %), in TRUCK by at least +24.2 % (os1_15_10); 3E-C_TRUCK (+12.7 %) is a trade point in TRUCK. The whole reading gives PASS in S (14 competitors and 95 chords BEATEN by point-sign pairs, smallest chord lower bound +11.2, os0_10_10 with MPC-F) and in TRUCK (11 competitors; no rule faster than v3w by point, so no point-sign chord).
- **C1's E30 rows** (V525; n = 960): p333 competes, E +30.5 % [+26.2, +34.9]. 3E-C_TRUCK (D +2.6 %) and no control (D +28.6 %) are slower; their chords with p333: w 0.25 [0.09, 0.38] and 0.02, edges +27.6 % [+23.8, +32.9] and +30.2 % [+25.9, +34.7].
- **Chords mainly block PASS, they rarely KILL:** with E(p333) near +30 % and D(p333) near −0.9 %, w stays at about 0.33 or less for a trade-point r, so such a chord reads MATCHED only if r has almost no close-following; for a competitor-class r, w can reach 1 and the chord tends to r's own E. A v3w lying exactly on a chord reads MATCHED about 0.04-0.2 of the time at n = 480, otherwise UNRESOLVED. Chord SE about 2.5-3.4 % (C1's halves).
- SE of E(r) at n = 480: about 1.5-3.0 % on the rules measured; a true tie reads MATCHED about 0.2-0.9 of the time; a 10 % edge reads BEATEN at 0.9 or above.
- The 20 other stored rules, MPC-F and the uniform rules have no E30 rows. The expected reading is PASS; a KILL needs a rule, or the uniform probes, to behave in E30 unlike in S and TRUCK. I cannot put a number on that.

## 3. Arms, checks and runs

| Arms | Count |
|---|---|
| v3w learners w0u250, w1u500, w2u250, w3u500, w4u500 (S6 checkpoints, frozen) | 5 |
| S6 rules: p333, z33133, r4a1, lr400_13_2, lr1000_16_2, lr1000_10_1, lr400_16_1, a4400_10_1, os0_10_10, os1_15_10, os1_10_0, copy, 3e, 3ex1, 3ex2, MPC-F, grid_a41000_10_2, grid_lr400_13_1, grid_os1_10_10, grid_r4a2, grid_z31333, 3E-C_TRUCK, 3E-D_TRUCK | 23 |
| no control | 1 |
| uniform rules p111, p222 (`cav_rule` [k, k, k], hold 10 s, as p333) | 2 |
| **Total** | **31 arms × 480 seeds = 14,880 runs** |

Every arm is its stored S config with E30's event, C1's `split` keys and the pack (`c1.arm_cfg`). MPC-F's model `mpcf_da8e9f8e5b59.pt` is shipped from `planb_s56_remote/jobs/` (DATA_EXTRA, data.sha256) and its config path rewritten to it in every stage, identity included; `model_sha256` is unchanged and MpcF checks it when it loads (`cfg`, `ctrl_sha256` and `files` are provenance).

**Checks (any failure: stop or VOID):**
- At the run commit `git diff 98cac5c -- v5b/` is empty (recorded in the V#), and every E30 job's `perturb` equals C1's: slowdown_draw, edge 2, onset [450, 800], dur [240, 420], taper 20, salt 505001, limit 30.
- Smoke on 7,489,640: every arm once and replayed (T3); split twins as C1; T0: the E30 limit read back; for p111, p222 and p333 the command read back (`tau_on_match == tau_on_n > 0`, `tau_mismatch == 0`) and the mean commanded level (`lv_sum_*` / `lv_n_*` on roads 2, 3, 4 and 5) within 0.15 of k (p333 on C1's rows: 2.97-3.00); split sums; per-arm wall time.
- Identity replays of all 29 stored arms on 7,480,400-402 (87 runs): rules equal S6 by value (else the bug rule); v3w's and MPC-F's traffic keys equal S6, a mismatch on a CPU model other than S6's disclosed and on S6's CPU the bug rule (C1 §10).
- One CPU model for every row. More than 3 dropped seeds: VOID. v3w's per-arm drain on the screen rows (C1 §2, against p333) fails: VOID; a rule failing it is labelled and stays in the reading (its delay includes its queues).
- The smoke measures the per-slot rate; the screen starts only if spent plus projected fits the cap.

**Runs and cost:** about 15,040 runs (screen, smoke about 70, identity 87). At C1's measured $0.154 per 1,000 runs and about 970 runs per hour with 30 workers on a 32-thread host: about $2.3 and 15-16 h (estimate; 23 arms have no E30 wall times yet).

**Build** (branch `c1/confirm` from `c1/core` 98cac5c, `v5b/` unchanged): stages and seed ranges; the plan of the stored arms and the uniform rules; MPC-F's model path in every stage, its file in DATA_EXTRA and data.sha256; T0 for the uniform rules; identity over all stored arms, MPC-F classed with the learners; per-arm drain and P0 over every rule (a rule failing drain labelled, not VOID); a reader with the competitor, chord, null and outcome rules and planted rows (§5), the chord nulls run in parallel; the remote order smoke, identity, screen, reading. A skeptic code review comes before the rental.

## 4. What a PASS says (template, fixed now)

> On the simulated r2m3 freeway (synthetic, uncalibrated, 50 % ALKS, 5,300 veh/h), in an incident-like slowdown (edge 2 limited to 30 km/h for 4-7 min) chosen after an exploratory screen of the same cell, on 480 fresh seeds, the frozen per-CAV DRL headway policy (5 independently trained learners, trained under random slowdowns on other edges) had at least [min lower bound] % less close-following (TTC below 3 s) than each of the [k] non-learning controllers not shown more than 1 % slower than it (none tuned on this event; [tuning cells]), and than every straight mix of a faster with a slower one of the [N] rules at its delay [| it was at least as fast as every rule, so no mix was read]. Its hard braking (−4.5 m/s² or harder) was [SHOWN lower than every one of them | not shown lower]; against the close-following-searched 3E-C_TRUCK (not converged) it was [x] % [CI]. Against p333 its delay was [x] % [CI] ([KEPT within 1 % | WORSE | not resolvable]; [y] % less close-following for [x] % delay). Merge-2 readings depend on the ramp-2 lane length (C1 check (a)). Merge-conflict and lane-change dynamics are not validated (PR-08, PR-28).

## 5. Planted-row tests

- every competitor and chord with lower bound above 0 → PASS; the same with one competitor's or one chord's upper bound at +4 % → KILL;
- a competitor with D lower bound exactly +1 % → competitor; with +1.01 % → trade point;
- a MATCHED competitor with D point +1.5 % → MATCHED AT A DELAY COST → UNRESOLVED;
- no rule with a D lower bound below 0 → no chords read; D(p333) = −0.9 with a rule at +2.6 % and C1's medians → w about 0.25; resamples with w below 0, above 1 or a negative or zero m_q + m_r → clamped (or 0.5), the chord equals the nearer rule's E in its own units; a ≠ b handled by m_q and m_r; a chord whose q is not p333 and whose r is a competitor;
- a test with a failed null → UNRESOLVED whatever it read (MATCHED included); a null at 2.0 % re-estimated at 1.5 % → passes; a braking edge with a failed null → "braking not shown";
- order: one MATCHED test plus a failed null elsewhere → KILL; the only MATCHED test with a failed null → UNRESOLVED; VOID and P0 FAILS read before KILL; 3E-C_TRUCK's braking stated when it is a trade point;
- the extension read: 960 seeds, 98.75 % intervals, classes and pairs recomputed, null bar 0.94 %; a different CPU model → VOID;
- P0 below 10 % → P0 FAILS; v3w failing drain → VOID; a rule failing drain → labelled, reading unchanged; an MPC-F traffic mismatch on another CPU model → disclosed, on S6's CPU → stop.

## 6. Disclosures

- A confirmation on fresh seeds of a cell chosen after an exploratory screen; post hoc for the cell. Not a claim beyond this cell and plant.
- v3w was trained under random slowdowns on edges 3-5 and its checkpoints were chosen on X1/X2 validation seeds (planb.md:188); E30 differs by edge and duration, and no rule was tuned on any slowdown of this kind.
- No rule is tuned on E30. Picked or searched on close-following under a delay cap, on other cells:
  - 3E-C_TRUCK (CMA-ES, TRUCK; **not converged at 100 generations**, a label every sentence naming it carries, V491);
  - 3e, 3ex1 and 3ex2 (3E-T, 3E-X1, 3E-X2: pooled close-following with a delay hinge, on T, X1, X2; 3e stopped at 40 of 100 generations and 3ex1 and 3ex2 were still improving at 40, so they are lower bounds, planb.md:216);
  - the grid re-picks grid_z31333, grid_r4a2, grid_lr400_13_1 and grid_a41000_10_2 (per form, the lowest close-following rule within 2 % delay of p333, in TRUCK), and os0_10_10, a carried rule that is also TRUCK's own-state pick and front row;
  - the steady pick lr1000_16_2 (the same in S; also ASCH's single member, V491).
- MPC-F minimises predicted delay + 10 × close-following with a model fitted on S and TRUCK, never on a slowdown (planb.md §3.5). 3E-D_TRUCK and grid_os1_10_10 (TRUCK's delay opponent, planb.md:212) target delay. copy was traced from DRL policies (planb.md:217). The other carried rules come from earlier rounds (planb.md §3.2). lr1000_16_2 (the scheduler) and MPC-F are CLAUDE.md's adaptive and MPC arms.
- A rule tuned on E30's close-following could do better (stage 2's search, closed by V524). A tuned rule between two rules could lie below their chord.
- The uniform rules p111 and p222 are untuned probes; their level acts only while V2V is on.
- The 5 % edge and the 1 % competitor margin are choices (CF-D3, CF-D4). Delay is not gating (CF-D6), a departure from C1's K2. A failed null reads UNRESOLVED, a departure from C1's VOID.
- Merge-2 close-following depends on the ramp-2 lane length (C1 check (a) SENSITIVE).
- Every run, failed ones included, goes into the ledger.
