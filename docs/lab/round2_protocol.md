# Round 2 (author choice 2026-10-02: all four options): protocol

*Committed before any Round 2 run. Branch `claude/vsl-lab-core`. Rules as in roadmap §0 and `CLAUDE.md`. Every run goes into the ledger.*

## C. DRL scheduling the tuned meter: **KILLED by the hybrid gate, using existing data (no runs)**

**G from R2 v2** (tuning seeds 7,110,100–7,110,119; door-to-door median per cell):

| Choice | q = 1,200 | q = 1,600 | q = 2,000 | q = 2,400 |
|---|---|---|---|---|
| Pooled tuned meter (`meter:10:6`) | 78.6 | 128.3 | 270.0 | 422.2 |
| Per-cell best of {off, meter grid} | 57.5 (`nc`) | 112.9 (`meter:20:6`) | 270.0 | 422.2 |

So **G = 4.1 % < 10 %**. G is biased upwards (selected on the same seeds), and the condition (inflow) is observable by an upstream detector, so a non-learning adaptive rule would capture most of it. **Conservative KILL** (`CLAUDE.md` T2 rule). The `madapt` and `msfix` controllers stay implemented, for reporting only.

## A. TM20 posted VSL on the bottleneck (BN4-VSL): thesis core

**Plant.** BN4 exactly as in R1 v4: NC is unchanged, so the capacity drop (1,044 → 900 veh/h, ratio 0.86) and the meter's authority (+45 %) are already measured.

**Actuator: posted VSL for ALL vehicles.**
- Gantries on edge 2 (application area) and edge 3 (acceleration area); b ∈ [0.2, 1] × 23 m/s.
- |Δb| ≤ 0.2 per decision; decisions every 10 s.
- Drivers' desired speed = speedFactor × limit, with human speedFactor ~ normc(1, 0.2). Partial compliance is therefore built in.
- H-R7 asserts the posted limits.

**Classical controllers:**
- constant `vsl:b2:b3`;
- `mtfcb`: Carlson MTFC on BN4, with ρ_out = vehicles on edge 4 / (0.24 km × 2 lanes) and q_c from the edge-3 end loops; period 20 s; b_acc 0.9 while active;
- the tuned meter `meter:10:6` as the cross-actuator reference.

| Step | Seeds | Content | Criterion / rule |
|---|---|---|---|
| **A-T0** (posted VSL binds) | 7,110,050–7,110,059 | q ∈ {1,600, 2,000}; `nc` vs `vsl:0.4:0.9`; outflow over the control window | PASS if \|Δ\| ≥ 5 % with the CI excluding 0 |
| **A-R2** (tuning) | 7,110,120–7,110,139 | q ∈ {1,200, 1,600, 2,000, 2,400}: `nc`; `vsl:{0.3, 0.4, 0.5, 0.6, 0.8}:0.9`; `mtfcb` ρ̂ ∈ {20, 30, 40, 50, 60, 70} × gains {paper (38, 9, 0.0015), double (76, 18, 0.003)}; `meter:10:6` (reference) | as BN4 R2: score = mean over cells of the median door-to-door time. Frozen in `docs/lab/t1_bn4vsl_baselines_frozen.json` |
| **A-P5** (DRL pilots) | validation q ∈ {1,600, 2,000, 2,400} × seeds 7,110,310–7,110,312 | **P5a:** PPO, `nocap_center`, log_std −0.5, R-OUT, 8 envs × 180 steps, batch 360, 600 updates, γ 0.99. **P5b:** P5a with R-TTS. | screening criteria as for P1 (C1, C2 vs the best constant VSL, C3 ≥ NC + 5 %) |
| **A-F/R5** | R5 on test seeds 7,110,530–7,110,559 | passers go to F class (3 seeds × 1,000 updates); R5 against `nc`, best `vsl`, tuned `mtfcb`, `meter:10:6` | **"DRL beats tuned rule-based control on the posted-VSL actuator"** needs: beating tuned `mtfcb` and the best `vsl` in ≥ 2 of 3 congested cells (median paired difference < 0, CI excluding 0, pooled and in ≥ 2 of 3 learner seeds), and no significant harm at q = 1,200 |

## B. 25 % AVs on the bottleneck (BN4-AV25)

The av_share is 0.25 for **every** controller (NC included).

| Step | Seeds | Content | Rule |
|---|---|---|---|
| **B-R2** | 7,110,140–7,110,159; same 4 cells | `nc`, `cap:{9, 13, 18}`, `avfb` (the 12-setting grid), `meter:10:6` (reference) | same selection rule as BN4 R2 |
| **B-P6** (pilot) | same validation seeds as A | the F2 configuration (stable, 4× batch, learning-rate decay) at av_share 0.25, 600 updates, 1 seed | screening as P1 |
| **B-F/R5** | R5 test seeds 7,110,560–7,110,589 | passers go to F class and R5 against the B-R2 tuned baselines at 25 % | the same-actuator reading as T1 R5 |

