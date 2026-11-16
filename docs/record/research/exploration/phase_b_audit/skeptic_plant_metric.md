# skeptic_plant_metric: attack on plant_choice.md and metric_audit.md

Scripts: `/tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/89ba3663-8e1a-45c3-9415-9e2a743fb16b/scratchpad/phaseB/audit2/skeptic/` (`drop_alt.py`, `lc_gap.py`, `own_metric.py`, `pert_check.py`, outputs). EXPL = exploratory, from rows already read for a verdict: median of paired differences, 95 % percentile bootstrap, 10,000 resamples, RNG 20261110, v3w as stacked single learners. No simulation ran.

**1 (major; blocker for any sentence that uses "no drop on plant_c3"). The drop estimate cannot fail for the 0.8-s fleet.**
- V244-V256 re-read. The account of V256 is right: closed "by decision" (V256(2)); "'No real drop' is supported only for lane-end Krauss" (V255(1)). Slips: V256(2) names bn4L and V180-V189 only, not V142-V145; V244(3)'s "upper bound of about 3 %" is left out.
- `drop.py` re-run: identical. The null (matched placebo) was computed; for no control it rests on 12 runs.
- EXPL, p333, S: after onset, outflow minus inflow is +24 veh/h [−12, +96]: no standing queue. A queue reaches upstream of merge 2 in 4 of 240 runs. Demand is 95.6 % of the saturated throughput (5,544; an_delay_floor.md:43), so a discharge loss up to 4.4 % passes unseen. V244's defect, mirrored.
- EXPL, no control, S: a queue forms, so the test is valid. Alternative breakdown, 4a below 50 km/h for 3 minutes: flow before minus after +1.1 % [+0.5, +1.9]; minus placebo +0.6 [−0.3, +1.1]. No loss above about 1 % is shown.
- Stronger than the evidence, toward "no drop": §C "Today it does not", §E "Breakdown costs speed, not flow".
- **Correction:** "No control: no flow loss above about 1 % (EXPL). 0.8-s fleet: untested; these rows cannot show a drop." Direction for PR-26 and V256's scope: unknown.

**2 (major). LC2013 gap rule: true in the code, mechanism mis-stated.**
- Confirmed: ALKS is IDM (fleet.py:264-268, :277; b_merge.py:45); `lcAssertive` 1.4 on every type (fleet.py:179); plant_choice §D's SUMO lines are right. No route file opened.
- Not stated: (a) 0.8 s holds only for an ALKS behind an ALKS (b_env.py:774-779). (b) "Halves" is true at equal speed only: ratio 0.61 with the merger 3 m/s slower. (c) The held gap halves too: an equal-speed human merger into an ALKS-ALKS gap at 27.78 m/s is short by 14.1 m at 0.8 s and 7.8 m at 1.6 s (`lc_gap.py`, my merger length and tau; agrees with critic_M.md:34).
- **Correction:** replace "Short tau admits mergers by construction" by "the rule takes back 1/`lcAssertive` = 71 % of every metre a longer ALKS headway adds (100 % at 1.0)".
- Fairness: the direction, toward the fixed rule, is fair. As a cause of p333's lead it is overstated: 0.8-s gaps admit no equal-speed merger either. As a handicap on every lengthening rule and policy (H1; critic_M F3) it is understated. Size unknown.

**3 (major). Stated directions that could run the other way.**
- V314 `lcAssertive` 1.4, "toward the fixed rule": not shown. On m32 before the tuning (default 1.0, INFERENCE), fixed 0.8 s everywhere already led at 5,300: flow +4.0 %, speed +8.9 %, against +1.0 % and +3.7 % with the merge zone at 1.6 s (V285, exploratory; not cited). By finding 2 the tuning made 29 % of added gap usable, up from 0. **Unknown; the lead predates V314.**
- "1.6 s as no control", "toward the fixed rule": it gives every controller, DRL included, its gain against no control (V419, quoted in memo §1.1). **Every controller alike.**
- PR-28, "toward DRL": INFERENCE, the opposite is as plausible. In SUMO a blocked merger waits; a driver who forces in makes a 0.8-s platoon brake, a cost p333 does not pay here. **Unknown.**
- PR-06 (no lag also makes headway switching free) and PR-15, PR-16 (noise-free inputs serve the policy too): **mixed; partly against p333.**

**4 (minor). Metric audit re-runs.**
- `sens_x.py`: identical. `sens_s6.py`: identical except the signs of `first5_m` and `last5_m` (`meas.py` was edited after the output was written); no quoted number found there. **Correction:** regenerate `sens_s6.out`.
- Pooled-arm null recomputed: +1.31 % (S), +0.46 % (TRUCK). Confirmed.

**5 (minor). Own definitions: no reversal; the TRUCK tie drifts toward v3w.** EXPL.
- Reference speed 80 to 130 km/h, or start-up excluded: S and TRUCK stay ties. v3w's X1 edge over p333: +9.78 % [+5.04, +13.76] at 80, +5.24 at 100, +3.88 [+1.96, +5.63] at 120. Every percentage depends on the reference.
- Unfinished vehicles at 1,800 s, v3w minus p333: S 0.0 [−1.0, +2.0]; TRUCK −2.0 [−4.0, −1.0] (medians 428 against 420-425.5). X1: p333 leaves 0.9 points [0.5, 1.3] more.
- A charge of up to 900 s per unfinished vehicle: S stays a tie. TRUCK, v3w minus p333, moves from −0.13 % [−0.65, +0.28] to −0.41 [−0.89, −0.02].
- The truncation argument holds: no arm has less delay and more backlog. Slowdown logs are identical across arms on 40 of 40 seeds.
- **Correction:** "p333's tie is robust" holds for S. TRUCK: "a tie inside the window; every window-end variant moves toward v3w, by about 0.4 % of network delay at most".

**6 (major). One-sidedness.**
- plant_choice labels six rows "toward the fixed rule" and one "toward DRL". After findings 1-3 one stands (LC2013) and one in part (PR-06). It went easy on DRL and lengthening rules and missed V285. Also missing: the policy was trained on this plant's merge-2 behaviour, with noise-free inputs and lag-free actuation.
- metric_audit is even-handed. Its one overstatement favours p333 (TRUCK "robust").

**Not done.** V142-V145 not opened. TRUCK left out of the drop check (truck event).
