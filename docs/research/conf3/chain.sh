#!/bin/bash
# Confirmatory 3, from rule tuning to the reading. usage: chain.sh code_dir out_dir. Stops at the first failure; every stop goes to the author.
set -u
C=$1; D=$2; W=24
PY=/home/catalin/work/phd/phd_speed_harmo_v5b1_toolchain/venv/bin/python
R=$C/docs/research/conf3
T=$D/train
mkdir -p "$T"
cd "$C"
unset SUMO_HOME
export OMP_NUM_THREADS=1 PYTHONPATH=$C:$R TMPDIR=/home/catalin/work/phd/v5b1_runs/phase3/scratch/tmp
say() { echo "$(date '+%F %T') $1" >> "$D/status.txt"; }
step() { say "start $1"; shift; "$@" 2>&1 | grep -v '^Warning' >> "$D/chain.log"; rc=${PIPESTATUS[0]}; say "end rc=$rc"; [ $rc -eq 0 ] || { say "STOPPED, goes to the author"; exit $rc; }; }

step "rule tuning" $PY $R/tune.py "$D" $W
step "first selection, early kill" $PY $R/select_opp.py "$D"
step "training config" $PY $R/make_env.py "$D/tune_nc.jsonl" "$D/env.json"

say "start training"
train() { $PY -m v5b.fleet.c_train train --out "$T" --learner "$1" --updates 500 --n-envs 3 --gamma 0.933 --lam 0.967 --levels '[4090.0, 4600.0, 5300.0]' --net-seed 20261205 --env "$(cat "$D/env.json")" 2>&1 | grep -v '^Warning' >> "$D/train_$1.log"; return ${PIPESTATUS[0]}; }
for L in 0 1 2 3 4; do train $L & pids[$L]=$!; done
for L in 0 1 2 3 4; do
  if ! wait ${pids[$L]}; then
    say "learner $L crashed, restarting with the same seeds"
    train $L || { say "learner $L failed twice, STOPPED, goes to the author"; exit 3; }
  fi
done
say "end training"

step "collapse check" $PY $R/collapse.py "$T" 5
step "tracing, copy rule" $PY $R/trace_copy.py "$T" "$D" $W
step "copy rule tuning" $PY $R/tune.py "$D" $W "$D/copy_rule.json"
step "final selection" $PY $R/select_opp.py "$D" "$D/copy_rule.json"
step "u250 report" $PY $R/u250.py "$T" "$D" $W
step "evaluation" $PY $R/eval_runs.py "$T" "$D" $W
step "reading" $PY $R/decide3.py "$D" "$D/decide3_table.csv"
say "DONE"
