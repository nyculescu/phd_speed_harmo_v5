# Design review of the H1 protocol draft (V155)

Workflow run `wf_029b6589-514` (2026-10-28): four read-only reviewers (mechanism, statistics, code, claims), one adversarial verifier per reviewer, one completeness critic; no simulations. This table is generated from the run journal. Critic findings (X) were not separately verified. Both the claims and code lenses used the prefix C; the lens column tells them apart.

| ID | Lens | Severity (verified) | Verdict | Finding |
|---|---|---|---|---|
| C1 | code | minor | confirmed | The breakdown share is always 100 % in the slowdown cell, and measure() returns other fields that do not apply here |
| C2 | code | major | confirmed | T1d is dropped at the new rates, and the per-edge emergency counter in p1c/episode.py never matches SUMO's warnings |
| C3 | code | minor | confirmed | The 'constant' meter releases pulses of about 11-15 vehicles, so a FAIL may come from the actuator rather than from the flow band |
| C4 | code | minor | confirmed | T0, T3 and a V147 reproduction check are missing; all three are cheap or free |
| C5 | code | minor | confirmed | Failed runs drop out of the validity count, and 'the run is void' is ambiguous |
| C6 | code | minor | confirmed | The edge rule is underspecified, and code above 2,215 veh/h differs from the gate page |
| C7 | code | minor | confirmed | Reusing bn4_slow_test.py verbatim would add runs and derive the grid at runtime; the QDF figure is inconsistent |
| C8 | code | minor | confirmed | 'With the CPU guard' means only a launch check in run_jobs |
| C1 | claims | major | confirmed | 'V147 KILL is not valid evidence' overreaches; the grid was pre-registered, not a code bug |
| C2 | claims | major | confirmed | Binding slowdown cell is likely structurally unpassable for any constant rate; §5 readings overclaim |
| C3 | claims | major | confirmed | Band upper bound 2,106 comes from the deviating detector; gate-detector value is about 2,064 |
| C4 | claims | major | confirmed | Plant failed T1a in V147; no later row resolves it, yet V149 and H1 call it realistic |
| C5 | claims | minor | confirmed | Tuned feedback controller not reported on the H1 seeds |
| C6 | claims | minor | confirmed | Old-plant drop mis-attributed; 'best tuned controller' imprecise |
| C7 | claims | minor | confirmed | Relation between H1 and V149's broad KILL left implicit |
| C8 | claims | minor | confirmed | Gate re-check placed in the study's tuning/evaluation seed ranges |
| C9 | claims | minor | confirmed | Clean-day cell has almost no headroom; its reading row is nearly unreachable |
| C10 | claims | minor | confirmed | QDF quoted inconsistently in §1 |
| M1 | mechanism | blocker | confirmed | The binding slowdown cell cannot test the band above QDF: after the incident, exit flow is fixed at QDF for any constant rate at or above QDF |
| M2 | mechanism | major | confirmed | Pre-queue flow 2,106 (V139) is not reproduced on fresh seeds with the gate detector; the band is narrower and is empty on 4/10 seeds |
| M3 | mechanism | major | confirmed | At 2,000-2,250 veh/h the meter clips bursts instead of limiting the rate; T0 never covered these rates and H1 reports no actuator diagnostics |
| M4 | mechanism | major | confirmed | The clean-day cell has a small, bimodal NC base; a 10 % relative bar there is not comparable to the slowdown cell |
| M5 | mechanism | minor | confirmed | 'Breakdown share at the edge-4 loops' cannot discriminate in the slowdown cell |
| M6 | mechanism | minor | confirmed | Meter-area safety (T1d) is not in the validity criteria for the new rates |
| M7 | mechanism | minor | confirmed | 'Hypothesis B' and 'H2' are not defined in any committed file |
| S1 | statistics | major | confirmed | Readings table leaves several outcomes unmapped, and one row can be read two ways |
| S2 | statistics | minor | confirmed | A point-estimate PASS is read as 'constant metering is alive', with no CI condition and no confirmation step |
| S3 | statistics | major | confirmed | The PASS reading ignores that the plant failed T1a in V147 |
| S4 | statistics | minor | confirmed | The clean-day reading is fragile: small baseline, no CI, and it feeds H2 |
| S5 | statistics | major | confirmed | No stopping rule across T1f, T1g, H1 and H2: repeated attempts at the KILL gate |
| S6 | statistics | minor | confirmed | Bug-rule propagation: no other completed run needs a re-run, but downstream text and the G3 plan do |
| S7 | statistics | minor | confirmed | Band figures mix detectors and seed sets; 'could not pass' is stronger than the evidence |
| S8 | statistics | minor | confirmed | Tuning rule: no tie-break, and the edge rule is one-sided with its end state unstated |
| S9 | statistics | minor | confirmed | The breakdown-share row cannot separate arms in the slowdown cell |
| S10 | statistics | minor | confirmed | Seeds are fresh and inside V135, but they use the study's evaluation partition for a gate re-check |
| S11 | statistics | minor | confirmed | Pre-registration mechanics: commit and hash, bootstrap parameters, no pooling |
| X1 | critic | major | not verified | No ceiling or informed-oracle bound: the 10 % bar sits at or near the fluid ceiling of any mainline meter in the slowdown cell |
| X2 | critic | minor | not verified | The §1 band treats capacity as a fixed number; V147 clean days show it is stochastic, and q_near itself comes from the old detector |
| X3 | critic | minor | not verified | The tuning and evaluation seed sets differ on the covariates that decide the constant meter's effect |
| X4 | critic | minor | not verified | H1 never defines 'best tuned constant rate' |
| X5 | critic | minor | not verified | H1 duplicates V153 G3's calibrated-Δ cell with a different status, and the relation is not stated |
| X6 | critic | minor | not verified | CLAUDE.md pre-batch duties are not in §6, and V147 has no record of them |
