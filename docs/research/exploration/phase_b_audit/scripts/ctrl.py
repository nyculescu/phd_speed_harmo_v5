import json
seen = {}
want = {"S|p333", "S|nc", "S|os0_10_10", "S|3E-C_TRUCK", "S|w0u250", "TRUCK|p333", "TRUCK|w0u250", "TRUCK|nc"}
with open("/home/catalin/work/phd/v5b1_runs/planb_s56_remote/s6/s6_rows.jsonl") as h:
    for line in h:
        r = json.loads(line)
        if r["name"] in want and r["name"] not in seen:
            c = r["cfg"].get("ctrl", {})
            seen[r["name"]] = True
            short = {k: (v if len(json.dumps(v)) < 300 else "<long>") for k, v in c.items()}
            print(r["name"], "| ctrl:", json.dumps(short), "| cell_spec:", json.dumps(r.get("cell_spec")), "| capped:", len(r.get("m_capped") or []), "| steps", r["steps"])
        if len(seen) == len(want):
            break
