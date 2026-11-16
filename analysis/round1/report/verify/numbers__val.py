"""Section 3: checkpoint choice, validation table, verdicts, floor."""
import json
import sys

sys.path.insert(0, sys.path[0])
from lib import OUT, P95, arm, f, med, stat, load, pmed

Q = 5300.0
T = load(OUT + "/val/validation.jsonl")
print("arms", len(T), "seeds per arm", {len(v) for v in T.values()})
C = ("X1", "X2")
R = "os1_15_10"


def choose(pfx, i):
    sc = {}
    for ck in (250, 500):
        n = sum(stat(T[(f"{c}|{pfx}{i}u{ck}", Q)], T[(f"{c}|{R}", Q)], "all_delay", pct=P95)[0] >= -2.0 for c in C)
        ttc = sum(med(T[(f"{c}|{pfx}{i}u{ck}", Q)], "ttc_net") for c in C)
        sc[ck] = (n, -ttc, ck)
    return max(sc, key=lambda k: sc[k]), sc


chosen = {}
for k, p in (("inc", "d"), ("v3w", "w"), ("res", "r"), ("attr", "a")):
    chosen[k] = {}
    for i in range(5):
        ck, sc = choose(p, i)
        chosen[k][i] = ck
        print(k, i, ck, {c: (s[0], round(-s[1], 1)) for c, s in sc.items()})
print("chosen", chosen)
stored = json.load(open(OUT + "/val/validation.json"))
print("stored chosen", stored["chosen"], stored["incumbent_chosen"])


def A(pfx, ck, c):
    return arm(T, [f"{c}|{pfx}{i}u{ck[i]}" for i in range(5)], Q)


floor_ttc, floor_delay = [], []
for k, p in (("v3w", "w"), ("res", "r"), ("attr", "a"), ("inc", "d")):
    row = {}
    for c in C:
        K, I = A(p, chosen[k], c), A("d", chosen["inc"], c)
        d = stat(K, I, "all_delay", pct=P95)
        t = stat(K, T[(f"{c}|{R}", Q)], "ttc_net", pct=P95)
        K5 = A(p, {i: 500 for i in range(5)}, c)
        tp = stat(K5, T[(f"{c}|p333", Q)], "ttc_net", pct=P95)
        dn = stat(K5, T[(f"{c}|nc", Q)], "all_delay", pct=P95)
        qual = d[1] > 0 and t[0] >= 10
        harm = d[2] < 0
        fl = tp[0] < 10 or dn[2] < 0
        print(k, c, "delay_vs_inc", f(d, 2), "ttc_vs_rule", f(t, 2), "qual", qual, "harm", harm, "| u500 ttc_vs_p333", f(tp, 2), "u500 delay_vs_nc", f(dn, 2), "floor", fl)
        if k != "inc":
            floor_ttc.append(tp[0])
            floor_delay.append(dn[0])
        # incumbent arm TTC vs rule, for the "lost most of the margin" claim
print("min u500 ttc_vs_p333 over candidates", round(min(floor_ttc), 2), "delay_vs_nc range", round(min(floor_delay), 2), round(max(floor_delay), 2))
