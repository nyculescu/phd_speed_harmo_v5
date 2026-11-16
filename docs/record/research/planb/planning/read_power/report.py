"""Tables from power_all.json (and check_bin.json if present)."""
import json
from pathlib import Path

import numpy as np

OUT = Path(__file__).resolve().parent
R = json.load(open(OUT / "power_all.json"))
IDX = {(r["cell"], r["scenario"], r["n"]): r for r in R}
NS = (20, 40, 60, 80)
MSHOW = (1, 2, 3, 4, 6, 8, 12, 20, 30)
L = []


def p(cell, sc, n, rule, m):
    return IDX[(cell, sc, n)]["power"][rule][m - 1]


def mc(x, reps):
    return 100 * np.sqrt(max(x * (1 - x), 1e-9) / reps)


L.append("# Power tables (bootstrap from stored X1/X2 and band rows; planning only)\n")
L.append("Rules: W1 delay CI lower bound > 0 against every rule; W2p W1 + close-following point >= -10 % against every rule; "
         "W2ni W1 + close-following CI lower bound > -10 %; W3 W1 + close-following CI lower bound > 0; W4 W3 + close-following "
         "point >= +10 %; W3b W3 + robust braking (events <= -4.0, cars + ALKS) CI lower bound > -10 % against every rule; W3bb W3b + "
         "ALKS past-limit events CI lower bound > -10 %; NC V459-style bar against no control (delay point >= 10 % and CI lower bound > 0, "
         "no close-following harm at 95 %); W3nc W3 and NC; W1any delay CI lower bound > 0 against at least one rule. "
         "All at Bonferroni level 1 - 0.05/m. Percent of simulated studies; Monte Carlo SE at most 1.6 points (1,000 reps) or 2.2 (500).\n")
for cell in ("X1@5300", "X2@5300"):
    L.append(f"\n## {cell}, stored effects (scenario obs, 1,000 simulated studies per n)\n")
    L.append("| rule | n | " + " | ".join(f"m={m}" for m in MSHOW) + " |")
    L.append("|---|---|" + "---|" * len(MSHOW))
    for rule in ("W1", "W2p", "W2ni", "W3", "W4", "W3b", "W3bb", "NC", "W3nc"):
        for n in NS:
            L.append(f"| {rule} | {n} | " + " | ".join(f"{100 * p(cell, 'obs', n, rule, m):.0f}" for m in MSHOW) + " |")
for cell in ("X1@5300", "X2@5300"):
    L.append(f"\n## {cell}, smaller true effects (delay and close-following effects scaled by f; braking as stored)\n")
    L.append("| rule | f | " + " | ".join(f"n={n} m=1/3/4" for n in NS) + " |")
    L.append("|---|---|" + "---|" * len(NS))
    for rule in ("W1", "W3", "W2ni"):
        for sc in ("obs", "f0.75", "f0.5", "f0.25"):
            f = "1.0" if sc == "obs" else sc[1:]
            L.append(f"| {rule} | {f} | " + " | ".join(
                "/".join(f"{100 * p(cell, sc, n, rule, m):.0f}" for m in (1, 3, 4)) for n in NS) + " |")

L.append("\n## False positives under the label-swap (sign-flip) null\n")
L.append("Per-comparison rate: share of simulated studies whose corrected CI lower bound is above 0 (a false 'v3w better'), mean "
         "and max over the 14 rules; nominal one-sided rate 2.5/m %. 'two' = CI excludes 0 on either side (nominal 5/m %).\n")
L.append("| cell | metric | n | " + " | ".join(f"m={m} mean/max (two)" for m in (1, 3, 4, 30)) + " |")
L.append("|---|---|---|" + "---|" * 4)
for cell in ("X1@5300", "X2@5300"):
    for met in ("all_delay", "ttc_net", "ev4_ca"):
        for n in NS:
            r = IDX[(cell, "null", n)]
            js = [j for j, c in enumerate(r["cols"]) if c.endswith("|" + met) and not c.startswith("nc|")]
            cells = []
            for m in (1, 3, 4, 30):
                one = [r["one"][m - 1][j] for j in js]
                two = [r["two"][m - 1][j] for j in js]
                cells.append(f"{100 * np.mean(one):.2f}/{100 * max(one):.2f} ({100 * np.mean(two):.2f})")
            L.append(f"| {cell} | {met} | {n} | " + " | ".join(cells) + " |")
L.append("\nRule-level false positives. Global null (every rule label-swapped): W1 and W3. Least favourable configuration: "
         "lfc_d = only the delay comparison against the closest rule is null, everything else as stored; lfc_t = the same "
         "for close-following. Percent of studies (1,000 reps; lfc_t 500).\n")
