# Learned anticipation of daily/weekly demand patterns for freeway control (RM, VSL, corridor)

Scope: ramp metering (RM), variable speed limits (VSL), coordinated freeway control. Traffic signals are out of scope. Date of search: 2026-10-04.

Read-status convention:
- **[READ: full text]**: PDF downloaded and the relevant sections (setup, comparators, results) read.
- **[VERIFY: abstract only]** or **[VERIFY: snippet only]**: only the abstract or a search-engine snippet was seen.
- **[SAGE]**: published by SAGE (TRR); the author cannot access these.

All percentages are copied from the sources unless marked "(my computation)". Every "gain" names its comparator. Where a source does not say whether the demand was known, or whether a comparator was tuned, this note says so.

---

## Q1. Which RL ramp-metering / VSL papers use time-of-day, demand-history or day-type inputs, or train on a library of daily demand profiles? Do they test on held-out days?

### Takeaway
In the RL freeway-control papers I could read in full, no policy takes an explicit time-of-day, day-type or demand-forecast feature as input. Demand variability is handled in two ways:
- randomising a single nominal peak profile (Gaussian noise, or randomly generated two-peak shapes) during training;
- at most, a stress test on scaled demand (60–150 %).

None evaluates on genuinely held-out *real* days. Train and test demand come from the same generator, or from the same nominal profile.

### Cited Findings

