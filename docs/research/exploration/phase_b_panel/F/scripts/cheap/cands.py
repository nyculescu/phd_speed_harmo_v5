import json
D = "/home/catalin/work/phd/v5b1_runs/planb_s34_remote/cmab/TRUCK_ttc/"
checks = [json.loads(l) for l in open(D + "checks.jsonl")]
print("check record keys:", list(checks[0]))
c0 = checks[0]
for k, v in c0.items():
    if isinstance(v, list): print(k, "list", len(v), list(v[0]) if v and isinstance(v[0], dict) else v[:3])
    elif isinstance(v, dict): print(k, "dict", list(v))
    else: print(k, v)
rows = []
for c in checks:
    for cand in c.get("cands", c.get("candidates", [])):
        rows.append((cand.get("check_loss"), cand.get("name"), c["gen"], cand.get("admissible"), cand.get("parts", {}).get("ttc_pct"), cand.get("parts", {}).get("delay_pct")))
print("n candidates", len(rows), "distinct names", len({r[1] for r in rows}))
rows.sort(key=lambda r: r[0])
for r in rows[:14]: print(r)
print("admissible:", sum(bool(r[3]) for r in rows))
