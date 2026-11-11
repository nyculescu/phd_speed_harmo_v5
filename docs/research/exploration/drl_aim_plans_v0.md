# Plans where DRL could win on a measure other than delay (v0)

2026-11-10. Desk work only. Background: `drl_win_directions_v1.md`. One small read-only script was run on the stored evaluation rows of the truck study; its numbers are marked "exploratory" and support no claim.

**Names used.** "The policy" is the frozen trained controller (v3w). "The fixed rule" sets every automated car to a 0.8-second gap (p333). "The searched rule" is the best rule found by machine search (3E-C). An "event" is a perturbation a real road has: a slow truck, a short blockage, a demand surge.

## What the stored rows say first (exploratory, 240 days, truck and steady traffic)

| Measure | Policy against the fixed rule | Policy against the searched rule |
|---|---|---|
| Delay on the worst tenth of days | +1.4 % [−1.3, +3.3] | +2.1 % [−0.9, +6.0] |
| Trip delay of ramp vehicles (ramp 1; ramp 2) | −0.6 %; +0.1 % | +3.6 %; −1.6 % |
| Fuel per km | +0.2 % [+0.1, +0.3] | +0.1 % [−0.0, +0.2] |
| Share of road and time in a jam (recorded) | +10.7 % [+0.0, +17.6] | −0.6 % [−7.3, +11.3] |

Positive means the policy is better. In short: **no other measure shows a win today.** Bad days, ramp fairness and fuel are ties. Ramp vehicles already wait less than the average trip under every controller, so there is little unfairness to repair. The one hint is about events: the truck added about 31,500 vehicle-seconds of delay under the policy and about 33,200 to 33,600 under four of the best rules. In the slowdown study the policy's edge sat in the days that went badly.

## The two best plans

### Plan 1. Recovery after an event

- **Measure.** The *event cost*: the extra delay an event causes, against the same day without the event. Beside it, the time until speed at the bottleneck is back to normal.
- **Lever.** Training: the policy sees a wider family of events (slow vehicle, short blockage, surge). The reward may stay as it is. A memory of the last few observations is a second step, only if the first check below passes.
- **Same goal for the rules.** One rule search with the event cost as its goal, on the same event family, and a rule with a timer that switches when an event is seen.
- **Independent check.** Fuel per km and the number of jams: neither side is tuned on them, and neither may get worse.
- **Pros.** It is the only measure with a hint in our own rows. Road operators care about it. If DRL loses, a map of how well tuned rules recover is still a thesis result.
- **Cons.** The three event cells already studied are closed, so the events must be new and fixed in advance. Each day runs twice, with and without the event. The event cost is a difference of two noisy numbers: the recorded 240-day interval against the fixed rule still includes zero.
- **Challenges.** The second on-ramp must be checked first (see below). The hint is small, about 5 % of the event cost.
- **Cost, rough.** First check: a rule that is told where and when the event is, against the best rule that is not: 400 to 800 runs, under $0.30. If being told does not help, stop. Full study: one rule search of about 81,000 runs ($9), one training ($1.5 to $3), evaluation of about 23,000 runs ($2 to $8). About $13 to $20 and 20 to 30 build hours.

### Plan 2. Reliability: the bad days and the worst trips

- **Measure.** Delay on the worst tenth of days, and the delay of the slowest 5 % of trips. Travel-time reliability is a standard real-road measure.
- **Lever.** The reward: weigh bad outcomes more than average ones. A trip log must be built, because the stored rows keep no single trips.
- **Same goal for the rules.** A rule search with the same bad-day goal.
- **Independent check.** Fuel per km and ramp delay.
- **Pros.** Easy to explain. It keeps delay as common ground and asks who protects the bad day.
- **Cons.** The stored rows show a tie on bad days. A searched rule may match it once it is given the same goal.
- **Challenges.** Bad days come from the second on-ramp, the least checked part of the model. Tails need many days: about 480.
- **Cost, rough.** Rule search $5, training $1.5 to $3, evaluation of about 11,500 runs $1 to $4. About $8 to $12 and 20 to 25 build hours.

## Why the others are weaker

- **Jam waves.** The model road makes almost no waves by itself, and the searched rule already matches the policy on jam share. A win would need human drivers set to be unstable, which a reviewer can call a rigged test.
- **Fairness between ramp and main road.** Ramp vehicles are not worse off here, and merging is where the simulator's own lane-change rule decides most.
- **Fuel and emissions.** All controllers are within 0.2 % of each other. A headway lever barely moves fuel.
- **Forced stops at the end of the on-ramp lane.** The policy has about 30 % fewer than the fixed rule and the same as the searched rule. It is exactly the unchecked part of the model.
- **Loss of roadside sensors.** Rules that read far ahead would suffer, but the fixed rule uses no sensors and would not, so DRL could only tie it.

## Telling a real weakness of the rules from a simulator quirk

1. The gain must not sit only at the end of the second on-ramp lane; report where it arises.
2. Repeat the verdict on one changed model (a longer ramp lane, or a merge rule that does not read the follower's commanded gap). The sign must hold.
3. The told-in-advance rule must show that knowing about the event helps. Then the mechanism is adaptation, not a quirk.

## Recommendation

No measure other than delay shows a win in the stored rows, so none of these plans is a safe bet. Recovery after an event is the best one: it has the only hint, it matters on a real road, and its first check costs under $0.30 and can stop it early. Do the check of the second on-ramp first, because both best plans depend on it. Then run the told-in-advance check on new events fixed beforehand. Only if that shows room, write the protocol for Plan 1 and keep Plan 2's bad-day measure in it as a second, pre-named reading. My chance estimates, as judgement only: Plan 1 about 20 to 25 %, Plan 2 about 10 to 15 %.

## References

- Stored rows: Plan B S6 (`v5b1_runs/planb_s56_remote/s6/s6_rows.jsonl`, seeds 7,480,400-639); script `aim1.py` in the session scratchpad; single learners, 95 % bootstrap over seeds.
- Jam share: `docs/research/baseline_v5/readings/read6_v23_supplement.json` (V501).
- Truck event cost and the bad-day pattern in the slowdown cell: `phase_a_reports/stored_rows_headroom.md` §2; `phase_b_round1/an_x1x2_delay_edge.md` §3.
- Closed cells: confirmatory_3.md:132 ([A3]), V466, planb.md:160 and :575. New events fixed before results: V456(3), planb.md:576.
- Second on-ramp and lane-change rule: plant_vv_record_v0.md PR-28, PR-08; `drl_win_directions_v1.md` §4.3.
- Same goal for rules; recorded resilience reading: planb.md §3.3; V496.
- Rates: V475, V490, V493 (`drl_win_directions_v1.md` §2).
