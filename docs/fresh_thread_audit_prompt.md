# Fresh-thread audit prompt

Copy the fenced block below into a **new** Claude conversation started in
`~/work/phd/phd_speed_harmo_v5/`. It instructs a fresh, adversarial LLM to
re-audit the paper-1 plan and the 9-config ablation from scratch.

Option C is in effect: **Task T1 is a blind reproduction** of the
anomaly-vs-normal breakdown; the expected numbers are sealed in **Appendix
R-1** at the bottom, which the new LLM must not open until it has computed
its own. A divergence between the two is itself a finding.

---

```
You are auditing a PhD project from a fresh, adversarial perspective. A
previous Claude instance and I built a paper-1 plan, a 9-config reward-weight
ablation, and an analysis over ~5 days. The previous LLM had two failure
modes I need you NOT to repeat: (1) it shortcut reasoning to save tokens,
(2) it rushed positive conclusions to please me — it once declared "base
config is the empirical winner" from a 4-config sample, and the full
9-config matrix later FALSIFIED that. Treat every prior conclusion as a
claim to verify, including the ones stored in project memory.

## EXHIBIT A — a verified result that already contradicts the plan

The full 9-config reward-weight ablation is complete and evaluated. All 9
configs ran on the SAME deterministic scenario pool (verified: the No-Control
baseline's physical metrics are byte-identical across all 9 — lane_sigma
17.655, ds_flow 4634.0 — so cross-config physical-KPI comparison is valid).

Sorted by lane_sigma (the harmonization KPI the paper's contribution claim
depends on; lower = better):

  rank  config            w_h   lane_sigma  L0-L2_diff  L0_act_std  seed_spread
  1     no_harmonization  0.00  1.21        +0.39       6.44        2.2
  2     throughput_heavy  0.20  1.29        +2.05       9.29        7.5
  3     no_temporal       0.44  1.40        +2.08       9.24        17.5
  4     base (HEADLINE)   0.35  1.61        +3.47       10.27       16.6
  5     uniform_weights   0.20  1.61        +2.91       9.01        21.8
  6     no_smoothness     0.37  1.62        +3.60       9.52        11.5
  7     no_throughput     0.47  1.66        +2.79       10.26       36.6
  8     no_lane_eq        0.41  1.68        +3.92       10.05       11.4
  9     harmo_pure        0.70  1.75        +4.15       10.88       68.6

The config that DROPS the harmonization reward term entirely
(no_harmonization, w_h=0) AND posts near-uniform per-lane limits
(L0-L2 differential 0.39 kph vs base's 3.47) achieves the BEST harmonization
KPI — and converges across all 5 seeds to within 2.2 reward points.
lane_sigma correlates POSITIVELY with per-lane differentiation across all
9 configs: the more the agent uses per-lane control, the worse it harmonizes.

This directly threatens the paper's Contribution Claim #2 ("per-lane
differential CAV-direct VSL is the contribution"). Full data is in
reports/2026-05-20_full_matrix/ (per-experiment .md + cross_experiment .md
+ per_policy_kpis.csv).

## Your job

Audit whether this project has a publishable paper, and if so which one.
Three outcomes are all valid and you must be willing to reach any of them:
  (a) "the per-lane framing survives — here's the evidence and the reframe"
  (b) "the per-lane framing is dead — pivot to a different contribution"
  (c) "this is the wrong paper / the result is not publishable — here's why"
Do NOT default to rescuing the existing plan. If you catch yourself
constructing a charitable interpretation, write the uncharitable one first.

## What to read FIRST (in this order)

1. reports/2026-05-20_full_matrix/cross_experiment_comparison.md and the 9
   per-experiment KPI files — the primary evidence. Verify at least 3 cells
   against the raw evaluation_summary.csv files yourself.
2. docs/plans/phd_thesis_plan_v0.md — plan v0.6. §8.5 is now KNOWN to be
   partly falsified by Exhibit A — read it as a flawed document, not a
   settled one. §2.3 contribution claims, §4 ADRs (esp. ADR-004 per-lane,
   ADR-006 reward, ADR-008 100% CAV, ADR-010 safety), §11 lit comparison.
3. docs/experiment_catalog.md v0.2 — which run is which (the ablation→folder
   mapping; §1.4 explains detection).
4. The project memory directory
   ~/.claude/projects/-home-catalin-work-phd-phd-speed-harmo-v5/memory/ —
   every entry. These encode decisions the prior LLM and I made. Question
   them, especially project_cash_cow_scope_discipline.md (is the narrow
   scope serving the paper or dodging hard questions?) and
   project_paper_first_directive.md.
5. docs/knowledge_base/ — read the 3 closest papers DIRECTLY, do not trust
   the plan's §11 summary: Lu et al. 2023 (TD3LVSL), Vinitsky et al. 2018
   (Lagrangian/CAV-direct), Zhang et al. 2024 (MARVEL).
6. core/env_interact.py, sar_components/rewards/r44_reward_v4.py,
   sar_components/actions/r44_action_v2.py — the actual reward + action code.

## Tasks you MUST perform (not just read — run/compute)

T1. Run the anomaly-vs-normal breakdown across all 9 configs — BLIND.
    The eval CSVs have an `anomaly_type` column; tools/eval_to_kpi.py
    already computes it per-experiment. Compute, for every config, the
    lane_sigma and the mean reward split into normal vs anomaly episodes,
    and the reward delta (anomaly − normal). Determine whether per-lane
    differentiation helps SPECIFICALLY under anomalies (ramp_spike /
    speed_reduction / lane_closure).
      Do this WITHOUT looking at Appendix R-1. Only after you have your
    own numbers written down, open Appendix R-1 and compare. If your
    numbers match within rounding, proceed. If they DIVERGE materially,
    that divergence is itself a finding — report it explicitly in §2 and
    treat the prior analysis as suspect.
      Statistical-power caveat you must carry into the verdict: the
    current eval pool contains only ~10 anomaly episodes per config
    (roughly 5 ramp_spike + 5 lane_closure + 0 speed_reduction). That n
    is too small for a confident anomaly verdict. If T1 is the deciding
    factor for the per-lane contribution, the honest recommendation is a
    dedicated anomaly-heavy eval rerun (anomaly probability raised, all 3
    anomaly types represented, ≥30 episodes/type) BEFORE the contribution
    is declared alive or dead.
      Net rule: if per-lane differentiation does not help under anomalies
    even with a properly powered rerun, the per-lane framing likely has
    no rescue.

T2. Test the "lane_sigma is gameable" hypothesis. lane_sigma is the std of
    the 3 lane speeds. A policy posting uniform limits trivially produces
    uniform speeds → low lane_sigma almost by construction. Read
    r44_reward_v4.py and confirm or refute that lane_sigma can be minimized
    by a trivial uniform policy. If confirmed, lane_sigma is the WRONG
    headline KPI and the paper's metric choice (plan §8.4) is itself a
    finding that needs correction.

T3. Re-derive the "real" comparison on a NON-gameable metric. From the eval
    CSVs: merge throughput, mean/p95 travel time, total TTS, and the
    Tier-A metrics (TTC, hard-braking) from core/eval_metrics.py. Does
    per-lane control (base) beat uniform (no_harmonization / uniform_weights)
    on ANY non-gameable traffic-engineering metric by a margin that exceeds
    seed noise? base's merge_speed is ~1.3 kph above no_harmonization —
    decide if that is signal or noise.

T4. Verify the contribution-novelty claim against the 3 papers directly.
    The plan claims "first TQC + per-lane + ramp + CAV-direct + stochastic
    anomalies". Check whether Lu 2023's lane-cell VSL already covers the
    per-lane element well enough to make our framing thin.

## The load-bearing claims to challenge

For each: defended (with verbatim citation) / needs revision / invalidated.

1. Contribution #1 "first TQC-based VSL controller" — is the algorithm
   choice a genuine contribution or a thin novelty wrapper?
2. Contribution #2 "per-lane differential CAV-direct VSL" — Exhibit A
   appears to falsify this. Can it be rescued (T1, T3) or is it dead?
3. Contribution #4 "safety by construction, 0 collisions / 4320 episodes"
   — SUMO's Krauss model cannot produce rear-end collisions by
   construction when parameters are sane. So 0 collisions is determined
   by the simulator, not the controller. Is this a real claim or a
   tautology dressed as a result?
4. 100% CAV scope (ADR-008) — unrealistic for near-term deployment. Does
   ADR-014's display-constraint argument actually answer the deployment
   objection, or just sidestep it?
5. The reward design (ADR-006) — Exhibit A shows the harmonization term
   is COUNTERPRODUCTIVE (no_harmonization beats base). The 5-term reward
   is not just un-tuned, it may be actively wrong. What does a defensible
   reward look like given this?
6. The +40 reward gain over M60_active — magnitude vs what TD3LVSL /
   MARVEL reported. Publishable, or thin?
7. TQC vs SAC — claimed superior but never compared at 100% CAV. Is the
   TQC claim supported by any measurement?
8. The 9-config ablation itself — did it strengthen the paper or did it
   produce a result (Exhibit A) that breaks the paper? Either way: was
   the ~$25 of compute well spent, and what does the result demand now?
9. Cash-cow scoping (ADR-012) — honest scope discipline, or avoidance of
   the hard comparisons (MPC, external DRL, multi-topology, HDV sweep)?
10. The §11 lit comparison — re-verify the verbatim quotes and the
    novelty conclusion against the actual PDFs.

## Anti-sycophancy rules

- When you start to agree with the prior plan, write the strongest
  counter-argument first.
- Verbatim quotes from docs/knowledge_base/ are REQUIRED when defending
  or attacking any claim — paraphrase is insufficient (standing user
  instruction).
- If your conclusion contradicts the prior LLM's, state the contradiction
  explicitly and do not soften it.
- Do NOT structure the output as "ratify with caveats". If the honest
  answer is "pivot" or "wrong paper", say exactly that in §1.

## Anti-token-economy rules

- Read full sources. Use Read with explicit PDF page ranges. Do not skim.
- Recompute any number a claim depends on from the source CSV yourself.
- When the plan cites a paper, open the PDF and verify the quote.

## Output

A markdown report:
- §1 Verdict in one sentence: "ship as-is" / "revise before submission" /
  "pivot the contribution" / "wrong paper, start over".
- §2 Per-claim audit (the 10 items) — defended / revise / invalidated,
  with verbatim evidence and the T1-T4 results. Include the T1 blind-vs-
  Appendix-R-1 comparison (match or divergence).
- §3 If a pivot is warranted: the 2-3 strongest alternative paper framings,
  with the evidence each would rest on. (One candidate to evaluate: the
  reward-design finding itself — "explicit harmonization rewards are
  counterproductive in per-lane VSL" is a contrarian, publishable result
  IF lane_sigma survives T2 as a valid metric.)
- §4 Reviewer-attack rehearsal: the 3 hardest questions, and the strongest
  honest answers.
- §5 One paragraph: did the prior LLM's framing serve me or mislead me?
  Be specific and unsparing.

Read and run the tasks before writing the audit. Do not commit anything.
Take as long as you need.

================================================================
## APPENDIX R-1 — SEALED. Do NOT read until T1 is computed blind.
================================================================

This is the prior LLM's anomaly-vs-normal result. It exists ONLY so you
can check your blind T1 computation against it. Reading it before you have
your own numbers defeats the purpose — the whole point is an independent
reproduction. Open it only after T1's numbers are written down.

Prior LLM's T1 result (computed 2026-05-20):
  * no_harmonization (w_h=0) wins physical lane_sigma in BOTH regimes:
      normal lane_sigma 1.174, anomaly lane_sigma 1.784.
  * no_harmonization is the MOST anomaly-robust config by reward delta
      (anomaly mean reward − normal mean reward):
        no_harmonization  Δ −3.1
        base (HEADLINE)   Δ −15.4
        harmo_pure        Δ −31.7
  * NO anomaly type favors the per-lane-heavy configs. The per-lane
      framing gets no rescue from the anomaly angle in this data.
  * CAVEAT (load-bearing): this rests on only ~10 anomaly episodes per
      config — 5 ramp_spike + 5 lane_closure + 0 speed_reduction. n is
      too small for a confident verdict, and speed_reduction is entirely
      unobserved. Do not treat this as settled; a properly powered
      anomaly-heavy rerun is required before the per-lane contribution
      is declared dead on this basis.

How to use this appendix:
  * If your blind T1 numbers match within rounding → the prior analysis
    reproduces; report "T1 reproduces Appendix R-1" and proceed.
  * If they DIVERGE → do not silently adopt either set. Report the
    divergence in §2, investigate which is correct from the raw CSVs,
    and treat the prior LLM's wider analysis as suspect.
```
