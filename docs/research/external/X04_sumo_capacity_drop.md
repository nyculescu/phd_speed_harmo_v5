# X04: SUMO driver-model settings that reproduce a motorway capacity drop

**Model:** Opus 5.5 · web search ON (max 25) · effort high · max tokens 16,000 · system prompt: Shared rules (README)

## Prompt (paste as the user message)
```
I simulate a motorway in the microscopic simulator SUMO (version 1.27, step 0.2 s): three lanes reduced to two at a lane drop (SUMO "zipper" node), human drivers modelled with SUMO's Extended IDM (EIDM) car-following model and the LC2013 lane-change model, mostly at default parameters. Test runs show NO capacity drop: once a queue forms at the lane drop, the queue discharge flow downstream (about 1,900-1,980 veh/h/lane) is equal to or higher than the maximum flow before breakdown. Field studies report that discharge after breakdown is lower than pre-breakdown capacity.

I need PUBLISHED evidence (peer-reviewed or official SUMO documentation) on how to make SUMO, or comparable microscopic models, reproduce a realistic capacity drop at lane drops and merges, with parameters chosen from the literature, NOT tuned to my own data.

Find and report:
1. Field values of the capacity drop at lane drops and on-ramp merges: magnitude (%), queue discharge rate per lane, how it was measured, and its dependence on queue speed (e.g. Yuan, Knoop, Hoogendoorn; Chung, Rudjanakanoknad, Cassidy; Srivastava and Geroliminis; Oh and Yeo review). Give numbers with sources.
2. Studies that reproduced a capacity drop in SUMO: which car-following model (Krauss, IDM, EIDM, ACC, Wiedemann), which parameters (e.g. actionStepLength / reaction time, tau, sigma, accel/decel, EIDM-specific parameters such as driver-error or "taction" settings, minGap), which lane-change parameters (lcCooperative, lcSpeedGain, lcAssertive, lcImpatience, lcStrategic, lcSigma), which node type (zipper vs priority merge), and the resulting drop magnitude. Include SUMO Users Conference papers and journal papers.
3. Known mechanisms that produce a capacity drop in microscopic models: slow acceleration out of queues, reaction delays and action steps, lane-change friction or voids at merges, driver heterogeneity. Which of these SUMO can represent, with which parameters, and with what evidence.
4. Known SUMO-specific pitfalls: e.g. the zipper node discharging "like a metronome", unrealistically high discharge with default models, step-size effects, or lane-change models that move bottlenecks upstream.
5. A ranked list of at most 4 concrete, literature-backed parameter sets I could pre-register as discrete candidates, each with its source, the expected drop magnitude, and the risks (e.g. collisions, unrealistic stop-and-go).

Rules: separate field data from simulation results; give the SUMO version used in each study when stated; mark any parameter value not read in a source as [VERIFY]. At most about 3,500 words.
```

## Run 2 (2026-10-13 21:47): stopped before answering
- **Status:** the model ran 7 web searches and 2 web fetches (both fetches failed: `url_not_accessible`, `url_not_in_prior_context`). It then called the **browser tool** (`navigate` to the SUMO EIDM docs page, then `get_page_text`). The Workbench waits for you to run that tool, so the response **ended with `stop_reason: tool_use` and no answer text**.
- **Cost:** 260,738 input tokens (mostly search results), 2,504 output tokens.
- **Fix for run 3:**
  - turn **off** `browser_toolset`;
  - keep `web_search` on (set max uses 15);
  - keep `web_fetch` on (max uses 10, max content tokens about 20,000) to cap the input cost;
  - paste the **Shared rules** into the System field (it was empty);
  - set max tokens 32,000 and effort high.
- **Searches run** (kept for reference):
  - SUMO simulation capacity drop reproduce lane drop merge
  - Yuan Knoop Hoogendoorn capacity drop relationship speed in congestion queue discharge rate
  - Chung Rudjanakanoknad Cassidy 2007 relation between traffic density and capacity drop three freeway bottlenecks percent
  - Srivastava Geroliminis 2013 empirical observations capacity drop freeway merges ramp control first-order model
  - Oh Yeo review capacity drop empirical literature magnitude Transport Reviews
  - https://www.tandfonline.com/doi/full/10.1080/21680566.2016.1245163
  - Yuan Knoop Hoogendoorn queue discharge rate linear function speed in congestion veh/h per lane A4 A12 capacity drop 26%
  - https://sumo.dlr.de/docs/Definition_of_Vehicles%2C_Vehicle_Types%2C_and_Routes.html
  - SUMO zipper merge capacity unrealistic discharge github issue

