#!/usr/bin/env bash
# P-M3 (t1_meter_gscan_protocol.md Addendum C): variants a (stack 4), b (recurrent), c (plain), 1,000 updates, then 50-seed screening.
set -u
P=/home/catalin/work/phd/phd_speed_harmo_v6_toolchain/venv314/bin/python
R=/home/catalin/work/phd/vsl_lab_runs
cd /run/media/catalin/Shared/Workspace/phd/phd_speed_harmo_v5
unset SUMO_HOME; export OMP_NUM_THREADS=1
K='[null,{"kind":"slow","dur":300,"v_mps":5.0},{"kind":"block","dur":180},{"kind":"surge","dur":300,"factor":1.3}]'
envk() { echo "{\"inflow\":[1400,1800],\"warmup_s\":40,\"control_s\":900,\"decision_s\":30,\"actuator\":\"meter_sched\",\"meter_grid\":[\"40:6\",\"40:8\",\"20:12\",\"5:8\"],\"allow_off\":false,\"obs_stack\":$1,\"perturb_mix\":$K,\"val_perturb_cycle\":$K}"; }
COMMON="--env bn4 --reward tts --updates 1000 --n-envs 16 --n-steps 60 --batch 240 --epochs 10 --lr 3e-4 --lr-decay --gamma 0.99 --gae 0.95 --net 128 128 --seed 0 --val-every 25 --val-conds 1600 1600 1600 1600 --val-seeds-per 3 --val-seed0 7110320 --val-metric tts_system_ctrl_vehh --max-fail-share 0.05"
$P -m vsl_lab.train.train_sb3 $COMMON --algo ppo --env-kwargs "$(envk 4)" --tag pm3a_bn4 > $R/t1/pm3a_train.log 2>&1 &
$P -m vsl_lab.train.train_sb3 $COMMON --algo recurrentppo --env-kwargs "$(envk 1)" --tag pm3b_bn4 > $R/t1/pm3b_train.log 2>&1 &
$P -m vsl_lab.train.train_sb3 $COMMON --algo ppo --env-kwargs "$(envk 1)" --tag pm3c_bn4 > $R/t1/pm3c_train.log 2>&1 &
wait
for v in a b c; do
  RUN=$(ls -td $R/t1/train/pm3${v}_bn4/*/ | head -1)
  ST=1; AL=ppo; [ $v = a ] && ST=4; [ $v = b ] && AL=recurrentppo
  $P -m vsl_lab.jobs.t1_meter_pm --run-dir "$RUN" --gate-ok --workers 32 --seeds 7110340-7110389 --obs-stack $ST --algo $AL --tag pm3${v}_screen > $R/t1/pm3${v}_screen.log 2>&1
done
echo pm3 done
