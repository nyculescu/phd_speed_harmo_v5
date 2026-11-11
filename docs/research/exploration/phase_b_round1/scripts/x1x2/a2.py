from lib import *
import re, pickle
Q = 5300.0
R1 = ["w0u250","w1u250","w2u500","w3u500","w4u500"]; R2 = ["w0u250","w1u500","w2u250","w3u500","w4u500"]
DS = {"r1test": (RUNS+"round1_remote/out/test/test.jsonl", ["w0","w1","w2","w3","w4"]),
      "r2val": (RUNS+"round2/val/rows_6c49e7e.jsonl", R1),
      "r2test": (RUNS+"round2/test/rows_6c49e7e.jsonl", R2)}
T = {k: load(f) for k, (f, _) in DS.items()}
pol = re.compile(r"^[a-z]\d(u\d+)?$")
def pooled(c, rule, sets, learner=None):
    A, B = {}, {}
    for s in sets:
        names = DS[s][1]
        if (f"{c}|{rule}", Q) not in T[s]: return None
        a = arm_mean(T[s], [f"{c}|{n}" for n in names], Q) if learner is None else T[s][(f"{c}|{names[learner]}", Q)]
        A |= a; B |= T[s][(f"{c}|{rule}", Q)]
    return A, B
res = {}
for c in ("X1", "X2"):
    rules = sorted({n.split("|")[1] for s in T for (n, q) in T[s] if n.startswith(c+"|") and q == Q and not pol.match(n.split("|")[1])})
    rows = []
    for r in rules:
        d = {}
        for s in DS:
            p = pooled(c, r, [s])
            d[s] = eff(*p) if p else None
        sets = [s for s in DS if d[s]]
        A, B = pooled(c, r, sets)
        d["pool"] = eff(A, B); d["pool975"] = eff(A, B, pct=(1.25, 98.75)); d["sets"] = sets
        d["learn"] = [eff(*pooled(c, r, sets, i)) for i in range(5)]
        d["learn_r2test"] = [eff(*pooled(c, r, ["r2test"], i)) for i in range(5)]
        rows.append((r, d))
    rows.sort(key=lambda x: x[1]["pool"][0])
    res[c] = rows
    print(f"\n## {c}: v3w arm delay effect % (positive = v3w less delay), median paired diff / rule median [95 % CI]")
    print("rule | r1test | r2val(r1 ckpts) | r2test | pooled n | pooled [95] | pooled [97.5] | SD% | mean% | learners pooled (CI>0 count) | learners r2test CI>0")
    f = lambda e: "-" if e is None else f"{e[0]:+.1f} [{e[1]:+.1f}, {e[2]:+.1f}]"
    for r, d in rows:
        L = d["learn"]
        print(f"{r} | {f(d['r1test'])} | {f(d['r2val'])} | {f(d['r2test'])} | {d['pool'][3]} | {f(d['pool'])} | [{d['pool975'][1]:+.1f}, {d['pool975'][2]:+.1f}] | {d['pool'][4]:.1f} | {d['pool'][5]:+.1f} | " + " ".join(f"{e[0]:+.1f}" for e in L) + f" ({sum(e[1]>0 for e in L)}/5) | {sum(e[1]>0 for e in d['learn_r2test'])}/5")
pickle.dump(res, open("a2.pkl", "wb"))
