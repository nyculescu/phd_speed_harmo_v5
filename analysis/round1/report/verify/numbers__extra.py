import sys
sys.path.insert(0, sys.path[0])
from lib import OUT, load, g, med, arm
T = load(OUT + "/test/test.jsonl")
Q = 5300.0
ev = {}
for (n, q), A in T.items():
    s = sum(g(r, "alks_full_moving") for r in A.values())
    k = sum(g(r, "alks_full_moving") > 0 for r in A.values())
    if s: ev[n] = (s, k)
print("arms with any moving full-emergency event (total, runs with >0):", ev)
for c in ("X1", "X2"):
    W = arm(T, [f"{c}|w{i}" for i in range(5)], Q)
    print(c, "v3w b3_step median %.3f" % med(W, "b3_step"), "nc delay median %.3f" % med(T[(f"{c}|nc", Q)], "all_delay"), "nc b3 %.6f" % med(T[(f"{c}|nc", Q)], "b3_step"))
    print(c, "b7_step median range over all arms: %.2f-%.2f" % (min(med(A, "b7_step") for (n, q), A in T.items() if n.startswith(c)), max(med(A, "b7_step") for (n, q), A in T.items() if n.startswith(c))))
