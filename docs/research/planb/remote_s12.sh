#!/bin/bash
# Runs on the rented machine (V483): Plan B S1, then S2 (planb.md §7.2-§7.3). S2 starts only if S1 passes. S2 runs its rows, the
# G4(iv) traces and the read; a cell left "G2 pending" gets the carried-rule fallback (§7.3) and a second read. A broken null (read
# exit 3) stops the stage. Progress in planb/status.txt; nothing is printed that reads performance.
# usage: remote_s12.sh WORKERS
set -u
W=${1:?WORKERS}
P=/home/catalin/work/phd
R=$P/v5b1_runs/planb
PY=$P/phd_speed_harmo_v5b1_toolchain/venv/bin/python
BASE=$P/code/79b889b
mkdir -p "$R"
unset SUMO_HOME
export OMP_NUM_THREADS=1
say() { echo "$(date -u '+%F %T') $1" >> "$R/status.txt"; }
step() { say "start $1"; shift; "$@" >> "$R/run.log" 2>&1; rc=$?; say "end rc=$rc"; return $rc; }

say "code $(cat COMMIT), base $(cat $BASE/COMMIT), workers $W"
step "S1" $PY docs/research/planb/s1.py --out "$R/s1" --base "$BASE" --workers "$W" || { say "STOPPED: S1 failed"; exit 1; }
step "S2 rows" $PY docs/research/planb/gates2.py run --out "$R/s2" --cells SURGE,TRUCK --workers "$W" || { say "STOPPED"; exit 1; }
step "S2 traces" $PY docs/research/planb/gates2.py trace --out "$R/s2" --cells SURGE,TRUCK --workers "$W" || { say "STOPPED"; exit 1; }
step "S2 read" $PY docs/research/planb/gates2.py read --out "$R/s2" --cells SURGE,TRUCK
rc=$?
[ $rc -eq 3 ] && { say "STOPPED: the placebo passed G1, the gate is broken"; exit 3; }
[ $rc -eq 0 ] || { say "STOPPED"; exit 1; }
pending=$($PY -c "import json; s = json.load(open('$R/s2/s2.json')); print(','.join(c for c, v in s['cells'].items() if v['passes'] is None))")
if [ -n "$pending" ]; then
  step "S2 G2 fallback in $pending" $PY docs/research/planb/gates2.py fallback --out "$R/s2" --cells SURGE,TRUCK --fallback "$pending" --workers "$W" || { say "STOPPED"; exit 1; }
  step "S2 read again" $PY docs/research/planb/gates2.py read --out "$R/s2" --cells SURGE,TRUCK || { say "STOPPED"; exit 1; }
fi
say "DONE"
