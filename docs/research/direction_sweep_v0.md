# Narrowing the PhD: three focused directions

*2026-10-15. Research only: no runs, no repository changes.*

## Short answer

- **Only two of the ten candidates survived** the adversarial review, and both only in narrowed form:
  - **A**: how much stop-and-go smoothing one car can capture in real time (C1);
  - **B**: an empirical cut-in hazard (C3).
- **No third candidate survived.** The best fallback is **C**, friction-brake demand (C8, narrowed). It failed as proposed, but its narrow core can be defended.
- **None of the three needs DRL.** All three share one small testbed: a recorded real leader, one controlled car, and a 1-D replay on your laptop. There is no SUMO, no network and no demand model.
- **I recommend A.** If A's first test KILLs it, switch to B, which reuses the same code.
- If you accept this narrowing, the 33 open protocol-v2 items (A36–A68) can be archived unanswered.

**Limits.**
- The web-search budget ran out during the review. The prior-art check is incomplete for all three options.
- In 11 months, expect both papers *submitted*, not both accepted. Check whether your doctoral school requires accepted papers [VERIFY].

```
         ONE SHARED TESTBED (no SUMO, no DRL, laptop CPU)
  recorded leader --> 1 controlled car --> (optional) model followers
        ____________________|______________________
       |                    |                      |
 [A] capture ratio   [B] cut-in hazard     [C] brake demand (fallback)
 judges 22/30        20/30                 20/30
 review: survives    survives (provisional) failed as proposed
 decisions: 5        5                     4
 main KILL: own      gap effect vanishes   result flips with
 radar is enough     after controls        filter/powertrain
 title fit: strong   fair                  fair
```

## Option A: how much smoothing can one car capture in real time? (C1, narrowed)

**Pitch.** Ji et al. (2026) computed an offline benchmark: the best smooth trajectory through real I-24 waves, found by an optimisation (a QP) that knows the future. No real car can drive it. You measure what share of it a real-time controller captures:
- with its own radar only;
- with the roadside radar (RDS) the road already has.

Then you test one simple planner that uses RDS.

**Research question.** On public I-24 data (lane 1, 33 weekday mornings), what share of the benchmark does one real-time car capture with its own radar, and what share with real RDS data? Report it by gap cap (0.02 and 0.1 mile) and by how severe the waves are that day.

**Why now.**
- **Ji et al. (arXiv, v2 Aug 2026)** give only the offline bound:
  - car CO2 falls by about 9.8–14.1 % at a 0.1-mile gap cap;
  - CO2 falls by about 6–11 % at 0.02 mile;
  - lanes 1–2 show lower values;
  - they name a model predictive control (MPC) version as a possible next step.
- **WaveX (Zenodo, CC BY 4.0)** pairs the speed field with real RDS radar on the same days.
- **The 100-car CIRCLES test** used INRIX data, which its authors call "somewhat opaque". So the value of each information source was never isolated.

**Method. DRL is not needed.**
- **Replay.** Recorded vehicle n−1 leads, and your controller replaces vehicle n. The baseline is vehicle n's own recorded trajectory.
- **Constraints.** The same as Ji et al.: the car never passes its recorded position and never exceeds the maximum gap.
- **Primary metric.** The capture ratio on the QP's own cost, which is at most 1.
  - Co-primary: RMS acceleration.
  - CO2 and NOx are secondary rows only.
- **Arms.** All are tuned on tuning days only:
  - FollowerStopper;
  - PI with saturation;
  - a linear MPC with a constant-speed forecast;
  - the same MPC, fed by RDS.
- **Perfect preview** is a pipeline check only, never a result.
- **Days replace seeds.** For example: 5 calibration, 10 tuning, 6 validation and 12 test days. The bootstrap resamples whole days.

**Data.**
- **WaveX:** 885.6 MB, no account needed. A reviewer read the file list: only lane 1 plus RDS, for 33 dates, is public.
- **Optional cross-check:** I-24 INCEPTION. It is free under a data-use agreement that allows academic use with citation.

**Impact.**
- Road operators deciding whether to publish low-latency detector data.
- Car makers deciding whether stock ACC radar is enough for smoothing.

**Two papers.**
- **P1:** the capture-ratio map (information source × gap cap × severity). It is publishable whatever the sign.
- **P2:** a planner fed by RDS, with parameters taken from a lookup table indexed by the estimated wave severity. It is compared with the best tuned radar-only controller.

**Plan.**

