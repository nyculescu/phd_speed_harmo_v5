"""Space-time checks: per-edge jam and speed mix, approach (speed-drop) exposure, same-demand check across cells."""
import json
import sys
from multiprocessing import Pool

import numpy as np

sys.path.insert(0, "/tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/24a0150f-4eb7-443d-8a6d-3d8d8c91d56d/scratchpad/s01/verify_x1_exposure")
from vlib import D, arms_for  # noqa: E402

OUT = "/tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/24a0150f-4eb7-443d-8a6d-3d8d8c91d56d/scratchpad/s01/verify_x1_exposure"
OFF = {"1": 0.0, "2": 3000.0, "3a": 3498.3, "3": 3793.02, "4a": 4987.32, "4": 5282.04, "5": 6278.04, "_end": 6778.04}
EDGES = ["1", "2", "3a", "3", "4a", "4", "5"]
DX, DT, T0 = 50.0, 10.0, 300.0
NX = 136
centre = (np.arange(NX) + 0.5) * DX
EDGE_OF = np.array([max(i for i, e in enumerate(EDGES) if OFF[e] <= c) for c in centre])
VCLS = [(0, 18), (18, 30), (30, 60), (60, 80), (80, 999)]


def periods(cell):
    t = T0 + (np.arange(150) + 0.5) * DT
    if cell == "X1":
        p = np.full(150, "rest", object)
        p[t < 600] = "before"
        for t0 in (600, 1200):
            p[(t >= t0) & (t < t0 + 120)] = "hold"
            p[(t >= t0 + 120) & (t < t0 + 240)] = "after"
    else:
        p = np.full(150, "rest", object)
        p[t < 700] = "before"
        p[(t >= 700) & (t < 880)] = "hold"
        p[(t >= 880) & (t < 1000)] = "after"
    return p


def one(args):
    cell, name, seed = args
    z = np.load(f"{D}/st/{cell}__{name}__5300__{seed}.npz")
    vs, n = z["v"].astype(float), z["n"].astype(float)
    V = np.where(n > 0, 3.6 * vs / np.maximum(n, 1e-9), np.nan)
    occ = n > 0
    out = {}
    per = periods(cell)
    for ei, e in enumerate(EDGES):
        m = EDGE_OF == ei
        Ve, ne = V[:, m], n[:, m]
        for lo, hi in VCLS:
            sel = (Ve >= lo) & (Ve < hi)
            out[f"vs_{e}_{lo}"] = float(ne[sel].sum())
        out[f"vs_{e}"] = float(ne.sum())
        mov = Ve >= 18
        # vehicle-weighted density of moving cells, veh per km over all lanes
        out[f"dens_mov_{e}"] = float((ne[mov] ** 2).sum() / max(ne[mov].sum(), 1) / (DT * DX) * 1000.0)
        for pp in ("before", "hold", "after", "rest"):
            pm = per == pp
            out[f"jam_{e}_{pp}"] = float(ne[pm][Ve[pm] < 30].sum())
    # approach exposure: vehicle-seconds in cells whose next 100 m downstream is >= k km/h slower
    Vd = np.full_like(V, np.nan)
    a1 = V[:, 1:]
    a2 = np.concatenate([V[:, 2:], np.full((150, 1), np.nan)], axis=1)
    Vd[:, :-1] = np.fmin(a1, a2)
    drop = V - Vd
    for k in (10, 20, 30):
        sel = occ & (drop >= k)
        out[f"app{k}"] = float(n[sel].sum())
        for ei, e in enumerate(EDGES):
            out[f"app{k}_{e}"] = float(n[sel & (EDGE_OF == ei)[None, :]].sum())
        for pp in ("before", "hold", "after", "rest"):
            out[f"app{k}_p_{pp}"] = float(n[sel & (per == pp)[:, None]].sum())
    # temporal drop at a fixed place over the next 10 s
    td = V[:-1] - V[1:]
    sel = occ[:-1] & (td >= 20)
    out["tdrop20"] = float(n[:-1][sel].sum())
    out["ms_total"] = float(n.sum())
    out["first30"] = (vs[:30].tobytes(), n[:30].tobytes())
    return cell, name, seed, out


if __name__ == "__main__":
    seeds = list(range(7440840, 7440880))
    jobs = []
    for cell in ("X1", "X2"):
        A = arms_for(cell)
        names = sorted({n for a in ("nc", "v3w", "tail", "sw", "inc", "p333", "3e", "3ex", "os1_15_10") for n in A[a]})
        jobs += [(cell, nm, s) for nm in names for s in seeds]
    with Pool(4) as p:
        R = p.map(one, jobs, chunksize=20)
    store = {}
    first = {}
    for cell, name, seed, out in R:
        first[(cell, name, seed)] = out.pop("first30")
        store[f"{cell}|{name}|{seed}"] = out
    # same-demand check: X1 nc vs X2 nc, first 300 s after warm-up (before either slowdown)
    same = sum(first[("X1", "nc", s)] == first[("X2", "nc", s)] for s in seeds)
    diffs = []
    for s in seeds:
        a = np.frombuffer(first[("X1", "nc", s)][1]); b = np.frombuffer(first[("X2", "nc", s)][1])
        diffs.append(float(np.abs(a - b).max()))
    # also an arm with control from t=300: v3w learner w0u250
    same_w = sum(first[("X1", "w0u250", s)] == first[("X2", "w0u250", s)] for s in seeds)
    # and a different seed as a contrast
    diff_seed = float(np.abs(np.frombuffer(first[("X1", "nc", seeds[0])][1]) - np.frombuffer(first[("X1", "nc", seeds[1])][1])).max())
    print(f"same-demand: X1 nc vs X2 nc identical first-300-s field in {same}/40 seeds; max|dn| {max(diffs)}; w0u250 identical {same_w}/40; different seeds max|dn| {diff_seed}")
    json.dump({"store": store, "same_nc": same, "same_w0": same_w}, open(f"{OUT}/v2_st.json", "w"))
