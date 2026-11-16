# Re-derives corridor.build's node arithmetic (c1c 4dfefca, corridor.py:62-71) without netconvert, to see what accel_len does on r2m3.
NODES = [("n1", 0.0, 0.0), ("n2", 3000.0, 0.0), ("m", 3500.0, 0.0), ("ae", 3800.0, 0.0), ("d", 5000.0, 0.0),
         ("b", 6000.0, 0.0), ("x", 6500.0, 0.0), ("r0", 3080.0, -40.0), ("rm", 3470.0, -4.0)]
R2_NODES = {"e2": (5300.0, 0.0), "b": (6300.0, 0.0), "x": (6800.0, 0.0), "r02": (4580.0, -40.0), "rm2": (4970.0, -4.0)}
def nodes(accel_len, accel2_len):
    x_ae = dict((n, x) for n, x, _ in NODES)["ae"]
    nd = [(n, x + (accel_len - 300.0 if x >= x_ae else 0.0), y) for n, x, y in NODES]
    r2 = {n: (x + (accel2_len - 300.0 if n in ("e2", "b", "x") else 0.0), y) for n, (x, y) in R2_NODES.items()}
    nd = [(n, *r2.get(n, (x, y))) for n, x, y in nd] + [(n, *r2[n]) for n in ("e2", "r02", "rm2")]
    return {n: (x, y) for n, x, y in nd}
for al, a2 in ((300, 300), (300, 600), (600, 300), (600, 600)):
    p = nodes(al, a2)
    L = lambda a, b: round(((p[b][0]-p[a][0])**2 + (p[b][1]-p[a][1])**2) ** 0.5, 1)
    print(al, a2, {"3a": L("m", "ae"), "3": L("ae", "d"), "4a": L("d", "e2"), "4": L("e2", "b"), "rj2(rm2-d)": L("rm2", "d")})
