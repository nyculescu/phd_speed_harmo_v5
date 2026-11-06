#!/bin/bash
# Round 1, from the pre-run checks to the test reading. usage: chain1.sh code_dir out_dir old_code_dir
# code_dir is a frozen copy of the run commit with a COMMIT file; old_code_dir is baseline-v3's frozen code (d2b2ecc).
# Stops at the first failed check; every stop goes to the author. A candidate failing its training checks leaves the round, the chain goes on.
set -u
C=$(realpath "$1"); D=$(realpath "$2"); OLD=$(realpath "$3"); W=64     # V421: the author asked for 64 evaluation workers, to measure throughput
PY=/home/catalin/work/phd/phd_speed_harmo_v5b1_toolchain/venv/bin/python
R=$C/docs/research/round1
mkdir -p "$D"
cd "$C"
unset SUMO_HOME
export OMP_NUM_THREADS=1 PYTHONPATH=$C:$R TMPDIR=/home/catalin/work/phd/v5b1_runs/phase3/scratch/tmp
say() { echo "$(date '+%F %T') $1" >> "$D/status.txt"; }
step() { say "start $1"; shift; "$@" 2>&1 | grep -av '^Warning' >> "$D/chain.log"; rc=${PIPESTATUS[0]}; say "end rc=$rc"; [ $rc -eq 0 ] || { say "STOPPED, goes to the author"; exit $rc; }; }
watchdog() { while sleep 300; do [ -n "$(find "$D" -type f -mmin -30 -print -quit)" ] || say "STALLED: no file changed for 30 minutes"; done; }
js() { $PY -c "import json, sys; d = json.load(open(sys.argv[1])); $2" "$3"; }

say "code $(cat "$C/COMMIT")"
watchdog & WD=$!
trap 'kill $WD $(jobs -p) 2>/dev/null' EXIT

step "tests" $PY -m pytest "$C/tests/test_round1.py" "$C/tests/test_conf3.py" "$C/tests/test_input_norm.py" -q -p no:cacheprovider
step "identity with baseline-v3's trainer" $PY $R/checks1.py identity "$D/checks" "$OLD"
step "stored rows and the zero-offset residual" $PY $R/checks1.py rows "$D/checks"
step "smoke in training mode" $PY $R/checks1.py smoke "$D/checks"
step "stage 0" $PY $R/stage0.py run "$D/stage0" $W
[ -f "$D/trained.json" ] || echo '{}' > "$D/trained.json"

train() {     # kind learner env lagr; event files of an earlier start are moved aside, never mixed in (review, V424)
  [ -d "$D/train_$1/tb/C$2" ] && mv "$D/train_$1/tb/C$2" "$D/train_$1/tb/C$2.old_$(date +%s)"
  $PY -m v5b.fleet.c_train train --out "$D/train_$1" --learner "$2" --updates 500 --n-envs 3 --gamma 0.933 --lam 0.967 --levels "$LEVELS" \
    --net-seed 20261205 --env "$3" --lagr "$4" 2>&1 | grep -av '^Warning' >> "$D/train_$1_$2.log"; return ${PIPESTATUS[0]}
}

LEVELS=$($PY -c "import json, common1; print(json.dumps(list(common1.LEVELS)))")
for K in v3w res attr lagr; do
  if [ "$K" = lagr ] && js "$D/stage0/stage0b.json" "sys.exit(0 if d['stop_2c'] else 1)"; then say "2C not trained: constraint not binding (stage 0b)"; continue; fi
  if [ -f "$D/train_$K/done" ]; then say "$K already trained and checked"; continue; fi
  ENVJ=$($PY -c "import json, sys, common1; print(json.dumps(common1.env_for('$K', json.load(open(sys.argv[1]))['refs'])))" "$D/stage0/stage0b.json")
  LAGR=""
  [ "$K" = lagr ] && LAGR=$(js "$D/stage0/stage0b.json" "print(json.dumps({'ref': d['d_ref']}))")
  say "start training $K"
  declare -A who=() tried=()
  for L in 0 1 2 3 4; do train $K $L "$ENVJ" "$LAGR" & who[$!]=$L; done
  while [ ${#who[@]} -gt 0 ]; do
    wait -n -p pid; rc=$?
    L=${who[$pid]}; unset "who[$pid]"
    [ $rc -eq 0 ] && { say "$K learner $L done"; continue; }
    if [ -n "${tried[$L]:-}" ]; then say "$K learner $L failed twice, STOPPED, goes to the author"; exit 3; fi
    tried[$L]=1
    say "$K learner $L crashed, rc=$rc, restarting with the same seeds"
    train $K $L "$ENVJ" "$LAGR" & who[$!]=$L
  done
  unset who tried
  say "end training $K"
  $PY $R/tbcheck1.py "$D/train_$K" $K "$D/stage0/stage0b.json" 2>&1 | grep -av '^Warning' >> "$D/chain.log"; rc=${PIPESTATUS[0]}
  if [ $rc -eq 0 ]; then
    $PY -c "import json, sys; p = sys.argv[1]; d = json.load(open(p)); d[sys.argv[2]] = sys.argv[3]; json.dump(d, open(p, 'w'))" "$D/trained.json" $K "$D/train_$K"
    say "$K passed its training checks"
  elif [ $rc -eq 1 ]; then
    say "$K OUT OF THE ROUND: collapse or lambda at its cap (see chain.log)"
  else
    say "$K training checks FAULT rc=$rc, STOPPED, goes to the author"; exit 2
  fi
  touch "$D/train_$K/done"
done

if js "$D/trained.json" "sys.exit(0 if d else 1)"; then :; else say "ROUND KILL: no candidate passed its training checks; baseline-v3 stays"; say "DONE"; exit 0; fi
step "validation" $PY $R/validate1.py run "$D/val" $W "$D/trained.json"
if js "$D/val/validation.json" "sys.exit(0 if d['finalists'] else 1)"; then :; else say "ROUND KILL: no candidate advanced; baseline-v3 stays; no test seed used"; say "DONE"; exit 0; fi
step "test, used once" $PY $R/test1.py run "$D/test" $W "$D/trained.json" "$D/val/validation.json"
say "DONE"
