"""EXPLORATORY, read-only: stuck rows, collisions, flow in stored S rows."""
import pickle, sys
import numpy as np
T = pickle.load(open(sys.argv[1], "rb"))
seeds = sorted(T["S|p333"])
for cond in ("S", "TRUCK"):
    for a in ("p333", "nc", "os0_10_10", "r4a1", "z33133", "grid_r4a2"):
        nm = f"{cond}|{a}"
        st = np.array([T[nm][s]["stuck"] for s in seeds], float)
        col = np.array([T[nm][s]["col"] for s in seeds], float)
        afm = np.array([T[nm][s]["afm"] if T[nm][s]["afm"] is not None else np.nan for s in seeds], float)
        pas = np.array([T[nm][s]["passed"] for s in seeds], float)
        P = np.array([T[f"{cond}|p333"][s]["passed"] for s in seeds], float)
        print(f"{nm:18s} rows with stuck>0: {int((st > 0).sum())} (seeds {[s for s, x in zip(seeds, st) if x > 0][:5]}) collisions mean {col.mean():.3f} rows>0 {int((col > 0).sum())}; full-emergency moving mean {np.nanmean(afm):.2f}; passed median {np.median(pas):.0f}; flow vs p333 % {100 * np.median(pas - P) / np.median(P):+.2f}")
