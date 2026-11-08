#!/bin/bash
# Runs on the rented machine: round 2 from the 3E-X pick check to the test and band, the same commands as chain2.sh with W workers
# instead of 31 (worker count does not change rows: one simulation per process). Rows resume by (name, level, seed).
# The machine has no repository: jobs/shim/git answers "rev-parse SHA" from the frozen copies' COMMIT files and refuses the rest.
# usage: remote2_eval.sh W
set -u
W=${1:?W}
D=/home/catalin/work/phd/v5b1_runs/round2; C=$(realpath "$D/code_6c49e7e")
PY=/home/catalin/work/phd/phd_speed_harmo_v5b1_toolchain/venv/bin/python
R=$C/docs/research/round2
RC=$(cat "$C/COMMIT")
cd "$C"
unset SUMO_HOME
export PATH=/home/catalin/work/phd/v5b1_runs/jobs/shim:$PATH OMP_NUM_THREADS=1 PYTHONPATH=$C:$R:$C/docs/research/round1 TMPDIR=/home/catalin/work/phd/v5b1_runs/phase3/scratch/tmp
mkdir -p "$TMPDIR"
say() { echo "$(date '+%F %T') $1" >> "$D/status_remote_eval.txt"; }
step() { say "start $1"; shift; "$@" 2>&1 | grep -av '^Warning' >> "$D/chain_remote.log"; rc=${PIPESTATUS[0]}; say "end rc=$rc"; [ $rc -eq 0 ] || { say "STOPPED, goes to the author"; exit $rc; }; }

say "code $RC, workers $W, $(nproc) CPUs visible"
[ "$(cat "$D/checks/PASSED" 2>/dev/null)" = "$RC" ] || { say "checks not passed for $RC, STOPPED"; exit 2; }
[ -f "$D/cma3e_x1/final.json" ] && [ -f "$D/cma3e_x2/final.json" ] || { say "3E-X picks missing, STOPPED"; exit 3; }
step "check 1 on the 3E-X picks" $PY $R/check2.py picks "$D/checks" "$RC" 8
V=$D/val
step "validation runs" $PY $R/validate2.py run "$V" "$RC" "$W"
step "checkpoints" $PY $R/validate2.py chosen "$V"
step "ahead's KILL job" $PY $R/validate2.py killjob "$V"
A=$(realpath "$D/code_66fa146")
say "start ahead's importance KILL"
(cd "$A" && PYTHONPATH=$A $PY $R/importance2.py "$V/killjob.json" "$V/importance.json" "$W") 2>&1 | grep -av '^Warning' >> "$D/chain_remote.log"
rc=${PIPESTATUS[0]}; say "end rc=$rc"; [ $rc -eq 0 ] || { say "STOPPED, goes to the author"; exit $rc; }
step "validation decision" $PY $R/validate2.py decide "$V"
step "test and band, used once" $PY $R/test2.py run "$D" "$RC" "$W" "$V/validation.json"
say "DONE"
