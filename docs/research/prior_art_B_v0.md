# Track B prior art: cooperative merging without a ramp signal (verified)

Date: 2026-11-01. Draft for V246 direction B. Nothing here was decided by the author.

## How this note was checked

- Metadata (title, authors, venue, year, volume, pages): checked against the arXiv API (19 IDs), Crossref and OpenAlex (25 DOIs). Every arXiv ID and DOI below resolved, and the authors matched unless a line says otherwise.
- Claims: the verifier reopened each source and checked the claimed numbers and quotes as far as access allowed:
  - full-text PDFs (pdftotext): Trust-MARL, Chen et al., RLPG, Sun & Yu, Vinitsky 2018, Zhu-Tasic-Qu 2022, FHWA-HRT-21-008, Davis (arXiv), Scarinci 2015 and 2017 (UCL eprints), Irshayyid dissertation, Fan & Chung;
  - HTML full text, read through an automated page extractor (numbers may need a PDF check): Z-Merge, Yan et al., DIACC (first 100k characters), Guo et al. (first 100k characters), Zhou et al.;
  - abstracts only: the remaining sources;
  - SUMO: the docs pages, the ChangeLog and the GitHub issues API.
- Status codes:
  - **V**: exists, and the claim is supported at the stated read level;
  - **V\***: verified, but part of the original claim is corrected below;
  - **EU**: exists, but the claim is not supported;
  - **MW**: metadata wrong, corrected here;
  - **NF**: not found.
- "Read level" names what the verifier checked. The searcher's read level is in brackets where it differs.
- **No source was NF.** Nothing looks fabricated. The appendix lists the items that are unverified or unidentified; they are kept out of the implications.

## 1. Closest work

### 1a. Learning-based, SUMO, mainline vehicles help ramp vehicles, no ramp signal

- **Yan, König, Burgard (2024).** Agent-Agnostic Centralized Training for Decentralized Multi-Agent Cooperative Driving. arXiv:2403.11914v2; the arXiv comment says "accepted by IROS 2024". **V**, HTML full text.
  - Setup: SUMO; ramp traffic merges into a two-lane freeway whose vehicles have right of way. Actions: left, right, or a target speed of 0 / 0.33 / 0.66 / 1 × the speed limit. Conservative AVs use lcAssertive 0.1 and lcSpeedGain 0. Five seeds.
  - On-ramp results:
    - throughput at 4,000 veh/h: 88.3 % with no control vs 90.5 % (DVC-80-100);
    - waiting time at 3,500 veh/h: 37.0 s with no control vs 29.3 s (DVC-80-100 and CVC-80), and 27.7 s for DVC-40-50;
    - ramp throughput about threefold at 80 % AVs, where no control falls to about 30 %.
  - ALINEA appears only in the lane-drop scenario. There are no collision or TTC metrics ("collision-free environment").
- **Ibork, Won, Das (2025).** Z-Merge: Multi-Agent Reinforcement Learning for On-Ramp Merging with Zone-Specific V2X Traffic Information. arXiv:2511.14910v1, no venue. **V\***, HTML full text.
  - Setup: SUMO plus Eclipse MOSAIC. A 320 m segment with a 100 m ramp. Demand 3,600 veh/h/lane mainline and 900 veh/h/lane ramp. AV shares 5-60 %. Actions include a gap of 5-20 m. TTC threshold 1.2 s.
  - Results at 60 % AVs (Table 2): Z-Merge 93.25 ± 2.85 % success and 2.66 ± 0.88 % collisions; Baseline-1 89.51 / 2.14; Baseline-2 59.36 / 0.07; Baseline-3 82.61 / 6.21.
  - Inconsistencies: the text gives Baseline-3's collision rate as 4.53 %, not 6.21 %. The acceleration range differs between the text and Table 1. The ± is undefined, and no seeds are given.
  - Correction: the paper does not *state* whether code is released. "No code released" is not established.
  - All baselines are learning-based (Liu et al. 2024; Zhu et al. 2024; Wu et al. 2025). The first two were not identified [VERIFY].
- **Pan, Wang, Claudel, Shi (2025).** Trust-MARL. arXiv:2506.12600v1, no venue. **V**, full-text PDF.
  - Setup: SUMO; a 10 km two-lane highway; demand 300 / 600 / 900 veh/h split 80/20; CAV shares 0 / 30 / 70 / 100 %; ten seeds; 1 h warm-up plus 5 h of data. Conflict-point sensors capture "minimum TTC, and post-encroachment time", but the term PET does not appear in the results.
  - Results at 100 % CAVs and 900 veh/h:
    - collisions 2.5 % vs 5.2 % (rule-based);
    - travel time 700 s vs 780 s;
    - jerk 0.8 vs 1.5 m/s³.
  - The rule-based baseline: "with purely human-driven traffic at 900 veh/hr, 10.5 % of merges still result in conflict". Its reference [56] lists Zhang, Zhuang, Zhu for the title "A rule-based cooperative merging strategy…". The indexed authors of that title are Ding, Li, Peng, Zhang (T-ITS 21(8), 2020). The mismatch is confirmed.
  - New red flag: HVs are said to use "IDM … and MOBIL" inside SUMO, but MOBIL is not one of SUMO's lane-change models, which suggests a modified setup or a description error [VERIFY].
