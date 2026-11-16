#!/bin/bash
# Night and day pace for round 1 (author, V432): from 23:00 to 09:00 the CPU stays at or below 40 %. usage: pace.sh night|day
# Restarts only the guard, with the new limit; the chain keeps running. THROTTLED tells the health monitor that paused workers are expected.
B=/home/catalin/work/phd/v5b1_runs/round1; D=$B/out; C=$B/code_$(grep -a " code " $D/status.txt | tail -1 | awk '{print $4}')     # the copy the chain runs from
PY=/home/catalin/work/phd/phd_speed_harmo_v5b1_toolchain/venv/bin/python
systemctl --user is-active -q r1-chain || exit 0
case "$1" in
  night) lim=0.40; touch "$D/THROTTLED" ;;
  day) lim=1.0; rm -f "$D/THROTTLED" ;;
  *) echo "usage: pace.sh night|day" >&2; exit 1 ;;
esac
systemctl --user stop r1-guard
for _ in 1 2 3 4 5 6; do systemctl --user is-active -q r1-guard || break; sleep 5; done
systemd-run --user --unit r1-guard --collect --working-directory="$C" /bin/bash -c "PYTHONPATH=$C $PY -m v5b.ops.watch --pattern '^/home/catalin/work/phd/phd_speed_harmo_v5b1_toolchain/venv/bin/python -c from multiprocessing.spawn' --unit r1-chain --cpu-limit $lim >> $D/guard_pace.log 2>&1"
echo "$(date '+%F %T') pace $1: guard limit $lim" >> "$D/status_pace.txt"
