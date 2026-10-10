# G-1 stage S2: Z9 follow-up (pre-registration, 2026-10-09; author chose option A)

**Why.** S1 (`g1_s1.md`) killed all 5 cells; Z9 (zipmerge · ramp 900 · main 3,600 · H5) was the only hint (H = 5.8 % [0, 27] on 10 seeds). S2 gives Z9 one larger, final look. **If S2's primary verdict is KILL, this SUMO-geometry line closes** (no length sweep).

- Seeds 7,170,300–329 (30, fresh; from the "reserved" part of the approved block 7,170,000–999; disclosed).
- Plant, controllers, constants, mtfc, timed-oracle windows and metric exactly as S1b (`g1_s1_prereg.md`).
- **H (binding form, fixed now):** the median over seeds of the paired relative difference (T_BNL − T_O2)/T_BNL, 95 % percentile bootstrap CI (10,000 resamples, seed 7,170,399). BNL = lowest median among nc, the tuned constant (in-sample) and mtfc. The ratio of medians is reported only.
- **Primary verdict (all 30 seeds):** KILL if H < 10 % or CI lower bound ≤ 0, else HEADROOM (oracle).
- **Secondary, report-only:** H_jam = the same statistic on the seeds whose NC run broke down (conditional headroom; it cannot change the verdict).
- Same disclosed biases as S1 (oracle minimum picks lucky noise → H biased up; KILL conservative).
