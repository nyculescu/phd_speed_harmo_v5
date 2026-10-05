# The PhD path with daily demand patterns, explained from scratch

*A plain-language proposal for updating the thesis path, subject and description (2026-10-05). It builds on:*
- *the idea note (`docs/plans/day_pattern_idea_v0.md`);*
- *the literature report (`docs/review/day_pattern_research_v0.md`);*
- *the plant options and draft gate (`docs/plans/day_pattern_plants_v0.md`, `day_pattern_gate_draft_v0.md`);*
- *the lab results (`docs/lab/STATUS.md`, `docs/lab/gate_ctx_r6/`, `docs/lab/day_pattern/`).*

*Numbers come from those files. Where a number comes from a paper that was only partly read, it says "unverified". **Nothing in the new part of the path is proven yet.** This is a plan to test an idea, not a result.*

---

## 1. The whole story in one paragraph

The thesis must show that a computer that learns by trial and error (**deep reinforcement learning**, DRL) can control road traffic measurably better than the methods engineers already use.

So far, one result has held up under strict testing:
- **R6:** a DRL "dial-turner" that adjusts a proven ramp meter beat the best tuned alternatives by **2.5–4.3 %** on a simulated motorway bottleneck. That win is small and narrow.
- Since then, two follow-ups were stopped by their own pre-registered checks.

The new idea, which the author first had in v4 and now revives with better tools, is about **the shape of the whole day**. Traffic demand follows recognisable daily shapes: two rush hours, one big peak, a weekend ramp, a quiet day. When the peaks exceed what the road can carry, the detectors **cannot see how big they really are**. They count only what squeezes through, so the measured peak looks flatter and longer than the real one.

A controller that learns the day's pattern could:
- act **before** the peak, rather than after;
- use speed limits and ramp meters together along a short corridor;
- treat a heavy Tuesday differently from a light one.

That is the "adaptive" in the thesis title, taken seriously. It is also **exactly the kind of claim that has failed before**. So the path adds it as a pillar with a cheap, early kill test: if a controller that *knows* the day's true demand can't beat the best honest controllers by 10 %, no learner can, and we stop and write up.

---

## 2. Where the thesis stands today

| What | Result | What it means for the thesis |
|---|---|---|
| **R6** (BN4 bottleneck, DRL scheduling a proven ramp meter, 210 fresh test runs) | **−4.3 %** delay vs a tuned event detector; **−2.5 %** vs a planner (MPC) with a model fitted on separate data | The one confirmed DRL win. Small, real and narrow. |
| R6's limits, found 2026-10-04 | It doesn't transfer to other event sizes (surges +16 % worse). Its training never fully settled (it fails the convergence check). And its simulated road **fails the realism test**: queue discharge of 900 veh/h per lane, where real roads discharge 1,600 or more | The claim holds for the simulator as specified, not for a realistic road. This must be said next to it. |
| Lead 1 (events of varying size on the same road) | Room to win **3.3 %**, not significant → stopped | More evidence that tuned control leaves little room. |
| Context-aware R6 restart (2026-10-04) | All three driver set-ups of that road failed the realism test (discharge 900–1,440 veh/h per lane) → stopped at step 1 | The road model was the problem, not the learner. |
| Earlier speed-harmonisation work (v5 Round 4) | One well-chosen *constant* speed limit already captured almost all the benefit. Adapting it added only **0.4–4 %** | Speed limits help only near capacity, and timing was never tested. |
| The v6 projects (other problems) | Six candidates stopped. Tuned methods came within 0–5 % of an all-knowing reference | The pattern is consistent: tuned control is hard to beat. |

> **Analogy: the honest scoreboard.** The thesis so far has one narrow win and a long list of carefully recorded "no room to win" results. That is not a failure. It is what traffic DRL looks like once the old methods get a fair chance. The question is whether there is one more place where the old methods are genuinely blind.

---

## 3. The idea: learning the shape of the day

### 3.1 Days have shapes

