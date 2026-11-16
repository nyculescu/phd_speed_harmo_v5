import pickle, json, sys
import numpy as np
S = sys.argv[1]
R = pickle.load(open(f"{S}/screen.pkl", "rb"))
scr = json.load(open("/home/catalin/work/phd/v5b1_runs/cf_remote/cf_screen/screen.json"))
n = 480; pos = {s: i for i, s in enumerate(range(7489160, 7489640))}
V3W = ("w0u250", "w1u500", "w2u250", "w3u500", "w4u500")
A, T = {}, {}
for r in R:
    A.setdefault(r["arm"], np.zeros(n))[pos[r["seed"]]] = r["away"]; T.setdefault(r["arm"], np.zeros(n))[pos[r["seed"]]] = r["E30"] + r["out_E30"]
M = {a: T[a] - A[a] for a in T}
idx = np.random.default_rng(20261108).integers(0, n, (20000, n))
def eff(X, opp):
    O = X[opp]; D = [-(X[w] - O) / np.median(O) * 100 for w in V3W]
    b = np.mean([np.median(d[idx], axis=1) for d in D], axis=0)
    return [round(float(x), 2) for x in (np.mean([np.median(d) for d in D]), *np.percentile(b, (1.25, 98.75)), *np.percentile(b, (2.5, 97.5)))], [round(float(np.median(d)), 1) for d in D]
for a in ("lr400_16_1", "grid_lr400_13_1", "3ex2", "p333", "nc"):
    print(a, "away [pt, lo, hi, lo95, hi95]", *eff(A, a), "| screen.json", round(scr["readings"][a]["away"]["pt"], 2), "| not-away (merges, ramps, junctions)", *eff(M, a))
v = np.mean([A[w] for w in V3W], axis=0); vt = np.mean([T[w] for w in V3W], axis=0)
print("medians away / total: v3w", np.median(v), np.median(vt), "| lr400_16_1", np.median(A["lr400_16_1"]), np.median(T["lr400_16_1"]), "| p333", np.median(A["p333"]), np.median(T["p333"]), "| nc", np.median(A["nc"]), np.median(T["nc"]))
print("share of close-following away from both merges (sum over seeds): v3w", round(float(v.sum() / vt.sum()), 3), "lr400_16_1", round(float(A["lr400_16_1"].sum() / T["lr400_16_1"].sum()), 3), "p333", round(float(A["p333"].sum() / T["p333"].sum()), 3))
aw = {a: scr["readings"][a]["away"] for a in scr["readings"]}
print("away readings: hi<0 (97.5 %):", [(a, round(x["pt"], 1), round(x["lo"], 1), round(x["hi"], 1)) for a, x in aw.items() if x["hi"] < 0], "| hi95<0:", [a for a, x in aw.items() if x["hi95"] < 0], "| lo>0:", sum(x["lo"] > 0 for x in aw.values()), "of", len(aw))
