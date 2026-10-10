#!/usr/bin/env bash
# R6+ (t1_meter_gscan_protocol.md Addendum G): vanilla RecurrentPPO on the metering rate, learners 2, 3, 4 run one at a
# time (each 16 envs), with the hybrid P-M4 configuration (constant lr 3e-4, as the frozen R6 candidate actually trained).
set -u
P=/home/catalin/work/phd/phd_speed_harmo_v6_toolchain/venv314/bin/python
R=/home/catalin/work/phd/vsl_lab_runs
cd /srv/shared/Workspace/phd/phd_speed_harmo_v5
unset SUMO_HOME; export OMP_NUM_THREADS=1
K='[null,{"kind":"slow","dur":300,"v_mps":5.0},{"kind":"block","dur":180},{"kind":"surge","dur":300,"factor":1.3}]'
ENV="{\"inflow\":[1400,1800],\"warmup_s\":40,\"control_s\":900,\"decision_s\":30,\"actuator\":\"meter_rate\",\"obs_stack\":1,\"perturb_mix\":$K,\"val_perturb_cycle\":$K}"
COMMON="--env bn4 --reward tts --updates ${UPDATES:-2000} --n-envs ${NENVS:-16} --n-steps 120 --batch 480 --epochs 10 --lr 3e-4 --gamma 0.99 --gae 0.95 --net 128 128 --val-every 25 --val-conds 1600 1600 1600 1600 --val-seeds-per 10 --val-seed0 7110400 --val-metric tts_system_ctrl_vehh --max-fail-share 0.05 --algo recurrentppo"
for S in ${SEEDS:-2 3 4}; do
  $P -m vsl_lab.train.train_sb3 $COMMON --seed $S --env-kwargs "$ENV" --tag ${TAG:-r6plus_vanilla} > $R/t1/${TAG:-r6plus_vanilla}_s$S.log 2>&1
done
echo r6plus training done
