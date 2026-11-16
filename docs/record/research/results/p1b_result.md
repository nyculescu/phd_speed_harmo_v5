# P1b result: incident information for mainline metering, with amber, PI-law plans and runners

**(P)** = pre-registered (rule or report-only row); **(D)** = descriptive, computed after the data. Delay: door-to-door s/veh, incl. origin and meter queues. rel = median(r − t) / median(r), paired seeds; positive = t better. All statements hold **given an incident**. Evidence: `p1b_verification/`.

## 1. Outcome and provenance

- **Same verdicts as P1:** S1a FAIL; S1b PASS in slow_q2000 and block_q1600.
- Page `p1b_addendum.md` (V108) on `p1_incident_information.md`; both sha256 values match. Code `93ba655`, frozen worktree, run once, no resume.
- Runs: 14,550 tool-check, 75,120 tuning (7,400,300–339), 255,182 evaluation (7,400,600–699). None failed, teleported or collided. T0, T1, T3, T4 PASS; VSL did not enter.
- **Verification (D):** an independent script (no `v5b` import) re-tunes every arm and recomputes all rows: **6,217 values, 0 mismatches.** Another bootstrap seed moves 654 CI values, no verdict. 6 spot re-runs are identical.
- V112's "tool checks 6,150" is stage A only (total 14,550, `run.log`).

## 2. Pre-registered statements

Table 1 (P). S1 rows at the S1 level (0.99375); the rule tests the CI of the median difference. Bold: the rule holds.

| Statement | slow_q1600 | slow_q2000 | block_q1600 | block_q2000 |
|---|---|---|---|---|
| S1a: ID vs FB, rel % [CI] | −1.5 [−4.6, 4.7] | +4.8 [1.1, 6.9] | −2.6 [−8.4, 3.7] | +6.6 [3.7, 10.1] |
| S1a: ID vs PI | −17.9 [−35.1, −6.7] | −1.8 [−5.2, 0.0] | −0.7 [−10.1, 6.7] | −2.1 [−6.6, 0.0] |
| S1b: IP vs ID | +16.2 [−16.7, 27.4] | **+11.8 [5.8, 16.7]** | **+22.0 [8.8, 31.4]** | 0.0 (same plan) |
| S2 bracket [y, x], % | [−0.4, 47.9] | [−2.4, 19.3] | **[0.4, 25.4]** | **[3.5, 22.4]** |
| TP placebo, % (report only) | 37.7 | 16.8 | 13.6 | 15.7 |
| S3 d\*, s [95 %], binding arm (no test) | 2.6 [0, 7.1] PI | 120.4 [20.1, 168.5] PI | > 240 [192.8, 240] | IP never ahead (PI) |
| S3 c\*, s | 115.2 [0, 156.2] PI | > 180 | > 180 | never ahead (PI) |
| S3 p\* | 0.13 [0, 0.30] PI | 0.53 [0.21, 0.89] PI | 0.21 [0.12, 0.33] FB | never ahead (PI) |
| Combined row vs IP, rel % [95 %] | −20.5 [−48.4, −8.6] | −1.6 [−6.3, 2.9] | −16.5 [−18.5, −11.4] | −3.4 [−5.2, −1.7] |

- **S1a:** ID meets (a) against neither FB nor PI in any cell; it fails (b) against PI in slow_q1600.
- **S2:** the plateau failed everywhere: brackets only. block_q1600's lower bound (0.4 %) is close to 0.

## 3. Information ladder per cell

Table 2. Medians over 100 seeds.

