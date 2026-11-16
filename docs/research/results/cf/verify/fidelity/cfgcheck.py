import pickle, json, sys, hashlib
S = sys.argv[1]
sha = lambda o: hashlib.sha256(json.dumps(o, sort_keys=True).encode()).hexdigest()
RUN = "/home/catalin/work/phd/v5b1_runs/cf_remote"
for stage, pk in (("cf_screen", "screen.pkl"), ("cf_ident", "ident.pkl")):
    R = pickle.load(open(f"{S}/{pk}", "rb"))
    jobs = json.load(open(f"{RUN}/{stage}/jobs.json"))
    meta = json.load(open(f"{RUN}/{stage}/meta.json"))
    print(stage, "jobs_sha256 matches meta:", sha(jobs["arms"]) == meta["jobs_sha256"])
    want = {n: sha({k: v for k, v in c.items() if k != "measure"}) for n, c in jobs["arms"].items()}
    bad = [(r["name"], r["seed"]) for r in R if r["ctrl_sha256"] != want[r["name"]] or r["cfg_sha"] != want[r["name"]]]
    print(stage, "rows whose cfg or ctrl_sha256 differs from its job:", len(bad), "of", len(R))
j = json.load(open(f"{RUN}/cf_screen/jobs.json"))["arms"]
ji = json.load(open(f"{RUN}/cf_ident/jobs.json"))["arms"]
m = j["E30|MPC-F"]["ctrl"]["mpcf"]; print("MPC-F screen", {k: (v if not isinstance(v, (dict, list)) else "...") for k, v in m.items()})
print("MPC-F ident model", ji["S|MPC-F"]["ctrl"]["mpcf"]["model"], ji["S|MPC-F"]["ctrl"]["mpcf"].get("model_sha256"))
# every screen arm = its identity (stored S) config + event + split, nothing else
def strip(c):
    c = json.loads(json.dumps(c)); c.pop("measure", None); c.pop("split", None)
    c.get("ctrl", {}).get("env", {}).pop("perturb", None); return c
def walk(a, b, p=""):
    out = []
    if isinstance(a, dict) and isinstance(b, dict):
        for k in sorted(set(a) | set(b)):
            if k not in a or k not in b: out.append((p + "/" + k, "only one side"))
            else: out += walk(a[k], b[k], p + "/" + k)
    elif a != b: out.append((p, str(a)[:60], str(b)[:60]))
    return out
for n, c in j.items():
    a = n.split("|")[1]
    if a in ("p111", "p222"):
        d = walk(strip(c), strip(j["E30|p333"])); print(a, "vs p333:", d)
    else:
        d = walk(strip(c), strip(ji["S|" + a]))
        if d: print(a, "screen vs ident config:", d[:6])

print("ident perturb", {json.dumps(c["ctrl"]["env"].get("perturb")) for c in ji.values()}, "ident split", {c.get("split") for c in ji.values()})
print("p333 ctrl", json.dumps({k: v for k, v in j["E30|p333"]["ctrl"].items() if k != "env"})[:300]); print("p333 env", json.dumps(j["E30|p333"]["ctrl"]["env"])[:600]); print("ident p333 ctrl", json.dumps(ji["S|p333"].get("ctrl"))[:600])
print("nc screen ctrl", json.dumps(j["E30|nc"].get("ctrl"))[:400], "| ident", json.dumps(ji["S|nc"].get("ctrl"))[:200])
