#!/usr/bin/env bash
# launch_training.sh — Run full experimental suite.
#
# Usage:
#   ./launch_training.sh --machine remote                        # all algorithms, 128+ cores
#   ./launch_training.sh --machine remote --single_algo sac_5    # SAC Box(5) only
#   ./launch_training.sh --machine local                         # all algorithms, 30 cores
#   ./launch_training.sh --machine test                          # quick sanity (1 seed, 50k steps)
#
# Available --single_algo values:
#   sac_4   — SAC Box(4)
#   sac_5   — SAC Box(5)
#   tqc_4   — TQC Box(4)
#   tqc_5   — TQC Box(5)

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

# ── Argument parsing ─────────────────────────────────────────────────────────
MODE=""
SINGLE_ALGO=""
POOL_OVERRIDE=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --machine)
            if [[ $# -lt 2 ]]; then
                echo "ERROR: --machine requires a value (remote, local, test)"
                exit 1
            fi
            MODE="$2"; shift 2 ;;
        --single_algo)
            if [[ $# -lt 2 ]]; then
                echo "ERROR: --single_algo requires a value (sac_4, sac_5, tqc_4, tqc_5)"
                exit 1
            fi
            SINGLE_ALGO="$2"; shift 2 ;;
        --pool)
            if [[ $# -lt 2 ]]; then
                echo "ERROR: --pool requires a path to an existing scenario pool directory"
                exit 1
            fi
            POOL_OVERRIDE="$2"; shift 2 ;;
        *)
            echo "Unknown argument: $1"
            echo "Usage: $0 --machine {remote|local|test} [--single_algo ...] [--pool <dir>]"
            exit 1 ;;
    esac
done

MODE="${MODE:-test}"

case "$MODE" in
  remote)
    N_ENVS=48; SEEDS="0 1 2 3 4"; TIMESTEPS=1000000
    echo "=== REMOTE VM: 5 seeds × ${N_ENVS} workers ==="
    echo "  ⚠  VM will shut down automatically when training completes (or fails)."
    ;;
  local)
    N_ENVS=8; SEEDS="0 1 2 3 4"; TIMESTEPS=1000000
    echo "=== LOCAL: 5 seeds × ${N_ENVS} workers ==="
    ;;
  test)
    N_ENVS=2; SEEDS="0"; TIMESTEPS=50000
    echo "=== TEST: 1 seed × ${N_ENVS} workers ==="
    ;;
esac

# ── Auto-shutdown for remote VMs ─────────────────────────────────────────────
# When --machine remote, the VM shuts down after training to avoid idle costs.
# The trap fires on EXIT (covers success, failure, and signals).
# A 2-minute grace period allows log sync and any post-training hooks.
if [ "$MODE" = "remote" ]; then
    _shutdown_vm() {
        local EXIT_CODE=$?
        echo ""
        echo "========================================"
        if [ $EXIT_CODE -eq 0 ]; then
            echo "Training completed successfully."
        else
            echo "Training exited with code $EXIT_CODE."
        fi
        echo "Shutting down VM in 120 seconds..."
        echo "  (Ctrl+C within 120s to cancel shutdown)"
        echo "  Finished: $(date)"
        echo "========================================"
        # sync logs to disk before shutdown
        sync

        # Pick the shutdown method that works on THIS host:
        #   1. vastai CLI + VAST_CONTAINERLABEL → vast.ai container (preferred)
        #   2. passwordless sudo → traditional VM with init/systemd
        #   3. neither → leave the box up, warn the user
        # vast.ai containers don't honor `sudo shutdown` (no systemd), so we
        # must call the vast.ai API from inside the container instead.
        if command -v vastai >/dev/null 2>&1 && [ -n "${VAST_CONTAINERLABEL:-}" ]; then
            INSTANCE_ID="${VAST_CONTAINERLABEL#C.}"
            echo "Stopping vast.ai instance ${INSTANCE_ID} via vastai CLI in 30s..."
            sleep 30  # last-chance sync window
            vastai stop instance "$INSTANCE_ID" 2>&1 \
                || echo "WARNING: 'vastai stop instance ${INSTANCE_ID}' failed — stop manually via dashboard."
        elif sudo -n true 2>/dev/null; then
            sudo shutdown +2 "Training script finished (exit=$EXIT_CODE). Auto-shutdown." 2>/dev/null \
                || echo "WARNING: 'sudo shutdown' failed. VM will NOT auto-shutdown."
        else
            echo "WARNING: no shutdown method available (no vastai CLI + VAST_CONTAINERLABEL,"
            echo "         and no passwordless sudo). Stop the VM manually via the cloud dashboard."
        fi
    }
    trap _shutdown_vm EXIT
