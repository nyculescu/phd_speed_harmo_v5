# Experiments catalog — `training_runs/experiment_*` reference

| Field | Value |
|---|---|
| Doc version | v0.2 (full ablation matrix + detection method) |
| Status | **Active** — append-only catalog; entries are added when an experiment lands, never deleted |
| Last updated | 2026-05-19 |
| Companion docs | [docs/plans/phd_thesis_plan_v0.md](plans/phd_thesis_plan_v0.md) (§8.5 records the headline results derived from these experiments); [README.md](../README.md) (operational); memory entry [`reference_experiments_catalog.md`](file:///home/catalin/.claude/projects/-home-catalin-work-phd-phd-speed-harmo-v5/memory/reference_experiments_catalog.md) (quick-lookup mirror for LLM context) |
| Purpose | Canonical, append-only mapping from `training_runs/experiment_*` folder names to their role, configuration, and headline metrics. When referencing an experiment by ID in any other doc, link back here. |
| Audit invariant | Every folder under `training_runs/experiment_*` either appears in §2 (active) or §3 (retired). Never delete a row — mark superseded entries with **SUPERSEDED BY ...** and keep the original metrics. |

> **Reading guide.** §1 is the policy header (what to keep, upload, strip, and **§1.4 how to detect which ablation a folder ran**). §2 is the live catalog of experiments. §3 is the retirement section. §4 is the cloud-storage layout + tooling. §5 is authoring rules. §6 is the change log.

---

## 1. Retention + upload policy

### 1.1 What each experiment folder contains

Every `experiment_<TS>/` directory produced by `train.py` follows this layout:

```
experiment_<TS>/
├── {algo_box}/                         # e.g. tqc_box4/
│   ├── config.yaml                     # ⭐ audit-trail snapshot of weights, hyperparams, CAV %, etc.
│   ├── {algo_box}_seed{N}.log          # 5 files (or 3 for partial runs) — train.py stdout per seed
│   └── {algo}_seed{N}/                 # 5 dirs (or 3 for partial)
│       ├── best_model/best_model.zip   # ⭐ EvalCallback-best snapshot per seed
│       ├── checkpoints/*_steps.zip     # intermediate snapshots — REDUNDANT after final exists
│       ├── eval_logs/evaluations.npz   # EvalCallback raw data — redundant with eval CSV
│       ├── final_model.zip             # ⭐ end-of-training save
│       └── tensorboard/{algo}_s{N}_1/  # ⭐ event files for paper-figure training curves
└── evaluation_<TS>/                    # produced per `evaluate_models.py` invocation
    ├── evaluation_summary.csv          # ⭐ THE paper data (one row per policy × episode)
    └── trajectories.json               # per-step data for per-step plots
└── evaluation_<TS>.log                 # eval-run stdout
```

⭐ = must-keep for paper reproducibility. The rest is recoverable from the must-keeps.

### 1.2 Strip-before-upload rules

For Google Cloud Storage uploads, strip the redundant files to save ~70 % storage:

| Pattern | Action | Why |
|---|---|---|
| `checkpoints/*_steps.zip` | **STRIP** | Intermediate snapshots — only `final_model.zip` + `best_model.zip` are needed for any future eval rerun |
| `eval_logs/evaluations.npz` | **STRIP** | Redundant with `evaluation_summary.csv` |
| `config.yaml`, `*.log`, `final_model.zip`, `best_model.zip`, `tensorboard/*`, `evaluation_*/*` | KEEP | Paper-essential |

### 1.3 Per-experiment paper-relevance tiers

| Tier | Meaning |
|---|---|
| **HEADLINE** | The single experiment whose numbers become the paper's load-bearing claim |
| **ABLATION** | Required for the reward-weight ablation table |
| **REFERENCE** | Required for a secondary claim (50→100 % CAV uplift, reproducibility, etc.) |
| **PAPER-2 HOOK** | Not in Paper 1 but reserved for the next paper |
| **TEST / DEV** | Throwaway runs — local-only, do not upload |

### 1.4 How to identify which ablation an experiment ran

The experiment folder name (`experiment_<TS>`) is **timestamp-only — it does not encode the ablation**. Use one of two detection methods, in order of preference:

**Method A — the `ABLATION:` log line (runs from 2026-05-19 train.py change onward).**
Every per-seed log (`experiment_<TS>/{algo_box}/{algo_box}_seed{N}.log`) prints, near the top:
```
  ABLATION: no_temporal
  Config file: configurations/per_lane_stochastic_no_temporal.yaml
  Reward weights: w_h=0.44 w_t=0.0 w_q=0.31 w_l=0.19 w_s=0.06
```
Detect with: `grep -m1 "ABLATION:" experiment_<TS>/*/*_seed0.log`. This is the canonical method for any run after the train.py change committed alongside catalog v0.2.

**Method B — config.yaml reward-weight fingerprint (works for ALL runs with a config snapshot, including pre-2026-05-19).**
`train.py` saves `experiment_<TS>/{algo_box}/config.yaml`. Parse `sar_config.reward_weights` into the 5-tuple `(w_h, w_t, w_q, w_l, w_s)` and match against this table (every tuple is unique):

| `(w_h, w_t, w_q, w_l, w_s)` | Ablation |
|---|---|
| `(0.35, 0.20, 0.25, 0.15, 0.05)` | base |
| `(0.37, 0.21, 0.26, 0.16, 0.00)` | no_smoothness |
| `(0.47, 0.27, 0.00, 0.20, 0.06)` | no_throughput |
| `(0.44, 0.00, 0.31, 0.19, 0.06)` | no_temporal |
| `(0.41, 0.24, 0.29, 0.00, 0.06)` | no_lane_eq |
| `(0.00, 0.31, 0.38, 0.23, 0.08)` | no_harmonization |
| `(0.70, 0.00, 0.00, 0.30, 0.00)` | harmo_pure |
| `(0.20, 0.10, 0.55, 0.10, 0.05)` | throughput_heavy |
| `(0.20, 0.20, 0.20, 0.20, 0.20)` | uniform_weights |

`tools/eval_to_kpi.py::detect_reward_weights()` implements Method B. If a future ablation collides on weights with an existing one, Method B becomes ambiguous — use Method A (the `ABLATION:` log line) which carries the explicit config name.

---

## 2. Active experiments (sorted by date ascending)

### 2026-05-16 — first 4-VM vast.ai deploy (50 % CAV baseline)

| Folder | Algo | CAV % | Reward config | Seeds | Tier | Size (raw) | Headline metric |
|---|---|---|---|---|---|---|---|
| [`experiment_20260516_094221`](../training_runs/experiment_20260516_094221) | SAC Box(4) | 50 | base | 5 | PAPER-2 HOOK | 420 MB | Mean reward −335 (eval) |
| [`experiment_20260516_094738`](../training_runs/experiment_20260516_094738) | **TQC Box(4)** | 50 | base | 5 | **REFERENCE** (50→100 % CAV uplift baseline — see plan §8.5.3) | 928 MB | Mean reward −321; `lane_sigma` ≈ 14; `max_lane_diff_kph` ≈ 26 |
| [`experiment_20260516_095013`](../training_runs/experiment_20260516_095013) | SAC Box(5) | 50 | base | 5 | PAPER-2 HOOK | 421 MB | Mean reward −343 |
| [`experiment_20260516_095542`](../training_runs/experiment_20260516_095542) | TQC Box(5) | 50 | base | 5 | PAPER-2 HOOK + ADR-014 evidence (CAV-direct / posted hybrid empirical underperformance) | 915 MB | Mean reward −335; cited in [ADR-014 §4](plans/phd_thesis_plan_v0.md#adr-014--pure-cav-direct-vsl-is-a-methodological-necessity-not-a-design-preference) as the hybrid-ablation evidence |

### 2026-05-17 — local reproducibility check

| Folder | Algo | CAV % | Reward config | Seeds | Tier | Size (raw) | Headline metric |
|---|---|---|---|---|---|---|---|
| [`experiment_20260517_174654`](../training_runs/experiment_20260517_174654) | **TQC Box(4)** | 50 | base | 5 | **REFERENCE** (reproducibility evidence — plan §2.2 RQ-table) | 348 MB | Mean reward −323.6 → within 2.4 reward points of `094738` ⇒ training pipeline is reproducible |

### 2026-05-18 — 100 % CAV headline + reward-weight ablation (the Paper 1 backbone)

| Folder | Algo | CAV % | Reward config | Seeds | Tier | Size (raw) | Headline metric |
|---|---|---|---|---|---|---|---|
| [`experiment_20260518_133246`](../training_runs/experiment_20260518_133246) | **TQC Box(4)** | **100** | **base** `(0.35, 0.20, 0.25, 0.15, 0.05)` | 5 | ⭐ **HEADLINE** (plan §8.5.1) | 636 MB | Mean reward **−164.8**; `lane_sigma` **1.61**; `max_lane_diff_kph` **3.29**; `ds_flow_vph` **4 657**; **0 collisions / 150 eps** |
| [`experiment_20260518_133504`](../training_runs/experiment_20260518_133504) | TQC Box(4) | 100 | **harmo_pure** `(0.70, 0.00, 0.00, 0.30, 0.00)` | 5 | ⭐ ABLATION ii (plan §8.5) | 480 MB | Mean reward −196.6; `lane_sigma` 1.75; **4× seed variance vs base** |
| [`experiment_20260518_144123`](../training_runs/experiment_20260518_144123) | TQC Box(4) | 100 | **no_smoothness** `(0.37, 0.21, 0.26, 0.16, 0.00)` | 5 | ⭐ ABLATION i (plan §8.5) | 174 MB | Mean reward −172.9; `lane_sigma` 1.62 — smoothness term is decorative |

### 2026-05-19 — completed reward-weight ablation matrix (5-seed runs)

These six runs complete the 9-config ablation matrix (base + 5 drop-one-out + harmo_pure + throughput_heavy + uniform_weights). All TQC Box(4), 100 % CAV, 5/5 seeds. `experiment_20260519_100431` is the **5-seed re-run** that supersedes the 3-seed partial `experiment_20260518_142808` (now in §3). Headline metrics below are pending — run `tools/eval_to_kpi.py` once these are evaluated.

| Folder | Algo | CAV % | Reward config | Seeds | Tier | Headline metric |
|---|---|---|---|---|---|---|
| [`experiment_20260519_100431`](../training_runs/experiment_20260519_100431) | TQC Box(4) | 100 | **no_throughput** `(0.47, 0.27, 0.00, 0.20, 0.06)` | 5 | ⭐ ABLATION iii (drop `w_q`) — **supersedes `_142808`** | pending eval |
| [`experiment_20260519_102240`](../training_runs/experiment_20260519_102240) | TQC Box(4) | 100 | **no_temporal** `(0.44, 0.00, 0.31, 0.19, 0.06)` | 5 | ⭐ ABLATION iv (drop `w_t`) | pending eval |
| [`experiment_20260519_102247`](../training_runs/experiment_20260519_102247) | TQC Box(4) | 100 | **no_lane_eq** `(0.41, 0.24, 0.29, 0.00, 0.06)` | 5 | ⭐ ABLATION v (drop `w_l`) | pending eval |
| [`experiment_20260519_102845`](../training_runs/experiment_20260519_102845) | TQC Box(4) | 100 | **throughput_heavy** `(0.20, 0.10, 0.55, 0.10, 0.05)` | 5 | ⭐ ABLATION vi (reverse-weighting) | pending eval |
| [`experiment_20260519_103431`](../training_runs/experiment_20260519_103431) | TQC Box(4) | 100 | **no_harmonization** `(0.00, 0.31, 0.38, 0.23, 0.08)` | 5 | ⭐ ABLATION vii (drop `w_h` — closes the matrix) | pending eval |
| [`experiment_20260519_104158`](../training_runs/experiment_20260519_104158) | TQC Box(4) | 100 | **uniform_weights** `(0.20, 0.20, 0.20, 0.20, 0.20)` | 5 | ⭐ ABLATION viii (naive baseline) | pending eval |

---

## 3. Retired / superseded experiments

| Folder | Was | Superseded by | Reason |
|---|---|---|---|
| [`experiment_20260518_142808`](../training_runs/experiment_20260518_142808) | TQC Box(4), 100 % CAV, no_throughput, **3 seeds** (partial) | **`experiment_20260519_100431`** (5 seeds) | The 2026-05-18 no_throughput run completed only 3/5 seeds. The 5-seed re-run on 2026-05-19 is the canonical no_throughput experiment. The partial run's eval data (`evaluation_20260519_085216`) was used in plan §8.5 v0.6 and should be **replaced** by `_100431`'s eval when the plan is next synced. Do not delete the folder — keep for audit per the §2 invariant. |

---

## 4. Cloud-storage layout + tooling

### 4.1 GCS bucket layout

Mirror the local tree so a `gsutil -m rsync` round-trip restores the exact local layout:

```
gs://<your-bucket>/phd_speed_harmo_v5/training_runs/
├── experiment_20260516_094221/   # SAC4 50% (PAPER-2 HOOK)
├── experiment_20260516_094738/   # TQC4 50% (REFERENCE — uplift baseline)
├── experiment_20260516_095013/   # SAC5 50% (PAPER-2 HOOK)
├── experiment_20260516_095542/   # TQC5 50% (PAPER-2 HOOK + ADR-014 evidence)
├── experiment_20260517_174654/   # TQC4 50% reproducibility (REFERENCE)
├── experiment_20260518_133246/   # TQC4 100% base — ⭐ PAPER 1 HEADLINE
├── experiment_20260518_133504/   # TQC4 100% harmo_pure (ABLATION ii)
├── experiment_20260518_142808/   # TQC4 100% no_throughput (ABLATION iii, 3 seeds)
└── experiment_20260518_144123/   # TQC4 100% no_smoothness (ABLATION i)
```

Recommended storage class: **Nearline** ($0.010/GB/mo) for archival; **Standard** ($0.020/GB/mo) if you expect frequent re-downloads. After stripping per §1.2, total upload is ~500-800 MB ⇒ ~$0.005-0.01/mo on Nearline.

### 4.2 Upload command pattern

```bash
BUCKET=gs://<your-bucket-name>
REMOTE_BASE=$BUCKET/phd_speed_harmo_v5/training_runs

# Strip + sync, preserves local copies, safe to re-run.
for exp in experiment_20260518_133246 \
           experiment_20260518_133504 \
           experiment_20260518_142808 \
           experiment_20260518_144123 \
           experiment_20260516_094738 \
           experiment_20260517_174654; do
    gsutil -m rsync -r -d \
        -x ".*/checkpoints/.*_steps\.zip$|.*/eval_logs/evaluations\.npz$" \
        training_runs/$exp $REMOTE_BASE/$exp
done

# Optional Paper-2 hook experiments:
for exp in experiment_20260516_094221 \
           experiment_20260516_095013 \
           experiment_20260516_095542; do
    gsutil -m rsync -r -d \
        -x ".*/checkpoints/.*_steps\.zip$|.*/eval_logs/evaluations\.npz$" \
        training_runs/$exp $REMOTE_BASE/$exp
done
```

### 4.3 Restore command (in case you need to rehydrate locally)

```bash
gsutil -m rsync -r $REMOTE_BASE/experiment_20260518_133246 \
                   training_runs/experiment_20260518_133246
```

---

## 5. How to use this catalog

- **When you launch a new experiment**: add a row to §2 with the folder name, algo, CAV %, reward config, seeds, tier, and a one-line headline metric. Bump the doc version + add a change-log entry.
- **When you retire / supersede an experiment**: move the row to §3 with a "SUPERSEDED BY `experiment_...`" note. Never delete data — the audit invariant is that every folder appearing in `training_runs/` has a row somewhere.
- **When you reference an experiment in another doc**: always use the full folder name (e.g. `experiment_20260518_133246`), link back here, and cite the tier (HEADLINE / ABLATION / REFERENCE / etc.) so future readers know why that run matters.

---

## 6. Change log

| Date | Doc version | Author | Change |
|---|---|---|---|
| 2026-05-19 | v0.1 | Catalin + Claude | Initial catalog. 9 experiments tracked: 4 from the 100 % CAV ablation run (HEADLINE + 3 ABLATIONs), 2 50 % CAV TQC Box(4) references (uplift baseline + reproducibility), 3 Paper-2 hooks. Retention + strip-before-upload policy documented in §1; GCS layout + upload commands in §4. |
| 2026-05-19 | v0.2 | Catalin + Claude | Added the 6 `experiment_20260519_*` runs that complete the 9-config reward-weight ablation matrix (no_throughput 5-seed re-run, no_temporal, no_lane_eq, throughput_heavy, no_harmonization, uniform_weights — all TQC Box(4), 100 % CAV, 5/5 seeds, pending evaluation). Retired the 3-seed partial `experiment_20260518_142808` to §3 (superseded by `_100431`). Added §1.4 "How to identify which ablation an experiment ran" — documents Method A (the new `ABLATION:` seed-log line, added to train.py same day) and Method B (config.yaml weight fingerprint, with the full 9-tuple table). |
