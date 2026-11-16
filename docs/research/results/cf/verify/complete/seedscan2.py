import os, sys, re, collections
lo, hi = 7489160, 7489639
pat = re.compile(r'(?:"seeds?"\s*:\s*\[?\s*|_s|seed[ =:]+|seeds[ =:]+|[-–]\s?)(7,?48[89],?\d{3})')
fpat = re.compile(r'_s(74\d{5})')
hits = collections.Counter(); ex = {}
nf = 0
for root, dirs, files in os.walk(sys.argv[1]):
    if root.startswith(os.path.join(sys.argv[1], "cf_remote")):
        dirs[:] = []; continue
    for f in files:
        m = fpat.search(f)
        if m and lo <= int(m.group(1)) <= hi:
            top = os.path.relpath(root, sys.argv[1]).split(os.sep)[0]; hits[top+" (filename)"] += 1; ex.setdefault(top+" (filename)", os.path.join(root, f))
        if not f.endswith((".json", ".txt", ".log", ".md", ".jsonl")): continue
        p = os.path.join(root, f)
        try:
            if os.path.getsize(p) > 300e6: continue
            s = open(p, errors="ignore").read()
        except Exception: continue
        nf += 1
        for m in pat.finditer(s):
            v = int(m.group(1).replace(",", ""))
            if lo <= v <= hi:
                top = os.path.relpath(root, sys.argv[1]).split(os.sep)[0]
                hits[top] += 1; ex.setdefault(top, (p, s[max(0, m.start()-80):m.end()+40].replace("\n", " ")))
                break
print("files", nf)
for k, v in hits.most_common(): print(k, v, ex[k])
