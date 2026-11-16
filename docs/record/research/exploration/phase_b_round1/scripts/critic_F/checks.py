"""Summarise the stored 3E-C TRUCK search (read only): incumbent per check, candidates, generation medians."""
import json, sys
import numpy as np
D = '/home/catalin/work/phd/v5b1_runs/planb_s34_remote/cmab/TRUCK_ttc/'
meta = json.load(open(D + 'meta.json'))
print("meta:", {k: meta[k] for k in ("cell", "objective", "pool", "check", "pop", "sigma", "seeds_per_gen", "gens", "check_at", "k_check", "cma_seed", "loss", "start")})
pick = json.load(open(D + 'pick.json'))
inc = pick["incumbent"]
print("pick label:", pick["label"], "| incumbent", inc["name"], "found_at", inc.get("found_at"), "check_loss %.2f" % inc["check_loss"], {k: round(v, 2) for k, v in inc["parts"].items() if isinstance(v, (int, float))})
print("incumbent params:", inc["params"])
for line in open(D + 'checks.jsonl'):
    c = json.loads(line)
    i = c["incumbent"]
    cands = c["candidates"]
    adm = [r for r in cands if r["admissible"]]
    print("check gen %3d: %d cands, %d admissible; cand check_loss min %.2f med %.2f; cand ttc_pct %s; cand delay_pct %s | incumbent %s found_at %s loss %.2f ttc %.2f delay %.2f" % (
        c["gen"], len(cands), len(adm), min(r["check_loss"] for r in cands), np.median([r["check_loss"] for r in cands]),
        " ".join("%.1f" % r["parts"]["ttc_pct"] for r in cands), " ".join("%.2f" % r["parts"]["delay_pct"] for r in cands),
        i["name"] if i else None, i.get("found_at") if i else None, i["check_loss"] if i else float("nan"), i["parts"]["ttc_pct"] if i else float("nan"), i["parts"]["delay_pct"] if i else float("nan")))
# generation medians from evals.jsonl without the runs
G = {}
S = {}
for line in open(D + 'evals.jsonl'):
    r = json.loads(line)
    G.setdefault(r["gen"], []).append((r["loss"], r["parts"]["ttc_pct"], r["parts"]["delay_pct"]))
    S[r["gen"]] = (r["seeds"][0], r["seeds"][-1], len(r["seeds"]))
print("generations:", len(G))
for g in sorted(G):
    a = np.array(G[g])
    if g % 5 == 0 or g >= 95:
        print("gen %3d seeds %d..%d (%d): loss min %.2f med %.2f | ttc_pct med %.2f | delay_pct med %.2f | share with delay>1%%: %.2f" % (g, *S[g], a[:, 0].min(), np.median(a[:, 0]), np.median(a[:, 1]), np.median(a[:, 2]), np.mean(a[:, 2] > 1.0)))
# by seed-window phase (windows repeat every 5 generations): median of generation medians in blocks of 10
med = np.array([np.median(np.array(G[g])[:, 0]) for g in sorted(G)])
ttc = np.array([np.median(np.array(G[g])[:, 1]) for g in sorted(G)])
for b in range(0, len(med), 10):
    print("gens %3d-%3d: median of generation-median loss %.2f, ttc_pct %.2f" % (b, b + 9, np.median(med[b:b + 10]), np.median(ttc[b:b + 10])))
