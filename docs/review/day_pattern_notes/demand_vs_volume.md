# Demand vs counted volume under freeway oversaturation, and recovering true demand

Research notes, 2026-10-04. Scope: freeways, ramps and freeway corridors. Arterial work is included only where its method carries over, and is labelled as arterial.

How sources were read (applies throughout):
- "[VERIFY: extracted]" means the page was fetched and machine-summarised, not read line by line by me; check quotes against the original before citing them in the thesis.
- "[VERIFY: abstract only]" and "[VERIFY: search snippet only]" mean exactly that.
- "[SAGE]" marks Transportation Research Record (TRR) items, which the author cannot access. Older TRR issues (for example TRR 1320, 1991) are also hosted openly on onlinepubs.trb.org, and that open copy is used where it exists.
- Only one primary document was read in substantial part from its text: Cetin et al. (2021, VTRC 22-R19), which is arterial. I also read the abstract and the background and capacity-drop sections of Hall and Agyemang-Duah (1991).

---

## Q1. What does the HCM (and FHWA guidance built on it) say about demand vs volume and estimating demand under oversaturation?

### Takeaway
"Demand" (the flow that wants to pass) and "volume served" (the counted flow, which can never exceed capacity) differ at an active bottleneck and at every segment downstream of it. HCM freeway-facility analysis expects demand, not counts, as input. It also expects the study window to start and end undersaturated (d/c < 1 in the first and last intervals). FHWA's microsimulation guidance tells analysts to make sure a count measures demand and not capacity, and to count from before queue onset until after the queue has fully cleared. I could not access the HCM 6th/7th edition text itself, so the exact chapter wording is unverified (see Gaps).

