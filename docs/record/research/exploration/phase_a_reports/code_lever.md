# code_lever: what the code lets the learner do

Paths: `B/` = `/home/catalin/work/phd/wt/planb_v23/v5b/fleet/`, `P/` = `/home/catalin/work/phd/wt/planb_v23/docs/research/planb/`, `R/` = `/home/catalin/work/phd/wt/planb_v23/docs/research/`. v3w config read from `/home/catalin/work/phd/v5b1_runs/baseline_v5/policies_v3w/C0_config.json` (C0 only; C1-C4 not opened). Nothing was run; every statement comes from reading code and records.

## (a) Interface

- **Controlled:** every ALKS, ramp-origin included (`alks_all`, B/b_env.py:400, :909), anywhere on the network. No control zone.
- **Action:** absolute level in 1.6/1.2/1.0/0.8 s (b_env.py:37). The only SUMO call is `ls.vehicle.setTau` (b_env.py:784). No speed, lane or acceleration command from the learner.
- **Gate:** the target applies only behind an ALKS leader within 150 m seen on two successive 1-s updates; otherwise 1.6 s (b_env.py:36, :774-779). A V2V outage forces 1.6 s (:776).
- **Rate limits:** one level per `hold` (b_env.py:704-711); a new vehicle starts at 1.6 s (:703); increases are capped at `tau_rise` 0.2 s per second (:781-782).
- **Timing:** env step 5 s (B/c_train.py:25), each vehicle asked on its own clock every hold = 10 s (b_env.py:942-945; config `hold: 10.0`). Episode 300 s warm-up + 1,500 s (b_env.py:102, :152); evaluation uses the same default (B/plant_sweep.py:78).
- **Plant behaviour in every arm, not an action:** the no-undertake speed cap via `setMaxSpeed` (b_env.py:350-391).
- **16 inputs (b_env.py:925-935):** 0 x/1000 from the 3a start; 1 x/300 clipped ±1; 2 on-ramp flag; 3 lane index; 4 own speed; 5 leader gap (≤ 100 m); 6 closing speed to leader; 7 leader is ALKS; 8 follower gap (≤ 100 m); 9 follower closing speed; 10 own level; 11 hold left; 12 own 200-m bin mean speed; 13 merge-zone mean speed; 14 distance to nearest accelerating-lane vehicle (±100 m); 15 vehicles on 3a_0 + 4a_0 (/40).
  - Input 13 covers merge 1 only: `_zone` puts 4a in ZONE_DOWN (b_env.py:499-509).
  - Critic adds 10 global values (b_env.py:946-949).

## (b) Reward as coded (v3w: `reward_mode` v3, `w_safety` 10, `w_flow` 0.4)

Per vehicle per decision = shared + own, averaged over the interval (b_env.py:967; c_train.py:220-224).

- **Own, per second (b_env.py:842-843):** 0.5 (v/limit − 1) + 0.5 (bin v/limit − 1) + 0.4 min((v/spacing)/0.6, 1.5) − 10 (ttc + hard + 0.5 (follower ttc + follower hard)); − 0.01 per level move (:715).
- **TTC below 3 s is in it:** `gap/dv < 3.0`, read once per second (b_env.py:31, :811-812), for the vehicle and, at half weight, its direct follower.
- **Shared (b_env.py:554):** smoothed flow/demand − 1 + mean speed/limit − 1 − (vehicles in system incl. insertion queue / no-control reference − 1), minus 10 per collision (:446). Identical for every vehicle of the env.
- **Delay:** door-to-door delay is not a term. It enters as the unattributed shared count (global) and as own and bin speed (local). `attr` (attributed delay, :845) and `lagr` (delay as a cost, :847-848, :859-861) exist; V449 records attr did not qualify, V448 lagr out at the λ cap.
- The code comment says the flow term "makes short headways pay outside the merge zone" (b_env.py:62).

## (c) Network and training

