#!/usr/bin/env bash
# check_training_status.sh — Report whether training on this VM is done.
#
# Usage (run on the VM after SSHing in):
#   cd ~/phd_speed_harmo_v5 && ./tools/check_training_status.sh
#
# Exit codes:
#   0 = training fully complete (5/5 final_model.zip present)
#   1 = still training (python processes alive)
#   2 = stopped without completing (no procs, <5 models saved)

set -u
cd "$(dirname "$0")/.."

EXP=$(ls -1td training_runs/experiment_* 2>/dev/null | head -1)
if [ -z "$EXP" ]; then
    echo "ERROR: no training_runs/experiment_* directory found"
    exit 2
fi

SAVED=$(find "$EXP" -name "final_model.zip" 2>/dev/null | wc -l)
PROCS=$(pgrep -fc "python.*train.py" || echo 0)
PID=$(pgrep -f "python.*train.py" | head -1)
ETIME=$(ps -o etime= -p "${PID:-0}" 2>/dev/null | xargs || echo "n/a")
MAX=$(grep -hoP "total_timesteps\s*\|\s*\K[0-9]+" "$EXP"/*_seed*.log 2>/dev/null | sort -n | tail -1)
MAX=${MAX:-0}
PCT=$(echo "scale=1; $MAX * 100 / 1000000" | bc -l 2>/dev/null || echo "0")

printf "exp:           %s\n" "$(basename "$EXP")"
printf "final_models:  %d/5\n" "$SAVED"
printf "procs alive:   %d\n" "$PROCS"
printf "etime:         %s\n" "$ETIME"
printf "max_step:      %d/1000000 (%s%%)\n" "$MAX" "$PCT"

if [ "$SAVED" -eq 5 ]; then
    echo "STATUS: ✓ DONE — safe to stop the VM"
    exit 0
elif [ "$PROCS" -eq 0 ]; then
    echo "STATUS: ⚠ STOPPED (incomplete — only $SAVED/5 models saved)"
    exit 2
else
    echo "STATUS: ⏳ TRAINING"
    exit 1
fi
