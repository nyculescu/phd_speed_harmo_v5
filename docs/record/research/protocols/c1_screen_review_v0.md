# C1 draft v0 review, and how v1 handles it

Reviewers (2026-11-11): statistics, logic and plant on Fable; rules and build on Opus; each serious finding went to a skeptic at Extra High. 37 findings: 6 blockers, 21 majors, 10 minors. Of the blockers and majors the skeptics confirmed 11 and partly confirmed 16; none was refuted. Full texts are in the session scratchpad.

| # | Finding | Verdict | v1 handling |
|---|---|---|---|
| 1 | The pooled v3w arm (mean of 5 runs against 1 rule run) is biased against v3w with no true effect (S6 S: delay −1.31, close-following −10.98 when nothing differs), and the swap null cannot see it (stats) | partly | deciding statistic is the mean of the five single-learner effects; pooled printed beside; a learner null added (C-D5, §5) |
| 2 | K2 closes C on a "not shown" non-inferiority reading; at n = 240 a true tie fires it 24-42 % of the time (logic, stats) | partly | K2 KILLs only if delay is shown worse; "neither kept nor worse" is NOT RESOLVABLE; delay added to the n rule |
| 3 | K1 can close C while its own interval allows the 10 % edge (stats) | confirmed | K1 closes only if the upper bound is below 10 %; otherwise NOT RESOLVABLE |
| 4 | NO COST is a "not shown" reading; stored jams are worse for v3w, so "v3w meets C's goal" would be wrong (logic, stats) | confirmed | NO COST needs the cost shown absent (lower bound above −3 %); otherwise COST UNDECIDED; cost added to the n rule; NO COST closes only "C as defined" and states the jams reading |
| 5 | 3E-C_TRUCK spends delay that stage 2's rule may not (admitted at +2 %) (logic) | partly | disclosed in §12 and in K1's sentence |
| 6 | The outcome is a conjunction of readings; the prior mixed truth and detectability (logic) | partly | §1 gives the outcome rate under C's premise; the n rule covers all three readings |
| 7 | C1 departs from V520's "rules-only" without saying so (logic, rules) | partly | labelled in the status line and C-D3; the author's yes is needed |
| 8 | In E30 "elsewhere" is dominated by the event zone (sizing rows: 19 % → about 40 % of close-following), so K3's sentence was wrong (plant) | partly | three-way split (merge 2, event zone, other); K3's sentence names where v3w is worse |
| 9 | Check (a)'s NOT SENSITIVE is unreachable for p333 at n = 60 (plant) | confirmed | label only: SENSITIVE or "sensitivity not shown at n = 60"; never NOT SENSITIVE |
| 10 | Check (b)'s bind test (tau_on_n rising) cannot fail; its drain test reads a capacity change as a failure (plant, rules) | confirmed | the command acts: p333 against no control CI excluding 0 on close-following or delay, with a swap null; queues printed, not gated |
| 11 | Deferring (b) departs from V520(2) on a wrong build estimate (fixed shares need no new seed stream) (rules) | confirmed | (b) runs beside (a) through a job-level share field |
| 12 | TTT missing; common §3 not inherited (rules) | partly | §3 inherited; `N` printed in every table |
| 13 | Zero-tolerance "any stuck row" drain rule has a false-fail rate that grows with n (rules) | confirmed | per-arm rule: more than 0.5 % stuck rows or mean end backlog more than 2 vehicles above no control |
| 14 | Cost quoted at an inferred rate; n = 1,920 reaches $3 at the measured rate (rules) | partly | both rates quoted; cap $4 proposed |
| 15 | v3w identity could VOID on known-harmless diagnostic differences (rules) | partly | traffic keys compared; decision diagnostics printed only |
| 16 | A pause after the pilot could mix CPU models (rules) | confirmed | host released; pilot seeds re-run on the new host |
| 17 | C-D8 "label only" contradicted §7's "fix its lane length" (rules) | confirmed | stage 2 reads at 295 m and, if SENSITIVE, at the shortest usable longer length, named now |
| 18 | The K3 power condition could never bind (stats) | partly | deleted |
| 19 | Pilot SE varies 20-25 % at 60 seeds (stats, minor) | minor | pilot SEs multiplied by 1.15 |
| 20 | SEs quoted in another convention (stats, minor) | minor | quoted under the chosen statistic |

## Round 2: recheck of v1, and how v2 handles it