- Actor MLP 16-64-64-4 tanh; critic 26-64-64-1; no recurrence (c_train.py:41-42, :72-73). Evaluation is greedy argmax (:133).
- PPO: 10 epochs, minibatch 4,096, lr 3e-4, clip 0.2, entropy 0.01, value 0.5, gradient 0.5 (c_train.py:30-31); Adam eps 1e-5 (:408); advantages normalised per minibatch (:302); critic scale fixed from the first returns (:432-433); inputs by running mean/SD, clip 5 (:85).
- v3w config: gamma 0.933, lambda 0.967 (code default 0.8/0.9, :29), 500 updates, 3 envs, one episode per env per update (:227-228). 5 learners (R/protocols/round_1.md:20).
- **Randomisation:** 7 demand levels 4,500-6,000 cycling, constant within an episode (b_env.py:142, :153); share fixed 0.5 (c_train.py:398); `perturb random`: one third none, else one tapered slowdown on edge 3, 4 or 5, limit U(25, 60) km/h, duration U(60, 180) s, start U(400, 1,200) s (B/perturb.py:67-71).
- Plan B ran the stored v3w checkpoints (P/pb.py:131; P/run6.py:6). INFERENCE: SURGE and TRUCK lie outside the training draw.

## (d) What the plant can do that the learner does not use

| Capability | Code | Tested / result | To expose |
|---|---|---|---|
| Lane change | `lane_action`, `changeLane(v, j, hold)` b_env.py:744-758; 2 extra inputs :760-766 | sizes test tests/test_fleet_b_env.py:206; V317 (m32): "fails as built", policies' collisions 30 and 68 in 10 runs | a safe design first |
| Per-CAV speed cap | `SPEED_CAPS` none/90/80 km/h b_env.py:77, :738-742, via the smooth cap :361 | V339 (r1m3 P0, 5,300): p333 with 90/80 km/h delay 111.6/133.4 s against p333 92.8 s; policies "no speed cap 88-95 % of the time" | flag exists |
| Ramp meter | `Meter`, `SumoMeter` B/control.py:72, :282; ALINEA in plant_sweep.py:306-309 | 32 tests (tests/test_fleet_control.py); V333: "ALINEA gains nothing" on r1m3 | r2m3 has a signal only at `rm`, ramp 2's node is priority (B/corridor.py:72-73); reset sets all green (b_env.py:167) |
| Per-lane limits for HDVs | none found as a controller; only the plant limit (b_env.py:168-170) and the edge-wide slowdown (perturb.py:179) | not built | build a VSL actuator and its taper (V345 issue noted at perturb.py:11-12) |
| Gap creation | central cap on mainline ALKS nearest merge 1, `MergeEnv._apply` b_env.py:245-266; `CourtesyGap` with `openGap` B/merge.py:18-56 | merge.py:1 docstring: courtesy gap "(V194, failed)"; used in day.py:282 only; the central cap is "not used since run 3" (baseline_v0/BASELINE.md, Controllers table) | port to r2m3, both merges |
| CACC | class `cacc` → SUMO CACC (B/fleet.py:66) | B mode has "no ACC/CACC" (fleet.py:92-94); ALKS use SUMO ACC | new fleet mix |
| V2V content | leader identity only (b_env.py:774-776); roadside 200-m bin speeds, ideal (:829-834) | outage kind exists | new messages |
| Hybrids | residual on a rule `base_rule` b_env.py:680-688; `ZoneSwitch`, `TailMean` c_train.py:137-173 | V449: res did not qualify | present |

**Verification record:** the CAV contract forbids `changeLane`, `openGap` and `setSpeed` (b_env.py:4-5; V309 records the lane action as a departure). INFERENCE: any of these as an action means new T0 (binds), T3 (determinism) and a smoke check, and for metering or VSL also T1/T2 on r2m3; the frozen plant_c3 record was built with `setTau` as the only commanded actuator (I did not open `verification_rev4.md`).

## (e) Opponents