| Month | Work |
|---|---|
| Nov | Read Coifman & Liu and Nice et al.; make the decisions; run the 2-week test |
| Dec–Feb | Pre-register and run P1 |
| Mar | Submit P1 and post a preprint |
| Apr–Jun | P2 |
| Jul | Submit P2 |
| Aug–Sep | Thesis |

**First test** (≤ 2 weeks, on 5 throw-away days). You fix the thresholds before seeing any data:
- **KILL-A:** the reproduced benchmark misses Ji et al.'s leftmost-lane values by more than a preset tolerance.
- **KILL-B:** RDS-informed capture minus radar-only capture is < 5 points (median paired), or its CI includes 0, at both gap caps.
- **KILL-C:** perfect preview captures < 80 % of the QP cost. That would mean a bug in the pipeline.

**Decisions (5).**
1. The primary metric.
2. The gap caps.
3. The day split, which replaces the seed block.
4. The controller set and the RDS latency.
5. The claim rule that replaces D5.8.

**Carries over.**
- Your paired bootstrap, pre-registration, operating maps, tuned baselines and KILL habits.
- The `literature_v0.md` sections on controllers and energy models.
- Your experience with MnDOT detector data.

**Risks and honest prior.**
- **Information value may be near zero.** Own radar may already be nearly enough. Lichtlé et al. found about 3 points of value from downstream information, and your v6 work found ≤ 5.7 %.
- **Scoop risk.** The I-24 group owns the data and ran field experiments in Fall 2025.
- **Closest prior work.** Coifman & Liu (TR-C 183) present a real-time controller that uses downstream information. I confirmed only its metadata [VERIFY the content first].
- **Narrow data.** One lane at one site.
- **Prior.** P1: high. P2's positive claim: low to medium.

## Option B: the cost of gaps, an empirical cut-in hazard (C3, narrowed)

**Pitch.**
- Smoothing controllers and string-stable ACC both keep larger gaps. The standard objection is "people will cut in".
- Ji et al. capped their gap for exactly this reason, but did not model it.
- You measure, on open data from three countries, how the cut-in rate grows with the follower's gap.
- Then you find the gap at which smoothing stops paying.

**Research question.** How does the rate of cut-ins into a follower's gap (per follower-hour) depend on the space gap and on the time gap within speed bands? The analysis controls for the speed difference to the adjacent lane, and for lane and site. A second question: does the result transfer between the US, Italy and Germany?

**Why now.**
- **Ji et al. 2026:** the gap needed to dissipate waves is "often impractically large". Large gaps invite cut-ins and tailgating, which were seen in field tests, but the paper does not model them.
- **Lichtlé et al. 2023:** they fitted a gap-dependent cut-in probability on unpublished data. A published hazard across datasets, based on exposure and with CIs, is still missing.
- **Alhuraish et al. 2026 (Waymo data):** humans accept shorter gaps when they cut in front of AVs: a median of 7.58 m against 9.57 m. The study is descriptive only.

**Method. DRL is not needed.**
- **P1:**
  - fit a piecewise-exponential (Poisson) hazard on follower-seconds;
  - measure the gap a fixed time Δ before the lateral move starts;
  - flag courtesy yields;
  - fit on US data, then predict Italy and Germany;
  - report only inside the observed range of gaps.
- **P2:**
  - inject the hazard, plus cut-outs and tailgating, into A's replay;
  - the primary result is the break-even gap, with its CI;
  - "an adaptive gap beats the best fixed gap" is reported only, never claimed.

**Data.**
- **Open now:**
  - NGSIM (CC BY-SA 3.0);
  - MiTra (CC BY 4.0), but only about 15–30 minutes of it is congested;
  - TGSIM I-294 (public).
- **highD and exiD:** free for non-commercial use after a manually reviewed application. Redistribution is not allowed. Apply on day 1.

**Impact.**
- Car makers choosing default ACC time gaps.
- Simulator developers who need a cut-in model.
- The smoothing research community.
- For UN R171 (para 5.3.7.2.5.2, recovery after a cut-in), it is relevant evidence, not a value a regulator would adopt.

**Two papers.**
- **P1:** a cut-in hazard based on exposure, using data from three countries.
- **P2:** the break-even gap for gap-opening smoothing and for ACC.

**Plan.**

