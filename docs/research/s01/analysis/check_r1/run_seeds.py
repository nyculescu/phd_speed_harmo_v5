import sys
sys.path.insert(0, ".")
import numpy as np
from mylib import *
T = load()
v = arm(T, "X1", "v3w", 5300, "ttc_net"); n = arm(T, "X1", "nc", 5300, "ttc_net")
d = sorted((v[s] - n[s], s) for s in v)
print("largest", d[-4:])
print("median region", d[18:22], "median", np.median([x for x, _ in d]))
