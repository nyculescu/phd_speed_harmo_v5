#!/usr/bin/env bash
# D-3 merge repair (round2_protocol.md): realism gate at 0.2 s on H5a,H5b,H3a,H3b (seeds 7,160,000-009 / 7,160,100-119)
# -> Round 3 tool checks on the first passing variant (round3_tm21_protocol.md; stages stop themselves if a gate fails).
set -u
P=/home/catalin/work/phd/phd_speed_harmo_v6_toolchain/venv314/bin/python
R=/home/catalin/work/phd/vsl_lab_runs
L=$R/locks
cd /run/media/catalin/Shared/Workspace/phd/phd_speed_harmo_v5
unset SUMO_HOME; export OMP_NUM_THREADS=1
echo $$ > $L/d3.pid
$P -m vsl_lab.jobs.t2_realism run --gate-ok --step 0.2 --variants H5a,H5b,H3a,H3b --cal-seeds 7160000-7160009 \
  --chk-seeds 7160100-7160119 --suffix _d3 > $R/t2/realism_d3_driver.log 2>&1
for S in tcav0 tx t0 t1c; do
  $P -m vsl_lab.jobs.round3 $S --gate-ok --verdict docs/lab/t2_realism_verdict_d3.json > $R/t2/round3_d3_$S.log 2>&1
done
rm -f $L/d3.pid
echo d3 chain done
