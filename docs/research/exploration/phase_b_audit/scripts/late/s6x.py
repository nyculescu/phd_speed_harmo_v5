"""Read-only extraction from S6 rows for the late-record classification. EXPLORATORY."""
import json, pickle, collections
ROWS = '/home/catalin/work/phd/v5b1_runs/planb_s56_remote/s6/s6_rows.jsonl'
ARMS = {"nc","p333","os0_10_10","grid_z31333","z33133","r4a1","grid_r4a2","3E-D_TRUCK","3E-C_TRUCK","lr1000_16_2","MPC-F","lr1000_10_1","copy","3e","w0u250","w1u500","w2u250","w3u500","w4u500"}
KEYS = ("all_delay","delay","N","passed","finished_pct","arrived","end_stop2","teleports","collisions")
PK = ('smooth','ease','smooth_s','ease_max','tau_rise','taper_fast','fix_x','geom')
T = {}; plants = collections.Counter(); names = collections.Counter(); n = 0
def find_plant(cfg):
    out = {}
    def walk(d):
        if isinstance(d, dict):
            for k, v in d.items():
                if k in PK and not isinstance(v, dict): out.setdefault(k, v)
                walk(v)
    walk(cfg)
    return tuple(sorted((k, str(v)) for k, v in out.items()))
with open(ROWS) as h:
    for line in h:
        r = json.loads(line); n += 1
        cell, arm = r["name"].split("|", 1)
        names[(cell, arm)] += 1
        plants[(cell, find_plant(r.get("cfg", {})))] += 1
        if arm in ARMS:
            T.setdefault((cell, arm), {})[r["seed"]] = {k: r.get(k) for k in KEYS}
print("rows", n, "arms", len(names))
for k, c in sorted(plants.items()): print(" plant", k[0], c, dict(k[1]))
print(sorted(set(a for _, a in names)))
pickle.dump(T, open("s6x.pkl", "wb"))
