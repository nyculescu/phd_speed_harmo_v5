# Screen M analysis: delay floor on r2m3 (delay_floor)

Every number computed here from stored rows is EXPLORATORY (S6 rows, 240 paired seeds; median of paired differences; 95 % percentile bootstrap, 10,000 resamples, RNG 20261110). v3w = per-seed mean of its 5 learners. Units: vehicle-seconds (veh-s). No simulation ran.

## 0. Answer

- Under p333 demand is served. The delay is speed loss plus an intermittent breakdown at merge 2; there is no standing fluid queue.
- Estimated split of p333's delay in S: about 43 % remains even at 3,500-veh/h speeds, about 5 % is off the mainline, about 51 % is tied to density. The part tied to merge-2 slow minutes is about 15 % (S) and 18 % (TRUCK): my estimate of the ceiling for any controller acting at the merges.
- The memo's no-merge arm would measure the 3-lane speed-flow curve and the origin's insertion limit, so its KILL rule can fire for the wrong reason.
- Stored rows already test 1.0-1.2 s before and at the merges: all have more delay than p333. Nothing above 1.6 s was ever run.

## 1. Plant facts

- **Geometry** (corridor.py:45-48; row field `m_offsets`): edges 1 and 2, 0-3,498 m, 3 lanes; 3a to 3,793 m (4 lanes, 295-m accelerating lane); 3 to 4,987 m; 4a to 5,282 m (4 lanes); 4 and 5 to 6,778 m (3 lanes).
- **Limit and reference speed:** both 100 km/h (fleet.py:27, :294; plant_sweep.py:31).
- **Demand:** one Poisson stream from t = 0, routes drawn 70/15/15 (fleet.py:336; corridor.py:22, :55). At 5,300: main 3,710, each ramp 795 veh/h; sections carry 1,237 / 1,502 / 1,767 veh/h per lane. Random fixed departure lane, `departSpeed="max"` (fleet.py:365-366).
- **Fleet:** 50 % ALKS, 7.5 % trucks, 42.5 % human cars (plant_sweep.py:78; fleet.py:95). Speed factors: ALKS 1.0, cars N(0.98, 0.12), trucks N(0.878, 0.055) capped at 25 m/s (fleet.py:202, :43-44, :29).
- **Window:** 300 s warm-up, then 1,500 s (b_env.py:102, :152).
- **Delay:** `all_delay = N - dist_step / REF_SPEED` (plant_sweep.py:347); N adds, each second, running vehicles plus those waiting for insertion (b_env.py:427-429). Unfinished vehicles count to the window end, uninserted ones count 1 veh-s per second, and every class is held to 100 km/h, trucks included.

## 2. Decomposition (medians; share = p333's mean share in S)

| Component | S: nc | S: p333 | S: v3w | Share | S: p333 − v3w | TRUCK: p333 | TRUCK: p333 − v3w |
|---|---|---|---|---|---|---|---|
| Total | 200,589 | 126,296 | 127,465 | | −1,988 [−3,303, −693] | 161,493 | −402 [−1,260, +739] |
| Origin queue, main | 4,418 | 4,404 | 4,338 | 3.6 % | +13 [−14, +38] | 4,384 | +6 [−22, +34] |
| Ramp roads | 4,654 | 1,693 | 1,909 | 1.6 % | −106 [−142, −73] | 1,732 | −114 [−158, −81] |
| Upstream, 1+2 | 50,615 | 39,435 | 39,584 | 30.2 % | −95 [−180, +16] | 49,128 | −123 [−188, +13] |
| Merge 1 (3a) | 7,168 | 5,563 | 5,745 | 4.4 % | −128 [−206, −84] | 7,035 | −187 [−256, −40] |
| Between (3) | 40,579 | 17,981 | 18,315 | 14.2 % | −425 [−688, −248] | 25,336 | −455 [−643, −244] |
| Merge 2 (4a) | 34,445 | 14,048 | 16,028 | 14.0 % | −666 [−1,494, −78] | 22,183 | +381 [−267, +1,275] |
| Downstream, 4+5 | 55,257 | 40,593 | 40,001 | 31.4 % | −96 [−492, +217] | 49,409 | −150 [−446, +101] |