| Month | Work |
|---|---|
| Nov | Apply for highD/exiD; read Nice et al. and Wang et al. 2019; run the pilot |
| Dec–Feb | Pre-register P1, fit the model, test transfer |
| Mar | Submit P1 |
| Apr–Jul | P2 |
| Aug–Sep | Thesis |

**First test** (≤ 2 weeks, on NGSIM plus the congested MiTra flights):
- **KILL:** after the controls, the rate ratio between the wide-gap and narrow-gap bins has a 95 % CI lower bound ≤ 1.2.
- **Sanity check:** at least 150 congested cut-ins.

**Decisions (5).**
1. The cut-in definition and Δ.
2. The gap measure and bins.
3. The datasets.
4. The model form.
5. The claim rule, with the break-even gap as primary.

**Carries over.**
- Statistics, your strongest skill.
- A's replay code.
- Real-data context for the SUMO lane-change problems seen in v5.B.1.

**Risks and honest prior.**
- **Gaps are not random.** Followers open gaps to let others in and close them to block cutters. Controls reduce this bias but cannot remove it.
- **Crowded field.** Gap acceptance is well studied.
- **Little data on ACC followers.** TGSIM has only 3 ACC cars over 10 runs.
- **Title fit.** P1 is not an algorithm, so the fit with the title rests on P2.
- **Prior.** P1: medium-high. P2's adaptive claim: low.

## Option C (fallback): friction-brake demand (C8, narrowed)

**Why it is only a fallback.** It failed the review as proposed, for three reasons:
- Hu et al. (TR-D 2026) already link ACC to brake-wear particles.
- JRC (2016) built the lab brake cycle from real braking data by road type.
- The particle model of Liu et al. (2025) is valid only in a narrow range.

It works best as an extra paper inside A.

**Research question.** Behind the same congested real leaders, at an equal mean gap and a fixed maximum gap, how much friction-brake energy per km does an anticipatory controller save against an identified commercial ACC? Report it by congestion level and by powertrain: combustion, or battery-electric with regenerative braking.

**Why now.**
- **Euro 7**, which adds brake-particle limits, applies to new types from 29 Nov 2026 and to all new cars from 29 Nov 2027.
- **The brake test is a lab test** (UN R179). So the impact is on real-world emission inventories, not on type approval.
- **Ji et al.** call particles "a particularly valuable addition" to their benchmark.

**Method. DRL is not needed.**
- A pre-registered vehicle model that splits braking into friction, coasting and regeneration.
- Particle estimates only inside the particle model's valid range.
- **Arms:** a standard human car-following model (IDM), an identified commercial ACC, an explicit smoothing law and a short MPC.
- Three pre-registered filters. The result must hold under all three.

**Data.** I-24 INCEPTION (free account), TGSIM and OpenACC (both open).

**Two papers.**
- **P1:** congested braking compared with the lab cycle.
- **P2:** brake energy against the maximum gap.

**Plan.** P1 Nov–Mar, P2 Apr–Jul, thesis Aug–Sep.

**First test** (≤ 2 weeks). KILL if either of these happens:
- the saving against the identified ACC is < 10 % under the gap cap;
- the conclusion flips across filters or powertrains.

**Decisions (4).**
1. The brake model.
2. The filters and gap rules.
3. The controllers.
4. The claim rule.

**Carries over.**
- The energy and hard-braking metrics (V10, V11, V25).
- Your statistics habits.
- A's code.

**Risks and prior.**
- Reviewers may say "smoother driving obviously brakes less".
- The eco-ACC literature has not been checked.
- The I-24 group may add particles to their benchmark first.
- **Prior.** The effect is likely real. Novelty is the weak point.

## Comparison

| | A | B | C |
|---|---|---|---|
| Judges (examiner/supervisor/impact) | 8/8/6 = 22 | 7/6/7 = 20 | 6/7/7 = 20 |
| Review | survives | survives (provisional) | failed as proposed |
| Decisions | 5 | 5 | 4 |
| Data | open, no account | open; highD/exiD by application | free account or open |
| DRL | no | no | no |
| Kill risk | medium | P1 low–medium; P2 medium | effect low; novelty medium |
| Title fit | strong | fair | fair |

## What dropping DRL means

**D5.8 cannot be met as written.** It requires a *learning-based* controller to:
- beat no control by ≥ 10 %;
- beat the best tuned proven controller in ≥ 1 pre-registered regime.

None of A, B or C has a learner.

