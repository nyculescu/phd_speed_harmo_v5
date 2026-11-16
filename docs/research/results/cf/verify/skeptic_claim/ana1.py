import pickle, json, numpy as np
P = pickle.load(open("rows.pkl", "rb")); T = P["T"]
S = json.load(open("/home/catalin/work/phd/v5b1_runs/cf_remote/cf_screen/screen.json"))
V = ("w0u250", "w1u500", "w2u250", "w3u500", "w4u500")
seeds = sorted(T["p333"]); n = len(seeds)
assert seeds[0] == 7489160 and seeds[-1] == 7489639 and n == 480, (seeds[0], seeds[-1], n)
for a in T: assert sorted(T[a]) == seeds
idx = np.random.default_rng(20261108).integers(0, n, (20000, n))
def c(a, f):
    return np.array([f(T[a][s]) for s in seeds], float)
def edge(opp, f, L=V, sign=-1.0, pct=(1.25, 98.75)):
    O = c(opp, f); m = max(np.median(O), 1e-9)
    D = [sign * (c(w, f) - O) / m * 100 for w in L]
    b = np.mean([np.median(d[idx], axis=1) for d in D], axis=0)
    return (float(np.mean([np.median(d) for d in D])), *map(float, np.percentile(b, pct)))
F = lambda t: "%+.2f [%+.2f, %+.2f]" % t
k = lambda key: (lambda d: d[key])
zf = lambda z: (lambda d: d["z"].get(z, 0.0))
pf = lambda p: (lambda d: d["p"].get(p, 0.0))
# split sums
bad = sum(abs(sum(T[a][s]["z"].values()) - T[a][s]["ttc_net"]) > 0 for a in T for s in seeds)
bad2 = sum(abs(T[a][s]["E30c"] + T[a][s]["outE30c"] - T[a][s]["ttc_net"]) > 0 for a in T for s in seeds)
print("rows with zone sum != ttc_net:", bad, "; E30+out_E30 != ttc_net:", bad2, "; 'other' zone total", sum(T[a][s]["z"].get("other", 0) for a in T for s in seeds))
print("collisions total", sum(T[a][s]["coll"] for a in T for s in seeds), "teleports", sum(T[a][s]["teleports"] for a in T for s in seeds))
print("\n== reproduce reader")
for a, m, key in (("lr400_16_1", "E", "ttc_net"), ("p333", "D", "all_delay"), ("p333", "E", "ttc_net"), ("MPC-F", "E", "ttc_net"), ("3E-C_TRUCK", "brake", "b45_step"), ("3ex2", "brake", "b45_step"), ("lr400_16_1", "brake", "b45_step"), ("3ex2", "ev45", "ev45"), ("3ex1", "ev45", "ev45"), ("3e", "ev45", "ev45")):
    r = S["readings"][a][m]; print(a, m, "mine", F(edge(a, k(key))), "reader", F((r["pt"], r["lo"], r["hi"])))
r = S["readings"]["lr400_16_1"]["away"]; print("lr400_16_1 away mine", F(edge("lr400_16_1", zf("away"))), "reader", F((r["pt"], r["lo"], r["hi"])))
r = S["readings"]["grid_lr400_13_1"]["away"]; print("grid_lr400_13_1 away mine", F(edge("grid_lr400_13_1", zf("away"))), "reader", F((r["pt"], r["lo"], r["hi"])))
print("\n== F1 zones vs lr400_16_1")
for z in ("m2", "m1", "away", "jn"):
    print(z, F(edge("lr400_16_1", zf(z))), "per learner", [(w, F(edge("lr400_16_1", zf(z), (w,)))) for w in V])
print("zone shares")
for a in ["v3w", "lr400_16_1", "p333", "nc", "3ex2", "os0_10_10", "grid_lr400_13_1"]:
    names = V if a == "v3w" else (a,)
    tot = np.mean([c(w, k("ttc_net")) for w in names], axis=0)
    zs = {z: np.mean([c(w, zf(z)) for w in names], axis=0) for z in ("m2", "m1", "away", "jn")}
    print(a, "median-of-share", {z: round(float(np.median(v / np.maximum(tot, 1))), 3) for z, v in zs.items()},
          "share-of-sum", {z: round(float(v.sum() / tot.sum()), 3) for z, v in zs.items()}, "zone medians", {z: round(float(np.median(v)), 1) for z, v in zs.items()}, "means", {z: round(float(np.mean(v)), 1) for z, v in zs.items()})
print("absolute differences v3w - lr400_16_1 per zone (mean over seeds of learner-mean), counts")
for z in ("m2", "m1", "away", "jn"):
    d = np.mean([c(w, zf(z)) for w in V], axis=0) - c("lr400_16_1", zf(z))
    print(z, "mean %.1f median %.1f" % (d.mean(), np.median(d)))
d = np.mean([c(w, k("ttc_net")) for w in V], axis=0) - c("lr400_16_1", k("ttc_net")); print("total mean %.1f median %.1f" % (d.mean(), np.median(d)))
print("\nall competitors away + zone edges")
for a in S["competitors"]:
    r = S["readings"][a]["away"]
    print(a, "E", F(edge(a, k("ttc_net"))), "away", F((r["pt"], r["lo"], r["hi"])), "m2", F(edge(a, zf("m2"))), "m1", F(edge(a, zf("m1"))))
print("\nperiods: v3w vs lr400_16_1 and p333", P["periods"])
for o in ("lr400_16_1", "p333"):
    for p in P["periods"]:
        print(o, p, F(edge(o, pf(p))), "medians v3w %.1f opp %.1f" % (np.median(np.mean([c(w, pf(p)) for w in V], axis=0)), np.median(c(o, pf(p)))))
for o in ("lr400_16_1",):
    for zp in ("away|rest", "away|before", "away|hold", "away|after", "away|taper", "m2|rest", "m2|after", "m2|hold", "m1|rest", "m1|before", "m1|hold", "m1|after"):
        f = lambda d, zp=zp: d["zp"].get(zp, 0.0)
        print(o, zp, "means v3w %.1f opp %.1f" % (np.mean(np.mean([c(w, f) for w in V], axis=0)), np.mean(c(o, f))))
print("roads means v3w vs lr400_16_1 vs p333")
for rd in P["roads"]:
    f = lambda d, rd=rd: d["rd"].get(rd, 0.0)
    print(rd, "%.1f %.1f %.1f" % (np.mean(np.mean([c(w, f) for w in V], axis=0)), np.mean(c("lr400_16_1", f)), np.mean(c("p333", f))))
