# an_s6_independent_measures: is v3w's safety edge visible outside its reward? (screen F)

Paths: `PS` = `/home/catalin/work/phd/wt/planb_v23/v5b/fleet/plant_sweep.py`, `BE` = `.../b_env.py`, `ME` = `.../measure.py`. Scripts and full tables: `/tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/89ba3663-8e1a-45c3-9415-9e2a743fb16b/scratchpad/phaseB/s6/` (`extract.py`; pooled effects with CIs for every field in `an2_out.txt`; per-learner ranges in `an5_out.txt`; shares and recorded entries in `an3_out.txt`).

**Every number is EXPLORATORY** unless marked "record". Method: 240 paired seeds; effect = −median(P − O) / median(O) × 100, positive = v3w lower; 95 % percentile bootstrap, 10,000 resamples, rng 20261110. "Pooled" = per-seed mean of the 5 learners (read6's convention). Tables give the **range of the 5 single-learner effects** and (a/b) = learners whose CI lies on the better / worse side. Check: pooled values reproduce read6 v2.3 `map_report_only` (ttc15 vs p333, TRUCK: record +51.85 [+43.11, +60.30], mine +51.9 [+43.0, +60.3]); rows with absent counters read as 0 match the record (sev3 265, ttc15 326, ttc2 3).

## 0. Answer

1. **Visible on stricter versions of the rewarded count, not on measures of another kind.** TTC below 2 s and 1.5 s and DRAC ≥ 3 m/s² (all 1 Hz) show an edge in both cells against every arm, 5 of 5 learners: larger than at 3 s against the rules, equal or larger against no control. They are subsets of the rewarded events.
2. On measures with no reward term, v3w is slightly better than p333, **not shown different from 3E-C_TRUCK** on most, and shown worse on 0.1-s jerk.
3. The memo's "braking events at 4.5 m/s² or harder" is already in the rows; there v3w is **shown worse than 3E-C_TRUCK** in TRUCK (record, pooled: −5.73 [−8.28, −2.31]; 3 of 5 learners).
4. **The pooled arm is biased against v3w on right-skewed measures.** In S its median `ttc_net` is 548.5 while the five learners' medians are 451.5-482.5; delay 127.5k against 124.7k-126.7k veh-s. The memo's "S: v3w has more delay than p333, −1.57 % [−2.70, −0.24]" is this artefact: per learner −0.8 to +0.5 %, 0 of 5 CIs exclude 0. INFERENCE: a mean of 5 runs carries a breakdown on more seeds than one run does.

## 1. Fields

Reward: per ALKS and second, TTC < 3 s and acceleration ≤ −3.0 m/s² ("hard"), own and, at half weight, its direct follower's (BE:31-32, :802, :811-812, :815-818, :842-843); collisions shared (BE:446).

| Class | Fields | What they count |
|---|---|---|
| In the reward | `ttc_net` = `ttc3` = `m_ttc3_all` (equal on all 13,920 rows); `brake_net`; `collisions` | 1-Hz vehicle-seconds over all pairs on the network (the reward charges pairs with an ALKS) |
| Closely tied | `ttc_half`; `ttc2`, `ttc15`; `sev3`; `E30`, `E15`; `b3/b45/b7_step`, `alks_b*_step`, `b45_net`, `b7_net`; `m_events_*`, `m_peak_*`, `m_dur_*`, `m_cascade_*`, `m_robust_road`; `alks_full_*`; `free_brake_alks*`; the splits `ttc*_s/_r/_p_*`, `m_road_ttc3`, `m_ttc3_lc`; side-file `brk` | TTC < 3 s at the half-second phase (PS:154-158); TTC < 2 and < 1.5 s and dv²/(2·gap) ≥ 3, i.e. DRAC, at 1 Hz (PS:194); merge-1 area only (BE:277-296); 0.1-s seconds at ≤ −3/−4.5/−7 (PS:139-146); 0.1-s braking events from −3, by peak (ME:174-204); onsets at ≤ −8.99 (PS:147-149) |
| Independent | `gap25`, `stop_gap`; `a2`, `m_a2_*`; `jerk`, `jerk_step`; `m_ah_*`, `m_vh_*`; `fuel*`, `m_fuel_mg_*`; `undertakes`, `pass_*`; `end_stop`, `end_stop2`, `halt_3a_*`; `m_cong_*`; side-file speed field (`osc_kmh`, jam metrics, ME:454-486); `teleports`, `m_stuck_n` | bumper gap < 2.5 m, moving or stopped (BE:809-810; a term of an earlier env's reward only, BE:559-561); Σa²; Σ\|Δa\|; acceleration and speed histograms; ALKS passing a left-lane vehicle above 60 km/h (PS:275-280); stopped in the last 30 m of an accelerating lane (PS:291-294) |

What the counts measure:
- `stop_gap` is 0 in every no-control run and 212 (median) under p333. INFERENCE: stopped short-headway ALKS resting inside 2.5 m in a queue (as V283); a queue artefact, not safety.
- `ttc15` is 98 % below 10 m/s in every arm; `sev3` is 91-94 % at 10 m/s or more. They are a low-speed and a high-speed severity count.
- INFERENCE: no field is statistically independent. Per-seed differences against p333 correlate with the `ttc3` difference at Spearman 0.61-0.98 (delay 0.83), except `undertakes` (0.37) and `end_stop` (0.14).

## 2. Comparisons: range of the 5 learners' effects, % (a/b)

**TRUCK.** Levels are medians per run: learners; p333; 3E-C_TRUCK; no control.

| Measure | vs p333 | vs os0_10_10 | vs 3E-C_TRUCK | vs no control |
|---|---|---|---|---|
| Rewarded `ttc_net` (773-836; 1178; 951; 1234) | +25.4..+32.9 (5/0) | +22.4..+25.7 (5/0) | +11.5..+13.9 (5/0) | +28.9..+35.5 (5/0) |
| Tied `ttc15` (26-30; 68; 48; 47) | +51.1..+56.3 (5/0) | +48.3..+51.7 (5/0) | +37.9..+42.1 (5/0) | +38.3..+46.8 (5/0) |
| Tied `sev3` (35-41; 64; 57; 74) | +35.4..+41.7 (5/0) | +35.9..+42.7 (5/0) | +27.2..+35.1 (5/0) | +43.2..+52.7 (5/0) |
| Tied `b45_step`, s (297-313; 363; 309; 375) | +12.4..+18.9 (5/0) | +4.5..+9.1 (5/0) | −3.0..+2.1 (0/0) | +11.8..+18.7 (5/0) |
| Tied events ≥ 4.5, all (667-695; 774; 668; 842) | +8.1..+15.9 (5/0) | +0.6..+7.7 (2/0) | **−6.6..+0.4 (0/3)** | +14.8..+20.4 (5/0) |
| Tied events ≥ 4.5, human cars (209-222; 241; 197; 267) | +2.9..+17.2 (4/0) | −4.3..+6.1 (0/0) | **−16.8..−5.1 (0/4)** | +13.7..+18.9 (5/0) |
| Tied `E30`, merge 1 (75-86; 104; 68; 140) | +10.1..+20.3 (5/0) | +5.2..+16.6 (3/0) | **−20.6..−12.5 (0/5)** | +26.4..+35.0 (5/0) |
| Indep. acceleration RMS, ALKS, 0.1 s | +1.4..+2.1 (5/0) | +0.6..+1.3 (5/0) | −0.4..+0.2 (0/0) | **−1.6..−0.6 (0/5)** |
| Indep. jerk per step, 0.1 s | +0.4..+0.7 (5/0) | +0.1..+0.4 (4/0) | **−0.6..−0.3 (0/5)** | **−5.2..−4.9 (0/5)** |
| Indep. seconds at −3 ≤ a < −1.5 | +0.7..+2.3 (3/0) | −0.7..+1.3 (0/0) | −0.7..+1.2 (0/0) | +10.2..+12.5 (5/0) |
| Indep. `undertakes` (200-205; 220; 206; 213) | +5.5..+8.2 (5/0) | +4.1..+8.3 (5/0) | +0.2..+3.4 (2/0) | +2.8..+5.6 (4/0) |
| Indep. `end_stop`, merge 1 (43-51; 57; 56; 95) | +9.6..+16.7 (0/0) | +6.4..+17.3 (0/0) | +0.0..+11.6 (1/0) | +33.2..+42.1 (5/0) |
| Indep. `end_stop2`, merge 2 (465-554; 850; 556; 610) | +25.3..+39.8 (5/0) | +18.7..+31.7 (5/0) | −4.8..+11.2 (0/0) | +2.2..+20.4 (3/0) |

**S (steady).**

| Measure | vs p333 | vs os0_10_10 | vs 3E-C_TRUCK | vs no control |
|---|---|---|---|---|
| Rewarded `ttc_net` (452-483; 629; 546; 1234) | +18.1..+31.7 (5/0) | +9.6..+28.1 (5/0) | +6.7..+29.4 (3/0) | +45.0..+51.3 (5/0) |
| Tied `ttc15` (12.5-15; 28; 25; 42) | +39.3..+57.1 (5/0) | +31.6..+52.6 (5/0) | +32.0..+50.0 (5/0) | +57.1..+64.3 (5/0) |
| Tied `sev3` (17-21; 32; 26; 72) | +31.2..+45.3 (5/0) | +23.4..+45.3 (5/0) | +23.1..+50.0 (5/0) | +58.3..+65.3 (5/0) |
| Tied events ≥ 4.5, human cars | +3.5..+19.9 (2/0) | −5.0..+9.6 (0/0) | −13.1..+1.2 (0/0) | +25.8..+31.7 (5/0) |
| Tied `E30`, merge 1 (38-46; 46; 37; 16) | +2.2..+15.4 (2/0) | +3.4..+9.0 (0/0) | −18.9..−2.7 (0/3) | **−146.9..−106.2 (0/5)** |
| Indep. acceleration RMS, ALKS | +0.3..+1.6 (1/0) | −0.5..+1.0 (0/0) | −0.6..+0.9 (0/0) | +7.1..+7.6 (5/0) |
| Indep. jerk per step | +0.3..+0.4 (5/0) | −0.0..+0.1 (0/0) | −0.3..−0.1 (0/1) | **−2.2..−2.0 (0/5)** |
| Indep. `undertakes` | +4.6..+7.4 (5/0) | +2.3..+5.3 (4/0) | +3.5..+6.5 (5/0) | +11.4..+14.9 (5/0) |
| Indep. `end_stop` (34-37; 35; 37; 20) | −2.9..+11.6 (0/0) | −3.1..+3.1 (0/0) | +2.7..+14.9 (0/0) | **−50.0..−37.5 (0/5)** |
| Indep. `end_stop2` | +22.6..+37.3 (5/0) | +8.3..+21.5 (2/0) | +1.7..+15.6 (1/0) | +32.1..+46.2 (5/0) |

Pooled CIs for the decisive column (vs 3E-C_TRUCK, TRUCK): `ttc_net` +11.8 [+6.2, +18.9]; `ttc2` +40.5 [+34.8, +45.7] (5 of 5; +31.3 [+26.5, +34.2] vs no control); `ttc15` +37.5 [+27.4, +46.5]; `sev3` +26.8 [+19.6, +38.9]; human-car events ≥ 4.5 −14.6 [−21.3, −8.7]; jerk −0.5 [−0.6, −0.3]. In S: `ttc15` +30.8 [+8.0, +63.2]; `sev3` +27.7 [+5.0, +51.5].

Speed oscillation `osc_kmh` (record, side files, pooled only): TRUCK −0.15 [−0.36, +0.28] vs p333, +1.02 [+0.55, +1.36] vs 3E-C_TRUCK, +6.94 [+6.36, +7.63] vs no control; S +1.11 [−0.99, +2.87] vs 3E-C_TRUCK, +12.11 [+10.53, +13.29] vs no control.

Tiny counts, not testable: `gap25` (0 in 1,200 v3w runs per cell); `collisions` (TRUCK: v3w 1 in 1,200 runs, w1u500, 65 contact steps, rules 0 in 5,520; S: v3w 0, rules 4 in 5,520); `teleports` 0; `b7*` 2-3 per run; `E15` 0-4; `alks_full_moving` 0.09-0.15 per run.

Tied counts where every controlled arm is worse than no control:
- moving full-emergency ALKS events: no control 0 in 240 runs per cell; v3w 109 events (102 of 1,200 runs) in TRUCK and 136 in S; the 23 rules 634 and 734 in 5,520 runs;
- ALKS events with a peak between −5 and −9 m/s² (record `alks_past_limit`, read6.py:143; TRUCK, pooled): −407.78 [−413.33, −395.56] against no control (44.8 against 9 per run), yet +17.61 [+15.23, +20.18] against 3E-C_TRUCK.

`pass_straight`, the only kind V369 calls an undertake (about 44 per run), is not shown different against any arm.

## 3. Where and at what speed

The rows split TTC at 5 and 10 m/s (PS:192) and by road, not by lane. So the share below 7 m/s and the accelerating-lane share **cannot be computed**. Edge 4a counts all its lanes. Shares are ratios of mean reductions, so pooling does not bias them.

| Share of v3w's reduction in `ttc3` | below 5 m/s | 5-10 m/s | ≥ 10 m/s | edge 4a | edge 3 | ramp 2 |
|---|---|---|---|---|---|---|
| vs p333, TRUCK (434 s per run) | 40.7 % [39.0, 42.3] | 25.6 % | 33.6 % | 77.0 % [73.8, 80.4] | 16.5 % | −0.1 % |
| vs p333, S (351) | 37.6 % [35.3, 39.4] | 27.3 % | 35.0 % | 85.6 % [80.4, 92.6] | 13.9 % | −2.3 % |
| vs 3E-C_TRUCK, TRUCK (136) | 15.0 % [4.0, 21.0] | 22.5 % | 62.5 % [54.3, 78.0] | 60.8 % [50.4, 70.0] | 32.9 % | 13.0 % |
| vs no control, TRUCK (395) | 44.6 % | 34.9 % | 20.6 % | 24.2 % [18.4, 29.7] | 10.5 % | 42.6 % [38.5, 47.0] |

- Against 3E-C_TRUCK in TRUCK, the edge is not shown below 5 m/s (pooled +4.6 [−3.9, +11.7], 2 of 5) and is shown at 10 m/s or more (+24.0 [+16.0, +30.2], 5 of 5).
- INFERENCE: memo reason M6 ("mostly low-speed queue following") fits the edge over p333 and no control. It does not describe the margin over the best rule.
- At merge 1, v3w has more close-following than 3E-C_TRUCK in both cells and, in S, more than twice no control's (`E30`).

## 4. Verdict per independent measure

Against 3E-C_TRUCK, which has the lowest median of the 23 rules on most fields, and against no control.

| Measure | vs best rule | vs no control |
|---|---|---|
| Acceleration RMS, 0.1 s | not shown different | TRUCK shown worse; S shown better |
| Jerk, 0.1 s | TRUCK shown worse (0.3-0.6 %); S 1 of 5. Against the lowest-jerk rule of each cell, shown worse, 5 of 5: `copy` in TRUCK, pooled −0.8 [−0.9, −0.6]; `3ex1` in S, −0.6 [−0.8, −0.4] | shown worse (2-5 %) |
| Sub-threshold braking seconds | not shown different (S: −0.9..+2.0, 0/0) | shown better (S: +27.1..+30.2) |
| `osc_kmh` (record) | TRUCK shown better (1.0 %); S not shown different | shown better |
| Fuel per km | not shown different (within 0.2 %) | shown better (0.5-1.3 %) |
| `undertakes` | TRUCK not shown different; S shown better | shown better |
| `end_stop`, merge 1 | not shown different | TRUCK shown better; S shown worse |
| `end_stop2`, merge 2 | not shown different | TRUCK 3 of 5; S shown better |
| `stop_gap` | queue artefact, no verdict | 0 under no control |
| `gap25`, collisions, teleports | too few to test | too few to test |

## 5. For a pre-registered screen F

- **Usable, outside the reward, enough counts:** acceleration RMS per class (`m_a2_*` / `m_n_*`; pooled CI half-width about 0.4 %); 0.1-s jerk; seconds at −3 ≤ a < −1.5 from `m_ah_*` (a check on threshold gaming; none seen); `osc_kmh` from the side files; `end_stop`, `end_stop2` (noisy); `pass_straight`.
- **Usable as severity checks, tied to the reward:** `ttc15` (13-68 per run), `sev3` (17-74), `ttc2`; hard-braking events by class (`m_peak_*[3:]`, 120-840 per run). Human-car events are only partly rewarded (a car behind an ALKS, half weight); the rows cannot split them by leader type.
- **Not usable:** `gap25`, `collisions`, `contact_steps`, `teleports`, `m_stuck_n`, `alks_full_moving`, `b7*`, `E15`.
- **Named by the memo, not in the rows:** TTC at 0.1 s at any threshold (only 1 Hz; the half-second phase changes nothing, pooled +25.8 [+19.9, +33.9] against +26.9 vs p333); DRAC at 0.1 s, or at 7 m/s². Also absent: TTC by lane and by leader class.
- **Named by the memo, already in the rows:** braking at 4.5 m/s² or harder at 0.1 s. If §5.2's second KILL rule counts it as "outside the reward", the stored TRUCK rows already trip it against 3E-C_TRUCK. I class it as tied.
- **The meter does not match the memo's list:** `docs/research/explore2/e1_meter.py:14` holds thresholds for TTC 3 s, DRAC 3 and 7, braking 3 and 7 only; no TTC 1.5 s, no 4.5 m/s². I found no ledger row after V435 saying it ran.
- **Statistic:** the screen should compare single learners with single rule runs, or pool both sides; the 5-run mean against one run is biased on skewed counts (§0.4).
