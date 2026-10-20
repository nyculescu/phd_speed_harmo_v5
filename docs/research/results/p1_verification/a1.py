import pickle, sys, math, numpy as np
from collections import Counter, defaultdict
R = pickle.load(open(sys.argv[1], "rb"))
print("runs", len(R))
print("signal", Counter(r["signal"] for r in R.values()))
print("commit", Counter(r["code_commit"][:7] for r in R.values()))
print("valid", Counter(r["valid"] for r in R.values()), "teleport runs", sum(r["teleports"]>0 for r in R.values()))
print("drained", Counter(r["drained"] for r in R.values()), "ntrips==gen", Counter(r["n_trips"]==r["generated"] for r in R.values()))
# index
def tick(x, t0=40.0):
    k = max(0, math.ceil(x - t0 - 1e-9)); return t0 + k
bad = Counter()
nsw = 0
for key, r in R.items():
    if r["post"] is None or r["fa"]: continue
    nsw += 1
    t_on, t_off = r["t_on"], r["t_off"]
    # check t_on/t_off equal ticks of onset/onset+dur
    if t_on != tick(r["onset_s"]) or t_off != tick(r["onset_s"] + r["duration_s"]): bad["inc_ticks"] += 1
    tsw_exp = tick(t_on + r["d"])
    if tsw_exp >= t_off - 1e-9:
        if r["t_switch"] is not None: bad["switch_when_none"] += 1
        continue
    if r["t_switch"] != tsw_exp: bad["t_switch"] += 1
    if r["back"]:
        tbk = tick(t_off + r["c"])
        exp = tbk if tbk <= 40 + 900 - 1 + 1e-9 else None
        if r["t_back"] != exp: bad["t_back"] += 1
    else:
        if r["t_back"] is not None: bad["stay_back"] += 1
print("switch runs", nsw, "timing mismatches", dict(bad))
# false alarms
fa = [r for r in R.values() if r["fa"]]
print("fa runs", len(fa), "t_switch set", sum(r["t_switch"] is not None for r in fa), "t_back set", sum(r["t_back"] is not None for r in fa),
      "dur", Counter(round(r["t_back"]-r["t_switch"],3) for r in fa if r["t_back"] is not None))
# window independent of k and arm: same onset per seed
on = defaultdict(set)
for r in R.values():
    if r["incident"] != "none": on[r["seed"]].add((round(r["onset_s"],6), round(r["duration_s"],6)))
print("seeds with >1 window", sum(len(v)>1 for v in on.values()))
# sumo/demand seed per k
print("rep seed rule bad", sum((r["sumo_seed"] != r["seed"] + r["k"]*10_000_000) or (r["demand_seed"] != r["sumo_seed"]) for r in R.values()))