- **Guo, Fu, Xu, Gu, Qiao, Ji (2026).** A Cooperative Merging Method for Mixed Traffic Based on Enhanced Graph Reinforcement Learning with Vehicle Collaboration Graphs. Sensors 26(4):1225, doi:10.3390/s26041225. **V**, HTML, first 100k characters.
  - Setup: Flow on SUMO; a 3-lane mainline and a 1-lane ramp; actions left / keep / right only.
  - "Rule-Base" = SUMO built-in IDM + LC2013. Average CPMR at medium density: 0.18 (proposed), 0.25 (GCAV-CPO), 0.46 (Rule-Base).
  - 50 test runs; no seeds or significance tests; N = 56 adjacency.
- **Chen, Hajidavalloo, Li, Chen, Wang, Jiang, Wang (2023).** Deep Multi-Agent Reinforcement Learning for Highway On-Ramp Merging in Mixed Traffic. IEEE T-ITS 24(11):11623-11638, doi:10.1109/TITS.2023.3285442; arXiv:2105.05701v3. **V**, full-text arXiv v3.
  - Setup: a highway-env-based simulator; HDVs use IDM / MOBIL.
  - Hard mode, collision rate: MPC 0.40, MAA2C 0.52, MAACKTR 0.18, MAPPO 0.34, proposed 0.
  - Hard mode, average speed: 21.02 / 19.68 / 18.19 / 22.41 / 22.73 m/s.
  - Code: github.com/DongChen06/MARL_CAVs.
  - Not re-checked: the agent counts per mode, Fig. 15, and the MOBIL lane-end remark.
- **Shi, ElSamadisy, Abdulhai (2026).** CoopSECRM2D: A Safe, Efficient, and Comfortable Multi-Agent Reinforcement Learning Model for Cooperative On-Ramp Merging. IET Intelligent Transport Systems 20(1):e70256, doi:10.1049/itr2.70256. **V\*** (year and volume added), abstract via OpenAlex; the full text returned 403.
  - The abstract confirms SUMO, synthetic setups and the Queen Elizabeth Way (Ontario). Baselines and numbers were not seen [VERIFY].
  - Precursor: Shi, Smirnov, ElSamadisy, Abdulhai, SECRM-2D, IET ITS 19(1):e70013 (2025), doi:10.1049/itr2.70013; arXiv:2407.16857. **V**, metadata.
- **Vinitsky, Kreidieh, Le Flem, Kheterpal, Jang, Wu, Wu, Liaw, Liang, Bayen (2018).** Benchmarks for reinforcement learning in mixed-autonomy traffic. CoRL 2018, PMLR 87:399-409. **V**, full-text PDF.
  - Merge benchmark: merge0/1/2 at 10 / 25 / 33.3 % CAVs, T = 750.
  - Average speed: Human 7.39 ± 0.55 m/s; TRPO 14.95 (merge0); ES 17.29 / 17.36 (merge1/2).
  - Quoted: "the trained policies started to gradually degrade after certain iterations". Lane changing and merging are "dictated by the simulator".
  - The only comparison is RL vs Human.

### 1b. Non-learning mainline gap creation (candidate tuned opponents)

- **Scarinci, Heydecker, Hegyi (2015).** Analysis of Traffic Performance of a Merging Assistant Strategy Using Cooperative Vehicles. IEEE T-ITS 16(4):2094-2103, doi:10.1109/TITS.2015.2394772. **V\*** (year, volume and pages now fixed: 2015, 16(4), 2094-2103), full-text accepted manuscript (UCL eprint 1460741).
  - Setup: VISSIM 5.40 plus MATLAB R2012b; a single-lane main carriageway at 2,000 veh/h; ramp demand 200-900 veh/h in 50 veh/h steps; 30 seeds per flow.
  - Strategy: Δv = 10 km/h, np = 10; signal cycle 18.0 s with 7.5 s green; slowing starts at least 1.8 km upstream.
  - Findings, quoted: at ≥ 850 veh/h "few empty spaces are left to be rearranged" and "the only possible control option could be to reduce the demand". The strategy "cannot increase the capacity of the main carriageway". Platoon release without mainline cooperation raises the breakdown rate.
  - Caveat: the p-value table did not extract cleanly, so which flows were non-significant needs the PDF table [VERIFY].
