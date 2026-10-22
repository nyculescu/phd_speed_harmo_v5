# Recent PhD theses on speed harmonization / VSL / freeway speed control with RL (v0, 2026-10-21)

**Method.**
- OpenAlex API, type `dissertation`, from 2018. Two passes: phrase search on title and abstract (36 queries), then relevance search (17 queries × 50 results). 564 unique records, 55 passed a keyword screen, screened by hand.
- Targeted web searches for known groups: Berkeley, Zagreb, UNC Charlotte, Vanderbilt, ENPC.
- Each listed thesis was checked against its repository or official record (degree, year, supervisor, topic, method).
- Scripts and raw hits: `~/work/phd/v5b1_runs/lit_phd_theses_2026-10-21/` (sweep.py, sweep2.py, candidates*.json).

**Basis key.** [REC] = read on the repository or official record page (abstract level). [SNIP] = search-engine summary of the record only. No full text was read in this pass, so methods details beyond the abstract are not verified.

**Coverage limits.**
- Fewer than 20 qualifying theses were confirmed (9 confirmed, 4 to confirm).
- Chinese, Korean and other national thesis databases (CNKI, RISS) and ProQuest were not searched; they are likely to hold more.
- A ProQuest export through the author's library would close most of this gap.

## A. Qualifying and confirmed (PhD, 2018+, RL core, freeway speed / VSL / CAV speed control)

| # | Year | Author, title | University, supervisor | Topic and method (from the record) | Link | Basis |
|---|---|---|---|---|---|---|
| 1 | 2025 | Nathan Lichtlé, *Deep Reinforcement Learning for Autonomous Vehicle Traffic Control and Stabilization: From Simulation to a 100-Vehicle Highway Field Deployment* | UC Berkeley EECS (BibTeX @phdthesis), A. Bayen; joint doctorate with ENPC/CERMICS (thesis id 2024ENPC0030, with A. Hayat) | Multi-agent DRL for decentralized bottleneck control; RL wave-smoothing cruise controllers trained on highway trajectory data; Nocturne simulator; deployed on 100 CAVs in rush-hour traffic on I-24 (Tennessee); "measurable traffic smoothing" (no numbers on the page) | https://www2.eecs.berkeley.edu/Pubs/TechRpts/2025/31905.html | [REC] |
| 2 | 2025 | Tianyu Shi, *Cooperative Multi-Agent Reinforcement Learning Framework for Concurrent Microscopic Safe, Efficient, and Comfortable Autonomous Driving and Macroscopic Congestion Management on Freeways* | University of Toronto, B. Abdulhai | RL car-following, lane change and merging models (SECRM family) for CAVs, extended to decentralized MARL linked to bottleneck flow and speed harmonization; synthetic networks and a QEW freeway model; algorithm not named on the page | https://utoronto.scholaris.ca/handle/1807/150500 | [REC] |
| 3 | 2024 | Chengying Hua, *Dynamic Speed Harmonization and Synergistic Performance Evaluation in a Connected and Automated Vehicle Environment* | UNC Charlotte (Infrastructure and Environmental Systems), W. Fan | DRL coordinated speed control of CAVs in mixed traffic (VSL / dynamic speed harmonization through CAVs, which comply fully); evaluated across market penetration rates | https://graduateschool.charlotte.edu/dynamic-speed-harmonization-and-synergistic-performance-evaluation-connected-and-automated-vehicle/ ; PDF https://ninercommons.charlotte.edu/record/2748/files/hua_uncc_0694D_13903.pdf | [REC] |
| 4 | 2023 | Krešimir Kušić, *Increasing Motorway Operational Capacity by Dynamic Adaptation of Variable Speed Limit Zones Based on Cooperative Learning Agents* | University of Zagreb, Faculty of Transport and Traffic Sciences; M. Šoštarić, E. Ivanjko | Distributed spatial-temporal multi-agent VSL based on W-learning; adapts length and position of VSL zones on urban motorways (related paper: Kušić et al. 2021, *Mathematics*, doi 10.3390/math9233081) | https://www.fpz.unizg.hr/zits/?p=2462 ; repository fpz:3193 (blocked to our fetcher) | [REC] defense page + [SNIP] repository abstract |
| 5 | 2023 | Lina Elmorshedy, *Dynamic Autonomous Driving Headway Optimization with Deep Reinforcement Learning for Freeway Congestion Management and Control* | University of Toronto, B. Abdulhai | DRL sets the ACC time headway per freeway section and control cycle; single- and multi-bottleneck networks, global and multi-agent; up to 57 % / 46 % less delay than fixed (non-dynamic) headways | https://utoronto.scholaris.ca/handle/1807/138479 | [REC] |
| 6 | 2022 | Abdul Rahman Kreidieh, *Efficient Learning Methods for Mixed Autonomy Traffic* | UC Berkeley, Civil and Environmental Engineering; A. Bayen (chair) | Learning methods for AV control in mixed autonomy (Flow line); details not verified (PDF too large for our fetcher) | https://bayen.berkeley.edu/sites/default/files/aboudy_dissertation.pdf | [SNIP] |
| 7 | 2019 | Reza Vatani Nezafat, *Deep Reinforcement Learning Approach for Lagrangian Control: Improving Freeway Bottleneck Throughput Via Variable Speed Limit* | Old Dominion University, M. Cetin | A3C agents set upstream VSL delivered to connected vehicles at three bottlenecks (sag curve, 3→2 lane reduction, on-ramp with capacity drop); gains even at low CV penetration; outperforms feedback-control solutions | https://digitalcommons.odu.edu/cee_etds/84 (doi 10.25777/dc8z-c232) | [REC] |
| 8 | 2018 | Thorsten Schmidt-Dumont, *Reinforcement Learning for the Control of Traffic Flow on Highways* | Stellenbosch University (Industrial Engineering), J. H. van Vuuren, M. Bruwer | Decentralised RL for joint ramp metering and VSL; RL-instructed AVs on an on-ramp; benchmark microsimulation with statistical comparisons, then N1 outbound Cape Town with real flow data | http://hdl.handle.net/10019.1/104851 | [REC] |
| 9 | 2018 | Cathy Wu, *Learning and Optimization for Mixed Autonomy Systems: A Mobility Context* | UC Berkeley EECS (UCB/EECS-2018-132), A. Bayen | Deep RL as a framework for mixed autonomy; a small share of automated vehicles raises system velocity; variance reduction for policy gradients; introduces Flow | https://www2.eecs.berkeley.edu/Pubs/TechRpts/2018/EECS-2018-132.html | [REC] |

