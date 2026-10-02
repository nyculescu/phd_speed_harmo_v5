# DRL lab: status (living document)

*Last update 2026-10-02 00:15 · branch `claude/vsl-lab-core` · every run is in `vsl_lab/runs/ledger.csv` · plan: `docs/plans/vsl_drl_run_roadmap_v0.md`*

## Where we are

| Track | Plant | Phase | State |
|---|---|---|---|
| T1 | BN4: Vinitsky/Flow zipper bottleneck, 10 % AVs | R1 v4, T0b v2 and R2 v2 done; **P1 (PPO) running** | **Capacity drop PASS** (1,044 → 900 veh/h, ratio 0.86); determinism PASS. **Tuned baselines** (mean door-to-door s, 4 cells): NC 412.3 · best constant AV cap 412.8 (≈ NC) · **tuned meter 224.8 (−45 %)** · tuned AV feedback 566.1 (+37 %, worse than NC). **No tuned classical controller on the AV actuator beats NC.** One FAIL in 3,120 runs: a teleport at a long red phase with an untuned meter setting. |
| T3 | RING22: Stern/Flow ring, 1 AV | R1/R2 v1 **invalid** at L ≤ 240 (placement bug); re-run queued | At L ≥ 250, where all 22 cars were present, PI-with-saturation reached ≈ 100 % of the IDM equilibrium speed, i.e. the uniform-flow ceiling. **No headroom over the classical controller on the closed ring.** |
| T2 | MRG3: merge, posted VSL, tuned MTFC (thesis core) | Code and protocol committed; calibration next | — |
| T4 | Corridor, SPECIALIST | Not started | — |

## Silent failures caught so far (each fixed, re-run, and logged)

1. **Bottleneck "light" node.** netconvert's default program at the bottleneck signal turned it red for 5 s every 90 s, which would have metered every "no-control" run. Fixed with a forced all-green program and the H-R7 assertion.
2. **Runner load counter.** The runner counted `loaded = 0`, because SUMO loads all vehicles inside `start()`. Caught by H-S2.
3. **Conservation check off by one.** `I1` was one step early for vehicles departing exactly at a checkpoint: 448 false FAILs, while end-of-run conservation held in all 500 runs.
4. **Emergency braking from abrupt AV caps** (caught in the DRL smoke test). Caps are now rate-limited to Vinitsky's −1.5 / +1.0 m/s².
5. **AV actuator silently disabled.** SUMO renames a vehicle's type to `av@<id>` after `setMaxSpeed`, so every cap baseline equalled no-control to the decimal. AVs are now identified by ID, with an actuator assertion.
6. **AV spec mismatch.** AVs had SUMO's default `speedDev` 0.1 (spec: speedFactor 1).
7. **Ring start positions.** A start-position clamp made one car fail to insert on short rings, leaving 21 instead of 22.
8. **Thermal (the platform, not a bug).**
   - One simulation on a P-core already held the package at ~90 °C.
   - All workers are pinned to E-cores, under a two-timescale guard: the 10-min mean pauses at 90 °C and resumes below 87 °C; the 10 s mean caps at 93 °C.
   - **One cap exceedance (fast 94 °C)** happened while two batches ran together alongside ad-hoc runs. The rule now is one batch at a time.

## Honest expectations so far (before any DRL)

- **BN4:** a tuned classical meter brings outflow to about the bottleneck's capacity. DRL with 10 % AVs can at best *match* it, as Vinitsky found. Worth showing: DRL against the tuned AV-feedback controller on the *same* actuator (`avfb`, R2 v2).
- **Ring:** PI-with-saturation is at the equilibrium ceiling. The ring is a pipeline check only (does DRL learn to harmonise from no-control?).
- **The thesis-relevant search** for a real DRL edge is T2: posted VSL at a merge against tuned MTFC. The niches: information lag, hidden compliance or driver mix, and CAV probe data that a loop-based MTFC cannot use.
