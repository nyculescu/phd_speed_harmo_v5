#!/usr/bin/env bash
# After P1: ring R1/R2 v2 (post placement fix) -> ring validation refs -> P2 (hybrid) -> P3 (direct) -> MRG3 smoke + calibration.
set -u
P=/home/catalin/work/phd/phd_speed_harmo_v6_toolchain/venv314/bin/python
R=/home/catalin/work/phd/vsl_lab_runs
cd /run/media/catalin/Shared/Workspace/phd/phd_speed_harmo_v5
unset SUMO_HOME; export OMP_NUM_THREADS=1
while pgrep -f "[r]un_p1.sh" > /dev/null; do sleep 20; done
$P -m vsl_lab.jobs.t3_r1r2_ring --workers 10 --gate-ok > $R/t3/r1r2_v2_driver.log 2>&1
$P -m vsl_lab.jobs.val_refs --track t3 --workers 10 --gate-ok > $R/t3/valrefs_driver.log 2>&1
FS=$($P -c "import json; print(json.load(open('docs/lab/t3_ring_baselines_frozen.json'))['tuned']['fs']['ctrl'])")
PI=$($P -c "import json; print(json.load(open('docs/lab/t3_ring_baselines_frozen.json'))['tuned']['pi']['ctrl'])")
$P -m vsl_lab.train.train_sb3 --env ring --reward speed --algo ppo --updates 150 --n-envs 8 --n-steps 150 --batch 300 \
   --epochs 10 --lr 3e-4 --gamma 0.99 --gae 0.95 --net 64 64 --seed 0 --val-every 25 --val-seeds-per 3 \
   --env-kwargs '{"mode":"hybrid","L_range":[220,270],"decision_s":1.0}' --tag p2_ring_hyb > $R/t3/p2_train.log 2>&1
RUN=$(ls -td $R/t3/train/p2_ring_hyb/*/ | head -1)
$P -m vsl_lab.eval.pilot_report --tag p2_ring_hyb --track t3 --run-dirs $RUN --refs docs/lab/t3_val_refs.json \
   --nc-key nc --const-key $FS --classical-key $PI --higher-better --metric-label "mean speed (m/s)" > $R/t3/p2_report.log 2>&1
$P -m vsl_lab.train.train_sb3 --env ring --reward speed --algo ppo --updates 150 --n-envs 8 --n-steps 300 --batch 400 \
   --epochs 10 --lr 3e-4 --gamma 0.99 --gae 0.95 --net 64 64 --seed 0 --val-every 25 --val-seeds-per 3 \
   --env-kwargs '{"mode":"direct","L_range":[220,270],"decision_s":0.5}' --tag p3_ring_dir > $R/t3/p3_train.log 2>&1
RUN=$(ls -td $R/t3/train/p3_ring_dir/*/ | head -1)
$P -m vsl_lab.eval.pilot_report --tag p3_ring_dir --track t3 --run-dirs $RUN --refs docs/lab/t3_val_refs.json \
   --nc-key nc --const-key $FS --classical-key $PI --higher-better --metric-label "mean speed (m/s)" > $R/t3/p3_report.log 2>&1
mkdir -p $R/t2
taskset -c 16-31 $P -m vsl_lab.jobs.mrg3_run --ctrl nc --seed 7120000 --main-peak 5400 --ramp-peak 900 --tag smoke > $R/t2/smoke.log 2>&1
$P -m vsl_lab.jobs.t2_calib --workers 10 --gate-ok > $R/t2/calib_driver.log 2>&1
echo chain2 done
