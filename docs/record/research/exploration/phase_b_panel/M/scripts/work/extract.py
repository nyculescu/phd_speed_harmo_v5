"""EXPLORATORY: per-run delay parts from the stored S6 rows (read-only). One pass, scalars only."""
import json, pickle
ROWS = '/home/catalin/work/phd/v5b1_runs/planb_s56_remote/s6/s6_rows.jsonl'
REF = 100.0 / 3.6
T, cfg = {}, {}
for line in open(ROWS):
    r = json.loads(line)
    cell, arm = r["name"].split("|", 1)
    vs = {g: sum(p.values()) for g, p in r["m_road_vs"].items()}
    ds = {g: sum(p.values()) for g, p in r["m_road_dist"].items()}
    dl = {g: vs[g] - ds.get(g, 0.0) / REF for g in vs}
    rate = lambda g: dl[g] / max(ds[g] / 1000.0, 1e-9)
    exc1 = dl["3a"] - rate("2") * ds["3a"] / 1000.0 + dl["pending_ramp"]
    exc2 = dl["4a"] - rate("3") * ds["4a"] / 1000.0 + dl["pending_ramp2"]
    T.setdefault((cell, arm), {})[r["seed"]] = dict(all_delay=r["all_delay"], passed=r["passed"], end_stop=r["end_stop"], end_stop2=r["end_stop2"],
        f2=dl["4a"] + dl["ramp2"] + dl["pending_ramp2"], d4a=dl["4a"], d3=dl["3"], ramp2=dl["ramp2"] + dl["pending_ramp2"], exc1=exc1, exc2=exc2,
        tau_on_n=r.get("tau_on_n"), tau_on_match=r.get("tau_on_match"), tau_mismatch=r.get("tau_mismatch"), planned=r.get("m_planned_window"))
    cfg[arm] = json.dumps({k: v for k, v in r["cfg"].get("ctrl", {}).items()})[:300]
pickle.dump((T, cfg), open("parts.pkl", "wb"))
print(len(T), sorted({c for c, _ in T}), sorted({a for _, a in T}))
