# P1c check T1g: does feedback metering beat no control on the realistic BN4 plant?

**Status:** fixed before data (V148). The design was approved by the author's choice "Feedback test, then decide" on the V147 results. Committed and hashed before any run.
**Why:** the gate's T1f tested constant rates only, and they lose to no control (V147). Before deciding the paper type, the proven feedback laws get a fair test.

## Plant and actuator

Exactly as V146/V147:
- BN4 with lane changes; zipper 100 m; Krauss defaults; lcCooperative 1.0; speedDev 0.10; step 0.5 s;
- release-tracking actuator; amber 5 s; r_min = 800 veh/h (0.4 × QDF);
- demand q = 2,100 veh/h; slowdown incident (edge 5 at 5 m/s; onset and duration as the gate defines);
- 300-s warm-up, 900-s control, control kept on during the drain;
- delay measured against nominal free flow.

## Arms (standard published forms; occupancy = mean period occupancy over the lanes of the chosen loop edge, 30 s)

- **ALINEA:** r(k) = r(k−1) + K_R (ô − o(k)). Form of Papageorgiou et al. 2008, eq. (1), checked in the local PDF. Grid: K_R ∈ {20, 40, 70} veh/h per %; ô ∈ {10, 15, 20, 25, 30} %; loop edge ∈ {e4, e5}. That gives 30 laws.
- **PI-ALINEA:** r(k) = r(k−1) − K_P (o(k) − o(k−1)) + K_R (ô − o(k)). The standard form; the audit checked it against Frejo et al. 2021 eq. (4), and Wang et al. 2014 is still to be read. Grid: K_P ∈ {20, 70}, with K_R, ô and the edge as for ALINEA. That gives 60 laws.
- **Reference:** no control (all green).

## Procedure

1. **Tuning.** Seeds 7,430,180-189, slowdown, every law. Pick the law with the lowest median delay; ties go to the earlier law in list order (ALINEA before PI, then grid order).
2. **Grid adequacy.** If the chosen law sits on an outer edge of its K_R or ô range, extend that parameter once by one step beyond the edge (K_R 120 or 10; ô 5 or 35) on the same tuning seeds, and re-pick.
3. **Test.** Seeds 7,430,190-199: the chosen law against no control, slowdown, paired.

## Criterion (the same bar as the gate's T1f; fixed here)

**T1g PASS** iff rel = median(NC − law) / median(NC) ≥ 10 % on the test seeds.

Report-only rows:
- the 95 % bootstrap CI of the median paired difference;
- window-TTT rel;
- served flow;
- seeds better;
- the chosen law's cost on clean days of the test seeds (paired vs no control).

**Outcome.**
- PASS: a metering claim on this plant is alive. The study protocol (ID/IP, regimes, day mix) is written next.
- FAIL: the metering claim is KILLed on the realistic plant; paper_1 is planned as a methods / cautionary paper.
- Either way the result is reported.
