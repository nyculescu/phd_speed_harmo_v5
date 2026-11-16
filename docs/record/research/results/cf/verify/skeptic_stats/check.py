import json, sys, numpy as np
z = np.load(sys.argv[1]); S = json.load(open(sys.argv[2]))
A, arms, keys = z["A"], list(z["arms"]), list(z["keys"])
col = lambda a, k: A[arms.index(a), :, keys.index(k)]
V = ["w0u250", "w1u500", "w2u250", "w3u500", "w4u500"]
n = A.shape[1]; pct = (1.25, 98.75)
print("ttc_net==E30+out_E30 all:", bool(np.all(col(V[0],"ttc_net")*0 + A[:,:,1] == A[:,:,3] + A[:,:,4])))
def Dl(o, k):
    O = col(o, k); m = np.median(O)
    return [-(col(w, k) - O) / m * 100 for w in V]
def boot(D, idx):
    return np.mean([np.median(d) for d in D]), np.mean([np.median(d[idx], axis=1) for d in D], axis=0)
idxP = np.random.default_rng(20261108).integers(0, n, (20000, n))
idxQ = np.random.default_rng(424242).integers(0, n, (20000, n))
rules = [a for a in arms if a not in V]
Dpt = {}
for a in rules:
    pt, b = boot(Dl(a, "all_delay"), idxP); Dpt[a] = pt
print("D pt<0:", sorted((round(v,2), a) for a, v in Dpt.items() if v < 0))
for a in ["lr400_16_1", "p333", "3E-C_TRUCK"]:
    for nm, idx in (("P", idxP), ("Q", idxQ)):
        pt, b = boot(Dl(a, "ttc_net"), idx); lo, hi = np.percentile(b, pct)
        print("E", a, nm, round(pt, 3), round(lo, 3), round(hi, 3), "screen", round(S["readings"][a]["E"]["lo"], 3) if nm == "P" else "")
# denominator re-drawn per resample
for a in ["lr400_16_1", "p333"]:
    O = col(a, "ttc_net"); mb = np.median(O[idxP], axis=1)
    b = np.mean([np.median(-(col(w, "ttc_net")[idxP] - O[idxP]), axis=1) / mb * 100 for w in V], axis=0)
    print("resample-denominator", a, np.round(np.percentile(b, pct), 2))
# per-learner vs lr400_16_1 and seed shares
for opp in ["lr400_16_1", "p333"]:
    for w, d in zip(V, Dl(opp, "ttc_net")):
        b = np.median(d[idxP], axis=1); lo, hi = np.percentile(b, pct)
        sh = np.mean(col(w, "ttc_net") < col(opp, "ttc_net")); tie = np.mean(col(w, "ttc_net") == col(opp, "ttc_net"))
        print(opp, w, round(np.median(d), 2), round(lo, 2), round(hi, 2), "share fewer", round(sh, 3), "ties", round(tie, 3))
    print(opp, "median ttc", np.median(col(opp, "ttc_net")), "learners", [np.median(col(w, "ttc_net")) for w in V])
# mean-of-5 per seed share
m5 = np.mean([col(w, "ttc_net") for w in V], axis=0)
print("mean-of-5 learners fewer than lr400_16_1 share", round(np.mean(m5 < col("lr400_16_1", "ttc_net")), 3))
# min E lo among other arms
los = sorted((S["readings"][a]["E"]["lo"], a) for a in rules)
print("E lo two smallest", los[:3])
ch = sorted(S["chords"], key=lambda c: c["lo"])
print("20 lowest chords:", [(c["q"], c["r"], round(c["w"], 3), round(c["pt"], 2), round(c["lo"], 2)) for c in ch[:20]])
print("n w0 pt==9.93 among 20:", sum(c["w"] == 0 and abs(c["pt"] - S["readings"]["lr400_16_1"]["E"]["pt"]) < 1e-9 for c in ch[:20]))
inl = [c for c in S["chords"] if "lr400_16_1" in (c["q"], c["r"])]; oth = [c for c in S["chords"] if c not in inl]
print("with lr400_16_1", len(inl), round(min(c["lo"] for c in inl), 3), round(max(c["lo"] for c in inl), 3), "others", len(oth), min((round(c["lo"], 2), c["q"], c["r"]) for c in oth))
print("interior min lo", min((round(c["lo"], 3), c["q"], c["r"], round(c["w"], 3)) for c in S["chords"] if 0 < c["w"] < 1))
print("min chord hi", round(min(c["hi"] for c in S["chords"]), 2))
c = [c for c in S["chords"] if {c["q"], c["r"]} == {"lr400_16_1", "os1_10_0"}][0]
print("lr400_16_1~os1_10_0", c["q"], c["r"], c["w"], c["w_ci"], round(c["hi"], 2))
