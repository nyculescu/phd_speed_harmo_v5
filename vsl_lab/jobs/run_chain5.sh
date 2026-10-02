#!/usr/bin/env bash
# After chain4: ring shield verification -> P2b/P3b (if shield leaves baselines unchanged) -> MRG3-v2 calibration,
# R1 checks, D-check, R2 (if R1 passes). All pre-registered (R3 addendum B; T2 R1 addendum MRG3-v2; T2 R2 protocol).
set -u
P=/home/catalin/work/phd/phd_speed_harmo_v6_toolchain/venv314/bin/python
R=/home/catalin/work/phd/vsl_lab_runs
cd /run/media/catalin/Shared/Workspace/phd/phd_speed_harmo_v5
unset SUMO_HOME; export OMP_NUM_THREADS=1
while pgrep -f "[r]un_chain2.sh|[r]un_chain3.sh|[r]un_chain4.sh" > /dev/null; do sleep 30; done
$P -m vsl_lab.jobs.ring_shield_verify > $R/t3/shield_verify.log 2>&1
if $P -c "import json,sys; sys.exit(0 if json.load(open('docs/lab/t3_shield_verify.json'))['PASS'] else 1)"; then
  FS=$($P -c "import json; print(json.load(open('docs/lab/t3_ring_baselines_frozen.json'))['tuned']['fs']['ctrl'])")
  PI=$($P -c "import json; print(json.load(open('docs/lab/t3_ring_baselines_frozen.json'))['tuned']['pi']['ctrl'])")
  for V in "p2b_ring_hyb hybrid 1.0 150 300" "p3b_ring_dir direct 0.5 300 400"; do
    set -- $V
    $P -m vsl_lab.train.train_sb3 --env ring --reward speed --algo ppo --updates 600 --n-envs 8 --n-steps $4 --batch $5 \
      --epochs 10 --lr 3e-4 --gamma 0.99 --gae 0.95 --net 64 64 --seed 0 --val-every 25 --val-seeds-per 3 \
      --env-kwargs "{\"mode\":\"$2\",\"L_range\":[220,270],\"decision_s\":$3,\"alpha\":0.0}" --tag $1 > $R/t3/$1.log 2>&1
    RUN=$(ls -td $R/t3/train/$1/*/ | head -1)
    $P -m vsl_lab.eval.pilot_report --tag $1 --track t3 --run-dirs $RUN --refs docs/lab/t3_val_refs.json \
      --nc-key nc --const-key $FS --classical-key $PI --higher-better --metric-label "mean speed (m/s)" > $R/t3/$1_report.log 2>&1
  done
else
  echo "shield changed baselines: ring R2 must be re-run first" > $R/t3/shield_verify_FAILED.txt
fi
$P -m vsl_lab.jobs.t2_calib --workers 10 --gate-ok --plant v2 --seed0 7120050 > $R/t2/calib_v2_driver.log 2>&1
$P -m vsl_lab.jobs.t2_r1_checks --workers 10 --gate-ok --plant v2 > $R/t2/r1_v2_driver.log 2>&1
R1=$(ls -td $R/t2/r1_v2_*/ | head -1)
$P -m vsl_lab.eval.dcheck --root $R1/t1 --out docs/lab/t2_dcheck_v2.json > $R/t2/dcheck_v2.log 2>&1
$P -m vsl_lab.jobs.t2_r2_baselines --workers 10 --gate-ok --plant v2 > $R/t2/r2_v2_driver.log 2>&1
echo chain5 done
