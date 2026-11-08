"""Merge-1 area close-following (b_env E30: lanes 2_0 tail, 3a_0, 3a_1, 3_0 head) against the rest of the network (out_E30)."""
import json

import numpy as np

import lib

T = lib.load()
out = {}
for cell in ("X1", "X2"):
    nc = T[(f"{cell}|nc", lib.Q)]
    for a in ("v3w", "tail", "sw", "baseline-v3", "3E-T"):
        A = lib.arm_mean(T, [f"{cell}|{n}" for n in lib.arms(cell)[a]])
        out[f"{cell}|{a}"] = {k: {"nc_med": float(np.median([nc[s][k] for s in nc])), "diff_mean": [round(x, 1) for x in lib.ci(lib.paired(A, nc, k), np.mean)]}
                              for k in ("E30", "out_E30")}
json.dump(out, open(lib.HERE / "merge1.json", "w"), indent=1)
for k, v in out.items():
    print(k, v)
