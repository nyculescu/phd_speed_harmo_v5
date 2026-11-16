import ast, math, json, glob
src = open("/home/catalin/work/phd/wt/c1c/v5b/fleet/corridor.py").read()
tree = ast.parse(src)
C = {}
for n in tree.body:
    if isinstance(n, ast.Assign) and n.targets[0].id in ("NODES", "R2_NODES") if isinstance(n, ast.Assign) and isinstance(n.targets[0], ast.Name) else False:
        C[n.targets[0].id] = ast.literal_eval(n.value)
NODES, R2_NODES = C["NODES"], C["R2_NODES"]
def nodes_of(accel_len, accel2_len):     # corridor.py:63-67 verbatim, r2m3 branch
    x_ae = dict((n, x) for n, x, _ in NODES)["ae"]
    nodes = [(n, x + (accel_len - 300.0 if x >= x_ae else 0.0), y) for n, x, y in NODES]
    r2 = {n: (x + (accel2_len - 300.0 if n in ("e2", "b", "x") else 0.0), y) for n, (x, y) in R2_NODES.items()}
    nodes = [(n, *r2.get(n, (x, y))) for n, x, y in nodes] + [(n, *r2[n]) for n in ("e2", "r02", "rm2")]
    return {n: (x, y) for n, x, y in nodes}
E = {"1": ("n1", "n2"), "2": ("n2", "m"), "3a": ("m", "ae"), "3": ("ae", "d"), "4a": ("d", "e2"), "4": ("e2", "b"), "5": ("b", "x"), "r": ("r0", "rm"), "rj": ("rm", "m"), "r2": ("r02", "rm2"), "rj2": ("rm2", "d")}
for a, b in ((300, 300), (300, 600), (600, 300), (600, 600), (600, 900)):
    N = nodes_of(float(a), float(b))
    L = {e: round(math.dist(N[u], N[v]), 2) for e, (u, v) in E.items()}
    print(a, b, {k: N[k][0] for k in ("m", "ae", "d", "e2", "b", "x", "rm2", "r02")}, L)
for f in glob.glob("/home/catalin/work/phd/**/_netcache/r2m3_*/spec.json", recursive=True)[:6]:
    s = json.load(open(f))
    print(f, {n: x for n, x, _ in s["nodes"] if n in ("ae", "d", "e2", "b", "x", "rm2")}, {k: v for k, v in s["lane_lengths"].items() if k.endswith("_0")})
