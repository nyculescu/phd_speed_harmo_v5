# M2: do our results depend on how SUMO handles the end of the second on-ramp lane? (PR-28)

Status: **DRAFT v0, not approved.** It is a plant verification check, not a DRL study. Its outcome labels recorded results; it never creates or strengthens a claim. Approval: V505 (the step), with the open decisions in §0.

## 0. Decisions for the author

| # | Decision | Recommendation | Why | Weaker alternative and why |
|---|---|---|---|---|
| D1 | May the frozen v3w policies run in M2? V505 said "rules only". | Yes, evaluation only. | PR-28 asks whether v3w's recorded gains come from the lane end (V396; the X1 edge sits 58-62 % on road 4a). Without v3w the check cannot answer that. No training, no checkpoint choice. | Rules and no control only: it shows whether the lane end changes rule rankings, but leaves every DRL result unlabelled. |
| D2 | May M2 run in closed cells? TRUCK is closed (planb.md:575); X1 is closed ([A3], planb.md:160). | TRUCK and X1 yes, under the rule "a V&V row may only label or withdraw a recorded result, never support a new one". | The two recorded results that most need PR-28 are the TRUCK tie (its halves sit at merge 2: road 4a −4.38 %, road 3 +1.31 %) and the X1 edge. | S and TRUCK only (−$1.0): the X1 edge stays unlabelled; it is the result most tied to the lane end (Spearman 0.73 with the lane-end stop difference). |
| D3 | Which plant variant removes most of the lane-end waiting? | V-A: ramp-2 vehicles get a higher `lcAssertive` (same geometry). | Geometry, positions and every policy input stay as in training, so a change in v3w's result cannot come from out-of-range inputs. One parameter, set per vehicle at departure, the way `fleet.py:349` already does for ramp 1. | V-L, a longer 4a: SUMO's own advice (Motorways.md:24-27), but it moves positions that v3w reads (`x/1000`, `x/300`, b_env.py:925) and every zone and stored baseline. V-G, our own gap acceptance through TraCI: closest to real merging, but a new model with collision risk and the heaviest build. |
| D4 | Seeds for the verdict. | Re-use the S6 seeds 7,480,400-639 for S and TRUCK: the base-plant rows are the stored S6 rows, and only the variant runs. X1 uses fresh seeds on both plants. | Exact pairing with n = 240 at half the cost. The stored rows are not re-read for any decision; only the base-versus-variant difference is new. | Fresh seeds on both plants (+5,280 runs, about +$1.9). |
| D5 | Spend cap for M2 and EV together. | $6, or $7 with X1. | V505's $3 was set on the memo's "under $0.30"; fair opponents for EV and both plants for M2 cost more (§7). | Keep $3: M2 without X1 and EV with one event only. |
| D6 | Where the code lives. | New branch `v505/core` from `planb/core` `a8b7a50`, worktree `~/work/phd/wt/v505`. | The plant, the pack and the runner exist only on planb/core; branch-per-approach rule. | Build on v5b1: planb_ctrl.py, measure.py and the TRUCK/SURGE kinds are missing there. |

## 1. Question

At merge 2, vehicles that find no gap stop at the end of the accelerating lane and wait (SUMO behaviour; Motorways.md:24-27: "human drivers ... may accelerate up to the end"). Ramp 2 shows 75-87 times ramp 1's lane-end waiting under no control (S6 medians 522.5 against 20.0 vehicle-seconds). The question has three parts:
1. **Trace.** Does the lane-end counter count what it claims (PR-24)?
2. **Variant.** Is there a variant plant in which lane-end waiting at merge 2 falls by at least 75 %, without new collisions or stuck vehicles?
3. **Conclusions.** Do the recorded conclusions in §3 hold on that variant?

## 2. Plant and variant

- **Base:** `plant_c3` on r2m3, 5,300 veh/h, 50 % ALKS, exactly as in S6.
- **Variant V-A:** every vehicle on route `ramp2` departs with `lcAssertive = a`, where `a` comes from the ladder {2, 3, 5, 10}. Every other setting equals the base. The row records `a`.
- **Variant pick, on no control and p333 only, in S, seeds 7,488,010-049 (n = 40):** the smallest `a` with all of:
  - the median `end_stop2` of no control falls by at least 75 % against the base on the same seeds;
  - the same holds for p333;
  - collisions per run are at most the base's + 0.05, for both arms;
  - `m_stuck_n` is 0 and the drain test of V486 passes.
  No delay or close-following value is read for the pick. If no `a` passes, M2 is **VOID**: the variant is not built another way inside this study. A V-L or V-G variant would be a new study.
- **Report beside the pick:** `end_stop` (merge 1) on the same runs, and `m_mergepos_m2`, so the variant's merge-2 waiting can be compared with merge 1's.

## 3. Conclusions tested (fixed now)

| # | Cell | Recorded conclusion | Comparison | Measure |
|---|---|---|---|---|
| C1 | TRUCK | Delay tie within about ±1 % (S6, V496) | v3w (each learner) against os0_10_10, p333, 3E-D_TRUCK, lr1000_16_2 | `all_delay` |
| C2 | TRUCK | Close-following edge against the searched rule, +11.80 % [+4.97, +19.71] | v3w against 3E-C_TRUCK | `ttc_net` |
| C3 | S | Delay tie with p333 (+0.13 % [−0.74, +0.98] with single learners) | v3w against p333, os0_10_10 | `all_delay` |
| C4 | S | p333 is the delay-best stored rule | p333 against os0_10_10, lr1000_16_2, 3E-D_TRUCK | `all_delay` |
| C5 (D2) | X1 | Delay edge, +4.2 % [+2.4, +5.9] against p333 (120 seeds) | v3w against p333, os0_10_10 | `all_delay` |

