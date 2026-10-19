# Direction sweep v2: self-calibrated margins in road traffic (V86, 2026-10-18)

**Method.** 4 scouts (freeway, vehicle, intersection, open), a synthesis step, 6 adversarial refuters, and a final ranking. 18 candidates went through the 5 gates of V86. The full output is in `direction_sweep_v2_margins.json`.

**Data hygiene.** Exploratory numbers use spent data only (NGSIM I-80/US-101, TGSIM, and the Hamburg screen days), with unreviewed scripts. WaveX was not opened.

**Outcome: no candidate passes all five gates. None is recommended for a build.**

| Candidate | Status | Weakest gate |
|---|---|---|
| Wave-smoothing caution margin from roadside radar (line #3) | possible | G3 crowding (CIRCLES/Vanderbilt, Toyota patent); G2 not measured (toy model only) |
| Ramp queue-override margin | possible | G2: analytic bound ~0.1–0.5 % of bottleneck flow; the fixed 25 % margin is already deployed (IRIS) |
| Permissive left-turn critical-gap margin (AV) | possible | G2: a phase-conditional fixed table expected to win; adaptive buffers already published (2026) |
| Incident detection threshold, queue warning, lane-change gap | killed | G2 or G5 |
| Bus-priority ETA window | killed | G2 **measured**: time-varying hindsight only 1.9 % narrower than a constant |
| ALINEA set point, VSL threshold, gap-out, yellow/all-red, pedestrian, FCW timing, V2X gap, curve/friction, truck eco-cruise band, weather speed, heavy-vehicle leader margin | killed | listed in the JSON |

**Pattern across every domain checked.** Line #1, screen #2 and the bus window (measured), plus queue warning, incident detection, lane change and left turn (literature or reasoning), all point the same way: a fixed per-site or per-regime table, or "calibrate once, then freeze", matches online self-calibration.

Reasoning (not a measured fact): a margin is a quantile of an error distribution. Online self-calibration only pays when there is drift within a site that observable regimes do not explain. No scout found such drift.

**Limits.**
- Patents are incomplete (Google Patents was not queried).
- G1 and G2 were not measured on real data for any survivor.
- arXiv counts are a poor proxy for fields that publish in TRR, TR-C and agency reports.
- The gate weights were set without the supervisor's input on the claim bar.
