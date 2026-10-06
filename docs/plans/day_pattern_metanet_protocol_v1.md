# U.S.169 SB METANET plant: calibration and plant gate (protocol v1)

*2026-10-05. Branch `claude/day-pattern-core`. Replaces the draft `day_pattern_metanet_protocol_v0.md` after design-review round 1 (58 kept issues, `/home/catalin/work/phd/dp_data/metanet_review1_kept.json`; one row per issue in Appendix A). Decisions D3.1–D3.3 (`day_pattern_decisions_v0.md`). Data facts: `docs/lab/day_pattern/us169_data_facts.json` (commit `edde7d2`).*

*Status: DRAFT until committed. It becomes binding when committed, after the author has answered the confirmations in §0.6, and that commit precedes any calibration run, any pre-calibration data fact in §3.6 and any model run on real data. Nothing in this file has been run.*

---

## 0. Purpose, scope and what is at stake

### 0.1 Purpose

Build the macroscopic plant on which the day-pattern headroom gate runs (decision P6b: a METANET gate with SUMO confirmation), and show **before any controller is tuned on it** that it reproduces the real U.S.169 SB corridor on days it was not fitted to.

### 0.2 What a PASS certifies, and what it does not

- **Certified:** the mainline response of the uncontrolled corridor to **replayed** 2023 Wednesday inflows (field metering already contained in the replayed ramp flows), at 5-min / station resolution: fit, where/whether/when B breaks down, discharge, no exaggerated drop, the demand dependence of breakdown, the extent and duration of B's queue, no spurious bottlenecks elsewhere, and the clipping mechanism inside the plant (§5).
- **Not certified:**
  - the plant's response to **metering rates other than the field ones** (no 2023 day with different field metering exists here). That response is an extrapolation of a calibrated model; every gate result inherits it, and the SUMO confirmation (P6b) is the only independent check;
  - ramp-queue and ramp-capacity behaviour under simulated metering (controlled mode, §2.7; required in a later protocol, §7 R1);
  - the **speed-limit (VSL) response**: the corridor has no VSL, so it is assumed (§2.8), never validated here;
  - true demand at the unmetered freeway-to-freeway merges on days when B's queue reaches them (their counts are served flows, §3.3.3).

### 0.3 Outcomes

- **PASS:** N0 and P1–P9 all pass (§5). The plant (and its ensemble, §4.6) may be used by the gate protocol.
- **FAIL:** at least one gated check fails. Exactly **one** pre-registered structural fallback, F1 (§6.1), is fitted and judged on the same criteria. Both outcomes are logged.
- **INCONCLUSIVE:** the real-data minimum evidence (§5.2) is not met. It is decided **on real data only, before the model is run on any validation day**. It is never a PASS, it does not trigger F1, and it goes to the author.
- **Route stop:** a plant that fails as built and again after F1 stops the METANET route. Whether the track continues on a SUMO plant (with its own realism protocol) is an author decision, recorded in the decision log.

### 0.4 The capacity drop (C4 deviation, D3.1)

The real drop at B is small and not stable across subsets (corridor-protocol estimator at Old Shakopee Rd):
- all 23 episode Wednesdays: median r = 0.984 (IQR 0.952–1.001);
- earlier splits (data facts; **these are the v0 odd/even and calendar halves, not the v1 split of §3.1**): odd 1-based index 0.997 (n = 11), even 0.961 (n = 12); first half 0.964 (n = 9), second half 0.991 (n = 14).

These data cannot pin the size of the drop, and they cannot exclude a drop of zero on every subset. The plant is therefore gated on **discharge (two-sided)** and on **not exaggerating the drop (one-sided)** (§5.3 P5). A plant with more drop than the data support inflates the prize of preventing breakdown, so it inflates the headroom and risks a false GO. A plant with too little drop understates that prize, which is the conservative direction for a GO. The drop is **not** a term of J. The uncertainty is carried into the gate as drop cells defined on the measured drop (§7 R4).

*Wording change for D3.1 (for the author to record in the decision log; this file does not edit it): "the real drop becomes the plant's calibration target" → "the real drop is a one-sided validation bound".*

### 0.5 Inspections made before this protocol (disclosed)

These were made while designing v1, on 2023 data, with no model fitted. They informed design choices, which is disclosed here; no threshold below was tuned on model output.
1. `us169_data_facts.json` (all 52 Wednesdays): upstream-boundary candidates; Pioneer Tr passage vs mainline balance (15:00–19:00 median ratio 1.235, n = 51); I-494 merges' share of PM inflow (median 0.376, n = 52); queue reach to Highwood Ave when Pioneer Tr is congested (37 of 38 days, coarse indicator: PM minimum 5-min speed < 40 mph at both); drop r by v0 splits.
2. Reviewer read-only checks (review round 1), on cached files: link residuals, Pioneer Tr passage/queue ratio (daily median 1.56), dead lane 5424 at Anderson Lakes Pkwy (43/52 Wednesdays), lane field lengths and free-flow speeds, peak merge flows, and **two day-agnostic null predictors evaluated on 26 Wednesdays used as validation days under a different split** (whole-day NRMSE_v: constant free-flow speed 0.126, median profile 0.085; median-profile NRMSE_q 0.123; in km 0.37–7.20 × 15:00–19:00: 0.30 and 0.21). About half of those days are validation days under §3.1. This is why P1 uses those nulls as references (§5.4) and why their window and stations are fixed now.
3. The configuration (`metro_config.xml.gz`) was parsed for this file (element table, lane sequence, cells, §1). This is geometry, not traffic data.
4. Detector availability in the cached Mayfly lists (`_detectors.json`) was checked for the detectors of the stretch (§3.7).

### 0.6 Confirmations needed from the author before the commit

| # | Item | Default if not confirmed |
|---|---|---|
| A1 | The lane geometry read from the configuration's `lanes`/`shift` (§1.3), in particular that **Pioneer Tr → Old Shakopee Rd is an add-drop auxiliary lane (a weave)**. To be checked against the IRIS r_node documentation or imagery [VERIFY]. | Commit blocked; the merge variant of §1.4 is the only alternative and is fully specified. |
| A2 | Upstream boundary at Minnetonka Blvd: **8.413 km upstream of the first controlled ramp, i.e. 1.587 km short of the ≥ 10 km target** (D2.5.2; `hybrid_combinations_v0.md` §2.2). It is 14.531 km upstream of the Pioneer Tr merge. Disclosed deviation. | Commit blocked. |
| A3 | Calibration/validation split by alternation within each month (§3.1), replacing v0's odd/even index. It gives 28/24 days. | Commit blocked. |
| A4 | The per-day bottleneck capacity factor (§4.7) makes the gate plant **stochastic in capacity** (§7 R3). | Commit blocked. |
| A5 | The one-sided drop criterion (§0.4, §5.3 P5b) and the D3.1 wording change. | Commit blocked. |
| A6 | Thresholds marked **[lab convention]** below (listed in §9.2). They have no literature anchor and are fixed at the commit. | As written. |
| A7 | α_0 for the later VSL extension (§2.8): the value used by Hegyi, De Schutter & Hellendoorn 2005 [VERIFY]. Matters only for H2. | α_0 = 0.1, disclosed as a lab assumption. |

---

## 1. Network (from `metro_config.xml.gz`, read only; km relative to the Valley View Rd entrance M169S51)

### 1.1 Stretch and boundaries

**Stretch:** U.S.169 southbound from **Minnetonka Blvd (station S453, km −8.413)** to **T.H.101 (station S1610, km +9.390)**: **17.803 km**.
- Distance from the upstream boundary to the first controlled ramp (Valley View Rd, km 0.000): **8.413 km** (short of ≥ 10 km; §0.6 A2).
- Distance from the upstream boundary to the B merge (Pioneer Tr entrance, km 6.118): **14.531 km**.
- B's downstream station (Old Shakopee Rd, km 7.199) is 2.191 km upstream of the downstream end.

**Why Minnetonka Blvd.** The boundary must be the most upstream station that (i) has a complete flow measurement and (ii) is free-flowing (5-min speed ≥ 45 mph in ≥ 95 % of 05:00–23:00 bins) on ≥ 90 % of Wednesdays. From the data facts (all 52 Wednesdays): N of I-394 0.365, S of I-394 0.160, 22nd St 0.885 (fail ii); Cedar Lake Rd 0.904 passes (ii) but fails (i), because its auxiliary-lane detector 9685 has no archived 2023 data (a reviewer found its two counted lanes about 7 % below 22nd St with no ramp between); **Minnetonka Blvd 0.923** passes both. The I-394 interchange queue upstream (N of I-394 meets the free-flow rule on only 36.5 % of Wednesdays) is outside the model; on those days the boundary flow is already capped by it (reported, §3.6 F13).

**Upstream boundary (input):** a mainstream origin at the Minnetonka Blvd station with demand = its measured flow (§2.2). Days on which this station is congested are excluded (§3.5 E2).

**Downstream boundary (endogenous, §2.2):** free outflow from the last cell with a virtual density ρ_{N+1} = min(ρ_N, ρ_cr) in the anticipation term. No measured downstream quantity enters the model. The same boundary is used in calibration, validation, the gate and DRL training. Days with spillback from beyond T.H.101 are excluded (§3.5 E3).

### 1.2 Element table (inside the stretch; generated from the configuration, and the build fails if code and table disagree)

Class **M** = measured by its own archived detector; class **B** = balance-estimated (§3.3.4).

**Entrances (15): 10 metered (6 upstream + 4 controlled), 4 unmetered freeway-to-freeway, 1 without detectors.**

| ID | km | Entrance | Kind | Meter (config `storage`) | Inflow source in replay | Lane event | δ_m term |
|---|---|---|---|---|---|---|---|
| E1 | −8.382 | Minnetonka Blvd | metered, upstream | M169S41 (326) | Passage 1979, rule §3.3.2 | merges | yes |
| E2 | −7.233 | T.H.7 WB | metered, upstream | M169S43 (350) | Passage 1987, rule §3.3.2 | merges | yes |
| E3 | −6.835 | T.H.7 EB | metered, upstream | M169S44 (550) | Passage 1990, rule §3.3.2 | merges | yes |
| E4 | −5.896 | Excelsior Blvd | metered, upstream | M169S45 (660) | Passage 1994, rule §3.3.2 | merges | yes |
| E5 | −4.576 | Lincoln Dr | metered, upstream | M169S46 (480) | Passage 1998, rule §3.3.2 | merges | yes |
| E6 | −2.901 | Bren Rd | metered, upstream | M169S47 (370) | Passage 1368 (unchecked: its link holds two undetected exits) | merges | yes |
| E7 | −2.300 | T.H.62 WB | freeway-to-freeway | none | Merge 1369 (served flow, §3.3.3) | merges | yes |
| E8 | −1.866 | T.H.62 EB | freeway-to-freeway | none | Merge 1372 (served flow) | merges | yes |
| E9 | 0.000 | Valley View Rd | metered, **controlled** | M169S51 (300) | Passage 1378, rule §3.3.2 | adds a lane | 0 |
| E10 | 1.730 | I-494 WB | freeway-to-freeway | none | Merge 7108 (served flow) | adds a lane | 0 |
| E11 | 1.810 | I-494 EB | freeway-to-freeway | none | Merge 7086 (served flow) | adds a lane | 0 |
| E12 | 1.833 | Marth Rd | metered, **controlled** | M169S54 (450) | Passage 7087, rule §3.3.2 | joins the added lane | yes |
| E13 | 4.055 | Anderson Lakes Pkwy | metered, **controlled** | M169S55 (500) | Passage 5425, rule §3.3.2 | merges | yes |
| E14 | 6.118 | Pioneer Tr | metered, **controlled** | M169S56 (420) | rule §3.3.2 (balance expected: data facts +24 %) | adds a lane (weave) | 0 |
| E15 | 7.518 | Old Shakopee Rd | no detectors | none | class B: balance Old Shakopee Rd → T.H.101 | merges | yes |

The config `storage` unit is not vehicles (values up to 1,394 occur) and is believed to be feet [VERIFY in the IRIS documentation]. Storage is not used in replay; it matters only in controlled mode (§7 R1).

**Exits (15): 11 measured, 4 class B (3 sinks, because the two T.H.62 exits are lumped).**

