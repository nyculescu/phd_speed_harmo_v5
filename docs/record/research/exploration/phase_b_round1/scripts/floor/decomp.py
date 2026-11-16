"""EXPLORATORY decomposition of all_delay from stored S6 rows. Paired seeds, median of paired differences, 95 % percentile bootstrap, 10,000 resamples, rng 20261110."""
import pickle
import numpy as np
T = pickle.load(open("comp.pkl", "rb"))
REF = 100.0 / 3.6
seeds = list(range(7480400, 7480640)); n = len(seeds)
IDX = np.random.default_rng(20261110).integers(0, n, (10_000, n))
LEARN = ["w0u250", "w1u500", "w2u250", "w3u500", "w4u500"]
def md(d):
    b = np.median(d[IDX], axis=1); lo, hi = np.percentile(b, (2.5, 97.5))
    return "%+.0f [%+.0f, %+.0f]" % (np.median(d), lo, hi)
def sc(cell, arm, k):
    return np.array([np.nan if T[(cell, arm)][s][k] is None else float(T[(cell, arm)][s][k]) for s in seeds])
GROUPS = ["pending_main", "pending_ramp", "pending_ramp2", "ramp1", "ramp2", "1", "2", "3a", "3", "4a", "4", "5", "junction"]
def comp(cell, arm, per=None):
    out = {g: np.zeros(n) for g in GROUPS}; vs = {g: np.zeros(n) for g in GROUPS}
    for i, s in enumerate(seeds):
        r = T[(cell, arm)][s]
        for g in GROUPS:
            v = r["road_vs"].get(g, {}); d = r["road_dist"].get(g, {})
            ks = v.keys() if per is None else [per]
            a = sum(v.get(k, 0.0) for k in ks); b = sum(d.get(k, 0.0) for k in ks)
            out[g][i] = a - b / REF; vs[g][i] = a
    return out, vs
def pooled(f):
    xs = [f(l) for l in LEARN]
    if isinstance(xs[0], tuple):
        return tuple({g: np.mean([x[j][g] for x in xs], axis=0) for g in GROUPS} for j in range(2))
    return np.mean(xs, axis=0)
