import json, collections
r0 = None
for line in open("/home/catalin/work/phd/v5b1_runs/measure_s01_remote/rows_s1.jsonl"):
    r = json.loads(line)
    if r["name"] == "B|p333" and r["q"] == 3500.0:
        r0 = r; break
print(sorted(k for k in r0 if not k.startswith("m_"))[:200])
print(sorted(k for k in r0 if k.startswith("m_")))
print("cfg", json.dumps(r0["cfg"])[:600]); print("pert_log", json.dumps(r0.get("pert_log"))[:300]); print(r0.get("commit"), r0.get("steps"))
c = collections.Counter(); k0 = None
for line in open("/home/catalin/work/phd/v5b1_runs/round1_sweep/out/sweep1.jsonl"):
    r = json.loads(line)
    if k0 is None:
        k0 = r; print("sweep keys with m_:", [k for k in r if k.startswith("m_")][:5], "pert_log" in r, json.dumps(r.get("pert_log"))[:300], json.dumps(r["cfg"])[:500])
    pl = r.get("pert_log")
    kind = "none" if not pl else "pert"
    c[(r["name"], r["q"], kind)] += 1
for k in sorted(c):
    if k[0] in ("T|nc", "T|p333") and k[1] in (2500.0, 3500.0, 5250.0): print(k, c[k])
