import json, sys
J = json.load(open(sys.argv[1]))
def show(d, depth=0, maxd=3, pre=""):
    if isinstance(d, dict):
        ks = list(d.keys())
        print(pre + f"dict[{len(ks)}]: " + ", ".join(map(str, ks[:40])) + (" ..." if len(ks) > 40 else ""))
        if depth < maxd:
            for k in ks[:6]:
                show(d[k], depth + 1, maxd, pre + "  " + str(k) + " -> ")
    elif isinstance(d, list):
        print(pre + f"list[{len(d)}] " + (str(d)[:160]))
    else:
        print(pre + str(d)[:160])
show(J, 0, int(sys.argv[2]) if len(sys.argv) > 2 else 2)
