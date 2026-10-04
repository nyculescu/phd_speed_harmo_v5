# Lead 2, ZM3: on-ramp merge modelled as a zipper junction. Realism gate pre-registered 2026-10-03, before any gate run

**Author decision:** both leads in parallel.

**Why.**
- MRG3 (an acceleration-lane merge) and LD3 failed the capacity-drop signature: IDM strands vehicles; W99 and EIDM merge without any drop.
- BN4's **zipper junctions** did produce a capacity drop (1,044 → 900 veh/h).
- ZM3 rebuilds the on-ramp merge as a zipper node, `ZM_SPEC` in `netgen/mrg3.py`:
  - the ramp lane and mainline lane 0 zipper into merge lane 0 (radius 20 m, as in BN4);
  - lanes 1–2 continue;
  - merge and down have 3 lanes;
  - the same 4 km approach, VSL areas and probes as MRG3.

**Smoke test** (throw-away seed 7,120,050, 4,800 and 5,400 / 900, 0.2 s; a code check only): IDM (H0), EIDM defaults (H5) and W99 (H3) all ran with 0 teleports and 0 collisions. **The IDM stranding artefact is gone.** All runs broke down.

**Realism gate:** `t2_realism_protocol.md`, with Addenda A and B unchanged (R-a between-run Q_dis/Q_ff in [0.82, 0.97], R-b, R-c, R-d).
- **Variants:** H5, H3, H0, at 0.2 s.
- **Grid:** main 4,200–6,000 (7 levels) × ramp {600, 900}; stress cell 6,000 / 900.
- **Seeds**, from the approved T2 plant-development block:
  - calibration 7,160,020–7,160,029 (throw-away);
  - checks 7,160,140–7,160,159;
  - determinism re-run 7,160,140.
- **Primary plant** = the first PASS in the order H5, H3, H0.
- **Outputs:** `t2_realism_zm.md` and `t2_realism_verdict_zm.json`.

**If a variant passes:** posted VSL, MTFC and the CAV arms get their tool checks on ZM3 (T0, T1c), pre-registered then.
**If all fail:** Lead 2 stops.

## Result (2026-10-03, `t2_realism_zm.md`): all FAIL, near miss for H5

| Variant | R-a (capacity drop) | R-b (waves) | R-c (discharge) | R-d (origin) | Other |
|---|---|---|---|---|---|
| **H5** (EIDM defaults) | **PASS** (onset share 0.80; Q_dis/Q_ff = 0.967 [0.923, 0.982], inside [0.82, 0.97]) | PASS (−16.9 km/h) | **FAIL** (1,528 veh/h/lane < 1,600) | PASS (100 %) | 0 teleports, deterministic |
| H3 (W99) | not measurable (n = 2 + 7) | — | 1,489 | — | — |
| H0 (IDM) | not measurable (n = 19 + 1) | — | 1,407 | — | 0 teleports |

- **The zipper junction removed the IDM stranding artefact** and produced a measurable capacity drop for EIDM (the first in any merge plant).
- **The bound is not relaxed post hoc.** Lead 2 stops here unless the author decides on a new pre-registered variant.
