# T1 R5 head-to-head: r5_bf_av25

*2026-10-02 13:46 · protocol `docs/lab/t1_bn4_r5_protocol.md` · test seeds 7110560-7110589 · raw `/home/catalin/work/phd/vsl_lab_runs/t1/r5_bf_av25_1790973716`*

Median of paired differences in door-to-door time (DRL − comparator, s; negative = DRL better) [95 % CI].

## q = 1200 veh/h

| comparator | drl0 | drl1 | drl2 | drl_pooled |
|---|---|---|---|---|
| nc | +2.5 [+1.5, +2.9] (+4.4%) | +2.6 [+2.4, +2.8] (+4.6%) | +2.0 [+1.6, +2.1] (+3.5%) | +2.5 [+1.6, +2.7] (+4.4%) |
| cap:18 | +0.6 [+0.4, +0.8] (+1.1%) | +0.8 [+0.5, +1.1] (+1.4%) | -0.1 [-0.3, +0.2] (-0.2%) | +0.5 [+0.3, +0.7] (+0.9%) |
| avfb:2:10 | +2.4 [-0.5, +2.8] (+4.2%) | +2.5 [+1.5, +2.8] (+4.4%) | +1.8 [+0.2, +2.1] (+3.1%) | +2.4 [-0.9, +2.6] (+4.2%) |
| meter:10:6 | -17.4 [-19.1, -16.6] (-22.2%) | -17.1 [-18.8, -15.7] (-21.8%) | -18.5 [-19.6, -17.5] (-23.6%) | -17.5 [-18.9, -16.1] (-22.3%) |

## q = 1600 veh/h

| comparator | drl0 | drl1 | drl2 | drl_pooled |
|---|---|---|---|---|
| nc | -6.5 [-64.6, -2.3] (-2.4%) | -12.6 [-43.9, +1.7] (-4.6%) | -2.8 [-5.9, -0.4] (-1.0%) | -6.3 [-29.1, -1.0] (-2.3%) |
| cap:18 | -1.1 [-7.2, +1.0] (-0.5%) | -2.4 [-17.9, +2.5] (-1.0%) | -0.2 [-2.9, +3.0] (-0.1%) | -1.0 [-7.6, +1.0] (-0.4%) |
| avfb:2:10 | -225.2 [-279.4, -131.6] (-54.7%) | -216.1 [-263.2, -126.9] (-52.5%) | -169.6 [-229.4, -125.7] (-41.2%) | -199.9 [-257.1, -125.1] (-48.6%) |
| meter:10:6 | +65.8 [+7.2, +93.8] (+51.3%) | +65.1 [-28.3, +115.2] (+50.8%) | +92.2 [+44.6, +140.7] (+71.9%) | +69.1 [+6.8, +101.0] (+53.9%) |

## q = 2000 veh/h

| comparator | drl0 | drl1 | drl2 | drl_pooled |
|---|---|---|---|---|
| nc | -1.8 [-22.6, +0.3] (-0.3%) | -3.1 [-13.8, +0.5] (-0.6%) | -0.6 [-11.7, +0.1] (-0.1%) | -2.3 [-15.9, +0.0] (-0.4%) |
| cap:18 | -6.2 [-12.6, -2.8] (-1.2%) | -2.5 [-10.0, +0.2] (-0.5%) | -0.7 [-7.9, +0.2] (-0.1%) | -3.6 [-7.9, -0.3] (-0.7%) |
| avfb:2:10 | -341.7 [-369.6, -266.0] (-41.8%) | -298.7 [-342.1, -258.0] (-36.5%) | -311.5 [-344.4, -259.6] (-38.1%) | -312.3 [-345.3, -258.5] (-38.2%) |
| meter:10:6 | +184.5 [+115.0, +237.4] (+56.5%) | +196.0 [+136.9, +237.2] (+60.0%) | +208.9 [+126.3, +253.4] (+63.9%) | +195.6 [+128.5, +245.0] (+59.9%) |

## q = 2400 veh/h

| comparator | drl0 | drl1 | drl2 | drl_pooled |
|---|---|---|---|---|
| nc | -1.8 [-11.6, +2.0] (-0.2%) | -4.7 [-10.1, +0.0] (-0.6%) | -1.4 [-3.6, +0.1] (-0.2%) | -1.8 [-5.3, +0.0] (-0.2%) |
| cap:18 | -1.7 [-4.8, -0.7] (-0.2%) | -1.2 [-9.1, +0.5] (-0.2%) | -0.3 [-2.1, +1.1] (-0.0%) | -1.0 [-1.7, -0.0] (-0.1%) |
| avfb:2:10 | -366.2 [-385.0, -336.4] (-31.9%) | -367.4 [-401.1, -335.5] (-32.0%) | -364.2 [-382.2, -329.6] (-31.8%) | -367.4 [-385.0, -332.7] (-32.0%) |
| meter:10:6 | +306.9 [+258.5, +354.8] (+68.6%) | +315.9 [+246.6, +365.0] (+70.6%) | +320.2 [+248.0, +361.2] (+71.6%) | +315.9 [+248.8, +359.5] (+70.6%) |

## Health

{"drl0": {"PASS": 105, "WARN": 15, "FAIL": 0}, "drl1": {"PASS": 102, "WARN": 18, "FAIL": 0}, "avfb_2_10": {"PASS": 78, "WARN": 42, "FAIL": 0}, "nc": {"PASS": 107, "WARN": 13, "FAIL": 0}, "meter_10_6": {"PASS": 0, "WARN": 120, "FAIL": 0}, "cap_18": {"PASS": 107, "WARN": 13, "FAIL": 0}, "drl2": {"PASS": 109, "WARN": 11, "FAIL": 0}}

## Reading (rule of `t1_bn4_r5_protocol.md`, applied unchanged)

**Rule:** a "beat" needs the pooled median paired difference < 0 with the CI excluding 0, **and** the same in ≥ 2 of 3 learner seeds.

**Against `cap:18`** (the tuned constant cap at 25 % AVs): **beaten in 0 of 3 congested cells.**
- q = 1,600: the pooled CI includes 0.
- q = 2,000 and q = 2,400: the pooled CI excludes 0, but only 1 of 3 learner seeds does (drl0).

Against the other comparators:
- **`avfb:2:10`:** beaten in all 3 congested cells. It is a weak comparator.
- **NC:** beaten only at q = 1,600 (pooled −2.3 %).
- **At q = 1,200:** DRL is worse than NC (+4.4 %, CI excluding 0). It stays within the "no significant harm" bound vs `cap:18` (+0.9 %).

**Verdict:** **"DRL beats tuned classical control on the same actuator": NO** (it fails against `cap:18`).
- Against the meter, DRL is 50–72 % worse in the congested cells.
- All effects against NC and against `cap:18` are below about 2.5 %.
- B-P6's screening pass (best checkpoint) was again a false positive, as P1c was at 10 % AVs.
