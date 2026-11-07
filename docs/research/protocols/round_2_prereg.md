# Round 2 pre-registration: four candidates trained while round 1 evaluates

Status: approved 2026-11-06 (V439), written before any round-1 validation or test result exists. Seeds approved: DRL training option A, 3E tuning 7,440,700–7,440,739.

## Why now

The author's request (2026-11-06): use the idle CPUs of the rented machine (V437) for the options from the nine-agent memo (`docs/reports/2026-11-05_21-29/`) not built in round 1. The author picked 2B, 1B, 1D and 3E.

## Candidates

The three DRL candidates each make one change to v3w's recipe, round 1's control. Everything else is as in round 1:
- plant r2m3;
- training levels 4,500–6,000 by 250;
- 5 learners × 3 envs, 500 updates;
- gamma 0.933, lambda 0.967, net seed 20261205;
- TensorBoard-only logging;
- the `tbcheck1.py` training checks.

Each candidate compares one-to-one against v3w.

| Candidate | Change | Memo finding | Design |
|---|---|---|---|
| 2B | learning rate and entropy coefficient decay linearly over the 500 updates; one critic scale for all learners: the median of v3w's five learner scales | F2: training stops improving early, then drifts toward close-following | memo §2B |
| 1B | gate mask: where the action cannot change anything, the level is held and the decision leaves the policy loss | F3: about half the decisions cannot act yet train the policy | memo §1B |
| 1D | the safety charge reads hard braking at every 0.1-s SUMO step instead of the 1-Hz sample | V367: 1-Hz metrics miss 9 m/s² ALKS braking | memo §1D |
| 3E | CMA-ES tunes a per-zone own-state rule (not DRL): the strongest non-learning opponent | memo: "before any thesis claim" | memo §3E |

"Memo §" means the option's section in `docs/reports/2026-11-05_21-29/drl_options_2026-11-05_21-29.html`. The `source/p*.md` files are the nine agents' raw reports, not option designs; this table first named them by mistake (corrected 2026-11-06, V440). Exact settings follow the memo sections. Where a design leaves a value open, the implementation states it, and it is fixed here before training starts.

## Values fixed before training (V440)

These are the open values from the implementation and the ultracode review (no blockers), set before any round-2 training starts.

**2B** (branch `r2/2b-anneal`)
- The learning rate and the entropy coefficient decay as v0·(1 − u/500), over the whole run, so the last update still learns. The memo puts the entropy decay in the second half only; this protocol keeps the whole run, as its table row says.
- The critic scale is fixed at 2.1246540546417236, the median of v3w's five scales (learner C1's own).
- The memo's gradient-norm and per-term diagnostics are not logged.

**1B** (branch `r2/1b-gate-mask`)
- A decision is masked when its vehicle is not in the V2V gate set at decision time, the memo's gate. Decisions inside a hold window are not masked; the level is still held there.
- GAE and the value loss keep every row. The policy loss, the entropy bonus and the advantage normalisation use the open rows of each minibatch.
- 1B's `ppo/entropy`, `kl` and `clipfrac` cover open rows only, so they are not comparable with v3w's all-row values.

**1D** (branch `r2/1d-brake-10hz`)
- Hard braking (≤ −3.0 m/s², the ALKS vehicle and its follower) is read at every 0.1-s step. The charge is the share of each second spent hard-braking, with the safety weight and the follower weight unchanged.
- The TTC term stays the 1-Hz flag. The memo's 1D also moves TTC to step resolution; that part is left for a later round.
- `ep/e*/brake_step` counts 0.1-s readings, about 10× `brake_hz`'s 1-Hz flags.

**All three**
- `tbcheck1.py` checks each new candidate's settings against `common2.env_for` and its trainer extras.
- It also requires each candidate's own TensorBoard tags at every update: 2B `ppo/lr` and `ppo/ent_coef`; 1B `ppo/mask_frac`; 1D `brake_hz` and `brake_step`.
- Launch: `docs/research/round2/chain2r.sh KIND CODE_DIR OUT_ROOT`. It runs from the candidate branch's snapshot, with round 1's stage-0 references.

**3E** (branch `r2/3e-cmaes`, settings fixed before the search, V441)

The rule family:
- **Zones:** 5 (up, merge 1, between, merge 2, down). The edges are −100, 594.72, 1389.02 and 2083.74 m from the start of edge 3a, and ramp vehicles count in their merge zone.
- **Parameters:** 4 per zone, 20 in all: th 0–25 m/s, crowd 0–30, level 0–3, and an on/off switch. They are encoded on the unit cube.
- **CMA:** diagonal, sigma 0.25, CMA seed 20261106.
- **Start point:** os1_15_10's values in zones 1–4, with the upstream zone off. The family cannot copy os1_15_10 exactly, because its x_min of 500 m falls inside merge 1. The reference stays os1_15_10 itself.

The objective, minimised, follows memo §3E: least close-following at a bounded delay cost. It adds three terms:
- the pooled change in TTC seconds against os1_15_10 on the same seeds: per level, the median of paired differences; summed over levels; divided by the summed reference medians; in %;
- 5 per % of all_delay above +2 % at each level;
- 5 per collision beyond the reference.

The search:
- **Condition:** T, the training slowdowns.
- **Levels:** 4,500, 5,000, 5,250, 5,500, 6,000.
- **Budget:** population 24, 100 generations. Each generation takes 8 seeds rotating through the 40 approved tuning seeds, shared by every candidate and the reference.

The final pick:
- The 5 best distinct configurations are re-evaluated with the reference on all 40 tuning seeds at the 5 levels. The lowest pooled loss is the opponent.
- Overfitting to the tuning seeds is judged in round 2 on fresh seeds.
- Side metrics, such as full-emergency events and flow, are not constrained here; round 2's admissibility checks apply them.

Before round 2 evaluates the opponent:
- The zone rule moves into `b_env.py` with a `plant_sweep` key, because today only the search's own worker can run it.
- Whether to tune at round 1's deciding cells (X1/X2 at 5,300) instead of condition T is round 2's protocol decision.

## Seeds (for approval)

- **DRL training, option A (recommended):** the same training seeds as round 1, 7,464,000–7,471,799. These are the seeds v3w trained on, so each candidate differs from the control only by its change. They are training seeds, not evaluation seeds.
- DRL training, option B: fresh seeds 7,471,800–7,479,599, in the same layout as round 1.
- **3E tuning:** 7,440,700–7,440,739, fresh.
- Smoke runs use the existing smoke seed 7,419,899.

## Evaluation

Training curves are not results. The candidates are judged in round 2:
- on fresh validation and test seeds;
- under a round-2 protocol written before any round-2 candidate's validation result is read;
- with the round-1 finalists and the tuned rules (3E among them) alongside.

## Machine

These run on the rented machine of V437. Its rows and training fingerprint equal the laptop's, so the machine cannot change results.
