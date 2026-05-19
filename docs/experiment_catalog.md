# Experiments catalog — `training_runs/experiment_*` reference

| Field | Value |
|---|---|
| Doc version | v0.1 (initial) |
| Status | **Active** — append-only catalog; entries are added when an experiment lands, never deleted |
| Last updated | 2026-05-19 |
| Companion docs | [docs/plans/phd_thesis_plan_v0.md](plans/phd_thesis_plan_v0.md) (§8.5 records the headline results derived from these experiments); [README.md](../README.md) (operational); memory entry [`reference_experiments_catalog.md`](file:///home/catalin/.claude/projects/-home-catalin-work-phd-phd-speed-harmo-v5/memory/reference_experiments_catalog.md) (quick-lookup mirror for LLM context) |
| Purpose | Canonical, append-only mapping from `training_runs/experiment_*` folder names to their role, configuration, and headline metrics. When referencing an experiment by ID in any other doc, link back here. |
| Audit invariant | Every folder under `training_runs/experiment_*` either appears in §2 (active) or §3 (retired). Never delete a row — mark superseded entries with **SUPERSEDED BY ...** and keep the original metrics. |

> **Reading guide.** §1 is the policy header (what to keep, what to upload, what to strip). §2 is the live catalog of experiments and what each one contains. §3 is the retirement section (none yet). §4 is the cloud-storage layout + tooling. §5 is the change log.

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
| [`experiment_20260518_142808`](../training_runs/experiment_20260518_142808) | TQC Box(4) | 100 | **no_throughput** `(0.47, 0.27, 0.00, 0.20, 0.06)` | **3** ⚠ | ⭐ ABLATION iii (plan §8.5) | 33 MB | Mean reward −182.6 (partial); **throughput preserved** at 4 662 vph despite `w_q=0` — key paper claim |
| [`experiment_20260518_144123`](../training_runs/experiment_20260518_144123) | TQC Box(4) | 100 | **no_smoothness** `(0.37, 0.21, 0.26, 0.16, 0.00)` | 5 | ⭐ ABLATION i (plan §8.5) | 174 MB | Mean reward −172.9; `lane_sigma` 1.62 — smoothness term is decorative |

---

## 3. Retired / superseded experiments

*(none yet — append here when retiring an entry from §2)*

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
