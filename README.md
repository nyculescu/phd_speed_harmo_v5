# phd_speed_harmo_v5

Speed harmonization at a highway **on-ramp / off-ramp interchange** using Lagrangian CAV direct control
(`traci.vehicle.slowDown()`) and distributional RL (TQC primary; SAC baseline).

Single topology: **ramps_v0** — 3-lane mainline → 4-lane weaving buffer (250 m) → 3-lane downstream,
with on-ramp and off-ramp flanking the weave.

Run all commands from the project root (`phd_speed_harmo_v5/`).

> **Research design, ADRs, system architecture, evaluation methodology, and literature positioning live in [`docs/plans/phd_thesis_plan_v0.md`](docs/plans/phd_thesis_plan_v0.md).** This README is purely operational — how to install, run, deploy, and collect results.

---

## Directory layout

```
phd_speed_harmo_v5/
├── core/                              SUMO/RL interface (env, regime detector, SAR ABCs)
├── sar_components/                    pluggable state/action/reward registry
├── tools/                             diagnostic utilities (no_control_baseline, status checker)
├── traffic_environment/               SUMO network + scenario + fleet + demand + anomaly generators
├── train.py                           SAC/TQC training entrypoint
├── evaluate_models.py                 held-out 30-ep evaluation vs 11 baselines
├── generate_scenarios.py              CLI for scenario pool generation
├── deploy_remote.sh                   bootstrap one vast.ai VM
├── deploy_4vm.sh                      per-VM dispatcher (1/2/3/4 → SAC/TQC × Box(4)/Box(5))
├── launch_training.sh                 config-aware training entrypoint
├── launch_evaluation.sh               config-aware evaluation entrypoint
├── configurations/                    YAML configs
├── tests/                             pytest + test_smoke_training.py
└── docs/
    ├── plans/phd_thesis_plan_v0.md    ← research design, ADRs, architecture
    └── knowledge_base/                literature corpus (gitignored)
```

---

## Step 1: No-control baseline (diagnostic)

```bash
# Run all 5 scenarios (requires SUMO 1.21+ and TraCI)
python3 -m tools.no_control_baseline

# Run with sumo-gui (interactive)
python3 -m tools.no_control_baseline --gui

# Run a single scenario (index 0 = lightest demand)
python3 -m tools.no_control_baseline --scenarios 0
```

Outputs → `tools/results/`:
- `baseline_<main>_<ramp>.csv` — per 30-s window: flow, space-mean speed, breakdown flag
- `baseline_summary.csv` — breakdown time, min/mean speed, throughput per scenario
- `baseline_<main>_<ramp>.png` — speed + flow time-series (requires matplotlib)

Breakdown criterion: harmonic-mean speed across all 4 lanes of `seg_0_after` entry drops below **60 km/h** for at least one 30-s window with ≥ 1 vehicle detected.

> ⚠ `ramps_v0.net.xml` must exist before running. If missing, run
> `python3 traffic_environment/sumo/generate_ramp_network.py` and then open the file
> in **netedit → Processing → Compute Junctions** to generate internal edges.

---

## Detector inventory

| Family | Count | ID pattern | Freq |
|---|---|---|---|
| E1 induction loops | 48 | `flow_loop_{seg}_{lane}_{pos}` | 30 s |
| E3 multi-entry-exit | 5 | `e3_seg_*`, `e3_corridor` | 30 s |

Segments covered: `seg_2_before`, `seg_1_before`, `seg_0_before`,
`seg_0_after` (4-lane weaving zone — **critical**),
`ramp_on_approach`, `ramp_on_transition`, `ramp_on_merge`,
`ramp_off_diverge`, `ramp_off_transition`, `ramp_off_departure`.

---

## Local smoke test (verify before remote deploy)

```bash
.venv/bin/python tests/test_smoke_training.py
# 8-test suite: imports → config → env dry-run → env live → SubprocVecEnv → SAC fit → TQC fit → save/load
# Expected: all 8 pass in < 30 s
```

---

## Remote VM bootstrap

Reproducible 8-step sequence to take a clean PyTorch VM (Ubuntu, sudo, internet) from zero to a running experiment. Run **on the VM** after SSH-ing in.

