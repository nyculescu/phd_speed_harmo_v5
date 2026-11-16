import json, sys, os, collections, datetime
O = sys.argv[1]
for f in ["stage0a.jsonl", "stage0b.jsonl", "stage0c.jsonl"]:
    p = os.path.join(O, "stage0", f)
    rows = [json.loads(l) for l in open(p) if l.strip()]
    keys = set().union(*[r.keys() for r in rows])
    tk = [k for k in keys if any(s in k.lower() for s in ("time", "commit", "code", "pid", "host", "stamp", "date"))]
    print(f, len(rows), "time/code-like keys:", sorted(tk))
    for k in tk:
        vals = [r.get(k) for r in rows]
        if all(isinstance(v, (int, float)) for v in vals if v is not None):
            nums = [v for v in vals if v is not None]
            print("  ", k, "min", min(nums) if nums else None, "max", max(nums) if nums else None)
        else:
            c = collections.Counter(str(v)[:40] for v in vals)
            print("  ", k, "distinct", len(c), c.most_common(3))
print("mtimes:")
for f in sorted(os.listdir(os.path.join(O, "stage0"))):
    p = os.path.join(O, "stage0", f)
    print(" ", f, datetime.datetime.fromtimestamp(os.path.getmtime(p)))