| Per cell | slow_q1600 | slow_q2000 | block_q1600 | block_q2000 |
|---|---|---|---|---|
| Plans IP / ID (P) | c1000+back / f40_10 | p70_40_8_e4 / p20_20_14_e4 | p20_20_16_e4 / f40_10 | p20_20_14_e4 (= ID = PI's law) |
| Delay s: NC; strongest L0 → ID → IP → ORX_4 → OR_in (P) | 308.8; PI 174.8 → 202.9 → 175.2 → 159.6 → 118.2 | 520.5; PI 359.0 → 375.7 → 353.2 → 343.7 → 297.0 | 312.9; FB 247.9 → 257.9 → 210.8 → 200.9 → 160.8 | 540.6; PI 373.4 → 375.5 → 375.5 → 368.6 → 310.4 |
| IP vs N / FX / FB / PI / AD, rel % (P, report only, S1 level) | +25.1 / +30.4 / +14.4 / +4.5 / +19.1 | +36.3 / +25.1 / +8.2 / +7.4 / +12.2 | +30.2 / +30.2 / +15.9 / +18.0 / +26.3 | +27.3 / +19.6 / +6.6 / −2.1 / +12.9 |
| IP vs PI, CI | [−35.2, 14.6] | [−2.7, 13.1] | **[8.9, 31.6]** | [−6.6, 0.0] |
| Max queue tail, m of 410 (P): PI / ID / IP | 260 / 264 / 188 | 368 / 368 / 368 | 326 / 329 / 288 | 368 / 368 / 368 |
| Spill share (D, V109): PI / ID / IP | 0.04 / 0.06 / 0.00 | 0.89 / 0.94 / 0.85 | 0.32 / 0.26 / 0.05 | 0.95 / 0.96 / 0.96 |
| Runners s = 10 / 30 %: IP vs ID, rel % (P, report only) | −29.5 / −37.3 | +9.2 / +10.7 | +15.9 / +17.3 | 0.0 / 0.0 |
| Runners: IP at s vs IP at s = 0, rel % | −7.4 / −49.8 | +1.5 / −0.0 | −0.1 / +1.7 | +3.8 / +4.6 |

- **Only in block_q1600 does IP beat every L0 arm**, PI included, with all CIs above 0 (report-only row). The tuning runner-up plan gives +16.3 % vs PI (D).
- **block_q2000:** the best plan is PI's own law; starting it at onset costs 2.1 %.

## 4. P1 → P1b

- **Verdicts unchanged.** S1b: slow_q2000 17.2 → 11.8 %; block_q1600 18.4 → 22.0 %.
- **IP vs PI:** block_q1600 −0.7 → **+18.0 %**; slow_q2000 +6.9 → +7.4 %; block_q2000 +9.8 → −2.1 %.
- **S2:** positive lower bounds in 2 cells (P1: 1).
- **d\*:** slow_q1600 45.3 → 2.6 s; slow_q2000 25.8 → 120.4 s; block_q1600 never ahead → > 240 s; block_q2000 210.1 s → never ahead.
- **Emergency stops** (same SUMO counter): runs with ≥ 1 fell from 87 % to 12.8 % (7,396 / 57,782 runs, s = 0; D). No collisions.
- **Queues:** median max queue up to 297 veh (P1: 267.5).
- **Controller-family confound: reduced, not removed.** 3 of 4 IP plans (both S1b passes) are PI laws, but plans still start from N, not PI.

## 5. Realism rows

- **Amber.** No red crossing in any of the 249,782 evaluation runs at s = 0 (D). First vehicle stopped at red: approach median 1.6 m/s (FX up to 9.5), max 24.8–26.3 m/s (P); 13.8 % at ≥ 10 m/s (D).
- **Discharge (D):** 2–21 % below the commanded rate (feedback and PI arms; sums of phase medians); partly green time with no queue (not separated).
- **Queues and spill.** The tail never passes 369.6 of 410 m, so the B4 flag (7 m tolerance) never fired (P). The recomputed spill (D, V109: tail within 50 m of the entry, or mean depart delay > 5 s) exceeds 5 % for some arm in every cell and reaches 85–100 % at q2000 for N, FB, PI, AD, ID and IP. Delay counts the origin wait, so S1–S3 stand; but q2000 assumes unlimited upstream storage.
- **Runners (P, report only).** "IP vs ID −29.5 %" (s = 10 %, slow_q1600): IP's paired delay exceeds ID's by 29.5 % of ID's median (60.6 s/veh). "IP vs itself −49.8 %" (s = 30 %): runners add 87.3 s/veh, 49.8 % of IP's s = 0 median. **This plan is fragile:** an open-loop constant 1,000 veh/h (cycle 28.8 s: amber 10 %, red 69 %) that won tuning by only 4 s over a PI plan. Runners raise amber plus red discharge from 44 to 246 veh/h (s = 30 %); IP's command stays at 1,523 veh/h, while ID, FB and PI cut theirs by 146–223 (D). A 30-s detection delay also raises IP's median from 175.2 to 275.5 s (D).

## 6. What the paper can honestly say

On one simulated freeway bottleneck with mainline metering (one signal with a 3-s amber across 4 lanes), and given an incident, knowing only that an incident is on gave no detected gain of 10 % or more over a tuned always-on feedback meter or PI law; against always-on PI it was never better (−0.7 to −17.9 %). Knowing the incident type added 11.8 % [5.8, 16.7] and 22.0 % [8.8, 31.4] over presence alone in two of four cells, with PI-law plans in the action set. In one cell (a crawling lane at 1,600 veh/h), the type plan also beat tuned always-on PI by 18.0 % [8.9, 31.6] (report-only row), stayed ahead of every always-on arm up to 240 s of detection delay, and kept its lead with runners (D). Per-incident hindsight information beyond the type plan is only bracketed: [−0.4, 47.9], [−2.4, 19.3], [0.4, 25.4] and [3.5, 22.4] %.

It cannot say:
- that presence and timing pays ≥ 10 %, or that such a gain is excluded (vs FB the CI reaches 10.1 %);
- that the block_q1600 lead over PI is confirmed (not a pre-registered statement);
- anything robust for slow_q1600 (fragile plan; TP 37.7 %);
- that q2000 metering works without upstream storage;
- anything about ramp metering, prevalence, generality or novelty.

## 7. Limits and disclosures

- **One plant** (BN4, one signal across 4 lanes); the block incident is a substitute (1 m/s lane crawl, no lane changes).
- **SUMO noise:** the placebo TP gains 13.6–37.7 %; a larger A inflates OR_in.
- **Spill-flag fix after data** (V109), disclosed; S1–S3 unchanged.
- **Unit test:** generated demand on evaluation seeds 7,400,600–601; no simulation (V109).
- **Seed labels** (V108): tool checks sit in the block's tuning range, tuning in its validation range; 700–999 untouched.
- **Runner share** is a model parameter, not a field violation rate (R4).
- **Prior art:** Tympakianaki et al. 2014 (PI mainstream signals at lane drops) is the established PI baseline; only the information ladder is ours [VERIFY: mostly abstracts read].

## 8. Next steps for the ITSC paper (9.6 runs/s, measured)

1. **Confirm block_q1600** on fresh seeds from 7,400,700–999 (author approval), plan and rule fixed first: < 3,000 runs, ~5 min.
2. **"PI by default + type plan"** (switch from PI) to close the confound: ~22,000 runs, ~40 min.
3. **Queue override at q2000:** re-tune and re-evaluate, no replicates: ~140,000 runs, ~4 h.
