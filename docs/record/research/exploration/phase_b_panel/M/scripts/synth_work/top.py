"""EXPLORATORY, read-only: exact sign of the top stored rules' median paired delay difference against p333 in S."""
import pickle, sys
import numpy as np
T = pickle.load(open(sys.argv[1], "rb"))
seeds = sorted(T["S|p333"]); P = np.array([T["S|p333"][s]["d"] for s in seeds]); med = np.median(P)
LEARN = ("w0u250", "w1u500", "w2u250", "w3u500", "w4u500")
pos = 0; k = 0
for nm in sorted(T):
    c, a = nm.split("|", 1)
    if c != "S" or a in LEARN or a in ("p333", "nc"):
        continue
    k += 1
    d = P - np.array([T[nm][s]["d"] for s in seeds])
    m = np.median(d)
    pos += m > 0
    if abs(m) / med < 1e-3:
        print(a, "median diff veh-s %.3f" % m, "wins", int((d > 0).sum()), "losses", int((d < 0).sum()), "ties", int((d == 0).sum()))
print("rules", k, "with median paired difference above 0:", pos)
