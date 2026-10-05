# Open real freeway traffic datasets with daily/weekly demand patterns (for calibrating simulation demand profiles)

Status of all access claims: **as seen 2026-10-04** unless stated otherwise. Convention: [VERIFY] = not read in full (abstract, snippet or landing page only); [SAGE] = SAGE-published (incl. Transportation Research Record), the author cannot access it. Items recalled from background knowledge and not checked in this session are put in **Gaps**, never in Cited Findings. Harvard-style short references are given inline.

---

## Q1. PeMS (Caltrans): access, resolution, ramp detectors, quality flags, and status as of 2026

### Takeaway
As of 2026-10-04, pems.dot.ca.gov is still online and still needs a free account (approval typically in 1-2 business days); a Caltrans-funded open-source "PeMS modernization" by Compiler LLC was archived/ended in October 2025, and I found no public notice that the legacy site's access model has changed. PeMS has mainline, on-ramp and off-ramp stations, 30-s raw data aggregated to 5 min, and heavy imputation; roughly 30 % of roadside data has been reported as questionable, so the observed percentage must be filtered on.

### Cited Findings
- **Access (as seen 2026-10-04):** "To use this site, you must apply for an account. Registering only takes a few minutes. Accounts are typically approved within one to two business days." The landing page says PeMS collects from "over 39,000 individual detectors", has more than a decade of history through its Archived Data User Service (ADUS), and integrates detectors, incidents, lane closures, toll tags, census counts, vehicle classification and WIM. The page shows no migration or discontinuation notice; its copyright line says 2026 — [Caltrans PeMS landing page](https://pems.dot.ca.gov/).
- **Modernization project ended:** Compiler LLC's open-source "caltrans/pems" was "designed, developed, and maintained by Compiler LLC on behalf of Caltrans Traffic Operations". Its docs say "As of October 2025, this project has ended and the repository is now archived". The roadmap planned a Q4 2025 go-live with contractor services to December 2025. The docs do **not** say whether it replaces pems.dot.ca.gov or changes registration — [Compiler PeMS docs](https://docs.compiler.la/pems/); [GitHub compilerla/pems](https://github.com/compilerla/pems).
- **Station types:** PeMS includes mainline, on-ramp and off-ramp stations. One Caltrans comparative analysis found that mainline segments have the most detector errors, followed by on-ramps and off-ramps — [Caltrans research note task3861 (2021)](https://dot.ca.gov/-/media/dot-media/programs/research-innovation-system-information/documents/research-notes/task3861-rns-11-21-a11y.pdf) [VERIFY: the search snippet attribution between this note and task1546 is uncertain]; [Caltrans research note task1546](https://dot.ca.gov/-/media/dot-media/programs/research-innovation-system-information/documents/research-notes/task1546-rns-8-21-a11y.pdf) [VERIFY].
- **Quality:** "approximately 30 percent of the data generated at Caltrans' roadside traffic detection stations is questionable in accuracy and therefore unusable" (as reported in a Caltrans research note quoting PeMS; same two notes as above) [VERIFY]. PeMS's statistical treatment of detector malfunction and imputation is described in Bickel et al. (2007) 'Measuring traffic', *Statistical Science* — [PDF](https://www.stat.berkeley.edu/~bickel/Bickel%20et%20al%202007-measuring%20traffic.pdf); [arXiv 0804.2982](https://arxiv.org/pdf/0804.2982) [VERIFY].
- **Resolution:** raw 30-s detector data aggregated into 5-min intervals (as used in the ASTGCN benchmarks) — [Guo et al. (2019) ASTGCN, AAAI](https://ojs.aaai.org/index.php/AAAI/article/view/3881/3759) [VERIFY]. PeMS 5-min flow, speed and occupancy are used for METANET calibration in [Chan, Raghavan & Wu (2026) arXiv:2605.23042](https://arxiv.org/abs/2605.23042) [VERIFY].
- **Derived open products:** a "Bottlenecks" dataset is published on the California Open Data portal (likely PeMS-derived; contents not inspected) — [data.ca.gov Bottlenecks](https://data.ca.gov/dataset/bottlenecks) [VERIFY]. A Berkeley Connected Corridors page describes road sensor data for the I-210 pilot — [Connected Corridors: Road Sensor Data](https://connected-corridors.berkeley.edu/node/590) [VERIFY].
- **Background reference:** Varaiya's PeMS tutorial (PeMS Version 3) — [PeMSTutorial.pdf](https://people.eecs.berkeley.edu/~varaiya/papers_ps.dir/PeMSTutorial.pdf) [VERIFY]; Choe, Skabardonis & Varaiya, 'Freeway Performance Measurement System (PeMS): an operational analysis tool' — [NTL PDF](https://ntlrepository.blob.core.windows.net/lib/34000/34000/34065/10.1.1.112.4428_1_.pdf) [VERIFY; venue/year not confirmed, possibly a TRB paper → possibly SAGE].

### Inferences
- Access to PeMS looks unchanged (manual-approval account), but the end of the modernization contract means there is a real risk of interface or URL changes in 2026-27. Download and archive the needed station-days and the station metadata now, under `/home/catalin/work/phd/` (not in the repo).
- For demand profiles, use only station-days with a high "% observed" (for example ≥ 80-90 %; the exact threshold is a choice that must be pre-registered). Imputed 5-min values smooth out the very breakdown dynamics (capacity drop, queue discharge) that a VSL/RM study needs.
- Ramp detectors are the weakest point. Where on-ramp counts are missing, joint ramp-flow estimation from mainline data (Chan et al. 2026) is one documented route. It makes the ramp demand a model output, though, so it is circular if the same model is then used to evaluate control.

### Gaps
- I could not find an official Caltrans statement (2025-2026) on whether the Compiler modernization went live, replaced, or will replace pems.dot.ca.gov. Verify directly with Caltrans or on the PeMS "Help/News" pages after logging in.
- I could not confirm from a primary page in this session: the exact PeMS station-type codes (from memory: ML, OR, FR, HV, CD, FF), the "% observed" field definition, or the 30-s raw "Station Raw" clearinghouse files. These are from memory [VERIFY].
- Chen, Kwon, Skabardonis & Varaiya (2003), 'Detecting errors and imputing missing data for single-loop surveillance systems', *TRR* 1855 — recalled, not checked [VERIFY][SAGE].
- PeMS data licence/terms-of-use wording was not visible without login. I found no explicit open licence.

---

## Q2. Other open sources: coverage, sensors, resolution, history, access/licence, ramps, caveats

### Takeaway
The strongest open alternatives to PeMS for **multi-year, per-lane, sub-5-min freeway data with ramp-metering context** are **MnDOT RTMC (Twin Cities; 30-s volume/occupancy; public JSON feed and archive; dense ramp metering)** and **NDW (Netherlands; minute data from about 2010-11; open)**. UK WebTRIS is open with no key, but it is aggregated. Germany's public data are mainly hourly permanent-count-station data. Trajectory sets (NGSIM, highD, I-24 MOTION) are far too short for daily or weekly profiles. ML benchmarks (METR-LA, PEMS-BAY, PEMS03/04/07/08, LargeST) are PeMS or LA-loop subsets with no ramp or geometry context.

### Cited Findings
**US — Minnesota DOT (RTMC, Twin Cities)**
- 30-s volume, occupancy and speed from loop detectors and Wavetronix radar on Twin Cities metro freeways and Rochester, 24/7. More than 4,500 loop detectors; the data are packaged daily into zip archives — [Kwon, UMN Duluth RTMC archive page](https://www.d.umn.edu/~tkwon/TMCdata/TMCarchive.html) [VERIFY]; [getTraf user manual](https://www.d.umn.edu/~tkwon/Download/getTraf_UserManual.pdf) [VERIFY].
- A public JSON feed has the URL pattern `http://data.dot.state.mn.us/trafdat/metro/[year]/[date]/[detector_id].c30.json` (30-s) — [Metropolitan Council tc.sensors README](https://github.com/Metropolitan-Council/tc.sensors/blob/main/README.Rmd) [VERIFY]; R package [metropolitan-council/tc.sensors](https://github.com/metropolitan-council/tc.sensors).
- The Twin Cities freeway–ramp merges under ramp control are the empirical base of Srivastava & Geroliminis (2013) (see Q4) — [EPFL Infoscience](https://infoscience.epfl.ch/record/188341).

**US — Washington (WSDOT, Seattle)**
- "Seattle 20 Second Freeway": raw and cleaned 20-s detector data for I-5 in Seattle, 1 May – 31 Oct 2011. It came from the USDOT Data Capture and Management programme and is a legacy dataset, available as attached files only — [data.gov catalog](https://catalog.data.gov/dataset/seattle-20-second-freeway).
- `data.wsdot.wa.gov/traffic` holds WSDOT traffic data for third parties, but "generally an agreement is needed" — [WSDOT traffic data](https://data.wsdot.wa.gov/traffic/) [VERIFY].

**US — Utah (UDOT)**
- UDOT publishes a freeway detector health report — [UDOT FPM Health Report](https://udottraffic.utah.gov/FPM/HealthCharts/HealthReport) [VERIFY: confirms the system exists; download access and licence not checked].

**US — Tennessee (I-24 MOTION, trajectories)**
- 276 4K cameras on 40 poles cover about 4.2 mi of a 4–5 lane freeway near Nashville with frequent congestion. The first public datasets contain at least 4 h of trajectories for each of 10 days. Reference: Gloudemans et al. (2023) 'I-24 MOTION: an instrument for freeway traffic science', *Transportation Research Part C*, 155 — [arXiv 2301.11198](https://arxiv.org/abs/2301.11198v1) [VERIFY]; [i24motion.org publication page](https://i24motion.org/publications/i-24-motion-instrument-freeway-traffic-science).
- INCEPTION v1.0 data: virtual-trajectory tools (VT-tools v1.0) and sample data are public. Other days are to be released "pending paper acceptance", and a data preview is available to **registered** users at i24motion.org — [Virtual trajectories for I-24 MOTION](https://paperswithcode.com/paper/virtual-trajectories-for-i-24-motion-data-and) [VERIFY]; [CPS 2025 MOTION slides](https://cps-vo.org/sites/cps-vo.org/files/2025-05/CPS25-MOTION-slides.pdf) [VERIFY].

**UK — National Highways WebTRIS / MIDAS**
- WebTRIS is a JSON REST API (v1.0) at `webtris.nationalhighways.co.uk/api/{version}/{resource}`. It is free, with no registration and no API key. It covers sites, site types, areas, daily and aggregated quality metrics, and site reports over date ranges. Licence: "Free Other (Open)" — [DfT Find Transport Data: WebTRIS Traffic Flow API](https://findtransportdata.dft.gov.uk/dataset/webtris-traffic-flow-api); [Swagger](https://webtris.highwaysengland.co.uk/API/Swagger); R client [webTRISr](https://www.rdocumentation.org/packages/webTRISr/versions/0.2.0).
- The sensors are predominantly MIDAS inductive loops — [N. Rennie, "national highways" blog](https://nrennie.rbind.io/national-highways/) [VERIFY; secondary source].
- data.gov.uk also lists "Highways England network journey time and traffic flow data" (journey-time and flow records) — [data.gov.uk](https://www.data.gov.uk/dataset/9562c512-4a0b-45ee-b6ad-afc0f99b841f/highways-england-network-journey-time-and-traffic-flow-data) [VERIFY].

**Netherlands — NDW**
- All NDW traffic data are in principle open, real-time and historical: intensity (flow), mean speed and travel time — [NDW: I want to use open data](https://english.ndw.nu/our-data/i-want-to-use-open-data) [VERIFY].
- Dexter (Data EXploration and exporTER) is the historical database: speeds, intensities, journey times, incidents and more. It provides minute data from >100,000 locations. History is given as "from 2010" on one page and "back to July 2011" on another (**conflict**). An open subset is available at `dexter.ndw.nu/opendata` — [NDW Dexter](https://english.ndw.nu/products-and-services/dexter); [NDW docs: Historical Data](https://docs.ndw.nu/en/handleidingen/DEXTER/) [VERIFY].

**Germany — Autobahn GmbH / BASt**
- Autobahn GmbH runs the counting on motorways and BASt compiles it. Automatic permanent counting stations (inductive loops; 8 vehicle classes) produce **hourly** volumes for every hour of the year, and gaps from equipment failure are filled with estimation algorithms — [BMV: Straßenverkehrszählung 2025](https://www.bmv.de/SharedDocs/DE/Artikel/StB/strassenverkehrszaehlung-2025.html) [VERIFY; attribution of the snippet to this page is likely but not certain]; annual BASt reports, e.g. [TRID: Verkehrsentwicklung auf Bundesfernstraßen 2012](https://trid.trb.org/View/1306974).

**Australia**
- Victoria (DTP, formerly VicRoads): 15-min SCATS **traffic-signal** volumes per site, detector and lane. Monthly files run to at least April 2026 — [opendata.transport.vic.gov.au: Traffic Signal Volume Data](https://opendata.transport.vic.gov.au/dataset/traffic-signal-volume-data) [VERIFY]. These are signal (mostly arterial) counts, **not** freeway mainline loops.
- NSW: Traffic Volume Counts API with permanent and sample **hourly** counts since 2006. TfNSW states the datasets "have been experiencing issues with data quality and sensor availability" and that a rebuild is underway — [NSW Roads Traffic Volume Counts API](https://opendata.transport.nsw.gov.au/dataset/nsw-roads-traffic-volume-counts-api) [VERIFY].

**Trajectory datasets (short duration)**
- highD: 60 drone recordings averaging about 17 min, 16.5 h total, 25 Hz, about 110,000 vehicles on German motorways. NGSIM: US-101 and I-80, 45 min per highway, 10 Hz, 9,206 vehicles — Krajewski et al. (2018) 'The highD dataset…' — [arXiv 1810.05642](https://arxiv.org/pdf/1810.05642) [VERIFY].

**ML forecasting benchmarks (derived)**
- METR-LA: 207 loop detectors on Los Angeles County highways, 1 Mar – 30 Jun 2012. PEMS-BAY: 325 PeMS sensors in the Bay Area, 1 Jan – 31 May 2017 (the snippet says "6 months", which does not match those dates; **inconsistency, VERIFY**) — Li et al. (2018) DCRNN — [arXiv 1707.01926](https://arxiv.org/pdf/1707.01926) [VERIFY].
- PeMSD4: 307 detectors, Jan–Feb 2018. PeMSD8: 170 detectors, Jul–Aug 2016. Both are 30-s data aggregated to 5 min — Guo et al. (2019) ASTGCN — [AAAI](https://ojs.aaai.org/index.php/AAAI/article/view/3881/3759) [VERIFY].
- LargeST: built from PeMS (18,954 loop detectors); 8,600 mainline sensors with coordinates are kept — Liu et al. (2023) 'LargeST: a benchmark dataset for large-scale traffic forecasting', NeurIPS Datasets & Benchmarks — [arXiv 2306.08259](https://arxiv.org/pdf/2306.08259) [VERIFY].

### Inferences
- **For daily/weekly demand profiles with ramp metering, the order of preference is: MnDOT (fully public, no login, 30-s, dense metering) > PeMS (login, 5-min, ramp stations exist but quality varies) > NDW (open minute data; ramp-metering context needs separate metadata) > WebTRIS (open, aggregated, MIDAS).** German and NSW hourly counts are suitable only for coarse day-type shapes, not for bottleneck dynamics.
- **ML benchmarks are not suitable for calibration.** They are mainline-only, cover 2–6 months, and have no ramp flows, lane counts or geometry. Some contain imputed values. They are useful only as sanity checks on day-type shapes. Their PeMS origin means they are not independent of PeMS evidence.
- **Trajectory sets (NGSIM 45 min/site, highD about 17 min/recording, I-24 MOTION a few hours/day over about 10 days in the first release) cannot provide daily or weekly demand patterns.** They can calibrate car-following parameters and capacity-drop micro-mechanics (headways, lane changing), which are complementary to loop-based demand profiles.

### Gaps
- Not checked this session [VERIFY]:
  - MIDAS raw 1-min data access (e.g. via the UK CEDA archive / "MIDAS Gold"; recalled, unconfirmed);
  - WebTRIS native resolution (recalled as 15-min report intervals; unconfirmed);
  - German Mobilithek (successor of MDM) motorway detector data at minute level and its licence;
  - NDW Dexter registration requirements for full (non-"opendata") exports.
- pNEUMA (Barmpounakis & Geroliminis 2020, TR-C, recalled) is an **urban** Athens drone dataset, not freeway. Details are unconfirmed [VERIFY].
- The provenance of PEMS03/PEMS07 (often attributed to STSGCN, Song et al. 2020, AAAI) was not checked [VERIFY].
- No Chinese-agency (non-PeMS) open freeway loop dataset with daily coverage was found in this session.

---

## Q3. Papers that calibrated SUMO, METANET or CTM to PeMS-like data (capacity drop, queue discharge); public calibrated scenarios

### Takeaway
I verified a recent open-source METANET calibration on PeMS with joint ramp-flow estimation (Chan, Raghavan & Wu, 2026, code on GitHub). I also verified a first-order CTM with a two-capacity fundamental diagram calibrated to Twin Cities ramp-metered merges (Srivastava & Geroliminis, 2013). A calibrated I-210 SUMO network from the Connected Corridors programme exists and has been reused for RL. I could not confirm that it is publicly downloadable or how it was calibrated against PeMS.

### Cited Findings
- **Chan, M., Raghavan, S. & Wu, C. (2026)** 'Open-Source METANET Calibration for Reproducible Freeway Traffic Macroscopic Simulation', arXiv:2605.23042 (submitted 21 May 2026). It is validated on PeMS loop data. It "jointly estimat[es] ramp flows and model parameters from mainline detector data alone", because ramp detector data are "frequently unavailable or unreliable", and it reproduces stop-and-go waves. Code: [github.com/woxsao/metanet-calibration](https://github.com/woxsao/metanet-calibration). Capacity drop and ramp metering are not discussed in the abstract — [arXiv](https://arxiv.org/abs/2605.23042) [VERIFY: abstract only].
- **Srivastava, A. & Geroliminis, N. (2013)** 'Empirical observations of capacity drop in freeway merges with ramp control and integration in a first-order model', *Transportation Research Part C*, 30, pp. 161–177. The work is based on Twin Cities freeway–ramp merges and estimates the drop from phase diagrams. **The drop size depends on the mainline/ramp flow ratio.** The paper investigates whether control affects the drop, and embeds it in a Godunov CTM with two capacities and a memory rule. The model is compared with real data and microsimulation — [EPFL Infoscience](https://infoscience.epfl.ch/record/188341); [PDF](https://infoscience.epfl.ch/record/188341/files/Sriv_Gerol_2013.pdf?version=1) [VERIFY].
- **I-210 SUMO network:** "The connected corridors model was built for Caltrans D7, and the I-210 network was simulated within SUMO", described as "a large, calibrated model of a portion of the Ventura Freeway". **Caution:** I-210 near Pasadena is usually called the Foothill Freeway, so this naming may be an error in the source or in the snippet — 'Reinforcement Learning Based Oscillation Dampening' — [OSTI 2545915](https://www.osti.gov/pages/servlets/purl/2545915) [VERIFY: authors, year and calibration details not read].
- **Managed-lane CTM calibration:** 'Macroscopic Modeling, Calibration, and Simulation of Managed Lane-Freeway Networks, Part II: Network-scale Calibration and Case Studies' — [arXiv 1908.09953](https://arxiv.org/pdf/1908.09953) [VERIFY: authors, data source and venue not confirmed here].
- **A METANET parameter-identification algorithm for limited loop detectors** — [ResearchGate 261111925](https://www.researchgate.net/publication/261111925_A_parameter_identification_algorithm_for_the_METANET_model_with_a_limited_number_of_loop_detectors) [VERIFY: authors and venue not confirmed].
- **Flow (Berkeley)** ships generic merge, bottleneck, ring and grid scenarios for mixed-autonomy RL — snippet in the [OSTI report above](https://www.osti.gov/pages/servlets/purl/2545915) [VERIFY].
- **Unvetted GitHub project:** "flowstate-v2: calibrated corridor digital twins… SUMO+IDM microscopic core, CTM screening tier, FHWA-style validation reports" — [GitHub](https://github.com/abc000cool/flowstate-v2). Provenance and quality are unknown; do not rely on it without inspection.
- **SUMO mesoscopic limitations:** 'Revisiting mesoscopic traffic flow simulation in SUMO: limitations, analysis, and an alternative' (2026) — [arXiv 2606.09282](https://arxiv.org/abs/2606.09282) [VERIFY].
- **Caltrans/PATH report:** 'Congestion-Responsive On-Ramp Metering' — [ROSA P dot/34214](https://rosap.ntl.bts.gov/view/dot/34214/dot_34214_DS1.pdf) [VERIFY: content not read].

### Inferences
- **Chan et al. (2026) is the most directly reusable artefact:** METANET, PeMS and open code. It could provide a macroscopic "MPC model fitted on separate seeds/days" for the repo's best-non-learning comparator. Note that its ramp-flow estimation is a fitted latent quantity.
- **Srivastava & Geroliminis (2013) is the key empirical prior for an RM bottleneck:** the capacity drop varies with the ramp share and may be affected by metering. Any SUMO calibration should therefore check the discharge rate against that relation, not against a single number.
- **No verified, public, PeMS-calibrated SUMO freeway scenario with ramp metering was found.** Treat "public calibrated I-210 SUMO" as unconfirmed until the files and calibration report are located.

### Gaps
- Not verified this session (recalled; all [VERIFY]):
  - Dervisoglu, Gomes, Kwon, Horowitz & Varaiya (2009), 'Automatic calibration of the fundamental diagram and empirical observations on capacity', TRB Annual Meeting (PeMS-based) [possibly SAGE if later in TRR];
  - Spiliopoulou, Kontorinaki, Papageorgiou & Kopelias (2014), METANET/CTM validation at congested off-ramp areas, *Transportation Research Part C*;
  - Muralidharan & Horowitz work on CTM imputation and calibration with PeMS for I-210;
  - CIRCLES consortium I-24 MVT (Nov 2022, 100 automated vehicles) data releases.
- The public availability and calibration targets of the I-210 Connected Corridors SUMO/Aimsun model were not established.
- No VISSIM or Aimsun calibration paper against PeMS or MnDOT data was checked in this session.

---

## Q4. Known recurrent bottlenecks with documented capacity-drop measurements

### Takeaway
I verified three classic empirical sources: Cassidy & Bertini (1999), two Toronto-area bottlenecks with queue discharge up to about 10 % below pre-queue flow; Chung, Rudjanakanoknad & Cassidy (2007), three geometrically different bottlenecks where the drop is tied to a reproducible lane-normalised density; and Srivastava & Geroliminis (2013), Twin Cities ramp-metered merges. Only the MnDOT sites are likely to be re-extractable today from fully open, long-history data.

### Cited Findings
- **Cassidy, M.J. & Bertini, R.L. (1999)** 'Some traffic features at freeway bottlenecks', *Transportation Research Part B*, 33(1), pp. 25–42. Two bottlenecks in and near Toronto. "The average rate vehicles discharge from a queue can be 10 % lower than the flow measured prior to the queue's formation". Discharge was nearly stationary and alternated between higher and lower rates. Method: oblique cumulative counts and cumulative occupancy curves from neighbouring loops — [IDEAS/RePEc](https://ideas.repec.org/a/eee/transb/v33y1999i1p25-42.html); [ITS Berkeley](https://its.berkeley.edu/node/4141) [VERIFY].
- **Chung, K., Rudjanakanoknad, J. & Cassidy, M.J. (2007)** 'Relation between traffic density and capacity drop at three freeway bottlenecks', *Transportation Research Part B*, 41(1), pp. 82–95. In all three bottlenecks, discharge falls once queues form, and a pronounced density rise always preceded the drop. Lane-normalised densities at the drop were similar across sites, which "hold[s] promise" for density-targeting control — [IDEAS/RePEc](https://ideas.repec.org/a/eee/transb/v41y2007i1p82-95.html); [ITS Berkeley](https://its.berkeley.edu/node/4092) [VERIFY].
- **Srivastava & Geroliminis (2013):** Twin Cities merges with ramp control; the drop depends on the mainline/ramp ratio (see Q3) — [EPFL Infoscience](https://infoscience.epfl.ch/record/188341) [VERIFY].
- **Related empirical work:**
  - 'Increasing Freeway Merge Capacity Through On-Ramp Metering' (ITS Berkeley record) — [ITS Berkeley](https://its.berkeley.edu/node/3337) [VERIFY: authors, year and site not confirmed here];
  - 'Observations at a Freeway Bottleneck' — [ITS Berkeley](https://its.berkeley.edu/node/4139) [VERIFY];
  - 'Some Observed Queue Discharge Features at a Freeway Bottleneck Downstream of a Merge' — [ITS Berkeley](https://its.berkeley.edu/node/4122) [VERIFY];
  - 'Empirical study of traffic features at a freeway lane drop', *Journal of Transportation Engineering*, 131(6), p. 397 (2005; Bertini et al. per the ResearchGate profile) — [ASCE](https://ascelibrary.com/doi/10.1061/%28ASCE%290733-947X%282005%29131%3A6%28397%29) [VERIFY].
- Another capacity-drop paper is hosted at journals.sagepub.com, DOI 10.3141/2491-08 (*TRR* 2491) — [SAGE](https://journals.sagepub.com/doi/10.3141/2491-08) [SAGE][VERIFY: title and authors not seen].

### Inferences
- The classic Toronto and California sites come from loop data of the 1990s–2000s. Their geometry and detector layouts have probably changed, so re-extracting them from today's open data is uncertain. These papers are better used as **method templates** (oblique cumulative curves, lane-normalised density at breakdown) and as **priors on drop magnitude** (about 10 % in Cassidy & Bertini 1999).
- For a ramp-metered bottleneck with daily and weekly demand variation, MnDOT Twin Cities merges are the most practical **open** target, given the 30-s public archive and the published Srivastava & Geroliminis analysis.

### Gaps
- I did not confirm which three sites Chung et al. (2007) used. From memory, one was in Toronto and two in California, but this is unverified.
- I did not confirm the exact I-210 Pilot bottleneck locations or any published capacity-drop measurements there.
- I did not confirm the Bertini & Leal (2005) site (recalled as a UK lane drop with MIDAS-type data).
- Yuan, Knoop & Hoogendoorn's work on capacity drop and queue discharge from Dutch NDW-type data was recalled but not checked [VERIFY].

---

## Q5. Day-type clustering, benchmarking use, and practical extraction of ramp-metered bottleneck sites with recurrent oversaturation

### Takeaway
Clustering daily profiles into day types is well established. Typical inputs are 96 × 15-min daily volume profiles, with k-means or agglomerative methods, and results usually separate working days (often Mon / core weekdays / Fri / holiday) from weekends. For this repo, the defensible pipeline is: pick open 30-s/5-min sites, filter on data quality, find recurrent breakdowns via speed drops, and cluster *demand* (upstream mainline plus ramp) rather than bottleneck throughput.

### Cited Findings
- **Day-type clustering literature:**
  - 'Revealing representative day-types in transport networks using traffic data clustering', *Journal of Intelligent Transportation Systems* (2023) — [T&F](https://www.tandfonline.com/doi/full/10.1080/15472450.2023.2205020) [VERIFY: authors not confirmed];
  - 'Temporal pattern mining of urban traffic volume data: a pairwise hybrid clustering method', *Transportmetrica B* (2023). It uses 15-min counts, 96 points per day, and k-means — [T&F](https://www.tandfonline.com/doi/full/10.1080/21680566.2023.2185496) [VERIFY];
  - 'Analyzing highway flow patterns using cluster analysis' (Weijermars & van Berkum, recalled as IEEE ITSC 2005) — [ResearchGate 4180713](https://www.researchgate.net/publication/4180713_Analyzing_highway_flow_patterns_using_cluster_analysis) [VERIFY];
  - 'K-Means Clustering Method to Classify Freeway Traffic Flow Patterns' — [ResearchGate 305057141](https://www.researchgate.net/publication/305057141_K-Means_Clustering_Method_to_Classify_Freeway_Traffic_Flow_Patterns) [VERIFY].
- **Typical results (from these papers, as summarised in the search):** four types of working day, with pre-classification into vacation days, Mondays, core weekdays and Fridays; weekends differ; differences between days are location-specific. Agglomerative and k-means were "the most robust methods" for transport data, and cluster patterns can be used to detect and impute bad data — [T&F 2023 JITS](https://www.tandfonline.com/doi/full/10.1080/15472450.2023.2205020); [ResearchGate 4180713](https://www.researchgate.net/publication/4180713_Analyzing_highway_flow_patterns_using_cluster_analysis) [VERIFY: attribution of each statement to a specific paper is uncertain].
- **Benchmarking use of PeMS-derived data:** DCRNN (METR-LA, PEMS-BAY), ASTGCN (PeMSD4/8) and LargeST (8,600 sensors) are forecasting benchmarks, not control benchmarks (see Q2 for the citations).
- **Ramp data quality limits calibration.** Ramp detectors are "frequently unavailable or unreliable in practice" — [Chan et al. 2026](https://arxiv.org/abs/2605.23042) [VERIFY]. PeMS errors are highest on mainline, then on-ramps, then off-ramps — [Caltrans research note](https://dot.ca.gov/-/media/dot-media/programs/research-innovation-system-information/documents/research-notes/task3861-rns-11-21-a11y.pdf) [VERIFY].

### Inferences (practical extraction recipe; my synthesis, not a published protocol)
1. **Choose the source.** MnDOT (public JSON/zip, 30-s, no login) or PeMS (login, 30-s clearinghouse or 5-min). Record the access date and terms (status as of 2026-10-04).
2. **Screen candidate sites.** Look for a mainline station pair straddling an on-ramp merge, with on-ramp passage (and ideally queue) detectors and an off-ramp counter between the stations. Use the data.ca.gov "Bottlenecks" product (PeMS-derived, not inspected) or the PeMS bottleneck reports as a first screen.
3. **Filter on quality.** Keep station-days with high observed (non-imputed) share at *all* boundary detectors: upstream mainline, on-ramp, off-ramp, downstream. Drop holidays and incident days, or label them separately. Pre-register the thresholds.
4. **Detect recurrent oversaturation.** Flag days where the upstream speed drops below a threshold (e.g. 70–80 km/h) while the downstream speed stays high (an active bottleneck, per the Cassidy–Bertini logic). Require the same weekday time window on ≥ N % of working days.
5. **Measure the capacity drop.** Use oblique cumulative counts or lane-normalised density at the breakdown (Cassidy & Bertini 1999; Chung et al. 2007). Check the dependence on ramp share (Srivastava & Geroliminis 2013).
6. **Cluster demand, not throughput.** Cluster *upstream boundary demand* (mainline in + on-ramp demand, ideally ramp queue + passage) into day types. Bottleneck throughput is censored by the capacity itself and by the existing metering. Assign the day-type clusters to the tuning, validation and test seed blocks *before* fitting, to stay consistent with the repo's protocol-before-data rule.
7. **Mind control confounding.** Observed on-ramp passage flows under active metering equal the metered release, not the demand. Use ramp queue detectors (if present) or entrance counts to reconstruct demand. Otherwise disclose that ramp demand is estimated.
- These steps are my synthesis for the author's use and have not been validated against a specific published protocol.

### Gaps
- I did not find a published, open, end-to-end "freeway day-type → SUMO/METANET demand profile" pipeline with code. The closest is Chan et al. (2026) for METANET.
- I did not verify which MnDOT detector types (ramp queue, passage, merge, green/release counts) are present in the public feed. This is recalled, not confirmed [VERIFY]; check a sample `.c30.json` file and the MnDOT detector metadata before relying on it.
- No source was checked in this session on how often PeMS-based clustering studies exclude imputed data. Treat this as a methodological risk to check per paper.