## B. To confirm (on-topic and RL, but degree or record not confirmed)

| Year | Author, title | Open point | Link |
|---|---|---|---|
| 2026 | Amir Hossein Karbasi, *Integrated Traffic and Infrastructure Management Using Deep Reinforcement Learning and Automated Vehicles* (McMaster) | DRL truck platooning and freeway-bottleneck / signal control; degree level not confirmed (repository blocked our fetcher) | https://hdl.handle.net/11375/33857 |
| 2022 | Eugene Vinitsky, *From sim-to-real: learning and deploying autonomous vehicle controllers that improve transportation metrics* (UC Berkeley, A. Bayen) | Title and year only from the Math Genealogy Project; no official record found | https://mathgenealogy.com/id.php?id=286363 |
| 2019 | Weiyi Zhou, *A Q-Learning Based Integrated Variable Speed Limit and Hard Shoulder Running Control to Reduce Travel Time at Freeway Bottleneck* (University of Maryland, L. Zhang) | Record type "Thesis", degree level not stated; Q-learning VSL + HSR on I-270 (DTA model), beats feedback-based VSL | https://drum.lib.umd.edu/handle/1903/25204 |
| 2018 | Mofan Zhou, *Modeling the Impact of Connected and Automated Vehicles on Highway Operations* (Griffith) | RL car-following controllers for CAVs to dampen stop-and-go oscillations (from the OpenAlex abstract); degree not confirmed (repository returned 403) | http://hdl.handle.net/10072/378093 |

