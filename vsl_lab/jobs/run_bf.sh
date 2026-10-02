#!/usr/bin/env bash
# B-F / B-R5 (round2_protocol.md): B-P6 passed screening (best checkpoint only; final = NC + 0.5 %). F class: PPO, F2 config,
# av_share 0.25, 3 learner seeds x 1,000 updates (seeds 0 and 1 in parallel, then 2), then R5 on test seeds
# 7,110,560-7,110,589 against the B-R2 tuned baselines at 25 % AVs (all controllers run at av_share 0.25).
set -u
P=/home/catalin/work/phd/phd_speed_harmo_v6_toolchain/venv314/bin/python
R=/home/catalin/work/phd/vsl_lab_runs
L=$R/locks
cd /run/media/catalin/Shared/Workspace/phd/phd_speed_harmo_v5
unset SUMO_HOME; export OMP_NUM_THREADS=1
echo $$ > $L/bf.pid
ENV='{"inflow":[1000,2000],"warmup_s":40,"control_s":900,"action_map":"nocap_center","av_share":0.25}'
tr() { $P -m vsl_lab.train.train_sb3 --env bn4 --algo ppo --reward out --updates 1000 --n-envs 16 --n-steps 450 --batch 900 \
  --epochs 10 --lr 3e-4 --lr-decay --gamma 0.99 --gae 0.95 --net 128 128 --log-std-init -0.5 --seed $1 --val-every 25 \
  --val-seeds-per 3 --val-seed0 7110310 --env-kwargs "$ENV" --tag bf_bn4av25 > $R/t1/bf_s$1.log 2>&1; }
tr 0 & tr 1 & wait
tr 2
RUNS=$(ls -td $R/t1/train/bf_bn4av25/*/ | head -3 | tr '\n' ' ')
$P -m vsl_lab.eval.pilot_report --tag bf_bn4av25 --track t1 --run-dirs $RUNS --refs docs/lab/t1av25_val_refs.json --nc-key nc \
  --const-key cap:18 --classical-key meter:10:6 --higher-better --metric-label "outflow over control window (veh/h)" > $R/t1/bf_report.log 2>&1
FINALS=$(for d in $RUNS; do echo -n "${d}final_model.zip:ppo "; done)
$P -m vsl_lab.jobs.t1_r5_eval --models $FINALS --tag r5_bf_av25 --gate-ok --seeds 7110560-7110589 \
  --frozen docs/lab/t1_bn4av25_baselines_frozen.json --plant-kwargs '{"av_share":0.25}' \
  --env-kwargs '{"action_map":"nocap_center"}' > $R/t1/r5_bf.log 2>&1
rm -f $L/bf.pid
echo bf done
