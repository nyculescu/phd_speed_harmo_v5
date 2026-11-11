import json, glob, sys
for f in sorted(glob.glob('/home/catalin/work/phd/v5b1_runs/planb_s56_remote/**/*.json', recursive=True))[:60]:
    try:
        j = json.load(open(f))
    except Exception as e:
        continue
    if isinstance(j, dict) and "arms" in j:
        a = j["arms"]
        print(f, len(a), [k for k in j if k != "arms"])
        for n in ("S|p333", "S|os0_10_10", "S|r4a1", "S|z33133", "S|grid_r4a2", "S|grid_z31333", "S|nc", "S|lr1000_10_1"):
            if n in a:
                print("  ", n, json.dumps(a[n])[:700])
        for k in j:
            if k != "arms":
                print("  ", k, json.dumps(j[k])[:300])
        break
