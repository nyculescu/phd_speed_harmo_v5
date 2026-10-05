# The PhD path with daily demand patterns, explained from scratch

*v1, 2026-10-05. A plain-language proposal for the thesis path, subject and description. v1 adds the author's answers and corrections of the same day.*

*It builds on:*
- *the idea note (`docs/plans/day_pattern_idea_v0.md`);*
- *the literature report (`docs/review/day_pattern_research_v0.md`);*
- *the plant options and draft gate (`docs/plans/day_pattern_plants_v0.md`, `day_pattern_gate_draft_v0.md`);*
- *the lab results (`docs/lab/STATUS.md`, `docs/lab/gate_ctx_r6/`, `docs/lab/day_pattern/`).*

*Numbers come from those files. Where a number comes from a paper that was only partly read, it says "unverified"; sources not read in full are marked [VERIFY]. **Nothing in the new part of the path is proven yet.** It is a plan to test an idea, not a result.*

---

## 1. The whole story in one paragraph

The thesis must show that **learning-based control** can control road traffic measurably better than the best **tuned** versions of the control methods already proven in practice. Here, learning-based control means deep reinforcement learning (DRL), used **on its own or combined with one or more proven control families**. Simulations of single vehicles (microscopic) or of traffic as a flow (macroscopic) both count.

So far one result has held up under strict testing:
- **R6:** a DRL "dial-turner" that adjusts a proven ramp meter beat the best tuned alternatives by **2.5–4.3 %**. The win is small and narrow, and it was obtained on a simulated road that later failed a realism test.

The new idea, which the author had in v4 and now revives with better tools, is about **the shape of the whole day**. Demand follows daily shapes: two rush hours, one big peak, a weekend ramp, a quiet day. When peaks exceed what the road can carry, the detectors at the bottleneck **cannot see how big they really are**.

A controller that learns the day's pattern, observing a **long stretch of road** rather than one spot, could do three things:
- act before the peak;
- use speed limits and ramp meters together;
- treat a heavy Tuesday differently from a light one.

The hardest part, which the author identified in earlier work, is that a learning controller sees only "demand is rising" or "demand is falling". It struggles to learn *when* to act. That problem gets its own section and its own study (§5).

Every step has a cheap kill test. Only **positive** DRL results count as thesis papers, so the tests exist to find out early where effort will pay off.

---

## 2. What exactly the thesis must show

### 2.1 The claim

> **Learning-based control (DRL), alone or as a hybrid with one or more proven control families, controls road traffic measurably better than the best tuned proven control.**

The proven control families, any of which can be a competitor or a partner in a hybrid:

| Family | What it does | Traffic example |
|---|---|---|
| Rule- or logic-based | Fixed if-then recipes | an event detector that switches a meter setting |
| Classical feedback | Measures the output and corrects towards a target | ALINEA ramp metering |
| Optimal | Computes the best actions for a model and a cost | an optimal metering plan for a known demand curve |
| Robust | Works acceptably for a whole range of uncertain models | a robust speed-limit design |
| Adaptive (formal sense) | Adjusts its own parameters online while running | ALINEA that estimates its critical occupancy on the fly [VERIFY] |
| Predictive (MPC) | Predicts with a model, plans a few steps, acts, re-plans | MPC with a fitted METANET model |
| Model-based learning control | Learns a model from data, then controls with it | learning-based MPC |
| Data-driven / model-free | Learns the controller directly from data, no explicit model | **model-free DRL (PPO, SAC, RecurrentPPO)** |
| Hybrid | Two or more of the above | R6: DRL choosing settings of a feedback meter |

### 2.2 Where DRL sits: the author's view, checked

The author's view, "DRL is a learning-based control", is **correct**. The control literature treats it the same way:
- Sutton, Barto & Williams (1992) call reinforcement learning "direct adaptive optimal control";
- Lewis & Vrabie (2009) present it as approximate (adaptive) dynamic programming for feedback control;
- Recht (2019) surveys it from the control side;
- Hewing et al. (2020) review learning-based MPC as part of the same field.

