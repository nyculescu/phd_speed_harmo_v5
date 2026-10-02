#!/usr/bin/env bash
# Round 4 Addendum C: when P-H2 training (PID $1) ends, screen its final and best-validation policies on the validation
# specs against the frozen R2-H references (round4 screen), then stop. Waits by PID only.
set -u
P=/home/catalin/work/phd/phd_speed_harmo_v6_toolchain/venv314/bin/python
R=/home/catalin/work/phd/vsl_lab_runs
cd /run/media/catalin/Shared/Workspace/phd/phd_speed_harmo_v5
unset SUMO_HOME; export OMP_NUM_THREADS=1
while kill -0 "$1" 2>/dev/null; do sleep 60; done
$P -m vsl_lab.jobs.round4 screen --gate-ok --run-dir "$2" > $R/t2/round4_screen_ph2.log 2>&1
echo ph2 screen done