## Run 1 (2026-10-13): no web search, truncated (orientation only)
> **Run quality (checked by Claude Code):**
> - **No web search ran.** The response holds only a thinking block and a text block; there are no search results. The model says so itself ("I could not query databases"). Every source below comes from model memory and is unverified.
> - **The answer was cut off** (`stop_reason: max_tokens`; 16,000 output tokens, 11,275 of them thinking). Section 3 ends mid-table, and sections 4–5 (the SUMO pitfalls and the ranked parameter sets) are missing.

# Capacity drop at lane drops and merges in SUMO and comparable microscopic models: a literature review

## Caveat on sourcing

I could not query databases or the SUMO documentation live. Everything below comes from my knowledge of the literature.

- Bibliographic facts I am confident of are given plainly.
- Any number or parameter value I cannot attribute with certainty to a page in the source is marked **[VERIFY]**.
- Most importantly, **I do not know of a peer-reviewed study that reproduces a calibrated capacity drop at a SUMO zipper lane drop with EIDM**. Treat that as a gap to confirm with a search of the SUMO User Conference proceedings (EPiC series 2018–2019; TIB Open Publishing / SUMO Conference Proceedings 2020–2024).

Candidate sets in Section 5 therefore borrow from comparable models whose capacity-drop behaviour is published. They do not come from SUMO lane-drop studies.

---

## 1. Field evidence

### 1.1 Magnitudes and measurement

| Source | Site type | Reported drop / discharge | Method |
|---|---|---|---|
| Hall & Agyemang-Duah (1991), *TRR* 1320 | Merge, QEW Toronto | ≈ 5–6 % **[VERIFY]** | Detector flows before and after breakdown; pre-queue maximum compared with mean queue discharge |
| Cassidy & Bertini (1999), *Transp. Res. B* 33(1) | Two merge bottlenecks, Toronto | Discharge ≈ 10 % below pre-queue peaks **[VERIFY]**; discharge rate nearly constant over long periods | Oblique (rescaled) cumulative vehicle counts and occupancies at detectors downstream of the bottleneck |
| Bertini & Leal (2005), *J. Transp. Eng.* 131(6) | Two UK motorway bottlenecks | ≈ 10 % **[VERIFY]** | Same oblique-curve method |
| Chung, Rudjanakanoknad & Cassidy (2007), *Transp. Res. B* 41(1), 82–95 | Three freeway bottlenecks, incl. merge/lane-drop types **[VERIFY which]** | Drops of a few % up to ~15–18 % **[VERIFY]**; **drop grows with density in the queue upstream (specifically in the shoulder/merging lane)** | Oblique cumulative counts; drop related to occupancy upstream |
| Cassidy & Rudjanakanoknad (2005), *Transp. Res. B* 39(10) | Isolated on-ramp merge | ≈ 10 % drop; restored by metering the on-ramp so the shoulder-lane queue did not form **[VERIFY %]** | Field experiment with metering |
| Srivastava & Geroliminis (2013), *Transp. Res. C* 30, 161–177 | On-ramp merges, Minnesota (Twin Cities) **[VERIFY]** | Drop of order 10–20 % **[VERIFY]**; **magnitude depends on on-ramp flow** and is reduced under ramp control | Loop detector data; drop integrated into a first-order (LWR/CTM) model with merge-ratio-dependent capacity |
| Oh & Yeo (2012), *TRR* 2286; Oh & Yeo (2015), *Transp. Res. B* 77 | Review plus merge sites (California) | Literature range ≈ 3–20 % **[VERIFY exact range]**; 2015 paper relates lower discharge to stop-and-go waves and lane changes in the recovery flow | Review; detector and trajectory analysis |
| Yuan, Knoop & Hoogendoorn (2015), *TRR* 2491, "Capacity drop: relationship between speed in congestion and the queue discharge rate" | Dutch motorway bottlenecks, including lane drop **[VERIFY sites]** | **Queue discharge rate increases (roughly linearly) with speed in congestion**; drop largest when the queue is near standstill. Drops up to ~25–30 % at very low speeds reported **[VERIFY]** | Head/tail wave speeds and fundamental-diagram estimation from loop data |
| Yuan, Knoop, Leclercq & Hoogendoorn (2017), *Transportmetrica B* 5(2) | Lane drop | Standing queue vs stop-and-go wave give different discharge rates, again governed by congested-state speed **[VERIFY direction and numbers]** | Detector / trajectory data |
| HCM 6th ed. (2016), freeway facilities chapter | Generic bottleneck | Default queue discharge ≈ 7 % below pre-breakdown capacity **[VERIFY chapter and value]** | Synthesis |

