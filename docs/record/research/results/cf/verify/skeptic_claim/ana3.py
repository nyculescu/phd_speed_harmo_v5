import pickle, numpy as np
P = pickle.load(open("rows.pkl", "rb")); T = P["T"]
V = ("w0u250", "w1u500", "w2u250", "w3u500", "w4u500"); seeds = sorted(T["p333"]); n = len(seeds)
idx = np.random.default_rng(20261108).integers(0, n, (20000, n))
def c(a, f): return np.array([f(T[a][s]) for s in seeds], float)
def boot(opp, f):
    O = c(opp, f); m = np.median(O); D = [-(c(w, f) - O) / m * 100 for w in V]
    return float(np.mean([np.median(d) for d in D])), np.mean([np.median(d[idx], axis=1) for d in D], axis=0)
q = 100 * 0.05 / 26 / 2
for name, opp, f in (("away lr400_16_1", "lr400_16_1", lambda d: d["z"].get("away", 0.0)), ("ev45 3ex2", "3ex2", lambda d: d["ev45"]), ("ev45 3ex1", "3ex1", lambda d: d["ev45"]), ("ev45 3e", "3e", lambda d: d["ev45"]),
                     ("E lr400_16_1", "lr400_16_1", lambda d: d["ttc_net"]), ("rest lr400_16_1", "lr400_16_1", lambda d: d["p"].get("rest", 0.0)), ("hold lr400_16_1", "lr400_16_1", lambda d: d["p"].get("hold", 0.0)),
                     ("m1+away lr400_16_1", "lr400_16_1", lambda d: d["z"].get("away", 0.0) + d["z"].get("m1", 0.0) + d["z"].get("jn", 0.0))):
    pt, b = boot(opp, f)
    print(name, "%+.2f  97.5%% [%+.2f, %+.2f]  Bonferroni-26 (%.3f%% tails) [%+.2f, %+.2f]  share of resamples > 0: %.4f" % (pt, *np.percentile(b, (1.25, 98.75)), q, *np.percentile(b, (q, 100 - q)), float(np.mean(b > 0))))
