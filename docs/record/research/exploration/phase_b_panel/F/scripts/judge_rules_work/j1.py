import json, sys
J = json.load(open('/home/catalin/work/phd/v5b1_runs/planb_s6_read_v23/read6_v23.json'))
def keys(d, depth=0, maxd=2, pre=''):
    if isinstance(d, dict) and depth < maxd:
        for k, v in list(d.items())[:40]:
            t = type(v).__name__
            n = len(v) if hasattr(v, '__len__') and not isinstance(v, str) else ''
            print(pre + str(k), t, n)
            keys(v, depth + 1, maxd, pre + '  ')
keys(J, 0, 2)
