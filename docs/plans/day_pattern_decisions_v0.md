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
