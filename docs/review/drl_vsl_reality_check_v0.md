# DRL for VSL: a reality check of the literature (v0, 2026-10-04)

*Scope: the 39 RL/DRL VSL papers read from full text in `docs/plans/vsl_hybrid_screen_v0.md` §3.2 (#1–#39), re-checked against the PDFs. Per-paper profiles, with page references and machine-verified quotes, are in `drl_vsl_red_flags_per_paper_v0.md`. The supervisor note is `supervisor_note_drl_vsl_v0.md`. Nothing here touched v6 or the running v5 lab tracks. From v6 I read only `docs/handoff/paths_tested.md` and `lessons_learned.md`, as you asked.*

## 0. Bottom line

1. **Not one of the 39 papers shows DRL beating a classical VSL controller that was tuned on scenarios separate from the test, with replicated runs and a dispersion measure.** This is not a claim that DRL cannot do it. It is a claim that this literature has not shown it.
2. **Where the comparator got real tuning effort, RL lost, tied, or won by about 0–2 %.** The cases are #1, #4, #10, #11 (VSL-only) and #28 (mobility). There are two exceptions with large gains:
   - #5, macroscopic, runs selected by a coverage criterion: 7–12 % vs a mismatched MPC;
   - #39, a PhD thesis on a custom simulator with single runs: 6–54 % vs an in-sample grid-searched P-controller, and 6–29 % on a held-out demand.

   Your own pre-registered numbers fall in the same band: v5 R6 gives −2.5 % vs a fitted MPC and −4.3 % vs a tuned event scheduler. Five v6 gates found < 10 % headroom.
3. **The optimistic bias is systematic, not occasional (category (a)):**
   - weak or untuned comparators;
   - asymmetric actuation;
   - evaluation on the training scenario;
   - single or selected runs, with no dispersion;
   - proxy headline metrics;
   - abstracts that overstate their own tables.

   These recur across venues, groups and years.
4. **The numerical inconsistencies found are best explained as honest errors (category (b)).** The headline case, #7's "50.47 %", **is reproducible from the paper's own Table IV.** The text quotes the wrong row's absolute values. One error, #34's, *understates* RL's gain.
5. **No evidence of misconduct (category (c)).** Four numbers cannot be derived from what is printed. Each has plausible innocent explanations, and none is impossible. That calls for questions to the authors, not allegations.

## 1. Frank assessment

### 1.1 Evidence base and its limits

**What the evidence is:**
- 39 papers, each re-read on 2026-10-04 against one brief with fixed flag codes (profiles §0).
- 354 verbatim quotes, all found on the cited PDF page by script.
- 10 values read from rendered images [VERIFY].
- I re-did three audits by hand: #7, #24 and #34.

**Limits:**
- **The corpus is a convenience sample, not a systematic search.** It is the PDFs you collected, plus 3 web-only papers that are not audited. It may over-represent visible, highly cited or Chinese-journal work. It may also under-represent negative results, which tend not to be published.
- So the counts below describe *this sample*. A publishable review needs a documented search (PRISMA-style) first (§4).
- Counts marked "≈" come from the reader agents' flag profiles. Several flags are marked "uncertain" there. Treat those counts as ±2.
- **Read in full, with figures and tables:** most papers. #16's text layer is garbled (read from images), and #33's appendices are missing from the PDF.

### 1.2 What the comparators were

| Strongest non-RL comparator | Papers | n |
|---|---|---|
| None: no control, a fixed limit, or other RL only | #2, 7, 8, 13, 14, 15, 24, 25, 26, 27, 31, 32, 33, 35, 38 | **15** |
| In-sample open-loop oracle only | #1 | 1 |
| Classical controller with a **documented** tuning procedure | #4 (GA, the authors' own rule), #11 (search over set-points and gains), #39 (grid search, one sentence) | 3 |
| Tuning effort claimed, **method not stated** | #3 ("calibrated to optimize"), #5 (SPECIALIST "trial-and-error"; MPC weights not printed), #10 ("tuned empirically"), #28 ("carefully searched") | 4 |
| Parameters **copied, hand-set, or not stated** | #6, 9, 12, 16, 17, 18, 19, 20, 21, 22, 23, 29, 30, 34, 36, 37 | 16 |

**None of the 23 papers with a classical comparator tuned it on scenarios or seeds separate from the test.** Where tuning is documented (#4, #11, #39), it was done on the test scenario. This is in-sample for both arms, which flatters neither side in principle. In practice, though, RL usually also got hyperparameter or checkpoint selection on the same data (E2 in ≈ 15 papers).

### 1.3 (a) Systematic optimistic bias: what the evidence shows

**1. The comparison set is the main mechanism.**
- 15 of 39 have no classical controller at all.
- Of the 23 that have one, 16 do not tune it, or do not say how they did.
- Some comparators are visibly non-binding:
  - #17's SPSC equals no control (Table II, p. 6);
  - #29's MTFC is worse than no control on travel time (Table 1, p. 6);
  - #37's rule VSL is worse than no control at low flow;
  - #6's FB is worse than no control around 0.3 h (p. 11).

  A gain over a controller that does nothing useful is a gain over no control under another name.

**2. Asymmetric comparisons (B4, ≈ 19 papers).** RL gets actuators or information the comparator lacks:
- #34: per-lane limits vs one limit for FB. The authors attribute part of the gain to this (p. 11).
- #11: two control sites vs one.
- #10: AV-actuated per-lane speeds vs a ramp signal.
- #6, #3, #9: RL observes demand that the comparator does not.

The cleanest internal control is in #18. The like-for-like 2-action DDPG **loses** to SPSC (207 vs 186; 590 vs 579 veh·h, Table 2, p. 13). Only the richer-action variants win.

**3. Evaluation on the training scenario (E1, ≈ 28 papers, some marked "cannot be excluded").**
- Held-out demand appears in only a few papers: #24 (30 of 130 scenarios), #39 (one new demand pattern), #36 (an off-training grid), #7 (testing demands, but the training demand is not stated).
- #23's headline is read off the training-episode curves (Fig. 11, p. 11).
- #5's scoring runs *are* the learning runs, by design.

**4. Thin statistics (S1/S2/S3).**
- No dispersion or test for the headline gain in ≈ 31 papers.
- A single, "representative" or best run in ≈ 20 papers.
- Explicit selection:
  - #18 reports the "last 10 best" runs and excludes terminated runs;
  - #5's 35.1 % holds only for runs with η > 0.8;
  - #17 shows the "most representative run";
  - #36 uses "one of the trained Q-networks";
  - #39's evaluated checkpoint is not stated, although training collapsed between 12,000 and 14,000 episodes (p. 51).
- "Significant(ly)" is used without a reported test in at least #3, #5, #6, #11, #13, #14, #15, #19, #20, #30, #32 and #34.

**5. Metric choice (M1 ≈ 32, M2 ≈ 19).**
- Origin and insertion queues are excluded or unstated almost everywhere. Throughput is rarely reported next to delay.
- Several headlines are proxies (speed, density, surrogate safety). Mobility is worse or absent in some:
  - #27: delay +5.0 / +6.5 % vs no control (Table II, p. 7);
  - #28: queue longer than no control in all three scenarios (Table 3, p. 15);
  - #25: the abstract claims travel-time and throughput gains, but neither metric is reported.

  This is the same gameability you documented in `docs/lessons_metric_gameability.md`.

**6. Abstracts overstate their own tables (C1, ≈ 30 papers).**
- **#9.** The abstract says the hybrid "outperforms" the other controllers. Table V shows it is 0.5–4.9 % *worse* than the best MPC variant in all 6 scenarios. It beats only its own standalone MPC and a DRL baseline that did not converge.
- **#37.** The abstract's "over 28.30 %" and "over 7.21 %" are gains vs no control, presented as gains vs other methods.
- **#36.** The abstract says "up to 30 %"; the proposed method peaks at 27.2 % (Table 2, p. 11).
- **#38.** The abstract calls an RL baseline "traditional".
- **#28.** The abstract says it "enhances traffic mobility by 58.6 %". That figure is max queue length vs Speed-Matching, best case.

**7. Publication bias and incentives. This is inference, not measured.**
- Only 5 of 39 report RL losing or tying on their own primary comparison (#1, #4, #10, #27, #28). All 5 report it openly, which is to their credit.
- A published sample cannot show what was not published. Still, a field where the method almost always "outperforms" while tuned comparators are almost never used is what selective reporting plus weak baselines would produce.
- I have no direct evidence about individual incentives and make no claim about any author.

**8. Gain partly built into the plant (P1, 7 macroscopic papers).** In CTM/METANET the capacity drop is an equation switch that VSL can switch off.
- #6's gain vs no control doubles with the drop parameter: 14.3 % at a 5 % drop vs 27.9 % at 15 % (c., Table 4, p. 16).
- #7's VSL TTS sits at ≈ 502–505 veh·h whatever the drop size (Tables II and IV).

  Microsimulation papers rarely show that a capacity drop exists in their setup (P2, ≈ 25). The exceptions are #10 (Fig. 6) and #39 (Fig. 15).

**Plain statement.** The large DRL-VSL gains in this sample come from comparisons that would not survive the protocol you now use: tuned baselines on separate seeds, paired replications with CIs, a door-to-door metric, and the same actuators for both arms. That is consistent with the 1,000+ hours you report not reproducing them. It does not show that any particular paper's result is false. It shows that most results are not informative about the question your thesis asks.

### 1.4 What happens when the comparator is taken seriously

| # | Setting | Comparator (tuning) | RL vs comparator |
|---|---|---|---|
| 1 | METANET | in-sample time-varying open-loop oracle | RL **worse**, +0.10 / +2.56 / +0.39 % (c., Table 3) |
| 4 | stochastic CTM | GA-optimised rule (the authors' own, same scenario) | RL **worse**, +5.1 % on its own crash-risk objective; TT +1.5 % |
| 10 | SUMO, Flow | feedback ramp meter, "tuned empirically" | "matches" above critical inflow; below it, RL ≈ 15–25 % lower outflow (fig., visual) |
| 11 | AnyLogic, calibrated | MTFC, PI-ALINEA, integrated FB (searched, same scenario) | VSL-only: 1.2–1.6 % relative. RM + VSL with 2 sites vs 1: 9.7 % vs integrated FB, 7.6 % vs PI-ALINEA |
| 28 | TransModeler | deployed Speed-Matching, "carefully searched" | safety: tie; mobility: queue longer than NC |
| 5 | METANET + mismatched CTM-MPC | SPECIALIST (trial and error), MPC (weights not printed) | 12.4 % vs MPC only for runs with η > 0.8; 7.3 % over all of training (c.) |
| 39 | custom micro, uncalibrated | P-feedback, grid search (undocumented, in-sample) | 21 / 54 / 7 % on the training demand; **22 / 29 / 6 % on held-out demand**; single runs |
| *v5 R6* | *SUMO BN4, your protocol* | *tuned event scheduler; MPC with model fitted on separate seeds* | ***−4.3 % [CI −14.7, −4.9 s]; −2.5 % [−14.9, −0.8 s]; 210 reserved seeds*** |

**Two exceptions remain, and both need replication before anyone leans on them:**
- **#39:** single runs, undocumented tuning, a custom simulator, not peer-reviewed;
- **#5:** macroscopic, with run selection.

### 1.5 (b) Honest errors: inconsistencies with the most likely explanation

| # | Inconsistency | Most likely explanation | Direction |
|---|---|---|---|
| **7** | Text (p. 7): NC 1020 → DDQN 812 veh·h, "a 50.47 % reduction" (and 719 → 587, "35.53 %"). 812/587 gives 20.4 / 18.4 %. | **812.26 / 587.89 is Table IV's scenario-7 *no-control* row (p. 9; I checked the rendered table).** (1020.68 − 505.55)/1020.68 = 50.47 %, and 505.5 veh·h is where the VSL lands in every scenario where it removes the drop. So the percentages are probably right and the absolute values were mis-transcribed. 35.53 % is matched only approximately (35.55–35.62 %). | **Your screen's "printed values give 20.4 %" needs correcting**: it is true of the text, not of the result. |
| **34** | "Improved by 21.34 % / 16.75 % vs FB" (p. 12) | These are **percentage-point** differences of NC-normalised reductions: (608.79 − 448.14)/752.8 = 21.34 pp. Relative to FB the reduction is **26.4 % / 19.0 %** (c.). I re-did this from Fig. 12. | **Understates** RL's gain |
| 24 | Table 5: "−16.37 %" vs no control | Wrong denominator: (29.87 − 25.67)/25.67 = 16.36 %; relative to NC, the correct value is 14.06 % (I re-did this). Other rows are off the same way. | Overstates |
| 11 | NC component TTS values sum to 1920.01; the printed TTS is 1960.01 | A digit slip: the difference is exactly 40.00. The kNN-TD VSL column is off by 69.5, unexplained. | Unclear |
| 12 | Two sums off by exactly 1.00 and 2.00 (Tables II, III) | Typos | Negligible |
| 22 | 32.75 % printed vs 31.75 % (c.); 37.60 % vs 39.60 % (c.); the conclusion's 27.49 % vs 16.69 % in Sec. 5.2 | First two: digit slips. The third is unexplained, possibly a different metric. | Mixed |
| 20 | Table A1 vs Table 2 (770.6 vs 778.2); "17.22 %" attributed to the wrong reward and CAV share | Copy errors between tables | Small |
| 32 | The abstract swaps which number belongs to density and which to risk | Copy error | None |
| 16, 37, 38, 29 | Action set 22–34 vs 20–32 m/s (#16); replay memory 512 vs 215 (#37); GAE λ 0.99 vs 0.95 (#38); CO2 in "kg/s" (#29) | Typos or unit labels | Reproducibility only |

**Lesson for your own papers.** State the denominator, the normalisation (relative vs percentage points) and the run set for every percentage. Three of these errors (#7, #24, #34) are exactly that kind.

### 1.6 (c) Misconduct: how far the evidence goes

**Nothing found is impossible or fabricated-looking:**
- every percentage in #7's Tables II–IV reproduces from the same table (34 of 34);
- #34's numbers all reproduce under one consistent, if non-standard, definition;
- the errors run in both directions.

**What remains unexplained** (could only be resolved by the authors, data or code):
- #16: the abstract's 28 % / 18 % / 12 % cannot be derived from any printed table.
- #38: "40 %" is not derivable from the figures, and it is worded three different ways (p. 1, 9, 10).
- #22: "27.49 %" vs the 16.69 % in Sec. 5.2.
- #11: the kNN-TD VSL column is off by 69.5.
- #7: VSL-TL TTSs = 502.39 in both scenario 1 (overspeed) and scenario 7 (5 % drop), while the TTSf values differ. In a deterministic CTM where VSL keeps the bottleneck below critical density, an identical TTS is plausible.

None of these is evidence of misconduct. **The appropriate action, if any, is a polite query to the corresponding author.** Do not claim (c) in any document, and do not let a co-author or reviewer push the paper towards it. The (a) findings carry the argument on their own.

### 1.7 Corrections to the screen (`vsl_hybrid_screen_v0.md` §3.2)

| # | Screen says | Re-check says |
|---|---|---|
| 1 | RL loses +0.4…+2.6 % | +0.10…+2.56 % (Table 3). The "best fixed assignment" is a time-varying open-loop oracle, in-sample. |
| 6 | FB "params not re-tuned" | tuning **not stated**; parameters come from ref. [33] |
| 7 | claims 50.47 %; printed values give 20.4 % | 50.47 % reproduces from Table IV; the text's absolute values are from the wrong row (§1.5); comparator is NC only; drop 8.4 % (text) vs 8.1 % (Table I) |
| 10 | ≈ 0 | matches only above the critical inflow; below it, RL outflow is ≈ 15–25 % lower than the ramp meter (visual, Fig. 10) |
| 11 | train = test | not confirmed: the training protocol is not in the text. Comparators were searched on the same scenario (B3). |
| 12 | venue VERIFY | no publication info in the PDF. The header is a T-ITS template ("Manuscript received April 19, 2005" is IEEEtran stock text) and the references run to 2017. Treat it as an unpublished manuscript [VERIFY]. |
| 13 | train = test | not supported or refuted by the text |
| 21 | 0…−1.5 % | up to −2.08 % (STM-QL-VSL2, scenario 2); STM2 is worse than NC in scenario 4 |
| 24 | −16.4 % vs NC | printed value; the derivable value is −14.06 % (wrong denominator) |
| 29 | baselines untuned | tuning **not stated** |
| 30 | 2 runs | 2 test scenarios (weekday, weekend); replications not stated |
| 34 | −21.34 / −16.75 % vs FB | those are percentage points. Relative: **−26.4 / −19.0 %** vs FB, −17.8 / −12.5 % vs DDPG. |
| 39 | no seeds or CI | 50-run boxplots exist, but only for RL's MPR sensitivity, not for RL vs FB. Held-out demand: −22 / −29 / −6 %. The 64 % lane-drop headline is above the thesis's own 50-run median (≈ 55 %, Fig. 33). |

## 2. Per-paper red-flag profiles

Full profiles, with page, table and figure references and verbatim quotes, are in `drl_vsl_red_flags_per_paper_v0.md` (one section per paper). Below is a one-line index. Codes are defined there; "(c.)" means computed.

| # | Paper | Strongest comparator [tuning] | Gain vs it (c.) | Main flags |
|---|---|---|---|---|
| 1 | Walraven 2016 | in-sample oracle | RL worse, +0.1…+2.6 % | B1 E1 S3 C1 |
| 2 | Zhu & Ukkusuri 2014 | NC | ≈ −18 % TTT vs NC (Fig. 10) | B1 E1 S1 B4/P1 C1 |
| 3 | Li Z. 2017 | Carlson FB ["calibrated", method unstated] | −32.5 / −12.2 % TTT | B2 E2 P1 S2/S3 M1 |
| 4 | Li Z. 2021 | GA rule [tuned, same scenario] | RL worse, +5.1 % crash risk | E1 M2 B4 S2/S3 |
| 5 | Han, Hegyi 2022 | mismatched MPC; SPECIALIST [trial and error] | −12.4 % (runs with η > 0.8), −7.3 % (all) vs MPC | E1 B2 B4 S3 P1 |
| 6 | Zheng 2023 | local FB [literature params] | −10.9 / −11.7 % TTS | B2 B4 P1 S3 R1 |
| 7 | Ke 2021 | NC | −50.47 % vs NC (§1.5) | N1 B1 P1 S1–S3 R1 |
| 8 | Tabadkani Aval 2019 | NC | no scalar result | B1 E1 M2 S1/S3 R1 |
| 9 | Sun 2024 (hybrid) | MPC variants [hand-set] | +0.5…+4.9 % **worse** than best MPC | C1 B2 B4 E1 S3 P1 |
| 10 | Vinitsky 2018 | FB ramp meter ["tuned empirically"] | ≈ tie above critical inflow, worse below | B4 B2/B3 M1/M2 S1 |
| 11 | Schmidt-Dumont 2019 | MTFC, PI-ALINEA, integrated FB [searched, same scenario] | VSL-only −1.2…−1.6 %; RM + VSL −9.7 % | B3 B4 N1 S3 M1 P2 |
| 12 | Schmidt-Dumont (ms.) | ALINEA [not stated] | −2.7…−8.9 % (RM) | B2 B4 B1 E1 S3 P2 |
| 13 | Wang C. 2019 | NC | −29.9 % TTT vs NC | B1 S1–S3 M1/M2 P2 |
| 14 | Kušić 2020 | single-agent RL | −4.5 % local TTS; network ≈ NC | B1 B4 S1 M1/M2 |
| 15 | Wu 2020 | other RL | −2.9 / −5.7 % ATT | B1 S1–S3 C1 N1 |
| 16 | Chai 2021 | integrated FB [not stated] | −21.5 % TTT | B2 E1 S1 N1 R1 |
| 17 | Gregurić 2020 | SPSC [not stated; = NC] | speed +12.7 %, density −25 % | B2 S1 M2 E1 |
| 18 | Gregurić 2022 | SPSC [literature gain] | −9.1 % bottleneck TTS, −3.1 / −3.3 % network; like-for-like variant loses | E2 B2 B4 M1/M2 |
| 19 | Cheng 2022 (hybrid) | own law, best of 30 random λ | flow +7.3 / +14.5 % | B1/B2 E2 S1 M2 R1 |
| 20 | Vrbanić 2022a | HCM rule [not tuned] | −0.2…−4.6 % TTS | E2 S1–S3 N1 B2 |
| 21 | Vrbanić 2022b | HCM rule [not tuned] | −0.1…−2.1 % TTS | C1 S1–S3 E1 B2 |
| 22 | Xiao 2022 | queue rule [derivation unstated] | −14.5 % TTT | N1 E1 S1 C1 B2 |
| 23 | Wang C. 2022 | IFBC [copied gains] | ≈ −9.5 % TTT (training curves) | E1 B2 C1 S1/S3 |
| 24 | Lu 2023 | other RL | −1.8 % TTS | B1 N1 S2/S3 E2 M2 |
| 25 | Chen X. 2023 | NC | speed +12.3 % | B1 M2/C1 E1 S1 B4 |
| 26 | Hua & Fan 2023 | NC | −3.9…−5.2 % MTT | B1 M2 E1 S3 |
| 27 | Zhang Yuhang 2023 | NC | delay **+5.0 / +6.5 %** (worse) | B1 M2 M1 |
| 28 | MARVEL 2024 | Speed-Matching ["carefully searched"] | safety tie; queue > NC | M2 B2/B3 C1 P2 |
| 29 | Pelenczei 2024 | MCS, MTFC [not stated; MTFC worse than NC] | −11.8 / −6.3 % TT | B2 S2/S3 M2 P2 R1 |
| 30 | Jin 2024 | MCTM-MPC [GA; tuning not stated] | −1.9 / −0.9 % time loss | S2/S3 B2 B4 M1 N1 |
| 31 | Jin 2025 | fixed limit; RL variants | no dominance | B1 E1? S2/S3 N1 |
| 32 | Kang 2024 | NC | density −53 % | B1 E1 N1 M2 S3 |
| 33 | Li & Lasenby 2024 | other RL | −2.6 % TTS | B1 S1/S3 E1 R1 |
| 34 | Han 2024 | Carlson FB [set, not tuned; one limit] | **−26.4 / −19.0 %** relative (printed as 21.34 / 16.75 pp) | B2 B4 E1 S1–S3 N1 R1 |
| 35 | Hua & Fan 2024 | NC | −4.4…−5.3 % ATT at equal MPR | B1 C1 E1 S3 M2 |
| 36 | Ko 2020 | FIFO, rule SH [not stated] | throughput −10.9…+19.2 % | N1 C1 B2 E2 S1 |
| 37 | Yang 2024 | rule VSL [undefined; worse than NC at low flow] | −3.7…−5.7 % ATT | N1/C1 B2 S2/S3 E1 |
| 38 | Yan 2025 | other RL | "40 %" not derivable | N1 C1 M2 S1–S3 |
| 39 | Vatani Nezafat 2019 | P-FB [grid search, in-sample, undocumented] | −21 / −54 / −7 % (train demand); −22 / −29 / −6 % (held out) | B3 R1 S1 S3 E2 N1(labels) |

**Good practice worth crediting** (details in the profiles):
- #5: deliberate model mismatch for the MPC; 20 repeats.
- #9: 10 replications; a hybrid that is honest about its structure.
- #10: capacity drop demonstrated.
- #11: calibrated network; tuned comparators.
- #24: held-out scenarios.
- #27: discloses the delay loss and gives standard deviations.
- #39: grid-searched comparator, held-out demand, and 50-run sensitivity analysis.

## 3. The strongest positive claims, and the cost of reproducing them

### 3.1 Which claims are worth testing

| Candidate | What the claim really is, after the re-check | Value of a reproduction |
|---|---|---|
| **#34 Han 2024** (TRR, SUMO) | 26 % / 19 % lower TTS than an **untuned, single-limit** Carlson FB, on the training demands, number of runs unknown | **High.** Native SUMO, a merge bottleneck close to your T1/T2 plants, and a large claimed gain. The two weaknesses (B2, B4) can be fixed directly: tune FB on separate seeds, and add a **per-lane FB** variant. |
| **#39 Vatani Nezafat 2019** (PhD) | 6–29 % less remaining delay than a grid-searched P-feedback VSL on a **held-out** demand; single runs; custom simulator | **High.** The only large gain against a comparator that had some tuning, and it includes a held-out test. The lane-drop case (54 % / 29 %) is the strongest. |
| **#7 Ke 2021** (T-ITS, CTM) | ≈ 50 % vs **no control** in a CTM whose capacity drop VSL can switch off; there is no classical comparator | **Low in SUMO** (it would test a claim the paper never made). **Medium as a CTM replication** with a tuned feedback added (§3.3). |

**Not a candidate but worth naming: #5 Han & Hegyi 2022.** It is the most carefully designed positive result in the sample (MPC with deliberate model mismatch, 20 repeats), but it is macroscopic and uses online learning. A SUMO port would change the claim. Read it as the best published case *for* RL, and cite it fairly.

### 3.2 Cost estimates

**Assumptions:**
- The v5 lab pipeline is reused: libsumo workers, health checks, ledger, paired bootstrap, and the frozen-baseline workflow.
- Plain runs use 32 workers.
- For scale: in the ledger, BN4 RecurrentPPO runs of 1,000–2,000 episodes finished within a few hours each (2026-10-03 rows). I did not measure per-episode wall time for these new networks, so **the CPU figures below are order-of-magnitude estimates, not measurements**.
- Person-days assume your current pace with Claude doing the build.

**#34 Han 2024, SUMO** (est. **10–15 working days**, ≈ 100–300 CPU-core-hours)

| Step | Est. days |
|---|---|
| Build the network: 5 km, 3 lanes, O1 / D1 / O2. Geometry is guessed from Fig. 4, because ramp positions and lengths are missing. | 1–2 |
| Digitise the demand in Fig. 5. Set up HDV (IDM + LC2013) and CAV (ACC/CACC, 30 %). The compliance distribution is a guess. | 1–2 |
| **T0/T1 checks first:** does O2 show a capacity drop (the paper claims 7.8 %), and does the limit bind? **This is the most likely kill point.** v5 never got a drop at a merge (MRG3 realism gate: discharge 1,528 < 1,600 veh/h/lane). | 1–3 |
| Baselines, all tuned on separate seeds: (1) Carlson FB with one limit, as in the paper; (2) per-lane FB; (3) a fitted-model MPC, if time allows. | 2–3 |
| MADDPG with 3 agents. It is not in SB3, so either implement it (≈ 2–3 days) or use parameter-shared PPO and declare the deviation. Then 1,000 episodes × 120 steps × 3–5 training seeds. | 3–5 |
| Pre-registered confirmatory run on reserved seeds | 1 |

**Decision value.** If RL beats the per-lane tuned FB by ≥ 10 % with a CI > 0, that is a strong positive result for your thesis. If not, it is a clean, publishable non-replication.

**#39 Vatani Nezafat, lane drop + on-ramp only, SUMO** (est. **8–12 working days**, ≈ 100–250 CPU-core-hours; +5–10 days for the sag case)

| Step | Est. days |
|---|---|
| Networks: 6 km, 3→2 lane drop; 6 km, 2 lanes + 150 m acceleration lane. Geometry and IDM parameters are fully given (Tables 1–2). | 1–2 |
| Lagrangian VSL: the max speed of CVs in the 1 km control section, via libsumo per vehicle | 1 |
| **T1 check:** does LC2013 or SL2015 reproduce the lane-drop capacity drop (≈ 4,000 → 2,800 veh/h in their Fig. 15)? LMRS is not in SUMO, so the drop will differ. | 1–2 |
| P-feedback (Eq. 33): grid search on tuning seeds, freeze, then evaluate on the held-out demand pattern | 1–2 |
| A3C → PPO (declared deviation): ≈ 10,000 episodes of 25–30 simulated minutes; 3–5 seeds × 2 networks | 3–4 |
| **Sag case** (optional): SUMO has no Goñi-Ros sag model. It needs a per-vehicle acceleration override or a C++ model [VERIFY how much SUMO 1.27 models slope]. | +5–10 |
| Confirmatory run | 1 |

**#7 Ke 2021** (est. **SUMO port 15–25 days; CTM replication 4–6 days**)
- **SUMO port.** The I-880 network is 7 miles with several ramps whose modelling is unclear. The training demand and all DDQN hyperparameters are missing. The capacity drop would be emergent, not built in. Expect a different and probably smaller gain; you would be testing a different claim.
- **CTM replication (recommended if you do #7 at all).** Re-implement the CTM with the inverse-λ drop (Eq. 7), using the parameters printed on pp. 3–6. Reproduce ≈ 50 % vs NC. Then add a **Carlson FB tuned on separate demands, in the same CTM**.

  This answers the one interesting question cheaply: *in the authors' own model, does DDQN beat a tuned feedback controller?* If the tuned FB also removes the drop, the two will tie near 505 veh·h. Results from the paper (VSL TTS ≈ 502–505 regardless of drop size) suggest a tie is likely, but that is my inference.

**My recommendation.** If you reproduce anything:
1. **Do #34 first.** It is the closest to your plants and has the best decision value. The T0/T1 check on day 3–5 may end it cheaply.
2. **Then #39's lane drop.**
3. **Skip #7 in SUMO.**

Each needs a fresh, author-approved seed range. The approved layout (roadmap §10) has no reproduction track, so a block would have to be allocated. That is your call.

**My prior** (judgement, not a measurement) is that neither reproduction will clear 10 % against a tuned, equally actuated comparator. That is based on #11 (≈ 1.6 %), #10, #18's like-for-like loss, and your R6 (2.5–4.3 %).

## 4. Is a critical review or a negative-results paper publishable, and where?

### 4.1 Assessment

**Paper A: a critical audit of DRL-VSL evaluations. Publishable, if three conditions are met.**
1. **A documented, reproducible search** (databases, strings, dates, inclusion rules; PRISMA-style flow). The current 39 are a convenience sample. A reviewer will ask first how the papers were chosen.
2. **A pre-specified, symmetric audit protocol.** The flag codes in the profiles are a start. Ideally a second rater codes a subset and you report agreement. With an agent as second rater, say so; a human second rater is better.
3. **Fair tone and an author query.** Send the N1 items (§1.5–1.6) to the corresponding authors before submission and report the replies. Credit good practice.

**Differentiation.** RL-VSL reviews already exist:
- Kušić et al. 2020, *Applied Sciences* 10(14):4917, local file. It already notes that most studies compare only with no control.
- A 2021 *Applied Sciences* review, 11(6):2574 [abstract only].

General RL-methodology critiques exist too:
- Henderson et al., AAAI 2018;
- Agarwal et al., NeurIPS 2021;
- Patterson et al., JMLR 2024;
- for traffic signal control: Varela et al., arXiv 2101.09614; Wang, Sanner & Abdulhai, arXiv 2211.14426; Ault & Sharon, NeurIPS Datasets & Benchmarks 2021.

All of these are [abstract only]; I have not read them in full. A limited search found no critique specific to RL-VSL baselines and statistics. That is not proof that none exists, and per your rules **do not claim "first"**.

The contribution would be the *recomputation*: comparator tuning status, gains vs the strongest comparator, and N1 resolution. That is concrete and checkable.

**Paper B: DRL vs tuned control under pre-registration (SUMO). Publishable, and I think it is the stronger paper.**
- It is not a pure null result. R6 is a pre-registered, confirmatory **small** win: −2.5 % vs a fitted-model MPC and −4.3 % vs a tuned event scheduler, on 210 reserved seeds, with a door-to-door metric. It also sits **+5.8 %** behind the condition-informed lookup reference (`docs/lab/t1_meter_r6.md`).
- Together with the killed tracks and gates, the message is **"DRL gains exist, but they are single-digit percent once baselines are tuned and statistics are paired"**. That is informative and citable.
- Adding the #34 reproduction (§3) would make it substantially stronger.
- Risk: some transport venues may see it as "no new method". The answer is the protocol itself (headroom gates, tool checks, reserved seeds), presented as reusable.

**A combined paper** (an audit in §2, your experiments in §3–5) is possible. But two papers fit your "2 papers" target better.

### 4.2 Venues

**Verification.** A web agent checked official pages on 2026-10-04. Its quotes come from fetched-page summaries, so **re-check each policy on the live page before relying on it**. Policies change.

| Venue | Fit | Verified detail (URL fetched) | Caveat |
|---|---|---|---|
| **IEEE Transactions on ITS** | A (survey) | survey papers are an official article type (ieee-itss.org/pub/t-its/) | no negative-results language; #3, #7, #9, #23, #33 appeared here, so the audit concerns its own papers. Handle that with care in the cover letter. |
| **Transactions on Machine Learning Research (TMLR)** | A or B (reproducibility study) | accepts "reproducibility studies of previously published results or claims"; the criterion is claims supported by evidence (jmlr.org/tmlr/acceptance-criteria.html) | ML audience, not transport |
| **PLOS ONE** | B | "we consider negative and null results" (journals.plos.org/plosone/s/criteria-for-publication) | broad audience; APC |
| **ReScience C** | a replication of #34 or #39 | replications of published computational work (rescience.github.io) | needs an editor with matching expertise; only for a replication, not for B as a whole |
| **IEEE ITSC 2027** | B (short) | the official list gives Boston | no CfP or dates found |
| **TRB Annual Meeting / TRR** | A or B | the 2027 paper window (1 Jul – 1 Aug 2026) is closed | the next cycle probably closes ≈ Aug 2027 (inference): late for the thesis |
| **Reinforcement Learning Conference / RLJ** | B | the 2026 call welcomes interdisciplinary work "which has an RL audience" | 2027 location announced, but no 2027 call found; a novelty criterion may hurt a null result |
| **SUMO User Conference** | B (tool-centred) | the 2026 edition was held 1–4 June, Berlin (sumo.dlr.de/hugo/2026/) | no 2027 edition found |

**Not assessed.** The agent could not read the journal pages on the Taylor & Francis, ScienceDirect and SAGE platforms (HTTP 403). Several audited papers appeared in *Transportation Research Part C* (#2, #5, #15, #24) and *Transportation Research Record* (#34), but I have **not** verified their policies on reviews or negative results. Check them yourself before choosing.

**No transport journal offering Registered Reports was found.** This is per the agent's reading of the COS list [VERIFY].

**My suggestion (judgement):**
- Paper B → IEEE T-ITS as a regular article (if framed around the protocol and R6), or PLOS ONE if a transport venue rejects it as "not novel".
- Paper A → IEEE T-ITS (survey type) or TMLR.
- ITSC 2027 as an early, short version of B, if its dates fit.

## 5. Supervisor note

See `supervisor_note_drl_vsl_v0.md` (one page).