- **Scarinci, Hegyi, Heydecker (2017).** Definition of a merging assistant strategy using intelligent vehicles. Transportation Research Part C 82:161-179, doi:10.1016/j.trc.2017.06.017. **V** (volume, pages and DOI added), full-text accepted manuscript (UCL eprint 1561171).
  - Assumptions: 100 % penetration and homogeneous drivers. Quoted: "near-side lane changes should be restricted in the vicinity of the on-ramp". The system "operates only in the free-flow state"; in congestion "other ITS should be used".
  - It credits Uno et al. (1999) for the virtual vehicle, and Xu & Sengupta (2003) and Davis (2007) for gap creation in mixed traffic.
- **Zhu, Tasic, Qu (2022).** Flow-level coordination of connected and autonomous vehicles in multilane freeway ramp merging areas. Multimodal Transportation 1(1):100005, doi:10.1016/j.multra.2022.100005; arXiv:2202.09454. **V** (venue confirmed), full-text arXiv.
  - Setup: VISSIM, 100 % CAVs at SAE level 4. Quoted: without the one-sided lane-change prohibition, inner-lane vehicles "may change into the gaps created in the outer lane … leading to a failure".
  - Table 6, overall delay: 1A 3.93 → 2.63 s; 2C (2,200 veh/h/ln, 500 veh/h ramp) 78.82 → 10.72 s, an 86.4 % reduction vs base (no control).
- **Zhu, Wang, Tasic, Qu (2024).** Improving Freeway Merging Efficiency via Flow-Level Coordination of Connected and Autonomous Vehicles. IEEE T-ITS 25(7):6703-6715, doi:10.1109/TITS.2023.3346832. **MW**: the searcher attached arXiv:2202.09454 to this paper, but that ID is the 2022 Multimodal Transportation paper above. This T-ITS paper has been checked for metadata only; its content has not been read [VERIFY].
- **Ma, Leslie, Ghiasi, Guo, Sethi, Hale, Shladover, Lu, Huang (2021).** Applying Bundled Speed-Harmonization, Cooperative Adaptive Cruise Control, and Cooperative-Merge Applications to Managed-Lane Facilities. FHWA-HRT-21-008, March 2021. **V\***, full-text PDF.
  - Gap regulation distance 200 m; critical gap 1.4 s.
  - Table 2 (cooperative vs non-cooperative):

    | CAV share | Throughput (veh/h/lane) | Delay (s) |
    |---|---|---|
    | 100 % | 2,850 → 3,064 (+7.51 %) | 163.82 → 37.33 (−77.21 %) |
    | 70 % | 2,518 → 3,012 (+19.61 %) | 111.87 → 36.74 (−67.15 %) |
    | 30 % | 2,364 → 2,401 (+1.57 %) | 92.40 → 34.27 (−62.91 %) |

  - **Correction:** "small gains at 30 %" holds only for throughput. The delay reduction at 30 % is still about 63 %. Throughput gains peak at 70 %.
  - Quoted: at 0 % the cooperative merge is "even worse than the noncooperative-merge". With manual drivers, "the identified gap no longer exists when the merge vehicle arrives". A too-small threshold causes "disruptions to the local traffic".
  - The simulator was not identified [VERIFY].
- **Davis (2007).** Effect of adaptive cruise control systems on mixed traffic flow near an on-ramp. Physica A 379(1):274-290, doi:10.1016/j.physa.2006.12.017; arXiv:physics/0506147. **V**.
  - arXiv full text: 18 % throughput and up to 3 km in 500 s at 50 % ACC. The published abstract (via Semantic Scholar) gives 20 % and 3.6 km in 600 s at moderate ramp demand; both versions are now confirmed.
  - For large demand, full implementation is required.
- **Pueboobpaphan, Liu, van Arem (2010).** The impacts of a communication based merging assistant on traffic flows of manual and equipped vehicles at an on-ramp using traffic flow simulation. ITSC 2010, pp. 1468-1473, doi:10.1109/ITSC.2010.5625245. **V**, abstract. The abstract confirms early, smooth mainline deceleration, effectiveness that depends on conditions and composition, and an unexplained "negative side effect" [mechanism VERIFY].
- **Hou, Zheng, Liu, Guo (2023).** Cooperative On-Ramp Merging Control Model for Mixed Traffic on Multi-Lane Freeways. IEEE T-ITS 24(10):10774-10790, doi:10.1109/TITS.2023.3274586. **V**, abstract.
  - CAVs plus connected HDVs with a driver compliance rate. Benefits are "marginal" at low CHV compliance and significant above 50 %. Merging and mainline throughput rise by more than 75 % at high CAV share.
  - These details were added by the verifier; the searcher had only a secondary mention.
