# Day-pattern track: decision log (v0)

*Author decisions, recorded verbatim in substance, with the date given. Interpretations are marked as such. The documents that asked each question link here.*

## 2026-10-05

| ID | Question (short) | Decision | Where it applies |
|---|---|---|---|
| D1 | What must the winning component be? | **A controller that relies on or integrates DRL.** Supervised neural-network hybrids are only opponents or complements (for example, their forecasts as DRL inputs). **Fallback:** if this research fails, switch to a supervised neural-network hybrid. | `hybrid_combinations_v0.md` §1.6, §6 |
| D2.1 | Does R6 count towards the thesis? | **A chapter with its limits stated, but no paper built on it.** The aim is to repeat the same idea (DRL scheduling a proven controller) on the realistic Minneapolis corridor, and count that. | thesis path §12 |
| D2.2.1 | Which experiment first? | **H1 (HERO + DRL day-pattern scheduler) is the main bet.** H2's quick tool checks (do the speed limits hold traffic back; does the best setting change with the day's capacity) run alongside on the same road and data. | `hybrid_combinations_v0.md` §2–3 |
| D2.2.2 | Surprise events in H1? | **Yes, as secondary surprises**: ramp-demand spikes, local slowdowns and lane closures, besides the day's demand pattern. *Interpretation:* the author pasted both options; the bracketed reason ("it is realistic, it keeps R6's idea alive, and it gives the DRL a second thing to detect early") argues for yes. | H1 design |
| D2.3.1 | Factor roles | **Fixed and calibrated to the real road:** cars, vans, trucks, truck-trailers; normal and mixed driver behaviour; car-following and lane changing. **Hidden, varied day to day:** the day's demand pattern (H1), the day's true capacity (H2), surprise events. **Varied only in the final tests:** weather, reckless drivers, speed-limit compliance outside the usual range, connected vehicles at 10–20 %. | `hybrid_combinations_v0.md` §1.2 |
| D2.3.2 | "Multimodal demand profiles" | **Demand with several peaks.** | all |
| D2.3.3 | Where do the simulated days come from? | **Reconstruct real Minneapolis days, fit a flexible multi-peak model to them, train on generated days, and test on real 2024 days.** | gate draft §2 |
| D2.3.4 | Full days or peak windows? | **Full days.** | gate draft §2 |
| D2.3.5 | Opponents and the informed reference | **Opponents** (all tuned): timetables per weekday type, first-hour pattern matching, tuned ALINEA and HERO, an adaptive ALINEA, an MPC with a forecast learned on separate days, a forecast-informed HERO (LSTM), a breakdown-classifier-triggered HERO, imitation of the informed reference, a simple linear learner (ARS), and DRL alone. **Informed reference:** the same HERO or MPC given the day's true demand. | gate draft §3 |
| D2.4.1 | Two looks under one 10 % rule | **Option (b):** two looks (all days pooled; heavy days only), **each with a stricter 97.5 % CI.** | gate draft §4 |
| D2.5.1 | The learnability ladder | **(b) Cheap rungs alongside the gate; expensive rungs only after a GO.** (a) "Aim it at the hybrid's DRL layer, with DRL alone only as a reference": **not answered explicitly**. Assumed **yes** from the "DRL must work in tandem" decision, and flagged to the author. | thesis path §5.5.4 |
| D2.5.2 | Extend the chosen corridor far upstream (≥ 10 km) | **Approved in principle.** The exact number of data requests is stated before pulling. | thesis path §4.4 |

## Earlier the same day (already recorded elsewhere)

- **The official title is kept.**
- **Priority:** alongside v6 if resources allow, otherwise before v6.
- **ARC-IT framing accepted.**
- **Only positive DRL results count; no negative Paper B.**
- **DRL works in tandem with a proven controller (hybrid first).**
- **Scope:** speed harmonisation and ramp metering on a 2–3-ramp corridor.
- **Plant:** P6b, a METANET gate with SUMO confirmation.
- **Seed block 7,190,000–7,190,999 approved.**
- **Compute rule:** CPU > 90 % for 2 minutes, plus the v6 thermal design.

These are in `Thesis path with daily patterns (human).md` §12, the gate draft §10, and `CLAUDE.md`.

## 2026-10-05 (evening)

