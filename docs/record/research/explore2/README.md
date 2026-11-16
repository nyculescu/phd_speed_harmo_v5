# explore2: work in parallel with round 1 (V433-V435)

Candidates: `candidates.md`. The author picked E1 and E2 (V434).

## E2: the delay test, from existing paired results (V435)

`e2_power.py`, output `e2_power_out.txt`. Noise: paired per-seed delay differences against os1_15_10 (X2 at 5,300, 40 seeds) of the 5 baseline-v3 policies and p333, each centred on 0. The paired SD is 7-11 % of the rule's delay. Statistic: median of paired differences, percentile bootstrap.

Pass rate, mean over the 6 arms:

| rule | true tie, 40 seeds | true +2 %, 40 seeds | true +3 %, 40 seeds |
|---|---|---|---|
| point estimate ≤ +2 % (round 1 T2) | 0.86 | 0.52 | 0.20 |
| upper 95 % bound ≤ 3 % | 0.40 | 0.09 | 0.03 |
| upper 95 % bound ≤ 5 % | 0.68 | 0.39 | 0.21 |
| upper 97.5 % bound ≤ 5 % | 0.58 | 0.30 | 0.14 |

Seeds for 80 % power at a true tie: margin 5 % needs about 60 (95 % bound) or 80 (97.5 % bound); margin 3 % needs about 160 (95 %); margin 2 % needs more than 160.

Reading:
- Round 1's point rule fails a true tie 14 % of the time at 40 seeds, but passes a policy truly 2 % worse half of the time. It does not bound harm.
- A non-inferiority bound does: a policy truly at the margin passes 2-3 % of the time.
- With a paired SD near 10 %, a margin under 5 % is not affordable. 80 seeds at 5 % double round 1's test, about 1 h more of evaluation at 1,330 runs per hour (V426).

Caveats: the noise comes from one cell (X2 at 5,300) and 40 seeds, so its shape is itself uncertain; other cells and demand levels may be noisier. Later rounds only; round 1 stays as approved.

## E1: safety at 0.1 s (V435)

`e1_meter.py`, tests `test_e1_meter.py` (6 pass, synthetic traces only). One run gives both readings: every 0.1-s step, and the whole-second steps the existing metrics use. Measures in vehicle-seconds: TTC < 3 s, DRAC > 3 and > 7 m/s², braking at -3 and -7 m/s², plus braking onsets. `read_libsumo` uses getters only.

Not done yet, after round 1 ends:
1. Hook the meter into the evaluation runner, called every SUMO step.
2. Smoke check: with and without the meter, the existing counters must be identical (V386), and its 1-Hz TTC reading must match the existing close-following count.
3. Then run it on the round-1 finalists and the tuned rules, on seeds the author approves.
