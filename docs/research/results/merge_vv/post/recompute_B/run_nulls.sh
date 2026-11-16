#!/bin/bash
# One process at a time, niced, single thread.
export OMP_NUM_THREADS=1
PY=/home/catalin/work/phd/phd_speed_harmo_v5b1_toolchain/venv/bin/python
cd /home/catalin/work/phd/v5b1_runs/vv_post/recompute_B
nice -n 19 $PY -I null.py "L600|ttc_net|lr400_16_1" 2000 4000 98.75 11
nice -n 19 $PY -I null.py "L600|ttc_net|grid_lr400_13_1" 2000 4000 98.75 12
for k in "L300|ttc_net|lr400_16_1" "L300|ttc_net|grid_lr400_13_1" "L300|vv_ttc3_main|lr400_16_1" "L300|vv_ttc3_main|grid_lr400_13_1" "L600|ttc_net|lr400_16_1" "L600|ttc_net|grid_lr400_13_1"; do
  nice -n 19 $PY -I null.py "$k" 2000 2000 97.5 21
done
echo ALLDONE
