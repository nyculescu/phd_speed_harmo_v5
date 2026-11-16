import pickle, json, sys, hashlib
from collections import Counter, defaultdict
import numpy as np
S = sys.argv[1]
R = pickle.load(open(f"{S}/screen.pkl", "rb"))
jobs = json.load(open("/home/catalin/work/phd/v5b1_runs/cf_remote/cf_screen/jobs.json"))
print("rows", len(R), "jobs arms", len(jobs["arms"]), jobs["stage"], jobs["seed_range"], jobs["q"], jobs["cell"], jobs["n"])
names = Counter(r["name"] for r in R)
print("arms in rows", len(names), set(names.values()))
seeds = sorted({r["seed"] for r in R}); print("seeds", len(seeds), seeds[0], seeds[-1], seeds == list(range(7489160, 7489640)))
print("dupes", len(R) - len({(r["name"], r["seed"]) for r in R}))
print("commit", Counter(r["commit"] for r in R)); print("cell", Counter(r["cell"] for r in R)); print("steps", Counter(r["steps"] for r in R)); print("nkeys", Counter(r["nkeys"] for r in R).most_common(6))
print("cell_spec", Counter(r["cell_spec"] for r in R))
# cfg per arm equals the job config
bad = []
for n, c in jobs["arms"].items():
    h = hashlib.sha256(json.dumps(c, sort_keys=True).encode()).hexdigest()
    hs = {r["cfg_sha"] for r in R if r["name"] == n}
    if hs != {h}: bad.append((n, len(hs)))
print("cfg mismatches vs jobs.json (whole job config)", bad[:5], len(bad))
print("perturb per job", Counter(json.dumps(c["ctrl"]["env"]["perturb"], sort_keys=True) for c in jobs["arms"].values()))
print("split", Counter(str(c.get("split")) for c in jobs["arms"].values()), "share/accel keys", Counter(k for c in jobs["arms"].values() for k in c if k not in ("ctrl",)))
# the drawn event per seed equal across arms, and inside the protocol's ranges
ev = defaultdict(set); al = defaultdict(set); vn = defaultdict(set)
for r in R:
    d = r["pert_log"][0]; assert d[0] == "drawn"
    ev[r["seed"]].add((d[1], d[2])); al[r["seed"]].add(r["alks_sha"]); vn[r["seed"]].add(r["veh_n"])
print("seeds with >1 drawn event", sum(len(v) > 1 for v in ev.values()), "alks sets differ", sum(len(v) > 1 for v in al.values()), "veh_n differ", sum(len(v) > 1 for v in vn.values()))
on = np.array([list(v)[0][0] for v in ev.values()]); du = np.array([list(v)[0][1] for v in ev.values()])
print("onset min/max/mean", on.min(), on.max(), on.mean(), "dur", du.min(), du.max(), du.mean())
print("pert_log shapes", Counter(len(r["pert_log"]) for r in R), Counter(tuple(x[1] for x in r["pert_log"][1:]) for r in R))
print("ttc_net == E30+out_E30", sum(r["ttc_net"] != r["E30"] + r["out_E30"] for r in R), "ttc_net == road sum", sum(r["ttc_net"] != r["road_ttc3_sum"] for r in R), "== m_ttc3_all", sum(r["ttc_net"] != r["m_ttc3_all"] for r in R))
for k in ("collisions", "teleports", "m_stuck_n", "m_dropped", "m_capped"):
    c = Counter()
    for r in R:
        if r[k]: c[r["arm"]] += 1
    print(k, "rows>0:", sum(c.values()), dict(c))
c = defaultdict(float)
for r in R: c[r["arm"]] += r["collisions"]
print("collisions total per arm", {a: v for a, v in c.items() if v})
w = np.array([r["wall_s"] for r in R]); print("wall_s mean/max", w.mean(), w.max(), "sum h / 30 workers", w.sum() / 3600 / 30)
print("learner field", Counter((r["arm"], r["learner"]) for r in R if r["learner"]).keys())
print("files per arm (distinct)", {a: len({r["files"] for r in R if r["arm"] == a}) for a in ("w0u250", "MPC-F", "p333")})
print("MPC-F files", {r["files"] for r in R if r["arm"] == "MPC-F"})
print("ctrl_sha per arm distinct", len({(r["arm"], r["ctrl_sha256"]) for r in R}), "distinct ctrl_sha", len({r["ctrl_sha256"] for r in R}))
for a in ("p333", "p222", "p111", "nc", "w0u250"):
    rr = [r for r in R if r["arm"] == a]
    lv = {rd: sum(r["lv"][rd][0] or 0 for r in rr) / max(sum(r["lv"][rd][1] or 0 for r in rr), 1) for rd in ("2", "3", "4", "5")}
    print(a, "tau_on_n>0", sum((r["tau_on_n"] or 0) > 0 for r in rr), "match==n", sum(r["tau_on_match"] == r["tau_on_n"] for r in rr), "mismatch>0", sum((r["tau_mismatch"] or 0) > 0 for r in rr), "level", {k: round(v, 3) for k, v in lv.items()},
          "min/max per-row level road 3", round(min(r["lv"]["3"][0] / r["lv"]["3"][1] for r in rr if r["lv"]["3"][1]), 3) if any(r["lv"]["3"][1] for r in rr) else None)
