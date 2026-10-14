# Pre-P0 pilot on the V68 layout (2026-10-13): plant behaviour, data checks, layout options

**Not protocol data (V69).** The pilot used:
- non-project seeds 1–5 and no controller;
- B0 (human only) and B1 (CAVs on SUMO's default ACC, no commands);
- protocol §2.2–2.4 settings where cheap;
- pilot-only choices: vehicle masses, induction loops every 250 m on every lane (evaluation only), and the delay proxy SUMO `timeLoss` + `departDelay`.

Scripts: `pilot.py` (network, inflow, runs), `batch.py` (24 workers in a systemd unit), `analyze.py` (metrics, charts). Per-run summary: `summary.json`. Raw runs (1.6 GB): `/home/catalin/work/phd/v5b1_runs/pilot_20261013/`.

**Runs:**
- **base:** 10 levels (λ = 0.55–1.00 of the B13 peak) × 5 seeds × {B0, B1} = 100;
- **laneend:** a plain lane end instead of the zipper, λ = 0.7/0.8/0.9 × 3 seeds × {B0, B1} = 18;
- **gap3k:** 3 km instead of 5 km between zones, the same grid = 18.

All 136 ended with return code 0. They took about 25 min wall time on 24 workers, at CPU utilisation ≤ 90 % (76 % sampled).

## 1. Results (medians over seeds)
| Layout · arm · λ | Teleports | Collisions | Emergency-braking warnings | Time lost per vehicle (s) | Queue max (km) | Queue reaches Z3 / Z2 / merge 2 | Pre-queue → discharge flow (veh/h/lane) | Waves at 1.5 km upstream of the drop |
|---|---|---|---|---|---|---|---|---|
| base B0 0.70 | 0 | 0 | 37 | 23 | 0.1 | 0/0/0 of 5 | 1,834 → – | 0 |
| base B0 0.80 | 0 | 0 | 62 | 64 | 1.1 | 4/0/0 | 1,882 → 1,861 (0.98) | 0 |
| base B0 0.90 | 0 | 0 | 73 | 241 | 3.6 | 5/0/0 | 1,894 → 1,971 (1.04) | 8 |
| base B0 1.00 | 1 | 0 | 95 | 489 | 7.6 | 5/4/5 | 1,864 → 1,980 (1.06) | 10 |
| base B1 0.80 | 0 | 0 | 192 | 81 | 1.6 | 5/0/0 | 1,770 → 1,888 (1.07) | 0 |
| base B1 0.90 | 0 | **5** | 272 | 298 | 4.6 | 5/0/0 | 1,800 → 1,914 (1.06) | 9 |
| base B1 1.00 | 1 | **5** | 439 | 580 (485 vehicles unfinished at the cap) | 9.1 | 5/5/5 | 1,802 → 1,921 (1.06) | 11 |
| laneend B0 0.90 | 0 | 0 | 0 | 38 | 1.8 | 2/0/0 of 3 | **2,310** → 2,124 | 0 |
| gap3k B0 0.90 | 0 | 0 | 73 | 244 | 3.6 | 3/0/1 of 3 | 1,864 → 1,970 | 6 |

The full table is in `summary.json`, and the charts are in this folder:
- `loss_vs_level.png`: delay vs inflow level;
- `st_*.png`: space-time speed diagrams.

## 2. Findings
1. **The jam forms where intended.**
   - The first and only active bottleneck is the lane drop at the end of Z3. The queue starts between λ ≈ 0.75 and 0.80; the desk estimate was 0.61–0.76, so SUMO's lanes carry about 1,900 veh/h each.
   - The queue reaches Z2 and merge 2 only at λ ≥ 0.95. **Z1 never sees congestion.** Merges 1 and 2 never become active bottlenecks below λ = 1.0.
2. **No capacity drop.** The flow leaving the queue (1,860–1,980 veh/h/lane) is **equal to or higher than** the flow just before the queue (ratio 0.92–1.08, median ≈ 1.05). Field studies report drops of a few to about 20 % [VERIFY; protocol §4.4 band 0.82–0.97]. This is the known SUMO weakness, and protocol P0-G1 predicted it. **Consequence:** with no capacity drop, keeping traffic flowing cannot raise throughput, so delay gains from harmonisation are capped. The ≥ 10 % bar then becomes unlikely (the early-KILL path).
3. **Stop-and-go waves exist.** From λ ≈ 0.85, 8–11 oscillations per run pass 1.5 km upstream of the drop, with minimum speeds around 20 km/h. They travel upstream, as in reality. The wave-speed estimate is too coarse with 1-min data (−5 to −45 km/h) and needs a better method.
4. **CAVs on default ACC make things worse (B1 vs B0).** At λ ≥ 0.85:
   - about 20–25 % more delay;
   - 3–4× more emergency-braking warnings;
   - **4–5 collisions per 5 runs**, against none for humans.
   
   Two causes:
   - the ACC defaults, which protocol §2.6 already expects to fail;
   - V43: CAVs drive at 100 km/h while 44.7 % of the same drivers in B0 drive 100–120 km/h.
   
   So B1 starts behind B0. "≥ 5 % better than B1" is easier, and "≥ 10 % better than B0" is harder.
5. **Energy looks plausible, and it rises little with congestion.** Medians over full trips:
   - petrol 6.2 → 6.7 L/100 km (λ 0.55 → 0.9);
   - diesel 6.8 → 7.3 L/100 km;
   - PHEV fuel mode 6.5 → 6.9 L/100 km;
   - BEV 14.8 → 15.1 kWh/100 km;
   - PHEV electric mode 19–21 kWh/100 km.
   
   **Flag:** HBEFA4 diesel uses *more* litres than petrol, the opposite of typical real-world figures [VERIFY: fleet mix inside the HBEFA4 class?]. **Car energy rises only about 7 % from light to heavy traffic**, so the energy upside of smoothing is small here. The HBEFA4 truck values (200–300 g/km) are not used (V34).
6. **Data integrity.**
   - Every vehicle is inserted below λ = 1.0, with insertion delays ≤ 10 s.
   - Teleports appear only at λ = 1.0 (1 per arm group).
   - Unfinished vehicles appear only at λ = 1.0 in B1 (drain cap), as the protocol's desk drain estimate predicted.
   - Loop flows are consistent with the inflow.
7. **Layout variants.**
   - **Plain lane end:** drivers leave lane 0 about 1.5 km early, and the 2-lane section then carries an unrealistic **2,300 veh/h/lane** with almost no queue. Rejected.
   - **3 km spacing:** the same bottleneck and delays as 5 km; the queue reaches merge 2 and Z2 earlier (at λ = 0.9).

## 3. Options to give a smart controller a fair chance (for the author; nothing decided)
| # | Problem | Option | Trade-off |
|---|---|---|---|
| O1 | No capacity drop (finding 2), the decisive issue | Before P0, adopt a **pre-registered driver-model variant** taken from published SUMO calibrations that reproduce a capacity drop (lane-change friction at merges, reaction or action-step settings), chosen from literature, **not tuned on our data** (protocol principle 10, §9.2) | Needs a literature search for SUMO capacity-drop calibrations [VERIFY], then a protocol addendum. Without it, P0-G1 is likely to FAIL |
| O2 | Zones Z1 and Z2 never see a jam (finding 1) | (a) Keep them, and use Z1/Z2 only for early harmonisation far upstream: probably little effect. (b) **Move the zones onto the drop's approach** (e.g. 1-km zones at 3, 6 and 9 km upstream of the drop), where the queue and the waves actually live. (c) Raise the on-ramp volumes so each merge becomes a real bottleneck: three interacting bottlenecks, a richer but harder task | (b) best fits "act before the jam forms" and coordination along the queue; (c) changes the inflow (B13) |
| O3 | B1 is worse than humans (finding 4) | Protocol ACC ladder A0–A3 (already approved, V60). Re-decide whether CAVs should keep the desired speed of the driver they replace (V43 / A13 (iii)), so automation itself does not add delay | A disclosed plant choice; it changes the B1 − B0 gap |
| O4 | Small energy upside (finding 5) | Keep energy in the generalised cost, but expect the gain to come mainly from delay and waves; report scenario totals (V24) | No change needed; set expectations |

## 4. Extension: higher inflows (V73), plus CAVs keeping the driver's speed (B1s, report-only)
27 more runs on non-project seeds:
- B0 at λ = 1.1–1.5 × 3 seeds;
- B1s (CAVs keep the desired speed of the driver they replace) at λ = 0.8/0.9/1.0/1.2 × 3 seeds.

The capacity drop is now measured at **each** bottleneck. An "active" minute needs ≥ 1 congested loop in [x_b − 750, x_b) **and** a downstream speed ≥ 70 km/h (the protocol's active-bottleneck rule). The ratio is the discharge in the first 60 active minutes divided by the maximum 15-min flow before activation.

| Arm · λ | Vehicles unfinished at the cap | Max insertion wait (s) | Time lost per vehicle (s) | Queue max (km) | Merge 1 active (min) | Merge 2 active (min) | Lane drop: discharge (veh/h/lane) |
|---|---|---|---|---|---|---|---|
| B0 1.0 | 18 | 9 | 489 | 7.6 | 0 | 1 | 1,922 |
| B0 1.1 | 2,168 | 129 | 832 | 12.6 | 1 | 6 | 1,917 |
| B0 1.2 | 5,106 | 917 | 1,179 | 14.9 (the whole road) | 3 | 4 | 1,922 |
| B0 1.3 | 8,583 | 1,946 | 1,514 | 14.9 | 8 | 3 | 1,946 |
| B0 1.5 | 10,246 | 3,358 | 2,125 | 14.9 | 10 (ratio 1.01) | 3 | 1,946 |
| B1 0.9 / 1.0 | 0 / 485 | 9 / 10 | 298 / 580 | 4.6 / 9.1 | 0 | 0–1 | 1,878 |
| B1s 0.9 / 1.0 | 0 / 318 | 18 / 20 | 302 / 586 | 4.6 / 9.1 | 0 | 0–3 | 1,880 |

**Findings:**
1. **No capacity drop appears at any inflow.** The lane drop discharges a nearly constant **≈ 1,920 veh/h/lane** (B0) whatever the inflow, from λ = 0.8 to 1.5. The flow before activation is never higher.
2. **The merges never become independent bottlenecks.** Above λ ≈ 1.1 the drop's queue swallows them. Merge 1 shows short independent activity only at λ ≥ 1.4, with no drop there either (ratio 0.98–1.01).
3. **Above λ ≈ 1.05 the road just fills up.** The queue reaches the network entry, and thousands of vehicles wait to enter or are still on the road at the cap (`st_base_B0_l1.30_s1.png`). These levels carry no information about control: **the useful range is λ ≈ 0.75–1.0.**
4. **CAVs on plain ACC lower the drop's discharge by about 2–3 %** (1,878 vs 1,922 veh/h/lane), consistent with longer ACC time gaps.
5. **CAVs keeping the driver's speed (B1s) do not remove the B1 delay penalty** (302 vs 298 s at λ = 0.9). The penalty comes from the ACC behaviour, not from obeying the limit. This supports V72 (b): obeying the limit costs little.
6. **Consequence for V70 (O1):** inflow cannot create a capacity drop in this plant. It must come from the driver model (published settings, prompt X04), or the plant will FAIL P0-G1.

The space-time chart of the 130 % run still shows the V68 zone positions; V71 has since moved the zones to 8–9, 11–12 and 14–15 km.
