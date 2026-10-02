#!/usr/bin/env bash
# P1 pipeline (Track 1): validation references -> PPO pilot -> screening report. Waits for R2 v2 first.
set -u
P=/home/catalin/work/phd/phd_speed_harmo_v6_toolchain/venv314/bin/python
cd /run/media/catalin/Shared/Workspace/phd/phd_speed_harmo_v5
unset SUMO_HOME; export OMP_NUM_THREADS=1
while pgrep -f "[t]1_r2_baselines" > /dev/null; do sleep 20; done
$P -m vsl_lab.jobs.val_refs --track t1 --workers 10 --gate-ok > /home/catalin/work/phd/vsl_lab_runs/t1/valrefs_driver.log 2>&1
$P -m vsl_lab.train.train_sb3 --env bn4 --reward out --algo ppo --updates 150 --n-envs 8 --n-steps 225 --batch 300 \
   --epochs 10 --lr 3e-4 --gamma 0.99 --gae 0.95 --net 128 128 --seed 0 --val-every 25 --val-seeds-per 2 \
   --env-kwargs '{"inflow":[1000,2000],"warmup_s":40,"control_s":900}' --tag p1_bn4 \
   > /home/catalin/work/phd/vsl_lab_runs/t1/p1_train.log 2>&1
RUN=$(ls -td /home/catalin/work/phd/vsl_lab_runs/t1/train/p1_bn4/*/ | head -1)
CAP=$($P -c "import json; print(json.load(open('docs/lab/t1_bn4_baselines_frozen.json'))['tuned']['cap']['ctrl'])")
MET=$($P -c "import json; print(json.load(open('docs/lab/t1_bn4_baselines_frozen.json'))['tuned']['meter']['ctrl'])")
$P -m vsl_lab.eval.pilot_report --tag p1_bn4 --track t1 --run-dirs $RUN --refs docs/lab/t1_val_refs.json \
   --nc-key nc --const-key $CAP --classical-key $MET --higher-better --metric-label "outflow over control window (veh/h)" \
   > /home/catalin/work/phd/vsl_lab_runs/t1/p1_report.log 2>&1
echo P1 pipeline done