- **Ding, Li, Peng, Zhang (2020).** A Rule-Based Cooperative Merging Strategy for Connected and Automated Vehicles. IEEE T-ITS 21(8):3436-3446, doi:10.1109/TITS.2019.2928969. **V**, abstract. A rule-based adjusting algorithm for a near-optimal merging sequence of two strings of vehicles, compared with rule-based and optimisation methods.
- **Uno, Sakaguchi, Tsugawa (1999).** A merging control algorithm based on inter-vehicle communication. IEEE/IEEJ/JSAI ITSC 1999, pp. 783-787, doi:10.1109/ITSC.1999.821160. **MW, corrected.**
  - The searcher gave "Uno & Tsugawa 1999, 'Inter-vehicle communications for merging control'". That title belongs to Sakaguchi, Uno, Tsugawa, IVEC'99, pp. 365-370, doi:10.1109/IVEC.1999.830706.
  - Sakaguchi is an author of both. The virtual-vehicle mapping is confirmed by the ITSC abstract; Scarinci 2017 cites the ITSC paper.
- **Rios-Torres, Malikopoulos (2017a).** A Survey on the Coordination of Connected and Automated Vehicles at Intersections and Merging at Highway On-Ramps. IEEE T-ITS 18(5):1066-1077, doi:10.1109/TITS.2016.2600504. **V**, abstract.
- **Rios-Torres, Malikopoulos (2017b).** Automated and Cooperative Vehicle Merging at Highway On-Ramps. IEEE T-ITS 18(4):780-789, doi:10.1109/TITS.2016.2587582. **V\*** (the searcher had only "ORNL record, 2016"), abstract. A closed-form solution; "can significantly reduce both fuel consumption and travel time".
- **Ntousakis, Nikolos, Papageorgiou (2016).** Optimal vehicle trajectory planning in the context of cooperative merging on highways. Transportation Research Part C 71:464-488, doi:10.1016/j.trc.2016.08.007. **V**, abstract via the TU Crete repository snippets: an analytic finite-horizon OCP, a time-variant LQR alternative and an MPC scheme.
- **Xiao, Cassandras (2018).** Decentralized Optimal Merging Control for Connected and Automated Vehicles. arXiv:1809.07916. **V**, abstract: joint travel time and energy with a speed-dependent safety constraint. The claims about FIFO and a human-driven baseline were not checked [VERIFY].
- **Liu, Zhuang, Yin, Li, Liu, Zhou (2021).** Decentralized On-Ramp Merging Control of Connected and Automated Vehicles in the Mixed Traffic Using Control Barrier Functions. arXiv:2111.00746. **V**, abstract.
- **Letter, Elefteriadou (2017).** Efficient control of fully automated connected vehicles at freeway merge segments. Transportation Research Part C 80:190-205, doi:10.1016/j.trc.2017.04.015. **V\***, abstract via search snippets. The objective is to maximise average travel speed. Evaluation is in CORSIM against a traditional stream; it is efficient in free flow, with gains that grow with demand. "Reduces travel time and raises throughput" is not confirmed in those words.

### 1c. Other learning-based work (context)

- **Liu, Li, Li, Li, Liu (2024).** GCAV-CPO. IEEE Internet of Things Journal 11(24):39809-39819, doi:10.1109/JIOT.2024.3447039. **V**, abstract. The simulator is not in the abstract [VERIFY].
- **Liu, Cai, Wang, He, Lv, Zuo (2026).** DIACC. arXiv:2603.03848v1. **V\***, HTML, first 100k characters.
  - Setup: SUMO plus TransSimHub and HARL; a 1.3 km route with 25 % and 50 % capacity-reduction segments; 10 of 25 vehicles are CAVs; 3 training seeds; the speed ± is a standard deviation.
  - Results: 25 %: 19.04 vs 17.05 m/s, p(SCEs) 0 vs 6.40 %. 50 %: 17.60 vs 14.10 m/s, p(SCEs) 0 vs 7.60 %.
  - Correction: the table labels the comparison row "SUMO mixed traffic". Whether it is the "pure HDV" or the "SUMO cooperative (CACC + lcCooperative = 1)" baseline needs the full table [VERIFY].
- **Irshayyid, A. S. (2024).** Highway Merging Control Using Multi-Agent Reinforcement Learning: Exploring Centralized and Decentralized Schemes. PhD dissertation, Oakland University (committee chair Jun Chen). **V**, full-text PDF.
  - Setup: SUMO via TraCI with the Krauss car-following model; the right lane ends after 300 m; 50 vehicles per episode.
  - Results: 1,498.75 vs 1,304.35 veh/h (+14.9 %) at 10 m/s; 2,135.23 vs 1,333.33 veh/h (+60.14 %) at 20 m/s vs a zipper merge.
