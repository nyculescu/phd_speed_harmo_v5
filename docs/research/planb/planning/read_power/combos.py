"""Study-level power for c new cells, assuming each cell behaves like X1 or like X2 (stored or scaled effects) and cells are
independent (separate seeds). 'any' = W3 in at least one cell at m = c (union over cells); 'all' = W3 in every cell at m = 1
(intersection, no correction)."""
import json
from itertools import product
from pathlib import Path

OUT = Path(__file__).resolve().parent
R = json.load(open(OUT / "power_all.json"))
IDX = {(r["cell"], r["scenario"], r["n"]): r for r in R}
RULE = "W3"


def pw(kind, sc, n, m):
    return IDX[({"X1": "X1@5300", "X2": "X2@5300"}[kind], sc, n)]["power"][RULE][m - 1]


L = ["| cells | mix | effects | n | any cell, m = c | every cell, m = 1 |", "|---|---|---|---|---|---|"]
for c in (2, 3, 4):
    mixes = {"all X1-like": ["X1"] * c, "half X1-like": ["X1"] * (c // 2) + ["X2"] * (c - c // 2), "all X2-like": ["X2"] * c}
    for (name, mix), sc, n in product(mixes.items(), ("obs", "f0.75"), (40, 60, 80)):
        miss, allp = 1.0, 1.0
        for k in mix:
            miss *= 1 - pw(k, sc, n, c)
            allp *= pw(k, sc, n, 1)
        L.append(f"| {c} | {name} | {'stored' if sc == 'obs' else 'x0.75'} | {n} | {100 * (1 - miss):.0f} | {100 * allp:.0f} |")
(OUT / "combos.md").write_text("\n".join(L) + "\n")
print("\n".join(L))