**Belletti et al. (2017/2018), multi-task DRL RM, BeATS simulator, I-80 Bay Bridge, 29 on-ramps.** [READ: full text, arXiv version]
- The state per cell is normalised density, an off-ramp flag and the on-ramp queue. There is no time-of-day or demand-history input.
- The scenario is one 4-h simulation (12:00–16:00) with one demand curve peaking at 15:00–16:00 ("Fig. 14 total demand curve").
- I found no description of held-out demand days.
- Comparator: ALINEA "using with model and parameters the exact same values used in the simulator".
- Aggregated scores over the congested period (veh·h, lower is better): ALINEA 10514, MWR (their method) 10575, NoMWR 10617, NoRM 11085. So the best RL is about 0.6 % *worse* than ALINEA (my computation). The authors put it as "MWR reproduces 96% of Alinea performance improvement" over no metering.
- No run count or dispersion is reported for Table I.
- Source: [arXiv 1701.08832](https://arxiv.org/pdf/1701.08832)

**Hua and Ma (2023), demonstration-guided DRL for coordinated RM plus perimeter control.** [READ: relevant sections, arXiv v1]
- Observations are local cell or region counts and flows plus "historical information h_t" (POMDP). I did not see time-of-day or day-type features.
- Demand randomisation: "given a demand profile, the actual traffic demand follows a normal distribution where the mean is the given demand for each OD pair, and the standard deviation is 30% of the demand mean".
- Robustness test: the policy trained on the normal profile is applied "directly in different demand profiles without extra training" at 60 %–150 % of normal volume. This is a scaled version of the same OD pattern, not held-out real days.
- Training: 5 seeds per model.
- Comparators: ALINEA and Gating, each grid-search tuned *individually*, not jointly. The authors say a joint search is "unrealistic".
- Small network: the proposed DRL "can outperform the teachers (i.e., demonstrators) by 46.1% in TTT", and TTT is −31.3 % vs no control.
- Hong Kong network: −7.8 % TTT vs no control, and "Compared to demonstrators (ALINEA and Gating), the proposed DRL method can reduce the TTT further by 12.9%".
- Source: [arXiv 2303.03395](https://arxiv.org/pdf/2303.03395)

**Airaldi, De Schutter and Dabiri (2023), MPC-based RL (Q-learning tunes a parametrised METANET-MPC).** [READ: relevant sections, arXiv]
- Demand: "two-peak profiles are generated randomly" at the start of each training episode; each episode lasts 4 h.
- The authors state that "a performance drop is anticipated were the controller to face a new unforeseen scenario, e.g., with a different number of peaks".
- There is no separate held-out test set. The reported curves are per learning episode (online learning, 80 episodes), averaged over 15 seeds, with 95 % CIs shown only for the proposed method.
- Source: [arXiv 2311.08820](https://arxiv.org/pdf/2311.08820)

**Liu et al. (2020), DQN RM from video frames (SUMO-type micro setup, Shanghai).** [READ: evaluation section]
- The input is video frames; there are no time or demand-history features.
- Training: 10^6 frames.
- Evaluation: 20 simulation experiments "initialized with different random seeds". I found no description of whether the demand profile differs between training and test.
- Source: [arXiv 2012.12104](https://arxiv.org/pdf/2012.12104)

**Ke, Li, Cao and Liu (2020/2021, IEEE T-ITS), DDQN VSL with transfer learning.** [VERIFY: abstract only]
- Tested with "a stable testing demand and a fluctuating testing demand", across target scenarios (overspeed, adverse weather, capacity drop).
- Reported TTS −26.02 % to −67.37 % (stable) and −21.31 % to −69.98 % (fluctuating). From the abstract I believe the comparator is no control, but this is unconfirmed.
- No day-type or time features are mentioned.
- Source: [OpenAlex record, doi:10.1109/TITS.2020.2990598](https://api.openalex.org/works/doi:10.1109%2FTITS.2020.2990598)

**Zheng, Li, Li and Ke (2024, IET ITS), DRL with curriculum learning for RM at uncertain bottlenecks.** [VERIFY: abstract only]
- Varies the bottleneck location and number, not the demand day.
- Training time is −45.1 % to −64.5 % vs DRL from scratch.
- Source: [OpenAlex search, doi:10.1049/itr2.12494](https://doi.org/10.1049/itr2.12494)

**Yu et al. (2024, Sustainability), "TRLCRM", an RL coordinated RM with two-stage training "to adapt to varying mixed-autonomy demand scenarios".** [VERIFY: abstract only]
- Compared with HERO and COE-HERO; the abstract gives no numbers.
- Source: [doi:10.3390/su162210055](https://doi.org/10.3390/su162210055)

**Zhou, Ozbay, Kachroo and Zuo (2020, J. Adv. Transp.), Q-learning RM for a distant downstream bottleneck.** [VERIFY: abstract only]
- The authors say anticipation of flow evolution is learned into a policy that is "in pure feedback form in that only the current state of the environment is needed". This is presented as an alternative to "incorporating predictors of traffic flow evolution".
- Source: [doi:10.1155/2020/8813467](https://doi.org/10.1155/2020/8813467)

**Day-to-day learning without RL: iterative learning control (ILC) that uses the previous day's data explicitly.**
- Xiang, Cenedese, Balta and Lygeros (2024, arXiv) [READ: via fetch summary of the HTML full text, not line-by-line]:
  - motivation: "traffic flows follow recurring patterns over days and weeks";
  - control on day d uses day d−1 data over the same time window, in receding-horizon form;
  - the experiments assume *identical* daily upstream demand (07:00–10:00) and 5 iterations (days);
  - comparators are uncontrolled and ground-truth MPC, with no ALINEA;
  - for 0.8× parameter underestimation: GT-MPC TTT 344.64 vs uncontrolled 358.49, and ILC converges to near GT-MPC "within one or two iterations".
  - Source: [arXiv 2411.11108](https://arxiv.org/html/2411.11108)
- Chi, Li, Hou, Liu and Yu (2014), QLIF-ILC for RM [VERIFY: abstract only]:
  - a feedforward part learned from previous trials plus current feedback;
  - simulation only, with no comparator stated in the abstract.
  - Source: [doi:10.1155/2014/321934](https://doi.org/10.1155/2014/321934)

**Search-engine summaries mentioned other studies that I could not attribute to any source:**
- a PPO agent trained on multiple weekday profiles and tested on weekend profiles;
- a set-up with "5 working days ... Gaussian distribution" for morning peaks.

Because I could not attribute them, I report them only as gaps, not as findings.

### Inferences
- The "library of daily profiles" design is mostly *noise around one nominal profile*. This tests robustness to amplitude noise, not to day-type structure (peak timing, shape, weekday vs weekend). With this design, a policy cannot learn day-type-conditional anticipation, because there is no day-type latent to learn.
- Among the papers read, the explicit use of day-to-day repetition is found in ILC, not in DRL. ILC needs repetitive days. The cited work assumes identical days, which is the most favourable case.
- A recurrent or history-conditioned DRL policy (Hua and Ma's h_t; DRQN as a baseline there) could in principle infer the demand phase. None of the papers read isolates the value of that history, for example with an ablation without h_t.

### Gaps
- I did not retrieve full texts for Fares and Gomaa (RL RM), Wang et al. (RL RM), or Han et al. (2022, TR-C) RL-VSL ("A new reinforcement learning-based variable speed limit control approach to improve traffic efficiency against freeway jam waves", doi:10.1016/j.trc.2022.103900, [VERIFY: title/metadata only]). Their state features and test protocols are unverified.
- Han, Wang, Li, Roncoli, Gao and Liu (2022, TR-C 137, 103584), physics-informed RL RM [VERIFY: snippet only]:
  - per a search summary of the abstract, trained on "historic data and synthetic data generated from a traffic flow model", and "outperforms classical feedback-based ramp metering strategies";
  - not read, so it is unknown whether historic *days* were held out or whether ALINEA/PI-ALINEA were tuned.
  - Link: [TU Dresden record](https://fis.tu-dresden.de/portal/en/publications/a-physicsinformed-reinforcement-learningbased-strategy-for-local-and-coordinated-ramp-metering(1a9d3d38-a026-4bfe-8257-a38fe3f4ec7f).html)
- I found no RL ramp-metering or VSL paper that (i) feeds explicit time-of-day or day-type features and (ii) tests on held-out real days with a tuned feedback comparator. This is a negative search result from about 30 queries and fetches, not proof of absence.
- No meta-RL or context-conditioned RL for freeway RM or VSL turned up in my searches.

---

## Q2. What did MPC with demand prediction gain over feedback control, and how sensitive is it to forecast error?

### Takeaway
Classical METANET-MPC and AMOC papers report large gains over ALINEA (about 3× ALINEA's gain on one E17 ramp, and about 23 % lower TTS than queue-constrained ALINEA on the Amsterdam ring). They mostly use:
- the same model for prediction and simulation;
- exact or "fairly good" demand predictions;
- one deterministic run, with no dispersion.

The one quantified forecast-error study I found (AMOC) shows that imperfect demand prediction gives up about 16–29 % of TTS relative to the perfect-information optimum. Even so, the hierarchical MPC remains well ahead of a non-tuned, queue-constrained ALINEA.

### Cited Findings

**Hegyi, De Schutter and Hellendoorn (2005), MPC for coordinated RM plus VSL, METANET.** [READ: full text, tech-report version]
- The authors state: "we have assumed that the real world coincides with the model used by the controller to make predictions, and that the disturbances (demands) are exactly known."
- TTS: RM-only MPC 1382.6 veh·h (−5.3 % vs no control); coordinated VSL+RM MPC 1251.0 veh·h (−14.3 % vs no control).
- No ALINEA or feedback comparator in this result. One deterministic demand scenario.
- Source: [TU Delft report 03-016](https://www.bartdeschutter.org/publications/03-016-model-predictive-control-optimal/03-016-model-predictive-control-optimal.pdf), published as *Transportation Research Part C*, 13(3), pp. 185–209, doi:10.1016/j.trc.2004.08.001

**Bellemans, De Schutter and De Moor (2006), MPC vs ALINEA RM on the E17 Ghent–Antwerp (METANET, real-data-based morning peak, 5-h simulation).** [READ: full text, tech-report version]
- No control: 2960 veh·h.
- Table 2 (with queue constraints; ALINEA uses a 100-veh queue override):

  | Controller | TTS (veh·h) | Change vs no control |
  |---|---|---|
  | ALINEA ramp 5 | 2931 | −0.9 % |
  | ALINEA ramp 6 | 2953 | −0.2 % |
  | ALINEA ramps 5 & 6 | 2922 | −1.3 % |
  | MPC ramp 5 | 2843 | −4.0 % |
  | MPC ramp 6 | 2856 | −3.5 % |
  | MPC ramps 5 & 6 | 2757 | −6.9 % |

- **Tuning caveat (important):**
  - The ALINEA in Table 2 uses K_R = 0.001, chosen as a "good trade-off" between TTS and metering-rate oscillation, *not* the TTS-best gain.
  - The authors' own gain sweep (Table 1, ramp 5) gives TTS 2854 at K_R = 0.1 and 2856 at K_R = 0.05.
  - Against the TTS-best ALINEA (2854), MPC on ramp 5 (2843) is only about **0.4 %** better (my computation from their tables), versus the headline "more than three times the gain achieved by ALINEA".
- MPC tuning: "not very sensitive to the length of the prediction horizon"; Np = 10 min, Nc = 5 min.
- I did not find an explicit statement of whether MPC received the true future demand. The prediction and simulation models are both METANET.
- Single deterministic run, no dispersion.
- Source: [TU Delft report 02-022](https://www.dcsc.tudelft.nl/~bdeschutter/pub/rep/02_022.pdf), published as *Control Engineering Practice*, 14(7), pp. 757–767, doi:10.1016/j.conengprac.2005.03.010

**Kotsialos and Papageorgiou (2005, ACC) and Kotsialos and Papageorgiou (2004, TRISTAN V): hierarchical AMOC plus ALINEA, Amsterdam ring road.** [READ: full text of both]
- Model and assumptions:
  - METANET is both the plant and the AMOC model, "no mismatch between the model parameters";
  - no incidents;
  - on-ramp demand from "a fairly good predictor" (an example in Fig. 8);
  - turning rates set to historical means, while METANET uses the real time-varying rates.
- TTS:

  | Strategy | TTS (veh·h) | vs no control |
  |---|---|---|
  | No control (TRISTAN) | 14,168 | |
  | ALINEA without queue constraints | | −44 % |
  | ALINEA with queue constraints | 10,478 | −26 % |
  | Open-loop optimal with **perfect** future disturbances (upper bound) | 6,974 | −50.8 % |
  | Rolling horizon with predicted demand, AMOC applied directly | 8,267 | −41.6 % |
  | Rolling horizon with predicted demand, AMOC + ALINEA at the direct-control layer | 8,086 | −42.9 % |

  The two rolling-horizon rows are 18.5 % and 15.9 % worse than the perfect-information optimum.
- TRISTAN Table 1 (1-h optimisation horizon), application horizon 30 / 20 / 10 min:
  - with local feedback: 8,472 / 8,317 / 8,211, which is 21.5 / 19.3 / 17.7 % above optimal;
  - direct application: 8,928 / 8,987 / 8,534, which is 28.0 / 28.7 / 22.4 % above optimal.
- The two papers give slightly different numbers for the 10-min case (8,086 vs 8,211). I cannot resolve this; they may be different runs or versions.
- Against queue-constrained ALINEA (10,478), hierarchical MPC (8,086) is −22.8 % TTS (my computation).
- ALINEA's set-point was the critical density; I saw no gain tuning. Single deterministic run.
- Sources: [ACC 2005 paper](https://skoge.folk.ntnu.no/prost/proceedings/acc05/PDFs/Papers/0403_ThA17_4.pdf); [TRISTAN V abstract](https://tristanconference.org/system/tristan-v/website/pdf/abstract_00035.pdf)
- Journal version: Papamichail, Kotsialos, Margonis and Papageorgiou, "Coordinated ramp metering for freeway networks – A model-predictive hierarchical control approach", *Transportation Research Part C* (OpenAlex lists 2008 online; commonly cited as 2010, 18(3)), doi:10.1016/j.trc.2008.11.002. [VERIFY: not read; volume and year not confirmed]

**Liu, Sadowska, Frejo, Núñez, Camacho, Hellendoorn and De Schutter (2016), scenario-based min-max receding-horizon parameterised control (RHPC), multi-class METANET, with demand uncertainty.** [VERIFY: abstract only]
- Compared against nominal RHPC and against "standard control" (state feedback "such as PI-ALINEA") with and without uncertainty handling, plus a queue override.
- Finding: nominal RHPC and standard control ignoring uncertainties "may lead to high queue length constraint violations"; including uncertainties in standard control reduces violations, "but the performance improvements are minor"; scenario-based RHPC "performs best".
- No numbers in the abstract.
- Source: [De Schutter pub 15-045](https://www.dcsc.tudelft.nl/~bdeschutter/pub/abs/15_045.html), *Int. J. Robust and Nonlinear Control*, 26(6), pp. 1211–1245

**Gu, Wu, Wu and Wiwatanapataphee (2022, Transportmetrica B), distributionally robust RM on CTM with only partial distributional demand information (WCVaR, SDP).** [VERIFY: abstract only]
- "can achieve reliable performances over a range of uncertain scenarios". No feedback comparator is stated in the abstract.
- Source: [doi:10.1080/21680566.2022.2025952](https://doi.org/10.1080/21680566.2022.2025952)

**Airaldi et al. (2023): MPC with a 30 % wrong model.** [READ: relevant sections]
- All controllers share the same 30 % parameter errors: ρ̃_crit = 0.7 ρ_crit and ã = 1.3 a.
- The untuned non-learning MPC "is stuck at the initial poor performance ... with high TTS and constraint violations".
- PI-ALINEA, with queue management and gains "fine-tuned to this specific task via Bayesian Optimisation", "is able to curb violations, but at the expense of a much higher control variability ... and higher TTS" than MPC-RL.
- The RL-tuned MPC's own TTS fell "from around 1100 to 700 veh h (or a 35% reduction)" during learning. That is a gain over *its own untuned start*, not over PI-ALINEA.
- I did not extract a numeric final TTS for PI-ALINEA.
- Source: [arXiv 2311.08820](https://arxiv.org/pdf/2311.08820)

### Inferences
- The MPC-over-ALINEA gains in the classical literature are upper-bound-like:
  - they share a plant/model, have exact or near-exact demand, and use one scenario;
  - the feedback comparator is often not tuned for the headline metric (Bellemans) or is hobbled by queue constraints (AMOC).
- When the comparator is put on its best TTS gain, at least one reported 3× advantage shrinks to under 1 % (Bellemans, single ramp).
- Forecast quality matters a lot in absolute terms. In the AMOC case, the loss from imperfect prediction (≈ 1,100–2,000 veh·h above the 6,974 optimum) is comparable in size to the remaining MPC-vs-ALINEA gap (≈ 2,400 veh·h). Shorter re-optimisation intervals ("feedback!") recover part of the loss.

### Gaps
- No study I read gives MPC a forecast fitted on separate days with *realistic* error statistics, for example a historical-average predictor evaluated on held-out days. AMOC's "fairly good predictor" is illustrated by one figure, with no error metric.
- No dispersion (multiple days or seeds) for any classical MPC-vs-ALINEA comparison read.
- Hegyi (2005) assumes exact demand. I found no follow-up quantifying VSL-MPC under forecast error, although Liu et al. (2016) and Shuai Liu's thesis (2016, [DANS](https://doi.org/10.4233/uuid:2d1d6e46-f90d-4d73-8021-aa6b6437c46d)) may contain it. [VERIFY: abstract only]

---

## Q3. Is there evidence that anticipation (acting before the peak) matters for RM/VSL, for example pre-emptive metering to delay breakdown? Is it quantified?

### Takeaway
The best quantified evidence is the perfect-information vs predicted-demand gap in AMOC (≈ 16–29 % higher TTS without perfect foresight). The evidence that anticipation is not needed is equally strong: a purely reactive coordinated feedback strategy (HERO) is reported to reach the efficiency of proactive optimal control. Learned anticipation can also be folded into a pure-feedback policy (Zhou et al. 2020). I found no ablation that isolates "acting before the peak" from coordination or from model knowledge.

### Cited Findings
- **Mechanism (stated, not measured in that paper).** Hegyi et al. (2005) note that any flow-improving control gains at most about the capacity-drop margin ("approximately 5–10 %"), but cite Papageorgiou et al. (1998) that "an increase of outflow of 5 % may result in an decrease of the total time spent in the network of 20 %". The secondary citation is [VERIFY: Papageorgiou et al. 1998 not read]. — [Hegyi et al. 2003/2005 report](https://www.bartdeschutter.org/publications/03-016-model-predictive-control-optimal/03-016-model-predictive-control-optimal.pdf)
- **Same paper.** In RM-only MPC, "performance breaks down"; coordinated VSL activates and holds density near 40 veh/km/lane, which "enables a higher outflow". This illustrates VSL acting at breakdown onset; it is not an anticipation ablation. — [same](https://www.bartdeschutter.org/publications/03-016-model-predictive-control-optimal/03-016-model-predictive-control-optimal.pdf)
- **Value of foresight (AMOC).** Perfect-foresight open-loop optimum 6,974 veh·h vs rolling-horizon MPC with predicted demand 8,086–8,987 veh·h, depending on the application horizon and on direct vs local-feedback implementation. — [ACC 2005](https://skoge.folk.ntnu.no/prost/proceedings/acc05/PDFs/Papers/0403_ThA17_4.pdf); [TRISTAN V](https://tristanconference.org/system/tristan-v/website/pdf/abstract_00035.pdf)
- **Reactive coordination reaches proactive optimal (HERO).** Papamichail and Papageorgiou (2008, IEEE T-ITS 9, pp. 111–121): HERO is "utterly reactive ... without any need for real-time model calculations or external disturbance prediction", and "the new strategy is shown to reach the efficiency of sophisticated proactive optimal control schemes". The scenario is a hypothetical freeway with two on-ramps. [VERIFY: abstract only] — [OpenAlex, doi:10.1109/tits.2007.908724](https://doi.org/10.1109/tits.2007.908724)
- **HERO field evidence, Monash Freeway, before/after vs the previous metering system.** AM peak +4.7 % average flow and +24.5 % average speed; PM peak +8.4 % flow and +58.6 % speed. This is a field before/after, not a randomised or paired comparison. [VERIFY: secondary summary in IEEE CSS "Impact of Control Technology"; primary source Papamichail et al. 2010 TRB Annual Meeting paper, not read] — [IEEE CSS IoCT Part 2](https://IEEECSS.org/sites/ieeecss/files/2019-07/IoCT-Part2-21RampMetering-LR.pdf)
- **Bellemans et al. (2006).** MPC was "not very sensitive to the length of the prediction horizon" (10 min chosen, about one congested traversal time). Coordination between the two MPC ramps "was found not to enhance the performance" because both hit queue limits at about the same time. Longer look-ahead added little in that case. — [TU Delft report 02-022](https://www.dcsc.tudelft.nl/~bdeschutter/pub/rep/02_022.pdf)
- **Learned anticipation in feedback form.** Zhou et al. (2020): the Q-learning RM handles the time-delay effect of a distant bottleneck "in pure feedback form", as an alternative to explicit predictors. [VERIFY: abstract only] — [doi:10.1155/2020/8813467](https://doi.org/10.1155/2020/8813467)
- **Learned "anticipation" in Belletti et al. (2017).** RL "manage[s] to implicitly deduce this optimal speed during training" (Fig. 9 caption). Performance stayed slightly below exact-parameter ALINEA. — [arXiv 1701.08832](https://arxiv.org/pdf/1701.08832)
- **Recent hybrid MPC + MARL residual (VSL + RM).** Ma, Sun, Yang and Yao (2026, arXiv 2609.35152): the upper MPC layer (lane-level METANET) does "long-horizon rolling optimization" and the lower MAPPO layer gives "residual actions for short-horizon adjustment". The abstract I saw was truncated, with no effect sizes. [VERIFY: abstract only, truncated] — [doi:10.48550/arxiv.2609.35152](https://doi.org/10.48550/arxiv.2609.35152)

### Inferences
- "Anticipation" in the freeway literature is mostly confounded with (a) network coordination and (b) exact model knowledge.
- Where a strong reactive coordinated controller (HERO) is used, reported gaps to proactive optimal control are small. This matches the v5/v6 prior of 0–6 % hybrid headroom over tuned controllers recorded in this repo's CLAUDE.md.
- The main way anticipation pays off in these papers is acting at breakdown onset; the reported value of looking further ahead before the peak appears to be small.

### Gaps
- I found no study that ablates "pre-emptive metering before the peak" (for example the same controller with and without a demand-forecast feed-forward, or a time-shifted activation) and reports the delay difference with dispersion. There is one partial example: FF-ALINEA is mentioned in Airaldi et al. as a variant, but I saw no effect size.
- The HERO-vs-optimal claim is abstract-level only. The underlying numbers and scenario count are not verified.

---

## Q4. What fraction of gains survives against tuned feedback controllers?

### Takeaway
Where the comparator is a *tuned* ALINEA or PI-ALINEA and results are paired over seeds, learning-based gains are small and inconsistent (median about 3 % in the one paired table available), or negative (Belletti: RL about 0.6 % worse than exact-parameter ALINEA). Large headline gains (30–70 %) are almost always relative to no control, or to untuned, individually tuned or queue-hobbled feedback.

### Cited Findings

**Liu et al. (2020), DQN RM vs PI-ALINEA "fine-tuned to minimize mean travel times", 20 paired seeds.** [READ: evaluation section and Table 3]
- Paper headline: DRL −13 % mean travel time vs no control on average.
- PI-ALINEA was worse than no control in some runs (+10 %, +22 %, +8 % in runs 6, 9, 17).
- From Table 3 (my computation, per-seed paired relative difference DRL vs PI-ALINEA):
  - median −2.9 %, mean −3.6 %, range −21.0 % to +5.3 %;
  - DRL is worse than PI-ALINEA in 4 of 20 runs.
- Medians vs no control (my computation): PI-ALINEA −9.6 %, DRL −12.4 %.
- Most of the DRL advantage comes from a few runs where PI-ALINEA failed (runs 6, 9, 17), which suggests its PI-ALINEA tuning is not robust across seeds.
- Source: [arXiv 2012.12104](https://arxiv.org/pdf/2012.12104)

**Belletti et al. (2017).** Best RL 10575 vs ALINEA 10514 veh·h: RL **0.6 % worse** (ALINEA uses exact simulator parameters). Single aggregated number, no dispersion. — [arXiv 1701.08832](https://arxiv.org/pdf/1701.08832)

**Hua and Ma (2023).** DRL beats ALINEA+Gating by 46.1 % (small network) and 12.9 % (Hong Kong). Caveats:
- the demonstrators were tuned individually per actuator, not jointly;
- in the Hong Kong case DRL is only −7.8 % vs no control yet −12.9 % vs ALINEA+Gating. This implies that the tuned demonstrators were *worse than no control* there (my inference from the two numbers; not stated explicitly in the text I read).
- Source: [arXiv 2303.03395](https://arxiv.org/pdf/2303.03395)

**Airaldi et al. (2023).** PI-ALINEA was BO-tuned. MPC-RL achieves lower TTS and variability; numbers were shown only graphically (not extracted). The 35 % figure is relative to the untuned MPC start. — [arXiv 2311.08820](https://arxiv.org/pdf/2311.08820)

**Bellemans et al. (2006).** MPC gain over ALINEA shrinks from "more than three times" (vs a smoothness-tuned K_R) to about 0.4 % TTS (vs the TTS-best K_R from the authors' own sweep, ramp 5 only, my computation). — [TU Delft report 02-022](https://www.dcsc.tudelft.nl/~bdeschutter/pub/rep/02_022.pdf)

**AMOC hierarchical vs ALINEA.** −22.8 % TTS vs queue-constrained, set-point-only ALINEA (my computation). This requires a matched model and good demand prediction; one run. — [ACC 2005](https://skoge.folk.ntnu.no/prost/proceedings/acc05/PDFs/Papers/0403_ThA17_4.pdf)

**Liu et al. (2016).** Adding uncertainty handling to standard feedback gives "minor" performance gains; scenario-RHPC "performs best". No numbers. [VERIFY: abstract only] — [pub 15-045](https://www.dcsc.tudelft.nl/~bdeschutter/pub/abs/15_045.html)

**HERO (reactive) is reported to reach proactive optimal-control efficiency.** [VERIFY: abstract only] — [doi:10.1109/tits.2007.908724](https://doi.org/10.1109/tits.2007.908724)

### Inferences
- Of the learning-based RM papers read in full, none uses held-out real days, pre-registered metrics or a jointly tuned coordinated feedback baseline (HERO) together.
- On the evidence available, the gains that survive a *tuned* feedback comparator are about 0–4 % (median), with wide per-seed dispersion (−21 % to +5 %). This is consistent with the 1.5–6 % hybrid prior in this repo's CLAUDE.md. It is my synthesis from 2–3 papers, not a meta-analytic estimate.
- Implication for the thesis protocol (inference): a defensible test of "learned anticipation of daily patterns" needs the following. These match roadmap §0/§9 rules already in this repo.
  - held-out *days* (not just seeds) drawn from a day-type library;
  - a tuned ALINEA/PI-ALINEA, and HERO where coordination exists;
  - an MPC whose demand forecast is fitted on separate days (not the true future);
  - an ablation removing time-of-day/day-type inputs.

### Gaps
- I found no paper reporting learning-based RM/VSL vs HERO with paired multi-day statistics.
- The field evidence (HERO, Monash) is before/after vs the previous system, not vs a tuned alternative, and comes from a secondary summary.
- Not retrieved: Fares and Gomaa; Wang et al. RL RM; Han et al. 2022 (both TR-C); Kotsialos et al. 2002 AMOC (TRR, [SAGE]); Papamichail et al. 2010 HERO Monash (TRB paper; TRR version would be [SAGE]); Frejo and Camacho global vs local MPC.

### Source key (Harvard; read status)

**Read (full text or relevant sections):**
- Airaldi, F., De Schutter, B. and Dabiri, A. (2023) 'Reinforcement Learning with Model Predictive Control for Highway Ramp Metering', arXiv:2311.08820. [READ: relevant sections] https://arxiv.org/abs/2311.08820
- Belletti, F., Haziza, D., Gomes, G. and Bayen, A.M. (2017) 'Expert Level control of Ramp Metering based on Multi-task Deep Reinforcement Learning', arXiv:1701.08832. Also published in IEEE T-ITS (2018) [VERIFY: journal volume/pages not checked]. [READ: arXiv full text] https://arxiv.org/abs/1701.08832
- Bellemans, T., De Schutter, B. and De Moor, B. (2006) 'Model predictive control for ramp metering of motorway traffic: A case study', *Control Engineering Practice*, 14(7), pp. 757–767. doi:10.1016/j.conengprac.2005.03.010. [READ: tech report version]
- Hegyi, A., De Schutter, B. and Hellendoorn, H. (2005) 'Model predictive control for optimal coordination of ramp metering and variable speed limits', *Transportation Research Part C*, 13(3), pp. 185–209. doi:10.1016/j.trc.2004.08.001. [READ: tech report version]
- Hua, Z. and Ma, W. (2023) 'Demonstration-guided Deep Reinforcement Learning for Coordinated Ramp Metering and Perimeter Control in Large Scale Networks', arXiv:2303.03395. [READ: relevant sections; journal version not checked]
- Kotsialos, A. and Papageorgiou, M. (2004) 'Hierarchical Nonlinear Model-Predictive Ramp Metering Control for Freeway Networks', TRISTAN V, Le Gosier, Guadeloupe. [READ: extended abstract]
- Kotsialos, A. and Papageorgiou, M. (2005) 'A Hierarchical Ramp Metering Control Scheme for Freeway Networks', Proc. American Control Conference, Portland, OR, ThA17.4. [READ]
- Liu, B., Tang, Y., Ji, Y., Shen, Y. and Du, Y. (2020) 'A Deep Reinforcement Learning Approach for Ramp Metering Based on Traffic Video Data', arXiv:2012.12104. [READ: evaluation; journal version, if any, not checked]
- Xiang, H., Cenedese, C., Balta, E.C. and Lygeros, J. (2024) 'Iterative Learning Control for Ramp Metering on Service Station On-ramps', arXiv:2411.11108. [READ: via fetch summary]

**Abstract only:**
- Chi, R. et al. (2014) *Math. Probl. Eng.*, doi:10.1155/2014/321934.
- Gu, C. et al. (2022) *Transportmetrica B*, doi:10.1080/21680566.2022.2025952.
- Ke, Z., Li, Z., Cao, Z. and Liu, P. (2020/2021) *IEEE T-ITS*, doi:10.1109/TITS.2020.2990598.
- Liu, S. et al. (2016) *IJRNC* 26(6), pp. 1211–1245.
- Ma, G. et al. (2026) arXiv:2609.35152 (truncated).
- Papamichail, I. and Papageorgiou, M. (2008) *IEEE T-ITS* 9, pp. 111–121, doi:10.1109/tits.2007.908724.
- Yu, H. et al. (2024) *Sustainability*, doi:10.3390/su162210055.
- Zheng, S. et al. (2024) *IET ITS*, doi:10.1049/itr2.12494.
- Zhou, Y. et al. (2020) *J. Adv. Transp.*, doi:10.1155/2020/8813467.

**Metadata or snippet only:**
- Han, Y. et al. (2022) TR-C 137, 103584 (RL RM), doi:10.1016/j.trc.2022.103584.
- Han, Y. et al. (2022) TR-C (RL VSL), doi:10.1016/j.trc.2022.103900.
- Papamichail, I. et al. (TR-C, AMOC hierarchical), doi:10.1016/j.trc.2008.11.002.
