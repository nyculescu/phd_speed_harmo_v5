# E1-lite: a few-hour direction check (V236)

Fixed on 2026-11-01, before any main-seed data. It replaces E1 stages A-C for now (author: "69 h is way too much. We must run it for few hours and force have a direction or estimate"). E1-lite is a screen that gives a direction, not a claim. Nothing from it is a thesis result.

## Design

- **Cell:** R only (recurrent PM breakdown, no incident).
- **Window:** PM slices 13:00-20:00. Demand enters only inside the slice, and every run drains.
- **Arms:** NC and the 9 points of the frozen grid at the stage-0 values (`fz_lite.json`; V227-V234):
  - ALINEA at `alinea_3`, K_R 70, setpoints 0.85, 0.95 and 1.05 × ô_cr,alinea (6.60 %);
  - MTFC on the drop loop, K_I 0.02, b_min 0.3, long and short zones, setpoints 0.85, 0.95 and 1.05 × ô_cr,drop (10.74 %).
  - Left out: PI-ALINEA (dropped, V226), MC*, and the per-day oracle as a pass route.
- **Seeds:** main seeds 7,430,230-239 (n = 10), SUMO seed = demand seed.
- **Code:** frozen at the launch commit. `e1 smoke` passes on all 9 controllers first (V231).

## Metric

D is the mean door-to-door delay per vehicle over the slice, including origin and insertion (ramp) queues (`d_all`).

Effect of an arm: rel = median paired difference (NC − arm) / median D_NC, with a 95 % percentile bootstrap CI (the E1 convention).

Reported for every arm (the full operating map), not used in the rule:
- served throughput and TTT;
- ramp emergency braking (the T0 meter braking is unresolved, V232-V233);
- validity;
- the per-seed oracle, labelled noise-dominated (φ_O ≈ 0.16-0.18 at n = 20, V220).

## Direction rule

Applied to the best arm, the one with the largest rel (in-sample; best-of-9 noise floor about +4 %, disclosed). An arm counts only if all of its runs are valid and break no §10.6 stop rule.

| Direction | Condition |
|---|---|
| **KILL direction** | best rel < 0.05 and its upper CI < 0.10 |
| **GO direction** | best rel ≥ 0.10 and its lower CI > 0 |
| **UNCLEAR** | anything else |

- **UNCLEAR:** one extension with 10 more seeds (7,430,240-249, the same arms). The rule is applied once more on n = 20 pooled. If it is still UNCLEAR, the author decides.
- **GO:** a GO direction is confirmed on fresh seeds before anything else is built on it.
- **KILL:** a KILL direction ends E1 on this plant unless the author decides otherwise.

## Known limits

- in-sample choice of the best arm;
- a CI half-width of about ±12 % at n = 10 (s = 0.155);
- no I cell;
- PM slice instead of the full day;
- R was underpowered for the full E1 (V220).

## Addendum (V239-V240, fixed before L2 was read)

- **ALINEA GO:** conditional. No confirmation and no build until the meter passes T0 and the V190 4-min wait question is settled.
- **UNCLEAR at n = 20:** no GO. The best arm's estimate is reported with its upper CI as the largest effect not excluded; E1 builds nothing on this plant.
- **Grid edge:** if the n = 20 best ALINEA point is 0.85, ma/p0.75 runs on the same 20 seeds, report-only (best-of-10, disclosed).
- **GO confirmation:** seeds 7,430,260-279 (seed check first), the n = 20 best arm only, pass = rel ≥ 0.10 and lower CI > 0 on those seeds alone.
- **Corrected limits:**
  - best-of-9 noise floor under the global null: about +6.7 to +9.9 % at n = 10 and +5.0 to +7.3 % at n = 20;
  - observed n = 10 CI half-widths 0.12-0.22;
  - a slice rel of 0.10 ≈ a full-day rel of 0.086;
  - the n = 20 rule's P(UNCLEAR) is about 0.72 with no effect and 0.48 at +10 %;
  - the pooled n = 20 look is a second look at the same family after L1 was read.
- **Report-only additions** (separate code; the rule code is unchanged):
  - per-block L1 and L2 effects;
  - diff, sign, mean version and harm label;
  - the §7.2-7.5 flags;
  - all-lane and `:m_0_0` braking;
  - served throughput with its caveat;
  - the slice loop tests.
