"""Skeptic re-derivation, part 2: periods, lane-end stops, speed bands, severity, exposure (read only)."""
import json, pickle
import numpy as np
from scipy.stats import spearmanr
exec(open("s1.py").read().split("ALLR =")[0])     # loader, col, edge, fm
m1 = lambda r: rsum(r, "m_road_ttc3", ("3a", "ramp1"))
m2 = lambda r: rsum(r, "m_road_ttc3", ("4a", "ramp2"))
COMP = S["competitors"]
med = lambda a, f: float(np.median(col(a, f)))
vmed = lambda f: float(np.median([med(w, f) for w in V3W]))
md = lambda a, f: float(np.mean([np.mean(col(a, f) - col(w, f)) for w in V3W]))
th = lambda r: r["ttc3_p_taper"] + r["ttc3_p_hold"]
print("A. periods. event draws:")
on = np.array([T["p333"][s]["pert"][0][1] for s in seeds]); du = np.array([T["p333"][s]["pert"][0][2] for s in seeds])
same = all(T[a][s]["pert"][0] == T["p333"][s]["pert"][0] for a in T for s in seeds)
print("  onset min/med/max", on.min().round(1), np.median(on).round(1), on.max().round(1), "dur", du.min().round(1), np.median(du).round(1), du.max().round(1), "same draw across arms:", same)
secs = {"before": on - 300, "taper+hold": du, "after": np.full(n, 120.0), "rest": 1800 - (on + du + 120)}
print("  mean seconds per period:", {k: round(float(v.mean()), 1) for k, v in secs.items()}, " rest min", round(float(secs["rest"].min()), 1))
P = {"before": "ttc3_p_before", "taper+hold": th, "after": "ttc3_p_after", "rest": "ttc3_p_rest"}
print("  share of each arm's own samples per period (mean counts), and rate per s")
for a in ("v3w", "p333", "lr400_16_1", "grid_lr400_13_1", "MPC-F"):
    mm = {k: (np.mean([col(w, f).mean() for w in V3W]) if a == "v3w" else col(a, f).mean()) for k, f in P.items()}
    tot = sum(mm.values())
    print("   ", a.ljust(16), " ".join(f"{k} {v:7.1f} ({100*v/tot:3.0f}%, {v/secs[k].mean():.3f}/s)" for k, v in mm.items()))
print("  additive share of the edge per period, and C-D5 on taper+hold / after / rest, all 14")
neg = []
for a in COMP:
    tot = md(a, "ttc3"); sh = {k: 100 * md(a, f) / tot for k, f in P.items()}
    e = {k: edge(a, P[k]) for k in ("taper+hold", "after", "rest", "before")}
    if e["taper+hold"][2] < 0: neg.append(a)
    print("   ", a.ljust(16), " ".join(f"{k} {v:4.0f}%" for k, v in sh.items()), "| t+h", fm(e["taper+hold"]), "| after", fm(e["after"]), "| rest", fm(e["rest"]), "| before", fm(e["before"]), flush=True)
print("  competitors with taper+hold upper bound < 0:", neg)
print("  medians taper+hold: v3w", vmed(th), {a: med(a, th) for a in ("lr400_16_1", "grid_lr400_13_1", "MPC-F", "p333", "nc", "lr1000_16_2", "lr400_13_2")})
# where are the taper+hold samples: by road group
def rp(roads, pers): return lambda r: rsum(r, "m_road_ttc3", roads, pers)
for nm, roads in (("event 1,2", ("1", "2")), ("merge1", ("3a", "ramp1")), ("merge2", ("4a", "ramp2")), ("between", ("3",))):
    f = rp(roads, ("taper", "hold"))
    print(f"   taper+hold mean samples on {nm}: v3w {np.mean([col(w, f).mean() for w in V3W]):6.1f}  lr400_16_1 {col('lr400_16_1', f).mean():6.1f}  p333 {col('p333', f).mean():6.1f}  nc {col('nc', f).mean():6.1f}")
