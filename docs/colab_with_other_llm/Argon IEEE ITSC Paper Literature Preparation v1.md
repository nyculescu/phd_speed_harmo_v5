I have read the full text of **Papageorgiou et al. (2008)** and updated your reference table, BibTeX, and draft sections accordingly. I also dropped **Haboian (1995)** (previously `#4`) as requested.

Notably, reading the full text of **Papageorgiou et al. (2008)** solves the loss of Haboian (1995) and provides direct, full-text-verified support for several of your paper's exact design choices:

1. **Real-world mainline signal precedent:** Section 2.5 and Section 3.1 explicitly cite the traffic lights installed at the **San Francisco–Oakland Bay Bridge** toll plaza, and Section 5 notes that traffic control at **tunnel entrances** has been practiced in the field.


2. **All-lane mainline signal metering at a lane-drop bottleneck:** Section 4 models a 3-to-1 work-zone lane drop with traffic lights across all entering lanes 50 m upstream of the merge area, with a constant green phase (4 s), variable red phase, minimum red constraint (2 s), and ALINEA occupancy feedback ($T = 30\text{ s}$). They explicitly justify metering **all** mainstream lanes rather than only the dropping lanes for equity and safety (preventing unbalanced queues and last-minute lane-changing).


3. **Red-light violations and integral feedback:** Section 2.7.1 explicitly notes that the integral-feedback structure of ALINEA guarantees stationary regulation accuracy even when there are implementation errors such as **red-light violations**—which directly supports your finding that 10 % / 30 % red-light runners leave your confirmed result intact!


4. **Microsimulation noise and occupancy spikes:** In Section 4.2 (Figs. 10–11), they observe that across 10 AIMSUN replications, random microscopic merging conflicts cause sharp occupancy spikes (up to 30 %) and large run-to-run variance in Average Vehicle Delay (AVD), such that some controlled replications perform worse than the best uncontrolled replication. This directly motivates your paired-seed, block-bootstrap, and cross-fitting methodology.


5. **Online critical-occupancy estimators:** Section 2.7.1 explicitly cites **Smaragdis et al. (2004)** and **Kosmatopoulos et al. (2006)** for real-time estimation of $\hat{o} = o_{\text{cr}}$.



---

### 1. Updated Verified Reference Table (Single Markdown Block)

*(Note: Haboian 1995 has been removed; keys are renumbered `[1]`–`[20]`, and Reference `[2]` is upgraded to **Full text**).*

| Key | IEEE Citation | DOI / URL | Status | Read Status | Category | Relation to Our Paper |
| --- | --- | --- | --- | --- | --- | --- |
| **[1]** | A. Tympakianaki, A. Spiliopoulou, A. Kouvelas, I. Papamichail, and M. Papageorgiou, "Real-time merging traffic control for throughput maximization at motorway work zones," *Transp. Res. Part C: Emerg. Technol.*, vol. 44, pp. 242–252, Jul. 2014. | `10.1016/j.trc.2014.04.006` | **VERIFIED** | Abstract & bibliographic record | Mainline metering | Closest prior work; establishes mainstream green-red signals with ALINEA/PI-ALINEA feedback at lane-drop bottlenecks as our L0 baseline. |
| **[2]** | M. Papageorgiou, I. Papamichail, A. D. Spiliopoulou, and A. F. Lentzakis, "Real-time merging traffic control with applications to toll plaza and work zone management," *Transp. Res. Part C: Emerg. Technol.*, vol. 16, no. 5, pp. 535–553, Oct. 2008.

 | `10.1016/j.trc.2007.11.002`<br> | **VERIFIED** | **Full text (PDF provided)** | Mainline metering | Foundational method source; establishes all-lane mainstream traffic signals upstream of a lane-drop merge with ALINEA feedback, minimum red, anti-windup bounds, robustness to red-light violations, and stochastic replication variance.

 |
