# Roadmap v0: paper 1 → paper 2 → PhD thesis (DRAFT, 2026-10-20)

**Superseded by `docs/thesis/outline_v1.md` (V459, 2026-11-07).** Kept as a record.

**Thesis title (fixed):** "Adaptive driving algorithms for intelligent road traffic systems". Submission ≈ September 2027. The author and Claude act as supervisors (V95).

**Thesis story (V96):** *When does adaptation pay in road traffic, and how do we measure it honestly?*

Status: **DRAFT**; the decisions in §5 belong to the author.

## 1. What already exists (BL-1, BL-2)

```
VEHICLE LEVEL ("adaptive driving")              SYSTEM LEVEL ("intelligent traffic systems")
 line #1 self-calibrating safety margin          screen #2 green-commit margin (Hamburg)    STOP
   screens #1/#1b (NGSIM, TGSIM)  CONTINUE       sweeps: 18 margins → fixed tables win
   confirmatory #1 (TGSIM)        VALID-ONLY     D1 detector faults (BN4)          STOP (+ bug re-run)
                                                 D2 incidents (BN4)                CONTINUE after bug fix
METHOD                                           P1/P1b information ladder         S1a FAIL · S1b PASS
 pre-registration · run once · bug rule          C1 confirmation                   CONFIRMED 16.2 %
 oracle headroom · cross-fitting · placebo  ───► paper_1 (draft, 4/6 pages)
```

## 2. Proposed thesis structure

| Ch. | Title (working) | Content | Source | Status |
|---|---|---|---|---|
| 1 | Introduction | question, scope, contributions; optional ARC-IT framing [VERIFY codes] | — | to write |
| 2 | Method: honest evaluation of adaptive control | pre-registration, two tiers (screen → confirm), oracle headroom, selection on noise and cross-fitting, common-random-number pitfalls in SUMO, the bug rule | protocols, P1/P1b methods | mostly material, to write |
| 3 | Adaptive safety margins for automated car-following | line #1: screens and confirmatory on real trajectories; the 18-candidate margin sweep; **lesson: fixed per-site tables match online calibration** | confirm_1_result.md, sweeps | done, to write |
| 4 | Adaptation in signal and freeway control: where it does not pay | screen #2 (green commit), D1 (detector faults, with bug re-run) | screen_2, D1 results | done, to write |
| 5 | How much incident information does mainline metering need? | **paper_1** (P1, P1b, C1) | p1b_result.md, C1 | paper in progress |
| 6 | **paper 2** (see §3) | — | — | to do |
| 7 | Synthesis: when adaptation pays | non-recurring events vs recurring variety; information levels; robustness (detection delay, compliance); limits of simulation evidence | all | to write |
| 8 | Conclusion | — | — | to write |

**Why this fits the title:** chapter 3 is vehicle-level driving algorithms; chapters 4–6 are traffic-system algorithms; chapters 2 and 7 give the common thread. The negative results (STOP, VALID-ONLY) are reported in full, which the method requires.

## 3. Paper 2: options (recommendation first)

| Option | What | New work | Risk | Fit | Venue (deadline [VERIFY]) |
|---|---|---|---|---|---|
| **A. Journal extension of paper_1** | "PI by default + type plan" (removes the last confound); queue override at q = 2000; a **second geometry with lane changing and a real lane closure**; possibly a second demand profile | 1 protocol, a plant variant, about 1–2 days build, 1–2 nights compute | medium: a second plant may not pass the tool checks (as MRG3 did not) | strongest for the thesis's main result | IEEE T-ITS or TR-C (rolling) |
| **B. Methods paper** | "Honest headroom in traffic microsimulation": the measured inflation of in-sample oracles (D2, P1, P1b data already exist: OR_in vs ORX vs placebo), the SUMO common-random-number mechanism, a short survey of how traffic papers use hindsight oracles, a replicate protocol | analysis + survey; almost no new simulation | medium: the statistics are known (Cameron 2016, van Hasselt 2010), so the contribution is traffic-specific evidence, the survey and the protocol | chapter 2 for free | SUMO User Conference, TRR, or ITSC |
| C. Real data (WaveX, unread) | wave smoothing from roadside radar (direction #3) | a new protocol and build; data is local | high: scoop risk (CIRCLES group); the oracle test is untested | weaker link to paper_1 | ITSC/IV |
| D. Ramp metering under incidents | the information ladder for an on-ramp meter | a new on-ramp plant (the archive's corridor plants failed checks) | high build risk | good for generality | journal |

**Recommendation: A, with B as a fallback or third item.** A turns the conference result into a journal result and closes the limits a reviewer will raise. B costs little, because the data already exist; it could be written in parallel, or become the second paper if A's second plant fails its tool checks.

## 4. Timeline (machine-speed; the author's time is the bottleneck)

```
2026 Nov ─ paper_1: verify Papageorgiou 2008 claims, fill the last [CITE], Discussion/Abstract,
           author review, 6-page check, PDF eXpress                         (author ~1–2 weeks part-time)
2026 Dec ─ paper_1 final polish  ·  paper 2 protocol (A) drafted + reviewed
2027 Jan ─ paper 2 build + runs (days)  ·  thesis ch. 2–4 drafting starts
2027 Mar 1 ─ paper_1 submitted to ITSC 2027
2027 Mar–May ─ paper 2 analysis + writing → submit (journal)  ·  thesis ch. 3–5
2027 Jun–Aug ─ thesis ch. 1, 6–8; ITSC decision [VERIFY date]; full thesis review
2027 Sep ─ thesis submission
```

Compute is never the bottleneck: the longest planned run is about 1–2 nights on the laptop.

## 5. Decisions for the author

1. **University requirements** [VERIFY with the doctoral school]: do the 2 papers need to be *submitted*, *accepted* or *published* before thesis submission? Is a conference paper enough for one of them? This decides whether A (journal, slower review) or B (conference, faster) should come first.
2. **Paper 2 choice:** A (recommended), B, or A + B.
3. **Thesis structure** (§2): approve, or change.
4. **Paper 2 venue:** journal (T-ITS / TR-C) or another conference.
