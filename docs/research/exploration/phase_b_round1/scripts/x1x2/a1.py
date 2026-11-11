from lib import *
import sys
DS = {"r1test(500-539)": (RUNS+"round1_remote/out/test/test.jsonl", {"v3w_r1ck": ["w0","w1","w2","w3","w4"]}),
      "r2val(800-839)": (RUNS+"round2/val/rows_6c49e7e.jsonl", {"v3w_r1ck": ["w0u250","w1u250","w2u500","w3u500","w4u500"], "v3w_r2ck": ["w0u250","w1u500","w2u250","w3u500","w4u500"]}),
      "r2test(840-879)": (RUNS+"round2/test/rows_6c49e7e.jsonl", {"v3w_r2ck": ["w0u250","w1u500","w2u250","w3u500","w4u500"]})}
Q = 5300.0
POL = ("w","d","t","s","a","r","f","b","g","k","h","p")
out = {}
ALL = {}
for lab, (f, arms) in DS.items():
    T = load(f); ALL[lab] = T
    for c in ("X1", "X2"):
        rules = sorted(n.split("|")[1] for (n, q) in T if n.startswith(c + "|") and q == Q and not (n.split("|")[1][0] in POL and n.split("|")[1][1].isdigit()))
        for an, names in arms.items():
            A = arm_mean(T, [f"{c}|{n}" for n in names], Q)
            res = []
            for r in rules:
                R = T[(f"{c}|{r}", Q)]
                e = eff(A, R)
                e975 = eff(A, R, pct=(1.25, 98.75))
                per = [eff(T[(f"{c}|{n}", Q)], R) for n in names]
                res.append((r, e, e975, per, float(np.median([val(x, "all_delay") for x in R.values()]))))
            res.sort(key=lambda x: x[1][0])
            print(f"\n## {lab} {c} arm {an} n={res[0][1][3]}  arm median all_delay {np.median([x['all_delay'] for x in A.values()]):.0f}")
            print("rule | rule med | arm eff% [95%] | [97.5%] | pairedSD% | learners eff% (w0..w4) | n learners CI>0 / point>0")
            for r, e, e9, per, m in res:
                print(f"{r} | {m:.0f} | {e[0]:+.1f} [{e[1]:+.1f}, {e[2]:+.1f}] | [{e9[1]:+.1f}, {e9[2]:+.1f}] | {e[4]:.1f} | " + " ".join(f"{p[0]:+.1f}[{p[1]:+.1f},{p[2]:+.1f}]" for p in per) + f" | {sum(p[1]>0 for p in per)}/{sum(p[0]>0 for p in per)}")
            out[(lab, c, an)] = res
import pickle; pickle.dump({k: [(r, e, e9, per, m) for r, e, e9, per, m in v] for k, v in out.items()}, open("a1.pkl", "wb"))