| **[3]** | A. D. Spiliopoulou, I. Papamichail, and M. Papageorgiou, "Toll plaza merging traffic control for throughput maximization," *J. Transp. Eng.*, vol. 136, no. 1, pp. 67–76, Jan. 2010. | `10.1061/(ASCE)0733-947X(2010)136:1(67)` | **VERIFIED** | Abstract & bibliographic record | Mainline metering | Supports our physical setup by demonstrating that mainstream signal metering upstream of a multi-lane merge bottleneck prevents capacity drop. |
| **[4]** | D. K. Hale, J. Ma, A. Ghiasi, P. Volet, B. Cesme, A. Kondyli, B. Schroeder *et al.*, *Alternative Designs to Alleviate Freeway Bottlenecks at Merging, Diverging, and Weaving Areas*, Federal Highway Administration, Washington, DC, USA, Rep. FHWA-HRT-20-008, May 2020. | [FHWA PDF](https://www.fhwa.dot.gov/publications/research/operations/20008/20008.pdf) | **VERIFIED** | Full text (exec. summary & TOC) | Mainline metering | Agency report confirming that mainline metering (dynamic signal control) yields operational benefits at freeway bottlenecks in microsimulation. |
| **[5]** | A. Ghiasi, D. Hale, J. Bared, A. Kondyli, and J. Ma, "A dynamic signal control approach for integrated ramp and mainline metering," in *Proc. 21st Int. Conf. Intell. Transp. Syst. (ITSC)*, Maui, HI, USA, Nov. 2018, pp. 2892–2898. | `10.1109/ITSC.2018.8569567` | **VERIFIED** | Abstract & citing methods | Mainline metering | Contrasts with our isolated mainline bottleneck by combining ramp and partial mainline signal metering at a freeway merge. |
| **[6]** | R. C. Carlson, I. Papamichail, M. Papageorgiou, and A. Messmer, "Optimal mainstream traffic flow control of large-scale motorway networks," *Transp. Res. Part C: Emerg. Technol.*, vol. 18, no. 2, pp. 193–212, Apr. 2010. | `10.1016/j.trc.2009.05.014` | **VERIFIED** | Abstract & bibliographic record | Mainline metering | Establishes the paradigm of Mainstream Traffic Flow Control (MTFC) to regulate flow upstream of a bottleneck. |
| **[7]** | R. C. Carlson, I. Papamichail, and M. Papageorgiou, "Local feedback-based mainstream traffic flow control on motorways using variable speed limits," *IEEE Trans. Intell. Transp. Syst.*, vol. 12, no. 4, pp. 1261–1276, Dec. 2011. | `10.1109/TITS.2011.2156792` | **VERIFIED** | Abstract & bibliographic record | Feedback control | Method source showing that local feedback MTFC achieves near-optimal throughput without network-wide optimization. |
| **[8]** | Y. Wang, E. B. Kosmatopoulos, M. Papageorgiou, and I. Papamichail, "Local ramp metering in the presence of a distant downstream bottleneck: Theoretical analysis and simulation study," *IEEE Trans. Intell. Transp. Syst.*, vol. 15, no. 5, pp. 2024–2039, Oct. 2014. | `10.1109/TITS.2014.2307884` | **CORRECTED** (2nd author is E. B. Kosmatopoulos) | Abstract & bibliographic record | Feedback control | Primary method source for the PI-ALINEA control structure used in our L0 always-on baseline. |
| **[9]** | M. Papageorgiou, H. Hadj-Salem, and J.-M. Blosseville, "ALINEA: A local feedback control law for on-ramp metering," *Transp. Res. Rec.*, no. 1320, pp. 58–64, 1991.

 | [SWOV Archive PDF](https://swov.nl/sites/default/files/bestanden/downloads/I%20852022.pdf) | **VERIFIED** | Full text | Feedback control | Method source for the integral feedback law in our L0 controller ladder. |
| **[10]** | J.-B. Sheu and M.-S. Chang, "Stochastic optimal-control approach to automatic incident-responsive coordinated ramp control," *IEEE Trans. Intell. Transp. Syst.*, vol. 8, no. 2, pp. 359–367, Jun. 2007. | `10.1109/TITS.2007.893327` | **VERIFIED** | Abstract & bibliographic record | Ramp metering under incidents | Contrasts with our work by designing incident-responsive control for on-ramps rather than mainline signals, without decomposing the value of incident information levels. |
| **[11]** | A. Dabiri and B. Kulcsár, "Incident parameter scheduled freeway traffic control," *IFAC Proc. Volumes*, vol. 47, no. 3, pp. 11338–11343, Aug. 2014. | `10.3182/20140824-6-za-1003.02383` | **VERIFIED** | Bibliographic record & citing text | Ramp metering under incidents | Supports our L2/L3 framing by scheduling controller parameters on incident state, though applied to macroscopic ramp control rather than microsimulated mainline signals. |
| **[12]** | Y. Wu, D. Yu, W. Yu, and T. Qin, "Double-layer ramp-metering model for incident congestion on expressway," *J. Traffic Transp. Eng. (Engl. Ed.)*, vol. 1, no. 2, pp. 129–136, Apr. 2014. | `10.1016/S2095-7564(15)30097-0` | **VERIFIED** | Bibliographic record & citing excerpts | Ramp metering under incidents | Contrasts with our work by proposing incident-triggered on-ramp metering assuming known incident characteristics. |
| **[13]** | C. Cameron, H. H. Hoos, and K. Leyton-Brown, "Bias in algorithm portfolio performance evaluation," in *Proc. 25th Int. Joint Conf. Artif. Intell. (IJCAI)*, New York, NY, USA, Jul. 2016, pp. 712–719. | [IJCAI Abstract](https://www.ijcai.org/Abstract/16/107) | **VERIFIED** | Full text | Selection bias | Directly supports our hindsight oracle decomposition by proving that a per-instance Virtual Best Solver (in-sample oracle) is optimistically biased when evaluated on noisy runs. |
| **[14]** | H. V. Hasselt, "Double Q-learning," in *Advances in Neural Information Processing Systems (NeurIPS)*, vol. 23, 2010, pp. 2613–2621. | [NeurIPS Paper](https://ir.cwi.nl/pub/16889) | **VERIFIED** | Full text | Selection bias | Method source for decoupling action selection from value evaluation via sample splitting to eliminate maximization bias. |
| **[15]** | J. E. Smith and R. L. Winkler, "The optimizer's curse: Skepticism and postdecision surprise in decision analysis," *Manage. Sci.*, vol. 52, no. 3, pp. 311–322, Mar. 2006. | `10.1287/mnsc.1050.0451` | **VERIFIED** | Abstract & bibliographic record | Selection bias | Theoretical foundation for the "winner's/optimizer's curse" explaining why selecting the best control plan in-sample inflates expected gains. |
| **[16]** | P. A. Lopez, M. Behrisch, L. Bieker-Walz, J. Erdmann, Y.-P. Flötteröd, R. Hilbrich, L. Lücken, J. Rummel, P. Wagner, and E. Wießner, "Microscopic traffic simulation using SUMO," in *Proc. 21st Int. Conf. Intell. Transp. Syst. (ITSC)*, Maui, HI, USA, Nov. 2018, pp. 2575–2582. | `10.1109/ITSC.2018.8569938` | **VERIFIED** | Full text | Simulation methodology | Standard reference for the SUMO microsimulator used in our experiments. |
| **[17]** | Traffic Operations and Safety (TOPS) Laboratory, *Evaluation of Ramp Metering on Madison Beltline*, Univ. Wisconsin–Madison, Madison, WI, USA, Tech. Rep. for WisDOT, Jan. 2005. | [TOPS Lab Portal](https://topslab.wisc.edu/research/tsmo/ramp-metering/) | **VERIFIED** | Portal metadata & citing reports | Compliance | Provides empirical field context on driver compliance and signal violations at metering installations. |
| **[18]** | C. Sun, P. Edara, and Z. Zhu, "Evaluation of temporary ramp metering for work zones," *Transp. Res. Rec.*, vol. 2337, no. 1, pp. 17–24, 2013. | `10.3141/2337-03` | **CORRECTED** (Author order is Sun, Edara, Zhu) | Abstract & report summary | Compliance | Empirical basis for our red-light runner sensitivity analysis (10 % and 30 % violation rates) at temporary/work-zone metering signals. |
| **[19]** | J. R. D. Frejo and B. De Schutter, "Logic-based traffic flow control for ramp metering and variable speed limits—Part 2: Simulation and comparison," *IEEE Trans. Intell. Transp. Syst.*, vol. 22, no. 5, pp. 2658–2668, May 2021. | `10.1109/TITS.2020.2973732` | **CORRECTED** (Part 2 has the PI-ALINEA + MTFC benchmark) | Full text (Part 1) & Abstract (Part 2) | Feedback control | Demonstrates that PI-ALINEA and MTFC remain standard, competitive benchmarks that can degrade when calibration conditions shift. |
| **[20]** | E. Smaragdis, M. Papageorgiou, and E. Kosmatopoulos, "A flow-maximizing adaptive local ramp metering strategy," *Transp. Res. Part B: Methodol.*, vol. 38, no. 3, pp. 251–270, Mar. 2004.

 | `10.1016/S0191-2615(03)00012-2` | **VERIFIED** (Explicitly cited in Papageorgiou et al. 2008 for online $\hat{o}$ estimation)

 | Bibliographic record & citing text in [2]

 | Feedback control | Method source for online critical-occupancy set-point estimation (AD-ALINEA) included in our L0 controller family.

 |

---

### 2. Updated Introduction & Background Drafts (Incorporating Full-Text Details from [2])

#### Introduction Draft (~450 words, IEEE Style)

Non-recurrent disturbances—such as lane blockages, vehicle breakdowns, and localized slowdowns—account for a large share of freeway delay and reduce bottleneck discharge rates through the congestion-induced capacity drop [2]. While on-ramp metering is widely deployed to regulate merging demand, it cannot control traffic already on the freeway mainstream when an incident occurs far from an entrance ramp or when mainstream demand alone exceeds the remaining bottleneck capacity [2]. In high-demand facilities where a larger number of lanes must merge into fewer lanes—such as bridge toll plazas, tunnels, and work-zone lane drops—**mainline (mainstream) metering** places traffic signals directly across all entering mainstream lanes upstream of the bottleneck to regulate inflow and prevent capacity drop [1]–[4]. Real-world traffic light installations at the San Francisco–Oakland Bay Bridge toll plaza and at tunnel entrances have demonstrated the feasibility of controlling mainstream flows [2], and microscopic simulation studies have extended mainstream signal control to freeway merges and work-zone lane drops [1], [2], [5].

For stationary bottlenecks with fixed geometry, closed-loop feedback controllers borrowed from ramp metering have proven highly effective [2]. Integral regulators such as ALINEA [2], [9] and proportional-integral extensions such as PI-ALINEA [1], [8] maintain downstream occupancy near its critical threshold without requiring upstream demand measurements, while automatically rejecting implementation disturbances such as red-light violations [2]. These local feedback laws have been successfully applied both to Mainstream Traffic Flow Control (MTFC) via variable speed limits [6], [7], [19] and to all-lane mainstream traffic signals at work zones and toll plazas [1]–[3]. Furthermore, adaptive schemes such as AD-ALINEA estimate the critical occupancy set point online [2], [20]. In parallel, the incident-management literature has developed incident-responsive ramp controllers that switch plans or schedule parameters when a non-recurring event occurs [10]–[12].

However, deploying an incident-responsive architecture requires real-time incident detection and classification, which introduce latency. A practical engineering question remains open: **how much incident information does a mainline metering signal actually need beyond strong always-on feedback?** Specifically, it is unclear whether binary incident presence is sufficient, whether classifying the incident type adds meaningful benefits, and how close these practical tiers come to the theoretical headroom of full per-incident hindsight.

To answer this question, we evaluate a four-level incident information ladder at a microsimulated four-to-one freeway bottleneck in SUMO [16] subject to stochastic non-recurring incidents (bottleneck slowdowns and single-lane crawls). We compare: (L0) always-on control without incident information (fixed rate, integral feedback [2], [9], PI-ALINEA [8], and online set-point adaptation [20]); (L1) binary incident presence switching; (L2) incident-type plan switching; and (L3) per-incident hindsight oracles. Because selecting the best control plan per incident realization on noisy microsimulation runs inflates oracle performance via the optimizer's curse [13], [15], we bracket the hindsight ceiling using both an in-sample oracle and a cross-fitted oracle [14].

The main contributions of this paper are:

* **An incident-information ladder decomposition for mainline signal metering:** We isolate the marginal value of binary incident presence (L1) and incident-type classification (L2) relative to strong always-on feedback baselines (L0) across multiple demand and incident regimes, confirming a 16.2 % gain for incident-type knowledge on out-of-sample simulation seeds in one operating regime while showing where binary presence alone yields less than 10 % improvement.
* **Honest headroom bracketing under simulation noise:** We address selection bias in microsimulation benchmarking by bounding the per-incident hindsight ceiling (L3) between an optimistic in-sample oracle and an out-of-sample cross-fitted oracle using pre-registered protocols and paired block-bootstrap confidence intervals.
* **Operational sensitivity to detection delay and signal compliance:** We quantify how realistic automatic incident detection delays and driver red-light running (10 % and 30 % violation rates [17], [18]) affect the gains of incident-aware mainline metering.

---

#### Background Section Draft (~400 words, IEEE Style)

##### A. Mainline Signal Metering and Feedback Controllers

Mainline metering regulates traffic directly on the freeway mainstream using traffic signals across all entering lanes upstream of a merge or bottleneck [1], [2]. Metering all mainstream lanes equally—rather than only the dropping lanes—prevents unbalanced upstream queues and unsafe last-minute lane changes toward un-metered lanes [2]. Positioned upstream of the merge area so vehicles can accelerate before merging, the signals enforce a target total flow $q(k)$ via green-amber-red cycles subject to a minimum red phase and anti-windup bounds $[q_{\min}, q_{\max}]$ [2]. Under Level 0 (L0, no explicit incident feed), mainline signals can operate at a fixed rate or via closed-loop feedback. Classical ALINEA [2], [9] uses integral (I) feedback on occupancy measured just upstream of where merge congestion first forms [2], whereas PI-ALINEA [8] adds a proportional term that accelerates recovery when the bottleneck is located further downstream of the signal [1], [8]. Because an incident alters bottleneck capacity and critical occupancy, fixed set points may become suboptimal [19]; online set-point estimators (AD-ALINEA style [2], [20]) attempt to track shifts in critical occupancy using local measurements. In contrast, incident-scheduled controllers (L1 and L2) explicitly switch control plans or parameters upon receiving an external incident flag [11].

##### B. Incident Detection Timing and Driver Compliance

The practical utility of L1 and L2 control depends on two field imperfections: detection latency and driver non-compliance. Automatic incident detection must balance detection delay against false alarms; because congestion builds rapidly when arrival demand exceeds bottleneck capacity [2], detection delays allow capacity drop and initial occupancy overshooting to set in before the mainline signal switches plans [2]. Furthermore, drivers encountering temporary or work-zone metering signals exhibit measurable red-light violation rates [17], [18]. Notably, theoretical analysis of integral feedback shows that I-type regulators automatically reject steady-state implementation errors caused by red-light violations [2], a property we test microscopically at 10 % and 30 % violation rates.

##### C. Honest Headroom in Stochastic Microsimulation

Even under identical average demand, microscopic traffic simulations of merge bottlenecks exhibit large run-to-run variance due to random vehicle merging conflicts and sharp, short-lived occupancy spikes [2]. In SUMO [16], changing a signal plan alters vehicle trajectories and desynchronizes common random numbers across paired seeds. When a hindsight oracle (L3) selects the best-performing plan on the same noisy simulation run used to evaluate its performance, it exploits lucky realization-specific fluctuations—a bias known as the *optimizer's curse* [15] or *Virtual Best Solver bias* [13]. Decoupling plan selection from evaluation across independent seed splits via cross-fitting [14] removes this upward bias and provides a conservative lower bound on the hindsight ceiling.

---

Whenever you have additional PDFs or Web of Science exports ready, upload or paste them and I will verify and integrate them immediately.