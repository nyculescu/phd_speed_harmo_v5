#!/usr/bin/env bash
# T1-M H step: H1 (tune evsched on tuning seeds) -> H2 (gate seeds). docs/lab/t1_meter_gscan_protocol.md Addendum A.
set -u
P=/home/catalin/work/phd/phd_speed_harmo_v6_toolchain/venv314/bin/python
R=/home/catalin/work/phd/vsl_lab_runs
cd /run/media/catalin/Shared/Workspace/phd/phd_speed_harmo_v5
unset SUMO_HOME; export OMP_NUM_THREADS=1
$P -m vsl_lab.jobs.t1_meter_h h1 --gate-ok --workers 32 > $R/t1/meter_h1.log 2>&1
$P -m vsl_lab.jobs.t1_meter_h h2 --gate-ok --workers 32 > $R/t1/meter_h2.log 2>&1
echo meter H done