- **Fan, Chung (2025).** Multi-Agent Reinforcement Learning for CAV Cooperative Merging Considering Communication Failure. hEART 2025 short paper 192 (The Hong Kong Polytechnic University). **V**, full text.
  - Setup: SUMO; 5 CAVs at 50 %; final rewards −200 for a collision and −100 for a timeout; packet loss p = 0.2.
  - Finding: local rewards gave more collisions, global rewards gave conservative behaviour.
- **Yadavalli, Das, Won (2023).** RLPG. arXiv:2212.03497v2. **V**, full text.
  - SUMO plus Simpla; gap range [2 m, 30 m]; average speed +31.8 % (platoon size 20) and +66.3 % (size 30) vs the base case. Safety is named only as a future avenue.
  - The IROS 2023 venue is not confirmed by arXiv [VERIFY].
- **Zhou, Huang, Tian, Huang, Ou, Lin (2025).** Deep reinforcement learning-based multi-lane mixed traffic ramp merging strategy. PLOS ONE 20(9):e0331986. **V**, HTML.
  - SUMO, 3 lanes, zones of 400 / 100 / 100 m. HDVs follow IDM and are limited in "spontaneous lane changes".
  - Completion 98.62 % at 1,200 veh/lane/h, "11.08 % higher" than D3QN; relative vs percentage points is not stated.
- **Sun, Yu (2024, v3 2026).** Reinforcement Learning for Freeway Lane-Change Regulation via Connected Vehicles. arXiv:2412.04341v3. **V\***, full text.
  - Setup: SUMO, 5 lanes, 1 km, SL2015 (lateral resolution 0.8 m).
  - Correction: speed gains are about 2-5 % under low and high demand, and **near zero under congested demand** (the table marks it "close to zero"; raw speeds change by −0.5 % to +0.7 %). The original note said "+0.3-0.5 %".
  - Below 30 % regulation the result is "comparable to the uncontrolled baseline".
- **Irshayyid, Chen, Xiong (2024).** A review on reinforcement learning-based highway autonomous vehicle control. Green Energy and Intelligent Transportation 3(4):100156. **V\***, abstract. The scope is confirmed (lane change, ramp merge, platoon coordination). The listed subtopics and the "calls for benchmarks" are not in the abstract [VERIFY].
- **Hua, Chen, Qi, Jiang, Liu, Zhou, Xu (2023, v3 2024).** Multi-Agent Reinforcement Learning for Connected and Automated Vehicles Control: Recent Advancements and Future Prospects. arXiv:2312.11084v3. **V**, abstract. On-ramp merging is not named in the abstract.
- **Zhu, Easa, Gao (2022).** Merging control strategies of connected and autonomous vehicles at freeway on-ramps: a comprehensive review. Journal of Intelligent and Connected Vehicles 5(2):99-111, doi:10.1108/JICV-02-2022-0005. **V**, abstract: 44 papers in three categories.
- **Jing, Pei, Yan, Han, Selpi, Andreotti, Ding (2022).** Safety benefit of cooperative control for heterogeneous traffic on-ramp merging. Transportation Safety and Environment 4(4):tdac031, doi:10.1093/tse/tdac031. **V\***, abstract; the authors were added (the searcher had only "Jing et al."). In SUMO via TraCI, conflicts fall significantly only "whereas the penetration rate is over 80 %", under random departure speed and higher arrival rate.
- Abstract-level checks on arXiv:
  - **Das, Won (2021).** D-ACC. arXiv:2006.01411, ICRA 2021 per the arXiv comment. **V**: SUMO plus Veins, flow "up to 70 %" vs an intelligent ACC.
  - **Hu, Nakhaei, Tomizuka, Fujimura (2019).** IDAS. arXiv:1904.06025, an IROS 2019 best-paper finalist. **V**.
  - **Nakka, Chalaki, Malikopoulos (2022).** ACC 2022, pp. 3297-3302, arXiv:2109.11672. **V**.
  - **Poots (2024).** RACE-SM. arXiv:2403.03359. **V**.
  - **Wu, Ji, Fan, Wang, Cheng, Chen, Letaief (2025).** arXiv:2501.12656, NS-3 plus Python. **V**.