| ID | km | Exit | Source | Split-ratio reference (§3.3.5) | Lane event |
|---|---|---|---|---|---|
| X1 | −8.074 | 36th St | Exit 1983 | T.H.7 station + X2 + X1 (downstream form) | — |
| X2 | −7.670 | T.H.7 | Exit 1984 | T.H.7 station + X2 | — |
| X3 | −6.221 | Excelsior Blvd | Exit 1991 | Excelsior Blvd station + X3 | — |
| X4 | −5.003 | Lincoln Dr | Exit 1995 | Lincoln Dr station + X4 | — |
| X5 | −3.492 | Bren Rd | Exit 1348 | Bren Rd station + X5 | — |
| X6+X7 | −2.549 (X6), −2.164 (X7) | T.H.62 WB + T.H.62 EB | none: **one lumped class-B sink at km −2.549** | Bren Rd station + E6 (upstream form) | — |
| X8 | −0.574 | Valley View Rd | Exit 1375 | Valley View Rd station + X8 | — |
| X9 | 0.466 | W 78th St | detector 7110 has no 2023 data: class B | I-494 station (3 lanes) + X9 | — |
| X10 | 1.355 | I-494 EB | none: class B | Highwood Ave station + X10 | the added lane ends here (3 → 2) |
| X11 | 3.751 | Anderson Lakes Pkwy | Exit 5422 | Anderson Lakes station + X11; if that station is invalid, S of Highwood Ave station (upstream form, no ramp between) | lane ends (3 → 2) |
| X12 | 5.818 | Pioneer Tr | Exit 5427 | Pioneer Tr station + X12 | — |
| X13 | 7.017 | Old Shakopee Rd | Exit 5432 | Old Shakopee Rd station + X13 | the weave lane ends (3 → 2) |
| X14 | 8.999 | T.H.101 NB | Exit 6764 | T.H.101 station + X14 + X15 | — |
| X15 | 9.217 | T.H.101 SB | Exit 6765 | T.H.101 station + X15 | — |

**Stations (17 data-bearing): the boundary, 15 interior, and the downstream end.** Station flow = the sum over **all** lanes the configuration counts, Auxiliary-category lanes included (7097 and 7077 were pulled with author approval: 416 requests, ledger row of `edde7d2`).

| km | Station | ID | Lanes | Lane detectors | Role in the fit (§4.2) |
|---|---|---|---|---|---|
| −8.413 | Minnetonka Blvd | S453 | 2 | 1977, 1978 | upstream boundary (input only) |
| −7.298 | T.H.7 | S455 | 2 | 1985, 1986 | flow + speed |
| −6.946 | Van Buren Way | S456 | 2 | 1988, 1989 | flow + speed |
| −5.974 | Excelsior Blvd | S457 | 2 | 1992, 1993 | flow + speed |
| −4.600 | Lincoln Dr | S458 | 2 | 1996, 1997 | flow + speed |
| −3.370 | Bren Rd | S459 | 2 | 1366, 1367 | flow + speed |
| −2.099 | T.H.62 | S460 | 2 | 1370, 1371 (field 20.0 / 11.0 ft) | speed only (flow closed by the T.H.62 balance) |
| −0.860 | 69th St | S461 | 2 | 1373, 1374 | flow + speed |
| −0.364 | Valley View Rd | S462 | 2 | 1376, 1377 | flow + speed |
| 0.370 | S of Valley View Rd | S1770 | 3 | 1379, 1380, 7094 | flow + speed; queue area |
| 1.137 | I-494 | S1771 | 3 | 7097 (Aux), 7098, 7099 | speed only (flow closed by the X9 balance); queue area |
| 1.667 | Highwood Ave | S1772 | 2 | 7084, 7085 | speed only (flow closed by the X10 balance); queue area |
| 2.893 | S of Highwood Ave | S1773 | 3 | 7077 (Aux), 7078, 7079 | flow + speed; queue area |
| 3.922 | Anderson Lakes Pkwy | S1147 | 2 | 5423, 5424 | flow + speed when valid (5424 dead on most days); queue area |
| 6.038 | Pioneer Tr | S1140 | 2 | 5428, 5429 | flow + speed; **B upstream**; queue area |
| 7.199 | Old Shakopee Rd | S1141 | 2 | 5433, 5434 | speed; flow only if E14 keeps Passage; **B downstream**; queue area |
| 9.390 | T.H.101 | S1610 | 2 | 6766, 6767 | downstream end (model output); speed only (flow closed by the E15 balance) |

**Not modelled** (beyond T.H.101): Co Rd 21 SB exit, Co Rd 21 NB and T.H.13 CD WB entrances, the Co Rd 21 and S of Co Rd 21 stations. **Upstream of the boundary** (not modelled): everything from N of I-394 to the Minnetonka Blvd exit (km −8.715).

### 1.3 Lane geometry from the configuration's r_nodes (not from stations)

λ is read from the `lanes` attribute of **every** active r_node, including the detector-less ones (rnd_89165, rnd_1506, rnd_143, rnd_89495, …). Lane events are read from the change of the right-edge `shift` attribute at ramp nodes: +1 at an entrance = a lane added; −1 at an exit = a lane ending as an exit lane; a drop between two plain r_nodes = a merging lane drop. This reading of `shift` is ours [VERIFY, §0.6 A1].

| From km | To km | λ | How the section starts |
|---|---|---|---|
| −8.413 | 0.000 | 2 | — |
| 0.000 | 1.355 | 3 | lane added by Valley View Rd (E9); it is the Auxiliary lane 7097 at I-494 and ends as the I-494 EB exit lane (X10) |
| 1.355 | 1.730 | 2 | — |
| 1.730 | 1.810 | 3 | lane added by I-494 WB (E10) |
| 1.810 | 2.390 | 4 | lane added by I-494 EB (E11); Marth Rd (E12, km 1.833) joins without adding a lane |
| 2.390 | 3.751 | 3 | **merging lane drop** between rnd_143 (km 2.283, 4 lanes) and rnd_89495 (km 2.390, 3 lanes); placed at 2.390, the first r_node with 3 lanes. The right lane (Auxiliary 7077 at S of Highwood Ave) ends as the Anderson Lakes Pkwy exit lane |
| 3.751 | 6.118 | 2 | — |
| 6.118 | 7.017 | 3 | lane added by Pioneer Tr (E14) that ends as the Old Shakopee Rd exit lane (X13): **B is an add-drop weaving section** (no r_node between 6.118 and 7.017 records a lane count) |
| 7.017 | 9.390 | 2 | — |

Sequence: **2 | 3 | 2 | 3 | 4 | 3 | 2 | 3 | 2**.

**Terms placed from this table (§2.1):**
- **φ (lane drop)** only at the merging drop at km 2.390, in the last cell before it (cell 22), with Δλ = 1.
- Where a lane ends as an exit lane (X10, X11, X13), λ changes at the exit node **without** a φ term; the exit split is applied in that cell.
- **δ_m (merging)** = 0 at the lane-adding entrances (E9, E10, E11, E14); δ_m applies at the entrances that merge into existing lanes (E1–E8, E12, E13, E15), in the cell they join.
- No exit-lane-end coefficient φ_x is added.

### 1.4 Cells (rule fixed now; the resulting table must be reproduced by code)

**Rule.**
1. Break points = every data-bearing station and every λ-change point of §1.3.
2. A sub-piece between break points shorter than **L_min = 250 m** is merged with an adjacent sub-piece of the **same λ** (removing a station break point; if both neighbours qualify, the shorter one). If no neighbour has the same λ, it is merged into the neighbour with the **larger λ**, which moves that λ-change point by at most the short piece's length (logged).
3. Each resulting piece of length L is split into n = max(1, round(L / 500 m)) equal cells.
4. The cell table and the merge log are written to the build manifest; the build fails if they differ from this section.

**Merges on this configuration:** 1.137–1.355 (218 m) into 0.370–1.137; 1.667–1.730 (63 m) into 1.355–1.667; **1.730–1.810 (80 m, λ = 3) into the 4-lane piece** (no same-λ neighbour: the I-494 EB lane addition moves 80 m upstream to km 1.730; disclosed); 3.751–3.922 (171 m) into 3.922–6.038; 6.038–6.118 (80 m) into 3.751–6.038; 7.017–7.199 (182 m) into 7.199–9.390.

**Result: 37 cells, 352–660 m.** Groups: G1 = cells 1–17 (2 lanes, 55 mph posted); G2 = cells 18–25 (the interchange, 2–4 lanes); G3 = cells 26–37 (65 mph posted, 2–3 lanes).

| Cells | From–to km | Length (m) | λ | Group | Stations read (§1.5) | Ramps (config order) |
|---|---|---|---|---|---|---|
| 1–2 | −8.413 to −7.298 | 2 × 557.5 | 2 | G1 | T.H.7 (cell 2) | E1, X1 (cell 1); X2 (cell 2) |
| 3 | −7.298 to −6.946 | 352 | 2 | G1 | Van Buren Way | E2 |
| 4–5 | −6.946 to −5.974 | 2 × 486 | 2 | G1 | Excelsior Blvd (5) | E3 (4); X3 (5) |
| 6–8 | −5.974 to −4.600 | 3 × 458 | 2 | G1 | Lincoln Dr (8) | E4 (6); X4 (8) |
| 9–10 | −4.600 to −3.370 | 2 × 615 | 2 | G1 | Bren Rd (10) | E5 (9); X5 (10) |
| 11–13 | −3.370 to −2.099 | 3 × 424 | 2 | G1 | T.H.62 (13) | E6, X6+X7 lumped (12); E7 (13) |
| 14–15 | −2.099 to −0.860 | 2 × 620 | 2 | G1 | 69th St (15) | E8 (14) |
| 16 | −0.860 to −0.364 | 496 | 2 | G1 | Valley View Rd | X8 |
| 17 | −0.364 to 0.000 | 364 | 2 | G1 | — | — |
| 18 | 0.000 to 0.370 | 370 | 3 | G2 | S of Valley View Rd | E9 |
| 19–20 | 0.370 to 1.355 | 2 × 492.5 | 3 | G2 | I-494 (20, inside) | X9 (19); X10 (20) |
| 21 | 1.355 to 1.730 | 375 | 2 | G2 | Highwood Ave (inside) | — |
| 22 | 1.730 to 2.390 | 660 | 4 | G2 | — | E10, E11, E12; φ applies here |
| 23 | 2.390 to 2.893 | 503 | 3 | G2 | S of Highwood Ave | — |
| 24–25 | 2.893 to 3.751 | 2 × 429 | 3 | G2 | — | X11 (25) |
| 26–30 | 3.751 to 6.118 | 5 × 473.4 | 2 | G3 | Anderson Lakes Pkwy (26, inside); Pioneer Tr (30, inside) | E13 (26); X12 (30) |
| **31–32** | 6.118 to 7.017 | 2 × 449.5 | 3 | G3 | — | E14 (31); X13 (32) |
| **33**–37 | 7.017 to 9.390 | 5 × 474.6 | 2 | G3 | Old Shakopee Rd (33, inside); T.H.101 (37) | E15 (34); X14, X15 (37) |

**B cells = 31, 32, 33** (the weave and the first 2-lane cell after the Old Shakopee Rd exit, which holds the Old Shakopee Rd station). They are where the capacity factor (§4.7) and F1 (§6.1) act. *Merge variant (only if A1 rejects the weave reading):* the 3.751–9.390 stretch is one 2-lane piece (11 cells of 512.6 m by the same rule), δ_m applies at E14, and the B cells are the cell containing km 6.118 and every cell downstream of it up to and including the cell containing km 7.199.

### 1.5 Ramp placement and station readings in the model

- An entrance at km x feeds the cell containing x; an entrance exactly on a cell boundary feeds the downstream cell. An exit at km x leaves the cell containing x; an exit exactly on a boundary leaves the upstream cell.
- **Model value at a station** = the cell containing the station's km (a station exactly on a boundary reads the upstream cell). Flow is corrected for ramps of the same cell that lie **downstream** of the station: q_s = q_i − Σ(entrance releases downstream of s in cell i) + Σ(exit flows downstream of s in cell i). On this configuration this matters at I-494 (cell 20: + X10) and Anderson Lakes Pkwy (cell 26: − E13). Model speed at the station = v_i.
- 5-min model aggregates: flow = mean of q_s over the 60 steps; speed = Σ q_s / Σ (q_s / v_i) over the bin (the model counterpart of the detector estimator ΣQ/ΣK).

### 1.6 B-mechanism diagnostic (real data, calibration days only, before any fit)

The geometry (§1.3) and the station pattern cannot separate a weave/merge-led breakdown from one led by the Old Shakopee Rd exit queue spilling back. METANET with fixed split ratios cannot produce the latter, so it is tested first.
- **Data:** exit detector 5432 (km 7.017), 5-min counts and occupancy; the B onset t0 from the corridor rule (§5.1) on each real-B-active **calibration** day.
- **Control:** the median 5432 occupancy in 15:00–19:00 on calibration days on which B is not active.
- **A day is exit-led** if (a) 5432 occupancy ≥ 2 × the control median **and** ≥ 20 % for ≥ 3 consecutive bins inside [t0 − 15 min, t0 + 30 min]; (b) the first such bin is no later than t0 + 5 min; (c) 5432 is valid that day.
- **Outcome** (over active calibration days with valid 5432): **EXIT** if ≥ 50 % are exit-led; **base** if ≤ 20 %; **INCONCLUSIVE** otherwise or if fewer than 6 days qualify. INCONCLUSIVE keeps the base structure and is reported. [Thresholds: lab convention.]
- **EXIT branch (pre-registered):** the base model (not F1) gets an exit-capacity cap at X13 (cell 32): s_X13 = min(β·F, C_x); when it binds, the cell-32 outflow is limited to (1 − β)/β · C_x (FIFO blocking). C_x is one extra calibrated parameter, bounds 900–2,200 veh/h [lab convention]. F1 stays as specified, so there is still exactly one fallback.
- Reported in both cases: P5 also as total bottleneck throughput (Old Shakopee Rd station + X13), for model and real data. If EXIT, the D3.1 drop (≈ 1.6 %) is flagged as measuring through-flow, not bottleneck capacity.

