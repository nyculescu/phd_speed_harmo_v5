#!/usr/bin/env bash
# D-4 lane-drop plant (round2_protocol.md): realism gate at 0.2 s on H5,H3,H0 -> Round 3 tool checks on the primary.
set -u
P=/home/catalin/work/phd/phd_speed_harmo_v6_toolchain/venv314/bin/python
R=/home/catalin/work/phd/vsl_lab_runs
L=$R/locks
cd /run/media/catalin/Shared/Workspace/phd/phd_speed_harmo_v5
unset SUMO_HOME; export OMP_NUM_THREADS=1
echo $$ > $L/ld3.pid
$P -m vsl_lab.jobs.t2_realism run --gate-ok --step 0.2 --geom lanedrop --variants H5,H3,H0 \
  --main 3300,3600,3900,4200,4500,4800,5100 --ramp 0 --stress 5100/0 --cal-seeds 7160010-7160019 \
  --chk-seeds 7160120-7160139 --suffix _ld3 > $R/t2/realism_ld3_driver.log 2>&1
for S in tcav0 tx t0 t1c; do
  $P -m vsl_lab.jobs.round3 $S --gate-ok --verdict docs/lab/t2_realism_verdict_ld3.json > $R/t2/round3_ld3_$S.log 2>&1
done
rm -f $L/ld3.pid
echo ld3 chain done
