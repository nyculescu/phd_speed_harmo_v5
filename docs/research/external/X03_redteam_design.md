# X03: red-team review of the research design (a second angle)

**Model:** Fable 5.1 · no tools · effort high · max tokens 32,000 · system prompt: Shared rules (README)

## Prompt (paste as the user message)
```
Act as a demanding PhD examiner in traffic engineering and control, and as a skeptical reviewer for a top transportation journal. Below is a complete research design that has not been run yet. Your job is to find what will make it fail or make its results unconvincing, BEFORE any simulation is run. Be concrete and constructive. Do not praise. Assume the author is competent but may have blind spots.

=== RESEARCH DESIGN ===

Thesis title: "Adaptive driving algorithms for intelligent road traffic systems". About 11 months remain.

Research question: Can connected automated vehicles (CAVs), each commanded individually and coordinated through vehicle-to-vehicle (V2V) and vehicle-to-infrastructure (V2X) information, reduce the generalised cost of a congested motorway morning peak (travel time plus energy), without costing commuters noticeable time? Compare against human traffic, against the same CAVs driving on plain adaptive cruise control (ACC), and against tuned published rule-based CAV controllers. Is a learned controller (multi-agent reinforcement learning) better than those rules in identifiable traffic regimes?

Plant (microscopic simulation, SUMO, 0.2 s step):
- Motorway inspired by Dublin's M50, 100 km/h limit.
- Layout: 3 lanes; at 3.0 km an on-ramp merge whose auxiliary lane becomes an off-ramp (weaving); at 4.5 km a lane drop from 3 to 2 lanes; at 5.75 km a second on-ramp merge with an auxiliary lane that becomes an off-ramp; 2 lanes downstream.
- Three control zones of 1 km each, just upstream of the three bottlenecks (2.0-3.0, 3.5-4.5, 4.75-5.75 km).
- No ramp meters and no variable speed limit signs in the proposed system: CAV commands are the only actuator. The motivation is a cheaper system without gantries.

Fleet (a near-future fleet: the 2025 Irish new-car sales mix):
- petrol 25.1 %, diesel 17.1 %, hybrids (HEV+PHEV) 37.3 %, battery-electric 18.9 %; plus 7.5 % heavy trucks at 90 km/h.
- CAVs = 50 % of the electrified and hybrid cars, about 28 % of cars, so the powertrain mix is identical in the human-only baseline and the CAV scenarios: only the driver changes.
- Human drivers: Enhanced IDM car-following. Desired speeds: 55 % at 100 km/h, 44.7 % at 100-120 km/h, 0.3 % at 120-150 km/h. Trucks 90 km/h.
- CAVs: SUMO's ACC car-following model as their base behaviour.

Control:
- Every 2 s each CAV inside a zone receives one of three commands: lower its target speed by 5 km/h, hold, or raise it by 5 km/h. The target is bounded to [50, 100] km/h. On zone entry the target starts at the current speed rounded to 5 km/h. The change is executed as a smooth 2-s ramp (about 0.7 m/s^2). The car's own safety (keeping a safe gap) always overrides the target. The command is released at zone exit.
- Information available to CAVs: their own onboard sensors (speed, radar gap and closing speed to the vehicle ahead, which may be human-driven); V2V from all CAVs within 300 m (the 5 nearest ahead in detail, plus the count and mean speed of the rest); V2X roadside units per zone, broadcasting CAV-probe statistics (mean speed and speed spread per lane) for the vehicle's own zone and the next zone downstream.
- No loop detectors. No time of day. Human-driven vehicles are never measured by the system.

Learned controller:
- Each CAV is an agent; one neural policy is shared by all CAVs (parameter sharing). Proximal Policy Optimisation (PPO), written in-house on the PettingZoo parallel multi-agent interface.
- Agents appear when a CAV enters a zone and leave when it exits.
- The vanilla arm sees onboard + V2V only. The candidate adds the V2X zone summaries and optionally a centralised critic during training.
- Reward per agent every 2 s: minus its own generalised cost increment (value of time x delay increment + energy price x energy increment), minus a share of the corridor-wide generalised cost increment (all vehicles, using simulator ground truth, training only), minus a penalty per hard brake. The reward and even the controller type may still change during the exploratory phase; the final candidate is frozen before a confirmatory run.

Comparators:
- B0: an all-human fleet (the same vehicles driven by humans).
- B1: the same CAVs on plain ACC, no commands.
- R1-R4, rule-based CAV controllers re-implemented with the same 2-s, +/-5 km/h command interface and tuned on tuning seeds:
  - R1: PI with saturation (Stern et al. 2018), re-parametrised for 100 km/h;
  - R2: the CIRCLES I-24 explicit controller with a speed planner fed by V2X;
  - R3: speed harmonisation upstream of merges (FHWA / Ghiasi family), adapted from loop detectors to CAV probes;
  - R4: a constant CAV speed cap.
- An informed oracle: the best rule with its parameters looked up per inflow level.
- Reported references, not part of the pass bar: VSL with low compliance, and VSL plus average-speed cameras with high compliance.

Metrics:
- Headline: generalised cost in euro per vehicle-km over ALL vehicles = value of time x door-to-door delay (including waiting to enter the network) + energy cost. It is divided by a fixed denominator: the planned vehicle-km of the scored vehicles.
- Value of time: Irish appraisal values (commuting about 8.90 EUR per person-hour in 2016 prices x 1.23 occupancy, uplifted to 2026).
- Energy:
  - cars from SUMO's HBEFA4 emission classes (petrol and diesel Euro 6d, battery-electric, plug-in hybrid as a pair of classes, one mode per trip, 50 % electric);
  - trucks from a road-load + Willans physics model, because HBEFA4's truck classes give fuel per km falling with speed at all speeds (a fitting artefact);
  - electricity priced at the battery (no charging loss);
  - prices are Irish retail including tax: petrol 1.98 EUR/L, diesel 2.15 EUR/L, electricity 0.4042 EUR/kWh.
- Guards and constraints:
  - delay must not exceed the human baseline by more than 2 %;
  - CAV hard braking (events below -3 m/s^2 per CAV-km) is a constraint, not a priced cost;
  - a run with more than 2 collisions or any teleport is invalid and counts as that arm's failure.
- Also reported: energy totals per scenario, stop-and-go cycles per vehicle-km, total travel time, throughput, per-zone travel time.

Inflow and protocol:
- Synthetic morning peaks: 15 min warm-up, a 2.5 h scored window shaped like a triangle, and a drain capped at 30 min. Poisson arrivals with per-episode noise.
- The peak level is swept. The "band worth controlling" = levels where the oracle or the best tuned rule cuts the generalised cost by at least 10 % vs the human baseline; it is fixed before any learning.
- Pass bar for a thesis claim: the best learned controller beats the human baseline by at least 10 % (median paired difference over seeds, 95 % bootstrap CI excluding 0), beats the same CAVs on plain ACC, beats the best tuned rule-based controller in at least one pre-registered regime (Bonferroni), and is never more than 5 % worse in any regime. The full operating map is reported.
- Separate seed blocks for calibration, checks, tuning, validation, test and a reserved confirmatory run.
- Every run is logged, including failures.

Known history: in earlier versions of this project the author found that DRL alone could smooth waves but gave little travel-time reduction; harmonisation that worked cost CAVs too much speed; SUMO reproduced capacity drop poorly (teleports and artefacts); and an earlier corridor was abandoned because the actuator had no leverage.

=== YOUR TASK ===

1. Top threats to validity: list the 10 most serious, ranked. For each: what goes wrong, why it is likely (mechanism), how an examiner would phrase the objection, and the cheapest design change that fixes or tests it.
2. Physics and plausibility: with about 28 % CAVs, commands of +/-5 km/h every 2 s, a 50-100 km/h target band and 1-km zones, is a 10 % reduction in generalised cost vs human traffic plausible? Reason quantitatively where you can (e.g. capacity drop magnitudes, wave dissipation by a fraction of vehicles, energy vs speed), and say which literature results you rely on (with [VERIFY] if unsure).
3. Metric design: can the generalised-cost metric be gamed by a learned policy? How? Is the fixed denominator sound? Is pricing energy at retail including tax defensible next to appraisal values of time? Is excluding the charging loss a bias?
4. Baselines and fairness: is B0 (all humans) vs B1 (CAVs on ACC) vs the rule-based controllers a fair and sufficient set? What would a reviewer say is missing?
5. The learning set-up: is per-CAV PPO with a shared policy, appearing and disappearing agents, and this reward likely to learn "when to act before the jam forms"? Name the most likely failure modes (credit assignment, non-stationarity, reward hacking, sparse effect of one car) and the mitigations you would try first.
6. The band-selection procedure: is selecting the inflow band with non-learning arms before learning a valid way to avoid cherry-picking? What residual bias remains?
7. If you could change only three things in this design, which and why?

Output structure: numbered sections 1-7 as above, then a final list "Questions the author must answer". Be specific; avoid generic advice. At most about 5,000 words.
```

## Output (pasted by the author, date: )
