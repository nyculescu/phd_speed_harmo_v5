import json, sys
f = sys.argv[1]
names = {}
first = None
with open(f) as fh:
    for i, line in enumerate(fh):
        r = json.loads(line)
        names[r["name"]] = names.get(r["name"], 0) + 1
        if first is None:
            first = r
print(len(names), "names")
for n in sorted(names):
    print(" ", n, names[n])
def desc(v):
    if isinstance(v, list):
        return f"list[{len(v)}]" + (f" of {type(v[0]).__name__}" if v else "")
    if isinstance(v, dict):
        return f"dict[{len(v)}] keys={sorted(v)[:12]}"
    return type(v).__name__
for k in sorted(first):
    print(k, desc(first[k]))