- **Zhao, Cui.** Multi-agent Reinforcement Learning for Cooperative On-Ramp Merging of Connected Automated Vehicles. LNICST (IoTaaS), pp. 200-221, doi:10.1007/978-3-031-70507-6_16. **V\***: Crossref gives 2025, not 2024. Content not read.
- **Mainline lane-change advisory.**
  - Park, H., Smith, B. L. (2012). Investigating Benefits of IntelliDrive in Freeway Operations: Lane Changing Advisory Case Study. J. Transp. Eng. 138(9):1113-1122, doi:10.1061/(ASCE)TE.1943-5436.0000407. **MW**: Crossref and OpenAlex list two authors, not "Park, Bhamidipati, Smith". The abstract confirms early mainline lane changes that make room at ramp merges, evaluated in PARAMICS.
  - The "Virginia dissertation" is Hayat, M. T. (2015). Investigating Drivers' Responses to Advisory Messages in a Connected Vehicle Environment. PhD, University of Virginia, doi:10.18130/V3MZ8K. **V**, abstract: compliance 84.8 % for merging control, 84.3 % for the lane-changing advisory, and 63 % for VSL (field test).
  - Balirano, Marchetta, Coppola (2025). Mitigating Merge Congestion with CCAM Services: A Comparative Study on A56 Italian Motorway. MT-ITS 2025, doi:10.1109/MT-ITS68460.2025.11223549. **V**, abstract (authors and title added): Eclipse MOSAIC, Gap-Opening at 40 % and 50 % CAVs, shorter average travel times. No numbers in the abstract.
- **Hidas (2005).** Modelling vehicle interactions in microscopic simulation of merging and weaving. Transportation Research Part C 13(1):37-62, doi:10.1016/j.trc.2004.12.003. **EU** for the attributed claim.
  - The record and the video-based congested merging data are confirmed in search snippets.
  - The claim that "only models with forced and cooperative lane changing reproduce realistic congested flow-speed" comes from the companion paper, Hidas (2002), Modelling lane changing and merging in microscopic traffic simulation, TR-C 10(5-6):351-371, doi:10.1016/S0968-090X(02)00026-8. That paper was seen only through secondary summaries [VERIFY]. Cite the 2002 paper for that sentence.

### 1d. SUMO behaviour (toolchain 1.27.1)

- **TraCI openGap and laneChangeMode.** SUMO docs, TraCI/Change_Vehicle_State. **V**, page grep.
  - openGap: "temporary increase of the vehicles desired time headway"; with a reference vehicle it "does not use the current leader". The Euler note is quoted: "the time headway control does not work properly for low speeds".
  - laneChangeMode default 1621 = 0b011001010101.
  - The rule "openGap ignores a headway below the current tau" is our own V195 observation, not in the docs.
- **Lane-change parameters.** SUMO docs, Definition of Vehicles, Vehicle Types, and Routes. **V**, page grep.
  - lcCooperativeHelpTime default 60 s; lcCooperativeHelpThreshold default −1; lcAssertive "required gap is divided by this value", default 1; lcStrategicLookahead default 3000 m.
  - lcImpatience, lcTimeToImpatience and lcAccelLat are SL2015 only.
  - Not confirmed on that page: the lcCooperativeMinSpeed default, and setting LC parameters through `setParameter("laneChangeModel.<ATTR>")` [VERIFY].
- **ChangeLog and issues** (GitHub API). **V\***.
  - Fixed in 1.28.0 (08.10.2026):
    - #18249 "Setting parameter lcCooperativeHelpTime is now working";
    - #17717 new lcCooperativeMinSpeed and lcCooperativeHelpThreshold;
    - #17502 "Fixed inefficient cooperative speeds during lane changing for carFollowModel IDM". The GitHub milestone says "backlog", but the ChangeLog places the fix in 1.28.0.
  - Fixed in Git Main only: #17483 "lane-changing deadlock with carFollowModel IDM" (closed 2026-10-17, milestone 1.29.0).
  - Fixed in 1.27.1: #18042 "insufficient backward safety gaps with respect to minGap".
  - #5124 (open since 2019): the maintainer diagnosis is quoted correctly (speed advice ignored; IDM stops imprecisely by "about 8cm").
  - #12120: the advice was given by two maintainers. m-kro suggested raising lcCooperative / lcCooperativeSpeed and reducing density. namdre suggested heterogeneity (occasional gaps) and making some drivers "agressive (lcAssertive > 1)". He added that reproducing aggressive behaviour may need "ignoring collisions".
  - #5223 (open): lcAssertive > 1 "may lead to strong braking directly after the lane change".
  - **#18130 correction:** the maintainer says the teleport-only case applies "if neither vehicle is able to continue on it's current lane". He also says it "should come up very rarely", mainly after insertion into such a configuration or in short weaving sections. A ramp car standing next to a mainline car that *can* continue is therefore not this case; it is closer to #5124. "Structural SUMO deadlock" overstates it.
- **Safety, teleport, motorway and sublane docs.** **V**, page grep.
  - `--collision.mingap-factor 0` registers only physical contact. lcAssertive can cause rear-end collisions.
  - Teleporting: the "wrong lane" definition; the 300 s default; mutual blocking in weaving sections.
  - Motorways: acceleration lanes "somewhat longer than in reality"; zipper nodes at lane drops.
  - Sublane model: run time rises as lateral resolution gets finer.

## 2. What was not found (searchers' queries, kept as reported)

