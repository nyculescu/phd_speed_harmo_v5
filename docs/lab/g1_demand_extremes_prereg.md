# G-1 stage S0: demand extremes on the 3-lane SUMO merge (pre-registration, 2026-10-09)

**Question.** At which demand does the 3-lane merge plant (T2's MRG3 code) go from never breaking down to always breaking down? Control can only matter inside that band: below it there is nothing to control, above it the jam is permanent (the author's λ-sweep principle, D4.11/D4.12). S0 is plant facts only: no controller, no DRL, no thesis claim. Author request 2026-10-09 ("check the extremes first, then narrow down to a range that we can truly control").

**Prior evidence (disclosed).** T2's realism gate (Oct 1–3) failed every variant, mainly on the capacity drop (best queue discharge ÷ pre-queue flow 0.967; target band 0.82–0.97). T4's headroom scan: G = 0.4 %, KILL. S0 does not re-judge those results.

## Grid (fixed now)
- Plant: `vsl_lab.jobs.mrg3_run`, `--ctrl nc --plant v3`, default lengths (acceleration lane 250 m, downstream 1,000 m), step 0.5 s, p_nc 0.3, trucks 0.1.
- Layouts: merge, lanedrop (3→2), zipmerge. Drivers: H5 (EIDM) and H3 (W99), the two T2 variants closest to a drop.
- main_peak ∈ {3,000, 3,600, 4,200, 4,800, 5,400, 6,000, 6,600, 7,200} veh/h (1,000–2,400 veh/h/lane); ramp_peak ∈ {300, 900, 1,500} veh/h.
- Seeds 7,170,010 and 7,170,011 (block 7,170,000–7,170,999 approved by the author 2026-10-09; 000–009 throw-away/smoke, 010–099 S0, 100–299 narrowed band). Smoke: one run on 7,170,000, timing only, not used.
- 3 × 2 × 8 × 3 × 2 = 288 runs. Resource rules of CLAUDE.md (CPU/thermal guard via `run_batch`, own systemd scope, ledger row).

## Reported per (layout, driver, ramp_peak)
- breakdown share (the existing `capacity_drop` onset rule: 5-min speed at up0b < 60 km/h) per main_peak;
- discharge ratio (discharge ÷ pre-queue max) of breakdown runs; teleports; drained flag;
- **transition band** = the main_peak levels with breakdown share strictly between 0 and 1, plus the last all-free and the first all-jammed level as its brackets.

## Use (fixed now)
- S0 only locates the band. The next stage (seeds 100–299) refines main_peak inside each bracket in 200 veh/h steps with ≥ 10 seeds, and is pre-registered separately after S0, before it runs.
- A (layout, driver) with no transition band in the grid, or with teleports in > 5 % of its runs, is reported and not refined.
- With 2 seeds per cell, a share of 0.5 is only "mixed"; no CI is claimed in S0.
