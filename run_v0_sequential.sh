#!/usr/bin/env bash
# =============================================================================
# m43_v0 Sequential Training + Evaluation
# -----------------------------------------------------------------------------
# Trains QRDQN (primary), then DQN (baseline), then evaluates all controllers.
# Run from the project root:
#   bash run_v0_sequential.sh
#
# Override CAV penetration rate (default 50%):
#   CAV_PERCENT=75.0 bash run_v0_sequential.sh
# =============================================================================
set -uo pipefail

echo -e "\033]0;m43_v0 Sequential Train+Eval\007"
cd "$(dirname "$0")" || exit 1

# ── Preflight ─────────────────────────────────────────────────────────────────
if [ ! -d "core" ]; then echo "Error: core/ not found. Run from phd_speed_harmo_v5/ root."; exit 1; fi
VENV_PATH=".venv"
if [ ! -f "${VENV_PATH}/bin/activate" ]; then echo "Error: venv not found at ${VENV_PATH}."; exit 1; fi

# Prevent thread explosion with many parallel SUMO envs.
export OMP_NUM_THREADS=1
export OPENBLAS_NUM_THREADS=1
export MKL_NUM_THREADS=1
export VECLIB_MAXIMUM_THREADS=1
export NUMEXPR_NUM_THREADS=1

# shellcheck source=/dev/null
source "${VENV_PATH}/bin/activate"

PY="${VENV_PATH}/bin/python"
if [ ! -x "$PY" ]; then echo "Error: $PY not executable."; exit 1; fi

CAV_PERCENT="${CAV_PERCENT:-50.0}"
S0_BASE="configurations/m43_v0"
LOG_DIR="/tmp/m43_v0_train_logs"
mkdir -p "$LOG_DIR"

echo "=========================================="
echo " m43_v0 Sequential Train+Eval"
echo "  CAV penetration: ${CAV_PERCENT}%"
echo "  Project root:    $(pwd)"
echo "  Logs:            $LOG_DIR/"
echo "=========================================="

# ── Step 0: verify SAR components ─────────────────────────────────────────────
echo ""
echo "[$(date +%H:%M:%S)] [0/3] Verifying SAR components..."
"$PY" -c "
from sar_components.discovery import discover_components
discover_components()
from sar_components.registry import STATE_REGISTRY, ACTION_REGISTRY, REWARD_REGISTRY
assert 'm43_state_v0'  in STATE_REGISTRY,  'ERROR: m43_state_v0 not registered'
assert 'm43_action_v0' in ACTION_REGISTRY, 'ERROR: m43_action_v0 not registered'
assert 'm43_reward_v0' in REWARD_REGISTRY, 'ERROR: m43_reward_v0 not registered'
from traffic_environment.scenario_generator import _resolve_topology_files
net, det = _resolve_topology_files('merge_4_to_3_v0')
assert 'v0' in det, f'ERROR: wrong detector file: {det}'
print('All SAR components OK')
" || { echo "Component verification failed. Aborting."; exit 1; }

# ── Step 1: train QRDQN ───────────────────────────────────────────────────────
echo ""
echo "[$(date +%H:%M:%S)] [1/3] Training QRDQN (primary)..."
ALGO_START=$(date +%s)
LOG_FILE="${LOG_DIR}/qrdqn_train.log"

"$PY" -u training/drl_vsl_train.py \
    --config "${S0_BASE}/qrdqn_config.yaml" \
    --override "scenario_generation.cavs_percentage=${CAV_PERCENT}" \
    2>&1 | tee "$LOG_FILE"
RC=${PIPESTATUS[0]}

ELAPSED=$(( $(date +%s) - ALGO_START ))
if [ $RC -eq 0 ]; then
    echo "[$(date +%H:%M:%S)] QRDQN training SUCCEEDED ($(( ELAPSED/3600 ))h$(( (ELAPSED%3600)/60 ))m)"
else
    echo "[$(date +%H:%M:%S)] QRDQN training FAILED (rc=$RC). Check $LOG_FILE"; exit 1
fi

# ── Step 2: train DQN ─────────────────────────────────────────────────────────
echo ""
echo "[$(date +%H:%M:%S)] [2/3] Training DQN (comparison baseline)..."
ALGO_START=$(date +%s)
LOG_FILE="${LOG_DIR}/dqn_train.log"

"$PY" -u training/drl_vsl_train.py \
    --config "${S0_BASE}/dqn_config.yaml" \
    --override "scenario_generation.new_scenarios=false" \
    --override "scenario_generation.cavs_percentage=${CAV_PERCENT}" \
    2>&1 | tee "$LOG_FILE"
RC=${PIPESTATUS[0]}

ELAPSED=$(( $(date +%s) - ALGO_START ))
if [ $RC -eq 0 ]; then
    echo "[$(date +%H:%M:%S)] DQN training SUCCEEDED ($(( ELAPSED/3600 ))h$(( (ELAPSED%3600)/60 ))m)"
else
    echo "[$(date +%H:%M:%S)] DQN training FAILED (rc=$RC). Check $LOG_FILE"; exit 1
fi

# ── Step 3: evaluate all controllers ──────────────────────────────────────────
echo ""
echo "[$(date +%H:%M:%S)] [3/3] Evaluating all controllers..."
EVAL_START=$(date +%s)
LOG_FILE="${LOG_DIR}/evaluation.log"

EVAL_CFG="$(realpath "${S0_BASE}/_common_agents.yaml")"
TEMP_CFG=""
if [ "${CAV_PERCENT}" != "50.0" ]; then
    TEMP_CFG=$(mktemp /tmp/m43_v0_eval_override_XXXX.yaml)
    printf 'meta:\n  base_configs:\n    - %s\nscenario_generation:\n  cavs_percentage: %s\n' \
        "${EVAL_CFG}" "${CAV_PERCENT}" > "${TEMP_CFG}"
    EVAL_CFG="${TEMP_CFG}"
fi

DRL_VSL_CONFIG_PATH="${EVAL_CFG}" \
    "$PY" -u evaluation/drl_vsl_eval.py \
    2>&1 | tee "$LOG_FILE"
EVAL_RC=${PIPESTATUS[0]}
[ -n "${TEMP_CFG}" ] && rm -f "${TEMP_CFG}"

ELAPSED=$(( $(date +%s) - EVAL_START ))
if [ $EVAL_RC -eq 0 ]; then
    echo "[$(date +%H:%M:%S)] Evaluation SUCCEEDED ($(( ELAPSED/3600 ))h$(( (ELAPSED%3600)/60 ))m)"
else
    echo "[$(date +%H:%M:%S)] Evaluation FAILED (rc=$EVAL_RC). Check $LOG_FILE"
fi

echo ""
echo "=========================================="
echo " m43_v0 Pipeline Complete"
echo "=========================================="
echo "  Training logs: $LOG_DIR/"
echo "  Results:       evaluation/results/m43_v0/"
echo "  TB logs:       logs/m43_v0/"
echo "=========================================="

deactivate || true
exit $EVAL_RC
