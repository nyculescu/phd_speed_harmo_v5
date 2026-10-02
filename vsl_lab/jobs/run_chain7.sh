#!/usr/bin/env bash
# F2 (stability test of the BN4 PPO policy; R3 addendum D) -> R5. Waits on chain5 via its PID (no pattern matching).
set -u
P=/home/catalin/work/phd/phd_speed_harmo_v6_toolchain/venv314/bin/python
R=/home/catalin/work/phd/vsl_lab_runs/t1
L=/home/catalin/work/phd/vsl_lab_runs/locks
cd /run/media/catalin/Shared/Workspace/phd/phd_speed_harmo_v5
unset SUMO_HOME; export OMP_NUM_THREADS=1
echo $$ > $L/chain7.pid
for f in $L/wait_*.pid; do [ -f "$f" ] && while kill -0 "$(cat $f)" 2>/dev/null; do sleep 30; done; done
ENVCEN='{"inflow":[1000,2000],"warmup_s":40,"control_s":900,"action_map":"nocap_center"}'
for S in 0 1 2; do
  $P -m vsl_lab.train.train_sb3 --env bn4 --algo ppo --reward out --updates 1000 --n-envs 16 --n-steps 450 --batch 900 \
    --epochs 10 --lr 3e-4 --lr-decay --gamma 0.99 --gae 0.95 --net 128 128 --log-std-init -0.5 --seed $S --val-every 25 \
    --val-seeds-per 3 --env-kwargs "$ENVCEN" --tag f2_bn4 > $R/f2_s$S.log 2>&1
done
RUNS=$(ls -td $R/train/f2_bn4/*/ | head -3 | tr '\n' ' ')
CAP=$($P -c "import json; print(json.load(open('docs/lab/t1_bn4_baselines_frozen.json'))['tuned']['cap']['ctrl'])")
MET=$($P -c "import json; print(json.load(open('docs/lab/t1_bn4_baselines_frozen.json'))['tuned']['meter']['ctrl'])")
$P -m vsl_lab.eval.pilot_report --tag f2_bn4 --track t1 --run-dirs $RUNS --refs docs/lab/t1_val_refs.json --nc-key nc \
  --const-key $CAP --classical-key $MET --higher-better --metric-label "outflow over control window (veh/h)" > $R/f2_report.log 2>&1
FINALS=$(for d in $RUNS; do echo -n "${d}final_model.zip:ppo "; done)
$P -m vsl_lab.jobs.t1_r5_eval --models $FINALS --tag r5_f2_final --gate-ok --env-kwargs '{"action_map":"nocap_center"}' > $R/r5_f2.log 2>&1
rm -f $L/chain7.pid
echo chain7 done
