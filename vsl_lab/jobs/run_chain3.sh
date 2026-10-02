#!/usr/bin/env bash
# P1 variants (R3 addendum A), two trainings at a time, after chain2 releases the CPU.
set -u
P=/home/catalin/work/phd/phd_speed_harmo_v6_toolchain/venv314/bin/python
R=/home/catalin/work/phd/vsl_lab_runs/t1
cd /run/media/catalin/Shared/Workspace/phd/phd_speed_harmo_v5
unset SUMO_HOME; export OMP_NUM_THREADS=1
while pgrep -f "[r]un_chain2.sh" > /dev/null; do sleep 30; done
COMMON="--env bn4 --n-envs 8 --n-steps 225 --batch 300 --epochs 10 --lr 3e-4 --gamma 0.99 --gae 0.95 --net 128 128 --seed 0 --val-every 25 --val-seeds-per 2"
ENVLIN='{"inflow":[1000,2000],"warmup_s":40,"control_s":900}'
ENVCEN='{"inflow":[1000,2000],"warmup_s":40,"control_s":900,"action_map":"nocap_center"}'
CAP=$($P -c "import json; print(json.load(open('docs/lab/t1_bn4_baselines_frozen.json'))['tuned']['cap']['ctrl'])")
MET=$($P -c "import json; print(json.load(open('docs/lab/t1_bn4_baselines_frozen.json'))['tuned']['meter']['ctrl'])")
report () { RUN=$(ls -td $R/train/$1/*/ | head -1); $P -m vsl_lab.eval.pilot_report --tag $1 --track t1 --run-dirs $RUN \
  --refs docs/lab/t1_val_refs.json --nc-key nc --const-key $CAP --classical-key $MET --higher-better \
  --metric-label "outflow over control window (veh/h)" > $R/$1_report.log 2>&1; }
$P -m vsl_lab.train.train_sb3 $COMMON --algo ppo --reward out --updates 600 --log-std-init -1.0 --env-kwargs "$ENVLIN" --tag p1b_bn4 > $R/p1b.log 2>&1 &
$P -m vsl_lab.train.train_sb3 $COMMON --algo ppo --reward out --updates 600 --log-std-init -0.5 --env-kwargs "$ENVCEN" --tag p1c_bn4 > $R/p1c.log 2>&1 &
wait; report p1b_bn4; report p1c_bn4
$P -m vsl_lab.train.train_sb3 $COMMON --algo trpo --reward out --updates 400 --env-kwargs "$ENVLIN" --tag p1d_bn4 > $R/p1d.log 2>&1 &
$P -m vsl_lab.train.train_sb3 $COMMON --algo recurrentppo --reward out --updates 400 --log-std-init -0.5 --env-kwargs "$ENVCEN" --tag p1e_bn4 > $R/p1e.log 2>&1 &
wait; report p1d_bn4; report p1e_bn4
$P -m vsl_lab.train.train_sb3 $COMMON --algo ppo --reward tts --updates 600 --log-std-init -0.5 --env-kwargs "$ENVCEN" --tag p1f_bn4 > $R/p1f.log 2>&1
report p1f_bn4
echo chain3 done
