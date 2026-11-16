import json, os, sys, re
lo, hi = 7489160, 7489639
hits = []
n = 0
for root, dirs, files in os.walk(sys.argv[1]):
    if root.startswith(os.path.join(sys.argv[1], "cf_remote")):
        dirs[:] = []; continue
    for f in files:
        if not (f.endswith(".json") or f.endswith(".txt") or f.endswith(".log") or f.endswith(".md")):
            continue
        p = os.path.join(root, f)
        try:
            if os.path.getsize(p) > 50e6: continue
            s = open(p, errors="ignore").read()
        except Exception: continue
        n += 1
        for m in re.finditer(r"7,?48[89],?\d{3}", s):
            v = int(m.group().replace(",", ""))
            if lo <= v <= hi:
                hits.append((p, v)); break
print("files scanned", n)
for h in hits[:40]: print(h)
print("hits", len(hits))