print("\nB. lane-end stops")
print("  medians end_stop2 / end_stop: v3w", vmed("end_stop2"), vmed("end_stop"), {a: (med(a, "end_stop2"), med(a, "end_stop")) for a in ("lr400_16_1", "p333", "MPC-F", "3E-D_TRUCK", "3E-C_TRUCK", "nc")})
print("  edge on end_stop2 vs p333", fm(edge("p333", "end_stop2")), " vs lr400_16_1", fm(edge("lr400_16_1", "end_stop2")))
vs4a = lambda r: rsum(r, "m_road_vs", ("4a",))
vs3 = lambda r: rsum(r, "m_road_vs", ("3",))
for a in ("p333", "lr400_16_1", "MPC-F", "3E-D_TRUCK"):
    r2 = [spearmanr(col(a, "end_stop2") - col(w, "end_stop2"), col(a, m2) - col(w, m2))[0] for w in V3W]
    r1 = [spearmanr(col(a, "end_stop") - col(w, "end_stop"), col(a, m1) - col(w, m1))[0] for w in V3W]
    rv = [spearmanr(col(a, vs4a) - col(w, vs4a), col(a, m2) - col(w, m2))[0] for w in V3W]
    rv3 = [spearmanr(col(a, vs3) - col(w, vs3), col(a, m2) - col(w, m2))[0] for w in V3W]
    rd = [spearmanr(col(a, "all_delay") - col(w, "all_delay"), col(a, m2) - col(w, m2))[0] for w in V3W]
    print("   ", a.ljust(12), "rho d(end_stop2),d(m2 TTC)", " ".join(f"{x:+.2f}" for x in r2), "| merge1", " ".join(f"{x:+.2f}" for x in r1),
          "| d(veh-s on 4a),d(m2 TTC)", " ".join(f"{x:+.2f}" for x in rv), "| d(veh-s on 3)", " ".join(f"{x:+.2f}" for x in rv3), "| d(delay)", " ".join(f"{x:+.2f}" for x in rd))
for a in ("w0u250", "p333", "lr400_16_1"):
    print("    within-arm rho(end_stop2, m2 TTC)", a, f"{spearmanr(col(a, 'end_stop2'), col(a, m2))[0]:+.2f}", " rho(veh-s 4a, m2 TTC)", f"{spearmanr(col(a, vs4a), col(a, m2))[0]:+.2f}")
res = []
for w in V3W:
    d = col("p333", "end_stop2") - col(w, "end_stop2"); k = np.abs(d) <= 25; dm = col("p333", m2) - col(w, m2)
    res.append((int(k.sum()), float(np.median(dm[k])), float(np.median(dm))))
print("  p333, seeds with |d end_stop2|<=25: (n, median d m2 there, median d m2 all)", res)
print("  E on merge-2 TTC per lane-end stop sample (ratio) vs p333:", fm(edge("p333", lambda r: m2(r) / max(r["end_stop2"], 1.0))), " vs lr400_16_1:", fm(edge("lr400_16_1", lambda r: m2(r) / max(r["end_stop2"], 1.0))))
print("\nC. speed bands and severity vs lr400_16_1")
print("  v3w medians lo/mid/hi", vmed("ttc3_s_lo"), vmed("ttc3_s_mid"), vmed("ttc3_s_hi"))
tot = md("lr400_16_1", "ttc3"); print("  additive shares lo/mid/hi", [round(100 * md("lr400_16_1", k) / tot) for k in ("ttc3_s_lo", "ttc3_s_mid", "ttc3_s_hi")])
for nm, f in (("ttc2", "ttc2"), ("ttc15", "ttc15"), ("sev3", "sev3"), ("mild 2-3", lambda r: r["ttc3"] - r["ttc2"]), ("ttc_half", "ttc_half"), ("not lc", lambda r: r["m_ttc3_all"] - r["m_ttc3_lc"])):
    print("   ", nm.ljust(10), fm(edge("lr400_16_1", f)), " p333", fm(edge("p333", f)), flush=True)
print("  medians ttc2/ttc15/sev3 v3w", vmed("ttc2"), vmed("ttc15"), vmed("sev3"), " lr400_16_1", med("lr400_16_1", "ttc2"), med("lr400_16_1", "ttc15"), med("lr400_16_1", "sev3"), " lc v3w", vmed("m_ttc3_lc"))
print("\nD. exposure vs lr400_16_1")
print("  medians passed/vs/dist: v3w", vmed("passed"), vmed("vs"), round(vmed("dist_step")), " lr", med("lr400_16_1", "passed"), med("lr400_16_1", "vs"), round(med("lr400_16_1", "dist_step")), " p333", med("p333", "passed"), med("p333", "vs"))
for nm, f in (("per veh-s", lambda r: r["ttc_net"] / r["vs"]), ("per veh-km", lambda r: r["ttc_net"] / r["dist_step"] * 1000), ("per passed", lambda r: r["ttc_net"] / r["passed"])):
    print("   ", nm.ljust(10), fm(edge("lr400_16_1", f)), " nc", fm(edge("nc", f)), flush=True)
print("  nc raw", fm(edge("nc", "ttc_net")))