- RL mainline gap creation for ramp vehicles (no ramp signal) compared against a **tuned** rule-based cooperative merging controller, under paired seeds with CIs. Queries:
  - "reinforcement learning cooperative on-ramp merging compared against rule-based or optimization-based cooperative merging (FIFO, virtual vehicle mapping, MPC) benchmark results mixed traffic" (extended);
  - "deep reinforcement learning on-ramp merging comparison rule-based cooperative merging baseline virtual platoon SUMO time-to-collision post-encroachment time".
  - The verified rule-based opponents found are SUMO LC2013 defaults (Guo et al.), an untuned zipper (Irshayyid), or an unspecified "fixed rules" baseline with a reference mismatch (Trust-MARL).
- An RL merging paper that reports PET as a result. Trust-MARL collects it but does not report it. Query: "post-encroachment time safety evaluation reinforcement learning on-ramp merging connected automated vehicles SUMO surrogate safety measures".
- A paper that separates physical contacts from minGap intrusions (V211). No query was recorded.
- A paper with door-to-door delay including ramp queues as the primary metric. No query was recorded.
- Dense, multi-km SUMO near-capacity RL merging with dozens of CAV agents. The closest are Irshayyid (50 vehicles per episode, lane drop) and Yan et al. (3,000-4,500 veh/h).
- Mainline gap creation in which human LC2013/SL2015 lane-changers can take the opened gap, studied explicitly. Zhou et al. limit HDV lane changes. Non-RL work (Zhu-Tasic-Qu, Scarinci, FHWA) shows that gap theft happens and has to be prevented. Query: "reinforcement learning mainline autonomous vehicle yield to merging vehicle courtesy lane change on-ramp facilitate merge mixed traffic" (extended).
- A SUMO study of mainline gap creation with LC2013 that reports teleports or collisions in dense ramp queues, and any use of openGap for ramp merging. Queries:
  - "SUMO TraCI openGap cooperative merging on-ramp connected vehicles simulation";
  - "rule-based cooperative on-ramp merging SUMO connected vehicles gap creation lane change mainline yield evaluation mixed traffic penetration" (extended);
  - GitHub "openGap repo:eclipse-sumo/sumo".
- A mixed-traffic cooperative-merging study with merge safety as the primary outcome and delay as a guard, or a head-to-head between a non-learning cooperative merge and DRL on the same plant. No query was recorded beyond those above.
- A dedicated 2025-2026 survey of RL for on-ramp merging. Query: "survey 2025 learning-based on-ramp merging connected automated vehicles review reinforcement learning taxonomy" (extended).
- "Not found in this search" is not "does not exist". The search covered English-language web and arXiv sources, and several full texts were blocked (see the appendix).

## 3. Implications for the B design (built only on V / V\* sources)

1. **Where B could add something (not found in this search):** a tuned non-learning cooperative-merge opponent vs RL in SUMO, with paired seeds and bootstrap CIs, and safety as the primary outcome.
   - Every verified RL paper compares against no control, SUMO defaults, an untuned rule or other RL.
   - The strong non-learning results (Scarinci, Zhu-Tasic-Qu, FHWA) compare against no control too.
   - The wording must stay "not found in this search".
2. **Expect a small mobility effect.**
   - Yan et al.: +2.2 pp aggregate throughput; the gain is mostly in ramp waiting (37.0 → 29.3 s).
   - Sun & Yu: about 2-5 % in speed, about 0 in congestion.
   - Scarinci: no effect at ≥ 850 veh/h ramp flow, and the strategy "cannot increase the capacity".
   - This supports V74 (safety and smoothness as the claim, delay as a guard), with ramp queues inside the delay metric.
3. **Regime:** the gap-creation benefits found come from free flow up to near-breakdown, not from standing queues.
   - Scarinci: "operates only in the free-flow state".
   - Davis: full implementation is needed at heavy demand.
   - Zhu-Tasic-Qu: the largest gains are where the uncontrolled base breaks down from free flow.
   - So B's bind check (T0) belongs at demand just below breakdown. Its outcomes: breakdown onset and probability, late merges, low-TTC exposure, hard braking. It should not ask the controller to clear standing queues.
4. **Gap protection is required.** Gaps were lost or stolen in all three relevant studies:
   - Scarinci 2017 restricts near-side lane changes;
   - Zhu-Tasic-Qu reports failure without a one-sided prohibition;
   - FHWA: with a human follower "the identified gap no longer exists".

   This matches V195. B should block right changes into lane 0 for vehicles in the merge zone, and report stolen gaps as a diagnostic.
5. **Start upstream, in moving traffic, with explicit speed commands.**
   - Scarinci starts at least 1.8 km upstream with Δv = 10 km/h.
   - The SUMO docs warn that openGap's headway control under Euler fails at low speed.
   - So the oracle should map each ramp vehicle onto lane 0 as a virtual vehicle (Uno, Sakaguchi, Tsugawa 1999) and drive the CAV follower with setSpeed/slowDown, not with openGap or SUMO-internal cooperation.
