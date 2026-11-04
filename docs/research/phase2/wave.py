"""V341 rule for the wave check. A cell is dipped if its mean speed is at least 30 % below the paired run without X; reach is
the upstream travel of a connected group of dipped cells. A wave: median reach at least 500 m and above the placebo's 95th
percentile. With cost: fleet fuel per km at least 3 % worse, CI excluding 0. usage: wave.py rows.jsonl out.csv"""
import csv
import json
import sys
from collections import defaultdict, deque

import numpy as np

T_N, X_N = 150, 65
DIP, MIN_N, REACH_M, FUEL_PCT = 0.30, 2, 500.0, 3.0
M = (("flow", "passed", 1), ("delay", "delay", -1), ("p95", "delay_p95", -1), ("ramp", "delay_ramp", -1), ("fuel", "fuel_km", -1), ("ttc", "ttc_net", -1), ("brake", "brake_net", -1), ("hard", "b45_net", -1), ("jerk", "jerk_vs", -1))
ROWS = defaultdict(dict)
ST = {}


def reach(v, n, v0, n0):
    """Largest upstream travel, in m, and that group's duration, in s."""
    ok = (n >= MIN_N) & (n0 >= MIN_N) & (v0 > 0)
    mask = np.zeros_like(ok)
    mask[ok] = 1.0 - v[ok] / v0[ok] >= DIP
    seen = np.zeros_like(mask)
    best = (0.0, 0.0)
    for t0, x0 in zip(*np.nonzero(mask)):
        if seen[t0, x0]:
            continue
        q, cells = deque([(t0, x0)]), []
        seen[t0, x0] = True
        while q:
            t, x = q.popleft()
            cells.append((t, x))
            for dt in (-1, 0, 1):
                for dx in (-1, 0, 1):
                    a, b = t + dt, x + dx
                    if 0 <= a < T_N and 0 <= b < X_N and mask[a, b] and not seen[a, b]:
                        seen[a, b] = True
                        q.append((a, b))
        if len(cells) < 3:
            continue
        ts = [c[0] for c in cells]
        first = max(c[1] for c in cells if c[0] == min(ts))
        r = (first - min(c[1] for c in cells)) * 100.0
        if r > best[0]:
            best = (float(r), (max(ts) - min(ts)) * 10.0)
    return best


for line in open(sys.argv[1]):
    r = json.loads(line)
    ST[(r["name"], r["q"], r["seed"])] = (np.array(r.pop("st_v"), float).reshape(T_N, X_N) / 10.0, np.array(r.pop("st_n"), float).reshape(T_N, X_N))
    r["jerk_vs"] = r["jerk"] / max(r["vs"], 1)
    ROWS[(r["name"], r["q"])][r["seed"]] = r


def base_of(name):
    return "p333" if name.startswith("outage") else "none"


REACH = {}
for (n, q), A in ROWS.items():
    if n in ("none", "p333"):
        continue
    REACH[(n, q)] = [reach(*ST[(n, q, s)], *ST[(base_of(n), q, s)]) for s in sorted(A)]
out = []
for q in sorted({k[1] for k in ROWS}):
    null = float(np.percentile([x[0] for x in REACH[("placebo", q)]], 95))
    print(f"--- {q:g}: placebo reach median {np.median([x[0] for x in REACH[('placebo', q)]]):.0f} m, p95 {null:.0f} m; no control delay {np.median([r['delay'] for r in ROWS[('none', q)].values()]):.1f} s, fuel {np.median([r['fuel_km'] for r in ROWS[('none', q)].values()]) / 1000:.1f} g/km")
    for n in sorted({k[0] for k in REACH if k[1] == q}, key=lambda x: (x[:4], x)):
        A, B = ROWS[(n, q)], ROWS[(base_of(n), q)]
        ds = sorted(set(A) & set(B))
        s = {"name": n, "q": q, "n": len(ds), "collisions": sum(A[k]["collisions"] for k in ds), "reach_m": float(np.median([x[0] for x in REACH[(n, q)]])), "reach_p90": float(np.percentile([x[0] for x in REACH[(n, q)]], 90)), "duration_s": float(np.median([x[1] for x in REACH[(n, q)]])), "placebo_p95": null}
        for lab, key, sign in M:
            ref = max(float(np.median([B[k][key] for k in ds])), 1e-9)
            d = np.array([sign * (A[k][key] - B[k][key]) / ref * 100 for k in ds])
            rng = np.random.default_rng(20261103)
            lo, hi = np.percentile(np.median(d[rng.integers(0, len(d), (20000, len(d)))], axis=1), [2.5, 97.5])
            s[lab], s[lab + "_lo"], s[lab + "_hi"] = round(float(np.median(d)), 1), round(float(lo), 1), round(float(hi), 1)
        s["wave"] = bool(s["reach_m"] >= REACH_M and s["reach_m"] > null)
        s["cost"] = bool(s["fuel"] <= -FUEL_PCT and s["fuel_hi"] < 0)
        out.append(s)
        print(f" {n}: reach {s['reach_m']:.0f} m (p90 {s['reach_p90']:.0f}), {s['duration_s']:.0f} s, coll {s['collisions']}, wave {s['wave']}, cost {s['cost']} | " + " ".join(f"{lab} {s[lab]:+.1f}[{s[lab + '_lo']:+.1f},{s[lab + '_hi']:+.1f}]" for lab, _, _ in M))
with open(sys.argv[2], "w", newline="") as f:
    w = csv.DictWriter(f, list(out[0]))
    w.writeheader()
    w.writerows(out)
