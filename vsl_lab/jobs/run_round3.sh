#!/usr/bin/env bash
# Author decisions 2026-10-02: Round 3 before B-P6; 0.2 s step. Chain: realism re-check at 0.2 s (t2_realism_protocol.md
# Addendum B) -> Round 3 T-CAV0 -> T-X -> T0 -> T1c (round3_tm21_protocol.md; each stage stops itself if its gate
# failed) -> B-P6 (round2_protocol.md). Waits on the running 0.5 s realism batch by PID (no pattern matching).
# Usage: run_round3.sh <pid of the 0.5 s t2_realism run> <comma list of variants in the 0.2 s scope>
set -u
P=/home/catalin/work/phd/phd_speed_harmo_v6_toolchain/venv314/bin/python
R=/home/catalin/work/phd/vsl_lab_runs
L=$R/locks
cd /run/media/catalin/Shared/Workspace/phd/phd_speed_harmo_v5
unset SUMO_HOME; export OMP_NUM_THREADS=1
echo $$ > $L/round3.pid
while kill -0 "$1" 2>/dev/null; do sleep 30; done
$P -m vsl_lab.jobs.t2_realism run --gate-ok --step 0.2 --variants "$2" --cal-seeds 7120260-7120269 \
  --chk-seeds 7120270-7120289 > $R/t2/realism_step0.2_driver.log 2>&1
for S in tcav0 tx t0 t1c; do
  $P -m vsl_lab.jobs.round3 $S --gate-ok > $R/t2/round3_$S.log 2>&1
done
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
rm -f $L/round3.pid
echo round3 chain done
