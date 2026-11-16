# Baseline v2: P0d, 2026-11-04

The frozen plant for confirmatory 3, with no controller. Git tag `baseline-v2`. Decisions: V367-V376. It replaces baseline v1 as the plant to compare with.

Exploratory: this describes the plant. There is no claim.

## The plant

r1m3 as in baseline v1 (road, demand pattern, fleet, 300-m acceleration lane, meter green, ALKS tau 1.6 s, 0.5-s delay, `lcAssertive` 1.4 for all vehicles), and the smooth no-undertaking rule for ALKS changed as in `plant_p0d.json`:

1. The rule's cap moves every 0.1 s, a small step under the vehicle's speed, at a ratio of 1.1 per second (`ease`). As built in P0, a lowered cap was reached within one 0.1-s step and the 0.5-s action step held that braking for 0.5 s, which every 1-Hz metric missed (V367).
2. The rule looks 8 s ahead instead of 5 s (`smooth_s`).
3. Braking may reach 4.4 m/s² when closing on a slower left-lane vehicle needs it (`ease_max`).

Items 2 and 3 were chosen after an earlier check failed on undertakes, on used seeds, and are disclosed as such. r2m3 has the same settings and a second ramp. Frozen code `823eb7f`. All of this is our model; `lcAssertive` 1.4 and the rule are not validated against real traffic.

## Check on seeds 7,440,045-064, 20 seeds, no controller

`check2_table.csv`, `check2_output.txt`, `check2_rows.jsonl.gz`. Real braking is counted every 0.1 s. At 5,300, earlier plant / P0d:

| Metric | Earlier | P0d | % better, CI |
|---|---|---|---|
| Flow | 1,972 | 2,083 | +6.0 [+4.7, +6.3] |
| Delay s | 140.8 | 129.8 | +8.6 [+4.0, +13.1] |
| Ramp delay s | 191.2 | 70.8 | +60.0 [+43.6, +75.3] |
| Fuel g/km | 87.6 | 79.8 | +9.3 [+8.2, +10.1] |
| Network TTC | 1,908 | 158.5 | +87.9 [+39.8, +100.8] |
| Braking 3+ | 4,835 | 1,939 | +59.1 [+46.6, +64.9] |
| Free-road ALKS braking | 1,788 | 221 | +88.2 [+78.6, +91.9] |
| Full-emergency events | 34.5 | 4 | +78.3 [+36.2, +102.9] |
| Undertakes | 10.5 | 14 | -14.3 [-33.3, -4.8] |

All items pass except undertakes at 5,300, which the author counts as met, with this disclosure (V376). 0 collisions and 0 teleports in 80 runs. 1-Hz braking is within 2.2 % of step braking at every level.

## Known gaps

- Instrumented detail runs, lane and vehicle tables as in baseline v1, are not yet stored; they run with the first batch.
- Undertakes are not zero: about 14 per run at 5,300, among about 1,300 ALKS.
- The check is on steady traffic. Perturbations are not yet checked at step resolution.
- On r2m3 at 5,300, lane-end stops are 608.5 at ramp 2 against 7 at ramp 1 (report only).
- Capacity drop is not settled, as in baseline v1.

## Where everything is

Read-only copy, with `SHA256SUMS`: `/home/catalin/work/phd/v5b1_runs/baseline_v2/`: frozen code and all rows. In git here: the plant files for both roads, `constants.json`, the check tables and rows.