6. **No signal, so timing has to come from prediction.** Scarinci and FHWA synchronise through a signal or an RSU release. B should pre-register an "offered vs accepted gap" diagnostic, so that a non-binding actuator shows up in T0.
7. **SUMO version risk** (1.27.1, IDM CAVs per V188):
   - the cooperative-speed imprecision (#17502) and the inability to set lcCooperativeHelpTime (#18249) are fixed only in 1.28.0;
   - the IDM deadlock (#17483) is fixed only in Git Main.

   Options: (a) disable SUMO-internal cooperation for CAVs and implement it explicitly over TraCI; (b) ask the author about a 1.28.0 cross-check for the bind check. V193-V197 may need a re-read with this in mind. A toolchain change needs an author decision.
8. **Penetration axis:**
   - FHWA: the cooperative merge is worse than none at 0 %; delay falls about 63 % already at 30 %; the throughput gain peaks at 70 %.
   - Jing et al.: conflict reductions mainly above 80 %.
   - Hou et al.: marginal benefit at low compliance.

   B should report the CAV share as an axis, not one point.
9. **Safety accounting.**
   - Keep the V211 split (physical contacts vs minGap intrusions; `--collision.mingap-factor 0` is the physical-only check).
   - Trust-MARL's 10.5 % "conflict" rate in all-HV SUMO shows how undefined "collision/conflict" counts mislead.
   - Each gate statistic needs a no-control-vs-no-control null on throw-away seeds before data (V244).
10. **Baseline ladder to tune on tuning seeds:**
    1. LC2013 defaults;
    2. raised lcCooperative / lcCooperativeSpeed for CAVs, with the version caveats;
    3. a CoopMA-style pooled gap without a signal (Δv, L, platoon size);
    4. an FHWA-style virtual platoon with a CAV follower;
    5. a near-side lane-change ban plus mainline moves to the left (the Park & Smith advisory and the Zhu-Tasic-Qu prohibition);
    6. a perfect-information oracle as headroom.

    Rule-based sequencing (Ding et al. 2020) and optimal control (Rios-Torres & Malikopoulos; Ntousakis et al.; Xiao & Cassandras) assume full automation, so they serve as upper-bound references only.
11. **Learning-side design:**
    - variable agent counts: parameter sharing plus attention over vehicle tokens with masks (Yan et al.), which fits PettingZoo parallel envs;
    - if a safety supervisor is used (Chen et al.; SECRM-2D), both the RL and the classical arms must share it, or the comparison is confounded;
    - Chen et al.'s large win over MPC is on collisions, the part the supervisor handles. Its speed gain over MAPPO is small (22.73 vs 22.41 m/s).
12. **For A (side note):**
    - DIACC varies the capacity reduction (25 % vs 50 %), and the speed gap grows (19.04 vs 17.05 → 17.60 vs 14.10). These are geometric reductions, not a behavioural capacity drop, and the baseline row identity is [VERIFY].
    - Vinitsky 2018's merge compares RL only with Human, so any reproduction for A needs a tuned non-learning arm (V153).

## Appendix: dropped, unidentified or unverified (not used above)

- **NF (likely fabricated): none.**
- **Unidentified (no title located):** Cai et al., ITSC 2024 graph RL; ScienceDirect S3050860625000079 (MARL cooperative merging, 2025); ScienceDirect S1000934525002123 (RL plus analytic optimal control, 2025); MDPI Future Internet 13(5):123 (2021, SUMO plus Python collaborative merging); TransAID D3.1 (elib.dlr.de/132647, found but not read). The Z-Merge baselines "Liu et al. 2024 (lane change)" and "Zhu et al. 2024 (gap adjustment)" are cited but not identified; the latter may or may not be the Zhu-Wang-Tasic-Qu T-ITS paper [VERIFY].
- **Unverified, low relevance:** the late-merge / zipper work-zone summaries (CDOT late-merge PDF; Iowa InTrans TPF-5(438), publications.iowa.gov/52208, which returned HTTP 403; TRR 1911/1948 records). These are search summaries only, with numbers unchecked; reopen them before any use in A's lane-drop node.
- **Unverified details inside otherwise verified sources:**
  - Chen et al.: agent counts per mode and Fig. 15;
  - Scarinci 2015: the alignment of the p-value table;
  - Xiao & Cassandras: the FIFO and baseline remarks;
  - the FHWA simulator;
  - the CoopSECRM2D baselines and numbers;
  - the Irshayyid review's contents beyond the abstract;
  - the RLPG venue;
  - the lcCooperativeMinSpeed default;
  - `laneChangeModel.<ATTR>` setParameter.
