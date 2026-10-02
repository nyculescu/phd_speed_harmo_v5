# Lessons — Metric Gameability (smoothing-rescue postmortem + reusable screen)

| Field | Value |
|---|---|
| Created | 2026-05-21 |
| Status | **Active** — read before choosing any KPI or reward term, in this project or its pivots |
| Companion docs | [audit_2026-05-20_fresh_thread.md](audit_2026-05-20_fresh_thread.md) (the audit that falsified Paper 1), [plans/phd_thesis_plan_v0.md](plans/phd_thesis_plan_v0.md) (the falsified plan) |
| Purpose | Document the 2026-05-21 "traffic smoothing" rescue attempt that failed, extract the generalized trap, and give a screen so the **pivot does not repeat it in a new costume**. |

---

## §1 — TL;DR (the one lesson)

**Every headline metric this project has tried — `lane_sigma`, acceleration magnitude, jerk — is minimized by uniform slow traffic, which a constant low speed limit produces for free.** A metric that a trivial non-learned policy can optimize cannot demonstrate that a learned controller has value. The learned controller was never beating a real bar; it was beating *No-Control*, while a one-line fixed cap (`M60_active`) quietly did the same or better. The fix is not a better metric of the same kind — it is to **screen every metric and reward term against a degenerate policy before adopting it** (§4), and to compare against the best *constant* controller, never just against No-Control.

---

## §2 — The failure being documented: the "traffic smoothing" rescue (2026-05-21)

**Context.** The fresh-thread audit ([audit_2026-05-20_fresh_thread.md](audit_2026-05-20_fresh_thread.md)) falsified Paper 1: the per-lane harmonization controller is worse than No-Control on every non-gameable metric (+23 % TTS, −6 % completed trips). The negative-results paper (Pivot A) was excluded by the user. The proposed rescue: maybe the controller, though it congests, produces **smoother** driving — measure acceleration/deceleration magnitude and jerk and claim a comfort/safety contribution: *"VSL methods that improve traffic smoothing without deteriorating road safety and without significantly deteriorating mobility."*

**What was done.** Added per-SUMO-step per-vehicle accel + jerk instrumentation to `core/eval_metrics.py` (`sumo_step()`: mean |a|, RMS, p95 deceleration, jerk distribution, severity-binned counts, merge-vs-upstream split). Re-evaluated the base experiment — **no retraining**, models reused. The re-eval reproduced the old physical KPIs byte-identically (NC reward −386.238, every tqc seed exact), so the new data is on the same scenario pool and trustworthy.

**Result.** Full three-axis comparison, base experiment, same scenario pool:

| axis | representative metric (merge zone) | NC | **M60_active** (fixed 60 km/h) | DRL (5 seeds) |
|---|---|--:|--:|--:|
| Smoothing | decel p95 (m/s²) | 3.62 | **2.33** | 2.37 |
| Smoothing | hard-decel rate /1k | 9.38 | **7.43** | 7.58 |
| Safety | n_ttc_critical | 66.9 | **64.5** | 73.4 |
| Safety | hard_brake_count | 117.9 | **111.9** | 124.6 |
| Mobility | n_arrived | 154.3 | **154.5** | 145.2 |
| Mobility | TTS (veh·h) | 220.0 | **257.2** | 270.5 |

Head-to-head DRL vs M60_active across 10 metrics, scored with DRL seed-noise awareness: **DRL better on 1 (a noise-level `ds_flow` +8 vph), M60 better on 6, tie on 3.** The DRL controller beats No-Control on smoothing, but it **ties M60 on smoothing and loses to M60 on safety and mobility**. A constant 60 km/h sign **Pareto-dominates** the learned per-lane distributional-RL controller across all three axes.

**Verdict.** The rescue failed for the *same root cause* as the original paper. Applying the user's own three-part criterion: there is no baseline against which the controller "improves smoothing without deteriorating safety without significantly deteriorating mobility" — vs No-Control it fails the safety and mobility clauses; vs M60 it fails all three.

Two structural sub-findings (see §4, tests 4 and 5):
- `decel_ct_severe` (< −6 m/s²) = **0 everywhere** — the SUMO Krauss model essentially cannot produce it. Same class as the "0 collisions" claim: a structural zero that measures the simulator, not the controller.
- Braking smoothness is **monotone in posted speed** (NC@85→3.62, M70@67→2.64, M60@60→2.33, DRL@~54→2.37). The controller's "smoothness" is just where ~54 km/h sits on that ladder — inherited by posting a low speed, not learned.

---

## §3 — The trap, generalized: the degenerate-policy / gameable-metric trap

**Definition.** A metric is *gameable* if a trivial, non-learned, degenerate policy can score on it as well as a good learned controller should. Adopting a gameable metric as a headline KPI — or as a reward term — guarantees a false positive: the numbers look excellent against No-Control, the controller appears to "work," and the result is an artifact.

**Why this project kept hitting it.** The project framed "speed harmonization" as **variance reduction** (speed σ across lanes, across segments, across time; then acceleration/jerk magnitude). But *variance of speed is trivially reduced by reducing the mean speed* — slow everything down uniformly and every dispersion metric collapses. A constant low speed limit does this with zero intelligence. So:

