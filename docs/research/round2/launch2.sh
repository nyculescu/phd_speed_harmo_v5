#!/bin/bash
# Start round 2's chain from the frozen run copy, with its guard, night timers and health log. usage: launch2.sh RUN_SHA7
D=/home/catalin/work/phd/v5b1_runs/round2; C=$D/code_$1; R=$C/docs/research/round2
[ -f "$C/COMMIT" ] || { echo "no frozen copy $C" >&2; exit 1; }
systemd-run --user --unit r2-chain --collect --working-directory="$C" /bin/bash "$R/chain2.sh" "$C" "$D"
sleep 2
h=$(date +%H); if [ "$h" -ge 23 ] || [ "$h" -lt 9 ]; then bash "$R/pace2.sh" night; else bash "$R/pace2.sh" day; fi
systemd-run --user --unit r2-pace-night --on-calendar='*-*-* 23:00:00' --collect /bin/bash "$R/pace2.sh" night
systemd-run --user --unit r2-pace-day --on-calendar='*-*-* 09:00:00' --collect /bin/bash "$R/pace2.sh" day
systemd-run --user --unit r2-health --collect /bin/bash "$R/health2.sh" "$D"
