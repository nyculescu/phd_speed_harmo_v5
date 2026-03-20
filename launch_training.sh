#!/usr/bin/env bash
# launch_training.sh — Run full experimental suite.
#
# Usage:
#   ./launch_training.sh remote   # 128+ cores
#   ./launch_training.sh local    # 30 cores
#   ./launch_training.sh test     # quick sanity (1 seed, 50k steps)

set -euo pipefail
cd "$(dirname "$0")"

# ── Python setup ─────────────────────────────────────────────────────────────
if [ -f ".venv/bin/python3" ]; then
    PY="$(pwd)/.venv/bin/python3"
else
    PY="python3"
fi
export SUMO_HOME="${SUMO_HOME:-/usr/share/sumo}"
export PATH="$SUMO_HOME/bin:$PATH"

# Prevent OpenBLAS/libgomp from spawning 64 threads per process.
# With 240 SUMO workers, 64 threads each = 15k threads → fork bomb.
# Our MLP is tiny — 1 thread per process is sufficient.
export OPENBLAS_NUM_THREADS=1
export OMP_NUM_THREADS=1
export MKL_NUM_THREADS=1

echo "Python: $($PY --version) at $PY"

$PY -c "import torch; import stable_baselines3; import sb3_contrib; import traci" 2>/dev/null || {
    echo "ERROR: Missing packages. Run: ./deploy_remote.sh"
    exit 1
}

# ── Mode selection ───────────────────────────────────────────────────────────
MODE="${1:-test}"

case "$MODE" in
  remote)
    N_ENVS=48; SEEDS="0 1 2 3 4"; TIMESTEPS=1000000
    echo "=== REMOTE: 5 seeds × ${N_ENVS} workers = $((5 * N_ENVS)) SUMO ==="
    ;;
  local)
    N_ENVS=8; SEEDS="0 1 2 3 4"; TIMESTEPS=1000000
    echo "=== LOCAL: 5 seeds × ${N_ENVS} workers = $((5 * N_ENVS)) SUMO ==="
    ;;
  test)
    N_ENVS=2; SEEDS="0"; TIMESTEPS=50000
    echo "=== TEST: 1 seed × ${N_ENVS} workers ==="
    ;;
  *)
    echo "Usage: $0 {remote|local|test}"; exit 1 ;;
esac

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
LOG_BASE="training_runs/experiment_${TIMESTAMP}"
mkdir -p "${LOG_BASE}"
echo "Output: ${LOG_BASE}"
echo "Started: $(date)"
echo ""

# ── Progress monitor ─────────────────────────────────────────────────────────
monitor_progress() {
    local EXP_NAME="$1"
    local LOG_PREFIX="$2"

    while jobs -r | grep -q .; do
        local LINE=""
        for SEED in ${SEEDS}; do
            local LOG="${LOG_BASE}/${LOG_PREFIX}_seed${SEED}.log"
            local STEPS=0 FPS=0
            if [ -f "$LOG" ]; then
                STEPS=$(grep -oP 'total_timesteps\s*\|\s*\K[0-9]+' "$LOG" 2>/dev/null | tail -1 || echo 0)
                FPS=$(grep -oP 'fps\s*\|\s*\K[0-9]+' "$LOG" 2>/dev/null | tail -1 || echo 0)
                STEPS=${STEPS:-0}
                FPS=${FPS:-0}
            fi
            local PCT=$((STEPS * 100 / TIMESTEPS))
            LINE="${LINE} s${SEED}:${PCT}%%@${FPS}fps"
        done
        # Use echo -ne for safe in-place update (no printf % issues)
        echo -ne "\r  ${EXP_NAME} |${LINE} |   "
        sleep 5
    done
    echo ""
}

# ── Run one experiment ───────────────────────────────────────────────────────
run_experiment() {
    local EXP_NAME="$1"
    local ALGO="$2"
    local LOG_PREFIX="$3"
    shift 3
    local EXTRA_ARGS="$*"

    echo ">>> ${EXP_NAME} — seeds [${SEEDS}] × ${N_ENVS} workers"

    for SEED in ${SEEDS}; do
        local LOG_DIR="${LOG_BASE}/${LOG_PREFIX%%_seed*}"
        [ -n "${LOG_PREFIX}" ] && LOG_DIR="${LOG_BASE}/${ALGO}_$(echo $EXTRA_ARGS | tr ' ' '_' | tr -d '-')"
        LOG_DIR="${LOG_BASE}/${LOG_PREFIX}"
        echo "  Starting ${ALGO} seed=${SEED}..."
        $PY train.py \
            --algo ${ALGO} \
            --seeds ${SEED} \
            --n-envs ${N_ENVS} \
            --timesteps ${TIMESTEPS} \
            --log-dir "${LOG_DIR}" \
            ${EXTRA_ARGS} \
            > "${LOG_BASE}/${LOG_PREFIX}_seed${SEED}.log" 2>&1 &
        sleep 5
    done

    monitor_progress "${EXP_NAME}" "${LOG_PREFIX}"
    wait
    echo "  ${EXP_NAME} complete at $(date)"
    echo ""
}

# ── Experiments ──────────────────────────────────────────────────────────────
run_experiment "Exp 1: SAC Box(4)"  sac  sac_box4  ""
run_experiment "Exp 2: TQC Box(4)"  tqc  tqc_box4  ""
run_experiment "Exp 3: TQC Box(5)"  tqc  tqc_box5  "--box5"

echo "=== ALL EXPERIMENTS COMPLETE ==="
echo "Results: ${LOG_BASE}"
echo "TensorBoard: tensorboard --logdir ${LOG_BASE} --bind_all"
echo "Finished: $(date)"
