# Merge V&V checks: review rounds and how the plan handles them

Each round: reviewers for design and statistics (Fable 5.2), build feasibility (Opus 5.5), a committee view (Opus 5.5) and field data (Fable 5.2). Each finding was re-derived by a skeptic on the other model, then a completeness critic (Opus 5.5) looked for gaps. All reviewers were read-only, with no simulation. Scripts, outputs and every finding with its verdict are in `docs/research/results/merge_vv/review_r1/`. The NGSIM first look made there (field and design folders) is disclosed under VV-D5.

## Round 1: draft v0 (2026-11-15)

| # | Finding | Verdict | v1 handling |
|---|---|---|---|
| D1, C1 | V3 cannot tell an artefact from "longer lanes remove merge close-following for every arm"; NOT SHOWN is the likely outcome (80-85 % of each arm's count is in the merge area) | confirmed (major) | Q3 reworded as dependence; expectation table before data; the "outside training range" excuse removed; a 300-m main-lane sensitivity added (V3a) |
| C2, D10 | The HOLDS sentence overclaimed | confirmed | record sentences fixed per outcome |
| D2, B7, C4, F8 | The stop gate was a point rule over both lanes; the counters are vehicle-seconds; merge 1 has 136-310 per run in E30 | confirmed | gate per merge with a 95 % bound; "lane-end standing (vehicle-seconds)" everywhere; distinct vehicles from the merge log |
| D3, B5 | V2 tested replication, not resolution; the meter uses a different TTC (no minGap) and samples off-phase | confirmed | meter on the counter's definition, exact equality BUG checks, deciding statistic = 0.1-s minus 1-Hz edge within ±3 points |
| D4, M11 | Levels, null bars and the power line did not match | confirmed (minor) | one readings table (§6): 97.5 % / 1.9 % for both-must-pass, 98.75 % / 0.94 % for WORSE |
| D5, VV-D10 | n = 480 resolves about +7 %; edges at 600 m are expected smaller | partly | n = 480 kept with the resolvable edge stated; 960 listed as the alternative |
| D6, C3, F1-F5 | V4's 6-median rule had no null, mostly measured NGSIM lane coding, and three quantities were not robust | confirmed | V4 descriptive with no verdict: lag gap and speed difference only; I-80 by lateral crossing, US-101 lane 6 → 5 after entry on 7 |
| F6 | NGSIM declared spent (V82); both sides partly seen before approval | confirmed | VV-D5 author decision with disclosure; extraction frozen before the plant log is read |
| D7, B6, C5, M2 | V1's criteria could hardly fail; the counters share one pass | partly | wiring checks labelled; gap rebuilt from positions; every sample classified by code; encounters; stored-seed traces; 0/40 bound stated |
| D8, B3, M4 | Policy position at 600 m not fixed; inputs stay in range but point to the wrong place | confirmed | VV-D7 road-preserving remap (identity at 300 m) |
| B1, B2, C9, D13 | `corridor.build` with `accel_len` in r2m3 leaves 4a at 300 m and stretches rj2; the geometry goal contradicted itself | confirmed | every edge but 3a and 4a keeps its length; r2m3 nodes shifted; T0 on the whole lane-length dict |
| B4, B9 | `LocalRule.N_BINS` hard-coded; other geometry-dependent arms would run silently | partly | bins from the network (equal at 300 m); run guard |
| B10, M12 | Cost left out the meter and the longer network; machine type | confirmed | re-quote from the smoke; one instance type |
| B11 | Identity replay unspecified | confirmed | stored seeds 7,489,160-161, every key |
| C6 | Claim wording should be same-lane close-following on the merge sections | partly | measure wording line at the top |
| C8, D9 | The 300-m readings are a fresh-seed replication of E30 | confirmed | replication line reported with every E30 sentence |
| D11, M5 | Location by road only; "away" was mostly edge 1 (entry) | confirmed | road groups fixed now (merge area, entry, rest); edge-1 samples traced |
| D12, C11 | V5 had no criterion; it is context, not validation | confirmed | criterion and wording fixed |
| M1 | No item answers whether lane-end standing is realistic | major | Q3b row, V6 literature item, limit M1 |
| M3 | "Trained on the metric" not covered | major | shorter-threshold and DRAC edges printed with a fixed sentence |
| M6 | PR-15 keeps the V462 wording gate shut | major | VV-D8, V7 inspection |
| M7 | Merge 1 alone not offered | major | VV-D3 option B |
| M8 | Seeds not approved; blocks could collide | major | VV-D4 approval request; separate trace block 7,493,000-019 |
| M9 | Reader not frozen before data | major | §3: committed before the rental, read once, frozen worktree |
| M10 | No consequence table | major | §6 |
| M13 | Lane-change parameters not varied | minor | VV-D11, a limit |
| D14, B12, C14 | Stored rows already show the half-second-shifted 1-Hz count gives the same edge | info | cited in V2 as post hoc |

## Final check of v1 (2026-11-15)

One checker (Fable 5.2, high), each finding re-derived by a skeptic (Opus 5.5). No blocker; most round-1 majors fixed correctly. Scripts and findings in `docs/research/results/merge_vv/final_check/`.

| # | Finding | Verdict | v1.1 handling |
|---|---|---|---|
| K1 | Q3 promised the size of the dependence, but no statistic measured the change from 300 to 600 m | confirmed (major) | the paired change with a 95 % interval answers Q3; "depends on lane length" only if it excludes 0 |
| K2 | The expected NOT SHOWN or WORSE is carried by edge-1 samples during the slowdown's hold (v3w and p333 22-26 per run, the lr rules 2-3), not by lane length | confirmed (major) | pre-stated; expectation table with an edge-1-excluded column (+11.5 to +6.0); printed 600-m edge without edge 1; "even with a perfect policy" struck |
| K3 | The standing gate voided a reading it no longer guarded; the 80 % bar was no decision | partly | printed cut per merge; "standing removed" wording only above VV-D12's bar; smoke prints standing at 600 m |
| K4 | The 0/40 bound was wrong for the 20 + 20 draw; "non-event" undefined; no cross-lane check | partly | simple random 40 (about 7 %); non-event defined; cross-lane class must be 0; recount wiring extended |
| K5 | "Equal on every key" contradicts V519 | confirmed | traffic keys as cf_ident; a tracer bug re-runs nothing in E30 |
| K6 | The "trained on the metric" sentence left out the braking term | confirmed | sentence fixed; `b45_step` +2.4 [−0.6, +5.0] added |
| K7 | "The two closest rules" vague; 600-m tuning and the 2-of-14 scope unstated | partly | rules named and defined in VV-D2; scope in the record sentences |
| K8 | V2's swap null and NOT INFORMATIVE clause did not fit an equivalence reading | partly | null dropped with its error stated; missed share defined; proxy power in VV-D9 as an assumption |
| K9 | VV-D10's resolvable edge understated; 960 rejected for the wrong reason | confirmed | figures and the real trade stated |
| K10 | V7 could hardly read MET; §6 overstated the V462 gate | confirmed | PR-15's own test; channels as assumptions; gate wording fixed; period split printed |
| K11 | No check that the remap is active at 600 m | partly | smoke assertion and the column-15 cap share |
| K12 | No cap, null details, interval convention, instrument table, combined outcomes, V6 scope | confirmed | all added; cap $4; junctions in "rest" |
| K13 | The main-lane sensitivity lacked its limit sentence | confirmed | added |
| K14 | TTT missing; V4 lag gap undefined; no cons column | partly | added |
| K15 | Reproductions; round the k = 0.2 HOLDS figure | info | "about 0.3-0.4" |
