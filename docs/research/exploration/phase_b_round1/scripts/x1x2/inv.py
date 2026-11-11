from lib import *
import hashlib
for lab, f in FILES.items():
    T = load(f)
    print("==", lab, len(T))
    by = defaultdict(list)
    for (n, q), S in T.items():
        c, a = n.split("|")
        by[(c, q)].append((a, len(S), min(S), max(S)))
    for (c, q), L in sorted(by.items()):
        rng = {(x[1], x[2], x[3]) for x in L}
        print(" ", c, q, len(L), "arms; (n,min,max):", sorted(rng))
        print("    ", " ".join(sorted(x[0] for x in L)))