fi

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
LOG_BASE="training_runs/experiment_${TIMESTAMP}"
mkdir -p "${LOG_BASE}"
echo "Output: ${LOG_BASE}"
echo "Started: $(date)"
if [ -n "${SINGLE_ALGO}" ]; then
    echo "Single algorithm: ${SINGLE_ALGO}"
fi
echo ""

# ── Pre-generate scenario pool (or use existing via --pool) ─────────────────
if [ -n "${POOL_OVERRIDE}" ]; then
    POOL_DIR="${POOL_OVERRIDE}"
    if [ ! -d "${POOL_DIR}" ]; then
        echo "ERROR: Pool directory does not exist: ${POOL_DIR}"
        exit 1
    fi
    echo ">>> Using existing scenario pool: ${POOL_DIR}"
    echo "  Pool: ${POOL_DIR} ($(ls ${POOL_DIR}/*.sumocfg 2>/dev/null | wc -l) scenarios)"
else
    POOL_DIR="scenario_pools/focused_${TIMESTAMP}"
    N_SCENARIOS=200
    echo ">>> Generating ${N_SCENARIOS} scenarios (focused band 5500-7250 vph)..."
    $PY generate_scenarios.py focused \
        --n ${N_SCENARIOS} \
        --band 5500 7250 \
        --noise 200 \
        --cav 50.0 \
        --weather "clear:0.7,rain:0.2,fog:0.1" \
        -o "${POOL_DIR}" 2>&1 | tail -3
    echo "  Pool: ${POOL_DIR} ($(ls ${POOL_DIR}/*.sumocfg 2>/dev/null | wc -l) scenarios)"
fi
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
        LOG_DIR="${LOG_BASE}/${LOG_PREFIX}"
        echo "  Starting ${ALGO} seed=${SEED}..."
        $PY train.py \
            --algo ${ALGO} \
            --seeds ${SEED} \
            --n-envs ${N_ENVS} \
            --timesteps ${TIMESTEPS} \
            --log-dir "${LOG_DIR}" \
            --scenario-pool "${POOL_DIR}" \
            ${EXTRA_ARGS} \
            > "${LOG_BASE}/${LOG_PREFIX}_seed${SEED}.log" 2>&1 &
        sleep 5
    done

    monitor_progress "${EXP_NAME}" "${LOG_PREFIX}"
    wait
    echo "  ${EXP_NAME} complete at $(date)"
    echo ""
}

# ── Determine which experiments to run ───────────────────────────────────────
should_run() {
    local ALGO_KEY="$1"
    if [ -z "${SINGLE_ALGO}" ]; then
        return 0  # no filter → run all
    fi
    if [ "${SINGLE_ALGO}" = "${ALGO_KEY}" ]; then
        return 0  # matches filter
    fi
    return 1  # skip
}

# ── Experiments ──────────────────────────────────────────────────────────────
if should_run "sac_4"; then
    run_experiment "Exp: SAC Box(4)"  sac  sac_box4  ""
fi

if should_run "tqc_4"; then
    run_experiment "Exp: TQC Box(4)"  tqc  tqc_box4  ""
fi

if should_run "sac_5"; then
    run_experiment "Exp: SAC Box(5)"  sac  sac_box5  "--box5"
fi

if should_run "tqc_5"; then
    run_experiment "Exp: TQC Box(5)"  tqc  tqc_box5  "--box5"
fi

echo "=== ALL EXPERIMENTS COMPLETE ==="
echo "Results: ${LOG_BASE}"
echo "TensorBoard: tensorboard --logdir ${LOG_BASE} --bind_all"
echo "Finished: $(date)"
