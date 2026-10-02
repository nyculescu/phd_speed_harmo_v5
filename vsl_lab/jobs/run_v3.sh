#!/usr/bin/env bash
# MRG3-v3 (round2_protocol.md D-2): calibration -> R1 -> D-check -> R2 (if R1 T1 & T0 pass). Waits on the round2 PID.
set -u
P=/home/catalin/work/phd/phd_speed_harmo_v6_toolchain/venv314/bin/python
R=/home/catalin/work/phd/vsl_lab_runs
L=$R/locks
cd /run/media/catalin/Shared/Workspace/phd/phd_speed_harmo_v5
unset SUMO_HOME; export OMP_NUM_THREADS=1
echo $$ > $L/v3.pid
[ -f $L/round2.pid ] && while kill -0 "$(cat $L/round2.pid)" 2>/dev/null; do sleep 20; done
$P -m vsl_lab.jobs.t2_calib --workers 10 --gate-ok --plant v3 --seed0 7120100 > $R/t2/calib_v3_driver.log 2>&1
$P -m vsl_lab.jobs.t2_r1_checks --workers 10 --gate-ok --plant v3 > $R/t2/r1_v3_driver.log 2>&1
R1=$(ls -td $R/t2/r1_v3_*/ | head -1)
$P -m vsl_lab.eval.dcheck --root $R1/t1 --out docs/lab/t2_dcheck_v3.json > $R/t2/dcheck_v3.log 2>&1
$P -m vsl_lab.jobs.t2_r2_baselines --workers 10 --gate-ok --plant v3 > $R/t2/r2_v3_driver.log 2>&1
rm -f $L/v3.pid
echo v3 done