- Ramp origin queues and junctions hold under 1 %. Components sum to `all_delay` within 61 veh-s per run. TRUCK: no control 231,312, v3w 161,591.
- v3w is below p333 on no component with a CI clear of 0.
- **By time.** Per-minute series exist only for edges 2, 3a, 3, 4a. Their delay per 5-minute block: S p333 7,470 / 7,875 / 8,122 / 8,236 / 8,592 (only 4a grows); S no control 9,662 to 23,332; TRUCK p333 7,357 to 16,325. TRUCK, 4a, last block: p333 − v3w +916 [+492, +1,199].

## 3. Fluid check

- Planned in the window: median 2,210 (2,096-2,332).
- **p333, S:** passed (entering edge 4) 2,202; passed − planned median −8, mean −12.0; pending at the end 2; teleports 0. Merge-2 outflow by block: 5,216 / 5,283 / 5,287 / 5,296 / 5,300 veh/h.
- **No control, S:** passed 2,137 (−73). **TRUCK:** p333 2,181 (−31), no control 2,110 (−98).
- **Capacity estimate:** p333's saturated throughput in the V419 sweep rows is 2,296-2,339 per window at 5,750-6,250, i.e. 5,510-5,614 veh/h; S1 map at 7,000, 6 unperturbed seeds: p333 5,544, no control 5,342 veh/h.
- INFERENCE: demand is about 95-96 % of p333's capacity and about equal to no control's. Under p333 0.5 % is unserved. Merge 2 is metastable: 4a is below 60 km/h for a median 7 of 25 minutes (22 seeds never) and its mean speed falls from 67.8 to 50.1 km/h over the window. Merge 1: mean 0.5 slow minutes.

## 4. Lower references (estimates)

| Reference | Value | Share of p333's S delay left |
|---|---|---|
| Drawn desired speeds, harmonic mean 97.35 km/h (my computation) | 6.65 s per main vehicle | 9.5 % [9.2, 9.6] |
| 2,500 veh/h, p333 (V419 rows; 9 of 10 seeds with a slowdown) | 20.0 s per planned vehicle | 35 % (57.1 s at 5,300) |
| 3,500 veh/h, p333, 6 unperturbed S1-map seeds | 25.5 s (no control 30.3 s) | 45 % |
| The same seeds' per-edge speeds applied to the 5,300 distances | 54,234 veh-s | 43.1 % [41.6, 43.7]; TRUCK 33.5 % |

- With the last row, the mainline excess is 51.4 % [50.6, 52.2] of p333's delay in S (TRUCK 61.8 %); off-mainline 5.5 %.
- Excess by edge, S: edge 1 12.4 %, 2 1.2 %, 3a 2.2 %, 3 6.9 %, 4a 11.0 %, 4 13.7 %, 5 5.4 %.
- INFERENCE: edge 1's excess is not merge spill-back, since edge 2, nearer the merge, is faster (86.8 against 82.7 km/h). A merge controller reaches at most 3a to 5, about 39 %, and only if 1,767 veh/h per lane could run at speeds seen at 1,167.
- **Breakdown-conditioned.** Least squares over seeds, p333: `all_delay` = 111,285 + 174 × (planned − mean) + 2,341 × (minutes with 4a below 60 km/h), R² 0.85. The intercept is 85.4 % of the mean in S, 81.7 % in TRUCK. The 22 seeds with no slow minute have 50.0 s per planned vehicle. An association across seeds, not an intervention.
- Assumptions: 3,500-level speeds are attainable at 5,300 (optimistic); low-demand delay is itself headway-dependent (V419); the origin queue is out of reach (no control − p333: +52 [+20, +86]).

## 5. The no-merge reference (§5.1, arm 2)

Not a meaningful reference as drafted.