- `lane_sigma` (cross-lane speed std) → minimized by uniform limits. Confirmed by the M60→M110 ladder: lane_sigma is monotone in posted speed.
- `r_harmo`, `r_temporal`, `r_lane_eq` (reward terms) → all variance terms → the agent maximized reward by congesting the road.
- acceleration magnitude, jerk → minimized by slow uniform traffic → M60 ties the learned controller (§2).

Every one of them measured the **symptom** (low dispersion) instead of the **goal** (efficient, safe throughput). And every one of them was validated against the **wrong yardstick** — No-Control. No-Control is not a controller; beating it is necessary but not sufficient. The yardstick that exposes gaming is the **best trivial controlled baseline** (a constant cap).

**The accel attempt was not wasted:** it proved the trap is *structural across all speed-derived metrics*, not a quirk of `lane_sigma`. That is the insight that protects the pivot.

---

## §4 — The screen: apply to every future KPI and every reward term

Before any metric becomes a headline KPI or enters the reward, it must pass **all five** tests. If it fails one, it can be a *secondary reported* metric at most — never a headline, never a reward term.

1. **Constant-policy test.** Score the metric for a trivial constant policy (post a fixed low limit always) and for No-Control. If a constant policy scores as well as a competent learned policy *should*, the metric is gameable. **The learned controller must beat the best constant — not just No-Control.**

2. **Degenerate-extremes test.** Is the metric optimized by an *extreme* of the action space (slowest possible, do-nothing)? A sound metric has its optimum in the **interior** — it forces a trade-off between competing pressures. If the metric is monotone in a single action knob (here: posted speed), it is gameable.

3. **Decoupling test.** Can the metric improve while the true objective gets worse? `lane_sigma` improved 90 % while TTS worsened 23 %. If metric and objective can move in opposite directions, the metric is a proxy — report it, never headline it, never reward it.

4. **Tautology test.** Can the simulator even produce the bad outcome the metric counts? `0 collisions` (Krauss cannot rear-end crash) and `0 severe decelerations` (Krauss will not brake < −6 m/s²) are **structural zeros** — they measure the model, not the controller. If the bad tail is unreachable by construction, the metric carries no information.

5. **Exposure test.** Is the metric a raw count that grows with time-in-network? A *worse* controller (more delay) accumulates more vehicle-steps and therefore more raw events. Normalize by exposure (per veh-km, per 1000 veh-steps) — `hard_brake_count` and `n_ttc_critical` are raw counts and are exposure-confounded.

**Positive corollary — what a good headline metric looks like:** it is the *objective itself* (total delay, completed throughput / outflow), it is **worsened** by the degenerate slow-uniform policy, its optimum is interior, and it cannot be improved while the objective regresses. Cf. Vinitsky et al. 2018, who used a single reward — *"we simply used the outflow over the past 20 seconds."*

---

## §5 — How the trap will reappear AFTER the pivot (new costumes to watch for)

The pivot (to a scenario that genuinely breaks down, with a throughput/TTS reward) does not remove the trap — it re-dresses it. Specific costumes:

- **TTS gaming via insertion blocking.** `total_tts_veh_h` counts only vehicles *inside* the network (`eval_metrics.py`). A controller that meters so hard that vehicles cannot enter pushes delay into the origin queue, which TTS does not see — TTS drops while real door-to-door delay rises. **Fix:** count origin-queue waiting too, or measure completed-trip delay (departure-intent → arrival), and co-headline with throughput (vehicles actually served). *Note:* the current eval already shows a TTS / `n_arrived` mismatch (TTS ≈ 220 veh·h implies ~220 vehicles always present, yet only ~150 arrive per episode) — **resolve this accounting before TTS becomes a reward.**

- **The "make NC break down" trap.** The pivot needs a scenario where No-Control shows *controllable* capacity drop. Two failure modes: (a) too gentle → NC never breaks down → nothing to fix → this exact failure again; (b) too severe → NC breaks down irrecoverably → the controller cannot help either → any "gain" is noise. The scenario must sit in the metastable, controllable band, and that must be **verified empirically** — run NC, confirm it breaks down on *some* episodes and not others, confirm a hand-tuned controller measurably helps — **not assumed from demand parameters.** (Plan ADR-013 assumed it from citations and was wrong: NC never drops below 83 km/h.)

- **The constant baseline is mandatory, forever.** Every pivot result must report the best *static/constant* controller (an M60-style ladder) next to No-Control and the learned controller. Beating No-Control is not a result. Beating the best constant on the real objective is.

- **Reward = objective, not proxy.** The pivot reward should be the objective (outflow / total delay) — one honest term. Do **not** re-introduce smoothness / variance / comfort terms into the reward; that reinstalls the gameability. Smoothness and safety belong in the *reported secondary metrics* (the §2 accel/jerk instrumentation is fine for that) — measured, never optimized.

- **"Beats NC" ≠ "is useful."** Carry this sentence into every results discussion.

---

## §6 — What this cost, and why documenting it is worth it

The smoothing rescue cost one re-evaluation (no retraining, ~$0, a few hours) and the trap was caught **before submission**, not by a reviewer. The original `lane_sigma` false positive cost the ~$25 ablation. Both were caught cheaply. That is the system working — the failures are inexpensive *if* they are screened early and documented so they are not re-bought.

The standing instruction this encodes: **when a new metric or reward term is proposed, run the §4 screen and say so explicitly in the response.** If a metric fails the screen, it does not get to be a headline or a reward term, regardless of how good its numbers look against No-Control.
