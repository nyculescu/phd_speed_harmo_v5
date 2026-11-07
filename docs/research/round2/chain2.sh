#!/bin/bash
# Round 2 evaluation (round_2.md, V454), from the pre-run checks to the readings. usage: chain2.sh code_dir out_dir
# code_dir is a frozen copy of r2/eval's run commit with a COMMIT file. Each step's failure stops the chain and goes to the author.
set -u
C=$(realpath "$1"); D=$(realpath "$2"); W=31     # V426
PY=/home/catalin/work/phd/phd_speed_harmo_v5b1_toolchain/venv/bin/python
R=$C/docs/research/round2
RC=$(cat "$C/COMMIT")
mkdir -p "$D"
cd "$C"
unset SUMO_HOME
export OMP_NUM_THREADS=1 PYTHONPATH=$C:$R:$C/docs/research/round1 TMPDIR=/home/catalin/work/phd/v5b1_runs/phase3/scratch/tmp
say() { echo "$(date '+%F %T') $1" >> "$D/status.txt"; }
step() { say "start $1"; shift; "$@" 2>&1 | grep -av '^Warning' >> "$D/chain.log"; rc=${PIPESTATUS[0]}; say "end rc=$rc"; [ $rc -eq 0 ] || { say "STOPPED, goes to the author"; exit $rc; }; }
watchdog() { while sleep 300; do [ -n "$(find "$D" -type f -mmin -30 -print -quit)" ] || say "STALLED: no file changed for 30 minutes"; done; }
snap() { realpath "$D/code_$1"; }

say "code $RC"
watchdog & WD=$!
trap 'kill $WD $(jobs -p) 2>/dev/null' EXIT

[ -f "$D/checks/PASSED" ] || {
  step "tests" $PY -m pytest "$C/tests/test_round2.py" -q -p no:cacheprovider
  step "check 1, identity" $PY $R/check2.py identity "$D/checks" "$RC" 8
  step "checks 2 and 4, stored rows in every snapshot" $PY $R/check2.py rows "$D/checks" "$RC"
  step "check 3, reading replay" $PY $R/check2.py replay "$D/checks" "$RC"
  step "check 5, smoke" $PY $R/check2.py smoke "$D/checks" "$RC" 8
  touch "$D/checks/PASSED"
}

search() {     # cell, start rule, workers: 3E-X (D4), then its pick
  local o=$D/cma3e_$1
  $PY $R/cma2.py --out "$o" --seeds 7440740-7440779 --seed-block 7440740-7440779 --seeds-per-gen 16 --levels 5300 --cond "${1^^}" --pop 24 --gens 40 \
    --ref p333 --cap 1 --start "$2" --shortlist norm --admit-cap 2 --workers "$3" >> "$D/cma3e_$1.log" 2>&1 || return 1
  $PY $R/cma2.py --out "$o" --final 5 --workers "$3" >> "$D/cma3e_$1.log" 2>&1
}
if [ ! -f "$D/cma3e_x1/final.json" ] || [ ! -f "$D/cma3e_x2/final.json" ]; then
  say "start 3E-X1 and 3E-X2"
  search x1 os0_10_10 15 & P1=$!
  search x2 os1_15_10 16 & P2=$!
  wait $P1; r1=$?; wait $P2; r2=$?
  say "end 3E-X1 rc=$r1, 3E-X2 rc=$r2"
  [ $r1 -eq 0 ] && [ $r2 -eq 0 ] || { say "STOPPED, goes to the author"; exit 3; }
fi
step "check 1 on the 3E-X picks" $PY $R/check2.py picks "$D/checks" "$RC" 8

V=$D/val
step "validation runs" $PY $R/validate2.py run "$V" "$RC" $W
step "checkpoints" $PY $R/validate2.py chosen "$V"
step "ahead's KILL job" $PY $R/validate2.py killjob "$V"
A=$(snap 66fa146)
say "start ahead's importance KILL"
(cd "$A" && PYTHONPATH=$A $PY $R/importance2.py "$V/killjob.json" "$V/importance.json" 20) 2>&1 | grep -av '^Warning' >> "$D/chain.log"
rc=${PIPESTATUS[0]}; say "end rc=$rc"; [ $rc -eq 0 ] || { say "STOPPED, goes to the author"; exit $rc; }
step "validation decision" $PY $R/validate2.py decide "$V"
step "test and band, used once" $PY $R/test2.py run "$D" "$RC" $W "$V/validation.json"
say "DONE"
