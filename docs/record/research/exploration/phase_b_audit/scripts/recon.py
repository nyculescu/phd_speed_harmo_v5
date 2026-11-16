"""(B) Check what all_delay measures: rebuild it from other stored fields. EXPLORATORY."""
import pickle, numpy as np
T = pickle.load(open("s6.pkl", "rb"))
REF = 100.0 / 3.6
PEND = ("pending_main", "pending_ramp", "pending_ramp2")
def parts(r):
    vs = {g: sum(x.values()) for g, x in r["road_vs"].items()}
    ds = {g: sum(x.values()) for g, x in r["road_dist"].items()}
    return vs, ds
def recon(r):
    vs, ds = parts(r)
    o = {}
    o["N"] = r["N"]; o["sum_road_vs"] = sum(vs.values()); o["res_N"] = r["N"] - sum(vs.values())
    o["pend_vs"] = sum(vs.get(g, 0.0) for g in PEND); o["N_minus_vs"] = r["N"] - r["vs"]
    o["net_vs_1hz"] = r["vs"]; o["net_vs_step"] = 0.1 * (r["m_n_alks"] + r["m_n_car"] + r["m_n_truck"])
    o["dist_step"] = r["dist_step"]; o["sum_class_dist"] = r["m_dist_m_alks"] + r["m_dist_m_car"] + r["m_dist_m_truck"]
    o["res_dist_class"] = o["dist_step"] - o["sum_class_dist"]
    o["dist_1hz"] = r["dist"]; o["sum_road_dist"] = sum(ds.values()); o["res_dist_road"] = r["dist"] - sum(ds.values())
    o["all_delay"] = r["all_delay"]
    o["A_formula"] = r["N"] - r["dist_step"] / REF
    o["B_road_1hz"] = sum(vs.values()) - sum(ds.values()) / REF
    o["C_class_step"] = o["net_vs_step"] + o["pend_vs"] - o["sum_class_dist"] / REF
    o["delay_s"] = r["delay_s"]
    for k in ("A_formula", "B_road_1hz", "C_class_step"):
        o["res_" + k] = r["all_delay"] - o[k]
    done = r["finished_pct"] / 100.0 * r["m_planned_window"]
    o["planned"] = r["m_planned_window"]; o["done"] = done; o["own_ref_finished_total"] = r["delay"] * done
    o["passed"] = r["passed"]; o["arrived"] = r["arrived"]
    return o
for cell, seed in (("S", 7480400), ("TRUCK", 7480400), ("S", 7480517)):
    print(f"\n## cell {cell} seed {seed}")
    rows = {a: recon(T[(cell, a)][seed]) for a in ("p333", "w0u250", "nc")}
    for k in rows["p333"]:
        print(f"{k:24s} " + "  ".join(f"{a} {rows[a][k]:14.2f}" for a in rows))
print("\n## residuals over all extracted S6 runs (11 arms x 2 cells x 240 seeds)")
R = {k: [] for k in ("res_N", "res_dist_class", "res_dist_road", "res_A_formula", "res_B_road_1hz", "res_C_class_step")}
extra = []
n = 0
for key, d in T.items():
    for s, r in d.items():
        o = recon(r); n += 1
        for k in R:
            R[k].append(o[k])
        extra.append((o["N_minus_vs"] - o["pend_vs"], o["net_vs_1hz"] - o["net_vs_step"], (r["all_delay"] - r["delay_s"])))
print("runs", n)
for k, v in R.items():
    v = np.array(v); print(f"{k:20s} min {v.min():+.3f} median {np.median(v):+.3f} max {v.max():+.3f} mean|.| {np.abs(v).mean():.3f}")
e = np.array(extra)
for i, nm in enumerate(("(N - vs) - pending groups", "net veh-s 1 Hz - step", "all_delay - delay_s (step vs 1-Hz distance)")):
    print(f"{nm:45s} min {e[:, i].min():+.3f} median {np.median(e[:, i]):+.3f} max {e[:, i].max():+.3f}")
