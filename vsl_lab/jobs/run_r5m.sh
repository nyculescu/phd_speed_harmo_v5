#!/usr/bin/env bash
# R5-M (Addendum D), split to use idle CPU: comparator arms now; DRL arms + analysis after the F class.
set -u
P=/home/catalin/work/phd/phd_speed_harmo_v6_toolchain/venv314/bin/python
R=/home/catalin/work/phd/vsl_lab_runs
cd /run/media/catalin/Shared/Workspace/phd/phd_speed_harmo_v5
unset SUMO_HOME; export OMP_NUM_THREADS=1
ROOT=$R/t1/r5m_main
R0=$(ls -td $R/t1/train/pm3b_bn4/*/ | head -1)
$P -m vsl_lab.jobs.t1_meter_r5 --runs "$R0" x x --part comps --root $ROOT --gate-ok --workers 48 > $R/t1/r5m_comps.log 2>&1
until grep -q "pmf done" $R/pmf_chain.log 2>/dev/null; do sleep 60; done
R1=$(ls -td $R/t1/train/pmf_bn4/*_s1_*/ | head -1)
R2=$(ls -td $R/t1/train/pmf_bn4/*_s2_*/ | head -1)
$P -m vsl_lab.jobs.t1_meter_r5 --runs "$R0" "$R1" "$R2" --part drl --root $ROOT --gate-ok --workers 48 > $R/t1/r5m.log 2>&1
echo r5m done
