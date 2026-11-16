import pickle, numpy as np, sys
D = sys.argv[1]
rows = pickle.load(open(D + "/rows.pkl", "rb"))
arms = sorted({a for a, s in rows}); seeds = sorted({s for a, s in rows})
print(len(arms), len(seeds), seeds[0], seeds[-1])
V3W = ["E30|w0u250", "E30|w1u500", "E30|w2u250", "E30|w3u500", "E30|w4u500"]
def rs(d, roads):
    return sum(sum(x.values()) for k, x in d.get("m_road_ttc3", {}).items() if k in roads)
def col(a, f):
    return np.array([f(rows[(a, s)]) for s in seeds], float)
F = {"ttc_net": lambda d: d["ttc_net"], "end_stop": lambda d: d.get("end_stop", 0), "end_stop2": lambda d: d.get("end_stop2", 0),
     "m1": lambda d: rs(d, ("3a", "ramp1")), "m2": lambda d: rs(d, ("4a", "ramp2")), "away": lambda d: rs(d, ("1", "2", "3", "4", "5")),
     "jn": lambda d: rs(d, ("junction",)), "ttc_half": lambda d: d.get("ttc_half", 0), "all_delay": lambda d: d["all_delay"],
     "ttc3_all": lambda d: d.get("m_ttc3_all", 0), "ttc3_lc": lambda d: d.get("m_ttc3_lc", 0), "b45_step": lambda d: d["b45_step"], "passed": lambda d: d["passed"]}
X = {k: {a: col(a, f) for a in arms} for k, f in F.items()}
np.savez(D + "/cols.npz", arms=np.array(arms), seeds=np.array(seeds), **{k: np.array([X[k][a] for a in arms]) for k in X})
print("arm | median ttc_net end_stop end_stop2 (mean end_stop, end_stop2) m1 m2 away jn | ttc_half | ttc3_lc/ttc3_all")
for a in arms:
    m = lambda k: np.median(X[k][a])
    print(a.ljust(22), m("ttc_net"), m("end_stop"), m("end_stop2"), "(%.1f %.1f)" % (X["end_stop"][a].mean(), X["end_stop2"][a].mean()), m("m1"), m("m2"), m("away"), m("jn"), "|", m("ttc_half"),
          "| lc share %.3f" % (X["ttc3_lc"][a].sum() / max(X["ttc3_all"][a].sum(), 1)), "| p10/p90 end_stop2 %.0f %.0f" % tuple(np.percentile(X["end_stop2"][a], [10, 90])),
          "| share seeds end_stop+2 < 20: %.2f" % np.mean(X["end_stop"][a] + X["end_stop2"][a] < 20))
print("ttc_net == m_ttc3_all all rows:", all(np.array_equal(X["ttc_net"][a], X["ttc3_all"][a]) for a in arms))
print("ttc_net == m1+m2+away+jn all rows:", all(np.array_equal(X["ttc_net"][a], X["m1"][a] + X["m2"][a] + X["away"][a] + X["jn"][a]) for a in arms))
