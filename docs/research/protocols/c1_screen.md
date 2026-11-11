# C1: does frozen v3w keep a close-following edge over the searched rule on a new event, and does it cost hard braking? (approach C, step 1)

Status: **DRAFT v3, not approved.** This is approach C's first step (V509-V511, V520), plus two rules-only model checks. Draft v0 came from a design panel (`c1_screen_design_log.md`); v1, v2 and v3 answer review rounds 1-3 (`c1_screen_review_v0.md`). C1 can open or close C. It never supports a claim. Words, measures, statistics, crashes, bugs and operation follow `v505_common.md` §1, §3, §4, §7 and §8 unless stated here. **Form A (recommended) departs from V520 and V509(2) ("rules-only")**: its deciding arm is the frozen v3w policies, which needs the author's yes (as V507(1) did for M2). Form B (§5b) is V520's literal rules-only step, written so that it can be run.

## 0. Decisions for the author

| # | Decision | Recommendation | Pros | Cons | Weaker alternatives |
|---|---|---|---|---|---|
| C-D1 | Cell | **E30**: EV-A's event (edge-2 limit to 30 km/h, 20-s taper, onset U(450, 800) s, duration U(240, 420) s; code `311f76c`) at 5,300 veh/h, behind a drain gate (§2) | no controller was trained or tuned on it; an incident zone is plausible on a real road; p333 drained on the 20 sizing seeds (ramp-2 +1.11, limit 2); TRUCK, X1 and X2 stay closed; a pass names stage 2's cell | a new post hoc study (+1 cell in form A); thin drain margin; the sizing rows of no control and p333 were seen; EV's sizing passed it over as mild (13.7 % of S); about 20 % of its close-following sits at merge 1 (3a), downstream of the event | **TRUCK reopened** (funnel-only amendment of planb.md:575): best precision, but closed, chosen because of the hint, and a pass opens nothing there. **S**: no perturbation (V504); rows already seen. **H1**: TRUCK under another name |
| C-D2 | Intended use | read "tapered slowdowns (X1, X2)" as examples, so E30 is inside | no amendment | a wider V&V target | label E30 "outside the intended use" |
| C-D3 | Form | **A**: frozen v3w (no charge) against 3E-C_TRUCK in E30 (§5). **Departs from V520's "rules-only"** | asks whether a policy has room above the searched rule, which is what the funnel trains on (reward_metric_options:59); in E30 nothing answers it yet | v3w has no charge and 3E-C_TRUCK no braking term: both are stand-ins; it resembles screen F (parked, V509(3)) moved to a new cell; 8 runs per seed | **B**, V520's literal step (§5b): 3E-C_TRUCK against p333, rules only, 3 runs per seed. Runnable, but it cannot tell whether a policy has room above the rule; stored rows point to its NO COST-R (in TRUCK the rule cut close-following with less braking than p333) |
| C-D4 | Braking measure paired with C's charge | **`b45_step`** (time at ≤ −4.5 m/s², read every 0.1 s, all vehicles) | the charge and the judged measure are one quantity; in every row | the stored hint ties on it (TRUCK −1.55 [−4.44, +2.37], 95 %); it was fixed knowing that | `events_ge45` (where the stored cost showed): chosen after seeing it, needs the pack in any later search; it stays a veto on NO COST (§7). 1D's −3.0 m/s²: does not match a −4.5 judgement |
| C-D5 | Deciding statistic | **mean of the five single-learner effects**, seeds resampled jointly; the pooled arm (read6's per-seed mean of the learners) printed beside | the pooled arm fails a no-effect null (memo §4.4; mean of 4 learners against the 5th: S6 S delay −1.31, close-following −10.98; TRUCK −0.46, −2.52) | a departure from read6's convention, which M2 used; it assumes the rule's single-run noise is like one learner's, which learner rows cannot test (disclosed) | the pooled arm: biased against v3w on every measure, so K1 and K2 would read noise as a verdict |
| C-D6 | Delay margin | against **p333**: **kept** if the 97.5 % lower bound is above −1 %; **worse** only if the point is at or below −1 % and the 95 % upper bound is below 0 (planb §8.2's harm level) | V504's tie; screen F's margin; p333 is V510's fixed rule; kept and worse cannot overlap | delay in S6 S against p333 was close to the margin on the stored rows | 2 %: a 2 % loss is not a tie. "Worse if the upper bound is below 0": a shown loss inside the tie band would kill C |
| C-D7 | Sample size | a **60-seed pilot** that prints only standard errors (SEs) and, at each candidate n, the outcome rates those SEs imply under three stated truths; n is the smallest of 240, 480, 960 and 1,920 that powers the edge, delay and cost (§5) | E30's spread is unknown | the SEs (never effects) are seen before n is fixed; an S-like spread asks the author about 4 times in 10 | fix n now: up to 8 times too many or too few |
| C-D8 | Lane check (a) | downstream extension; 295, 445 and 595 m; **a label only**, printed with every C1 and stage-2 sentence; controllers are compared at 295 m only | merge spacing kept; no plant choice after control rows; the rules' zone edges, the 4a bins and the policy's position input are fixed for 295 m (§6) | TTT not comparable across lengths | upstream extension: edge 3 shrinks (weaving confound). Adopting a length: breaches V245 and V456(3). Reading controllers at a longer length: rules act in the wrong place |
| C-D9 | Share check (b) | **beside (a)** at fixed 0.3 and 0.7 through a job-level share field (no new seed stream) | follows V520(2); adds 240 runs | none | defer it: a second rental and a cross-rental reference |
| C-D10 | Seed block | 7,489,000-7,491,919 (§8) | above every assigned seed | needs approval; large | V505's unrun ranges: still assigned |
| C-D11 | Machine and cap | one rental, one CPU model (EPYC preferred, V488); **cap $4** | guard 3; n up to 1,920 fits | larger than V505's | $3: n = 1,920 would reach it at the measured rate |
| C-D12 | Cost readings | **present** (read first): the 97.5 % upper bound below 0 and the point at or below −3 %. **absent**: no cost shown (upper bound at or above 0) and a 5 % cost excluded (lower bound above −5 %). Anything else, a shown cost smaller than 3 % included, is undecided | absence is powered at the planned n (P(absent \| true 0) about 0.80 at the planned SE); NO COST never closes C on a shown cost | a small real cost parks C instead of closing it | absent above −3 %: P(absent \| 0) about 0.35, so COST UNDECIDED would be the usual reading. Powering −3 % in the n rule: TRUCK-like goes to 960 and S-like never passes. Absent without the upper-bound clause: NO COST could close C on a shown cost of 0-3 % |
| C-D13 | Cells-tested base | **94 → 95** in form A, as V508 D7 recorded (form B: stays 94, no policy runs in E30) | no recorded decision changes; the larger count is the conservative disclosure | V508 D7 counted three variant cells in which no policy ran (M2 was VOID at the pick, V518) | 91 → 92, by planb.md:145's unit (cells where a policy ran): needs a V# correcting V508 D7 |
| C-D14 | Share amendment (V510: "the author's decision when C's protocol is approved") | decided now, **conditional**: if (b) reads PLANT OK at both shares, the intended use gains **30-70 % automated share in steady traffic at 5,300 veh/h**, the condition (b) checks; otherwise it is not amended and the failing share is named. Stage 2's robustness row in E30 first gates E30's drain at 0.3 and 0.7 under its own protocol | V510's timing kept; evidence before effect; the amendment covers only what was checked | an amendment by rule, not by a fresh look | amend the whole intended use: (b) checks only steady S. Amend now without (b): no plant evidence. Decide after (b): departs from V510's timing |

## 1. Question

C is "close-following without its costs" (V509). Before anything is trained, C needs room. On fresh seeds, in a cell nobody was tuned on, C1 asks:
1. **Room:** does frozen v3w show a close-following edge over 3E-C_TRUCK, with delay kept against p333?
2. **Cost:** does that edge come with more hard braking, which C's charge would cure?
3. **Where:** does the edge hold away from both merges?

**Stored hint** (TRUCK, 240 seeds, exploratory; positive = v3w better): close-following +11.80 % [+4.97, +19.71] (97.5 %, pooled); braking events −5.73 % [−8.28, −2.31] (95 %); braking seconds −1.55 % [−4.44, +2.37] (95 %); jams −8.57 % [−14.29, −4.29] (95 %).

**What to expect** (review round 3: simulated from stored S6 SEs with normal projections, exploratory).
- **n:** a TRUCK-like pilot picks n = 480 about 8 times in 10 (240 or 960 otherwise). An S-like pilot picks 1,920 about 6 times in 10 and finds no n about 4 times in 10, which asks the author.
- **Under C's premise** (10 % edge, −5 % cost, delay tie, the same edge away from the merges): stage 2 opens with probability about 0.97 at TRUCK-like n = 480 and 0.94 at S-like n = 1,920. About half of the TRUCK-like openings are merge-weighted.
- **Under the stored truths:** TRUCK-like, C is most likely **parked** (about 0.9, mostly COST ON ANOTHER MEASURE through the `events_ge45` veto); S-like, **NO COST** closes C as defined (about 0.96).
- **Under a null edge:** K1 about 0.99 at the modal n.

So ROOM is not the likely outcome. C1 is built so that a park or a close is the honest answer if the stored rows carry over to E30.

## 2. Cell and gate

- **E30:** as C-D1. Every arm meets the same drawn event on a seed.
- **Gate,** no control and p333, S and E30, 40 seeds. Read only:
  - drain in V486's form: the mean of (E30 − S, same seed) of `ramp1_queue`, `ramp2_queue` and `backlog` (`planb/drain.py` `series_from_row`, V486's window), at most 2 vehicles, for both arms;
  - stuck: at most 1 run with `m_stuck_n` > 0 per arm and cell (false-fail rate about 0.1 % at the stored rate of 1 in 960; EV's zero rule would fail 4 % of the time);
  - the event binds: no control's delay cost has its 95 % lower bound above 0.
  - No size bar (the sizing rows were seen).
- **Fallback, fixed now:** if drain or stuck fails, the duration becomes U(120, 240) s on fresh gate seeds. This cell is labelled **E30-short, unsized** in every sentence. If it also fails, C1 is VOID and C is parked. If the bind part fails, C1 is VOID with no fallback.
- **Per-arm drain on the screen rows,** both parts on the same seeds:
  - **Queues (V486's form within E30):** an arm fails if the mean over screen seeds of (arm − p333, same seed) of `ramp1_queue`, `ramp2_queue` or `backlog` is above 2 vehicles. For v3w the five learners are averaged per seed first. Exploratory false-fail rate on S6 rows: 0.000 for v3w and 3E-C_TRUCK at n = 240 and 1,920; the same form flags no control (+2.26 vehicles in S, +2.63 in TRUCK).
  - **Stuck rows:** an arm fails if more than 1 % of its rows have `m_stuck_n` > 0. v3w's 5n learner rows are pooled; per-learner counts are printed. False-fail rate at the stored rule rate (21 of 11,520 S6 rule rows): 3E-C_TRUCK 1.0 % at n = 240, 0.2 % at 480, about 0 above; v3w pooled about 0 (its stored rate is 0 of 2,400).
  - Consequence: v3w or 3E-C_TRUCK fails → VOID. p333 fails the stuck part → in form A, if the edge is shown, NOT RESOLVABLE (delay); in form B, VOID. No control → printed only.

## 3. Arms (E30, every seed)

- **v3w:** w0u250, w1u500, w2u250, w3u500, w4u500 (S6 checkpoints, hashes in baseline_v5), frozen.
- **3E-C_TRUCK** (`g098i00`): the deciding opponent.
- **p333:** the delay reference.
- **No control:** printed, used for P0, never deciding.

Form B runs 3E-C_TRUCK, p333 and no control only.

## 4. Measures

Every measure is printed whole-road and by road group: **merge 2** (`4a`, `ramp2`); **merge 1** (`3a`, `ramp1`); **between** (`3`); **event approach** (`1`, `2`); **downstream** (`4`, `5`); **junctions**. Delay adds the insertion queues: `pending_ramp2` joins merge 2, `pending_ramp` joins merge 1, and `pending_main` is its own group, **origin queue**. "Away from both merges" = `1`, `2`, `3`, `4`, `5`. A road key absent from a row counts as 0. Served flow `passed` and TTT `N` are printed in every table (common §3).

| Role | Key | Split |
|---|---|---|
| Star | `ttc_net` | `m_road_ttc3` by group (the parts sum to `ttc_net`) |
| Cost (deciding) | `b45_step` | a new 0.1-s accumulator by group (new keys only) |
| Cost (veto on NO COST) | `events_ge45` | events by group at the peak |
| Cost (printed) | `alks_b45_step`, `alks_full_moving` | none |
| Delay | `all_delay`, with `passed` and `N` | `read6.location`, groups as above |
| Independent check (`jams` vetoes NO COST; neither decides otherwise) | `jams`, `fuel_km` | jams by head cell; fuel by a new accumulator |
| Side | collisions, `m_stuck_n`, `end_stop2`, `end_stop`, teleports | none |

Sizing rows (EVA30, 20 seeds, share of close-following by group): no control merge 2 60.3 %, merge 1 23.5 % (3a 21.0 %), between 10.0 %, event approach 4.2 %, junctions 1.9 %, downstream 0; p333 61.7 %, 19.7 %, 15.1 %, 2.7 %, 0.9 %, 0. So "away from both merges" holds about 14-18 % of the star.

## 5. Reading, form A (fixed before data)

**Statistic (C-D5):** for each learner, the median of paired % differences against the opponent on the same seeds (median of the opponent in the denominator); the deciding effect is the mean of the five; seeds resampled jointly, B = 20,000, rng 20261108. Positive = v3w better (less close-following, braking, delay, events or jams). The pooled arm and each learner are printed beside.

**Levels:** four readings decide (R-star, R-delay, R-cost, R-else). Readings that open or close by showing a good or absent effect (shown, kept, present, absent, SHOWN, and R-star's upper bound used by K1) use 97.5 % intervals. Harm readings (delay WORSE, R-else WORSE, and the NO COST vetoes) use 95 % (planb §8.2).

| Reading | Comparison | Rule |
|---|---|---|
| R-star | v3w against 3E-C_TRUCK, `ttc_net` | **shown** if the lower bound is above 0 |
| R-delay (read only after the edge is shown) | v3w against p333, `all_delay` | **KEPT** if the lower bound is above −1 %; **WORSE** if the point is at or below −1 % and the 95 % upper bound is below 0; otherwise not resolvable |
| R-cost | v3w against 3E-C_TRUCK, `b45_step` | **present** if the upper bound is below 0 and the point at or below −3 %; otherwise **absent** if the upper bound is at or above 0 and the lower bound above −5 %; otherwise undecided |
| R-else | R-star's statistic on "away from both merges"; merge 2, merge 1 and junctions printed | **SHOWN** if the lower bound is above 0; **WORSE** if the 95 % upper bound is below 0; otherwise NOT SHOWN. **Not readable** (read as NOT SHOWN) if the opponent's median there is 0, or any learner's median paired difference is exactly 0, or more than 10 % of seeds have a paired difference of exactly 0 for any learner (stored S: 18-20 %, 4 of 5 learner medians exactly 0; stored TRUCK: 4-7 %) |
| NO COST vetoes | v3w against 3E-C_TRUCK, `events_ge45` and `jams` | **shown worse** if the 95 % upper bound is below 0 |
| P0 (CLAUDE.md early KILL, on delay) | 3E-C_TRUCK and p333 against no control, `all_delay`, positive = less delay | passes if either arm's point is at least 10 % and its 95 % lower bound above 0 (stored S6 S: p333 has 35.3 % less delay than no control); the close-following version is printed |

**Null (V244):** the swap null. v3w's and the opponent's values are swapped within seed (per learner), 2,000 swaps. The false rate of "shown", "present" and "SHOWN" must each be at most 1.9 % (1.5 × 1.25 %); of delay "WORSE" and R-else "WORSE", at most 3.75 % (1.5 × 2.5 %). Otherwise C1 is VOID. The vetoes' false rates are printed beside them and never VOID C1, because a veto can only park C, never open or close it; a veto that fires above 3.75 % is labelled so in the sentence (review round 3: `events_ge45` 4.3 % on TRUCK rows). The share of `jams` bootstrap upper bounds at exactly 0 is printed.

**Printed, never gating:** the 4-against-1 learner effect (a random held-out learner against the mean of the other four, on every deciding measure) as the size of the pooled arm's bias; each learner's effect and the range across the five; R-else's opponent median, SE and share of exact-zero paired differences. Sentence: "the deciding effect is the mean of five fixed policies; it assumes the rule's single-run noise is like one learner's, which learner rows cannot test."

**Power (by script, before the screen):**
- The pilot is the first 60 screen seeds, all arms. The SE at a candidate n is projected as SE_n = 1.15 × SE_60 × sqrt(60 / n); the 1.15 covers the 20-25 % spread of a 60-seed SE.
- n is the smallest of 240, 480, 960 and 1,920 at which all hold: 10 / SE_n,edge ≥ 3.08; 1 / SE_n,delay ≥ 3.08; 5 / SE_n,cost ≥ 3.08 (80 % power at a 10 % edge, a delay tie against the 1 % margin, and a 5 % cost).
- The script prints only the SEs, R-else's opponent median and exact-zero share (neither is a paired effect) and, at each candidate n, the outcome rates simulated from those SEs under three truths: C's premise (as §1, vetoes at 0), the stored truths (TRUCK mean of effects: edge +12.68, cost −0.93, delay +0.14, else +30.54, `events_ge45` −4.10, jams −4.29) and a null edge. It never prints a pilot effect. P(present | −5 %), P(absent | 0) and P(COST UNDECIDED | stored truths) are in that table.
- If no n passes or the cap would be passed, the author is asked before any more runs. The host is released. On any new host the identity replays and T3 run first, then the pilot seeds are re-run; n stays as fixed on the first host, and the re-run pilot prints nothing.
- The realised SE at n is printed against the projected one.
- For scale (stored rows, mean of effects, n = 240): edge SE S 5.99 / TRUCK 2.79; cost 3.48 / 1.47; delay 0.44 / 0.25.

**Planted-row tests:**
- edge 10 % [4, 16], cost −5 % [−8, −2] → ROOM WITH COST;
- edge 0 [−4, +4] → K1; edge 0 [−4, +12] → NOT RESOLVABLE (edge); edge 0 [−4, +4] with delay undecided → K1;
- edge 10 % with a cost of +1 % [−2, +4] and no veto → NO COST; the same with `events_ge45` worse → COST ON ANOTHER MEASURE;
- cost −4 % [−4.8, −0.5] → ROOM WITH COST (present first); cost −2.5 % [−4.9, −0.1] → COST UNDECIDED;
- delay −0.5 % [−0.8, −0.2] → KEPT;
- a merge-only edge with −10 % [−18, −2] away from both merges → K3; R-else with 30 % exact-zero differences → not readable, ROOM merge-weighted; R-else with 19 % exact-zero differences and one learner median of 0 → not readable;
- P0 with p333 +35 % [+33, +37] → passes; with p333 and 3E-C_TRUCK both at +5 % → fails;
- rows with absent road keys sum to their totals.

## 5b. Reading, form B (only if the author picks B in C-D3)

V520's literal question: does the searched rule's close-following result carry a braking cost? Same cell, gate, seeds, levels, null, pilot rule (on SE_edge' and SE_cost'), P0 and checks; 3 runs per seed. The statistic is the median of paired % differences of 3E-C_TRUCK against p333 (single arms); positive = 3E-C_TRUCK better.

| Reading | Comparison | Rule |
|---|---|---|
| R-star' | 3E-C_TRUCK against p333, `ttc_net` | **shown** if the 97.5 % lower bound is above 0 |
| R-cost' | 3E-C_TRUCK against p333, `b45_step` | as R-cost (present first; absent needs the upper bound at or above 0 and the lower bound above −5 %) |
| R-else' | R-star' on "away from both merges" | as R-else |
| Vetoes' | 3E-C_TRUCK against p333, `events_ge45` and `jams` | as the NO COST vetoes |
| Printed | delay (3E-C_TRUCK was admitted at +2 % over p333) | none |

Consequences, in order: VOID (as §7, plus p333 failing either drain part); P0 fails → C KILLED; star' not shown → NOT RESOLVABLE (C parked); R-else' WORSE → **K3'** (C KILLED in this form, sentence as K3); cost' present → **ROOM-R**, stage 2 (§7), merge-weighted if R-else' is NOT SHOWN; cost' absent and no veto' shown worse → **NO COST-R**: C as defined closes ("the searched rule already cuts close-following without a braking cost on E30"); otherwise C is parked.

The pilot's three truths for B: C's premise (edge' +10, cost' −5, else' +10, vetoes' 0); the stored TRUCK truths (3E-C_TRUCK against p333: edge' +21.18, cost' +14.51, delay −1.28; else', `events_ge45` and `jams` computed from the same S6 rows by the pilot script before the pilot runs); a null edge'. NO COST-R is the likely reading.

## 6. Model checks (rules only; S at 5,300; seeds 7,489,020-079; they add 0 cells)

**(a) Longer ramp-2 lane (V520(2)), a label for the PR-28 record.**
- No control and p333 at 295, 445 and 595 m (downstream extension): 360 runs.
- **Usable length,** point form for both bounds (M2 used the point form for collisions): the mean extra collisions per run against 295 m at most 0.05, and the mean extra `alks_full_moving` per run at most 0.15. Null false-fail per length on 120 stored S rows each: p333 0.3 %, no control 0 (a one-sided 95 % upper bound at 0.05 would fail p333 73 % of the time). Stuck runs are dropped from the paired reading and counted in the record.
- **Label:** at each usable length, paired against 295 m, for each arm: merge-2 close-following and merge-2 `b45_step` (up to 8 tests); delay and `end_stop2` printed. **SENSITIVE** if any test shows a change of at least 10 % with its Bonferroni interval (95 % over the tests read; 99.375 % each for 8) excluding 0; otherwise **sensitivity not shown at n = 60**. If no longer length is usable: **(a) not readable**. NOT SENSITIVE is never claimed.
- The script prints the label's null rate, by sign-flipping the paired differences (2,000 flips). Review round 2 found an uncorrected 95 % family false rate of 0.13-0.21 on S6 S rows; the Bonferroni bar is there for that reason.
- **Consequence:** a label printed with every C1 and stage-2 sentence. Stage 2 compares controllers at 295 m only: the 3E rules' zone edges (`b_env.py:1110`), ZonePattern's positions (`b_env.py:1036-1037`), the 4a bins (`b_env.py:1006`) and the policy's position input are fixed for 295 m, so at another length the controllers would act in the wrong place. Never a plant change.

**(b) 30 % and 70 % share (V510), beside (a).**
- No control and p333 at fixed shares 0.3 and 0.7, against (a)'s 50 % rows at 295 m on the same seeds: 240 runs. A job-level share field; the ALKS sets nest across shares; nominal and realised shares logged.
- **PLANT OK at a share** if all hold:
  - collisions: for both arms the one-sided 95 % upper bound of extra collisions at most 0.05 per run;
  - stuck or teleported: at most 1 of the 120 runs at that share (false-fail rate about 0.7 % at the stored rate of 1 in 960; a zero rule would fail falsely 11.8 % of the time);
  - **the command acts:** p333 against no control at that share, `all_delay`, 95 % interval excluding 0 (stored 50 %: p333 has 35.3 % less delay, [34.5, 37.3], n = 240). A within-seed swap null of that test must give a false rate of at most 7.5 % (1.5 × 5 %), otherwise (b) is VOID;
  - **not oversaturated:** for both arms, the mean over the 60 seeds of the growth of `backlog` from the five minutes before V486's window to that window is at most 2 vehicles above the 50 % rows' mean growth on the same seeds (V486's form; its sign-flip null is printed; per-seed SD about 3 vehicles, so the mean's SE is about 0.55).
- Printed: delay, flow, TTT, jams, close-following, braking, the queues, `end_stop`, `end_stop2`, `tau_on_match / tau_on_n`.
- **Consequence (C-D14):** PLANT OK at both shares → the intended use gains 30-70 % automated share in steady traffic at 5,300 veh/h. Otherwise it is not amended, the robustness row is not run as written, the failing share is named, and any narrower range needs the author's V#.

## 7. Consequences, form A (fixed now; read in this order)

| Reading | Closes | Opens |
|---|---|---|
| VOID (gate fails twice or its bind part fails, the swap null, T0, per-arm drain of v3w or 3E-C_TRUCK, a same-CPU identity mismatch under the bug rule, a CPU-model change within a stage) | nothing | a re-run needs its own V# |
| P0 fails | C (not expected) | nothing |
| NOT RESOLVABLE (edge): edge not shown, R-star's 97.5 % upper bound at or above 10 % | nothing: C is parked | logged |
| **K1 NO ROOM:** edge not shown, upper bound below 10 % | **C is KILLED:** no C search, no training. Sentence: "On E30, frozen v3w without a braking charge did not show a close-following edge over 3E-C_TRUCK (a rule admitted at +2 % delay over p333, not converged); an edge of up to [UB] % is not excluded; a charged policy and a same-goal rule were not tested." | reopening needs new evidence in a new pre-registered cell |
| NOT RESOLVABLE (delay): edge shown, delay neither KEPT nor WORSE; or p333 failed the stuck part; or the author declines the pilot's n | nothing: C is parked | logged |
| **K2 DELAY:** edge shown, delay WORSE | **C is KILLED as defined.** Sentence: "frozen v3w without a braking charge kept its edge only at a delay cost against p333 [interval]; a charged policy was not tested." | nothing |
| **K3 MERGES ONLY:** edge shown, delay kept, R-else WORSE | **C is KILLED in this form.** The sentence states R-else's interval away from both merges, the printed merge-2 and merge-1 parts, and that merge-conflict safety is outside the intended use (PR-28 gap) | nothing |
| **ROOM WITH COST:** edge shown, delay kept, cost present, R-else SHOWN | nothing | stage 2 |
| **ROOM WITH COST, merge-weighted:** as above, R-else NOT SHOWN or not readable | nothing | stage 2, with the star away from both merges read as a co-star |
| **NO COST:** edge shown, delay kept, cost absent, and neither `events_ge45` nor `jams` shown worse | **C as defined (a braking charge):** v3w already meets C's braking goal. The sentence states the `b45_step` and `events_ge45` intervals and the jams reading | optionally, a fresh-seed confirmation of frozen v3w in E30 under its own protocol |
| COST ON ANOTHER MEASURE: as NO COST, but `events_ge45` or `jams` shown worse | nothing: C is parked; its charge goes back to the author | logged |
| COST UNDECIDED: edge shown, delay kept, cost neither present nor absent (a shown cost smaller than 3 % included) | nothing: C is parked | logged |

**What a ROOM (or ROOM-R) commits stage 2 to (fixed now):** a same-goal rule search with cmab and a new loss (close-following %, plus the `b45_step` charge, plus collisions; a 1 % delay cap against p333, admission at +1 %), on the policy's training conditions, at least 100 generations with the plateau label; C's charge at −4.5 m/s² read every 0.1 s; choose on one seed set, confirm on fresh seeds in E30 unless the author names another cell first; jams and fuel not worse; the V510-V511 robustness row if (b) read PLANT OK at both shares (C-D14), after its own E30 drain gate at 0.3 and 0.7; the road-group split; controllers compared at 295 m with (a)'s label. Rough cost $7-14 (reward_metric_options:47).

## 8. Seeds (proposed; nothing above 7,488,999 is assigned; the author must approve)

| Seeds | Use |
|---|---|
| 7,489,000-019 | smoke, T0, T3, traced against untraced, the per-run rate |
| 7,489,020-079 | model checks (a) and (b) |
| 7,489,080-119 | E30 gate |
| 7,489,120-159 | fallback gate (E30-short), only if needed |
| 7,489,160-999 | reserved (repeats after a code fix, later stages); each use needs a V# |
| 7,490,000-7,491,919 | screen, used in order up to the pilot's n; 7,490,000-059 is the pilot |
| 7,480,400-402 | identity replays in S only (S6 seeds), never read |

## 9. Runs, cost, build

| Stage | Runs (pack on) |
|---|---|
| Smoke, T0, T3, identity | about 130 |
| Checks (a) and (b) | 360 + 240 |
| Gate (+ fallback) | 160 (+160) |
| Screen, form A, 8 runs per seed | 1,920 at n = 240; 15,360 at n = 1,920 |
| Screen, form B, 3 runs per seed | 720 at n = 240; 5,760 at n = 1,920 |
| **Total, form A** | **about 2,800 at n = 240; about 16,200 at n = 1,920** |

- **Rates:** measured on the V505 rental (EPYC 7702, 60 workers, rule runs only): about $0.17-0.19 per 1,000 pack runs; inferred for the EPYC 7663 class: about $0.14. So about $0.5 at n = 240 and about $2.8-3.1 at n = 1,920, plus about $0.1-0.2 overhead. In form A, 62.5 % of screen runs are policy runs with the new accumulators; the smoke measures their rate, and common §7's cap action applies. Cap $4 (C-D11), inside the $40 per 7 days.
- **Order:** identity; (a) and (b); gate; pilot; screen.
- **Build:** about 8-12 h (estimate), branch `c1/core` from `v505/core` `311f76c`: the by-group accumulators, the road groups, `accel2_len` (downstream), the share field, the pilot script with its outcome table and the reader with planted rows. A skeptic code review comes before the rental.

## 10. Checks before data (any failure: stop)

| Check | Requirement |
|---|---|
| T0 | the edge-2 limit read back every 0.1 s follows the taper and 30 km/h (V505's per-candidate tolerance); `4a_0` length within 1 m of the plan and edge 3 unchanged; p333's command read back; at each share the realised share is logged and the same vehicle IDs are automated for every arm on a seed; 50 % rows identical with the share field present |
| Splits | the parts sum to the totals, absent keys as 0: close-following and events exactly; braking and fuel within 1e-9 relative; delay, insertion queues included, within 0.1 % |
| Traced = untraced (V386); T3 | equal; the new accumulators change no stored key |
| Key classes (both identity rows) | **provenance** = `commit`, `name`, `cfg`, `ctrl_sha256`, `files`, `m_st_file`: not compared. **Decision diagnostics** = `m_dec_*`, `lv_sum_*`, `lv_n_*`, `tau_on_n`, `tau_on_match`, `tau_mismatch`: printed with their largest relative difference, never gating (V519 named no tolerance value; this is a stated departure). **Traffic** = every other key present in the stored S6 row: compared for equality. Keys absent from S6 rows are checked by traced = untraced only |
| Identity, rules | 3E-C_TRUCK, p333 and no control on S6 seeds 7,480,400-402 in S: traffic keys equal S6 (else the bug rule) |
| Identity, v3w (V519) | checkpoint hashes equal baseline_v5; traffic keys equal S6. A traffic mismatch on a CPU model other than S6's is logged and disclosed, not VOID (every C1 arm runs on one machine); on the same CPU model it falls under the bug rule |
| One machine type | one CPU model per stage, named in the record; a change voids the stage |
| Smoke; readers | rows carry arm, seed, cell, L_ev, lane length and share; the per-run rate of policy and rule runs is measured; the planted rows pass |

No criterion changes after the first smoke row without a V#.

## 11. Closures and counts

- TRUCK, X1 and X2 stay closed; nothing runs there. S carries only rule rows (the gate's S rows, checks (a) and (b)) and the identity replays; no controller comparison for C is read in S ((b)'s p333 against no control is a plant check).
- E30 is a new study, labelled post hoc (planb.md:576), not one of Plan B's cells. The line's cells-tested count (planb.md:145, as V508 D7 raised it) becomes 95 in form A; in form B no policy runs in E30, so it stays 94 (C-D13). The gate and the checks add 0. The count of approaches tried rises by 1 whatever the outcome. EV stays VOID.

## 12. Disclosures every C1 sentence carries

- A screen, not a claim. E30 (or E30-short) is post hoc. Form A departs from V520's "rules-only" (C-D3).
- No control and p333 at 30 km/h were seen on 20 sizing seeds (no-control cost 13.7 % of S, p333 23.2 %, p333 ramp-2 drain +1.11, limit 2). At 20 km/h the event failed drain (V518).
- 3E-C_TRUCK is not "a rule tuned on the same goal": no braking term (planb.md:227); not converged at 100 generations; tuned on TRUCK only; admitted at +2 % delay over p333 and +1.28 % against p333 in TRUCK. It spends delay that stage 2's rule may not, which biases K1 toward a KILL.
- The deciding effect is the mean of five fixed policies, assuming the rule's single-run noise is like one learner's.
- Stored rows point to a park (TRUCK-like) or NO COST (S-like), not to ROOM (§1). `b45_step` was fixed knowing that the stored cost showed on events, which now veto NO COST. Stored jams were worse for v3w.
- In E30's sizing rows about 60 % of close-following sits at merge 2 and about 20 % at merge 1 (3a, the discharge through the first merge); about 14-18 % lies away from both merges. Merge-conflict safety is outside the intended use.
- The split is by edge, not lane. (a)'s label is printed; a longer 4a widens "merge 2". A share change redraws human attributes.
- Policy rows repeat on traffic values across CPU models, not bit for bit (V519).
- The pilot's SEs were seen before n was fixed; n may exceed the funnel's "a few hundred runs".
- Every run, failed ones included, goes into the ledger.