---

## 2. Model

METANET (Papageorgiou, Blosseville & Hadj-Salem 1990; Kotsialos et al. 2002 [VERIFY both]). Notation: cell i = 1…37, step k, T = 5 s, L_i and λ_i from §1.4, g(i) the cell's group.

### 2.1 Equations

**Flow:** q_i(k) = ρ_i(k) · v_i(k) · λ_i.

**Density:** ρ_i(k+1) = ρ_i(k) + T / (L_i λ_i) · [ q_{i−1}(k) − q_i(k) + r_i(k) − s_i(k) ],
with r_i the sum of origin releases into cell i (§2.3) and s_i the sum of exit flows from cell i (§2.4).

**Speed:**
v_i(k+1) = v_i(k)
 + (T/τ) · [ V_i(ρ_i(k)) − v_i(k) ]
 + (T/L_i) · v_i(k) · [ v_{i−1}(k) − v_i(k) ]
 − (ν T)/(τ L_i) · [ ρ_{i+1}(k) − ρ_i(k) ] / [ ρ_i(k) + κ ]
 − δ_m · T · r_i^m(k) · v_i(k) / [ L_i λ_i (ρ_i(k) + κ) ]
 − φ · T · Δλ_i · ρ_i(k) · v_i(k)² / [ L_i λ_i ρ_cr,i ]

- r_i^m = the releases of the **merging** entrances in cell i (δ_m-entrances of §1.2); the lane-adding entrances do not enter this term.
- Δλ_i = 1 in cell 22 only, otherwise 0 (§1.3).
- The merging coefficient is named **δ_m** to avoid a clash with the gate draft's drop variable.

**Fundamental diagram:** V_i(ρ) = v_f,g · exp( −(1/a_g) · (ρ/ρ_cr,i)^{a_g} ), with one (v_f, ρ_cr, a) per group. ρ_cr,i = ρ_cr,g, except in the B cells, where ρ_cr,i = c · ρ_cr,g (c = 1 for the frozen plant; c varies only in §4.7 and later in the gate) and where F1 acts (§6.1). Cell capacity per lane: Q_cap,i = v_f,g · ρ_cr,i · e^{−1/a_g}.

### 2.2 Boundaries

- **Mainstream origin (Minnetonka Blvd):** q_0(k) = min[ d_0(k) + w_0(k)/T, q_lim(k) ], w_0(k+1) = w_0(k) + T (d_0 − q_0), with d_0 = the measured station flow. q_lim = λ_1 v_1 ρ_cr,1 (−a_1 ln(v_1/v_f,1))^{1/a_1} if v_1 < V_1(ρ_cr,1); otherwise q_lim = λ_1 Q_cap,1 (form after Kotsialos et al. 2002 [VERIFY]).
- **Virtual upstream speed:** v_0(k) = v_1(k).
- **Downstream:** outflow of cell 37 uncapped; ρ_38(k) = min(ρ_37(k), ρ_cr,G3) in the anticipation term.

### 2.3 Origins: replay mode (calibration and the plant gate)

For every entrance o feeding cell μ, with queue w_o (vehicles), w_o = 0 at 04:00:
- q_o(k) = min[ d_o(k) + w_o(k)/T, Q_o, Q_o · (ρ_max − ρ_μ(k)) / (ρ_max − ρ_cr,μ) ];
- w_o(k+1) = w_o(k) + T · (d_o(k) − q_o(k)).

**Demand d_o in replay:**
- metered ramps (E1–E6, E9, E12–E14): the replay inflow chosen by §3.3.2 (Passage, or the balance-derived inflow). There is **no meter-rate cap** in replay: the field meter's action is already in d_o;
- freeway-to-freeway ramps (E7, E8, E10, E11): the measured Merge flow (a served flow, §3.3.3);
- Old Shakopee Rd (E15): the class-B balance (§3.3.4).

**Capacity Q_o = 2,200 veh/h per ramp lane** (configuration `lanes` = 1 for all 15 entrances), fixed and not fitted. In replay it is chosen to be non-binding (all observed 5-min ramp flows quoted in the review are ≤ 1,800 veh/h); any bin where d_o > Q_o is reported. Volume clipped by the supply term stays in w_o and is released as soon as the mainline admits it: replayed vehicles are never discarded and never forced into a jammed cell.

**Why the ramp-capacity scale and ρ_max are not fitted:** in replay they bind only through supply-limited bins, which are a model misfit, so they are not identifiable from replay data. ρ_max is fixed at **180 veh/km/lane** (Hegyi et al. 2005, citing Kotsialos et al. 1999 [VERIFY]; Poole & Kotsialos 2016 report calibrated 173–183 [VERIFY]).

**Reported per origin and day (not gated):** supply-clipped volume Σ T (d_o − q_o)⁺, end-of-day w_o, queue-minutes. Any origin (mainstream included) with w_o > 0 for ≥ 15 consecutive minutes is listed as a **plant misfit** next to P1–P9, with the vehicles it withheld from B. Next to P5 and P9: the share of P5 days on which Pioneer Tr had clipped volume > 0, and that volume as a share of its daily inflow.

### 2.4 Exits

For each exit e in cell i, with split ratio β_e(k) from §3.3.5:
- s_e(k) = β_e(k) · F_e^mod(k), where F_e^mod = q_{i−1}(k) + Σ q_o(k) over entrances in cell i upstream of e − Σ s_x(k) over exits in cell i upstream of e (configuration order);
- s_i = Σ s_e over the exits of cell i.

This is the model counterpart of β defined against the flow **arriving at the diverge** (§3.3.5). Examples: X1 in cell 1 sees q_0 + E1; X14 then X15 in cell 37 see q_36 and q_36 − s_X14.

### 2.5 Numerics (fixed now)

- **Time step T = 5 s** (60 steps per 5-min bin).
- **CFL, asserted at build against the bound maxima, not the current iterate:** v_cap = 1.05 × v_f,max = 1.05 × 150 km/h = 157.5 km/h (43.75 m/s); T · v_cap = 218.75 m ≤ min L_i = 352 m. Courant number ≤ 0.62 (margin 1.61).
- **Relaxation, asserted at build:** τ_min = 10 s = 2T, so T/τ ≤ 0.5 over the whole τ range (the explicit relaxation step never overshoots V).
- **State limits after every step:** v_i ∈ [v_min, 1.05 · v_f,g(i)] with **v_min = 7.4 km/h fixed** (Kotsialos et al. 2002, Table II, as reported by the review [VERIFY]); ρ_i ∈ [0, ρ_max]; w_o ≥ 0.
- **Admissibility during estimation:** an evaluation with a non-finite value, or with density or upper-speed clipping in > 1 % of cell-steps on any calibration day, gets **J = 10** (worse than any admissible J) and is counted per restart. v_min floor activations are part of the model and are reported only.
- **Gate check N0 (§5.3):** on every usable validation day, density and upper-speed clipping ≤ 1 % of cell-steps.
- **Step-halving (reported, not gated):** the frozen parameters re-run at T = 2.5 s on all calibration days; report the relative change of J and the per-station RMS change of 5-min speeds.
- T, L_min, the cell rule and these bounds are frozen by this commit; any change is a protocol amendment.

### 2.6 Implementation choices (fixed now)

- Inputs are 5-min means held constant over the 60 steps of the bin; class-B balances (15 min) are held constant over their three 5-min bins.
- **Warm-up:** at 04:00 every cell starts at the free-flow steady state of the 04:00 boundary flow (ρ = q/(λ v_f), v = v_f), all queues empty; the model runs on the measured 04:00–05:00 inputs; nothing before 05:00 is scored. Scoring and all criteria use 05:00–23:00 (216 bins).
- Units in the model: km, h, veh; detector speeds are converted from mph (1 mph = 1.609344 km/h).
- Model code: `vsl_lab/plants/metanet.py`; vectorised over days. Days are independent.

### 2.7 Plant modes

- **Mode R (replay)** is the only mode in this protocol (§2.3).
- **Mode C (controlled)** is used by the headroom gate, H1 and H2. Its definition, its demand reconstruction (controlled ramps from Queue detectors; freeway-to-freeway demand on clipped days), ramp storage and `max_wait`, and an equivalence check against mode R are **requirements on a later protocol**, stated in §7 R1–R2, and must be committed before any gate run. Ramp demand (Queue detectors) is not used here.

### 2.8 Speed-limit extension (not calibrated, not validated here; fixed now for later use)

- **The calibrated plant has no speed-limit term:** V_i = V(ρ_i) in every cell. The posted 55/65 mph limits are absorbed in the fitted v_f. "No VSL displayed" (including b = 1) means the term is absent, so the no-VSL plant is exactly the plant judged in §5 (unit test, bit-for-bit, §8.4).
- **Primary response form when a VSL v_VSL,i is displayed:** V_i = min[ V(ρ_i), (1 + α) · v_VSL,i ] (Hegyi, De Schutter & Hellendoorn 2005 [VERIFY]). Under this form a cell's static capacity falls only if (1 + α) v_VSL,i < v_f e^{−1/a}.
- **Pre-registered variant for H2:** the VSL-modified fundamental diagram of the MTFC literature (Carlson et al. 2010 [VERIFY]), in which the VSL scales v_f and shifts ρ_cr, with its parameters taken from that source.
- **α** cannot be identified from these data (no VSL on the corridor). α_0 = the Hegyi et al. 2005 value [VERIFY, §0.6 A7; default 0.1]; sensitivity values {0.0, 0.2}. Neither the form nor α_0 may change after any VSL result has been seen. The binding rules for their use are in §7 R6.

---

## 3. Data

### 3.1 Days and split

**Days:** the 52 Wednesdays of 2023 in the D3.3 pull. The 52 weekend days (26 Saturdays, 26 Sundays) are a reported check only (§5.5). **2024 is not opened by this protocol** (D3.3); the transfer check P-T is defined in §5.6 and executed under the gate protocol.

**Split (fixed before any exclusion):** within each calendar month, number the Wednesdays 1, 2, 3, … in date order; **odd positions → calibration, even positions → validation**. Months with five Wednesdays (March, May, August, November) give three calibration days and two validation days. Code: `[d for _, g in groupby(weds_2023, key=lambda d: d.month) for j, d in enumerate(g) if j % 2 == 0]` for calibration and `j % 2 == 1` for validation, with `weds_2023` all 2023 Wednesdays in date order.

- **Calibration (28):** 01-04, 01-18, 02-01, 02-15, 03-01, 03-15, 03-29, 04-05, 04-19, 05-03, 05-17, 05-31, 06-07, 06-21, 07-05, 07-19, 08-02, 08-16, 08-30, 09-06, 09-20, 10-04, 10-18, 11-01, 11-15, 11-29, 12-06, 12-20.
- **Validation (24):** 01-11, 01-25, 02-08, 02-22, 03-08, 03-22, 04-12, 04-26, 05-10, 05-24, 06-14, 06-28, 07-12, 07-26, 08-09, 08-23, 09-13, 09-27, 10-11, 10-25, 11-08, 11-22, 12-13, 12-27.

Excluded days (§3.5) are removed from their own set and counted per reason. They are never moved between sets, never replaced, and the sets are never re-balanced. Both date lists, and every exclusion with its reason, go to `metanet_calibration.json`. The alternation spreads seasons and multi-week regimes (work zones, detector faults) over both sets; validation therefore tests interpolation within 2023, not transfer to 2024 (that is P-T).

**Holiday-adjacent days stay in** (the plant replays measured inputs) and are reported as a stratum: 2023-01-04 (calibration), 07-05 (calibration), 11-22 (validation), 12-27 (validation).

### 3.2 Cleaning: two layers (fixed now)

**3.2.1 Event layer** (every real-side event: B active, onsets, episodes, Q_dis, r, queue extent, bottleneck pairs, boundary and spillback congestion). It is the corridor-protocol estimator **unchanged** (`vsl_lab/data/corridor_analysis.py`: `lane_bins`, `station_day`, `episodes`, the C4 block of `analyse_corridor`): 5-min bins from ≥ 9 of 10 30-s values, a lane-day is dead if it has zero counts 06:00–20:00, a station-day is valid only if ≥ 90 % of its bins have a value for every lane and no lane is dead, speed = ΣQ/ΣK in mph. The only extension: a station's lanes are all lanes the configuration counts (Auxiliary included at I-494 and S of Highwood Ave). The B stations (Pioneer Tr, Old Shakopee Rd) have no Auxiliary lane, so the committed v2 references for B are unchanged.

**3.2.2 Fit layer** (inputs and the NRMSE terms).
- 30-s gaps of ≤ 15 min are linearly interpolated **before** 5-min aggregation; longer gaps make the lane-day invalid for fitting (disclosed deviation from the corridor protocol, which does not interpolate).
- Lane-day validity: ≥ 90 % valid 5-min bins after interpolation, and not dead (Addendum B rule).
- **Flow-valid station-day:** every lane valid, Auxiliary included.
- **Speed-valid station-day:** at least one retained lane (§3.2.3) valid; station speed = ΣQ/ΣK over the retained valid lanes.