v3w is read as the mean of the five learners' effects, each learner's run against the rule's run, seeds resampled jointly. That is the statistic that passes its no-effect null (memo §4.4). Plan B's pooled arm is printed beside it and is not read.

## 4. Arms and cells

- **S and TRUCK:** no control, p333, os0_10_10, 3E-C_TRUCK, 3E-D_TRUCK, lr1000_16_2, and the five v3w learners (11 arms), each exactly as in S6 (same config hashes, same checkpoint hashes).
- **X1 (if D2 allows):** no control, p333, os0_10_10, 3E-T, and the five learners (9 arms), on both plants.
- **Identity:** before any variant row, the base plant is replayed on 3 S6 seeds for every S and TRUCK arm. Every key must be equal by value (V499: never by line text). A difference stops M2 until it is explained.

## 5. Measures

- **Deciding:** `all_delay` and `ttc_net`, per §3.
- **Location report (PR-28's own wording):** delay and close-following by road (`m_road_*`) and by period, `end_stop2`, `end_stop`, `delay_ramp2`, `m_mergepos_m2`, on both plants.
- **Report-only:** flow, collisions, hard braking (`b45_net`), `m_stuck_n`, the drain values.

## 6. Reading (fixed now)

For each comparison, the paired effect on the base plant is Δb and on the variant Δv, both in % of the rule's median. The interaction is I = Δv − Δb, computed per seed and bootstrapped (B = 20,000, percentile, 97.5 % two-sided).
- **HOLDS:** the CI of I lies inside ±1.0 percentage point for delay, or ±5 points for close-following.
- **LANE-END-BOUND:** the CI of I excludes 0, and |I| is at least 1.0 point for delay or 5 points for close-following.
- **UNCLEAR:** otherwise.

A conclusion with several comparisons takes the worst reading of them: LANE-END-BOUND before UNCLEAR before HOLDS.
- **Consequences, fixed now:**
  - LANE-END-BOUND: every later sentence about that conclusion carries "depends on SUMO's lane-end behaviour at merge 2 (PR-28)", and the variant's value is printed beside the base value.
  - HOLDS for every conclusion: PR-28 moves from "gap" to "partial: located; robust to V-A" in the V&V record.
  - No reading reopens a closed cell or counts toward a claim.
- **Effect on EV (§ of the EV protocol):** EV runs on the base plant. If C1 or C3 reads LANE-END-BOUND, EV's deciding comparison is also run on the variant before any pass is read.
- **Null:** before the reading, the label-swap null of I (base and variant labels swapped within seed) must give a CI excluding 0 in at most 1.5 times the nominal 2.5 % share; otherwise the reading is VOID. Power is planned in §8.

## 7. Seeds, runs and cost

| Seeds | Use |
|---|---|
| 7,488,000-009 | smoke, determinism (T3), traced against untraced, PR-24 trace of `end_stop` and `end_stop2` |
| 7,488,010-049 | variant pick (no control and p333, S) |
| 7,488,050-099 | reserved: smoke repeats after a code fix |
| 7,480,400-639 (D4) | S and TRUCK verdict: variant runs only; base rows are the stored S6 rows |
| 7,488,600-759 (D2) | X1 verdict, both plants, n = 160 |

| Stage | Runs |
|---|---|
| Smoke, identity replays (11 arms × 2 cells × 3 seeds), trace, determinism | about 90 |
| Variant pick: 5 levels (base + 4) × 2 arms × 40 seeds, no pack | 400 |
| Verdict S and TRUCK, variant only: 11 arms × 2 cells × 240 seeds, with the pack | 5,280 |
| Verdict X1 (D2): 9 arms × 2 plants × 160 seeds, with the pack | 2,880 |

At $0.36 per 1,000 pack runs (V493) and about $0.12 per 1,000 runs without the pack (V490): about $2.0 without X1 and $3.0 with it, plus setup. Machine time: about 3.5 h without X1 and 5.5 h with it, at 1,690 pack runs per hour on 90 workers. Build: the variant flag, the runner's seed block, the reader with planted-row tests: about 5-7 h.

## 8. Checks before the verdict

| Check | Requirement | If it fails |
|---|---|---|
| Identity | base replays equal stored rows by value | stop; explain; re-run (§11 bug rule) |
| Determinism (T3) | the same run twice is equal | stop |
| Trace (PR-24) | traced `end_stop2` samples equal the counter on 2 seeds × {no control, p333} | the counter is not read; M2's lane-end numbers are dropped |
| Variant binds | `lcAssertive` read back from libsumo equals `a` for ramp-2 vehicles on 4a_0 | stop |
| Untraced equal | traced and untraced runs equal (V386) | stop |
| Power (planning) | computed from the S6 rows before any variant run: the share of studies in which I's CI lies inside the HOLDS band when the true I = 0, and excludes 0 when the true I = 2 points | stated in the run record; the bands are not changed after it |

## 9. Disclosures every M2 sentence carries

- V&V check; post hoc; the plant variant is a sensitivity case, not a validated plant.
- No field reference exists for lane-end behaviour; SUMO's documentation is the only primary statement found.
- V-A keeps SUMO's gap rule that reads the follower's commanded headway (PR-08); M2 does not test that rule.
- If D4: the S and TRUCK base rows are S6's, run at `b0c9360`; identity replays tie them to the M2 code.
