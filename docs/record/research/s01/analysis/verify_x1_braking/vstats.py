import sys
from vlib import *
mets = sys.argv[1].split(',')
pairs = [x.split(':') for x in sys.argv[2].split(',')]
cells = sys.argv[3].split(',') if len(sys.argv) > 3 else ['X1', 'X2']
n = 0
for cell in cells:
    for m in mets:
        for a, b in pairs:
            b2 = {'3exc': '3ex1' if cell == 'X1' else '3ex2'}.get(b, b)
            sign = 1 if m in ('passed',) else -1
            t = comp(arm(cell, a, m), arm(cell, b2, m), sign)
            n += 1
            print(f'{cell} {m:24s} {a}-{b2:9s} {fmt(t)}')
print('comparisons', n)