Two recheckers at Extra High (2026-11-11): statistics and logic (Fable), rules, plant and build (Opus). 2 blockers, 11 majors, 4 minors. All numbers are exploratory recomputes on stored rows (scripts in the session scratchpad, `c1v1/` and `c1v1rules/`).

| # | Finding | Severity | v2 handling |
|---|---|---|---|
| 21 | The learner null (4 against 1) is the biased construct C-D5 rejects; it VOIDs with probability about 1 at the n the rule picks | blocker | deleted as a gate; the 4-against-1 effect and per-learner range printed; the single-run-noise assumption disclosed (§5, §12) |
| 22 | Delay "worse" (upper bound < 0) overlapped "kept" (lower bound > −1 %): a shown loss inside the tie band would kill C | blocker | house harm form: WORSE needs the point at or below −1 % and the 95 % upper bound below 0; K2's sentence names the uncharged policy; planted row (C-D6, §5, §7) |
| 23 | Cost absence above −3 % is not powered: P(absent \| 0) about 0.35 at the planned SE | major | absence bar −5 % (the planned cost), present read first (C-D12); the pilot table prints P(present \| −5), P(absent \| 0), P(COST UNDECIDED \| stored truths) |
| 24 | The "event zone" (edges 1-2) holds 3-4 % of E30's star; 3a (merge 1) holds about 20 %; K3's "only at merge 2" is tested by nothing | major | six road groups; R-else on "away from both merges" (1-5); K3's sentence states R-else and the printed merge parts; §12's figures replaced by the by-group shares (§4) |
| 25 | §1's 0.74 is at an n the rule rarely picks; the pilot prints SEs only | major | §1 quotes the modal-n rates (0.95, 0.92) and the S-like ask rate; the pilot prints the outcome table at each n; realised SE printed |
| 26 | NO COST says "goal met" even when `events_ge45` is shown worse | major | `events_ge45` and `jams` veto NO COST at 95 %; new reading COST ON ANOTHER MEASURE (parked) |
| 27 | Levels of R-delay and R-else not stated; harm convention is 95 % | minor | levels stated: good readings 97.5 %, harm readings 95 %; null bounds 1.9 % and 3.75 % |
| 28 | The delay clause was read before K1, so a decisive no-edge reading could be parked | minor | order: edge, K1, then delay only after the edge is shown; planted row |
| 29 | The per-arm backlog test against no control can never fail and is blind to EV's drain failure (also v0's plant.5 fix, dropped without a row) | major | V486's form within E30 against p333, v3w averaged per seed; false-fail rate written in (§2) |
| 30 | The stuck rule's pooling was unstated; false VOID 7.2 % for 3E-C_TRUCK at n = 240; no rule if p333 fails | major | v3w pooled, per-learner counts printed; threshold 1 % (false VOID 1.0 % at 240); p333 failing parks C (§2) |
| 31 | Stage 2 reading at a longer lane puts position-fixed controllers in the wrong place | major | controllers compared at 295 m only; (a) is a label printed with every sentence (C-D8, §6) |
| 32 | Check (a)'s SENSITIVE has no null (family false rate 0.13-0.21); stuck-0 fails a length 11.8 % of the time; "no usable length" undefined | major | Bonferroni bar; sign-flip null printed; stuck runs dropped and counted; "(a) not readable" named |
| 33 | Check (b)'s swap null has no bar; zero stuck/teleport rules; lane-end stops and oversaturation missing; §11 contradicted | major | delay-only command test with a 7.5 % null bar; at most 1 of 120 stuck or teleported; oversaturation item; `end_stop`, `end_stop2` printed; §11 reworded |
| 34 | Declining C-D3 left V520's literal step with no bar, so it could not be chosen | major | form B written with readings and consequences (§5b) |
| 35 | Identity key classes incomplete; departs from V519's tolerance; a new-CPU mismatch VOIDed; host-change pilot unclear | minor | three key classes defined; departure stated; new-CPU mismatch logged and disclosed; new host: identity and T3 first, n kept |
| 36 | Dropped v0 minors: count base (rules-build.9), P0 label (logic.6), absent keys (plant.6), unsized fallback (plant.4); V510's timing; per-run rate of policy runs | minor | C-D13 and C-D14 added; P0 on delay as CLAUDE.md states; absent keys count as 0 with a planted row; fallback labelled E30-short, unsized; smoke measures the policy-run rate |

## Round 3: recheck of v2, and how v3 handles it

