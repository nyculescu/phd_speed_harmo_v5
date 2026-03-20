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

# Activate venv if it exists (remote deploy creates .venv/)
if [ -f ".venv/bin/activate" ]; then
    source .venv/bin/activate
    echo "Activated venv: $(which python3)"
fi

# Ensure SUMO_HOME is set
export SUMO_HOME="${SUMO_HOME:-/usr/share/sumo}"
export PATH="$SUMO_HOME/bin:$PATH"

# Quick sanity check
python3 -c "import torch; import stable_baselines3; import sb3_contrib" 2>/dev/null || {
    echo "ERROR: Missing Python packages. Run: source .venv/bin/activate && pip install -r requirements.txt"
    exit 1
}

MODE="${1:-test}"

case "$MODE" in
  remote)
    # 128 cores, 504 GB RAM
    # SUMO workers use ~50% core each (idle between traci calls),
    # so 48 workers/seed × 5 seeds = 240 processes ≈ 120 effective cores
    N_ENVS=48
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
# --- Progress monitor function ---
monitor_progress() {
  local EXP_NAME="$1"
  local LOG_PREFIX="$2"

  echo "  Monitoring ${EXP_NAME}..."
  while true; do
    # Check if any background job is still running
    if ! jobs -r | grep -q .; then
      break
    fi

    # Collect progress from all seed logs
    local ALL_DONE=true
    local LINE=""
    for SEED in ${SEEDS}; do
      local LOG="${LOG_BASE}/${LOG_PREFIX}_seed${SEED}.log"
      if [ ! -f "$LOG" ]; then
        continue
      fi
      local STEPS=$(grep -oP 'total_timesteps\s*\|\s*\K[0-9]+' "$LOG" 2>/dev/null | tail -1)
      local FPS=$(grep -oP 'fps\s*\|\s*\K[0-9]+' "$LOG" 2>/dev/null | tail -1)
      STEPS=${STEPS:-0}
      FPS=${FPS:-0}
      if [ "$STEPS" -lt "$TIMESTEPS" ] 2>/dev/null; then
        ALL_DONE=false
      fi
      local PCT=$((STEPS * 100 / TIMESTEPS))
      local BAR_FULL=$((PCT * 20 / 100))
      local BAR_EMPTY=$((20 - BAR_FULL))
      local BAR=$(printf '█%.0s' $(seq 1 $BAR_FULL 2>/dev/null) 2>/dev/null)$(printf '░%.0s' $(seq 1 $BAR_EMPTY 2>/dev/null) 2>/dev/null)
      LINE="${LINE}  s${SEED}:|${BAR}|${PCT}%@${FPS}fps"
    done

    if [ -n "$LINE" ]; then
      printf "\r  ${EXP_NAME}${LINE}    "
    fi

    if $ALL_DONE; then
      break
    fi
    sleep 30
  done
  echo ""
}

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
  sleep 5
done
monitor_progress "SAC Box(4)" "sac_box4"
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
monitor_progress "TQC Box(4)" "tqc_box4"
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
monitor_progress "TQC Box(5)" "tqc_box5"
wait
echo "  TQC Box(5) complete at $(date)"
echo ""

echo "=== ALL EXPERIMENTS COMPLETE ==="
echo "Results in: ${LOG_BASE}"
echo "View with: tensorboard --logdir ${LOG_BASE}"
echo "Finished at $(date)"
