# Remote Machine Deployment Guide

Deploy `phd_speed_harmo_v5` on a fresh vast.ai / Ubuntu 22.04+ machine and run the v5.1 training pipeline (SAC + TQC with per-lane differential VSL, stochastic demand, and anomaly injection).

Tested on vast.ai (root@, web terminal, Ubuntu 22.04, no GPU required — training is CPU-bound by SUMO).

---

## Step 1 — SSH key for GitHub

```bash
ssh-keygen -t ed25519 -C "cn.cata@gmail.com"
# Press Enter for defaults (no passphrase is fine)

cat ~/.ssh/id_ed25519.pub
# Copy the output
```

Go to https://github.com/settings/keys → **New SSH key** → paste → **Add SSH key**.

Verify:

```bash
ssh -T git@github.com
# Expected: "Hi nyculescu! You've successfully authenticated..."
```

## Step 1.5 — Connect via VS Code (Optional but Recommended)

1. Install **Remote - SSH** extension in VS Code.
2. Open `~/.ssh/config` and add:

```
Host VastContainer
    HostName <IP from vast.ai>
    User root
    Port <Port from vast.ai>
    IdentityFile ~/.ssh/id_ed25519
```

3. Connect via Command Palette → **Remote-SSH: Connect to Host** → VastContainer.

## Step 2 — Clone and deploy

```bash
cd /workspace
git clone git@github.com:nyculescu/phd_speed_harmo_v5.git
cd phd_speed_harmo_v5
bash deploy_remote.sh
```

The deploy script automatically:
- Installs Python 3.12, SUMO (via `ppa:sumo/stable`), tmux
- Creates `.venv` with all pip dependencies (SB3, SB3-Contrib, PyTorch, etc.)
- Sets `SUMO_HOME` in `~/.bashrc`
- Runs the **8-stage smoke test** to verify the full pipeline
- Prints hardware info and recommended `--n-envs` for this machine

## Step 3 — Run training

```bash
source .venv/bin/activate
export SUMO_HOME="/usr/share/sumo"

# Quick sanity test first (2 min):
bash launch_training.sh test

# Full experimental suite:
#   128-core machine → ~9 hours (SAC + TQC Box(4) + TQC Box(5))
#   30-core machine  → ~42 hours
nohup bash launch_training.sh remote > training.log 2>&1 &
tail -f training.log
```

**Use tmux** so training survives SSH disconnects:

```bash
tmux new -s v5train
bash launch_training.sh remote
# Ctrl+B, D to detach
# tmux attach -t v5train to reattach
```

## Step 4 — Monitor training

```bash
# Live log
tail -f training.log

# Per-seed logs
tail -f training_runs/experiment_*/sac_box4_seed*.log

# TensorBoard (access via browser at http://<IP>:6006)
tensorboard --logdir training_runs/ --bind_all --port 6006
```

## Step 5 — Results

| Output | Location |
|--------|----------|
| Training logs | `training_runs/experiment_<timestamp>/` |
| Per-seed logs | `training_runs/experiment_<timestamp>/<algo>_box4_seed*.log` |
| Best models | `training_runs/experiment_<timestamp>/<algo>_box4/<algo>_seed<N>/best_model/` |
| Final models | `training_runs/experiment_<timestamp>/<algo>_box4/<algo>_seed<N>/final_model.zip` |
| Eval metrics | `training_runs/experiment_<timestamp>/<algo>_box4/<algo>_seed<N>/eval_logs/` |
| TensorBoard | `training_runs/experiment_<timestamp>/<algo>_box4/<algo>_seed<N>/tensorboard/` |
| Config snapshot | `training_runs/experiment_<timestamp>/<algo>_box4/config.yaml` |

## What the training runs

| Experiment | Algorithm | Action space | Workers/seed | Seeds |
|------------|-----------|-------------|-------------|-------|
| 1 | SAC | Box(4) per-lane Lagrangian | 24 (remote) / 5 (local) | 0–4 |
| 2 | TQC | Box(4) per-lane Lagrangian | 24 / 5 | 0–4 |
| 3 | TQC | Box(5) mixed Lagrangian-Eulerian | 24 / 5 | 0–4 |

Each seed trains for 1M timesteps (~8,333 episodes × 120 steps). Episodes use stochastic demand profiles (peak 5500–8000 vph) with 15% anomaly injection.

---

## Quick reference (copy-paste the whole block)

```bash
# 1. SSH key (only once per machine)
ssh-keygen -t ed25519 -C "cn.cata@gmail.com"
cat ~/.ssh/id_ed25519.pub
# → Add to https://github.com/settings/keys
ssh -T git@github.com

# 2. Clone + deploy (installs everything)
cd /workspace
git clone git@github.com:nyculescu/phd_speed_harmo_v5.git
cd phd_speed_harmo_v5
bash deploy_remote.sh

# 3. Train (in tmux)
source .venv/bin/activate
export SUMO_HOME="/usr/share/sumo"
tmux new -s v5train
bash launch_training.sh remote
# Ctrl+B, D to detach

# 4. Monitor
tail -f training.log
tensorboard --logdir training_runs/ --bind_all --port 6006
```

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `python3.12: command not found` | The deploy script handles this — run `bash deploy_remote.sh` |
| `SUMO_HOME environment variable not set` | `export SUMO_HOME="/usr/share/sumo"` before running |
| `No module named 'sb3_contrib'` | Run `source .venv/bin/activate` first |
| Smoke test fails at "SubprocVecEnv" | Check if SUMO is installed: `sumo --version` |
| `OSError: [Errno 28] No space left on device` | PyTorch + CUDA need ~5 GB — free space or use `--no-cache-dir` in pip |
| `Could not connect` SUMO errors | Reduce `--n-envs` (too many SUMO processes for available ports) |
| Training seems stuck | Check per-seed logs: `tail training_runs/experiment_*/*.log` |
| `source ~/.bashrc` doesn't load SUMO_HOME | vast.ai tmux sessions may skip `.bashrc` — use `export` directly |
