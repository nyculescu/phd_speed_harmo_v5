# Feasibility Study — Distributional-RL Harmonization Layer for CAV String Stability

| Field | Value |
|---|---|
| Date | 2026-05-20 |
| Status | Pre-rework feasibility assessment — go/no-go gate before any codebase rework |
| Inputs | All 7 papers in `docs/knowledge_base/papers_RL-DRL_CFM/` (SECRM read in full; 6 others in depth); corpus survey of `papers_RL_VSL` / `papers_RL_RM` / `papers_DistRL`; the 2026-05-20 audit |
| Companion | [audit_2026-05-20_fresh_thread.md](audit_2026-05-20_fresh_thread.md) |

---

## §1 — Verdict

**Conditionally feasible. Do not rework the codebase yet.** The converged direction — a learned harmonization layer that modulates CAV ACC set-points to damp stop-and-go waves, with a distributional / risk-sensitive method core — clears the four filters the prior VSL work failed. But it rests on **two make-or-break assumptions** that are cheap to test and have not been tested. Run the two probes in §5 first. If both pass, the rework is justified. If either fails, the direction is not viable — and you will have spent days, not weeks of training compute, to learn that.

This is the honest answer to "should we rework the whole codebase": **not on faith — on the probes.**

---

## §2 — The converged design

**What it is.** Not a new car-following model, not roadside VSL. A **harmonization layer on top of production ACC**:

- The vehicle's existing ADAS/ACC keeps doing safe car-following (gap-keeping, braking) — untouched. This respects the deployment reality: that controller is solved and shipped (SECRM, ElSamadisy et al. 2024, is the mature research endpoint; commercial ACC is the product).
- The learned layer **modulates the ACC set-point** — target speed *and* target time-gap, both standard, driver-selectable ACC settings — so the vehicle damps the stop-and-go wave passing through it. It is a *feature on top of* ACC, not a replacement of it.

**Why string stability, not speed variance.** Speed variance is the gameable metric the audit killed: minimizing it is trivially won by a slow uniform cruise (the old agent did exactly this — merge speed 85→54 km/h, `lane_sigma` 17.6→1.6, TTS +23%). **String stability is the non-gameable downstream consequence.** It has a rigorous definition — a disturbance must *attenuate*, not amplify, as it propagates upstream — and attenuating a perturbation is real work that a slow cruise does not perform. The amplification *ratio* is dimensionless, so "drive slow" does not trivially win it (a residual speed-dependence is closed by the mobility constraint below).

**The MDP, in brief.**
- *Environment*: a corridor / platoon of vehicles on a fixed, credible low-level controller (SUMO ACC/CACC `carFollowModel`, or SECRM frozen as the low level), with stochastic heterogeneous HDVs and the ramp merge as a recurring perturbation source.
- *Action*: bounded modulation of the controlled CAVs' ACC target speed + target time-gap. Bounded so the low-level safety guarantee is never overridden.
- *Objective*: minimize wave amplification (perturbation attenuation) **subject to a hard mobility constraint** (episode travel time / mean speed bounded) — so the layer cannot game by slowing.
- *Baselines*: plain ACC (no layer), a hand-tuned rule-based layer, and a risk-neutral (SAC) version of the same layer.

**Why this clears the filters the VSL work failed:**

| Filter | VSL work | This design |
|---|---|---|
| True objective, measured directly | ✗ 5 variance proxies | ✓ perturbation attenuation, mobility-constrained |
| Non-gameable metric | ✗ `lane_sigma` | ✓ amplification ratio + mobility constraint |
| Real & solvable problem | ✗ no breakdown / unsolvable breakdown | ✓ stop-and-go waves are real, documented, and damping them is a demonstrated CAV benefit (Stern et al.) |
| TQC load-bearing | ✗ decorative | **conditional — see §3** |

---

## §3 — Where TQC / distributional RL genuinely fits — and where it does not

**It does NOT fit the low-level controller.** SECRM settles this: low-level safety is best handled as a *hard analytic action constraint* (a worst-case stopping bound), and a guarantee strictly beats any statistical tail bound. Verbatim, SECRM: *"for agents trained using reward alone, the satisfaction of safety constraints is not guaranteed."* Efficiency and comfort at the low level are mean-shaped. TQC adds nothing here, and we are not building the low-level controller anyway.

**It fits the harmonization layer — conditionally.** The honest argument:

- In a *stochastic* string (heterogeneous HDVs, random perturbation timing/severity), wave amplification is itself a random variable. Most disturbances attenuate; a jam forms only on the **bad tail** — a rare alignment of timing, driver states and a hard brake. A jam does not form on the *average* disturbance.
- A risk-neutral controller optimizes the *mean* amplification and will still let occasional waves through. A risk-sensitive one bounds the **tail** — exactly the wave-forming events. This reframes string stability itself as a **probabilistic / risk-based** property: not "transfer-function magnitude ≤ 1" (deterministic) but "CVaR of amplification ≤ 1" (distributional).
- TQC's quantile critic is the natural, low-variance estimator of that CVaR (Route 2: risk in a constraint, via the Rockafellar–Uryasev reduction). The corpus confirms **zero** papers apply distributional RL to car-following / string stability — this lens is the genuine gap.

