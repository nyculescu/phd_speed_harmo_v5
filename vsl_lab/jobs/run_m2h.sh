#!/usr/bin/env bash
# Lead 1 stage H chain (t1_meter2_protocol.md Addendum A): tune -> fit -> gate. Stops on the first failure.
set -euo pipefail
unset SUMO_HOME; export OMP_NUM_THREADS=1
PY=/home/catalin/work/phd/phd_speed_harmo_v6_toolchain/venv314/bin/python
cd /run/media/catalin/Shared/Workspace/phd/phd_speed_harmo_v5
$PY -m vsl_lab.jobs.t1_meter2_h tune --gate-ok
$PY -m vsl_lab.jobs.t1_meter2_h fit
$PY -m vsl_lab.jobs.t1_meter2_h gate --gate-ok
