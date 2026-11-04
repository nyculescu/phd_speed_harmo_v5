"""V342: upstream travel measured from where X acts, because a limit drop on edge 4 dips all of edge 4 at once. Only cells
upstream of X's start count; a group must touch the 200 m next to it. usage: wave2.py rows.jsonl out.csv"""
import csv
import json
import sys
from collections import defaultdict, deque

import numpy as np

T_N, X_N = 150, 65
EDGE4, BRAKE = 4989.02, 5489.02
ROWS = defaultdict(dict)
ST = {}
for line in open(sys.argv[1]):
    r = json.loads(line)
    ST[(r["name"], r["q"], r["seed"])] = (np.array(r.pop("st_v"), float).reshape(T_N, X_N) / 10.0, np.array(r.pop("st_n"), float).reshape(T_N, X_N))
    ROWS[(r["name"], r["q"])][r["seed"]] = r


def start_of(n):
    return EDGE4 if n.startswith("slow") else BRAKE if n.startswith(("brake", "placebo")) else None


def base_of(n):
    return "p333" if n.startswith("outage") else "none"


def beyond(v, n, v0, n0, x0):
    ok = (n >= 2) & (n0 >= 2) & (v0 > 0)
    mask = np.zeros_like(ok)
    mask[ok] = 1.0 - v[ok] / v0[ok] >= 0.30
    j0 = int(x0 // 100)
    mask[:, j0:] = False
    seen = np.zeros_like(mask)
    best = (0.0, 0.0)
    for t0, x in zip(*np.nonzero(mask)):
        if seen[t0, x]:
            continue
        q, cells = deque([(t0, x)]), []
        seen[t0, x] = True
        while q:
            a, b = q.popleft()
            cells.append((a, b))
            for da in (-1, 0, 1):
                for db in (-1, 0, 1):
                    c, d = a + da, b + db
                    if 0 <= c < T_N and 0 <= d < X_N and mask[c, d] and not seen[c, d]:
                        seen[c, d] = True
                        q.append((c, d))
        if len(cells) < 3 or max(c[1] for c in cells) < j0 - 2:
            continue
        lo = min(c[1] for c in cells)
        r = (j0 - lo) * 100.0
        if r > best[0]:
            t_start, t_far = min(c[0] for c in cells), min(c[0] for c in cells if c[1] == lo)
            best = (float(r), r / max((t_far - t_start) * 10.0, 10.0))
    return best


out = []
for q in sorted({k[1] for k in ROWS}):
    print(f"--- {q:g}")
    null = None
    for n in sorted({k[0] for k in ROWS if k[1] == q and start_of(k[0])}, key=lambda x: (x != "placebo", x)):
        rr = [beyond(*ST[(n, q, s)], *ST[(base_of(n), q, s)], start_of(n)) for s in sorted(ROWS[(n, q)])]
        if n == "placebo":
            null = float(np.percentile([x[0] for x in rr], 95))
        med = float(np.median([x[0] for x in rr]))
        sp = [x[1] for x in rr if x[0] > 0]
        out.append({"name": n, "q": q, "upstream_m": med, "upstream_p90": float(np.percentile([x[0] for x in rr], 90)), "runs_reaching_500m": sum(x[0] >= 500 for x in rr), "wave_speed_ms": float(np.median(sp)) if sp else None, "placebo_p95": null, "wave": med >= 500 and med > null})
        print(n, {k: (round(v, 1) if isinstance(v, float) else v) for k, v in out[-1].items() if k not in ("name", "q")})
with open(sys.argv[2], "w", newline="") as f:
    w = csv.DictWriter(f, list(out[0]))
    w.writeheader()
    w.writerows(out)
A, B = ST[("slow25", 4600.0, 7419743)], ST[("none", 4600.0, 7419743)]
ok = (A[1] >= 2) & (B[1] >= 2)
d = np.zeros_like(A[0])
d[ok] = 1 - A[0][ok] / B[0][ok]
print("dip map slow25 at 4,600, seed 743: rows 600-1,000 s every 40 s after window start, columns x = 3,000 to 6,300 m every 300 m")
print("        " + " ".join(f"{x // 100:>2d}" for x in range(3000, 6400, 300)))
for t in range(300, 700, 40):
    print(f"{300 + t:>6d}s " + " ".join("##" if d[t // 10, x // 100:(x + 300) // 100].max() >= 0.5 else "++" if d[t // 10, x // 100:(x + 300) // 100].max() >= 0.3 else " ." for x in range(3000, 6400, 300)))
