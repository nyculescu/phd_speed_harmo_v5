import pickle, json, sys
import numpy as np
S = sys.argv[1]
R = pickle.load(open(f"{S}/screen.pkl", "rb"))
scr = json.load(open("/home/catalin/work/phd/v5b1_runs/cf_remote/cf_screen/screen.json"))
n = 480; pos = {s: i for i, s in enumerate(range(7489160, 7489640))}
V3W = ("w0u250", "w1u500", "w2u250", "w3u500", "w4u500")
T = {}
for r in R: T.setdefault(r["arm"], np.zeros(n))[pos[r["seed"]]] = r["E30"] + r["out_E30"]
def null(opp, seed, swaps=2000, nb=1000):
    O = T[opp]; D = [-(T[w] - O) / np.median(O) * 100 for w in V3W]
    rng = np.random.default_rng(seed); idx = np.random.default_rng(seed + 1).integers(0, n, (nb, n)); lo_hit = hi_hit = 0
    for _ in range(swaps):
        F = [d * rng.choice((-1.0, 1.0), n) for d in D]
        b = np.mean([np.median(f[idx], axis=1) for f in F], axis=0); lo, hi = np.percentile(b, (1.25, 98.75))
        lo_hit += lo > 0; hi_hit += hi < 0
    return (lo_hit + hi_hit) / (2 * swaps), lo_hit / swaps, hi_hit / swaps
comp = scr["competitors"]
for a in ("lr400_16_1", "p333"):
    i = comp.index(a); print(a, "test index", i, "mine (mean, lower-side, upper-side)", null(a, 20261100 + 2 * i), "screen.json", scr["nulls"][f"E {a}"])
allr = [v["rate"] for v in scr["nulls"].values()] + [c["null"]["rate"] for c in scr["chords"]]
dec = [scr["nulls"][f"E {a}"]["rate"] for a in comp] + [c["null"]["rate"] for c in scr["chords"]]
print("all nulls", len(allr), min(allr), max(allr), "| deciding 234:", len(dec), min(dec), max(dec), "| E+brake 28:", min(v["rate"] for v in scr["nulls"].values()), max(v["rate"] for v in scr["nulls"].values()))
print("E-only 14:", min(scr["nulls"][f"E {a}"]["rate"] for a in comp), max(scr["nulls"][f"E {a}"]["rate"] for a in comp), "| chords 220:", min(c["null"]["rate"] for c in scr["chords"]), max(c["null"]["rate"] for c in scr["chords"]), "| mean of all", float(np.mean(allr)))
print("any re-estimate:", any("re_rate" in v for v in scr["nulls"].values()) or any("re_rate" in c["null"] for c in scr["chords"]))
