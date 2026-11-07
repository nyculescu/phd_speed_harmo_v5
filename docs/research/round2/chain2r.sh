#!/bin/bash
# Round 2 on the rented machine (V439, V440): one DRL candidate trained like a round-1 slot (5 learners x 3 envs, 500 updates, round 1's seeds and stage-0 references), from its own branch's snapshot, then its training checks.
# usage: chain2r.sh KIND CODE_DIR OUT_ROOT   KIND is 2b, 1b or 1d; CODE_DIR is that candidate branch's deployed snapshot.
set -u
K=$1; C=$(realpath "$2"); O=$3; D=$O/train_$K
PY=/home/catalin/work/phd/phd_speed_harmo_v5b1_toolchain/venv/bin/python
R1=$C/docs/research/round1; R2=$C/docs/research/round2
S0=/home/catalin/work/phd/v5b1_runs/round1/out/stage0/stage0b.json
cd "$C"
unset SUMO_HOME
export OMP_NUM_THREADS=1 PYTHONPATH=$C:$R1:$R2 TMPDIR=/home/catalin/work/phd/v5b1_runs/phase3/scratch/tmp TZ=America/Vancouver
mkdir -p "$D" "$TMPDIR"
say() { echo "$(date '+%F %T') $K: $1" >> "$O/status.txt"; }

ENVJ=$($PY -c "import json, sys, common2; print(common2.train_args(sys.argv[1], json.load(open(sys.argv[2]))['refs'])[0])" "$K" "$S0") || { say "no candidate settings, STOPPED"; exit 2; }
FLAGS=$($PY -c "import json, sys, common2; print(' '.join(common2.train_args(sys.argv[1], json.load(open(sys.argv[2]))['refs'])[1]))" "$K" "$S0")
LEVELS=$($PY -c "import json, common1; print(json.dumps(list(common1.LEVELS)))")
say "code $(basename "$C"), env $ENVJ, flags [$FLAGS]"

train() {
  [ -d "$D/tb/C$1" ] && mv "$D/tb/C$1" "$D/tb/C$1.old_$(date +%s)"
  # FLAGS is a word list on purpose: each candidate adds whole flags such as --anneal or --scale X.
  $PY -m v5b.fleet.c_train train --out "$D" --learner "$1" --updates 500 --n-envs 3 --gamma 0.933 --lam 0.967 --levels "$LEVELS" \
    --net-seed 20261205 --env "$ENVJ" --lagr "" $FLAGS 2>&1 | grep -av '^Warning' >> "$O/train_${K}_$1.log"; return ${PIPESTATUS[0]}
}

say "start training"
declare -A who=() tried=()
for L in 0 1 2 3 4; do train $L & who[$!]=$L; done
while [ ${#who[@]} -gt 0 ]; do
  wait -n -p pid; rc=$?
  L=${who[$pid]}; unset "who[$pid]"
  [ $rc -eq 0 ] && { say "learner $L done"; continue; }
  if [ -n "${tried[$L]:-}" ]; then say "learner $L failed twice, STOPPED, goes to the author"; exit 3; fi
  tried[$L]=1
  say "learner $L crashed, rc=$rc, restarting with the same seeds"
  train $L & who[$!]=$L
done
say "end training"
$PY $R1/tbcheck1.py "$D" "$K" "$S0" 2>&1 | grep -av '^Warning' >> "$O/check_$K.log"; rc=${PIPESTATUS[0]}
case $rc in
  0) say "passed its training checks" ;;
  1) say "OUT: collapse (see check_$K.log)" ;;
  *) say "training checks FAULT rc=$rc, goes to the author"; exit 2 ;;
esac
touch "$D/done"
