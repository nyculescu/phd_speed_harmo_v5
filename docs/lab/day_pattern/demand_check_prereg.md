# Pre-registration: hidden-demand check before a METANET v5 (D4.12, 2026-10-07)

**Purpose.** This is a data-only check on the 22 usable 2023 calibration days, with no model fit. It asks whether any **already pre-registered** demand reconstruction puts enough vehicles into B1 and B2 to exceed their real discharge on the days they really jammed. It informs one decision: whether a METANET v5 with a realism demand uplift is worth writing (option A, D4.12). It is not a plant test and supports no claim. No validation day and no 2024 day is read.

**Background.** In the v4 fit every restart chose G3 capacities of 2,700–3,400 veh/h/lane, so the plant never jams (D4.11). The diagnosis, an inference not yet tested: counts at merges inside the queue record served flow, so the replayed demand never exceeds capacity.

## Reconstructions (all defined before this check)

| Mode | Freeway-to-freeway merges E7, E8, E10, E11 | Controlled ramps E9, E12, E13, E14 |
|---|---|---|
| R | served counts (as replayed) | replay source of part 1 (E14 = Queue) |
| R-NL | in queued bins, s_m,d · P_m(t), exactly as v3 §3.3.3 | as R |
| R-NL+Q | as R-NL | Queue-detector arrivals (v3 §7 R1), where valid; otherwise as R |

Every other input is as replayed: boundary, metered ramps, class-B elements and exit flows.

## Quantities

- **Arrivals A_b(t)** in 15-min bins: the v3 §5.4 P9 definition, implemented as `metanet_gate.arrivals`. Travel times use the v4 nominal group v_f, which affects timing only.
- **Real discharge Q_dis,b,d:** the C4 discharge (2-lane flow at the downstream station) of the day's longest real episode at b, as in F8. B1 is censored at the B2 onset.
- **Excess minutes:** 15 × the number of 15-min bins in [onset − 60 min, episode end] with A_b > Q_dis,b,d, per heavy day at b.

## Signal (fixed now)

**"Worth writing v5"** if, for at least one of R-NL or R-NL+Q, the excess is ≥ 15 min on ≥ 75 % of the real heavy days at B1 **and** on ≥ 75 % of the real heavy days at B2.

Otherwise the reconstruction cannot restore the overload a plant needs, and option A is not pursued (D or E instead). R is reported as the reference.

## Reported only

For each mode:
- the per-day excess minutes;
- the median peak A_b / Q_dis ratio;
- on real-B2-inactive days, the share with A_B2 above the median heavy-day Q_dis,B2 for ≥ 15 min in 15:00–19:00. This is a spurious-overload sanity check.

## Disclosures

- The thresholds 15 min and 75 % are lab conventions; 75 % mirrors P4's and P5's matched shares.
- v3 itself states that R-NL "removes the timing leak more than it restores the demand level", so a negative result is plausible.
- Calibration days are used again, in-sample. No seed is needed (deterministic).
