#!/bin/bash
# V141/V143 chain: WZ calibration stage 1 (seeds 7,430,020-029) -> chosen configuration -> gate tool checks (7,430,100-149).
set -e
O=$1; PY=/home/catalin/work/phd/phd_speed_harmo_v5b1_toolchain/venv/bin/python
STAGE=${2:-1}; SEED0=${3:-7430020}
$PY -m v5b.p1c.calibrate run --out $O/calib --workers 24 --geom wz --seed0 $SEED0 --stage $STAGE
CFG=$($PY -c "import json;c=json.load(open('$O/calib/calibration_stage$STAGE.json'))['chosen'];assert c, 'no configuration passes: stage 2 needed';print(json.dumps({'merge':c['merge'],'cf':c['cf'],'lc_coop':c['lc_coop'],'speed_dev':c['speed_dev'],'step':c['step'],'geom':'wz','lc_coop_speed':c['lc_coop_speed'],'decel':c['decel']}))")
QN=$($PY -c "import json;c=json.load(open('$O/calib/calibration_stage$STAGE.json'))['chosen'];print(round(c['median_pre']/50)*50)")
echo "chosen $CFG q_near $QN"
$PY -m v5b.p1c.t1checks --out $O/t1 --workers 24 --seed-base 50 --q-near $QN --cfg "$CFG"
