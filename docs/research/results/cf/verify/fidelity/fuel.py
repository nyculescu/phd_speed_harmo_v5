import json, pickle
import numpy as np
n = 480; pos = {s: i for i, s in enumerate(range(7489160, 7489640))}
keys = ("fuel_km", "end_stop", "end_stop2", "passed", "N", "alks_full_moving", "alks_b45_step", "b7_step", "collisions")
X = {k: {} for k in keys}
for line in open("/home/catalin/work/phd/v5b1_runs/cf_remote/cf_screen/s6_rows.jsonl"):
    r = json.loads(line)
    for k in keys: X[k].setdefault(r["arm"], np.zeros(n))[pos[r["seed"]]] = float(r.get(k) or 0.0)
pickle.dump(X, open("/tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/2d269ac5-95be-4f04-801b-ec9cc9873355/scratchpad/cfv/fidelity/side.pkl", "wb"))
V3W = ("w0u250", "w1u500", "w2u250", "w3u500", "w4u500"); idx = np.random.default_rng(20261108).integers(0, n, (20000, n))
scr = json.load(open("/home/catalin/work/phd/v5b1_runs/cf_remote/cf_screen/screen.json")); comp = scr["competitors"]
def eff(k, opp):
    O = X[k][opp]; D = [-(X[k][w] - O) / max(np.median(O), 1e-9) * 100 for w in V3W]
    b = np.mean([np.median(d[idx], axis=1) for d in D], axis=0); lo, hi = np.percentile(b, (1.25, 98.75)); return float(np.mean([np.median(d) for d in D])), float(lo), float(hi)
for k in ("fuel_km", "N", "passed"):
    res = {a: eff(k, a) for a in X[k] if a not in V3W}
    print(k, "(positive = v3w lower): competitors", {a: [round(x, 2) for x in res[a]] for a in comp})
    print("   nc", [round(x, 2) for x in res["nc"]], "| arms with hi<0:", [a for a, v in res.items() if v[2] < 0], "| arms with lo>0:", len([a for a, v in res.items() if v[1] > 0]))
for k in ("end_stop", "end_stop2", "collisions", "alks_full_moving", "b7_step"):
    v = np.mean([X[k][w] for w in V3W], axis=0)
    print(k, "mean per run: v3w", round(float(v.mean()), 3), "| lr400_16_1", round(float(X[k]["lr400_16_1"].mean()), 3), "| p333", round(float(X[k]["p333"].mean()), 3), "| nc", round(float(X[k]["nc"].mean()), 3), "| 3ex2", round(float(X[k]["3ex2"].mean()), 3))
