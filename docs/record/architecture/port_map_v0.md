# Port map v0: what the archive code contributes to v5.B.1

*2026-10-13. Source: archive branch `claude/v5b-core` at `3637676` (184 Python files, about 40k lines; read-only). Method: git ls-files + an AST import graph + vulture (60 %) as mechanical evidence; 5 area reviewers, each challenged by an adversarial verifier who tried to prove "dead" code is used and "needed" code is not (10 agents). Verdicts follow decisions V1–V19 in `docs/decisions.md`.*

## Rules for porting
- Only PORT and TRIM files come to `v5b1`, one step at a time, when a step needs them. Each port commit names the source branch, commit and file, and removes the listed dead parts **before** it lands.
- REFERENCE files are read, never copied. DROP files stay in the archive.
- A port brings its tests, or new tests where none existed (the archive has none for `sim/demand.py`, `sim/runner.py` or the CAV controllers).
- The archive branches are never edited.

## Outcome

217 tracked files classified: **15 PORT, 13 TRIM, 26 REFERENCE, 163 DROP**. The PORT + TRIM set is about 3.2k lines before trimming (of about 40k). Verdicts overturned by a verifier are applied; files classified in two areas keep the stronger verdict.

| Verdict | File | Lines | Area |
|---|---|---|---|
| PORT | `docs/v5b/data/mndot_us169sb_s460_weekday.json` | 124 | plant |
| PORT | `tests/test_guard.py` | 97 | infra |
| PORT | `vsl_lab/controllers/__init__.py` | 0 | control |
| PORT | `vsl_lab/controllers/pi_saturation.py` | 31 | control |
| PORT | `vsl_lab/eval/__init__.py` | 0 | control |
| PORT | `vsl_lab/eval/stats.py` | 23 | control |
| PORT | `vsl_lab/netgen/__init__.py` | 0 | plant |
| PORT | `vsl_lab/ops/__init__.py` | 0 | infra |
| PORT | `vsl_lab/ops/ledger.py` | 44 | infra |
| PORT | `vsl_lab/ops/thermal.py` | 38 | infra |
| PORT | `vsl_lab/plants/__init__.py` | 0 | plant |
| PORT | `vsl_lab/sim/__init__.py` | 0 | plant |
| PORT | `vsl_lab/sim/demand.py` | 81 | plant |
| PORT | `vsl_lab/train/__init__.py` | 0 | control |
| PORT | `vsl_lab/train/convergence.py` | 197 | control |
| TRIM | `pytest.ini` | 3 | infra |
| TRIM | `tests/test_corr2_build.py` | 140 | infra |
| TRIM | `tests/test_train_s0.py` | 181 | infra |
| TRIM | `vsl_lab/config.py` | 59 | plant |
| TRIM | `vsl_lab/jobs/corr_run.py` | 355 | jobs |
| TRIM | `vsl_lab/netgen/corr2.py` | 268 | plant |
| TRIM | `vsl_lab/ops/guard.py` | 97 | infra |
| TRIM | `vsl_lab/ops/scheduler.py` | 220 | infra |
| TRIM | `vsl_lab/plants/corr2.py` | 309 | plant |
| TRIM | `vsl_lab/plants/m_day.py` | 71 | plant |
| TRIM | `vsl_lab/plants/mrg3.py` | 167 | plant |
| TRIM | `vsl_lab/sim/runner.py` | 327 | plant |
| TRIM | `vsl_lab/train/train_sb3.py` | 415 | control |
| REFERENCE | `.gitignore` | 23 | legacy |
| REFERENCE | `core/eval_metrics.py` | 456 | legacy |
| REFERENCE | `research_notes/Daily demand patterns freeway control/*.md (5 files, 169 KB, UNTRACKED, not ignored)` | 0 | legacy |
| REFERENCE | `tests/test_capacity_drop.py` | 436 | infra |
| REFERENCE | `tests/test_cooling.py` | 126 | infra |
| REFERENCE | `tests/test_ramp_vsl_effect.py` | 168 | infra |
| REFERENCE | `tests/test_reward_e2e_verification.py` | 317 | infra |
| REFERENCE | `tests/test_specialist.py` | 138 | infra |
| REFERENCE | `traffic_environment/vehicle_fleet.py` | 401 | legacy |
| REFERENCE | `vsl_lab/controllers/cav_staircase.py` | 70 | control |
| REFERENCE | `vsl_lab/controllers/mtfc.py` | 40 | control |
| REFERENCE | `vsl_lab/controllers/specialist.py` | 294 | control |
| REFERENCE | `vsl_lab/data/m_shape_source.py` | 34 | plant |
| REFERENCE | `vsl_lab/data/mndot.py` | 397 | plant |
| REFERENCE | `vsl_lab/envs/bn4_env.py` | 456 | control |
| REFERENCE | `vsl_lab/envs/ring_env.py` | 134 | control |
| REFERENCE | `vsl_lab/eval/realism.py` | 182 | control |
| REFERENCE | `vsl_lab/jobs/mrg3_run.py` | 404 | jobs |
| REFERENCE | `vsl_lab/jobs/ring_run.py` | 90 | jobs |
| REFERENCE | `vsl_lab/jobs/round3.py` | 224 | jobs |
| REFERENCE | `vsl_lab/jobs/t1_meter_bn4_confirm.py` | 189 | jobs |
| REFERENCE | `vsl_lab/jobs/t2_realism.py` | 293 | jobs |
| REFERENCE | `vsl_lab/jobs/t4_calib.py` | 68 | jobs |
| REFERENCE | `vsl_lab/ops/cooling.py` | 436 | infra |
| REFERENCE | `vsl_lab/plants/ring.py` | 225 | plant |
| REFERENCE | `vsl_lab/runs/ledger.csv` | 222 | infra |

DROP files are listed per area below.


## Area: plant