## C. Related, not qualifying (read for context)

- **Julian Isser (ETH Zurich, 2026), replication study:** checks the claim of Hou et al. that RL (Ape-X DQN, PPO, A3C) beats no metering, fixed-time and ALINEA for freeway ramp metering. Thesis type not confirmed; ramp metering only. **Directly relevant to fair-baseline questions; read it.** https://doi.org/10.3929/ethz-c-000801167
- **Saeed Mansouryar (Sapienza, PhD 2026):** freeway VSL is *rule-based*, validated on about a year of Padua-Mestre field data (up to 19 % less travel time under congestion). It is compared in SUMO with a DRL jam-shrinking controller; DRL is used for urban signals. https://iris.uniroma1.it/handle/11573/1758911
- **Mladen Miletić (Zagreb):** doctoral thesis *topic* defended on 9 Jan 2024 (spatial-temporal VSL with congestion detection and ML in a CAV environment); related Q-learning paper in *Machines* 2023; the thesis itself was not found.
- **Prajwal Bindu Vinod (TU Delft, MSc 2025):** SAC for combined ramp metering and VSL in SUMO. A master's thesis.
- **Not RL or not confirmed as RL:** Amirreza Kandiri (UCD 2025, VSL optimisation framework; RL not stated); Zeyu Mu (UVA 2026, CAV platooning; RL not stated); Aditya Maheshwari (Carleton 2020, RL for mixed-autonomy highways; degree not checked); Daniel Lazar (Berkeley 2021, mostly theory of mixed-autonomy routing).
- **Key non-thesis work:**
  - the Vanderbilt MARVEL MARL-VSL line, with I-24 field deployment from March 2024 (arXiv 2310.12359, 2407.08021, 2503.01017);
  - Vinitsky et al. 2023 (ACM, doi 10.1145/3582576), MARL AVs on the Bay Bridge 4→2→1 bottleneck: +20 % throughput at 5 % penetration, +33 % at 40 %;
  - Flow (Wu et al., IEEE T-RO 2021).

## D. Synthesis (what the records show; full texts not read)

1. **Two families.**
   - (a) Infrastructure VSL / ramp metering learned by RL: Vatani Nezafat, Schmidt-Dumont, Kušić, W. Zhou.
   - (b) Lagrangian control: a share of CAVs learns speed or headway policies that smooth waves or raise bottleneck throughput (Wu, Kreidieh, Lichtlé, Hua, Elmorshedy, Shi).

   Since about 2022 the trend is family (b) and field deployment (I-24: Lichtlé; MARVEL papers).
2. **Baselines.**
   - The records mostly compare with no control, fixed settings or "feedback control". Two claim to beat feedback VSL (Vatani Nezafat, W. Zhou).
   - Whether the feedback baselines were tuned cannot be seen at abstract level. Only the ETH replication (Isser) explicitly tests RL against ALINEA.
3. **Capacity drop and plant realism.**
   - No record states that the simulated capacity drop was calibrated against field data.
   - The Berkeley line, including Vinitsky et al. 2023, uses the Bay Bridge 4→2→1 bottleneck. That is the same BN4 geometry for which our calibration (V139) measured a 50-54 % drop with the Flow IDM parameters, against field values of 2-11 %.
   - **This is the clearest gap our work can fill.** Gains reported on that plant may depend on an unrealistic drop. That is to be checked in the full texts before any claim.
4. **Negative or null results** are rare in the records. Isser's replication study is the only explicit test of an earlier positive RL claim found here.
5. **Open gaps seen:**
   - plant-realism checks (capacity drop, discharge);
   - pre-registered evaluation;
   - tuned classical opponents;
   - detection errors;
   - a day mix of incident and normal days.

   These match our P1c work (V132-V149).

## E. Next steps (proposed)

1. Read the full texts of A1-A9 and of Isser (C), recording simulator, capacity-drop treatment, baselines and their tuning, number of seeds, and statistics.
2. Confirm the four theses in section B.
3. Optionally, a ProQuest export (RIS/CSV) from the author's library account, for completeness, plus CNKI for Chinese theses.