**What must change:**
- "learning-based controller" becomes "the proposed adaptive algorithm";
- drop the "≥ 10 % vs no control" bar and its early-KILL rule. In A, even the oracle saves only about 6–11 % CO2 at 0.02 mile;
- delay stops being the primary metric, because smoothing does not remove queueing delay;
- the rules on the fair DRL arm and the DRL budget lapse.

**What stays:**
- "beats the best tuned baseline in ≥ 1 pre-registered regime (Bonferroni CI excluding 0)";
- "never > 5 % worse";
- "full operating map";
- paired statistics.

**Also revisit** the 2026-10-05 decision that only positive DRL results count. P1 in A and in B is a measurement, so it is useful whatever the sign.

This is your decision. Record it as a V-decision.

**Title fit.** "Adaptive driving algorithms for intelligent road traffic systems" does not require DRL.
- A fits both halves: an adaptive vehicle planner, plus roadside detectors.
- B fits through P2's gap policy.
- C fits through the controller, but it leans toward emissions.

## Rejected and why

- **C2 (follower robustness):** failed review.
  - Its adaptive arm is already published (Wang Q. et al. 2022; Li D. et al. 2024).
  - IDM cannot reproduce the oscillation growth measured in platoons (Jiang et al. 2014).
  - It needs about 10 decisions.

  It is the runner-up fallback.
- **C5 (R171 string-stability test):** failed review. El-Baklish et al. 2025 pre-empt its P2, and its validity design is circular.
- **C6 (cut-in anticipation):** overlaps Mattas et al. 2022 and needs a highD licence.
- **C9 (detector headroom atlas):** a measurement, not an algorithm.
- **C4 (humans behind AVs):** the TU Delft group owns this framing (Jiao et al. 2024), and the freeway sample is small.
- **C10 (jam absorption):** the highest risk of ending with nothing.
- **C7 (adaptive safety filter):** shrinking safety margins conflicts with worst-case safety logic.
- **Dropped at merge:**
  - SUMO safety realism: it brings back the SUMO plant;
  - stand-alone safe Bayesian optimisation: small expected gain;
  - LLM controllers: proof-of-concept only;
  - game-theoretic lane change: needs a multi-lane plant;
  - ISA study: no usage data exist;
  - field-scale DRL: needs large teams.

## Your next decision

1. Choose A (recommended), B or C.
2. Approve replacing D5.8.
3. Answer that option's ≤ 5 decisions.

I will then record them as V-decisions and draft the 2-week test protocol. Writing a protocol is an Extra High phase, with ultracode on for its review.

## Sources

Checked by a reviewer (exists = true) unless marked [VERIFY].

