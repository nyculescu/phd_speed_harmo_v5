#!/bin/bash
# Runs on the rented machine (V488), TRUCK only: S1 again on this CPU, then S3a, S4a (3E-C, 3E-D), S4b (ASCH), S4c (MPC-F). Each step must
# succeed before the next. Searches resume from their rows if restarted at the same commit. Progress in planb_s34/status.txt.
# usage: remote_s34.sh WORKERS
set -u
W=${1:?WORKERS}
P=/home/catalin/work/phd
R=$P/v5b1_runs/planb_s34
PY=$P/phd_speed_harmo_v5b1_toolchain/venv/bin/python
BASE=$P/code/79b889b
D=docs/research/planb
mkdir -p "$R"
unset SUMO_HOME
export OMP_NUM_THREADS=1
say() { echo "$(date -u '+%F %T') $1" >> "$R/status.txt"; }
step() { say "start $1"; shift; "$@" >> "$R/run.log" 2>&1; rc=$?; say "end rc=$rc"; [ $rc -eq 0 ] || { say "STOPPED"; exit 1; }; }

say "code $(cat COMMIT), base $(cat $BASE/COMMIT), workers $W"
[ -f "$R/s1/s1.json" ] && grep -q '"all_pass": true' "$R/s1/s1.json" || step "S1 on this machine" $PY $D/s1.py --out "$R/s1" --base "$BASE" --workers "$W"
step "S3a" $PY $D/repick.py --out "$R/s3a" --conds S,TRUCK --workers "$W"
for obj in ttc delay; do
  step "S4a TRUCK $obj" $PY $D/cmab.py --out "$R/cmab/TRUCK_$obj" --cell TRUCK --objective $obj --repick "$R/s3a/repick.json" --workers "$W"
done
step "inputs" $PY $D/plan6.py inputs --repick "$R/s3a/repick.json" --cmab "$R/cmab" --cells TRUCK --out "$R/inputs"
step "S4b ASCH" $PY $D/asch.py --out "$R/asch" --steady "$R/inputs/steady.json" --library "$R/inputs/library.json" --conds S,TRUCK --workers "$W"
step "S4c MPC-F" $PY $D/mpcf.py all --out "$R/mpcf" --actions "$R/inputs/actions.json" --conds S,TRUCK --workers "$W"
say "DONE"