```bash
# 1. Generate an SSH keypair on the VM
ssh-keygen -t ed25519 -C "phd-vm-$(hostname)" -f ~/.ssh/id_ed25519 -N ""

# 2. Print the public key
cat ~/.ssh/id_ed25519.pub

# 3. Paste it into GitHub as a *deploy key* on this repo
#    https://github.com/nyculescu/phd_speed_harmo_v5/settings/keys
#    (Add deploy key → leave "Allow write access" unchecked → Add key)

# 4. Verify SSH auth to GitHub
ssh -T git@github.com
#    Expected: "Hi nyculescu/phd_speed_harmo_v5! You've successfully authenticated..."

# 5. Clone the repo
git clone git@github.com:nyculescu/phd_speed_harmo_v5.git ~/phd_speed_harmo_v5

# 6. Enter it
cd ~/phd_speed_harmo_v5

# 7. Bootstrap (system pkgs, SUMO, venv, deps, smoke test) — ~5 min
bash deploy_remote.sh

# 8. Launch the assigned experiment inside tmux (N ∈ {1,2,3,4})
tmux new -s v5

# 8a — headline run (default reward weights, 100% CAV)
./deploy_4vm.sh N      # 1=SAC Box(4) · 2=TQC Box(4) · 3=SAC Box(5) · 4=TQC Box(5)

# 8b — reward-weight ablation runs for TQC Box(4) - same algorithm slot + a --config override
./deploy_4vm.sh 2 --config configurations/per_lane_stochastic_harmo_pure.yaml
./deploy_4vm.sh 2 --config configurations/per_lane_stochastic_no_smoothness.yaml
./deploy_4vm.sh 2 --config configurations/per_lane_stochastic_no_throughput.yaml
./deploy_4vm.sh 2 --config configurations/per_lane_stochastic_no_temporal.yaml
./deploy_4vm.sh 2 --config configurations/per_lane_stochastic_no_lane_eq.yaml
./deploy_4vm.sh 2 --config configurations/per_lane_stochastic_throughput_heavy.yaml

#    Ctrl-B, D to detach.  tmux attach -t v5 to reattach.
```

Available reward configs (rationale + ADR linkage in [docs/plans/phd_thesis_plan_v0.md §4](docs/plans/phd_thesis_plan_v0.md), §8.5 for results):

| Config file | Weights `(w_h, w_t, w_q, w_l, w_s)` | Output dir suffix | Ablation role |
|---|---|---|---|
| `per_lane_stochastic.yaml` (default) | `(0.35, 0.20, 0.25, 0.15, 0.05)` | `tqc_box4_<ts>/` | **headline** — base 5-term reward |
| `per_lane_stochastic_no_smoothness.yaml` | `(0.37, 0.21, 0.26, 0.16, 0.00)` | `tqc_box4_no_smoothness_<ts>/` | drop-one-out: `w_s = 0` |
| `per_lane_stochastic_no_throughput.yaml` | `(0.47, 0.27, 0.00, 0.20, 0.06)` | `tqc_box4_no_throughput_<ts>/` | drop-one-out: `w_q = 0` |
| `per_lane_stochastic_no_temporal.yaml` | `(0.44, 0.00, 0.31, 0.19, 0.06)` | `tqc_box4_no_temporal_<ts>/` | drop-one-out: `w_t = 0` |
| `per_lane_stochastic_no_lane_eq.yaml` | `(0.41, 0.24, 0.29, 0.00, 0.06)` | `tqc_box4_no_lane_eq_<ts>/` | drop-one-out: `w_l = 0` |
| `per_lane_stochastic_harmo_pure.yaml` | `(0.70, 0.00, 0.00, 0.30, 0.00)` | `tqc_box4_harmo_pure_<ts>/` | extreme: only `w_h + w_l` |
| `per_lane_stochastic_throughput_heavy.yaml` | `(0.20, 0.10, 0.55, 0.10, 0.05)` | `tqc_box4_throughput_heavy_<ts>/` | reverse-weighting: throughput dominant |

Use a distinct VM per config — each one is a separate 1M-step training run (~9.5 h wallclock on EPYC 7B13). The output dir suffix lets you rsync them into non-overlapping `artifacts/` subdirectories.

> ⚠ **vast.ai shutdown gotcha:** `sudo shutdown` does NOT work inside vast.ai containers (no systemd init). The auto-shutdown trap will print `WARNING: 'sudo shutdown' failed`. Either stop each VM manually from the vast.ai web console after `.done_SUCCESS` is touched, OR install vastai CLI on the VM (`pip install vastai`, set `VAST_API_KEY`) and run `vastai stop instance $VAST_CONTAINERLABEL` from a completion hook.

---

## Result collection (rsync from your laptop)

Run from the project root (`cd ~/work/phd/phd_speed_harmo_v5/`) so the relative `./artifacts/...` path lands inside the repo.