**But the honest contribution is the necessity question, not an assumed win.** Distributional RL is *a* route to a tail objective; a scalar critic with state augmentation is the established competitor (Chow & Ghavamzadeh). The thesis question — *"does wave-damping control need a distributional critic, or does plain SAC suffice?"* — is rigorous, publishable either way, and is the form in which TQC honestly earns (or does not earn) its place. Do not pre-assume TQC wins.

---

## §4 — Honest risks

1. **Crowding.** RL for CAV wave damping is a covered area (Stern et al. / CIRCLES; Flow; the Bilateral-DRL paper in your own CFM folder does perturbation damping with DDPG). Novelty rests narrowly on (a) the distributional / risk-based lens and the "probabilistic string stability" metric, and (b) the set-point-layer-on-ADAS framing. Before committing, verify by external search that risk-sensitive / distributional wave damping is genuinely unpublished — the corpus is curated, not exhaustive.
2. **The necessity question can land "scalar SAC suffices."** Then TQC's home is "we rigorously established the right tool," not "TQC wins." Honest, publishable — but know it going in.
3. **The tail must be real (make-or-break — Probe A).** If wave amplification is light-tailed in simulation, risk-sensitivity has nothing to optimize and the entire distributional contribution collapses.
4. **Set-point modulation must have wave-damping authority (make-or-break — Probe B).** The layer acts *through* the ACC, not directly on acceleration. If modulating target speed + time-gap is too weak an actuator to damp a wave, RL on top will not fix that — and direct acceleration control would violate the "don't replace ADAS" caveat.

Risks 3 and 4 are not research questions — they are assumptions, and they are cheap to test now.

---

## §5 — Make-or-break probes (run BEFORE reworking the codebase)

Both probes use simulation only — **no RL training, no training compute.** Both also produce baselines the paper needs anyway, so they are not throwaway.

**Probe A — Is wave amplification heavy-tailed?**
Run the corridor (stochastic heterogeneous HDVs on Krauss-with-imperfection or string-unstable IDM, ramp merge as perturbation source) on **plain ACC, no harmonization, no RL**, over many randomized episodes. Measure per-episode wave amplification (e.g. ratio of downstream to upstream speed-oscillation amplitude, or stop-and-go wave count/severity). Plot the distribution.
- **Go:** the distribution has a meaningful heavy tail — bad episodes materially worse than the median.
- **No-go:** amplification is near-constant across episodes → the distributional/risk angle has nothing to optimize.

**Probe B — Does set-point modulation have wave-damping authority?**
Same environment. Implement a **hand-tuned rule-based** harmonization layer: when an approaching wave is detected (downstream speed drop / leader deceleration), the rule smoothly opens the ACC time-gap and/or lowers target speed; restores when clear. No RL. Compare amplification vs plain ACC.
- **Go:** the hand-tuned layer measurably reduces amplification → set-point modulation is a sufficient actuator; RL can then improve on the rule.
- **No-go:** a reasonable hand-tuned rule damps nothing → the actuator is too weak; stop here.

**Decision:** rework the codebase only if **A and B both pass**. This is the feasibility gate.

---

## §6 — Codebase rework scope ("rework the whole codebase")

The **infrastructure survives** — TraCI integration, the TQC training harness, SubprocVecEnv, multi-seed, the vast.ai deploy, the SAR plugin registry. What is reworked is the **MDP**, which is exactly what the plugin architecture exists for:

| Component | Fate |
|---|---|
| TraCI / SUMO integration, training harness, deploy scripts | **Keep** |
| SAR plugin registry pattern | **Keep** — swap the plugins |
| Environment (`env_interact.py`) | **Rework** — corridor/platoon with a fixed low-level ACC; agent sets set-points only |
| Action (`r44_action_*`) | **Replace** — ACC target-speed + time-gap modulation, bounded |
| Reward (`r44_reward_*`) | **Replace** — perturbation attenuation, mobility-constrained; no variance terms |
| State (`r44_state_*`) | **Rework** — local string state (own/neighbour speed, gap, relative speed, disturbance indicator) |
| TQC build (`train.py`) | **Keep**, then **extend** for the Route-2 CVaR constraint (cost critic + Lagrangian) |
| Baselines (`evaluate_models.py`) | **Replace** — plain ACC, rule-based layer, SAC version |

"Rework the whole codebase" = rework the MDP, keep the engine. Bounded, and the architecture was built for it.

---

## §7 — Open design decisions (resolve after the probes pass)

1. **Single-CAV vs platoon.** Single controlled CAV among stochastic HDVs (Stern setting; clean single-agent TQC; tractable) vs a multi-CAV cooperative platoon (multi-agent; harder). Recommend single-CAV first.
2. **CAV penetration as a contribution axis** — "how much wave damping does X% of CAVs running the layer buy?" turns the old deferred penetration question into a result.
3. **Necessity-question scope** — a section inside the controller paper, or a co-equal methods study.
4. **Route-2 form** — CVaR as a hard constraint (Rockafellar–Uryasev + Lagrangian) vs as a risk-averse term in the objective. The TQC deep-dive favoured the constraint form.

These do not block the probes. The probes block everything else.