All four are [VERIFY]: their bibliographic details are checked, but none was read in full.

Three precision points, because the words matter:

1. **DRL is inside the list, not outside it.** Model-free DRL *is* data-driven/model-free control; model-based DRL *is* model-based learning control. So "DRL vs learning-based control" is not a contrast. DRL is one way of doing learning-based control.
2. **"Adaptive" in the title is not the same as formal "adaptive control".**
   - In control theory, *adaptive control* means a controller that **changes its own parameters while it runs** (self-tuning regulators, model-reference adaptive control).
   - A DRL policy that was trained and then frozen for testing does **not** change its parameters. A recurrent one adapts its **actions** to what it has seen (it infers the situation from history), which is adaptation in the everyday sense.
   - The thesis title's "adaptive" is fully met in that sense. If the thesis ever claims to beat *adaptive control*, a formally adaptive competitor (one that estimates parameters online) must be in the comparison.
3. **DRL approximately solves an optimal-control problem,** the same Bellman problem as dynamic programming, but it gives no guarantee of optimality. That is why it is always compared, never assumed best.

> **Analogy: the chef and the recipe book.** A recipe (rule-based), a cook who tastes and corrects (feedback), a cook who plans the whole menu from a known guest list (optimal / predictive), a cook who adjusts the recipe itself as the evening goes (adaptive): these are the proven families. A cook who learned by cooking ten thousand dinners (DRL) is a *learning* cook. The thesis must show the learning cook, alone or helping one of the others, serves measurably better dinners than the best-prepared proven cooks.

This definition applies to the v5 and v6 work alike.

---

## 3. Where the thesis stands today

| What | Result | What it means |
|---|---|---|
| **R6** (BN4 bottleneck, DRL scheduling a proven ramp meter, 210 fresh test runs) | **−4.3 %** delay vs a tuned event detector; **−2.5 %** vs an MPC with a model fitted on separate data | The one confirmed hybrid win (DRL + feedback). Small, real and narrow. |
| R6's limits, found 2026-10-04 | It doesn't transfer to other event sizes (surges +16 % worse). Its training never fully settled. Its simulated road **fails the realism test** (queue discharge 900 veh/h per lane; real roads 1,600 or more) | It holds for the simulator as specified, not for a realistic road. Whether R6 counts towards the thesis is still open (§12). |
| Lead 1 and the context-aware R6 restart | Stopped by their own pre-registered checks (room to win 3.3 %; the road failed realism) | — |
| Earlier speed harmonisation (v5 Round 4) | One well-chosen *constant* speed limit captured almost all the benefit; adapting it added only 0.4–4 % | The narrow demand band again (§5.3) |
| v6 projects | Tuned methods came within 0–5 % of an all-knowing reference in six problems | Tuned control is hard to beat |

---

## 4. The idea: learning the shape of the day

### 4.1 Days have shapes, and real days are never clean letters