| Shape | Typical day | Everyday analogy |
|---|---|---|
| **M** | morning and evening rush | a restaurant's lunch rush and dinner rush |
| **^** | one big peak | a single Sunday-brunch crowd |
| **/** or **\\** | demand builds or fades all day (often weekends) | a shop before a holiday, or the day after |
| **free flow** | almost no demand | a quiet bank holiday |

Real days are never perfect letters. The two peaks of an M can differ in height and width; the slopes can be steep or gentle; the peaks can arrive early or late. So the plan treats the shapes as a **continuum**: each day is a few peaks with their own height, timing and width, and the letters are only labels. No controller is ever told "today is an M".

### 3.2 Why counts hide the true peak

When a peak asks for more than the road can carry, the extra cars **wait**. They queue on the on-ramps or upstream. The detector at the bottleneck counts only the cars that get through, and that can never exceed the road's capacity.

```
 what drivers want (demand)               what the detector counts (volume)

          /\        /\                              _______   _______
         /  \      /  \                            /       \_/       \
        /    \____/    \           ──►            /                   \
  _____/                \_____               ____/                     \____
```

Three things follow:
1. **The true size of a heavy peak is invisible in counts.** It shows up only in queues, delays and travel times.
2. **The flat top lasts longer than the real peak,** because the queue keeps draining at capacity after demand has fallen. Timing judged from counts is late.
3. **Timetables fitted to counted volumes,** which is common practice, **underestimate heavy days.** Engineering guidance gives worked examples where counts understate demand by 16–20 %. Those are examples, not field measurements.

> **Analogy: the turnstile at a football ground.** If you count people through one turnstile, you can never count more than the turnstile allows per minute. Ten thousand fans arriving in ten minutes look exactly like five thousand arriving steadily over twenty. Only the length of the queue outside tells you which day it was.

### 3.3 Why this adds adaptability

A controller that has learned the day's pattern could do three things a timetable or a simple feedback rule cannot:
- **Act before the peak.** Start metering and lowering speed limits slightly early, so the bottleneck doesn't break down. A breakdown permanently lowers what the road carries until it clears (the **capacity drop**).
- **Tell a heavy day from a normal one early,** using the queues and the morning's shape rather than the counts.
- **Coordinate a short corridor:** 2–3 metered ramps plus speed limits, deciding where to store waiting cars and when to release them.

> **Analogy: the experienced shopkeeper.** One shop opens extra tills only once the queue is long. An experienced shopkeeper, by nine in the morning, already knows what kind of day it will be, and opens tills just before the rush. The learning controller is meant to be the experienced shopkeeper.

---

## 4. Why it is still unproven, and might well fail

This section matters most. The idea is attractive, and attractive ideas are where this project has been fooled before.

1. **Feedback controllers already adapt to live demand.** ALINEA, the standard ramp-meter rule, doesn't need to know what kind of day it is. It watches the traffic just downstream and reacts.
   > **Analogy: the thermostat** doesn't need to know thirty people walked in; it feels the room warming up.
2. **Most of the "day type" is known from the calendar.** Published clustering finds 3–6 day types, closely matching weekday versus weekend (unverified). A simple calendar timetable already holds most of that information.
3. **Against tuned feedback control, published learning-based gains are small.**
   - About **0–4 %** (median). One study's 20 paired runs range from 21 % better to 5 % worse.
   - Another study's learner was 0.6 % *worse* than ALINEA.
   - Some of these papers were only partly read.
   - Large published gains come from weak competitors, or from planners given the true future.
4. **No study was found that tests "day-type knowledge on top of tuned feedback"** against tuned feedback alone. There is no precedent effect size.
5. **The project's own record:** adapting speed limits to conditions added 0.4–4 %, and R6's edge vanished outside its training conditions.

**Prior expectation, written before any test:** a KILL is the likely outcome. The literature's prior for hybrid gains is 1.5–6 %.

**What could still make it work** (hypotheses, not findings):
- heavy days that counts hide;
- acting before breakdown, where breakdown is costly;
- coordinating several ramps and speed limits at once;
- realistic (imperfect) forecasts for the planner competitor. Earlier tests that gave the planner the true demand made the room to win zero by construction.

---

## 5. How it will be tested: kill early, kill cheap

The test is the same "headroom gate" used throughout the project.

> **Analogy: the friend who already knows how busy today will be.** Imagine a controller that knows the day's true demand curve in advance: the same timetable or planner, given the answer. Compare it with the best honest controllers. The gap is the biggest prize *any* learner could win. If it is under 10 %, don't spend months building one.

**The honest side** (every method tuned on separate days before the test):
- timetables per calendar day type, fitted to counted volumes (as in practice);
- "pattern matching": compare the first hour with past days and pick their plan;
- ALINEA, PI-ALINEA, and HERO (coordinated ALINEA);
- speed-limit feedback (MTFC) and a wave-resolving speed-limit scheme (SPECIALIST);
- a predictive planner (MPC) whose model and forecast are fitted on separate days, never given the truth.

**The informed reference:** the same timetable or planner, but fed the day's **true** demand.

**The test days:**
- real days are reconstructed from loop detectors **upstream** of the congestion, where counts still equal demand;
- the timetables are tuned on 2023 data;
- the gate runs on **2024** days that nobody tuned on.

**The rule:** KILL unless the gap is at least 10 %, with statistical confidence, pooled or on above-capacity days. A GO that appears only under a capacity drop larger than the one measured on the real road doesn't count.

**The stop rule for heavy days:** cars queuing at the entries and still moving count as normal oversaturation. Teleports, zero outflow for 10 minutes, or a car stuck for more than 600 s count as gridlock.

### The simulated road: two models, on purpose

| Role | Model | Why |
|---|---|---|
| **Gate and training** | METANET, a fast "fluid" model calibrated to a real Minneapolis–St Paul corridor | A full day runs in seconds. It reproduces the stop-and-go waves that speed limits act on. |
| **Confirmation, if the gate says GO** | SUMO, a car-by-car simulator, rebuilt for this corridor | A car-level check that the ranking isn't an artefact of the fluid model. It must first pass the realism test. |

> **Why two?** A fluid model can be told how much capacity a jam destroys, so it can "manufacture" the very effect a controller is rewarded for preventing. Testing cheaply in it and confirming in a different kind of model guards against that. Kill cheap; confirm expensively, and only if needed.

---

## 6. What has been done so far (2026-10-04 to 2026-10-05)

| Step | Result |
|---|---|
| Literature review, five strands | No study tests day-type knowledge on top of tuned feedback. Gains against tuned feedback are about 0–4 %. Counts hide heavy days. MnDOT (Twin Cities) has the best open ramp data. |
| Simulated-road choice | METANET for the gate, SUMO for confirmation (author decision; speed harmonisation and ramp metering both in scope). |
| SUMO pre-check (88 runs) | **Passed.** On a plain lane, SUMO's drivers discharge a queue at 2,300–2,650 veh/h per lane, at or above the realistic range. So the earlier failures (900–1,528) came from how SUMO handles **merges**, not from its drivers. A SUMO corridor is worth building later. |
| Corridor screening (15,291 data requests, 2023) | Of 440 instrumented stretches with 2–3 metered ramps, 55 have **days that differ** (congested on 30–90 % of days) and one clear bottleneck. Top three: **I-35W southbound** (morning), **I-394 westbound** (afternoon), **T.H.100 southbound** (afternoon). |
| Now running | 2023 data for the top three corridors (Wednesdays plus weekend days), to measure capacity, the capacity drop and the real daily shapes. Then one corridor is proposed. |

---

## 7. The proposed thesis subject and description

### 7.1 Title

**Keep the official title:** *"Adaptive driving algorithms for intelligent road traffic systems"*. The new pillar fits it, so a formal change seems unnecessary. That is for the author and supervisor to decide (§10).

### 7.2 Working subject (one sentence)

> *When, and by how much, can learning-based control improve on tuned rule-based, adaptive and predictive freeway control, including by adapting ramp metering and speed limits to the shape of the day, when every competitor is tuned and the test is fixed in advance?*

### 7.3 Description (abstract-style draft)

> Deep reinforcement learning (DRL) is often reported to outperform classical traffic control, but most comparisons use untuned or no-control baselines. This thesis asks when DRL adds measurable value over **tuned** rule-based, adaptive and predictive controllers. It uses a pre-registered method: a cheap "headroom gate" that measures the most any learner could gain, before any DRL is trained.
>
> The thesis reports one confirmed gain: a recurrent DRL policy scheduling a validated ramp meter improves on a tuned event scheduler and a fitted-model MPC by 2.5–4.3 % in simulation. It also documents its limits, and several pre-registered negative results that locate where tuned control leaves no room.
>
> It then tests a long-standing intuition: that freeway control should adapt to the **daily pattern** of demand. Capacity-constrained counts hide the true size and timing of peaks, so timetables fitted to counts under-serve heavy days. On a real Minneapolis–St Paul corridor with two to three metered ramps and variable speed limits, calibrated to loop data, the thesis measures how much a controller that knows each day's true demand could gain over calendar timetables, pattern matching, coordinated feedback and forecast-based MPC. Only if that gap reaches 10 % does it train a memory-based DRL scheduler on synthetic days fitted to real ones, test it on held-out real days, and confirm the ranking in a second, microscopic simulator.
>
> Either outcome is reported. The contribution is both a result and a method: an honest map of where learning helps freeway control, and by how much.

### 7.4 Research questions

| # | Question | Status |
|---|---|---|
| RQ1 | How should DRL be compared with traffic control fairly (tuned competitors, headroom gates, pre-registration, paired statistics)? | Answered: method in use since 2026-10-01 |
| RQ2 | Can DRL that schedules a validated controller beat tuned non-learning schedulers under hidden events? | Answered with caveats: R6, 2.5–4.3 %, narrow, unrealistic road |
| **RQ3 (new)** | On a real, calibrated corridor, does knowing the day's true demand leave ≥ 10 % room over the best tuned non-learning control? | **Open:** the day-pattern gate |
| **RQ4 (new, only if RQ3 = GO)** | Can a memory-based DRL scheduler recover part of that room on held-out real days, and does the ranking survive in a second simulator? | **Open, conditional** |

---

## 8. The path forward, with kill points

*Month estimates, not commitments; about 11 months remain (submission around September 2027).*

| When (estimate) | Step | Can kill the pillar? |
|---|---|---|
| Oct 2026 | Choose the corridor from the 2023 data; measure capacity, the capacity drop and real day shapes | Yes, if no corridor shows a usable capacity drop |
| Oct–Nov 2026 | Calibrate METANET to the corridor; plant realism check | Yes (realism) |
| Nov 2026 | Tune every competitor on 2023 days; **run the headroom gate on 2024 days** | **Yes, the main kill.** Expected outcome: KILL |
| *If KILL* | Write up: "learning daily patterns adds < X % over tuned freeway control on a real corridor". A negative result that answers RQ3. | — |
| *If GO:* Dec 2026–Feb 2027 | DRL scheduler (memory-based, hybrid: it chooses among tuned controller settings), trained on fitted synthetic days | Yes (validation screening) |
| *If GO:* Mar–Apr 2027 | Rebuild the corridor in SUMO, pass realism, confirm the ranking | Yes, if the ranking flips |
| *If GO:* May 2027 | One confirmatory run on reserved data | Yes, under the pre-registered claim rule |
| Jun–Sep 2027 | Thesis writing | — |

**Two papers** (the target), one option:
- **Paper A:** R6 plus the fair-evaluation method and the documented stops ("When does DRL beat tuned freeway control?").
- **Paper B:** the day-pattern study, whichever way it comes out. Or, if the author prefers, the v6 connected-vehicle traffic-light study, with the day-pattern result as a thesis chapter.

---

## 9. What this path can and cannot claim

- **Can claim, whatever happens:** a fair method, one small confirmed win with its limits, and a measured answer to the daily-pattern question on real data.
- **Can claim only after a GO and confirmation:** that learning the daily pattern improves freeway control by a stated amount on a real corridor.
- **Cannot claim:** that DRL "crushes" classical control; any "first" or "novel" result; anything the confirmation simulator did not reproduce.

> **Analogy: the weather app.** Before building a weather app, you check how much better a picnic planner does with *tomorrow's real weather* than with the ordinary forecast. If the difference is small, you've learned something worth publishing: forecasts are good enough. If it's large, you've earned the right to build the app.

---

## 10. Decisions for the author (to discuss)

1. **Title.** Keep "Adaptive driving algorithms for intelligent road traffic systems" and change only the subject statement (§7.2)? Or adjust the title?
2. **Priority between leads.** With about 11 months left, does the day-pattern pillar run *before*, *after* or *alongside* the v6 connected-vehicle traffic-light lead? Both can't be fully explored.
3. **Does R6 count** towards the thesis, with its newly found caveats (unrealistic road, unconverged training)? The v6 report asked the same question.
4. **ARC-IT framing.** The new pillar maps to the motorway speed-limit and metering service packages (TM20/TM21 for speed limits, and the ramp-metering package). The package and PSpec codes still have to be checked against the ARC-IT site copy [VERIFY].
5. **Which outcome would the supervisor accept as Paper B:** a well-run negative gate result, or only a positive DRL result?

---

## 11. Glossary

| Term | Plain meaning |
|---|---|
| **DRL** | A neural network that learns a control strategy by trial and error in a simulator. |
| **Tuned competitor** | An existing method whose settings were optimised on separate days before the comparison. |
| **Headroom gate** | A cheap test of the biggest possible gain: the best honest method vs an informed reference. Below 10 %, stop. |
| **Informed reference** | The same method given information nobody has in practice (here, the day's true demand). Not a real controller. |
| **Demand vs volume** | Demand is how many cars *want* to pass; volume is how many the detector *counts*. At a full bottleneck, volume is capped and hides demand. |
| **Capacity drop** | Once a bottleneck jams, fewer cars per minute get through than just before it jammed. |
| **Queue discharge** | The flow out of a standing queue. Real freeways: roughly 1,600–2,400 vehicles per hour per lane. |
| **Ramp metering / ALINEA / HERO** | Traffic lights on on-ramps. ALINEA is the classic feedback rule; HERO coordinates several ramps. |
| **Speed harmonisation / VSL** | Variable speed limits that smooth traffic and delay breakdown. |
| **MPC** | A planner that predicts the next minutes with a model, acts, and re-plans. |
| **METANET / SUMO** | A fast "fluid" traffic model / a car-by-car traffic simulator. |
| **Pre-registration** | Writing the test and its pass/fail rule down before seeing any data. |
| **Seed** | One random version of the simulated traffic, like a roll of the dice. |
| **Mayfly** | MnDOT's public web service for Minneapolis–St Paul loop-detector data. |
