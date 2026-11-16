import json, io
from collections import Counter
import numpy as np
RUN = "/home/catalin/work/phd/v5b1_runs/cf_remote/cf_smoke"
A = {r["name"]: r for r in map(json.loads, open(f"{RUN}/a/s6_rows.jsonl"))}
B = {r["name"]: r for r in map(json.loads, open(f"{RUN}/b/s6_rows.jsonl"))}
print("a", len(A), "b", len(B), "same names", set(A) == set(B), "seeds", {r["seed"] for r in A.values()} | {r["seed"] for r in B.values()}, "commits", {r["commit"] for r in A.values()} | {r["commit"] for r in B.values()})
print("extra arms beyond the 31:", sorted(n for n in A if "~" in n))
j = lambda v: json.dumps(v, sort_keys=True)
skip = {"cfg", "m_st_file", "commit", "wall_s"}
d = {n: [k for k in set(A[n]) | set(B[n]) if k not in skip and j(A[n].get(k)) != j(B[n].get(k))] for n in A}
print("T3 replay: arms with any differing key", {n: v for n, v in d.items() if v}, "| keys compared per arm min", min(len(set(A[n]) - skip) for n in A))
nd = 0
for n in A:
    fa, fb = f"{RUN}/a/st/{A[n]['m_st_file']}", f"{RUN}/b/st/{B[n]['m_st_file']}"
    with np.load(fa) as za, np.load(fb) as zb:
        if set(za.files) != set(zb.files) or any(not np.array_equal(za[k], zb[k]) for k in za.files): nd += 1
print("side files differing a vs b:", nd, "of", len(A))
def split_key(k): return k in ("c1_t0", "wall_s") or k.startswith(("b45_step_g_", "fuel_g_"))
tskip = skip | {"name", "arm", "learner", "ctrl_sha256", "files"}
for m, n in [("E30|p333", "E30|p333~untraced"), ("E30|p111", "E30|p111~untraced"), ("E30|w0u250", "E30|w0u250~untraced"), ("E30|MPC-F", "E30|MPC-F~untraced"), ("E30|nc", "E30|nc~untraced"), ("E30|nc~trace", "E30|nc~untraced")]:
    ks = [k for k in set(A[m]) | set(A[n]) if k not in tskip and j(A[m].get(k)) != j(A[n].get(k))]
    print("twin", m, "vs", n, "differing keys:", sorted(ks)[:12], "| not split-own:", sorted(k for k in ks if not split_key(k))[:12], "| split flags", A[m]["cfg"].get("split"), A[n]["cfg"].get("split"))
print("trace job keys", {k: v for k, v in A["E30|nc~trace"]["cfg"].items() if k not in ("ctrl", "geom")}.keys(), [k for k in A["E30|nc~trace"] if k not in A["E30|nc"]][:10])
for n in ("E30|p333", "E30|p111", "E30|p222", "E30|nc", "E30|w0u250", "E30|MPC-F", "E30|3E-C_TRUCK"):
    r = A[n]; print(n, "delay", round(r["all_delay"]), "ttc_net", r["ttc_net"], "pert", r["pert_log"][0][1:], "tau n/match/mis", r.get("tau_on_n"), r.get("tau_on_match"), r.get("tau_mismatch"))