| Shape | Typical day | Everyday analogy |
|---|---|---|
| **M** (bimodal) | weekday morning and afternoon/evening peaks | a restaurant's lunch and dinner rush |
| **^** | one peak | a single Sunday-brunch crowd |
| **/** or **\\** | builds up or fades all day (often weekends) | a shop before a holiday, or the day after |
| **free flow** | almost no demand | a quiet bank holiday |

Real days vary in how high and wide each peak is, how fast demand rises and falls, how sharp the peak is, and how far apart the peaks are (§5.2). So the plan treats shapes as a **continuum**: the letters are only labels, and no controller is ever told "today is an M".

### 4.2 Why counts hide the true peak

When a peak asks for more than the road can carry, the extra cars wait in queues. The detector at the bottleneck counts only what gets through, and that can never exceed capacity.

```
 what drivers want (demand)               what the bottleneck detector counts (volume)

          /\        /\                              _______   _______
         /  \      /  \                            /       \_/       \
        /    \____/    \           ──►            /                   \
  _____/                \_____               ____/                     \____
```

> **Analogy: the turnstile at a football ground.** One turnstile can never count more people per minute than it lets through. Ten thousand fans arriving in ten minutes look exactly like five thousand arriving steadily over twenty. Only the queue outside tells you which day it was.

So timetables fitted to counted volumes (common practice) **underestimate heavy days**. Engineering guidance gives worked examples of 16–20 %; those are examples, not field measurements.

### 4.3 What adaptation buys, and the words used for it

A controller that has learned the day's pattern could:
1. **act before the peak,** rather than after;
2. **use speed limits and ramp meters together** along a corridor;
3. **treat a heavy Tuesday differently from a light one.**

That is what "adaptive" in the thesis title means here. Following §2.2, the careful wording is:
- a **learning-based** (DRL) or **hybrid** controller that **adapts its actions to the day**;
- not "adaptive control" in the formal sense, unless online parameter adaptation is part of the design.

### 4.4 A long road with detectors along it

Acting before the peak is only possible if the controller can **see the peak coming**. A controller watching only the bottleneck sees the problem when it is already there, and the local data piles up into a picture that misrepresents the whole road.

So the corridor must be **long enough**, with **detectors distributed along it**:
- upstream far enough that a rise in demand is seen minutes before it reaches the bottleneck. At motorway speeds, 10 km of upstream road gives roughly 6 minutes of warning; this is a rough figure, to be sized from the data;
- every on-ramp's queue and passage detectors, and the off-ramps, so the flows balance.

Real roads have such detectors: the Minneapolis–St Paul freeways have stations roughly every half to one kilometre.

> **Cost note.** Instrumenting a long road densely may not be cost-effective for a road authority. The thesis prioritises **new, validated knowledge** (does seeing the whole road let a learner act earlier and better?) over engineering economics, while keeping costs within plausible bounds.

---

## 5. The hardest part: learning *when* to act

*This section records the author's diagnosis from earlier work. It is treated as its own problem, whatever the rest of the design turns out to be.*

### 5.1 The problem in one sentence

**Whatever the day's pattern, a learning controller observing traffic sees only that demand is rising or falling. From that alone it cannot tell whether this rise is a small bump, a sharp spike or the start of a long broad peak, so it struggles to learn when acting pays off.**

> **Analogy: the lift with no floor display.** You feel the lift start to rise. Is it going up one floor or twenty? From the feeling of acceleration alone you cannot tell. You need a floor display (where you are in the day), a memory of how far you've already gone (cumulative demand so far), or a view out of a window (upstream detectors).

### 5.2 The shapes the controller must cope with

Demand over time is built from a few primitive shapes, over the whole day or over several hours:

| Primitive | Description |
|---|---|
| constant | flat demand |
| step increase / decrease | a sudden jump up or down |
| ramp-up / ramp-down | a steady rise or fall |
| triangular peak | rises then falls, sharp top |
| trapezoidal peak | rises, holds a plateau, falls |
| Gaussian / bell-shaped peak | smooth rise and fall |

A real day combines them into a **highly variable multi-peak profile**. The peaks differ in amplitude, duration, rising and falling rates, sharpness and spacing, which makes the profile complex and **non-stationary** (its statistics change through the day):

```
Demand
  ^
  |                                       __________
  |                                      /          \                    /\
  |                     /\              /            \                  /  \
  |                    /  \____________/              \________________/    \__
  |       ____________/                                                        \
  |      /                                                                      \
  |_____/                                                                        \_____
  +------------------------------------------------------------------------------------> time
              ↑                 ↑                  ↑                               ↑
            small             sharp           broad/flat                        sharp
            peak              peak               peak                           peak
```

The **M** (bimodal) weekday profile is the simplified, common case. The design must cope with the general case above.

### 5.3 The narrow band where an M turns into a trapezoid

In the author's earlier work, raising a full day's demand from X to X + Y vehicles per hour, with Y quite small, quickly turned the traffic's **M into a trapezoid**.

```
 demand X: two peaks, traffic recovers between them     demand X + Y: one long congested plateau

        _       _                                             _______________
       / \     / \                                           /               \
   ___/   \___/   \___                                   ___/                 \___
```

**Why this happens** [Inference, consistent with the clipping physics of §4.2]:
1. Once the morning peak exceeds capacity, a queue forms.
2. It drains only at the queue-discharge rate, which is lower still if the bottleneck has broken down (the capacity drop).
3. If the morning queue has not drained before the evening demand arrives, the valley never recovers, and the two peaks merge into one long plateau.

Capacity is a hard threshold, and a breakdown "locks in" the lower discharge rate. So the switch from "two separate peaks" to "one long congested plateau" happens over a **narrow range of demand levels**.

**Why it matters:**
- **Below the band,** there is little to control.
- **Well above it,** the day is one long queue, and control can mostly only move delay around.
- **Inside the band,** a controller can decide whether the M survives or merges. That is where control matters most, where learning is hardest, and where a "narrow demand band" in the experiments really was the true picture, not a mistake.
- **Consequence for the design:** demand levels must be set **relative to each corridor's transition point** and concentrated around it, not spread evenly.
- **The real data can check this:** on which days does the real bottleneck show an M, and on which a trapezoid?

### 5.4 Possible causes of the past failures: design all of them deliberately

The author's list of what may have gone wrong before, each on its own or in combination:

| Area | Choices that must each be designed and justified |
|---|---|
| **Network topology** | detector placement; bottleneck and disturbance location; VSL / speed-actuation locations; control-zone length; speed-actuation timing; magnitude of speed change; spatial propagation of the speed recommendation; lane-level topology |
| **Controller family** | algorithm; hyperparameters; policy type; neural-network architecture; data normalisation; training configuration; environment set-up |
| **State–action–reward framework** | what is observed, what is decided, what is rewarded |
| **The combination** | even if each choice is right on its own, the combination can be wrong |

So the system is designed **as a whole**:
- every choice is written down with its reason before the runs;
- each is checked on its own (for example, does a speed limit at this location actually change the flow?);
- the main ones are varied at least once, so that the result isn't an accident of one combination.

### 5.5 How the design answers the timing problem

These responses are proposals for discussion, not decisions.

1. **Give the controller its bearings.** The observation includes:
   - the time of day and the calendar day type (the floor display);
   - cumulative demand since the morning (how far the lift has gone);
   - upstream detectors along the long road (the window);
   - ramp queues and travel times, which still carry information when bottleneck counts are clipped;
   - a memory (recurrent policy) to integrate all of this.
2. **Build the training days from the primitives, fitted to real days.**
   - Each day is a sum of peaks, each with its own amplitude, timing, rise rate, plateau length, fall rate and sharpness, plus spacing between peaks.
   - The joint statistics come from real Minneapolis–St Paul days, so the predictability in the training days is real, not invented by us.
   - Demand levels are concentrated around each corridor's M-to-trapezoid transition.
3. **A predictability check before any DRL.**
   - Before training, test whether **any** predictor, an ordinary forecasting model rather than DRL, can tell from the same observations how much demand is still coming and when the breakdown will happen.
   - If it can't, no policy can time its actions from those observations either: stop or add better observations.
   - The check is cheap and needs no training.
4. **A learnability ladder for DRL on its own** (the separate study the author asked for):
   - train and test on increasingly hard days: constant → step → ramp → triangle → trapezoid → bell → two peaks → the full variable multi-peak day;
   - at each rung, measure whether the policy acts at the right *time* (its action timing against the true onset), not only its overall score;
   - a "context head" that tries to predict the time to the next peak shows whether the policy's memory has learned the day's phase.
   - This tells us exactly at which level of difficulty DRL alone stops learning, which is new knowledge in itself, and which design choices move that point.
5. **Two timescales.**
   - Fast feedback (ALINEA, speed-limit feedback) handles seconds to minutes.
   - The learning layer decides every 5–15 minutes in the hybrid design, or every 30–60 s for DRL alone, with its time horizon sized to hours, not minutes.

> **Analogy: learning to drive a hilly road at night.** With only the engine's feel (rising or falling), you brake late at every crest. With headlights (upstream detectors), a map (time of day and calendar), and a memory of the road so far (a recurrent policy), you can ease off *before* the crest. Training first on gentle hills, then on steep ones, then on a mix, shows exactly where you stop coping.

---

## 6. Why it is still unproven, and might well fail

1. **Feedback controllers already adapt to live demand.** ALINEA watches the traffic just downstream and reacts.
   > **Analogy: the thermostat** doesn't need to know thirty people walked in; it feels the room warming up.
2. **Most of the "day type" is known from the calendar.** Published clustering finds 3–6 day types, closely matching weekday versus weekend (unverified).
3. **Against tuned feedback control, published learning-based gains are about 0–4 %.**
   - In one study's 20 paired runs, results range from 21 % better to 5 % worse; another study's learner was 0.6 % *worse* than ALINEA. Some of these papers were only partly read.
   - Large published gains come from weak competitors, or from planners given the true future.
4. **No study was found that tests "day-type knowledge on top of tuned feedback"** against tuned feedback alone.
5. **The timing problem (§5) is real,** and it defeated DRL alone in earlier work.

**Prior expectation, written before any test:** a KILL at the headroom gate is the most likely outcome. The literature's prior for hybrid gains is 1.5–6 %.

**What could make it work** (hypotheses):
- heavy days that counts hide;
- acting before breakdown, using the long instrumented road;
- coordinating several ramps and speed limits;
- competitors that, like the real ones, rely on counts and imperfect forecasts.

---

## 7. How it will be tested: kill early, kill cheap

> **Analogy: the friend who already knows how busy today will be.** A controller that knows the day's true demand curve in advance is compared with the best honest controllers. The gap is the biggest prize any learner could win. Under 10 %: don't build the learner.

**The honest side.** Every method is tuned on separate days; the side covers every family the claim names:
- timetables per calendar day type, fitted to counted volumes (as in practice);
- pattern matching on the first hour;
- ALINEA, PI-ALINEA and HERO (coordinated ALINEA);
- **a formally adaptive metering variant (online parameter estimation)** [to be added, §2.2];
- speed-limit feedback (MTFC) and a wave-resolving speed-limit scheme (SPECIALIST);
- an MPC whose model and forecast are fitted on separate days, never given the truth.

**The informed reference:** the same timetable or MPC, fed the day's **true** demand.

**The data split:**
- demand is reconstructed from detectors **upstream** of the congestion;
- tuning uses 2023 days;
- the gate runs on **2024** days that nobody tuned on.

**The rule:** KILL unless the gap is at least 10 % with statistical confidence.

**The stop rule for heavy days:** cars queuing at the entries and still moving count as normal oversaturation. Teleports, zero outflow for 10 minutes, or a car stuck for more than 600 s count as gridlock.

**The simulated road: two models, on purpose.**

| Role | Model | Why |
|---|---|---|
| Gate and training | **METANET**, a fast "fluid" model calibrated to a real Minneapolis–St Paul corridor | A full day runs in seconds. It reproduces the stop-and-go waves that speed limits act on. |
| Confirmation (only after a GO) | **SUMO**, a car-by-car simulator, rebuilt for the corridor | A check that the ranking isn't an artefact of the fluid model. It must first pass the realism test. |

---

## 8. What has been done so far (2026-10-04 to 2026-10-05)

| Step | Result |
|---|---|
| Literature review, five strands | No study tests day-type knowledge on top of tuned feedback. Gains against tuned feedback are about 0–4 %. Counts hide heavy days. Minneapolis–St Paul (MnDOT) has the best open ramp data. |
| Simulated-road choice | METANET for the gate, SUMO for confirmation; speed harmonisation and ramp metering both in scope (author decision). |
| SUMO pre-check (88 runs) | **Passed.** On a plain lane, SUMO's drivers discharge a queue at 2,300–2,650 veh/h per lane. So earlier failures (900–1,528) came from how SUMO handles **merges**, not from its drivers. |
| Corridor screening (15,291 data requests, 2023) | Of 440 instrumented stretches with 2–3 metered ramps, 55 have **days that differ** and one clear bottleneck. Top three: **I-35W southbound** (morning), **I-394 westbound** (afternoon), **T.H.100 southbound** (afternoon). |
| Running now | 2023 data for the top three (104 days: every Wednesday plus alternate weekend days). Their current extent is 4 km upstream and 2 km downstream. **Following §4.4, the chosen corridor will be extended much further upstream** before the full-year pull. |

---

## 9. Thesis title, subject and description

### 9.1 Title (kept; author decision)

**"Adaptive driving algorithms for intelligent road traffic systems"**

### 9.2 Working subject (one sentence)

> *When, and by how much, can learning-based control (DRL), alone or combined with proven control families, measurably improve on tuned rule-based, feedback, adaptive and predictive freeway control, including by adapting ramp metering and speed limits to the shape of the day?*

### 9.3 Description (abstract-style draft)

> This thesis studies learning-based control for motorway traffic: deep reinforcement learning (DRL) used on its own and as a hybrid with proven control families. It asks when such control measurably improves on **tuned** rule-based, feedback, adaptive and predictive controllers. A pre-registered method is applied throughout: a cheap "headroom gate" measures the most any learner could gain before any DRL is trained, and every competitor is tuned on separate data.
>
> A first result shows a recurrent DRL policy scheduling a validated ramp meter improving on a tuned event scheduler and a fitted-model MPC by 2.5–4.3 %, with its limits stated.
>
> The thesis then addresses adaptation to the **daily pattern** of demand. Capacity-limited counts hide the true size and timing of peaks, and a learning controller observing only local rises and falls struggles to learn when to act. On a long, densely instrumented Minneapolis–St Paul corridor with two to three metered ramps and variable speed limits, the thesis:
> - (i) measures how much a controller that knows each day's true demand could gain over calendar timetables, pattern matching, coordinated and adaptive feedback, and forecast-based MPC;
> - (ii) studies at which level of demand-profile complexity DRL alone stops learning the timing of its actions, and which observations and structures restore it;
> - (iii) where the gate shows room, trains hybrid and stand-alone DRL controllers on synthetic days fitted to real ones. These are tested on held-out real days and confirmed in a second, microscopic simulator.

### 9.4 Research questions

| # | Question | Status |
|---|---|---|
| RQ1 | How should learning-based control be compared with proven control fairly (tuned competitors, headroom gates, pre-registration, paired statistics)? | Method in use |
| RQ2 | Can DRL scheduling a validated controller beat tuned non-learning schedulers under hidden events? | R6: yes, 2.5–4.3 %, with caveats; counting it is undecided |
| **RQ3** | On a long, real, instrumented corridor, does knowing the day's true demand leave ≥ 10 % room over the best tuned proven control? | **Open (gate)** |
| **RQ4** | Up to which demand-profile complexity can DRL alone learn *when* to act, and which observations or structures extend that limit? | **Open (learnability study, §5.5)** |
| **RQ5** | Can a hybrid or stand-alone DRL controller recover part of the RQ3 room on held-out real days, and does the ranking survive in a second simulator? | **Open, needs RQ3 = GO** |

---

## 10. The path forward

*Month estimates, not commitments; about 11 months remain (submission around September 2027). **Priority (author decision):** this pillar runs alongside the v6 work if resources allow, otherwise before it.*

| When (estimate) | Step | Kill point |
|---|---|---|
| Oct 2026 | Choose the corridor; extend it far upstream; pull 2023 and 2024; measure capacity, the capacity drop, real day shapes, and where the M turns into a trapezoid | No corridor with a usable capacity drop and M/trapezoid variety |
| Oct–Nov 2026 | Calibrate METANET; realism check; the predictability check (§5.5.3) | Realism fails; observations can't predict demand onset |
| Nov 2026 | Tune every competitor on 2023; **headroom gate on 2024** | **The main kill** |
| Nov 2026–Jan 2027 | Learnability ladder for DRL alone (§5.5.4), which can run in parallel with the gate | A finding either way; it shapes the RQ5 design |
| Dec 2026–Mar 2027 (if GO) | Hybrid and stand-alone DRL trained on fitted days, screened on validation days | Validation screening |
| Mar–Apr 2027 (if GO) | Rebuild the corridor in SUMO, pass realism, confirm the ranking | The ranking flips |
| May 2027 (if GO) | One confirmatory run on reserved data | The pre-registered claim rule |
| Jun–Sep 2027 | Thesis writing | — |

**If the gate KILLs:** the pillar ends quickly and cheaply, and effort moves to the v6 lead. **No negative-result paper is written** (author decision).

---

## 11. What the path can and cannot claim

- **Papers and the thesis's main claims need positive DRL results.** A positive result is learning-based or hybrid control measurably beating the best tuned proven control, with the comparison fixed in advance.
- **Gates and stops are tools, not results.** They decide where to spend the remaining months. They may appear in the thesis only as the method that selected the problem.
- **The learnability study (RQ4) produces knowledge either way.** Whether it can count depends on whether it leads to a DRL design that wins (RQ5).
- **Never claimed:** "first" or "novel"; "adaptive control" in the formal sense without online adaptation; anything the confirmation simulator did not reproduce.

---

## 12. Decisions

**Settled by the author (2026-10-05):**
- the title is kept;
- priority: alongside v6 if resources allow, otherwise before v6;
- the ARC-IT framing is accepted (TM20/TM21 for speed limits, plus the ramp-metering package; the codes still to be checked [VERIFY]);
- only positive DRL results count; no negative Paper B.

**Still open:**
1. **Does R6 count** towards the thesis, with its caveats (unrealistic road, unconverged training)?
2. **Corridor extension** (§4.4): extending the chosen corridor far upstream means more data requests. The size will be stated before asking.
3. **"Resources"** for running alongside v6: what is the limit? Computer time, or the author's own time?
4. **The learnability ladder** (§5.5.4): run it as soon as the corridor is chosen, in parallel with the gate? Or only after the gate?

---

## 13. Glossary

| Term | Plain meaning |
|---|---|
| **Learning-based control** | Control whose policy or model is learned from data. DRL is one kind. |
| **DRL** | A neural-network policy learned by trial and error in a simulator. Model-free DRL is data-driven control; model-based DRL is model-based learning control. |
| **Adaptive control (formal)** | A controller that changes its own parameters while running. Not the same as the everyday "adaptive". |
| **Hybrid control** | Two or more control families combined, for example DRL choosing the settings of a feedback controller. |
| **Tuned competitor** | An existing method whose settings were optimised on separate data before the comparison. |
| **Headroom gate** | A cheap test of the biggest possible gain: the best honest method vs an informed reference. Below 10 %, stop. |
| **Informed reference** | The same method given information nobody has in practice (here, the day's true demand). |
| **Demand vs volume** | Demand is how many cars want to pass; volume is how many the detector counts. At a full bottleneck, volume is capped. |
| **Capacity drop** | Once a bottleneck jams, fewer cars per minute get through than just before. |
| **M-to-trapezoid transition** | The narrow range of demand levels at which two daily peaks merge into one long congested plateau. |
| **Non-stationary demand** | Demand whose behaviour changes through the day (peaks of different heights, widths and rates). |
| **Predictability check** | Testing whether any forecaster can predict the coming demand from the controller's observations, before training DRL. |
| **Learnability ladder** | Training on progressively harder demand shapes to find where DRL stops learning when to act. |
| **METANET / SUMO** | A fast "fluid" traffic model / a car-by-car traffic simulator. |
| **Mayfly** | MnDOT's public web service for Minneapolis–St Paul loop-detector data. |
