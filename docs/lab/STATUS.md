# DRL lab: status (living document)

*Last update 2026-10-02 13:50 · branch `claude/vsl-lab-core` · every run is in `vsl_lab/runs/ledger.csv` · roadmap `docs/plans/vsl_drl_run_roadmap_v0.md`*

## Bottom line so far (honest)

**No DRL controller has yet beaten a tuned classical controller.** Everything below is exploratory.

**The most promising thread is Round 4: harmonisation on a lane drop.**
- A tuned **constant posted VSL (90 km/h)** cuts both delay (−25 %) and stops (−55 %) in heavy congestion.
- SPECIALIST, MTFC and an adaptive rule all do worse.
- DRL pilot **P-H2** is training to beat it (J = delay + 40 s per stop; it must reach ≥ 5 % better J and stay within 2 % on each measure).

## Tracks

| Track | State | Key result |
|---|---|---|
| **T1 BN4 bottleneck, 10 % AVs** | done | DRL ≈ NC on test seeds (F1, F2). The infrastructure meter gives −45 %. |
| **T1-A posted VSL on BN4** | stopped | Does not bind (A-T0 FAIL); A-R2 = NC. |
| **T1-B 25 % AVs** | **B-F running** | B-R2: no classical AV controller beats NC by more than about 1.5 %. B-P6 passed screening only on its best checkpoint (final = NC + 0.5 %). F class (3 × 1,000 updates) then R5 on 7,110,560–7,110,589. |
| **T1-C DRL meter scheduling** | killed | G = 4.1 % < 10 % |
| **T3 ring** | done | PI-with-saturation is at the ceiling (H ≈ 0). |
| **T2 merge (MRG3)** | **closed by the realism gate** | See below. |
| **Round 3 TM21 vs TM20 (CAVs)** | parked | SUMO's default CACC at 0.5 s brakes hard; at 0.2 s and 25 %, CACC alone worsens delay by 46–93 %. CAV arms showed no authority (T-H). |
| **Round 4 harmonisation (LD3 lane drop, EIDM defaults, 0.2 s)** | **P-H2 training** | T-H0 PASS (posted VSL has authority over stops). R2-H tuned classical = `const:0.75` (J 287 vs NC 381). |

## Plant-realism gate: what SUMO can and cannot do here

**Checks:**
- **R-a:** capacity drop of 3–18 % (Chung et al. 2007, verified: 3–18 % across three bottlenecks);
- **R-b:** wave speed between −25 and −10 km/h;
- **R-c:** no artefacts, plausible discharge;
- **R-d:** congestion starts at the bottleneck.

**Results:**
- **Realistic everywhere:** waves travel at −14 to −19 km/h and start at the bottleneck (R-b, R-d), for IDM, EIDM and W99.
- **Never achieved without artefacts:** a measurable capacity drop.
  - IDM strands ramp or lane-drop vehicles, causing teleports.
  - W99 has no drop (discharge 3–6 % above free flow) and collides in heavy congestion.
  - EIDM's breakdowns at the 50 %-share cell are too short to measure a drop.
  - Assertive merging (`lcAssertive`) moved onsets to the network entry ("waves from nowhere").
- **Plants tried:** the MRG3 merge (v1–v3; 0.5 s and 0.2 s steps; 8 driver and lane-change variants) and the LD3 lane drop.
- **Author decision:** pivot to harmonisation, with delay and stops co-primary.

## Silent failures and artefacts caught (each fixed, re-run, logged)

1. Bottleneck "light" node.
2. Runner load counter.
3. I1 off-by-one.
4. Abrupt AV caps causing emergency braking.
5. AV actuator silently disabled (the `av@<id>` rename).
6. AV `speedDev` default.
7. Ring AV collisions.
8. Ring start clamp.
9. IDM insertion failure at `departSpeed="max"`.
10. **SUMO silently accepts unknown vType attributes** (behavioural R-0 check).
11. Quiet stderr hid tracebacks.
12. Discrete action spaces crashed the evaluator.
13. **Capacity-drop estimator confounded by the demand ramp.** Found in the smoke test, fixed before data (Addendum A).
14. **SUMO ACC/CACC emergency-braking artefact at 0.5 s** (the docs warn about coarse steps).
15. **Ramp vehicles stranded at the acceleration-lane end** (MRG3-v3 teleports in every cell).
16. A ':' in a tag broke SUMO's `--log` path (smoke only).
17. The P-H action grid did not contain the tuned classical b = 0.75. Corrected before screening (P-H2).

## Compute

- **Thermal guard (author, 2026-10-02):** pause at a 5-min median ≥ 99 °C, resume below 96 °C.
- **Workers:** 32 on all threads.
- **Peak so far:** watchdog maximum 96 °C.