### 1.2 Takeaways for your study

1. **Typical magnitude.** The drop is about 5–15 % in most merge and lane-drop studies, with values up to ~20–30 % at low queue speeds. Queue discharge rates of about 1,600–1,850 veh/h/lane are common in reported data **[VERIFY per source]**. Your 1,900–1,980 veh/h/lane is at the high end.
2. **Dependence on queue state.** The drop depends on queue speed or density (Chung et al. 2007; Yuan et al. 2015) and on merge ratio (Srivastava & Geroliminis 2013; Leclercq et al. 2011, below). The drop is therefore not a fixed constant. A model that produces a constant drop independent of queue speed is not reproducing the empirical mechanism.
3. **Measurement protocol.** Field studies measure downstream of the bottleneck, using cumulative curves to separate the pre-queue peak from stationary discharge. Use the same protocol in simulation (Section 4), otherwise comparisons are not like-for-like.

---

## 2. Simulation studies

### 2.1 Studies in SUMO itself

| Source | Relevance | Version | Notes |
|---|---|---|---|
| Krajzewicz et al. / Krauß (1998), DLR thesis "Microscopic modeling of traffic flow: investigation of collision free vehicle dynamics"; Krauß, Wagner & Gawron (1997), *Phys. Rev. E* 55, 5597, "Metastable states in a microscopic model of traffic flow" | The Krauss model (SUMO's default) shows **metastability and hysteresis, so outflow from a jam is below maximum free-flow throughput**, for suitable combinations of acceleration *a*, deceleration *b* and noise σ. Low *a* plus nonzero σ favours a drop. | Pre-SUMO / theory | Reported in terms of model parameters, not lane drops |
| Erdmann (2014), "SUMO's lane-changing model", SUMO 2014 conference (LNCS / Springer, *Modeling Mobility with Open Data*, 2015) | Defines LC2013 (strategic, cooperative, speed-gain, keep-right motivations; `lcAssertive`, etc.) | SUMO ≈ 0.2x **[VERIFY]** | Not a capacity-drop study; behavioural basis for lane-change parameters |
| Salles, Kaufmann & Reuss (2020), "Extending the Intelligent Driver Model in SUMO and Verifying the Drive Off Trajectories with Aerial Measurements", SUMO User Conference 2020 | **Origin of EIDM.** Adds HDM-type reaction time, estimation errors, driving errors, jerk limits and a drive-off acceleration profile; drive-off verified against drone data | SUMO 1.7/1.8 **[VERIFY]** | Validated at **intersection drive-off**, not motorway discharge; no capacity-drop result I am aware of |
| TransAID project (H2020) deliverables and papers, e.g. Lücken et al. (2019) SUMO conference on control transitions; Mintsis et al. on work-zone lane drops **[VERIFY titles]** | Motorway merges and lane drops in SUMO with LC2013 parameter adjustments | SUMO 1.1–1.6 **[VERIFY]** | I cannot confirm they report a calibrated capacity-drop magnitude, nor which values. Check deliverables D3.1 / D6.2 **[VERIFY]** |

**Bottom line:** I cannot cite a SUMO paper that states "with parameters X, a zipper lane drop yields a Y % drop." If your search confirms this gap, say so explicitly in the pre-registration. It justifies importing parameters from the general car-following literature.

### 2.2 Comparable microscopic and mesoscopic models with published capacity-drop behaviour

**IDM and its descendants**
- **Treiber, Hennecke & Helbing (2000)**, *Phys. Rev. E* 62, 1805, "Congested traffic states in empirical observations and microscopic simulations."
  - IDM parameters: v0 = 120 km/h, T = 1.6 s, s0 = 2 m, a = 0.73 m/s², b = 1.67 m/s², δ = 4.
  - Result: the **dynamic capacity (outflow from congestion) Q_out is below Q_max**, giving metastability and hysteresis.
  - Treiber & Kesting, *Traffic Flow Dynamics* (Springer 2013), explain that Q_out decreases with lower *a* and higher T, and give a "highway" set: T = 1.0 s, s0 = 2 m, a = 1.0 m/s², b = 1.5 m/s² **[VERIFY exact table]**.
- **Treiber, Kesting & Helbing (2006)**, *Physica A* 360, 71–88, "Delays, inaccuracies and anticipation in microscopic traffic models" (Human Driver Model, HDM).
  - Mechanisms: reaction time, estimation errors, multi-vehicle anticipation.
  - These are the conceptual basis of EIDM's `treaction`, `sigmagap`, `sigmaleader`, `tPersEstimate` and related parameters.
- **Treiber & Helbing (2003)**, *Phys. Rev. E* 68, 046119, "Memory effects in microscopic traffic models."
  - Drivers increase their time gap after spending time in congestion. This directly produces a capacity drop.
  - SUMO has no native parameter for this.
- **Kesting, Treiber & Helbing (2010)**, *Phil. Trans. R. Soc. A* 368, 4585–4605.
  - Enhanced IDM / constant-acceleration heuristic (coolness c = 0.99), designed for ACC.
  - This is the source of EIDM's `ccoolness = 0.99`. It reduces over-reaction to cut-ins, which plausibly *suppresses* merge-induced voids (my inference).

**Stochastic and behavioural car-following**
- Yuan, Laval, Knoop, Jiang & Hoogendoorn (2019), *Transportmetrica B* 7(1), "A geometric Brownian motion car-following model: towards a better understanding of capacity drop." Stochastic acceleration reproduces queue-speed-dependent discharge.
- Chen, Laval, Zheng & Ahn (2012), *Transp. Res. B* 46(6). Driver timidity and aggressiveness heterogeneity produces oscillations.
- Jiang et al. (2014), *PLoS ONE*, and Tian et al. (2016), *Transp. Res. B*. Platoon experiments showing concave growth of oscillations. A stochastic-acceleration lineage similar to the GBM model above.

**Lane-change and merge mechanisms**
- Laval & Daganzo (2006), *Transp. Res. B* 40(3), "Lane-changing in traffic streams." Lane changers with bounded acceleration create voids, which reduce discharge.
- Leclercq, Laval & Chiabaut (2011), *Transp. Res. B* 45(9), "Capacity drops at merges: an endogenous model." Drop depends on merge ratio and on speed of merging vehicles.
- Leclercq, Knoop, Marczak & Hoogendoorn (2016), *Transp. Res. C* 62. Analytical link between merge drop and congested speed.
- Schakel, Knoop & van Arem (2012), *TRR* 2316, LMRS (lane-change model with relaxation and synchronization). Relaxation after lane changes matters for discharge. Not available in SUMO; SL2015/LC2013 do not implement LMRS relaxation **[VERIFY]**.

**Wiedemann / VISSIM:** I have no reliable citation for a published, literature-parameterised lane-drop capacity drop. Omit, or search specifically.

---

## 3. Mechanisms and SUMO representability

| Mechanism | Literature | SUMO representation | Evidence quality in SUMO |
|---|---|---|---|
| **Slow or bounded acceleration out of queues** (outflow below max flow) | THH 2000; Krauß 1997; Laval & Daganzo 2006 | `accel` (all models); EIDM drive-off shaping via `taccmax`, `Mflatness`, `Mbegin`, `jerkmax`; IDM `delta` | Strong in theory. EIDM drive-off validated by Salles et al. 2020 at intersections only |
| **Reaction delay / action step** | Treiber et al. 2006 (HDM); Krauß | `actionStepLength` (vehicles update decisions only every *n* s; generic); EIDM `treaction` with `tPersDrive` (how long drivers maintain an action) | Documented features. Quantitative capacity effect in SUMO not published as far as I know. Large values raise collision risk |
| **Estimation and driving errors** | HDM 2006 

## Run 3 (2026-10-13): stopped again on the browser tool; X04 abandoned
6 web searches and 1 fetch were made, then `stop_reason: tool_use` (browser `navigate`), with no answer text; 141,863 input tokens. Author decision: stop using the Console for X04 and do the research in Claude Code (`docs/research/capacity_drop_lit_v0.md`).