```bash
# Generic pattern — replace PORT, IP, and KEY (one of vm1_sac_4 / vm2_tqc_4 / vm3_sac_5 / vm4_tqc_5)
rsync -avz --partial --mkpath -e "ssh -p <PORT>" \
    root@<IP>:~/phd_speed_harmo_v5/training_runs/ \
    ./artifacts/<KEY>/training_runs/

# Concrete example — vast.ai gives you:
#   ssh -p 46704 root@108.197.217.16 -L 8080:localhost:8080
# Drop the -L tunnel (not needed for rsync). For VM 3 (sac_5):
rsync -avz --partial --mkpath -e "ssh -p 46704" \
    root@108.197.217.16:~/phd_speed_harmo_v5/training_runs/ \
    ./artifacts/vm3_sac_5/training_runs/
```

Notes:
- `-e "ssh -p <PORT>"` is mandatory — vast.ai uses non-standard SSH ports per container.
- `--mkpath` (rsync ≥ 3.2.3) auto-creates the destination's parent directories. Without it you'd need `mkdir -p ./artifacts/<KEY>/training_runs/` first.
- VM keys are exactly: `vm1_sac_4`, `vm2_tqc_4`, `vm3_sac_5`, `vm4_tqc_5` (matching `deploy_4vm.sh N` mapping).

### Checking training status from your laptop

To run [tools/check_training_status.sh](tools/check_training_status.sh) on a VM in one shot:

```bash
# Generic
ssh -p <PORT> root@<IP> 'cd ~/phd_speed_harmo_v5 && git pull -q && ./tools/check_training_status.sh'

# Concrete — vast.ai gave you `ssh -p 46704 root@108.197.217.16 -L 8080:localhost:8080`:
ssh -p 46704 root@108.197.217.16 'cd ~/phd_speed_harmo_v5 && git pull -q && ./tools/check_training_status.sh'
```

> ⚠ **Don't copy the SSH fragment out of the rsync line above.** The rsync uses `-e "ssh -p <PORT>"` and the `"` is the closing quote of that argument — for a direct `ssh` command, drop the surrounding quotes: just `ssh -p <PORT> root@<IP>`. If you see bash sitting at a `>` continuation prompt, that's the unclosed quote — Ctrl-C and retype.

Interactive form if you want a shell on the VM (then run commands by hand):
```bash
ssh -p <PORT> root@<IP>
# you're now on the VM
cd ~/phd_speed_harmo_v5 && git pull && ./tools/check_training_status.sh
```

Exit codes: `0` = DONE (5/5 final_model.zip) · `1` = still TRAINING · `2` = STOPPED incomplete. Useful for chaining:
```bash
ssh -p <PORT> root@<IP> 'cd ~/phd_speed_harmo_v5 && ./tools/check_training_status.sh' \
  && echo "VM done — safe to stop"
```

---

## Hardware spec for vast.ai (next deploy)

Per VM, `deploy_4vm.sh N` runs 5 seeds × 48 SUMO workers (≈240 processes), 1M timesteps. **Workload profile:** CPU-bound · peak RAM ≈ 94 GB · peak disk ≈ 8 GB · no GPU needed.

### CPU ranking — fastest first (TQC Box(4) reference)

| CPU model | Silicon | fps | Source |
|---|---|---|---|
| AMD EPYC 9xxx | Genoa / Bergamo (Zen 4) | likely > 32 | untested |
| AMD EPYC 7B13 | Milan (Zen 3, Google custom) | 32 | measured, 1-socket dedicated, 2026-05-16 |
| AMD EPYC 7J13 | Milan (Zen 3, Google custom) | 32 | measured, 1-socket dedicated, 2026-05-18 |
| AMD EPYC 7V13 | Milan (Zen 3, Azure custom) | ~30 | normalized from 2026-05-16 (was shared 128/256) |
| AMD EPYC 7773X | Milan-X (Zen 3 + V-Cache) | ~30 | normalized from 2026-05-16; extra L3 unused here |
| AMD EPYC 7B12 | **Rome** (Zen 2, Google custom) | 27–29 | measured, 1-socket dedicated, 2026-05-18 |
| AMD EPYC 7742 / 7763 / 7702 | **Rome** (Zen 2) | ~24–28 | extrapolated from 7742 measurement |

**Generation flag in the model number:** the trailing digit is what changes Zen generation, not the letter. `…X3` = Milan (Zen 3, fast), `…X2` = Rome (Zen 2, slower), `…X4` = Genoa (Zen 4, expected faster). Letter prefix (`B`/`J`/`V`/none) is just the customer (Google/Google/Azure/retail).

**Variables beyond model number that change observed fps:** sockets (1 vs 2 → NUMA), CPU allocation (dedicated `128/128` vs shared `128/256` → noisy neighbor), and per-listing boost state. The numbers above are from 1-socket dedicated instances. Dual-socket and shared variants are untested.
