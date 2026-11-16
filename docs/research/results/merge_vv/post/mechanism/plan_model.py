"""Post hoc: the plan's pre-data model (merge-area counts scaled by one factor k in all arms) applied to the 300-m rows here,
with 'rest' kept (as the plan's table assumed, to my reading) and with 'rest' scaled too; C-D5 points only."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from analyze import tables, V3W, RULES  # noqa: E402

T = tables(pd.read_pickle(sys.argv[1]))["L300"]


def edge(r, k, scale_rest, drop_e1=False):
    def tot(a):
        x = T[a]
        return (k * x["merge"] + (k if scale_rest else 1.0) * x["rest"] + (0.0 if drop_e1 else 1.0) * x["e1"]).to_numpy()
    R = tot(r)
    m = np.median(R)
    return round(float(np.mean([np.median(-(tot(w) - R) / m * 100) for w in V3W])), 2)


for r in RULES:
    for k in (1.0, 0.34, 0.2, 0.1, 0.06, 0.02):
        print(r, k, "rest kept:", edge(r, k, False), "no e1:", edge(r, k, False, True), "| rest scaled too:", edge(r, k, True), "no e1:", edge(r, k, True, True))
