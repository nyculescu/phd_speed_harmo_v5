import json
D = "/home/catalin/work/phd/v5b1_runs/planb_s34_remote/cmab/TRUCK_ttc/"
checks = [json.loads(l) for l in open(D + "checks.jsonl")]
rows = []
for c in checks:
    for cand in c.get("cands", c.get("candidates", [])):
        rows.append((cand.get("check_loss"), cand.get("name"), c["gen"], cand.get("admissible")))
print("n candidates", len(rows), "distinct", len({r[1] for r in rows}), "admissible", sum(bool(r[3]) for r in rows))
adm = sorted([r for r in rows if r[3]], key=lambda r: (r[0], r[2]))
for r in adm[:10]: print(round(r[0], 2), r[1], r[2])
print("incumbent trace", [(c["gen"], c["incumbent"]["name"], round(c["incumbent"]["check_loss"], 2)) for c in checks])
m = json.load(open(D + "meta.json"))
print({k: m[k] for k in ("cell", "objective", "pool", "check", "pop", "seeds_per_gen", "gens", "cma_seed", "k_check", "loss")})
p = json.load(open(D + "pick.json"))
print("pick keys", list(p.keys())[:12])
print({k: p[k] for k in p if k in ("name", "label", "gen", "check_loss")})
