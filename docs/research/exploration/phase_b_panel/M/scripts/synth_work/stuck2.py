"""EXPLORATORY, read-only: rows with a stuck vehicle per stored arm; side-event means against p333."""
import pickle, sys, collections
import numpy as np
T = pickle.load(open(sys.argv[1], "rb"))
seeds = sorted(T["S|p333"])
LEARN = ("w0u250", "w1u500", "w2u250", "w3u500", "w4u500")
for cond in ("S", "TRUCK"):
    c = collections.Counter(); worst = []
    for nm in sorted(T):
        cc, a = nm.split("|", 1)
        if cc != cond or a in LEARN:
            continue
        st = np.array([T[nm][s]["stuck"] for s in seeds], float)
        c[int((st > 0).sum())] += 1
        if (st > 0).sum() >= 2:
            worst.append((a, int((st > 0).sum())))
    print(cond, "arms by number of rows with a stuck vehicle:", dict(sorted(c.items())), "arms with 2 or more:", worst)
