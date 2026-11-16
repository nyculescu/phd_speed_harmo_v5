"""EXPLORATORY, read-only: configuration of a few stored S6 arms in cell S; prints small fields only."""
import json
ROWS = "/home/catalin/work/phd/v5b1_runs/planb_s56_remote/s6/s6_rows.jsonl"
want = {"S|p333", "S|os0_10_10", "S|z33133", "S|r4a1", "S|nc", "S|lr400_16_1"}
seen = {}
names = {}
for line in open(ROWS):
    i = line.find('"name": "')
    name = line[i + 9:line.index('"', i + 9)]
    names[name.split("|")[0]] = names.get(name.split("|")[0], 0) + 1
    if name in want and name not in seen:
        r = json.loads(line)
        seen[name] = 1
        c = r.get("cfg", {})
        print(name, "seed", r["seed"], "q", r.get("q"), "| ctrl:", json.dumps(c.get("ctrl"))[:300], "| len lv", len(r.get("lv", [])), "| len m_dec_want", len(r.get("m_dec_want", [])), "len m_dec_level_s", len(r.get("m_dec_level_s", [])))
        if name == "S|p333":
            print("   keys with 'lv' or 'tau' or 'stuck' or 'end_stop':", sorted(k for k in r if k.startswith(("lv", "tau", "m_stuck", "end_stop", "m_dec")))[:40])
            print("   lv", r["lv"], "m_dec_want", r["m_dec_want"], "m_dec_level_s", r["m_dec_level_s"], "tau_mismatch", r.get("tau_mismatch"))
            print("   m_minute keys:", sorted(r["m_minute"].keys())[:40])
            print("   m_road_vs groups:", sorted(r["m_road_vs"].keys()))
print("cells:", names)
