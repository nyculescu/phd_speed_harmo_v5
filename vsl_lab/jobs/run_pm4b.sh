#!/usr/bin/env bash
# P-M4 continuation: relaunch learner seed 4 (--fail-min-episodes 500), wait for seeds 3, 5 (PIDs $1 $2) and 4, then R5-M2.
set -u
P=/home/catalin/work/phd/phd_speed_harmo_v6_toolchain/venv314/bin/python
R=/home/catalin/work/phd/vsl_lab_runs
cd /run/media/catalin/Shared/Workspace/phd/phd_speed_harmo_v5
unset SUMO_HOME; export OMP_NUM_THREADS=1
K='[null,{"kind":"slow","dur":300,"v_mps":5.0},{"kind":"block","dur":180},{"kind":"surge","dur":300,"factor":1.3}]'
ENV="{\"inflow\":[1400,1800],\"warmup_s\":40,\"control_s\":900,\"decision_s\":30,\"actuator\":\"meter_sched\",\"meter_grid\":[\"40:6\",\"40:8\",\"20:12\",\"5:8\"],\"allow_off\":false,\"obs_stack\":1,\"perturb_mix\":$K,\"val_perturb_cycle\":$K}"
COMMON="--env bn4 --reward tts --updates 2000 --n-envs 16 --n-steps 120 --batch 480 --epochs 10 --lr 3e-4 --lr-decay --gamma 0.99 --gae 0.95 --net 128 128 --val-every 25 --val-conds 1600 1600 1600 1600 --val-seeds-per 10 --val-seed0 7110400 --val-metric tts_system_ctrl_vehh --max-fail-share 0.05 --algo recurrentppo"
$P -m vsl_lab.train.train_sb3 $COMMON --seed 4 --fail-min-episodes 500 --env-kwargs "$ENV" --tag pm4_bn4 > $R/t1/pm4_s4b.log 2>&1 &
S4=$!
while kill -0 "$1" 2>/dev/null || kill -0 "$2" 2>/dev/null || kill -0 "$S4" 2>/dev/null; do sleep 60; done
R3=$(ls -td $R/t1/train/pm4_bn4/*_s3_*/ | head -1); R4=$(ls -td $R/t1/train/pm4_bn4/*_s4_*/ | head -1); R5=$(ls -td $R/t1/train/pm4_bn4/*_s5_*/ | head -1)
$P -m vsl_lab.jobs.t1_meter_r5 --runs "$R3" "$R4" "$R5" --model-file best_val_model.zip --seeds 7110690-7110789 --tag r5m2 --gate-ok --workers 48 > $R/t1/r5m2.log 2>&1
$P -m vsl_lab.jobs.t1_meter_r5 --runs "$R3" "$R4" "$R5" --model-file final_model.zip --seeds 7110690-7110789 --tag r5m2_final --part drl --root $(ls -td $R/t1/r5m_*/ | head -1) --drl-prefix drlf --gate-ok --workers 48 > $R/t1/r5m2_final.log 2>&1
echo pm4 done
