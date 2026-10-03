#!/usr/bin/env bash
# P-M (t1_meter_gscan_protocol.md Addendum B): train -> screen.
set -u
P=/home/catalin/work/phd/phd_speed_harmo_v6_toolchain/venv314/bin/python
R=/home/catalin/work/phd/vsl_lab_runs
cd /run/media/catalin/Shared/Workspace/phd/phd_speed_harmo_v5
unset SUMO_HOME; export OMP_NUM_THREADS=1
K='[null,{"kind":"slow","dur":300,"v_mps":5.0},{"kind":"block","dur":180},{"kind":"surge","dur":300,"factor":1.3}]'
ENV="{\"inflow\":[1400,1800],\"warmup_s\":40,\"control_s\":900,\"decision_s\":30,\"actuator\":\"meter_sched\",\"meter_grid\":[\"40:6\",\"40:8\",\"20:12\",\"5:8\"],\"allow_off\":false,\"perturb_mix\":$K,\"val_perturb_cycle\":$K}"
$P -m vsl_lab.train.train_sb3 --env bn4 --algo ppo --reward tts --updates 500 --n-envs 16 --n-steps 60 --batch 240 --epochs 10 \
  --lr 3e-4 --lr-decay --gamma 0.99 --gae 0.95 --net 128 128 --seed 0 --val-every 25 --val-conds 1600 1600 1600 1600 \
  --val-seeds-per 3 --val-seed0 7110320 --val-metric tts_system_ctrl_vehh --max-fail-share 0.05 --env-kwargs "$ENV" --tag pm2_bn4 > $R/t1/pm2_train.log 2>&1
RUN=$(ls -td $R/t1/train/pm2_bn4/*/ | head -1)
$P -m vsl_lab.jobs.t1_meter_pm --run-dir "$RUN" --gate-ok --workers 32 --tag pm2_screen > $R/t1/pm2_screen.log 2>&1
echo pm2 done