| ID | Question (short) | Decision | Where it applies |
|---|---|---|---|
| D3.1 | Corridor after analysis v2 (none eligible; C4 binding) | **U.S.169 SB**, option (a): C4 (a capacity drop of at least 3 %) is **waived as a disclosed deviation decided by the author**. The real median drop, about 1.6 % (r = 0.984, IQR 0.952–1.001), becomes the plant's calibration target. *Interpretation:* the author replied "Proceed" to a message recommending option (a). | `day_pattern_corridor_analysis_v0.md` v2 |
| D3.2 | Controlled ramps | Valley View Rd (M169S51), Marth Rd (M169S54), Anderson Lakes Pkwy (M169S55) and **Pioneer Tr (M169S56)**. Pioneer Tr is added because the all-lane analysis places the active bottleneck at the Pioneer Tr merge (Pioneer Tr → Old Shakopee Rd). | METANET calibration protocol |
| D3.3 | Data | **12,484 requests now** for the complete corridor on the 104 days: the upstream extension to −11.8 km (approved in principle) plus every entrance and exit. The rest of 2023 (≤ 59,769) and 2024 (≤ 83,814) are **asked separately**; 2024 stays unopened until the gate protocol is committed. | data |
| D3.4 | A8: is the corridor still U.S.169 SB now that the data show **two bottlenecks in series**? (B1 = the Anderson Lakes Pkwy merge, near-daily and first; B2 = the Pioneer Tr merge, 45 % of Wednesdays) | **Yes** (author, 2026-10-05). It is a two-bottleneck system with the same four controlled ramps. Day-to-day variety at B1 lies in queue duration and extent, not occurrence. | METANET protocol v2 |
| D3.5 | A2: the upstream boundary (Minnetonka Blvd) is 8.4 km upstream of the first controlled ramp (Valley View), 1.6 km short of the ≥ 10 km rule; it is 14.5 km upstream of the Pioneer Tr merge | **(a) Accept 8.4 km as a disclosed deviation** (author, 2026-10-05). Further upstream is inside the I-394 interchange queue. | METANET protocol v2 |
| D3.6 | Pre-fetch the validation-extension days? | **Yes, now, in parallel** (author, 2026-10-05: "do it now, in parallel, just in case"). All 2023 Tuesdays and Thursdays on the full stretch (commit `4af0674`). They are used only if the METANET protocol's extension rule (§5.2) triggers, never for fitting. | METANET protocol v3 A10 |
| D3.7 | METANET protocol v3 author items (§0.6: A1 (i)–(iii), A3, A4, A5, A6, A7, A9) | **All confirmed as written** (author, 2026-10-05): "confirm all as written. If something goes bad, we will adjust later, after we have a clear path and clear results." A1 (ii): no lane check is performed, so the §1.7 step (b) default applies if F16 flags (G4). Disclosure: v3 was committed (`fc77668`) before this confirmation, contrary to its §8.6 step 1; no real-data step had run. Later adjustments follow the protocol's change rule (§6.3: a new version, committed first). | METANET protocol v3 |
| D3.8 | Install pycma into the shared toolchain venv `venv314` | **Yes** (author, 2026-10-05). cma 4.5.0 installed. | calibration (§4.4) |

## 2026-10-06

| ID | Question (short) | Decision | Where it applies |
|---|---|---|---|
| D4.1 | The gated step-halving check (protocol v3 §2.5) failed at the frozen METANET optimum: J changed by 0.23 % (limit 5 %), but the calibration-day set with a model P_2 (B2) episode changed (20230517 has one at 2.5 s, not at 5 s). By §2.5, §6.1 and §8.6 step 4 this is an N0 FAIL and a route stop before any validation run. Options: (a) accept the stop as pre-registered; (b) a post hoc v4 amendment. | **(a) Accept the route stop as pre-registered** (author, 2026-10-06: "go with (a)"). The FAIL was checked by an adversarial review (4 lenses; none refuted it). Finer steps (2.5, 1.25, 0.625 s) agree with each other, so the 5-s plant is not converged inside the B2 queue. No validation day was simulated; the gate code refuses to run. The next plant is a separate author decision (§0.3, e.g. SUMO with its own realism protocol). | `docs/lab/day_pattern/metanet_calibration.md` (route stop section); protocol v3 §0.3, §2.5, §6.2 |

