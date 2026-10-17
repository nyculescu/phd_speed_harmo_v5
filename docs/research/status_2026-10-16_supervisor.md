# PhD status for the supervisor meeting (16 Oct 2026)

**Thesis:** "Adaptive driving algorithms for intelligent road traffic systems". Submission is planned for about September 2027, with 2 papers targeted.

## 1. What happened this month

We narrowed the work to **algorithm-first** ideas that fit the title (decisions V77–V79) and tested each in two tiers:
1. a one-page screen on throw-away data;
2. a confirmatory protocol, written and approved before any data was read (V80).

| Idea | Screen (throw-away data) | Confirmatory (unread data) |
|---|---|---|
| #2 Commit margin at signals (Hamburg signal archive) | **STOP.** Fixed margins already transfer week to week; even the best fixed margin gains < 1 point, so there is no room for adaptation. | not run |
| #1 Self-calibrating safety margin for car-following (NGSIM, then TGSIM) | **CONTINUE.** Fixed margins fitted on one freeway were wrong on another, by up to 55 % misses against a 5 % target. | **VALID-ONLY.** The method met its 7.5 % miss limit, but it used ~5–25 % longer gaps than the simple alternatives. No paper. |

**Confirmatory facts:**
- Protocol V84; run once; independently re-checked.
- Only two regimes, on the *same* freeway on another day, had enough data to count.
- The "new road" question could not be tested. One dataset's congestion fell in a single 8-minute run, which I did not check before fixing the protocol's gate.
- TGSIM is now fully used.
- Details: `docs/research/results/confirm_1_result.md`.

## 2. What we learned

- **Pre-registration worked as intended.** It stopped two attractive-looking screen results from turning into overclaims.
- **The adaptive idea did not beat simple baselines when tested properly.** Its validity was nearly built into the update rule, so validity alone is weak evidence.
- **The planning lesson:** check that the data can actually fill the cells a protocol requires before fixing its gates.

## 3. Options for the thesis's positive result

| Option | What it is | Cost (author / build / compute) | Main risk |
|---|---|---|---|
| A | **Idea #3:** uncertainty-adaptive wave smoothing from roadside radar, on real I-24 waves (WaveX). The data is downloaded and unread. | ~3 h decisions / 2–4 days / hours | Others are working on this (scoop risk); the gain may be about 0 |
| B | **Idea #1, version 2:** a redesigned margin on fresh freeway data (e.g. highD/exiD, access request needed [VERIFY]) | several hours plus waiting for access / 1–2 days / < 1 h | It may lose to "calibrate briefly, then freeze" again |
| C | **Resume the SUMO coordinated-zones line** (protocol P0–P2 v1 approved; v2 on hold) or the traffic-signal line (v6) | many hours / days to weeks / hours to days | A broad scope, which is what V77 tried to avoid |
| D | **A chapter-based thesis** in which the pre-registered studies, including null and VALID-ONLY results, are a contribution in their own right | ~2 h / ~1 day / none | Depends on what the university accepts |

## 4. Questions for the supervisor

1. **What counts as a "paper"** for the thesis: submitted, accepted, workshop?
2. **Which claim bar applies at thesis level** now that DRL has been dropped (V83)? Is a pre-registered "conditional advantage" enough, or must a learning-based controller still beat a tuned baseline (the old D5.8)?
3. **Is a VALID-ONLY or null chapter acceptable** if it is pre-registered and reported in full?
4. **Which option, A–D,** with about 11 months left? The ITSC 2027 deadline is 1 Mar 2027.
