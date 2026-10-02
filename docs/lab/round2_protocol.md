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

## D-2 result: MRG3-v3 calibration (2026-10-02 09:18)

**No eligible cell.** Every grid cell (4,800–6,000 / 600–900) had teleports (4–8 per 10 runs) and health FAILs (`t2_mrg3_calibration_v3.json`). Breakdown occurred at every cell (share 0.8–1.0).

**Cause.** All 58 teleports in the 100 runs are **on-ramp vehicles stuck at the end of the acceleration lane** (`merge_0`, "waited too long (wrong lane)", > 300 s). With IDM and the default LC2013 lane-change model, ramp drivers neither find a gap nor force one.
- The `departSpeed="avg"` insertion fix did not cause this. It exposed it, because the plant now receives its full demand.
- D-1 (v2) had already shown up to 3 vehicles stopped at the acceleration-lane end.

**Consequences:**
- R1, D-check and R2 for v3 did not run.
- The chain scripts crashed on the missing cell instead of skipping. This was fixed after the crash: `t2_r1_checks` and `t2_r2_baselines` now print a skip JSON and write a ledger row.

**Next.** The realism gate (running) reports this per driver variant through R-c. A lane-change / merge repair would be a new plant variant, pre-registered as D-3 after the gate. Raising `time-to-teleport` would only hide the artefact, so it is excluded.

## D-3: merge repair (author decision 2026-10-02), pre-registered before any D-3 run

**Why.** The 0.2 s realism re-check failed every variant (`t2_realism_step0.2.md`):
- IDM strands ramp vehicles at the acceleration-lane end, which causes teleports;
- W99 and EIDM merge without any capacity drop.

The capacity drop at merges is attributed in the literature to merging and lane-changing behaviour [VERIFY: e.g. Laval & Daganzo 2006; Leclercq, Laval & Chiabaut 2011]. SUMO's default gap acceptance is the documented gap.

**Repair: LC2013 `lcAssertive`.** SUMO's vType docs say: "willingness to accept lower front and rear gaps on the target lane. The required gap is divided by this value"; the default is 1. `lcImpatience` exists only in SL2015, so it is not used.

**Variants** (values ad hoc; the milder value is preferred):

| ID | Base driver model | `lcAssertive` |
|---|---|---|
| **H5a** | EIDM, SUMO defaults (H5) | 1.5 |
| **H5b** | EIDM, SUMO defaults (H5) | 3.0 |
| **H3a** | W99 (H3) | 1.5 |
| **H3b** | W99 (H3) | 3.0 |

The setting applies to every human vType.

**Seeds** (block 7,160,000–7,160,999, approved by the author on 2026-10-02):
- calibration: 7,160,000–7,160,009 (throw-away);
- checks: 7,160,100–7,160,119;
- determinism re-run: 7,160,100.

**Gate.** The same realism gate as before (`t2_realism_protocol.md`, with Addenda A and B), at a 0.2 s step:
- **smoke first:** the 4 variants on throw-away seed 7,120,050 at 5,400 / 900. A variant whose hash equals its base's 0.2 s smoke hash is INERT and dropped. A run that is not drained means COLLAPSED, and the variant is dropped.
- **outputs:** `t2_realism_verdict_d3.json` and `t2_realism_d3.md`.

**Primary plant for Round 3** = the first PASS in the order H5a, H5b, H3a, H3b. Round 3 then runs at 0.2 s on that variant.

**If all four fail:** build a lane-drop plant. It gets its own pre-registration, and its seeds come from the same block.

## D-3 result and D-4: lane-drop plant (pre-registered 2026-10-02, before any D-4 gate run)

**D-3 result** (`t2_realism_d3.md`): all four variants FAIL.
- Assertive merging (`lcAssertive` 1.5 or 3.0) did **not** create a capacity drop. H5b: Q_dis/Q_ff = 1.011 [1.000, 1.027].
- It moved breakdown onsets to the **network entry** (`up3`), so the share of runs whose congestion starts at the bottleneck fell to 0–0.54. That is the "waves from nowhere" artefact, and R-d caught it.
- Merge plant: closed, as pre-registered. Next: the lane-drop fallback.

**D-4 plant LD3** (`netgen/mrg3.py` `LD_SPEC`, `--geom lanedrop`):
- the same 4 km three-lane approach, VSL areas and probes as MRG3;
- the `merge` edge becomes a 263 m three-lane zone whose lane 0 ends (a **3 → 2 lane drop**), followed by a two-lane `down` edge;
- no ramp demand. The ramp edge is kept unused, so detector IDs stay valid.

**Lane-drop smoke** (throw-away seed 7,120,050, 0.2 s, main 3,900 and 4,500, a code check only):
- H0 (IDM): stranded vehicles at the end of the dropping lane, with teleports at both demands;
- H5 (EIDM defaults) and H3 (W99): clean, with no teleports.

**Gate:** the realism gate as amended (Addenda A and B), at 0.2 s, with these changes for the main-only geometry:
- **variants:** H5, H3 and H0 (H0 for the record);
- **grid:** main peak ∈ {3,300, 3,600, 3,900, 4,200, 4,500, 4,800, 5,100}, ramp 0, 10 seeds each;
- **stress cell:** 5,100 / 0;
- **seeds:** calibration 7,160,010–7,160,019 (throw-away); checks 7,160,120–7,160,139; determinism re-run 7,160,120;
- **primary plant** = the first PASS in the order H5, H3, H0;
- **outputs:** `t2_realism_verdict_ld3.json` and `t2_realism_ld3.md`.

**Then Round 3 runs on the primary LD3 variant**, with its seeds, X rule and criteria unchanged. Its T0 stage additionally runs **arm A** (posted VSL `const:0.4`, no CAVs) against NC-human on seeds 7,150,010–7,150,019, with the same rule (≤ −10 % application-area outflow, CI excluding 0). All three arms are therefore tested for authority on the same plant.
