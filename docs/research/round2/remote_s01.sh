#!/bin/bash
# Runs on the rented machine (V470, report-only): S0, the measurement pack over round 2's test and band, then S1, v3w and four rules
# at 3,500 and 7,000 veh/h. Both smokes must pass first: the 7 stored runs must reproduce on this CPU with the pack on.
# Rows resume by (name, level, seed). usage: remote_s01.sh WORKERS
set -u
W=${1:?WORKERS}
R=/home/catalin/work/phd/v5b1_runs; OUT=$R/round2; WK=$R/measure_s01
PY=/home/catalin/work/phd/phd_speed_harmo_v5b1_toolchain/venv/bin/python
M=docs/research/round2/measure2.py
mkdir -p "$WK"
unset SUMO_HOME
export OMP_NUM_THREADS=1
say() { echo "$(date -u '+%F %T') $1" >> "$WK/status.txt"; }
step() { say "start $1"; shift; "$@" 2>&1 | grep -av '^Warning' >> "$WK/run.log"; rc=${PIPESTATUS[0]}; say "end rc=$rc"; [ $rc -eq 0 ] || { say "STOPPED"; exit $rc; }; }

say "code $(basename "$(pwd -P)"), workers $W"
step "smoke: 7 stored runs with the pack" $PY $M smoke "$OUT" "$WK/smoke" 7
step "smoke1: S1 sample runs" $PY $M smoke1 "$OUT" "$WK/smoke1" 3
step "plan" $PY $M plan "$OUT" "$WK"
step "run S0 and S1" $PY $M run "$OUT" "$WK" "$W" --go
step "row count" $PY -c "
import json, sys
n = {f: len({(r['name'], r['q'], r['seed']) for r in map(json.loads, open('$WK/rows_' + f + '.jsonl'))}) for f in ('test', 'band', 's1')}
print('rows', n); sys.exit(0 if n == {'test': 2800, 'band': 2400, 's1': 360} else 1)"
for f in test band s1; do step "report $f" $PY $M report "$OUT" "$WK" "rows_$f.jsonl"; done
say "DONE"
