"""Compare the 26 spot re-runs (rerun.py: 16 into rerun/runs/; spot.py: 10 into spot/) with the stored runs.
Reads JSON only. Usage: python -I rerun_compare.py RERUN_DIR SPOT_DIR"""
import json, os, sys
STORED = '/home/catalin/work/phd/v5b1_runs/p1/v99/runs/'
F = ('hash', 'delay_s', 'served_ctrl_vph', 'ttt_ctrl_vehh', 'max_queue', 'meter_log', 't_switch', 't_back', 'valid')
n = same = 0
for d in sys.argv[1:]:
    for fn in sorted(f for f in os.listdir(d) if f.endswith('.json')):
        new, old = json.load(open(os.path.join(d, fn))), json.load(open(STORED + fn))
        diff = [f for f in F if new.get(f) != old.get(f)]
        n += 1; same += not diff
        print(f"{os.path.basename(d.rstrip('/'))}/{fn[:-5]}: {'IDENTICAL' if not diff else 'DIFF ' + str(diff)} "
              f"hash {old['hash'][:12]} delay {old['delay_s']:.3f}")
print(f'{same}/{n} identical on {F}')
