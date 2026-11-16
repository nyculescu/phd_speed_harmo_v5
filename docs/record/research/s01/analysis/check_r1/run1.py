import sys
sys.path.insert(0, ".")
from mylib import *
T = load()
cells = sorted({(c, q) for (c, a, q) in T})
print(cells)
for c, q in cells:
    print(c, q, sorted({a for (cc, a, qq) in T if cc == c and qq == q}))
