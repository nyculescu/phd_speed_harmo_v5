#!/usr/bin/env bash
# Round 4 Addendum D: when P-H3 training (PID $1) ends, screen its policies (mode residual_c) on the validation specs.
set -u
P=/home/catalin/work/phd/phd_speed_harmo_v6_toolchain/venv314/bin/python
R=/home/catalin/work/phd/vsl_lab_runs
cd /run/media/catalin/Shared/Workspace/phd/phd_speed_harmo_v5
unset SUMO_HOME; export OMP_NUM_THREADS=1
while kill -0 "$1" 2>/dev/null; do sleep 60; done
$P -m vsl_lab.jobs.round4 screen --gate-ok --mode residual_c --run-dir "$2" > $R/t2/round4_screen_ph3.log 2>&1
echo ph3 screen done