- **Origin limit.** It puts 1,767 veh/h per lane on the insertion point; the stored maximum is 1,237. The main insertion queue is already 4,404 veh-s there, equal in every arm. On the no-control ladder (V354 rows) the total insertion queue grows convexly: 272 / 700 / 1,278 / 4,080 veh-s at 3,500 / 4,090 / 4,600 / 5,300. INFERENCE: the origin becomes the bottleneck, and its queue counts in `all_delay`.
- **Density.** Edges 1-3 would rise from 1,237-1,502 to 1,767 veh/h per lane. At edge 5's current 76.4 km/h over 6.8 km, delay is 75.4 s per vehicle, above p333's 57.1 s; at edge 1's 82.7 km/h, 51.1 s. INFERENCE: an unmeasured speed-flow relation decides the result, so "KILL if not 5 % below p333" could kill M, P1 and P2 without measuring merge friction.

Better references:
1. **No-ramp arm:** same seeds, ramp vehicles dropped, main demand unchanged. The change in the main-route vehicles' delay is what the ramps cause. No controller can remove the ramp vehicles, so it is a ceiling and a safe basis for a KILL. It needs a per-route veh-s counter.
2. **Flow-matched ideal merge:** ramp vehicles inserted on the mainline lanes at 3a and 4a at speed; same flow per section, no forced lane change. Report its insertion queue.
3. **Long auxiliary lane:** `accel_len` moves only merge 1 (corridor.py:59-62); merge 2 has fixed nodes (corridor.py:47). Needs code.
4. **No runs:** the 15-18 % above.

Arm 3: a target headway binds only behind an ALKS within 150 m, otherwise 1.6 s (b_env.py:36, :779). The memo must say whether that gate stays; without it the arm is a new actuator.

## 6. Records on longer headways near a merge

- V274 (m32, every ALKS, 5,300; 1.2 / 1.0 / 0.8 s against 1.6 s): flow +8.1 / +9.9 / +12.2 %.
- V276 (V2V gate, 5,300): flow +3.9 / +6.0 / +7.9 %.
- V347: 1.2 s near a slowdown, delay −4.5 [−5.5, −3.0] %; "Fallback to 1.6 s costs too much delay (-8 to -15 %)".
- V349 (r1m3, 4,600, slowdown to 25 km/h): fixed 1.0 s −6.6 %, fixed 1.2 s −15.5 % delay against p333.
- V355 (r2m3, 32 zone patterns of 1.2 or 0.8 s): 5,300 p31333 delay +0.6 [−9.9, +5.4]; KILL for this form.
- S6 rows, arm minus p333, % of p333's median delay (S; TRUCK):
  - z33133, 1.2 s on the 800 m before merge 2: +4.14 [+2.60, +5.61]; +3.00 [+2.35, +4.08]. Delay on 4a itself +11.51 [+4.66, +20.70] in S.
  - grid_z31333, 1.2 s around merge 1: +2.11 [+1.00, +3.52]; +1.41 [+0.76, +2.10].
  - r4a1, 1.2 s on 4a: +7.51 [+4.74, +9.24]; +3.91 [+3.12, +4.97].
  - grid_r4a2, 1.0 s on 4a: +3.75 [+2.56, +5.57]; +2.30 [+1.22, +3.12].
- **Above 1.6 s: no record found.** `HEADWAYS_S = (1.6, 1.2, 1.0, 0.8)` (b_env.py:37). A ledger search for 1.8-4.0 s beside "tau" or "headway" returns only V158 (an older ACC class at 2.2 s, not a test). No lane-0-only or per-merging-vehicle gap rule was found.

## Files

- Scripts and outputs: `/tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/89ba3663-8e1a-45c3-9415-9e2a743fb16b/scratchpad/phaseB/floor/` (`decomp.py`, `lowref.py`, `floor.py`, `extra.py`, `longhw.py`, each with `*_out.txt`).
- Low-demand inputs: `/home/catalin/work/phd/v5b1_runs/measure_s01_remote/rows_s1.jsonl` and `st/`; `/home/catalin/work/phd/v5b1_runs/round1_sweep/out/sweep1.jsonl`; `/srv/shared/Workspace/phd/phd_speed_harmo_v5b1/docs/research/r2m3/ladder_rows.jsonl.gz`.
- Not found: S6 space-time side files, so no per-minute delay for edges 1, 4, 5.
