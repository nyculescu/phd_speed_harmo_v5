"""Acceleration histograms (vehicle-steps per 0.5 m/s2 bin) near the -4.5 threshold, per class and arm: is the -4.5 count a decel-limit artefact?"""
import pickle
from pathlib import Path

import numpy as np

OUT = Path(__file__).resolve().parent
T = pickle.load(open(OUT / "test_rows.pkl", "rb"))
GRP = {"v3w": ("w0u250", "w1u500", "w2u250", "w3u500", "w4u500")}
lab = [f"[{-10 + 0.5 * i:.1f},{-9.5 + 0.5 * i:.1f})" for i in range(30)]
for cell in ("X1", "X2"):
    for g, names in (("nc", ("nc",)), ("v3w", GRP["v3w"]), ("3e", ("3e",)), ("p333", ("p333",))):
        rows = [r for (n, s), r in T.items() if n.split("|")[0] == cell and n.split("|")[1] in names]
        for c in ("car", "alks", "truck"):
            ah = np.sum([r[f"m_ah_{c}"] for r in rows], axis=0) / len(rows)
            print(cell, g, c, " ".join(f"{lab[i]}:{ah[i]:.0f}" for i in range(0, 14)))
        ex = np.mean([r["alks_b45_step"] / 0.1 - sum(r["m_ah_alks"][:11]) for r in rows])
        print(cell, g, "ALKS steps exactly -4.5 per run:", round(ex, 1))
