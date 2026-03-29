#!/usr/bin/env bash
# deploy_4vm.sh — Deploy one experiment per VM (4 VMs total).
#
# Usage:
#   ./deploy_4vm.sh vm1-host vm2-host vm3-host vm4-host
#   ./deploy_4vm.sh user@10.0.0.1 user@10.0.0.2 user@10.0.0.3 user@10.0.0.4
#
# Each VM runs one Box variant:
#   VM1: SAC Box(4)    VM2: TQC Box(4)    VM3: SAC Box(5)    VM4: TQC Box(5)
#
# Prerequisites on each VM:
#   - git clone <repo> ~/phd_speed_harmo_v5
#   - pip install -r requirements.txt
#   - SUMO installed (apt install sumo sumo-tools)
#
# The script:
#   1. Pushes latest code to all 4 VMs (git pull)
#   2. Generates identical scenario pools on each VM (same --seed)
#   3. Launches training in tmux sessions (detached, survives SSH disconnect)
#   4. Shows how to monitor progress

set -euo pipefail

if [ $# -ne 4 ]; then
    echo "Usage: $0 <vm1-host> <vm2-host> <vm3-host> <vm4-host>"
    echo "  Each host is an SSH target, e.g. user@10.0.0.1"
    exit 1
fi

VM1="$1"  # SAC Box(4)
VM2="$2"  # TQC Box(4)
VM3="$3"  # SAC Box(5)
VM4="$4"  # TQC Box(5)

REPO_DIR="phd_speed_harmo_v5"
POOL_DIR="scenario_pools/shared"
POOL_SEED=42
POOL_N=200

declare -A ALGO_MAP
ALGO_MAP[$VM1]="sac_4"
ALGO_MAP[$VM2]="tqc_4"
ALGO_MAP[$VM3]="sac_5"
ALGO_MAP[$VM4]="tqc_5"

echo "=== 4-VM Deployment ==="
echo "  VM1 ($VM1): SAC Box(4)"
echo "  VM2 ($VM2): TQC Box(4)"
echo "  VM3 ($VM3): SAC Box(5)"
echo "  VM4 ($VM4): TQC Box(5)"
echo ""

# Step 1: Update code on all VMs
echo ">>> Step 1: Pulling latest code on all VMs..."
for VM in "$VM1" "$VM2" "$VM3" "$VM4"; do
    echo "  $VM..."
    ssh "$VM" "cd ~/${REPO_DIR} && git pull --ff-only" &
done
wait
echo "  Done."
echo ""

# Step 2: Generate identical scenario pools
echo ">>> Step 2: Generating scenario pools (seed=${POOL_SEED}, n=${POOL_N})..."
for VM in "$VM1" "$VM2" "$VM3" "$VM4"; do
    echo "  $VM..."
    ssh "$VM" "cd ~/${REPO_DIR} && python3 generate_scenarios.py focused \
        --n ${POOL_N} --band 5500 7250 --noise 200 --seed ${POOL_SEED} \
        --weather 'clear:0.7,rain:0.2,fog:0.1' \
        -o ${POOL_DIR}" &
done
wait
echo "  Done."
echo ""

# Step 3: Launch training in tmux (survives SSH disconnect)
echo ">>> Step 3: Launching training..."
for VM in "$VM1" "$VM2" "$VM3" "$VM4"; do
    ALGO="${ALGO_MAP[$VM]}"
    echo "  $VM → ${ALGO}..."
    ssh "$VM" "cd ~/${REPO_DIR} && \
        tmux new-session -d -s train_${ALGO} \
        './launch_training.sh --machine remote --single_algo ${ALGO} --pool ${POOL_DIR}'"
done
echo "  All 4 experiments launched."
echo ""

# Step 4: Monitoring instructions
echo "=== MONITORING ==="
echo ""
echo "Attach to a running experiment:"
for VM in "$VM1" "$VM2" "$VM3" "$VM4"; do
    ALGO="${ALGO_MAP[$VM]}"
    echo "  ssh ${VM} -t 'tmux attach -t train_${ALGO}'"
done
echo ""
echo "Quick status check (all VMs):"
echo "  for VM in ${VM1} ${VM2} ${VM3} ${VM4}; do"
echo "    echo \"=== \$VM ===\""
echo "    ssh \$VM 'tail -5 ~/${REPO_DIR}/training_runs/experiment_*/sac_box*_seed0.log ~/${REPO_DIR}/training_runs/experiment_*/tqc_box*_seed0.log 2>/dev/null | tail -10'"
echo "  done"
echo ""
echo "Collect results when done:"
echo "  mkdir -p results_4vm"
echo "  for VM in ${VM1} ${VM2} ${VM3} ${VM4}; do"
echo "    scp -r \${VM}:~/${REPO_DIR}/training_runs/experiment_* results_4vm/"
echo "  done"
