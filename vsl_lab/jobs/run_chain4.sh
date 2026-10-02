#!/usr/bin/env bash
# Track 2: R1 checks at the calibrated cell -> (if T1 & T0 PASS) R2 tuning + T2 mechanism -> D-check on R1 NC runs.
set -u
P=/home/catalin/work/phd/phd_speed_harmo_v6_toolchain/venv314/bin/python
R=/home/catalin/work/phd/vsl_lab_runs/t2
cd /run/media/catalin/Shared/Workspace/phd/phd_speed_harmo_v5
unset SUMO_HOME; export OMP_NUM_THREADS=1
while pgrep -f "[r]un_chain2.sh|[r]un_chain3.sh|[r]un_chain6.sh" > /dev/null; do sleep 30; done
[ -f docs/lab/t2_mrg3_calibration.json ] || { echo "no calibration"; exit 1; }
$P -m vsl_lab.jobs.t2_r1_checks --workers 10 --gate-ok > $R/r1_driver.log 2>&1
R1=$(ls -td $R/r1_*/ | head -1)
$P -m vsl_lab.eval.dcheck --root $R1/t1 --out docs/lab/t2_dcheck.json > $R/dcheck.log 2>&1
$P -m vsl_lab.jobs.t2_r2_baselines --workers 10 --gate-ok > $R/r2_driver.log 2>&1
echo chain4 done
