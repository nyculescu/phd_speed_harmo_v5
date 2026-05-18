#!/usr/bin/env bash
# deploy_4vm.sh — Run ON each VM with an integer 1-4 selecting the experiment.
#
# Usage (after deploy_remote.sh has bootstrapped this VM):
#   ./deploy_4vm.sh <N> [--config <yaml-path>]
#     1 → SAC Box(4)    2 → TQC Box(4)    3 → SAC Box(5)    4 → TQC Box(5)
#
# The optional --config flag selects a YAML other than the default
# configurations/per_lane_stochastic.yaml. Use it for reward-weight
# ablations, e.g.:
#   ./deploy_4vm.sh 2 --config configurations/per_lane_stochastic_harmo_pure.yaml
# The config path may be absolute, project-relative, or just the basename
# (resolved against configurations/).
#
# Generates a deterministic shared scenario pool (seed=42, cav=100%) so all
# VMs train on identical demand distributions — fair cross-algorithm and
# cross-ablation comparison.
#
# Run inside tmux so SSH drops don't kill the trainer or block auto-shutdown:
#   tmux new -s v5
#   ./deploy_4vm.sh 2
#   # Ctrl-B, D to detach; tmux attach -t v5 to reattach

set -euo pipefail
cd "$(dirname "$0")"

if [ $# -lt 1 ]; then
    echo "Usage: $0 <1|2|3|4> [--config <yaml-path>]"
    echo "  1 → SAC Box(4)    2 → TQC Box(4)    3 → SAC Box(5)    4 → TQC Box(5)"
    exit 1
fi

SLOT="$1"
shift

CONFIG_PATH=""
while [[ $# -gt 0 ]]; do
    case "$1" in
        --config)
            if [[ $# -lt 2 ]]; then
                echo "ERROR: --config requires a path"
                exit 1
            fi
            CONFIG_PATH="$2"; shift 2 ;;
        *)
            echo "Unknown argument: $1"
            echo "Usage: $0 <1|2|3|4> [--config <yaml-path>]"
            exit 1 ;;
    esac
done

case "$SLOT" in
  1) ALGO="sac_4"; LABEL="SAC Box(4)" ;;
  2) ALGO="tqc_4"; LABEL="TQC Box(4)" ;;
  3) ALGO="sac_5"; LABEL="SAC Box(5)" ;;
  4) ALGO="tqc_5"; LABEL="TQC Box(5)" ;;
  *) echo "ERROR: slot must be 1, 2, 3, or 4 (got: $SLOT)"; exit 1 ;;
esac

# Pre-flight: refuse to run if the VM hasn't been bootstrapped.
[ -x .venv/bin/python3 ] || { echo "ERROR: .venv missing — run deploy_remote.sh first."; exit 1; }
[ -x launch_training.sh ] || { echo "ERROR: launch_training.sh missing or not executable."; exit 1; }
command -v sumo >/dev/null || { echo "ERROR: SUMO not on PATH (check SUMO_HOME / deploy_remote.sh)."; exit 1; }

# Pre-flight: if a custom config was passed, verify it exists.
if [ -n "${CONFIG_PATH}" ]; then
    if [ ! -f "${CONFIG_PATH}" ] && [ ! -f "configurations/${CONFIG_PATH}" ] && [ ! -f "configurations/$(basename ${CONFIG_PATH})" ]; then
        echo "ERROR: --config file not found at any of: ${CONFIG_PATH} | configurations/${CONFIG_PATH} | configurations/$(basename ${CONFIG_PATH})"
        exit 1
    fi
    CFG_LABEL=" + config=$(basename ${CONFIG_PATH%.yaml})"
else
    CFG_LABEL=""
fi

POOL_SEED=42
POOL_N=200
POOL_CAV=100   # ADR-008: paper headline experiment uses 100% CAV. Must match
               # configurations/per_lane_stochastic.yaml::cav_percentage.
POOL_DIR="scenario_pools/shared_seed${POOL_SEED}_n${POOL_N}_cav${POOL_CAV}"

if [ ! -d "${POOL_DIR}" ] || [ "$(ls -1 ${POOL_DIR}/*.sumocfg 2>/dev/null | wc -l)" -lt "${POOL_N}" ]; then
    echo ">>> Generating shared pool (seed=${POOL_SEED}, n=${POOL_N}, cav=${POOL_CAV}%)..."
    .venv/bin/python3 generate_scenarios.py focused \
        --n ${POOL_N} --band 5500 7250 --noise 200 --seed ${POOL_SEED} \
        --cav ${POOL_CAV} \
        --weather 'clear:0.7,rain:0.2,fog:0.1' \
        -o "${POOL_DIR}"
else
    echo ">>> Reusing existing pool: ${POOL_DIR} ($(ls -1 ${POOL_DIR}/*.sumocfg | wc -l) scenarios)"
fi

echo ""
echo "=========================================="
echo "  This VM → ${LABEL} (${ALGO})${CFG_LABEL}"
echo "  Auto-shutdown ON. VM dies ~2 min after training finishes."
echo "  Started: $(date)"
echo "=========================================="
echo ""

# Build the launch_training.sh command. --config is appended only if set so
# the default path (no --config) is byte-identical to the pre-refactor flow.
LAUNCH_ARGS=(--machine remote --single_algo "${ALGO}" --pool "${POOL_DIR}")
if [ -n "${CONFIG_PATH}" ]; then
    LAUNCH_ARGS+=(--config "${CONFIG_PATH}")
fi

exec ./launch_training.sh "${LAUNCH_ARGS[@]}"
