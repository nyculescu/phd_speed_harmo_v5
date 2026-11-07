import json, sys
import numpy as np
from collections import defaultdict
sys.path.insert(0, '/srv/shared/Workspace/phd/phd_speed_harmo_v5b1/docs/research/conf3')
from common import effect
rows = defaultdict(dict)
for line in open(sys.argv[1]):
    r = json.loads(line)
    cell, arm = r['name'].split('|', 1)
    rows[(cell, arm)][r['seed']] = r
def arm(cell, names, keys):
    seeds = set.intersection(*[set(rows[(cell, a)]) for a in names])
    return {s: {k: float(np.mean([rows[(cell, a)][s].get(k, 0) for a in names])) for k in keys} for s in seeds}
keys = ('ttc2', 'ttc15', 'sev3', 'ttc_net')
for cell, rule in (('X1', 'p333'), ('X2', 'os1_15_10')):
    v = arm(cell, ['w0','w1','w2','w3','w4'], keys)
    for opp in (rule, 'nc'):
        o = arm(cell, [opp], keys)
        print(cell, 'v3w vs', opp, {k: effect(v, o, k, -1, (2.5, 97.5)) for k in keys})