### Cited Findings
- **Demand vs volume served.** McTrans (University of Florida, the HCS software centre) defines demand as the traffic that wishes to travel through a segment, and volume served as what is actually accommodated, which never exceeds capacity. "An active bottleneck has a demand greater than capacity, but the actual volume served in this location is metered by its capacity." Downstream segments therefore see a volume lower than the real demand. — [Sasahara, F. (2021) *Analyzing Active and Hidden Bottlenecks*, McTrans Center, 1 Apr 2021](https://mctrans.ce.ufl.edu/analyzing-active-and-hidden-bottlenecks/) [VERIFY: extracted]
- **Hidden bottlenecks and the size of the gap (worked HCS example).** Demand entering the facility is 7,500 pc/h. An upstream bottleneck has capacity 6,750 pc/h, applies a 7 % queue-discharge capacity drop, and serves 6,285 pc/h. A downstream segment has capacity 7,200 pc/h. Its d/c on true demand is 1.04, yet it looks uncongested on served volume. Here counts downstream understate demand by about 16 %: (7,500 − 6,285)/7,500, my arithmetic. The article concludes: "For truly removing congestion, all active and hidden bottlenecks may need to be addressed." — [Sasahara (2021)](https://mctrans.ce.ufl.edu/analyzing-active-and-hidden-bottlenecks/) [VERIFY: extracted]
- **Two regimes in the HCM freeway-facilities method.** It has an "undersaturated" method, used when all segments are below capacity, and an "oversaturated" method, used when at least one segment is over capacity or at LOS F. The FHWA document applying it to part-time shoulder use uses the oversaturated method because "demand is likely to exceed capacity and result in a breakdown". — [FHWA Office of Operations, *Decision Support Framework and Parameters for Dynamic Part-Time Shoulder Use*, FHWA-HOP-19-029, Appendix C](https://ops.fhwa.dot.gov/publications/fhwahop19029/appc.htm) [VERIFY: extracted]
- **Analysis-window requirement.** "The completeness of the analysis will be limited if freeway segments in the first time interval, the last time interval, and the first freeway segment do not all have demand-to-capacity ratios less than 1.00." The method "is limited to the extent that it can accommodate demand in excess of capacity. The procedures address only local oversaturated flow situations, not systemwide oversaturated flow conditions." This text describes the HCM 2000-era freeway method, so it may be outdated relative to HCM 6th/7th. — [FHWA *Traffic Analysis Toolbox Vol. II*, Appendix A](https://ops.fhwa.dot.gov/trafficanalysistools/tat_vol2/sectapp_a.htm) [VERIFY: extracted]
- **Counts must measure demand, not capacity.** FHWA microsimulation guidance (2019 update), Ch. 2: "If congestion is present at or upstream of a count location, care should be taken to ensure that the count measures demand and not capacity." It also says: "The count period should ideally start before the onset of congestion and end after the dissipation of all congestion to ensure that all queued demand is eventually included in the count." — [FHWA (2019) *Traffic Analysis Toolbox Vol. III: Guidelines for Applying Traffic Microsimulation Modeling Software, 2019 Update to the 2004 Version*, FHWA-HOP-18-036, Ch. 2](https://ops.fhwa.dot.gov/publications/fhwahop18036/chapter2.htm) [VERIFY: extracted]
- **Where to measure bottleneck throughput, and count reconciliation.** Throughput "should be measured either immediately upstream (within 0.5 miles and prior to any major intersection or interchange) or downstream of the bottleneck". "Upstream counts should be compared to downstream counts", with differences above 10 % investigated where no sources or sinks lie in between. According to the automated extraction, the chapter does *not* give a procedure for deriving demand from counts plus queues. — [FHWA (2019) FHWA-HOP-18-036, Ch. 2](https://ops.fhwa.dot.gov/publications/fhwahop18036/chapter2.htm) [VERIFY: extracted]
- **Sensitivity to over-capacity demand.** The 2004 Vol. III, Appendix F ("Demand Constraints"): "Microsimulation results are highly sensitive to the amount by which the demand exceeds the capacity of the facility, so it is vital that realistic demand forecasts be used."
  - It gives a proportional rule for constraining demand downstream of an upstream bottleneck: X = (D − C)/C, and constrained demand = unconstrained demand × (1 − X).
  - Worked example: bottleneck capacity 4,000 veh/h against unconstrained demand 5,000 veh/h, giving a 20 % reduction applied to downstream off-ramps.
  - Note: this appendix runs in the *forward* direction, from forecast demand to constrained flows, not from counts back to demand.
  - Source: [FHWA (2004) *Traffic Analysis Toolbox Vol. III*, Appendix F](https://ops.fhwa.dot.gov/trafficanalysistools/tat_vol3/sectapp_f.htm) [VERIFY: extracted; this is the 2004 version, superseded in part by the 2019 update]
- **"Unmet demand" in microsimulation practice (Texas DOT manual).** Unmet demand (vehicles that cannot enter the model) is common in oversaturated networks. It is measured in vehicles, roughly as queue length divided by average vehicle occupancy length. — [TxDOT, *Traffic Safety/Simulation manual*, §13.6 "Unmet Demand"](https://www.txdot.gov/manuals/des/tsp/chapter-13-microsimulation-analysis/13-6-unmet-demand.html) [VERIFY: search snippet only]
- **Arterial analogue that cites the HCM directly.** A VDOT/FHWA-funded report states that below capacity "the flow rate measured by traffic detectors ... will be identical to the demand". Above capacity, "measuring demand with the commonly available sensors (e.g., loop detectors) in the field is generally not possible", because "the queue grows beyond the sensor, and the flow measurements at a given point cannot exceed the capacity". — [Cetin, M., Yang, H., Xie, K., Kattepogu, G. and Salahshour, B. (2021) *What Is an Effective Way to Measure Arterial Demand When It Exceeds Capacity?* VTRC 22-R19, Virginia Transportation Research Council](https://rosap.ntl.bts.gov/view/dot/60865/dot_60865_DS1.pdf) (read in part from the text)

### Inferences
- The HCM and FHWA position, as far as I can confirm from these open secondary sources:
  1. Demand is the required input.
  2. Counts equal demand only when the count site and everything upstream of it are uncongested for the whole window.
  3. If the window brackets the congestion episode (it starts and ends undersaturated), the *total* count over the window equals total demand by vehicle conservation, but its *time profile* does not.

  Point 3 is my inference from the FHWA "start before onset, end after dissipation" rule; the sources do not state it this way.
- Counting immediately downstream of an active bottleneck measures discharge capacity, not demand. This is why the 2019 guidance treats bottleneck throughput as a separate calibration quantity.

### Gaps
- **HCM text not accessed.** I could not read the HCM 6th or 7th edition. From memory, unverified:
  - HCM 6th ed. Ch. 10 (Freeway Facilities Core Methodology) and Ch. 25 (Freeway Facilities: Supplemental) carry the oversaturated method;
  - Ch. 4 (Traffic Operations and Capacity Concepts) defines demand vs volume;
  - the HCM recommends estimating demand at a congested site as the downstream count plus the change in queued vehicles, or from counts at an upstream unconstrained location.

  Do not cite chapter or section numbers or wording until checked against a copy.
- The NCHRP corridor HCM report (*HCM Methodologies for Corridors Involving Freeways and Surface Streets*, NAP 25963, 2020) has an appendix on "Off-Ramp Queue Spillback Check". Its text did not render through the fetch tool, so I could not extract it.
- The NCHRP 2025 synthesis *Practices for Operational Traffic Simulation Models* (NAP 29076), literature-review chapter: the extraction found **no** passage on separating counts from demand under oversaturation. This is mildly informative: the issue seems under-treated in practice syntheses. [VERIFY: extracted; other chapters not checked]

---

## Q2. Physics: clipped plateaus, queue discharge at (dropped) capacity, cumulative (Newell) curves; and how capacity drop interacts with demand estimation

### Takeaway
Once a queue forms at a bottleneck, the bottleneck and every detector downstream of it count the *queue discharge rate*. That rate is nearly constant and is typically about 5–10 % (reported range up to about 20–26 %) below the pre-queue maximum flow.

So the counted series is a plateau:
- it is flatter than the demand peak;
- it lasts longer than the demand peak (it continues until the queue clears);
- it sits below both the demand and the pre-breakdown capacity.

Cumulative arrival and departure curves (Newell N-curves) make this explicit: queue = A(t) − D(t), and demand rate = dD/dt + dQ/dt.

### Cited Findings
- **Discharge is lower than pre-queue flow (Cassidy and Bertini 1999).** At two freeway bottlenecks near Toronto, "the average rate vehicles discharge from a queue can be 10 % lower than the flow measured prior to the queue's formation".
  - Discharge flows were "nearly stationary": cumulative discharge counts "generally did not deviate by more than about 50 vehicles from a trend line of constant slope".
  - Queue formation was always accompanied by a relatively low discharge rate, followed later by a temporary surge.
  - Method: transformed (oblique) cumulative count and cumulative occupancy curves at neighbouring loops.
  - Source: [Cassidy, M.J. and Bertini, R.L. (1999) 'Some traffic features at freeway bottlenecks', *Transportation Research Part B*, 33(1), pp. 25–42](https://ideas.repec.org/a/eee/transb/v33y1999i1p25-42.html); summary at [UC Berkeley ITS](https://its.berkeley.edu/node/4141) [VERIFY: abstract only]
- **About 6 % drop, and capacity must be measured in the bottleneck (Hall and Agyemang-Duah 1991).**
  - "There appears to be roughly a 6 percent reduction in maximum flow rates after the onset of congestion."
  - Capacity "can only be measured in a bottleneck, and not in a queue".
  - Maximum flows at one site were roughly normally distributed, with mean 6,071 and standard deviation 262 veh/h.
  - Source: [Hall, F.L. and Agyemang-Duah, K. (1991) 'Freeway capacity drop and the definition of capacity', *Transportation Research Record*, 1320, pp. 91–98](https://onlinepubs.trb.org/Onlinepubs/trr/1991/1320/1320-012.pdf) [SAGE, but an open TRB copy exists] [VERIFY: abstract and background read; page range inferred from the issue's first page 91, not checked]
- **The drop depends on speed in congestion (Yuan, Knoop and Hoogendoorn).** Literature puts the queue discharge rate 5–20 % below pre-queue capacity. Their empirical data from the Dutch A4 and A12 freeways show the discharge rate rising with the speed in congestion. The drop is "around 26 %" when the speed in congestion is 0 km/h. — [Yuan, K., Knoop, V.L. and Hoogendoorn, S.P. (2015) 'Capacity drop: relationship between speed in congestion and the queue discharge rate', *Transportation Research Record*, 2491](https://research.tudelft.nl/files/75552687/2491_08.pdf) [SAGE; TU Delft open copy exists but returned HTTP 403 to my fetcher] [VERIFY: search snippet only; year and title from memory plus the URL's "2491_08" identifier]
- **HCS example of the drop.** The McTrans hidden-bottleneck example applies a 7 % queue-discharge capacity drop. — [Sasahara (2021)](https://mctrans.ce.ufl.edu/analyzing-active-and-hidden-bottlenecks/) [VERIFY: extracted]
- **Newell's cumulative-curve theory (1993).** Newell's simplified kinematic-wave theory combines kinematic waves with deterministic queueing by tracking cumulative vehicle counts N(x,t) at selected points.
  - With a triangular flow–density relation, the cumulative curve at a point is the lower envelope of a shifted upstream curve and a shifted downstream curve.
  - N-curves directly give vehicle-hours, vehicle-miles and accumulation.
  - Tests showed the theory "works best under over-saturated conditions".
  - Source: [Newell, G.F. (1993) 'A simplified theory of kinematic waves in highway traffic, Part II: Queueing at freeway bottlenecks', *Transportation Research Part B*, 27(4), pp. 289–303](https://ideas.repec.org/a/eee/transb/v27y1993i4p289-303.html); [TRID record](https://trid.trb.org/View/382297) [VERIFY: abstract only]
- **Input–output identity for demand.** The arrival volume in an interval equals departures plus the end-of-interval queue minus the start-of-interval queue (Berry 1987, as summarised by Cetin et al.). The method "hinges on an accurate way to observe the maximum queue length", and "current queue estimation methods ... are not effective for estimating the queue beyond the upstream detector". — [Cetin et al. (2021) VTRC 22-R19, literature review](https://rosap.ntl.bts.gov/view/dot/60865/dot_60865_DS1.pdf) (read; Berry 1987 itself not read [VERIFY])

### Inferences (my derivation; not stated in this form by any one source)
- **Plateau width.** Let demand d(t) exceed discharge rate μ = C(1 − δ) during [t1, t2]. Here C is pre-queue capacity and δ is the capacity drop. Then:
  - the queue Q(t) = ∫(d − μ) grows until t2;
  - it clears at t3 > t2, where ∫_{t1}^{t3} (d − μ) dt = 0;
  - the counted flow at or after the bottleneck equals μ over [t1, t3].

  The counted "peak" is therefore flat, lower (μ < max d), wider (t3 − t1 > t2 − t1) and later-centred than the true demand peak. The demand maximum lies inside [t1, t2], but counts show no maximum at all.
- **Capacity drop makes it worse in two ways.**
  1. Counts during the episode underestimate demand by (d − μ), which is larger than the (d − C) one would expect without the drop.
  2. The plateau also *underestimates pre-queue capacity* C by δ, roughly 6–10 % per Hall and Agyemang-Duah (1991) and Cassidy and Bertini (1999).

  An analyst who takes the counted plateau as "capacity" and the counts as "demand" sets d/c ≈ 1 on a day where true d/c may be well above 1, and builds a plant that never breaks down.
- **The discharge period lengthens with δ.** For the same demand, a larger δ lengthens t3 − t1, so the clipped plateau gets wider still.
- **Ramps.** On-ramp counts taken at the meter or merge are also clipped, by the metering rate or merge capacity, once the ramp queue reaches past the detector. Ramp demand is hidden in the same way. Queue detectors at the ramp entrance exist for that reason.

### Gaps
- I did not find an open, fully read source that gives the plateau-widening and peak-shift effect on *time-of-day demand profiles* in numbers, beyond the generic queueing algebra above.
- I did not access Srivastava and Geroliminis (2013) or Oh and Yeo's capacity-drop reviews, which may give additional ranges. Not cited.

---

## Q3. Methods to recover unconstrained demand from congested freeway data, and their accuracy

### Takeaway
Five families of methods exist:
1. **Count upstream of the furthest queue extent**, or count over a window that brackets the whole episode (practice guidance; no accuracy figure).
2. **Throughput plus queue accumulation** (input–output / Newell N-curves; capacity + queued vehicles).
3. **Shockwave back-calculation from the speed of the queue tail:** q_A = q_C + w·(k_A − k_C), with densities written as q/u.
4. **Delay or travel-time inversion through a calibrated volume–delay function.**
5. **Model-based estimation:** Kalman-filter or dynamic OD estimation on loop data.

The only accuracy figures I could verify come from an *arterial* study using probe speeds: MAPE 2.5–2.8 % in simulation and under 4 % against field counts. The freeway-specific papers are mostly TRR [SAGE] or known only by abstract. Model-based OD methods are biased under congestion unless queueing and spill-back are modelled.

### Cited Findings
- **Shockwave (SW) method and VDF inversion (Cetin et al. 2021).** Both methods use probe speeds (INRIX) and the bottleneck capacity.
  - **SW method:** w = (q_A − q_C)/(k_A − k_C), solved for the arrival (demand) rate q_A using k = q/u.
  - **VDF method:** the HCM oversaturated delay equation is solved for X = v/c, given the probe-measured delay.
  - **Simulation accuracy:** "mean absolute percentage errors were calculated to be 2.5 % and 2.8 % for the SW and VDF methods respectively". Individual errors range from about −12 % to +6 %. Errors are largest for short analysis periods (0.25 h), where event timing accurate only to about ±1 min dominates.
  - **Field accuracy:** "less than 4 % error when tested with field data". Field site: Indian River Road, Virginia Beach (an arterial). Ground truth was video counts on three September days.
  - **Scope caution:** the study and site are arterial. The SW method is generic kinematic-wave physics and transfers to freeways; the VDF variant uses the signalised-intersection delay equation and does not transfer directly.
  - Source: [Cetin et al. (2021) VTRC 22-R19](https://rosap.ntl.bts.gov/view/dot/60865/dot_60865_DS1.pdf) (read in part). A journal version: [Kattepogu, G., Cetin, M., Salahshour, B., Yang, H. and Xie, K. (2024) 'Estimating demand volume for signalized corridors under oversaturated conditions using aggregated probe vehicle speed data', *Transportation Research Record*](https://doi.org/10.1177/03611981231178305) [SAGE] [VERIFY: not read]
- **Freeway VDF calibration with "demand = capacity + queue" (Huntsinger and Rouphail 2011).** Per Cetin et al.'s summary, they "successfully applied this technique to estimate the demand under oversaturation on freeways", where "actual demand is the sum of demand at capacity plus the queue length", and the method "is applicable only for freeway corridors". — Huntsinger, L.F. and Rouphail, N.M. (2011) 'Bottleneck and queuing analysis: calibrating volume–delay functions of travel demand models', *Transportation Research Record*, 2255, pp. 117–124 (reference as listed in [Cetin et al. 2021](https://rosap.ntl.bts.gov/view/dot/60865/dot_60865_DS1.pdf)) [SAGE] [VERIFY: not read; secondary description only; no accuracy figure available to me]
- **"Symmetric" method and the capacity + queue definition (Pan et al., 2026).**
  - The paper states that conventional detector data "significantly underestimates the true demand under congested conditions".
  - It defines bottleneck demand as observed flow when uncongested, and capacity plus queued vehicles when congested.
  - It proposes a "symmetric method" that reflects flow values across the capacity threshold to approximate unserved demand (Greenshields-grounded).
  - Source: [Pan, Y., Hu, X., Tang, Q., Chen, Y. and Zhou, X.S. (2026) 'Enhancing traffic state estimation at bottlenecks through improved demand modeling: a Greenshields-grounded approach', *Transportation Research Record*](https://doi.org/10.1177/03611981251394673) [SAGE] [VERIFY: search snippet only; accuracy not seen]
- **Freeway queue length from point detectors plus AVI (Fakharian Qom et al. 2017).** Two methods combine point detectors and AVI readers, for off-line and real-time use. They report that the combination "produces accurate estimates of queue length". Queue length is the missing input for the capacity + queue demand identity. — [Fakharian Qom, S., Hadi, M., Xiao, Y. and Al-Deek, H. (2017) 'Queue length estimation for freeway facilities: based on combination of point traffic detector and automatic vehicle identification data', *Transportation Research Record*, 2616](https://doi.org/10.3141/2616-03) [SAGE] [VERIFY: search snippet only; numbers not seen]
- **Shockwave-based real-time freeway queue estimation.** An open-access record exists of a freeway queue estimation model based on shockwave analysis. — ['Real-time queue estimation model development for uninterrupted freeway flow based on shockwave analysis', *Canadian Journal of Civil Engineering*](https://doi.org/10.1139/cjce-2014-0218) [VERIFY: title only; authors, year and results not checked]
- **Extended Kalman filter OD estimation on freeway corridors (Chang and Wu 1994).** A dynamic model and on-line extended-Kalman-filter algorithm for time-varying freeway OD matrices. It uses mainline counts, ramp flows and macroscopic traffic characteristics, "to realistically consider the interrelations between O-D distributions and observed flows under congested conditions". — Chang, G.-L. and Wu, J. (1994) 'Recursive estimation of time-varying origin-destination flows from traffic counts in freeway corridors', *Transportation Research Part B*, 28(2) [VERIFY: abstract via [TRID](https://trid.trb.org/View/390452) only; volume and issue from memory]
- **Loop-detector OD split estimation, tested only without congestion (Wu, Davis and Levinson 2004).** Compares constrained least squares (off-line) with a constrained Kalman filter and an SQP-based recursive estimator (on-line) for freeway OD *split* parameters from loop data. The simulation test explicitly had no congestion ("no congestion was observed during the simulation period"). Such methods split *counted* flows. They cannot by themselves recover demand that never reached the detectors. — [Wu, Y., Davis, G. and Levinson, D. (2004) *Improving the Estimation of Travel Demand for Traffic Simulation: Part II*, CTS 04-11, University of Minnesota](https://rosap.ntl.bts.gov/view/dot/39368/dot_39368_DS1.pdf) [VERIFY: abstract and selected passages read]
- **Bias in dynamic OD estimation under congestion (Frederix, Viti and Tampère).** They give three conditions for unbiased dynamic OD estimation in congested networks.
  1. The network-loading model must represent queueing correctly: "an incorrect representation of queuing leads to an incorrect interpretation of information from the detectors, and thus leads to biased results".
  2. The usual *linear* assignment-matrix relation between OD flows and link counts is inadequate under congestion.
  3. Unbiased estimation "requires the calculation of the sensitivity of the link flows to all origin–destination flows, in order to incorporate the effects of congestion spillback".

  — Frederix, R., Viti, F. and Tampère, C.M.J., work summarised on [KU Leuven Lirias](https://lirias.kuleuven.be/bitstream/123456789/293927/1/paper_25.pdf) (HTTP 404 on fetch) and [hierarchical DODE, Univ. Luxembourg ORBilu](https://orbilu.uni.lu/bitstream/10993/7405/1/hierarchical.pdf), [TRID 1354533](https://trid.trb.org/view/1354533) [VERIFY: search snippet only; exact paper, year and venue of the "three conditions" result not confirmed]
- **Kalman filters for on-line demand estimation.** A secondary source asserts that "the Kalman Filter has been proven to outperform all other algorithms for the Online Dynamic Demand Estimation (ODDE) problem". This is a strong generalisation; treat it as an opinion of that source, not a fact. — [Frontiers in Future Transportation (2021), article 640570](https://www.frontiersin.org/journals/future-transportation/articles/10.3389/ffutr.2021.640570/pdf) [VERIFY: search snippet only]

### Inferences
- **Practical ranking for a simulation study that needs heavy-day demand profiles:**
  - Use counts from the upstream-most detector *beyond the maximum queue extent*, plus on-ramp counts at queue-entrance detectors, when they exist.
  - Otherwise use N-curve reconstruction: bottleneck discharge counts plus queue accumulation, with queue size from detector occupancy along the queue or from probe travel times.
  - Shockwave back-calculation from the speed of the queue tail is a cheap cross-check, needing only probe speeds.
- **These methods disagree most** at the peak minute and around onset, because estimates of the queue tail position or onset time drive the error. The ±1 min timing error dominates in Cetin et al.'s short periods.
- **OD and Kalman approaches** recover unserved demand only if the process model holds queues explicitly (for example as CTM or Newell states). Otherwise they inherit the clipping from the counts (Frederix et al.; Wu et al.'s uncongested test).

### Gaps
- **No verified freeway accuracy figures** for demand recovered from congested loop data against an independent ground truth, such as upstream unconstrained counts or full-trajectory data like NGSIM or highD. The freeway papers found are TRR [SAGE] or abstract-only.
- **Not reached in the tool budget; relevant open candidates for follow-up:**
  - Wang and Papageorgiou (2005), extended-Kalman-filter freeway state estimation with boundary-flow estimation, TR-B;
  - Ashok and Ben-Akiva's Kalman-filter OD work;
  - Muñoz and Daganzo's bottleneck discharge studies;
  - Cassidy and Windover's oblique-curve method.

  All [VERIFY]; titles and years not checked here.

---

## Q4. Consequences for time-of-day plans and demand profiles fitted to counts; documented cases

### Takeaway
A demand profile or time-of-day plan fitted to counted volumes at or downstream of an active bottleneck has three systematic errors:
- it underestimates the peak demand rate;
- it overestimates the peak duration and pushes its centre later;
- it caps heavy days at the (dropped) discharge rate, so heavy days collapse towards ordinary days.

The size of the error is (d_peak − μ)/d_peak, where μ is the discharge rate. Verified worked examples give 16–20 %. I found **no documented real-world case** where a control plan was shown to underperform specifically because demand was hidden by capacity constraints.

### Cited Findings
- **Worked examples of the gap** (both are illustrative examples in guidance, not field measurements):
  - FHWA 2004 Vol. III example: 5,000 veh/h demand vs 4,000 veh/h bottleneck capacity, a 20 % reduction in downstream flows. — [FHWA (2004) TAT Vol. III, App. F](https://ops.fhwa.dot.gov/trafficanalysistools/tat_vol3/sectapp_f.htm) [VERIFY: extracted]
  - HCS example: 7,500 pc/h demand vs 6,285 pc/h served, about 16 %, with a 7 % capacity drop. — [Sasahara (2021)](https://mctrans.ce.ufl.edu/analyzing-active-and-hidden-bottlenecks/) [VERIFY: extracted]
- **Wrong conclusions downstream.** A segment with d/c = 1.04 on true demand appears uncongested when assessed on served volume (hidden bottleneck). An improvement at the active bottleneck then moves the queue rather than removing it. — [Sasahara (2021)](https://mctrans.ce.ufl.edu/analyzing-active-and-hidden-bottlenecks/) [VERIFY: extracted]
- **Model outputs scale with excess demand.** Microsimulation results are "highly sensitive to the amount by which the demand exceeds the capacity". A count-based demand that truncates the excess therefore biases delay and queue outputs downwards. — [FHWA (2004) TAT Vol. III, App. F](https://ops.fhwa.dot.gov/trafficanalysistools/tat_vol3/sectapp_f.htm) [VERIFY: extracted]
- **Fixed-time ramp metering limitation.** Fixed-time (time-of-day) ramp-metering rates are set from historical data and "do not perform effectively in the presence of severe traffic fluctuations". This is a statement of the generic limitation of time-of-day plans. It is not evidence of the hidden-demand mechanism specifically. — [Arxiv 2005.13992, 'A novel ramp metering approach based on machine learning and historical data'](https://arxiv.org/pdf/2005.13992) [VERIFY: search snippet only; authors not checked]

### Inferences (flagged as mine)
- **Underestimation is worst on the heaviest days.** On a day with d_peak ≤ C the count-fitted profile is unbiased. On heavier days the bias grows with (d_peak − μ). A day-pattern or clustering model trained on counts therefore *compresses the upper tail* of the day-to-day demand distribution, and the error is largest exactly where control matters most. This is my derivation from the queueing identity; I found no source that quantifies it across a population of days.
- **Total daily volume is a weak discriminator.** If the count window brackets the episode, total volume is conserved. Heavy and normal days can then have similar daily totals at the bottleneck but very different peak d(t). Day clustering on bottleneck counts may mis-assign them. Clustering on upstream counts, queue extent or travel time is more robust. (Inference.)
- **Capacity drop biases a plant calibrated from counts towards optimism.** It underestimates both demand (by d − μ) and capacity (by δ·C). If it then uses a capacity *without* a drop, it never reproduces the observed queue. For a controller evaluation (VSL or ramp metering), this removes the headroom the controller is supposed to recover. This bears directly on this repo's T1 check, "capacity drop exists ... and control matters". (Inference.)
- **Peak timing is biased late.** The demand peak occurs before the end of the plateau, while the plateau ends only when the queue clears (t3). A time-of-day plan whose switching times are set from count profiles will switch to peak settings late and back to off-peak settings late. (Inference.)

### Gaps
- **No documented case found** of a freeway control plan (TOD ramp metering, VSL schedule) or demand forecast that was evaluated and shown to fail *because* counted volumes hid demand. Such evidence may exist in agency before/after reports or in TRR [SAGE]; I could not locate an open one.
- **No source quantifying the error across days** (for example, percentage underestimation of the 85th or 95th-percentile day peak when profiles are fitted to bottleneck counts).
- **The HCM's own recommended demand-estimation procedure** for counts under oversaturation was not accessed (see Q1 Gaps).