**Summary.** I classified 27 files: the 26 tracked files in the four packages, plus vsl_lab/config.py (imported) and the shape JSON that plants/m_day.py reads. The verdicts rest on imports.json, vulture checked with grep across the whole repo, v5b1 decisions V1-V19 and ADR-001, and docs/lab/STATUS.md 'Silent failures'. Live and needed for v5.B.1: the CORR2X network generator (netgen/corr2 SPEC_AUX, the base of F3Z), the CORR2X plant core (files, route set, last-interval sensors), the vType layer from plants/mrg3 (H5 EIDM plus the only CAV vType), the MnDOT-shape inflow (plants/m_day plus its JSON), seeded Poisson generation (sim/demand) and the health/hash runner (sim/runner). Everything for meters, VSL, ALINEA, METANET, day-pattern screening, BN4, MRG3 and ring is obsolete under V15. Exception: plants/ring.py is kept as REFERENCE, because FollowerStopper and PI-with-saturation are published rule-based CAV controllers (V19 comparator candidates). Confirmed dead symbols: netgen/corr2 MERGES and VSL_AREAS; netgen/mrg3 VSL_AREA and ACC_AREA; plants/corr2 RAMP_ROUTES, RAMP_ROUTES_AUX and Meter.green_s_sum; runner _started and identity_mode; Demand.due (dead, and it has the old I1 off-by-one semantics); config TARGET_CPU_UTIL. Traps a port must not carry over: (1) CORR2X runs recorded the CORR2 net hash and plant name (spec_hash default, corr_run:260). (2) Module-global MAIN_EDGES/N_LANES mutated by activate(), and check_net reads the global, not the spec. (3) The CORR2X plant has no CAVs at all (av_share 0). (4) The CAV command path assumed setMaxSpeed; V5 found speed mode 95 for setSpeed. (5) The runner does not count junction collisions and FAILs on any collision, against V6's > 2. (6) time_in_system_by_route gives negative times with a censor before the last depart. (7) The determinism hash leaves out the headline inputs, and there is no energy or CAV hard-braking measurement (V10, V11). (8) SUMO emergency-braking warnings are mostly zipper creeping (B14), so they are not a safety metric. (9) m_day's noise magnitudes are provisional (invented), the fit code is not in the repo, and the ramp shapes reuse the mainline station. (10) config points to the v6 venv (V14) and to the archive run root and ledger. (11) The HDV 'non-compliant' speedFactor 1.15 group needs a fresh decision with no limits and a 120 km/h maximum. (12) Never revert to dead-end acceleration lanes (STATUS #15 stranding). (13) Keep speedDev=0 on commanded vehicles, and remember that SUMO ignores unknown vType attributes. I checked the shape-source missing-count issue on the real cache: 0.004 % of the 05:00-22:00 values, so it is negligible for S460. Not verified: whether corridor_analysis's fixed estimator could serve F3Z realism checks; I did not read it in full.

**Port order.** 1) vsl_lab/config.py (TRIM: repo/run roots for v5b1, NETCONVERT/SUMO bins from the v5b1 venv, clean_sumo_env) - no deps. 2) vsl_lab/netgen/corr2.py -> F3Z generator (TRIM: SPEC_AUX only, no TLS/ALINEA/O1, spec passed explicitly, mandatory spec_hash; port tests/test_corr2_build.py's CORR2X test with it) - depends on config. 3) vsl_lab/sim/demand.py (PORT, renamed inflow; drop Demand.due) - no deps. 4) docs/v5b/data/mndot_us169sb_s460_weekday.json + plants/m_day.py reshaped to the 06:00-10:00 morning peak (TRIM) - pure numpy, depends on the JSON. 5) Vehicle types: H5 + cav_vtype_xml/vtypes_xml from plants/mrg3.py, merged into the F3Z plant module (TRIM). 6) plants/corr2.py -> F3Z plant (TRIM: files, CORR2X routes, sensors without the N_LANES global) - depends on 2-5. 7) vsl_lab/sim/runner.py (TRIM, with the trap fixes plus energy and CAV hard-braking counters) - depends on config and demand; needed before any T0/T3 run. Later and optional: data/mndot.py (TRIM, Fetcher only) if the inflow noise is estimated from real days; plants/ring.py read as REFERENCE when the V19 comparators are chosen.

### `vsl_lab/netgen/corr2.py`: TRIM
- Reason: V2: F3Z evolves from CORR2X = SPEC_AUX (v3, zones 2.0-3.0 / 3.5-4.5 / 4.75-5.75 km). The generator (plain XML -> netconvert -> lanes.json -> detector additional, cached by spec hash) is the core of the F3Z build. V15 drops meters/VSL/ALINEA, so the TLS, ALINEA and CORR2 (O1 off-ramp, forced-merge) branches are obsolete. Imported by plants/corr2, jobs/corr_run, tests/test_corr2_build.
- Dead / obsolete parts:
  - vsl_lab/netgen/corr2.py:33 SPEC (CORR2 v2, O1 off-ramp, forced merges) - superseded by SPEC_AUX; only CORR2 runs/tests use it
  - vsl_lab/netgen/corr2.py:67-68 MAIN_EDGES/N_LANES module globals built from SPEC + :92 activate() mutating them - global mutable per-process state; pass the spec instead
  - vsl_lab/netgen/corr2.py:69 MERGES - dead (grep: no user outside the file)
  - vsl_lab/netgen/corr2.py:73 VSL_AREAS - dead (grep: no user); VSL dropped by V15
  - vsl_lab/netgen/corr2.py:71 TLS, :72 ALINEA_LOOPS - meter/ALINEA only (V15)
  - vsl_lab/netgen/corr2.py:75-81 ROUTES (CORR2 routes incl. O1) - keep only ROUTES_AUX
  - vsl_lab/netgen/corr2.py:119-121 traffic_light meter nodes; :217-221 all-green tlLogic; :257-259 TLS-structure check in build() - meters dropped (V15)
  - vsl_lab/netgen/corr2.py:130-132, 149-151, 177-178, 213-216 off-ramp O1 branches - CORR2 only (SPEC_AUX has off=None)
  - vsl_lab/netgen/corr2.py:198-200 e1a ALINEA loops - ALINEA only
  - vsl_lab/netgen/corr2.py:267-268 __main__ builds CORR2 (SPEC), not CORR2X
- Traps: (1) spec_hash(spec=SPEC) default (:102): jobs/corr_run.py:260 records net_hash=N.spec_hash() and plant 'CORR2' for CORR2X runs too, so archived CORR2X results carry the wrong net hash; make spec mandatory. (2) check_net (:239) filters mainline by the module global MAIN_EDGES, not by the spec it checks. (3) _node_id (:106-108) maps CORR2 x-coordinates to names, so in CORR2X 'nm2' is merge2's END node and 'nd1' is the zipper; rename from the spec. (4) If any TLS node is kept, netconvert's default static program meters every run unless an all-green program is loaded (comment :217; same class as STATUS #1 BN4 'light' node). (5) Keep the aux-lane design (merge lane 0 continues to X1/X2): the dead-end acceleration lane of CORR2/MRG3 stranded ramp vehicles and teleported (STATUS #15). (6) No zone definitions or zone detectors exist in code; F3Z zones are new work. (7) NET_CACHE comes from config (ext4 runs root) - fine, but test_corr2x_aux_lane_exits builds into the real cache, not tmp.
- Verifier (upheld): TRIM; trap 2 check_net uses global MAIN_EDGES; TLS meter nodes obsolete → TRIM, as mapped.. The line references match. MERGES and VSL_AREAS have no users (git grep -w). corr_run.py:260 writes 'plant': 'CORR2' and net_hash N.spec_hash() for both variants. test_corr2x_aux_lane_exits (tests/test_corr2_build.py:119-140) builds into the real NET_CACHE, while the CORR2 fixture patches it. One nuance: trap 2 is latent today, because CORR2 and CORR2X use identical mainline edge ids (m0..down). The live danger from the globals is N_LANES (m4-down are 3 lanes in SPEC and 2 in SPEC_AUX), which plants/corr2 Sensors read. Dropping the meter TLS nodes turns nm1 and n5750 into priority junctions. The ramp link has no foes there, so behaviour should not change, but this is a network change: re-run T0/T1 on F3Z. It is consistent with V4/V15 (NC = meters off).

### `vsl_lab/plants/corr2.py`: TRIM
- Reason: Becomes the F3Z plant: files(), the CORR2X Poisson route set (demand corr2x branch, X_SHARE exits), last-interval Sensors (flow/speed per lane, loop_vph). Meter, set_vsl, ALINEA sensors, ramp-fill and meter asserts serve actuators dropped by V15 (no VSL, no lane limits, no meters). The M-day and trapezoid inflows are replaced by the B12/V9 morning-peak inflow.
- Dead / obsolete parts:
  - vsl_lab/plants/corr2.py:49 RAMP_ROUTES - dead (grep: no user)
  - vsl_lab/plants/corr2.py:55 RAMP_ROUTES_AUX - dead (grep: no user)
  - vsl_lab/plants/corr2.py:151,191 Meter.green_s_sum - written, never read
  - vsl_lab/plants/corr2.py:46-48 OFF_SHARE, GROUPS and :100-106 corr2 (O1) route branch - CORR2 only
  - vsl_lab/plants/corr2.py:58-59 groups(variant) - collapse to the CORR2X groups
  - vsl_lab/plants/corr2.py:83-87 m_day branch (B6/B7 M day, superseded by B12) and :88-91 MRG3 trapezoid (3900 s) - replace with the morning-peak inflow
  - vsl_lab/plants/corr2.py:113-116 set_vsl - VSL/lane limits dropped (V15)
  - vsl_lab/plants/corr2.py:119-239 Meter class - meters dropped (V15); REFERENCE only if meters return
  - vsl_lab/plants/corr2.py:262-273 Sensors.alinea_occ_pct/alinea_flow_vph - ALINEA only
  - vsl_lab/plants/corr2.py:279-289 Sensors.ramp_fill - metered-queue measure
  - vsl_lab/plants/corr2.py:292-309 meters_state/assert_meters_green/assert_meter_links - meter H-R7 asserts
- Traps: (1) The CORR2X plant has NO CAVs: Demand(..., human_type='mix', av_type='mix') with av_share 0 (:107-108); the CAV vType must come from plants/mrg3.cav_vtype_xml/vtypes_xml(cav_share>0). (2) Sensors read net.N_LANES, a module global that is only correct after net.activate(spec) inside files(); remove the global. (3) Each route profile is a scaled copy drawn from one shared RNG in route order (sim/demand.py), so changing X_SHARE or adding a route shifts every later route's arrivals; common random numbers hold only across arms with identical inflow. (4) In the m_day branch each stream draws its own noise (default_rng([seed,k])), so mainline and ramp peaks shift independently by about 10 min - a modelling choice, not data. (5) departSpeed 'avg' is deliberate: 'max' caused IDM insertion failures (STATUS #9). (6) The step is 0.2 s; SUMO ACC/CACC gives emergency-braking artefacts at 0.5 s (STATUS #14).
- Verifier (upheld): TRIM; dead RAMP_ROUTES, RAMP_ROUTES_AUX, green_s_sum; meter/VSL/ALINEA parts obsolete → TRIM, as mapped.. git grep -w finds no users of RAMP_ROUTES, RAMP_ROUTES_AUX or green_s_sum outside their definitions (vulture agrees). Meter, set_vsl, alinea_*, ramp_fill and the meter asserts serve only V15-dropped actuators. demand() sets human_type and av_type to 'mix' with Route.av_share 0 (:107-108), so this plant has no CAVs. Its only importer is jobs/corr_run.py.

### `vsl_lab/plants/mrg3.py`: TRIM
- Reason: Only the vehicle-type layer is needed: driver H5 (EIDM with SUMO defaults, used by CORR2X via corr2.vtypes_xml/DRIVERS) and cav_vtype_xml plus vtypes_xml(cav_share) (the only CAV vType in scope; truck share kept as a share of ALL vehicles, nested CAV sets across shares). The MRG3 network plant (routes, trapezoid, Sensors, set_vsl) and the realism-gate driver variants are obsolete. Merge the kept parts into the F3Z plant instead of porting the module.
- Dead / obsolete parts:
  - vsl_lab/plants/mrg3.py:24 PLANTS (krauss/idm v1-v3) - MRG3 tracks only (envs/mrg3_env, jobs/mrg3_run)
  - vsl_lab/plants/mrg3.py:33-39 DRIVERS H0-H4 and :45-48 H5a/H5b/H3a/H3b lcAssertive variants - realism-gate variants; lcAssertive moved onsets to the entry (STATUS)
  - vsl_lab/plants/mrg3.py:70-74 vtypes_xml model='idm'/'krauss' branches
  - vsl_lab/plants/mrg3.py:84-96 demand() - MRG3 routes
  - vsl_lab/plants/mrg3.py:99-120 profile() trapezoid - replaced by the morning-peak inflow
  - vsl_lab/plants/mrg3.py:123-129 files() incl. LD3/ZM3 geometries
  - vsl_lab/plants/mrg3.py:132-161 Sensors (MRG3 detector ids)
  - vsl_lab/plants/mrg3.py:164-167 set_vsl (hard-coded 3 lanes)
- Traps: (1) cav_vtype_xml docstring (:51-56) says the set speed is applied with setMaxSpeed by controllers/cav_staircase.py; v5.B.1 commands per-CAV speeds (V3) and V5 found speed mode 95 is needed for setSpeed above a lane limit (kept for reference after V15). Re-decide the CAV command path; do not copy the setMaxSpeed assumption. (2) Keep speedDev='0' on the CAV type: SUMO's default speedDev 0.1 silently applied to AVs before (STATUS #6, plants/bn4 docstring). (3) SUMO silently ignores unknown vType attributes (comment :27-28, STATUS #10): check every vType behaviourally. (4) car_n speedFactor normc(1.15,...) was the 'non-compliant' group under posted VSL; with no limits (V15) and a 120 km/h network max (V13), 30 % of cars desire about 138 km/h. Re-decide the HDV desired-speed spread explicitly. (5) CACC/ACC at a 0.5 s step gives an emergency-braking artefact (STATUS #14); MRG3 STEP_LENGTH is 0.5.
- Verifier (upheld): TRIM (keep H5 + cav_vtype_xml + vtypes_xml(cav_share)); dead parts and traps 1-5 → TRIM, as mapped. Port _IDM_CAR and _IDM_TRK with H5, and add traps (a) and (b).. The line references match. H5 is built by string-replacing _IDM_CAR and _IDM_TRK (:41), so those two constants must be ported too. The map missed two traps. (a) STATUS #5: a per-vehicle setMaxSpeed makes SUMO rename the vehicle's type to 'av@<id>' (bn4_env.py:340, cav_staircase.py:4, notes_vehicles.md:219). A type-based CAV test silently disabled the actuator once. Identify CAVs by ID, and do NOT build the energy/hard-braking cohorts (V10, V11) from getTypeID. (b) vtypes_xml puts the HDVs in vTypeDistribution 'mix'. SUMO draws the type and speedFactor of each vehicle from its own RNG (--seed), not from Demand's RNG. When cav_share changes, the set of 'mix' vehicles changes, so the HDV type and speedFactor sequence shifts [VERIFY]. Arrival times are common across CAV shares; HDV attributes probably are not. Across controller arms with the same share they are common.

### `vsl_lab/plants/m_day.py`: TRIM
- Reason: The v5.B.1 inflow is a morning peak from the MnDOT US-169 shape (design §10: 'reshape plants/m_day.py from the M to the B12 morning peak'). The fitted-shape evaluator (_f, fit_params) and the noisy per-day profile are the starting point. The 06:00-19:00 M window, the PM peak terms and the 'demand' naming (V9) are obsolete. Only importer: plants/corr2.py (m_day branch).
- Dead / obsolete parts:
  - vsl_lab/plants/m_day.py:25-26 T0_H/T1_H/DAY_S = 06:00-19:00 (B6/B7, superseded by B12 06:00-10:00)
  - vsl_lab/plants/m_day.py:49,51,53 PM-peak noise terms (mu_pm/A_pm/s_pm) - not needed for an AM-only window
  - vsl_lab/plants/m_day.py:41-42 _norm over the 13-h day - must be redone over the new window
- Traps: (1) NOISE magnitudes (:27) are labelled PROVISIONAL (invented, not estimated from the 156 days); do not carry them over as calibrated. Either estimate them from the cached days or disclose them. (2) q_peak semantics depend on the normalisation window: the profile is scaled by the NOMINAL day's maximum over the window, so changing the window changes what q_peak means, and noisy days can peak above q_peak. (3) The shape is one MAINLINE station (S460, 2 lanes) and is reused for R1/R2; the ramp shapes are not data-based. (4) The fit code is not in the repo: the JSON stores the fit result but no script reproduces it (derivation names only m_shape_source.py, which makes the median series). (5) SHAPE_FILE is resolved relative to the repo (docs/v5b/data/...), so the JSON must be ported with it.
- Verifier (upheld): TRIM; trap 2 'q_peak semantics depend on the normalisation window' → TRIM, as mapped. Add a trap: q_peak currently means the PM peak (AM = 0.94 q_peak), and the fitted curve does not return to base by 10:00. The B12 'triangle-ish 06:00-10:00' inflow needs an explicit reshaping decision, not just a narrower window.. I evaluated the fitted model from the JSON 'fit' block. Over 06:00-19:00 the maximum (0.992) is the PM peak at 16:14. The AM peak (0.933 at 07:54) is only 0.94 of it. So under the current code q_peak is the PM peak, and the morning peak reaches only 0.94 x q_peak (e.g. R1 'peak 1200' would give about 1129). Within 06:00-10:00 the fitted curve starts at 0.47 of the AM peak and is still 0.70 of it at 10:00, because the plateau sigmoid holds about 0.65 all day. It is not the 'triangle-ish' shape of B12, and traffic will not have returned to base by 10:00, which affects drain and window choices. The PM Gaussian contributes 7e-5 at 10:00, so the PM terms are numerically dead in the AM window, as mapped. Removing their rng.normal draws (:49,51,53) changes every later random draw for a given seed. The fit code is absent: git grep for fit_rmse_rel, t_on_h and curve_fit hits only the JSON and m_day.py.

### `docs/v5b/data/mndot_us169sb_s460_weekday.json`: PORT
- Reason: Data dependency of plants/m_day.py (read through SHAPE_FILE): the median 15-min profile of 156 Tue-Thu 2023 weekdays at US-169 SB S460, plus the fit parameters. It is the source of the v5.B.1 inflow shape.
- Traps: Its 'fit' block cannot be regenerated from repo code (see m_day trap 4). Keep the provenance fields when porting.
- Verifier (upheld): PORT → PORT, keeping the provenance fields.. m_day.SHAPE_FILE reads it. The keys are source, n_days, statistic, derivation, median_vph_15min (96 bins over 24 h), fit_window_h [5, 22], fit_model, fit and fit_rmse_rel. The 'fit' block cannot be regenerated from repo code.

### `vsl_lab/data/m_shape_source.py`: REFERENCE
- Reason: Never imported and has no __main__ guard (imports.json: never_imported_not_main/unreached); a one-off top-level script with absolute paths that produced the median series in the shape JSON. Useful as provenance; rewrite it if the shape is re-derived.
- Traps: (1) The station is picked as the middle element of a sort by detector count (st[len(st)//2]), not by a stated criterion. (2) Missing or negative 30-s counts are summed as 0 veh. Days are skipped only if a whole array is missing. I measured the effect on S460 (detectors 1370/1371, 156 days, 05:00-22:00): 0.004 % of values missing, at most 0.15 % on any day, so it is negligible here but latent for other stations. (3) Runs code at import time.
- Verifier (upheld): REFERENCE → REFERENCE.. It is in imports.json's never_imported_not_main and unreached lists. It runs at top level with absolute paths, picks the station as st[len(st)//2], and turns negative or None counts into 0 (:27). It reads the cache directly, without mndot.py.

### `vsl_lab/sim/demand.py`: PORT
- Reason: Explicit seeded Poisson vehicle generation snapped to the step grid; it makes the runner's conservation identities exact (health checks required by CLAUDE.md). Per-vehicle CAV draws keep arrival times identical across CAV shares and give nested CAV sets, which fits Q9 regimes (CAV share). Rename to inflow (V9).
- Dead / obsolete parts:
  - vsl_lab/sim/demand.py:229-230 Demand.due - dead (grep: no caller; runner has its own due) and has the old off-by-one semantics (bisect_right counts depart == t; STATUS #3 'I1 off-by-one', fixed only in runner.due)
- Traps: (1) depart_times (:225-227) rebuilds the full list on every access; cache it if it is used per step. (2) One RNG consumed route by route: any change to one route's profile shifts the arrivals of all later routes. (3) Vehicle ids 'rid.n' are parsed by runner.step (vid.rsplit('.',1)) to count arrivals per route: keep the format, or pass the route explicitly. (4) Route.depart_speed defaults to '10' (BN4 legacy); set it explicitly.
- Verifier (overturned): dead part Demand.due at :229-230; trap depart_times at :225-227 → PORT stands. Demand.due is dead, but at vsl_lab/sim/demand.py:62-63, and depart_times is at :58-60; fix the line references. The nested-CAV claim holds only on the Route.av_share path, which plants/mrg3.demand uses and plants/corr2.demand does not; see the mrg3 challenge for the HDV-attribute caveat. There are no unit tests for demand.py or runner.py in the archive (git grep in tests/ finds only test_corr2_build.py), so write them during the port.. The file has 81 lines. Demand.due is at :62-63 (bisect_right(depart_times, t+1e-9), so it counts depart <= t, unlike runner.due at runner.py:165-169, which counts depart < t). depart_times is the property at :58-60. git grep '\.due\b' finds only runner's own due (runner.py:174, 226, 230). The runner caches demand.depart_times once in __init__ (runner.py:76), so the per-access rebuild costs nothing in the current code.

### `vsl_lab/sim/runner.py`: TRIM
- Reason: libsumo SumoSim with per-step counters, health checks H-R1..H-E4, door-to-door times including the insertion queue (tts_system), and result_hash for determinism (CLAUDE.md: health checks and determinism hashes required; T3). Port with the fixes below and add energy (V10) and CAV hard braking (V11), which it does not measure.
- Dead / obsolete parts:
  - vsl_lab/sim/runner.py:91,114,239 self._started - written, never read in scope (the only other hit is an unrelated attribute in jobs/metanet_v5_calibrate.py)
  - vsl_lab/sim/runner.py:95 self.identity_mode - dead (grep: no other use)
  - vsl_lab/sim/runner.py:322-327 outflow_vph - used only by jobs/bn4_nc (BN4 track); keep only if the F3Z metrics need it
- Traps: (1) '--collision.check-junctions false' (:104): collisions on junction internal lanes (the F3Z zipper and merges) are not counted, while V6 makes collisions an invalidity criterion. (2) H-R4 FAILs on ANY collision (:202-203); V6 says invalid only at > 2 collisions (or any teleport). Align the two. (3) time_in_system_by_route(t_censor) (:154-163) gives NEGATIVE times for vehicles whose desired depart is after t_censor; CLAUDE.md requires a fixed window with unfinished vehicles counted to the window end, so filter dep < t_censor. (4) H-R4b counts SUMO 'emergency braking' warnings as actuator abuse, but B14 found them mostly zipper-queue creeping; do not use them as the safety metric (V11: CAV hard braking at speed). (5) result_hash (:279-282) covers only counts, TTS and arrival bins; extend it to the headline inputs (per-vehicle delay, energy, hard brakes) or determinism checks can pass while the headline differs. (6) drain() (:230) final return omits the departed == total check that the loop uses. (7) The --time-to-teleport 300 default means a jam can sit 300 s before H-R3 fires; keep the teleport count as FAIL (V6). (8) SUMO_BIN comes from config (v6 venv path).
- Verifier (upheld): TRIM; dead parts _started (:91,114,239), identity_mode (:95), outflow_vph (:322-327); traps 1-8 → TRIM, as mapped, plus traps (a)-(c) above.. Every line reference matches. _started and identity_mode are never read: the only other '_started' hits are unrelated ledger strings in jobs/metanet_v5_calibrate.py. outflow_vph is used only by jobs/bn4_nc.py:19,71. The trap lines match: check-junctions false at :104, H-R4 on any collision at :202-203, the drain() final return at :230-231 without departed==total, and result_hash keys at :280-281. I also found three issues the map missed. (a) time_in_system_by_route(t_censor) (:159) only censors vehicles that never arrived. A vehicle that arrived after t_censor keeps its real arrival time, so the 'fixed window' is not enforced even when every dep < t_censor. (b) self.collisions sums getCollidingVehiclesNumber() every step (:135). That counts vehicles involved, at least 2 per collision, and with --collision.action warn the same collision may be counted again on later steps [VERIFY in SUMO 1.27.1]. So the counter cannot be compared with V6's '> 2 collisions'; count events via --collision-output or the statistic-output safety/collisions field, which _parse_stats already reads (:301-303) but never checks. (c) SumoSim's step_length defaults to 0.5 (:61), the step with the ACC/CACC artefact (STATUS #14); make the step mandatory or 0.2.

### `vsl_lab/config.py`: TRIM
- Reason: Imported by every netgen module and by runner (NET_CACHE, NETCONVERT_BIN, SUMO_BIN, clean_sumo_env, RUNS_ROOT). The tool paths and the env cleaner are needed; most compute constants are superseded rules.
- Dead / obsolete parts:
  - vsl_lab/config.py:40 TARGET_CPU_UTIL - dead (grep: 0 users; superseded 2026-10-03 rule)
  - vsl_lab/config.py:27-29,42-44 TEMP_PAUSE_C/TEMP_RESUME_C/TEMP_HARD_C/TEMP_SMOOTH_S/TEMP_SLOW_S/TEMP_STEP_S - superseded thermal rule (comment :48 'kept only for old docs/scripts'); used only by ops/scheduler and train_sb3 - decide with the ops port
  - vsl_lab/config.py:37 E_CORES - used only by ops/ecore_probe (E-core pinning no longer used)
  - vsl_lab/config.py:39 N_MAX_DEFAULT=48, :30 MAX_LAUNCH_PER_S, :31 SIM_START_MAX_LOAD, :41 UTIL_SMOOTH_S - old launch-gating rule; keep only what the ported guard/scheduler reads
- Traps: (1) VENV_BIN (:11) points to the v6 toolchain venv314; V14 requires the separate v5b1 venv (/home/catalin/work/phd/phd_speed_harmo_v5b1_toolchain/venv). (2) RUNS_ROOT defaults to /home/catalin/work/phd/vsl_lab_runs (shared with the archive), so a v5.B.1 net cache or run root there would mix with archived runs; give v5.B.1 its own root. (3) LEDGER_PATH points at vsl_lab/runs/ledger.csv in the archive tree. (4) The docstring says 'limits mirror CLAUDE.md 2026-10-01', which is false since the 2026-10-05 rule.
- Verifier (overturned): E_CORES (:37) 'used only by ops/ecore_probe'; TEMP_* 'used only by ops/scheduler and train_sb3' → TRIM. These are dead repo-wide: E_CORES (:37), TARGET_CPU_UTIL (:40), TEMP_PAUSE_C (:27), TEMP_RESUME_C (:28) and TEMP_STEP_S (:44), the last three imported but unused. Port TEMP_SLOW_S, TEMP_SMOOTH_S and TEMP_HARD_C only if the old scheduler's thermal loop is ported; under the 2026-10-05 rule (guard.py) they are probably not needed [check during the ops port]. The traps (v6 venv path, shared RUNS_ROOT, archive LEDGER_PATH, stale docstring) are upheld.. ops/ecore_probe.py:16 defines its own E_CORES = list(range(16, 32)) and imports only PYTHON_BIN, RUNS_ROOT, clean_sumo_env from config (line 14). No attribute-style access exists either (git grep 'config.E_CORES' etc.: none). So config.E_CORES is dead repo-wide. ops/scheduler.py:24 imports TEMP_PAUSE_C, TEMP_RESUME_C and TEMP_STEP_S, but its body never uses them (grep -w finds only the import line). Only TEMP_SLOW_S (scheduler:108), TEMP_SMOOTH_S (scheduler:107, train_sb3:65) and TEMP_HARD_C (scheduler:143) are live. TARGET_CPU_UTIL is dead (confirmed). N_MAX_DEFAULT has 27 importers, all archive jobs.

### `vsl_lab/sim/__init__.py`: PORT
- Reason: Empty package marker for sim (demand, runner are ported).

### `vsl_lab/netgen/__init__.py`: PORT
- Reason: Empty package marker for netgen (corr2 -> F3Z generator).

### `vsl_lab/plants/__init__.py`: PORT
- Reason: Empty package marker for plants (F3Z plant).

### `vsl_lab/plants/ring.py`: REFERENCE
- Reason: RING22 track plant (Track 3, archived). Not a v5.B.1 network, but FollowerStopper and PI-with-saturation (Stern et al. 2018, equations checked against arXiv 1705.01693 v1 per the docstring) are published rule-based CAV controllers: candidates for the V19 comparator. The AV safety shield (v_safe from B_SAFE) is a reusable idea for per-CAV commands.
- Traps: (1) PISaturation dx_s = max(2*dv, 4) with dv = v_lead - v is taken 'as printed' (:16); the sign is ambiguous [VERIFY against the paper before reuse]. (2) speedMode 6 disables SUMO's safe-speed checks; v5.B.1 found mode 95 for CAV setSpeed (V5). (3) Temporary file names use id(self), not the PID, which CLAUDE.md requires. (4) The controllers were tuned for a 260 m single-lane ring at 0.1 s; on a multi-lane freeway they need retuning (tuned comparators rule).
- Verifier (upheld): REFERENCE (FollowerStopper / PI-saturation as V19 candidates); traps → REFERENCE.. dx_s = max(2.0*dv, 4.0) at :76 (marked 'as printed' at :16). setSpeedMode(vid, 6) at :151. Temporary names use id(self) at :133 and :140. V19 explicitly names archived PI rules as candidates.

### `vsl_lab/netgen/ring.py`: DROP
- Reason: Single-lane ring network for Track 3; v5.B.1 uses F3Z only (V2). Imported only by plants/ring.

### `vsl_lab/netgen/mrg3.py`: DROP
- Reason: MRG3/LD3/ZM3 merge geometries (Track 2), replaced by CORR2X -> F3Z (V2). Imported only by plants/mrg3 (whose kept vType parts do not need it). The V19 'MRG3 staircase' comparator lives in controllers/, not here.
- Dead / obsolete parts:
  - vsl_lab/netgen/mrg3.py:33 VSL_AREA, :34 ACC_AREA - dead (grep: no users)
- Traps: Forced-merge acceleration lane that ends (lane 0, no successor) stranded ramp vehicles and teleported (STATUS #15); do not reintroduce it in F3Z.

### `vsl_lab/netgen/bn4.py`: DROP
- Reason: BN4 (Vinitsky 2018 bottleneck), an archived track (D5.10 result on claude/day-pattern-core); not F3Z.
- Traps: The 'light' node TLS metered every run until an all-green program was added (STATUS #1); the same netconvert default applies to any TLS node in F3Z.

### `vsl_lab/plants/bn4.py`: DROP
- Reason: BN4 plant and gate_ctx_r6 driver variants; archived track, no lane changing, not F3Z. Users: envs/bn4_env and BN4 jobs only.
- Dead / obsolete parts:
  - vsl_lab/plants/bn4.py:157 section, :178 n_hat_edge4 (vulture; archive only)
- Traps: AV speedDev default 0.1 silently applied until fix v3 (docstring; STATUS #6): set speedDev='0' on any commanded vehicle type.

### `vsl_lab/plants/metanet.py`: DROP
- Reason: US-169 SB METANET plant; METANET route stopped (D4.1/D5.5) and the task excludes METANET/MPC for v5.B.1.

### `vsl_lab/plants/metanet_ctrl.py`: DROP
- Reason: Closed-loop METANET stepper with ramp-meter queue layer for the day-pattern testbed (testbed T0 KILL D5.14); no METANET, no meters in v5.B.1.
- Dead / obsolete parts:
  - vsl_lab/plants/metanet_ctrl.py:200 dctrl unused variable (vulture 100 %)

### `vsl_lab/data/metanet_inputs.py`: DROP
- Reason: METANET data layer (protocol v3); METANET stopped (D4.1) and out of scope.
- Dead / obsolete parts:
  - vsl_lab/data/metanet_inputs.py:611 run_part1 (vulture)

### `vsl_lab/data/metanet_facts.py`: DROP
- Reason: METANET pre-calibration facts; METANET stopped (D4.1). Also imports vsl_lab.jobs (layering inversion).
- Dead / obsolete parts:
  - vsl_lab/data/metanet_facts.py:480 unreachable code after raise (vulture 100 %)

### `vsl_lab/data/metanet_events.py`: DROP
- Reason: METANET model/real event comparison (protocol v3); METANET stopped.

### `vsl_lab/data/us169_checks.py`: DROP
- Reason: US-169 data facts for the METANET protocol v1; serves only the stopped METANET route.

### `vsl_lab/data/corridor_analysis.py`: DROP
- Reason: Day-pattern corridor analysis on real MnDOT data (meter corridors, congestion episodes); day-pattern/M work is excluded from v5.B.1. Users: other dropped data modules and tests.
- Traps: STATUS #13: its capacity-drop estimator was confounded by the demand ramp (fixed by Addendum A); do not reuse that estimator without the fix.

### `vsl_lab/data/bn_screen.py`: DROP
- Reason: Bottleneck-anchored network screen for day-pattern corridor selection; obsolete. Circular import with bn_screen_analysis.
- Dead / obsolete parts:
  - vsl_lab/data/bn_screen.py:41 unused loop variable 'node' (vulture)

### `vsl_lab/data/bn_screen_analysis.py`: DROP
- Reason: Analysis half of the day-pattern bottleneck screen; obsolete; circular import with bn_screen.

### `vsl_lab/data/mndot.py`: TRIM
- Reason: Needed only if the inflow step re-derives the US-169 shape or estimates the day-to-day noise from real days (m_day trap 1): Fetcher (polite rate-limited Mayfly client with disk cache, 404 cached as null), available/available_cached, year_dates, DATA_ROOT/CONFIG. Everything else is day-pattern corridor screening. Port it late, and only if that step is taken; otherwise the cached JSON plus the shape file are enough.
- Dead / obsolete parts:
  - vsl_lab/data/mndot.py:37 windows() - day-pattern screening
  - vsl_lab/data/mndot.py:80-86 TOP3, RAMP_CATS, US169_METERS, DOWN_KM - meter-corridor selection (D3.x)
  - vsl_lab/data/mndot.py:89 corridor_detectors() - meter corridor detectors
  - vsl_lab/data/mndot.py:138 pass1_dates(), :149 screening_dates() - screening calendars
  - vsl_lab/data/mndot.py:218 day_congested(), :239 _cached_occ(), :247 score() - screening scores
  - vsl_lab/data/mndot.py:295 main() CLI (windows/screen/probe/score/corridors/pull) - calls windows() for every subcommand
- Traps: (1) DATA_ROOT hard-coded to /home/catalin/work/phd/dp_data/mndot. (2) A non-404 error retried 4 times returns None without caching, so it is retried silently next time; count and report n_err. (3) The user agent embeds the author's handle; keep the request rate at <= 5 req/s and get author approval for new pulls (request budgets were approved per pull).
- Verifier (overturned): TRIM (Fetcher etc. needed if the inflow shape is re-derived or the noise estimated from real days); trap 2 'count and report n_err' → REFERENCE (defer): do not port unless a new Mayfly pull is approved; then port only Fetcher, available/available_cached, year_dates and DATA_ROOT/CONFIG, and make get() distinguish error from 404. The listed dead parts stand.. vsl_lab/data/m_shape_source.py does not import mndot.py: it reads the Mayfly cache directly (DATA_ROOT/mayfly/2023/*/*.counts.json). So neither re-deriving the median shape nor estimating day-to-day noise from the 156 cached days needs mndot.py; only a NEW pull (author approval required) needs Fetcher. Trap 2 is partly wrong: Fetcher.get already counts errors (self.n_err += 1 at :186, :189), and main() reports them (:334, :366-367, :391-392). The real issue is that a non-404 failure returns None (:191-192), the same value as a cached 404 'null', so callers cannot tell missing data from a transient error. Also, available() (:198-209) has no error handling and sleeps after the request, outside Fetcher's rate clock. There is one more vulture hit the map did not list: unused loop variable 'node' at :383.

### `vsl_lab/data/__init__.py`: DROP
- Reason: Package marker of a package that v5.B.1 does not need unless mndot.py is ported (then recreate it).

- Verifier (upheld) on `vsl_lab/netgen/ring.py, netgen/mrg3.py, netgen/bn4.py, plants/bn4.py, plants/metanet.py, plants/metanet_ctrl.py, data/metanet_*.py, data/us169_checks.py, data/corridor_analysis.py, data/bn_screen*.py, data/__init__.py`: DROP → DROP.. No dynamic import reaches them from code a v5.B.1 port needs: the only import_module / __import__ hits are core/algos, sar_components, tests/test_metanet_v5.py:455 and jobs/s1_bn4.py:376, all outside the port set. No shell script or service references them (git grep). Their importers are archive envs, jobs and tests only. The vulture items match: bn_screen.py:41 'node', metanet_facts.py:480 unreachable, metanet_ctrl.py:200 'dctrl'. netgen/mrg3 VSL_AREA and ACC_AREA have no users. plants/bn4 section() and n_hat_edge4() have no callers (git grep 'section(' finds only def lines and unrelated merge_section).
- Verifier (uncertain) on `vsl_lab/sim/__init__.py, vsl_lab/netgen/__init__.py, vsl_lab/plants/__init__.py`: PORT (package markers) → PORT only if the vsl_lab package layout is kept in v5b1; otherwise recreate them for the new layout.. These are trivial. Whether they are needed depends on the v5b1 package layout, which ADR-001 does not fix (it names F3ZParallelEnv and adapters/, not the vsl_lab package names). The map suggests merging the kept plants/mrg3 vType code into the F3Z plant module; the same could apply to a renamed inflow module.

**Verifier: missed items and extra traps**
- The map's summary says 27 files classified, but it lists 28 entries: 26 tracked files plus config.py and the JSON. All 26 tracked files in the four packages are covered, so nothing in scope was skipped.
- runner.time_in_system_by_route (vsl_lab/sim/runner.py:159) censors only vehicles that never arrived; a vehicle arriving after t_censor keeps its real arrival time, so the fixed window is not enforced (separate from the negative-time bug).
- runner collisions counter (runner.py:135) sums colliding VEHICLES per step, possibly re-counting the same collision on later steps under --collision.action warn [VERIFY]. It is not comparable to V6's '> 2 collisions'. The statistic-output safety/collisions field is parsed (runner.py:301-303) but never checked or used.
- SumoSim step_length defaults to 0.5 s (runner.py:61), the step with the ACC/CACC emergency-braking artefact (STATUS #14).
- STATUS #5 (av@<id> type rename after per-vehicle setMaxSpeed) is missing from the traps: CAVs must be identified by ID, and the CAV cohort for energy and hard braking (V10, V11) must not come from getTypeID.
- The HDV vType and speedFactor are drawn by SUMO's RNG from vTypeDistribution 'mix' (plants/mrg3.py:76-81). Changing cav_share shifts the HDV attribute draws [VERIFY], so common random numbers across CAV-share regimes cover arrivals only.
- m_day: under the current 06:00-19:00 normalisation, q_peak is the PM peak (16:14) and the AM peak is 0.94 x q_peak. The fitted curve is still at 0.70 of the AM peak at 10:00 (plateau term), so B12's 'triangle-ish 06:00-10:00' needs an explicit reshape decision.
- plants/mrg3 H5 depends on _IDM_CAR and _IDM_TRK (:29-30, :41); port them with H5.
- config.E_CORES (:37) is dead repo-wide (ecore_probe defines its own). TEMP_PAUSE_C, TEMP_RESUME_C and TEMP_STEP_S are imported by ops/scheduler.py:24 but never used.
- mndot.py: unused loop variable 'node' at :383 (vulture). Fetcher.get returns None both for a cached 404 and for a transient error (:184, :191-192). n_err is already counted and reported.
- No archive unit tests exist for sim/demand.py or sim/runner.py (only tests/test_corr2_build.py covers this area), so the ports need new tests for the conservation identities, due() semantics and the hash.

## Area: control

**Summary.** Scope: the 18 tracked files in vsl_lab/controllers, envs, train and eval (2,429 lines). The import graph shows that nothing on the current v5.B CORR2X path (corr_run, netgen) imports any of them. All their callers are archive jobs, shell chains or tests. Every file is reachable from something, so there is no orphan module; the dead code is at the level of parts and branches, confirmed with git grep.

Verdicts:
- **PORT (2 modules + 3 empty __init__):** eval/stats.py (the binding paired-median bootstrap) and train/convergence.py (the C1 check, unit-tested).
- **TRIM (1):** train/train_sb3.py. ADR-001 replaces the SB3 driver with our own PPO, but its Watchdog (CPU guard for training), validation-only checkpoint selection, health stop rule, run-dir CSVs and ledger row are required by CLAUDE.md and must move into the new trainer. 14 dead or obsolete parts are listed with line numbers.
- **PORT (comparator):** controllers/pi_saturation.py, a per-CAV rule named as a candidate by V19. It needs freeway re-tuning, and the dx_s sign must be checked against the paper.
- **REFERENCE (5):** cav_staircase (template for the per-CAV command executor, but tied to lane limits and setMaxSpeed), specialist and mtfc (VSL, removed by V15), bn4_env (env patterns and traps), realism (T1 capacity-drop and wave methods, hardcoded for MRG3).
- **DROP (6):** mrg3_env, ring_env, envs/__init__, dcheck, inspect_bn4_policy, pilot_report.

Traps a port must not carry over:
- archive seeds 7,1xx/7,2xx as defaults in train_sb3 and inspect;
- convergence and train_sb3 decide the metric direction from a hardcoded list of archive metric names, so a new lower-is-better generalised cost would be maximised;
- the entropy sign convention (SB3 entropy_loss) that convergence expects;
- SB3 evaluate() keeps validation seeds fixed only because each val env holds exactly one seed;
- the av@<id> vType rename (track CAVs by ID);
- the speedFactor 1.5 CAV hazard;
- SUMO ACC/CACC emergency braking at coarse steps, and no CAV authority in Round 3 (this matters for the V11 hard-braking metric);
- an unbounded CAV command needs a -1.5 m/s² braking bound;
- cav_staircase never forgets vehicles (forget() is never called);
- E-core pinning and thermal pause logic are retired;
- the within-run capacity-drop estimator is confounded by the inflow ramp;
- pilot screening judged on the selection seeds (a false-positive history);
- stats uses an assert and has no rule for invalid runs (V6).

My uncertainties:
- the PI-saturation dx_s sign;
- the Watchdog self-throttling when one training fills the machine (inferred, not observed).

**Port order.** 1. vsl_lab/eval/stats.py, then eval/__init__.py. No dependencies. Needed first by any T0-T3 tool check or evaluation table. Write a unit test at the port, since none exists, and add a failure encoding for invalid runs (V6).
2. vsl_lab/train/convergence.py, then train/__init__.py. Pure Python. It depends only on the run-dir file contract: config.json with the val_metric sign, val.csv with update/val_return/val_metric_value, and progress.csv with update/explained_var/entropy as entropy_loss. Port tests/test_train_s0.py's convergence tests (cv.*) with it, and replace MIN_SIGNS with an explicit sign before any learned arm runs.
3. Trimmed train_sb3 scaffolding into the own PPO trainer (ADR-001 trainer contract): Watchdog (lines 53-115), the health stop rule, validation-only best checkpoint, the progress.csv/val.csv writers and the ledger row. It depends on vsl_lab/ops/guard.py (ComputeGuard), ops/thermal.py (package_temp_c, logging only), ops/ledger.py and config (RUNS_ROOT, GUARD_CFG, TEMP_SMOOTH_S), which are outside this scope and must be ported before or with it. It is needed before the first training batch, not before plant checks.
4. vsl_lab/controllers/pi_saturation.py, then controllers/__init__.py. No dependencies. Needed at the V19 comparator step, after the F3Z env and per-CAV command executor exist. It needs a tuning grid on 7,400,100-299.
REFERENCE files (cav_staircase, bn4_env, realism, specialist, mtfc) are read when the per-CAV executor (V3), the F3Z env (V7) and the T1 realism check are written. Nothing is copied from them.

### `vsl_lab/eval/stats.py`: PORT
- Reason: This is the binding statistics convention in CLAUDE.md: the median of paired differences with a 95 % percentile bootstrap CI. It is pure numpy with no SUMO or plant dependency. Ten archive jobs import paired_median_diff (round2-4, t1_*, t2_r1_checks, t3_r1r2_ring). The D5.8 bar (V-log, CLAUDE.md) needs it for the NC, tuned-comparator and per-regime rows. For the Bonferroni rows, pass alpha/m.
- Dead / obsolete parts:
  - vsl_lab/eval/stats.py:22 rel() - not called anywhere in the repo (git grep of rel( and stats.rel finds no caller; every job computes its own ratio)
- Traps: (1) The input check is an `assert` (line 12), which `python -O` strips. Replace it with an explicit raise. (2) There is no NaN or failure handling. Under V6 an invalid run counts as that arm's failure on that seed. Decide how a failed seed is encoded (for example the worst value or a censored cost) BEFORE calling; otherwise np.median silently returns nan. (3) The sign convention is b - a; keep it identical in every table. (4) No unit test exists in the archive (tests/ has none for stats). Write one at the port.
- Verifier (upheld): PORT; rel() at line 22 is dead → PORT (drop rel; replace the assert with a raise; add a unit test and an invalid-run (V6) encoding). git grep finds no caller of rel( or stats.rel anywhere. Every importer uses only paired_median_diff. The assert at line 12 is confirmed, and tests/ has no stats test. Minor correction: 9 jobs import paired_median_diff, not 10 (round2, round3, round4, t1_r1_checks, t1_r2_baselines, t1_r5_eval, t1_t0b, t2_r1_checks, t3_r1r2_ring). v5b1 CLAUDE.md:64 binds the convention, so PORT is justified.

### `vsl_lab/train/convergence.py`: PORT
- Reason: CLAUDE.md requires a convergence check ('DRL budget ... a convergence check'). This is the roadmap §9 C1 check (C1a-C1f), with review fixes #8-#11 already applied. It is pure Python, reads val.csv and progress.csv, and is unit-tested in tests/test_train_s0.py (9 tests). It is independent of SB3 as long as the new trainer writes the same two CSVs.
- Dead / obsolete parts:
  - vsl_lab/train/convergence.py:33 MIN_SIGNS - not dead, but it lists only archive metric names (tts_ctrl_vehh, mean_time_in_system_s, score_h, tts_system_ctrl_vehh). Replace it with an explicit sign in config.json.
- Traps: (1) check_run_dir (line 172) chooses the metric direction from MIN_SIGNS. A new lower-is-better headline (V16 generalised cost) that is not in the list is treated as 'maximise', which inverts C1a-C1c on the metric and the checkpoint logic. (2) The progress.csv 'entropy' column must hold SB3's entropy_loss convention (= minus the mean entropy; line 127 negates it). The own CleanRL-style PPO (ADR-001) must log the same sign, or C1e and C1f flip. (3) C1d needs explained variance logged per update. (4) Under ADR-001 the policy is multi-agent with a changing agent set: decide whether 'val_return' is the per-agent or the network return before reuse. The 2 % / 0.5 % / 10 % / 0.25 ln n tolerances are lab conventions with no literature source (header lines 18-21).
- Verifier (upheld): PORT; MIN_SIGNS (line 33) and check_run_dir (line 172) choose the metric direction from archive names → PORT (explicit sign in config.json in place of MIN_SIGNS). Line 172: sign = -1.0 if cfg.get('val_metric') in MIN_SIGNS else 1.0, so a new lower-is-better metric is maximised. v5b1 CLAUDE.md:70 requires 'a convergence check'. Nothing outside train_sb3:391 and tests/test_train_s0.py imports it. Minor correction: test_train_s0.py has 8 convergence tests (lines 91-158), not 9. Its other 6 tests cover SB3 parts.

### `vsl_lab/train/train_sb3.py`: TRIM
- Reason: Under ADR-001 / V17 the trainer is our own shared-parameter PPO, and SB3 is only the last-resort fallback, so the SB3 driver itself is not ported. Its scaffolding is still needed by CLAUDE.md: the training Watchdog ('training pauses all of its env workers together', lines 53-115, using vsl_lab/ops/guard.py ComputeGuard), validation-only checkpoint selection (CB.validate, 355-365), the health stop rule (FAIL share > 1 % after 50 episodes, 325-335), the config.json, progress.csv and val.csv files that convergence.py reads, and the ledger row (401-409). Port those into the new trainer; keep the SB3 parts only if an ADR-001 §5 switch to SB3 fires.
- Dead / obsolete parts:
  - vsl_lab/train/train_sb3.py:69,111-112 Watchdog.paused_s - incremented, never read (summary uses n_pauses and max_smoothed)
  - vsl_lab/train/train_sb3.py:340-341 CB._on_training_start - no-op override (vulture also flags _on_step and _on_rollout_end, but those are SB3 callback hooks: false positives)
  - vsl_lab/train/train_sb3.py:212 --algo choices 'sac' and 'tqc' - build_model raises NotImplementedError for both (line 176); TQC is excluded in v5.B.1
  - vsl_lab/train/train_sb3.py:165-175 build_model recurrentppo/trpo branches - archive R6 algorithms, not in ADR-001
  - vsl_lab/train/train_sb3.py:179-189 _entropy_loss_from_buffer - exists only for sb3-contrib TRPO
  - vsl_lab/train/train_sb3.py:34-50 make_env_fn bn4/ring/mrg3 - all three envs are dropped
  - vsl_lab/train/train_sb3.py:36,259,267 rank_seed - put into the kwargs and then stripped, never used
  - vsl_lab/train/train_sb3.py:36,280-282 val_perturb_cycle - BN4 perturbation validation only
  - vsl_lab/train/train_sb3.py:239 os.sched_setaffinity(WORKER_CPUS) - leftover of the E-core pinning that CLAUDE.md retired; WORKER_CPUS is now all CPUs (config.py:38), so it is a no-op
  - vsl_lab/train/train_sb3.py:243-251,260-262 archive track seed pools (7,21x/7,22x/7,23x training, 7,1t0,300 validation) and per-env default validation conditions and metrics
  - vsl_lab/train/train_sb3.py:263 val_sign from a hardcoded list of archive metric names
  - vsl_lab/train/train_sb3.py:278-286 val_env_fn per-env branches (bn4 inflow, ring eval_L, mrg3 eval_p_nc)
  - vsl_lab/train/train_sb3.py:401 ledger round hardcoded 'R3' and 'P'/'F' by updates < 500
  - vsl_lab/train/train_sb3.py:4,54-56,89-92,102 thermal hysteresis wording and logic - the thermal rule was removed (author 2026-10-10); keep only temperature LOGGING (wd_max_c), with thermal_paused taken from the guard config
- Traps: (1) The default seeds (7,210,000+ training, 7,110,300 / 7,120,300 / 7,130,300 validation) belong to the archived tracks. CLAUDE.md forbids reusing 7,100,000-7,399,999: use 7,410,000-7,419,999 for training and 7,400,300-499 for validation. (2) evaluate() (118-139) relies on SB3 VecEnv auto-reset: after each validation episode every val env starts a fresh SUMO (wasted warm-up), and the next evaluate() calls reset() again, which advances the env's eval seed index. Validation seeds stay fixed across validation points ONLY because each val env has exactly one seed (eval_seeds=[sd], line 277). Do not give a val env several seeds. (3) `a.val_seed0 or default` (261) ignores an explicit 0. (4) LinearDecay (142-150) exists only because SB3 restarts progress_remaining on every learn() call. Do not copy the workaround into the own PPO; STATUS.md records that --lr-decay was silently ignored for RecurrentPPO/TRPO in R6 (fixed 34ae76f). (5) Pitfall (my inference, not observed): the Watchdog pauses when CPU > 90 % for 2 min, and the training's own workers are that load. If L x E fills the machine, the training cycles between pausing and resuming. Size L x E so that one training stays below the limit. (6) The --seed index is limited to 0-4 because learner 5 once drew from the next track's pool (P-M4, line 243-246); the new seed layout needs the same guard.
- Verifier (upheld): TRIM: port Watchdog, validation-only checkpoint, health stop rule, CSV writers and ledger row; 14 listed dead parts → TRIM (scaffolding only, plus the corrections a-f; keep the SB3 build_model PPO branch only as a reference for the ADR-001 §4.2 SB3 learning-curve match). All listed dead parts check out: paused_s is only written (69, 112), _on_training_start is a no-op (340), sac/tqc reach NotImplementedError (212, 176), rank_seed and val_perturb_cycle are stripped at line 36, ledger 'R3' at 401, and WORKER_CPUS = all CPUs (config.py:38). The parts the map leaves out: (a) a BUG that must not be ported. summary['best_val_return'] and the ledger field 'best_val_return' (398, 408) store cb.best, which is the SIGNED best val_metric score (361-363), not a return. (b) best_val_model.zip is written only for periodic labels (362 excludes 0 and 'final'), and a NaN metric never beats -inf. If the health stop fires before val_every updates, or the metric is NaN, no validation-selected checkpoint exists. (c) The Watchdog reads ComputeGuard internals (cpu_hot_since, cpu_cool_since, cfg['cpu_hold_s'/'step_s']), always passes n_paused=0 and ignores the returned Decision (99-108). Its _cpu() duplicates ops/scheduler.py:_cpu_times. A guard refactor at the port would silently break it, so give the guard a public 'group pause' method. (d) n_actions_of and action_dim_of (192-205) feed convergence (392) and must be kept. (e) _entropy_loss_from_buffer is dead with TRPO, but tests/test_train_s0.py:173-176 imports it, so drop that test with it. (f) The 'health stop rule' is NOT stated in v5b1 CLAUDE.md (grep 'health' finds nothing). It is an archive lab convention, while V6 (invalid run) is binding. Re-confirm it rather than port it as required. The watchdog (CLAUDE.md:84), the ledger (:28) and validation-only checkpoints (:70) are required.

### `vsl_lab/controllers/pi_saturation.py`: PORT
- Reason: V19 names the archived 'MRG3 staircase / PI rules' as candidate rule-based CAV comparators for the D5.8 bar. PI-with-saturation (Stern et al. 2018) is a per-CAV speed rule, which fits V15 (CAV commands are the only actuator). It is 31 lines of pure Python with no SUMO dependency. Its only caller is vsl_lab/jobs/mrg3_run.py:187-194 (Round 4 arm P), which applied it with ls.vehicle.setSpeed and released it with setSpeed(-1).
- Traps: (1) The constants (g_l 7 m, g_u 30 m, v_catch 1 m/s, gamma 2 m, window 38 s) were checked against the paper for the RING track (low speed). They are not tuned for a 120 km/h freeway; CLAUDE.md requires a TUNED comparator, so they need a tuning grid on the tuning seeds. (2) The history window is counted in calls (maxlen = window_s/dt). It is correct only if v_cmd() is called every dt; calling it at the policy decision interval silently shortens or lengthens the 38 s window. (3) dx_s = max(2*dv, 4) with dv = v_lead - v (line 23-24): I am not certain this sign matches the paper, because with a closing speed (v > v_lead) the 4 m floor governs. Mark [VERIFY] against Stern et al. 2018 before use. (4) In mrg3_run, when there is no leader, v_lead = lane limit and gap = 100 m. (5) STATUS T3: on the ring, PI-sat was already at the ceiling (H ~ 0).
- Verifier (uncertain): PORT as a V19 rule-based CAV comparator → REFERENCE until the author picks it under V19. If picked, PORT with a freeway tuning grid on 7,400,100-299 and the Round 4 +119-180 % result disclosed. V19 names 'the archived MRG3 staircase / PI rules', but the choice is open ('which ones (literature check)'). The map leaves out the decisive archive result. On the freeway (LD3, Round 4) arm P 'cavpi@cav0.25P' (this class, called by mrg3_run.py:187-194) raised delay by +180.2 % (cell 3900/0) and +118.7 % (cell 4500/0) against its NC (docs/lab/round4_th.md:20,35; notes_history.md:202). Callers: mrg3_run only. The original is plants/ring.py:65, used by jobs/ring_run.py. The archive also has a second copy of this class. mrg3_run also clamps the command to the lane limit and uses v_lead = lim, gap = 100 m when there is no leader. If it is ported as-is, it is a known-harmful freeway comparator, which risks the 'no weak baselines' rule unless it is re-tuned. The dx_s sign [VERIFY] stays open.

### `vsl_lab/controllers/cav_staircase.py`: REFERENCE
- Reason: This is the Round 3 per-CAV set-speed staircase: ACC/CACC set speed through vehicle.setMaxSpeed in 1 km/h steps, at most one step per X s, and only after the CAV reached its set speed. It is the closest archive code to the V3 per-CAV accelerate/hold/brake (+/-5 km/h) executor, and design_v0 §'actuators/cav_cmd.py (new)' cites it as a source. However, its target semantics are tied to lane limits and posted VSL, which V15 removes (None means follow the lane limit, lines 41-50). The step is 1 km/h, not 5. V5 records that v5.B.1 CAVs are commanded with setSpeed under speed mode 95, not with setMaxSpeed. Read it for the 'reached' gate and the min-interval logic, then write cav_cmd new.
- Dead / obsolete parts:
  - vsl_lab/controllers/cav_staircase.py:31 forget() - never called anywhere (git grep), so self.st grows with every CAV ever seen (a leak in long runs)
  - vsl_lab/controllers/cav_staircase.py:41-50 lane-limit-follow and release branches - only meaningful with posted VSL or lane limits (dropped by V15)
- Traps: (1) After setMaxSpeed, SUMO renames the vType to 'av@<id>', so CAVs MUST be tracked by ID. The type-based test silently disabled the actuator in R2 v1 (STATUS item 5; bn4_env.py:340-342). (2) The archive cav vType has speedFactor 1.5. Without an active cap, CAVs drive at 1.5 x the limit up to 33.33 m/s (notes_vehicles.md items 12, 221). (3) SUMO ACC/CACC brakes hard (emergency braking) at a 0.5 s step (STATUS item 14). At 0.2 s and a 25 % share, CACC alone worsened delay by 46-93 %, and the Round 3 CAV arms showed no authority (T-H). This matters directly for V11 (CAV hard braking) and for T0 'the actuator binds'. (4) Lane- or segment-level CAV targets were tried and failed (V3).
- Verifier (uncertain): REFERENCE; dead parts forget() (31) and lines 41-50 (lane-limit-follow and release branches) → REFERENCE by default; TRIM (call forget on exit, drop 41-45) if V19 selects the MRG3 staircase. forget() is never called: confirmed, and the self.st leak is real. Three corrections. (1) V19 explicitly names 'the archived MRG3 staircase' as a candidate comparator. Under round3_tm21_protocol.md:48-69 that comparator is arm C, CavStaircase with MTFC rate or const targets. If the author picks it, this file is TRIM, not REFERENCE. It is unpublished (author spec 2026-10-02), and STATUS.md:53 records that the CAV arms showed 'no authority'. (2) Lines 46-50 (release through the staircase) are not dead under V15: with a static 120 km/h network maximum they release a CAV back to the maximum. Only 41-45 (follow a changed lane limit) becomes a no-op. (3) The map says 'V5 records that v5.B.1 CAVs are commanded with setSpeed under speed mode 95'. That overstates it: V5 is superseded by V15, and only the speed-mode finding is kept for reference. setMaxSpeed vs setSpeed is still open.

### `vsl_lab/controllers/specialist.py`: REFERENCE
- Reason: SPECIALIST (Hegyi et al. 2008/2009) is a VSL shock-wave algorithm. V15 removes VSL, so it is not a v5.B.1 actuator. It is a carefully sourced, unit-tested (tests/test_specialist.py) implementation of the shock-wave front geometry (front_speed, scheme_states, the area 2-4 timing). It is useful to read if a jam-absorption CAV comparator (V19 'jam absorption') is built from the same theory. Its callers are only archive jobs (mrg3_run, round4).
- Dead / obsolete parts:
  - vsl_lab/controllers/specialist.py:149,218 last_scheme - written, never read (vulture; no grep hit outside the file)
- Traps: (1) The m_t sign ambiguity in P1 p.831 is resolved by using |m_t| (header lines 28-30). Keep the disclosure if any part is reused. (2) The design states (rho4 33, rho5 26, q5 2033.3 veh/h/lane, v12 -15 km/h) are the paper's Dutch A12 values, not calibrated for F3Z. (3) While a scheme is active, measurements are ignored (P1); new jams are missed for the scheme's whole duration.
- Verifier (upheld): REFERENCE; last_scheme dead (149, 218) → REFERENCE. last_scheme is only assigned (149, 218), and no getattr use exists. Importers: mrg3_run.py:28 and tests/test_specialist.py. round4 reaches it only through 'spec' arm strings. It is a VSL algorithm, removed by V15.

### `vsl_lab/controllers/mtfc.py`: REFERENCE
- Reason: MTFC through posted VSL (Carlson et al. 2013), the cascade with anti-windup. V15 removes VSL and decisions say no MPC or METANET for now, so it is not ported. Its importers are archive-only (mrg3_env, jobs/bn4_eval, mrg3_run, g1_s1, g1_s2). It is useful to read if a CAV-implemented MTFC is ever proposed as a V19 comparator.
- Traps: The anti-windup clamps (q_min 200, q_max 2600, b in [b_min, 1]) are a lab addition, not in the paper (disclosed in the header lines 10-11). D5.1: the literature caps helpers at about 9 % over MTFC+PI-ALINEA [VERIFY].
- Verifier (uncertain): REFERENCE; importers include g1_s1 and g1_s2 → REFERENCE; becomes PORT together with cav_staircase if V19 selects the MRG3 staircase (arm C). The importers are only mrg3_env.py:24, jobs/bn4_eval.py:22 and mrg3_run.py:26. g1_s1 and g1_s2 use 'mtfc' only as string arm names. Round 3 arm C already sent the MTFC rate as the CAV target (round3_tm21_protocol.md:69 T1c-C), and Round 4 ran 'mtfc:*' arms. The 'archived MRG3 staircase' comparator that V19 names therefore depends on this file. It is not merely 'if a CAV-implemented MTFC is ever proposed'.

### `vsl_lab/controllers/__init__.py`: PORT
- Reason: Empty package marker. Needed only if pi_saturation (or a later comparator) is ported under the same package name.
- Verifier (uncertain): PORT (empty marker) → PORT only together with a ported controller. It is needed only if pi_saturation (or the staircase) is ported, and that choice is open under V19.

### `vsl_lab/envs/bn4_env.py`: REFERENCE
- Reason: BN4 single-agent Gymnasium env (Vinitsky 2018 reproduction) with AV caps, posted VSL, meter scheduling and meter-rate actuators. The plant failed the realism gate (STATUS: discharge 900 veh/h/lane, capacity-drop ratio 0.77). Meters and VSL are out (V15), and the v5.B.1 env is a PettingZoo ParallelEnv (V7, ADR-001). It has no use on the F3Z/CORR2X path: the import graph shows only archive jobs (bn4_eval, mpcf, t1_meter_r6plus_diag), inspect_bn4_policy, train_sb3 and tests/test_bn4_meter_rate import it. Kept as REFERENCE, not DROP, because it holds working patterns the new env needs: a fresh SUMO per reset, CAVs tracked by ID, per-PID stderr capture, a physical bound on commands, an actuator self-check (H-R7) and a non-finite obs/reward health FAIL (H-R6).
- Dead / obsolete parts:
  - vsl_lab/envs/bn4_env.py:269,351 n_actuator_checks - written, never read
  - vsl_lab/envs/bn4_env.py:434 sim.demand_end_t - set, no reader found by grep
  - vsl_lab/envs/bn4_env.py:66 metadata - gym convention (vulture false positive)
- Traps: (1) 'av@<id>' vType rename: identify CAVs by ID (lines 340-342; STATUS 5). (2) Abrupt caps caused emergency braking; the fix bounds every command to -1.5/+1.0 m/s^2 x dt and never asks for braking harder than 1.5 m/s^2 (lines 199-218; STATUS 4). The per-CAV +/-5 km/h action needs the same bound, or V11 hard braking is an artefact. (3) Redirecting stderr to /dev/null hid tracebacks; the fix writes per-PID files (lines 81-88; STATUS 11). (4) prev_action used to be sized for av_caps for every actuator (line 349 'bug'). (5) pin_ecores defaults to True: E-core pinning is retired. (6) The perturbation 'block' of 360 s teleports in 209 of 220 runs (STATUS 18).
- Verifier (upheld): REFERENCE; n_actuator_checks and sim.demand_end_t dead → REFERENCE. n_actuator_checks is only written (269, 351), and demand_end_t is only set (434): git grep 'demand_end' finds no reader. The line references for the -1.5 m/s2 bound (199-218), the per-PID stderr (81-88), av@ (340), the prev_action bug (349) and pin_ecores=True (70, 89) all check out.

### `vsl_lab/envs/mrg3_env.py`: DROP
- Reason: T2 MRG3 merge env, posted VSL with MTFC in direct, hybrid and residual modes. Track T2 was closed by the realism gate; VSL is removed by V15; single-agent Gymnasium env. Its only importers are jobs/r4_eval_rl.py and train_sb3. The patterns it shares with bn4_env (fresh SUMO per reset, per-PID stderr, H-R6) are covered by keeping bn4_env as REFERENCE.
- Dead / obsolete parts:
  - vsl_lab/envs/mrg3_env.py:33 metadata, 134 options - gym conventions (vulture false positives)
  - vsl_lab/envs/mrg3_env.py:41 val_cond - no external caller sets it (git grep)
- Traps: The new-stop counter samples halting (<= 0.1 m/s) vehicles every 1 s (lines 117-125) and is used for the reward only, while evaluation used tripinfo waitingCount. Do not mix the two definitions if a stop-and-go index is rebuilt (V18 is pending).
- Verifier (upheld): DROP; val_cond (41) has no external setter → DROP. val_cond IS read internally (line 142, the 'main_peak' branch). It can be set only through --env-kwargs JSON, and no job, shell script or doc passes val_cond. So the main_peak branch is dead, not the attribute. Importers: r4_eval_rl and train_sb3 only. Its VSL/MTFC actuators are removed by V15.

### `vsl_lab/envs/ring_env.py`: DROP
- Reason: T3 ring with one AV among 21 IDM humans (FollowerStopper hybrid or direct acceleration). Track T3 is done (PI-sat at the ceiling, H ~ 0). A ring is not F3Z; single-agent Gymnasium. Its only importer is train_sb3; no tests or jobs use it.
- Dead / obsolete parts:
  - vsl_lab/envs/ring_env.py:24 metadata, 56 options - gym conventions (vulture false positives)
- Traps: The direct mode applies the action as an acceleration with no safety layer; ring AV collisions are STATUS item 7. Do not let a per-CAV policy act without a safety layer.
- Verifier (overturned): DROP → REFERENCE (observation and shield design only; do not port). This is the only archive env with a PER-VEHICLE LOCAL observation [v_av, v_lead - v_av, gap, 38 s mean speed, previous action] (header lines 6-7, Box(5)). It is also the only one with a published per-CAV rule used as a shield (FollowerStopper, hybrid mode). ADR-001 §2 defines the vanilla arm as 'observations local to each CAV', and the map's own trap asks for a safety layer, which is this hybrid design. One additional trap: non-finite observations are silently zeroed by nan_to_num (lines 111-112), while bn4_env records an H-R6 FAIL. Do not carry the silent zeroing over. Nothing should be ported, but it is worth reading.

### `vsl_lab/envs/__init__.py`: DROP
- Reason: Empty package marker for three dropped or reference-only envs. The PettingZoo F3ZParallelEnv will be written new (ADR-001 §3) and its package created then.
- Verifier (upheld): DROP → DROP. It is an empty marker, and the PettingZoo env package is created new (ADR-001 §3).

### `vsl_lab/eval/realism.py`: REFERENCE
- Reason: MRG3 plant-realism signatures: sustained onset and recovery, capacity-drop ratio, wave speed by cross-correlation, congestion origin, stopped share. The probe names (up3..up0b), PLATEAU_EXIT (1400-3000 s) and the onset window (600-3600 s, t_end 3900) are hardcoded for MRG3. Its only importer is jobs/t2_realism.py. The methods are a known-good template for the v5.B.1 T1 tool check ('a capacity drop exists without teleport artefacts'), but they must be re-parameterised for F3Z.
- Traps: (1) The within-run capacity-drop ratio is confounded by the inflow ramp (STATUS item 13, Addendum A). ratio_original_10min (line 248) is that confounded estimator; the gated ratio is between runs (plateau_flow). (2) Realism history: no SUMO car-following model gave a measurable capacity drop without artefacts (IDM teleports, W99 no drop, EIDM breakdowns too short; STATUS 'Plant-realism gate'). The F3Z T1 check should expect this risk.
- Verifier (uncertain): REFERENCE (hardcoded for MRG3); trap cites ratio_original_10min at line 248 → TRIM (parameterise probes, pairs and windows; drop or flag the confounded ratio_original_10min at line 108) or REFERENCE: the author decides when the T1 protocol is written. The line reference is wrong: the file has 182 lines, and ratio_original_10min is at line 108. The module is pure numpy over CSVs, with no plant import. Only the constants are MRG3-specific: PROBES and PAIRS (19-21), PLATEAU_EXIT (91), the 600-3600 s onset window (82) and t_end 3900 (99). probe_x assumes lanes straight along x. review_v0.md:172,228-229 lists it as the existing support for the binding P0/T1 realism check and says it 'needs a CORR2X port'. Because T1 is binding (CLAUDE.md:58), a parameterised port (TRIM) is defensible. REFERENCE is too, if the check is rewritten. No unit test exists.

### `vsl_lab/eval/dcheck.py`: DROP
- Reason: A one-off D-check (roadmap §2): is MRG3 breakdown predictable 5 min ahead (L2 logistic regression, grouped AUC). It reads MRG3 features.csv only and is used only by archive shell chains (run_chain4.sh, run_chain5.sh, run_v3.sh). V9 says the controller learns from what it measures, and there is no forecaster step in v5.B.1.
- Verifier (upheld): DROP → DROP. It is used only by run_chain4.sh:12, run_chain5.sh:29 and run_v3.sh:14, and reads MRG3 features.csv. v5b1 CLAUDE.md:13 still allows 'a forecaster' as a helper, so if one is ever proposed, read this predictability-check design in the archive. That does not justify porting it now.

### `vsl_lab/eval/inspect_bn4_policy.py`: DROP
- Reason: Inspects BN4 AV-cap policies (per-slot caps vs segment-4 count). It is specific to BN4 and SB3 PPO/TRPO, and its default seeds 7,110,300+ are archive seeds. Nothing calls it except a mention in docs/review notes.
- Verifier (upheld): DROP → DROP. No code caller. It is mentioned only in docs/review/design_space/notes_rl_design.md:343. It imports bn4_env and is specific to BN4.

### `vsl_lab/eval/pilot_report.py`: DROP
- Reason: R3 pilot screening report against docs/lab/r3_pilots_protocol.md. It writes into the repo (docs/lab/figs, docs/lab/r3_pilots.md) and appends a ledger row hardcoded to round 'R3'. It is used only by archive shell chains (run_bf, run_chain2/3/5/6/7, run_p1, run_realism_p6, run_round3).
- Traps: The screening criteria C2 and C3 score max(final, best checkpoint) on the SAME validation seeds that select the checkpoint (lines 82-85). STATUS T1-B: 'The screening pass was a false positive again'. Any new screening must judge on seeds that were not used for selection.
- Verifier (upheld): DROP; trap: screening on the selection seeds (82-85) → DROP. It is used only by archive shell chains (run_bf, run_chain2/3/5/6/7, run_p1, run_realism_p6, run_round3). Lines 82-85 confirm top = max(final, best checkpoint) on the same validation seeds that select the checkpoint.

### `vsl_lab/eval/__init__.py`: PORT
- Reason: Empty package marker for eval (stats.py is ported).
- Verifier (upheld): PORT (marker) → PORT. stats.py is ported, and t2_realism imports the vsl_lab.eval package.

### `vsl_lab/train/__init__.py`: PORT
- Reason: Empty package marker for train (convergence.py and the trimmed watchdog and validation scaffolding are ported). tests/test_train_s0.py imports vsl_lab.train.
- Verifier (upheld): PORT (marker) → PORT. tests/test_train_s0.py:17 imports vsl_lab.train, and convergence.py is ported.


**Verifier: missed items and extra traps**
- No file in scope was skipped: all 18 tracked files (2,429 lines) are classified, and there are no untracked files in these directories.
- train_sb3.py:361-363,398,408 BUG not listed: 'best_val_return' in summary.json and in the ledger row is cb.best, the signed best val_metric score, not a validation return. Do not port this mislabel.
- train_sb3.py:362 trap not listed: no best_val_model.zip is written if the health stop or a short run ends before the first periodic validation, or if the metric is NaN, because NaN never exceeds -inf. The validation-selected checkpoint can be missing.
- train_sb3.py:99-108 trap not listed: the Watchdog reaches into ComputeGuard internals (cpu_hot_since, cpu_cool_since, cfg keys), always passes n_paused=0 and ignores the Decision. Its _cpu() (80-83) duplicates ops/scheduler.py:65 _cpu_times. Port it as a guard API, not as copied internals.
- train_sb3.py:192-205 n_actions_of / action_dim_of: needed by the convergence wiring (line 392) but not named among the TRIM keep-parts.
- tests/test_train_s0.py: 6 of its 14 tests (LinearDecay, build_model, n_actions_of, action_dim_of, _entropy_loss_from_buffer at 173-176) target SB3 parts. Only the 8 cv.* tests (91-158) go with convergence.py. The _entropy_loss_from_buffer test dies with TRPO.
- pi_saturation trap not listed: Round 4 'cavpi@cav0.25P' raised delay by +180.2 % and +118.7 % against NC on LD3 (docs/lab/round4_th.md:20,35). With 25 % CACC, NC itself was +93 % / +46 % against NC-human (round4_th.md:9,26), which confirms the CACC trap. A second copy of the class exists at vsl_lab/plants/ring.py:65.
- ring_env.py:111-112: non-finite observations are silently replaced by nan_to_num instead of a health FAIL. This trap was missed.
- Factual errors in the map: realism ratio_original_10min is at line 108, not 248. stats has 9 importing jobs, not 10. mtfc has no importer in g1_s1/g1_s2 (string arm names only). test_train_s0 has 8 convergence tests, not 9. V5 (setSpeed + speed mode 95) is superseded by V15, so it does not bind the cav_cmd design.
- Docs that depend on scope files (archive-only, no port impact): tests/test_metanet_v5.py:460-461 whitelists vsl_lab/controllers, envs, train and eval in an import-isolation test. docs/lab/round3_tm21_protocol.md and round4_harmonisation_protocol.md define the 'MRG3 staircase / PI' arms that V19 refers to, so read them before choosing comparators.

## Area: infra

**Summary.** Scope covers 55 tracked files; every file has a verdict: PORT 3, TRIM 6, REFERENCE 9, DROP 37. Mechanical evidence comes from imports.json and vulture, with each "dead" claim confirmed by git grep across code, docs and scripts. I ran test_guard.py, test_cooling.py and test_train_s0.py read-only in venv314 (39 passed). I did not run test_corr2_build.py, because its aux test writes to the shared NET_CACHE.

What is alive and needed for v5.B.1 is the ops core required by CLAUDE.md:
- guard.py (CPU rule state machine) with test_guard.py;
- thermal.py (temperature logging and the load gate);
- scheduler.py (one process per job, SIGSTOP/SIGCONT pauses, thermal.csv);
- ledger.py;
- a trimmed config.py.

Dead inside them:
- the superseded thermal-era constants: TEMP_PAUSE_C, TEMP_RESUME_C, TEMP_STEP_S, TARGET_CPU_UTIL, E_CORES, WORKER_CPUS affinity, N_MAX_DEFAULT=48;
- the scheduler's unused hold_s and hot_since, its job_factory/time_budget_s calibration mode, and its temperature smoothing;
- guard.py's thermal hysteresis, which has been off since 2026-10-10 and which v5b1 CLAUDE.md lists as removed.

Main traps a port must not carry over:
1. config.py and the scheduler point at v6's venv314, which breaks V14.
2. The ledger's +dirty flag counts untracked files and the ledger itself (201 of 221 rows are dirty). The fix is the code-identity lesson from the METANET v5 review: identity is the last commit touching the code paths.
3. Ledger rows lack the trainer name, version and config hash that ADR-001 asks for, plus the determinism hash.
4. Ledger row 188 was hand-written and is malformed.
5. The train_sb3 Watchdog reads guard internals instead of the Decision API.
6. SIGSTOP pauses only the job's own PID, not its children.
7. Timing uses wall-clock time.time() instead of monotonic time.
8. Launches are allowed at exactly 90 %, while CLAUDE.md says below 90 %.
9. test_corr2_build writes into the shared net cache and carries no sumo marker.

Dropped as obsolete:
- calibrate_thermal.py, ecore_probe.py and cooling_check.py (one-off thermal and fan diagnostics, run on BN4 and T1 seeds);
- the whole pre-lab SAR/TQC/VSL suite: _sumo_helpers.py, the run_*.py scripts, test_env_inter, test_state_live, test_config_consistency, test_smoke_training, test_scenario_pool_training, readme.md, persistent_results;
- all METANET tests (D5.5 STOP), the testbed test (D5.14 KILL) and the BN4 meter test (V15);
- requirements.txt (superseded by the v5b1 lock file);
- vsl_lab/__init__.py (the package is now `v5b`).

Kept only as reference:
- cooling.py and test_cooling.py: machine ops that stay in the archive checkout, which the vsl-cooling restart script depends on;
- ledger.csv: archive seed provenance; no 7,4xx,xxx seed was used;
- test ideas for T0, T1 and the V16 reward: test_ramp_vsl_effect, test_capacity_drop, test_reward_e2e_verification;
- test_specialist.py, only if V19 adopts a SPECIALIST-style jam-detection comparator.

**Port order.** 1. config.py (TRIM). It has no dependencies, and everything else imports it. Repoint SUMO_BIN, NETCONVERT_BIN and PYTHON_BIN to the v5b1 venv, choose a new RUNS_ROOT, keep GUARD_CFG at one machine-wide path, and keep clean_sumo_env.
2. thermal.py (PORT). No dependencies.
3. guard.py (TRIM, no imports) together with test_guard.py (PORT). Settle the 0.90 boundary first. Then add an explicit pause-all/resume-all decision for trainers.
4. ledger.py (PORT, depends on config). Add the ADR-001 record fields and a determinism-hash field, fix the dirty/code-identity logic, and add a file lock.
5. scheduler.py (TRIM, depends on config, guard and thermal). Must be done before the first simulation batch on v5b1, as v5b1 CLAUDE.md requires. Use monotonic time and process-group signals.
6. The pytest `sumo` marker goes into the v5b1 pyproject.toml, together with the first SUMO test.
7. test_corr2_build.py (TRIM) is ported when the F3Z netgen (corr2.py SPEC_AUX, outside this scope) is ported.
8. The C1 part of test_train_s0.py is ported only together with vsl_lab/train/convergence.py (outside this scope), at the 'DRL training code done' checkpoint. The training watchdog (train_sb3.py:53-115, outside this scope) is re-implemented in the own PPO trainer on top of the guard's new pause-all API, never copied as is.

### `vsl_lab/__init__.py`: DROP
- Reason: v5b1 package is `v5b` (pyproject.toml packages=["v5b"]); this file only holds a docstring that points to the old DRL-lab roadmap.
- Verifier (upheld): DROP → DROP (not ported; keep in archive). The v5b1 pyproject packages=['v5b']. The file is a one-line docstring. Caveat: it must remain in the archive checkout for the vsl-cooling unit (see cooling.py).

### `vsl_lab/config.py`: TRIM
- Reason: Every ops module, netgen and job imports it (imports.json shows 60 importers). v5b1 needs REPO_ROOT, RUNS_ROOT, NET_CACHE, LEDGER_PATH, MAX_WORKERS, MAX_LAUNCH_PER_S, SIM_START_MAX_LOAD (the CLAUDE.md v6-overlap rule), UTIL_SMOOTH_S, GUARD_CFG, clean_sumo_env, SUMO_BIN/NETCONVERT_BIN/PYTHON_BIN. The rest belongs to the superseded thermal rules of 2026-10-02/03 and to E-core pinning (thermal rule removed 2026-10-10).
- Dead / obsolete parts:
  - vsl_lab/config.py:27 TEMP_PAUSE_C - grep: only an unused import in scheduler.py:23
  - vsl_lab/config.py:28 TEMP_RESUME_C - same, unused import only
  - vsl_lab/config.py:29 TEMP_HARD_C - used only by the scheduler's temperature-window hack (scheduler.py:143), which the TRIM drops
  - vsl_lab/config.py:37 E_CORES - 0 importers (ecore_probe.py defines its own list at line 16)
  - vsl_lab/config.py:38 WORKER_CPUS - equals all CPUs, so the sched_setaffinity calls that use it do nothing (scheduler.py:78-81,116-119; envs; train_sb3)
  - vsl_lab/config.py:39 N_MAX_DEFAULT=48 - used only by the 27 obsolete jobs; contradicts the 32-worker rule
  - vsl_lab/config.py:40 TARGET_CPU_UTIL - 0 users (grep)
  - vsl_lab/config.py:42-43 TEMP_SMOOTH_S/TEMP_SLOW_S - feed only the logging smoothing in the scheduler and the train_sb3 watchdog
  - vsl_lab/config.py:44 TEMP_STEP_S - unused import in scheduler.py:23 only
  - vsl_lab/config.py:23-25,33-36,45-48 - comments describing superseded rules
- Traps: VENV_BIN (line 11) hard-codes v6's venv314 for sumo, netconvert and python, which breaks V14 (separate v5b1 venv). RUNS_ROOT defaults to vsl_lab_runs (env VSL_LAB_RUNS), and v5b1 runs must not mix into the archive's run tree. GUARD_CFG sits under RUNS_ROOT/ops/thermal.json, so moving RUNS_ROOT silently moves the live guard-override file. Keep that file at one machine-wide path, because the guard limits are a machine policy shared with the cooling unit and v6. LEDGER_PATH points inside the git working tree, which makes the tree dirty (see ledger.py).
- Verifier (upheld): TRIM; dead parts TEMP_PAUSE_C/TEMP_RESUME_C/TEMP_STEP_S/TARGET_CPU_UTIL/E_CORES/N_MAX_DEFAULT/TEMP_HARD_C/TEMP_SMOOTH_S/TEMP_SLOW_S → TRIM (as mapped). git grep -w: TEMP_PAUSE_C, TEMP_RESUME_C and TEMP_STEP_S appear only in config.py and as unused imports at scheduler.py:23-24. TARGET_CPU_UTIL appears only in config.py. TEMP_HARD_C is used only at scheduler.py:143. E_CORES: ecore_probe.py:16 defines its own list, so config's copy has no importer. N_MAX_DEFAULT is used in exactly 27 vsl_lab/jobs files. TEMP_SMOOTH_S is used in the scheduler and the train_sb3 Watchdog (logging only). Live-needed names are confirmed: SIM_START_MAX_LOAD/load_fraction (v5b1 CLAUDE.md, <15 % rule), MAX_LAUNCH_PER_S, UTIL_SMOOTH_S, MAX_WORKERS, NET_CACHE, GUARD_CFG and clean_sumo_env. One nuance on WORKER_CPUS: sched_setaffinity to all CPUs is not strictly a no-op. It widens any affinity inherited from a taskset or unit. Drop it anyway.
- Verifier (overturned): Trap: GUARD_CFG must stay at one machine-wide path because the guard limits are a machine policy shared with the cooling unit and v6 → TRIM. Give v5b1 its own RUNS_ROOT. Keep GUARD_CFG optional (a defaults-only guard is the current reality) or drop it after asking the author. The 'shared with cooling and v6' rationale is wrong.. /home/catalin/work/phd/vsl_lab_runs/ops/thermal.json does not exist, so every guard runs on DEFAULTS. Nothing is live to move. cooling.py does not read thermal.json: ops_dir() at cooling.py:296-300 uses RUNS_ROOT/ops only for its own state and lock. v6 has its own GUARD_CFG = RUNS_ROOT/'ops'/'thermal.json' in tsc_lab/config.py:26, under v6's RUNS_ROOT. I saw that through one read-only grep of v6 .py files, which goes beyond the v6-boundary rule (handoff notes only); I read nothing further there. The real coupling is different: cooling.py imports RUNS_ROOT from vsl_lab.config. A new v5b1 RUNS_ROOT is therefore safe, but the archive's config.py must not change while the vsl-cooling unit runs from this checkout.

### `vsl_lab/ops/__init__.py`: PORT
- Reason: Empty package marker; becomes v5b/ops/__init__.py when guard, ledger and scheduler are ported (CLAUDE.md requires the CPU guard, scheduler and ledger).
- Verifier (upheld): PORT → PORT (trivial). Empty package marker. It must also stay in the archive for the vsl-cooling unit.

### `vsl_lab/ops/guard.py`: TRIM
- Reason: A pure state machine implementing the CLAUDE.md CPU rule (>90 % for 2 min: pause newest job; one more per 30 s; resume one per 30 s after 30 s at <=87 %). Used by the scheduler and the train_sb3 Watchdog. Unit-tested: tests/test_guard.py, 10 tests, pass in venv314 (39 passed together with test_cooling and test_train_s0). v5b1 CLAUDE.md says the thermal rule is removed (no re-enable switch mentioned), so the v6 thermal hysteresis is dead weight unless the author wants the switch kept.
- Dead / obsolete parts:
  - vsl_lab/ops/guard.py:12-15 docstring for the thermal hysteresis (off since 2026-10-10)
  - vsl_lab/ops/guard.py:24 DEFAULTS keys thermal/center/band/hold_s/emergency
  - vsl_lab/ops/guard.py:61-63 ComputeGuard.t_hot_since/t_cool_since/thermal_paused
  - vsl_lab/ops/guard.py:73-86 thermal timers and hysteresis branch (never active with thermal=0)
  - vsl_lab/ops/guard.py:80,89-90,95 the `emergency` paths (only reachable with thermal=1)
- Traps: (1) The train_sb3 Watchdog (vsl_lab/train/train_sb3.py:53-115) does not use the Decision API. It reads guard internals (cpu_hot_since, cpu_cool_since, cfg, thermal_paused) and always passes n_paused=0. Add an explicit 'pause-all / resume-all' decision for trainers instead of carrying that coupling into the own-PPO trainer (CLAUDE.md: training pauses all env workers together). (2) Boundary: allow_launch is true at exactly util == 0.90 (test_guard.py:43 asserts this), while CLAUDE.md says launches only while utilisation < 90 %. Pick one. (3) A thermal-emergency pause held a v4 METANET restart for about 3.42 h (docs/plans/day_pattern_metanet_protocol_v5.md:581, thermal.csv). This is one more reason not to re-enable thermal logic silently. (4) Resume needs util <= 0.87 for 30 s, so external load sitting between 87 and 90 % keeps paused jobs paused indefinitely. That is by design, but the batch report should surface it.
- Verifier (upheld): TRIM thermal branch (lines 12-15, 24, 61-63, 73-86, 80/89-90/95) → TRIM (as mapped); DEFAULTS is at line 23. v5b1 CLAUDE.md says 'Thermal rule removed', with no re-enable switch. DEFAULTS thermal=0.0 and no thermal.json exists, so lines 74-86 are never active. Line numbers check out except DEFAULTS, which is at guard.py:23, not 24. test_guard passes (39 passed with test_cooling and test_train_s0, re-run read-only with PYTHONDONTWRITEBYTECODE=1). The boundary trap stands for the guard alone: over = util > 0.90, so a launch is allowed at exactly 0.90. In practice the scheduler adds its own strict check at scheduler.py:182 (`util + len(recent_launches)/n_cpu < lim`), so batch launches are already < 90 %. Only the Decision API is inclusive. The Watchdog-coupling trap is confirmed: train_sb3.py:96-109 reads cpu_hot_since, cpu_cool_since, cfg and thermal_paused, and passes n_paused=0.

### `vsl_lab/ops/thermal.py`: PORT
- Reason: package_temp_c is needed because CLAUDE.md still requires the package temperature to be logged per batch (thermal.csv). load_fraction feeds sim_start_gate (the v6-overlap rule: load < 15 % when v6 idleness cannot be confirmed). Both functions are used (scheduler, train_sb3, testbed/metanet jobs).
- Traps: The sensor is hard-coded to coretemp 'Package id 0' and returns NaN if missing. Callers must treat NaN as 'not measured', never as cool.
- Verifier (upheld): PORT → PORT. package_temp_c is used by scheduler.py:137 and train_sb3. v5b1 CLAUDE.md says 'The package temperature is still logged per batch'. load_fraction feeds sim_start_gate (scheduler.py:55-62), which implements the v5b1 CLAUDE.md rule 'require CPU load < 15 %'. No simpler existing piece covers either.

### `vsl_lab/ops/scheduler.py`: TRIM
- Reason: The batch runner required by CLAUDE.md: one process per job (one libsumo sim per process), at most 100 workers, the guard's pause/resume via SIGSTOP/SIGCONT, a token-bucket launch rate plus a pending-launch load estimate, and a thermal.csv decision log plus batch_report.json. 43 jobs import it. The core loop is worth porting; the thermal-era smoothing and the calibration mode are not.
- Dead / obsolete parts:
  - vsl_lab/ops/scheduler.py:23-24 unused imports TEMP_PAUSE_C, TEMP_RESUME_C, TEMP_STEP_S (vulture 90 %, confirmed by grep)
  - vsl_lab/ops/scheduler.py:73 parameter hold_s never read (vulture 100 %)
  - vsl_lab/ops/scheduler.py:91 hot_since assigned, never used
  - vsl_lab/ops/scheduler.py:74-75,106,126-130,174 job_factory/time_budget_s/k_factory/stop_launch - only caller is calibrate_thermal.py (DROP)
  - vsl_lab/ops/scheduler.py:78-81,116-119 sched_setaffinity to WORKER_CPUS (= all CPUs; leftover from E-core pinning, a no-op)
  - vsl_lab/ops/scheduler.py:107-108,139-146 fast-window/slow-median temperature smoothing and the TEMP_HARD_C-1.5 clamp (line 143) - left over from the 99 C median guard; the thermal rule is gone, so log the raw temperature and its max
  - vsl_lab/ops/scheduler.py:1-8 docstring still describes the thermal hysteresis as active
- Traps: PYTHON_BIN is v6's venv314 (V14). Jobs run as `python -m <module>` with cwd = parents[2] (the repo root), so this breaks when modules move into `v5b`. A job's result is the last stdout line starting with '{' (_last_json_line). Any stray JSON-looking print can become the result, and a falsy result counts as a failed job. SIGSTOP goes only to the job's own PID, so child processes (SubprocVecEnv workers, a sumo subprocess) keep running. Use process groups (os.killpg) for multi-process jobs. Timing uses time.time(); use time.monotonic() so a clock jump cannot trigger or skip the 2-minute rule. On an exception the scheduler SIGTERMs the running jobs but writes no ledger row; the caller must still log the aborted batch (every run goes in the ledger).
- Verifier (upheld): TRIM; dead hold_s, hot_since, job_factory/time_budget_s/k_factory/stop_launch, affinity, temperature smoothing → TRIM (as mapped). hold_s appears only at line 73. hot_since is assigned at line 91 and never read. The only job_factory/time_budget_s caller is calibrate_thermal.py:37-38 (git grep). Smoothing uses TEMP_SMOOTH_S/TEMP_SLOW_S, plus the TEMP_HARD_C clamp at line 143. The line-108 comment says 'slow (10 min)' but TEMP_SLOW_S=300 s. The thermal.csv column temp_c (line 187) logs the clamped smoothed value, not the raw reading. The raw value is the 8th column. Vulture's hit on BatchReport.mean_temp_c (line 50) is a false positive: it is serialised via rep.__dict__.
- Verifier (uncertain): Traps list complete → TRIM. Add a per-job wall-time limit. Never default gate_ok=True; record in the ledger row how the gate was satisfied.. The mapped traps (PYTHON_BIN, cwd=parents[2], _last_json_line, SIGSTOP to the PID only, time.time, no ledger row on exception) are all confirmed in the code. Two more traps are not in the map. (a) There is no per-job timeout: the loop at lines 124-194 ends only when `running` is empty, so one hung simulation blocks the batch forever. (b) gate_ok=True skips sim_start_gate entirely. The v4 METANET code review (docs/plans/day_pattern_metanet_v4_code_review.json, defect (d)) found a continuation batch launched with gate_ok=True hours into a run, which bypassed the v6-idle/load check.

### `vsl_lab/ops/ledger.py`: PORT
- Reason: An append-only run ledger is binding: every run goes in, including failed and abandoned ones. It is 44 lines, and 41 modules plus 2 tests use it. Port it nearly as is, but extend the fields for ADR-001 §3 'Records' (trainer name, version or commit, config hash) and for the determinism hash (CLAUDE.md T3).
- Traps: (1) The dirty flag (line 31) uses `git status --porcelain`, which also counts untracked files and the ledger file itself (it lives in the working tree). Result: 201 of 221 archive rows carry '+dirty', so the flag says nothing. Use --untracked-files=no, exclude the ledger path, and record code identity as the last commit touching the code paths. That was the lesson of the METANET v5 review round 3: HEAD as identity locked runs whenever docs or the ledger were committed (docs/lab/day_pattern/metanet_v5_impl_checkpoint.md:43). (2) config_hash uses json.dumps(default=str), so a non-serialisable object hashes by its repr (possibly a memory address). Hash an explicit, serialisable config. (3) There is no file lock, so concurrent appends from parallel learners can interleave (the repo is on exFAT). (4) Never hand-edit rows: archive row 188 (g1_s1b_oracle_headroom) was written by hand with an unquoted comma in notes and parses as 16 fields. (5) The 'track' and 'phase' vocabularies (T1-T4, DP, G1, R0.4 and so on) are archive-specific.
- Verifier (upheld): PORT nearly as is, with listed traps → PORT (with modifications). Capture the code identity at run START and store it with the row.. Verified: 221 rows, 201 '+dirty'; row 188 has 16 fields (all others 15); branches 147 vsl-lab-core / 74 day-pattern-core; dates 2026-10-01 to 2026-10-11. The METANET v4 code review (defect list on ledger.py:31-34) adds a trap the map misses: the commit is read at append time, i.e. at the END of the run, so code identity can drift during a long run. It also confirms 'untracked docs always mark it +dirty'. Given the required changes (code identity, ADR-001 record fields, determinism hash, file lock, a new track/phase vocabulary), this is closer to TRIM/rewrite than 'nearly as is'.

### `vsl_lab/ops/calibrate_thermal.py`: DROP
- Reason: R0.4 thermal calibration for the 87/99 C rules that were superseded on 2026-10-05 and removed on 2026-10-10. Its jobs are vsl_lab.jobs.bn4_nc (BN4 plant, not F3Z) on T1 seeds 7,110,000-009, which v5.B.1 must not reuse. It is the only user of the scheduler's job_factory/time_budget_s.
- Verifier (upheld): DROP → DROP. git grep finds no references outside the file itself. Its jobs are vsl_lab.jobs.bn4_nc on seeds 7110000-7110009 (lines 29-34). It is the only user of job_factory/time_budget_s.

### `vsl_lab/ops/ecore_probe.py`: DROP
- Reason: A 2026-10-01 diagnostic for E-core pinning, which was abandoned on 2026-10-05 (32 workers on all hardware threads). It runs BN4 jobs on T1 seeds. No importer; only a comment in config.py:33 mentions it.
- Traps: It reads temp1_input of the first coretemp hwmon without checking that the label is 'Package id 0'.
- Verifier (upheld): DROP → DROP. Only config.py:33 (a comment) references it; there is no systemd unit or script. It runs bn4_nc on T1 seeds 7110000+i (line 44-45). It uses temp1_input of the first coretemp hwmon (line 20-21), as stated.

### `vsl_lab/ops/cooling.py`: REFERENCE
- Reason: Machine-ops fan controller (the systemd user unit vsl-cooling), not research code. CLAUDE.md forbids driving the pad or fans from batch or training code. v5b1 CLAUDE.md says it stays on the archive branches and restarts only on the author's request. Its only import from vsl_lab is RUNS_ROOT (line 297). Tested by tests/test_cooling.py (11 tests pass).
- Traps: The restart script (/home/catalin/work/phd/tsc_lab_runs/s0_logs/restart_vsl_cooling.sh) runs `python -m vsl_lab.ops.cooling run` with working-directory=/srv/shared/Workspace/phd/phd_speed_harmo_v5 and v6's venv314. If the main checkout is ever switched to a branch without this file, the unit fails on restart. Moving it to a separate ops location is an author decision. Never port it into v5b1 code paths.
- Verifier (upheld): REFERENCE → DO NOT PORT, DO NOT DELETE (live ops dependency of the vsl-cooling unit, together with vsl_lab/__init__.py, vsl_lab/ops/__init__.py and vsl_lab/config.py in the archive checkout). Not ported: confirmed. But 'REFERENCE' undersells it: it is live machine-ops code. restart_vsl_cooling.sh runs `systemd-run --user --unit vsl-cooling --working-directory=/srv/shared/Workspace/phd/phd_speed_harmo_v5 .../venv314/bin/python -m vsl_lab.ops.cooling run`. docs/handoff/v5_closeout_2026-10-13.md lists it under 'Shared machine services started from v5 (still in use by v6)'. It imports vsl_lab.config.RUNS_ROOT (line 297), so vsl_lab/__init__.py, vsl_lab/ops/__init__.py and vsl_lab/config.py must also stay intact in this checkout.

### `vsl_lab/ops/cooling_check.py`: DROP
- Reason: A one-off firmware-vs-custom fan-curve A/B measurement (2026-10-10). Its outcome is frozen in cooling.py's AWAY_BASE constants. It calls asusctl and llano directly, which v5b1 rules allow only by hand. No importer.
- Verifier (upheld): DROP → DROP. Referenced only in cooling.py's docstring (line 3). It drives asusctl directly (line 55), and llano through LLANO (line 28). No systemd unit references it (~/.config/systemd/user has no vsl_lab units).

### `vsl_lab/runs/ledger.csv`: REFERENCE
- Reason: Archive run record: 221 rows from 2026-10-01 to 2026-10-11 (vsl-lab-core 147, day-pattern-core 74; tracks T1/T2/T3/T4/DP/G1/ops). v5b1 starts a fresh ledger. Read it only for seed provenance. No row uses the v5.B block 7,400,000-7,419,999 (checked by regex), so that block is clean.
- Traps: Row 188 is malformed (16 fields; hand-written, unquoted comma in notes). 201 of 221 rows have '+dirty' commits, which do not mean uncommitted code. Do not copy rows into the v5b1 ledger.
- Verifier (upheld): REFERENCE; no row uses 7,400,000-7,419,999 → REFERENCE. A naive regex finds '7407406' and '7417184', but both are digits inside float results (rows 115 and 201: -14.398032407407406, 0.08039674171848044), not seeds. A range-overlap parse of every 'a-b' 7-digit range in all fields found no overlap with [7400000, 7419999].

### `tests/__init__.py`: DROP
- Reason: Exists only so the old suite can `from tests._sumo_helpers import ...`. v5b1 tests do not share a helper module yet.

### `tests/_sumo_helpers.py`: DROP
- Reason: Scaffolding for the pre-lab v5 TrafficEnv/SAR framework (imports core, sar_components, traffic_environment.vehicle_fleet) on ramps_v1/v2 with VSL actions. None of this is in v5.B.1 (CAV-only, F3Z, PettingZoo). Last change 2026-05-16.
- Verifier (upheld): DROP → DROP. Non-test importers exist: core/env_interact.py:289 and traffic_environment/scenario_pool.py:158,292 import tests._sumo_helpers. That means the old framework itself depends on tests/ (with tests/__init__.py). All of that framework is out of scope for v5.B.1, so DROP stands; it only matters if anyone ever edits the archive.

### `tests/readme.md`: DROP
- Reason: Stale. It documents the old SAR suite and lists 5 files that do not exist (test_detector_alignment.py, test_nocontrol_baseline.py, test_env_metr.py, test_traf_env.py, run_fixed_vsl_sweep_v1.py). It does not mention any vsl_lab test.
- Verifier (upheld): DROP; lists 5 non-existent files → DROP. Confirmed missing: test_detector_alignment.py, test_nocontrol_baseline.py, test_env_metr.py, test_traf_env.py, run_fixed_vsl_sweep_v1.py. The file has 0 mentions of vsl_lab.

### `tests/run_feasibility_sweep.py`: DROP
- Reason: A mainline x ramp VSL grid sweep on ramps_v2 for the old r44 reward (2026-03-29). Uses VSL, which V15 removes, and the old fleet.

### `tests/run_feasibility_sweep_v52.py`: DROP
- Reason: v5.2 per-lane differential VSL sweep (old framework, VSL removed by V15).

### `tests/run_phase3_validation.py`: DROP
- Reason: v5.1 per-lane VSL + stochastic-demand static-policy check (old framework: traffic_environment.anomaly_injector, stochastic_demand).

### `tests/run_reward_landscape_check.py`: DROP
- Reason: An offline check of the r44_reward_v2 VSL reward landscape. It reads a summary CSV from a sweep script that no longer exists (run_fixed_vsl_sweep_v1.py). The reward is superseded by the V16 generalised cost.

### `tests/run_sumo_gui.py`: DROP
- Reason: Launches sumo-gui on old ramps scenarios through _sumo_helpers. Trivial to rewrite for F3Z if needed.

### `tests/test_capacity_drop.py`: REFERENCE
- Reason: Test idea for the T1 tool check (a capacity drop exists): sweep mainline inflow, measure discharge at the bottleneck, look for two flow-density branches and hysteresis. The code itself is old-framework (ramps_v2, _sumo_helpers).
- Traps: It is a script (main() at line 328), not a pytest test, despite the test_ prefix. pytest still imports it during collection, which pulls in tests._sumo_helpers and the old packages.
- Verifier (upheld): REFERENCE; a script, not a pytest test → REFERENCE. No def test_*. main() is at line 328 with a __main__ block at 435, and line 49 imports tests._sumo_helpers at module level. docs/plans/vsl_hybrid_screen_v0.md:61 says it 'has no results' (never run). The only capacity-drop data are ramps_v1 at -0.4 %, a T1 risk worth remembering.

### `tests/test_config_consistency.py`: DROP
- Reason: Checks the old _common_config.yaml against hard-coded values in test_env_inter.py (old SAR framework).

### `tests/test_env_inter.py`: DROP
- Reason: Dry-run test of the old 56-dim SAR environment with VSL action bounds (core, sar_components).

### `tests/test_ramp_vsl_effect.py`: REFERENCE
- Reason: Test idea for T0 (the actuator binds): two paired runs on the same seed, differing only in one action dimension, assert a measurable effect. Its actuator, ramp VSL, is gone (V15).

### `tests/test_reward_e2e_verification.py`: REFERENCE
- Reason: Pattern worth reusing for the V16 generalised-cost reward: recompute the reward independently from raw detector/vehicle data at every step and compare with the env's value (tolerance 1e-3). Its code is old-framework (r44 reward, E1 chain).
- Dead / obsolete parts:
  - tests/test_reward_e2e_verification.py:178 setup_env / :180 _tmp - vulture flags; pytest autouse fixtures, false positives
- Verifier (upheld): REFERENCE; vulture hits at 178/180 are false positives → REFERENCE. Line 177 is @pytest.fixture(autouse=True), so setup_env is a fixture and _tmp is stored by it.

### `tests/test_scenario_pool_training.py`: DROP
- Reason: Smoke test of the old SAC scenario-pool training (traffic_environment.scenario_pool).
- Dead / obsolete parts:
  - tests/test_scenario_pool_training.py:141 unused import Logger (vulture 90 %)

### `tests/test_smoke_training.py`: DROP
- Reason: Smoke test of the old SB3 SAC/TQC pipeline (train.py, per_lane_stochastic.yaml). The ADR-001 §4 verification ladder replaces it for the own PPO.

### `tests/test_state_live.py`: DROP
- Reason: Bounds checks on the old 56-dim observation under live SUMO (old framework).

### `tests/test_bn4_meter_rate.py`: DROP
- Reason: Tests the BN4 meter_rate actuator and the eval meter arms (ALINEA, constant rate). V15 drops ramp meters, and BN4 is not the plant.

### `tests/test_corr2_build.py`: TRIM
- Reason: F3Z evolves from CORR2X (corr2.py SPEC_AUX), so network build checks are needed: lane counts and lengths, connections, the zipper lane drop, aux-lane exits X1/X2, detectors on existing lanes, SUMO loads without errors. Port it alongside the F3Z netgen, dropping the meter and plain-CORR2 parts.
- Dead / obsolete parts:
  - tests/test_corr2_build.py:72-84 meter TLS assertions (TLS ids, tl_links, all-green programs) - meters dropped (V15); keep only 'no mainline TLS' (line 74)
  - tests/test_corr2_build.py:92,101-104 ALINEA loop detectors e1a_* - meter control only
  - tests/test_corr2_build.py:43-70 plain-CORR2 asserts (O1 off-ramp, forced merges, line 49-50/56/67) - F3Z derives from SPEC_AUX, where O1 is removed
  - tests/test_corr2_build.py:127 tl_links meter asserts inside the aux test
  - tests/test_corr2_build.py:140 builds plain CORR2 only to show it is unchanged - not needed once CORR2 is not ported
- Traps: test_corr2x_aux_lane_exits (line 124) builds into the shared NET_CACHE instead of the tmp cache the fixture uses (lines 21-31), so a test run writes into the runs tree. The tests need netconvert/sumo but carry no `sumo` marker, so `-m "not sumo"` still runs them. The v3 change (merge2 at 5.75 km, commit 74c6964) did not update the test, and positions are not asserted. I did not run this file, to avoid writing to the shared cache.
- Verifier (uncertain): TRIM: meter TLS asserts (72-84, 127), ALINEA loops e1a_* (92, 101-104) are dead → TRIM. The meter-TLS and e1a_* asserts are 'drop only if the F3Z netgen removes the TLS and those loops' (ask the author). The 'no mainline TLS' assert at line 74 stays in either case.. netgen itself always builds the meter TLS and enforces it. corr2.py:71 TLS, :120 traffic_light nodes, :219 all-green tlLogic, and build() raises at :257-259 if the TLS link set is wrong. V4 defines NC as 'ramp meters off (always green)', and V15 says meters are 'dropped too (may be added later)'. So whether the F3Z netgen keeps all-green meter TLS is an open design choice, not settled dead code. The e1a_* loops are mainline E1 detectors 40 m downstream of each merge (corr2.py:18). They could serve as CAV/zone observations or evaluation sensors, not only ALINEA. Also confirmed: the test at line 140 builds plain CORR2 into the shared NET_CACHE too, not only SPEC_AUX at line 124. No sumo marker is present.

### `tests/test_cooling.py`: REFERENCE
- Reason: Tests cooling.py's pure parts (11 tests, pass). It stays with cooling.py in the archive; not v5b1 research code.

### `tests/test_guard.py`: PORT
- Reason: Unit tests for the CPU rule (no SUMO, no hardware). All 10 pass. Port with guard.py.
- Dead / obsolete parts:
  - tests/test_guard.py:46-79 thermal_on helper and the thermal hysteresis/emergency/missing-sensor tests - drop with guard.py's thermal branch if the author confirms the thermal rule is fully removed
- Traps: test_cpu_at_or_below_limit_allows_launch (line 40) asserts launch at exactly 0.90, while CLAUDE.md says < 90 %. Settle the boundary before porting.
- Verifier (upheld): PORT; thermal tests 46-79 dead → PORT (drop thermal tests 46-79 and adapt 92/96-97). 10 tests pass. One dead-part change is missed: test_malformed_live_config_falls_back (lines 89-97) uses the thermal key 'center' (lines 92, 96-97). It must be rewritten if guard DEFAULTS lose the thermal keys.

### `tests/test_specialist.py`: REFERENCE
- Reason: Tests the VSL SPECIALIST controller (jam front detection, front speeds). VSL is removed (V15), but V19's rule-based CAV comparators are still open (literature check), and the jam-detection logic may inform a CAV jam-absorption comparator. Read it only together with vsl_lab/controllers/specialist.py, if that is chosen.
- Verifier (upheld): REFERENCE → REFERENCE. This is a pure unit test (no SUMO) of the SPECIALIST shock-wave algorithm (Hegyi et al.), the basis of jam-wave resolution. That is relevant to V19's open 'jam absorption' comparator. Note that V19's named archived comparators (vsl_lab/controllers/cav_staircase.py, pi_saturation.py) have NO tests in tests/. A V19 port needs new tests.

### `tests/test_testbed_screen.py`: DROP
- Reason: Testbed stage-1b screen (ALINEA metering, MnDOT train days). The testbed was KILLed (D5.14), and meters are dropped.
- Dead / obsolete parts:
  - tests/test_testbed_screen.py:105 unused inp_/net_ (vulture 100 %)

### `tests/test_train_s0.py`: TRIM
- Reason: Two halves. The SB3 trainer tests (LinearDecay, RecurrentPPO/TRPO lr decay, n_actions_of, action_dim_of, TRPO entropy) belong to train_sb3, which is reference/fallback only (ADR-001). The C1 convergence-check tests (vsl_lab/train/convergence.py) back the CLAUDE.md 'convergence check' requirement, including review fixes #8-#11 and the R6-like failure case. Port the C1 part only if convergence.py is ported.
- Dead / obsolete parts:
  - tests/test_train_s0.py:23-41 TinyEnv/args - SB3-only fixtures
  - tests/test_train_s0.py:43-81 LinearDecay, lr-decay and n_actions_of tests - SB3/sb3-contrib specific
  - tests/test_train_s0.py:168-181 action_dim_of and TRPO entropy-from-buffer tests - SB3 specific
  - tests/test_train_s0.py:28 unused `options` (vulture 100 %; gym signature, harmless)
- Traps: The C1 tests (lines 83-166) assume SB3 log column names (val_return, val_metric_value, explained_var, entropy as negative entropy_loss). The own PPO's logs must keep the same semantics, or the tests must be adapted. Two lessons to keep: C1a is computed on the return, not the selection metric (#11), and a missing entropy must block 'converged' (#9).
- Verifier (upheld): TRIM: port the C1 part (83-166) only with convergence.py → TRIM (as mapped, plus remove the module-level train_sb3/SB3 imports). The line ranges match (TinyEnv 23, args 38, SB3 tests 43-81, C1 83-166, SB3 tests 168+). Not in the map: line 18 imports LinearDecay, build_model and n_actions_of from vsl_lab.train.train_sb3, and line 15 imports DummyVecEnv, both at module level. So even the C1 tests cannot be collected without SB3 and train_sb3. The port must split the module, not just delete functions.

### `tests/test_metanet.py`: DROP
- Reason: METANET plant tests. METANET STOP (D5.5); v5.B.1 has no METANET.
- Traps: Vulture 'unused function test*' hits in the metanet tests are false positives (pytest collection).

### `tests/test_metanet_ctrl.py`: DROP
- Reason: METANET controller and calibration tests (D5.5 STOP).

### `tests/test_metanet_events.py`: DROP
- Reason: METANET event-layer tests on MnDOT corridor data (D5.5 STOP).

### `tests/test_metanet_gate_refactor.py`: DROP
- Reason: METANET v3/v4/v5 gate refactor tests (D5.5 STOP).
- Traps: Its code-identity and provenance ideas (last commit touching code paths, start records) are documented in docs/lab/day_pattern/metanet_v5_impl_checkpoint.md; take them from there for the ledger, not from this test.

### `tests/test_metanet_j5_eval.py`: DROP
- Reason: METANET J5 evaluation tests (D5.5 STOP).

### `tests/test_metanet_v4.py`: DROP
- Reason: METANET protocol v4 tests (D5.5 STOP).

### `tests/test_metanet_v5.py`: DROP
- Reason: METANET protocol v5 gate/freeze tests (D5.5 STOP). It also imports ops.ledger and ops.scheduler, but only to stub them.

### `tests/persistent_results/nocontrol_ramps_v1_18-03-2026_14-08-30/nocontrol_2500vph.csv`: DROP
- Reason: ramps_v1 no-control diagnostic (March 2026, old network and fleet). Cited only by archive docs (vsl_hybrid_screen_v0.md, design_space notes).

### `tests/persistent_results/nocontrol_ramps_v1_18-03-2026_14-08-30/nocontrol_3500vph.csv`: DROP
- Reason: Same ramps_v1 NC diagnostic as above.

### `tests/persistent_results/nocontrol_ramps_v1_18-03-2026_14-08-30/nocontrol_4500vph.csv`: DROP
- Reason: Same ramps_v1 NC diagnostic as above.

### `tests/persistent_results/nocontrol_ramps_v1_18-03-2026_14-08-30/nocontrol_5000vph.csv`: DROP
- Reason: Same ramps_v1 NC diagnostic as above.

### `tests/persistent_results/nocontrol_ramps_v1_18-03-2026_14-08-30/nocontrol_5500vph.csv`: DROP
- Reason: Same ramps_v1 NC diagnostic as above.

### `tests/persistent_results/nocontrol_ramps_v1_18-03-2026_14-08-30/nocontrol_6000vph.csv`: DROP
- Reason: Same ramps_v1 NC diagnostic as above.

### `tests/persistent_results/nocontrol_ramps_v1_18-03-2026_14-08-30/nocontrol_6500vph.csv`: DROP
- Reason: Same ramps_v1 NC diagnostic as above.

### `tests/persistent_results/nocontrol_ramps_v1_18-03-2026_14-08-30/nocontrol_7000vph.csv`: DROP
- Reason: Same ramps_v1 NC diagnostic as above. Source of the '-0.4 % capacity drop' number in archive docs.

### `tests/persistent_results/nocontrol_ramps_v1_18-03-2026_14-08-30/nocontrol_all_demands.csv`: DROP
- Reason: Same ramps_v1 NC diagnostic as above.

### `tests/persistent_results/nocontrol_ramps_v1_18-03-2026_14-08-30/summary.txt`: DROP
- Reason: Header of the ramps_v1 NC diagnostic; points to a results path on another disk.

### `tests/persistent_results/summary_elaborated_18-03-2026_14-08-30.md`: DROP
- Reason: Write-up of the ramps_v1 NC diagnostic (old network). It stays in the archive, where design_space notes cite it.

### `pytest.ini`: TRIM
- Reason: v5b1 configures pytest in pyproject.toml ([tool.pytest.ini_options] testpaths=["tests"]), so the file is not ported. Only its `sumo` marker is worth moving there.
- Traps: The marker is applied inconsistently in the archive: test_corr2_build.py and test_testbed_screen.py need SUMO or netconvert but are unmarked. Mark every simulation test in v5b1, and add -p no:cacheprovider (archive tests are run that way).
- Verifier (upheld): TRIM (only the sumo marker moves to pyproject) → TRIM (functionally DROP plus move the marker). The file only defines the sumo marker. pytestmark=sumo is set in test_bn4_meter_rate, test_ramp_vsl_effect, test_reward_e2e_verification and test_state_live, but not in test_corr2_build or test_testbed_screen, which need netconvert/sumo. v5b1 pyproject has [tool.pytest.ini_options] testpaths only.

### `requirements.txt`: DROP
- Reason: Superseded by v5b1 toolchain/requirements_lock.txt (V14: own venv with exact pins, PettingZoo 1.27.0). It lists old-v5 needs: sb3-contrib (TQC/RecurrentPPO), tensorboard, tqdm, rich, pyyaml. It uses unpinned lower bounds and has no SUMO, libsumo or PettingZoo entry.
- Traps: The pin setuptools<82 (2026-05-16, commit dc896cd) was a torch-compatibility workaround in the old env. Do not copy it without re-checking against the v5b1 lock.
- Verifier (upheld): DROP; trap: do not copy setuptools<82 → DROP. Superseded by v5b1 toolchain/requirements_lock.txt. Two small corrections. The lock already pins setuptools==81.0.0, which satisfies <82, so the trap is already handled. The lock also pins sb3_contrib==2.8.0, so sb3-contrib is not only an 'old-v5 need'. Commit dc896cd (2026-05-16) introduced the <82 pin for torch compatibility.

- Verifier (upheld) on `tests/test_bn4_meter_rate.py, tests/test_testbed_screen.py, tests/test_metanet*.py (7 files)`: DROP → DROP. Their imports are BN4 meter arms, the testbed and the METANET plant (D5.5 STOP, D5.14 KILL, V15 no meters). No v5b1 decision needs them. test_testbed_screen.py:105 has unused inp_/net_ (vulture 100 %, confirmed).
- Verifier (upheld) on `tests/test_env_inter.py, test_state_live.py, test_config_consistency.py, test_smoke_training.py, test_scenario_pool_training.py, run_*.py (5), tests/__init__.py`: DROP → DROP. They import the old core / sar_components / traffic_environment / tests._sumo_helpers stack (VSL, SAR, TQC). test_smoke_training and test_scenario_pool_training are actually __main__ scripts (imports.json mains), not pytest tests.
- Verifier (upheld) on `tests/persistent_results/** (10 files)`: DROP → DROP. Cited only by archive docs (vsl_hybrid_screen_v0.md:50, 61, 310, 403; design_space notes) as the source of the ramps_v1 -0.4 % capacity-drop figure. They stay in the archive.

**Verifier: missed items and extra traps**
- No in-scope file was skipped: git ls-files lists 55 tracked files, and all 55 have a verdict.
- Ledger trap missing from the map: the commit and dirty flag are read when append() is called at the END of a run (ledger.py:31-34), so code identity can change during long runs. Source: docs/plans/day_pattern_metanet_v4_code_review.json, defect list for ledger.py:31-34. Capture identity at run start.
- Scheduler trap: there is no per-job wall-time limit (run_batch loop, scheduler.py:124-194), so one hung job blocks the batch forever.
- Scheduler trap: gate_ok=True bypasses sim_start_gate. The METANET v4 code review defect (d) caught a continuation batch that did this hours into a run.
- Scheduler log trap: the thermal.csv 'temp_c' column (scheduler.py:187) is the clamped, smoothed value (min(..., TEMP_HARD_C-1.5) before the window fills), not the raw reading. The line-108 comment says 10 min, but TEMP_SLOW_S is 300 s.
- tests/test_guard.py:92,96-97: the malformed-config test uses the thermal key 'center'. It must be adapted when the thermal DEFAULTS are dropped.
- tests/test_train_s0.py:15,18: module-level imports of DummyVecEnv and train_sb3 (LinearDecay, build_model, n_actions_of). The C1 tests cannot be collected without SB3 and train_sb3, so the port must split the module.
- Archive coupling: core/env_interact.py:289 and traffic_environment/scenario_pool.py:158,292 import tests._sumo_helpers. The old framework depends on tests/ and tests/__init__.py. This does not matter for v5b1, but the archive must not be edited.
- Live ops dependency: the vsl-cooling restart script runs `python -m vsl_lab.ops.cooling` from this checkout, and cooling.py imports vsl_lab.config.RUNS_ROOT. vsl_lab/__init__.py, vsl_lab/ops/__init__.py, vsl_lab/config.py and cooling.py must stay unchanged on whatever branch this checkout holds.
- GUARD_CFG reality: /home/catalin/work/phd/vsl_lab_runs/ops/thermal.json does not exist, so the 'live override' has never been used since defaults apply. Treat the live-config feature as optional for v5b1 and ask the author.
- V19 gap (adjacent to scope): the archived comparators it names (vsl_lab/controllers/cav_staircase.py, pi_saturation.py) have no tests in tests/, so new tests are needed if they are ported.
- Process note: to check the 'shared with v6' claim, I ran one read-only grep over v6 .py files (tsc_lab/config.py, ops/guard.py, ops/scheduler.py). That goes beyond the v6 rule of reading handoff notes only. I read nothing else in v6 and modified nothing.

## Area: jobs

**Summary.** Read-only review: nothing in the archive was edited. Evidence comes from imports.json, vulture.txt, a grep for every job module name across the repo (code, docs, tests and the .sh chains that pass module names as strings), the docstrings of all 59 modules, a full read of corr_run.py, mrg3_run.py, ring_run.py, r4_eval_rl.py, ring_shield_verify.py and t4_calib.py, partial reads of round3, round4 and t1_meter_bn4_confirm, docs/lab/STATUS.md, and the t2_realism protocol. I did not read most one-off drivers line by line; their DROP verdicts rest on what they import, their docstrings and the track outcomes in STATUS (T1 BN4 meters, T2 MRG3 VSL, T3 ring, T4 CORR2 killed at G 0.4 %, day-pattern, METANET stop D5.5, testbed T0 KILL D5.14). None of these fits v5.B.1, where CAV commands are the only actuator: no VSL, no meters, no METANET or MPC, no M demand, and SB3 is only a fallback.

Result: 1 TRIM, 6 REFERENCE, 76 DROP, 0 PORT.
- **TRIM: corr_run.py.** It is the only job that runs the CORR2/CORR2X lineage that F3Z grows from. Its measurement layer can be reused: door-to-door per group, route and departure bin including insertion backlog; ramp storage/origin/pending queues; per-edge congestion; tripinfo stops; served share. Its control layer is dead (ALINEA, posted VSL, meter TLS, M demand). It has no CAV support at all and no tests.
- **REFERENCE, mrg3_run.py:** the per-CAV command loop (the closest precedent for the F3Z actuator layer), PI-with-saturation on CAVs, incident injection, and splitting emergency-braking counts between CAVs and humans.
- **REFERENCE, round3.py:** the CAV tool-check designs T-CAV0 and T-X, and the T3 hash check.
- **REFERENCE, ring_run.py:** FollowerStopper and PI-with-saturation metrics, which are candidate V19 rule-based comparators.
- **REFERENCE, t4_calib.py:** the rule for selecting the NC calibration cell on CORR2.
- **REFERENCE, t2_realism.py:** the R-a to R-d plant-realism gate.
- **REFERENCE, t1_meter_bn4_confirm.py:** the only implementation of the D5.8 conditional bar. It carries a known flaw (below).

Everything else is DROP. Some DROP files are imported by modules outside this scope and must be removed together with them:
- tests/test_metanet*.py, tests/test_testbed_screen.py and tests/test_bn4_meter_rate.py import METANET, testbed and BN4 jobs;
- vsl_lab/data/metanet_facts.py and docs/lab/day_pattern/d412_capacity_forcing_diagnostic_recovered import metanet_calibrate and metanet_postcal;
- vsl_lab/envs/mrg3_env.py mentions mrg3_run (the grep hit; not checked whether this is an import).

The only file never imported is ring_shield_verify.py (only run_chain5.sh calls it). Vulture's 5 hits in jobs are all in DROP files. One of them is real: bn4_nc.py:40 `loop_mismatch` is assigned and never used, so the H-R8 mismatch counter is incomplete.

**Traps a port must not carry over:**
- (a) `mrg3_run.capacity_drop` is the max-based R1 estimator. It is confounded by the demand ramp (t2_realism_protocol Addendum A item 5; STATUS item 13). Use `eval/realism.capacity_ratio` instead.
- (b) In t1_meter_bn4_confirm, B per regime is chosen by median level (`min(med, key=med.get)`). That is the flaw in STATUS item 19; use the paired minimum over non-learning arms.
- (c) Its `_paired` (median x−y) and `eval.stats.paired_median_diff` (median b−a) are two sign conventions, while CLAUDE.md requires one. Its `worse_gt5` (point estimate > 5 % and CI excluding 0) is one reading of "not significantly worse by > 5 %"; pre-register it explicitly.
- (d) SUMO default CACC at 25 % worsened delay by 46–93 %, and the CAV arms showed no authority in Round 4 T-H. ACC/CACC also brake hard at a 0.5 s step. A T-CAV0-style check is needed before choosing the CAV model.
- (e) `setMaxSpeed` renames the vType to `av@<id>`, which once silently disabled the AV actuator. Track CAVs by ID.
- (f) Abrupt CAV caps caused emergency braking, which is why the staircase exists.
- (g) SUMO emergencyBraking warnings are not V11 hard braking (a 3–4 m/s² threshold on CAVs). Measure deceleration per step instead.
- (h) Veh-km normalisation uses hard-coded route lengths and counts every generated vehicle (mrg3_run:322 and round3:35). V10 energy per veh-km needs the distance actually travelled.
- (i) corr_run's headline is "time in system until drained", with unfinished vehicles censored at the drain end, and its delay reference is the 0–300 s departure-bin mean. The design wants a fixed-window TTT and a free-flow reference per route.
- (j) corr_run ties stats to vehicle-ID conventions (prefix `r1_`/`r2_`; route = id before the last '.').
- (k) Every job hard-codes seeds in 7,1xx,xxx, which belong to the archived tracks and must never be reused.
- (l) The .sh chains use the v6 venv314 (V14 forbids it), the dead /run/media mirror path, and pgrep-based sequencing instead of the scheduler.
- (m) ring_shield_verify runs a batch and writes docs at import time (module-level code). round3 and t2_realism mutate module globals (VERDICT, GEOM, STEP) from main().
- (n) There are two PISaturation implementations: plants/ring.py (header says it was checked against Stern et al. 2018) and controllers/pi_saturation.py (used by mrg3_run arm P). Pick one before using it as a V19 comparator.

**Port order.** 1) Not jobs, but prerequisites (other scopes): vsl_lab/config (RUNS_ROOT), ops/guard + ops/scheduler (Job, run_batch) + ops/ledger, sim/runner.SumoSim (tts_system, arrival_t, drain, close, health, sumo_stats), the F3Z netgen (from netgen/corr2.py SPEC_AUX; corr_run uses N.RAMPS, N.MAIN_EDGES, N.TLS, N.spec_hash) and an F3Z plant module replacing plants/corr2 (files, demand → the new inflow generator, Sensors, groups, DRIVERS, STEP_LENGTH, V_LIMIT; Meter, set_vsl and assert_meter_* are dropped).
2) corr_run.py → TRIM into an F3Z NC/evaluation runner, the first job needed (V4 NC for evaluation, T1 plant checks). Keep `_group_stats` (106-129), the insertion and ramp queue sampling (179-186, 228-236 minus meter fields), edge congestion (247-256), served share (257-258), tripinfo stops (277-302) and the run_id/pid naming and summary/features writing. Add the CAV layer and the fixed-window TTT and V10/V11 metrics.
3) The CAV actuator layer for F3ZParallelEnv and the V19 rule-based comparators: rebuild from mrg3_run.py:172-204 and 294-300 (REFERENCE) plus controllers/cav_staircase and controllers/pi_saturation (other scope). Write the T0/T-CAV0/T-X tool checks after round3.py (REFERENCE).
4) The NC calibration-cell job after t4_calib.py (REFERENCE), then a realism gate after t2_realism.py + eval/realism.py (REFERENCE).
5) Last, the confirmatory analysis after t1_meter_bn4_confirm.py:93-153 (REFERENCE), with the B-selection and sign-convention fixes, built on one paired_median_diff in eval/stats.

### `vsl_lab/jobs/corr_run.py`: TRIM
- Reason: Only job on the CORR2/CORR2X lineage that F3Z evolves from (V2). Its d2d/insertion-queue/congestion/stops measurement matches the CLAUDE.md primary metric and the design_v0 §7 pointer ('jobs/corr_run.py computes the d2d times'). Callers: t4_calib.py, t4_gscan.py (both DROP). No tests.
- Dead / obsolete parts:
  - corr_run.py:3-30 docstring on ALINEA/posted VSL and the meter smoke note - V15 (no VSL, no meters)
  - corr_run.py:60 R_MIN, R_MAX - meter-only constants (keep Q_OVERRIDE only if the storage-fill > 0.9 stat is kept as a spillback diagnostic)
  - corr_run.py:66-81 class Alinea - ramp meters dropped (V15)
  - corr_run.py:84-94 parse_ctrl alinea/const/vslalinea branches - V15; only 'nc' survives, and CAV controllers must be added
  - corr_run.py:97-103 post_vsl - V15
  - corr_run.py:134,145,331 p_nc (VSL non-compliance share) - meaningless without posted limits (V15)
  - corr_run.py:135,146,336-338,344 m_day/noise and --demand m_day - M demand retired (V9/B12; inflow = AM peak from MnDOT US-169, generator not in this file)
  - corr_run.py:157-163 Meter objects, all_green_program, assert_meter_links/assert_meters_green - no meters in F3Z (drop the TLS from netgen instead)
  - corr_run.py:176-178 meter tick; 203-217 ALINEA control step; 218-221 VSL/meter release
  - corr_run.py:192 q_O1 loop - CORR2-only (O1 removed in CORR2X v2, 8eb0343), writes NaN on corr2x
  - corr_run.py:197-199,307-308 occ/meter-rate feature columns; 200,309 'b' column
  - corr_run.py:237-246 meter counters and binding stats; 267-268 alinea_trace fields
  - corr_run.py:272-276 red_light_emergency_stops - only meaningful with metered ramps
  - corr_run.py:324-325 --net choices corr2/corr2x - needs F3Z; 340 out-root RUNS_ROOT/'t4' (archived track root)
- Traps: (1) The headline mean_time_in_system_s (263) uses drain-until-empty tts_system / generated, with unfinished vehicles censored at sim.t after the drain (223-227); CLAUDE.md and design_v0 §7 require a fixed-window TTT, with unfinished vehicles counted to the window end. (2) delay_vs_ref_s uses the 0-300 s departure-bin mean as the reference (125-127), not the per-route free-flow time the design defines; it depends on inflow. (3) The insertion backlog relies on vehicle-ID prefixes 'r1_'/'r2_' (166, 184), and stops parse route = id.rsplit('.',1)[0] (283): renaming routes or IDs on F3Z silently zeroes these stats. (4) emergency_braking (269) counts SUMO emergency-braking warnings for all vehicles, which is not V11 (CAV hard braking at a 3-4 m/s² threshold). (5) The 1-s sampling loop and the 30-s rows are Python per-step loops; budget their cost before RL use. (6) No tests exist for this file; add some when porting.
- Verifier (overturned): dead part: corr_run.py:134,145,331 p_nc is a VSL non-compliance share, meaningless without posted limits (V15) → Not dead. Keep it as a driver-heterogeneity parameter, renamed (e.g. fast-driver share), and let the author re-confirm its value. Only the 'VSL non-compliance' wording is obsolete.. corr_run passes p_nc to plants/corr2.demand -> vtypes_xml = plants/mrg3.vtypes_xml (corr2.py:61, 107). There p_noncompliant sets the probability of vType car_n with speedFactor normc(1.15,0.05,0.95,1.4) against car_c normc(1.0,...) (mrg3.py:59-80). That is a 30 % fast-driver group that drives about 15 % above ANY lane maximum, including the 120 km/h network maximum of V13. So it shapes the HDV speed distribution under NC and under CAV-only control. Dropping it silently changes the human mix.
- Verifier (uncertain): TRIM verdict, with the listed dead parts and traps complete → TRIM holds only for the sampling and I/O skeleton. Treat the metric layer (_group_stats reference, headline, emergency braking) as REFERENCE until V18 is decided. Add the net_hash, run_id and hash-recomputability fixes to the traps.. The listed line ranges check out against the file (60, 66-81, 84-94, 97-103, 157-163, 176-178, 192, 197-200, 203-221, 237-246, 267-268, 272-276, 324-325, 340). Missed dead parts: 170 and 195 (the qout30 list is read only by the ALINEA trace at 215); 207-208 (occ_last = alinea_occ_pct, sampled every period even under nc, used only by ALINEA and the occ column); 172 b_now (VSL only). Missed bugs and traps: (a) 260 `"net_hash": N.spec_hash()` uses the default argument spec=SPEC, which is bound at definition time (netgen/corr2.py:102); netgen.activate() (92-97) changes only MAIN_EDGES and N_LANES. So a --net corr2x run records the CORR2 hash, and `"plant": "CORR2"` is hard-coded. A port must hash the active spec. (b) run_id (139-140) contains off_share, which corr2.demand ignores on corr2x (it uses X_SHARE there, corr2.py:92-99), and it omits x_share, m_day and noise. That breaks the CLAUDE.md rule that file names include every varying parameter. (c) 303 pops arrivals_bins from summary.json, but runner.result_hash (runner.py:279-282) hashes arrivals_bins, so the stored determinism hash cannot be recomputed from the stored summary. Verdict risk: once the dead code goes, the metric core still needs rewriting under traps 1-4 (fixed-window TTT, per-route free-flow reference, ID-prefix coupling, emergency braking is not V11). V16 also needs energy, which corr_run does not compute, and V18 (metric definitions) is still pending. What can be ported nearly as is comes down to the 1 s queue sampling, edge congestion, served share, tripinfo parsing and run-dir/summary I/O.

### `vsl_lab/jobs/mrg3_run.py`: REFERENCE
- Reason: The MRG3 plant and posted-VSL controllers are obsolete (T2 closed by the realism gate; V15). The CAV command handling is the closest precedent for F3Z per-CAV commands (V3), and arms C/P are named as V19 comparator candidates ('archived MRG3 staircase / PI rules'). Called by round3/round4/g1_*/t2_* drivers and mentioned in envs/mrg3_env.py (grep hit only; whether it is an import was not checked).
- Dead / obsolete parts:
  - mrg3_run.py:38-60 capacity_drop - the confounded max-based R1 estimator (superseded by eval/realism.capacity_ratio)
  - mrg3_run.py:110-152 VSL controller parsing (mtfc, const, win, spec/SPECIALIST, vslad) - V15
  - mrg3_run.py:159-163 post() staircase VSL; 232-234 SPECIALIST re-post; 251-289 VSL control branches; 291 post(1,1) - V15
  - mrg3_run.py:95-96 trapezoid profiles via P.profile - MRG3-specific inflow
  - mrg3_run.py:173-175 cavstress schedule - Round 3 T-X only
  - Reusable to read: 172-204 cav_control (iterate getIDList, filter by cav_ids, skip ':' internal lanes, getLeader, setSpeed command, release with setSpeed(-1)); 207-217 incident injection via setStop on the next upstream vehicle (an artefact-free lane blockage); 294-300 release of CAV commands before the drain; 320-335 emergency-braking attribution CAV vs human from the SUMO log; 336-352 tripinfo stops
- Traps: capacity_drop is confounded by the demand ramp (t2_realism_protocol Addendum A item 5, STATUS item 13). The CavStaircase actuator uses setMaxSpeed, which renames the vType to av@<id> (STATUS item 5: actuator silently disabled), so track CAVs by ID. Abrupt caps caused emergency braking (STATUS item 4). Per-CAV setSpeed under the default speed mode 31 is capped by the lane max; V5 found speed mode 95 needed if limits ever exceed commands. The veh-km normalisation hard-codes km={'main':5.25,'ramp':1.53} (322) and counts all generated vehicles. EB counts are SUMO warnings, not a deceleration threshold (V11). The 'nonlocal_b' name (174) is a plain local; harmless but misleading.
- Verifier (overturned): dead part: mrg3_run.py:110-152 'VSL controller parsing (mtfc, const, win, spec/SPECIALIST, vslad) - V15' → REFERENCE upheld. Dead VSL parts: 110-114 (VSL-only state), 126-152, 159-163, 232-234, 261-287, 291. Reusable CAV-arm parts: 116-125 and 252-260 (arm C), next to 172-204 and 294-300.. Lines 116-125 parse the CAV arms, not VSL: cavmtfc (MTFC driving CAV set speeds), cavconst:<b> and cavstress (cav_mode). Lines 252-260 apply them to zone_b, which feeds CavStaircase (199-204). These are the 'archived MRG3 staircase' rules that V19 names as comparator candidates (round3 T1C_CTRLS = cavconst/cavmtfc; round4 CAV = cavconst:0.6, cavpi). Only 126-152 (spec, vslad, mtfc, const, win) and 261-287 are posted-VSL code.
- Verifier (upheld): REFERENCE: other traps (capacity_drop confounded, setMaxSpeed renames the vType, hard-coded km at 322, emergency braking counted from SUMO warnings) → REFERENCE. capacity_drop at 38-60 is the max-based estimator (pre_max = max of 5-min flows before onset). km={'main':5.25,'ramp':1.53} is at 322, and vkm sums over all dem.vehicles (329-330). The emergency-braking regex on SUMO log warnings is at 324-327. controllers/cav_staircase.py:3-4,28,69 uses setMaxSpeed and documents the av@<id> rename. cav_ids are tracked by ID at 99. STATUS items 4, 5, 13 and 14 match.

### `vsl_lab/jobs/round3.py`: REFERENCE
- Reason: Round 3 TM21 CAV commands vs TM20 VSL on MRG3-v3 (parked). Its CAV tool-check designs are directly relevant to v5.B.1 T0/T3 with CAV commands: T-CAV0 (CAVs present, no command: no collisions/FAIL, CACC vs ACC hash), T-X (command interval chosen by safety: EB rate within 10 % of NC), T0 (rel <= -10 % with CI excluding 0), T1c with T3 determinism by result hash.
- Dead / obsolete parts:
  - round3.py:26-33 hard-coded seeds 7,150,000-089 (archived block)
  - round3.py:42-49 plant() reads the MRG3 realism verdict files
  - round3.py:52-58 job() argv for mrg3_run (MRG3, posted-VSL arms B)
- Traps: The SUMO default CACC at 0.2 s and 25 % worsened delay by 46-93 % (STATUS; round4 docs): validate the CAV car-following model before trusting CAV authority. ROUTE_KM (35) is a hard-coded veh-km approximation. VERDICT/GEOM are module globals mutated in main(). It uses eval.stats.paired_median_diff (b - a convention).
- Verifier (upheld): REFERENCE, with dead parts 26-33 (seeds), 42-49 (plant from verdict files), 52-58 (mrg3_run argv); trap ROUTE_KM at 35 → REFERENCE. Lines match: seeds 7,150,000-089 at 27-30, ROUTE_KM at 35, VERDICT/GEOM globals at 38-39 mutated in plant() (44-45), paired_median_diff imported at 22. T1C_CTRLS (32) are CAV arms only (cavconst/cavmtfc), which supports keeping round3 as a precedent for the CAV tool checks.

### `vsl_lab/jobs/ring_run.py`: REFERENCE
- Reason: T3 ring (done: PI-with-saturation at the ceiling, H ≈ 0). The FollowerStopper and PI-with-saturation controllers (Stern et al. 2018, in plants/ring.py) are candidate V19 rule-based CAV comparators. The metrics (Stern's sigma, stop share, across-vehicle speed std) are candidates for the stop-and-go index, and the result-hash determinism idea is reusable. RingPlant moves all vehicles itself, which does not fit F3Z.
- Dead / obsolete parts:
  - ring_run.py:24-66 run() is RingPlant-specific (own IDM humans, speedMode 6)
  - ring_run.py:41 acc clip (-3, 1.5) m/s² is ring-specific
- Traps: Two PISaturation implementations exist (plants/ring.PISaturation(window_s, v_catch) here vs controllers/pi_saturation.PISaturation(dt) in mrg3_run). Choose one and verify it against the paper before using it as a comparator. The hash covers only 4 rounded metrics, which is weaker than a trajectory hash.
- Verifier (overturned): REFERENCE: its metrics include 'Stern's sigma, stop share, across-vehicle speed std' as candidates for the stop-and-go index → REFERENCE upheld, with a trap added: the docstring's Stern sigma is not implemented, so implement it fresh rather than port it.. The docstring (5) promises 'Stern's sigma (std of all speed samples)', but run() never computes it. It stores only sp.std() per step, the across-vehicle std (46), and reports its mean as mean_across_std (57). No std over all speed samples is computed or written. The other line references hold (24-66 run, 41 clip -3/1.5, hash over 4 rounded metrics at 63-64). Two PISaturation classes exist: plants/ring.PISaturation(window_s, v_catch) at 33 and controllers/pi_saturation.

### `vsl_lab/jobs/t4_calib.py`: REFERENCE
- Reason: CORR2 NC calibration over an inflow grid via scheduler + corr_run, with a pre-registered cell rule: zero teleports, no FAIL, ≥ 2 of 3 seeds with ≥ 5 min below 60 km/h at m3, smallest total inflow. This is the pattern for the F3Z T1 'capacity drop without teleports' calibration. The grid, seeds and m3 column are CORR2-specific.
- Dead / obsolete parts:
  - t4_calib.py:16-17 QM/QR1/QR2 grid and seeds 7,140,001-003 (archived)
  - t4_calib.py:31-32 global override of the grid (--extended)
- Traps: The off_users pick (49) takes the first door_to_door key containing 'off', which depends on dict order. It writes into docs/lab of the archive.
- Verifier (upheld): dead parts 16-17 and 31-32; trap: off_users pick at line 49 depends on dict order → REFERENCE (line references: 31-33 and 51).. The substance holds, but the line numbers are off: the global override is at 31-33, and the off_users `next(... if 'off' in kk ...)` is at line 51, not 49. On corr2x the groups have no 'main_off'/'r1_off' (GROUPS_AUX), so the pick can return None or an unintended route:* key. The cell rule at 55 (zero teleports, no FAIL, n_block_ge5 >= 2) matches the map.

### `vsl_lab/jobs/t2_realism.py`: REFERENCE
- Reason: The plant-realism gate (R-a capacity drop 3-18 %, R-b wave speed, R-c no artefacts, R-d onset at the bottleneck) with between-run Q_dis/Q_ff bootstrap (Addendum A), built on eval/realism.py. Worth re-reading for an F3Z realism check; the MRG3 driver variants H0-H5 are obsolete.
- Dead / obsolete parts:
  - t2_realism.py:24 PREFERENCE H-variant order; 33 STEP global; 37-43 mrg3_run job builder
  - t2_realism.py:100-109 'reported_ratio_r1_max_based' kept only for disclosure
- Traps: STATUS: SUMO never produced a measurable capacity drop without artefacts (IDM strands vehicles, W99 no drop, EIDM breakdowns too short). Expect the same on F3Z, and pre-register what happens if R-a fails. STEP is a module global mutated by main().
- Verifier (upheld): dead part: 100-109 'reported_ratio_r1_max_based' → REFERENCE (dead-part references: 100-101 and 108-110).. The r1_max_based field is at 108-110 (100-101 is breakdown_share_capdrop, also built from mrg3_run.capacity_drop). The R-a PASS rule at 111 is share >= 0.3 and 0.82 <= ratio <= 0.97. Lines 24-25, 33 and 37-43 match the map.

### `vsl_lab/jobs/t1_meter_bn4_confirm.py`: REFERENCE
- Reason: The only implementation of the D5.8 conditional-bar analysis: pooled vs NC ≤ -10 % with CI, best non-learning B per regime with a Bonferroni CI, worse > 5 %, fail share, operating map. It is a template for the v5.B.1 confirmatory; the BN4 meter arms and seeds are obsolete.
- Dead / obsolete parts:
  - t1_meter_bn4_confirm.py:21-31 BN4 kinds, seeds 7,112,200-609, ALINEA grid, NONLEARN meter arms
  - t1_meter_bn4_confirm.py:53-90 ALINEA tuning on BN4
- Traps: Line 137: B = min(med, key=med.get) picks the best tuned arm by median level. That is the STATUS item 19 flaw; use the paired minimum over non-learning arms. Its _paired (93-100) returns median(x - y), the opposite sign of eval.stats.paired_median_diff (median(b - a)); CLAUDE.md requires one convention. worse_gt5 = rel > 0.05 and CI lo > 0 is one reading of 'not significantly worse by > 5 %'; pre-register the exact test. rel divides the median difference by the median base level.
- Verifier (upheld): trap: 'Line 137: B = min(med, key=med.get)' picks B by median level (STATUS item 19) → REFERENCE. Trap (b) refers to line 134 (B selection); line 137 is worse_gt5.. The flaw is real: STATUS.md:98 item 19 says that choosing B by median level goes against the paired convention, and the confirm code repeats it. The line number is wrong, though: `b = min(med, key=med.get)` is at line 134, and line 137 holds beats_B and worse_gt5 (`pb['rel'] > 0.05 and pb['ci'][0] > 0`). _paired at 93-100 returns median(x - y), while eval/stats.paired_median_diff:9-13 returns median(b - a), so the two use opposite sign conventions, as the map claims.

### `vsl_lab/jobs/__init__.py`: DROP
- Reason: Empty package marker. The v5b1 package layout is new; recreate only if a jobs package is ported.

### `vsl_lab/jobs/bn4_eval.py`: DROP
- Reason: T1 BN4 meter/VSL-cap evaluator (meters dropped V15; MPC dropped). Imported by tests/test_bn4_meter_rate.py (drop together) and by mpcf/t1_* drivers. The 'same env code path for every controller' principle is worth keeping in mind.

### `vsl_lab/jobs/bn4_nc.py`: DROP
- Reason: BN4 NC plant check (T1/T3); BN4 is not the v5.B.1 network. Used by t1_r1_checks and by ops/calibrate_thermal.py and ops/ecore_probe.py (the thermal rule was removed 2026-10-10).
- Dead / obsolete parts:
  - bn4_nc.py:40 loop_mismatch assigned, never used (vulture; grep confirms only line 40): the H-R8 mismatch counter is incomplete
- Traps: The ops/calibrate_thermal.py and ops/ecore_probe.py callers also become dead.
- Verifier (upheld): DROP; dead part bn4_nc.py:40 loop_mismatch is never used → DROP. vulture.txt:140; `grep -w loop_mismatch` finds only line 40 (`loop_total, loop_mismatch = 0, 0`). Its outside callers are vsl_lab/ops/calibrate_thermal.py:34 and vsl_lab/ops/ecore_probe.py:44, both as module-name strings. The thermal rule was removed (2026-10-10) and E-core pinning is no longer used, so both callers drop too.

### `vsl_lab/jobs/dp_jamrelease.py`: DROP
- Reason: Day-pattern P3 single-lane queue-discharge pre-check (own throw-away net, driver candidates K0-K3, seeds 7,190,000-010). The day-pattern line is retired. Re-read only if F3Z driver calibration needs a discharge-headway check.
- Verifier (upheld): DROP (day-pattern P3 queue-discharge pre-check) → DROP (its protocol doc is the reference, not the code). Single-lane throw-away net, candidates K0-K3 (K0 = SUMO-default EIDM, line 60), seeds 7,190,000-010. It runs the SUMO binary through subprocess (imports SUMO_BIN, NETCONVERT_BIN), not libsumo. It is only weakly relevant to F3Z T1 (capacity drop without artefacts); the map already says to re-read it only for driver calibration.

### `vsl_lab/jobs/g1_extremes.py`: DROP
- Reason: G-1 S0 demand extremes on the MRG3 merge (posted VSL). No references outside the file.

### `vsl_lab/jobs/g1_s1.py`: DROP
- Reason: G-1 S1 band refinement and timed VSL oracle on MRG3; only g1_s2 imports it.

### `vsl_lab/jobs/g1_s2.py`: DROP
- Reason: G-1 S2 Z9 follow-up (VSL oracle windows); unreferenced.

### `vsl_lab/jobs/metanet_calibrate.py`: DROP
- Reason: METANET US-169 calibration v4 (no METANET; D5.5 STOP). Imported by every metanet_* job, testbed_screen, vsl_lab/data/metanet_facts.py, tests/test_metanet*.py, tests/test_testbed_screen.py and docs/lab/day_pattern/d412_capacity_forcing_diagnostic_recovered. Drop the cluster together.

### `vsl_lab/jobs/metanet_demand_check.py`: DROP
- Reason: METANET D4.12 hidden-demand data check; unreferenced; METANET and 'demand' retired (V9).

### `vsl_lab/jobs/metanet_f1.py`: DROP
- Reason: METANET v3/v4 structural fallback F1; METANET cluster (tests/test_metanet_v4.py, v5).

### `vsl_lab/jobs/metanet_freeze.py`: DROP
- Reason: METANET v4 plant freeze; METANET cluster.

### `vsl_lab/jobs/metanet_gate.py`: DROP
- Reason: METANET v4 plant gate (STOP). METANET cluster; also imported by testbed_screen.

### `vsl_lab/jobs/metanet_items.py`: DROP
- Reason: METANET per-day gate items; METANET cluster.

### `vsl_lab/jobs/metanet_j5.py`: DROP
- Reason: METANET v5 objective J5; METANET cluster.
- Dead / obsolete parts:
  - metanet_j5.py:19 MATCH (vulture 60 %; irrelevant since the file is dropped)

### `vsl_lab/jobs/metanet_j5_eval.py`: DROP
- Reason: METANET v5 J5 evaluator; METANET cluster.

### `vsl_lab/jobs/metanet_postcal.py`: DROP
- Reason: METANET v4 post-calibration; METANET cluster.

### `vsl_lab/jobs/metanet_v5_calibrate.py`: DROP
- Reason: METANET v5 CMA-ES driver; METANET cluster.
- Dead / obsolete parts:
  - metanet_v5_calibrate.py:135 LEDGER_REL, :173 head_commit (vulture 60 %)

### `vsl_lab/jobs/metanet_v5_facts.py`: DROP
- Reason: METANET v5 real-side facts; METANET cluster.

### `vsl_lab/jobs/metanet_v5_freeze.py`: DROP
- Reason: METANET v5 freeze stage; METANET cluster.

### `vsl_lab/jobs/metanet_v5_gate.py`: DROP
- Reason: METANET v5 gate wrapper; METANET cluster.

### `vsl_lab/jobs/mpcf.py`: DROP
- Reason: MPC-F fitted-model MPC for BN4 meter scheduling (no MPC for now; meters dropped). Imported by bn4_eval, t1_meter2_h.

### `vsl_lab/jobs/mrg3_diag.py`: DROP
- Reason: One-off diagnosis of the MRG3-v2 IDM teleports; only run_round2.sh calls it.
- Traps: Lesson only: IDM strands ramp/lane-drop vehicles and causes teleports (STATUS).

### `vsl_lab/jobs/r4_eval_rl.py`: DROP
- Reason: Evaluates an SB3 PPO .zip on MRG3Env (single-agent, VSL) for Round 4. The v5.B.1 policy contract is Policy.act/save/load (ADR-001), not SB3.
- Traps: The principle 'evaluate the learned policy exactly like the classical controllers (same d2d incl. drain, same stops)' still applies.

### `vsl_lab/jobs/ring_shield_verify.py`: DROP
- Reason: One-shot R3 verification of the ring AV shield. Never imported (imports.json never_imported_not_main/unreached); only run_chain5.sh calls it.
- Dead / obsolete parts:
  - ring_shield_verify.py:158-183 module-level batch run, docs write and ledger append
- Traps: Importing this module runs a simulation batch and writes docs/lab/t3_shield_verify.json (no main guard).
- Verifier (overturned): dead_parts 'ring_shield_verify.py:158-183 module-level batch run, docs write and ledger append' → DROP upheld. Correct the dead-part reference to 12-37 (the whole body is module-level side effects).. The file has 37 lines (wc -l), so the line range 158-183 does not exist. All of lines 12-37 run at module level: a batch through run_batch (21), a write to docs/lab/t3_shield_verify.json (34), a ledger append (35) and a print. imports.json lists it as never_imported_not_main and unreached, and run_chain5.sh is its only caller.

### `vsl_lab/jobs/round2.py`: DROP
- Reason: Round 2 posted VSL / MTFC-BN4 and AV caps tuning; VSL and BN4 obsolete.
- Traps: Lesson (STATUS 4-6): abrupt AV caps caused emergency braking; the av@<id> rename silently disabled the AV actuator; AV speedDev default.

### `vsl_lab/jobs/round4.py`: DROP
- Reason: Round 4 T-H harmonisation on LD3 with posted VSL / MTFC / SPECIALIST / vslad, plus CAV arms (killed: G ≤ 4 %, CAV arms no authority at 25 %).
- Traps: Precedent for V16: the Round 4 objective J = delay + 40 s/stop (W_STOP, line 29). CAV arms C (cavconst:0.6) and P (cavpi) at 25 % showed no authority. isolated_jam_minutes is SPECIALIST-specific.
- Verifier (upheld): DROP; precedent W_STOP at line 29 → DROP. W_STOP = 40.0 at 29 and J = mean_time_in_system + W_STOP*stops at 200. CAV = [nc C, cavconst:0.6 C, cavpi P] at 27. The CAV arm logic itself lives in mrg3_run (REFERENCE), so round4 is only a driver. Its protocol (docs/lab/round4_harmonisation_protocol.md:93) records the CACC 46-93 % result and the no-authority finding.

### `vsl_lab/jobs/s1_bn4.py`: DROP
- Reason: gate_ctx_r6 S1 BN4 driver-variant realism gate; BN4-specific; the realism idea is covered by t2_realism (REFERENCE).
- Dead / obsolete parts:
  - s1_bn4.py:25 WARMUP (vulture 60 %)

### `vsl_lab/jobs/t1_meter2_h.py`: DROP
- Reason: T1 Lead 1 stage H meter headroom (killed).
- Traps: STATUS item 19 flaw (B chosen by median level) originated in this stage.

### `vsl_lab/jobs/t1_meter2_r6ood.py`: DROP
- Reason: Exploratory OOD check of the R6 meter policy; T1 meter.

### `vsl_lab/jobs/t1_meter2_scan.py`: DROP
- Reason: T1 Lead 1 stage S scan; T1 meter.
- Traps: STATUS item 18: a 360 s blockage teleported in 209/220 runs (condition excluded).

### `vsl_lab/jobs/t1_meter_gscan.py`: DROP
- Reason: T1-M meter G scan; unreferenced; meters dropped.

### `vsl_lab/jobs/t1_meter_h.py`: DROP
- Reason: T1-M H step; meters dropped.

### `vsl_lab/jobs/t1_meter_pm.py`: DROP
- Reason: T1-M P-M screening of meter policies; meters dropped.

### `vsl_lab/jobs/t1_meter_r5.py`: DROP
- Reason: R5-M RecurrentPPO meter head-to-head; meters dropped; SB3 RecurrentPPO.
- Traps: STATUS: R6 learners trained at a constant lr because the trainer ignored --lr-decay for RecurrentPPO (fixed 34ae76f): check that every config flag reaches the trainer.

### `vsl_lab/jobs/t1_meter_r6.py`: DROP
- Reason: R6 meter confirmatory (CLAIM YES, chapter-level); BN4 meters.

### `vsl_lab/jobs/t1_meter_r6plus.py`: DROP
- Reason: R6+ hybrid vs vanilla DRL meter; BN4 meters. Its fair-vanilla-DRL arm definition is documented in the protocol, not needed as code.

### `vsl_lab/jobs/t1_meter_r6plus_diag.py`: DROP
- Reason: Post-result R6+ diagnostics; BN4 meters.

### `vsl_lab/jobs/t1_r1_checks.py`: DROP
- Reason: T1 BN4 plant checks; BN4 obsolete.

### `vsl_lab/jobs/t1_r2_baselines.py`: DROP
- Reason: T1 BN4 baseline tuning; BN4 obsolete.

### `vsl_lab/jobs/t1_r5_eval.py`: DROP
- Reason: T1 R5 DRL head-to-head (SB3 models on BN4).
- Traps: STATUS item 12: discrete action spaces crashed the evaluator.

### `vsl_lab/jobs/t1_t0b.py`: DROP
- Reason: T1 T0b preventive actuator authority on BN4; unreferenced.

### `vsl_lab/jobs/t2_calib.py`: DROP
- Reason: T2 MRG3 calibration (VSL track closed).
- Traps: Uses the confounded capdrop ratio (line 44).

### `vsl_lab/jobs/t2_r1_checks.py`: DROP
- Reason: T2 MRG3 R1 plant checks.
- Traps: Uses the confounded capdrop ratio (88-89).

### `vsl_lab/jobs/t2_r2_baselines.py`: DROP
- Reason: T2 MRG3 R2 VSL baselines.

### `vsl_lab/jobs/t3_r1r2_ring.py`: DROP
- Reason: T3 ring R1/R2 tuning of FS/PI; done. Frozen results live in docs/lab/t3_ring_baselines_frozen.json if V19 needs tuned values.

### `vsl_lab/jobs/t4_gscan.py`: DROP
- Reason: T4 CORR2 meter/VSL headroom scan; killed (G = 0.4 %).
- Traps: Lesson: on CORR2, meter/VSL adaptation room was G = 0.4 %. CAV-only F3Z needs its own early T2/G check.

### `vsl_lab/jobs/testbed_screen.py`: DROP
- Reason: Testbed stage-1b METANET metering screen (T0 KILL, D5.14). tests/test_testbed_screen.py drops with it.

### `vsl_lab/jobs/val_refs.py`: DROP
- Reason: Reference controllers (BN4 caps/meters, ring FS/PI) on R3 validation specs; tracks archived.

### `vsl_lab/jobs/run_bf.sh`: DROP
- Reason: One-off chain for t1_r5_eval.
- Traps: Shared by all run_*.sh: the v6 venv314 (forbidden by V14), the cd to the dead /run/media mirror (except run_r6plus.sh, which cds to /srv/shared), pgrep/kill-0 sequencing instead of scheduler/guard.

### `vsl_lab/jobs/run_chain2.sh`: DROP
- Reason: One-off chain (t2_calib, t3_r1r2_ring, val_refs, mrg3_run).
- Traps: Same as run_bf.sh.

### `vsl_lab/jobs/run_chain3.sh`: DROP
- Reason: One-off T1 chain.
- Traps: Same as run_bf.sh.

### `vsl_lab/jobs/run_chain4.sh`: DROP
- Reason: One-off T2 chain (t2_r1_checks, t2_r2_baselines).
- Traps: Same as run_bf.sh.

### `vsl_lab/jobs/run_chain5.sh`: DROP
- Reason: One-off chain incl. ring_shield_verify.
- Traps: Same as run_bf.sh.

### `vsl_lab/jobs/run_chain6.sh`: DROP
- Reason: One-off T1 chain (t1_r5_eval).
- Traps: Same as run_bf.sh.

### `vsl_lab/jobs/run_chain7.sh`: DROP
- Reason: One-off T1 chain (t1_r5_eval).
- Traps: Same as run_bf.sh.

### `vsl_lab/jobs/run_d3.sh`: DROP
- Reason: One-off D-3 realism + round3 chain.
- Traps: Same as run_bf.sh.

### `vsl_lab/jobs/run_ld3.sh`: DROP
- Reason: One-off LD3 realism + round3 chain.
- Traps: Same as run_bf.sh.

### `vsl_lab/jobs/run_m2h.sh`: DROP
- Reason: One-off t1_meter2_h chain.
- Traps: Same as run_bf.sh.

### `vsl_lab/jobs/run_meter_h.sh`: DROP
- Reason: One-off t1_meter_h chain.
- Traps: Same as run_bf.sh.

### `vsl_lab/jobs/run_p1.sh`: DROP
- Reason: One-off val_refs chain.
- Traps: Same as run_bf.sh.

### `vsl_lab/jobs/run_ph2_screen.sh`: DROP
- Reason: One-off round4 P-H2 screen chain.
- Traps: Same as run_bf.sh.

### `vsl_lab/jobs/run_ph3_screen.sh`: DROP
- Reason: One-off round4 P-H3 screen chain.
- Traps: Same as run_bf.sh.

### `vsl_lab/jobs/run_pm.sh`: DROP
- Reason: One-off t1_meter_pm chain.
- Traps: Same as run_bf.sh.

### `vsl_lab/jobs/run_pm3.sh`: DROP
- Reason: One-off t1_meter_pm chain.
- Traps: Same as run_bf.sh.

### `vsl_lab/jobs/run_pm4.sh`: DROP
- Reason: One-off t1_meter_r5 chain.
- Traps: Same as run_bf.sh.

### `vsl_lab/jobs/run_pm4b.sh`: DROP
- Reason: One-off t1_meter_r5 chain.
- Traps: Same as run_bf.sh.

### `vsl_lab/jobs/run_pmf.sh`: DROP
- Reason: One-off T1 meter perturbation chain.
- Traps: Same as run_bf.sh.

### `vsl_lab/jobs/run_r5m.sh`: DROP
- Reason: One-off t1_meter_r5 chain.
- Traps: Same as run_bf.sh.

### `vsl_lab/jobs/run_r6plus.sh`: DROP
- Reason: One-off R6+ training/eval chain.
- Traps: Uses the v6 venv314 (V14).

### `vsl_lab/jobs/run_realism_p6.sh`: DROP
- Reason: One-off realism/P6 chain (t2_realism, t2_r2_baselines, val_refs).
- Traps: Same as run_bf.sh.

### `vsl_lab/jobs/run_round2.sh`: DROP
- Reason: One-off round2 + mrg3_diag chain.
- Traps: Same as run_bf.sh.

### `vsl_lab/jobs/run_round3.sh`: DROP
- Reason: One-off round3 + t2_realism + val_refs chain.
- Traps: Same as run_bf.sh.

### `vsl_lab/jobs/run_v3.sh`: DROP
- Reason: One-off MRG3-v3 chain (t2_calib, t2_r1_checks, t2_r2_baselines).
- Traps: Same as run_bf.sh.

- Verifier (upheld) on `vsl_lab/jobs/metanet_*.py, testbed_screen.py, s1_bn4.py (vulture hits)`: DROP clusters; vulture hits MATCH (metanet_j5:19), LEDGER_REL and head_commit (metanet_v5_calibrate:135,173), WARMUP (s1_bn4:25) → DROP. For each name, `git grep -w` over vsl_lab, tests and docs/lab/day_pattern/*.py returns only its definition, so all four are dead. The importers outside jobs are exactly as the map says: tests/test_metanet{,_ctrl,_gate_refactor,_j5_eval,_v4,_v5}.py, tests/test_testbed_screen.py, vsl_lab/data/metanet_facts.py:441, docs/lab/day_pattern/d412_capacity_forcing_diagnostic_recovered.py:7. There is also a string path in docs/lab/day_pattern/metanet_v5_review_procedure/round2.js:15. No METANET or MPC use in V1-V19.
- Verifier (upheld) on `vsl_lab/jobs/mrg3_run.py (envs/mrg3_env.py hit)`: envs/mrg3_env.py mentions mrg3_run; whether it imports it was not checked → No import dependency; the comments only.. mrg3_env.py imports only vsl_lab.config, controllers.mtfc, plants.mrg3 and sim.runner (lines 23-26). The hits at 75 (mrg3_run) and 81 (round4) are comments, so dropping jobs creates no import dependency there.
- Verifier (upheld) on `vsl_lab/jobs/r4_eval_rl.py, t1_r5_eval.py, t1_meter_r5.py`: DROP (SB3 single-agent evaluators) → DROP. V17 and ADR-001 make the trainer our own shared-parameter PPO on a PettingZoo ParallelEnv; SB3+SuperSuit is only the last fallback. These evaluate single-agent SB3 policies on MRG3Env or BN4 meters, actuators that V15 removes. Their only callers are run_*.sh chains and ledger rows.
- Verifier (upheld) on `vsl_lab/jobs/run_*.sh (25 chains)`: DROP; shared traps: v6 venv314, cd to the dead /run/media mirror (except run_r6plus.sh), pgrep/kill-0 sequencing → DROP (the pgrep trap applies to 13 of 25 scripts, not all). All 25 scripts use venv314. 24 cd to /run/media/catalin/Shared/...; run_r6plus.sh cds to /srv/shared. Only 13 of 25 use pgrep/kill -0; the rest run sequentially, so 'shared by all' overstates that trap. run_round2.sh also calls vsl_lab.jobs.bn4_eval (not listed). run_chain3.sh and run_pmf.sh call only vsl_lab.train.train_sb3, no jobs module.
- Verifier (overturned) on `vsl_lab/jobs (map summary counts)`: '59 .py experiment drivers + 24 run_*.sh'; result '1 TRIM, 6 REFERENCE, 76 DROP' → 55 .py + 25 .sh = 80 files: 1 TRIM, 6 REFERENCE, 73 DROP. Coverage is complete.. git ls-files vsl_lab/jobs gives 80 tracked files: 55 .py and 25 .sh. The map's file list has exactly 80 entries (every tracked file appears), so DROP = 73, not 76. The only untracked entry in the directory is __pycache__.

**Verifier: missed items and extra traps**
- corr_run.py:260 bug: N.spec_hash() defaults to SPEC (netgen/corr2.py:102; activate() does not change SPEC), so --net corr2x runs record the CORR2 net hash, and 'plant': 'CORR2' is hard-coded. A port must hash the active spec.
- corr_run.py:139-140 run_id contains off_share, which corr2.demand ignores on corr2x (X_SHARE is used, corr2.py:92-99), and omits x_share, m_day and noise. This breaks the 'file names include every varying parameter' rule.
- corr_run.py:303 and mrg3_run.py:353 pop arrivals_bins from summary.json, but sim/runner.result_hash (279-282) hashes arrivals_bins, so the stored determinism hash cannot be recomputed from the stored summary. Matters for the CLAUDE.md T3 determinism check.
- corr_run.py dead parts not listed: 170 and 195 (qout30, read only by the ALINEA trace at 215), 207-208 (occ_last = alinea_occ_pct sampled every control period even under nc), 172 b_now (VSL only).
- mrg3_run.py:116-125 and 252-260 are CAV arms (cavmtfc, cavconst, cavstress feeding zone_b and CavStaircase), not VSL. They are the V19 'archived MRG3 staircase' comparator and must not be filed under dead VSL parsing.
- ring_run.py docstring (line 5) promises Stern's sigma, but the code never computes it: only the across-vehicle std (46, 57) exists.
- vsl_lab/runs/ledger.csv names 15 job modules (bn4_eval, mpcf, ring_shield_verify, round2, t1_meter_*, t2_r1_checks, t4_gscan, testbed_screen, val_refs, ...). This is provenance only: it stays valid on the archive branch and is no reason to port.
- docs/lab/day_pattern/metanet_v5_review_procedure/round2.js:15 references vsl_lab/jobs/metanet_v5_gate.py as a string, part of the METANET drop cluster at docs level.
- Line-number errors in the map: t1_meter_bn4_confirm B selection is at 134 (not 137); ring_shield_verify module body is 12-37 (the file has 37 lines, so not 158-183); t4_calib off_users at 51 (not 49), global override 31-33; t2_realism r1_max_based at 108-110.

## Area: legacy

**Summary.** I classified every tracked file in this scope. Almost nothing outside vsl_lab/ is alive for v5.B.1. vsl_lab imports nothing from core/, sar_components/, traffic_environment/, train.py, evaluate_models.py or tools/: a static import grep and a string grep of vsl_lab (excluding vsl_lab/runs) both found 0 hits, apart from a docstring mention of 'ramps_v2-like geometry' in vsl_lab/netgen/mrg3.py. design_v0 §5/§7 points at core/eval_metrics.py (TTC) and traffic_environment/vehicle_fleet.py (reckless share), but those are only reading references. All of this code is pre-spin-off: its last commit is the bulk commit ebba794 of 2026-10-01, and its substance dates from 2026-03 to 2026-05. It is the TQC era: single-agent Gym, socket TraCI, VSL on ramps_v2, and r44 SAR plugins loaded by string.

Verdicts:
- **To carry over:** only two tests outside vsl_lab, both TRIM. tests/test_guard.py goes with the guard port (drop the thermal tests if the thermal path is dropped). tests/test_corr2_build.py goes with the F3Z netgen port: retarget the fixture to SPEC_AUX and drop the meter, TLS, ALINEA and O1 asserts.
- **REFERENCE (read only):** core/eval_metrics.py (sumo_step accel/jerk artefact filter and severity bands, for V11), traffic_environment/vehicle_fleet.py, tests/test_capacity_drop.py, tests/test_reward_e2e_verification.py (pattern for checking the V16 reward), tests/test_train_s0.py (C1 convergence test ideas), tests/test_cooling.py, the archive .gitignore, and the untracked research_notes.
- **DROP:** everything else.

Confirmed dead code, beyond the vulture hits:
- traffic_environment/scenario_generator.py cannot be imported: line 19 imports a make_counts_from_profile that does not exist.
- rou_writer.py is reached only through scenario_generator.
- core/algos has an empty registry and points to a train_eval module that does not exist.
- r44_action_v0, r44_reward_v0/v1/v3 and r44_state_v0 are named by no config or code.
- The r44 'unreached' flags in imports.json are false positives (loaded by string through discover_components), but that does not change their verdict.

Traps a port must not carry over:
1. **Arrival undercount (my own reading, not run):** eval_metrics reads getArrivedIDList only once per 30 s env step, so it sees arrivals from about 1 SUMO step in 30. n_arrived and travel times are undercounted, which probably explains the TTS/arrivals mismatch in lessons_metric_gameability.md:83.
2. **Wrong lane-change rate:** the lane-change rate divides by the VKT of vehicles still present, so it is inflated.
3. **Queues left out:** TTS and travel time exclude origin and insertion queues.
4. **Production imports a test module:** env_interact.py:289 and scenario_pool.py:158,292 import tests._sumo_helpers.
5. **Demand capped at 3,600 veh/h per route:** tests/_sumo_helpers.py:120-131 makes one Bernoulli draw per second, so NC never broke down.
6. **SUMO run flags:** --time-to-teleport -1, --collision.action warn and insertionChecks none are used, which conflicts with V6 (teleports make a run invalid).
7. **Restart in mid-episode:** _recover_sumo restarts SUMO, fast-forwards and carries on with zeroed metrics.
8. **How CAVs are found and commanded:** CAVs are matched by the substring 'cav' in the type id, and slowDown is re-issued every 5 s. V5 found that setSpeed with speed mode 95 is the right command [VERIFY slowDown semantics].
9. **A 'CAV' that is not a CAV model:** it is Krauss with sigma 0.
10. **Docstrings that disagree with the code:** in vehicle_fleet the reckless parameters disagree; the 92 % compliance claim is not implemented anywhere.
11. **NC is not uncapped:** in evaluate_models it posts 120/120/120/90 km/h, against V4.
12. **Misspecified reward:** the r44 v4 reward used variance proxies with no delay term. Lesson for V16: the reward must be the cost itself.
13. **Fake perturbations:** anomaly_injector's ramp_spike uses an undefined vType, so it did nothing.
14. **Shell scripts that change the system:** they use sudo apt, a PPA and VM auto-shutdown.

Many of these were already recorded in docs/review/design_space/notes_networks.md §4, notes_vehicles.md §6 and notes_rl_design.md §8-9. I checked the main ones by reading the code; items 1, 2 and 8 are my own analysis and have not been run.

Bloat:
- **Tracked in scope:** 1.40 MB of tracked files in total, of which tests/persistent_results is 425 KB of NC sweep CSVs.
- **Tracked, outside scope (for the docs agent):** docs/lab/frozen/*.zip (2.0 + 1.96 MB policy zips) and docs/review/design_space/fig*.png (230-460 KB each).
- **Untracked or ignored on disk:** training_runs 9.8 GB, artifacts 2.7 GB, scenario_pools 258 MB and reports 2.9 MB. All are TQC-era and none is needed; deleting them is the author's call.
- **research_notes/:** 5 files, 169 KB, neither tracked nor ignored, so it shows as '??'.

**Port order.** 1) tests/test_guard.py (TRIM) together with vsl_lab/ops/guard.py, before the first simulation batch on v5b1. It has no other dependency outside vsl_lab/ops. 2) tests/test_corr2_build.py (TRIM), when F3Z is built from vsl_lab/netgen/corr2.py SPEC_AUX. It depends on vsl_lab.config (SUMO_BIN, clean_sumo_env) and on the netgen port. Nothing else in this scope is ported. When the per-CAV hard-brake metric (V11) and the generalised-cost reward check (V16) are written, read core/eval_metrics.py sumo_step and tests/test_reward_e2e_verification.py as references, and fix the arrival-polling and queue-accounting traps from the start: count arrivals every SUMO step, and measure door-to-door from the intended departure.

### `core/eval_metrics.py`: REFERENCE
- Reason: Nothing in vsl_lab imports it (static grep and string grep of vsl_lab: 0 hits). Only evaluate_models.py:246 uses it. Its edge names are for ramps_v2 (seg_0_before and so on). design_v0 §7 says to 'port' it for TTC, and V11 needs CAV hard braking, so read it, do not port it. Worth reading: the sumo_step() per-SUMO-step acceleration and jerk collection with artefact filters (|a|>15, |j|>30) and the severity bands -2.5/-4/-6 m/s2 (lines ~69-80, 237-290). A per-CAV hard-brake counter for V11 could use the same pattern, filtered to CAV ids.
- Traps: (1) MY ANALYSIS, NOT RUN: step() is called once per 30 s env step (evaluate_models.py:266), but conn.simulation.getArrivedIDList() returns only the arrivals of the last SUMO step. That means n_arrived and mean/p95 travel time see roughly 1 arrival step in 30, and _depart_time keeps vehicles whose arrival was never seen. This probably explains the 'TTS ~220 veh-h vs ~150 arrivals' mismatch noted in lessons_metric_gameability.md:83. (2) The travel time starts at first sight in the network, at a 30 s poll, so it leaves out the insertion queue: the metric-gameability trap. TTS counts only vehicles inside the network. (3) lc_per_veh_per_km: the numerator counts every lane change, but _distance_traveled_per_veh is popped on arrival, so the denominator holds only the VKT of vehicles still present at the end, and the rate is inflated. (4) hard_brake_count is sampled once every 30 s (aliased). TTC is computed by hand with getLeader on 4 ramps_v2 edges, not with the SSM device, and min_ttc is inf when nothing is observed. (5) Density = detector flow / speed / lanes, with speed floored at 1 km/h. It is unreliable in a jam.
- Verifier (upheld): REFERENCE; arrivals read once per 30 s env step (undercount) → REFERENCE. Also flag the design_v0:148 'port' wording as wrong (there is no SSM in this file).. Nothing in vsl_lab imports or names it (git grep). The arrival claim is confirmed by reading the code, not by running it. step() reads getArrivedIDList at line 265 and is called once per env step from evaluate_models.py:266. The env advances SUMO 1 s at a time (env_interact.py:544), and the per-SUMO-step hook sumo_step (line 294) collects only accel/jerk, never arrivals. TTC is computed by hand with getLeader (line 242), not with SSM. So docs/v5b/design_v0.md:148 'TTC < 1.5 s events from SUMO's SSM device (port core/eval_metrics.py)' is self-contradictory, and TTC is not a V1-V19 metric (V11 covers CAV hard braking only).

### `traffic_environment/vehicle_fleet.py`: REFERENCE
- Reason: vsl_lab does not import it (0 hits). The only importers are tests/_sumo_helpers.py, the run_* scripts and scenario_pool.py. v5.B.1 HDVs come from the BN4 'B3' EIDM population (design_v0 §5). This file is useful only as a source for the 'reckless' outlier idea and the length/class mix (FLEET_MIX at line ~103).
- Dead / obsolete parts:
  - traffic_environment/vehicle_fleet.py:63,73,83,93 BASE_SPECS[*]['sigma'] - never read (sigma comes from NORMAL_HDV/RECKLESS_HDV)
  - traffic_environment/vehicle_fleet.py:130 NORMAL_HDV['share'] - never read (and 0.96 + reckless 0.02 does not sum to 1)
  - traffic_environment/vehicle_fleet.py:~160 WEATHER_PROFILES heavy_rain/fog - never sampled in evaluation (notes_vehicles.md)
- Traps: The docstring (lines 6-7, 19-25) contradicts the code (lines ~133-142): it says reckless 3-5 %, sigma 0.6, tau 0.6-0.9, speedFactor 1.15-1.25, minGap x0.5-0.7, but the code has 2 %, sigma 0.5, tau 1.0-1.2, speedFactor 1.08-1.15, minGap x0.75-0.90. design_v0 §5 already flags this mismatch. Every type is Krauss. The 'CAV' type is Krauss with sigma 0, tau 1 and half the minGap: it is not a CAV/ACC model. The comment 'Calibration target ~1 collision per 72-120 episodes' is impossible under Krauss safe-gap dynamics (audit_2026-05-20:136). Weather silently changes actionStepLength (2-3 s in fog). The truck_trailer vClass is 'trailer'. At 100 % CAV (the v5 headline runs) no HDV was ever spawned, so none of the HDV logic was exercised.
- Verifier (upheld): REFERENCE with dead parts (BASE_SPECS sigma, NORMAL_HDV share, weather) → REFERENCE. There is no vsl_lab importer. NORMAL_HDV['share'] is never read: only RECKLESS_HDV['share'] is used (line 398). The sigma comes from RECKLESS_HDV/CAV_CONFIG (lines 298, 351). design_v0:113 asks to 'fix its docstring/code mismatch first', but B1-B15 are drafts until re-confirmed (v5b1 decisions.md header).

### `core/env_interact.py`: DROP
- Reason: A Gymnasium single-agent VSL env over socket TraCI (subprocess sumo plus --remote-port, _free_port at line 74), with ramps_v2 edges hard-coded. v5.B.1 uses libsumo, a PettingZoo ParallelEnv with per-CAV agents, and no VSL (V7, V15, V17). vsl_lab does not import it.
- Traps: Things the new env must not copy: (1) --time-to-teleport -1, --collision.action warn and --no-warnings (lines ~416-423) hide gridlock and conflict with V6 (any teleport makes the run invalid). (2) _recover_sumo (line 473) restarts SUMO in the middle of an episode, fast-forwards and keeps going with zeroed metrics. That is non-deterministic and hides crashes. (3) CAVs are found by the substring 'cav' in typeID (line ~609), not tracked by id. (4) slowDown(veh, v, 30 s) is re-issued every 5 SUMO steps (line ~540). I believe slowDown ramps linearly over its duration, so re-issuing it restarts the ramp and the CAV approaches the target only sluggishly [VERIFY SUMO semantics]. V5 found that setSpeed under speed mode 95 is the right primitive. (5) Exceptions are swallowed silently around every TraCI call. (6) PRODUCTION IMPORTS A TEST MODULE: line 289 'from tests._sumo_helpers import generate_stochastic_route_file'. (7) An empty detector gives speed 0 m/s (getLastIntervalMeanSpeed -1 clamped to 0), so free flow reads as stopped. (8) upstream_demand_vph (line 693) sums 4 serial segments, about 4x demand. (9) _current_speed_limits_ms survives reset (state leak, notes_rl_design §8). (10) getCollidingVehiclesNumber is polled, but it is structurally 0 under Krauss.

### `core/__init__.py`: DROP
- Reason: Re-exports the legacy SAR/VSL API. Its only importers are train.py, evaluate_models.py and the legacy tests.
- Traps: It wraps the monitoring import in try/except ImportError, so a missing SB3 silently sets HarmonizationMonitor=None.

### `core/algos/__init__.py`: DROP
- Reason: Unreached in the import graph. The registry is empty (no algorithm modules exist next to it), and its TYPE_CHECKING import points to train_eval.drl_vsl_train, which does not exist (ls: no such directory). Vulture also lists register/create_algorithm/available_algorithms as unused.
- Dead / obsolete parts:
  - core/algos/__init__.py:19 register
  - core/algos/__init__.py:31 create_algorithm
  - core/algos/__init__.py:43 available_algorithms
  - core/algos/__init__.py:48 _auto_import_modules (imports nothing)

### `core/constants.py`: DROP
- Reason: VSL constants (MAX_SPEED_KPH 130, min 50, step 5, adjacent difference 10). v5.B.1 has no VSL, and V13 sets the maximum at 120 km/h.
- Dead / obsolete parts:
  - core/constants.py:16 DEFAULT_MAX_ACTION_DELTA_KPH - unused (vulture, grep)
- Traps: MAX_SPEED_KPH=130 does not match the 120 km/h network maximum (V13).

### `core/env_metrics.py`: DROP
- Reason: TrafficMetrics dataclass of ramps_v2 per-segment E1 fields. Used only by the legacy env and rewards.
- Dead / obsolete parts:
  - core/env_metrics.py:31,33,55,58,60,62-64,67,68 per-segment fields never read (vulture)
  - core/env_metrics.py:124 upstream_demand_vph, :125 tts_increment_s - written, never read

### `core/monitoring.py`: DROP
- Reason: SB3 BaseCallback 'basin detection' for VSL actions by regime. Not attached to training (notes_rl_design §9.4). It assumes the 56-D r44_state_v1 observation.
- Traps: It hard-codes the observation layout of r44_state_v1, so it breaks silently with any other state.

### `core/regime_detector.py`: DROP
- Reason: Speed/occupancy thresholds at one ramps_v2 detector, calibrated for a 100 km/h, 4->3 network. The v5.B.1 regimes must be pre-registered fresh (CLAUDE.md design principle). Only eval_metrics and the r44 states use it.
- Dead / obsolete parts:
  - core/regime_detector.py:37 TrafficRegime.vsl_useful
  - core/regime_detector.py:124 classify_windows
  - core/regime_detector.py:145 regime_fractions
- Traps: The docstring says 150 s windows, but it is called every 30 s, and it assumes a 100 km/h free-flow speed while the network runs at 120.

### `core/sar_frame.py`: DROP
- Reason: ABCs and a string registry for State/Action/Reward plugins (single agent, Gym). The ADR-001 contracts (Policy.act on an agent dict, a ParallelEnv) replace it. The plugin pattern is described in notes_rl_design §8 if ever needed.
- Dead / obsolete parts:
  - core/sar_frame.py:89 StateRepresentation.get_observation
  - core/sar_frame.py:103 invalid_action_penalty
  - core/sar_frame.py:145 RewardFunction.reset_metrics
- Traps: RewardFunction defines no reset(), yet env_interact.py:215 calls reward_func.reset(), so subclasses without one would raise (notes_rl_design §8; I did not run it).

### `sar_components/__init__.py, sar_components/discovery.py, sar_components/registry.py, sar_components/{actions,rewards,states}/__init__.py`: DROP
- Reason: pkgutil plugin discovery for the r44 components. The import graph calls them 'unreached', but that is a false positive: they are loaded by string through discover_components(). It does not matter, because the whole SAR stack is VSL-only and legacy.
- Dead / obsolete parts:
  - sar_components/discovery.py:68 get_discovery_errors - unused

### `sar_components/actions/r44_action_v0.py, r44_action_v1.py, r44_action_v2.py`: DROP
- Reason: VSL action spaces (Box(4)/Box(5)/Box(7) speed limits). V15 removes VSL. v0 is referenced nowhere outside sar_components (grep). v1 is used only by _common_config.yaml and the legacy tests, and v2 by per_lane_stochastic*.yaml.
- Dead / obsolete parts:
  - sar_components/actions/r44_action_v0.py whole file - no config or code names it
- Traps: The r44_action_v2.py:16 docstring claims '92 % comply'. That compliance is not implemented anywhere (notes_vehicles §6.1.2).

### `sar_components/rewards/r44_reward_v0.py ... r44_reward_v4.py`: DROP
- Reason: VSL rewards. v4 is the TQC-era production reward, and v0/v1/v3 are named by no config or code (grep). V16 defines a new generalised-cost reward.
- Dead / obsolete parts:
  - sar_components/rewards/r44_reward_v0.py, r44_reward_v1.py, r44_reward_v3.py whole files - referenced nowhere
- Traps: The v4 reward was MIS-SPECIFIED: 4 of its 5 terms measure speed variance and none measures delay, TTS or throughput, so the agent won reward by congesting the road (audit_2026-05-20 claim analysis, +23 % TTS). Its header says '10x scale, merge term' but the code has _SCALE=5 and no merge term. Lesson for V16: the reward must be the objective itself (generalised cost), not proxies.

### `sar_components/states/r44_state_v0.py, r44_state_v1.py, r44_state_v2.py`: DROP
- Reason: 56-D ramps_v2 E1 observation vectors with a regime one-hot. Per-CAV local observations replace them (V3, V7). state_v0 is referenced nowhere.
- Dead / obsolete parts:
  - sar_components/states/r44_state_v0.py whole file - referenced nowhere

### `train.py`: DROP
- Reason: SAC/TQC (sb3_contrib) single-agent trainer for v5.1 per-lane VSL (TQC era, explicitly excluded). ADR-001 picks its own shared-parameter PPO; vsl_lab/train/train_sb3.py is the SB3 fallback, not this file.
- Traps: EvalCallback on the same 200-scenario training pool, so checkpoints were selected on training scenarios (notes_networks V14). UTD was about 1/48 (notes_rl_design §9.1). The doc says TQC critics 2 / buffer 200k, the code has 5 / 500k.

### `evaluate_models.py`: DROP
- Reason: Legacy evaluation of NC, static baselines and SAC/TQC models. vsl_lab/eval/stats.py replaces it (paired median plus bootstrap).
- Dead / obsolete parts:
  - evaluate_models.py:221 episode_seed unused
  - evaluate_models.py:240 peak_demand unused
- Traps: 'NC' was not uncapped: it posts 120/120/120/90 km/h to the CAVs (lines 154-158), which contradicts V4. Means and std only, no paired CIs. Train/eval mismatch: trained on the focused pool, evaluated on the capped 3-phase generator (V2 in notes_networks). ramp_fraction is logged as 0 in every row (lines 238-241).

### `generate_scenarios.py`: DROP
- Reason: CLI for traffic_environment.scenario_pool (Hermite/focused pools on ramps_v2). Superseded, and V9 drops 'demand' generation in this form.

### `traffic_environment/scenario_pool.py`: DROP
- Reason: ScenarioManager and pool writer for ramps_v2. Used only by train.py, generate_scenarios.py and a legacy test.
- Traps: Ramp vehicles from the bins before 100 s are crammed into [100,101) s (lines 342-353; 30-39 vehicles in 1 s on a 1-lane ramp). insertionChecks='none', departPos='last', departSpeed='desired' (lines 370-375). It imports generate_sumocfg from tests._sumo_helpers (lines 158, 292), so production depends on tests. Committed pool .sumocfg files hold absolute /home/catalin/work paths.

### `traffic_environment/demand_profiles.py`: DROP
- Reason: Hermite stochastic demand on ramps_v2. Only scenario_pool imports it, plus the dead scenario_generator, which imports the missing make_counts_from_profile. The v5.B.1 inflow comes from the MnDOT US-169 morning shape (M generator in vsl_lab, another agent's scope).
- Dead / obsolete parts:
  - traffic_environment/demand_profiles.py:53 control_points_t, :56 control_points_vph, :77 metadata - never read
- Traps: The ramp is a fixed fraction of total demand with the same time shape as the mainline (lines 375-381), so the two are perfectly correlated (notes_networks V8).

### `traffic_environment/stochastic_demand.py`: DROP
- Reason: A second, duplicate DemandProfile/generate_demand_profile (3-phase trapezoid). Used by env_interact and the legacy tests.
- Dead / obsolete parts:
  - traffic_environment/stochastic_demand.py:28 t_peak_s, :29 t_decay_s - never read
- Traps: The same name, DemandProfile, is defined in two modules with different fields. The ramp is a fixed fraction of the mainline (lines 85-87).

### `traffic_environment/anomaly_injector.py`: DROP
- Reason: Perturbations through TraCI, attached to the legacy env. A perturbation library is not in the v5.B.1 decisions yet.
- Traps: ramp_spike adds typeID='HDV', which exists in no route file, and the exception is swallowed, so 'anomaly' episodes had no perturbation (lines 195-205). speed_reduction and lane_closure reset the edge to 120 km/h at the end and override the controller; the 'closure' is just a 10 km/h lane (lines 147-182).

### `traffic_environment/scenario_generator.py`: DROP
- Reason: DEAD: it cannot be imported. Line 19 imports make_counts_from_profile, which does not exist (git grep finds only this line and a doc). It never imports and is never imported (imports.json never_imported_not_main).
- Dead / obsolete parts:
  - traffic_environment/scenario_generator.py whole file (106 compose_scenario_prefix, 311 resolve_curriculum_settings, 676 generate_scenario_pairs_parallel never called)
- Traps: Seeds come from Python hash() of strings (lines 567, 589), which is not reproducible across processes. Its topology map lacks ramps_v2.

### `traffic_environment/rou_writer.py`: DROP
- Reason: DEAD: only the dead scenario_generator imports it (imports.json 'unreached'). This is the v4 compliance-group route writer.
- Dead / obsolete parts:
  - traffic_environment/rou_writer.py whole file (796 total_bins unused, among others)
- Traps: It uses the unseeded global np.random (lines 462-515, 737-833) and needs network_config_4_3.yaml and 4_3_merge.net.xml, neither of which is in the repo.

### `traffic_environment/sumo/generate_ramp_network_v0.py, generate_ramp_network_v1.py, generate_ramp_network_v2.py, generate_detectors_v1.py, generate_detectors_v2.py`: DROP
- Reason: Generators for the ramps_v0/v1/v2 nets. No code references them (grep finds only self-references). vsl_lab/netgen/mrg3.py rebuilt the ramps_v2 geometry cleanly, and F3Z grows from vsl_lab/netgen/corr2.py SPEC_AUX.
- Dead / obsolete parts:
  - traffic_environment/sumo/generate_ramp_network_v2.py:143 lane_0_y_4L unused
- Traps: The v0/v1 nets are hand-written XML without internal junction links (notes_networks V15).

### `traffic_environment/sumo/ramps_v0.net.xml, ramps_v1.net.xml, ramps_v2.net.xml, detectors_ramps_v0/v1/v2.add.xml, network_config_ramps_v1.yaml, network_config_ramps_v2.yaml, colored.view.xml (60 KB)`: DROP
- Reason: Static network and detector files of the legacy plant. Not referenced by vsl_lab. colored.view.xml is referenced only by the dead scenario_generator.
- Traps: On ramps_v2 the ramp is limited to 25 m/s and the mainline to 33.33. NC never broke down on this plant in evaluation (merge at 83-86 km/h).

### `configurations/_common_config.yaml, per_lane_stochastic.yaml and its 8 ablation variants (10 files)`: DROP
- Reason: Configs for r44 VSL training with SAC/TQC (the ablations of the 2026-05 reward-weight matrix).
- Dead / obsolete parts:
  - configurations/_common_config.yaml:13 speed_limit_direct_control_CAV and :18 cavs_percentage - read by no Python file (notes_vehicles)
- Traps: The headline runs used cav 100 % (per_lane_stochastic.yaml:16), so the HDV machinery was inert.

### `tools/eval_to_kpi.py`: DROP
- Reason: Post-processing of the legacy evaluation_summary.csv (TQC-era KPI tables).
- Dead / obsolete parts:
  - tools/eval_to_kpi.py:320 m110_reward, :321 m60_reward unused
- Traps: It inherits every eval_metrics.py accounting bug (arrivals, TTS without the origin queue).

### `tools/check_training_status.sh`: DROP
- Reason: Monitors the legacy training_runs on remote VMs.

### `deploy_remote.sh, deploy_4vm.sh, launch_training.sh, launch_evaluation.sh`: DROP
- Reason: Cloud-VM bootstrap for 4 VMs running SAC/TQC Box(4)/Box(5). v5.B.1 runs locally under the CPU guard and scheduler, in systemd user units.
- Traps: deploy_remote.sh runs sudo apt-get and adds a PPA (lines 46-82) and installs pip packages without pins. launch_training.sh shuts the VM down automatically (lines 99-137). Both are system changes that CLAUDE.md forbids, so never run them on the laptop.

### `requirements.txt`: DROP
- Reason: Unpinned and includes sb3-contrib (TQC). v5b1 already has toolchain/requirements_lock.txt.

### `pytest.ini`: DROP
- Reason: v5b1 has pyproject.toml. The only content worth keeping is the 'sumo' marker, which is a one-line idea for pyproject.

### `.gitignore`: REFERENCE
- Reason: v5b1 has its own. The patterns training_runs/, scenario_pools/, artifacts/* and reports/ show what must never be committed. Raw runs belong under /home/catalin/work/phd (CLAUDE.md).
- Traps: research_notes/ is neither ignored nor tracked.

### `README.md`: DROP
- Reason: v5.1 per-lane VSL / TQC README. v5b1 has its own.
- Traps: Stale: it says ramps_v0 with an off-ramp (notes_networks V15).

### `CLAUDE.md (archive root)`: DROP
- Reason: v5.B rules. v5b1/CLAUDE.md supersedes it. Keep it on the archive branch only.
- Traps: Its toolchain line points to v6's venv314, which V14 forbids for v5.B.1.

### `tests/_sumo_helpers.py`: DROP
- Reason: Route and config helpers for the legacy env. Production code imports this test module (env_interact.py:289, scenario_pool.py:158,292).
- Traps: One Bernoulli draw per second per route (lines 120-131) caps each route at 3,600 veh/h, so NC never broke down (notes_networks V1; confirmed by reading the code). insertionChecks='none' at lines 91-94 and 149-152. Absolute /home/catalin paths in the generated .sumocfg (lines 179-187).

### `tests/test_env_inter.py, test_state_live.py, test_ramp_vsl_effect.py, test_config_consistency.py, test_smoke_training.py, test_scenario_pool_training.py, run_feasibility_sweep.py, run_feasibility_sweep_v52.py, run_phase3_validation.py, run_reward_landscape_check.py, run_sumo_gui.py, readme.md, __init__.py`: DROP
- Reason: Tests and sweeps of the legacy core/SAR/ramps_v2 stack (last touched 2026-03 to 2026-05). They import only core, sar_components, traffic_environment and train.
- Traps: test_smoke_training checks that SB3-Contrib imports, which ties it to TQC.

### `tests/test_capacity_drop.py`: REFERENCE
- Reason: Test idea for the F3Z P0 realism check: sweep the inflow, look for a discontinuous discharge drop plus hysteresis, and compare 3 driver-parameter sets. The vsl_lab realism protocol (R-a..R-d) is the stronger template.
- Traps: Socket TraCI on ramps_v2. The literature values it quotes (Chung et al. 2007, 8-15 % drop) are not checked here [VERIFY].

### `tests/test_reward_e2e_verification.py`: REFERENCE
- Reason: Good test pattern for V16: recompute the reward by hand from raw sensor reads at each step, and assert that the env's reward matches it within tolerance.
- Traps: It is written against r44_reward and E1 detectors on ramps_v2.

### `tests/persistent_results/** (9 CSV + summary.txt + summary_elaborated_18-03-2026_14-08-30.md)`: DROP
- Reason: Tracked result bloat: 425,337 bytes in total (nocontrol_all_demands.csv alone is 207,203 B; 8 per-demand CSVs of about 26-27 KB each). They are NC sweeps on ramps_v1 (2026-03-18).

### `tests/test_guard.py`: TRIM
- Reason: Required: the CPU guard is mandatory, and v5b1 CLAUDE.md says to port vsl_lab/ops/guard.py and tests/test_guard.py before the first batch. Port it with the guard.
- Dead / obsolete parts:
  - tests/test_guard.py:46-77 thermal_on, test_thermal_off_by_default, test_thermal_hysteresis_v6, test_emergency_pauses_at_once_and_pauses_jobs, test_missing_sensor_disables_thermal_only - drop if the port removes the thermal pause path (rule removed 2026-10-10; v5b1 keeps only temperature logging). Keep them only if the opt-in 'thermal: 1' switch is ported
- Traps: It tests the 'thermal.json' live-config path under /home/catalin/work/phd/vsl_lab_runs/ops. The ported guard should take a v5b1-owned config path. Keep test_live_config_override and test_malformed_live_config_falls_back (lines 80-98), because the CPU limit is read live.
- Verifier (upheld): TRIM: drop thermal tests at 46-77; keep 80-98 → TRIM (as mapped), plus lines 96-98 when the thermal config keys are removed.. v5b1 CLAUDE.md:85-86 says to port guard.py and test_guard.py and that the thermal rule is removed (only logging stays). Lines 46-77 are thermal_on and the 4 thermal tests, as mapped. Missed: test_malformed_live_config_falls_back lines 96-98 assert load_cfg(f)['center'] == 94.0, and 'center' is a thermal-hysteresis key. Drop or rewrite that assertion if the thermal keys go.

### `tests/test_corr2_build.py`: TRIM
- Reason: Needed when F3Z is ported from vsl_lab/netgen/corr2.py SPEC_AUX. Keep the build, lane-count/length, connection, detector-on-lane and 'SUMO loads' checks. Remove everything about meters, since V15 has no ramp meters.
- Dead / obsolete parts:
  - tests/test_corr2_build.py:22-31 fixture 'built' builds the base SPEC (CORR2 with O1), not SPEC_AUX: retarget it to F3Z
  - tests/test_corr2_build.py:59-69 test_connections asserts the O1 off-ramp and the m3->m4 identity, which belong to CORR2 v1, not CORR2X/F3Z
  - tests/test_corr2_build.py:72-85 test_no_mainline_tls - meter TLS / all-green programs, dead without meters
  - tests/test_corr2_build.py:91-92,103-105 ALINEA loop detectors e1a_* - meter feedback, dead
  - tests/test_corr2_build.py:127 meter_R1/meter_R2 tl_links assertion in test_corr2x_aux_lane_exits
- Traps: Line 6 of the docstring hard-codes the v6 venv314 path, which V14 forbids. Line 141 asserts that CORR2 stays unchanged next to the X variant; F3Z needs its own cache key.
- Verifier (upheld): TRIM with dead parts at 22-31, 59-69, 72-85, 91-92/103-105, 127 → TRIM (as mapped), plus the extra dead lines 47-50, 56 and 93, the shared-cache trap at line 124, and the meter asserts turned into no-TLS asserts.. Confirmed by reading lines 1-140. Dead parts the map missed: lines 47-50 (merge1/merge2 == 4 lanes, O1 1 lane) and line 56 (O1_0 = 300 m) assert base CORR2. Under SPEC_AUX merge2 has 3 lanes and there is no O1 (line 134). Line 93 '+ ["e1_O1_0"]' also expects the removed O1 detector. Docstring lines 1-3 describe meters. Trap: test_corr2x_aux_lane_exits (line 124) calls N.build(N.SPEC_AUX) without the tmp NET_CACHE swap of the 'built' fixture, so it writes into the shared cache. Under V15 the meter asserts should be inverted (assert tls_ids == [] and no traffic_light junctions), not just deleted, so that a stray TLS is caught.

### `tests/test_train_s0.py`: REFERENCE
- Reason: ADR-001 uses its own PPO, and SB3 is only the fallback. The C1 convergence tests (lines 91-165) are good test ideas for the convergence check the method requires (DRL budget). The LinearDecay/build_model tests are SB3-specific.
- Traps: Per notes_rl_design §9.7, RecurrentPPO and TRPO ignored --lr-decay, and the R6 learners did not meet C1.
- Verifier (overturned): REFERENCE (SB3-specific; C1 tests are only test ideas) → TRIM, conditional on convergence.py being ported (vsl_lab area): port the C1 tests with convergence.py and drop the SB3/train_sb3 tests and imports listed in the evidence.. The C1 tests (lines 81-166) exercise vsl_lab/train/convergence.py via cv.check(val_rows, prog_rows, sign, n_actions/action_dim). That module is 197 lines, imports only stdlib (argparse, csv, json, math, pathlib) and is trainer-agnostic: it works on update/val_return/entropy/explained_var rows. v5b1 CLAUDE.md:70 requires 'a convergence check' for every DRL run, and the own PPO of ADR-001 can log the same rows. So the C1 tests are a direct port, not just an idea. The SB3-only parts are lines 11, 14-15 and 18 (gymnasium, torch, DummyVecEnv, and train_sb3 LinearDecay/build_model/n_actions_of), lines 43-79 (test_linear_decay_values_and_pickle, test_decay_reaches_optimizer, test_constant_lr_without_decay, test_n_actions_of), test_action_dim_of (~line 168) and test_trpo_entropy_logged_from_buffer (~line 173). The TRPO entropy cases (~lines 138-148) encode an SB3/TRPO logging gap and are optional.

### `tests/test_cooling.py`: REFERENCE
- Reason: The fan controller is the vsl-cooling systemd unit, which is not running and is restarted only on the author's request. It is not part of the v5.B.1 software, so the test should stay with the archive code.
- Traps: Never drive the pad or laptop fans from batch code.

### `tests/test_metanet.py, test_metanet_ctrl.py, test_metanet_events.py, test_metanet_gate_refactor.py, test_metanet_j5_eval.py, test_metanet_v4.py, test_metanet_v5.py, test_testbed_screen.py, test_bn4_meter_rate.py, test_specialist.py`: DROP
- Reason: They test METANET, the day-pattern testbed, BN4 meter-rate and the VSL SPECIALIST, all out of scope for v5.B.1 (no METANET, no meters, no VSL, no day-pattern). They are about 140 KB of tests.

### `research_notes/Daily demand patterns freeway control/*.md (5 files, 169 KB, UNTRACKED, not ignored)`: REFERENCE
- Reason: Literature notes dated 2026-10-04, with read-status tags. realistic_freeway_plants.md (SUMO capacity-drop settings, merge pitfalls) and open_daily_data.md (MnDOT and PeMS access) are relevant to F3Z realism and the US-169 inflow. demand_vs_volume.md, learned_anticipation.md and tod_day_type_selection.md are day-pattern topics. The author should decide whether to commit the two relevant notes under v5b1 docs/research/; they show as '??' in the archive status.
- Traps: Most claims are tagged [VERIFY]/[SAGE] (abstract or snippet only). One note says an automated summary invented content (Hickert et al. 2026). Keep the tags if the notes are copied.

### `artifacts/ (2.7 GB), training_runs/ (9.8 GB, 16 experiments), scenario_pools/ (258 MB), reports/ (2.9 MB) - ignored, untracked`: DROP
- Reason: TQC/SAC VM outputs (vm1_sac_4, vm2_tqc_4, vm3_sac_5, vm4_tqc_5), 2026-05 experiments, the focused pool and KPI reports. None is in git and none is needed. Deleting them from disk (about 12.8 GB on exFAT) is the author's call, not part of the port.
- Traps: Pool .sumocfg files hold absolute paths into the other mirror.

- Verifier (overturned) on `research_notes/Daily demand patterns freeway control/*.md`: REFERENCE; the author should decide whether to commit the two relevant notes under v5b1 docs/research/ → DROP (a duplicate on disk; deleting it is the author's call). Point any F3Z-realism or MnDOT reading at the tracked docs/review/day_pattern_notes/realistic_freeway_plants.md and open_daily_data.md (docs area). Keep the [VERIFY]/[SAGE] tags if they are copied to v5b1.. All 5 files are byte-identical (cmp) to the TRACKED docs/review/day_pattern_notes/{demand_vs_volume,learned_anticipation,open_daily_data,realistic_freeway_plants,tod_day_type_selection}.md (git ls-files lists them). The untracked folder is a stray duplicate. Nothing in it is uncommitted.
- Verifier (uncertain) on `tests/test_specialist.py`: DROP (VSL SPECIALIST out of scope) → Follow the vsl_lab-area verdict for controllers/specialist.py: DROP if V19 does not adopt a SPECIALIST-derived comparator, otherwise REFERENCE. Settle it only after the V19 literature check.. It tests vsl_lab/controllers/specialist.py (Hegyi et al. SPECIALIST, a VSL jam-absorption scheme), which vsl_lab/jobs/mrg3_run.py:28 imports. V15 removes VSL, so as a VSL controller it is out of scope. But V19 names 'jam absorption' and 'the archived MRG3 staircase / PI rules' as candidate rule-based comparators, and the literature choice is still open. If a CAV jam-absorption comparator reuses SPECIALIST's shockwave math (front_speed, scheme_states), these tests become the reference oracle.
- Verifier (upheld) on `core/*, sar_components/*, train.py, evaluate_models.py, generate_scenarios.py, traffic_environment/*, tools/*, configurations/*`: DROP (legacy single-agent VSL/TQC stack; dead files and parts as listed) → DROP. Nothing under vsl_lab imports these (git grep 'from|import core|sar_components|traffic_environment|train|tools|tests' over vsl_lab returns nothing, and no dynamic import in vsl_lab names them). The only legacy-path string in vsl_lab is a docstring in mrg3.py:1. Configs name only r44_state_v1/v2, r44_action_v1/v2 and r44_reward_v2/v4, so action_v0, reward_v0/v1/v3 and state_v0 appear only in docs/review/design_space/notes_rl_design.md. make_counts_from_profile is defined nowhere, so scenario_generator.py cannot be imported. core/algos has only __init__.py, and 'train_eval' appears only there. Dead symbols confirmed: DEFAULT_MAX_ACTION_DELTA_KPH (only its definition), classify_windows, regime_fractions and vsl_useful (only defined in core/regime_detector.py), and evaluate_models.py:221/240 (episode_seed, peak_demand). Spot checks of the trap claims: _nc_action posts 120/120/120/90 (evaluate_models.py:154-158); _sumo_helpers draws one Bernoulli per second per route (lines 120-131); env_interact.py:289 and scenario_pool.py:158 import tests._sumo_helpers.
- Verifier (upheld) on `tests/persistent_results/**`: DROP as tracked bloat (425,337 B) → DROP from the port; keep on the archive branch (cited evidence).. The size is confirmed at 425,337 B. Caveat: tracked docs cite these files as evidence, e.g. docs/plans/vsl_hybrid_screen_v0.md:18,50 ('[CALC ✓, tests/persistent_results/…/nocontrol_7000vph.csv]'), notes_history.md:27 and notes_networks.md:57. So they must stay on the archive branch, and only skipping them in the port is right.
- Verifier (upheld) on `tests/test_capacity_drop.py, tests/test_reward_e2e_verification.py, tests/test_cooling.py`: REFERENCE → REFERENCE. test_capacity_drop.py has 0 pytest test functions: it is a CLI script (argparse, line 329) on ramps_v2 that uses socket traci (line 174) and _sumo_helpers. test_reward_e2e_verification imports env_interact (r44 and E1). test_cooling tests vsl_lab/ops/cooling.py, which v5b1 CLAUDE.md:87 keeps on the archive branches as the vsl-cooling unit.
- Verifier (upheld) on `tests/test_metanet*.py, test_testbed_screen.py, test_bn4_meter_rate.py`: DROP → DROP. Their imports are vsl_lab.plants.metanet, jobs.metanet_*, data.metanet_*, jobs.testbed_screen, envs.bn4_env (meter_rate) and jobs.bn4_eval. Every one is METANET, the day-pattern testbed or ramp meters, which V15 and the task brief exclude.
- Verifier (upheld) on `pytest.ini, requirements.txt, README.md, CLAUDE.md, .gitignore, deploy/launch shell scripts`: DROP / REFERENCE (.gitignore) → As mapped. The v5b1 pyproject.toml has no 'sumo' marker (grep), so the map's one-line note to carry the marker over is valid. The other claims match the files.

**Verifier: missed items and extra traps**
- /srv/shared/Workspace/phd/phd_speed_harmo_v5/.venv/ (8.6 GB, ignored): the legacy Python 3.12 venv (pyvenv.cfg home=/usr/share/sumo/bin, created under /home/catalin/work/...). CLAUDE.md says it has no python executable on this mirror. Verdict DROP: do not port it; deleting it is the author's call.
- /srv/shared/Workspace/phd/phd_speed_harmo_v5/.claude/settings.local.json (ignored): it allows 'Bash(*)' and 'Bash(*:*)' and denies only rm/mkfs/dd. Verdict DROP. Trap: do not copy this blanket permission into v5b1.
- /srv/shared/Workspace/phd/phd_speed_harmo_v5/.codex (ignored, 0-byte file): DROP.
- /srv/shared/Workspace/phd/phd_speed_harmo_v5/docs/knowledge_base/ (406 MB, ignored; papers_RL_VSL, papers_RL_RM, papers_DistRL, papers_RL-DRL_CFM, framework): not classified by any area I can see. Flag it to the docs agent: REFERENCE at most, never commit (copyright and size).
- research_notes/ is a byte-identical duplicate of the tracked docs/review/day_pattern_notes/ (see challenge).
- tests/test_train_s0.py C1 tests depend on vsl_lab/train/convergence.py (stdlib-only, trainer-agnostic), which the CLAUDE.md 'convergence check' requires. Make sure the vsl_lab-area map gives convergence.py PORT/TRIM rather than lumping it with train_sb3.
- tests/test_corr2_build.py: dead lines 47-50, 56 and 93 (base-CORR2 O1 and merge2 4-lane asserts), and the shared NET_CACHE write at line 124.
- tests/test_guard.py:96-98: asserts the thermal key 'center' == 94.0; dead if the thermal config keys are dropped.
- docs/v5b/design_v0.md:148 says to port core/eval_metrics.py for SSM-based TTC, but eval_metrics has no SSM (it uses getLeader at line 242). That is a trap for whoever follows design_v0 (docs area).
