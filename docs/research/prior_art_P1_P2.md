# Prior-art check: P1 and P2 (V96, 2026-10-19)

Two agents, each with ≤ 15 web searches plus Crossref, arXiv and OpenAlex. Mostly abstracts were read, so treat every item as [VERIFY] unless noted. Full reports are in the session scratchpad (`pa1/`, `pa2/`).

## P1: "event-triggered" incident ramp metering. The mechanism is prior art.

| Work | What it does |
|---|---|
| Sheu & Chang 2007, T-ITS, doi:10.1109/tits.2007.893327 | SPRT detection, then incident-responsive group control (Paramics) |
| Sheu 2007, Physica A, doi:10.1016/j.physa.2007.08.005 | Local version of the above |
| Dabiri & Kulcsár 2014, IFAC, doi:10.3182/20140824-6-za-1003.02383 (full text read) | Gain scheduled on incident parameters estimated online (macroscopic model) |
| Wu et al. 2014, JTTE, doi:10.1016/s2095-7564(15)30097-0 | NN recognition of the incident, then the meter layer (~25 % less delay) |
| Lu, Chen & Grant-Muller 2014/ITSC 2013 | Dyna-Q under incidents |
| Toan et al. 2022, JTE-A, doi:10.1061/JTEPBS.0000679 | Fuzzy decision support |
| Gao & Xu 2026, TPT, doi:10.1080/03081060.2026.2724319 | SUMO incident merges, constrained MARL (same plant class: must be cited) |
| Wang, Papageorgiou et al. 2010 (TRR); Zheng et al. 2024 (IET ITS) | Always-on metering for uncertain bottlenecks |
| FHWA Ramp Management Handbook §8.3.1 (read); Hegyi et al. 2001 | Pre-planned incident response plans |

- **The term is taken:** "event-triggered" already means something else in control theory.
- **Not found:** the decomposition "per-type plan vs per-incident information", cross-fitted, with the ramp queue in the delay. Also not found: sensitivity to detection delay, false alarms, type misclassification and switch-back.
- **Verdict:** publishable at ITSC only if reframed as **"How much incident information does ramp metering need?"**. That needs strong always-on baselines (PI-ALINEA aimed at the incident bottleneck, AD-ALINEA, a robust tuning over the incident mix), the sensitivity rows, and ideally a second geometry.

## P2: oracle inflation from selection on noise. The general statistics are known.

| Work | Relation to P2 |
|---|---|
| Cameron, Hoos & Leyton-Brown, IJCAI 2016 | Virtual-best-solver bias: the same oracle |
| van Hasselt 2010 (double Q-learning) | Choose on one sample, evaluate on another: the cross-fit, biased low |
| Smith & Winkler 2006 | The optimizer's curse |
| Boesel, Nelson & Kim 2003 | Selection after simulation optimisation |
| Klein et al. 2024, arXiv 2409.02086 | Common random numbers broken in agent-based models, with a fix |
| Riehl, Kouvelas & Makridis 2026 (sumoITScontrol) | SUMO ramp metering; recommends identical seeds for paired runs |

- **SUMO mechanism (agent read the source):** `MSBaseVehicle::getRNG()` uses the current lane's RNG from a shared pool. A controller change therefore shifts every later random draw: the same seed does not give common random numbers.
- **What may be new for traffic:** the measured size of the inflation in standard SUMO, the mechanism, and a replicate protocol.
- **Verdict:** not a standalone method paper. It works as a pitfalls note, or better **as a methods section inside P1**, with bracketing:
  - in-sample oracle = upper bound; one-replicate cross-fit = lower bound;
  - choose on the mean of R ∈ {1, 2, 4, 8} replicates;
  - a placebo test (the same controller under K seeds).

## Consequence for D2 (V94 corrected in V97)

ORX (one-replicate cross-fit) is a double estimator and is biased low. So D2's "per-incident adds 0–1 %" is a **lower bound**. Honest reading: per-incident headroom over the per-type plan lies between ~0–1 % (lower bound) and 5–40 % (inflated upper bound), and was **not shown** to reach 10 %. The STOP stands under the pre-registered rule.
