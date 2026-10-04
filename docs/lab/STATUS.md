# DRL lab: status (living document)

*Last update 2026-10-03 21:00 · branch `claude/vsl-lab-core` · every run is in `vsl_lab/runs/ledger.csv` · roadmap `docs/plans/vsl_drl_run_roadmap_v0.md`*

## Bottom line so far (honest)

**First confirmatory DRL claim (R6, 2026-10-03):** a hybrid RecurrentPPO policy scheduling the validated Vinitsky feedback meter on BN4 under perturbations beats the tuned event scheduler (−4.3 %, CI [−14.7, −4.9] s) and a fitted-model MPC (−2.5 %, CI [−14.9, −0.8] s) on 210 reserved seeds (`docs/lab/t1_meter_r6.md`, caveats there). Everything else is exploratory.

**Open now: Lead 1 (T1-M2), incident severity and duration on BN4.**
- The stage-S scan found headroom G = 12.2 % on 21 conditions (`t1_meter2_scan.md`; correction in Addendum A).
- Stage H is running: a tuned event scheduler and a refitted MPC against the oracle lookup on fresh gate seeds 7,170,220–239. The pre-registered prior is that a KILL is likely, with H ≈ 4–13 %.

**Closed since 2026-10-02:**
- Round 4 harmonisation on LD3 was killed (G ≤ 4 %; P-H3 stopped).
- The CORR2 corridor was killed (G 0.4 %).
- Lead 2 (ZM3 zipper merge) failed the realism gate: H5 was a near miss, with discharge 1,528 < 1,600 veh/h/lane.

## Tracks

| Track | State | Key result |
|---|---|---|
| **T1 BN4 bottleneck, 10 % AVs** | done | DRL ≈ NC on test seeds (F1, F2). The infrastructure meter gives −45 %. |
| **T1-A posted VSL on BN4** | stopped | Does not bind (A-T0 FAIL); A-R2 = NC. |
| **T1-B 25 % AVs** | **done: no DRL win** | B-R5 (test seeds 7,110,560–7,110,589): DRL beats the tuned constant cap `cap:18` in **0 of 3** congested cells under the pre-registered rule. Against NC it wins only at q = 1,600 (−2.3 %), and it is worse at q = 1,200 (+4.4 %). The meter is 50–72 % better than DRL. The screening pass was a false positive again (B-F validation finals: 980 / 1,050 / 959 against NC 978). |
| **T1-C DRL meter scheduling** | killed | G = 4.1 % < 10 % |
| **T3 ring** | done | PI-with-saturation is at the ceiling (H ≈ 0). |
| **T2 merge (MRG3)** | **closed by the realism gate** | See below. |
| **Round 3 TM21 vs TM20 (CAVs)** | parked | SUMO's default CACC at 0.5 s brakes hard; at 0.2 s and 25 %, CACC alone worsens delay by 46–93 %. CAV arms showed no authority (T-H). |
| **Round 4 harmonisation (LD3 lane drop, EIDM defaults, 0.2 s)** | killed | T-H0 PASS. Tuned constant VSL (90 km/h) gives −25 % delay and −55 % stops, but G ≤ 4 %. P-H3 stopped. |
| **T1-M hybrid meter scheduling under perturbations** | **CLAIM YES (R6)** | The frozen RecurrentPPO beats `evsched` (−4.3 %) and MPC-F (−2.5 %) on 210 reserved seeds (`t1_meter_r6.md`). |
| **T1-M2 Lead 1 (incident severity and duration)** | **stage H running** | Stage S: G = 12.2 % (21 conditions). Gate rule: H ≥ 10 % with CI lower bound > 0 (`t1_meter2_protocol.md`, Addendum A). |
| **T2 Lead 2 (ZM3 zipper merge)** | FAIL (realism) | H5: capacity drop 0.967, waves −16.9 km/h, origin 100 %, 0 teleports; discharge 1,528 < 1,600 floor. |
| **T4 corridor (CORR2)** | killed | G = 0.4 %. |

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
18. **A 360 s blockage on BN4 teleports in 209 of 220 runs, whatever the controller.** Found after the Lead 1 scan, before stage H. The condition was excluded and both stage-S outcomes logged (G 12.0 % → 12.2 %).

## Compute

- **Thermal guard (author, 2026-10-02):** pause at a 5-min median ≥ 99 °C, resume below 96 °C.
- **Workers:** 32 on all threads.
- **Peak so far:** watchdog maximum 96 °C.