Two recheckers at Extra High (2026-11-11): statistics and logic (Fable), rules, plant and build (Opus). Rows 21-31 confirmed fixed; no blocker. Scripts and outputs in the session scratchpad `c1v2/`.

| # | Finding | Severity | v3 handling |
|---|---|---|---|
| 37 | "absent" could fire on a shown cost of 0-3 % (e.g. −2.5 [−4.9, −0.1]), so NO COST would close C on a shown cost; C-D12's con was wrong | major | absent also needs the upper bound at or above 0; a shown cost under 3 % is COST UNDECIDED; planted row (C-D12, §5) |
| 38 | The n rule named no projection, so as written no n ever passes | major | SE_n = 1.15 × SE_60 × sqrt(60/n) written in |
| 39 | The NO COST vetoes had no null; `events_ge45` fired falsely 4.3 % on TRUCK swaps | major | vetoes' null rates printed and labelled; they never VOID, since a veto only parks C |
| 40 | §1's bracket hid that stored truths park C (TRUCK-like, 0.89) or close it (S-like, NO COST 0.96) | minor | §1 rewritten with round 3's rates; §12 says ROOM is not the likely outcome |
| 41 | K1's 10 % bound had no level | minor | R-star's 97.5 % upper bound |
| 42 | R-else degenerates in S-like spreads (opponent median 23.5, many exact-zero differences) | minor | "not readable" rule (read as NOT SHOWN); pilot prints its median, SE and tie share |
| 43 | Planted K1 rows had no interval | minor | intervals planted; NOT RESOLVABLE (edge) row added |
| 44 | (a)'s usable-length rule quoted M2's braking rate; its real null false-fail was 0.73 for p333 | major | point form for both bounds, `alks_full_moving` bar 0.15 per run; null false-fail 0.3 % (p333) and 0 (no control) on stored rows |
| 45 | Key classes missed `ctrl_sha256` and `name`; the rules identity row had no classes | major | one class definition for both identity rows |
| 46 | The road groups left out the insertion queues, so the delay split check would stop the run at smoke | major | queues assigned to merge 1, merge 2 and an origin-queue group; tolerance 0.1 % |
| 47 | Form B lacked V520 guard (1)'s elsewhere reading and a K3; P0 only printed; vetoes outside the rule table; p333 stuck unhandled | major | R-else' and K3' added; P0 deciding; vetoes in the table; p333 failing either drain part VOIDs B |
| 48 | C-D14 amended the whole intended use on evidence from steady S only | major | amendment limited to steady traffic at 5,300 veh/h; stage 2's robustness row gates E30 drain at 0.3 and 0.7 first |
| 49 | §2's p333 stuck consequence disagreed with §7's order | minor | conditional on the edge being shown |
| 50 | No path for a gate bind failure; EV's stuck item dropped | minor | bind failure → VOID, no fallback; stuck item restored as "at most 1 per arm and cell" |
| 51 | (b)'s oversaturation statistic undefined | minor | mean over the 60 seeds, V486's form, null printed |
| 52 | Stage 2's robustness row listed unconditionally | minor | conditional on PLANT OK (C-D14) |
| 53 | §11 omitted the gate's S rows; count wording contradictory; form B count unstated | minor | reworded; form B stays 94 |
| 54 | P0's example was in the raw sign | minor | "positive = less delay"; planted rows |
| 55 | `b_env.py:1111` is blank at `311f76c` | minor | `b_env.py:1110` |
| 56 | Form B's pilot truths undefined | minor | stated in §5b |

## Round 4: final check of v3

One checker at Extra High (Fable, 2026-11-11). Rows 37-56 confirmed fixed; (a)'s numbers, the code references, form B's signs, the n rule and the planted rows under §7's order reproduce.

| # | Finding | Severity | v3 handling |
|---|---|---|---|
| 57 | The "not readable" rule did not fire on stored S (tie shares 18-20 %, 4 of 5 learner medians exactly 0) | major | adds "any learner's median exactly 0" and a 10 % tie share; planted row at 19 % |
| 58 | The pilot did not print R-else's median and tie share | minor | printed by the pilot (not paired effects) |
| 59 | The planted P0 fail row left 3E-C_TRUCK passing | minor | both arms at +5 % |
| 60 | Form B's truths lacked else' and the vetoes' | minor | premise values stated; stored values computed by the pilot script from S6 rows before the pilot |
