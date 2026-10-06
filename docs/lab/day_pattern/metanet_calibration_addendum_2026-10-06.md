# Addendum (2026-10-06) to the METANET v3 freeze and route-stop record

The record `metanet_calibration.md` / `.json` (commit 0f02418) is not edited. This addendum changes one statement and adds the post-stop findings, by author decision D4.4.

## 1. The post-stop sentence is lifted for the next protocols

The record says that the post-stop results (capacity grid, c2*, F̂, identifiability profiles, §4.8 diagnostics) "may not inform any capacity-factor, plant or protocol choice". By D4.4 this restriction is **lifted for the protocols written after the v3 stop** (the prize screen of D4.2 and a possible METANET v4). The conditions:

- Every post-stop finding a later protocol uses is listed in that protocol's disclosures as **design input taken after seeing v3 calibration-day model output**.
- The restriction still holds for v3 itself: no v3 result is re-labelled, re-run to pass, or replaced.
- Validation days stay unsimulated by any model until the next plant protocol's freeze. That freeze is the single METANET look at the 97 validation days.

## 2. Post-stop findings available as design input

The post-stop findings are listed in `next_plant_study_v0.md` §1. In short:

1. **The 5-s explicit scheme was unstable for this model.** The diffusion number ν·T/L_min² is 1.01 at the ν bound and 0.61 at the fitted ν; v3's build checks did not cover it.
2. **The v3 B1 agreement was a speed–density artefact.** G2's speed at capacity is 46.5–48.1 km/h in all 8 restarts, below the 67.4 km/h event threshold.
3. **B2 is a knife edge on the deterministic plant**: model B2 on 2 (5 s) or 3 (2.5 s) of the 9 real-B2 calibration days.
4. **Event stations read capacity-scaled bottleneck cells.**
5. **Relocation at the E15 merge cell** occurs on 6 of 22 days at c = 1.

The runs behind these findings are ledgered as report-only (`metanet-poststop` rows, 2026-10-06).
