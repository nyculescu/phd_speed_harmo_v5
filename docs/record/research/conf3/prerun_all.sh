#!/bin/bash
# Pre-run checks at the run commit: T3, T0 with T1 and T2, smoke in training mode. usage: prerun_all.sh code_dir out_dir. Writes prerun_passed only if all pass.
set -u
C=$(realpath "$1"); D=$(realpath "$2"); W=24
PY=/home/catalin/work/phd/phd_speed_harmo_v5b1_toolchain/venv/bin/python
R=$C/docs/research/conf3
mkdir -p "$D"
cd "$C"
unset SUMO_HOME
export OMP_NUM_THREADS=1 PYTHONPATH=$C:$R TMPDIR=/home/catalin/work/phd/v5b1_runs/phase3/scratch/tmp
L=$D/prerun.log
run() { echo "== $1" >> "$L"; shift; "$@" 2>&1 | grep -av '^Warning' >> "$L"; rc=${PIPESTATUS[0]}; echo "rc=$rc" >> "$L"; [ $rc -eq 0 ] || exit $rc; }
echo "code $(cat "$C/COMMIT")" >> "$L"
run tests $PY -m pytest "$C/tests/test_conf3.py" -q -p no:cacheprovider
run T3 $PY $R/t3.py "$C/docs/research/baseline_v2/check2_rows.jsonl.gz" "$D/t3"
run T0 $PY $R/prerun.py "$D/t0" $W "$C/docs/research/phase3/shot_policies/C0_final.pt"
cat "$D/t0/prerun.jsonl" "$D/t0/prerun_nc.jsonl" > "$D/t0/nc_rows.jsonl"
run "smoke config" $PY $R/make_env.py "$D/t0/nc_rows.jsonl" "$D/smoke_env.json" 10
run smoke $PY $R/smoke_train.py "$D/smoke_env.json" "$D/smoke_rd"
cat "$C/COMMIT" > "$D/prerun_passed"
echo "ALL PASS" >> "$L"