- Ji et al. 2026, *Emission reduction potential of freeway stop-and-go wave smoothing*: https://arxiv.org/abs/2603.21476
- Ji et al. 2025, *WaveX* dataset (CC BY 4.0): https://zenodo.org/records/17122740
- Lee et al., *Traffic Control via Connected and Automated Vehicles: An Open-Road Field Experiment with 100 CAVs*: https://arxiv.org/abs/2402.17043
- Lichtlé et al. 2023, *Traffic Smoothing Controllers for Autonomous Vehicles Using Deep Reinforcement Learning and Real-World Trajectory Data*: https://arxiv.org/abs/2401.09666
- Coifman & Liu, *Using connected and automated vehicles to attenuate disturbances in freeway traffic*, TR-C 183:105497 (online Dec 2025). Metadata only; content [VERIFY]: https://api.openalex.org/works/doi:10.1016/j.trc.2025.105497
- Stern et al. 2018, *Dissipation of stop-and-go waves via control of autonomous vehicles*: https://arxiv.org/abs/1705.01693
- I-24 MOTION documentation and Data Use Agreement: https://github.com/I24-MOTION/I24M_documentation
- I-24 MOTION data page. One reviewer confirmed it; the others hit a certificate error: https://i24motion.org/data
- Alhuraish, Wang & Zhou 2026, *Cut-In Gap Acceptance Toward Autonomous vs. Human-Driven Vehicles*: https://arxiv.org/abs/2605.01485
- Chaudhari, Treiber & Okhrin 2025, *MiTra*: https://pmc.ncbi.nlm.nih.gov/articles/PMC12241643/
- NGSIM: https://catalog.data.gov/dataset/next-generation-simulation-ngsim-vehicle-trajectories-and-supporting-data
- TGSIM I-294 L1: https://catalog.data.gov/dataset/third-generation-simulation-data-tgsim-i-294-l1-trajectories
- highD: https://levelxdata.com/highd-dataset/
- exiD: https://levelxdata.com/exid-dataset/
- UN R171 01 series, EU OJ L 2025/1899: https://www.boe.es/doue/2025/1899/L00001-00089.pdf
- Hu et al. 2026, *Driving behavior shapes PHEV brake energy and brake wear particle emissions*, TR-D 150:105087: https://trid.trb.org/View/2625635
- Grigoratos, Martini & Steven 2016, JRC103870: https://publications.jrc.ec.europa.eu/repository/bitstream/JRC103870/tech_report_typical%20driving%20conditions.pdf
- Liu et al. 2025, TR-D 149:105027: https://eprints.whiterose.ac.uk/id/eprint/232991
- Euro 7 summary (EUR-Lex): https://eur-lex.europa.eu/EN/legal-content/summary/vehicle-emissions-and-battery-durability-euro-7-technical-requirements-and-certification-rules.html
- C(2026) 3144 (Council ST 10638/26): https://data.consilium.europa.eu/doc/document/ST-10638-2026-INIT/en/pdf
- Makridis et al. 2021, *openACC*: https://arxiv.org/abs/2004.06342
- El-Baklish, Kouvelas & Makridis 2025: https://arxiv.org/abs/2402.14110
- Wang Q. et al. 2022: https://arxiv.org/abs/2210.02147
- Li D. et al. 2024: https://arxiv.org/abs/2306.01387
- Jiang et al. 2014, PLoS ONE: https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0094351
- Mattas et al. 2022: https://pmc.ncbi.nlm.nih.gov/articles/PMC9378973/
- Jiao et al. 2024, TR-C 164:104673: https://research.tudelft.nl/en/publications/beyond-behavioural-change-investigating-alternative-explanations-/
- [VERIFY] Nice et al., *A middle way to traffic enlightenment*, ICCPS 2024. Cited by Ji et al.; not fetched.
- [VERIFY content] Wang, Yang & Hurwitz 2019, *Analysis of cut-in behavior based on naturalistic driving data*, AAP 124:127–137. Metadata only.
## Main-session check (2026-10-15, after the workflow)

Fetched myself; overrides the text above where they differ.

- **Ji et al., arXiv 2603.21476: confirmed.** v1 23 Mar 2026, v2 30 Aug 2026.
  - 9.80–14.08 % CO2 across lanes at the 0.1-mile cap (abstract).
  - 6–11 % at 0.02 mile (body text).
  - "Offline evaluation"; it says the pipeline "can be recast as a model predictive control problem".
  - **Correction:** the paper uses **40 weekdays, lanes 1–4**, and **virtual trajectories reconstructed from mean speed fields, not raw vehicle tracks**. Option A's "replay vehicle n−1" therefore means replaying virtual trajectories; say so in any protocol.
- **WaveX, Zenodo 17122740: confirmed.**
  - CC BY 4.0, 885.6 MB, one `raw.zip` with MOTION and RDS folders.
  - Collected 17 May – 17 Jul 2024.
  - "Lane 1 only, 33 dates" is **not stated on the landing page** [VERIFY by opening the zip].
  - The page says the RDS lane data "needs further processing".
- **Coifman & Liu, TR-C 183:105497 (13 Dec 2025): the closest prior work, and closer than the text above suggests.**
  - The journal abstract is not available. The related Ohio State reports are on ROSAP (Phase 1, dot:77501, Jul 2024, plus Phases 2 and 3).
  - The method: a single CAV uses the instantaneous states of downstream vehicles to forecast its leader's trajectory. On empirical trajectories it "can rapidly nullify stop and slow waves" with "large reduction in vehicle emissions".
  - Phase 2 extends it to a platoon of 15 CAVs; Phase 3 to multiple platoons.
  - **Consequence for A:** a "planner fed by downstream information" (A's P2) is largely done. What remains for A is the measurement against the offline oracle, by information source: own radar, roadside RDS, downstream CAVs.
  - **Read the full Coifman & Liu reports before choosing A.**
- **Alhuraish, Wang & Zhou, arXiv 2605.01485 (2 May 2026): confirmed.**
  - Waymo Open Motion Dataset, 706 HDV→AV and 3,172 HDV→HDV cut-ins.
  - Median accepted gap 7.58 m vs 9.57 m.
- **Not checked by me:** all other numbers and sources above, including the "≈ 3 points" attributed to Lichtlé et al., and the dataset licences for highD, exiD, MiTra and TGSIM.
