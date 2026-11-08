"""p333 climb from the per-vehicle side files; V2V-off churn for v3w and rules (D10)."""
import numpy as np, sys
from base import *
ST = "/home/catalin/work/phd/v5b1_runs/measure_s01_remote/st/"
rows, T = load()
f = np.load(ST + T[("X1", "p333", 5300.0)][7440840]["m_st_file"])
print({k: (f[k].shape, f[k].dtype) for k in f.files})
print("ids sample", f["dec_ids"][:3], f["dec_ids"][-3:])
def climb(cell, q):
    out = []
    for s, r in sorted(T[(cell, "p333", q)].items()):
        z = np.load(ST + r["m_st_file"])
        L = z["dec_level_s"]  # on-seconds per level 0..3, then off
        on = L[:, :4].sum(1)
        out.append((L[:, :3].sum() / len(L), on.sum() / len(L), 1 - L[:, :3].sum() / on.sum(), np.median(L[:, :3].sum(1)), L[:, :3].sum(1).max(),
                    np.bincount(z["dec"][:, 5], minlength=4).tolist(), len(L), (z["dec"][:, 1] - z["dec"][:, 5]).max()))
    a = np.array([o[:5] for o in out])
    print(f"{cell} {q:.0f}: climb s/ALKS med {np.median(a[:,0]):.2f}, on s/ALKS med {np.median(a[:,1]):.1f}, share3 med {np.median(a[:,2]):.4f}, per-veh climb median-of-medians {np.median(a[:,3]):.0f}, max {a[:,4].max():.0f}; first seed last-level counts {out[0][5]} of {out[0][6]}; max excess {max(o[7] for o in out)}")
for cell, q in [("X1", 5300.0), ("X2", 5300.0), ("B", 3500.0), ("B", 4500.0), ("B", 6000.0), ("B", 7000.0)]:
    climb(cell, q)