**3.2.3 Lane speed screen (fixed before fitting; calibration days only).** For each mainline lane: the median 5-min speed over 05:00–06:00 bins with volume > 0, pooled over the usable calibration days. A lane whose median lies outside 50–80 mph, or that has fewer than 100 such bins, is excluded from the speed term on **all** days; its counts stay in the flow. The excluded-lane list (with field lengths, e.g. T.H.62 lane 2 at 11.0 ft) is frozen in the pre-calibration facts commit.

**3.2.4 Station speed scaling (speed term only; fixed before fitting; calibration days only).** For each interior station s: m_s = the median over calibration station-days of the station's median 05:00–06:00 speed (retained lanes). For each group, m_G = the median of m_s over its stations. Scale c_s = m_G / m_s, frozen and applied unchanged to validation and weekend days. A station with |c_s − 1| > 0.15 [lab convention] is dropped from the speed term (kept for flow). Scaled speeds are used **only** in the NRMSE_v terms (J, P1); every event-layer quantity uses raw speeds, so the real references stay those of the corridor analysis. c_s at Pioneer Tr and Old Shakopee Rd is reported; if either |c_s − 1| > 0.05, P2–P5 are also reported with the real speeds scaled (not gated). **No detector-bias parameter is fitted** (a per-group offset is collinear with the group v_f in free flow).

### 3.3 Inputs

**3.3.1 Upstream boundary.** Fit-layer 5-min flow of the Minnetonka Blvd station (both lanes).

**3.3.2 Metered-ramp inflow: the passage-vs-balance rule (fixed now; calibration days only).** For each metered ramp o whose merge lies in a link that can be closed (both bounding stations flow-valid that day, every other element of the link class M):
- balance-derived inflow B_o = q_down + Σ(measured exits in the link) − q_up − Σ(other measured entrances in the link) + ΔN/Δt, with ΔN from §3.3.4;
- daily ratio ρ_o,d = Σ passage / Σ B_o over **05:00–23:00**, and separately over **15:00–19:00**;
- **rule:** if the median over calibration days of |ρ_o,d − 1| exceeds **0.10** in either window, ramp o replays the **balance-derived inflow** (15-min, storage-corrected, clipped at ≥ 0, held over its three 5-min bins); otherwise it replays its Passage detector. At least 8 calibration days with a closable link are needed; otherwise the ramp keeps Passage and is listed as "unchecked" (E6 Bren Rd is unchecked by construction).
- The links used: E1 Minnetonka Blvd → T.H.7 (with X1, X2); E2 T.H.7 → Van Buren Way; E3 Van Buren Way → Excelsior Blvd (X3); E4 Excelsior Blvd → Lincoln Dr (X4); E5 Lincoln Dr → Bren Rd (X5); E9 Valley View Rd → S of Valley View Rd; E12 Highwood Ave → S of Highwood Ave (with the measured E10, E11); E13 Anderson Lakes Pkwy → Pioneer Tr (X12), or S of Highwood Ave → Pioneer Tr (X11, X12) when the Anderson Lakes station is invalid; E14 Pioneer Tr → Old Shakopee Rd (X13; the Old Shakopee Rd entrance E15 lies downstream of the Old Shakopee Rd station, so it does not bias this balance).
- **Reported for every metered ramp:** the median and IQR of ρ_o,d in both windows (calibration days; validation days are reported after validation for information only), and, for each ramp switched to the balance, the same ratio for its Queue detector as corroboration (the review found the Pioneer Tr Queue detector within −1.1 % to +1.8 % of the 15-min balance). A balance can also absorb a station-count error; where the Queue detector does not corroborate within 5 %, the switch is still applied and flagged "station error not excluded".
- A ramp on the balance makes its link balance-closed: the link leaves the conservation check (§3.4) and its downstream station leaves the flow terms (§4.2).
- **Sensitivity (reported, not gated):** J and P1–P9 at the frozen parameters with Pioneer Tr replaying its Queue detector instead (no refit).

**3.3.3 Freeway-to-freeway merges (E7, E8, E10, E11).** They replay their measured Merge counts as d_o into an unmetered origin. **Disclosure:** on days when B's queue reaches them, these counts are **served (capped) flows, not demand**. The coarse data-fact indicator says the queue reached Highwood Ave (just upstream of the I-494 merges) on 37 of 38 Wednesdays (97 %) with a congested Pioneer Tr, and the I-494 merges carry about 38 % of the PM inflow between Valley View Rd and Pioneer Tr. Calibration therefore replays served flows. **Demand reconstruction for counterfactual runs is a separate later protocol** (§7 R2).

**3.3.4 Class-B elements (15-min balances; fixed now).** For a link from station u to station d with one unknown element y and measured entrances E and exits X:
- stored vehicles N(t) = ℓ · [K_u(t) + K_d(t)] / 2, with K the station density over all lanes (occupancy × 5280 / field length, converted to veh/km) and ℓ the link length;
- unknown entrance: y = q_d + ΣX − q_u − ΣE + ΔN/Δt; unknown exit: y = q_u + ΣE − q_d − ΣX − ΔN/Δt; Δt = 15 min, ΔN from the 5-min densities at the start and end of the bin;
- clipped at ≥ 0; the clipped volume is reported per element and day; a day is excluded if any element's clipped volume exceeds 2 % of its daily total (§3.5 E1).

| Element | Link (u → d) | Other elements in the link |
|---|---|---|
| X6+X7 (T.H.62 WB + EB, lumped at km −2.549) | Bren Rd → T.H.62 | E6 (Passage), E7 (Merge) |
| X9 W 78th St | S of Valley View Rd (3 lanes) → I-494 (3 lanes) | none |
| X10 I-494 EB | I-494 (3 lanes) → Highwood Ave | none |
| E15 Old Shakopee Rd | Old Shakopee Rd → T.H.101 | X14, X15 |
| E14 Pioneer Tr (if §3.3.2 switches it) | Pioneer Tr → Old Shakopee Rd | X13 |

The lumped T.H.62 sink leaves the mainline at its first element (km −2.549); the data cannot split it. The storage term is an approximation: during B onset and recovery the Pioneer Tr balance carries an error, reported as the share of its daily inflow in bins with |ΔN/Δt| > 10 % of the balance.

**3.3.5 Exit split ratios (fixed now).** β_e(t) = e(t) / F_e(t), with F_e the measured flow **arriving at the diverge**, taken from one reference station with **no entrance between it and the exit**:
- downstream form (preferred): F_e = q_d + e + Σ(other exits between e and d);
- upstream form (fallback, when the downstream station is invalid that day): F_e = q_u − Σ(exits between u and e);
- if neither form is available that day, the day is invalid (§3.5 E1);
- the assignment is the table in §1.2; the build asserts it. The plain upstream-station denominator is never used, and no reference path may contain an undetected entrance (E15).
- β is computed on 5-min bins, smoothed with a centred 3-bin moving average, clipped to [0, 1], and carried forward from the last bin with F_e ≥ 300 veh/h in bins where F_e < 300 veh/h. Class-B exits use their 15-min balance and are held over 15 min.
- Build check (calibration days): Σ_t β_e F_e Δt equals the measured daily exit volume within 1 % for every measured exit; the Anderson Lakes Pkwy fallback share is reported (expected high: 5424 dead on 43/52 Wednesdays per the review).

### 3.4 Conservation check and station flow reliability (calibration days decide; fixed now)

- **Closed links:** both end stations flow-valid and every element between them class M (after §3.3.2). Balance-closed links are listed and not checked.
- **Statistic:** e_link,d = |Σ(inflow − outflow)| / Σ inflow over 05:00–23:00.
- **Detector-fault rule (calibration days only, before any fit):** a closed link with e > 3 % on more than 20 % of calibration days is systematic. Its downstream station is marked **flow-unreliable** (dropped from the flow terms and as a balance or β reference; its speed stays), the link is merged with the next one, and the merged link is re-tested with the same rule until none is systematic. The frozen classification, link by link with its e distribution, goes to the pre-calibration facts.
- **Day rule (both sets):** after the classification, a day is excluded if any remaining closed link has e > 5 %.
- Counts of checkable links per day, and of excluded days per set, are reported.

### 3.5 Day exclusions (both sets; same rules; counted per set and reason)

| ID | Rule |
|---|---|
| E1 data | Fit-layer validity fails for: the upstream boundary station; any class-M entrance or exit detector; any station used in a class-B balance or as a β reference that day (with the fallbacks of §3.3.5); or fewer than 80 % of the 15 interior stations are speed-valid; or a class-B element clips > 2 %; or a closed link fails the §3.4 day rule. |
| E2 upstream boundary | The Minnetonka Blvd station (event layer, raw speed) is below 45 mph in more than 5 % of its valid 05:00–23:00 bins. |
| E3 downstream spillback | The T.H.101 station (event layer) is below 45 mph for ≥ 3 consecutive 5-min bins within 05:00–23:00. Spillback from beyond T.H.101 is outside the model. |
| E4 weather proxy | On ≥ 50 % of the speed-valid interior stations, the median speed of the station's free-flow bins (06:00–20:00, occupancy < 10 % and flow ≤ 1,200 veh/h/lane) is ≥ 8 mph below that station's median of the same statistic over the usable calibration days [thresholds: lab convention]. Weather is a held-out test condition (D2.3.1), not plant realism. Optional later cross-check against NOAA daily records [VERIFY source] is reported only. |

**Stop rules (checked before calibration; no rule is relaxed):**
- fewer than 18 usable calibration days → stop and report to the author;
- E2 removes more than one third of either set's real-B-active days → stop and report;
- E3 or E4 removes more than 25 % of either set → stop and report (the author decides on extending the stretch past T.H.13, on new data, or on stopping).

The exclusions apply identically to every real reference statistic of §5 and must apply to the gate's day library (§7 R9).

### 3.6 Pre-calibration data facts (computed after the commit and before calibration; committed as `metanet_precal_facts.json` before the first CMA-ES evaluation)

Decisions use calibration days only. Validation-day statistics are real-side counts needed for §5.2 and the exclusion counts; no model is run.

| ID | Fact |
|---|---|
| F1 | Element table, lane table, cell table and merge log (must equal §1). |
| F2 | Per-set usable days and exclusions by reason (E1–E4), with date, real-B-active status and demand half/quartile. |
| F3 | **Upstream boundary (E2):** count of congested-boundary days per set and in all 52; the 2 × 2 table (boundary congested × real B active) with Fisher's exact two-sided p; dates. |
| F4 | Ramp-source table (§3.3.2), with ratios, Queue-detector corroboration and the resulting replay source per ramp. |
| F5 | Conservation link table and flow-reliability classification (§3.4). |
| F6 | Lane screen and c_s table (§3.2.3–3.2.4). |
| F7 | B-mechanism diagnostic outcome (§1.6). |
| F8 | Real drop on **calibration** active days: median r, IQR, 95 % percentile bootstrap CI (seed 7,190,094); the share of days with r ≥ 1; Q_dis per lane; r_cap (§5.5). |
| F9 | Real queue extent at B on calibration active days (§5.4 P7 rule): distribution, and the exits and merges inside it. |
| F10 | Real per-pair episode counts over the whole stretch on calibration days (corridor rule). |
| F11 | Real-side minimum evidence on validation days (§5.2): n_val, n_A, n_H, half sizes. |
| F12 | Freeway-to-freeway share of B's 15:00–19:00 inflow (calibration median); per merge, the share of B-active days on which the station just upstream of it is below 45 mph in ≥ 30 % of episode bins. |
| F13 | Upstream clip: share of days and of 15:00–19:00 minutes with N of I-394 or S of I-394 below 45 mph (context for the boundary demand). |
| F14 | Configuration-to-data audit (§3.7). |
| F15 | The weather-proxy and holiday strata. |

### 3.7 Configuration-to-data audit

