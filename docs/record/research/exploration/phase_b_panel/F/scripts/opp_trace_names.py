import json
J = json.load(open("/home/catalin/work/phd/v5b1_runs/planb_remote/s2/s2_trace.json"))
def walk(d, depth=0, pre=""):
    if isinstance(d, dict):
        print(pre + "dict:", list(d.keys())[:14])
        if depth < 2:
            for k in list(d.keys())[:3]:
                walk(d[k], depth + 1, pre + "  " + str(k) + " -> ")
    elif isinstance(d, list):
        print(pre + f"list[{len(d)}]", str(d[0])[:300] if d else "")
    else:
        print(pre + str(d)[:200])
walk(J)
