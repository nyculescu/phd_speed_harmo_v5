"""EXPLORATORY: arm names and levels in stored rows (read-only)."""
import json, sys
from collections import Counter
for path in sys.argv[1:]:
    c = Counter(); keys = None; cfg = {}
    with open(path) as f:
        for line in f:
            r = json.loads(line)
            c[(r["name"], r.get("q"))] += 1
            if keys is None:
                keys = sorted(r)
            cfg.setdefault(r["name"], json.dumps(r.get("cfg", {}).get("ctrl"))[:200])
    print(path, len(c))
    names = sorted({n for n, _ in c})
    print(" names:", names[:80])
    print(" levels:", sorted({q for _, q in c}), "counts:", Counter(c.values()))
    print(" has road keys:", [k for k in keys if k.startswith("m_road") or k in ("end_stop2", "all_delay", "tau_on_n", "tau_on_match", "tau_mismatch")])
    for n in names[:6]:
        print("  ", n, cfg[n])
