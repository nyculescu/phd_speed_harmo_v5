#!/usr/bin/env bash
# launch_training.sh — Run full experimental suite on remote machine.
#
# Usage:
#   # Remote machine (128 cores, 1 TB RAM):
#   bash launch_training.sh remote
#
#   # Local machine (30 cores, 64 GB RAM):
#   bash launch_training.sh local
#
#   # Single quick test (1 seed, 50k steps):
#   bash launch_training.sh test
#
# Prerequisites:
#   - SUMO >= 1.20 installed, SUMO_HOME set
#   - pip install -r requirements.txt
#   - tmux installed (for parallel seed execution)

set -euo pipefail
cd "$(dirname "$0")"

MODE="${1:-test}"

case "$MODE" in
  remote)
    # 128 cores, 1 TB RAM
    # 5 seeds × 24 workers = 120 SUMO processes
    N_ENVS=24
    SEEDS="0 1 2 3 4"
    TIMESTEPS=1000000
    echo "=== REMOTE MODE: 5 seeds × ${N_ENVS} workers = $((5 * N_ENVS)) SUMO processes ==="
    ;;
  local)
    # 30 cores, 64 GB RAM
    # 5 seeds × 5 workers = 25 SUMO processes
    N_ENVS=5
    SEEDS="0 1 2 3 4"
    TIMESTEPS=1000000
    echo "=== LOCAL MODE: 5 seeds × ${N_ENVS} workers = $((5 * N_ENVS)) SUMO processes ==="
    ;;
  test)
    N_ENVS=2
    SEEDS="0"
    TIMESTEPS=50000
    echo "=== TEST MODE: 1 seed × ${N_ENVS} workers ==="
    ;;
  *)
    echo "Usage: $0 {remote|local|test}"
    exit 1
    ;;
esac

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
LOG_BASE="training_runs/experiment_${TIMESTAMP}"
mkdir -p "${LOG_BASE}"

echo "Output: ${LOG_BASE}"
echo "Starting at $(date)"
echo ""

# --- Experiment 1: SAC Box(4) ---
echo ">>> Experiment 1: SAC Box(4) — ${SEEDS} seeds × ${N_ENVS} workers"
for SEED in ${SEEDS}; do
  LOG_DIR="${LOG_BASE}/sac_box4"
  echo "  Starting SAC seed=${SEED}..."
  python3 train.py \
    --algo sac \
    --seeds ${SEED} \
    --n-envs ${N_ENVS} \
    --timesteps ${TIMESTEPS} \
    --log-dir "${LOG_DIR}" \
    > "${LOG_BASE}/sac_box4_seed${SEED}.log" 2>&1 &
  # Small delay between seed launches to stagger SubprocVecEnv startup
  sleep 5
done
echo "  Waiting for all SAC Box(4) seeds..."
wait
echo "  SAC Box(4) complete at $(date)"
echo ""

# --- Experiment 2: TQC Box(4) ---
echo ">>> Experiment 2: TQC Box(4) — ${SEEDS} seeds × ${N_ENVS} workers"
for SEED in ${SEEDS}; do
  LOG_DIR="${LOG_BASE}/tqc_box4"
  echo "  Starting TQC seed=${SEED}..."
  python3 train.py \
    --algo tqc \
    --seeds ${SEED} \
    --n-envs ${N_ENVS} \
    --timesteps ${TIMESTEPS} \
    --log-dir "${LOG_DIR}" \
    > "${LOG_BASE}/tqc_box4_seed${SEED}.log" 2>&1 &
  sleep 5
done
echo "  Waiting for all TQC Box(4) seeds..."
wait
echo "  TQC Box(4) complete at $(date)"
echo ""

# --- Experiment 3: TQC Box(5) ---
echo ">>> Experiment 3: TQC Box(5) — ${SEEDS} seeds × ${N_ENVS} workers"
for SEED in ${SEEDS}; do
  LOG_DIR="${LOG_BASE}/tqc_box5"
  echo "  Starting TQC Box(5) seed=${SEED}..."
  python3 train.py \
    --algo tqc \
    --box5 \
    --seeds ${SEED} \
    --n-envs ${N_ENVS} \
    --timesteps ${TIMESTEPS} \
    --log-dir "${LOG_DIR}" \
    > "${LOG_BASE}/tqc_box5_seed${SEED}.log" 2>&1 &
  sleep 5
done
echo "  Waiting for all TQC Box(5) seeds..."
wait
echo "  TQC Box(5) complete at $(date)"
echo ""

echo "=== ALL EXPERIMENTS COMPLETE ==="
echo "Results in: ${LOG_BASE}"
echo "View with: tensorboard --logdir ${LOG_BASE}"
echo "Finished at $(date)"
