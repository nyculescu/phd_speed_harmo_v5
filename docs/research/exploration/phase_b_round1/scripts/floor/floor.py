"""EXPLORATORY estimate: how much of p333's delay at 5,300 remains if every mainline edge ran at its 3,500-veh/h speed."""
import pickle
import numpy as np
T = pickle.load(open("comp.pkl", "rb")); LR = pickle.load(open("lowref.pkl", "rb"))
REF = 100.0 / 3.6
seeds = list(range(7480400, 7480640)); n = len(seeds)
IDX = np.random.default_rng(20261110).integers(0, n, (10_000, n))
LEARN = ["w0u250", "w1u500", "w2u250", "w3u500", "w4u500"]
EDGES = ["1", "2", "3a", "3", "4a", "4", "5"]
OTHER = ["pending_main", "pending_ramp", "pending_ramp2", "ramp1", "ramp2", "junction"]
def arr(cell, arm, key, g):
    return np.array([sum(T[(cell, arm)][s][key].get(g, {}).values()) for s in seeds])
def ci(x):
    b = np.median(x[IDX], axis=1); lo, hi = np.percentile(b, (2.5, 97.5)); return "%.1f [%.1f, %.1f]" % (np.median(x), lo, hi)
sp_p = LR["ref_speed"][("p333", "none")]; sp_n = LR["ref_speed"][("nc", "none")]
FF = 97.35 / 3.6     # harmonic mean of the drawn desired speeds, computed from fleet.py:43-44, :29, :202
for cell in ("S", "TRUCK"):
    print("#####", cell)
    for arm in ("nc", "p333", "v3w"):
        arms = LEARN if arm == "v3w" else [arm]
        vs = {g: np.mean([arr(cell, a, "road_vs", g) for a in arms], axis=0) for g in EDGES + OTHER}
        ds = {g: np.mean([arr(cell, a, "road_dist", g) for a in arms], axis=0) for g in EDGES + OTHER}
        tot = sum(vs[g] - ds[g] / REF for g in EDGES + OTHER)
        print(f" {arm}: per-edge mean speed km/h (sum dist / sum veh-s over 240 seeds): " + ", ".join(f"{e} {ds[e].sum()/vs[e].sum()*3.6:.1f}" for e in EDGES) + f"; ramp1 {ds['ramp1'].sum()/vs['ramp1'].sum()*3.6:.1f}, ramp2 {ds['ramp2'].sum()/vs['ramp2'].sum()*3.6:.1f}")
        if arm == "nc":
            continue
        for label, sp in (("3,500 p333 unperturbed speeds", sp_p), ("3,500 no-control unperturbed speeds", sp_n), ("drawn desired speeds 97.35 km/h", {e: FF for e in EDGES})):
            floor_main = sum(ds[e] * (1.0 / sp[e] - 1.0 / REF) for e in EDGES)
            now_main = sum(vs[e] - ds[e] / REF for e in EDGES)
            rest = sum(vs[g] - ds[g] / REF for g in OTHER)
            share = 100.0 * floor_main / tot
            removable_main = now_main - floor_main
            print(f"   reference = {label}: mainline delay now median {np.median(now_main):.0f}, at reference speeds {np.median(floor_main):.0f} veh-s; share of total all_delay at reference speeds {ci(share)} %; mainline excess over reference {ci(100.0 * removable_main / tot)} % of total = median {np.median(removable_main):.0f} veh-s; off-mainline (origin queues, ramps, junctions) {ci(100.0 * rest / tot)} %")
            if label.startswith("3,500 p333"):
                for e in EDGES:
                    ex = vs[e] - ds[e] / REF - ds[e] * (1.0 / sp[e] - 1.0 / REF)
                    print(f"      edge {e}: excess over reference median {np.median(ex):.0f} veh-s ({100*np.mean(ex)/np.mean(tot):.1f} % of mean total)")
