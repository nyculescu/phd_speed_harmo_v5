#!/usr/bin/env bash
# Round 2 (docs/lab/round2_protocol.md): smoke of new actuators -> A-T0 -> A-R2 -> B-R2 -> D-1. Waits on PID files.
set -u
P=/home/catalin/work/phd/phd_speed_harmo_v6_toolchain/venv314/bin/python
R=/home/catalin/work/phd/vsl_lab_runs
L=$R/locks
cd /run/media/catalin/Shared/Workspace/phd/phd_speed_harmo_v5
unset SUMO_HOME; export OMP_NUM_THREADS=1
echo $$ > $L/round2.pid
for f in $L/wait_r2_*.pid; do [ -f "$f" ] && while kill -0 "$(cat $f)" 2>/dev/null; do sleep 20; done; done
mkdir -p $R/t1/round2_smoke
for C in "vsl:0.4:0.9" "mtfcb:40:38:9:0.0015" "madapt:1200:1"; do
  taskset -c 16-31 $P -m vsl_lab.jobs.bn4_eval --ctrl $C --inflow 1600 --seed 7110000 --tag smoke --out-root $R/t1/round2_smoke >> $R/t1/round2_smoke/smoke.log 2>&1
done
taskset -c 16-31 $P -m vsl_lab.jobs.bn4_eval --ctrl avfb:1:6 --inflow 1600 --seed 7110000 --tag smoke --out-root $R/t1/round2_smoke --env-kwargs '{"av_share":0.25}' >> $R/t1/round2_smoke/smoke.log 2>&1
$P -m vsl_lab.jobs.round2 a_t0 --gate-ok > $R/t1/round2_a_t0.log 2>&1
$P -m vsl_lab.jobs.round2 a_r2 --gate-ok > $R/t1/round2_a_r2.log 2>&1
$P -m vsl_lab.jobs.round2 b_r2 --gate-ok > $R/t1/round2_b_r2.log 2>&1
rm -f $L/round2.pid
echo round2 batches done
