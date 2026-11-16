from vlib import *
n = 0
for a in ('nc', 'v3w', '3e', 'p333', 'os1_15_10'):
    for m in ('ev45_all', 'ev45_car', 'ev45_alks', 'ev4_all', 'ev5_alks', 'all_delay', 'km_all'):
        t = comp(arm('X1', a, m), arm('X2', a, m))
        n += 1
        print(f'{a:10s} {m:10s} X1-X2 {fmt(t)}')
print('comparisons', n)
