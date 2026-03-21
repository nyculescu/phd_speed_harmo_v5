#!/usr/bin/env bash
# launch_evaluation.sh — Run ground-truth evaluation of trained models.
#
# Usage:
#   ./launch_evaluation.sh --experiment training_runs/experiment_20260320_201005
#   ./launch_evaluation.sh --experiment training_runs/experiment_20260320_201005 --episodes 50
#   ./launch_evaluation.sh --experiment training_runs/experiment_20260320_201005 --best_seed_only

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
export OPENBLAS_NUM_THREADS=1
export OMP_NUM_THREADS=1
export MKL_NUM_THREADS=1

echo "Python: $($PY --version) at $PY"

# ── Argument parsing ─────────────────────────────────────────────────────────
EXPERIMENT=""
EPISODES=30
BEST_SEED_ONLY=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --experiment)
            if [[ $# -lt 2 ]]; then echo "ERROR: --experiment requires a path"; exit 1; fi
            EXPERIMENT="$2"; shift 2 ;;
        --episodes)
            if [[ $# -lt 2 ]]; then echo "ERROR: --episodes requires a number"; exit 1; fi
            EPISODES="$2"; shift 2 ;;
        --best_seed_only)
            BEST_SEED_ONLY="--best-seed-only"; shift ;;
        *)
            echo "Unknown argument: $1"
            echo "Usage: $0 --experiment <path> [--episodes N] [--best_seed_only]"
            exit 1 ;;
    esac
done

if [ -z "$EXPERIMENT" ]; then
    echo "ERROR: --experiment is required"
    echo "Usage: $0 --experiment training_runs/experiment_20260320_201005 [--episodes 30] [--best_seed_only]"
    exit 1
fi

if [ ! -d "$EXPERIMENT" ]; then
    echo "ERROR: experiment directory not found: $EXPERIMENT"
    exit 1
fi

# ── Run evaluation ───────────────────────────────────────────────────────────
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
LOG_FILE="${EXPERIMENT}/evaluation_${TIMESTAMP}.log"

echo "=== Ground-truth evaluation ==="
echo "  Experiment: $EXPERIMENT"
echo "  Episodes:   $EPISODES"
echo "  Best seed:  ${BEST_SEED_ONLY:-all seeds}"
echo "  Log:        $LOG_FILE"
echo "  Started:    $(date)"
echo ""

$PY evaluate_models.py \
    --experiment "$EXPERIMENT" \
    --episodes "$EPISODES" \
    $BEST_SEED_ONLY \
    2>&1 | tee "$LOG_FILE"

echo ""
echo "=== Evaluation complete ==="
echo "  Log: $LOG_FILE"
echo "  Finished: $(date)"