L.append("| cell | n | W1 global m=1/3/4 | W3 global m=1/3/4 | W1 lfc_d m=1/3/4 | W3 lfc_d m=1/3/4 | W3 lfc_t m=1/3/4 |")
L.append("|---|---|---|---|---|---|---|")
for cell in ("X1@5300", "X2@5300"):
    for n in NS:
        f = lambda sc, rule: "/".join(f"{100 * p(cell, sc, n, rule, m):.1f}" for m in (1, 3, 4))  # noqa: E731
        L.append(f"| {cell} | {n} | {f('null', 'W1')} | {f('null', 'W3')} | {f('lfc_d', 'W1')} | {f('lfc_d', 'W3')} | "
                 f"{f('lfc_t', 'W3')} |")

L.append("\n## Binding opponents: per-comparison pass rate at m = 3 (stored effects), percent\n")
L.append("| cell | opponent | delay lo>0 n=20/40/60/80 | close-following lo>0 n=20/40/60/80 | braking ev4_ca lo>-10 n=40/60 |")
L.append("|---|---|---|---|---|")
for cell in ("X1@5300", "X2@5300"):
    r0 = IDX[(cell, "obs", 40)]
    opps = sorted({c.split("|")[0] for c in r0["cols"]})
    for o in opps:
        def rate(met, n, m=3):
            r = IDX[(cell, "obs", n)]
            return r["one"][m - 1][r["cols"].index(f"{o}|{met}")]
        L.append(f"| {cell} | {o} | " + "/".join(f"{100 * rate('all_delay', n):.0f}" for n in NS) + " | "
                 + "/".join(f"{100 * rate('ttc_net', n):.0f}" for n in NS) + " | see W3b |")

L.append("\n## Mean 95 % CI width (points of %) of the effect, stored effects\n")
L.append("| cell | metric | opponent with the smallest stored effect | n=20 | n=40 | n=60 | n=80 |")
L.append("|---|---|---|---|---|---|---|")
for cell in ("X1@5300", "X2@5300"):
    r40 = IDX[(cell, "obs", 40)]
    for met in ("all_delay", "ttc_net", "ev4_ca", "ev5_alks"):
        js = [(j, c) for j, c in enumerate(r40["cols"]) if c.endswith("|" + met) and not c.startswith("nc|")]
        j, c = min(js, key=lambda x: r40["pt_mean"][x[0]])
        L.append(f"| {cell} | {met} | {c.split('|')[0]} (mean point {r40['pt_mean'][j]:+.1f}) | "
                 + " | ".join(f"{IDX[(cell, 'obs', n)]['w95_mean'][j]:.1f}" for n in NS) + " |")

L.append("\n## Band and S1 levels (outside the plant's stated intended use, V462(4)); only 3 rules ran there "
         "(p333, os1_15_10, 3E-T), 20 stored seeds; 500 simulated studies\n")
L.append("| level | rule | " + " | ".join(f"n={n} m=1/3/4" for n in NS) + " | FPR W1 global null n=40 m=1/3 |")
L.append("|---|---|" + "---|" * len(NS) + "---|")
for q in (3500, 4500, 5000, 5250, 5500, 6000, 7000):
    cell = f"B@{q}"
    if (cell, "obs", 20) not in IDX:
        continue
    for rule in ("W1", "W3", "W3b", "NC"):
        L.append(f"| {q} | {rule} | " + " | ".join("/".join(f"{100 * p(cell, 'obs', n, rule, m):.0f}" for m in (1, 3, 4))
                                               for n in NS)
                 + f" | {100 * p(cell, 'null', 40, 'W1', 1):.1f}/{100 * p(cell, 'null', 40, 'W1', 3):.1f} |")

cb = OUT / "check_bin.json"
if cb.exists():
    C = json.load(open(cb))
    L.append("\n## Inner bootstrap size check (same simulated studies, B_in 4,000 against 20,000)\n")
    L.append("| cell | scenario | n | reps | rule | m=1 | m=3 | m=4 | m=30 |")
    L.append("|---|---|---|---|---|---|---|---|---|")
    for a, b in zip(C["b4000"], C["b20000"]):
        for rule in ("W1", "W3", "NC"):
            L.append(f"| {a['cell']} | {a['scenario']} | {a['n']} | {a['reps']} | {rule} | "
                     + " | ".join(f"{100 * a['power'][rule][m - 1]:.1f} / {100 * b['power'][rule][m - 1]:.1f}"
                                  for m in (1, 3, 4, 30)) + " |")
        js = [j for j, c in enumerate(a["cols"]) if c.endswith("|all_delay") and not c.startswith("nc|")]
        L.append(f"| {a['cell']} | {a['scenario']} | {a['n']} | {a['reps']} | delay one-sided mean | "
                 + " | ".join(f"{100 * np.mean([a['one'][m - 1][j] for j in js]):.2f} / "
                              f"{100 * np.mean([b['one'][m - 1][j] for j in js]):.2f}" for m in (1, 3, 4, 30)) + " |")

(OUT / "power_tables.md").write_text("\n".join(L) + "\n")
print("\n".join(L))