for cell in ("S", "TRUCK"):
    print("\n#####", cell)
    C = {a: comp(cell, a) for a in ("nc", "p333", "os0_10_10")}
    C["v3w"] = pooled(lambda l: comp(cell, l))
    A = {a: sc(cell, a, "all_delay") for a in ("nc", "p333", "os0_10_10")}; A["v3w"] = pooled(lambda l: sc(cell, l, "all_delay"))
    Nn = {a: sc(cell, a, "N") for a in ("nc", "p333", "os0_10_10")}; Nn["v3w"] = pooled(lambda l: sc(cell, l, "N"))
    for a in ("nc", "p333", "v3w"):
        tot = sum(C[a][0][g] for g in GROUPS); tv = sum(C[a][1][g] for g in GROUPS)
        print(f"{a}: all_delay median {np.median(A[a]):.0f} mean {np.mean(A[a]):.0f}; sum of components median {np.median(tot):.0f}; max |all_delay - sum| {np.max(np.abs(A[a]-tot)):.0f}; N median {np.median(Nn[a]):.0f}; max |N - sum vs| {np.max(np.abs(Nn[a]-tv)):.0f}")
    print("component | nc median (mean) | p333 median (mean) | v3w median (mean) | p333 share of its mean total % | paired p333 - v3w median [CI] | paired nc - p333")
    tp = np.mean(sum(C["p333"][0][g] for g in GROUPS))
    agg = {"origin queue main": ["pending_main"], "origin queues ramps": ["pending_ramp", "pending_ramp2"], "ramp roads": ["ramp1", "ramp2"], "upstream 1+2": ["1", "2"], "merge 1 (3a)": ["3a"], "between (3)": ["3"], "merge 2 (4a)": ["4a"], "downstream 4+5": ["4", "5"], "junction": ["junction"]}
    for nm, gs in list({g: [g] for g in GROUPS}.items()) + [("--", [])] + list(agg.items()):
        if not gs:
            continue
        x = {a: sum(C[a][0][g] for g in gs) for a in C}
        print(f"{nm} | {np.median(x['nc']):.0f} ({np.mean(x['nc']):.0f}) | {np.median(x['p333']):.0f} ({np.mean(x['p333']):.0f}) | {np.median(x['v3w']):.0f} ({np.mean(x['v3w']):.0f}) | {100*np.mean(x['p333'])/tp:.1f} | {md(x['p333']-x['v3w'])} | {md(x['nc']-x['p333'])}")
    print("total all_delay paired p333 - v3w:", md(A["p333"] - A["v3w"]), "; nc - p333:", md(A["nc"] - A["p333"]), "; os0_10_10 - p333:", md(A["os0_10_10"] - A["p333"]))
    # periods
    pers = sorted({k for s in seeds for g in T[(cell, "p333")][s]["road_vs"].values() for k in g})
    print("periods:", pers)
    if len(pers) > 1:
        for per in pers:
            Cp = {a: comp(cell, a, per) for a in ("nc", "p333")}; Cp["v3w"] = pooled(lambda l: comp(cell, l, per))
            x = {a: sum(Cp[a][0][g] for g in GROUPS) for a in Cp}
            v = {a: sum(Cp[a][1][g] for g in GROUPS) for a in Cp}
            print(f" period {per}: delay nc {np.median(x['nc']):.0f}, p333 {np.median(x['p333']):.0f}, v3w {np.median(x['v3w']):.0f}; veh-s p333 {np.median(v['p333']):.0f}; p333 - v3w {md(x['p333']-x['v3w'])}")
    # served
    print("planned in window: median %.0f min %.0f max %.0f" % (np.median(sc(cell, "p333", "m_planned_window")), sc(cell, "p333", "m_planned_window").min(), sc(cell, "p333", "m_planned_window").max()))
    for a in ("nc", "p333", "os0_10_10") + tuple(LEARN):
        pw = sc(cell, a, "m_planned_window"); pa = sc(cell, a, "passed"); ar = sc(cell, a, "arrived"); pe = sc(cell, a, "m_pending_end"); fp = sc(cell, a, "finished_pct")
        print(f" {a}: passed median {np.median(pa):.0f} mean {np.mean(pa):.1f}; passed - planned median {np.median(pa-pw):+.0f} mean {np.mean(pa-pw):+.1f} [min {np.min(pa-pw):+.0f}, max {np.max(pa-pw):+.0f}]; arrived median {np.median(ar):.0f}; pending at end median {np.median(pe):.0f} mean {np.mean(pe):.1f} max {np.max(pe):.0f}; finished_pct median {np.median(fp):.2f}; delay/veh finished median {np.nanmedian(sc(cell,a,'delay')):.2f}, ramp {np.nanmedian(sc(cell,a,'delay_ramp')):.2f}, ramp2 {np.nanmedian(sc(cell,a,'delay_ramp2')):.2f}; teleports max {np.max(sc(cell,a,'teleports')):.0f}")
    # per-minute series
    def ser(arm, f):
        return np.array([f(T[(cell, arm)][s]) for s in seeds])
    for a in ("nc", "p333", "w0u250"):
        mp = ser(a, lambda r: r["m_main_pending_min"]); r1 = ser(a, lambda r: r["minute"]["ramp1_pending"]); r2 = ser(a, lambda r: r["minute"]["ramp2_pending"])
        q1 = ser(a, lambda r: r["minute"]["ramp1_queue"]); q2 = ser(a, lambda r: r["minute"]["ramp2_queue"])
        o1 = ser(a, lambda r: r["minute"]["m1_out"]); o2 = ser(a, lambda r: r["minute"]["m2_out"])
        v1 = ser(a, lambda r: r["minute"]["m1_acc_vs"]).sum(0) / ser(a, lambda r: r["minute"]["m1_acc_n"]).sum(0)
        v2 = ser(a, lambda r: r["minute"]["m2_acc_vs"]).sum(0) / ser(a, lambda r: r["minute"]["m2_acc_n"]).sum(0)
        u1 = ser(a, lambda r: r["minute"]["m1_up_vs"]).sum(0) / ser(a, lambda r: r["minute"]["m1_up_n"]).sum(0)
        u2 = ser(a, lambda r: r["minute"]["m2_up_vs"]).sum(0) / ser(a, lambda r: r["minute"]["m2_up_n"]).sum(0)
        blk = lambda x: " ".join("%.1f" % np.mean(x[..., i:i + 5]) for i in range(0, 25, 5))
        print(f" {a} per 5-min block (window minutes 0-25; mean over seeds):")
        print("   main pending veh (mean number waiting):", blk(mp / 60.0), "| ramp1 pending:", blk(r1 / 60.0), "| ramp2 pending:", blk(r2 / 60.0))
        print("   ramp1 queued veh (<queue speed):", blk(q1 / 60.0), "| ramp2:", blk(q2 / 60.0))
        print("   m1_out veh/h:", blk(o1 * 60.0), "| m2_out veh/h:", blk(o2 * 60.0))
        print("   speed km/h: 3a", blk(v1 * 3.6), "| edge 2", blk(u1 * 3.6), "| 4a", blk(v2 * 3.6), "| edge 3", blk(u2 * 3.6))
        slow1 = (ser(a, lambda r: r["minute"]["m1_acc_vs"]) / np.maximum(ser(a, lambda r: r["minute"]["m1_acc_n"]), 1) * 3.6 < 60).sum(1)
        slow2 = (ser(a, lambda r: r["minute"]["m2_acc_vs"]) / np.maximum(ser(a, lambda r: r["minute"]["m2_acc_n"]), 1) * 3.6 < 60).sum(1)
        print(f"   minutes (of 25) with 3a mean speed < 60 km/h: median {np.median(slow1):.0f}, mean {np.mean(slow1):.1f}, seeds with 0: {(slow1==0).sum()}; 4a: median {np.median(slow2):.0f}, mean {np.mean(slow2):.1f}, seeds with 0: {(slow2==0).sum()}")
        mo = ser(a, lambda r: r["minute"]["m2_out"])
        best5 = np.array([max(x[i:i + 5].sum() for i in range(21)) * 12 for x in mo])
        print(f"   m2_out: mean over window {np.mean(mo.sum(1))*2.4:.0f} veh/h; best 5-min per seed median {np.median(best5):.0f} veh/h, p95 {np.percentile(best5,95):.0f}; max 1-min median {np.median(mo.max(1))*60:.0f}")
    # class decomposition (0.1 s steps)
    print(" class delay (n*0.1 - dist/REF), veh-s, median | per vehicle-second share:")
    for a in ("nc", "p333", "w0u250"):
        s_ = []
        for c in ("alks", "car", "truck"):
            nn = sc(cell, a, f"m_n_{c}") * 0.1; dd = sc(cell, a, f"m_dist_m_{c}")
            s_.append(f"{c}: delay {np.median(nn - dd/REF):.0f}, veh-s {np.median(nn):.0f}, mean speed {np.median(dd/nn)*3.6:.1f} km/h")
        print("  ", a, "; ".join(s_))
