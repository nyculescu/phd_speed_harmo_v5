import json
from collections import Counter
RUN = "/home/catalin/work/phd/v5b1_runs/cf_remote"
new = {}
for l in open(f"{RUN}/cf_ident/s6_rows.jsonl"):
    r = json.loads(l); new[(r["name"], r["seed"])] = r
print("ident rows", len(new), "arms", len({k[0] for k in new}), "seeds", sorted({k[1] for k in new}), "cells", {k[0].split("|")[0] for k in new})
ref = {}; s6_seeds = Counter(); s6_commit = Counter()
for l in open("/home/catalin/work/phd/v5b1_runs/planb_s56_remote/s6/s6_rows.jsonl"):
    if '"S|' not in l: continue
    r = json.loads(l)
    if r["name"].startswith("S|"): s6_seeds[r["seed"]] += 1
    if (r["name"], r["seed"]) in new: ref[(r["name"], r["seed"])] = r; s6_commit[r.get("commit")] += 1
print("S6 refs found", len(ref), "S6 S seeds", min(s6_seeds), max(s6_seeds), len(s6_seeds), "S6 commit", s6_commit)
PROV = {"commit", "name", "cfg", "ctrl_sha256", "files", "m_st_file", "wall_s"}
DIAGP = ("m_dec_", "lv_sum_", "lv_n_"); DIAG = {"tau_on_n", "tau_on_match", "tau_mismatch"}
def eq(a, b):
    if isinstance(a, dict) and isinstance(b, dict): return set(a) == set(b) and all(eq(a[k], b[k]) for k in a)
    if isinstance(a, list) and isinstance(b, list): return len(a) == len(b) and all(eq(x, y) for x, y in zip(a, b))
    return type(a) == type(b) and a == b or (isinstance(a, (int, float)) and isinstance(b, (int, float)) and not isinstance(a, bool) and float(a) == float(b) and type(a) == type(b))
nt = Counter(); bad = Counter(); dbad = Counter(); onlynew = Counter(); provdiff = Counter()
for k, r in new.items():
    o = ref[k]
    for x in o:
        if x in PROV:
            if not eq(r.get(x), o[x]): provdiff[x] += 1
            continue
        d = x in DIAG or x.startswith(DIAGP)
        if d:
            if not eq(r.get(x), o[x]): dbad[x] += 1
        else:
            nt[k] += 1
            if x not in r or not eq(r[x], o[x]): bad[(k[0], x)] += 1
    for x in r:
        if x not in o: onlynew[x] += 1
print("traffic keys compared per row: min", min(nt.values()), "max", max(nt.values()), "total", sum(nt.values()))
print("traffic mismatches", dict(bad)); print("diagnostic mismatches", dict(dbad)); print("keys only in new rows", dict(onlynew)); print("provenance differing", dict(provdiff))
# MPC-F config vs S6's
a, b = new[("S|MPC-F", 7480400)]["cfg"], ref[("S|MPC-F", 7480400)]["cfg"]
print("MPC-F model new", a["ctrl"]["mpcf"]["model"], "| S6", b["ctrl"]["mpcf"]["model"], "| sha equal", a["ctrl"]["mpcf"]["model_sha256"] == b["ctrl"]["mpcf"]["model_sha256"])
def strip(c):
    c = json.loads(json.dumps(c)); m = c.get("ctrl", {}).get("mpcf"); 
    if m: m.pop("model", None)
    return c
print("configs equal to S6's (MPC-F path aside):", sum(strip(new[k]["cfg"]) == strip(ref[k]["cfg"]) for k in new), "of", len(new))
print("m_dec_entropy_mean largest rel diff", max(abs(new[k]["m_dec_entropy_mean"] - ref[k]["m_dec_entropy_mean"]) / abs(ref[k]["m_dec_entropy_mean"]) for k in new if "m_dec_entropy_mean" in ref[k] and ref[k]["m_dec_entropy_mean"]))
