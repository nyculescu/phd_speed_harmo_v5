#!/usr/bin/env bash
# Realism gate (docs/lab/t2_realism_protocol.md) -> B-P6 (docs/lab/round2_protocol.md: val refs at 25 % AVs, PPO F2 config,
# screening report) -> MRG3-v3 R2 (runs only if H0 PASSED the realism gate). Waits on the round2 and v3 chains by PID file.
set -u
P=/home/catalin/work/phd/phd_speed_harmo_v6_toolchain/venv314/bin/python
R=/home/catalin/work/phd/vsl_lab_runs
L=$R/locks
cd /run/media/catalin/Shared/Workspace/phd/phd_speed_harmo_v5
unset SUMO_HOME; export OMP_NUM_THREADS=1
echo $$ > $L/realism.pid
for f in $L/round2.pid $L/v3.pid; do [ -f "$f" ] && while kill -0 "$(cat $f)" 2>/dev/null; do sleep 30; done; done
$P -m vsl_lab.jobs.t2_realism run --gate-ok > $R/t2/realism_driver.log 2>&1
$P -m vsl_lab.jobs.val_refs --track t1av25 --workers 10 --gate-ok > $R/t1/valrefs_av25.log 2>&1
ENV='{"inflow":[1000,2000],"warmup_s":40,"control_s":900,"action_map":"nocap_center","av_share":0.25}'
$P -m vsl_lab.train.train_sb3 --env bn4 --algo ppo --reward out --updates 600 --n-envs 16 --n-steps 450 --batch 900 \
  --epochs 10 --lr 3e-4 --lr-decay --gamma 0.99 --gae 0.95 --net 128 128 --log-std-init -0.5 --seed 0 --val-every 25 \
  --val-seeds-per 3 --val-seed0 7110310 --env-kwargs "$ENV" --tag p6_bn4av25 > $R/t1/p6.log 2>&1
RUN=$(ls -td $R/t1/train/p6_bn4av25/*/ | head -1)
CAP=$($P -c "import json; print(json.load(open('docs/lab/t1_bn4av25_baselines_frozen.json'))['tuned']['cap']['ctrl'])")
MET=$($P -c "import json; print(json.load(open('docs/lab/t1_bn4av25_baselines_frozen.json'))['tuned']['meter']['ctrl'])")
$P -m vsl_lab.eval.pilot_report --tag p6_bn4av25 --track t1 --run-dirs $RUN --refs docs/lab/t1av25_val_refs.json --nc-key nc \
  --const-key $CAP --classical-key $MET --higher-better --metric-label "outflow over control window (veh/h)" > $R/t1/p6_report.log 2>&1
$P -m vsl_lab.jobs.t2_r2_baselines --workers 10 --gate-ok --plant v3 > $R/t2/r2_v3_after_realism.log 2>&1
rm -f $L/realism.pid
echo realism_p6 done