The geometry, lanes, field lengths and storage come from the current IRIS configuration, applied to 2023 data. For every detector of the stretch, report the number of 2023 days on which it appears in the cached `_detectors.json`.
- Absent on every day → treated as not existing in 2023: an exit becomes class B (known: 7110, W 78th St); a Queue detector affects only the later demand reconstruction (known in the stretch: 3679 T.H.7 EB, 3670 one of Lincoln Dr's two).
- Absent on some days → those lane-days are invalid (E1).
- Within-year steps (reported): per lane, a monthly median 05:00–06:00 speed step > 10 % makes that lane speed-invalid in the affected months; per closed link, a monthly median e step > 3 % is reported.
- Any lane count or field length contradicted by 2023 data is a disclosed deviation.

---

## 4. Estimation (calibration days only)

### 4.1 Parameters, constants and bounds

**Fitted (14):** per group G1–G3: v_f, ρ_cr, a (9); shared: τ, ν, κ, δ_m, φ (5). EXIT branch (§1.6): + C_x (15).

**Fixed:** T = 5 s; ρ_max = 180 veh/km/lane; v_min = 7.4 km/h; Q_o = 2,200 veh/h per ramp lane; c = 1 in the B cells; no speed-limit term.

| Parameter | Bounds | Source and status |
|---|---|---|
| v_f (each group) | 80–150 km/h | must exceed observed low-density speeds (review: G3 median 117–120, p90 127–129 km/h at 300–900 veh/h/lane); upper 150 as in Chan, Raghavan & Wu 2026 Table I [VERIFY]; Poole & Kotsialos 2016 used 80–130 [VERIFY] |
| ρ_cr (each group) | 15–45 veh/km/lane | Kotsialos et al. 2002: 27.7–35.9 [VERIFY]; Zhao, Roncoli & Yildirimoglu 2025 limits 15–40 [VERIFY] |
| a (each group) | 1.0–3.5 | calibrated 1.87–2.50 in Hegyi et al. 2005, Kotsialos et al. 2002, Zhao et al. 2025 [VERIFY] |
| τ | 10–60 s | lower = 2T (§2.5); Kotsialos 18 s; Poole 11.4–22.7 s; Zhao real-data fit 45.5 s [VERIFY] |
| ν | 5–90 km²/h | Kotsialos 60; Poole 40–57; Zhao real-data 87.8 [VERIFY] |
| κ | 5–60 veh/km/lane | Kotsialos 40; Poole 22–29; Zhao 6.6–8.0 [VERIFY] |
| δ_m | 0–4 | Kotsialos 0.012; Poole ≤ 0.093; Zhao up to 4.0 at its bound [VERIFY] |
| φ | 0–4 | Kotsialos 2.2; Poole at its lower bound [VERIFY] |

Literature status: the values above were reported by the review's literature lens; the author has not read these sources in full ([VERIFY]). Wang et al. 2022 (TR-C) was not read by anyone and is not cited as a source. Bounds are frozen at the commit and **never widened after a fit**. A parameter within 1 % of the bound range of either bound at the frozen optimum is reported as **bound-active** next to the identifiability flags; it does not trigger a refit.

### 4.2 Error definitions (used by J and P1)

For a variable x ∈ {q (veh/h), v (km/h)}, a day d and a set S of valid (station, 5-min bin) pairs:

**NRMSE_x(d, S) = sqrt( (1/|S|) Σ_{(s,b)∈S} (x̂_{s,b} − x_{s,b})² ) / ( (1/|S|) Σ_{(s,b)∈S} x_{s,b} )**

x̂ = model value at the station (§1.5), x = fit-layer real value (speeds scaled by c_s, §3.2.4). Pooling is over the station-bins of that day (no per-station averaging); normalisation is always by the mean of the real data over the same pairs. A (day, set) with fewer than 100 valid pairs is not scored (counted).

**Sets:**
- **S_q,d (flow):** flow stations of §1.2 (interior, flow-valid, not balance-closed, not flow-unreliable) × 05:00–23:00.
- **S_v,d (speed, whole day):** interior speed-valid stations not dropped by §3.2.4, plus T.H.101 × 05:00–23:00, bins with K > 0.
- **Q_A (queue area):** the speed-valid stations with 0.37 ≤ km ≤ 7.20: S of Valley View Rd, I-494, Highwood Ave, S of Highwood Ave, Anderson Lakes Pkwy, Pioneer Tr, Old Shakopee Rd. Chosen from the corridor analysis and the data facts (B and its queue reach), disclosed, not tuned further.
- **S_c,d (congestion term):** Q_A × W_d, where W_d = 15:00–19:00 ∪ [onset − 30 min, end + 30 min] of every real B episode of day d (event layer). On days without a real B episode W_d = 15:00–19:00, so spurious congestion in the queue area is penalised as well as missed congestion.

### 4.3 Objective

**J_d = 0.25 · NRMSE_q(d, S_q,d) + 0.25 · NRMSE_v(d, S_v,d) + 0.5 · NRMSE_v(d, S_c,d); J = mean of J_d over the usable calibration days.**

Why this weighting: free flow dominates the whole-day sets (the review measured a median 2.4 % of station-bins below 40 mph), and with replayed inputs the flow term is governed mainly by conservation, while the speed equation carries most parameters (argued in Chan et al. 2026 [VERIFY]). The congestion term (speed in the queue area during B's active periods and the PM window) keeps CMA-ES from trading bottleneck fidelity for free-flow fit. Weights and windows are fixed now and not tuned. The v0 objective (0.5/0.5 whole day) is reported at the frozen optimum.

### 4.4 Optimiser (settings frozen; record the pycma version)

- pycma CMA-ES in the normalised space [0, 1]^14 ([0, 1]^15 in the EXIT branch, with λ = 12), log-scaled for τ, ν, κ and linear otherwise; bound handling by pycma's BoundTransform [VERIFY that it is the default in the installed version].
- **8 restarts, seeds 7,190,011–7,190,018.** Restart i: initial mean drawn uniformly from [0.25, 0.75]^14 with its seed; σ0 = 0.25; popsize λ = 4 + ⌊3 ln 14⌋ = 11; **4,000 evaluations**; tolerance-based stops (tolfun, tolx, tolstagnation and similar) disabled, so the budget is the only stopping rule.
- **Convergence (calibration J only):** report per restart the final J, final σ, the covariance condition number and the relative J improvement over the last 20 % of evaluations. If the best restart improved by > 1 % in that window, **all** restarts are continued once, on the same seed streams, to 8,000 evaluations before anything else is run; both results are logged and the continued one is frozen.
- The restart with the lowest J is the **nominal plant**, frozen with all its settings in `metanet_calibration.json` and committed **before any validation run**.
- Any other optimiser setting counts as a new calibration: it is logged in the ledger and never replaces this one.

### 4.5 Identifiability (reported, not gated)

- **Restart spread:** restarts with J ≤ 1.02 · J_best. If ≥ 3 qualify, report for each parameter the range of those restarts divided by its bound width (normalised coordinates); otherwise "not assessable". No coefficient of variation is computed.
- **Profiles** for v_f(G3), ρ_cr(G3), τ, ν, κ, δ_m, φ: 9 equally spaced points across each bound (normalised); at each point the parameter is fixed and the other 13 (14 in the EXIT branch) are re-optimised by CMA-ES warm-started at the frozen optimum (σ0 = 0.1, λ = 11, 600 evaluations), **seeds 7,190,030–7,190,092** (seed = 7,190,030 + 9p + j for parameter p = 0…6 in the order listed and point j = 0…8). Under-optimisation can only make a profile look less flat; this is stated in the report.
- A parameter is flagged **non-identifiable** if its profile J stays ≤ 1.02 · J_best over ≥ 50 % of its bound width, or its restart range is ≥ 50 % of its bound width, or it is "not assessable".
- Also reported: the capacity of each group v_f ρ_cr e^{−1/a} (same spread and profile-derived range), the v_f–ρ_cr correlation within each group across near-best restarts, bound-active parameters, and per-group median (model − detector) speed over 05:00–06:00.

### 4.6 Plant ensemble (no hidden variants)

- **Admissible:** any restart with J ≤ 1.02 · J_best that also passes N0 and P1–P9 on its own (validation days used **as a filter only**, never to fit).
- **Ensemble:** the nominal plant plus at most **2** admissible members, the ones farthest from it in (τ, ν, κ, δ_m, φ), each normalised by its bound width. Chosen before any gate run; frozen and listed with their J and P-results. An empty set is reported as such.
- The gate uses the ensemble by the rule in §7 R5.

### 4.7 Per-day bottleneck capacity factor (stochastic element for the gate; calibration days only)

**Definition.** c multiplies ρ_cr (hence the capacity) of the B cells 31–33 and everywhere ρ_cr appears in them (FD, origin supply term). c = 1 is the frozen plant.

**Estimator (fixed now).** With every §4.1 parameter frozen, for each usable calibration day d and each grid value c ∈ {0.800, 0.805, …, 1.200} (81 values), run the replay and record A_d(c) (model B active, §5.1) and L_d(c) = NRMSE_v(d, S_c,d).
- **Real-B-active day:** let C_d = the grid values at which the model has a B episode overlapping a real B episode (±60 min). If C_d is not empty, **ĉ_d = argmin_{c ∈ C_d} L_d(c)** (ties → the value nearest 1); this is an exact observation. If C_d is empty (the model cannot break down that day even at c = 0.80), the day is "not reproducible": it is excluded from the distribution and counted; if more than 20 % of the active calibration days are not reproducible, this is flagged to the author.
- **Real-inactive day:** right-censored at **c_low,d** = the smallest grid value such that the model is not B-active at that value or any larger one. If the model is B-active even at 1.200, the day is censored at 1.200 and flagged.
- Days on which A_d(c) is not monotone in c are reported.

**Distribution F̂.** The Kaplan–Meier product-limit estimate of the distribution of c from the exact observations and the right-censored values (ties: events before censorings). If the largest observation is censored, the remaining mass is placed at 1.200 (high-capacity days; the conservative placement for breakdown frequency) and disclosed. KM assumes censoring independent of c; reported checks: the Spearman correlation of ĉ_d with daily boundary demand (active days, with a bootstrap CI, seed 7,190,094), and of ĉ_d with the real Q_dis on heavy days (expected positive).

**Reported alongside:** the median of F̂ and its mass below and above 1; a censored-normal (Tobit) maximum-likelihood fit (μ, σ) as a parametric check; the CV of the real Q_dis on heavy calibration days against the spread of F̂.

**Use:** P1–P9 run at **c = 1**. Reported only: P3 and P6 with c drawn per validation day from F̂ (200 draws per day, seed 7,190,095): the expected agreement and the Brier score of the model's P(B active) against the real classification, deterministic vs stochastic. The gate samples F̂ per day and seed under the rules in §7 R3. F̂ is re-estimated for each ensemble member and for F1 if used.

### 4.8 Reported calibration-day diagnostics (before any validation run)

Each J term separately; the v0 whole-day J; the model's Q_dis and r at B against the real values on the same calibration days; the B-active agreement on calibration days; clip counts; step-halving; origin misfits; the agreement of the best daily-demand threshold classifier on calibration days (a stylised ceiling for P3, see §9.1).

---

## 5. Plant gate (validation days; real data as the reference; fixed now)

The frozen plant is driven by each usable validation day's measured inputs in replay mode, at c = 1. **PASS requires N0 and all of P1–P9.**

### 5.1 Model-side event detection (identical to the real side)

- Model 5-min speed and flow are read at every real station's km (§1.5) and **masked by that real station-day's event-layer validity**, so model and real use the same valid station pairs.
- The corridor-protocol rule is applied **unchanged** to both: consecutive valid stations ≤ 3 km apart; v_u < 40 mph and v_d − v_u ≥ 20 mph in ≥ 5 of 7 consecutive bins; onset = the first bin of the first qualifying window; episodes separated by < 30 min are merged; episode end = the last covered bin.
- **"B active"** (model or real) = at least one episode at the pair (Pioneer Tr, Old Shakopee Rd), AM or PM.
- **Episode matching:** every real B episode is matched to the model B episode with the nearest onset within ±90 min, one-to-one (smallest |Δonset| first).
- **Heavy matched day:** the day's longest real B episode is ≥ 30 min, is usable by the C4 estimator, and is matched to a model B episode that is also ≥ 30 min and C4-usable.
- **Q_dis, r:** the C4 block of `analyse_corridor`, applied unchanged to the 5-min flow at the Old Shakopee Rd station (2 lanes), real and model alike.

### 5.2 Minimum evidence and outcomes

Checked on **real data only**, after §3 cleaning and **before the model is run on any validation day** (F11):
- n_val (usable validation days) ≥ 16, so that each demand half has ≥ 8 days (P6);
- n_A (usable validation days with real B active) ≥ 8 (P1c, P2, P3, P4);
- n_H (real B active with a longest episode ≥ 30 min, C4-usable) ≥ 6 (P5, P7, P9).

If any minimum fails, the plant gate is **INCONCLUSIVE**: not run, never PASS, no F1, reported to the author with the counts. Extending the day set (for example 2023 Tuesdays and Thursdays) needs new data and is a separate addendum approved by the author with its request count, using the frozen parameters with no refit; both outcomes would be reported. Rough expectation (an estimate, not a computed fact): with 24 validation Wednesdays, about 20 usable, and a B-active share near 0.45, n_A ≈ 9 and n_H ≈ 8, so INCONCLUSIVE is a realistic outcome.

**When the real minima are met, a model-dependent set that is too small is a FAIL** (the model did not reproduce enough of the real events), never INCONCLUSIVE: P2 needs n_2 ≥ 6, P4 needs ≥ 6 matched episodes, P5/P7/P9 need ≥ 6 heavy matched days, P9(2) needs ≥ 5 days with model excess.

### 5.3 Gated checks

| ID | Check | Qualifying set (denominator) | Criterion |
|---|---|---|---|
| **N0** numerics | Density and upper-speed clipping per validation day | all usable validation days | ≤ 1 % of cell-steps on every day |
| **P1a** flow fit | NRMSE_q(d, S_q,d) | all usable validation days | median ≤ **0.10** |
| **P1b** speed sanity | NRMSE_v(d, S_v,d) | all usable validation days | median ≤ **0.20** (a sanity floor; not discriminating, §5.4) |
| **P1c** queue-area speed | NRMSE_v on Q_A × [onset − 30, end + 30] of the real B episodes, model vs two day-agnostic nulls N1, N2 (§5.4) | the n_A real-B-active days | vs N1: upper bound of the 95 % bootstrap CI of the median paired difference (model − N1) **< 0**; vs N2: median paired difference **< 0** |
| **P2** where | Of the model episodes overlapping (±60 min) a real B episode, the one with the earliest onset is at pair B | n_2 = real-B-active days with at least one overlapping model episode at any pair (real-B days without one count in P3/P4, not here) | ≥ **80 %** of n_2, and n_2 ≥ 6 |
| **P3** whether | Model "B active" = real "B active" | all usable validation days | agreement ≥ **75 %**; confusion matrix and Wilson CI reported |
| **P4** when | \|model onset − real onset\| over matched episodes | matched episodes | median ≤ **15 min**, and ≥ 6 matched; unmatched episodes counted and reported |
| **P5a** discharge | D_i = Q_dis,model,i / Q_dis,real,i − 1 | heavy matched days | \|median D_i\| ≤ **0.05** (two-sided) |
| **P5b** drop not exaggerated | median of r_model,i | heavy matched days | ≥ **L_r**, the lower limit of the 95 % percentile bootstrap CI (2.5th percentile, i.e. the lab's single two-sided CI convention; 10,000 resamples of days, seed 7,190,093) of the **real** median r on the same days (one-sided) |
| **P6** narrow band | B-active counts in the lower and upper half of daily demand (§5.4) | all usable validation days | (a) \|M_h − R_h\| ≤ k_h in both halves (binomial tolerance at the realised n); (b) if the real gradient > 0, the model's gradient > 0 and (c) ≥ 0.5 × the real gradient |
| **P7** queue extent and duration | (a) duration of the matched B episode; (b) queue extent (§5.4) | heavy matched days | (a) median \|dur_model − dur_real\| ≤ **30 min**; (b) model extent = the real extent station or an adjacent speed-valid station on ≥ **70 %** of the days |
| **P8** no spurious bottleneck | Model episodes at pairs other than B (§5.4) | all usable validation days | (i) every pair: model episode-days − real episode-days ≤ **2**; (ii) days with ≥ 1 spurious model episode ≤ **max(2, ⌈0.10 · n_val⌉)** |
| **P9** D-check (model side) | (1) peak 15-min counted flow / Q_dis; (2) plateau / excess duration (§5.4) | heavy matched days; (2) on days with model excess > 0 | medians: (1) ≤ **1.05**; (2) ≥ **1.2**, with ≥ 5 qualifying days |

Threshold status: P1a, P1b, P2, P3, P4, P5a, P7, P8 and the 1 % in N0 are **[lab convention]** (P1a: see §5.4 for its context). P5b, P6 and P1c are defined relative to the real data or to nulls. P9 follows the gate draft §1 D-check and supersedes its wording (gate T1 refers to P9).

**Why P5 is one-sided on the drop and two-sided on discharge.** A plant with more drop than the data support inflates the gain from preventing breakdown, which inflates the headroom H and risks a false GO. Too little drop understates that gain, which can only make a KILL more likely (conservative). The discharge level sets when and how long B is active in both directions, so it is two-sided. The breakdown-prevention prize is the H1 mechanism; the queue-spillback part of any prize is covered by P7.

### 5.4 Definitions behind the table

**P1 context (literature lens; [VERIFY], the author has not read these in full).** No comparable out-of-sample METANET fit threshold was found. The fits the review read are in-sample, on short windows, with other metrics: Poole & Kotsialos 2016 report per-station speed errors of about 6–7 % on the calibration day and much larger errors on other days; Chan, Raghavan & Wu 2026 report in-sample MAPE of about 28–35 % for flow and 5–28 % for speed; Zhao, Roncoli & Yildirimoglu 2025 report a speed RMSE of 18.6 km/h and a flow RMSE of 832 veh/h on three lanes. Kotsialos et al. 2002 report no numerical fit error. These are context, not thresholds. Therefore:
- P1a's 0.10 is a lab convention; for scale, the day-agnostic median-profile null scored 0.123 in the review's check (§0.5), so P1a asks the replay plant to beat a profile that ignores the day.
- P1b's 0.20 is kept only as a sanity floor: a never-congesting predictor scored 0.126, so P1b cannot tell good plants from bad ones.
- P1c carries the discriminating fit test, in the queue area while B is active.

**P1c nulls** (built from usable calibration days only, on scaled speeds): **N1** = per station, the median of all 05:00–23:00 speeds ≥ 45 mph (a plant that never congests); **N2** = per station and 5-min bin, the median calibration-day speed (the typical day). Per real-B-active day, D_d = NRMSE_v,model − NRMSE_v,null on the same pairs. The bootstrap (10,000 resamples of days, seed 7,190,093) gives the CI of median D. N1 must be beaten with confidence; N2 must be beaten on the median (the CI is reported), because a mechanistic model driven by the day's inputs should at least match the typical profile, while requiring a CI against N2 at n_A ≈ 9 would make a false FAIL likely.

**P6 halves and tolerance.** Daily demand = the measured 05:00–23:00 total at the Minnetonka Blvd boundary (an input, identical for model and real). Sort the usable validation days by it; lower half L, upper half U (the median day goes to U if n_val is odd). M_h, R_h = model and real counts of B-active days in half h, n_h its size. Tolerance: p̃_h = (R_h + 0.5)/(n_h + 1); **k_h = the smallest integer k with P(|X − round(n_h p̃_h)| ≤ k) ≥ 0.9747 for X ~ Binomial(n_h, p̃_h)** (0.9747 = 0.95^{1/2}, so a plant that reproduces the breakdown probability in both halves fails (a) with probability ≈ 5 % in this stylised model). Gradient = M_U/n_U − M_L/n_L (model) and R_U/n_U − R_L/n_L (real). If the real gradient is ≤ 0, (b)–(c) are not applied and the report says the narrow band is absent in the validation data. Why halves, not quartiles: at n_q = 5–7 per quartile the same rule (at the per-quartile level 0.95^{1/4}) gives tolerances of 2–3 days, up to ±60 pp, so a quartile test has almost no power; at n_h = 8–12 it gives 2–4 days (about ±25–35 pp; computed for every possible R_h before this commit). This is still weak, and it is disclosed as such: (a) guards the level, (b)–(c) guard the demand dependence. Per-quartile shares (model and real, with exact binomial CIs) and the same table keyed on the Bren Rd flow (comparable with corridor analysis v2) are reported.

**P7 queue extent.** A station is congested if its event-layer speed is < 40 mph for ≥ 15 consecutive minutes overlapping the episode window [onset, end]. The extent is the most upstream congested station in the unbroken run of congested stations upstream of B, starting at Pioneer Tr; event-invalid stations are skipped and do not break the run; the model uses the same mask. Duration = end − onset + 5 min of the matched B episode. The signed median difference of duration is reported too.

**P8 spurious episodes.** The corridor rule runs on all event-valid pairs of the stretch (model and real, same mask). A model episode at a pair P ≠ B is **spurious** if the real data have no episode that day at P or at any pair sharing a station with P. Pair B itself is judged by P2–P4. Reported: per-pair model-minus-real counts and the list of spurious episodes (pair, onset, duration).

**P9 D-check.** On each heavy matched day:
- **Arrivals at B**, A_B(t), in 15-min bins: boundary flow + every replayed entrance inflow up to and including Pioneer Tr − every measured exit flow up to and including X13, each shifted by its free-flow travel time to the Old Shakopee Rd station at the frozen group v_f. It is an input series, the same for both sides; on clipped days it is a lower bound on demand (§3.3.3).
- (1) S1 = the maximum 3-bin rolling 15-min model flow at the Old Shakopee Rd station in [onset − 60 min, end] divided by the model's 2-lane Q_dis.
- (2) Plateau = the longest contiguous run of 5-min bins containing the onset with model flow ≥ 0.95 × model Q_dis; excess = the minutes with A_B > model Q_dis; S2 = plateau / excess, on days with excess > 0 (days with excess = 0 are counted).
- The real-data counterpart is reported only, as a lower-bound form (§5.5): with served counts at merges inside the queue, the real excess is unobservable, so "the real data show this" is not claimed. The gate draft's absolute rule (plateau ≥ 1.2 × excess) applies to the plant only.

### 5.5 Reported, not gated

- MAPE and RMSE (km/h, veh/h) on the whole-day and queue-area sets; per-station errors; the null scores.
- Paired differences r_model − r_real with a bootstrap CI; the real median r and CI per set (calibration, validation, pooled 52 days) next to the model's. If the model's median r lies above the validation CI upper bound, the plant is labelled "drop under-reproduced; conservative for breakdown-prevention gains" in every later result, and the author is told before the gate runs.
- **r_cap** = Q_dis / (maximum 3-bin rolling 15-min flow in the 60 min before onset), the corridor protocol's `capacity_15min` window, for model and real; disclosed limitation: a maximum over noisy detector bins biases the real r_cap downwards relative to smoother model output. The corridor-v2 ratio of medians (1,850.4 / 1,938.0 ≈ 0.955) is unpaired. Per-day real r outside [0.8, 1.2] is listed and kept (medians are used).
- Real D-check, lower-bound form: (a) the real S1; (b) the growth of stored vehicles between the boundary and B during queue growth, from served arrivals and the measured outflow (§3.3.4 storage), and whether the real data meet plateau ≥ 1.2 × excess with served arrivals.
- Upstream congestion-front speed from onset times at successive event-valid stations inside the extent (an estimate needs ≥ 2 stations; n/a with fewer than 5 estimates). **R-b (internal stop-and-go wave speed) is n/a** at 5-min / ~1 km resolution; this limits any wave-based VSL claim, and the SUMO confirmation must test it.
- Exposure to blocking, model vs real: for each exit and freeway merge between km 1.7 and B, the share of episode minutes with the nearest upstream station congested.
- Excess vehicle-hours between the extent station and B, model/real ratio, 15:00–20:00.
- Origin misfits and clipped ramp volume (§2.3); clip counts; step-halving; the T.H.101 measured-density boundary as a sensitivity (frozen parameters, no refit); the Pioneer Tr Queue-detector replay sensitivity (§3.3.2).
- c_s at the B stations and, if needed, P2–P5 with scaled real speeds (§3.2.4).
- Stochastic-capacity P3/P6 and Brier scores (§4.7).
- Holiday-adjacent stratum: P1, P3, P4 separately.
- **Weekend days:** the same metrics, reported only.
- Validation-day ramp ratios (§3.3.2), for information.
- Every P statistic with its n and a 95 % interval (percentile bootstrap over days for medians, Wilson for shares).

### 5.6 P-T transfer to 2024 (defined here; executed under the gate protocol)

After the gate protocol is committed and 2024 is opened, and **before any controller is run or tuned**, the frozen plant(s), with no refit and no change of parameters, inputs or cleaning rules, are driven in replay by the 2024 days the gate will use, after the §3.7 audit on those days. Criteria: N0, P1a and P3 with the §5.3 thresholds. FAIL → the plant is not valid for the 2024 gate; the gate does not run and the author is told. 2024 data may never be used to refit or reselect this plant. The outcome is logged either way.

---

## 6. Failure handling (fixed now)

### 6.1 F1: the single pre-registered structural fallback

*Our own METANET adaptation of the two-capacity, memory-based capacity-drop idea of Srivastava & Geroliminis 2013 (TR-C 30:161–177) [VERIFY: read by the review, not by the author]. The source is a first-order LWR/Godunov model, not METANET; this adaptation is ours and is disclosed as such.*

- **Cells:** only the B cells 31–33 (§1.4). No other cell changes.
- **Memory state:** m_i(k) ∈ {0, 1}, m_i = 0 at 04:00 every day. After each density update: m_i(k) = 1 if ρ_i(k) > ρ_cr,i, or if m_i(k−1) = 1 and ρ_i(k) > η · ρ_cr,i; otherwise 0. (The name m avoids a clash with the exit flow s.)
- **Switch:** while m_i = 1, cell i uses ρ_cr,i^F1 = (1 − Δ) · ρ_cr,i everywhere ρ_cr appears (FD, supply term). With v_f and a unchanged, its capacity falls by the factor (1 − Δ).
- **New parameters (2):** Δ ∈ [0, 0.15] (about 3 × the corridor's 75th-percentile drop, 1 − 0.952 ≈ 4.8 %; [lab convention]); η ∈ [0.6, 1.0] (release hysteresis; [lab convention]).
- **No per-cell v_f and no other new freedom** (per-cell v_f at the merge cells would make P2 pass almost by construction).
- **Refit:** all 14 base parameters (+ C_x in the EXIT branch) plus Δ, η, jointly, from a cold start; same objective, days and settings as §4.4 with λ = 4 + ⌊3 ln 16⌋ = 12, **seeds 7,190,021–7,190,028**, 4,000 evaluations each, the same convergence rule; the best restart is frozen. Identifiability: restart spread and bound activity only (no profiles; disclosed). F̂ (§4.7) and the ensemble (§4.6) are re-derived for F1. The gate statistics use bootstrap seed 7,190,096.
- **Judged on** N0 and P1–P9 unchanged, on the same validation days. No validation-day result may inform any F1 choice: F1 is fully specified here.

### 6.2 After F1

If F1 also fails, see §0.3 (route stop; SUMO is an author decision). No criterion is relaxed. Both outcomes are logged.

### 6.3 Change rule

After the first validation evaluation, model or job code may change **only** to correct a deviation from this file's equations (§2) or data rules (§3). Each fix comes with a unit test, committed with the fix, that fails before it and passes after. Calibration, the plant gate and F1 (if used) are then re-run in full, with the original seeds, and **both outcomes are logged**. Any other change to the model, inputs, objective or criteria is a new protocol version, committed before it is run, with fresh optimiser seeds and a decision-log entry.

---

## 7. Requirements this protocol places on later protocols

| ID | Requirement (binding on the controlled-plant and gate protocols; to be restated there before any gate run) |
|---|---|
| R1 | **Controlled mode C.** Exogenous inputs identical across arms and seeds within a day: the mainstream origin; the 6 upstream metered ramps (their replay inflow; demand mode is unavailable upstream because Queue detectors 3679 and 3670 have no 2023 data); the class-B elements; the split ratios. The 4 controlled ramps take reconstructed demand (Queue-detector arrivals). Required before use: (a) the storage unit of the IRIS `storage` attribute confirmed [VERIFY] and storage in vehicles = storage × 0.3048 × storage lanes / s_jam, with s_jam from a cited source and a ±25 % sensitivity; (b) `max_wait` (240 s at all four controlled ramps) enforced for every arm through the same queue-override rule; (c) **P0 ramp-demand validity** per controlled ramp-day (\|Σ arrivals − Σ release\| ≤ 5 % of Σ release; reconstructed queue within [0, 1.2 × storage] in ≥ 95 % of bins), with a fallback if fewer than 80 % of ramp-days are valid; (d) a **mode-equivalence check**: mode C with each controlled ramp's meter rate set to its replay inflow must pass N0 and P1–P9 with the §5.3 thresholds. Origin queues are unbounded and count in the delay metric; vehicles are never dropped. |
| R2 | **Freeway-to-freeway demand on clipped days.** The protocol must pre-register how demand at E7, E8, E10, E11 is generated on days when the merge lies inside a queue (for example an uplift fitted only on days when that merge is uncongested, or a draw from uncongested days at the same time of day), disclose it as model-imposed and not observed, and report gate results separately for days with and without the queue at the merges. Any H1 statement that true demand "can be reconstructed from upstream detectors" is limited to the upstream boundary and the metered ramps. |
| R3 | **Capacity factor.** Each gate day draws c_d from F̂ (§4.7) of the plant in use, from the gate seed. **No arm sees c_d**, the informed reference I included (it knows the true demand, not the true capacity). mpc_f, I_mpc and I_plan use the median of F̂ or their own fitted models; mpc_f's model is refitted on tuning-seed plant data generated with random c. The protocol states whether c is re-centred and reports a sensitivity with c fixed at 1. H2's capacity classes are quantiles of F̂. |
| R4 | **Drop cells.** The gate draft's CTM δ ∈ {0, 5, 10, 15} % cells and δ_field are replaced by cells defined on the **measured** drop Δ_drop = 1 − (the plant's median r on the validation heavy matched days, corridor estimator): primary = the frozen plant; sensitivity = a low-drop variant (the F1 switch with Δ set, negative if needed to cancel drop that the base dynamics produce, so that the measured Δ_drop equals 1 − the upper CI limit of the real r on those days, i.e. no drop if that limit is ≥ 1) and a high-drop variant (Δ_drop = 1 − L_r), each within ±0.5 pp, everything else frozen. A GO must also hold on the low-drop variant; a GO that appears only at a drop above the primary's is not a GO. |
| R5 | **Ensemble.** The GO/KILL decision is computed on the nominal plant; every arm is re-tuned on each ensemble member with the same budget and tuning days. A GO additionally requires H ≥ 10 % with the paired CI lower bound > 0 on every member; otherwise it is "plant-dependent" and not a GO. A nominal KILL with a member meeting the GO criterion stays a KILL, recorded as "plant-dependent KILL" with the parameter direction that flips it; it is never rescued. All per-member H values are logged. |
| R6 | **VSL (H2 and every VSL-using arm: mtfc_rm, specialist, the VSL-extended mpc_f).** Primary form and α_0 as in §2.8, sensitivity α ∈ {0.0, 0.2}; H2's T0 must pass under both response forms (Hegyi min form and the MTFC modified FD); H2's T2 and gate are run on the primary form with the variant reported; an H2 GO also needs the SUMO T0 to agree. A GO involving a VSL arm must keep the sign of H at α = 0.0 and 0.2, otherwise it is reported as α-sensitive and is not a claim. mpc_f never receives the plant's α or FD parameters. b_i applies only inside a declared VSL application area. Every VSL result states that the VSL response is assumed, not validated. |
| R7 | **P-T** (§5.6) runs before any controller on 2024 days. |
| R8 | **D-check.** Gate T1 refers to P9 of this protocol; the real-data version is a lower bound only and the absolute plateau rule applies to the plant. |
| R9 | **Exclusions.** E2–E4 (and the weather-proxy rule) apply to the real days of the gate's day library; weather days are a held-out test (D2.3.1). |
| R10 | **Corridor-analysis caveat.** A dated addendum to the corridor analysis (not an edit of committed results) records the counter-evidence to "metering limits the drop": Srivastava & Geroliminis 2013 report about 15 % at a U.S.169 northbound merge, of similar size with and without metering [VERIFY]; different direction, site and years, so it does not transfer directly to Pioneer Tr. |
| R11 | **Decision log.** The author records the D3.1 wording change (§0.4), the boundary deviation (§0.6 A2) and the split change (A3). |

---

## 8. Seeds, compute, outputs, statistics, logging

### 8.1 Seeds (approved block 7,190,000–7,190,999; this protocol uses only 7,190,000–099)

| Seeds | Use |
|---|---|
| 7,190,011–018 | base CMA-ES restarts (8) |
| 7,190,021–028 | F1 CMA-ES restarts (8) |
| 7,190,030–092 | profile re-optimisations (7 parameters × 9 points) |
| 7,190,093 | bootstrap of the base-plant gate statistics (P1c, P5b, all CIs) |
| 7,190,094 | bootstrap of pre-calibration real facts (F8, the §4.7 correlations) |
| 7,190,095 | capacity-factor draws for the reported stochastic P3/P6 |
| 7,190,096 | bootstrap of the F1 gate statistics |
| all others in 000–099 | unused; a re-run after a bug fix reuses the original seeds |

The model is deterministic given its inputs; the capacity grid (§4.7) uses no seed. No real day is used for timing: the timing test runs on synthetic inputs.

### 8.2 Compute

- CMA-ES and profile batches run as background jobs on **≤ 32 worker processes** (libsumo is not involved) under `vsl_lab/ops/guard.py` (CPU > 90 % for 2 consecutive minutes → pause rules; the 95 ± 3 °C thermal band with the `thermal.json` limits; decisions logged in the batch's `thermal.csv`). Before every batch: check machine resources and that the v6 sessions are idle (otherwise CPU load < 15 %). `export OMP_NUM_THREADS=1`; `venv314`.
- Cost (estimate, to be measured on synthetic inputs before the first run): 37 cells × 13,680 steps per model-day; one evaluation = up to 28 model-days. The base fit is 32,000 evaluations (64,000 with the continuation), the profiles 37,800, the capacity grid 81 × 28 model-days. If the measured timing projects more than 24 h of wall time for §4, the author is told before launch; the budget is never cut silently.
- Raw run files go under `/home/catalin/work/phd/vsl_lab_runs/day_pattern/metanet/` (ext4), never into the repo. Logs are tailed at most every 10 minutes.

### 8.3 Outputs

- `docs/lab/day_pattern/metanet_precal_facts.json` (§3.6), committed before the first CMA-ES evaluation;
- `docs/lab/day_pattern/metanet_calibration.json` (date lists, exclusions, element/cell tables, branch outcomes, frozen parameters and settings, convergence, identifiability, ensemble, F̂, all P results with n and intervals), committed in two stages: the freeze before any validation run, then the gate results;
- `docs/lab/day_pattern/metanet_calibration.md` (report, including the Appendix-A cross-references);
- ledger rows in `vsl_lab/runs/ledger.csv` for every batch, including failed and abandoned ones;
- code: `vsl_lab/plants/metanet.py` (model), `vsl_lab/data/metanet_inputs.py` (both cleaning layers, §3 rules), `vsl_lab/jobs/metanet_calibrate.py` (§4–§6).

### 8.4 Unit tests (`tests/test_metanet.py`, synthetic inputs only)

1. Mass conservation over the whole network including all origin queues: Σ inflows − Σ outflows − Δ(Σ ρ_i L_i λ_i + Σ w_o) = 0 to numerical tolerance, including a supply-limited ramp whose queue must drain to 0 once its merge cell clears.
2. CFL and τ ≥ 2T assertions at the bound corners; no negative speed and no density above ρ_max under a worst-case shock input.
3. Free-flow steady state is stationary.
4. Queue spillback: a capacity restriction produces a queue that propagates upstream and dissolves after demand falls.
5. Exit reproduction: on a free-flow replay with measured-style inputs, every model exit volume equals Σ β_e F_e Δt within 1 % over the day.
6. The no-VSL plant is bit-for-bit identical with the speed-limit extension disabled.
7. c = 1 in the B cells reproduces the frozen plant exactly; F1 with Δ = 0 reproduces the base plant.
8. F1 hysteresis: switch-on above ρ_cr and switch-off only below η ρ_cr.
9. The cell builder reproduces the §1.4 table and merge log from the configuration; the split builder reproduces the §3.1 date lists.
10. NRMSE and the corridor-rule wrappers give known answers on toy series.

### 8.5 Statistics conventions

Real days are the units; there are no simulation seeds to pair. Medians; one convention for comparisons (the median of paired differences, or of paired ratios − 1 for discharge); 95 % percentile bootstrap over days with 10,000 resamples; Wilson intervals for shares; exact binomial intervals for the P6 quartile shares. Gating uses the pre-registered point estimate, except where a CI limit is itself the criterion (P1c vs N1, P5b's L_r). CIs are always reported, so that a narrow PASS or FAIL can be read as such. **Validation days are never used for fitting** (they filter the ensemble, §4.6, and nothing else).

### 8.6 Order of work

1. Author confirmations (§0.6); commit this protocol.
2. Code and unit tests (synthetic only); timing on synthetic inputs.
3. Pre-calibration facts (§3.6) and branch decisions (§1.6, §3.2.3–3.2.4, §3.3.2, §3.4) on calibration days; real-side minima on validation days. Stop rules (§3.5) and INCONCLUSIVE (§5.2) are checked here. Commit the facts.
4. Calibration (§4.4), identifiability (§4.5), capacity factor (§4.7), calibration diagnostics (§4.8). Commit the freeze.
5. Plant gate (§5) and ensemble filter (§4.6). Log the outcome.
6. If FAIL: F1 (§6.1), then §5 again. Log both outcomes.
7. Reported checks (§5.5).

---

## 9. Known limits

### 9.1 Limits of what this gate can show

- **Small n.** With 24 validation Wednesdays, the event-based checks rest on roughly 8–10 real-B-active days (an estimate). P2–P9 are coarse, and INCONCLUSIVE is a realistic outcome. The conjunction of 13 gated rows (N0, P1a–P9) raises the false-FAIL risk; the one fallback and the INCONCLUSIVE route are the only protections, and no criterion may be relaxed.
- **P3 ceiling.** If breakdown depended only on the daily-demand quartile with the v2 shares (15/33/46/85 %), the best deterministic classifier would agree on only about 73 % of days (a stylised calculation, not a measurement). The plant sees the day's 5-min inputs, so it can do better, but the 75 % threshold may be near the attainable ceiling. The calibration-day threshold classifier (§4.8) shows this before validation; the stochastic-capacity version of P3 is reported.
- **Replay, not control.** Only mode R is validated. The metering response, ramp queues and freeway-to-freeway demand on clipped days are extrapolations or later reconstructions (§7 R1–R2).
- **Served flows at the I-494 merges.** About 38 % of the PM inflow towards B enters there, and on most congested days those counts are capped. True demand at B is not observable on this corridor, and the real D-check exists only as a lower bound.
- **The drop.** The data cannot separate the real drop from zero on every subset; the plant is only prevented from exaggerating it. The headroom's dependence on the drop is handled in the gate (§7 R4).
- **Geometry readings.** The `shift` semantics (and with it the weave at B) and the 80-m relocation of the I-494 EB lane addition are readings of the configuration [VERIFY]. The configuration is current (2026), not 2023 (§3.7).
- **Balance-derived flows** (Pioneer Tr, Old Shakopee Rd, the T.H.62, W 78th St and I-494 EB exits) inherit station-count errors and a rough storage term, especially during B onset.
- **Upstream extent** is 8.4 km from the first controlled ramp, short of the 10 km target (§0.6 A2).
- **No wave validation** (R-b n/a): METANET was chosen partly for its speed dynamics, but 5-min station data cannot validate stop-and-go waves; the SUMO confirmation must.
- **Literature anchors** for bounds and P1 come from the review's reading, not the author's [VERIFY].

### 9.2 Thresholds fixed by lab convention (no literature anchor)

L_min 250 m and the 500 m cell target; the 1 % clip limit (N0, J penalty); 0.10 (ramp rule); 3 %/20 %/5 % (conservation); 2 % (class-B clipping); E2 45 mph / 5 %; E3 45 mph / 15 min; E4 50 % / 8 mph / 10 % occupancy / 1,200 veh/h/lane; the stop-rule fractions; 50–80 mph and 100 bins (lane screen); |c_s − 1| 0.15 and 0.05; J weights 0.25/0.25/0.5 and the 15:00–19:00 / ±30 min windows; the km 0.37–7.20 queue area; the §1.6 diagnostic thresholds and C_x bounds; P1a 0.10; P1b 0.20; P2 80 %; P3 75 %; P4 15 min; P5a 5 %; P7 30 min and 70 %; P8 2 days and 10 %; P9 1.05 and 1.2 (from the gate draft); the ±60 and ±90 min matching windows; the minimum counts in §5.2; F1's Δ and η bounds; the capacity grid 0.80–1.20; the ensemble size 2 and the 2 % J band.

---

## Appendix A. Review round 1: issue → resolution

Lens/severity as in `metanet_review1_kept.json`. "Proposed" = the reviewer's change; "better" = a refuter's text; "alt." = a justified alternative.

| # | Lens / sev. | Issue (short) | Resolution | Where |
|---|---|---|---|---|
| 0 | model / high | Undetected exits, unpulled aux lanes, wrong element counts make the protocol unrunnable | Adopted (better 1, adapted to the Minnetonka stretch): explicit element table (15 entrances, 15 exits); class-B balances; aux 7097/7077 pulled and counted; closed-link-only conservation | §1.2, §3.3.4, §3.4 |
| 1 | model / high | λ from stations; φ and δ misplaced; B may be a weave | Adopted (better 1): λ from every r_node, stated sequence 2-3-2-3-4-3-2-3-2; φ only at the 4→3 merging drop; δ_m = 0 at lane-adding entrances; B read as an add-drop weave [VERIFY]; no φ_x | §1.3, §2.1 |
| 2 | model / high | Replayed metering loses vehicles or overfills cells | Adopted (better 1): store-and-release replay origin, non-binding Q_o, clipped volume reported; mass-conservation test | §2.3, §8.4 |
| 3 | model / high | T = 10 s violates CFL; τ ≥ 5 s unstable; no clipping | Alt. per design choice 5: T = 5 s, cells ≥ 352 m, v_f ≤ 150 km/h, cap 1.05 v_f (Courant ≤ 0.62), τ ≥ 10 s; clipping with J penalty | §1.4, §2.5 |
| 4 | model / medium | s_i undefined; β against the upstream station overstates exits | Adopted (better 0/1 combined): β on the flow arriving at the diverge; s_e = β·(flow arriving in the cell) | §2.4, §3.3.5 |
| 5 | model / medium | Unmetered/mainstream release undefined; one ramp-capacity scale | Adopted in part: explicit origin equations and v_0 = v_1; Q_o fixed at 2,200 veh/h (not identifiable in replay) instead of fitted; origin misfits reported | §2.2, §2.3 |
| 6 | model / medium | VSL extension changes the no-control plant; form decides H2's T0 | Adopted (better 0/1): no cap in the calibrated plant; Hegyi form primary, MTFC modified FD pre-registered; T0 under both | §2.8, §7 R6 |
| 7 | model / medium | P5 drop cannot fail (IQR contains r = 1) | Replaced by design choice 7: P5b one-sided vs the real CI lower limit on the same days; P5a two-sided | §5.3 |
| 8 | model / low | Free-flow offsets undefined / collinear with v_f | Adopted (better 0): offsets deleted; lane screen + station scaling instead | §3.2.3–3.2.4, §4.1 |
| 9 | statistics / high | Missing exits and aux lanes; day rule yields no days; no minimum days | Adopted with changes: element table, balances, closed links, stop rule (< 18 calibration days) | §1.2, §3.3–3.5 |
| 10 | statistics / high | β denominator wrong exactly at B | Adopted (better 0): downstream anchor, upstream fallback, smoothing, low-flow carry-forward | §3.3.5 |
| 11 | statistics / high | Deterministic capacity makes breakdown too predictable (false-GO risk) | Per design choice 6: per-day capacity factor c_d on the B cells, estimated on calibration days with shared parameters frozen; KM distribution; hidden from all arms in the gate | §4.7, §7 R3 |
| 12 | statistics / high | Drop unfalsifiable; δ name clash; gate δ cells undefined for METANET | Adopted: one-sided P5b; δ → δ_m; gate drop cells on the measured drop | §5.3, §2.1, §7 R4 |
| 13 | statistics / high | Model-side rules and denominators differ from real ones | Adopted (better 1, refined): identical corridor rule on masked model series; explicit denominators and matching; real-side minima → INCONCLUSIVE, model-side shortfall → FAIL | §5.1–5.3 |
| 14 | statistics / medium | NRMSE normaliser undefined; free flow dominates | Adopted (better 1): mean-normalised, per-day pooled NRMSE; J with a 0.5 queue-area term; P1c | §4.2–4.3, §5.3 |
| 15 | statistics / medium | P6 fails good plants; small n; no CIs | Adopted: binomial tolerance at realised n (halves), minimum n, intervals for every statistic | §5.3–5.4, §8.5 |
| 16 | statistics / medium | Cell rule and CFL infeasible | Adopted in substance: deterministic cell rule (n = round(L/500)), T = 5 s, build asserts; step-halving reported | §1.4, §2.5 |
| 17 | statistics / medium | Measured downstream density is leaky and absent in the gate | Adopted (better 1): endogenous ρ_{N+1}; spillback exclusion with a 25 % cap; measured-density sensitivity reported | §2.2, §3.5, §5.5 |
| 18 | statistics / medium | F1 under-specified; no change rule; open implementation choices; §0/§6 contradiction | Adopted: F1 fully specified, §2.6 choices, change rule, route stop with SUMO as an author decision | §6, §2.6, §0.3 |
| 19 | statistics / medium | Split ambiguous; weather and holidays; no 2024 check | Split per design choice 8 (monthly alternation, listed); traffic-based weather proxy; holiday stratum; P-T | §3.1, §3.5, §5.6 |
| 20 | statistics / medium | D-check contradictory; replay-only validation | Adopted: gated model-side P9; real lower-bound form reported; PASS scope stated; mode-C check required later | §5.3, §0.2, §7 R1 |
| 21 | statistics / medium | Spurious bottlenecks elsewhere not gated | Adopted (better 0, only pair B excluded): P8 | §5.3–5.4 |
| 22 | statistics / medium | CMA-ES settings and identifiability rules undefined | Adopted (better 1 + better 0's continuation): frozen settings, normalised spread, profiles, no CV | §4.4–4.5 |
| 23 | statistics / low | α can be chosen after VSL results | Adopted: α_0 fixed, sensitivity set, no change after results, PASS scope | §2.8, §7 R6 |
| 24 | data / high | Day rule and conservation leave zero days; order of operations | Adopted (better 1): element classes M/B, closed-link statistic, detector-fault rule on calibration days, interpolation before validity | §3.2.2, §3.4 |
| 25 | data / high | Pioneer Tr Passage over-counts by a time-varying factor | Per design choice 2: 10 % passage/balance rule for every metered ramp; balance-derived inflow where it triggers; Queue detector as corroboration and sensitivity | §3.3.2 |
| 26 | data / high | Boundary N of I-394 sits in a recurrent queue | Per design choice 1: boundary at Minnetonka Blvd (km −8.413); E2 exclusion; correlation with B days reported; stop rule | §1.1, §3.5, §3.6 |
| 27 | data / high | Aux lanes not fetched; λ vs partial flows | Resolved: 7097/7077 pulled (416 requests) and summed; Cedar Lake Rd/9685 now outside the stretch | §1.2, §3.2.2 |
| 28 | data / high | Five exits without data; counts wrong | Adopted: element table; W 78th St and I-494 EB separate balances (aux pulled); T.H.62 lumped | §1.2, §3.3.4 |
| 29 | data / medium | β denominators: dead lane, aux lane, Pioneer ramp between | Adopted (better 0): reference-station rule with the Anderson Lakes fallback; complete stations only | §3.3.5 |
| 30 | data / high | Freeway merges inside B's queue; real D-check unsupported | Per design choice 3: served counts replayed and disclosed; real D-check lower bound only; later demand protocol required | §3.3.3, §5.4, §7 R2 |
| 31 | data / high | Drop unstable across halves | Adopted: one-sided P5b on the same days; per-set reals reported; §0 rewritten | §0.4, §5.3, §5.5 |
| 32 | data / medium | P6 uninterpretable at ~22 days | Adopted (better 1 structure: halves + gradient) with the binomial tolerance | §5.3–5.4 |
| 33 | data / medium | Field-length rule excludes nothing; offsets cannot absorb station bias | Adopted (better 1): station scaling c_s in the speed term only; raw speeds for events | §3.2.4 |
| 34 | data / low | Cell lengths vs CFL | Resolved with design choice 5 (T = 5 s, frozen cell rule) | §1.4, §2.5 |
| 35 | purpose / high | Aux lanes break flows and conservation | Resolved: aux pulled; closed links; detector-fault rule | §3.2.2, §3.4 |
| 36 | purpose / high | Storage unit; ramp-queue model unvalidated; replay not mass-safe; max_wait ignored | Replay made mass-safe (see 2); storage, max_wait and P0 ramp-demand validity are requirements of the controlled-plant protocol (design choice 2: ramp demand for later use only) | §2.3, §7 R1 |
| 37 | purpose / high | Counterfactual mode undefined (forking path) | Modes defined; mode C and its equivalence check required before any gate run (design choice 3) | §2.7, §7 R1 |
| 38 | purpose / high | P5 passes no drop and 3× drop | P5b one-sided (design choice 7); GO must hold on the low-drop variant; r_cap reported | §5.3, §7 R4, §5.5 |
| 39 | purpose / medium | β overestimated for 10 of 15 exits | Adopted (better 1): downstream form, build assertion | §3.3.5 |
| 40 | purpose / medium | T, cells and speed bounds contradict | Resolved: T = 5 s, cells and bounds frozen | §2.5 |
| 41 | purpose / medium | D-check "must" but not gated; undefined demand | P9 gated (model side); A_B defined; "the real data show this" deleted | §5.3–5.4 |
| 42 | purpose / high | Spillback, propagation, exit blocking not gated | P7 (extent + duration) gated; front speed, blocking exposure, excess veh-h reported; R-b n/a disclosed | §5.3–5.5 |
| 43 | purpose / medium | NRMSE undefined; J ignores the bottleneck | Adopted: §4.2 definitions and the queue-area term | §4.2–4.3 |
| 44 | purpose / medium | No minimum n or INCONCLUSIVE | Adopted (better 1): real-side minima before any model run; INCONCLUSIVE; extension only by addendum | §5.2 |
| 45 | purpose / medium | B could be exit-led, not a merge | Adopted (better 0): pre-calibration diagnostic on calibration days; EXIT branch with C_x | §1.6 |
| 46 | purpose / medium | 2026 config vs 2023 data; no 2024 check | Adopted: configuration-to-data audit; P-T transfer | §3.7, §5.6 |
| 47 | purpose / low | Offsets collinear; field length errors are per lane | Adopted: offsets deleted; lane-level screen | §3.2.3, §4.1 |
| 48 | purpose / low | Node counts wrong | Corrected for the Minnetonka stretch | §1.2 |
| 49 | literature / high | P1 unfalsifiable and unanchored | Adopted: full NRMSE definition; P1a lab convention with literature status; P1c vs nulls N1/N2 | §4.2, §5.3–5.4 |
| 50 | literature / high | Numerics infeasible; no v_min | Adopted: v_min 7.4 km/h fixed [VERIFY], τ ≥ 2T, clips counted | §2.5 |
| 51 | literature / high | F1 not pre-registerable | Adopted with changes: density-hysteresis two-capacity switch on B cells, Δ and η fitted, no per-cell v_f, seeds and budget fixed | §6.1 |
| 52 | literature / medium | Bounds unverifiable; some exclude published fits | Adopted: sourced bounds [VERIFY], v_f 80–150, ρ_max and v_min fixed, bound-active reporting, never widened | §4.1 |
| 53 | literature / medium | One drop estimator, possibly biased to 1 | r_cap reported for both sides (not gated, limitation stated); corridor caveat addendum required | §5.5, §7 R10 |
| 54 | literature / medium | One arbitrary restart; control-relevant parameters non-identifiable | Ensemble of ≤ 2 admissible members; GO needs all members; KILL stays KILL | §4.6, §7 R5 |
| 55 | literature / medium | J dominated by free flow | J = 0.25/0.25/0.5 with the queue-area term | §4.3 |
| 56 | literature / medium | Queue duration and extent not gated | P7 | §5.3–5.4 |
| 57 | literature / low | 0- vs 1-based index ambiguous | Superseded by design choice 8: monthly alternation with explicit dates and code | §3.1 |
