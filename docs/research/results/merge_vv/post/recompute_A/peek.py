import json, sys
p = sys.argv[1]
with open(p) as f:
    line = f.readline()
r = json.loads(line)
def show(d, pre="", depth=0):
    for k, v in d.items():
        if isinstance(v, dict):
            print(f"{pre}{k}: dict({len(v)})")
            if depth < 2 and len(v) < 60:
                show(v, pre + "  ", depth + 1)
        elif isinstance(v, list):
            print(f"{pre}{k}: list({len(v)}) first={str(v[:3])[:80]}")
        else:
            print(f"{pre}{k}: {str(v)[:80]}")
show(r)