- **Fixed and grid rules:** `CavRule` level per 3 zones (b_env.py:970-988); `ZonePattern` 5 zones (:1029); `RoadLevels` per road (:1091); `OwnState` level, speed threshold, x_min, crowd (:1078-1088); `LocalRule` r, th, level (:991-1026); `AdaptiveOn4a` (:1060).
- **CMA-ES rule = `ZoneOwnState` (b_env.py:1117-1129):** per zone of 5 fixed zones, `level` if own speed < `th` and accelerating-lane count ≥ `crowd`, else `free`. 20 parameters; th 0-25 m/s, crowd 0-30 (R/round2/cma2.py:37-41). Population 24, 16 seeds per generation, 100 generations (P/cmab.py:44); objectives close-following or delay against p333 (cmab.py:48, :115-130).
- **KEY ANSWER:** the CMA-ES rule reads observation columns 0, 2, 4 and 15 only, and returns the same absolute level through the same `_apply`. Same action, a 4-input subset of the actor's 16.
  - The actor can represent what the rule cannot: dependence on leader/follower gap and closing speed, leader type, lane, bin speed, merge-zone speed, nearest merging vehicle, and position as a continuous variable.
  - The reverse, for the CMA-ES rule: nothing in the function class. One timing difference: rules answer for every vehicle at every 5-s step (b_env.py:1088; plant_sweep.py:312), the policy only for vehicles due on their 10-s clock (c_train.py:130-134). INFERENCE: a rule can react up to 5 s sooner.
  - Other opponents read what the actor does not see: `LocalRule` the bin speeds up to r m ahead (:1005-1019; r 400 or 1,000 in opponents.json); ASCH and MPC-F below.
- **ASCH (B/planb_ctrl.py:48-78):** two whole rules switched corridor-wide; to the disturbed rule when any of 3 zone speeds stays below theta for tau s, back with hysteresis. It has memory. Grid theta 40/55/70 km/h, tau 10/30/60 s, h 5/15 km/h (P/asch.py:22).
- **MPC-F (planb_ctrl.py:115-182):** every 30 s a 2×64 MLP predicts the 300-s cost (delay + 10 × close-following vehicle-seconds, :82-90) of holding each member rule, from 10 roadside features (zone speeds, zone counts, both accelerating-lane counts, ramp queues, :93-99); applies the cheapest. INFERENCE: a fitted cost regression over whole rules, not a rollout model.

## (f) Disturbances

- Cells (R/conf3/common.py:13-20): X1 edge 4 to 25 km/h, 120 s, at 600 and 1,200 s; X2 edge 3 to 30 km/h, 180 s, at 700 s; both taper 20 s. H1 periodic truck 50 km/h every 300 s. H2 ramp bursts, 120-s cycle. SURGE 5,300 → 6,000 → 4,600 veh/h in 600-s segments. TRUCK 10 lane-0 trucks capped at 40 km/h, 80 s apart from 360 s.
- Other kinds: `brake` (perturb.py:135-160), `outage` of V2V (:186-190), oracles (:118-127), hidden driver types `hw_type` (b_env.py:717-731; V353 "no value").
- **Not wired into b_env:** weather (fleet.py:81 states; set only in B/day.py:509; calibrated on ld32), incident passing zone (B/incident.py:33; day plant), detector faults (`v5b/d1/faults.py`; fleet.py:12 "Not modelled yet"). Roadside bins are ground truth.

## (g) INFERENCE: the three interface limits most likely to cap the learner

1. **The lever is one-sided and gated.** The action only matters behind an ALKS leader, and 0.8 s is the floor. Against p333 a policy can only lengthen headways somewhere, which trades delay for close-following. That fits H1 and H3 and explains a delay tie by construction.
2. **The actor sees less of the road than its opponents.** No memory, 100 m to the leader, its own 200-m bin, merge 1 only. LocalRule, ASCH and MPC-F read downstream or corridor state; the CMA-ES rule already uses the actor's own inputs. So the unused 12 inputs must carry the whole advantage (H4).
3. **Delay has no attributed signal.** It reaches a vehicle through a term shared by all vehicles and through local speed; the close-following term is local, dense and weighted 10. The gradient favours the metric where the edge was found (H2).

Not found or not checked: the round 2 `ahead` result (two look-ahead inputs, R/protocols/round_2_prereg.md:82); whether C1-C4 configs equal C0's.
