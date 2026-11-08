"""(d) ASCII space-time maps: seed-median of the cell speed (km/h), cells pooled to 30 s x 100 m, for nc, v3w (the 5 learners' sums
pooled per seed) and 3E-T, cell X1 or X2, and the median paired difference v3w - nc. One character per cell: speed // 10 (9 = 90+),
'.' = no vehicle. Difference map: '+' v3w faster by >= 5 km/h, '#' >= 15 km/h faster, '-' slower by >= 5, '=' slower by >= 15."""
import pickle
import sys
from pathlib import Path

import numpy as np

OUT = Path(__file__).resolve().parent
ST = Path("/home/catalin/work/phd/v5b1_runs/measure_s01_remote/st")
rows = pickle.load(open(OUT / "test_rows.pkl", "rb"))
cell = sys.argv[1] if len(sys.argv) > 1 else "X1"
V3W = ["w0u250", "w1u500", "w2u250", "w3u500", "w4u500"]
X0, X1_, TB, XB = 3500.0, 6400.0, 3, 2     # x range (m), time pooling (bins of 10 s), space pooling (cells of 50 m)
j0, j1 = int(X0 // 50), int(X1_ // 50)
seeds = sorted({s for (n, s) in rows if n == f"{cell}|nc"})


def field(names, s):
    v = n = 0
    for a in names:
        f = np.load(ST / rows[(f"{cell}|{a}", s)]["m_st_file"])
        v, n = v + f["v"].astype(float), n + f["n"].astype(float)
    v, n = v[:, j0:j1], n[:, j0:j1]
    nt, nx = v.shape[0] // TB, v.shape[1] // XB
    v = v[:nt * TB, :nx * XB].reshape(nt, TB, nx, XB).sum((1, 3))
    n = n[:nt * TB, :nx * XB].reshape(nt, TB, nx, XB).sum((1, 3))
    with np.errstate(invalid="ignore", divide="ignore"):
        return np.where(n > 0, 3.6 * v / n, np.nan)


F = {k: np.array([field(names, s) for s in seeds]) for k, names in (("nc", ["nc"]), ("v3w", V3W), ("3e", ["3e"]))}
M = {k: np.nanmedian(x, axis=0) for k, x in F.items()}
D = np.nanmedian(F["v3w"] - F["nc"], axis=0)
xs = X0 + 100.0 * np.arange(M["nc"].shape[1])
print(f"cell {cell}; columns = 100 m from {X0:.0f} m; rows = 30 s from 300 s. Edges: 3a 3498, 3 3793, 4a 4987, 4 5282, 5 6278 m.")
marks = "".join("|" if any(abs(x - e) < 50 for e in (3498.3, 3793.0, 4987.3, 5282.0, 6278.0)) else " " for x in xs)
print("        " + "  ".join(f"{'':{len(marks)}s}" for _ in range(0)) + f"{'nc':<{len(marks) + 2}s}{'v3w':<{len(marks) + 2}s}{'3E-T':<{len(marks) + 2}s}v3w - nc")
print("        " + "  ".join([marks] * 4))
for i in range(M["nc"].shape[0]):
    t = 300 + 30 * i
    def row(A):
        return "".join("." if np.isnan(x) else str(min(int(x // 10), 9)) for x in A[i])
    def drow():
        return "".join("." if np.isnan(x) else "#" if x >= 15 else "+" if x >= 5 else "=" if x <= -15 else "-" if x <= -5 else " " for x in D[i])
    print(f"{t:5d}s  {row(M['nc'])}  {row(M['v3w'])}  {row(M['3e'])}  {drow()}")