## D. Repair the merge plant (MRG3-v2)

**D-1 diagnosis** (throw-away seed 7,120,050, already used by the v2 calibration; disclosed):
- one NC run at 5,400 / 900, logging the teleport reasons and the vehicles stuck at the acceleration-lane end;
- no criteria, because this is a diagnosis.

**D-2 repair** (pre-registered as an addendum *after* D-1 and before any repaired run):
- choose **one** literature-plausible fix (LC2013 assertiveness / cooperation, or a longer acceleration lane);
- recalibrate on fresh throw-away seeds 7,120,100–7,120,109;
- then run R1 on 7,120,110–7,120,149 with the v1 criteria.

**Seed note.** These ranges overlap the old T2 R2 tuning range 7,120,100–7,120,299, which **was never run** because T2 R1 failed. They are re-assigned here before any use, and the reassignment is disclosed.

## Order

1. A-T0
2. A-R2
3. B-R2
4. D-1 (single run)
5. A-P5
6. B-P6
7. F-class for passers
8. R5

One batch at a time. Thermal guard per `CLAUDE.md`.

---

## D-1 result and D-2 pre-registration (2026-10-02, before any v3 run)

**D-1 diagnosis** (seed 7,120,050, NC, 5,400 / 900; `docs/lab/t2_mrg3v2_diag.json`). It is **not** a ramp deadlock: 1 teleport, at most 3 vehicles stopped at the acceleration-lane end. It is an **insertion failure**: the origin queue grows to 1,955 vehicles. With IDM (b = 1.5 m/s²), SUMO's insertion check at `departSpeed="max"` (33 m/s) needs very large gaps, so the mainline never receives its demand. The merge lanes 0–1 do congest locally.

**Insertion test** (same throw-away seed; pending vehicles at 1,500 s):

| `departSpeed` | Pending at 1,500 s |
|---|---|
| `max` | 440 |
| `desired` | 380 |
| `random` | 444 |
| `0` | 546 |
| **`avg`** | **0** (all 1,716 due vehicles inserted; up0b congested at 11 m/s) |

**D-2: MRG3-v3 = MRG3-v2 (IDM) + `departSpeed="avg"` on both routes.**
- This changes only how demand enters, not the vehicle dynamics or the geometry.
- **v3 calibration:** throw-away seeds 7,120,100–7,120,109; the same grid and cell-selection rule as v1.
- **v3 R1:**
  - T1 and T1c on 7,120,110–7,120,139; T0 on 7,120,140–7,120,149; 5 T3 re-runs;
  - the v1 criteria;
  - T1c gets one MTFC set-point grid adapted to IDM densities: ρ̂ ∈ {20, 25, 32} with the paper gains, plus const 0.6 / 0.8.
- **v3 R2** (only if T1 and T0 pass): tuning seeds 7,120,150–7,120,169, with the R2 protocol grid and compliance classes.
- Seeds 7,120,100–7,120,169 were never used before; their reassignment from the unused T2 R2 range is disclosed.

---

## A-track stop after A-T0 / A-R2 (2026-10-02, logged before any A-P5 run)

**A-T0 FAILED.** Posted VSL does not bind on BN4: the outflow changes by −0.8 % and +3.5 %, and both CIs include 0 (`round2_a_t0.md`).

**A-R2 confirms it** (`round2_a_r2.md`). Every posted-VSL and MTFC setting scores 427–430 s, against 430 s for NC. The tuned meter scores 270 s.

**Why the actuator cannot work here.** BN4's 4 → 2 → 1 zipper is a lane-drop bottleneck. Four lanes, even at very low speed limits, still feed more than the bottleneck can discharge.

**A-P5 (DRL on posted VSL) is therefore not run.** A policy limited to an actuator that does not bind cannot beat NC through that actuator. The decision follows the A-T0 gate's logic, but was taken after seeing A-R2, and is disclosed as such. Posted VSL stays the thesis core on the **merge** plant (Track 2), where T0 is checked separately.

**MRG3-v3 R2 gate (2026-10-02, before the v3 R1 runs).** R2 needs all of the following:
1. R1 T0 PASS;
2. R1 T1's share, teleport and FAIL parts;
3. an H0 PASS in the plant-realism gate (`t2_realism_protocol.md`, Addendum A). Its R-a replaces T1's confounded max-based ratio.
